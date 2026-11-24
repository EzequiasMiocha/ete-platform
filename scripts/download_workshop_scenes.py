"""Imagens para o Workshop de Estudantes 1 (aula prática): seca e estação chuvosa de 11 anos.

    .venv/bin/python scripts/download_workshop_scenes.py

Só a planície do Incomáti em Marracuene (32.64-32.86 E, 25.47-25.77 S, 22 x 33 km), a 30 m,
bandas azul, verde, vermelho, nir, swir1 e `nuvem` (1 = nuvem, sombra ou sem dados).
Ficheiros em data/raw/optical/workshop_1/. Internet: cerca de 200 MB, uma vez.

As datas foram escolhidas medindo as nuvens SÓ dentro desta área (Earth Engine, 2026-10-26):
  chuvosa  a imagem mais limpa perto do pico de caudal do ano (GloFAS)
  seca     uma imagem limpa da estação seca anterior (jul-nov)
Landsat 8 para 2014-2017 (o Sentinel-2 com correcção atmosférica quase não existe antes de 2019
nesta zona); Sentinel-2 para 2019-2026. 2015 saiu da lista: nenhuma imagem Landsat da estação
chuvosa tinha mais de metade da planície sem nuvens. 2026 é o exemplo do notebook guiado.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ee  # noqa: E402
from pyproj import Transformer  # noqa: E402

from ete.config import load_config  # noqa: E402
from ete.gee import download_image, init  # noqa: E402
from ete.grid import snapped_grid  # noqa: E402

OUT = ROOT / "data/raw/optical/workshop_1"
BOX = (32.64, -25.77, 32.86, -25.47)          # oeste, sul, leste, norte (graus)
BANDS = ["azul", "verde", "vermelho", "nir", "swir", "nuvem"]
SCALE = {b: 10000 for b in BANDS[:5]} | {"nuvem": 1}

# ano: (satélite, data seca, data chuvosa)
SCENES = {
    2014: ("landsat", "2013-08-04", "2014-03-16"),
    2016: ("landsat", "2015-10-13", "2016-04-22"),
    2017: ("landsat", "2016-10-15", "2017-03-08"),
    2019: ("sentinel2", "2018-09-28", "2019-02-18"),
    2020: ("sentinel2", "2019-09-21", "2020-02-15"),
    2021: ("sentinel2", "2020-09-25", "2021-01-30"),
    2022: ("sentinel2", "2021-09-25", "2022-01-10"),
    2023: ("sentinel2", "2022-09-25", "2023-02-22"),
    2024: ("sentinel2", "2023-09-30", "2024-01-20"),
    2025: ("sentinel2", "2024-09-04", "2025-01-24"),
    2026: ("sentinel2", "2025-10-23", "2026-01-24"),
}


def sentinel2(day: str, region) -> ee.Image:
    col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(day, ee.Date(day).advance(1, "day")).filterBounds(region)
    img = col.mosaic()
    scl = img.select("SCL")
    bad = scl.eq(0).Or(scl.eq(1)).Or(scl.eq(3)).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10))
    refl = img.select(["B2", "B3", "B4", "B8", "B11"], BANDS[:5]).divide(10000)
    return refl.addBands(bad.rename("nuvem"))


def landsat(day: str, region) -> ee.Image:
    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
           .filterDate(day, ee.Date(day).advance(1, "day")).filterBounds(region))
    img = col.mosaic()
    qa = img.select("QA_PIXEL")
    bad = qa.bitwiseAnd((1 << 0) | (1 << 1) | (1 << 3) | (1 << 4)).neq(0)    # sem dados, nuvem dilatada, nuvem, sombra
    refl = img.select(["SR_B2", "SR_B3", "SR_B4", "SR_B5", "SR_B6"], BANDS[:5]).multiply(0.0000275).add(-0.2)
    return refl.addBands(bad.rename("nuvem"))


def main() -> None:
    cfg = load_config()
    cfg["gee"]["workers"] = 3            # projecto em modo restrito: no máximo ~3 pedidos ao mesmo tempo
    init(cfg)
    region = ee.Geometry.Rectangle(list(BOX))
    t = Transformer.from_crs(4326, "EPSG:32736", always_xy=True)
    (x0, y0), (x1, y1) = t.transform(BOX[0], BOX[1]), t.transform(BOX[2], BOX[3])
    grid = snapped_grid((x0, y0, x1, y1), "EPSG:32736", 30)
    print(f"grelha: {grid.width} x {grid.height} píxeis de 30 m")
    OUT.mkdir(parents=True, exist_ok=True)
    for ano, (sensor, seca, chuvosa) in SCENES.items():
        for epoca, day in (("seca", seca), ("chuvosa", chuvosa)):
            out = OUT / f"{ano}_{epoca}_{sensor}_{day}_30m.tif"
            if out.exists():
                continue
            img = sentinel2(day, region) if sensor == "sentinel2" else landsat(day, region)
            download_image(img, BANDS, grid, out, cfg, dtype="int16", scale=SCALE,
                           tags={"ano": ano, "epoca": epoca, "satelite": sensor, "data": day})
            print(f"{out.name:48s} {out.stat().st_size / 1e6:5.1f} MB", flush=True)


if __name__ == "__main__":
    main()
