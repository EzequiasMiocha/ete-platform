"""Earth Engine download helpers.

Rasters are pulled straight to disk with `ee.data.computePixels` on an explicit
grid, split into tiles that respect the request size limit. No Google Drive
export step is needed and downloads can be interrupted and resumed: existing
files are skipped and partial files never keep the final name.
"""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timedelta, timezone
from pathlib import Path

import ee
import numpy as np
import pandas as pd
import rasterio
import requests
from rasterio.io import MemoryFile
from rasterio.windows import Window
from tqdm.auto import tqdm

from .config import log_manifest, period_end
from .grid import Grid, native_latlon_grid

HIGH_VOLUME_URL = "https://earthengine-highvolume.googleapis.com"
NODATA = {"float32": -9999.0, "int16": -9999, "uint8": 255, "uint16": 65535}
UNSCALED_BANDS = ("n_obs", "label_mode")


# -----------------------------------------------------------------------------
# Session
# -----------------------------------------------------------------------------

def init(cfg: dict) -> None:
    """Initialise Earth Engine (run `earthengine authenticate` once beforehand)."""
    project = cfg["gee"]["project"]
    if not project:
        raise RuntimeError("Set EE_PROJECT in the .env file (Google Cloud project with Earth Engine).")
    url = HIGH_VOLUME_URL if cfg["gee"].get("high_volume", True) else None
    try:
        # a slow or busy network can make the first attempt fail: try a few times first
        retry(lambda: ee.Initialize(project=project, opt_url=url), tries=4, wait=5)
    except Exception:
        import sys
        if "ipykernel" not in sys.modules and not sys.stdin.isatty():
            raise          # unattended script: never start a browser login, just fail clearly
        ee.Authenticate()
        ee.Initialize(project=project, opt_url=url)
    # a request that gets no answer (network drop) fails after 3 minutes and is retried,
    # instead of hanging the whole download
    ee.data.setDeadline(180_000)


def ee_geometry(gdf) -> ee.Geometry:
    """GeoDataFrame (any CRS) -> ee.Geometry in EPSG:4326."""
    geom = gdf.to_crs(4326).union_all()
    return ee.Geometry(geom.__geo_interface__)


def retry(fn, tries: int = 5, wait: float = 4.0):
    """Call fn() with exponential backoff (quota and transient server errors)."""
    for attempt in range(tries):
        try:
            return fn()
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(wait * 2 ** attempt)


def describe_asset(asset_id: str) -> dict:
    """Type and date coverage of a catalogue asset (used to confirm IDs/versions)."""
    info = ee.data.getAsset(asset_id)
    out = {"id": asset_id, "type": info.get("type"), "first": None, "last": None}
    if info.get("type") == "IMAGE_COLLECTION":
        col = ee.ImageCollection(asset_id)
        rng = col.reduceColumns(ee.Reducer.minMax(), ["system:time_start"]).getInfo()
        out["first"] = pd.to_datetime(rng["min"], unit="ms").date().isoformat()
        out["last"] = pd.to_datetime(rng["max"], unit="ms").date().isoformat()
    return out


# -----------------------------------------------------------------------------
# Raster download
# -----------------------------------------------------------------------------

def _tiles(grid: Grid, n_bands: int, itemsize: int, max_mb: float):
    """Split the grid into windows whose uncompressed size fits in one request."""
    side = int((max_mb * 1e6 / (n_bands * itemsize)) ** 0.5)
    side = max(64, min(side, 4096))
    for row in range(0, grid.height, side):
        for col in range(0, grid.width, side):
            yield Window(col, row, min(side, grid.width - col), min(side, grid.height - row))


def _fetch(image: ee.Image, grid: Grid, window: Window) -> np.ndarray:
    request = {
        "expression": image,
        "fileFormat": "GEO_TIFF",
        "grid": {
            "dimensions": {"width": int(window.width), "height": int(window.height)},
            "affineTransform": {
                "scaleX": grid.res, "shearX": 0,
                "translateX": grid.x0 + window.col_off * grid.res,
                "shearY": 0, "scaleY": -grid.res,
                "translateY": grid.y0 - window.row_off * grid.res,
            },
            "crsCode": grid.crs,
        },
    }
    data = retry(lambda: ee.data.computePixels(request))
    with MemoryFile(data) as mem, mem.open() as src:
        return src.read()


