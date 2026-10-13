"""Reading and summarising the coarse daily series (NetCDF) and quick raster plots."""

from __future__ import annotations

from pathlib import Path

import numpy as np

from .config import path


def open_series(cfg: dict, folder_key: str, var_name: str):
    """Concatenate all NetCDF files of one variable into a (time, lat, lon) DataArray."""
    import xarray as xr

    files = sorted(path(cfg, folder_key, var_name).glob("*.nc"))
    if not files:
        raise FileNotFoundError(f"no NetCDF files for {var_name} in {cfg['paths'][folder_key]}")
    parts = [xr.open_dataset(f)[var_name].load() for f in files]
    return xr.concat(parts, dim="time").sortby("time")


def area_mean(da, gdf):
    """Daily mean over the cells touched by the polygons of `gdf` (pandas Series)."""
    from rasterio.features import geometry_mask
    from rasterio.transform import from_origin

    res = float(abs(da.lon[1] - da.lon[0]))
    transform = from_origin(float(da.lon[0]) - res / 2, float(da.lat[0]) + res / 2, res, res)
    inside = geometry_mask(gdf.to_crs(4326).geometry, out_shape=(da.sizes["lat"], da.sizes["lon"]),
                           transform=transform, invert=True, all_touched=True)
    return da.where(inside).mean(dim=("lat", "lon")).to_series()


def missing_days(da) -> list:
    """Calendar days between the first and last time step that have no data."""
    import pandas as pd

    expected = pd.date_range(da.time.values[0], da.time.values[-1], freq="D")
    return list(expected.difference(pd.DatetimeIndex(da.time.values)))


def read_scaled(file: Path, bands: list[str] | None = None):
    """Read a GeoTIFF in physical units: (masked float32 array [band, row, col], band names).

    Integer rasters store e.g. reflectance * 10000; the factor kept in the file is
    applied here. Always read project rasters through this function.
    """
    import rasterio

    with rasterio.open(file) as src:
        names = list(src.descriptions)
        indexes = [names.index(b) + 1 for b in bands] if bands else list(range(1, src.count + 1))
        data = np.ma.stack([src.read(i, masked=True).astype("float32") * src.scales[i - 1] for i in indexes])
    return data, [names[i - 1] for i in indexes]


def show_raster(file: Path, band: int | str = 1, ax=None, **imshow_kwargs):
    """Plot one band of a GeoTIFF in physical units (nodata hidden). `band` is an index or a name."""
    import matplotlib.pyplot as plt
    import rasterio
    from rasterio.plot import plotting_extent

    with rasterio.open(file) as src:
        index = src.descriptions.index(band) + 1 if isinstance(band, str) else band
        data = src.read(index, masked=True).astype("float32") * src.scales[index - 1]
        extent = plotting_extent(src)
        name = src.descriptions[index - 1] or f"band {index}"
    ax = ax or plt.subplots(figsize=(6, 7))[1]
    im = ax.imshow(np.ma.filled(data, np.nan), extent=extent, **imshow_kwargs)
    ax.set_title(f"{Path(file).name}\n{name}", fontsize=9)
    plt.colorbar(im, ax=ax, shrink=0.7)
    return ax


def monthly_inventory(folder: Path):
    """Table (period, file, size_mb) of the monthly GeoTIFFs under `folder`."""
    import pandas as pd

    rows = []
    for f in sorted(Path(folder).rglob("*.tif")):
        if ".part" in f.name:
            continue
        period = next((p for p in f.stem.split("_") if len(p) == 7 and p[4] == "-"), None)
        rows.append({"period": period, "file": f.name, "size_mb": round(f.stat().st_size / 1e6, 2)})
    return pd.DataFrame(rows, columns=["period", "file", "size_mb"])
