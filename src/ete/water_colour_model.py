"""Forecast maps of the water colour of the lower Incomati, up to 30 days ahead.

Two models, each tested on data it never saw:

1. The map model (Earth Engine, `fit_pixel_model`). For every 20 m pixel of the river from Manhiça
   to the mouth, a straight line learned from the Sentinel-2 images of 2017-2025:
       colour of the pixel = a + b x (colour of the river at Marracuene) + c x (tide at the image time)
   The colour is the index NDTI = (red - green) / (red + green) of the pure-water pixels (the rules of
   module_q.pure_water: no clouds, no shadows, no plants or leaves, not the pixel next to the bank).
   "Colour of the river at Marracuene" is the median NDTI of section Q8 in the same image. The model
   learns where the water is usually muddier or clearer than at Marracuene, and how the estuary
   changes with the tide. Tested on the 2026 images (`test_pixel_model`).

2. The Marracuene model (here, `fit_reach_model`). The colour of the river at Marracuene for each
   morning up to 30 days ahead, from: the river flow (GloFAS, observed before and forecast after),
   the computed tide, the time of year, and the latest measurement with its age. Tested year by year
   (each year predicted by a model that never saw it) at 1, 7, 14, 21 and 30 days ahead, against the
   time of year alone and against "the same as the last measurement".

A forecast map is model 2 for the chosen day put into model 1. The page always says how well each
model did in its tests. Nothing here says whether the water is safe to drink.

Internet: the list of image dates and the Marracuene values (a few hundred KB) and the map model
(about 1-2 MB, once). The model is computed on Earth Engine's computers.
"""

from __future__ import annotations

import json
import time
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import module_q
from .config import path
from .turbidity_map import CRS, SECTIONS, STEPS

DRIVER_SECTION = "Q8"                       # Marracuene: the colour that drives the map
MODEL_RES_M = 20
MIN_DRIVER_PIXELS = 200                     # pure-water pixels of 20 m needed in Q8 (8 ha) for the image to count
LAST_TRAIN_DAY = "2025-12-31"               # the map model learns from 2017-2025; 2026 is kept for the test
OVERPASS_LOCAL = "09:30"                    # the mornings of the forecast: the time of the satellite images (about 08:00 UTC)


def folder(cfg: dict) -> Path:
    out = path(cfg, "processed") / "water_colour"
    out.mkdir(parents=True, exist_ok=True)
    return out


def asset_id(name: str) -> str:
    import os

    return f"projects/{os.environ['EE_PROJECT']}/assets/{name}"


# ----------------------------------------------------------------------------- the Sentinel-2 days and their tide
def passes(cfg: dict) -> pd.DataFrame:
    """Days with a Sentinel-2 image over the lower river, the UTC time of the image and the computed
    tide then (from forecast_models.tide_features). Read from passagens_sentinel2.csv."""
    from .forecast_models import tide_features

    table = pd.read_csv(folder(cfg) / "passagens_sentinel2.csv", parse_dates=["utc"])
    tide = tide_features(cfg, table["utc"])
    return table.assign(mare=tide["t_h"].to_numpy(), mare_sobe=tide["t_dh"].to_numpy(), amplitude=tide["t_range"].to_numpy())


def _daily_colour(cfg: dict, dates: list[str], tides: dict, bounds):
    """Earth Engine: one image per day (the tiles of the day put together) with the band ndti (pure
    water only) and the properties data, q8 (median NDTI of Q8), n8 (its pure-water pixels) and mare."""
    import ee

    from .turbidity_map import _sources

    _, _, s2 = _sources(cfg, bounds)
    regions = ee.FeatureCollection(module_q.regions_asset(cfg))
    driver = regions.filter(ee.Filter.eq("troco", DRIVER_SECTION)).geometry()
    tide = ee.Dictionary(tides)

    def per_day(day):
        day = ee.String(day)
        start = ee.Date(day)
        img = s2.filterDate(start, start.advance(1, "day")).mosaic()
        sr = module_q.s2_reflectance(img)
        ok = module_q.s2_clear(img).And(module_q.pure_water(sr))
        ndti = sr.select("red").subtract(sr.select("green")).divide(sr.select("red").add(sr.select("green"))).rename("ndti").updateMask(ok)
        stats = ndti.reduceRegion(ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True), driver, MODEL_RES_M, maxPixels=1e9, tileScale=4)
        return ndti.set({"data": day, "q8": stats.get("ndti_median"), "n8": stats.get("ndti_count"), "mare": tide.get(day)})

    return ee.ImageCollection(ee.List(dates).map(per_day)).filter(ee.Filter.gte("n8", MIN_DRIVER_PIXELS))


