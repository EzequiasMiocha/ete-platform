"""Overlap analysis (week 2, task S2-08): do independent sources agree where they coexist?

Each function returns a table of paired samples; the notebook turns them into
R2, bias and figures.
"""

from __future__ import annotations

import numpy as np
import pandas as pd
import rasterio

from .features import optical_indices
from .rasters import monthly_file, sample_raster
from .training import OPTICAL, sampling_frame


def _random_pixels(rng, mask: np.ndarray, n: int):
    idx = np.flatnonzero(mask)
    take = rng.choice(idx, size=min(n, len(idx)), replace=False)
    return np.unravel_index(take, mask.shape)


def landsat_vs_sentinel2(cfg: dict, months: list[str], n_land: int = 3000, n_water: int = 1000) -> pd.DataFrame:
    """Same pixels, same month, two satellites. Sentinel-2 (10 m) is first averaged to
    the 30 m Landsat pixel (3 x 3 block mean of reflectance), then indices are compared.
    Pixels are drawn at random, part of them in places that are often water."""
    frame = sampling_frame(cfg)
    rng = np.random.default_rng(cfg["processing"]["seed"] + 10)
    often_water = frame["domain"] & (frame["static"]["jrc_occurrence"] >= 50)
    parts = []
    for month in months:
        f_l, f_s = monthly_file(cfg, "landsat", month), monthly_file(cfg, "sentinel2", month)
        if f_l is None or f_s is None:
            continue
        r1, c1 = _random_pixels(rng, frame["domain"] & ~often_water, n_land)
        r2, c2 = _random_pixels(rng, often_water, n_water)
        rows, cols = np.concatenate([r1, r2]), np.concatenate([c1, c2])
        landsat = sample_raster(f_l, rows, cols, OPTICAL)
        s2 = {}
        with rasterio.open(f_s) as src:
            names = list(src.descriptions)
            for band in OPTICAL:
                i = names.index(band) + 1
                raw = src.read(i)
                block = np.stack([raw[rows * 3 + dr, cols * 3 + dc] for dr in range(3) for dc in range(3)]).astype("float32")
                block[block == src.nodata] = np.nan
                # a 30 m pixel is used only when all nine 10 m pixels were observed
                s2[band] = block.mean(axis=0) * np.float32(src.scales[i - 1])
        ind_l = optical_indices(*(landsat[b].to_numpy() for b in OPTICAL))
        ind_s = optical_indices(*(s2[b] for b in OPTICAL))
        part = pd.DataFrame({"month": month, "often_water": np.r_[np.zeros(len(r1), bool), np.ones(len(r2), bool)]})
        for name in ("ndwi", "mndwi", "ndvi", "ndmi"):
            part[f"{name}_landsat"], part[f"{name}_s2"] = ind_l[name], ind_s[name]
        for band in OPTICAL:
            part[f"{band}_landsat"], part[f"{band}_s2"] = landsat[band].to_numpy(), s2[band]
        parts.append(part.dropna())
    return pd.concat(parts, ignore_index=True)


def jrc_vs_sentinel1(cfg: dict, months: list[str], n: int = 4000) -> pd.DataFrame:
    """JRC monthly water (from Landsat) against Sentinel-1 backscatter on the same pixels:
    two independent ways of seeing water. Half of the sample is JRC water, half is not."""
    frame = sampling_frame(cfg)
    rng = np.random.default_rng(cfg["processing"]["seed"] + 11)
    parts = []
    for month in months:
        f_j, f_s = monthly_file(cfg, "jrc_monthly", month), monthly_file(cfg, "sentinel1", month)
        if f_j is None or f_s is None:
            continue
        with rasterio.open(f_j) as src:
            water = src.read(1)
        picks = []
        for value in (1, 2):
            mask = frame["domain"] & (water == value)
            if mask.sum() >= 50:
                picks.append(_random_pixels(rng, mask, n // 2))
        if len(picks) < 2:
            continue
        rows, cols = np.concatenate([p[0] for p in picks]), np.concatenate([p[1] for p in picks])
        s1 = sample_raster(f_s, rows * 3 + 1, cols * 3 + 1, ["VV", "VH"])
        part = pd.DataFrame({"month": month, "jrc_water": water[rows, cols] == 2,
                             "permanent": frame["permanent"][rows, cols],
                             "in_district": frame["district"][rows, cols],
                             "vv": s1["VV"].to_numpy(), "vh": s1["VH"].to_numpy()})
        parts.append(part.dropna())
    return pd.concat(parts, ignore_index=True)
