"""Acrescenta as bandas VV_p10 e VH_p10 aos meses de Sentinel-1 já descarregados.

Só as duas bandas novas são descarregadas (cerca de 25 MB por mês) e juntas ao
ficheiro existente. Pode ser interrompido e retomado: os meses já completos são
saltados.

    .venv/bin/python scripts/add_s1_p10.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd
import rasterio

from ete import config, datasets, gee, rasters
from ete import grid as G

cfg = config.load_config()
gee.init(cfg)
want = cfg["datasets"]["sentinel1"]["bands"] + ["n_obs"]
new = ["VV_p10", "VH_p10"]
region = gee.ee_geometry(G.load_aoi(cfg))
mask = gee.ee_geometry(G.imagery_mask(cfg))
grid10 = G.load_grid(cfg, 10)

def process(month, file):
    with rasterio.open(file) as src:
        have = list(src.descriptions)
        if have == want:
            return
        profile, tags, old, scales = src.profile, src.tags(), src.read(), dict(zip(have, src.scales))
    orbit = tags.get("orbit_pass", "ASCENDING")
    nxt = (pd.Timestamp(month + "-01") + pd.offsets.MonthBegin(1)).strftime("%Y-%m-%d")
    image, _ = datasets.sentinel1_builder(cfg, region, orbit)(month + "-01", nxt)
    tmp = file.with_name(file.stem + ".p10.tif")
    try:
        gee.download_image(image, new, grid10, tmp, cfg, dtype="int16", scale=100, mask=mask)
    except Exception as err:
        print(f"falhou   {month}: {repr(err)[:160]}", flush=True)
        return
    with rasterio.open(tmp) as src:
        extra = dict(zip(new, src.read()))
    agree = float(((extra["VV_p10"] == -9999) == (old[have.index("VV")] == -9999)).mean())
    data = np.stack([extra[b] if b in extra else old[have.index(b)] for b in want])
    profile.update(count=len(want))
    part = file.with_name(file.stem + ".part.tif")
    with rasterio.open(part, "w", **profile) as dst:
        dst.write(data)
        for i, band in enumerate(want, start=1):
            dst.set_band_description(i, band)
        dst.scales = [scales.get(b, 0.01) for b in want]
        dst.update_tags(**tags, p10_added="yes")
    part.replace(file)
    file.with_name(file.name + ".aux.xml").unlink(missing_ok=True)
    size = tmp.stat().st_size / 1e6
    tmp.unlink()
    print(f"ok       {month}  +{size:.0f} MB  nodata igual à mediana: {agree:.4f}", flush=True)


import os

# vários processos podem correr ao mesmo tempo (ex.: um do início, outro do fim com "reverse"):
# cada mês em curso fica marcado com um ficheiro .lock, que os outros processos respeitam
months = rasters.available_months(cfg, "sentinel1")
if "reverse" in sys.argv:
    months = months[::-1]
if "middle" in sys.argv:
    half = len(months) // 2
    months = months[half:] + months[:half]

for month in months:
    file = rasters.monthly_file(cfg, "sentinel1", month)
    lock = file.with_suffix(".lock")
    try:
        os.close(os.open(lock, os.O_CREAT | os.O_EXCL))
    except FileExistsError:
        continue
    try:
        process(month, file)
    finally:
        lock.unlink(missing_ok=True)
print("concluído")
