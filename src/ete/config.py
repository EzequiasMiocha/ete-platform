"""Configuration, paths and the download manifest."""

from __future__ import annotations

import csv
import os
from datetime import date, datetime, timezone
from pathlib import Path

import yaml


def find_root(start: Path | None = None) -> Path:
    """Return the repository root (the folder that holds config/config.yaml)."""
    here = (start or Path.cwd()).resolve()
    for folder in [here, *here.parents]:
        if (folder / "config" / "config.yaml").exists():
            return folder
    raise FileNotFoundError("config/config.yaml not found above " + str(here))


ROOT = find_root(Path(__file__).parent)


def load_config() -> dict:
    """Load config/config.yaml and the optional .env file."""
    try:
        from dotenv import load_dotenv

        load_dotenv(ROOT / ".env")
    except ImportError:
        pass
    with open(ROOT / "config" / "config.yaml", encoding="utf-8") as f:
        cfg = yaml.safe_load(f)
    cfg["gee"]["project"] = os.getenv("EE_PROJECT") or cfg["gee"]["project"]
    return cfg


def path(cfg: dict, key: str, *parts: str, mkdir: bool = True) -> Path:
    """Absolute path for a key of the `paths` section, e.g. path(cfg, "landsat", "2006")."""
    p = ROOT / cfg["paths"][key]
    p = p.joinpath(*parts)
    if mkdir:
        (p if not p.suffix else p.parent).mkdir(parents=True, exist_ok=True)
    return p


def period_end(cfg: dict, end: str | None = None) -> str:
    """Resolve an end date. None means the last day of the last complete month."""
    end = end or cfg["period"]["end"]
    if end:
        return str(end)
    first_of_month = date.today().replace(day=1)
    return date.fromordinal(first_of_month.toordinal() - 1).isoformat()


MANIFEST_FIELDS = [
    "timestamp_utc", "dataset", "source_id", "period", "status",
    "n_images", "file", "bands", "crs", "resolution", "note",
]


def log_manifest(cfg: dict, **row) -> None:
    """Append one row to data/metadata/download_manifest.csv (traceability, pillar 4).

    status is one of: downloaded, absent (no source data for that period), failed.
    """
    manifest = path(cfg, "manifest")
    new = not manifest.exists()
    row = {"timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), **row}
    if "file" in row and row["file"]:
        row["file"] = str(Path(row["file"]).resolve().relative_to(ROOT))
    with open(manifest, "a", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, extrasaction="ignore")
        if new:
            writer.writeheader()
        writer.writerow(row)