def download_image(image: ee.Image, bands: list[str], grid: Grid, out_path: Path,
                   cfg: dict, dtype: str = "float32", tags: dict | None = None,
                   scale: float | dict = 1, mask: ee.Geometry | None = None,
                   fetch=_fetch) -> Path:
    """Download `image` (bands in the given order) to a compressed GeoTIFF on `grid`.

    Masked pixels are written with the nodata value of the dtype (see NODATA).

    `scale` stores values as integers: each band is multiplied by its factor and
    rounded (e.g. reflectance * 10000 as int16). The inverse factor is written to
    the GeoTIFF band scale, so `series.read_scaled` returns physical values.
    Count/class bands (UNSCALED_BANDS) are never scaled. `mask` keeps only the
    pixels inside that geometry; the rest becomes nodata.
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    nodata = NODATA[dtype]
    factors = [1 if b in UNSCALED_BANDS else (scale.get(b, 1) if isinstance(scale, dict) else scale)
               for b in bands]
    image = image.select(bands)
    if any(f != 1 for f in factors):
        image = image.multiply(ee.Image.constant(factors)).round().rename(bands)
    if dtype == "int16":
        image = image.clamp(-9998, 32767)      # keep clear of the nodata value
    if mask is not None:
        image = image.clip(mask)
    image = image.unmask(nodata, False).cast({b: dtype.replace("float32", "float") for b in bands})

    profile = dict(
        driver="GTiff", width=grid.width, height=grid.height, count=len(bands),
        dtype=dtype, crs=grid.crs, transform=grid.transform, nodata=nodata,
        compress="deflate", predictor=3 if dtype.startswith("float") else 2,
        tiled=True, blockxsize=512, blockysize=512, BIGTIFF="IF_SAFER",
    )
    windows = list(_tiles(grid, len(bands), np.dtype(dtype).itemsize, cfg["gee"]["max_tile_mb"]))
    part = out_path.with_suffix(".part.tif")
    try:
        with rasterio.open(part, "w", **profile) as dst:
            with ThreadPoolExecutor(cfg["gee"].get("workers", 4)) as pool:
                for window, data in zip(windows, pool.map(lambda w: fetch(image, grid, w), windows)):
                    dst.write(data.astype(dtype), window=window)
            for i, band in enumerate(bands, start=1):
                dst.set_band_description(i, band)
            dst.scales = [1 / f for f in factors]
            dst.update_tags(**{k: str(v) for k, v in (tags or {}).items()},
                            downloaded_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"))
    except BaseException:
        part.unlink(missing_ok=True)       # never leave a half-written file behind
        raise
    part.replace(out_path)
    return out_path


def month_starts(start: str, end: str) -> list[pd.Timestamp]:
    return list(pd.date_range(pd.Timestamp(start).replace(day=1), end, freq="MS"))


def download_monthly(cfg: dict, dataset: str, source_id: str, builder, bands: list[str],
                     grid: Grid, out_dir: Path, start: str, end: str | None = None,
                     dtype: str = "float32", scale: float | dict = 1,
                     mask: ee.Geometry | None = None) -> pd.DataFrame:
    """Download one composite per month into out_dir/<year>/.

    `scale` and `mask` are passed to `download_image`.

    `builder(start, end)` receives ISO dates (end exclusive) and returns
    (ee.Image, ee.Dictionary); the dictionary must contain `n_images`.
    Months without any source image are logged as `absent` and no file is
    written: missing data is never filled in.
    """
    aoi_name = cfg["project"]["aoi_name"]
    rows = []
    months = month_starts(start, period_end(cfg, end))
    for month in tqdm(months, desc=dataset):
        label = month.strftime("%Y-%m")
        out = Path(out_dir) / str(month.year) / f"{dataset}_{aoi_name}_{label}_{grid.res:g}m.tif"
        if out.exists():
            rows.append({"period": label, "status": "exists", "file": out.name})
            continue
        nxt = (month + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d")
        image, info = builder(month.strftime("%Y-%m-%d"), nxt)
        info = retry(info.getInfo)
        row = dict(dataset=dataset, source_id=source_id, period=label, n_images=info["n_images"],
                   bands=" ".join(bands), crs=grid.crs, resolution=grid.res,
                   note="; ".join(f"{k}={v}" for k, v in info.items() if k != "n_images"))
        if info["n_images"] == 0:
            log_manifest(cfg, status="absent", **row)
            rows.append({"period": label, "status": "absent", "file": ""})
            continue
        try:
            download_image(image, bands, grid, out, cfg, dtype=dtype, scale=scale, mask=mask,
                           tags={"dataset": dataset, "source_id": source_id, "period": label, **info})
            log_manifest(cfg, status="downloaded", file=out, **row)
            rows.append({"period": label, "status": "downloaded", "file": out.name, **info})
        except Exception as err:  # keep going; the month is retried on the next run
            log_manifest(cfg, status="failed", **{**row, "note": repr(err)[:300]})
            rows.append({"period": label, "status": "failed", "file": "", "error": repr(err)[:200]})
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Coarse daily series (CHIRPS, IMERG, ERA5-Land, SMAP) -> NetCDF
# -----------------------------------------------------------------------------

def collection_grid(collection: ee.ImageCollection, band: str, bounds, fallback_res: float) -> Grid:
    """Native lat/lon grid of a collection over `bounds` (west, south, east, north)."""
    proj = collection.first().select(band).projection().getInfo()
    if proj.get("crs") == "EPSG:4326":
        return native_latlon_grid(proj["transform"], bounds)
    return native_latlon_grid([fallback_res, 0, -180, 0, -fallback_res, 90], bounds)


def available_days(collection: ee.ImageCollection, start: str, end: str) -> list[datetime]:
    """Distinct UTC days with at least one image in [start, end)."""
    times = retry(collection.filterDate(start, end).aggregate_array("system:time_start").getInfo)
    days = {datetime.fromtimestamp(t / 1000, tz=timezone.utc).date() for t in times}
    return sorted(days)


def daily_stack(collection: ee.ImageCollection, band: str, days, multiply: float = 1.0) -> ee.Image:
    """One band per day (daily mean of the source images, times `multiply`)."""
    images = []
    for day in days:
        nxt = day + timedelta(days=1)
        daily = collection.filterDate(day.isoformat(), nxt.isoformat()).select(band).mean()
        images.append(daily.multiply(multiply).rename(day.strftime("d%Y%m%d")))
    return ee.Image.cat(images)


def download_daily_netcdf(cfg: dict, dataset: str, source_id: str, band: str, grid: Grid,
                          out_dir: Path, start: str, end: str | None = None,
                          freq: str = "YS", multiply: float = 1.0, units: str = "",
                          var_name: str | None = None) -> pd.DataFrame:
    """Download a daily series on a lat/lon grid, one NetCDF per year (freq="YS")
    or per month (freq="MS"). Sub-daily sources are averaged per UTC day and
    scaled by `multiply` (e.g. mm/hr * 24 = mm/day)."""
    import xarray as xr

    collection = ee.ImageCollection(source_id)
    var_name = var_name or band
    aoi_name = cfg["project"]["aoi_name"]
    end = period_end(cfg, end)
    last = pd.Timestamp(end) + pd.Timedelta(days=1)
    first = pd.Timestamp(start)
    anchor = first.replace(day=1) if freq == "MS" else first.replace(month=1, day=1)
    rows = []
    for chunk in tqdm(list(pd.date_range(anchor, end, freq=freq)), desc=f"{dataset}:{var_name}"):
        nxt = min(chunk + pd.tseries.frequencies.to_offset(freq), last)
        chunk_start = max(chunk, first)
        label = chunk.strftime("%Y" if freq == "YS" else "%Y-%m")
        complete = nxt == chunk + pd.tseries.frequencies.to_offset(freq)
        out = Path(out_dir) / var_name / f"{dataset}_{var_name}_{aoi_name}_{label}.nc"
        done = False
        if out.exists():
            with xr.open_dataset(out) as existing:
                done = existing.attrs.get("complete") == "yes"
        if done:
            rows.append({"period": label, "status": "exists", "n_days": None})
            continue
        days = available_days(collection.select(band), chunk_start.strftime("%Y-%m-%d"), nxt.strftime("%Y-%m-%d"))
        row = dict(dataset=dataset, source_id=source_id, period=label, n_images=len(days),
                   bands=var_name, crs=grid.crs, resolution=grid.res)
        if not days:
            log_manifest(cfg, status="absent", **row)
            rows.append({"period": label, "status": "absent", "n_days": 0})
            continue
        names = [d.strftime("d%Y%m%d") for d in days]
        image = daily_stack(collection, band, days, multiply).unmask(NODATA["float32"], False).toFloat()
        data = _fetch(image.select(names), grid, Window(0, 0, grid.width, grid.height))
        data = np.where(data == NODATA["float32"], np.nan, data).astype("float32")
        left, bottom, right, top = grid.bounds
        da = xr.DataArray(
            data, dims=("time", "lat", "lon"), name=var_name,
            coords={"time": pd.to_datetime([d.isoformat() for d in days]),
                    "lat": top - grid.res * (np.arange(grid.height) + 0.5),
                    "lon": left + grid.res * (np.arange(grid.width) + 0.5)},
            attrs={"units": units, "source_id": source_id, "source_band": band},
        )
        ds = da.to_dataset()
        # an unfinished year/month is rewritten on the next run until it is complete
        ds.attrs = {"complete": "yes" if complete else "no", "crs": "EPSG:4326",
                    "downloaded_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}
        out.parent.mkdir(parents=True, exist_ok=True)
        tmp = out.with_suffix(".part.nc")
        ds.to_netcdf(tmp, encoding={var_name: {"zlib": True, "complevel": 4}})
        tmp.replace(out)
        log_manifest(cfg, status="downloaded", file=out, **row)
        rows.append({"period": label, "status": "downloaded", "n_days": len(days)})
    return pd.DataFrame(rows)


# -----------------------------------------------------------------------------
# Vectors
# -----------------------------------------------------------------------------

def download_vector(fc: ee.FeatureCollection, out_path: Path, selectors: list[str] | None = None,
                    timeout: int = 600) -> Path:
    """Download a FeatureCollection as GeoJSON."""
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    url = retry(lambda: fc.getDownloadURL(filetype="geojson", selectors=selectors, filename=out_path.stem))
    response = requests.get(url, timeout=timeout)
    response.raise_for_status()
    out_path.write_bytes(response.content)
    return out_path


def download_static(cfg: dict, name: str, source_id: str, image: ee.Image, bands: list[str],
                    grid: Grid, folder_key: str, dtype: str = "float32") -> Path:
    """Download a single (non time-varying) layer as <name>_<aoi>_<res>m.tif."""
    from .config import path

    res = f"{grid.res:g}m" if grid.crs != "EPSG:4326" else "native"
    out = path(cfg, folder_key, f"{name}_{cfg['project']['aoi_name']}_{res}.tif")
    if out.exists():
        print("exists    ", out.name)
        return out
    download_image(image, bands, grid, out, cfg, dtype=dtype,
                   tags={"dataset": name, "source_id": source_id})
    log_manifest(cfg, dataset=name, source_id=source_id, period="static", status="downloaded",
                 n_images=1, file=out, bands=" ".join(bands), crs=grid.crs, resolution=grid.res)
    print("downloaded", out.name)
    return out


def download_vector_tiled(fc: ee.FeatureCollection, bounds, out_dir: Path, keep=None,
                          max_depth: int = 4, name: str = "tile", timeout: int = 120) -> list[Path]:
    """Download a large FeatureCollection as GeoJSON tiles over `bounds` (W, S, E, N).

    Big tables make single requests fail with server errors, so a tile whose
    request fails twice is split into four smaller ones (up to `max_depth`
    times). `keep(west, south, east, north)` may return False to skip a tile,
    e.g. tiles outside the study polygon. Existing tiles are not requested again.
    """
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    files: list[Path] = []

    def visit(box, key, depth):
        west, south, east, north = box
        if keep is not None and not keep(*box):
            return
        tile = out_dir / f"{name}_{key}.geojson"
        split_marker = out_dir / f"{name}_{key}.split"
        if tile.exists():
            files.append(tile)
            return
        if not split_marker.exists():
            try:
                cell = ee.Geometry.Rectangle([west, south, east, north])
                retry(lambda: download_vector(fc.filterBounds(cell), tile, timeout=timeout), tries=2, wait=5)
                files.append(tile)
                return
            except Exception:
                if depth >= max_depth:
                    raise
                split_marker.touch()        # remember the split, so a re-run does not retry the big tile
        mx, my = (west + east) / 2, (south + north) / 2
        quads = [(west, south, mx, my), (mx, south, east, my), (west, my, mx, north), (mx, my, east, north)]
        for q, child_box in zip("0123", quads):
            visit(child_box, f"{key}{q}", depth + 1)

    visit(tuple(bounds), "r", 0)
    return files