def _design(img):
    import ee

    ndti = img.select("ndti")
    return (ee.Image.cat([ee.Image.constant(1), ee.Image.constant(img.get("q8")), ee.Image.constant(img.get("mare")), ndti])
            .rename(["k", "q8", "mare", "ndti"]).toFloat().updateMask(ndti.mask()))


def driver_values(cfg: dict, log=print) -> pd.DataFrame:
    """The colour of Q8 (Marracuene) on every Sentinel-2 day, computed exactly as the map model sees it
    (a table of a few hundred KB). Saved as cor_marracuene_diaria.csv."""
    import ee

    from .gee import init, retry
    from .turbidity_map import frame

    init(cfg)
    _, bounds = frame(cfg)
    days = passes(cfg)
    rows = []
    for year, part in days.groupby(days["data"].str[:4]):
        daily = _daily_colour(cfg, part["data"].tolist(), dict(zip(part["data"], part["mare"])), bounds)
        found = retry(lambda: daily.aggregate_array("data").zip(daily.aggregate_array("q8")).zip(daily.aggregate_array("n8")).getInfo())
        rows += [{"data": d, "ndti_q8": q, "pixeis_q8": n} for (d, q), n in found]
        log(f"   {year}: {len(found)} dias com Marracuene visível")
    table = days.merge(pd.DataFrame(rows), on="data")
    table.to_csv(folder(cfg) / "cor_marracuene_diaria.csv", index=False)
    return table


def update_driver_values(cfg: dict, log=print) -> pd.DataFrame:
    """Weekly: the Sentinel-2 days of this year and the colour of Marracuene on each (earlier years are kept).
    Asks Earth Engine for the list of passes of the last 60 days first."""
    import ee

    from .gee import init, retry
    from .turbidity_map import _sources, frame

    init(cfg)
    _, bounds = frame(cfg)
    _, _, s2 = _sources(cfg, bounds)
    start = (pd.Timestamp.now() - pd.Timedelta(days=60)).strftime("%Y-%m-%d")
    recent = s2.filterDate(start, (pd.Timestamp.now() + pd.Timedelta(days=1)).strftime("%Y-%m-%d")).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 70))
    stamps = retry(lambda: recent.aggregate_array("system:time_start").getInfo())
    new = pd.DataFrame({"utc": pd.to_datetime(stamps, unit="ms")})
    new["data"] = new["utc"].dt.strftime("%Y-%m-%d")
    file = folder(cfg) / "passagens_sentinel2.csv"
    old = pd.read_csv(file, parse_dates=["utc"])
    both = pd.concat([old, new.groupby("data")["utc"].min().reset_index()]).drop_duplicates("data").sort_values("data")
    both.to_csv(file, index=False)
    days = passes(cfg)
    days = days[days["data"] >= start]
    daily = _daily_colour(cfg, days["data"].tolist(), dict(zip(days["data"], days["mare"])), bounds)
    found = retry(lambda: daily.aggregate_array("data").zip(daily.aggregate_array("q8")).zip(daily.aggregate_array("n8")).getInfo())
    fresh = days.merge(pd.DataFrame([{"data": d, "ndti_q8": q, "pixeis_q8": n} for (d, q), n in found]), on="data")
    table_file = folder(cfg) / "cor_marracuene_diaria.csv"
    table = pd.read_csv(table_file)
    table = pd.concat([table[table["data"] < start], fresh]).sort_values("data")
    table.to_csv(table_file, index=False)
    log(f"cor de Marracuene: {len(fresh)} dias novos (desde {start})")
    return table


