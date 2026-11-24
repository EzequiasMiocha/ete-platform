"""Módulo Q: extrai (ou atualiza) os valores de cor da água por imagem e por troço, da fronteira à foz.

    .venv/bin/python scripts/update_module_q_series.py            # todos os sensores
    .venv/bin/python scripts/update_module_q_series.py sentinel2  # só um

Landsat 5/7 (2006-2013), Landsat 8/9 (2013-hoje) e Sentinel-2 (2017-hoje), no Earth Engine.
As respostas são tabelas (cerca de 10 a 20 MB na primeira vez; depois só o ano corrente).
Os anos já completos em disco não são pedidos de novo.

Antes da primeira vez, os troços e a máscara de água têm de existir (notebook 29) e ser
enviados para o Earth Engine: isso é feito aqui se ainda não estiver feito.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import ee  # noqa: E402

from ete import config, module_q  # noqa: E402
from ete.gee import init  # noqa: E402

cfg = config.load_config()
init(cfg)
try:
    ee.data.getAsset(module_q.regions_asset(cfg))
except ee.EEException:
    print("a enviar os polígonos dos troços para o Earth Engine...", flush=True)
    module_q.upload_regions(cfg)
sensors = [a for a in sys.argv[1:] if a in module_q.SENSORS] or None
module_q.update_series(cfg, sensors, log=lambda m: print(m, flush=True))
print("concluído")
