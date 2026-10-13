"""Hydro-meteorological driver tables (week 2).

Turns the coarse daily grids (rain, soil moisture, runoff, discharge) into tidy
daily and monthly tables for two areas: the whole Incomati basin (what feeds the
river) and the Marracuene district (what falls locally).

Tables are written to data/processed/series/ as CSV, indexed by date (daily) or
by 'YYYY-MM' (monthly).
"""

from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import series
from .config import path
from .features import month_index, monthly_percentile, rolling_sums, seasonal_percentile
from .grid import load_aoi

AREAS = ("basin", "district")


def table(cfg: dict, name: str) -> Path:
    return path(cfg, "series", f"{name}.csv")


def read_table(cfg: dict, name: str) -> pd.DataFrame:
    """Read a table of data/processed/series/. Daily tables get a DatetimeIndex."""
    file = table(cfg, name)
    if not file.exists():
        raise FileNotFoundError(f"{file.name} not found: run the week-2 notebook that builds it first.")
    df = pd.read_csv(file, index_col=0)
    if df.index.name == "date":
        df.index = pd.to_datetime(df.index)
    return df


def _area_means(cfg: dict, folder_key: str, var_name: str) -> pd.DataFrame:
    da = series.open_series(cfg, folder_key, var_name)
    return pd.DataFrame({area: series.area_mean(da, load_aoi(cfg, area)) for area in AREAS})


# -----------------------------------------------------------------------------
# Rainfall (S2-05)
# -----------------------------------------------------------------------------