def fit_pixel_model(cfg: dict, last_train_day: str = LAST_TRAIN_DAY, wait_minutes: float = 120, log=print) -> Path:
    """Fit the map model on Earth Engine (an export task, so it may run long), then download it:
    a GeoTIFF with a, b, c, the typical error of each pixel (rmse) and the number of images used (n)."""
    import ee

    from .gee import download_image, init
    from .grid import snapped_grid
    from .turbidity_map import frame

    init(cfg)
    _, bounds = frame(cfg)
    days = passes(cfg)
    train = days[days["data"] <= last_train_day]
    daily = _daily_colour(cfg, train["data"].tolist(), dict(zip(train["data"], train["mare"])), bounds)
    regression = daily.map(_design).reduce(ee.Reducer.linearRegression(numX=3, numY=1))
    coefficients = regression.select("coefficients").arrayProject([0]).arrayFlatten([["a", "b", "c"]])
    error = regression.select("residuals").arrayFlatten([["rmse"]])
    count = daily.select("ndti").count().rename("n")
    regions = ee.FeatureCollection(module_q.regions_asset(cfg)).filter(ee.Filter.inList("troco", list(SECTIONS)))
    river = ee.Image(0).paint(regions, 1).eq(1)
    image = coefficients.addBands(error).addBands(count.toFloat()).updateMask(river).updateMask(count.gte(20)).toFloat()
    grid = snapped_grid(bounds, CRS, MODEL_RES_M)
    asset = asset_id("ete_cor_da_agua_modelo_mapa")
    try:
        ee.data.deleteAsset(asset)
    except ee.EEException:
        pass
    task = ee.batch.Export.image.toAsset(image=image, description="ete_cor_da_agua_modelo_mapa", assetId=asset, crs=CRS,
                                         crsTransform=[grid.res, 0, grid.x0, 0, -grid.res, grid.y0], dimensions=f"{grid.width}x{grid.height}", maxPixels=1e10)
    task.start()
    log(f"   tarefa no Earth Engine iniciada ({len(train)} dias de treino)")
    deadline = time.time() + wait_minutes * 60
    while time.time() < deadline:
        state = task.status()["state"]
        if state in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(30)
    if state != "COMPLETED":
        raise RuntimeError(f"map model on Earth Engine ended as {state}: {task.status().get('error_message', '')}")
    out = folder(cfg) / "modelo_mapa.tif"
    quiet = {**cfg, "gee": {**cfg["gee"], "workers": 1}}
    download_image(ee.Image(asset), ["a", "b", "c", "rmse", "n"], grid, out, quiet, dtype="float32")
    (folder(cfg) / "modelo_mapa.json").write_text(json.dumps({
        "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "train_days": int(len(train)), "last_train_day": last_train_day,
        "formula": "ndti_pixel = a + b * ndti_Q8 + c * tide_m", "resolution_m": MODEL_RES_M, "driver": DRIVER_SECTION}, indent=1))
    return out


# ----------------------------------------------------------------------------- 2. the Marracuene model
LEADS = (1, 3, 7, 10, 14, 21, 30)
FLOW = ["lq", "lq_mean7", "lq_max7", "dq3"]
SEASON = ["sin", "cos"]
TIDE = ["mare", "mare_sobe", "amplitude"]
LAST = ["last_ndti", "last_age", "last_lq", "dlq", "rec3", "rec5"]      # the latest measurement, and the median of the latest 3 and 5
FEATURES = FLOW + SEASON + TIDE + LAST
REACH_MIN_PIXELS = 5000     # a day counts for Marracuene when at least a fifth of Q8 was seen (about 23 600 pixels of 20 m in all):
                            # a nearly cloud-covered image gave values far from its neighbours; tested year by year, this and
                            # the medians of the latest measurements raised "right or one step off" from 77-80 % to 79-84 %


def _flow(cfg: dict, extra_q: pd.Series | None = None) -> pd.DataFrame:
    """Daily flow features (log of GloFAS discharge, its 7-day mean and maximum, change in 3 days) and the
    time of year. `extra_q` (forecast days) extends the observed record."""
    from .forecast import load_history
    from .forecast_models import _daily_drivers

    history = load_history(cfg).dropna(subset=["q"])
    q = history["q"]
    if extra_q is not None and len(extra_q):
        q = pd.concat([q[q.index < extra_q.index.min()], extra_q.astype(float)])
    daily = pd.DataFrame({"q": q, "rain": 0.0})
    daily = daily.reindex(pd.date_range(daily.index.min(), daily.index.max())).interpolate(limit=3)
    return _daily_drivers(daily)[FLOW + SEASON]


