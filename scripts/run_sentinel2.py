"""Download the Sentinel-2 monthly composites from the command line.

Same recipe and parameters as notebooks/07_sentinel2_monthly_composites.ipynb,
for long runs outside Jupyter. Resumable: existing months are skipped.

    .venv/bin/python scripts/run_sentinel2.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ete import config, datasets, gee
from ete import grid as G

cfg = config.load_config()
gee.init(cfg)
ds = cfg["datasets"]["sentinel2"]
region = gee.ee_geometry(G.load_aoi(cfg))
log = gee.download_monthly(
    cfg, "sentinel2", ds["id"], datasets.sentinel2_builder(cfg, region),
    list(ds["bands"].values()) + ["n_obs"], G.load_grid(cfg, 10), config.path(cfg, "sentinel2"),
    start=ds["start"], dtype="int16", scale=10000, mask=gee.ee_geometry(G.imagery_mask(cfg)),
)
print(log["status"].value_counts().to_string())
