"""Monthly composite recipes (Earth Engine).

Each `*_builder` returns a function `builder(start, end)` (ISO dates, end
exclusive) that gives `(ee.Image, ee.Dictionary)` for `gee.download_monthly`.
Every composite carries an `n_obs` band: the number of clean observations per
pixel (reliability pillar 5 of the project plan).
"""

from __future__ import annotations

import ee

OPTICAL = ["blue", "green", "red", "nir", "swir1", "swir2"]

# -----------------------------------------------------------------------------
# Landsat 5/7/8/9 Collection 2 Level-2
# -----------------------------------------------------------------------------

_LANDSAT_BANDS = {
    "LT05": ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"],
    "LE07": ["SR_B1", "SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B7"],
    "LC08": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
    "LC09": ["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6", "SR_B7"],
}
# Roy et al. (2016), Remote Sensing of Environment 185: OLI = intercept + slope * ETM+
_ROY_SLOPES = [0.8474, 0.8483, 0.9047, 0.8462, 0.8937, 0.9071]
_ROY_INTERCEPTS = [0.0003, 0.0088, 0.0061, 0.0412, 0.0254, 0.0172]


def _landsat_prepare(sensor: str, harmonize: bool):
    def prepare(img):
        qa = img.select("QA_PIXEL")
        # bits: 0 fill, 1 dilated cloud, 2 cirrus, 3 cloud, 4 cloud shadow
        clear = qa.bitwiseAnd(0b11111).eq(0)
        unsaturated = img.select("QA_RADSAT").eq(0)
        sr = img.select(_LANDSAT_BANDS[sensor], OPTICAL).multiply(0.0000275).add(-0.2)
        if harmonize and sensor in ("LT05", "LE07"):
            sr = sr.multiply(ee.Image.constant(_ROY_SLOPES)).add(ee.Image.constant(_ROY_INTERCEPTS))
            sr = sr.rename(OPTICAL)
        # no lower bound on reflectance: water is often slightly negative in SWIR
        # one pixel type for all sensors, otherwise mixed-sensor months cannot be merged
        sr = sr.updateMask(clear).updateMask(unsaturated).toFloat()
        return ee.Image(sr.copyProperties(img, ["system:time_start", "SPACECRAFT_ID"]))

    return prepare


def landsat_collection(cfg: dict, region: ee.Geometry) -> ee.ImageCollection:
    """Cloud-masked, scaled (0-1 reflectance) Landsat 5/7/8/9 merged collection."""
    ds = cfg["datasets"]["landsat"]
    merged = None
    for sensor, spec in ds["sensors"].items():
        col = ee.ImageCollection(spec["id"]).filterBounds(region)
        end = spec["end"] or "2100-01-01"
        col = col.filterDate(spec["start"], ee.Date(end).advance(1, "day"))
        col = col.map(_landsat_prepare(sensor, ds["harmonize_tm_etm_to_oli"]))
        merged = col if merged is None else merged.merge(col)
    return merged


def landsat_builder(cfg: dict, region: ee.Geometry):
    collection = landsat_collection(cfg, region)

    def builder(start, end):
        col = collection.filterDate(start, end)
        n_obs = col.select("green").count().unmask(0).rename("n_obs")
        info = ee.Dictionary({"n_images": col.size(),
                              "sensors": col.aggregate_histogram("SPACECRAFT_ID")})
        return col.median().addBands(n_obs), info

    return builder


# -----------------------------------------------------------------------------
# Sentinel-1 GRD IW
# -----------------------------------------------------------------------------

def sentinel1_collection(cfg: dict, region: ee.Geometry, orbit_pass: str | None = None) -> ee.ImageCollection:
    col = (ee.ImageCollection(cfg["datasets"]["sentinel1"]["id"])
           .filterBounds(region)
           .filter(ee.Filter.eq("instrumentMode", "IW"))
           .filter(ee.Filter.eq("resolution_meters", 10))
           .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VV"))
           .filter(ee.Filter.listContains("transmitterReceiverPolarisation", "VH")))
    if orbit_pass:
        col = col.filter(ee.Filter.eq("orbitProperties_pass", orbit_pass))
    return col


def sentinel1_builder(cfg: dict, region: ee.Geometry, orbit_pass: str):
    """Monthly median and 10th percentile of VV and VH (dB), mean incidence angle, n_obs. Fixed orbit pass."""
    collection = sentinel1_collection(cfg, region, orbit_pass)

    def builder(start, end):
        col = collection.filterDate(start, end)
        low = col.select(["VV", "VH"]).reduce(ee.Reducer.percentile([10])).rename(["VV_p10", "VH_p10"])
        image = (col.select(["VV", "VH"]).median()
                 .addBands(col.select("angle").mean())
                 .addBands(low)
                 .addBands(col.select("VV").count().unmask(0).rename("n_obs")))
        info = ee.Dictionary({"n_images": col.size(), "orbit_pass": orbit_pass,
                              "relative_orbits": col.aggregate_histogram("relativeOrbitNumber_start")})
        return image, info

    return builder


# -----------------------------------------------------------------------------
# Sentinel-2 L2A
# -----------------------------------------------------------------------------

def sentinel2_builder(cfg: dict, region: ee.Geometry):
    """Monthly median surface reflectance (0-1) after the SCL cloud/shadow mask."""
    ds = cfg["datasets"]["sentinel2"]
    src, names = list(ds["bands"].keys()), list(ds["bands"].values())

    def prepare(img):
        scl = img.select("SCL")
        clear = scl.remap(ds["scl_mask"], [0] * len(ds["scl_mask"]), 1)
        return ee.Image(img.select(src, names).multiply(0.0001).updateMask(clear)
                        .copyProperties(img, ["system:time_start"]))

    collection = ee.ImageCollection(ds["id"]).filterBounds(region).map(prepare)

    def builder(start, end):
        col = collection.filterDate(start, end)
        n_obs = col.select("green").count().unmask(0).rename("n_obs")
        return col.median().addBands(n_obs), ee.Dictionary({"n_images": col.size()})

    return builder


# -----------------------------------------------------------------------------
# JRC Global Surface Water - monthly history (labels 2006-2021)
# -----------------------------------------------------------------------------

def jrc_monthly_builder(cfg: dict):
    """Band `water`: 0 = no observation, 1 = not water, 2 = water."""
    collection = ee.ImageCollection(cfg["datasets"]["jrc_monthly"]["id"])

    def builder(start, end):
        col = collection.filterDate(start, end)
        return col.max().select("water"), ee.Dictionary({"n_images": col.size()})

    return builder


# -----------------------------------------------------------------------------
# Dynamic World
# -----------------------------------------------------------------------------

def dynamic_world_builder(cfg: dict, region: ee.Geometry):
    """Monthly mean probability of `water` and `flooded_vegetation`, modal class, n_obs."""
    collection = ee.ImageCollection(cfg["datasets"]["dynamic_world"]["id"]).filterBounds(region)

    def builder(start, end):
        col = collection.filterDate(start, end)
        image = (col.select(["water", "flooded_vegetation"]).mean()
                 .addBands(col.select("label").mode().rename("label_mode"))
                 .addBands(col.select("label").count().unmask(0).rename("n_obs")))
        return image, ee.Dictionary({"n_images": col.size()})

    return builder