def reach_table(cfg: dict) -> pd.DataFrame:
    """Every Sentinel-2 day on which the river at Marracuene was seen, with its flow, tide and time of year."""
    seen = pd.read_csv(folder(cfg) / "cor_marracuene_diaria.csv", parse_dates=["utc"]).dropna(subset=["ndti_q8"])
    seen = seen[seen["pixeis_q8"] >= REACH_MIN_PIXELS]
    seen["date"] = pd.to_datetime(seen["data"])
    seen = seen.join(_flow(cfg), on="date").dropna(subset=FLOW).sort_values("date").reset_index(drop=True)
    seen["rec3"] = seen["ndti_q8"].rolling(3, min_periods=1).median()       # the river lately: is it running above or below its usual?
    seen["rec5"] = seen["ndti_q8"].rolling(5, min_periods=1).median()
    return seen


def lead_rows(table: pd.DataFrame, lead: int) -> pd.DataFrame:
    """Each measured day as it could have been forecast `lead` days before: the latest measurement known
    then (at least `lead` days old), its age, the flow on that day and how much the flow changed since."""
    known = table[["date", "ndti_q8", "lq", "rec3", "rec5"]].rename(columns={"date": "last_date", "ndti_q8": "last_ndti", "lq": "last_lq"}).sort_values("last_date")
    rows = table.drop(columns=["rec3", "rec5"]).assign(cut=table["date"] - pd.Timedelta(days=lead)).sort_values("cut")
    rows = pd.merge_asof(rows, known, left_on="cut", right_on="last_date", direction="backward").dropna(subset=["last_ndti"])
    rows["last_age"] = (rows["date"] - rows["last_date"]).dt.days
    rows["dlq"] = rows["lq"] - rows["last_lq"]
    rows["lead"] = lead
    return rows.drop(columns="cut")


def _classes(values) -> np.ndarray:
    return np.digitize(np.asarray(values, "float64"), STEPS)


def _model(kind: str):
    from sklearn.ensemble import HistGradientBoostingRegressor
    from sklearn.linear_model import Ridge
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler

    if kind == "boosting":
        return HistGradientBoostingRegressor(max_depth=3, learning_rate=0.05, max_iter=300, min_samples_leaf=30, l2_regularization=1.0, random_state=0)
    return make_pipeline(StandardScaler(), Ridge(alpha=1.0))


