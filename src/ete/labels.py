"""Reference labels from public flood maps (Copernicus EMS Rapid Mapping).

EMS delineation products are flood extents drawn by an operational service from
satellite images, often from sensors this project does not use (COSMO-SkyMed,
ICEYE). They are therefore an independent reference for testing the models.
"""

from __future__ import annotations

from pathlib import Path

import pandas as pd

from .config import path
from .grid import imagery_mask

SCHEMA = ["class", "month", "event_id", "source", "author", "confidence", "notes"]


def ems_labels_file(cfg: dict) -> Path:
    return path(cfg, "ems_unosat", "ems_labels.gpkg")


def _layer(folder: Path, name: str):
    import geopandas as gpd

    files = sorted(Path(folder).glob(f"*_{name}_*.shp"))
    return gpd.read_file(files[0]) if files else None


def ems_reference_polygons(cfg: dict, product_folders: list[Path], month: str, event_id: str,
                           edge_m: float = 30, margin_m: float = 100):
    """Turn EMS delineation products of one event into `water` / `non_water` polygons.

    water      flooded at any of the mapped dates (union of the `observedEvent` layers),
               shrunk by `edge_m` so the uncertain edge is left out
    non_water  inside the area EMS analysed, at least `margin_m` away from any observed
               flood and from the modelled maximum flood extent

    The band in between is left unlabelled on purpose: radar can miss water under
    vegetation or between buildings, so "not mapped as flooded" is only trusted away
    from the flood.
    """
    import geopandas as gpd
    from shapely.ops import unary_union

    crs = cfg["grid"]["crs"]
    study = imagery_mask(cfg).to_crs(crs).union_all()
    flooded, possible, analysed, sensors = [], [], [], []
    for folder in product_folders:
        observed, aoi = _layer(folder, "observedEventA"), _layer(folder, "areaOfInterestA")
        if observed is None or aoi is None:
            continue
        flooded.append(observed.to_crs(crs).union_all())
        analysed.append(aoi.to_crs(crs).union_all())
        maximum = _layer(folder, "maximumFloodExtentA")
        if maximum is not None:
            possible.append(maximum.to_crs(crs).union_all())
        sensors.append(Path(folder).name)
    flood = unary_union(flooded).intersection(study)
    area = unary_union(analysed).intersection(study)
    water = flood.buffer(-edge_m)
    non_water = area.difference(unary_union([flood, *possible]).buffer(margin_m))
    rows = [("water", water), ("non_water", non_water)]
    out = gpd.GeoDataFrame(
        {"class": [r[0] for r in rows], "month": month, "event_id": event_id,
         "source": "Copernicus EMS " + event_id + ": " + ", ".join(sensors), "author": "Copernicus EMS Rapid Mapping",
         "confidence": "alta", "notes": f"water shrunk {edge_m:g} m; non_water at least {margin_m:g} m from any mapped or modelled flood"},
        geometry=[r[1] for r in rows], crs=crs).explode(index_parts=False, ignore_index=True)
    return out[out.geometry.area > 900].reset_index(drop=True)


def write_ems_labels(cfg: dict, polygons) -> Path:
    """Add (or replace, for the same event and month) EMS reference polygons in ems_labels.gpkg."""
    import geopandas as gpd

    file = ems_labels_file(cfg)
    if file.exists():
        old = gpd.read_file(file, layer="amostras")
        keys = set(zip(polygons["event_id"], polygons["month"]))
        old = old[[k not in keys for k in zip(old["event_id"], old["month"])]]
        polygons = pd.concat([old, polygons], ignore_index=True)
    gpd.GeoDataFrame(polygons, crs=cfg["grid"]["crs"]).to_file(file, layer="amostras", driver="GPKG")
    return file
