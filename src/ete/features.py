"""Feature engineering (week 2): spectral and radar indices, rainfall features,
monthly driver tables, quantile mapping and agreement statistics.

Everything here works on arrays or tables already on disk: no internet needed.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

# -----------------------------------------------------------------------------
# Spectral and radar indices
# -----------------------------------------------------------------------------

INDEX_NAMES = ["ndwi", "mndwi", "ndvi", "ndmi", "awei_sh", "awei_nsh"]


def _ratio(a, b):
    """Normalised difference (a - b) / (a + b); NaN where the sum is not positive."""
    a, b = np.asarray(a, "float32"), np.asarray(b, "float32")
    total = a + b
    with np.errstate(divide="ignore", invalid="ignore"):
        out = (a - b) / total
    return np.where(total > 0, np.clip(out, -1, 1), np.nan).astype("float32")


def optical_indices(blue, green, red, nir, swir1, swir2) -> dict:
    """Water and vegetation indices from surface reflectance (0-1).

    ndwi   (green - nir) / (green + nir)        open water
    mndwi  (green - swir1) / (green + swir1)    open water, better near built-up areas
    ndvi   (nir - red) / (nir + red)            vegetation
    ndmi   (nir - swir1) / (nir + swir1)        vegetation / soil moisture
    awei   Automated Water Extraction Index (Feyisa et al., 2014), shadow / no-shadow forms
    """
    f = lambda x: np.asarray(x, "float32")
    blue, green, red, nir, swir1, swir2 = map(f, (blue, green, red, nir, swir1, swir2))
    return {
        "ndwi": _ratio(green, nir),
        "mndwi": _ratio(green, swir1),
        "ndvi": _ratio(nir, red),
        "ndmi": _ratio(nir, swir1),
        "awei_sh": blue + 2.5 * green - 1.5 * (nir + swir1) - 0.25 * swir2,
        "awei_nsh": 4 * (green - swir1) - (0.25 * nir + 2.75 * swir2),
    }


def water_quality_indices(green, red, red_edge1=None) -> dict:
    """Turbidity proxy NDTI = (red - green) / (red + green) and, with Sentinel-2 band 5,
    chlorophyll proxy NDCI = (red_edge1 - red) / (red_edge1 + red). Only meaningful on water."""
    out = {"ndti": _ratio(red, green)}
    if red_edge1 is not None:
        out["ndci"] = _ratio(red_edge1, red)
    return out


def radar_features(vv, vh, vv_dry=None, vh_dry=None) -> dict:
    """Radar features in dB. Smooth open water is very dark in VV.

    vv_vh_ratio  VV - VH (a ratio, because the values are in dB)
    dvv, dvh     change against the dry-season reference; strongly negative = new water
    """
    vv, vh = np.asarray(vv, "float32"), np.asarray(vh, "float32")
    out = {"vv_vh_ratio": vv - vh}
    if vv_dry is not None:
        out["dvv"] = vv - np.asarray(vv_dry, "float32")
    if vh_dry is not None:
        out["dvh"] = vh - np.asarray(vh_dry, "float32")
    return out


def twi(upstream_area_km2, slope_deg, cell_m: float = 30.0):
    """Topographic Wetness Index ln(a / tan(slope)), a = upstream area per unit contour length.
    Slopes below 0.1 degree are set to 0.1 to keep flat land finite."""
    area_m2 = np.maximum(np.asarray(upstream_area_km2, "float32"), 1e-4) * 1e6
    tan_slope = np.tan(np.radians(np.maximum(np.asarray(slope_deg, "float32"), 0.1)))
    return np.log(area_m2 / cell_m / tan_slope).astype("float32")


# -----------------------------------------------------------------------------
# Rainfall features (plan task S2-05)
# -----------------------------------------------------------------------------

def rolling_sums(daily: pd.Series, windows=(3, 7, 14, 30)) -> pd.DataFrame:
    """Accumulated rainfall over the last N days, including the day itself."""
    daily = daily.asfreq("D")
    return pd.DataFrame({f"p{w}": daily.rolling(w, min_periods=w).sum() for w in windows})


def seasonal_percentile(values: pd.Series, half_window: int = 15) -> pd.Series:
    """Percentile (0-100) of each daily value against all values of the same time of
    year (+/- half_window days) in every year of the series: the anomaly against the
    climatology of the whole period. 50 = normal, above 90 = unusually high."""
    values = values.dropna()
    doy = values.index.dayofyear.to_numpy()
    x = values.to_numpy()
    out = np.full(len(x), np.nan)
    for day in range(1, 367):
        distance = np.abs(doy - day)
        pool = np.sort(x[np.minimum(distance, 366 - distance) <= half_window])
        today = doy == day
        if today.any() and len(pool):
            out[today] = 100.0 * np.searchsorted(pool, x[today], side="right") / len(pool)
    return pd.Series(out, index=values.index)


def monthly_percentile(monthly: pd.Series) -> pd.Series:
    """Percentile (0-100) of each monthly value among the same calendar month of all years."""
    return monthly.groupby(monthly.index.month).rank(pct=True) * 100


def month_index(series_or_frame):
    """Re-index a monthly table by 'YYYY-MM' strings (the key used in every project table)."""
    out = series_or_frame.copy()
    out.index = pd.DatetimeIndex(out.index).strftime("%Y-%m")
    out.index.name = "month"
    return out


# -----------------------------------------------------------------------------
# Quantile mapping (plan task S2-07)
# -----------------------------------------------------------------------------

class QuantileMapping:
    """Empirical quantile mapping: makes the distribution of `source` match `target`.

    fit() learns, over a calibration period where both exist, which target value
    corresponds to each quantile of the source. transform() applies it to any
    period. Values outside the calibration range are shifted by the correction of
    the nearest quantile, so the tails are never flattened.
    """

    def __init__(self, n_quantiles: int = 100):
        self.q = np.linspace(0, 1, n_quantiles + 1)

    def fit(self, source, target) -> "QuantileMapping":
        pair = pd.concat([pd.Series(source), pd.Series(target)], axis=1, keys=["s", "t"]).dropna()
        self.n_ = len(pair)
        self.source_q_ = np.quantile(pair["s"], self.q)
        self.target_q_ = np.quantile(pair["t"], self.q)
        return self

    def transform(self, source):
        x = np.asarray(source, "float64")
        y = np.interp(x, self.source_q_, self.target_q_)
        low, high = x < self.source_q_[0], x > self.source_q_[-1]
        y[low] = x[low] + (self.target_q_[0] - self.source_q_[0])
        y[high] = x[high] + (self.target_q_[-1] - self.source_q_[-1])
        return pd.Series(y, index=source.index) if isinstance(source, pd.Series) else y


# -----------------------------------------------------------------------------
# Agreement statistics (plan task S2-08)
# -----------------------------------------------------------------------------

def agreement(reference, other) -> dict:
    """Agreement of `other` against `reference` on the pairs where both exist.

    r2    squared Pearson correlation (1 = the two move together perfectly)
    bias  mean(other - reference): systematic difference
    rmse  root mean squared difference
    slope of the least-squares line other = slope * reference + intercept
    """
    a, b = np.asarray(reference, "float64").ravel(), np.asarray(other, "float64").ravel()
    ok = np.isfinite(a) & np.isfinite(b)
    a, b = a[ok], b[ok]
    if len(a) < 3 or a.std() == 0 or b.std() == 0:
        return {"n": int(len(a)), "r2": np.nan, "bias": np.nan, "rmse": np.nan, "slope": np.nan}
    slope = np.cov(a, b)[0, 1] / a.var(ddof=1)
    return {"n": int(len(a)), "r2": float(np.corrcoef(a, b)[0, 1] ** 2), "bias": float((b - a).mean()),
            "rmse": float(np.sqrt(((b - a) ** 2).mean())), "slope": float(slope)}
