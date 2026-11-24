"""Gera os mapas mensais de água e cheia do Modelo B (radar) para todos os meses de Sentinel-1.

    .venv/bin/python scripts/run_model_b_maps.py

Cerca de 40 segundos por mês; os meses já feitos são saltados.
"""

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ete import config, rasters
from ete import models as M

cfg = config.load_config()
model, features = M.load_model(cfg, "modelo_b_radar")
months = rasters.available_months(cfg, "sentinel1")
for i, month in enumerate(months, start=1):
    start = time.time()
    done = M.water_map_file(cfg, month).exists()
    M.water_map(cfg, model, features, month)
    if not done:
        print(f"{i}/{len(months)} {month} ({time.time() - start:.0f} s)", flush=True)
M.flood_area_series(cfg).round(3).to_csv(config.path(cfg, "series", "modelo_b_area_mensal.csv"))
print("concluído")
