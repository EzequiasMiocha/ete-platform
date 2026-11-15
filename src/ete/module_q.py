"""Module Q: water quality of the Incomati per river section, from the border to the mouth.

The plan asks for the river split into 5 to 10 sections (border -> mouth), a pure-water mask,
20 years of optical parameters per section and month, their normal values, anomalies and trends,
and a model of the turbidity expected from rain and river flow.

This file holds the sections and the extraction of the per-image values in Earth Engine.
The analysis is in `module_q_analysis.py`.

Sections: the main stem is traced in the HydroSHEDS river network from the outlet upstream,
always following the branch with the largest upstream area, until it leaves Mozambique. It is
cut into pieces of equal length. The river network stops before the real estuary, so one more
section is added from the estuary reaches measured since week 3 (notebook 34).
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import path

N_LINE_SECTIONS = 8
CORRIDOR_M = 2500              # the water mask is searched this far on each side of the river line
ANCHOR_TOWNS = ["Ressano Garcia", "Moamba", "Sabié", "Magude", "Xinavane", "Manhiça", "Marracuene"]
ESTUARY_NORTH = -25.769        # latitude where the river network ends; south of it is the estuary section


def trace_main_stem(cfg: dict):
    """Segments of the Incomati main stem inside Mozambique, ordered from the outlet upstream."""
    import geopandas as gpd
    from shapely.geometry import Point

    rivers = gpd.read_file(path(cfg, "static_hydrography", "rivers_incomati.geojson", mkdir=False))
    mozambique = rivers[rivers["COUNTRY"] == "Mozambique"]
    near_mouth = mozambique.loc[mozambique.distance(Point(32.722, -25.865)).nsmallest(5).index]
    current = near_mouth.sort_values("UPLAND_SKM", ascending=False).iloc[0]
    while (rivers["NOID"] == current["NDOID"]).any():
        current = rivers[rivers["NOID"] == current["NDOID"]].iloc[0]
    chain = [current]
    while True:
        upstream = rivers[rivers["NDOID"] == chain[-1]["NOID"]]
        if upstream.empty or upstream.sort_values("UPLAND_SKM", ascending=False).iloc[0]["COUNTRY"] != "Mozambique":
            break
        chain.append(upstream.sort_values("UPLAND_SKM", ascending=False).iloc[0])
    return gpd.GeoDataFrame(chain, crs=rivers.crs)


def _place_names(cfg: dict):
    import geopandas as gpd

    cols = ["geonameid", "name", "asciiname", "alternatenames", "lat", "lon", "fclass", "fcode", "country", "cc2",
            "adm1", "adm2", "adm3", "adm4", "pop", "elev", "dem", "tz", "mod"]
    gn = pd.read_csv(path(cfg, "places", "MZ.txt", mkdir=False), sep="\t", names=cols, dtype=str, keep_default_na=False)
    gn = gn[gn["fclass"] == "P"]
    return gpd.GeoDataFrame({"name": gn["name"], "pop": pd.to_numeric(gn["pop"], errors="coerce").fillna(0)},
                            geometry=gpd.points_from_xy(gn["lon"].astype(float), gn["lat"].astype(float)), crs=4326)


def build_sections(cfg: dict):
    """The river sections of Module Q, numbered from the border (Q1) to the mouth.

    Writes `trocos_rio.gpkg` with two layers: `linhas` (the river line of each section) and
    `corredores` (the area in which the water of that section is looked for), and returns the
    corridors (EPSG:4326). Columns: troco, nome, km_desde_fronteira_inicio/_fim, comprimento_km,
    lugar_proximo (largest named place within 10 km of the middle of the section, GeoNames;
    not validated locally)."""
    import geopandas as gpd
    from shapely.geometry import box
    from shapely.ops import linemerge, substring, unary_union

    from .water_quality import reach_polygons

    crs = cfg["grid"]["crs"]
    stem = trace_main_stem(cfg).to_crs(crs)
    line = linemerge(unary_union(list(stem.geometry)))
    if line.geom_type != "LineString":                       # keep the longest piece if the merge left gaps
        line = max(line.geoms, key=lambda g: g.length)
    mouth_xy = stem.geometry.iloc[0].centroid
    if line.project(mouth_xy) < line.length / 2:             # make the line run border -> mouth
        line = substring(line, line.length, 0)
    step = line.length / N_LINE_SECTIONS
    places = _place_names(cfg).to_crs(crs)
    rows = []
    for i in range(N_LINE_SECTIONS):
        piece = substring(line, i * step, (i + 1) * step)
        rows.append({"numero": i + 1, "km_desde_fronteira_inicio": round(i * step / 1000, 1), "km_desde_fronteira_fim": round((i + 1) * step / 1000, 1),
                     "comprimento_km": round(step / 1000, 1), "line": piece, "geometry": piece.buffer(CORRIDOR_M, cap_style="flat")})
    # the estuary: the reaches of notebook 34 south of where the river network ends
    reaches = reach_polygons(cfg)
    estuary = unary_union(list(reaches.geometry)).intersection(box(32.0, -26.5, 33.5, ESTUARY_NORTH))
    estuary = gpd.GeoSeries([estuary], crs=4326).to_crs(crs).iloc[0]
    rows.append({"numero": N_LINE_SECTIONS + 1, "km_desde_fronteira_inicio": round(line.length / 1000, 1), "km_desde_fronteira_fim": np.nan,
                 "comprimento_km": np.nan, "line": estuary.centroid, "geometry": estuary.buffer(60)})
    table = pd.DataFrame(rows)
    # name each section after the best-known town on it: the anchor towns are looked up in GeoNames
    # and given to the section whose river line passes closest (within 15 km)
    names = {}
    for town in ANCHOR_TOWNS:
        match = places[places["name"] == town]
        if match.empty:
            continue
        distance = table["line"].apply(lambda g: min(g.distance(point) for point in match.geometry))
        if distance.min() <= 15_000 and int(distance.idxmin()) not in names:
            names[int(distance.idxmin())] = town
    table["lugar_proximo"] = [names.get(i, "") for i in table.index]
    table["troco"] = [f"Q{n}" for n in table["numero"]]
    fixed = {1: "fronteira", N_LINE_SECTIONS + 1: "foz / estuário"}
    label = lambda r: " / ".join(x for x in (fixed.get(r["numero"], ""), r["lugar_proximo"]) if x) or f"km {r['km_desde_fronteira_inicio']:.0f} a {r['km_desde_fronteira_fim']:.0f}"
    table["nome"] = [f"Q{r['numero']} {label(r)}" for _, r in table.iterrows()]
    keep = ["troco", "numero", "nome", "lugar_proximo", "km_desde_fronteira_inicio", "km_desde_fronteira_fim", "comprimento_km"]
    out = path(cfg, "sections", "trocos_rio.gpkg")
    out.unlink(missing_ok=True)
    corridors = gpd.GeoDataFrame(table[keep], geometry=list(table["geometry"]), crs=crs)
    corridors.to_file(out, layer="corredores", driver="GPKG")
    gpd.GeoDataFrame(table[keep], geometry=list(table["line"]), crs=crs).to_file(out, layer="linhas", driver="GPKG")
    return corridors.to_crs(4326)


def load_sections(cfg: dict, layer: str = "corredores"):
    import geopandas as gpd

    file = path(cfg, "sections", "trocos_rio.gpkg", mkdir=False)
    if not file.exists():
        build_sections(cfg)
    return gpd.read_file(file, layer=layer).to_crs(4326)


# ----------------------------------------------------------------------------- pure water and river width
WATER_FREQUENCY = 0.6           # Dynamic World: classified as water in at least 60 % of the clear images 2019-2025
MIN_ELONGATION = 3.0            # a river piece is long and thin; rounder water bodies (lagoons, ponds) are left out
MIN_PIECE_HA = 0.3
INNER_BUFFER_M = {"sentinel2": 10, "landsat": 30}        # kept away from the banks (mixed pixels)
SENSORS = {"landsat57": 2006, "landsat89": 2013, "sentinel2": 2017}      # first year extracted


def _elongation(polygon) -> float:
    box = polygon.minimum_rotated_rectangle
    x, y = box.exterior.coords.xy
    sides = sorted([np.hypot(x[1] - x[0], y[1] - y[0]), np.hypot(x[2] - x[1], y[2] - y[1])])
    return sides[1] / max(sides[0], 1.0)


def build_pure_water(cfg: dict):
    """Pure-water polygons of each section and the river-width table.

    Where water is found: the 10 m Dynamic World land-cover series (2019-2025) gives, for each
    pixel, the share of clear images classified as water. Pixels at or above WATER_FREQUENCY
    inside the corridor are turned into polygons in Earth Engine (the 30 m JRC map misses the
    narrow upstream river). Rounder water bodies are dropped: they are lagoons and ponds, not the
    river. Locally, an inner buffer is taken off the banks: 10 m for Sentinel-2, 30 m for Landsat.
    The estuary section keeps the channel of notebook 34.

    Writes the layers `agua_permanente`, `agua_pura_sentinel2`, `agua_pura_landsat` to
    trocos_rio.gpkg and `largura_por_troco.csv`:
      largura_media_m          permanent-water area / section length
      area_pura_*_ha           area left after the inner buffer
      landsat_utilizavel       True when at least 5 ha are left for Landsat (river wide enough
                               for 30 m pixels); otherwise only Sentinel-2 is used there
    The mask is automatic. It should be checked in QGIS by someone who knows the river.
    """
    import ee
    import geopandas as gpd
    from shapely.geometry import shape
    from shapely.ops import unary_union

    from .gee import init, retry

    init(cfg)
    crs = cfg["grid"]["crs"]
    sections = load_sections(cfg)
    dw = ee.ImageCollection("GOOGLE/DYNAMICWORLD/V1").filterDate("2019-01-01", "2026-01-01").select("label")
    rows = []
    for _, section in sections.iterrows():
        if section["numero"] == N_LINE_SECTIONS + 1:                    # estuary: already a water polygon
            rows.append({"troco": section["troco"], "nome": section["nome"], "geometry": section.geometry})
            continue
        region = ee.Geometry(section.geometry.__geo_interface__)
        frequency = dw.filterBounds(region).map(lambda img: img.eq(0)).mean()
        vectors = frequency.gte(WATER_FREQUENCY).selfMask().reduceToVectors(geometry=region, scale=10, geometryType="polygon", eightConnected=True,
                                                                             maxPixels=1e10, tileScale=4)
        features = retry(lambda: vectors.getInfo())["features"]
        pieces = gpd.GeoSeries([shape(f["geometry"]) for f in features], crs=4326).to_crs(crs)
        pieces = [g for g in pieces if g.area >= MIN_PIECE_HA * 1e4 and _elongation(g) >= MIN_ELONGATION]
        rows.append({"troco": section["troco"], "nome": section["nome"],
                     "geometry": gpd.GeoSeries([unary_union(pieces)], crs=crs).to_crs(4326).iloc[0] if pieces else None})
        print(section["troco"], len(features), "polígonos,", len(pieces), "mantidos", flush=True)
    permanent = gpd.GeoDataFrame(rows, crs=4326).to_crs(crs)
    permanent = permanent[permanent.geometry.notna() & ~permanent.geometry.is_empty]
    file = path(cfg, "sections", "trocos_rio.gpkg")
    permanent.to_file(file, layer="agua_permanente", driver="GPKG")
    width = sections[["troco", "nome", "comprimento_km"]].merge(pd.DataFrame({"troco": permanent["troco"], "area_agua_permanente_ha": permanent.area.to_numpy() / 1e4}), how="left")
    width["largura_media_m"] = width["area_agua_permanente_ha"] * 1e4 / (width["comprimento_km"] * 1000)
    for label, metres in INNER_BUFFER_M.items():
        pure = permanent.assign(geometry=permanent.buffer(-metres))
        pure = pure[~pure.geometry.is_empty]
        pure.to_file(file, layer=f"agua_pura_{label}", driver="GPKG")
        width = width.merge(pd.DataFrame({"troco": pure["troco"], f"area_pura_{label}_ha": pure.area.to_numpy() / 1e4}), how="left")
    width = width.fillna({"area_agua_permanente_ha": 0, "area_pura_sentinel2_ha": 0, "area_pura_landsat_ha": 0})
    width["landsat_utilizavel"] = width["area_pura_landsat_ha"] >= 5
    width.round(1).to_csv(path(cfg, "sections", "largura_por_troco.csv"), index=False)
    return width


def pure_water(cfg: dict, sensor: str):
    """Pure-water polygons (EPSG:4326) used for a sensor."""
    import geopandas as gpd

    layer = "agua_pura_sentinel2" if sensor == "sentinel2" else "agua_pura_landsat"
    return gpd.read_file(path(cfg, "sections", "trocos_rio.gpkg", mkdir=False), layer=layer).to_crs(4326)


# ----------------------------------------------------------------------------- per-image values (Earth Engine)
REGIONS_TOLERANCE_M = 8
LANDSAT57_END = "2014-01-01"     # Landsat 5/7 are used up to 2013; Landsat 8 takes over (plan, Part I)
VEGETATION_NDVI = 0.4
# Shadows. Water darker than this in the green band is in the shadow of trees, clouds or relief: its
# colour is mostly noise (two tiny numbers divided), so it never counts. Measured on Sentinel-2 images
# of October-November 2026: in a narrow part of Manhica a third of the water pixels were this dark and
# looked clearer than the sunlit water next to them; in Marracuene almost none are.
SHADOW_GREEN = 0.02
# Leaves and banks. Plants are counted only this far inside the permanent water. Nearer the bank a
# pixel mixes water with the trees, reeds and fields of the bank: in the same images, 25-40 % of the
# Manhica section looked "covered by plants", but only 2-10 % at 20 m from the banks.
CORE_M = 20
MASK_VERSION = 2                 # version of these pixel rules; tables written with an older one are extracted again


def regions_asset(cfg: dict) -> str:
    import os

    return f"projects/{os.environ['EE_PROJECT']}/assets/ete_modulo_q_agua_permanente"


def upload_regions(cfg: dict, wait_minutes: float = 20) -> str:
    """Store the permanent-water polygons of the sections as an Earth Engine table, once, so the
    yearly requests do not have to send them again (saves upload data)."""
    import time

    import ee
    import geopandas as gpd
    import shapely

    from .gee import init

    init(cfg)
    asset = regions_asset(cfg)
    water = gpd.read_file(path(cfg, "sections", "trocos_rio.gpkg", mkdir=False), layer="agua_permanente")
    water = water.assign(geometry=water.simplify(REGIONS_TOLERANCE_M)).to_crs(4326)
    water = water.assign(geometry=shapely.set_precision(water.geometry.values, 1e-5))
    features = [ee.Feature(ee.Geometry(g.__geo_interface__), {"troco": t}) for t, g in zip(water["troco"], water.geometry)]
    try:
        ee.data.deleteAsset(asset)
    except ee.EEException:
        pass
    task = ee.batch.Export.table.toAsset(collection=ee.FeatureCollection(features), description="ete_modulo_q_regioes", assetId=asset)
    task.start()
    deadline = time.time() + wait_minutes * 60
    while time.time() < deadline:
        state = task.status()["state"]
        if state in ("COMPLETED", "FAILED", "CANCELLED"):
            break
        time.sleep(15)
    if state != "COMPLETED":
        raise RuntimeError(f"upload of the section polygons to Earth Engine ended as {state}: {task.status().get('error_message', '')}")
    return asset


def ndvi(sr):
    """NDVI of an Earth Engine image with the bands red and nir."""
    return sr.select("nir").subtract(sr.select("red")).divide(sr.select("nir").add(sr.select("red")))


def pure_water(sr):
    """1 where a pixel of this image can be trusted for the colour of the water, else 0. The same rules
    for the per-section series and for the map of the water colour:
      - open water: MNDWI above 0, no plants on it (NDVI below 0.1), dark in the short-wave infrared;
      - pure: one pixel away from anything that is not water in this image (banks, sand, plants, leaves);
      - lit: not in the shadow of trees, clouds or relief (green reflectance at least SHADOW_GREEN)."""
    green, swir = sr.select("green"), sr.select("swir1")
    water = green.subtract(swir).divide(green.add(swir)).gt(0).And(ndvi(sr).lt(0.1)).And(swir.lt(0.05))
    return water.unmask(0).focal_min(radius=1, kernelType="square", units="pixels").eq(1).And(green.gte(SHADOW_GREEN))


def s2_clear(img):
    """1 where a Sentinel-2 pixel is free of clouds and cloud shadows (Scene Classification and Cloud
    Score+, needs the band cs_cdf linked from GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED)."""
    return img.select("SCL").remap([0, 1, 3, 8, 9, 10, 11], [0] * 7, 1).And(img.select("cs_cdf").gte(0.65))


def s2_reflectance(img):
    return img.select(["B3", "B4", "B5", "B8A", "B11"], ["green", "red", "red_edge1", "nir", "swir1"]).multiply(0.0001)


def _collection(cfg: dict, sensor: str, regions):
    """(collection, prepare(image) -> image with the bands to reduce, scale in metres)."""
    import ee

    # the river core: permanent water at least CORE_M from its edge (leaves and reeds of the banks left out)
    core = ee.Image(0).paint(regions, 1).focal_min(radius=CORE_M, kernelType="square", units="meters").eq(1)

    def finish(sr, clear, extra):
        green, red = sr.select("green"), sr.select("red")
        out = sr.select(["green", "red", "nir"]).addBands(red.subtract(green).divide(red.add(green)).rename("ndti"))
        for band in extra:
            out = out.addBands(band)
        vegetation = ndvi(sr).gt(VEGETATION_NDVI).rename("veg").updateMask(clear).updateMask(core)   # share of the river core covered by plants
        return out.updateMask(clear).updateMask(pure_water(sr)).addBands(vegetation)

    if sensor == "sentinel2":
        score = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
        collection = ee.ImageCollection(cfg["datasets"]["sentinel2"]["id"]).filterBounds(regions).linkCollection(score, ["cs_cdf"])

        def prepare(img):
            clear = s2_clear(img)
            sr = s2_reflectance(img)
            re, red = sr.select("red_edge1"), sr.select("red")
            return finish(sr, clear, [re.subtract(red).divide(re.add(red)).rename("ndci")])

        return collection, prepare, 10
    if sensor == "landsat89":
        collection = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")).filterBounds(regions)
        names, thermal = ["SR_B3", "SR_B4", "SR_B5", "SR_B6"], "ST_B10"
    elif sensor == "landsat57":
        collection = (ee.ImageCollection("LANDSAT/LT05/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LE07/C02/T1_L2"))
                      .filterBounds(regions).filterDate("2000-01-01", LANDSAT57_END))
        names, thermal = ["SR_B2", "SR_B3", "SR_B4", "SR_B5"], "ST_B6"
    else:
        raise ValueError(sensor)

    def prepare(img):
        clear = img.select("QA_PIXEL").bitwiseAnd(0b11111).eq(0)
        sr = img.select(names, ["green", "red", "nir", "swir1"]).multiply(0.0000275).add(-0.2)
        temperature = img.select(thermal).multiply(0.00341802).add(149.0 - 273.15).rename("temp_c")
        return finish(sr, clear, [temperature])

    return collection, prepare, 30


def extract_period(cfg: dict, sensor: str, start: str, end: str) -> pd.DataFrame:
    """One row per image and section between two dates: median green, red, near-infrared, NDTI
    (plus NDCI for Sentinel-2, water temperature for Landsat) of the pure-water pixels (clear, away
    from the banks, not in shadow), how many there were, and the share of the river core (CORE_M
    from the banks) covered by plants, with the number of clear core pixels it was measured on."""
    import ee

    from .gee import init, retry

    init(cfg)
    regions = ee.FeatureCollection(regions_asset(cfg))
    collection, prepare, scale = _collection(cfg, sensor, regions)
    reducer = ee.Reducer.median().combine(ee.Reducer.count(), sharedInputs=True).combine(ee.Reducer.mean(), sharedInputs=True)
    extra = "ndci" if sensor == "sentinel2" else "temp_c"
    keep = ["troco", "date", "image", "green_median", "red_median", "nir_median", "ndti_median", "ndti_count", f"{extra}_median", "veg_mean", "veg_count"]

    def per_image(img):
        stats = prepare(img).reduceRegions(regions, reducer, scale)
        stats = stats.filter(ee.Filter.Or(ee.Filter.gt("veg_count", 0), ee.Filter.gt("ndti_count", 0)))     # the image saw some of the section
        return stats.map(lambda f: ee.Feature(None, f.set("date", img.date().format("YYYY-MM-dd"), "image", img.get("system:index")).toDictionary(keep)))

    features = retry(lambda: collection.filterDate(start, end).map(per_image).flatten().getInfo())["features"]
    table = pd.DataFrame([f["properties"] for f in features])
    if table.empty:
        return table
    table = table.rename(columns={"green_median": "green", "red_median": "red", "nir_median": "nir", "ndti_median": "ndti", "ndti_count": "pixeis",
                                  f"{extra}_median": extra, "veg_mean": "vegetacao", "veg_count": "pixeis_limpos"})
    table["sensor"] = sensor
    table["versao_mascara"] = MASK_VERSION
    return table


def _mask_version(file) -> int:
    """The pixel-rule version a per-image table was written with (1 = before the version column)."""
    head = pd.read_csv(file, nrows=1)
    return int(head["versao_mascara"].iloc[0]) if "versao_mascara" in head and len(head) else (MASK_VERSION if "versao_mascara" in head else 1)


def update_series(cfg: dict, sensors=None, log=print) -> None:
    """Create or extend the per-image files in data/raw/water_quality/modulo_q/ (one per sensor and
    year). Complete past years are not asked again; the current year always is. Sentinel-2 is
    asked in quarters, because a full year is too much for one request. Files written with older
    pixel rules (MASK_VERSION) are asked again, so the whole record follows the same rules."""
    from datetime import date

    folder = path(cfg, "module_q_raw")
    this_year = date.today().year
    for sensor in sensors or SENSORS:
        last_year = min(this_year, 2013) if sensor == "landsat57" else this_year
        for year in range(SENSORS[sensor], last_year + 1):
            out = folder / f"{sensor}_{year}.csv"
            if out.exists() and (year < this_year or sensor == "landsat57") and _mask_version(out) >= MASK_VERSION:
                continue
            cuts = [f"{year}-01-01", f"{year}-04-01", f"{year}-07-01", f"{year}-10-01", f"{year + 1}-01-01"] if sensor == "sentinel2" else [f"{year}-01-01", f"{year + 1}-01-01"]
            parts = [extract_period(cfg, sensor, a, b) for a, b in zip(cuts[:-1], cuts[1:])]
            parts = [p for p in parts if len(p)]
            table = pd.concat(parts, ignore_index=True) if parts else pd.DataFrame(columns=["troco", "date", "image", "sensor", "versao_mascara"])
            table.to_csv(out, index=False)
            log(f"{sensor} {year}: {len(table)} linhas")
