"""Map of the colour of the water (turbidity) of the lower Incomati, from the latest clear Sentinel-2 image.

For the communities: the river painted in the colour the satellite gives it, from clearer (blue) to
muddier (brown), compared with ten years of images of this same stretch of river.

What is measured
  The colour index NDTI = (red - green) / (red + green) of each 10 m water pixel, smoothed over 30 m
  (median of 3 x 3 pixels), in five steps fixed from the Sentinel-2 record of the sections Q7 to Q9
  (STEPS). The steps do not change from one map to the next, so two dates can be compared. Higher =
  more mud in the water. Nothing here says whether the water is safe: river water must always be
  treated before drinking.

Pixels that never get a colour ("sem leitura") follow module_q.s2_clear and module_q.pure_water, the
same rules as the per-section series: clouds and cloud shadows, shadows of trees and relief, plants
and leaves, sand, and the pixel next to the bank.

Steps (needs Earth Engine, run weekly by scripts/update_water_quality_scenes.py, about 1 MB):
  choose_day()        the most recent day of the last LOOKBACK_DAYS with at least MIN_SHARE of the river readable
  download()          the colour of that day as a small GeoTIFF (one byte per 10 m pixel, about 0.25 MB)
  download_natural()  the photograph of the same day, in natural colour, for the picture of the pages (JPEG, about 0.3 MB)
Then, offline (platform.export_water_colour): render() draws the light map for phones and the
transparent layer for the interactive map, and summary() says which colour dominates in each section.
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from pathlib import Path

import numpy as np

from . import module_q
from .config import path

SECTIONS = ("Q7", "Q8", "Q9")                 # Manhiça, Marracuene, mouth
SECTION_NAMES = {"Q7": "Manhiça", "Q8": "Marracuene", "Q9": "Foz"}
NORTH_LAT = -25.46                            # the map starts a little north of the district of Marracuene
MARGIN_M = 1500
RES_M = 10
CRS = "EPSG:32736"
# Five steps of the colour index, fixed from the record: quintiles of the per-image medians of
# Sentinel-2 in Q7-Q9, 2017-2026 (steps_from_record). Each step holds a fifth of ten years of images.
STEPS = (-0.099, -0.058, -0.030, 0.002)
CLASSES = (("muito clara", "#1D6B8F"), ("clara", "#6FAFC9"), ("habitual", "#E3D5A8"), ("turva", "#C08A45"), ("muito turva", "#6F3B14"))
NO_READING = ("sem leitura", "#B4B9BE")
# How each step reads in a sentence (the light page; the application has the same words in plataforma/tema.py)
SENTENCES = {"muito clara": "muito mais clara do que o costume", "clara": "mais clara do que o costume", "habitual": "com a cor do costume",
             "turva": "mais turva do que o costume", "muito turva": "muito mais turva do que o costume"}
LAND, OUTLINE, BORDER, INK = "#F3F1EB", "#8A949E", "#9AA3AB", "#26323B"
MIN_SHARE = 0.6                               # part of the river that must be readable to use a day
LOOKBACK_DAYS = 45
SMOOTH_M = 15                                 # radius: 3 x 3 pixels of 10 m
ENC_LOW, ENC_STEP = -0.25, 0.002              # stored as round((ndti - ENC_LOW) / ENC_STEP), 0..250
RIVER_NO_READING, OUTSIDE = 254, 255
PLACES = ("Mapelane", "Moveja", "Marracuene", "Macaneta")      # OpenStreetMap names, to find one's way on the map


# ----------------------------------------------------------------------------- the frame
def frame(cfg: dict):
    """(permanent water of the sections inside the map, in EPSG:32736; map bounds west, south, east, north in metres)."""
    import geopandas as gpd
    from shapely.geometry import box

    water = gpd.read_file(path(cfg, "sections", "trocos_rio.gpkg", mkdir=False), layer="agua_permanente").to_crs(CRS)
    water = water[water["troco"].isin(SECTIONS)]
    south_of = gpd.GeoSeries([box(31.0, -27.0, 34.0, NORTH_LAT)], crs=4326).to_crs(CRS).iloc[0]
    water = water.clip(south_of)
    w, s, e, n = water.total_bounds
    bounds = (np.floor((w - MARGIN_M) / 100) * 100, np.floor((s - MARGIN_M) / 100) * 100,
              np.ceil((e + MARGIN_M) / 100) * 100, np.ceil((n + MARGIN_M) / 100) * 100)
    return water, tuple(float(b) for b in bounds)


def steps_from_record(cfg: dict) -> list[float]:
    """Quintiles of the per-image Sentinel-2 colour index in Q7-Q9 (how STEPS were chosen)."""
    import pandas as pd

    files = sorted(path(cfg, "module_q_raw", mkdir=False).glob("sentinel2_*.csv"))
    table = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
    table = table[table["troco"].isin(SECTIONS) & (table["pixeis"] >= 200)]
    return [round(float(q), 3) for q in table["ndti"].quantile([0.2, 0.4, 0.6, 0.8])]


# ----------------------------------------------------------------------------- Earth Engine
def _sources(cfg: dict, bounds):
    import ee

    regions = ee.FeatureCollection(module_q.regions_asset(cfg)).filter(ee.Filter.inList("troco", list(SECTIONS)))
    area = ee.Geometry.Rectangle(list(bounds), CRS, False)
    permanent = ee.Image(0).paint(regions, 1)
    score = ee.ImageCollection("GOOGLE/CLOUD_SCORE_PLUS/V1/S2_HARMONIZED")
    s2 = ee.ImageCollection(cfg["datasets"]["sentinel2"]["id"]).filterBounds(area).linkCollection(score, ["cs_cdf"])
    return area, permanent, s2


def _colour(images):
    """Colour index of one day (its tiles put together) where it can be read, and the readable mask."""
    img = images.mosaic()
    sr = module_q.s2_reflectance(img)
    readable = module_q.s2_clear(img).And(module_q.pure_water(sr))
    ndti = sr.select("red").subtract(sr.select("green")).divide(sr.select("red").add(sr.select("green")))
    return ndti.updateMask(readable), readable


def _day(images, day: date):
    return images.filterDate(day.isoformat(), (day + timedelta(days=1)).isoformat())


def choose_day(cfg: dict, today: date | None = None, log=print) -> dict:
    """The most recent day with at least MIN_SHARE of the river readable; else the best day found
    ({"data", "parte_legivel", "abaixo_do_minimo"})."""
    import ee

    from .gee import init, retry

    init(cfg)
    _, bounds = frame(cfg)
    area, permanent, s2 = _sources(cfg, bounds)
    today = today or date.today()
    recent = s2.filterDate((today - timedelta(days=LOOKBACK_DAYS)).isoformat(), (today + timedelta(days=1)).isoformat()) \
               .filter(ee.Filter.lt("CLOUDY_PIXEL_PERCENTAGE", 80))
    stamps = retry(lambda: recent.aggregate_array("system:time_start").getInfo())
    days = sorted({datetime.fromtimestamp(t / 1000, timezone.utc).date() for t in stamps}, reverse=True)
    total = list(retry(lambda: permanent.reduceRegion(ee.Reducer.sum(), area, 20, maxPixels=1e9).getInfo()).values())[0]
    best = None
    for day in days:
        _, readable = _colour(_day(recent, day))
        seen = list(retry(lambda: readable.And(permanent).reduceRegion(ee.Reducer.sum(), area, 20, maxPixels=1e9).getInfo()).values())[0] or 0
        share = round(seen / total, 3)
        log(f"   {day}: {100 * share:.0f} % do rio legível")
        if best is None or share > best["parte_legivel"]:
            best = {"data": day.isoformat(), "parte_legivel": share}
        if share >= MIN_SHARE:
            return {**best, "data": day.isoformat(), "parte_legivel": share, "abaixo_do_minimo": False}
    if best is None:
        raise RuntimeError(f"no Sentinel-2 image of the lower Incomati in the last {LOOKBACK_DAYS} days")
    return {**best, "abaixo_do_minimo": True}


def download(cfg: dict, day: str, folder: Path | None = None) -> Path:
    """The colour of the river on `day` as a GeoTIFF of one byte per 10 m pixel: 0-250 colour index
    (ENC_LOW + value x ENC_STEP), RIVER_NO_READING inside the river where nothing can be read,
    OUTSIDE elsewhere. Returns the file (data/processed/water_colour/cor_da_agua_<day>.tif)."""
    import ee

    from .gee import download_image, init
    from .grid import snapped_grid

    init(cfg)
    _, bounds = frame(cfg)
    area, permanent, s2 = _sources(cfg, bounds)
    ndti, readable = _colour(_day(s2, date.fromisoformat(day)))
    smooth = ndti.focal_median(radius=SMOOTH_M, kernelType="square", units="meters").updateMask(readable)
    code = smooth.subtract(ENC_LOW).divide(ENC_STEP).round().clamp(0, 250)
    river = permanent.eq(1)
    out = (ee.Image(OUTSIDE).where(river, RIVER_NO_READING).where(code.mask().gt(0).And(river), code.unmask(0))
           .toUint8().rename("cor"))
    folder = Path(folder or path(cfg, "processed") / "water_colour")
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"cor_da_agua_{day}.tif"
    quiet = {**cfg, "gee": {**cfg["gee"], "workers": 1}}          # Earth Engine allows few requests at once on this project
    download_image(out, ["cor"], snapped_grid(bounds, CRS, RES_M), file, quiet, dtype="uint8")
    return file


NATURAL_RES_M = 20                            # the photograph: 20 m pixels are enough for a picture shown 360-470 px wide


def download_natural(cfg: dict, day: str, folder: Path | None = None) -> Path:
    """The natural-colour photograph of the same day (red, green, blue), as the satellite saw it, clouds
    included, for the picture shown on the pages (crop_bounds, from just north of Marracuene to the mouth).
    A JPEG on a 20 m grid (about 0.3 MB) and its bounds in a .json beside it."""
    import ee

    from .gee import init, retry
    from .grid import snapped_grid

    init(cfg)
    _, whole = frame(cfg)
    bounds = crop_bounds(cfg)
    _, _, s2 = _sources(cfg, whole)
    image = _day(s2, date.fromisoformat(day)).mosaic().visualize(bands=["B4", "B3", "B2"], min=0, max=2600, gamma=1.3)
    grid = snapped_grid(bounds, CRS, NATURAL_RES_M)
    request = {"expression": image, "fileFormat": "JPEG", "grid": {
        "dimensions": {"width": grid.width, "height": grid.height},
        "affineTransform": {"scaleX": grid.res, "shearX": 0, "translateX": grid.x0, "shearY": 0, "scaleY": -grid.res, "translateY": grid.y0},
        "crsCode": CRS}}
    data = retry(lambda: ee.data.computePixels(request))
    folder = Path(folder or path(cfg, "processed") / "water_colour")
    folder.mkdir(parents=True, exist_ok=True)
    file = folder / f"cor_natural_{day}.jpg"
    file.write_bytes(data)
    file.with_suffix(".json").write_text(json.dumps({"bounds": [grid.x0, grid.y0 - grid.height * grid.res, grid.x0 + grid.width * grid.res, grid.y0], "crs": CRS}))
    return file


def update(cfg: dict, log=print) -> dict | None:
    """Weekly step: find the latest readable day and download it, unless it is already on disk."""
    chosen = choose_day(cfg, log=log)
    folder = path(cfg, "processed") / "water_colour"
    file = folder / f"cor_da_agua_{chosen['data']}.tif"
    if not file.exists():
        download(cfg, chosen["data"], folder)
    if not (folder / f"cor_natural_{chosen['data']}.jpg").exists():
        download_natural(cfg, chosen["data"], folder)
    (folder / f"cor_da_agua_{chosen['data']}.json").write_text(json.dumps({**chosen, "satelite": "Sentinel-2"}, indent=1))
    log(f"mapa da cor da água: {chosen['data']} ({100 * chosen['parte_legivel']:.0f} % do rio legível)")
    return chosen


def latest(cfg: dict) -> tuple[Path, dict] | None:
    """The most recent map on disk and its notes, or None."""
    files = sorted((path(cfg, "processed") / "water_colour").glob("cor_da_agua_*.tif"))
    if not files:
        return None
    notes = files[-1].with_suffix(".json")
    return files[-1], (json.loads(notes.read_text()) if notes.exists() else {"data": files[-1].stem[-10:]})


# ----------------------------------------------------------------------------- offline: classes, summary, pictures
def classes(code: np.ndarray) -> np.ndarray:
    """One-byte codes -> 0..4 (the five steps), 5 = no reading in the river, 6 = outside the river."""
    ndti = ENC_LOW + code.astype("float32") * ENC_STEP
    out = np.digitize(ndti, STEPS).astype("uint8")
    out[code == RIVER_NO_READING] = 5
    out[code == OUTSIDE] = 6
    return out


def _read(file: Path):
    import rasterio

    with rasterio.open(file) as src:
        return src.read(1), src.transform, src.crs


def summary(cfg: dict, file: Path) -> dict:
    """Per section: the share of the river that could be read and the share of each step."""
    from rasterio.features import rasterize

    code, transform, _ = _read(file)
    found = classes(code)
    water, _ = frame(cfg)
    out = {}
    for section in SECTIONS:
        shapes = water[water["troco"] == section].geometry
        if shapes.empty:
            continue
        inside = rasterize([(g, 1) for g in shapes], out_shape=code.shape, transform=transform, fill=0, dtype="uint8").astype(bool)
        river = inside & (found <= 5)
        read = inside & (found <= 4)
        if not river.any():
            continue
        shares = {CLASSES[k][0]: round(float((found[read] == k).mean()), 3) if read.any() else 0.0 for k in range(5)}
        median = float(np.median(ENC_LOW + code[read].astype("float32") * ENC_STEP)) if read.any() else None
        out[section] = {"nome": SECTION_NAMES[section], "parte_legivel": round(float(read.sum() / river.sum()), 3), "partes": shares,
                        "classe_dominante": max(shares, key=shares.get) if read.sum() >= 50 else None,
                        "classe_da_mediana": CLASSES[int(np.digitize(median, STEPS))][0] if median is not None and read.sum() >= 50 else None,
                        "indice_mediano": round(median, 4) if median is not None else None}
    return out


def _blocks(code: np.ndarray, size: int) -> np.ndarray:
    """Coarser picture for phones: each block of size x size pixels takes the mean colour index of
    its readable pixels; blocks of river with nothing readable stay "no reading"."""
    h, w = (code.shape[0] // size) * size, (code.shape[1] // size) * size
    c = code[:h, :w].reshape(h // size, size, w // size, size).swapaxes(1, 2).reshape(h // size, w // size, size * size)
    readable = c <= 250
    total = np.where(readable, c.astype("float32"), 0).sum(axis=2)
    count = readable.sum(axis=2)
    mean = np.where(count > 0, np.round(total / np.maximum(count, 1)), 0).astype("uint8")
    river = (c == RIVER_NO_READING).any(axis=2)
    return np.where(count > 0, mean, np.where(river, RIVER_NO_READING, OUTSIDE)).astype("uint8")


HOME_NORTH_LAT = -25.70                       # the picture of the home page: from just north of Marracuene to the mouth


def _utm_y(lat: float, lon: float = 32.72) -> float:
    from pyproj import Transformer

    return Transformer.from_crs(4326, CRS, always_xy=True).transform(lon, lat)[1]


def crop_bounds(cfg: dict, north_lat: float = HOME_NORTH_LAT) -> tuple[float, float, float, float]:
    """The picture of the home page: from `north_lat` to the mouth, the sides 2.5 km beyond the river."""
    from shapely.geometry import box

    water, (west, south, east, north) = frame(cfg)
    north = min(north, _utm_y(north_lat))
    near = water.clip(box(west, south, east, north)).total_bounds
    return max(west, near[0] - 2500), south, min(east, near[2] + 2500), north


def decorate(cfg: dict, ax, bounds, text: float = 1.25, places=PLACES) -> None:
    """Place names, a 5 km bar and the north on a map in EPSG:32736 (shared by the maps and the photographs)."""
    import geopandas as gpd
    import matplotlib.patheffects as effects

    west, south, east, north = bounds
    found = gpd.read_file(path(cfg, "places", "osm_places.gpkg", mkdir=False)).to_crs(CRS)
    found = found[found["name"].isin(places)]
    for _, row in found.iterrows():
        x, y = row.geometry.centroid.x, row.geometry.centroid.y
        if west < x < east and south < y < north:
            ax.plot(x, y, "o", color=INK, markersize=4.2 * text, zorder=5, markeredgecolor="white", markeredgewidth=0.8)
            ax.annotate(row["name"], (x, y), xytext=(5, 2), textcoords="offset points", fontsize=8.2 * text, color=INK, zorder=6,
                        fontweight="bold", path_effects=[effects.withStroke(linewidth=2.6 * text, foreground="white")])
    x0, y0 = west + 0.06 * (east - west), south + 0.025 * (north - south)                  # 5 km bar, bottom left
    ax.plot([x0, x0 + 5000], [y0, y0], color=INK, linewidth=2.2 * text, solid_capstyle="butt", zorder=6,
            path_effects=[effects.withStroke(linewidth=4.2 * text, foreground="white")])
    ax.annotate("5 km", (x0 + 2500, y0), xytext=(0, 4), textcoords="offset points", ha="center", fontsize=7.8 * text, color=INK, zorder=6,
                path_effects=[effects.withStroke(linewidth=2.4 * text, foreground="white")])
    ax.annotate("N", (east - 0.07 * (east - west), north - 0.03 * (north - south)), ha="center", va="top", fontsize=9 * text, fontweight="bold", color=INK,
                path_effects=[effects.withStroke(linewidth=2.4 * text, foreground="white")], zorder=6)
    ax.set_xlim(west, east), ax.set_ylim(south, north)


def render(cfg: dict, file: Path, out_png: Path, width_px: int = 900, north_lat: float | None = None, natural: Path | None = None) -> None:
    """The light map for phones: the river in the five colours, land plain, a few place names, a 5 km
    bar. No words that need translating except place names (the legend is drawn by the page).
    `north_lat` cuts the map there (the smaller picture of the home page). With `natural` (the JPEG of
    download_natural) the picture is the satellite photograph instead, with the same frame, names and
    bar, so the page can slide from one to the other; it is then saved as JPEG."""
    import geopandas as gpd
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.patheffects as effects
    import matplotlib.pyplot as plt
    from matplotlib.colors import ListedColormap
    from PIL import Image

    from .grid import load_aoi

    code, transform, _ = _read(file)
    res = transform.a
    west, north = transform.c, transform.f
    east, south = west + code.shape[1] * res, north - code.shape[0] * res
    data_north = north
    data_west = west
    if north_lat is not None:                                                         # a cut: north there, and the sides close to the river
        west, south, east, north = crop_bounds(cfg, north_lat)
    block = max(1, int(round((east - west) / res / width_px * 1.6)))                 # about 1.6 data blocks per output pixel
    coarse = classes(_blocks(code, block))
    colours = [c for _, c in CLASSES] + [NO_READING[1], LAND]
    height_in = 4.6 * (north - south) / (east - west)
    text = 1.6 if north_lat is not None else 1.25          # names readable on a phone, where the picture is shown about 360 px wide
    fig = plt.figure(figsize=(4.6, height_in), dpi=width_px / 4.6)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.set_facecolor(LAND)
    if natural is not None:
        photo = np.asarray(Image.open(natural).convert("RGB"))
        notes = Path(natural).with_suffix(".json")
        fw, fs, fe, fn = json.loads(notes.read_text())["bounds"] if notes.exists() else frame(cfg)[1]     # older photographs cover the whole frame
        ax.imshow(photo, extent=[fw, fe, fs, fn], interpolation="bilinear", zorder=2)
    else:
        ax.imshow(coarse, extent=[data_west, data_west + coarse.shape[1] * block * res, data_north - coarse.shape[0] * block * res, data_north],
                  cmap=ListedColormap(colours), vmin=-0.5, vmax=6.5, interpolation="nearest", zorder=2)
        water, _ = frame(cfg)
        water.boundary.plot(ax=ax, color=OUTLINE, linewidth=0.35, zorder=3)
        district = load_aoi(cfg, "district").to_crs(CRS)
        district.boundary.plot(ax=ax, color=BORDER, linewidth=0.8, linestyle=(0, (4, 3)), zorder=1)
    decorate(cfg, ax, (west, south, east, north), text)
    ax.set_axis_off()
    out_png.parent.mkdir(parents=True, exist_ok=True)
    if natural is not None:                                                           # a photograph: JPEG keeps it small
        buffer = __import__("io").BytesIO()
        fig.savefig(buffer, dpi=width_px / 4.6, facecolor=LAND, format="png")
        plt.close(fig)
        Image.open(buffer).convert("RGB").save(out_png, "JPEG", quality=80, optimize=True, progressive=True)
        return
    fig.savefig(out_png, dpi=width_px / 4.6, facecolor=LAND)
    plt.close(fig)
    Image.open(out_png).convert("RGB").quantize(colors=96, method=Image.Quantize.MEDIANCUT).save(out_png, optimize=True)


def overlay(file: Path, out_png: Path, step_deg: float = 0.0001, alpha: int = 235) -> list[list[float]]:
    """Transparent layer for the interactive map (latitude/longitude); returns its corners."""
    from .grid import Grid
    from .platform import write_overlay

    code, transform, _ = _read(file)
    found = classes(code).astype("float32")
    found[found == 6] = np.nan
    grid = Grid(CRS, transform.a, transform.c, transform.f, code.shape[1], code.shape[0])
    legend = {k: (name, colour) for k, (name, colour) in enumerate(CLASSES)} | {5: NO_READING}
    return write_overlay(found, grid, legend, out_png, step_deg, alpha)


def legend() -> list[dict]:
    """The steps for the page: name, colour and the range of the colour index."""
    edges = (None,) + STEPS + (None,)
    return [{"valor": k, "nome": name, "cor": colour, "de": edges[k], "ate": edges[k + 1]} for k, (name, colour) in enumerate(CLASSES)] + \
           [{"valor": 5, "nome": NO_READING[0], "cor": NO_READING[1], "de": None, "ate": None}]
