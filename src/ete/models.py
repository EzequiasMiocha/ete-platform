"""Models (week 3): Model B (water and flood detection, 10 m) and Model A
(flood susceptibility, 30 m), their validation and their maps.

Design choices that come from what the data showed in week 2:

* Model B is validated by spatial blocks on the January 2026 flood mapped by
  Copernicus EMS: each 3 km block is predicted by a model that never saw it.
  JRC labels alone hold almost no short floods, so part of the event has to be
  in the training set; the price is that the test is "new places of the same
  event", not a new event.
* A one-line physical rule (VH at the darkest moment of the month below a
  threshold) is always reported next to the model: a model must beat it.
* Model A uses terrain only by default. `jrc_occurrence` and same-month Landsat
  columns are never features: they are the label under another name.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import (cohen_kappa_score, f1_score, jaccard_score, precision_score, recall_score,
                             roc_auc_score)

from .config import path
from .grid import load_grid
from .rasters import (monthly_file, read_bands, s1_dry_reference_file, static_stack_file, study_masks,
                      write_raster)

# ----------------------------------------------------------------------------- feature sets
RADAR = ["vv", "vh", "vv_p10", "vh_p10", "vv_vh_ratio", "ratio_p10", "dvv_p10", "dvh_p10", "s1_angle"]
OPTICAL = ["s2_ndwi", "s2_mndwi", "s2_ndvi", "s2_ndmi"]
TERRAIN_B = ["hand", "slope", "twi"]
TERRAIN_A = ["hand", "slope", "twi", "elevation", "log_upstream_area", "distance_to_river_m",
             "distance_to_water_m", "distance_to_stream_m"]
HYDROMET = ["rain_basin_mm", "rain_basin_mm_lag1", "rain_basin_max_p7", "rain_district_mm",
            "q_mean", "q_max", "q_mean_lag1", "sm_cal_basin", "sm_cal_basin_lag1", "runoff_mm_basin"]
VH_RULE_DB = -22.0     # physical baseline: darkest VH of the month at or below this = water


def load_table(cfg: dict, name: str) -> pd.DataFrame:
    table = pd.read_parquet(path(cfg, "training", f"{name}.parquet", mkdir=False))
    if "vv_p10" in table:
        table["ratio_p10"] = table["vv_p10"] - table["vh_p10"]
    return table


def forest(n_estimators: int = 150, seed: int = 0) -> RandomForestClassifier:
    """Random Forest sized for a 14 GB laptop: leaves of at least 20 samples, each tree on
    30 % of the rows, 4 cores. Classes are balanced so that rare water still counts."""
    return RandomForestClassifier(n_estimators, min_samples_leaf=20, max_samples=0.3, n_jobs=4,
                                  random_state=seed, class_weight="balanced")


def algorithms(seed: int = 0) -> dict:
    """The candidate algorithms, each as a function that builds a fresh model.

    All use sensible, untuned settings sized for a 14 GB laptop; they are compared with the
    same rows, the same features and the same spatial folds, so only the algorithm changes.
    """
    from sklearn.ensemble import HistGradientBoostingClassifier
    from sklearn.impute import SimpleImputer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from xgboost import XGBClassifier

    def xgb():
        # scale_pos_weight is set at fit time by `fit_any`, to balance the classes like the others
        return XGBClassifier(n_estimators=300, max_depth=6, learning_rate=0.1, subsample=0.8, colsample_bytree=0.8,
                             tree_method="hist", n_jobs=4, random_state=seed, eval_metric="logloss")

    return {
        "Regressão logística": lambda: make_pipeline(SimpleImputer(strategy="median"), StandardScaler(),
                                                     LogisticRegression(max_iter=500, class_weight="balanced")),
        "Random Forest": lambda: forest(seed=seed),
        "Gradient Boosting (HistGB)": lambda: HistGradientBoostingClassifier(max_iter=300, learning_rate=0.1, random_state=seed,
                                                                           class_weight="balanced"),
        "XGBoost": xgb,
    }


def fit_any(make, x, y):
    """Fit a model built by `make`, balancing the classes for XGBoost as the others do."""
    model = make()
    if type(model).__name__ == "XGBClassifier":
        y = np.asarray(y)
        model.set_params(scale_pos_weight=float((y == 0).sum()) / max(float((y == 1).sum()), 1.0))
    return model.fit(x, y)


def scores(y, predicted, weight=None, probability=None) -> dict:
    """IoU, F1, Kappa, precision, recall (and ROC-AUC when a probability is given).
    `weight` makes every row count for the real area it represents."""
    out = {"n": int(len(y)),
           "iou": jaccard_score(y, predicted, sample_weight=weight),
           "f1": f1_score(y, predicted, sample_weight=weight),
           "kappa": cohen_kappa_score(y, predicted, sample_weight=weight),
           "precisao": precision_score(y, predicted, sample_weight=weight, zero_division=0),
           "recall": recall_score(y, predicted, sample_weight=weight, zero_division=0)}
    if probability is not None:
        out["auc"] = roc_auc_score(y, probability, sample_weight=weight)
    return out


def _x(table: pd.DataFrame, features: list[str]):
    return table[features].to_numpy("float32")       # plain arrays: the maps predict on arrays too


# ----------------------------------------------------------------------------- Model B
def model_b_sets(cfg: dict, table: pd.DataFrame, n_jrc: int = 100_000):
    """Rows used by Model B: a sample of JRC rows (everyday water, from model_b_start_year on),
    a separate JRC check sample, and all rows of the 2026 event (EMS)."""
    seed = cfg["processing"]["seed"]
    jrc = table[(table["label_source"] == "jrc") & (table["year"] >= cfg["processing"]["model_b_start_year"])]
    train = jrc.sample(min(n_jrc, len(jrc) // 2), random_state=seed)
    check = jrc.drop(train.index).sample(min(60_000, len(jrc) - len(train)), random_state=seed + 1)
    event = table[table["label_source"] == "ems"]
    return train, check, event


def spatial_cv_event(cfg: dict, table: pd.DataFrame, features: list[str], make=None) -> tuple[pd.Series, pd.Series]:
    """Out-of-fold probabilities for the event rows and mean probabilities for the JRC check rows.

    For each of the spatial folds: train on JRC rows + the event rows of the other folds,
    predict the event rows of this fold. No 3 km block is ever in both sides.
    `make` builds the model (default: the Random Forest).
    """
    make = make or forest
    train, check, event = model_b_sets(cfg, table)
    oof = pd.Series(np.nan, index=event.index)
    check_p = pd.Series(0.0, index=check.index)
    folds = sorted(event["fold"].unique())
    for fold in folds:
        inside = event["fold"] == fold
        rows = pd.concat([train, event[~inside]])
        model = fit_any(make, _x(rows, features), rows["label_water"])
        oof[inside[inside].index] = model.predict_proba(_x(event[inside], features))[:, 1]
        check_p += model.predict_proba(_x(check, features))[:, 1] / len(folds)
    return oof, check_p


def fit_model_b(cfg: dict, table: pd.DataFrame, features: list[str], name: str, make=None):
    """Final Model B on all its rows (JRC sample + whole event); saved to models/."""
    train, _, event = model_b_sets(cfg, table)
    rows = pd.concat([train, event])
    model = fit_any(make or forest, _x(rows, features), rows["label_water"])
    save_model(cfg, model, name, features, {"rows": int(len(rows)), "event_rows": int(len(event)),
                                           "target": "label_water", "start_year": cfg["processing"]["model_b_start_year"]})
    return model


def save_model(cfg: dict, model, name: str, features: list[str], info: dict) -> Path:
    import joblib

    out = path(cfg, "models", f"{name}.joblib")
    joblib.dump({"model": model, "features": features}, out, compress=3)
    meta = {"name": name, "features": features, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "algorithm": type(model).__name__, "params": {k: v for k, v in model.get_params().items() if k in
                                                         ("n_estimators", "min_samples_leaf", "max_samples", "class_weight",
                                                          "max_depth", "learning_rate", "max_iter")}, **info}
    out.with_suffix(".json").write_text(json.dumps(meta, indent=2))
    return out


def load_model(cfg: dict, name: str):
    import joblib

    saved = joblib.load(path(cfg, "models", f"{name}.joblib", mkdir=False))
    return saved["model"], saved["features"]


def importance(model, features: list[str], x=None, y=None, weight=None) -> pd.Series:
    """How much each feature matters. With `x` and `y`: permutation importance, i.e. how much
    the ROC-AUC drops when that feature is shuffled (works for any algorithm, so the numbers are
    comparable). Without them: the importances stored by tree models."""
    if x is None:
        return pd.Series(model.feature_importances_, index=features).sort_values(ascending=False)
    from sklearn.inspection import permutation_importance

    result = permutation_importance(model, x, y, scoring="roc_auc", n_repeats=3, random_state=0, sample_weight=weight, n_jobs=1)
    return pd.Series(result.importances_mean, index=features).sort_values(ascending=False)


def radar_feature_block(cfg: dict, month: str, window, dry: dict | None = None) -> dict:
    """The RADAR features of Model B for a block of 10 m pixels, as 2-D arrays."""
    from rasterio.windows import Window  # noqa: F401  (window type)

    s1 = read_bands(monthly_file(cfg, "sentinel1", month), ["VV", "VH", "VV_p10", "VH_p10", "angle"], window)
    dry = dry or read_bands(s1_dry_reference_file(cfg), ["VV", "VH"], window)
    return {"vv": s1["VV"], "vh": s1["VH"], "vv_p10": s1["VV_p10"], "vh_p10": s1["VH_p10"],
            "vv_vh_ratio": s1["VV"] - s1["VH"], "ratio_p10": s1["VV_p10"] - s1["VH_p10"],
            "dvv_p10": s1["VV_p10"] - dry["VV"], "dvh_p10": s1["VH_p10"] - dry["VH"], "s1_angle": s1["angle"]}


def water_map_file(cfg: dict, month: str) -> Path:
    return path(cfg, "maps", "modelo_b", f"agua_{cfg['project']['aoi_name']}_{month}_10m.tif")


def water_map(cfg: dict, model, features: list[str], month: str, block_rows: int = 600,
              overwrite: bool = False) -> Path:
    """Apply a radar Model B to every 10 m pixel of the modelling domain for one month.

    Writes data/processed/maps/modelo_b/agua_<month>_10m.tif with three bands:
    `probabilidade` (0-1), `agua` (1 where probability >= water_probability, after removing
    patches smaller than min_patch_px) and `cheia` (water outside permanent water).
    Processed in row blocks, so memory stays low.
    """
    from rasterio.windows import Window
    from scipy import ndimage as ndi

    out = water_map_file(cfg, month)
    if out.exists() and not overwrite:
        return out
    unknown = [f for f in features if f not in RADAR]
    if unknown:
        raise ValueError(f"water_map only builds radar features; not available: {unknown}")
    p = cfg["processing"]
    grid30, grid10 = load_grid(cfg), load_grid(cfg, 10)
    static = read_bands(static_stack_file(cfg), ["hand", "jrc_occurrence"])
    domain30 = study_masks(cfg)["study"] & np.isfinite(static["hand"])
    up = lambda a: np.repeat(np.repeat(a, 3, axis=0), 3, axis=1)
    domain, permanent = up(domain30), up(static["jrc_occurrence"] >= p["permanent_water_occurrence"])
    probability = np.full((grid10.height, grid10.width), np.nan, "float32")
    for row0 in range(0, grid10.height, block_rows):
        window = Window(0, row0, grid10.width, min(block_rows, grid10.height - row0))
        rows = slice(row0, row0 + window.height)
        block = radar_feature_block(cfg, month, window)
        valid = domain[rows] & np.isfinite(block["vv"]) & np.isfinite(block["vv_p10"])
        if valid.any():
            x = np.column_stack([block[f][valid] for f in features]).astype("float32")
            probability[rows][valid] = model.predict_proba(x)[:, 1]
    water = np.nan_to_num(probability, nan=0.0) >= p["water_probability"]
    patches, n = ndi.label(water)
    if n:
        sizes = np.bincount(patches.ravel())
        water &= sizes[patches] >= p["min_patch_px"]
    observed = np.isfinite(probability)
    layers = {"probabilidade": probability,
              "agua": np.where(observed, water, np.nan).astype("float32"),
              "cheia": np.where(observed, water & ~permanent, np.nan).astype("float32")}
    return write_raster(out, layers, grid10, dtype="int16", scale=100, tags={"month": month, "model": "modelo_b_radar"})


def flood_area_series(cfg: dict) -> pd.DataFrame:
    """Monthly areas (km2) from the Model B maps on disk: observed domain, water, and flood
    (water outside permanent water), in the whole domain and inside the district."""
    import rasterio

    from .rasters import available_months

    district = np.repeat(np.repeat(study_masks(cfg)["district"], 3, axis=0), 3, axis=1)
    rows = []
    for month in available_months(cfg, "sentinel1"):
        file = water_map_file(cfg, month)
        if not file.exists():
            continue
        with rasterio.open(file) as src:
            water, flood = src.read(2), src.read(3)
        observed = water != src.nodata
        rows.append({"month": month, "observado_km2": observed.sum() / 1e4, "agua_km2": (water == 100).sum() / 1e4,
                     "cheia_km2": (flood == 100).sum() / 1e4, "cheia_distrito_km2": ((flood == 100) & district).sum() / 1e4})
    return pd.DataFrame(rows).set_index("month")


def vectorise(cfg: dict, raster_file: Path, band: str, out: Path, value: float = 1.0, min_area_m2: float = 5000) -> Path:
    """Polygons of the pixels where `band` equals `value` (GIS post-processing, task S3-05)."""
    import geopandas as gpd
    import rasterio
    from rasterio.features import shapes
    from shapely.geometry import shape

    data = read_bands(raster_file, [band])[band]
    mask = data == value
    with rasterio.open(raster_file) as src:
        transform, crs = src.transform, src.crs
    polygons = [shape(geom) for geom, v in shapes(mask.astype("uint8"), mask=mask, transform=transform) if v == 1]
    frame = gpd.GeoDataFrame({"classe": [band] * len(polygons)}, geometry=polygons, crs=crs)
    frame = frame[frame.area >= min_area_m2]
    frame["area_ha"] = (frame.area / 1e4).round(2)
    out.parent.mkdir(parents=True, exist_ok=True)
    frame.to_file(out, driver="GPKG")
    return out


def reference_raster(cfg: dict, month: str, res: int = 10):
    """EMS / manual reference polygons of a month burned on the grid: 2 = water, 1 = not water, 0 = no label."""
    import geopandas as gpd
    from rasterio.features import rasterize

    from .training import LABEL_FILES

    grid = load_grid(cfg, res)
    shapes_ = []
    for key, name, _ in LABEL_FILES.values():
        file = path(cfg, key, name, mkdir=False)
        if file.exists():
            polygons = gpd.read_file(file)
            polygons = polygons[polygons["month"] == month].to_crs(grid.crs)
            shapes_ += [(g, 2 if c == "water" else 1) for g, c in zip(polygons.geometry, polygons["class"])]
    if not shapes_:
        return None
    return rasterize(sorted(shapes_, key=lambda s: s[1]), out_shape=(grid.height, grid.width), transform=grid.transform, fill=0)


# ----------------------------------------------------------------------------- Model A
def model_a_sets(table: pd.DataFrame):
    """Temporal split of the historical table: train (<= 2019), validation (2020-2021), and the
    independent test (January 2026, Copernicus EMS: label = flooded or not)."""
    jrc = table[table["label_source"] == "jrc"]
    return jrc[jrc["split"] == "train"], jrc[jrc["split"] == "val"], table[table["label_source"] == "ems"]


def fit_model_a(cfg: dict, table: pd.DataFrame, features: list[str], name: str | None = None, n_train: int = 250_000,
                make=None):
    train, _, _ = model_a_sets(table)
    rows = train.sample(min(n_train, len(train)), random_state=cfg["processing"]["seed"])
    model = fit_any(make or forest, _x(rows, features), rows["label_flood"])
    if name:
        save_model(cfg, model, name, features, {"rows": int(len(rows)), "target": "label_flood", "train_years": "<= 2019"})
    return model


def susceptibility_map(cfg: dict, model, features: list[str]) -> Path:
    """Model A (terrain only) on every 30 m pixel of the domain.

    Bands: `suscetibilidade` (0-1, the model's score) and `classe` (0 permanent water, 1 baixa,
    2 média, 3 alta, 4 muito alta), the classes being percentile bands of the score over land.
    """
    static = read_bands(static_stack_file(cfg))
    domain = study_masks(cfg)["study"] & np.isfinite(static["hand"])
    x = np.column_stack([static[f][domain] for f in features]).astype("float32")
    score = np.full(domain.shape, np.nan, "float32")
    score[domain] = model.predict_proba(x)[:, 1]
    # permanent water (river, lagoons) is not a flood zone: it gets its own class 0, and the
    # class limits are percentiles over the land only
    permanent = domain & (static["jrc_occurrence"] >= cfg["processing"]["permanent_water_occurrence"])
    land = domain & ~permanent
    limits = np.nanquantile(score[land], cfg["processing"]["susceptibility_classes"])
    classes = np.full(domain.shape, np.nan, "float32")
    classes[land] = 1 + np.searchsorted(limits, score[land], side="right")
    classes[permanent] = 0
    out = path(cfg, "maps", "modelo_a", f"suscetibilidade_{cfg['project']['aoi_name']}_30m.tif")
    return write_raster(out, {"suscetibilidade": score, "classe": classes}, load_grid(cfg),
                        tags={"model": "modelo_a_terreno", "class_limits": list(map(float, limits))})
