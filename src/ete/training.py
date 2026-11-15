"""Training tables (week 2, tasks S2-10 and S2-11).

One row = one pixel in one month, with its features and its label. The full
grids hold hundreds of millions of pixel-months, far more than a model needs,
so each month is *sampled* by strata (flood water, permanent water, dry low
ground, other dry ground). Every row carries a `weight` = how many real pixels
it represents, so statistics can still be computed for the whole area.

Rasters are read one month at a time: memory use stays low.
"""

from __future__ import annotations

import ast
import json
from datetime import datetime, timezone

import numpy as np
import pandas as pd
import rasterio
from tqdm.auto import tqdm

from . import __version__
from .config import path
from .drivers import load_monthly_drivers
from .features import optical_indices, radar_features
from .grid import load_grid
from .rasters import (available_months, monthly_file, read_bands, s1_dry_reference_file,
                      sample_raster, static_stack_file, study_masks)

STATIC_FEATURES = ["elevation", "slope", "aspect", "hand", "log_upstream_area", "twi",
                   "distance_to_river_m", "distance_to_water_m", "distance_to_stream_m", "land_cover"]
OPTICAL = ["blue", "green", "red", "nir", "swir1", "swir2"]


# -----------------------------------------------------------------------------
# Sampling frame
# -----------------------------------------------------------------------------

