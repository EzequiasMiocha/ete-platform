"""Pictures of each place for the page «A sua zona» of the platform.

For every named place (the points of lugares_por_ordem_de_alagamento, in the same order), three small
pictures of the same 6 km square centred on the place, at the 30 m of the scenes (200 x 200 pixels,
a few KB each):
  antes   the Sentinel-2 photograph of 23/10/2025, before the flood, in natural colour;
  cheia   the Sentinel-2 photograph of the flood (24 or 27/01/2026) with the fewest clouds over the middle
          of the square (3 km around the place); where clouds cover more than a fifth of it in both, the
          water seen by the radar in January 2026 (Model B) over the photograph before, in grey, because
          the radar sees through clouds;
  zonas   the warning zones (zone 1 red, zone 2 orange) over the photograph before, in grey.
The page draws the 500 m circle over the pictures and enlarges them in the browser, so the pictures
carry no words to translate. lugares/lugares.json says, for each place, its files, what the flood
picture is (date or radar), and the river section nearest to it.

Nothing is downloaded here: the scenes are those of scripts/download_flood_scenes.py.

    .venv/bin/python -c "from ete import config, place_images; place_images.refresh(config.load_config())"
"""

from __future__ import annotations

import json
from pathlib import Path

import numpy as np

from .config import path

SIDE_M = 6000                                        # the square around each place
BEFORE = ("sentinel2_antes_2025-10-23_30m.tif", "2025-10-23")
FLOOD = (("sentinel2_cheia_2026-01-24_30m.tif", "2026-01-24"), ("sentinel2_depois_2026-01-27_30m.tif", "2026-01-27"))
RADAR_MONTH = "2026-01"
MOST_CLOUD = 0.2                                     # clouds over the middle of the square above this: the radar instead of the photograph
ZONES = {1: "#c0392b", 2: "#e67e22"}                 # platform.ZONE_COLOURS
WATER = {1: "#2e86c1", 2: "#c0392b"}                 # platform.WATER: usual water, water out of its usual place


def _rgb(colour: str) -> np.ndarray:
    return np.array([int(colour[i:i + 2], 16) for i in (1, 3, 5)], "float32")


def _grey(picture: np.ndarray) -> np.ndarray:
    """The photograph in light grey, so that coloured layers read on top of it."""
    grey = picture.astype("float32") @ np.array([0.30, 0.59, 0.11], "float32")
    return np.repeat((0.55 * grey + 0.45 * 238)[..., None], 3, axis=2)


def _paint(base: np.ndarray, classes: np.ndarray, colours: dict, alpha: float) -> np.ndarray:
    out = base.astype("float32").copy()
    for value, colour in colours.items():
        inside = classes == value
        out[inside] = (1 - alpha) * out[inside] + alpha * _rgb(colour)
    return np.clip(out, 0, 255).astype("uint8")


def _cloud(file: Path, box) -> float:
    """Share of the square hidden by clouds or without data in a scene."""
    import rasterio
    from rasterio.windows import from_bounds

    with rasterio.open(file) as src:
        window = from_bounds(*box, src.transform)
        cloud = src.read(src.descriptions.index("nuvem") + 1, window=window, boundless=True, fill_value=1)
        red = src.read(src.descriptions.index("red") + 1, window=window, boundless=True, fill_value=src.nodata if src.nodata is not None else -9999)
    empty = red == (src.nodata if src.nodata is not None else -9999)
    return float(((cloud > 0) | empty).mean())


def _classes(file: Path, band: str, box, shape) -> np.ndarray:
    """A class band read inside `box` at the size of the pictures (the most common class of each cell)."""
    import rasterio
    from rasterio.enums import Resampling
    from rasterio.windows import from_bounds

    with rasterio.open(file) as src:
        window = from_bounds(*box, src.transform)
        i = src.descriptions.index(band) + 1 if band in src.descriptions else 1
        nodata = src.nodata if src.nodata is not None else 0
        raw = src.read(i, window=window, out_shape=shape, boundless=True, fill_value=nodata, resampling=Resampling.mode)
        values = np.rint(raw.astype("float32") * np.float32(src.scales[i - 1])).astype("int16")      # the radar maps keep 1 as 100 (scale 0.01)
        return np.where(raw == nodata, 0, values)


def _save(picture: np.ndarray, file: Path) -> None:
    from PIL import Image

    Image.fromarray(picture, "RGB").save(file, "JPEG", quality=80, optimize=True, progressive=True)


