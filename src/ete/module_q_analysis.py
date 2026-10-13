"""Module Q analysis: parameters, monthly dataset, normal values, anomalies, trends and the
turbidity expected from rain and river flow.

Inputs are the per-image tables written by `module_q.update_series` (one row per satellite
image and river section). Everything here runs offline.

What the numbers are, and are not
  ndti          colour index (red - green) / (red + green). Repeatable between satellites; the
                basis of every relative result (normal values, anomalies, trends).
  turbidez_fnu  Dogliotti et al. (2015), red band only. An ESTIMATE: it is computed from land
                surface reflectance, not from water-specific reflectance, and has no local
                calibration. The two satellites differ by a typical factor of about 1.5.
  tss_mg_l      Nechad et al. (2010), red band. Same input as the turbidity, same caveats.
  secchi_m      transparency estimated from the red reflectance with a relation fitted to the
                GLORIA global measurements. Wide uncertainty; no local Secchi readings yet.
  ndci          Sentinel-2 only. In this river it follows the sediment, so it is NOT reported
                as chlorophyll.
  vegetacao     share of the permanent water covered by green plants in the image.
  temp_c        Landsat surface temperature (100 m thermal pixel): only meaningful where the
                river is wide.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from .config import path

MIN_PIXELS = {"sentinel2": 50, "landsat89": 20, "landsat57": 20}       # pure-water pixels needed (0.5 ha and 1.8 ha)
MIN_CLEAR_PIXELS = {"sentinel2": 500, "landsat89": 60, "landsat57": 60}  # clear pixels needed for the vegetation share
LANDSAT_MIN_WIDTH_M = 90              # three Landsat pixels; the estuary section (no width) counts as wide
WIDE_RIVER_M = 300                    # below this mean width the Landsat temperature mixes river and banks
DOGLIOTTI_RED = (228.1, 0.1641)       # A (FNU), C at 645 nm; Dogliotti et al. 2015 (values as distributed with ACOLITE)
NECHAD_RED = {"sentinel2": (355.85, 1.74, 0.1728), "landsat89": (289.29, 2.10, 0.1686), "landsat57": (327.84, 1.91, 0.1708)}  # A, B, C at 665, 655, 660 nm
RED_MAX = 0.13                        # the red band saturates in very turbid water; above this the estimate is capped
ELEVATED, VERY_ELEVATED = 0.75, 0.90  # percentiles of the section's own record for that month of the year
ERAS = {"Landsat 5/7 (2006-2013)": ("2006-01", "2013-03"), "Landsat 8/9 (2013-2026)": ("2013-04", "2100-01")}


# ----------------------------------------------------------------------------- parameters per image
def turbidity_fnu(red):
    rho = np.clip(np.asarray(red, "float64"), 0, RED_MAX)
    return DOGLIOTTI_RED[0] * rho / (1 - rho / DOGLIOTTI_RED[1])


def tss_mg_l(red, sensor: str):
    a, b, c = NECHAD_RED[sensor]
    rho = np.clip(np.asarray(red, "float64"), 0, RED_MAX)
    return a * rho / (1 - rho / c) + b


def secchi_model(cfg: dict) -> dict | None:
    file = path(cfg, "models", "secchi_gloria.json", mkdir=False)
    return json.loads(file.read_text()) if file.exists() else None


def secchi_m(red, model: dict | None):
    if model is None:
        return np.full(np.shape(red), np.nan)
    rho = np.clip(np.asarray(red, "float64"), 1e-4, None)
    return 10 ** (model["intercept"] + model["slope"] * np.log10(rho))


def load_images(cfg: dict) -> pd.DataFrame:
    """One row per day, section and sensor group, with the parameters. Images of the same day
    are merged (weighted by their pure-water pixels). Rows with too few pixels keep the
    vegetation share but lose the water-colour values."""
    files = sorted(path(cfg, "module_q_raw", mkdir=False).glob("*.csv"))
    if not files:
        raise FileNotFoundError("run scripts/update_module_q_series.py first (needs Earth Engine)")
    raw = pd.concat([pd.read_csv(f) for f in files if f.stat().st_size > 60], ignore_index=True)
    raw["date"] = pd.to_datetime(raw["date"])
    raw["pixeis"] = raw["pixeis"].fillna(0)
    parts = []
    for sensor, table in raw.groupby("sensor"):
        values = [c for c in ("green", "red", "nir", "ndti", "ndci", "temp_c") if c in table and table[c].notna().any()]
        weighted = table[values].multiply(table["pixeis"], axis=0)
        weighted[["date", "troco"]] = table[["date", "troco"]]
        weighted["pixeis"] = table["pixeis"]
        weighted["veg_w"], weighted["pixeis_limpos"] = table["vegetacao"] * table["pixeis_limpos"], table["pixeis_limpos"]
        summed = weighted.groupby(["date", "troco"]).sum(min_count=1)
        day = summed[values].div(summed["pixeis"].where(summed["pixeis"] > 0), axis=0)
        day["pixeis"], day["pixeis_limpos"] = summed["pixeis"], summed["pixeis_limpos"]
        day["vegetacao"] = (summed["veg_w"] / summed["pixeis_limpos"]).where(summed["pixeis_limpos"] >= MIN_CLEAR_PIXELS[sensor])
        day.loc[day["pixeis"] < MIN_PIXELS[sensor], values] = np.nan
        day["sensor"] = sensor
        parts.append(day.reset_index())
    images = pd.concat(parts, ignore_index=True)
    model = secchi_model(cfg)
    images["turbidez_fnu"] = turbidity_fnu(images["red"])
    images["tss_mg_l"] = np.nan
    for sensor in images["sensor"].unique():
        rows = images["sensor"] == sensor
        images.loc[rows, "tss_mg_l"] = tss_mg_l(images.loc[rows, "red"], sensor)
    images["secchi_m"] = secchi_m(images["red"], model)
    images.loc[images["red"].isna(), ["turbidez_fnu", "tss_mg_l", "secchi_m"]] = np.nan
    return images.sort_values(["troco", "date", "sensor"]).reset_index(drop=True)


def cross_sensor(images: pd.DataFrame) -> pd.DataFrame:
    """Sentinel-2 against Landsat 8/9 on the same day and section: is each value repeatable?
    r = correlation (log scale for turbidity); fator_tipico = typical ratio between the two."""
    a = images[images["sensor"] == "sentinel2"].dropna(subset=["ndti"])
    b = images[images["sensor"] == "landsat89"].dropna(subset=["ndti"])
    pairs = a.merge(b, on=["date", "troco"], suffixes=("", "_landsat"))
    rows = []
    for name, group in [("todos os troços", pairs)] + list(pairs.groupby("troco")):
        if len(group) < 8:
            rows.append({"troco": name, "pares": len(group)})
            continue
        la, lb = np.log10(group["turbidez_fnu"].clip(lower=0.5)), np.log10(group["turbidez_fnu_landsat"].clip(lower=0.5))
        rows.append({"troco": name, "pares": len(group), "r_ndti": np.corrcoef(group["ndti"], group["ndti_landsat"])[0, 1],
                     "dif_ndti": float((group["ndti_landsat"] - group["ndti"]).mean()), "r_turbidez": np.corrcoef(la, lb)[0, 1],
                     "fator_tipico_turbidez": float(10 ** np.sqrt(((lb - la) ** 2).mean())), "razao_mediana_turbidez": float(np.median(group["turbidez_fnu_landsat"] / group["turbidez_fnu"]))})
    return pd.DataFrame(rows).set_index("troco")


MIN_AGREEMENT = 0.7                   # same-day correlation between the two satellites below which a section is flagged


def section_reliability(images: pd.DataFrame) -> pd.Series:
    """`boa` or `reduzida` per section: is the colour index of the section repeatable between
    Sentinel-2 and Landsat 8/9 on the same day? Sections with fewer than 15 pairs, or a
    correlation below MIN_AGREEMENT, are `reduzida`: their values are shown but raise no alert."""
    table = cross_sensor(images).drop(index="todos os troços", errors="ignore")
    good = (table["pares"] >= 15) & (table.get("r_ndti", pd.Series(dtype=float)).reindex(table.index) >= MIN_AGREEMENT)
    return good.map({True: "boa", False: "reduzida"})


# ----------------------------------------------------------------------------- monthly dataset
def monthly_dataset(cfg: dict) -> pd.DataFrame:
    """qualidade_trocos.parquet: one row per river section and month, 2006 to today.

    For each parameter the Landsat value is used where the river is wide enough for Landsat
    (20-year continuity) and the Sentinel-2 value elsewhere (2017 onwards); `fonte` says which.
    The values of each satellite are also kept apart (suffixes _landsat and _s2). Months
    without a clear image stay empty: nothing is filled in. Rain and river flow of the month
    (basin rain from CHIRPS, with IMERG where CHIRPS is not yet published; GloFAS flow at
    Marracuene) are added, with their values one and two months before.
    """
    images = load_images(cfg)
    images["month"] = images["date"].dt.to_period("M").astype(str)
    images["grupo"] = np.where(images["sensor"] == "sentinel2", "s2", "landsat")
    values = ["ndti", "turbidez_fnu", "tss_mg_l", "secchi_m", "vegetacao", "ndci", "temp_c"]
    grouped = images.groupby(["troco", "month", "grupo"])
    wide = grouped[values].median().unstack("grupo")
    wide.columns = [f"{v}_{g}" for v, g in wide.columns]
    counts = grouped["ndti"].count().unstack("grupo").rename(columns=lambda g: f"n_imagens_{g}")
    table = wide.join(counts).reset_index()
    for col in [f"{v}_{g}" for v in values for g in ("landsat", "s2")] + ["n_imagens_landsat", "n_imagens_s2"]:
        if col not in table:
            table[col] = np.nan
    table = table.drop(columns=[c for c in ("ndci_landsat", "temp_c_s2") if c in table])

    width = pd.read_csv(path(cfg, "sections", "largura_por_troco.csv", mkdir=False)).set_index("troco")
    # Landsat (30 m pixels) is used only where the river is at least three pixels wide on average;
    # in the narrower sections only Sentinel-2 is used, from 2017 (rule of the plan)
    usable = width["largura_media_m"].fillna(1000) >= LANDSAT_MIN_WIDTH_M
    months = pd.period_range("2006-01", pd.Timestamp.today().to_period("M"), freq="M").astype(str)
    full = pd.MultiIndex.from_product([width.index, months], names=["troco", "month"]).to_frame(index=False)
    table = full.merge(table, how="left", on=["troco", "month"])
    table["landsat_utilizavel"] = table["troco"].map(usable).fillna(False)
    for v in ("ndti", "turbidez_fnu", "tss_mg_l", "secchi_m", "vegetacao"):
        table[v] = np.where(table["landsat_utilizavel"], table[f"{v}_landsat"], table[f"{v}_s2"])
    table["fonte"] = np.where(table["landsat_utilizavel"], "Landsat", "Sentinel-2")
    table["fonte"] = table["fonte"].where(table["ndti"].notna(), "")
    table["ndci"], table["temp_c"] = table["ndci_s2"], table["temp_c_landsat"]
    table.loc[table["troco"].map(width["largura_media_m"]).fillna(1000) < WIDE_RIVER_M, "temp_c"] = np.nan
    table[["n_imagens_landsat", "n_imagens_s2"]] = table[["n_imagens_landsat", "n_imagens_s2"]].fillna(0).astype(int)

    series = path(cfg, "series", mkdir=False)
    rain = pd.read_csv(series / "rain_monthly.csv").set_index("month")
    drivers = pd.DataFrame({"chuva_mm": rain["rain_basin_mm"].fillna(rain["imerg_basin_mm"]),
                            "caudal_m3s": pd.read_csv(series / "hydromet_monthly.csv").set_index("month")["q_mean"]})
    for lag in (1, 2):
        drivers[f"chuva_mm_m{lag}"], drivers[f"caudal_m3s_m{lag}"] = drivers["chuva_mm"].shift(lag), drivers["caudal_m3s"].shift(lag)
    table = table.join(drivers, on="month")
    table["ano"], table["mes"] = table["month"].str[:4].astype(int), table["month"].str[5:].astype(int)
    table["epoca"] = np.where(table["mes"].isin([11, 12, 1, 2, 3, 4]), "chuvosa", "seca")
    table["nome"] = table["troco"].map(width["nome"])
    table["fiabilidade"] = table["troco"].map(section_reliability(images)).fillna("reduzida")
    table.to_parquet(path(cfg, "training", "qualidade_trocos.parquet"), index=False)
    return table


def load_dataset(cfg: dict) -> pd.DataFrame:
    file = path(cfg, "training", "qualidade_trocos.parquet", mkdir=False)
    return pd.read_parquet(file) if file.exists() else monthly_dataset(cfg)


# ----------------------------------------------------------------------------- normal values and anomalies
def climatology(data: pd.DataFrame, value: str = "ndti", min_years: int = 4) -> pd.DataFrame:
    """Normal value of each section in each month of the year: median and percentiles over
    the years with data. Months of the year with fewer than `min_years` years are left out."""
    grouped = data.dropna(subset=[value]).groupby(["troco", "mes"])[value]
    table = grouped.agg(anos="count", mediana="median", p10=lambda s: s.quantile(0.10), p25=lambda s: s.quantile(0.25),
                        p75=lambda s: s.quantile(ELEVATED), p90=lambda s: s.quantile(VERY_ELEVATED))
    return table[table["anos"] >= min_years]


def anomalies(data: pd.DataFrame, value: str = "ndti") -> pd.DataFrame:
    """Each month against the normal for that section and month of the year.
    anomalia = value - median; classe = normal / elevada (above the 75th percentile of that
    month of the year) / muito elevada (above the 90th)."""
    normal = climatology(data, value)
    out = data[["troco", "nome", "month", "ano", "mes", value]].join(normal, on=["troco", "mes"])
    out["anomalia"] = out[value] - out["mediana"]
    spread = (out["p75"] - out["p25"]).replace(0, np.nan)
    out["anomalia_padronizada"] = out["anomalia"] / spread
    out["classe"] = np.select([out[value].isna() | out["mediana"].isna(), out[value] > out["p90"], out[value] > out["p75"]],
                              ["sem dados", "muito elevada", "elevada"], "normal")
    return out


def isolation_forest(cfg: dict, data: pd.DataFrame, share: float = 0.05) -> pd.DataFrame:
    """Unusual months per section, found with an Isolation Forest on what is measured together
    (colour, vegetation on the water, and how far the colour is from what rain and flow explain).
    `share` is the part of the months flagged. Columns: pontuacao (lower = more unusual),
    invulgar (bool) and the values that went in. A flag says "look at this month", not "pollution"."""
    from sklearn.ensemble import IsolationForest

    frames = []
    for value in ("ndti", "vegetacao"):
        frames.append(anomalies(data, value).set_index(["troco", "month"])["anomalia_padronizada"].rename(f"anomalia_{value}"))
    table = pd.concat(frames, axis=1)
    if "residuo" in data:
        table = table.join(data.set_index(["troco", "month"])["residuo"])
    table = table.dropna(subset=["anomalia_ndti"]).reset_index()
    features = [c for c in table.columns if c not in ("troco", "month")]
    rows = []
    for section, group in table.groupby("troco"):
        if len(group) < 40:
            continue
        x = group[features].fillna(0.0)
        forest = IsolationForest(n_estimators=300, contamination=share, random_state=cfg["processing"]["seed"]).fit(x)
        rows.append(group.assign(pontuacao=forest.score_samples(x), invulgar=forest.predict(x) == -1))
    return pd.concat(rows, ignore_index=True) if rows else pd.DataFrame()


# ----------------------------------------------------------------------------- trends
def seasonal_mann_kendall(series: pd.Series) -> dict:
    """Seasonal Mann-Kendall test (Hirsch et al., 1982) and Sen's slope for a monthly series
    indexed by "YYYY-MM". Each month of the year is compared only with itself, so the yearly
    cycle does not create a false trend. Returns the slope per decade, the p-value and the
    direction (sobe / desce / sem tendência at 5 %). Serial correlation is not corrected."""
    from scipy.stats import norm

    s = series.dropna()
    years, months = s.index.str[:4].astype(int).to_numpy(), s.index.str[5:].astype(int).to_numpy()
    total, variance, slopes = 0.0, 0.0, []
    for month in range(1, 13):
        x, t = s.to_numpy()[months == month], years[months == month]
        n = len(x)
        if n < 3:
            continue
        i, j = np.triu_indices(n, 1)
        total += np.sign(x[j] - x[i]).sum()
        ties = pd.Series(x).value_counts().to_numpy()
        variance += (n * (n - 1) * (2 * n + 5) - (ties * (ties - 1) * (2 * ties + 5)).sum()) / 18
        slopes.append((x[j] - x[i]) / (t[j] - t[i]))
    if variance <= 0 or not slopes:
        return {"n": int(len(s)), "inclinacao_por_decada": np.nan, "p": np.nan, "tendencia": "dados insuficientes"}
    z = (total - np.sign(total)) / np.sqrt(variance)
    p = float(2 * (1 - norm.cdf(abs(z))))
    slope = float(np.median(np.concatenate(slopes))) * 10
    return {"n": int(len(s)), "inclinacao_por_decada": slope, "p": p, "tendencia": "sem tendência" if p >= 0.05 else "sobe" if slope > 0 else "desce"}


def trends(data: pd.DataFrame, values=("ndti", "vegetacao", "temp_c")) -> pd.DataFrame:
    """Trend of each parameter in each section, for the whole record and for each satellite era
    apart. A trend that appears only in the whole record, and in neither era, may come from
    the change of satellite in 2013 and must not be reported as a change in the river."""
    rows = []
    for (section, name), group in data.groupby(["troco", "nome"]):
        group = group.set_index("month")
        for value in values:
            periods = {"registo completo": ("2006-01", "2100-01"), **(ERAS if group["fonte"].eq("Landsat").any() or value == "temp_c" else {})}
            for label, (first, last) in periods.items():
                part = group.loc[(group.index >= first) & (group.index < last), value]
                if part.notna().sum() >= 24:
                    rows.append({"troco": section, "nome": name, "parametro": value, "periodo": label, **seasonal_mann_kendall(part),
                                 "primeiro_mes": part.dropna().index.min(), "ultimo_mes": part.dropna().index.max()})
    table = pd.DataFrame(rows)
    if table.empty:
        return table
    # a trend of the whole record counts as confirmed only if the Landsat 8/9 era alone shows it too
    # (same direction, significant); sections measured by one satellite family need no such check
    recent = table[table["periodo"].str.startswith("Landsat 8/9")].set_index(["troco", "parametro"])["tendencia"]
    def verdict(row):
        if row["periodo"] != "registo completo" or row["tendencia"] in ("sem tendência", "dados insuficientes"):
            return ""
        key = (row["troco"], row["parametro"])
        if key not in recent.index:
            return "um só satélite: válida para o período medido"
        return "confirmada" if recent[key] == row["tendencia"] else "não confirmada: pode vir da mudança de satélite"
    table["leitura"] = table.apply(verdict, axis=1)
    return table


# ----------------------------------------------------------------------------- turbidity expected from rain and flow
EXPECTED_FEATURES = ["lq", "lq_mean7", "lq_max7", "dq3", "p3", "p7", "p30", "sin", "cos", "t_h", "t_dh", "t_range", "s2"]
MIN_SKILL = 0.3                       # below this R2 the model explains too little for "not explained" to mean anything
IMAGE_HOUR_UTC = "07:35"              # both satellites pass between about 07:25 and 07:45 UTC


def expected_turbidity(cfg: dict, data: pd.DataFrame | None = None) -> tuple[pd.DataFrame, pd.DataFrame, pd.DataFrame]:
    """Model of the colour index expected from rain and river flow, per section.

    It works image by image, not month by month: a monthly mean of one or two images cannot be
    explained by the rain of the month (tested: R2 below zero in every section). Each image gets
    the river flow of the day and of the days before (GloFAS at Marracuene), the basin rain of
    the last 3, 7 and 30 days, the time of year and the computed tide at the hour of the
    satellite (it matters only near the mouth). One gradient-boosting model per section; each
    year is predicted by a model that never saw it.

    `residuo` = measured - expected. In the monthly table it is the median over the images of
    the month, and a month is `nao_explicada` when that residual is above the 90th percentile
    of the section. Only in sections where the model explains at least MIN_SKILL of the
    variation; elsewhere the flag is left empty. "Not explained" can be a discharge, works in
    the river, a dam release upstream, or a measurement error: a reason to look, not a finding.

    Returns (monthly data with esperado, residuo, nao_explicada; skill per section; the images
    with their expected value).
    """
    from sklearn.ensemble import GradientBoostingRegressor
    from sklearn.metrics import r2_score

    from .forecast import load_history
    from .forecast_models import _daily_drivers, tide_features

    data = (load_dataset(cfg) if data is None else data).copy()
    source = data.drop_duplicates("troco").set_index("troco")
    images = load_images(cfg).dropna(subset=["ndti"])
    # wide sections: every image of every satellite; narrow sections: Sentinel-2 only
    wanted = images["troco"].map(source["landsat_utilizavel"]).fillna(False).astype(bool) | (images["sensor"] == "sentinel2")
    images = images[wanted].join(_daily_drivers(load_history(cfg).dropna(subset=["q"])), on="date")
    tide = tide_features(cfg, images["date"] + pd.Timedelta(IMAGE_HOUR_UTC + ":00"))
    for col in tide:
        images[col] = tide[col].to_numpy()
    images["s2"] = (images["sensor"] == "sentinel2").astype(float)
    images["ano"], images["mes"] = images["date"].dt.year, images["date"].dt.month
    images = images.dropna(subset=EXPECTED_FEATURES).reset_index(drop=True)
    images["esperado"], images["esperado_epoca"] = np.nan, np.nan
    rows = []
    for section, group in images.groupby("troco"):
        if len(group) < 60 or group["ano"].nunique() < 5:
            continue
        for year in sorted(group["ano"].unique()):
            train, test = group[group["ano"] != year], group[group["ano"] == year]
            model = GradientBoostingRegressor(n_estimators=200, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=cfg["processing"]["seed"])
            images.loc[test.index, "esperado"] = model.fit(train[EXPECTED_FEATURES], train["ndti"]).predict(test[EXPECTED_FEATURES])
            season = train.groupby("mes")["ndti"].median()
            images.loc[test.index, "esperado_epoca"] = test["mes"].map(season).fillna(train["ndti"].median()).to_numpy()
        done = images.loc[group.index]
        rows.append({"troco": section, "nome": source.loc[section, "nome"], "imagens": len(group), "anos": int(group["ano"].nunique()),
                     "r2_chuva_caudal_mare": r2_score(done["ndti"], done["esperado"]), "r2_epoca_do_ano": r2_score(done["ndti"], done["esperado_epoca"]),
                     "corr_com_caudal": float(np.corrcoef(done["ndti"], done["lq"])[0, 1])})
    skill = pd.DataFrame(rows).set_index("troco") if rows else pd.DataFrame(columns=["r2_chuva_caudal_mare"])
    skill["modelo_fiavel"] = skill["r2_chuva_caudal_mare"] >= MIN_SKILL
    images["residuo"] = images["ndti"] - images["esperado"]
    images["month"] = images["date"].dt.to_period("M").astype(str)
    monthly = images.groupby(["troco", "month"])[["esperado", "residuo"]].median()
    data = data.drop(columns=[c for c in ("esperado", "residuo", "nao_explicada") if c in data]).join(monthly, on=["troco", "month"])
    reliable = data["troco"].map(skill["modelo_fiavel"]).fillna(False).astype(bool)
    data.loc[~reliable, "residuo"] = np.nan
    limit = data.groupby("troco")["residuo"].transform(lambda r: r.quantile(0.90))
    data["nao_explicada"] = (data["residuo"] > limit).where(data["residuo"].notna())
    return data, skill, images


def upstream_downstream(data: pd.DataFrame, upstream: str = "Q1", downstream: str = "Q8", value: str = "ndti_s2") -> dict:
    """The cross-border question: does the water arrive at the border already turbid?
    Compares the monthly values at the border section and at the downstream section in the
    months both were measured (Sentinel-2, 2017 onwards)."""
    wide = data.pivot(index="month", columns="troco", values=value)
    if upstream not in wide or downstream not in wide:
        return {"meses": 0}
    both = wide[[upstream, downstream]].dropna()
    if len(both) < 12:
        return {"meses": int(len(both))}
    difference = both[downstream] - both[upstream]
    return {"meses": int(len(both)), "correlacao": float(np.corrcoef(both[upstream], both[downstream])[0, 1]),
            "mediana_montante": float(both[upstream].median()), "mediana_jusante": float(both[downstream].median()),
            "meses_mais_turva_a_jusante": float((difference > 0).mean()), "diferenca_mediana": float(difference.median()),
            "tabela": both.assign(diferenca=difference)}


# ----------------------------------------------------------------------------- state per section (platform)
def section_state(cfg: dict, data: pd.DataFrame | None = None, months_back: int = 3) -> pd.DataFrame:
    """Latest measured month of each section (within the last `months_back` months) against its
    normal: classe, and whether the colour is above what rain and flow explain. The quality
    alert of the plan: outside the monthly normal AND not explained by rain and flow."""
    if data is None or "residuo" not in data:
        data = expected_turbidity(cfg, data)[0]
    classes = anomalies(data, "ndti").set_index(["troco", "month"])
    recent = sorted(data["month"].unique())[-months_back:]
    rows = []
    for (section, name), group in data.groupby(["troco", "nome"]):
        measured = group[group["month"].isin(recent) & group["ndti"].notna()]
        if measured.empty:
            rows.append({"troco": section, "nome": name, "mes": "", "fiabilidade": group["fiabilidade"].iloc[0], "classe": "sem medição recente", "alerta_de_qualidade": False})
            continue
        last = measured.iloc[-1]
        info = classes.loc[(section, last["month"])]
        unexplained = bool(last["nao_explicada"]) if pd.notna(last["residuo"]) and pd.notna(last["nao_explicada"]) else False
        rows.append({"troco": section, "nome": name, "mes": last["month"], "fonte": last["fonte"], "fiabilidade": last["fiabilidade"], "ndti": float(last["ndti"]), "normal_do_mes": float(info["mediana"]) if pd.notna(info["mediana"]) else np.nan,
                     "classe": info["classe"], "turbidez_fnu_estimada": float(last["turbidez_fnu"]) if pd.notna(last["turbidez_fnu"]) else np.nan,
                     "vegetacao": float(last["vegetacao"]) if pd.notna(last["vegetacao"]) else np.nan, "acima_do_explicado": unexplained,
                     "alerta_de_qualidade": bool(info["classe"] in ("elevada", "muito elevada") and unexplained and last["fiabilidade"] == "boa")})
    return pd.DataFrame(rows).set_index("troco")


# ----------------------------------------------------------------------------- validation with GLORIA
def gloria_validation(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Test the published algorithms on GLORIA: real reflectance measured at the water surface
    together with turbidity, suspended solids, chlorophyll-a and Secchi depth, in hundreds of
    lakes, rivers and coasts (Lehmann et al., 2023). It checks the FORMULAS, with ideal
    reflectance. It does not check our satellite reflectance over the Incomati.

    Also fits the relation Secchi depth ~ red reflectance used for `secchi_m` and saves it in
    models/secchi_gloria.json. Returns (metrics table, the samples used).
    r2_log = R2 of log10 values; fator_tipico = typical ratio between estimate and measurement.
    """
    folder = path(cfg, "water_quality", "validacao", "gloria", "GLORIA_2022", mkdir=False)
    wanted = {"GLORIA_ID", "Rrs_mean_560", "Rrs_mean_645", "Rrs_mean_655", "Rrs_mean_665", "Rrs_mean_705"}
    rrs = pd.read_csv(folder / "GLORIA_Rrs_mean.csv", usecols=lambda c: c in wanted)
    lab = pd.read_csv(folder / "GLORIA_meta_and_lab.csv", low_memory=False, usecols=["GLORIA_ID", "Water_body_type", "Chla", "TSS", "Turbidity", "Secchi_depth"])
    samples = rrs.dropna(subset=["Rrs_mean_665"]).merge(lab, on="GLORIA_ID")
    for wave in (560, 645, 655, 665, 705):
        samples[f"rho_{wave}"] = np.pi * samples[f"Rrs_mean_{wave}"]            # water-leaving reflectance
    samples = samples[(samples["rho_665"] > 0) & (samples["rho_560"] > 0)]
    samples["fnu_dogliotti"] = DOGLIOTTI_RED[0] * samples["rho_645"].clip(0, RED_MAX) / (1 - samples["rho_645"].clip(0, RED_MAX) / DOGLIOTTI_RED[1])
    a, b, c = NECHAD_RED["sentinel2"]
    samples["tss_nechad"] = a * samples["rho_665"].clip(0, RED_MAX) / (1 - samples["rho_665"].clip(0, RED_MAX) / c) + b
    samples["ndci"] = (samples["rho_705"] - samples["rho_665"]) / (samples["rho_705"] + samples["rho_665"])
    samples["ndti"] = (samples["rho_665"] - samples["rho_560"]) / (samples["rho_665"] + samples["rho_560"])

    def log_metrics(name, measured, estimate, note):
        ok = (measured > 0) & (estimate > 0) & np.isfinite(measured) & np.isfinite(estimate)
        m, e = np.log10(measured[ok]), np.log10(estimate[ok])
        return {"teste": name, "amostras": int(ok.sum()), "r2_log": float(1 - ((m - e) ** 2).sum() / ((m - m.mean()) ** 2).sum()), "correlacao_log": float(np.corrcoef(m, e)[0, 1]),
                "fator_tipico": float(10 ** np.sqrt(((e - m) ** 2).mean())), "razao_mediana": float(10 ** np.median(e - m)), "nota": note}

    rows = [log_metrics("turbidez: Dogliotti 2015, banda vermelha", samples["Turbidity"], samples["fnu_dogliotti"], "fórmula usada em `turbidez_fnu`"),
            log_metrics("sólidos suspensos: Nechad 2010, 665 nm", samples["TSS"], samples["tss_nechad"], "fórmula usada em `tss_mg_l`")]
    turbid = samples["TSS"] >= 20
    for label, part in (("clorofila-a vs NDCI: águas pouco turvas (TSS < 20 mg/L)", samples[~turbid & samples["TSS"].notna()]),
                        ("clorofila-a vs NDCI: águas turvas (TSS >= 20 mg/L)", samples[turbid])):
        ok = part["Chla"].gt(0) & part["ndci"].notna()
        rows.append({"teste": label, "amostras": int(ok.sum()), "correlacao_log": float(np.corrcoef(np.log10(part.loc[ok, "Chla"]), part.loc[ok, "ndci"])[0, 1]) if ok.sum() > 10 else np.nan,
                     "nota": "no GLORIA as águas turvas são sobretudo lagos com algas; no Incomáti o NDCI segue o sedimento (notebook 34)"})
    ok = samples["TSS"].gt(0) & samples["ndti"].notna()
    rows.append({"teste": "sólidos suspensos vs NDTI", "amostras": int(ok.sum()), "correlacao_log": float(np.corrcoef(np.log10(samples.loc[ok, "TSS"]), samples.loc[ok, "ndti"])[0, 1]),
                 "nota": "o NDTI ordena as águas pela carga de sedimento?"})
    # Secchi depth from the red reflectance: straight line in log-log, tested with 5 folds
    part = samples[samples["Secchi_depth"].gt(0)].sample(frac=1.0, random_state=cfg["processing"]["seed"])
    x, y = np.log10(part["rho_665"].to_numpy()), np.log10(part["Secchi_depth"].to_numpy())
    predicted = np.zeros(len(part))
    for fold in range(5):
        test = np.arange(len(part)) % 5 == fold
        slope, intercept = np.polyfit(x[~test], y[~test], 1)
        predicted[test] = intercept + slope * x[test]
    slope, intercept = np.polyfit(x, y, 1)
    rows.append({"teste": "transparência (Secchi) a partir da refletância no vermelho", "amostras": int(len(part)), "r2_log": float(1 - ((y - predicted) ** 2).sum() / ((y - y.mean()) ** 2).sum()),
                 "correlacao_log": float(np.corrcoef(y, predicted)[0, 1]), "fator_tipico": float(10 ** np.sqrt(((predicted - y) ** 2).mean())), "razao_mediana": 1.0,
                 "nota": "relação ajustada aqui e usada em `secchi_m` (validação cruzada, 5 partes)"})
    path(cfg, "models", "secchi_gloria.json").write_text(json.dumps({
        "name": "secchi_gloria", "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "formula": "log10(Secchi depth, m) = intercept + slope * log10(pi * Rrs(665 nm))", "intercept": float(intercept), "slope": float(slope),
        "samples": int(len(part)), "typical_factor": rows[-1]["fator_tipico"], "source": "GLORIA (Lehmann et al., 2023), doi:10.1594/PANGAEA.948492"}, indent=1))
    return pd.DataFrame(rows).set_index("teste"), samples
