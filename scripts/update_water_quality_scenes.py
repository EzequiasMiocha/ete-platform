"""Extrai (ou atualiza) as séries de cor da água do Incomáti imagem a imagem, com o Earth Engine.

    .venv/bin/python scripts/update_water_quality_scenes.py

Sentinel-2 desde 2017 e Landsat 8/9 desde 2013. As respostas são tabelas pequenas (centenas de KB).
Os anos já completos em disco não são pedidos de novo; o ano corrente é sempre atualizado.
"""

import sys
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import pandas as pd

from ete import config
from ete import water_quality as W

cfg = config.load_config()
folder = config.path(cfg, "water_quality")
this_year = date.today().year
for sensor, first in (("sentinel2", 2017), ("landsat89", 2013)):
    for year in range(first, this_year + 1):
        out = folder / f"{sensor}_{year}.csv"
        if out.exists() and year < this_year:
            continue
        table = W.extract_scene_series(cfg, sensor, year, year)
        table.to_csv(out, index=False)
        print(f"{sensor} {year}: {len(table)} linhas", flush=True)
print("concluído")
