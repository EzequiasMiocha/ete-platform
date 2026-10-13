"""Local raster helpers (week 2): reading the monthly files in physical units,
writing derived rasters on the project grid, and building the derived layers
(study mask, static stack, Sentinel-1 dry-season reference).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import rasterio
from rasterio.features import geometry_mask
from rasterio.windows import Window

from .config import path
from .features import twi
from .grid import Grid, imagery_mask, load_aoi, load_grid

# dataset key in config paths -> file name prefix written by the week-1 downloads
MONTHLY = {
    "landsat": ("landsat", 30),
    "sentinel2": ("sentinel2", 10),
    "sentinel1": ("sentinel1", 10),
    "dynamic_world": ("dynamicworld", 10),
    "jrc_monthly": ("jrcmonthly", 30),
}


def monthly_file(cfg: dict, key: str, month: str) -> Path | None:
    """Path of the monthly GeoTIFF of a dataset ('YYYY-MM'), or None if that month has no file."""
    prefix, res = MONTHLY[key]
    file = path(cfg, key, month[:4], mkdir=False) / f"{prefix}_{cfg['project']['aoi_name']}_{month}_{res}m.tif"
    return file if file.exists() else None


def available_months(cfg: dict, key: str) -> list[str]:
    prefix, res = MONTHLY[key]
    files = path(cfg, key, mkdir=False).rglob(f"{prefix}_*_{res}m.tif")
    return sorted(f.stem.split("_")[2] for f in files if ".part" not in f.name)


def read_bands(file: Path, bands: list[str] | None = None, window: Window | None = None) -> dict:
    """Bands of a project GeoTIFF as float32 arrays in physical units, NaN where there is no data."""
    out = {}
    with rasterio.open(file) as src:
        names = list(src.descriptions)
        for band in bands or names:
            i = names.index(band) + 1
            raw = src.read(i, window=window)
            data = raw.astype("float32") * np.float32(src.scales[i - 1])
            if src.nodata is not None:
                data[raw == src.nodata] = np.nan
            out[band] = data
    return out


def sample_raster(file: Path, rows, cols, bands: list[str] | None = None, prefix: str = "") -> pd.DataFrame:
    """Values of a raster at pixel positions (rows, cols), one column per band.
    Reads one band at a time, so even the 10 m files need little memory."""
    rows, cols = np.asarray(rows), np.asarray(cols)
    out = {}
    with rasterio.open(file) as src:
        names = list(src.descriptions)
        for band in bands or names:
            i = names.index(band) + 1
            raw = src.read(i)[rows, cols]
            values = raw.astype("float32") * np.float32(src.scales[i - 1])
            if src.nodata is not None:
                values[raw == src.nodata] = np.nan
            out[prefix + band] = values
    return pd.DataFrame(out)


def write_raster(file: Path, arrays: dict, grid: Grid, dtype: str = "float32",
                 scale: float = 1, tags: dict | None = None) -> Path:
    """Write named 2-D arrays as a compressed GeoTIFF on `grid`. NaN becomes nodata.
    With an integer dtype, values are stored as round(value * scale)."""
    file = Path(file)
    file.parent.mkdir(parents=True, exist_ok=True)
    nodata = {"float32": -9999.0, "int16": -9999, "uint8": 255, "int32": -9999}[dtype]
    profile = dict(driver="GTiff", width=grid.width, height=grid.height, count=len(arrays), dtype=dtype,
                   crs=grid.crs, transform=grid.transform, nodata=nodata, compress="deflate",
                   predictor=3 if dtype == "float32" else 2, tiled=True, blockxsize=512, blockysize=512)
    part = file.with_suffix(".part.tif")
    with rasterio.open(part, "w", **profile) as dst:
        for i, (name, data) in enumerate(arrays.items(), start=1):
            data = np.asarray(data, "float32")
            stored = np.where(np.isfinite(data), data * scale if dtype != "float32" else data, nodata)
            dst.write((np.round(stored) if dtype != "float32" else stored).astype(dtype), i)
            dst.set_band_description(i, name)
        dst.scales = [1 / scale] * len(arrays)
        dst.update_tags(**{k: str(v) for k, v in (tags or {}).items()})
    part.replace(file)
    # QGIS leaves a statistics cache next to rasters it opens; a stale one would override
    # the band names of a file written again
    file.with_name(file.name + ".aux.xml").unlink(missing_ok=True)
    return file


# -----------------------------------------------------------------------------
# Derived layers
# -----------------------------------------------------------------------------

def study_masks(cfg: dict) -> dict:
    """Boolean rasters on the 30 m grid: `study` = district + buffer (where monthly imagery
    exists), `district` = the district itself (land and inland water, no open sea)."""
    grid = load_grid(cfg)
    shape = (grid.height, grid.width)
    inside = lambda gdf: geometry_mask(gdf.to_crs(grid.crs).geometry, shape, grid.transform, invert=True)
    return {"study": inside(imagery_mask(cfg)), "district": inside(load_aoi(cfg, "district"))}


def static_stack_file(cfg: dict) -> Path:
    return path(cfg, "features", f"static_stack_{cfg['project']['aoi_name']}_30m.tif")


def build_static_stack(cfg: dict) -> Path:
    """One 30 m GeoTIFF with every static feature, aligned on the project grid.

    WorldCover (10 m) is reduced to the most frequent class of each 3 x 3 block.
    """
    name = cfg["project"]["aoi_name"]
    grid = load_grid(cfg)
    terrain = path(cfg, "static_terrain", mkdir=False)
    one = lambda file, band=None: next(iter(read_bands(file, [band] if band else None).values()))
    layers = {
        "elevation": one(terrain / f"dem_{name}_30m.tif"),
        "slope": one(terrain / f"slope_{name}_30m.tif"),
        "aspect": one(terrain / f"aspect_{name}_30m.tif"),
        "hand": one(terrain / f"hand_{name}_30m.tif"),
        "upstream_area_km2": one(terrain / f"flow_accumulation_{name}_30m.tif"),
        # distance to any HydroSHEDS stream line (coarse lines, small tributaries included)
        "distance_to_stream_m": one(path(cfg, "interim", "static", mkdir=False) / f"distance_to_river_{name}_30m.tif"),
    }
    layers["log_upstream_area"] = np.log10(np.maximum(layers["upstream_area_km2"], 1e-4))
    layers["twi"] = twi(layers["upstream_area_km2"], layers["slope"], grid.res)

    with rasterio.open(path(cfg, "static_land_cover", mkdir=False) / f"worldcover_{name}_10m.tif") as src:
        cover = src.read(1)
    blocks = cover.reshape(grid.height, 3, grid.width, 3).transpose(0, 2, 1, 3).reshape(grid.height, grid.width, 9)
    classes = np.unique(cover[cover != 255])
    counts = np.stack([(blocks == c).sum(axis=2) for c in classes])
    majority = classes[counts.argmax(axis=0)].astype("float32")
    majority[counts.sum(axis=0) == 0] = np.nan
    layers["land_cover"] = majority

    jrc = read_bands(path(cfg, "static_surface_water", mkdir=False) / f"jrc_gsw_{name}_30m.tif",
                     ["occurrence", "seasonality"])
    layers["jrc_occurrence"] = np.nan_to_num(jrc["occurrence"], nan=0.0)     # never water = 0 %
    layers["jrc_seasonality"] = np.nan_to_num(jrc["seasonality"], nan=0.0)

    channel, water = river_channel(layers["upstream_area_km2"], layers["jrc_occurrence"], layers["hand"],
                                   cfg["processing"]["permanent_water_occurrence"])
    from scipy.ndimage import distance_transform_edt
    layers["distance_to_river_m"] = (distance_transform_edt(~channel) * grid.res).astype("float32")
    layers["distance_to_water_m"] = (distance_transform_edt(~water) * grid.res).astype("float32")
    _save_channel(cfg, channel, grid)
    return write_raster(static_stack_file(cfg), layers, grid, tags={"dataset": "static_stack"})


def river_channel(upstream_area_km2, jrc_occurrence, hand, permanent: float = 75,
                  main_stem_km2: float = 10000, reach_px: int = 10):
    """The real Incomati channel and all permanent inland water, as boolean rasters.

    The HydroSHEDS river lines are drawn at about 500 m and miss the meanders. Here the
    main stem comes from the terrain itself (MERIT Hydro cells draining more than
    `main_stem_km2`) and is widened to the water actually seen by satellite: every
    patch of frequent water (JRC occurrence >= 50 %) lying within `reach_px` pixels of
    it. Open sea is excluded (MERIT Hydro has no data there).
    Returns (channel, permanent_water).
    """
    from scipy import ndimage as ndi

    inland = np.isfinite(hand)
    main = np.nan_to_num(upstream_area_km2, nan=0.0) >= main_stem_km2
    frequent = (jrc_occurrence >= 50) & inland
    patches, _ = ndi.label(frequent, structure=np.ones((3, 3)))
    touching = np.unique(patches[ndi.binary_dilation(main, iterations=reach_px) & frequent])
    channel = main | np.isin(patches, touching[touching > 0])
    return channel, (jrc_occurrence >= permanent) & inland


def _save_channel(cfg: dict, channel: np.ndarray, grid: Grid) -> Path:
    """River channel as polygons, for QGIS."""
    import geopandas as gpd
    from rasterio.features import shapes
    from shapely.geometry import shape

    polygons = [shape(geom) for geom, value in shapes(channel.astype("uint8"), mask=channel, transform=grid.transform) if value == 1]
    out = path(cfg, "features", f"river_channel_{cfg['project']['aoi_name']}.gpkg")
    gpd.GeoDataFrame({"name": ["Incomati channel"] * len(polygons)}, geometry=polygons, crs=grid.crs).dissolve().to_file(out, driver="GPKG")
    return out


def s1_dry_reference_file(cfg: dict) -> Path:
    return path(cfg, "features", f"sentinel1_dry_reference_{cfg['project']['aoi_name']}_10m.tif")


def build_s1_dry_reference(cfg: dict, block_rows: int = 256) -> Path:
    """Per-pixel median of VV and VH (dB) over all dry-season months: the 'normal dry'
    radar image against which each month is compared (delta-VV). Computed in row
    blocks so it fits in memory."""
    dry = set(cfg["processing"]["dry_months"])
    months = [m for m in available_months(cfg, "sentinel1") if int(m[5:]) in dry]
    files = [monthly_file(cfg, "sentinel1", m) for m in months]
    grid = load_grid(cfg, 10)
    out = {"VV": np.full((grid.height, grid.width), np.nan, "float32"),
           "VH": np.full((grid.height, grid.width), np.nan, "float32"),
           "n_months": np.zeros((grid.height, grid.width), "float32")}
    for row0 in range(0, grid.height, block_rows):
        window = Window(0, row0, grid.width, min(block_rows, grid.height - row0))
        rows = slice(row0, row0 + window.height)
        stacks = {"VV": [], "VH": []}
        for file in files:
            data = read_bands(file, ["VV", "VH"], window)
            stacks["VV"].append(data["VV"])
            stacks["VH"].append(data["VH"])
        for band in ("VV", "VH"):
            cube = np.stack(stacks[band])
            valid = np.isfinite(cube).sum(axis=0)
            with np.errstate(all="ignore"):
                import warnings
                with warnings.catch_warnings():
                    warnings.simplefilter("ignore", RuntimeWarning)
                    out[band][rows] = np.nanmedian(cube, axis=0)
            if band == "VV":
                out["n_months"][rows] = valid
    return write_raster(s1_dry_reference_file(cfg), out, grid, dtype="int16", scale=100,
                        tags={"dataset": "sentinel1_dry_reference", "months": " ".join(months)})


def export_month_features(cfg: dict, month: str) -> list[Path]:
    """Write the derived feature rasters of one month (for QGIS, the workshop or a report):
    Landsat indices (30 m), Sentinel-2 indices (10 m) and Sentinel-1 radar features (10 m).
    Indices are cheap to recompute, so they are exported only for the months asked for."""
    from .features import optical_indices, radar_features

    name, out = cfg["project"]["aoi_name"], []
    folder = path(cfg, "features", "indices", month)
    optical = ["blue", "green", "red", "nir", "swir1", "swir2"]
    for key, res in (("landsat", 30), ("sentinel2", 10)):
        file = monthly_file(cfg, key, month)
        if file is not None:
            bands = read_bands(file, optical)
            indices = optical_indices(*(bands[b] for b in optical))
            del bands
            out.append(write_raster(folder / f"{key}_indices_{name}_{month}_{res}m.tif", indices,
                                    load_grid(cfg, res), dtype="int16", scale=10000, tags={"source": file.name}))
    file = monthly_file(cfg, "sentinel1", month)
    if file is not None and s1_dry_reference_file(cfg).exists():
        with rasterio.open(file) as src:
            has_p10 = "VV_p10" in src.descriptions
        s1 = read_bands(file, ["VV", "VH"] + (["VV_p10", "VH_p10"] if has_p10 else []))
        dry = read_bands(s1_dry_reference_file(cfg), ["VV", "VH"])
        radar = {"vv": s1["VV"], "vh": s1["VH"], **radar_features(s1["VV"], s1["VH"], dry["VV"], dry["VH"])}
        if has_p10:   # darkest moment of the month and its change against the dry season
            radar.update({"vv_p10": s1["VV_p10"], "vh_p10": s1["VH_p10"],
                          "dvv_p10": s1["VV_p10"] - dry["VV"], "dvh_p10": s1["VH_p10"] - dry["VH"]})
        out.append(write_raster(folder / f"sentinel1_features_{name}_{month}_10m.tif", radar,
                                load_grid(cfg, 10), dtype="int16", scale=100, tags={"source": file.name}))
    return out


def s1_change_series(cfg: dict, drop_db: float = -3.0, water_db: float = -16.0) -> pd.DataFrame:
    """Radar change indicators for every Sentinel-1 month, inside the modelling domain.

    The whole image gets brighter or darker from month to month for reasons that are
    not floods: wet or dry soil, and the mix of the two orbits (relative orbits 145 and
    72, about 10 degrees apart in incidence angle) that make up each monthly composite.
    That common shift is measured on ground that cannot flood (never water in the JRC
    record and HAND above the low-ground limit) and removed:

    s1_offset_vv, s1_offset_vh  median change against the dry reference on that stable ground (dB)
    s1_darker_km2     area where VV, after removing the offset, dropped by `drop_db` or more
    s1_new_water_km2  the same, only where VV is also as dark as open water (`water_db` or
                      lower) and the place is not permanent water
    """
    p = cfg["processing"]
    stack = read_bands(static_stack_file(cfg), ["hand", "jrc_occurrence"])
    domain30 = study_masks(cfg)["study"] & np.isfinite(stack["hand"])
    up = lambda mask: np.repeat(np.repeat(mask, 3, axis=0), 3, axis=1)
    domain = up(domain30)
    stable = up(domain30 & (stack["jrc_occurrence"] == 0) & (stack["hand"] > p["low_hand_m"]))
    not_permanent = up(stack["jrc_occurrence"] < p["permanent_water_occurrence"])
    dry = read_bands(s1_dry_reference_file(cfg), ["VV", "VH"])
    rows = []
    for month in available_months(cfg, "sentinel1"):
        s1 = read_bands(monthly_file(cfg, "sentinel1", month), ["VV", "VH"])
        dvv, dvh = s1["VV"] - dry["VV"], s1["VH"] - dry["VH"]
        valid = domain & np.isfinite(dvv)
        offset_vv, offset_vh = float(np.nanmedian(dvv[stable])), float(np.nanmedian(dvh[stable]))
        darker = valid & ((dvv - offset_vv) <= drop_db)
        rows.append({"month": month, "s1_observed_fraction": valid.sum() / domain.sum(),
                     "s1_offset_vv": offset_vv, "s1_offset_vh": offset_vh,
                     "s1_darker_km2": darker.sum() * 100 / 1e6,
                     "s1_new_water_km2": (darker & (s1["VV"] <= water_db) & not_permanent).sum() * 100 / 1e6})
    return pd.DataFrame(rows).set_index("month")
