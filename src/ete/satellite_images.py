"""Satellite photographs for the platform: what the satellite really saw, in natural colour.

People understand a photograph from space at once. The platform shows them in pairs, to slide from
one to the other:
  - the flood of January 2026: the flood plain before (Sentinel-2, 23/10/2025, no clouds) and
    during the flood (Sentinel-2, 24/01/2026, 18 % clouds over the plain);
  - the latest clear image of the river at Marracuene beside the map of the water colour of the same
    day (turbidity_map.download_natural and turbidity_map.render; written by platform.export_water_colour).
The flood scenes were downloaded for the presentation figures (scripts/download_flood_scenes.py):
nothing is downloaded here.
"""

from __future__ import annotations

import io
from pathlib import Path

import numpy as np

from .config import path
from .turbidity_map import CRS, LAND, decorate

FLOOD_BOX = (463890.0, 7149720.0, 485940.0, 7183020.0)         # the flood plain north of Marracuene (EPSG:32736)
FLOOD_PAIR = (("antes", "sentinel2_antes_2025-10-23_30m.tif", "2025-10-23"), ("cheia", "sentinel2_cheia_2026-01-24_30m.tif", "2026-01-24"))
FLOOD_PLACES = ("Mapelane", "Moveja", "Marracuene", "Macaneta", "Bachite")
TOP_REFLECTANCE, GAMMA = 0.26, 1.3                                # the same stretch as the latest photograph (Earth Engine visualize)


def natural(file: Path, box) -> np.ndarray:
    """Red, green and blue of a scene inside `box`, stretched to a photograph (uint8, rows x columns x 3).
    Pixels without data are shown in the colour of the land of the maps."""
    import rasterio
    from rasterio.windows import from_bounds

    with rasterio.open(file) as src:
        window = from_bounds(*box, src.transform)
        bands = [src.descriptions.index(name) + 1 for name in ("red", "green", "blue")]
        raw = src.read(bands, window=window, boundless=True, fill_value=src.nodata if src.nodata is not None else -9999).astype("float32")
        empty = (raw == (src.nodata if src.nodata is not None else -9999)).any(axis=0)
        reflectance = raw * np.array(src.scales[: len(bands)], "float32")[:, None, None]
    picture = (np.clip(reflectance / TOP_REFLECTANCE, 0, 1) ** (1 / GAMMA) * 255).astype("uint8").transpose(1, 2, 0)
    land = tuple(int(LAND[i:i + 2], 16) for i in (1, 3, 5))
    picture[empty] = land
    return picture


def render_photo(cfg: dict, picture: np.ndarray, box, out: Path, width_px: int = 900, text: float = 1.3, places=FLOOD_PLACES) -> None:
    """A photograph with the place names, a 5 km bar and the north, as JPEG."""
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from PIL import Image

    west, south, east, north = box
    fig = plt.figure(figsize=(4.6, 4.6 * (north - south) / (east - west)), dpi=width_px / 4.6)
    ax = fig.add_axes([0, 0, 1, 1])
    ax.imshow(picture, extent=[west, east, south, north], interpolation="bilinear", zorder=2)
    decorate(cfg, ax, box, text, places)
    ax.set_axis_off()
    buffer = io.BytesIO()
    fig.savefig(buffer, dpi=width_px / 4.6, format="png")
    plt.close(fig)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.open(buffer).convert("RGB").save(out, "JPEG", quality=80, optimize=True, progressive=True)


def export(cfg: dict, folder) -> list[dict]:
    """The flood pair in the platform package (imagens/) and its entry for the catalogue."""
    scenes = path(cfg, "sentinel2", mkdir=False).parent / "cenas_cheia_2026"
    if not all((scenes / name).exists() for _, name, _ in FLOOD_PAIR):
        return []
    out = Path(folder) / "imagens"
    pictures = {}
    for key, name, day in FLOOD_PAIR:
        file = out / f"cheia_2026_{key}.jpg"
        render_photo(cfg, natural(scenes / name, FLOOD_BOX), FLOOD_BOX, file)
        pictures[key] = {"ficheiro": f"imagens/{file.name}", "data": day, "satelite": "Sentinel-2"}
    return [{"id": "imagens_satelite", "titulo": "Imagens de satélite", "tipo": "imagens", "atualizacao": "quando houver uma nova cheia fotografada",
             "pares": [{"id": "cheia_2026", "titulo": "A cheia de Janeiro de 2026", "antes": pictures["antes"], "depois": pictures["cheia"],
                        "texto": "A 24 de Janeiro de 2026 a água cobria pelo menos 246 km² do distrito; antes da cheia eram cerca de 31 km², o rio e as lagoas.",
                        "fonte": "Copernicus Sentinel-2 (ESA), cor natural. Medição da água: índice MNDWI acima de zero."}],
             "descricao": "Fotografias reais do satélite, em cor natural: a mesma zona antes e durante a cheia de 2026.",
             "limites": "Cada fotografia é de um só dia e de uma só passagem do satélite; as nuvens tapam partes da imagem."}]