def evaluate_reach_model(cfg: dict, log=print) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Each year forecast by models that never saw it, at each lead. Returns (skill by lead and method,
    the out-of-year predictions). Methods:
      modelo (boosting)          flow, tide, time of year and the latest measurement
      modelo (linear)            the same, a straight-line model
      sem a última medição       boosting with flow, tide and time of year only
      sem saber o caudal         boosting, the flow of the forecast days replaced by the usual flow of that
                                 time of year (what is left if the flow forecast were useless)
      referência: época do ano   the median colour of that month in the other years
      referência: última medição the latest measurement repeated
    mae = typical error in NDTI units; r2 = share of the day-to-day variation explained;
    classe_certa = the colour step of the map was right; classe_vizinha = right or one step off."""
    table = reach_table(cfg)
    stacked = pd.concat([lead_rows(table, lead) for lead in LEADS], ignore_index=True)
    stacked["ano"] = stacked["date"].dt.year
    usual_flow = table.groupby(table["date"].dt.dayofyear)[FLOW].median()
    out = []
    for year in sorted(stacked["ano"].unique()):
        train, test = stacked[stacked["ano"] != year], stacked[stacked["ano"] == year].copy()
        if len(test) == 0 or len(train) < 200:
            continue
        for name, kind, cols in (("modelo (boosting)", "boosting", FEATURES), ("modelo (linear)", "linear", FEATURES),
                                 ("sem a última medição", "boosting", FLOW + SEASON + TIDE)):
            model = _model(kind).fit(train[cols], train["ndti_q8"])
            test[name] = model.predict(test[cols])
            if name == "modelo (boosting)":
                blind = test[cols].copy()
                usual = usual_flow.reindex(test["date"].dt.dayofyear).to_numpy()
                for i, col in enumerate(FLOW):
                    blind[col] = usual[:, i]
                blind["dlq"] = blind["lq"] - test["last_lq"]
                test["sem saber o caudal"] = model.predict(blind[cols])
        month = train.groupby(train["date"].dt.month)["ndti_q8"].median()
        test["referência: época do ano"] = test["date"].dt.month.map(month).to_numpy()
        test["referência: última medição"] = test["last_ndti"]
        out.append(test)
        log(f"   {year}: {len(test) // len(LEADS)} dias de teste")
    predictions = pd.concat(out, ignore_index=True)
    methods = ["modelo (boosting)", "modelo (linear)", "sem a última medição", "sem saber o caudal", "referência: época do ano", "referência: última medição"]
    rows = []
    for lead, group in predictions.groupby("lead"):
        truth = group["ndti_q8"].to_numpy()
        for method in methods:
            guess = group[method].to_numpy()
            error = guess - truth
            rows.append({"antecedencia_dias": lead, "metodo": method, "dias": len(group), "mae": float(np.mean(np.abs(error))),
                         "r2": float(1 - np.sum(error ** 2) / np.sum((truth - truth.mean()) ** 2)),
                         "classe_certa": float(np.mean(_classes(guess) == _classes(truth))),
                         "classe_vizinha": float(np.mean(np.abs(_classes(guess) - _classes(truth)) <= 1))})
    skill = pd.DataFrame(rows)
    skill.round(4).to_csv(folder(cfg) / "teste_modelo_marracuene.csv", index=False)
    return skill, predictions


def fit_reach_model(cfg: dict, predictions: pd.DataFrame) -> dict:
    """Fit the chosen model (boosting) on all the days and save it with the typical errors of each lead
    (from the out-of-year test), used to draw the band of the forecast."""
    import joblib

    table = reach_table(cfg)
    stacked = pd.concat([lead_rows(table, lead) for lead in LEADS], ignore_index=True)
    model = _model("boosting").fit(stacked[FEATURES], stacked["ndti_q8"])
    residual = predictions.assign(err=predictions["ndti_q8"] - predictions["modelo (boosting)"]).groupby("lead")["err"]
    bands = {int(k): [float(v.quantile(0.1)), float(v.quantile(0.9))] for k, v in residual}
    saved = {"model": model, "features": FEATURES, "bands": bands, "steps": list(STEPS), "leads": list(LEADS), "typical_range": float(table["amplitude"].median()),
             "trained_days": int(len(table)), "period": [str(table["date"].min().date()), str(table["date"].max().date())]}
    joblib.dump(saved, path(cfg, "models", "modelo_cor_marracuene.joblib"))
    return saved


# ----------------------------------------------------------------------------- the daily forecast (run by the daily bulletin)
FORECAST_DAYS = 30


def forecast_reach(cfg: dict, fc: dict | None = None, today: pd.Timestamp | None = None) -> pd.DataFrame:
    """The colour of the river at Marracuene for each morning of the next FORECAST_DAYS days: the most
    likely value at the satellite hour (ndti_q8), a band where 8 days out of 10 fell in the tests
    (p10-p90), its colour step, the same with an average tide (ndti_semana, for the weekly maps), the
    tide and the flow used. `fc` is the day's forecast (forecast.fetch_forecast): its 30-day GloFAS
    scenarios give the flow (their median); without it, the usual flow of the time of year is used."""
    import joblib

    from .forecast_models import tide_features

    saved = joblib.load(path(cfg, "models", "modelo_cor_marracuene.joblib", mkdir=False))
    today = pd.Timestamp(fc["date"] if fc else (today or pd.Timestamp.now().normalize())).normalize()
    days = pd.date_range(today + pd.Timedelta(days=1), periods=FORECAST_DAYS)
    extra = fc["discharge"].median(axis=1).dropna() if fc else None
    flow = _flow(cfg, extra)
    rows = flow.reindex(days)
    if rows[FLOW].isna().any(axis=None):                      # beyond the flow forecast: the usual flow of that time of year
        usual = flow[FLOW].groupby(flow.index.dayofyear).median()
        rows[FLOW] = rows[FLOW].fillna(pd.DataFrame(usual.reindex(days.dayofyear).to_numpy(), index=days, columns=FLOW))
    when = days + pd.Timedelta(hours=8)                       # the satellite passes at about 08:00 UTC (09:30-10:00 in Maputo)
    tide = tide_features(cfg, when)
    rows["mare"], rows["mare_sobe"], rows["amplitude"] = tide["t_h"].to_numpy(), tide["t_dh"].to_numpy(), tide["t_range"].to_numpy()
    seen = pd.read_csv(folder(cfg) / "cor_marracuene_diaria.csv").dropna(subset=["ndti_q8"])
    seen = seen[(pd.to_datetime(seen["data"]) <= today) & (seen["pixeis_q8"] >= REACH_MIN_PIXELS)].sort_values("data")
    last = seen.iloc[-1]
    last_date = pd.Timestamp(last["data"])
    rows["last_ndti"] = float(last["ndti_q8"])
    rows["rec3"] = float(seen["ndti_q8"].tail(3).median())
    rows["rec5"] = float(seen["ndti_q8"].tail(5).median())
    rows["last_age"] = (days - last_date).days
    rows["last_lq"] = float(flow["lq"].get(last_date, np.nan))
    rows["dlq"] = rows["lq"] - rows["last_lq"]
    value = saved["model"].predict(rows[saved["features"]])
    # the same mornings with an average tide: what the week is like whatever the hour (the weekly maps and sentences);
    # at a fixed hour the tide swings with the spring and neap tides and would make one week look muddier than the next
    neutral = rows.assign(mare=0.0, mare_sobe=0.0, amplitude=float(saved.get("typical_range", 1.6)))
    week_value = saved["model"].predict(neutral[saved["features"]])
    leads = np.array(saved["leads"])
    low, high = [], []
    for age in rows["last_age"]:
        lead = int(leads[np.argmin(np.abs(leads - min(age, leads.max())))])
        low.append(saved["bands"][lead][0])
        high.append(saved["bands"][lead][1])
    names = ["muito clara", "clara", "habitual", "turva", "muito turva"]
    return pd.DataFrame({"ndti_q8": value, "p10": value + np.array(low), "p90": value + np.array(high), "classe": [names[k] for k in _classes(value)],
                         "ndti_semana": week_value,
                         "mare_m": rows["mare"].to_numpy(), "caudal_m3s": np.expm1(rows["lq"].to_numpy()), "ultima_medicao": str(last_date.date())},
                        index=pd.Index(days.date, name="date"))


# ----------------------------------------------------------------------------- the pieces the page needs to draw a forecast map
def prepare_map_layers(cfg: dict, out_folder: Path) -> dict:
    """For the application: the map model cut to the picture of the home page (a, b, c as small arrays),
    and that picture's land (below) and names (above) as images. The page then paints a forecast map
    in a fraction of a second, with numpy and Pillow only."""
    import io

    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import rasterio
    from PIL import Image

    from .turbidity_map import LAND, crop_bounds, decorate, frame

    with rasterio.open(folder(cfg) / "modelo_mapa.tif") as src:
        coef = src.read().astype("float32")
        res, west0, north0 = src.transform.a, src.transform.c, src.transform.f
        nodata = src.nodata
    water, _ = frame(cfg)
    west, south, east, north = crop_bounds(cfg)                 # the same picture as the photograph and the measured colour
    c0, c1 = int(round((west - west0) / res)), int(round((east - west0) / res))
    r0, r1 = int(round((north0 - north) / res)), int(round((north0 - south) / res))
    a, b, c = (coef[i, r0:r1, c0:c1] for i in range(3))
    ok = np.isfinite(a) & np.isfinite(b) & np.isfinite(c) & (a != nodata)
    out_folder.mkdir(parents=True, exist_ok=True)
    np.savez_compressed(out_folder / "mapa_cor_modelo.npz", a=np.where(ok, a, 0).astype("float16"), b=np.where(ok, b, 0).astype("float16"),
                        c=np.where(ok, c, 0).astype("float16"), ok=ok, steps=np.array(STEPS, "float32"))
    width_px = 760
    for name, draw_names in (("mapa_cor_fundo.png", False), ("mapa_cor_letras.png", True)):
        fig = plt.figure(figsize=(4.6, 4.6 * (north - south) / (east - west)), dpi=width_px / 4.6, facecolor=LAND)
        ax = fig.add_axes([0, 0, 1, 1])
        if draw_names:                        # the names: a transparent layer on top
            fig.patch.set_alpha(0.0)
            ax.patch.set_alpha(0.0)
        if draw_names:
            decorate(cfg, ax, (west, south, east, north), 1.6)
        else:
            ax.set_xlim(west, east), ax.set_ylim(south, north)
            water.boundary.plot(ax=ax, color="#8A949E", linewidth=0.5, zorder=3)
        ax.set_axis_off()
        buffer = io.BytesIO()
        fig.savefig(buffer, dpi=width_px / 4.6, format="png", transparent=draw_names, facecolor=fig.get_facecolor())
        plt.close(fig)
        Image.open(buffer).save(out_folder / name, optimize=True)
    return {"modelo": "mapa_cor_modelo.npz", "fundo": "mapa_cor_fundo.png", "letras": "mapa_cor_letras.png",
            "limites_m": [west, south, east, north], "resolucao_m": res}


def test_pixel_model(cfg: dict, log=print) -> dict:
    """The map model on the 2026 images it never saw. In each image, the measured colour of Marracuene and
    the tide go into the model; every predicted point of the river is compared with what the satellite
    measured there. Two references: a flat map (every point with the colour of Marracuene) and the usual
    colour of each point (its mean over 2017-2025). Saved as teste_modelo_mapa.json."""
    import ee

    from .gee import init, retry
    from .turbidity_map import frame

    init(cfg)
    _, bounds = frame(cfg)
    model = ee.Image(asset_id("ete_cor_da_agua_modelo_mapa"))
    a, b, c = model.select("a"), model.select("b"), model.select("c")
    days = passes(cfg)
    seen = pd.read_csv(folder(cfg) / "cor_marracuene_diaria.csv").dropna(subset=["ndti_q8"])
    train = seen[seen["data"] <= LAST_TRAIN_DAY]
    usual = a.add(b.multiply(float(train["ndti_q8"].mean()))).add(c.multiply(float(train["mare"].mean())))   # least squares pass through the means
    test = days[days["data"] > LAST_TRAIN_DAY]
    daily = _daily_colour(cfg, test["data"].tolist(), dict(zip(test["data"], test["mare"])), bounds)

    def step(x):
        return x.gte(STEPS[0]).add(x.gte(STEPS[1])).add(x.gte(STEPS[2])).add(x.gte(STEPS[3]))

    def scores(img):
        measured = img.select("ndti")
        guesses = {"modelo do mapa": a.add(b.multiply(ee.Number(img.get("q8")))).add(c.multiply(ee.Number(img.get("mare")))),
                   "mapa liso (a cor de Marracuene em todo o rio)": ee.Image.constant(ee.Number(img.get("q8"))),
                   "a cor habitual de cada ponto": usual}
        bands = []
        for i, guess in enumerate(guesses.values()):
            bands += [guess.subtract(measured).abs().rename(f"mae_{i}"), step(guess).eq(step(measured)).rename(f"certa_{i}"),
                      step(guess).subtract(step(measured)).abs().lte(1).rename(f"vizinha_{i}")]
        return ee.Image.cat(bands).toFloat().updateMask(measured.mask()).updateMask(model.select("a").mask())

    region = ee.Geometry.Rectangle(list(bounds), CRS, False)
    result = retry(lambda: daily.map(scores).mean().reduceRegion(ee.Reducer.mean(), region, 40, maxPixels=1e9, tileScale=8).getInfo())
    names = ["modelo do mapa", "mapa liso (a cor de Marracuene em todo o rio)", "a cor habitual de cada ponto"]
    summary = {"dias": int(retry(lambda: daily.size().getInfo())), "periodo": [str(test["data"].min()), str(test["data"].max())],
               "metodos": [{"metodo": n, "classe_certa": round(100 * result[f"certa_{i}"], 1), "classe_vizinha": round(100 * result[f"vizinha_{i}"], 1),
                            "mae": round(result[f"mae_{i}"], 4)} for i, n in enumerate(names)]}
    (folder(cfg) / "teste_modelo_mapa.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
    log(json.dumps(summary, ensure_ascii=False))
    return summary


# ----------------------------------------------------------------------------- the river month by month (the past of the map)
def crop_grid(cfg: dict):
    """The 20 m grid of the picture of the pages (crop_bounds), aligned with the map model, so that
    past months, today and the forecast are drawn on the same pixels."""
    import rasterio

    from .grid import Grid
    from .turbidity_map import crop_bounds

    with rasterio.open(folder(cfg) / "modelo_mapa.tif") as src:
        res, west0, north0 = src.transform.a, src.transform.c, src.transform.f
    west, south, east, north = crop_bounds(cfg)
    c0, c1 = int(round((west - west0) / res)), int(round((east - west0) / res))
    r0, r1 = int(round((north0 - north) / res)), int(round((north0 - south) / res))
    return Grid(CRS, res, west0 + c0 * res, north0 - r0 * res, c1 - c0, r1 - r0)


def monthly_maps(cfg: dict, first: str = "2017-01", last: str | None = None, log=print) -> Path:
    """The colour of the river in every month since 2017: the median colour index of the pure-water
    pixels of all the Sentinel-2 images of the month (at least 2 readings per pixel), in the five
    steps of the map (0-4), 5 = river with no reading that month, 255 = not river. One small request
    per month (about 20-30 KB each); months already on disk are not asked again. Saved together in
    mapa_cor_meses.npz (only the river pixels of the picture)."""
    import io

    import ee
    import rasterio

    from .gee import init, retry
    from .turbidity_map import _sources, frame

    init(cfg)
    _, whole = frame(cfg)
    _, permanent, s2 = _sources(cfg, whole)
    grid = crop_grid(cfg)
    months_dir = folder(cfg) / "meses"
    months_dir.mkdir(exist_ok=True)
    last = last or (pd.Timestamp.now().to_period("M") - 1).strftime("%Y-%m")
    months = [str(p) for p in pd.period_range(first, last, freq="M")]
    river = permanent.eq(1)

    def step(x):
        return x.gte(STEPS[0]).add(x.gte(STEPS[1])).add(x.gte(STEPS[2])).add(x.gte(STEPS[3]))

    def reading(img):
        sr = module_q.s2_reflectance(img)
        ok = module_q.s2_clear(img).And(module_q.pure_water(sr))
        return sr.select("red").subtract(sr.select("green")).divide(sr.select("red").add(sr.select("green"))).rename("ndti").updateMask(ok)

    request_grid = {"dimensions": {"width": grid.width, "height": grid.height},
                    "affineTransform": {"scaleX": grid.res, "shearX": 0, "translateX": grid.x0, "shearY": 0, "scaleY": -grid.res, "translateY": grid.y0},
                    "crsCode": CRS}
    for month in months:
        out = months_dir / f"{month}.npy"
        if out.exists():
            continue
        start = ee.Date(month + "-01")
        images = s2.filterDate(start, start.advance(1, "month")).filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80)).map(reading)
        empty = ee.Image(255).where(river, 5).toUint8().rename("cor")              # a month with no usable image: all river "no reading"

        def coloured():
            code = step(images.median()).updateMask(images.count().gte(2))
            return ee.Image(255).where(river, 5).where(code.mask().gt(0).And(river), code.unmask(0)).toUint8().rename("cor")

        image = ee.Image(ee.Algorithms.If(images.size().gt(0), coloured(), empty))
        data = retry(lambda: ee.data.computePixels({"expression": image, "fileFormat": "GEO_TIFF", "grid": request_grid}))
        with rasterio.MemoryFile(data) as mem, mem.open() as src:
            np.save(out, src.read(1))
        log(f"   {month}")
    ok = np.load(path(cfg, "platform") / "modelos" / "mapa_cor_modelo.npz")["ok"]
    stack = np.stack([np.load(months_dir / f"{m}.npy")[ok] for m in months])
    file = folder(cfg) / "mapa_cor_meses.npz"
    np.savez_compressed(file, meses=np.array(months), codigos=stack.astype("uint8"))
    return file


def monthly_summary(cfg: dict) -> pd.DataFrame:
    """One line per month of the past maps: the share of the river that could be read, the colour of
    Marracuene that month (median of the Sentinel-2 days with at least a fifth of Q8 seen) and its step,
    and the mean river flow (GloFAS). Saved as meses_resumo.csv."""
    from .forecast import load_history

    data = np.load(folder(cfg) / "mapa_cor_meses.npz")
    months, codes = list(data["meses"]), data["codigos"]
    seen = pd.read_csv(folder(cfg) / "cor_marracuene_diaria.csv").dropna(subset=["ndti_q8"])
    seen = seen[seen["pixeis_q8"] >= REACH_MIN_PIXELS]
    seen["mes"] = seen["data"].str[:7]
    colour = seen.groupby("mes")["ndti_q8"].agg(["median", "count"])
    flow = load_history(cfg)["q"].dropna()
    flow = flow.groupby(flow.index.to_period("M").astype(str)).mean()
    names = ["muito clara", "clara", "habitual", "turva", "muito turva"]
    rows = []
    for month, row in zip(months, codes):
        value = colour["median"].get(month, np.nan)
        rows.append({"mes": month, "parte_lida": round(float((row < 5).mean()), 3), "ndti_marracuene": round(float(value), 4) if pd.notna(value) else np.nan,
                     "imagens_marracuene": int(colour["count"].get(month, 0)), "classe": names[int(_classes([value])[0])] if pd.notna(value) else "",
                     "caudal_m3s": round(float(flow.get(month, np.nan)), 1)})
    table = pd.DataFrame(rows)
    table.to_csv(folder(cfg) / "meses_resumo.csv", index=False)
    return table
