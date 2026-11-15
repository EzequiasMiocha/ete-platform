"""Water-quality indicators of the Incomati from Sentinel-2 (optical proxies).

What a satellite can see of water quality is its COLOUR: muddy water reflects more
red light, water rich in algae reflects more in the "red edge". Two standard
indices turn that into numbers:

    NDTI = (red - green) / (red + green)            turbidity (suspended sediment)
    NDCI = (red_edge1 - red) / (red_edge1 + red)    chlorophyll-a (algae)

They are relative indicators. Without water samples taken in the river they
cannot be converted to NTU or mg/L, and they say nothing about bacteria,
chemicals or salinity.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
from rasterio.windows import Window
from scipy import ndimage as ndi

from .config import path
from .features import _ratio
from .grid import load_grid
from .rasters import available_months, monthly_file, read_bands, static_stack_file, study_masks, write_raster

REACHES = {1: "1 montante (norte)", 2: "2 troço médio", 3: "3 jusante", 4: "4 foz / estuário"}
BANDS = ["green", "red", "red_edge1", "nir", "swir1", "n_obs"]


def river_frame(cfg: dict, shrink_px: int = 2) -> dict:
    """The river at 10 m: where to measure and how it is split into reaches.

    The channel comes from the static stack (distance to the real channel = 0), is taken to
    10 m and shrunk by `shrink_px` pixels so the banks (mixed land and water) are left out.
    Reaches are four stretches with the same number of channel pixels, from north (upstream)
    to south (the mouth). Returns the read window, the mask and the reach number per pixel.
    """
    stack = read_bands(static_stack_file(cfg), ["distance_to_river_m", "hand"])
    channel30 = (stack["distance_to_river_m"] == 0) & study_masks(cfg)["study"] & np.isfinite(stack["hand"])
    channel = np.repeat(np.repeat(channel30, 3, axis=0), 3, axis=1)
    core = ndi.binary_erosion(channel, iterations=shrink_px)
    rows = np.flatnonzero(core.any(axis=1))
    cols = np.flatnonzero(core.any(axis=0))
    window = Window(int(cols[0]), int(rows[0]), int(cols[-1] - cols[0] + 1), int(rows[-1] - rows[0] + 1))
    core = core[rows[0]:rows[-1] + 1, cols[0]:cols[-1] + 1]
    row_index = np.indices(core.shape)[0]
    limits = np.quantile(row_index[core], [0.25, 0.5, 0.75])
    reach = np.where(core, 1 + np.searchsorted(limits, row_index, side="right"), 0)
    return {"window": window, "core": core, "reach": reach}


def month_indices(cfg: dict, month: str, frame: dict) -> dict | None:
    """NDTI, NDCI and red reflectance on the river pixels that were open water that month."""
    file = monthly_file(cfg, "sentinel2", month)
    if file is None:
        return None
    b = read_bands(file, BANDS, frame["window"])
    # open water this month: MNDWI above 0 and dark in the near infrared (no floating plants, no sand bars)
    water = frame["core"] & (_ratio(b["green"], b["swir1"]) > 0) & (b["nir"] < 0.15) & np.isfinite(b["red_edge1"])
    hide = lambda a: np.where(water, a, np.nan).astype("float32")
    return {"ndti": hide(_ratio(b["red"], b["green"])), "ndci": hide(_ratio(b["red_edge1"], b["red"])),
            "red": hide(b["red"]), "n_obs": hide(b["n_obs"]), "water": water}


def monthly_series(cfg: dict, min_pixels: int = 300) -> pd.DataFrame:
    """One row per month and reach (plus the whole river): median NDTI, NDCI and red reflectance.
    A reach needs at least `min_pixels` open-water pixels (3 ha) in the month, otherwise it is left empty."""
    frame = river_frame(cfg)
    rows = []
    for month in available_months(cfg, "sentinel2"):
        ind = month_indices(cfg, month, frame)
        groups = {**{name: frame["reach"] == k for k, name in REACHES.items()}, "rio inteiro": frame["core"]}
        for name, zone in groups.items():
            seen = zone & ind["water"]
            row = {"month": month, "troco": name, "pixeis_de_agua": int(seen.sum()),
                   "parte_do_troco_observada": float(seen.sum() / zone.sum())}
            enough = seen.sum() >= min_pixels
            for key in ("ndti", "ndci", "red"):
                row[key] = float(np.nanmedian(ind[key][seen])) if enough else np.nan
            row["n_obs"] = float(np.nanmedian(ind["n_obs"][seen])) if enough else np.nan
            rows.append(row)
    return pd.DataFrame(rows)


def channel_vegetation_series(cfg: dict, ndvi_limit: float = 0.4, min_pixels: int = 300) -> pd.DataFrame:
    """Share of the river channel covered by green vegetation, per month and reach (Sentinel-2, 10 m).

    The channel is where water is present most of the time, with the banks left out. A channel
    pixel that is green (NDVI above `ndvi_limit`) in the monthly image is vegetation on the water:
    floating plants such as water hyacinth, or plants growing on exposed bars. The satellite does
    not tell the species. Columns: month, troco, pixeis_vistos, vegetacao (share 0-1), area_ha.
    """
    frame = river_frame(cfg)
    rows = []
    for month in pd.period_range("2017-01", pd.Timestamp.today().to_period("M"), freq="M").astype(str):
        file = monthly_file(cfg, "sentinel2", month)
        if file is None:
            continue
        b = read_bands(file, ["red", "nir"], frame["window"])
        seen = frame["core"] & np.isfinite(b["red"]) & np.isfinite(b["nir"])
        green = _ratio(b["nir"], b["red"]) > ndvi_limit
        for number, name in REACHES.items():
            inside = seen & (frame["reach"] == number)
            if inside.sum() >= min_pixels:
                rows.append({"month": month, "troco": name, "pixeis_vistos": int(inside.sum()),
                             "vegetacao": float(green[inside].mean()), "area_ha": float(green[inside].sum()) / 100})
    table = pd.DataFrame(rows)
    table.to_csv(path(cfg, "series", "vegetacao_no_rio_mensal.csv"), index=False)
    return table


def quality_map(cfg: dict, month: str):
    """NDTI and NDCI rasters of the river for one month (10 m), for maps and QGIS."""
    frame = river_frame(cfg)
    ind = month_indices(cfg, month, frame)
    grid = load_grid(cfg, 10)
    w = frame["window"]
    layers = {}
    for key in ("ndti", "ndci"):
        full = np.full((grid.height, grid.width), np.nan, "float32")
        full[w.row_off:w.row_off + w.height, w.col_off:w.col_off + w.width] = ind[key]
        layers[key] = full
    out = path(cfg, "maps", "qualidade_agua", f"qualidade_agua_{cfg['project']['aoi_name']}_{month}_10m.tif")
    return write_raster(out, layers, grid, dtype="int16", scale=10000, tags={"month": month}), ind, frame


def relative_class(series: pd.Series) -> pd.Series:
    """Each value against the history of its own series: normal, elevado (top 25 %), muito elevado (top 10 %)."""
    p75, p90 = series.quantile(0.75), series.quantile(0.90)
    return pd.Series(np.select([series >= p90, series >= p75, series.notna()], ["muito elevado", "elevado", "normal"], default="sem dados"),
                     index=series.index)


# ----------------------------------------------------------------------------- per-image series (Earth Engine)
# Turbidity in physical units (FNU) from the near-infrared water reflectance:
#     T = A * rho / (1 - rho / C)
# Dogliotti et al. (2011), EARSeL eProceedings 10(2), Table 2, 858 nm: A = 3078.9 FNU, C = 0.211.
# Calibrated on the North Sea and the Scheldt and tested on the La Plata estuary; NOT calibrated on
# the Incomati. Meant for turbid water (above about 10 FNU); below that the near-infrared signal is
# too weak to trust.
TURBIDITY_A, TURBIDITY_C = 3078.9, 0.211


def turbidity_fnu(nir, swir=0.0):
    """Turbidity (FNU) from near-infrared reflectance at about 860 nm, after subtracting the
    short-wave infrared (residual haze and glint). Arrays or numbers."""
    rho = np.clip(np.asarray(nir, "float64") - np.asarray(swir, "float64"), 0, 0.19)
    return TURBIDITY_A * rho / (1 - rho / TURBIDITY_C)


def reach_polygons(cfg: dict):
    """The four river reaches as polygons (EPSG:4326), from the 10 m measuring mask."""
    import geopandas as gpd
    from rasterio.features import shapes
    from rasterio.windows import transform as window_transform
    from shapely.geometry import shape
    from shapely.ops import unary_union

    frame = river_frame(cfg)
    grid = load_grid(cfg, 10)
    transform = window_transform(frame["window"], grid.transform)
    rows = []
    for number, name in REACHES.items():
        mask = frame["reach"] == number
        polygons = [shape(g) for g, v in shapes(mask.astype("uint8"), mask=mask, transform=transform) if v == 1]
        rows.append({"troco": name, "geometry": unary_union(polygons).simplify(10)})
    return gpd.GeoDataFrame(rows, crs=grid.crs).to_crs(4326)


def _scene_table(collection, prepare, reaches, scale: int, start: str, end: str) -> pd.DataFrame:
    """Median water colour of every image and reach between two dates, computed in Earth Engine."""
    import ee

    from .gee import retry

    def per_image(img):
        stats = prepare(img).reduceRegions(reaches, ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True), scale)
        return stats.map(lambda f: f.set("date", img.date().format("YYYY-MM-dd"), "image", img.get("system:index")).setGeometry(None))

    features = retry(lambda: collection.filterDate(start, end).map(per_image).flatten().getInfo())["features"]
    return pd.DataFrame([f["properties"] for f in features])


def extract_scene_series(cfg: dict, sensor: str, start_year: int, end_year: int) -> pd.DataFrame:
    """Per-image series for 'sentinel2' or 'landsat89': one row per image date and reach, with the
    median green, red, red-edge (Sentinel-2 only) and near-infrared reflectance of the open-water
    pixels, their NDTI, NDCI and turbidity (FNU), and the number of pixels used.

    Needs Earth Engine (the answers are small tables: a few hundred KB in total).
    """
    import ee

    from .gee import ee_geometry, init

    init(cfg)
    polygons = reach_polygons(cfg)
    reaches = ee.FeatureCollection([ee.Feature(ee.Geometry(g.__geo_interface__), {"troco": n}) for n, g in zip(polygons["troco"], polygons.geometry)])
    region = ee_geometry(polygons)
    a, c = TURBIDITY_A, TURBIDITY_C

    from .module_q import SHADOW_GREEN

    def indices(sr, has_red_edge):
        green, red, nir, swir = sr.select("green"), sr.select("red"), sr.select("nir"), sr.select("swir1")
        # open water only: MNDWI above 0, no floating plants (NDVI below 0.1), dark in the short-wave
        # infrared (water reflects almost nothing there; haze, thin cloud and sun glint do), and not in
        # the shadow of trees, clouds or relief (too dark for its colour to mean anything)
        water = (green.subtract(swir).divide(green.add(swir)).gt(0).And(nir.subtract(red).divide(nir.add(red)).lt(0.1))
                 .And(swir.lt(0.05)).And(green.gte(SHADOW_GREEN)))
        # what is left in the short-wave infrared is residual haze or glint, about the same in the
        # near infrared: it is subtracted before the turbidity formula (the idea of the two-band
        # version of the algorithm in Dogliotti et al., 2011)
        rho = nir.subtract(swir).clamp(0, 0.19)
        out = (sr.select(["green", "red", "nir"])
               .addBands(red.subtract(green).divide(red.add(green)).rename("ndti"))
               .addBands(rho.multiply(a).divide(ee.Image(1).subtract(rho.divide(c))).rename("turbidez_fnu")))
        if has_red_edge:
            re = sr.select("red_edge1")
            out = out.addBands(re).addBands(re.subtract(red).divide(re.add(red)).rename("ndci"))
        return out.updateMask(water)

    if sensor == "sentinel2":
        # Cloud Score+ (Google) rates how clear each pixel is; 0.65 is its recommended limit
        cloud_score = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
        collection = ee.ImageCollection(cfg["datasets"]["sentinel2"]["id"]).filterBounds(region).linkCollection(cloud_score, ["cs_cdf"])

        def prepare(img):
            scl = img.select("SCL")
            clear = scl.remap([0, 1, 3, 8, 9, 10, 11], [0] * 7, 1).And(img.select("cs_cdf").gte(0.65))
            sr = img.select(["B3", "B4", "B5", "B8A", "B11"], ["green", "red", "red_edge1", "nir", "swir1"]).multiply(0.0001).updateMask(clear)
            return indices(sr, True)

        scale = 20
    elif sensor == "landsat89":
        collection = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))).filterBounds(region)

        def prepare(img):
            clear = img.select("QA_PIXEL").bitwiseAnd(0b11111).eq(0)
            sr = img.select(["SR_B3", "SR_B4", "SR_B5", "SR_B6"], ["green", "red", "nir", "swir1"]).multiply(0.0000275).add(-0.2).updateMask(clear)
            return indices(sr, False)

        scale = 30
    else:
        raise ValueError(sensor)

    parts = [_scene_table(collection, prepare, reaches, scale, f"{y}-01-01", f"{y + 1}-01-01") for y in range(start_year, end_year + 1)]
    table = pd.concat([p for p in parts if len(p)], ignore_index=True)
    keep = {"date": "date", "troco": "troco", "image": "image", "ndti_count": "pixeis", "green_median": "green", "red_median": "red",
            "nir_median": "nir", "ndti_median": "ndti", "turbidez_fnu_median": "turbidez_fnu",
            "red_edge1_median": "red_edge1", "ndci_median": "ndci"}
    table = table[[k for k in keep if k in table]].rename(columns=keep)
    table["sensor"] = sensor
    return table


def daily_reach_series(scenes: pd.DataFrame, min_pixels: int = 150, pixel_m: int = 20) -> pd.DataFrame:
    """One row per date and reach: images of the same day are merged (weighted by their pixel count),
    and reaches with fewer than `min_pixels` open-water pixels that day are dropped."""
    scenes = scenes[scenes["pixeis"] >= 1].copy()
    values = [c for c in ("green", "red", "nir", "ndti", "turbidez_fnu", "red_edge1", "ndci") if c in scenes]
    weighted = scenes[values].multiply(scenes["pixeis"], axis=0)
    weighted[["date", "troco", "pixeis"]] = scenes[["date", "troco", "pixeis"]]
    summed = weighted.groupby(["date", "troco"]).sum()
    out = summed[values].div(summed["pixeis"], axis=0)
    out["pixeis"] = summed["pixeis"]
    out = out[out["pixeis"] >= min_pixels].reset_index()
    out["date"] = pd.to_datetime(out["date"])
    return out


# ----------------------------------------------------------------------------- analysis of the per-image series
MIN_PIXELS = {"sentinel2": 4000, "landsat89": 2000}        # about a quarter of a reach at 20 m and at 30 m


def load_scene_series(cfg: dict, sensor: str) -> pd.DataFrame:
    """Daily series per reach from the files written by scripts/update_water_quality_scenes.py.
    A reach counts on a day only when about a quarter of it or more was seen as clear open water."""
    files = sorted(path(cfg, "water_quality", mkdir=False).glob(f"{sensor}_*.csv"))
    if not files:
        raise FileNotFoundError("run scripts/update_water_quality_scenes.py first (needs Earth Engine)")
    scenes = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    daily = daily_reach_series(scenes, MIN_PIXELS[sensor])
    daily["sensor"] = sensor
    return daily


def cross_sensor_pairs(s2: pd.DataFrame, landsat: pd.DataFrame, max_days: int = 1) -> pd.DataFrame:
    """Pairs of Sentinel-2 and Landsat measurements of the same reach at most `max_days` apart.
    The two satellites and their atmospheric corrections are independent, so their agreement
    measures how repeatable the turbidity estimate is."""
    rows = []
    for reach, a in s2.groupby("troco"):
        b = landsat[landsat["troco"] == reach].sort_values("date")
        merged = pd.merge_asof(a.sort_values("date"), b, on="date", direction="nearest", tolerance=pd.Timedelta(days=max_days),
                               suffixes=("_s2", "_landsat")).dropna(subset=["turbidez_fnu_landsat"])
        merged["troco"] = reach
        rows.append(merged)
    return pd.concat(rows, ignore_index=True)


def log_agreement(reference, other) -> dict:
    """Agreement of two positive series in log10 space: correlation, typical factor between them
    (10 ** RMS difference) and systematic factor (10 ** mean difference; 1 = no bias)."""
    a, b = np.log10(np.maximum(np.asarray(reference, "float64"), 1)), np.log10(np.maximum(np.asarray(other, "float64"), 1))
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    return {"n": int(len(a)), "r": float(np.corrcoef(a, b)[0, 1]), "fator_tipico": float(10 ** np.sqrt(((b - a) ** 2).mean())),
            "fator_sistematico": float(10 ** (b - a).mean())}
