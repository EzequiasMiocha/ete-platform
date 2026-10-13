"""Pixel grids and the study-area files.

Everything exported from Earth Engine is requested on an explicit grid
(CRS + origin + pixel size + dimensions), so all rasters of the project are
pixel-aligned from the moment they are downloaded.
"""

from __future__ import annotations

import json
import math
from dataclasses import asdict, dataclass

from .config import path


@dataclass(frozen=True)
class Grid:
    """North-up pixel grid. (x0, y0) is the outer corner of the top-left pixel."""

    crs: str
    res: float
    x0: float
    y0: float
    width: int
    height: int

    @property
    def bounds(self) -> tuple[float, float, float, float]:
        """(left, bottom, right, top) in grid CRS units."""
        return (self.x0, self.y0 - self.height * self.res,
                self.x0 + self.width * self.res, self.y0)

    @property
    def transform(self):
        from rasterio.transform import Affine

        return Affine(self.res, 0, self.x0, 0, -self.res, self.y0)

    def with_res(self, res: float) -> "Grid":
        """Same extent at another pixel size (the extent must be a multiple of it)."""
        left, bottom, right, top = self.bounds
        width, height = (right - left) / res, (top - bottom) / res
        if abs(width - round(width)) > 1e-6 or abs(height - round(height)) > 1e-6:
            raise ValueError(f"extent is not a multiple of {res}")
        return Grid(self.crs, res, self.x0, self.y0, round(width), round(height))


def snapped_grid(bounds, crs: str, res: float, snap: float | None = None) -> Grid:
    """Grid covering `bounds` (left, bottom, right, top), expanded outwards so its
    edges fall on multiples of `snap` (default: the pixel size)."""
    snap = snap or res
    left, bottom, right, top = bounds
    x0 = math.floor(left / snap + 1e-9) * snap
    y0 = math.ceil(top / snap - 1e-9) * snap
    x1 = math.ceil(right / snap - 1e-9) * snap
    y1 = math.floor(bottom / snap + 1e-9) * snap
    return Grid(crs, res, x0, y0, round((x1 - x0) / res), round((y0 - y1) / res))


def native_latlon_grid(transform: list[float], bounds) -> Grid:
    """Grid in EPSG:4326 that follows the native pixels of a coarse dataset.

    `transform` is the Earth Engine projection transform [sx, 0, tx, 0, sy, ty];
    `bounds` is (west, south, east, north). Pixels are not resampled.
    """
    sx, _, tx, _, sy, ty = transform
    res = abs(sx)
    west, south, east, north = bounds
    col0 = math.floor((west - tx) / res + 1e-9)
    col1 = math.ceil((east - tx) / res - 1e-9)
    row0 = math.floor((ty - north) / abs(sy) + 1e-9)
    row1 = math.ceil((ty - south) / abs(sy) - 1e-9)
    return Grid("EPSG:4326", res, tx + col0 * res, ty - row0 * abs(sy),
                col1 - col0, row1 - row0)


# -----------------------------------------------------------------------------
# Study-area files written by notebook 01
# -----------------------------------------------------------------------------

AOI_FILES = {
    "district": "marracuene_district.geojson",
    "basin": "incomati_basin.geojson",
    "subbasin": "incomati_lower_subbasin.geojson",
    "aoi": "aoi.geojson",                  # imagery AOI (task S1-03 deliverable)
    "aoi_climate": "aoi_climate.geojson",  # basin bounding box for coarse data
    "grid": "grid.json",
}


def save_grid(cfg: dict, grid: Grid) -> None:
    with open(path(cfg, "aoi", AOI_FILES["grid"]), "w", encoding="utf-8") as f:
        json.dump(asdict(grid), f, indent=2)


def load_grid(cfg: dict, res: float | None = None) -> Grid:
    """Project grid (30 m by default); pass res=10 for the Sentinel layer."""
    file = path(cfg, "aoi", AOI_FILES["grid"])
    if not file.exists():
        raise FileNotFoundError("Run notebooks/01_study_area_aoi.ipynb first (grid.json missing).")
    with open(file, encoding="utf-8") as f:
        grid = Grid(**json.load(f))
    return grid if res in (None, grid.res) else grid.with_res(res)


def imagery_mask(cfg: dict):
    """District + buffer polygon (EPSG:4326). Monthly imagery outside it is stored as
    nodata, because the rectangular AOI also covers sea and land that is never used."""
    district = load_aoi(cfg, "district").to_crs(cfg["grid"]["crs"])
    return district.buffer(cfg["aoi"]["imagery_buffer_km"] * 1000).to_crs(4326).to_frame("geometry")


def load_aoi(cfg: dict, name: str = "aoi"):
    """Read one of the study-area layers as a GeoDataFrame (EPSG:4326)."""
    import geopandas as gpd

    file = path(cfg, "aoi", AOI_FILES[name])
    if not file.exists():
        raise FileNotFoundError(f"Run notebooks/01_study_area_aoi.ipynb first ({file.name} missing).")
    return gpd.read_file(file)