def export(cfg: dict, folder) -> list[dict]:
    """The pictures of every place in the package (lugares/) and their entry for the catalogue."""
    import geopandas as gpd

    from .satellite_images import natural

    name = cfg["project"]["aoi_name"]
    scenes = path(cfg, "sentinel2", mkdir=False).parent / "cenas_cheia_2026"
    zones_file = path(cfg, "maps", "zonas_de_aviso", f"zonas_de_aviso_{name}_30m.tif", mkdir=False)
    radar_file = path(cfg, "maps", "modelo_b", mkdir=False) / f"agua_{name}_{RADAR_MONTH}_10m.tif"
    needed = [scenes / BEFORE[0], zones_file, radar_file] + [scenes / f for f, _ in FLOOD]
    if not all(f.exists() for f in needed):
        return []
    folder = Path(folder)
    out = folder / "lugares"
    out.mkdir(parents=True, exist_ok=True)
    places = gpd.read_file(path(cfg, "maps", "zonas_de_aviso", f"lugares_{name}.gpkg", mkdir=False)).to_crs("EPSG:32736")
    reaches = gpd.read_file(folder / "vetores" / "trocos_modulo_q.geojson").to_crs("EPSG:32736")
    lonlat = places.to_crs(4326)
    half = SIDE_M / 2
    records, kept = [], set()
    for i, row in places.iterrows():
        x, y = row.geometry.x, row.geometry.y
        box = (x - half, y - half, x + half, y + half)
        before = natural(scenes / BEFORE[0], box)
        middle = (x - half / 2, y - half / 2, x + half / 2, y + half / 2)           # where the place and its 500 m circle are
        clouds = {day: _cloud(scenes / f, middle) for f, day in FLOOD}
        day = min(clouds, key=clouds.get)
        if clouds[day] <= MOST_CLOUD:
            flood = natural(scenes / dict((d, f) for f, d in FLOOD)[day], box)
            flood_picture = {"tipo": "foto", "data": day, "nuvens": round(clouds[day], 2)}
        else:
            radar = _classes(radar_file, "cheia", box, before.shape[:2])
            water = _classes(radar_file, "agua", box, before.shape[:2])
            flood = _paint(_grey(before), np.where(radar == 1, 2, np.where(water == 1, 1, 0)), WATER, 0.8)
            flood_picture = {"tipo": "radar", "mes": RADAR_MONTH, "nuvens": round(clouds[day], 2)}
        zones = _paint(_grey(before), _classes(zones_file, "zona", box, before.shape[:2]), ZONES, 0.62)
        files = {}
        for key, picture in (("antes", before), ("cheia", flood), ("zonas", zones)):
            file = out / f"{i:02d}_{key}.jpg"
            _save(picture, file)
            files[key] = f"lugares/{file.name}"
            kept.add(file.name)
        distances = reaches.distance(row.geometry)
        nearest = reaches.loc[distances.idxmin()]
        records.append({"id": int(i), "lugar": row["lugar"], "lon": round(float(lonlat.geometry[i].x), 5), "lat": round(float(lonlat.geometry[i].y), 5),
                        "ficheiros": files, "cheia": flood_picture, "troco": nearest["troco"], "troco_nome": nearest["nome"],
                        "distancia_ao_troco_m": int(round(float(distances.min()), -1))})
    for old in out.glob("*.jpg"):
        if old.name not in kept:
            old.unlink()
    (out / "lugares.json").write_text(json.dumps({"lado_m": SIDE_M, "resolucao_m": 30, "antes": {"data": BEFORE[1], "satelite": "Sentinel-2"},
                                                   "lugares": records}, ensure_ascii=False, indent=1))
    return [{"id": "zona_lugares", "titulo": "A sua zona: imagens de cada lugar", "tipo": "lugares", "ficheiro": "lugares/lugares.json",
             "atualizacao": "quando houver uma nova cheia fotografada",
             "descricao": "Para cada lugar, um quadrado de 6 km visto pelo satélite antes e durante a cheia de janeiro de 2026, e as zonas de aviso à sua volta.",
             "limites": "Imagens de 30 m: mostram a zona, não cada casa. Onde as nuvens tapavam a cheia, a imagem da cheia é a do radar (o mês inteiro de janeiro de 2026)."}]


def refresh(cfg: dict) -> dict:
    """Write the pictures of the places in the package and add them to the catalogue."""
    from .platform import _write_catalogue

    folder = path(cfg, "platform")
    return _write_catalogue(cfg, folder, export(cfg, folder))