def sampling_frame(cfg: dict) -> dict:
    """Everything that does not change from month to month, on the 30 m grid."""
    p = cfg["processing"]
    grid = load_grid(cfg)
    static = read_bands(static_stack_file(cfg))
    masks = study_masks(cfg)
    # modelling domain: inside district + buffer AND with terrain data (MERIT Hydro has no
    # values over the open sea, which is not part of the flood problem)
    domain = masks["study"] & np.isfinite(static["hand"])
    size = round(p["block_size_m"] / grid.res)
    rows, cols = np.indices((grid.height, grid.width))
    block = (rows // size) * 1000 + (cols // size)
    ids = np.unique(block[domain])
    order = np.random.default_rng(p["seed"]).permutation(len(ids))
    fold_of = dict(zip(ids.tolist(), (order % p["n_folds"]).tolist()))
    return {"grid": grid, "static": static, "domain": domain, "district": masks["district"],
            "permanent": static["jrc_occurrence"] >= p["permanent_water_occurrence"],
            "low": static["hand"] <= p["low_hand_m"], "block": block, "fold_of": fold_of}


def sample_month(rng, water: np.ndarray, frame: dict, counts: dict) -> pd.DataFrame:
    """Stratified random sample of one month. `water` is the JRC monthly band
    (0 = not observed, 1 = not water, 2 = water); unobserved pixels are never sampled."""
    observed = frame["domain"] & ((water == 1) | (water == 2))
    is_water = observed & (water == 2)
    dry = observed & (water == 1)
    strata = {
        "flood": is_water & ~frame["permanent"],
        "permanent": is_water & frame["permanent"],
        "dry_low": dry & frame["low"],
        "dry_other": dry & ~frame["low"],
    }
    parts = []
    for name, mask in strata.items():
        idx = np.flatnonzero(mask)
        if len(idx) == 0:
            continue
        take = rng.choice(idx, size=min(counts[name], len(idx)), replace=False)
        rows, cols = np.unravel_index(take, mask.shape)
        parts.append(pd.DataFrame({"row": rows, "col": cols, "stratum": name,
                                   "weight": np.float32(len(idx) / len(take))}))
    if not parts:
        return pd.DataFrame(columns=["row", "col", "stratum", "weight"])
    return pd.concat(parts, ignore_index=True)


LABEL_FILES = {  # label_source -> (path key, file name, pixels kept per class and month)
    "manual": ("labels_manual", "labels.gpkg", 5000),
    "ems": ("ems_unosat", "ems_labels.gpkg", 20000),
}


def reference_label_pixels(cfg: dict, month: str, frame: dict, rng=None) -> pd.DataFrame:
    """Pixels inside reference polygons for `month`: drawn in QGIS (labels.gpkg) or taken
    from Copernicus EMS flood maps (ems_labels.gpkg). `stratum` holds the source.
    A `non_water` polygon never labels permanent water (rivers and lagoons inside it)."""
    import geopandas as gpd
    from rasterio.features import rasterize

    grid = frame["grid"]
    parts = []
    for source, (key, name, cap) in LABEL_FILES.items():
        file = path(cfg, key, name, mkdir=False)
        if not file.exists():
            continue
        polygons = gpd.read_file(file)
        polygons = polygons[(polygons["month"] == month) & polygons["class"].isin(["water", "non_water"])]
        if polygons.empty:
            continue
        polygons = polygons.to_crs(grid.crs)
        shapes = [(geom, 2 if cls == "water" else 1) for geom, cls in zip(polygons.geometry, polygons["class"])]
        burned = rasterize(sorted(shapes, key=lambda s: s[1]), out_shape=(grid.height, grid.width), transform=grid.transform, fill=0)
        for value in (1, 2):
            mask = (burned == value) & frame["domain"]
            if value == 1:
                mask &= ~frame["permanent"]
            idx = np.flatnonzero(mask)
            if len(idx) == 0:
                continue
            total = len(idx)
            if total > cap:
                idx = (rng or np.random.default_rng(0)).choice(idx, cap, replace=False)
            rows, cols = np.unravel_index(idx, burned.shape)
            parts.append(pd.DataFrame({"row": rows, "col": cols, "stratum": source,
                                       "weight": np.float32(total / len(idx)), "label_water": np.int8(value == 2)}))
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _base_columns(sample: pd.DataFrame, month: str, frame: dict, cfg: dict) -> pd.DataFrame:
    p = cfg["processing"]
    grid = frame["grid"]
    rows, cols = sample["row"].to_numpy(), sample["col"].to_numpy()
    year, month_num = int(month[:4]), int(month[5:])
    out = pd.DataFrame({
        "month": month, "year": np.int16(year), "month_num": np.int8(month_num),
        "season": "wet" if month_num in p["wet_months"] else "dry",
        "row": rows.astype("int32"), "col": cols.astype("int32"),
        "x": (grid.x0 + (cols + 0.5) * grid.res).astype("float32"),
        "y": (grid.y0 - (rows + 0.5) * grid.res).astype("float32"),
        "block_id": frame["block"][rows, cols].astype("int32"),
        "in_district": frame["district"][rows, cols],
        "stratum": sample["stratum"].to_numpy(), "weight": sample["weight"].to_numpy(),
    })
    out["fold"] = out["block_id"].map(frame["fold_of"]).astype("int8")
    out["split"] = "train" if year <= p["splits"]["train_end"] else "val" if year <= p["splits"]["val_end"] else "test"
    permanent = frame["permanent"][rows, cols]
    out["label_water"] = sample["label_water"].to_numpy().astype("int8")
    out["label_flood"] = (out["label_water"].astype(bool) & ~permanent).astype("int8")
    out["label_source"] = np.where(sample["stratum"].isin(list(LABEL_FILES)), sample["stratum"], "jrc")
    out["jrc_occurrence"] = frame["static"]["jrc_occurrence"][rows, cols]
    for name in STATIC_FEATURES:
        out[name] = frame["static"][name][rows, cols]
    return out


def _month_samples(cfg, month, frame, rng) -> pd.DataFrame:
    """JRC-labelled sample of a month plus any manually labelled pixels."""
    parts = []
    jrc = monthly_file(cfg, "jrc_monthly", month)
    if jrc is not None:
        with rasterio.open(jrc) as src:
            water = src.read(1)
        sample = sample_month(rng, water, frame, cfg["processing"]["sampling"])
        sample["label_water"] = (water[sample["row"], sample["col"]] == 2).astype("int8")
        parts.append(sample)
    reference = reference_label_pixels(cfg, month, frame, rng=rng)
    if len(reference):
        parts.append(reference)
    return pd.concat(parts, ignore_index=True) if parts else pd.DataFrame()


def _finish(cfg: dict, frames: list, name: str, description: str) -> pd.DataFrame:
    table = pd.concat(frames, ignore_index=True)
    drivers = load_monthly_drivers(cfg)
    table = table.join(drivers.astype("float32"), on="month")
    for col in table.select_dtypes("float64"):
        table[col] = table[col].astype("float32")
    for col in ("month", "season", "stratum", "split", "label_source"):
        table[col] = table[col].astype("category")
    out = path(cfg, "training", f"{name}.parquet")
    table.to_parquet(out, index=False)
    meta = {"name": name, "description": description, "created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "code_version": __version__, "rows": int(len(table)), "columns": int(table.shape[1]),
            "months": [str(table["month"].astype(str).min()), str(table["month"].astype(str).max())],
            "rows_per_split": {k: int(v) for k, v in table["split"].value_counts().items()},
            "rows_per_stratum": {k: int(v) for k, v in table["stratum"].value_counts().items()},
            "processing": cfg["processing"]}
    out.with_suffix(".meta.json").write_text(json.dumps(meta, indent=2))
    return table


# -----------------------------------------------------------------------------
# Layer 1: historical, 30 m (Model A)
# -----------------------------------------------------------------------------

def build_historical(cfg: dict, months: list[str] | None = None) -> pd.DataFrame:
    """train_historico.parquet: Landsat + terrain + monthly drivers, labelled by JRC monthly water."""
    frame = sampling_frame(cfg)
    rng = np.random.default_rng(cfg["processing"]["seed"])
    months = months or sorted(set(available_months(cfg, "jrc_monthly")) | set(_manual_months(cfg)))
    frames = []
    for month in tqdm(months, desc="camada 1"):
        sample = _month_samples(cfg, month, frame, rng)
        if sample.empty:
            continue
        rows = _base_columns(sample, month, frame, cfg)
        landsat = monthly_file(cfg, "landsat", month)
        if landsat is not None:
            values = sample_raster(landsat, rows["row"], rows["col"])
            with rasterio.open(landsat) as src:
                sensors = src.tags().get("sensors", "")
            for band in OPTICAL:
                rows[band] = values[band].to_numpy()
            for index, data in optical_indices(*(values[b].to_numpy() for b in OPTICAL)).items():
                rows[index] = data
            rows["landsat_n_obs"] = values["n_obs"].to_numpy()
            rows["landsat_sensors"] = "+".join(sorted(k.replace("LANDSAT_", "L") for k in ast.literal_eval(sensors))) if sensors else ""
        else:
            rows["landsat_n_obs"] = np.float32(0)
            rows["landsat_sensors"] = ""
        frames.append(rows)
    return _finish(cfg, frames, "train_historico",
                   "Layer 1 (30 m): one row per sampled pixel and month, Landsat + terrain + rain, soil moisture and discharge.")


# -----------------------------------------------------------------------------
# Layer 2: recent, 10 m (Model B)
# -----------------------------------------------------------------------------

def build_recent(cfg: dict, months: list[str] | None = None) -> pd.DataFrame:
    """train_recente.parquet: Sentinel-1 + Sentinel-2 (+ Dynamic World) at 10 m.

    The label comes from the 30 m JRC cell; the 10 m pixel sampled is the centre one of
    that cell (of its 3 x 3), which avoids the mixed pixels at the cell edges.
    Rows without a Sentinel-1 value are dropped: Model B is a radar-first model.
    """
    frame = sampling_frame(cfg)
    rng = np.random.default_rng(cfg["processing"]["seed"] + 1)
    labelled = set(available_months(cfg, "jrc_monthly")) | set(_manual_months(cfg))
    months = months or sorted(labelled & set(available_months(cfg, "sentinel1")))
    dry = read_bands(s1_dry_reference_file(cfg), ["VV", "VH"])
    offsets_file = path(cfg, "series", "s1_change_monthly.csv")
    offsets = pd.read_csv(offsets_file, index_col=0) if offsets_file.exists() else pd.DataFrame()
    s2_bands = list(cfg["datasets"]["sentinel2"]["bands"].values())
    frames = []
    for month in tqdm(months, desc="camada 2"):
        sample = _month_samples(cfg, month, frame, rng)
        if sample.empty:
            continue
        rows = _base_columns(sample, month, frame, cfg)
        r10, c10 = rows["row"].to_numpy() * 3 + 1, rows["col"].to_numpy() * 3 + 1

        s1_file = monthly_file(cfg, "sentinel1", month)
        s1 = sample_raster(s1_file, r10, c10)
        rows["vv"], rows["vh"], rows["s1_angle"] = s1["VV"].to_numpy(), s1["VH"].to_numpy(), s1["angle"].to_numpy()
        rows["s1_n_obs"] = s1["n_obs"].to_numpy()
        for feature, data in radar_features(rows["vv"], rows["vh"], dry["VV"][r10, c10], dry["VH"][r10, c10]).items():
            rows[feature] = data
        # darkest moment of the month (10th percentile): what catches floods lasting a few days
        if "VV_p10" in s1:
            rows["vv_p10"], rows["vh_p10"] = s1["VV_p10"].to_numpy(), s1["VH_p10"].to_numpy()
            rows["dvv_p10"] = rows["vv_p10"] - dry["VV"][r10, c10]
            rows["dvh_p10"] = rows["vh_p10"] - dry["VH"][r10, c10]
        # change with the month-wide shift removed (soil wetness, orbit mix); see rasters.s1_change_series
        if month in offsets.index:
            rows["dvv_rel"] = rows["dvv"] - np.float32(offsets.at[month, "s1_offset_vv"])
            rows["dvh_rel"] = rows["dvh"] - np.float32(offsets.at[month, "s1_offset_vh"])

        s2_file = monthly_file(cfg, "sentinel2", month)
        if s2_file is not None:
            s2 = sample_raster(s2_file, r10, c10)
            for band in s2_bands:
                rows[f"s2_{band}"] = s2[band].to_numpy()
            for index, data in optical_indices(*(s2[b].to_numpy() for b in OPTICAL)).items():
                rows[f"s2_{index}"] = data
            rows["s2_n_obs"] = s2["n_obs"].to_numpy()
        else:
            rows["s2_n_obs"] = np.float32(0)

        dw_file = monthly_file(cfg, "dynamic_world", month)
        if dw_file is not None:
            dw = sample_raster(dw_file, r10, c10, ["water", "flooded_vegetation"], prefix="dw_")
            rows["dw_water"], rows["dw_flooded_vegetation"] = dw["dw_water"].to_numpy(), dw["dw_flooded_vegetation"].to_numpy()

        frames.append(rows[np.isfinite(rows["vv"])])
    return _finish(cfg, frames, "train_recente",
                   "Layer 2 (10 m): one row per sampled pixel and month, Sentinel-1 + Sentinel-2 + terrain + monthly drivers.")


def _manual_months(cfg: dict) -> list[str]:
    """Months that have reference polygons (QGIS or EMS)."""
    import geopandas as gpd

    months = set()
    for key, name, _ in LABEL_FILES.values():
        file = path(cfg, key, name, mkdir=False)
        if file.exists():
            months |= set(gpd.read_file(file, ignore_geometry=True)["month"].dropna().unique().tolist())
    return sorted(m for m in months if isinstance(m, str) and len(m) == 7)


# -----------------------------------------------------------------------------
# Data dictionary (written next to the parquet files, in Portuguese for the team)
# -----------------------------------------------------------------------------

_GROUPS = [
    # (test on the column name, group, description, unit)
    (lambda c: c in ("month", "year", "month_num", "season"), "metadados", "Data do registo (mês, ano, época chuvosa/seca)", ""),
    (lambda c: c in ("row", "col"), "metadados", "Posição do píxel na grelha de 30 m", "índice"),
    (lambda c: c in ("x", "y"), "metadados", "Coordenadas do centro do píxel (EPSG:32736)", "m"),
    (lambda c: c in ("block_id", "fold"), "validacao", "Bloco espacial de 3 km e grupo (fold) para validação cruzada espacial", ""),
    (lambda c: c == "split", "validacao", "Divisão temporal: train (até 2019), val (2020-2021), test (2022+)", ""),
    (lambda c: c == "in_district", "metadados", "Verdadeiro se o píxel está dentro do distrito de Marracuene", ""),
    (lambda c: c == "stratum", "amostragem", "Estrato de onde o píxel foi sorteado", ""),
    (lambda c: c == "weight", "amostragem", "Número de píxeis reais que esta linha representa", "píxeis"),
    (lambda c: c == "label_water", "rotulo", "1 = água nesse mês, 0 = não é água", ""),
    (lambda c: c == "label_flood", "rotulo", "1 = água fora da água permanente (cheia ou água sazonal), 0 = resto", ""),
    (lambda c: c == "label_source", "rotulo", "Origem do rótulo: jrc (JRC mensal), ems (mapa Copernicus EMS) ou manual (QGIS)", ""),
    (lambda c: c == "jrc_occurrence", "rotulo_auxiliar", "Frequência histórica de água (JRC). NÃO usar como feature: é quase o rótulo", "%"),
    (lambda c: c in STATIC_FEATURES, "terreno", "Camada estática de terreno ou cobertura do solo", ""),
    (lambda c: c in OPTICAL, "landsat", "Refletância de superfície Landsat (mediana mensal)", "0-1"),
    (lambda c: c in ("ndwi", "mndwi", "ndvi", "ndmi", "awei_sh", "awei_nsh"), "landsat", "Índice espectral Landsat", ""),
    (lambda c: c.startswith("landsat_"), "landsat", "Qualidade Landsat: nº de observações limpas / satélites usados", ""),
    (lambda c: c in ("vv", "vh", "s1_angle", "s1_n_obs", "vv_vh_ratio", "dvv", "dvh", "dvv_rel", "dvh_rel"), "sentinel1", "Radar Sentinel-1 (dB), diferença para a época seca (_rel: sem o desvio geral do mês), ângulo, nº de observações", "dB"),
    (lambda c: c in ("vv_p10", "vh_p10", "dvv_p10", "dvh_p10"), "sentinel1", "Radar no momento mais escuro do mês (percentil 10) e a sua diferença para a época seca: apanha cheias de poucos dias", "dB"),
    (lambda c: c.startswith("s2_"), "sentinel2", "Sentinel-2: reflectância, índices e nº de observações limpas", ""),
    (lambda c: c.startswith("dw_"), "dynamic_world", "Probabilidade Dynamic World (produto de um modelo, não é rótulo)", "0-1"),
    (lambda c: c.startswith(("rain_", "imerg_")), "chuva", "Chuva mensal: total, máximos e percentis (bacia e distrito)", "mm ou percentil"),
    (lambda c: c.startswith(("sm_", "smap_")), "humidade_solo", "Humidade do solo (ERA5-Land, ERA5-Land calibrado, SMAP)", "m3/m3"),
    (lambda c: c.startswith(("runoff_", "evap_", "temp_")), "hidrometeorologia", "Escoamento, evaporação e temperatura (ERA5-Land)", "mm ou °C"),
    (lambda c: c.startswith("q_"), "caudal", "Caudal GloFAS em Marracuene: média, máximo, percentil", "m3/s"),
]


def data_dictionary(table: pd.DataFrame) -> pd.DataFrame:
    """One row per column: group, meaning, unit, share of missing values."""
    rows = []
    for col in table.columns:
        group, description, unit = next(((g, d, u) for test, g, d, u in _GROUPS if test(col)), ("outro", "", ""))
        rows.append({"coluna": col, "grupo": group, "descricao": description, "unidade": unit,
                     "tipo": str(table[col].dtype), "em_falta_pct": round(100 * float(table[col].isna().mean()), 1)})
    return pd.DataFrame(rows)
