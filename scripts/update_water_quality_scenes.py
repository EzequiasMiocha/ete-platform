"""Extrai (ou atualiza) as séries de cor da água do Incomáti imagem a imagem, com o Earth Engine.

    .venv/bin/python scripts/update_water_quality_scenes.py

Sentinel-2 desde 2017 e Landsat 8/9 desde 2013. As respostas são tabelas pequenas (centenas de KB).
Os anos já completos em disco não são pedidos de novo; o ano corrente é sempre atualizado.
No fim, descarrega o mapa da cor da água do dia mais recente com o rio legível (0,2 a 0,5 MB)
e põe-no no pacote da plataforma. Depois é só enviar: .venv/bin/python scripts/publicar_plataforma.py
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

# O mapa da cor da água (o dia mais recente com o rio legível): cerca de 0,2 a 0,5 MB
try:
    from ete import platform, turbidity_map
    turbidity_map.update(cfg, log=lambda m: print(m, flush=True))
    platform.refresh_water_colour(cfg)          # o mapa novo entra no pacote da plataforma: depois é só enviar
    from ete import water_colour_model           # a cor de Marracuene nos dias novos: o ponto de partida da previsão a 30 dias
    water_colour_model.update_driver_values(cfg, log=lambda m: print(m, flush=True))
    water_colour_model.monthly_maps(cfg, log=lambda m: print(m, flush=True))      # o mapa do mês que acabou (cerca de 25 KB)
    platform.refresh_water_colour(cfg)
except Exception as erro:                       # o mapa nunca impede a actualização das séries
    print(f"mapa da cor da água: não foi possível actualizar ({erro})", flush=True)
print("concluído")
