"""Forecast models trained on our own data (production).

Model C  discharge at Marracuene 1 to 7 days ahead, from the river's recent discharge
         and the rain that has already fallen on the basin. It needs no rain forecast,
         so it is an independent second opinion (and a fallback) next to the GloFAS
         scenarios.
Turbidity  probability that the river water is more turbid than usual ("elevada")
         on each of the coming mornings, per river reach, from discharge, rain, the
         time of year, the computed tide and the latest satellite measurement.

Both are evaluated on data they never saw; the skill tables are saved next to the
models so the bulletin can say how far each number can be trusted.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from functools import lru_cache

import numpy as np
import pandas as pd

from .config import path
from .drivers import read_table
from .forecast import fetch_json, load_history, load_limits

# ----------------------------------------------------------------------------- Model C: discharge
RAIN_WINDOWS = (1, 2, 3, 5, 7, 14, 30, 60)
Q_LAGS = (0, 1, 2, 3, 5, 7)


def discharge_features(daily: pd.DataFrame) -> pd.DataFrame:
    """Features of day t from a daily table with `q` and `rain`: what is known that day."""
    lq = np.log1p(daily["q"])
    x = pd.DataFrame(index=daily.index)
    for lag in Q_LAGS:
        x[f"lq_{lag}"] = lq.shift(lag)
    x["dq1"], x["dq3"] = lq - lq.shift(1), lq - lq.shift(3)
    for w in RAIN_WINDOWS:
        x[f"p{w}"] = daily["rain"].rolling(w, min_periods=w).sum()
    x["rain_max3"] = daily["rain"].rolling(3, min_periods=3).max()
    doy = daily.index.dayofyear
    x["sin"], x["cos"] = np.sin(2 * np.pi * doy / 365.25), np.cos(2 * np.pi * doy / 365.25)
    return x


def _nse(obs, pred) -> float:
    obs, pred = np.asarray(obs, "float64"), np.asarray(pred, "float64")
    return float(1 - ((obs - pred) ** 2).sum() / ((obs - obs.mean()) ** 2).sum())


def fit_discharge_model(cfg: dict) -> pd.DataFrame:
    """Train one XGBoost regressor per lead time on the history up to `calibration_end`, test it on
    the later years, save models/modelo_c_caudal.joblib and return the skill table.

    Skill columns (test years only), for the model and for persistence ("the discharge stays as
    it is today"):
      nse        1 = perfect, 0 = no better than always saying the average
      pod        of the days above the laranja limit, share that was forecast
      far        of the days forecast above the limit, share that was a false alarm
      csi        hits / (hits + misses + false alarms)
    """
    import joblib
    from xgboost import XGBRegressor

    f = cfg["forecast"]
    daily = load_history(cfg).dropna()
    x = discharge_features(daily)
    lq = np.log1p(daily["q"])
    limit = load_limits(cfg)["discharge_m3s"]["laranja"]
    models, rows, test_series = {}, [], {}
    for lead in f["model_leads"]:
        y = lq.shift(-lead)
        ok = x.notna().all(axis=1) & y.notna()
        train, test = ok & (x.index <= f["calibration_end"]), ok & (x.index > f["calibration_end"])
        model = XGBRegressor(n_estimators=400, max_depth=5, learning_rate=0.05, subsample=0.8, colsample_bytree=0.8,
                             n_jobs=4, random_state=cfg["processing"]["seed"]).fit(x[train], y[train])
        models[lead] = model
        obs, pred, persistence = np.expm1(y[test]), np.expm1(model.predict(x[test])), daily["q"][test]
        row = {"dias_a_frente": lead, "dias_de_teste": int(test.sum())}
        for name, p in (("modelo", pred), ("persistencia", persistence.to_numpy())):
            above_f, above_o = p >= limit, obs.to_numpy() >= limit
            hits = (above_f & above_o).sum()
            row.update({f"nse_{name}": _nse(obs, p), f"pod_{name}": hits / max(above_o.sum(), 1),
                        f"far_{name}": (above_f & ~above_o).sum() / max(above_f.sum(), 1),
                        f"csi_{name}": hits / max((above_f | above_o).sum(), 1)})
        rows.append(row)
        test_series[lead] = pd.DataFrame({"observado": obs.to_numpy(), "modelo": pred, "persistencia": persistence.to_numpy()},
                                         index=obs.index + pd.Timedelta(days=lead))
    skill = pd.DataFrame(rows).set_index("dias_a_frente")
    out = path(cfg, "models", "modelo_c_caudal.joblib")
    joblib.dump({"models": models, "features": list(x.columns), "leads": f["model_leads"]}, out, compress=3)
    out.with_suffix(".json").write_text(json.dumps({
        "name": "modelo_c_caudal", "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "train": [str(daily.index.min().date()), f["calibration_end"]], "test_from": str((pd.Timestamp(f["calibration_end"]) + pd.Timedelta(days=1)).date()),
        "target": "log1p(discharge) at t + lead", "skill": skill.round(3).reset_index().to_dict("records")}, indent=1))
    skill.attrs["test_series"] = test_series
    return skill


def predict_discharge(cfg: dict, fc: dict) -> pd.DataFrame:
    """Model C forecast for the coming days, from the river and rain observed up to today.

    The recent discharge comes from the forecast service (median of the scenarios for past days,
    which are all equal there) and the recent rain from the weather service.
    """
    import joblib

    saved = joblib.load(path(cfg, "models", "modelo_c_caudal.joblib", mkdir=False))
    today = pd.Timestamp(fc["date"])
    history = load_history(cfg)
    q = pd.concat([history["q"].dropna(), fc["discharge"].median(axis=1)])
    q = q[~q.index.duplicated(keep="last")].sort_index().loc[:today]
    rain = pd.concat([history["rain"].dropna(), fc["rain"]])
    rain = rain[~rain.index.duplicated(keep="last")].sort_index().loc[:today]
    daily = pd.DataFrame({"q": q, "rain": rain}).loc[today - pd.Timedelta(days=90):today].dropna()
    row = discharge_features(daily).iloc[[-1]][saved["features"]]
    if row.isna().any(axis=None) or daily.index.max() < today - pd.Timedelta(days=2):
        return pd.DataFrame(columns=["caudal_modelo_c"])
    values = {daily.index.max() + pd.Timedelta(days=lead): float(np.expm1(model.predict(row)[0])) for lead, model in saved["models"].items()}
    return pd.Series(values, name="caudal_modelo_c").to_frame().rename_axis("date")


# ----------------------------------------------------------------------------- turbidity outlook
# What the tests showed (notebook 35): machine-learning models do not predict turbidity better
# than the time of year, but turbidity rises steadily with discharge. The outlook is therefore a
# transparent table: how often the water was "elevada" at each level of discharge.
ELEVATED_QUANTILE = 0.75        # "elevada" = among the 25 % most turbid days of the reach's own record
UNRELIABLE_REACH = "1 montante (norte)"     # narrow reach: the two satellites agree poorly there (r 0.65)


def discharge_classes(cfg: dict) -> tuple[list[float], list[str]]:
    """Discharge classes of the turbidity table: three below the yellow limit, then the alert levels."""
    limits = load_limits(cfg)["discharge_m3s"]
    edges = [0.0, 20.0, 60.0, limits["amarelo"], limits["laranja"], float("inf")]
    labels = ["abaixo de 20", "20 a 60", f"60 a {limits['amarelo']:.0f}",
              f"{limits['amarelo']:.0f} a {limits['laranja']:.0f} (amarelo)", f"acima de {limits['laranja']:.0f} (laranja ou mais)"]
    return edges, labels


def turbidity_days(cfg: dict, sensor: str = "sentinel2", limits: dict | None = None) -> pd.DataFrame:
    """One row per day and reach measured by satellite: NDTI, the discharge of the day and its class,
    and whether the turbidity was `elevada` (NDTI above the reach's own limit, from Sentinel-2)."""
    from .water_quality import load_scene_series

    measured = load_scene_series(cfg, sensor)
    table = measured.join(load_history(cfg)["q"], on="date").dropna(subset=["q", "ndti"]).reset_index(drop=True)
    if limits is None:
        limits = table.groupby("troco")["ndti"].quantile(ELEVATED_QUANTILE).to_dict()
    edges, labels = discharge_classes(cfg)
    table["classe_caudal"] = pd.cut(table["q"], edges, labels=labels, right=False)
    table["elevada"] = (table["ndti"] >= table["troco"].map(limits)).astype(int)
    table["ano"], table["mes"] = table["date"].dt.year, table["date"].dt.month
    table.attrs["limits"] = limits
    return table


def fit_turbidity_table(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Build the table "share of days with elevated turbidity, by discharge class" and test it.

    Uses the three reaches where the measurement is reliable. Returns
    (the table, its skill, the Sentinel-2 days with out-of-year predictions).
    Skill rows:
      tabela (ano deixado de fora)   each year predicted with a table built from the other years
      referência: época do ano       share of elevated days of that calendar month in the other years
      tabela, dias do Landsat antes de 2017   another satellite and other years
    auc = ranking skill (0.5 = chance); brier = error of the probability (lower is better);
    bss = Brier skill against the time-of-year reference (above 0 = better).
    """
    from sklearn.metrics import brier_score_loss, roc_auc_score

    days = turbidity_days(cfg)
    limits = days.attrs["limits"]
    days = days[days["troco"] != UNRELIABLE_REACH].copy()
    days["prob_tabela"], days["prob_epoca"] = np.nan, np.nan
    for year in sorted(days["ano"].unique()):
        inside = days["ano"] == year
        train = days[~inside]
        rate = train.groupby("classe_caudal", observed=False)["elevada"].mean().fillna(train["elevada"].mean())
        days.loc[inside, "prob_tabela"] = days.loc[inside, "classe_caudal"].map(rate).astype(float)
        season = train.groupby("mes")["elevada"].mean()
        days.loc[inside, "prob_epoca"] = days.loc[inside, "mes"].map(season).fillna(train["elevada"].mean())

    grouped = days.groupby("classe_caudal", observed=False)["elevada"]
    table = pd.DataFrame({"dias_medidos": grouped.size(), "turbidez_elevada": grouped.mean()})
    # 90 % interval of the share (Wilson), so a class with few days shows how uncertain it is
    n, share, z = table["dias_medidos"].clip(lower=1), table["turbidez_elevada"], 1.645
    centre, half = (share + z**2 / (2 * n)) / (1 + z**2 / n), z * np.sqrt(share * (1 - share) / n + z**2 / (4 * n**2)) / (1 + z**2 / n)
    table["intervalo_min"], table["intervalo_max"] = (centre - half).clip(0, 1), (centre + half).clip(0, 1)
    table.index.name = "caudal_m3s"

    def row(name, frame, prob, base=None):
        out = {"previsao": name, "dias": int(len(frame)), "auc": roc_auc_score(frame["elevada"], frame[prob]),
               "brier": brier_score_loss(frame["elevada"], frame[prob])}
        if base is not None:
            out["bss"] = 1 - out["brier"] / brier_score_loss(frame["elevada"], frame[base])
        return out

    rows = [row("tabela por caudal (ano deixado de fora)", days, "prob_tabela", "prob_epoca"), row("referência: época do ano", days, "prob_epoca")]
    other = turbidity_days(cfg, "landsat89", limits=limits)
    other = other[(other["troco"] != UNRELIABLE_REACH) & (other["date"] < days["date"].min())].copy()
    if len(other) >= 50 and other["elevada"].nunique() == 2:
        other["prob_tabela"] = other["classe_caudal"].map(table["turbidez_elevada"]).astype(float)
        rows.append(row("tabela, dias do Landsat antes de 2017", other, "prob_tabela"))
    skill = pd.DataFrame(rows).set_index("previsao")

    path(cfg, "models", "turbidez_por_caudal.json").write_text(json.dumps({
        "name": "turbidez_por_caudal", "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "indicator": "NDTI = (red - green) / (red + green), median of the open-water pixels of the reach, per satellite image",
        "elevated_definition": f"NDTI at or above the {int(ELEVATED_QUANTILE * 100)}th percentile of the reach's Sentinel-2 record",
        "ndti_limits": {k: round(float(v), 4) for k, v in limits.items()}, "reaches_used": sorted(days["troco"].unique()),
        "period": [str(days["date"].min().date()), str(days["date"].max().date())],
        "classes": {"edges_m3s": [e if np.isfinite(e) else None for e in discharge_classes(cfg)[0]], "labels": discharge_classes(cfg)[1]},
        "table": table.round(3).reset_index().to_dict("records"), "skill": skill.round(3).reset_index().to_dict("records")}, indent=1, ensure_ascii=False))
    return table, skill, days


# ---- turbidity model: tide and latest measurement ----------------------------------------------
# What the tests showed (notebook 35):
#   * the day-to-day swings of the water colour that discharge and season could not explain
#     follow the tide (test 5);
#   * what is still unexplained lasts for weeks, so the latest satellite measurement of the
#     reach improves the forecast (test 6);
#   * wind, local rain, rain per sub-basin and training on both satellites were tested and did
#     not improve the probability of "elevada", so they are not used.
# The tide is computed from harmonic constants fitted to an hourly sea-level series of Maputo
# Bay, so it is known for any past or future moment.
M2_PERIOD_H = 12.4206012
OVERPASS_UTC = "07:30"                   # Sentinel-2 passes between 07:26 and 07:42 UTC (about 09:30 local)
LANDSAT_OVERPASS_UTC = "07:40"           # Landsat scene time is not stored; results barely change within +/- 15 min
TIDE_SPEEDS = {"M2": 28.9841042, "S2": 30.0, "N2": 28.4397295, "K2": 30.0821373, "K1": 15.0410686, "O1": 13.9430356,
               "P1": 14.9589314, "Q1": 13.3986609, "M4": 57.9682084, "MS4": 58.9841042, "MN4": 57.4238337, "L2": 29.5284789,
               "NU2": 28.5125831, "MU2": 27.9682084, "2N2": 27.8953548, "T2": 29.9589333, "M6": 86.9523127, "SA": 0.0410686,
               "SSA": 0.0821373, "MM": 0.5443747, "MSF": 1.0158958, "MF": 1.0980331}      # degrees per hour
DRIVER_FEATURES = ["lq", "lq_mean7", "lq_max7", "dq3", "p3", "p7", "p30", "sin", "cos"]
M2_FEATURES = ["m2_sin", "m2_cos"]                       # the first tide test; kept for the record
TIDE_FEATURES = ["t_h", "t_dh", "t_range"]               # height (m), change per hour, range of the last 12.5 h
LAST_FEATURES = ["last_ndti", "last_age", "last_t_h", "last_lq", "has_last"]
TIDE_MODEL_FEATURES = DRIVER_FEATURES + TIDE_FEATURES + LAST_FEATURES
TRAIN_LAGS = (1, 3, 5, 10, None)         # ages of the latest measurement the model is trained for (None = no measurement)
MAX_AGE_DAYS = 30                        # an older measurement is not used


def _tide_design(times) -> np.ndarray:
    hours = np.asarray((pd.DatetimeIndex(times) - pd.Timestamp("2000-01-01")) / pd.Timedelta(hours=1), "float64")
    columns = [np.ones_like(hours)]
    for speed in TIDE_SPEEDS.values():
        columns += [np.cos(np.radians(speed) * hours), np.sin(np.radians(speed) * hours)]
    return np.column_stack(columns)


def fit_tide_constants(cfg: dict) -> dict:
    """Fit the harmonic constants of the tide to the hourly sea level of Maputo Bay and save them.

    The series comes from the Open-Meteo marine service (about 0.8 MB, downloaded once and kept in
    data/raw/tide). The test: constants fitted without the last 12 months must reproduce them.
    The constants are fixed: the slow 18.6-year change of the tide is not modelled.
    """
    f = cfg["forecast"]
    file = path(cfg, "tide", "nivel_do_mar_baia_de_maputo.csv")
    if not file.exists():
        lat, lon = f["tide_point"]
        parts, last = [], datetime.now(timezone.utc).date()
        for year in range(int(f["tide_history_start"][:4]), last.year + 1):
            j = fetch_json(f["marine_api"], {"latitude": lat, "longitude": lon, "hourly": "sea_level_height_msl", "timezone": "GMT",
                                             "start_date": max(f"{year}-01-01", f["tide_history_start"]), "end_date": min(f"{year}-12-31", str(last))})
            parts.append(pd.Series(j["hourly"]["sea_level_height_msl"], index=pd.to_datetime(j["hourly"]["time"]), dtype="float64"))
        pd.concat(parts).rename("nivel_m").rename_axis("time").to_csv(file)
    level = pd.read_csv(file, index_col=0, parse_dates=True).iloc[:, 0].dropna()
    cut = level.index.max() - pd.Timedelta(days=365)
    train, test = level[:cut], level[cut:]
    trial = np.linalg.lstsq(_tide_design(train.index), train.to_numpy(), rcond=None)[0]
    error = test.to_numpy() - _tide_design(test.index) @ trial
    coef = np.linalg.lstsq(_tide_design(level.index), level.to_numpy(), rcond=None)[0]
    names = list(TIDE_SPEEDS)
    out = {"name": "mare_maputo", "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "source": "Open-Meteo marine API, sea_level_height_msl", "point": f["tide_point"],
           "period": [str(level.index.min()), str(level.index.max())], "hours": int(len(level)),
           "test_last_12_months": {"r2": round(float(1 - (error ** 2).sum() / ((test - test.mean()) ** 2).sum()), 4), "rmse_m": round(float(np.sqrt((error ** 2).mean())), 3)},
           "amplitude_m": {n: round(float(np.hypot(coef[1 + 2 * i], coef[2 + 2 * i])), 3) for i, n in enumerate(names)},
           "epoch": "2000-01-01T00:00Z", "speeds_deg_per_hour": TIDE_SPEEDS, "coefficients": [float(c) for c in coef]}
    path(cfg, "models", "mare_maputo.json").write_text(json.dumps(out, indent=1))
    _tide_coefficients.cache_clear()
    return out


@lru_cache(maxsize=4)
def _tide_coefficients(file: str) -> np.ndarray:
    saved = json.loads(open(file).read())
    if list(saved["speeds_deg_per_hour"]) != list(TIDE_SPEEDS):
        raise ValueError("tide constants do not match the code: run forecast_models.fit_tide_constants")
    return np.asarray(saved["coefficients"], "float64")


def tide_height(cfg: dict, times) -> np.ndarray:
    """Computed tide (m above mean sea level) in Maputo Bay at the given UTC times."""
    return _tide_design(times) @ _tide_coefficients(str(path(cfg, "models", "mare_maputo.json", mkdir=False)))


def tide_features(cfg: dict, times) -> pd.DataFrame:
    """Tide at the given UTC times: height, change over one hour (rising or falling) and the range
    of the 12.5 hours before (large on spring tides, small on neap tides)."""
    times = pd.DatetimeIndex(times)
    steps = np.arange(-750, 1, 10)
    before = np.column_stack([tide_height(cfg, times + pd.Timedelta(minutes=int(m))) for m in steps])
    return pd.DataFrame({"t_h": before[:, -1], "t_dh": tide_height(cfg, times + pd.Timedelta(minutes=30)) - tide_height(cfg, times - pd.Timedelta(minutes=30)),
                         "t_range": before.max(axis=1) - before.min(axis=1)}, index=times)


def m2_phase(times) -> pd.DataFrame:
    """Sine and cosine of the phase of the main lunar tide (M2) at the given UTC times."""
    times = pd.DatetimeIndex(times)
    hours = (times - pd.Timestamp("2000-01-01")) / pd.Timedelta(hours=1)
    phase = 2 * np.pi * ((np.asarray(hours, "float64") / M2_PERIOD_H) % 1)
    return pd.DataFrame({"m2_sin": np.sin(phase), "m2_cos": np.cos(phase)}, index=times)


def image_times(cfg: dict) -> pd.Series:
    """UTC time of the Sentinel-2 image of each date, read from the image identifiers."""
    files = sorted(path(cfg, "water_quality", mkdir=False).glob("sentinel2_*.csv"))
    scenes = pd.concat([pd.read_csv(f, usecols=["date", "image"]) for f in files])
    stamp = pd.to_datetime(scenes["image"].str.extract(r"^(\d{8}T\d{6})")[0], format="%Y%m%dT%H%M%S")
    return stamp.groupby(pd.to_datetime(scenes["date"])).min()


def _overpass(cfg: dict, dates: pd.Series, sensor: str) -> pd.Series:
    if sensor == "sentinel2":
        return dates.map(image_times(cfg)).fillna(dates + pd.Timedelta(OVERPASS_UTC + ":00"))
    return dates + pd.Timedelta(LANDSAT_OVERPASS_UTC + ":00")


def _daily_drivers(history: pd.DataFrame) -> pd.DataFrame:
    lq = np.log1p(history["q"])
    doy = history.index.dayofyear
    return pd.DataFrame({"lq": lq, "lq_mean7": lq.rolling(7, min_periods=5).mean(), "lq_max7": lq.rolling(7, min_periods=5).max(),
                         "dq3": lq - lq.shift(3), "p3": history["rain"].rolling(3, min_periods=3).sum(),
                         "p7": history["rain"].rolling(7, min_periods=7).sum(), "p30": history["rain"].rolling(30, min_periods=30).sum(),
                         "sin": np.sin(2 * np.pi * doy / 365.25), "cos": np.cos(2 * np.pi * doy / 365.25)}, index=history.index)


def tide_model_table(cfg: dict, sensor: str = "sentinel2", limits: dict | None = None, reaches: list[str] | None = None) -> pd.DataFrame:
    """Measured days with their drivers and the tide at image time (reaches with a forecast only)."""
    days = turbidity_days(cfg, sensor, limits=limits)
    limits = days.attrs["limits"]
    days = days[days["troco"] != UNRELIABLE_REACH].join(_daily_drivers(load_history(cfg).dropna(subset=["q"])), on="date")
    when = _overpass(cfg, days["date"], sensor)
    for block in (m2_phase(when), tide_features(cfg, when)):
        for col in block:
            days[col] = block[col].to_numpy()
    days = days.dropna(subset=DRIVER_FEATURES).reset_index(drop=True)
    reaches = reaches or sorted(days["troco"].unique())
    for reach in reaches:
        days[f"troco={reach}"] = (days["troco"] == reach).astype(float)
    days.attrs.update(limits=limits, reaches=reaches)
    return days


def measurement_source(cfg: dict, bias: float | None = None) -> pd.DataFrame:
    """Every satellite measurement of the reaches, Sentinel-2 and Landsat 8/9 together, used as
    "the latest measurement". Landsat is put on the Sentinel-2 scale by adding `bias` (by default
    the mean difference on the days both satellites measured). `.attrs["bias"]` holds the value."""
    from .water_quality import load_scene_series

    s2, landsat = load_scene_series(cfg, "sentinel2"), load_scene_series(cfg, "landsat89")
    if bias is None:
        pairs = s2.merge(landsat, on=["date", "troco"], suffixes=("", "_landsat"))
        pairs = pairs[pairs["troco"] != UNRELIABLE_REACH]
        bias = float((pairs["ndti"] - pairs["ndti_landsat"]).mean())
    landsat = landsat.assign(ndti=landsat["ndti"] + bias)
    parts = []
    for sensor, table in (("sentinel2", s2), ("landsat89", landsat)):
        tide = tide_features(cfg, _overpass(cfg, table["date"], sensor))
        parts.append(table[["date", "troco", "ndti"]].assign(sensor=sensor, t_h=tide["t_h"].to_numpy()))
    source = pd.concat(parts, ignore_index=True).drop_duplicates(subset=["date", "troco"], keep="first")      # same day: Sentinel-2 first
    source = source.join(np.log1p(load_history(cfg)["q"]).rename("lq"), on="date").sort_values(["troco", "date"]).reset_index(drop=True)
    source.attrs["bias"] = bias
    return source


def add_last_measurement(rows: pd.DataFrame, source: pd.DataFrame, min_lag: int | None, medians: dict) -> pd.DataFrame:
    """Add to each row (date, troco, lq) the latest measurement of its reach made at least `min_lag`
    days before and at most MAX_AGE_DAYS before: its NDTI, its age in days, and the tide and the
    discharge when it was made. `min_lag=None`, or no measurement in range: has_last = 0 and
    neutral values (the reach's usual NDTI)."""
    out = rows.copy()
    out["last_ndti"], out["last_age"] = out["troco"].map(medians).astype(float), 99.0
    out["last_t_h"], out["last_lq"], out["has_last"] = 0.0, out["lq"].astype(float), 0.0
    if min_lag is None:
        return out
    for reach, group in rows.groupby("troco"):
        src = source[(source["troco"] == reach) & source["ndti"].notna()].sort_values("date")
        if src.empty:
            continue
        dates = src["date"].to_numpy()
        pos = np.searchsorted(dates, (group["date"] - pd.Timedelta(days=min_lag)).to_numpy(), side="right") - 1
        safe = np.clip(pos, 0, None)
        age = (group["date"].to_numpy() - dates[safe]) / np.timedelta64(1, "D")
        ok = (pos >= 0) & (age <= MAX_AGE_DAYS)
        lq = src["lq"].to_numpy()[safe]
        ok &= np.isfinite(lq)
        idx = group.index[ok]
        out.loc[idx, "last_ndti"], out.loc[idx, "last_age"] = src["ndti"].to_numpy()[safe][ok], age[ok]
        out.loc[idx, "last_t_h"], out.loc[idx, "last_lq"], out.loc[idx, "has_last"] = src["t_h"].to_numpy()[safe][ok], lq[ok], 1.0
    return out


def _tide_models(seed: int):
    from sklearn.ensemble import GradientBoostingClassifier, GradientBoostingRegressor

    settings = dict(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=seed)
    return GradientBoostingRegressor(**settings), GradientBoostingClassifier(**settings)


def _stack_lags(days: pd.DataFrame, source: pd.DataFrame, medians: dict) -> pd.DataFrame:
    parts = [add_last_measurement(days, source, lag, medians).assign(atraso=-1 if lag is None else lag) for lag in TRAIN_LAGS]
    return pd.concat(parts, ignore_index=True)


def fit_turbidity_model(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Train the turbidity model and test it.

    Inputs: discharge, rain, time of year, the computed tide at the hour of the satellite, and the
    latest satellite measurement of the reach (either satellite). The model is trained for several
    ages of that measurement, and for having none, so it can be used on every day of the horizon.

    Returns (skill table, Sentinel-2 days with out-of-year predictions, Landsat days with predictions).
    Skill rows, all "ano deixado de fora" (each year predicted by models that never saw it):
      modelo final, by age of the latest measurement, and with no measurement
      steps that led here: tide as the M2 phase only; no tide; the time of year
    and the final model, trained on Sentinel-2 only, on the days measured by Landsat.
    r2 = share of the variation of NDTI explained; auc and bss refer to "turbidity elevated".
    """
    import joblib
    from sklearn.metrics import brier_score_loss, mean_absolute_error, r2_score, roc_auc_score

    seed = cfg["processing"]["seed"]
    if not path(cfg, "models", "mare_maputo.json", mkdir=False).exists():
        fit_tide_constants(cfg)
    days = tide_model_table(cfg)
    limits, reaches = days.attrs["limits"], days.attrs["reaches"]
    reach_cols = [c for c in days if c.startswith("troco=")]
    final = TIDE_MODEL_FEATURES + reach_cols
    steps = {"m2": DRIVER_FEATURES + M2_FEATURES + reach_cols, "sem": DRIVER_FEATURES + reach_cols}
    source = measurement_source(cfg)
    medians = days.groupby("troco")["ndti"].median().to_dict()
    stacked = _stack_lags(days, source, medians)
    stacked["ndti_modelo"], stacked["prob_modelo"] = np.nan, np.nan
    for col in ("ndti_m2", "prob_m2", "ndti_sem", "prob_sem", "ndti_epoca", "prob_epoca"):
        days[col] = np.nan
    for year in sorted(days["ano"].unique()):
        inside, s_inside = days["ano"] == year, stacked["ano"] == year
        train, test = days[~inside], days[inside]
        regressor, classifier = _tide_models(seed)
        stacked.loc[s_inside, "ndti_modelo"] = regressor.fit(stacked.loc[~s_inside, final], stacked.loc[~s_inside, "ndti"]).predict(stacked.loc[s_inside, final])
        stacked.loc[s_inside, "prob_modelo"] = classifier.fit(stacked.loc[~s_inside, final], stacked.loc[~s_inside, "elevada"]).predict_proba(stacked.loc[s_inside, final])[:, 1]
        for tag, features in steps.items():
            regressor, classifier = _tide_models(seed)
            days.loc[inside, f"ndti_{tag}"] = regressor.fit(train[features], train["ndti"]).predict(test[features])
            days.loc[inside, f"prob_{tag}"] = classifier.fit(train[features], train["elevada"]).predict_proba(test[features])[:, 1]
        season = train.groupby(["troco", "mes"])[["ndti", "elevada"]].mean()
        key = list(zip(test["troco"], test["mes"]))
        days.loc[inside, "ndti_epoca"] = [season["ndti"].get(k, train["ndti"].mean()) for k in key]
        days.loc[inside, "prob_epoca"] = [season["elevada"].get(k, train["elevada"].mean()) for k in key]
    # the stacked table repeats the days in the same order for every age, so the columns line up
    for lag in TRAIN_LAGS:
        tag = "sem_medicao" if lag is None else f"{lag}d"
        part = stacked[stacked["atraso"] == (-1 if lag is None else lag)]
        days[f"ndti_modelo_{tag}"], days[f"prob_modelo_{tag}"] = part["ndti_modelo"].to_numpy(), part["prob_modelo"].to_numpy()

    def row(name, frame, value, prob, base=None):
        out = {"modelo": name, "dias": int(len(frame)), "r2": r2_score(frame["ndti"], frame[value]),
               "mae": mean_absolute_error(frame["ndti"], frame[value]), "auc": roc_auc_score(frame["elevada"], frame[prob])}
        if base is not None:
            out["bss"] = 1 - brier_score_loss(frame["elevada"], frame[prob]) / brier_score_loss(frame["elevada"], frame[base])
        return out

    rows = [row(f"modelo final: última medição há {lag} dia{'s' if lag > 1 else ''} ou mais", days, f"ndti_modelo_{lag}d", f"prob_modelo_{lag}d", "prob_epoca")
            for lag in TRAIN_LAGS if lag is not None]
    rows += [row("modelo final: sem medição recente", days, "ndti_modelo_sem_medicao", "prob_modelo_sem_medicao", "prob_epoca"),
             row("passo anterior: maré só pela fase M2", days, "ndti_m2", "prob_m2", "prob_epoca"),
             row("sem maré", days, "ndti_sem", "prob_sem", "prob_epoca"),
             row("referência: época do ano", days, "ndti_epoca", "prob_epoca")]

    regressor, classifier = _tide_models(seed)
    regressor.fit(stacked[final], stacked["ndti"])
    classifier.fit(stacked[final], stacked["elevada"])
    other = tide_model_table(cfg, "landsat89", limits=limits, reaches=reaches)
    other = add_last_measurement(other, source, 5, medians)
    other["ndti_modelo"] = regressor.predict(other[final])
    other["prob_modelo"] = classifier.predict_proba(other[final])[:, 1]
    rows.append(row("modelo final no Landsat 8/9 (outro satélite): todos os anos", other, "ndti_modelo", "prob_modelo"))
    before = other[other["date"] < days["date"].min()]
    if len(before) >= 50 and before["elevada"].nunique() == 2:
        rows.append(row("modelo final no Landsat antes de 2017 (outro satélite e outros anos)", before, "ndti_modelo", "prob_modelo"))
    skill = pd.DataFrame(rows).set_index("modelo")

    out = path(cfg, "models", "modelo_turbidez.joblib")
    joblib.dump({"regressor": regressor, "classifier": classifier, "features": final, "reaches": reaches, "limits": limits,
                 "medians": medians, "landsat_bias": source.attrs["bias"]}, out, compress=3)
    out.with_suffix(".json").write_text(json.dumps({
        "name": "modelo_turbidez", "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "target": "NDTI (water colour index) of the reach at the morning satellite overpass; and the event 'elevada'",
        "features": final, "reaches": reaches, "ndti_limits_elevada": {k: round(float(v), 4) for k, v in limits.items()},
        "landsat_bias_added": round(source.attrs["bias"], 4), "latest_measurement_max_age_days": MAX_AGE_DAYS,
        "rows": int(len(days)), "period": [str(days["date"].min().date()), str(days["date"].max().date())],
        "valid_for": f"about {OVERPASS_UTC} UTC (09:30 local): the only time of day the satellites observe",
        "tested_and_not_used": ["wind", "local rain", "rain per sub-basin", "training on both satellites together"],
        "skill": skill.round(3).reset_index().to_dict("records")}, indent=1, ensure_ascii=False))
    return skill, days, other


def turbidity_skill(cfg: dict) -> pd.DataFrame:
    """The skill table saved with the model (no training)."""
    saved = json.loads(path(cfg, "models", "modelo_turbidez.json", mkdir=False).read_text())
    return pd.DataFrame(saved["skill"]).set_index("modelo")


def turbidity_outlook(cfg: dict, fc: dict) -> pd.DataFrame:
    """Turbidity per reach: the measured state of the last 20 days and the forecast for the mornings
    of the coming days.

    estado, medicoes_em_20_dias   class of the median of the recent images, and how many images
    medicao_usada                 date of the latest measurement (either satellite) the forecast starts from
    dias_elevada                  days of the horizon on which elevated turbidity is likely (>= 50 %)
    prob_max, dia_prob_max        highest daily probability over the horizon and its day
    previsao                      provável / possível / pouco provável, from prob_max
    The daily probabilities are in `.attrs["daily"]` (rows = days, columns = reaches).
    The upstream reach has no forecast (its measurements are not reliable enough to model).
    """
    import joblib

    from .water_quality import load_scene_series

    saved = joblib.load(path(cfg, "models", "modelo_turbidez.joblib", mkdir=False))
    today = pd.Timestamp(fc["date"])
    horizon = pd.date_range(today, periods=cfg["forecast"]["horizon_days"] + 1)
    history = load_history(cfg)
    q = pd.concat([history["q"].dropna().loc[:today - pd.Timedelta(days=1)], fc["discharge"].median(axis=1).dropna()])
    q = q[~q.index.duplicated(keep="last")].sort_index()
    rain = pd.concat([history["rain"].dropna(), fc["rain"]])
    rain = rain[~rain.index.duplicated(keep="last")].sort_index()
    index = pd.date_range(today - pd.Timedelta(days=45), horizon[-1])
    daily = pd.DataFrame({"q": q.reindex(index).interpolate(limit=3), "rain": rain.reindex(index).fillna(0.0)})
    x = _daily_drivers(daily).reindex(horizon)
    tide = tide_features(cfg, horizon + pd.Timedelta(OVERPASS_UTC + ":00"))
    for col in tide:
        x[col] = tide[col].to_numpy()
    probability, used = pd.DataFrame(index=horizon), {}
    if not x[DRIVER_FEATURES + TIDE_FEATURES].isna().any(axis=None):
        source = measurement_source(cfg, bias=saved["landsat_bias"])
        source = source[source["date"] <= today]                    # a re-run of a past day must not see later images
        for reach in saved["reaches"]:
            rows = x.assign(date=horizon, troco=reach).reset_index(drop=True)
            rows = add_last_measurement(rows, source, 1, saved["medians"])
            for other in saved["reaches"]:
                rows[f"troco={other}"] = float(other == reach)
            probability[reach] = saved["classifier"].predict_proba(rows[saved["features"]])[:, 1]
            if rows["has_last"].iloc[0]:
                used[reach] = str((today - pd.Timedelta(days=float(rows["last_age"].iloc[0]))).date())

    measured = load_scene_series(cfg, "sentinel2")
    rows = []
    for reach in sorted(measured["troco"].unique()):
        series = measured[measured["troco"] == reach].sort_values("date")
        limit = saved["limits"].get(reach, series["ndti"].quantile(ELEVATED_QUANTILE))
        very_high = series["ndti"].quantile(0.90)
        # state = median of the last 20 days, counting only images that saw at least half of the reach
        recent = series[(series["date"] > today - pd.Timedelta(days=20)) & (series["date"] <= today)
                        & (series["pixeis"] >= 0.5 * series["pixeis"].quantile(0.95))]
        if len(recent):
            value = float(recent["ndti"].median())
            state = "muito elevada" if value >= very_high else "elevada" if value >= limit else "normal"
            last_day = str(recent["date"].max().date())
        else:
            state, last_day = "sem medição recente", ""
        row = {"troco": reach, "estado": state, "medicoes_em_20_dias": int(len(recent)), "ultima_medicao": last_day,
               "fiabilidade": "reduzida" if reach == UNRELIABLE_REACH else "boa", "medicao_usada": used.get(reach, "")}
        if reach in probability:
            p = probability[reach]
            row.update({"dias_elevada": int((p >= 0.5).sum()), "prob_max": float(p.max()), "dia_prob_max": str(p.idxmax().date()),
                        "previsao": "provável" if p.max() >= 0.5 else "possível" if p.max() >= 0.25 else "pouco provável"})
        else:
            row.update({"dias_elevada": -1, "prob_max": float("nan"), "dia_prob_max": "", "previsao": "sem previsão"})
        rows.append(row)
    out = pd.DataFrame(rows).set_index("troco")
    out.attrs["daily"] = probability
    return out


def turbidity_ml_benchmark(cfg: dict) -> pd.DataFrame:
    """Can machine learning predict the daily turbidity index? A fair test, kept for the record.

    A gradient-boosting model with discharge, rain and time-of-year features is compared, leaving
    one year out at a time, with two simple references (the usual value for the month; a straight
    line on the discharge of the day), and then tested on Landsat days before the Sentinel-2 record.
    r2 = share of the variation of NDTI explained; mae = typical error in NDTI units.
    """
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.linear_model import LinearRegression
    from sklearn.metrics import mean_absolute_error, r2_score

    history = load_history(cfg).dropna(subset=["q"])
    lq = np.log1p(history["q"])
    drivers_ = pd.DataFrame({"lq": lq, "lq_mean7": lq.rolling(7, min_periods=5).mean(), "lq_max7": lq.rolling(7, min_periods=5).max(),
                             "dq3": lq - lq.shift(3), "p3": history["rain"].rolling(3).sum(), "p7": history["rain"].rolling(7).sum(),
                             "p30": history["rain"].rolling(30).sum(),
                             "sin": np.sin(2 * np.pi * history.index.dayofyear / 365.25), "cos": np.cos(2 * np.pi * history.index.dayofyear / 365.25)})

    def table(sensor):
        days = turbidity_days(cfg, sensor)
        days = days[days["troco"] != UNRELIABLE_REACH].join(drivers_, on="date").dropna(subset=list(drivers_.columns)).reset_index(drop=True)
        for reach in sorted(days["troco"].unique()):
            days[f"troco={reach}"] = (days["troco"] == reach).astype(float)
        return days

    days = table("sentinel2")
    reach_cols = [c for c in days if c.startswith("troco=")]
    features = list(drivers_.columns) + reach_cols
    make = lambda: GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=cfg["processing"]["seed"])
    for col in ("modelo", "epoca", "reta"):
        days[col] = np.nan
    for year in sorted(days["ano"].unique()):
        inside = days["ano"] == year
        train, test = days[~inside], days[inside]
        days.loc[inside, "modelo"] = make().fit(train[features], train["ndti"]).predict(test[features])
        season = train.groupby(["troco", "mes"])["ndti"].mean()
        days.loc[inside, "epoca"] = [season.get(k, train["ndti"].mean()) for k in zip(test["troco"], test["mes"])]
        days.loc[inside, "reta"] = LinearRegression().fit(train[["lq"] + reach_cols], train["ndti"]).predict(test[["lq"] + reach_cols])
    rows = [{"previsao": name, "dias": int(len(days)), "r2": r2_score(days["ndti"], days[col]), "mae": mean_absolute_error(days["ndti"], days[col])}
            for name, col in (("modelo de IA (gradient boosting)", "modelo"), ("referência: época do ano", "epoca"), ("referência: reta sobre o caudal", "reta"))]
    other = table("landsat89")
    other = other[other["date"] < days["date"].min()]
    if len(other) >= 50:
        pred = make().fit(days[features], days["ndti"]).predict(other[features])
        rows.append({"previsao": "modelo de IA, dias do Landsat antes de 2017", "dias": int(len(other)), "r2": r2_score(other["ndti"], pred),
                     "mae": mean_absolute_error(other["ndti"], pred)})
    return pd.DataFrame(rows).set_index("previsao")
