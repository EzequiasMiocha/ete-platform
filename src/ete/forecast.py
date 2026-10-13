"""Daily forecast for production: flood-alert outlook and its inputs.

What is forecast, and from what:

* River discharge at Marracuene for the next 30 days, as 51 scenarios (GloFAS v4
  ensemble served by the Open-Meteo flood API). The alert level of each day is
  the share of scenarios above the alert limits.
* Rain over the Incomati basin for the next 16 days (ECMWF IFS), turned into
  7-day totals and compared with the normal for the time of year.

The limits are computed once from the same service's history up to
`calibration_end` and saved to models/limites_previsao.json, so a bulletin can
always be traced to the limits that produced it.

Every run stores its raw inputs under data/raw/forecast/runs/<date>/ and its
results under data/processed/forecast/archive/<date>/. That archive is what will
allow the forecasts to be verified against what really happened.
"""

from __future__ import annotations

import json
import time
from datetime import date, datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd
import requests

from .alerts import LEVELS
from .config import path
from .grid import load_aoi


# ----------------------------------------------------------------------------- download
def fetch_json(url: str, params: dict, tries: int = 5, wait: float = 6.0):
    """GET with retries (the mobile link drops requests now and then)."""
    for attempt in range(tries):
        try:
            response = requests.get(url, params=params, timeout=120)
            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt == tries - 1:
                raise
            time.sleep(wait * (attempt + 1))


def basin_points(cfg: dict) -> list[tuple[float, float]]:
    """(lat, lon) of the lattice points inside the Incomati basin, used to average the rain."""
    from shapely.geometry import Point

    basin = load_aoi(cfg, "basin")
    west, south, east, north = basin.total_bounds
    shape = basin.union_all()
    step = cfg["forecast"]["rain_lattice_deg"]
    return [(float(y), float(x)) for y in np.arange(south + step / 2, north, step)
            for x in np.arange(west + step / 2, east, step) if shape.contains(Point(x, y))]


def _rain_params(cfg: dict) -> dict:
    points = basin_points(cfg)
    return {"latitude": ",".join(f"{a:.3f}" for a, _ in points), "longitude": ",".join(f"{b:.3f}" for _, b in points),
            "daily": "precipitation_sum", "timezone": "GMT"}


def _basin_mean(payload) -> pd.Series:
    payload = payload if isinstance(payload, list) else [payload]
    frame = pd.DataFrame({i: p["daily"]["precipitation_sum"] for i, p in enumerate(payload)},
                         index=pd.to_datetime(payload[0]["daily"]["time"]))
    return frame.astype("float64").mean(axis=1).rename("rain")


# ----------------------------------------------------------------------------- history
def history_files(cfg: dict) -> dict:
    folder = path(cfg, "forecast_raw", "history")
    return {"discharge": folder / "discharge_history.csv", "rain": folder / "rain_era5_basin.csv"}


def update_history(cfg: dict, today: date | None = None) -> dict:
    """Create or extend the long history used for limits and model training.

    discharge: daily GloFAS v4 at the chosen cell; rain: daily ERA5 basin mean. Only the days
    missing since the last update are downloaded.
    """
    f = cfg["forecast"]
    today = today or datetime.now(timezone.utc).date()
    files = history_files(cfg)
    lat, lon = f["discharge_point"]

    def extend(file: Path, start: str, fetch):
        old = pd.read_csv(file, index_col=0, parse_dates=True).iloc[:, 0] if file.exists() else None
        first = (old.dropna().index.max() - pd.Timedelta(days=10)).date() if old is not None else pd.Timestamp(start).date()
        new = fetch(first)
        if old is not None:
            new = pd.concat([old[old.index < new.index.min()], new])
        new[~new.index.duplicated(keep="last")].rename_axis("date").to_csv(file)

    def discharge(first):
        j = fetch_json(f["flood_api"], {"latitude": lat, "longitude": lon, "daily": "river_discharge",
                                        "start_date": str(first), "end_date": str(today)})
        return pd.Series(j["daily"]["river_discharge"], index=pd.to_datetime(j["daily"]["time"]), name="q", dtype="float64")

    def rain(first):
        last = today - pd.Timedelta(days=6)                      # ERA5 is published about 5 days late
        parts, year = [], first.year
        while year <= last.year:                                 # six years per request keeps answers small
            a = max(first, date(year, 1, 1))
            b = min(last, date(year + 5, 12, 31))
            parts.append(_basin_mean(fetch_json(f["archive_api"], {**_rain_params(cfg), "start_date": str(a), "end_date": str(b)})))
            year += 6
        return pd.concat(parts)

    extend(files["discharge"], f["history_start"], discharge)
    extend(files["rain"], f["rain_history_start"], rain)
    return files


