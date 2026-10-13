"""Alert engine (week 3, task S3-03).

ALERT = triggers (rain and river discharge, daily)  x  where it can flood
(Model A classes)  x  what is exposed there. Model B confirms afterwards, on
the satellite image, where the water actually is.

Levels: 0 verde, 1 amarelo, 2 laranja, 3 vermelho.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from .config import path
from .drivers import read_table
from .grid import load_grid
from .rasters import read_bands, study_masks

LEVELS = {0: "verde", 1: "amarelo", 2: "laranja", 3: "vermelho"}


def thresholds(cfg: dict) -> dict:
    """Numeric limits of the triggers. Discharge limits are percentiles of the daily
    discharge up to `calibration_end`, so later years are a fair test of the rules."""
    a = cfg["processing"]["alerts"]
    q = read_table(cfg, "hydromet_daily")["discharge_m3s"].loc[:a["calibration_end"]].dropna()
    return {"rain_p7_min_mm": a["rain_p7_min_mm"], "rain_pct": a["rain_pct"],
            "discharge_m3s": {k: float(np.percentile(q, v)) for k, v in a["discharge_pct"].items()}}


def daily_alerts(cfg: dict) -> pd.DataFrame:
    """One row per day: the two triggers and the alert level.

    rain      amarelo: 7-day basin rain in the top 5 % for the time of year (and above the
              minimum total); laranja: top 1 %.
    discharge amarelo / laranja / vermelho: daily discharge above its percentile limits.
    level     the higher of the two; laranja rain together with laranja discharge is vermelho.
    """
    t = thresholds(cfg)
    rain = read_table(cfg, "rain_daily")[["rain_basin", "p7_basin", "p7_pct_basin"]]
    q = read_table(cfg, "hydromet_daily")[["discharge_m3s", "provisional"]]
    df = rain.join(q, how="outer").sort_index()
    enough = df["p7_basin"] >= t["rain_p7_min_mm"]
    df["rain_level"] = np.select([enough & (df["p7_pct_basin"] >= t["rain_pct"]["laranja"]),
                                  enough & (df["p7_pct_basin"] >= t["rain_pct"]["amarelo"])], [2, 1], 0)
    d = t["discharge_m3s"]
    df["discharge_level"] = np.select([df["discharge_m3s"] >= d["vermelho"], df["discharge_m3s"] >= d["laranja"],
                                       df["discharge_m3s"] >= d["amarelo"]], [3, 2, 1], 0)
    df["level"] = df[["rain_level", "discharge_level"]].max(axis=1)
    df.loc[(df["rain_level"] == 2) & (df["discharge_level"] >= 2), "level"] = 3
    df["alerta"] = df["level"].map(LEVELS)
    return df


def episodes(alerts: pd.DataFrame, min_level: int = 2, gap_days: int = 7) -> pd.DataFrame:
    """Alert episodes: runs of days at or above `min_level`, merged when less than `gap_days` apart."""
    days = alerts.index[alerts["level"] >= min_level]
    if len(days) == 0:
        return pd.DataFrame()
    group = (pd.Series(days).diff().dt.days.fillna(1) > gap_days).cumsum().to_numpy()
    rows = []
    for _, idx in pd.Series(days).groupby(group):
        part = alerts.loc[idx.iloc[0]:idx.iloc[-1]]
        rows.append({"inicio": idx.iloc[0].date(), "fim": idx.iloc[-1].date(), "dias_em_alerta": int(len(idx)),
                     "nivel_maximo": LEVELS[int(part["level"].max())],
                     "chuva_7d_max_mm": round(float(part["p7_basin"].max()), 0),
                     "caudal_max_m3s": round(float(part["discharge_m3s"].max()), 0),
                     "primeiro_gatilho": "chuva" if part["rain_level"].iloc[0] >= part["discharge_level"].iloc[0] else "caudal"})
    return pd.DataFrame(rows)


def lead_time(alerts: pd.DataFrame, event_date: str, min_level: int = 2, window_days: int = 30) -> dict:
    """First day at or above `min_level` in the `window_days` before an event date, and how many
    days of warning that gave."""
    event = pd.Timestamp(event_date)
    before = alerts.loc[event - pd.Timedelta(days=window_days):event]
    hits = before.index[before["level"] >= min_level]
    if len(hits) == 0:
        return {"primeiro_alerta": None, "dias_de_antecedencia": None, "nivel_no_dia": LEVELS[int(alerts["level"].get(event, 0))]}
    return {"primeiro_alerta": hits[0].date(), "dias_de_antecedencia": int((event - hits[0]).days),
            "nivel_no_dia": LEVELS[int(alerts["level"].get(event, 0))]}


# ----------------------------------------------------------------------------- exposure
def exposure_by_class(cfg: dict, flooded=None) -> pd.DataFrame:
    """Buildings, schools and health facilities inside the district, per susceptibility class
    of Model A. With `flooded` (a boolean 30 m raster), also how many lie in flooded pixels."""
    import geopandas as gpd

    grid = load_grid(cfg)
    name = cfg["project"]["aoi_name"]
    classes = read_bands(path(cfg, "maps", "modelo_a", f"suscetibilidade_{name}_30m.tif", mkdir=False), ["classe"])["classe"]
    district = study_masks(cfg)["district"]
    layers = {"edificios": path(cfg, "buildings", f"open_buildings_{name}.gpkg", mkdir=False),
              "escolas": path(cfg, "osm", f"osm_schools_{name}.gpkg", mkdir=False),
              "unidades_de_saude": path(cfg, "osm", f"osm_health_{name}.gpkg", mkdir=False)}
    labels = {1: "baixa", 2: "média", 3: "alta", 4: "muito alta"}
    out = pd.DataFrame(index=list(labels.values()))
    out["area_km2"] = [float((district & (classes == k)).sum()) * grid.res ** 2 / 1e6 for k in labels]
    if flooded is not None:
        out["area_alagada_km2"] = [float((district & (classes == k) & flooded).sum()) * grid.res ** 2 / 1e6 for k in labels]
    for layer, file in layers.items():
        points = gpd.read_file(file).to_crs(grid.crs).geometry.representative_point()
        cols = ((points.x - grid.x0) // grid.res).astype(int).to_numpy()
        rows = ((grid.y0 - points.y) // grid.res).astype(int).to_numpy()
        ok = (rows >= 0) & (rows < grid.height) & (cols >= 0) & (cols < grid.width)
        rows, cols = rows[ok], cols[ok]
        inside = district[rows, cols]
        cls = classes[rows, cols]
        out[layer] = [int((inside & (cls == k)).sum()) for k in labels]
        if flooded is not None:
            out[f"{layer}_em_zona_alagada"] = [int((inside & (cls == k) & flooded[rows, cols]).sum()) for k in labels]
    out.index.name = "suscetibilidade"
    return out


# ----------------------------------------------------------------------------- warning zones
ZONES = {1: "zona 1: primeiras a alagar", 2: "zona 2: cheia grande"}


def warning_zones(cfg: dict) -> dict:
    """Where to warn, from where the water really went in the reference flood (January 2026).

    zone 1  flooded in the first maps of the event (17-18 January, Copernicus EMS): the
            first places to go under water
    zone 2  flooded at the largest mapped extent (23-24 January) and not in zone 1
    Outside the area Copernicus analysed there is no observed extent; there, Model A's
    classes "muito alta" and "alta" stand in for zones 1 and 2 (flagged as estimated).

    Writes data/processed/maps/zonas_de_aviso/ (GeoTIFF and GeoPackage) and returns
    {"raster": 30 m array (0 none, 1, 2), "estimated": bool array, "file": gpkg path}.
    """
    import geopandas as gpd
    from rasterio.features import rasterize, shapes
    from shapely.geometry import shape

    from .rasters import write_raster

    grid = load_grid(cfg)
    name = cfg["project"]["aoi_name"]
    base = path(cfg, "ems_unosat", "EMSR857_AOI06_Palmeira", mkdir=False)
    burn = lambda frames: rasterize([(g, 1) for f in frames for g in f.to_crs(grid.crs).geometry],
                                    out_shape=(grid.height, grid.width), transform=grid.transform, fill=0).astype(bool)
    read = lambda product, layer: gpd.read_file(next((base / f"EMSR857_AOI06_{product}").glob(f"*_{layer}_*.shp")))
    early = burn([read("DEL_PRODUCT_v1", "observedEventA"), read("DEL_MONIT01_v1", "observedEventA")])
    largest = burn([read(p, "observedEventA") for p in ("DEL_PRODUCT_v1", "DEL_MONIT01_v1", "DEL_MONIT03_v2", "DEL_MONIT04_v1")])
    analysed = burn([read("DEL_MONIT04_v1", "areaOfInterestA")])
    classes = read_bands(path(cfg, "maps", "modelo_a", f"suscetibilidade_{name}_30m.tif", mkdir=False), ["classe"])["classe"]
    domain = np.isfinite(classes) & (classes > 0)                       # land of the modelling domain, river excluded
    zone = np.zeros(early.shape, "uint8")
    zone[largest & domain] = 2
    zone[early & domain] = 1
    estimated = domain & ~analysed
    zone[estimated & (classes == 3)] = 2
    zone[estimated & (classes == 4)] = 1
    folder = path(cfg, "maps", "zonas_de_aviso")
    write_raster(folder / f"zonas_de_aviso_{name}_30m.tif", {"zona": np.where(domain, zone, np.nan), "estimada": np.where(domain, estimated, np.nan)},
                 grid, dtype="uint8", tags={"reference_event": "EMSR857 January 2026"})
    rows = []
    for value in ZONES:
        mask = zone == value
        for geom, v in shapes(mask.astype("uint8"), mask=mask, transform=grid.transform):
            rows.append({"zona": value, "nome": ZONES[value], "geometry": shape(geom)})
    frame = gpd.GeoDataFrame(rows, crs=grid.crs).dissolve(by="zona", as_index=False)
    out = folder / f"zonas_de_aviso_{name}.gpkg"
    frame.to_file(out, driver="GPKG")
    return {"raster": zone, "estimated": estimated, "file": out}


def exposure_by_zone(cfg: dict, zones: np.ndarray) -> pd.DataFrame:
    """What lies in each warning zone inside the district: area, cropland, buildings, schools,
    health facilities and kilometres of road. Rows are cumulative for the alert levels:
    zone 1 alone, then zones 1 and 2 together."""
    import geopandas as gpd

    from .rasters import static_stack_file

    grid = load_grid(cfg)
    name = cfg["project"]["aoi_name"]
    district = study_masks(cfg)["district"]
    cropland = read_bands(static_stack_file(cfg), ["land_cover"])["land_cover"] == 40
    km2 = grid.res ** 2 / 1e6
    groups = {"zona 1 (primeiras a alagar)": zones == 1, "zonas 1 e 2 (cheia grande)": (zones == 1) | (zones == 2)}
    out = pd.DataFrame(index=list(groups))
    out["area_km2"] = [float((m & district).sum()) * km2 for m in groups.values()]
    out["area_agricola_km2"] = [float((m & district & cropland).sum()) * km2 for m in groups.values()]

    def pixel_index(points):
        cols = ((points.x - grid.x0) // grid.res).astype(int).to_numpy()
        rows = ((grid.y0 - points.y) // grid.res).astype(int).to_numpy()
        ok = (rows >= 0) & (rows < grid.height) & (cols >= 0) & (cols < grid.width)
        return rows[ok], cols[ok]

    for layer, file in {"edificios": path(cfg, "buildings", f"open_buildings_{name}.gpkg", mkdir=False),
                        "escolas": path(cfg, "osm", f"osm_schools_{name}.gpkg", mkdir=False),
                        "unidades_de_saude": path(cfg, "osm", f"osm_health_{name}.gpkg", mkdir=False)}.items():
        rows, cols = pixel_index(gpd.read_file(file).to_crs(grid.crs).geometry.representative_point())
        out[layer] = [int((m[rows, cols] & district[rows, cols]).sum()) for m in groups.values()]
    roads = gpd.read_file(path(cfg, "osm", f"osm_roads_{name}.gpkg", mkdir=False)).to_crs(grid.crs)
    roads = roads[roads.geometry.geom_type.isin(["LineString", "MultiLineString"])]
    pieces = roads.geometry.segmentize(grid.res).get_coordinates()          # road length ~ number of 30 m vertices
    rows, cols = pixel_index(gpd.GeoSeries(gpd.points_from_xy(pieces.x, pieces.y), crs=grid.crs))
    out["estradas_km"] = [float((m[rows, cols] & district[rows, cols]).sum()) * grid.res / 1000 for m in groups.values()]
    # people: WorldPop 2020 (about 100 m cells); each cell goes to the zone of its centre. This product
    # spreads people over all land, so on a floodplain with few buildings it is an upper estimate.
    import rasterio
    from rasterio.warp import transform as warp_points

    with rasterio.open(next(path(cfg, "population", mkdir=False).glob("worldpop_*_native.tif"))) as src:
        people = src.read(1).astype("float64")
        people[(people == src.nodata) | ~np.isfinite(people) | (people < 0)] = 0.0
        cell_rows, cell_cols = np.nonzero(people > 0)
        lon, lat = rasterio.transform.xy(src.transform, cell_rows, cell_cols)
        x, y = warp_points(src.crs, grid.crs, lon, lat)
    rows, cols = ((grid.y0 - np.asarray(y)) // grid.res).astype(int), ((np.asarray(x) - grid.x0) // grid.res).astype(int)
    ok = (rows >= 0) & (rows < grid.height) & (cols >= 0) & (cols < grid.width)
    rows, cols, counts = rows[ok], cols[ok], people[cell_rows, cell_cols][ok]
    out["pessoas_worldpop_2020"] = [float(counts[m[rows, cols] & district[rows, cols]].sum()) for m in groups.values()]
    out.index.name = "zona"
    return out
