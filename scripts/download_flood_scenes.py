"""Cenas de um só dia, antes e durante a cheia de janeiro de 2026 (Landsat e Sentinel-2).

    .venv/bin/python scripts/download_flood_scenes.py

Os compósitos mensais (mediana do mês) apagam uma cheia que dura poucos dias. Aqui
descarregam-se cenas de datas escolhidas, sem nuvens sobre Marracuene, a partir de
reports/apresentacao/passagens_2025_2026.csv:

  Primeira escolha (nuvens medidas depois SÓ dentro do distrito: 21-65%, fica guardada):
    antes    24 out 2025   Landsat 8 e Sentinel-2C órbita 92, no mesmo dia
    depois   27 jan 2026   Sentinel-2B órbita 92;  28 jan 2026  Landsat 8 (65% de nuvens no distrito)
  Escolha final (nuvens no distrito):
    antes    22 set 2025   Landsat 9 (0%)            23 out 2025  Sentinel-2A órbita 49 (0%)
    cheia    24 jan 2026   Sentinel-2B órbita 49 (25%), caudal ~1700 m³/s, 5 dias depois do pico
             (nenhum Landsat apanhou o distrito sem nuvens durante a cheia)
    recuo    08 fev 2026   Sentinel-2C órbita 49 (0%)  13 fev 2026  Landsat 8 (9%)

Ficheiros em data/raw/optical/cenas_cheia_2026/ (int16, reflectância x 10000, banda `nuvem`
0/1). Distrito inteiro a 30 m para os dois satélites (comparáveis entre si) e a zona agrícola
da figura 3 a 10 m para o Sentinel-2. Internet: ~130 MB a primeira escolha, ~125 MB a final.
"""

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

import ee  # noqa: E402
from pyproj import Transformer  # noqa: E402

from ete.config import load_config  # noqa: E402
from ete.gee import download_image, init  # noqa: E402
from ete.grid import load_aoi, load_grid, snapped_grid  # noqa: E402

OUT = ROOT / "data/raw/optical/cenas_cheia_2026"
FIELDS = (32.765, -25.515, 32.815, -25.470)   # a mesma zona agrícola de build_presentation_figures.py
BANDS = ["blue", "green", "red", "swir1", "nuvem"]
SCALE = {"blue": 10000, "green": 10000, "red": 10000, "swir1": 10000, "nuvem": 1}

SCENES = [  # (nome, sensor, data, órbita relativa do Sentinel-2, distrito a 30 m, zona agrícola a 10 m)
    ("antes_2025-10-24", "landsat", "2025-10-24", None, True, False),
    ("antes_2025-10-24", "sentinel2", "2025-10-24", 92, True, True),
    ("depois_2026-01-27", "sentinel2", "2026-01-27", 92, True, True),
    ("depois_2026-01-28", "landsat", "2026-01-28", None, True, False),
    ("antes_2025-09-22", "landsat", "2025-09-22", None, True, False),
    ("antes_2025-10-23", "sentinel2", "2025-10-23", 49, True, True),
    ("cheia_2026-01-24", "sentinel2", "2026-01-24", 49, True, True),
    ("recuo_2026-02-08", "sentinel2", "2026-02-08", 49, False, True),
    ("recuo_2026-02-13", "landsat", "2026-02-13", None, True, False),
]


def sentinel2(day: str, orbit: int, region) -> ee.Image:
    end = ee.Date(day).advance(1, "day")
    col = ee.ImageCollection("COPERNICUS/S2_SR_HARMONIZED").filterDate(day, end).filterBounds(region)
    col = col.filter(ee.Filter.eq("SENSING_ORBIT_NUMBER", orbit))
    if col.size().getInfo() == 0:
        raise RuntimeError(f"sem Sentinel-2 SR em {day}, órbita {orbit}")
    img = col.mosaic()
    scl = img.select("SCL")
    cloud = scl.eq(3).Or(scl.eq(8)).Or(scl.eq(9)).Or(scl.eq(10)).rename("nuvem")
    return img.select(["B2", "B3", "B4", "B11"], BANDS[:4]).divide(10000).addBands(cloud)


def landsat(day: str, region) -> ee.Image:
    end = ee.Date(day).advance(1, "day")
    col = (ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(ee.ImageCollection("LANDSAT/LC09/C02/T1_L2"))
           .filterDate(day, end).filterBounds(region))
    if col.size().getInfo() == 0:
        raise RuntimeError(f"sem Landsat em {day}")
    img = col.mosaic()
    qa = img.select("QA_PIXEL")
    cloud = qa.bitwiseAnd((1 << 1) | (1 << 3) | (1 << 4)).neq(0).rename("nuvem")   # nuvem dilatada, nuvem, sombra
    sr = img.select(["SR_B2", "SR_B3", "SR_B4", "SR_B6"], BANDS[:4]).multiply(0.0000275).add(-0.2)
    return sr.addBands(cloud)


def main() -> None:
    cfg = load_config()
    cfg["gee"]["workers"] = 3          # projecto em modo restrito: no máximo ~3 pedidos ao mesmo tempo
    init(cfg)
    aoi = load_aoi(cfg)
    region = ee.Geometry(aoi.to_crs(4326).geometry.iloc[0].__geo_interface__)
    grid30 = load_grid(cfg)
    t = Transformer.from_crs(4326, grid30.crs, always_xy=True)
    (x0, y0), (x1, y1) = t.transform(FIELDS[0], FIELDS[1]), t.transform(FIELDS[2], FIELDS[3])
    fields10 = snapped_grid((x0 - 300, y0 - 300, x1 + 300, y1 + 300), grid30.crs, 10, snap=30)
    OUT.mkdir(parents=True, exist_ok=True)
    for name, sensor, day, orbit, full, crop in SCENES:
        jobs = [(grid30, f"{sensor}_{name}_30m.tif")] if full else []
        if crop:
            jobs.append((fields10, f"{sensor}_{name}_zona_agricola_10m.tif"))
        if all((OUT / fname).exists() for _, fname in jobs):
            continue
        img = sentinel2(day, orbit, region) if sensor == "sentinel2" else landsat(day, region)
        for grid, fname in jobs:
            out = OUT / fname
            if out.exists():
                print("já existe:", fname)
                continue
            download_image(img, BANDS, grid, out, cfg, dtype="int16", scale=SCALE,
                           tags={"sensor": sensor, "data": day, "orbita": orbit or ""})
            print(f"{fname:55s} {out.stat().st_size / 1e6:6.1f} MB", flush=True)


if __name__ == "__main__":
    main()