def load_history(cfg: dict) -> pd.DataFrame:
    """Daily table with `q` (m3/s) and `rain` (mm, basin mean)."""
    files = history_files(cfg)
    if not all(f.exists() for f in files.values()):
        raise FileNotFoundError("forecast history missing: run forecast.update_history(cfg) (needs internet once)")
    q = pd.read_csv(files["discharge"], index_col=0, parse_dates=True).iloc[:, 0].rename("q")
    rain = pd.read_csv(files["rain"], index_col=0, parse_dates=True).iloc[:, 0].rename("rain")
    return pd.concat([q, rain], axis=1).sort_index()


# ----------------------------------------------------------------------------- limits
def limits_file(cfg: dict) -> Path:
    return path(cfg, "models", "limites_previsao.json")


def build_limits(cfg: dict) -> dict:
    """Alert limits from the history up to `calibration_end`; saved as JSON.

    discharge  m3/s at the percentiles of config `processing.alerts.discharge_pct`
    rain       for each day of the year, the 7-day basin total (mm) at the percentiles of
               `processing.alerts.rain_pct`, among the same time of year (+/- 15 days) in all years
    """
    a, f = cfg["processing"]["alerts"], cfg["forecast"]
    history = load_history(cfg).loc[:f["calibration_end"]]
    q = history["q"].dropna()
    p7 = history["rain"].rolling(7, min_periods=7).sum().dropna()
    doy = p7.index.dayofyear.to_numpy()
    rain = {}
    for day in range(1, 367):
        distance = np.abs(doy - day)
        pool = p7.to_numpy()[np.minimum(distance, 366 - distance) <= 15]
        rain[str(day)] = {name: round(float(np.percentile(pool, pct)), 1) for name, pct in a["rain_pct"].items()}
    limits = {"created_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
              "calibration": [str(q.index.min().date()), f["calibration_end"]],
              "discharge_point": f["discharge_point"], "discharge_pct": a["discharge_pct"], "rain_pct": a["rain_pct"],
              "rain_p7_min_mm": a["rain_p7_min_mm"],
              "discharge_m3s": {name: round(float(np.percentile(q, pct)), 1) for name, pct in a["discharge_pct"].items()},
              "rain_p7_mm_by_doy": rain}
    limits_file(cfg).write_text(json.dumps(limits, indent=1))
    return limits


def load_limits(cfg: dict) -> dict:
    file = limits_file(cfg)
    return json.loads(file.read_text()) if file.exists() else build_limits(cfg)


# ----------------------------------------------------------------------------- today's forecast
def fetch_forecast(cfg: dict, today: date | None = None) -> dict:
    """Download today's forecasts and keep the raw answers.

    Returns {"date", "discharge": DataFrame (one column per scenario, past 10 days included),
             "rain": Series (basin mean, past 60 days + 16 forecast days), "fetched_utc"}.
    """
    f = cfg["forecast"]
    today = today or datetime.now(timezone.utc).date()
    lat, lon = f["discharge_point"]
    q_raw = fetch_json(f["flood_api"], {"latitude": lat, "longitude": lon, "daily": "river_discharge", "ensemble": "true",
                                        "past_days": 10, "forecast_days": f["ensemble_days"]})
    r_raw = fetch_json(f["weather_api"], {**_rain_params(cfg), "past_days": 60, "forecast_days": 16})
    folder = path(cfg, "forecast_raw", "runs", str(today))
    (folder / "discharge_ensemble.json").write_text(json.dumps(q_raw))
    (folder / "rain_forecast.json").write_text(json.dumps(r_raw))
    return parse_forecast(q_raw, r_raw, today)


def parse_forecast(q_raw: dict, r_raw, today: date) -> dict:
    members = [k for k in q_raw["daily"] if k != "time"]
    discharge = pd.DataFrame({k: q_raw["daily"][k] for k in members}, index=pd.to_datetime(q_raw["daily"]["time"])).astype("float64")
    return {"date": today, "discharge": discharge, "rain": _basin_mean(r_raw),
            "fetched_utc": datetime.now(timezone.utc).isoformat(timespec="seconds")}


def load_run(cfg: dict, day: str) -> dict:
    """Re-read the raw forecast of a past run (for audits and for working offline)."""
    folder = path(cfg, "forecast_raw", "runs", day, mkdir=False)
    return parse_forecast(json.loads((folder / "discharge_ensemble.json").read_text()),
                          json.loads((folder / "rain_forecast.json").read_text()), pd.Timestamp(day).date())


def latest_run(cfg: dict) -> str | None:
    folder = path(cfg, "forecast_raw", "runs", mkdir=False)
    runs = sorted(p.name for p in folder.iterdir() if (p / "discharge_ensemble.json").exists()) if folder.exists() else []
    return runs[-1] if runs else None