def build_rain_tables(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily and monthly rainfall features from CHIRPS (IMERG kept alongside for comparison).

    Daily columns, for each area: rain (mm), p3/p7/p14/p30 (accumulated mm) and
    p7_pct/p30_pct (percentile against the same time of year in all years).
    """
    chirps = _area_means(cfg, "chirps", cfg["datasets"]["chirps"]["band"])
    imerg = _area_means(cfg, "imerg", cfg["datasets"]["imerg"]["band"])

    daily = pd.DataFrame(index=pd.date_range(chirps.index.min(), max(chirps.index.max(), imerg.index.max()), name="date"))
    for area in AREAS:
        rain = chirps[area].reindex(daily.index)
        daily[f"rain_{area}"] = rain
        sums = rolling_sums(rain)
        for col in sums:
            daily[f"{col}_{area}"] = sums[col]
        daily[f"p7_pct_{area}"] = seasonal_percentile(sums["p7"])
        daily[f"p30_pct_{area}"] = seasonal_percentile(sums["p30"])
        daily[f"imerg_{area}"] = imerg[area].reindex(daily.index)

    by_month = daily.resample("MS")
    monthly = pd.DataFrame(index=by_month.size().index)
    for area in AREAS:
        days = by_month[f"rain_{area}"].count()
        full = days == monthly.index.days_in_month                   # only complete months get a total
        monthly[f"rain_{area}_mm"] = by_month[f"rain_{area}"].sum().where(full)
        monthly[f"rain_{area}_max_day"] = by_month[f"rain_{area}"].max().where(full)
        monthly[f"rain_{area}_max_p7"] = by_month[f"p7_{area}"].max().where(full)
        monthly[f"rain_{area}_pct"] = monthly_percentile(monthly[f"rain_{area}_mm"])
        monthly[f"rain_{area}_p30_pct_max"] = by_month[f"p30_pct_{area}"].max().where(full)
        imerg_days = by_month[f"imerg_{area}"].count()
        monthly[f"imerg_{area}_mm"] = by_month[f"imerg_{area}"].sum().where(imerg_days == monthly.index.days_in_month)
    monthly = month_index(monthly)

    daily.round(3).to_csv(table(cfg, "rain_daily"))
    monthly.round(3).to_csv(table(cfg, "rain_monthly"))
    return daily, monthly


# -----------------------------------------------------------------------------
# Soil moisture, runoff, temperature, discharge (S2-06)
# -----------------------------------------------------------------------------

def glofas_series(cfg: dict) -> pd.DataFrame:
    """Daily discharge (m3/s) at the main-stem cell of the Incomati inside the district:
    the cell with the highest mean discharge. `provisional` marks the intermediate product."""
    import xarray as xr

    folder = path(cfg, "glofas", mkdir=False)
    parts = []
    for file in sorted(folder.glob("glofas_discharge_*.nc")):
        with xr.open_dataset(file) as ds:
            da = ds["avg_dis"].load()
        parts.append(da.assign_coords(provisional=("valid_time", np.full(da.sizes["valid_time"], "intermediate" in file.name))))
    dis = xr.concat(parts, dim="valid_time").sortby("valid_time")
    w, s, e, n = load_aoi(cfg, "district").total_bounds
    local = dis.where((dis.latitude >= s) & (dis.latitude <= n) & (dis.longitude >= w) & (dis.longitude <= e), drop=True)
    mean = local.where(~local.provisional).mean("valid_time")
    flat = mean.to_series().dropna()
    lat, lon = flat.idxmax()
    cell = dis.sel(latitude=lat, longitude=lon)
    out = pd.DataFrame({"discharge_m3s": cell.values, "provisional": cell.provisional.values},
                       index=pd.DatetimeIndex(cell.valid_time.values).normalize().rename("date"))
    out.attrs["cell"] = (float(lat), float(lon))
    return out[~out.index.duplicated(keep="first")]


def build_hydromet_tables(cfg: dict) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Daily and monthly tables of ERA5-Land, SMAP and GloFAS.

    Units: soil moisture m3/m3, runoff and evaporation mm/day (monthly: mm/month),
    temperature degrees C, discharge m3/s.
    """
    frames = {}
    for band, (name, convert) in {
        "volumetric_soil_water_layer_1": ("sm_era5_l1", lambda x: x),
        "volumetric_soil_water_layer_2": ("sm_era5_l2", lambda x: x),
        "surface_runoff_sum": ("runoff_mm", lambda x: x * 1000),
        "total_evaporation_sum": ("evap_mm", lambda x: -x * 1000),      # ERA5 sign: evaporation is negative
        "temperature_2m": ("temp_c", lambda x: x - 273.15),
    }.items():
        means = convert(_area_means(cfg, "era5_land", band))
        for area in AREAS:
            frames[f"{name}_{area}"] = means[area]
    for band, name in {"sm_surface": "smap_surface", "sm_rootzone": "smap_rootzone"}.items():
        means = _area_means(cfg, "smap", band)
        for area in AREAS:
            frames[f"{name}_{area}"] = means[area]
    daily = pd.DataFrame(frames)
    daily.index = pd.DatetimeIndex(daily.index).normalize().rename("date")

    q = glofas_series(cfg)
    daily = daily.join(q, how="outer")
    daily.index.name = "date"

    by_month = daily.resample("MS")
    monthly = by_month.mean(numeric_only=True).drop(columns=["discharge_m3s"])
    for col in [c for c in monthly if c.startswith(("runoff_mm", "evap_mm"))]:
        monthly[col] = by_month[col].sum(min_count=25)
    monthly["q_mean"] = by_month["discharge_m3s"].mean()
    monthly["q_max"] = by_month["discharge_m3s"].max()
    monthly["q_pct"] = monthly_percentile(monthly["q_mean"])
    monthly["q_provisional"] = by_month["provisional"].max().astype("float")
    # a month only counts when most of its days exist
    enough = by_month.count().drop(columns=["provisional"]).rename(columns={"discharge_m3s": "q_mean"}) >= 25
    for col in enough:
        if col in monthly:
            monthly[col] = monthly[col].where(enough[col])
    monthly.loc[~enough["q_mean"], ["q_max", "q_pct"]] = np.nan
    monthly = month_index(monthly)

    daily.round(5).to_csv(table(cfg, "hydromet_daily"))
    monthly.round(5).to_csv(table(cfg, "hydromet_monthly"))
    monthly.attrs["glofas_cell"] = q.attrs["cell"]
    return daily, monthly


# -----------------------------------------------------------------------------
# One monthly table for the training datasets
# -----------------------------------------------------------------------------

LAGGED = ["rain_basin_mm", "rain_district_mm", "sm_cal_basin", "q_mean"]


def load_monthly_drivers(cfg: dict) -> pd.DataFrame:
    """All monthly drivers in one table indexed by 'YYYY-MM', plus the previous month's
    value (`*_lag1`) of the main ones: floods depend on what came before, too."""
    monthly = read_table(cfg, "rain_monthly").join(read_table(cfg, "hydromet_monthly"), how="outer")
    calibrated = table(cfg, "soil_moisture_calibrated_monthly")
    if calibrated.exists():
        monthly = monthly.join(pd.read_csv(calibrated, index_col=0), how="left")
    full = pd.period_range(monthly.index.min(), monthly.index.max(), freq="M").strftime("%Y-%m")
    monthly = monthly.reindex(full).rename_axis("month")
    for col in [c for c in LAGGED if c in monthly]:
        monthly[f"{col}_lag1"] = monthly[col].shift(1)
    return monthly
