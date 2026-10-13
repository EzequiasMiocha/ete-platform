"""Place names for the warning zones: which localities flood first.

People do not read zone numbers; they know the name of where they live. This
module puts names on the warning zones, using the January 2026 flood (Copernicus
EMS maps of 17, 18, 23 and 24 January) as the reference for the ORDER in which
places went under water.

Name sources (both public, both imperfect):
  * OpenStreetMap place nodes
  * GeoNames gazetteer (populated places; many names are old and some are former
    farm names)
A place is a point with a 500 m circle around it, not an official boundary. The
list must be checked by people who know Marracuene before it is published: the
CSV has an empty `validado` column for that.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .alerts import warning_zones
from .config import path
from .grid import load_aoi, load_grid
from .rasters import read_bands, static_stack_file, study_masks

# EMS products of the reference flood, in the order they were mapped
REFERENCE_MAPS = [("DEL_PRODUCT_v1", "2026-01-17"), ("DEL_MONIT01_v1", "2026-01-18"),
                  ("DEL_MONIT03_v2", "2026-01-23"), ("DEL_MONIT04_v1", "2026-01-24")]
REFERENCE_ALERT_DAY = "2026-01-13"       # first day at laranja or above with the observed discharge and rain
CATEGORIES = ["alaga primeiro", "alaga em cheia grande", "na margem da cheia", "fora das zonas de aviso"]


def load_place_names(cfg: dict):
    """Named places inside the district + buffer: OpenStreetMap first, then GeoNames names that are
    not already there (same name within 1.5 km counts as the same place)."""
    import geopandas as gpd

    folder = path(cfg, "places", mkdir=False)
    crs = cfg["grid"]["crs"]
    osm = gpd.read_file(folder / "osm_places.gpkg").to_crs(crs)
    osm = osm.rename(columns={"name": "lugar", "place": "tipo"}).assign(fonte="OpenStreetMap")
    cols = ["geonameid", "name", "asciiname", "alternatenames", "lat", "lon", "fclass", "fcode", "country", "cc2",
            "adm1", "adm2", "adm3", "adm4", "pop", "elev", "dem", "tz", "mod"]
    gn = pd.read_csv(folder / "MZ.txt", sep="\t", names=cols, dtype=str, keep_default_na=False)
    gn = gn[gn["fclass"] == "P"]
    gn = gpd.GeoDataFrame({"lugar": gn["name"], "tipo": "povoação", "fonte": "GeoNames"},
                          geometry=gpd.points_from_xy(gn["lon"].astype(float), gn["lat"].astype(float)), crs=4326).to_crs(crs)
    gn = gn[gn.within(load_aoi(cfg, "district").to_crs(crs).union_all().buffer(2000))]
    key = lambda s: s.str.lower().str.normalize("NFKD").str.encode("ascii", "ignore").str.decode("ascii").str.strip()
    keep = []
    for _, row in gn.iterrows():
        same = osm[key(osm["lugar"]) == key(pd.Series([row["lugar"]]))[0]]
        keep.append(same.empty or same.distance(row.geometry).min() > 1500)
    places = pd.concat([osm[["lugar", "tipo", "fonte", "geometry"]], gn[keep]], ignore_index=True)
    places = gpd.GeoDataFrame(places, crs=crs)
    places = places[places.within(load_aoi(cfg, "district").to_crs(crs).union_all().buffer(1000))]
    return places.drop_duplicates(subset=["lugar", "geometry"]).reset_index(drop=True)


def flood_order(cfg: dict, radius_m: float = 500, min_share: float = 0.05):
    """For every named place: is it in a warning zone, and when did the water arrive in the
    reference flood?

    Each place is a circle of `radius_m`. Columns:
      categoria          alaga primeiro / alaga em cheia grande / na margem da cheia / fora das zonas de aviso
      primeira_data      first reference map in which at least `min_share` of the circle was flooded
      dias_apos_alerta   days between the reference alert day and that map
      parte_alagada      share of the circle flooded at the largest extent
      edificios          buildings within the circle; edificios_alagados: those inside the largest extent
      distancia_ao_rio_m, altura_acima_do_rio_m   from the terrain stack
    Sorted by the order in which the water arrived.
    """
    import geopandas as gpd
    from rasterio.features import rasterize

    grid = load_grid(cfg)
    name = cfg["project"]["aoi_name"]
    places = load_place_names(cfg)
    zones = warning_zones(cfg)["raster"]
    static = read_bands(static_stack_file(cfg), ["hand", "distance_to_river_m"])
    base = path(cfg, "ems_unosat", "EMSR857_AOI06_Palmeira", mkdir=False)
    extents = []
    for product, day in REFERENCE_MAPS:
        shp = next((base / f"EMSR857_AOI06_{product}").glob("*_observedEventA_*.shp"))
        geoms = gpd.read_file(shp).to_crs(grid.crs).geometry
        extents.append((day, rasterize([(g, 1) for g in geoms], out_shape=zones.shape, transform=grid.transform, fill=0).astype(bool)))
    buildings = gpd.read_file(path(cfg, "buildings", f"open_buildings_{name}.gpkg", mkdir=False)).to_crs(grid.crs).geometry.representative_point()
    b_cols = ((buildings.x - grid.x0) // grid.res).astype(int).to_numpy()
    b_rows = ((grid.y0 - buildings.y) // grid.res).astype(int).to_numpy()
    b_ok = (b_rows >= 0) & (b_rows < grid.height) & (b_cols >= 0) & (b_cols < grid.width)
    count = np.zeros(zones.shape, "int32")
    np.add.at(count, (b_rows[b_ok], b_cols[b_ok]), 1)

    posts = gpd.read_file(path(cfg, "places", "postos_administrativos.geojson", mkdir=False)).to_crs(grid.crs)
    near_zone = rasterize([(g.buffer(radius_m), 1) for g in gpd.read_file(path(cfg, "maps", "zonas_de_aviso", f"zonas_de_aviso_{name}.gpkg", mkdir=False)).geometry],
                          out_shape=zones.shape, transform=grid.transform, fill=0).astype(bool)
    rows = []
    for _, place in places.iterrows():
        circle = rasterize([(place.geometry.buffer(radius_m), 1)], out_shape=zones.shape, transform=grid.transform, fill=0).astype(bool)
        if not circle.any():
            continue
        share = lambda mask: float((mask & circle).sum() / circle.sum())
        first = next((day for day, extent in extents if share(extent) >= min_share), None)
        zone1, zone_any = share(zones == 1), share(zones > 0)
        category = (CATEGORIES[0] if zone1 >= min_share else CATEGORIES[1] if zone_any >= min_share
                    else CATEGORIES[2] if (near_zone & circle).any() else CATEGORIES[3])
        post = posts[posts.contains(place.geometry)]
        rows.append({
            "lugar": place["lugar"], "posto_administrativo": post["posto_administrativo"].iloc[0] if len(post) else "",
            "categoria": category, "primeira_data": first,
            "dias_apos_alerta": None if first is None else int((pd.Timestamp(first) - pd.Timestamp(REFERENCE_ALERT_DAY)).days),
            "parte_alagada": round(share(extents[-1][1] | extents[-2][1]), 2), "parte_na_zona_1": round(zone1, 2),
            "edificios": int(count[circle].sum()), "edificios_alagados": int(count[circle & (zones > 0)].sum()),
            "distancia_ao_rio_m": round(float(np.nanmin(static["distance_to_river_m"][circle])), -1),
            "altura_acima_do_rio_m": round(float(np.nanmedian(static["hand"][circle])), 1) if np.isfinite(static["hand"][circle]).any() else None,
            "fonte_do_nome": place["fonte"], "validado": "", "geometry": place.geometry})
    table = gpd.GeoDataFrame(rows, crs=grid.crs)
    table["ordem"] = table["categoria"].map({c: i for i, c in enumerate(CATEGORIES)})
    table = table.sort_values(["ordem", "primeira_data", "parte_alagada"], ascending=[True, True, False], na_position="last").drop(columns="ordem").reset_index(drop=True)
    folder = path(cfg, "maps", "zonas_de_aviso")
    table.to_file(folder / f"lugares_{name}.gpkg", driver="GPKG")
    table.drop(columns="geometry").to_csv(folder / f"lugares_por_ordem_de_alagamento_{name}.csv", index=False)
    return table


def names_for_bulletin(cfg: dict, limit: int = 12) -> dict:
    """Place names per category for the bulletin, most flooded first (empty if the table is missing)."""
    file = path(cfg, "maps", "zonas_de_aviso", f"lugares_por_ordem_de_alagamento_{cfg['project']['aoi_name']}.csv", mkdir=False)
    if not file.exists():
        return {}
    table = pd.read_csv(file)
    return {category: table[table["categoria"] == category].sort_values("parte_alagada", ascending=False)["lugar"]
            .drop_duplicates().head(limit).tolist() for category in CATEGORIES[:2]}