# ----------------------------------------------------------------------------- alert outlook
def alert_outlook(cfg: dict, fc: dict, limits: dict | None = None) -> pd.DataFrame:
    """One row per day from today to today + horizon: discharge scenarios, rain, and alert levels.

    caudal_mediana, caudal_p10, caudal_p90   spread of the 51 discharge scenarios (m3/s)
    prob_amarelo / prob_laranja / prob_vermelho   share of scenarios above each discharge limit
    nivel_caudal            highest level reached by at least `probability.provavel` of the scenarios
    nivel_caudal_possivel   highest level reached by at least `probability.possivel` of them
    chuva_7d_mm, nivel_chuva   7-day basin rain ending that day (observed + forecast) and its level;
                               only used up to `rain_skill_days` ahead
    nivel, nivel_possivel   combined levels (rule of the alert engine: the higher trigger;
                            laranja rain together with laranja discharge is vermelho)
    """
    f = cfg["forecast"]
    limits = limits or load_limits(cfg)
    today = pd.Timestamp(fc["date"])
    days = pd.date_range(today, periods=f["horizon_days"] + 1, freq="D")
    q = fc["discharge"].reindex(days)
    out = pd.DataFrame(index=days.rename("date"))
    out["dias_a_frente"] = np.arange(len(days))
    out["caudal_mediana"] = q.median(axis=1)
    out["caudal_p10"], out["caudal_p90"] = q.quantile(0.1, axis=1), q.quantile(0.9, axis=1)
    order = ["amarelo", "laranja", "vermelho"]
    for name in order:
        out[f"prob_{name}"] = (q >= limits["discharge_m3s"][name]).mean(axis=1).where(q.notna().any(axis=1))

    def level(share):
        return sum((out[f"prob_{name}"] >= share).astype(int) for name in order)      # nested limits: count = level

    out["nivel_caudal"] = level(f["probability"]["provavel"])
    out["nivel_caudal_possivel"] = level(f["probability"]["possivel"])

    p7 = fc["rain"].rolling(7, min_periods=7).sum().reindex(days)
    out["chuva_7d_mm"] = p7
    doy_limits = [limits["rain_p7_mm_by_doy"][str(d.dayofyear)] for d in days]
    enough = p7 >= limits["rain_p7_min_mm"]
    usable = out["dias_a_frente"] <= f["rain_skill_days"]
    out["nivel_chuva"] = np.select([usable & enough & (p7 >= [d["laranja"] for d in doy_limits]),
                                    usable & enough & (p7 >= [d["amarelo"] for d in doy_limits])], [2, 1], 0)

    def combine(discharge_level):
        combined = np.maximum(discharge_level, out["nivel_chuva"])
        return np.where((out["nivel_chuva"] == 2) & (discharge_level >= 2), 3, combined)

    out["nivel"] = combine(out["nivel_caudal"])
    out["nivel_possivel"] = combine(out["nivel_caudal_possivel"])
    out["alerta"] = out["nivel"].map(LEVELS)
    out["alerta_possivel"] = out["nivel_possivel"].map(LEVELS)
    return out


def perfect_forecast_backtest(cfg: dict, limits: dict | None = None) -> pd.DataFrame:
    """Daily alert levels over the whole history, as if every forecast had been exactly right.

    This is NOT a test of forecast skill (past forecasts are not archived anywhere we can
    reach). It shows what the limits would have done with the discharge and rain that really
    happened: an upper bound on what the forecast-based alerts can achieve.
    """
    limits = limits or load_limits(cfg)
    history = load_history(cfg).dropna(subset=["q"])
    out = pd.DataFrame(index=history.index)
    out["caudal"], out["chuva_7d_mm"] = history["q"], history["rain"].rolling(7, min_periods=7).sum()
    d = limits["discharge_m3s"]
    out["nivel_caudal"] = np.select([out["caudal"] >= d["vermelho"], out["caudal"] >= d["laranja"], out["caudal"] >= d["amarelo"]], [3, 2, 1], 0)
    by_doy = pd.DataFrame(limits["rain_p7_mm_by_doy"]).T
    by_doy.index = by_doy.index.astype(int)
    lim = by_doy.reindex(out.index.dayofyear).set_axis(out.index)
    enough = out["chuva_7d_mm"] >= limits["rain_p7_min_mm"]
    out["nivel_chuva"] = np.select([enough & (out["chuva_7d_mm"] >= lim["laranja"]), enough & (out["chuva_7d_mm"] >= lim["amarelo"])], [2, 1], 0)
    out["level"] = np.maximum(out["nivel_caudal"], out["nivel_chuva"])
    out.loc[(out["nivel_chuva"] == 2) & (out["nivel_caudal"] >= 2), "level"] = 3
    out["alerta"] = out["level"].map(LEVELS)
    return out
