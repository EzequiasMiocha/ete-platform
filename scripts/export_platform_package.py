"""Cria o pacote de dados da plataforma em plataforma/dados/ (poucos MB, sem internet).

    .venv/bin/python scripts/export_platform_package.py

Reúne tudo o que a aplicação mostra: mapas em PNG com as coordenadas dos cantos, camadas em
GeoJSON, o último boletim, as séries dos gráficos e o catálogo (catalogo.json). Correr depois
de treinar modelos de novo ou de produzir novos mapas mensais. O que muda todos os dias é
atualizado por scripts/run_daily_pipeline.py.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ete import config, platform  # noqa: E402

cfg = config.load_config()
catalogue = platform.export_package(cfg)
folder = config.path(cfg, "platform")
size = sum(f.stat().st_size for f in folder.rglob("*") if f.is_file()) / 1e6
print(f"{len(catalogue['camadas'])} camadas em {folder} ({size:.1f} MB)")
for layer in catalogue["camadas"]:
    print(f"  {layer['id']:22s} {layer['tipo']:14s} {layer['ficheiro']}")
