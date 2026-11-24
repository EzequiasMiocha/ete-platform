"""Figures for the English documentation (documentation/ in the project, published with the platform on GitHub).

    .venv/bin/python scripts/build_documentation.py                    # every figure, then the link check
    .venv/bin/python scripts/build_documentation.py --only charts      # one group: charts, maps, satellite, platform
    .venv/bin/python scripts/build_documentation.py --check            # only the link check

Writes documentation/figures/{charts,maps,satellite,platform}/. Nothing is downloaded. The figures are drawn from:
  * the project's data, models and reports (charts and maps);
  * the English presentation figures in reports/apresentacao/en/ (scripts/build_presentation_figures.py);
  * English screenshots of the platform, taken from a local server with
        scripts/capturar_plataforma.py --lingua en --larguras 1280 --pasta reports/plataforma/capturas/docs_en
        scripts/capturar_plataforma.py --lingua en --larguras 390  --pasta reports/plataforma/capturas/docs_en
    The crop rows in SCREENS fit the screenshots of 24 Nov 2026; check them after new screenshots.
The daily series (discharge history, alert history) are read from deploy/ete-plataforma when it exists, because the
daily bulletin on GitHub keeps them up to date there.

The check at the end fails if a page links to a figure that does not exist, or if a figure is not used by any page.
"""

import argparse
import io
import json
import re
import sys
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.patheffects as effects  # noqa: E402
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402
from PIL import Image  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from ete import config  # noqa: E402

DOCS = ROOT / "documentation"
FIG = DOCS / "figures"
DEPLOY = ROOT / "deploy" / "ete-plataforma"
CAPTURES = ROOT / "reports" / "plataforma" / "capturas" / "docs_en"
cfg = config.load_config()

# Colours: the platform's chart palette (plataforma/graficos.py, checked with the data-viz validator), the alert
# colours and map colours of the platform (src/ete/platform.py) and the water-colour steps (src/ete/turbidity_map.py).
INK, MUTED, GRID, BAND = "#212529", "#6C6E74", "#E2E1EA", "#F0EFF8"
SERIES = ["#1F5F8F", "#E07A9F", "#8C6BB1"]
QUIET = "#C9CBD6"
ALERT = {"verde": "#27ae60", "amarelo": "#f1c40f", "laranja": "#e67e22", "vermelho": "#c0392b"}
ALERT_EN = {"verde": "green", "amarelo": "yellow", "laranja": "orange", "vermelho": "red"}
WATER, FLOOD, LAND = "#2e86c1", "#c0392b", "#F3F1EB"
UTM = "EPSG:32736"
DPI = 160

plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "text.color": INK, "axes.labelcolor": INK,
                     "axes.edgecolor": "#B9BBC6", "xtick.color": MUTED, "ytick.color": MUTED, "axes.titleweight": "bold",
                     "axes.titlesize": 11, "axes.titlecolor": INK, "axes.titlelocation": "left", "legend.frameon": False})


# ----------------------------------------------------------------------------- helpers
def figure(w=10.0, h=5.6, top=0.80, bottom=0.14, left=0.08, right=0.97):
    fig = plt.figure(figsize=(w, h), dpi=DPI)
    fig.subplots_adjust(top=top, bottom=bottom, left=left, right=right)
    return fig


def header(fig, title, sub=None):
    fig.text(0.04, 0.965, title, fontsize=15, weight="bold", color=INK, va="top")
    if sub:
        fig.text(0.04, 0.965 - 0.85 / fig.get_figheight() * 0.62, sub, fontsize=10.2, color=MUTED, va="top")


def source(fig, text):
    fig.text(0.04, 0.022, text, fontsize=8.2, color=MUTED, va="bottom")


def tidy(ax, grid_axis="y"):
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    ax.spines["left"].set_color("#B9BBC6")
    ax.spines["bottom"].set_color("#B9BBC6")
    if grid_axis:
        ax.grid(axis=grid_axis, color=GRID, linewidth=0.8)
        ax.set_axisbelow(True)
    ax.tick_params(length=3, width=0.6)


def halo(width=2.6, colour="white"):
    return [effects.withStroke(linewidth=width, foreground=colour)]


def save(fig, rel, photo=False):
    """PNG with a reduced palette for charts and maps (sharp text, small files); JPEG for photographs."""
    out = FIG / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    buffer = io.BytesIO()
    fig.savefig(buffer, dpi=DPI, facecolor="white", format="png")
    plt.close(fig)
    image = Image.open(buffer).convert("RGB")
    if photo or out.suffix == ".jpg":
        image.save(out, "JPEG", quality=84, optimize=True, progressive=True)
    else:
        image.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
    print(f"  {rel:<48} {out.stat().st_size / 1e3:6.0f} KB")


def series_file(rel):
    """The daily bulletin keeps these files up to date in the published repository."""
    published = DEPLOY / rel
    return published if published.exists() else ROOT / rel


def district():
    from ete.grid import load_aoi
    return load_aoi(cfg, "district").to_crs(UTM)


def read_decimated(file, bands, factor=3):
    """Bands of a 10 m project raster at 30 m (nearest), in physical units, NaN for no data; plus the extent."""
    import rasterio
    from rasterio.enums import Resampling

    with rasterio.open(file) as src:
        names = list(src.descriptions)
        shape = (src.height // factor, src.width // factor)
        out = {}
        for band in bands:
            i = names.index(band) + 1
            raw = src.read(i, out_shape=shape, resampling=Resampling.nearest)
            data = raw.astype("float32") * np.float32(src.scales[i - 1])
            if src.nodata is not None:
                data[raw == src.nodata] = np.nan
            out[band] = data
        b = src.bounds
    return out, [b.left, b.right, b.bottom, b.top]


def map_axes(ax, extent, d=None, bar_km=10):
    """District outline, a scale bar and the north arrow on a map in UTM 36S."""
    west, east, south, north = extent
    if d is not None:
        d.boundary.plot(ax=ax, color=INK, linewidth=0.7, zorder=6)
    x0, y0 = west + 0.06 * (east - west), south + 0.04 * (north - south)
    ax.plot([x0, x0 + bar_km * 1000], [y0, y0], color=INK, linewidth=2.4, solid_capstyle="butt", zorder=8, path_effects=halo(4.4))
    ax.annotate(f"{bar_km} km", (x0 + bar_km * 500, y0), xytext=(0, 5), textcoords="offset points", ha="center", fontsize=8.5,
                weight="bold", zorder=8, path_effects=halo())
    ax.annotate("N", (east - 0.06 * (east - west), north - 0.04 * (north - south)), ha="center", va="top", fontsize=11, weight="bold",
                zorder=8, path_effects=halo())
    ax.set_xlim(west, east), ax.set_ylim(south, north)
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_xlabel(""), ax.set_ylabel("")
    for side in ax.spines.values():
        side.set_color("#B9BBC6")


LEFT_LABELS = {"Marracuene"}          # names written to the left of their dot (a neighbour sits on the right)


def label_places(ax, names, extent, size=8.2):
    import geopandas as gpd

    places = gpd.read_file(ROOT / "data/raw/places/osm_places.gpkg").to_crs(UTM)
    west, east, south, north = extent
    done = set()
    for _, row in places[places["name"].isin(names)].iterrows():
        if row["name"] in done:
            continue
        x, y = row.geometry.centroid.x, row.geometry.centroid.y
        if west < x < east and south < y < north:
            done.add(row["name"])
            ax.plot(x, y, "o", color=INK, markersize=3.6, markeredgecolor="white", markeredgewidth=0.7, zorder=9)
            left = row["name"] in LEFT_LABELS
            ax.annotate(row["name"], (x, y), xytext=(-4 if left else 4, 2), textcoords="offset points", fontsize=size, weight="bold", zorder=9,
                        ha="right" if left else "left", path_effects=halo())


# ----------------------------------------------------------------------------- charts
def chart_timeline():
    rows = [  # group, name, start, end (None = today), note
        ("Optical images", "Landsat 5 TM (30 m)", "2006-01", "2011-11", ""),
        ("Optical images", "Landsat 7 ETM+ (30 m)", "2006-01", "2013-12", ""),
        ("Optical images", "Landsat 8 OLI (30 m)", "2013-04", None, ""),
        ("Optical images", "Landsat 9 OLI-2 (30 m)", "2021-11", None, ""),
        ("Optical images", "Sentinel-2 L2A (10 m)", "2017-01", None, ""),
        ("Radar images", "Sentinel-1 GRD, VV and VH (10 m)", "2014-10", None, ""),
        ("Water and land cover", "JRC Global Surface Water, monthly (30 m)", "2006-01", "2021-12", ""),
        ("Water and land cover", "Dynamic World (10 m)", "2015-07", None, ""),
        ("Rain and soil", "CHIRPS daily rain (5 km)", "2006-01", None, ""),
        ("Rain and soil", "GPM IMERG daily rain (10 km)", "2006-01", None, ""),
        ("Rain and soil", "ERA5-Land soil moisture, runoff (9 km)", "2006-01", None, ""),
        ("Rain and soil", "SMAP L4 soil moisture (9 km)", "2015-04", None, ""),
        ("River and sea", "GloFAS v4 river discharge (5 km)", "1997-01", None, ""),
        ("River and sea", "Sea level, Maputo Bay (tide fit)", "2023-01", "2026-10", ""),
        ("Daily forecasts", "GloFAS 51-scenario discharge forecast", "2026-10", None, ""),
        ("Daily forecasts", "ECMWF IFS rain forecast", "2026-10", None, ""),
    ]
    events = [("Copernicus EMS EMSR650", "2023-02-15"), ("Copernicus EMS EMSR857", "2026-01-20")]
    today = pd.Timestamp("2026-11-24")
    fig = figure(10, 7.4, top=0.86, bottom=0.10, left=0.37, right=0.97)
    header(fig, "Twenty years of open data behind the platform",
           "Period of each dataset used in this project (bars). The diamonds are the two mapped flood events used as test labels.")
    ax = fig.add_subplot(111)
    y, ticks, labels, group_y = 0, [], [], []
    last_group = None
    for group, name, start, end, _ in rows:
        if group != last_group:
            y += 0.7
            group_y.append((y, group))
            y += 0.8
            last_group = group
        s, e = pd.Timestamp(start), pd.Timestamp(end) if end else today
        ax.barh(y, (e - s).days, left=s, height=0.62, color=SERIES[0], edgecolor="white", linewidth=0)
        ticks.append(y), labels.append(name)
        y += 1
    y += 0.7
    group_y.append((y, "Reference floods"))
    y += 0.8
    for name, day in events:
        ax.plot(pd.Timestamp(day), y, "D", color=SERIES[1], markersize=8, markeredgecolor="white", markeredgewidth=1.2)
        ticks.append(y), labels.append(name)
        y += 1
    for gy, g in group_y:
        ax.text(-0.02, gy, g.upper(), transform=ax.get_yaxis_transform(), ha="right", va="center", fontsize=8.4, weight="bold", color=MUTED)
    ax.set_yticks(ticks, labels, fontsize=9)
    ax.set_ylim(y, -0.2)
    ax.set_xlim(pd.Timestamp("1996-06-01"), pd.Timestamp("2027-06-01"))
    tidy(ax, "x")
    ax.tick_params(axis="y", length=0, colors=INK)
    ax.spines["left"].set_visible(False)
    ax.axvline(pd.Timestamp("2022-01-01"), color=INK, linewidth=0.8)
    ax.text(pd.Timestamp("2021-11-01"), 0.1, "test years from 2022 →", fontsize=8, color=INK, va="top", ha="right")
    source(fig, "Sources: USGS/NASA, ESA/Copernicus, JRC, Google, UCSB-CHC, NASA, ECMWF, Copernicus EMS. Daily forecasts through the Open-Meteo service.")
    save(fig, "charts/data_timeline.png")


def chart_discharge_history():
    h = pd.read_csv(series_file("data/raw/forecast/history/discharge_history.csv"), parse_dates=["date"]).dropna().set_index("date")["q"]
    limits = json.loads((ROOT / "models/limites_previsao.json").read_text())["discharge_m3s"]
    fig = figure(10, 5.4, top=0.80, bottom=0.13)
    header(fig, "Thirty years of the Incomati at Marracuene, and the three alert limits",
           "Daily discharge simulated by GloFAS v4 (no gauge is published here). Limits: 90th, 97th and 99.5th percentiles of 1997-2021.")
    ax = fig.add_subplot(111)
    ax.axvspan(pd.Timestamp("2022-01-01"), h.index.max(), color=BAND, zorder=0)
    ax.text(pd.Timestamp("2022-03-01"), 4250, "test years\n(not used to set\nthe limits)", fontsize=8, color=MUTED, va="top")
    ax.plot(h.index, h.values, color=SERIES[0], linewidth=0.6)
    for level in ("amarelo", "laranja", "vermelho"):
        ax.axhline(limits[level], color=ALERT[level], linewidth=1.3, zorder=1)
        ax.text(pd.Timestamp("1996-09-01"), limits[level] + 40, f"{ALERT_EN[level]}  {limits[level]:,.0f} m³/s", fontsize=8.2, color=INK,
                weight="bold", va="bottom", path_effects=halo())
    for start, end, side in (("1999-01-01", "1999-12-31", 1), ("2000-01-01", "2000-12-31", 1), ("2023-01-01", "2023-12-31", 1), ("2026-01-01", "2026-12-31", -1)):
        part = h.loc[start:end]
        day, value = part.idxmax(), part.max()
        ax.annotate(f"{day:%b %Y}\n{value:,.0f} m³/s", (day, value), xytext=(8 * side, -4 if day.year != 1999 else 30), textcoords="offset points",
                    fontsize=8, va="top", ha="left" if side > 0 else "right", color=INK, path_effects=halo())
    ax.set_ylabel("Discharge (m³/s)")
    ax.set_ylim(0, 4400)
    ax.set_xlim(pd.Timestamp("1996-06-01"), h.index.max() + pd.Timedelta(days=60))
    tidy(ax)
    source(fig, f"Source: GloFAS v4 (Copernicus EMS) through the Open-Meteo flood API, cell 25.775 S 32.675 E, 1 Jan 1997 to {h.index.max():%d %b %Y}.")
    save(fig, "charts/discharge_history.png")


def _alert_history():
    a = pd.read_csv(series_file("plataforma/dados/series/alertas_historicos.csv"), parse_dates=["data"]).set_index("data")
    return a


def chart_january_2026():
    a = _alert_history().loc["2025-12-15":"2026-02-15"]
    lim = pd.read_csv(ROOT / "reports/semana_3/32_limites_dos_alertas.csv", index_col=0)["caudal (m³/s)"]
    fig = plt.figure(figsize=(10, 7.2), dpi=DPI)
    gs = fig.add_gridspec(3, 1, height_ratios=[3.2, 1.6, 0.45], hspace=0.16, top=0.84, bottom=0.10, left=0.09, right=0.97)
    header(fig, "January 2026: the alert rules, replayed on the flood",
           "Orange on 12 January, five days before the first satellite map showed flood water at Marracuene (17 January).")
    ax1 = fig.add_subplot(gs[0])
    ax1.plot(a.index, a["caudal_m3s"], color=SERIES[0], linewidth=2)
    for level in ("amarelo", "laranja", "vermelho"):
        ax1.axhline(lim[level], color=ALERT[level], linewidth=1.2, zorder=1)
        ax1.text(pd.Timestamp("2025-12-15"), lim[level] + 35, f"{ALERT_EN[level]} {lim[level]:,.0f} m³/s", fontsize=8, weight="bold",
                 va="bottom", path_effects=halo())
    peak = a["caudal_m3s"].idxmax()
    ax1.annotate(f"peak {a['caudal_m3s'].max():,.0f} m³/s, {peak:%d %b}", (peak, a["caudal_m3s"].max()), xytext=(12, 0),
                 textcoords="offset points", fontsize=8.5, va="center", path_effects=halo())
    ax1.set_ylabel("Discharge (m³/s)")
    ax1.set_ylim(0, 3700)
    ax2 = fig.add_subplot(gs[1], sharex=ax1)
    ax2.bar(a.index, a["chuva_7d_mm"], width=0.8, color=SERIES[0], alpha=0.55)
    ax2.set_ylabel("7-day basin\nrain (mm)")
    ax3 = fig.add_subplot(gs[2], sharex=ax1)
    ax3.bar(a.index, np.ones(len(a)), width=1.0, color=[ALERT[x] for x in a["alerta"]], edgecolor="white", linewidth=0.4)
    ax3.set_yticks([])
    ax3.set_ylabel("Level", rotation=0, ha="right", va="center")
    for day, text, side in ((pd.Timestamp("2026-01-12"), "first orange\n12 Jan", -1), (pd.Timestamp("2026-01-17"), "first flood map\n(Copernicus EMS) 17 Jan", 1)):
        for ax in (ax1, ax2, ax3):
            ax.axvline(day, color=INK, linewidth=0.8, zorder=5)
        ax1.text(day + side * pd.Timedelta(hours=10), 3650, text, fontsize=8.2, ha="right" if side < 0 else "left", va="top")
    for ax in (ax1, ax2):
        tidy(ax)
        plt.setp(ax.get_xticklabels(), visible=False)
    tidy(ax3, None)
    ax3.spines["left"].set_visible(False)
    ax3.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d %b"))
    ax2.legend(handles=[Patch(color=ALERT[k], label=ALERT_EN[k]) for k in ALERT], ncol=4, loc="upper right", fontsize=8.2,
               title="Alert level (bottom row)", title_fontsize=8.2)
    source(fig, "Discharge: GloFAS reanalysis. Rain: CHIRPS, mean over the basin. Limits set on 2006-2021 (alert history of the platform, src/ete/alerts.py).")
    save(fig, "charts/january_2026_alert_replay.png")


def chart_alert_days():
    a = _alert_history()
    a = a.loc["2006-10-01":"2026-09-30"]
    year = a.index.year + (a.index.month >= 10)
    counts = pd.crosstab(year, a["alerta"]).reindex(columns=["amarelo", "laranja", "vermelho"], fill_value=0)
    with_orange = int(((counts["laranja"] + counts["vermelho"]) > 0).sum())
    with_red = int((counts["vermelho"] > 0).sum())
    fig = figure(10, 5.0, top=0.80, bottom=0.17)
    header(fig, f"Days a year the alert rules would have warned: orange or red in {with_orange} of {len(counts)} years",
           f"Hydrological years, October to September (2007 = Oct 2006 to Sep 2007). Red in {with_red} years.")
    ax = fig.add_subplot(111)
    bottom = np.zeros(len(counts))
    for level in ("amarelo", "laranja", "vermelho"):
        ax.bar(counts.index, counts[level], bottom=bottom, color=ALERT[level], width=0.72, edgecolor="white", linewidth=1.2, label=ALERT_EN[level])
        bottom += counts[level].to_numpy()
    ax.set_xticks(counts.index, [str(y) for y in counts.index], fontsize=8.4)
    ax.set_ylabel("Days")
    ax.legend(loc="upper left", ncol=3)
    tidy(ax)
    source(fig, "Same data as the 'Twenty years of the river' chart of the platform (plataforma/dados/series/alertas_historicos.csv).")
    save(fig, "charts/alert_days_per_year.png")
    return with_orange, len(counts), with_red


def chart_algorithms():
    blocks = pd.read_csv(ROOT / "reports/semana_3/30_modelo_b_por_bloco.csv")
    b = blocks.groupby("modelo")["iou"].agg(["mean", "min", "max"])
    a = pd.read_csv(ROOT / "plataforma/dados/modelos/modelo_a_algoritmos.csv").set_index("algoritmo")
    names = {"Regressão logística": "Logistic regression", "Random Forest": "Random Forest", "Gradient Boosting (HistGB)": "HistGradientBoosting",
             "XGBoost": "XGBoost (chosen)"}
    order = ["Regressão logística", "Random Forest", "Gradient Boosting (HistGB)", "XGBoost"]
    fig = plt.figure(figsize=(10, 5.0), dpi=DPI)
    fig.subplots_adjust(top=0.74, bottom=0.17, left=0.19, right=0.97, wspace=0.55)
    header(fig, "Four algorithms compared with a rule stated before the test",
           "XGBoost was chosen for both flood models. Both are scored on the January 2026 flood mapped by Copernicus EMS.")
    ax = fig.add_subplot(121)
    y = np.arange(len(order))
    vals = b.loc[order]
    pooled = pd.read_csv(ROOT / "plataforma/dados/modelos/modelo_b_algoritmos.csv").set_index("algoritmo").loc[order, "iou"]
    colours = [SERIES[0] if k == "XGBoost" else QUIET for k in order]
    ax.barh(y, pooled, color=colours, height=0.6)
    ax.errorbar(pooled, y, xerr=[np.maximum(pooled - vals["min"], 0), np.maximum(vals["max"] - pooled, 0)], fmt="none", ecolor=INK, elinewidth=0.9, capsize=3)
    for i, v in enumerate(pooled):
        ax.text(0.02, i, f"{v:.3f}", va="center", ha="left", fontsize=8.6, color="white" if order[i] == "XGBoost" else INK, weight="bold")
    ax.axvline(0.88, color=SERIES[1], linewidth=1.6)
    ax.text(0.87, -0.55, "simple rule VH p10 ≤ -22 dB: 0.88", fontsize=7.8, color=INK, va="center", ha="right")
    ax.set_yticks(y, [names[k] for k in order])
    ax.set_xlim(0, 1)
    ax.set_ylim(3.5, -0.9)
    ax.set_title("Model B (radar water): IoU", fontsize=10)
    ax.set_xlabel("IoU (1 = perfect overlap)")
    tidy(ax, "x")
    ax2 = fig.add_subplot(122)
    v2 = a.loc[order, "auc_cheia_2026"]
    ax2.barh(y, v2, color=colours, height=0.6)
    for i, v in enumerate(v2):
        ax2.text(0.02, i, f"{v:.2f}", va="center", ha="left", fontsize=8.6, color="white" if order[i] == "XGBoost" else INK, weight="bold")
    ax2.set_yticks(y, [names[k] for k in order])
    ax2.set_xlim(0, 1)
    ax2.set_ylim(3.5, -0.9)
    ax2.set_title("Model A (terrain): ROC-AUC", fontsize=10)
    ax2.set_xlabel("ROC-AUC (0.5 = chance, 1 = perfect)")
    tidy(ax2, "x")
    source(fig, "Model B: all 5 spatial blocks of 3 km together; error bars = lowest and highest block. Model A never saw the 2026 flood (trained on JRC up to 2019).")
    save(fig, "charts/algorithm_comparison.png")


def chart_model_b_area():
    m = pd.read_csv(ROOT / "data/processed/series/modelo_b_area_mensal.csv")
    m["month"] = pd.to_datetime(m["month"])
    m = m[m["month"] >= "2016-01-01"]                       # 2015 has a single radar orbit: Model B starts in 2016
    dry = m[m["month"].dt.month.isin([6, 7, 8, 9])]["cheia_distrito_km2"].median()
    fig = figure(10, 4.8, top=0.78, bottom=0.14)
    header(fig, "Flood water seen by radar every month since 2016",
           "Model B on Sentinel-1, 2016-2026: water outside the usual river and lagoons, inside the district (km²). Radar sees through clouds.")
    ax = fig.add_subplot(111)
    ax.bar(m["month"], m["cheia_distrito_km2"], width=25, color=SERIES[0])
    ax.axhline(dry, color=SERIES[1], linewidth=1.4)
    ax.text(pd.Timestamp("2026-11-15"), dry, f"median of the\ndry months\n(Jun-Sep):\n{dry:.0f} km²", fontsize=8, color=INK, va="center")
    for start, end in (("2021-01-01", "2021-04-30"), ("2023-01-01", "2023-04-30"), ("2026-01-01", "2026-04-30")):
        r = m[(m["month"] >= start) & (m["month"] <= end)].nlargest(1, "cheia_distrito_km2").iloc[0]
        ax.annotate(f"{r['month']:%b %Y}\n{r['cheia_distrito_km2']:.0f} km²", (r["month"], r["cheia_distrito_km2"]), xytext=(-16, 0),
                    textcoords="offset points", fontsize=8, va="top", ha="right", path_effects=halo())
    ax.set_xlim(pd.Timestamp("2015-10-01"), pd.Timestamp("2027-09-01"))
    ax.set_ylabel("km² inside the district")
    tidy(ax)
    source(fig, "Dry-month values are false water (wet fields, built-up areas). Source: data/processed/series/modelo_b_area_mensal.csv.")
    save(fig, "charts/model_b_monthly_flood_area.png")


def chart_model_c():
    skill = pd.DataFrame(json.loads((ROOT / "models/modelo_c_caudal.json").read_text())["skill"]).set_index("dias_a_frente")
    fig = plt.figure(figsize=(10, 4.6), dpi=DPI)
    fig.subplots_adjust(top=0.74, bottom=0.17, left=0.07, right=0.86, wspace=0.62)
    header(fig, "Model C (our own discharge forecast) against 'tomorrow equals today'",
           "Tested on 2022-2026, years the model never saw. Higher is better in both panels.")
    for i, (metric, title, ylab) in enumerate((("nse", "Nash-Sutcliffe efficiency of the discharge", "NSE"),
                                                ("csi", "Days above the orange limit: critical success index", "CSI"))):
        ax = fig.add_subplot(1, 2, i + 1)
        for name, colour, label in (("modelo", SERIES[0], "Model C (XGBoost)"), ("persistencia", SERIES[1], "Persistence")):
            ax.plot(skill.index, skill[f"{metric}_{name}"], "-o", color=colour, linewidth=2, markersize=6, markeredgecolor="white", label=label)
            ax.annotate(label, (skill.index[-1], skill[f"{metric}_{name}"].iloc[-1]), xytext=(6, 0), textcoords="offset points", fontsize=8.4,
                        va="center", color=INK)
        ax.set_title(title, fontsize=9.8)
        ax.set_xlabel("Days ahead")
        ax.set_ylabel(ylab)
        ax.set_xticks(skill.index)
        ax.set_ylim(0, 1)
        tidy(ax)
    source(fig, "Source: models/modelo_c_caudal.json. The bulletin uses the GloFAS 51-scenario forecast; Model C is shown as a second opinion.")
    save(fig, "charts/model_c_skill.png")


def chart_turbidity_skill():
    t = pd.read_csv(ROOT / "plataforma/dados/modelos/turbidez_modelo.csv").set_index("modelo")
    rows = [("referência: época do ano", "Time of year only (reference)"),
            ("sem maré", "Flow, rain and season, no tide"),
            ("passo anterior: maré só pela fase M2", "+ tide (phase of the main lunar tide only)"),
            ("modelo final: última medição há 1 dia ou mais", "Final model: tide + latest measurement"),
            ("modelo final: sem medição recente", "Final model, no measurement in 30 days"),
            ("modelo final no Landsat 8/9 (outro satélite): todos os anos", "Final model on Landsat 8/9 (another satellite)"),
            ("modelo final no Landsat antes de 2017 (outro satélite e outros anos)", "Final model on Landsat before 2017")]
    fig = plt.figure(figsize=(10, 5.2), dpi=DPI)
    fig.subplots_adjust(top=0.76, bottom=0.14, left=0.33, right=0.97, wspace=0.12)
    header(fig, "The tide was the missing clue for the colour of the river",
           "Water-colour index (NDTI) of the reach at the morning satellite pass. Each year is predicted by a model that never saw it.")
    y = np.arange(len(rows))
    for i, (col, title, lim) in enumerate((("r2", "R² of the colour index", (0, 0.8)), ("auc", "ROC-AUC: 'more turbid than usual'", (0.5, 0.95)))):
        ax = fig.add_subplot(1, 2, i + 1)
        vals = [t.loc[k, col] for k, _ in rows]
        colours = [SERIES[0] if "Final model: tide" in name else (QUIET if "reference" in name or "no tide" in name else "#9DB7CE") for _, name in rows]
        ax.barh(y, np.array(vals) - lim[0], left=lim[0], color=colours, height=0.62)
        for j, v in enumerate(vals):
            ax.text(v + (lim[1] - lim[0]) * 0.01, j, f"{v:.2f}", va="center", fontsize=8.4)
        ax.set_yticks(y, [name for _, name in rows] if i == 0 else [])
        ax.set_xlim(*lim)
        ax.set_ylim(len(rows) - 0.4, -0.6)
        ax.set_title(title, fontsize=9.8)
        tidy(ax, "x")
    source(fig, "Reaches 2-4 of the lower river, Sentinel-2 2017-2026 (2,211 reach-days). Source: plataforma/dados/modelos/turbidez_modelo.csv.")
    save(fig, "charts/turbidity_model_skill.png")


def chart_tide_effect():
    from ete import forecast_models

    t = forecast_models.tide_model_table(cfg)
    t["tide"] = pd.qcut(t["t_h"], 3, labels=["low tide", "mid tide", "high tide"])
    share = t.groupby(["troco", "tide"], observed=True)["elevada"].mean().unstack() * 100
    counts = t.groupby("troco").size()
    names = {"2 troço médio": "Middle reach", "3 jusante": "Downstream (Marracuene)", "4 foz / estuário": "Mouth / estuary"}
    ramp = ["#A9C4DC", "#5E8DB4", "#1F4E79"]
    fig = figure(10, 5.2, top=0.78, bottom=0.18, left=0.08)
    header(fig, "At low tide the river is muddier: the share of 'more turbid than usual' mornings",
           "Sentinel-2 mornings 2017-2026, split into thirds by the computed tide height at the time of the satellite pass.")
    ax = fig.add_subplot(111)
    x = np.arange(len(share))
    for k, tide in enumerate(share.columns):
        bars = ax.bar(x + (k - 1) * 0.26, share[tide], width=0.24, color=ramp[k], label=tide, edgecolor="white", linewidth=1.2)
        for bar, v in zip(bars, share[tide]):
            ax.text(bar.get_x() + bar.get_width() / 2, v + 1.2, f"{v:.0f}%", ha="center", fontsize=8.2)
    ax.set_xticks(x, [f"{names[r]}\n({counts[r]} images)" for r in share.index])
    ax.set_ylabel("% of mornings more turbid than usual")
    ax.set_ylim(0, 100)
    ax.legend(loc="upper right", ncol=3)
    tidy(ax)
    source(fig, "'More turbid than usual' = colour index above the 75th percentile of the reach. Tide: 22 harmonic constants fitted to Open-Meteo sea level of Maputo Bay.")
    save(fig, "charts/tide_and_water_colour.png")


def chart_turbidity_by_discharge():
    d = json.loads((ROOT / "models/turbidez_por_caudal.json").read_text())
    tab = pd.DataFrame(d["table"])
    labels = ["below 20", "20 to 60", "60 to 164", "164 to 376\n(yellow)", "above 376\n(orange or more)"]
    fig = figure(10, 4.9, top=0.78, bottom=0.21)
    header(fig, "The more water the river carries, the muddier it gets",
           "Share of measured mornings with water 'more turbid than usual', by river discharge that day (reaches 2-4, Sentinel-2).")
    ax = fig.add_subplot(111)
    x = np.arange(len(tab))
    v = tab["turbidez_elevada"] * 100
    ax.bar(x, v, color=SERIES[0], width=0.6)
    ax.errorbar(x, v, yerr=[v - tab["intervalo_min"] * 100, tab["intervalo_max"] * 100 - v], fmt="none", ecolor=INK, elinewidth=0.9, capsize=3)
    for i, (val, n) in enumerate(zip(v, tab["dias_medidos"])):
        ax.text(i + 0.33, val, f"{val:.0f}%\n{n} days", fontsize=8, va="center")
    ax.set_xticks(x, labels)
    ax.set_xlabel("Discharge at Marracuene (m³/s)")
    ax.set_ylabel("% more turbid than usual")
    ax.set_ylim(0, 100)
    tidy(ax)
    source(fig, "Error bars: 95% interval. Source: models/turbidez_por_caudal.json.")
    save(fig, "charts/water_colour_by_discharge.png")


def chart_cross_satellite():
    c = pd.read_csv(ROOT / "plataforma/dados/modelos/concordancia_entre_satelites.csv")
    sec = c[c["troco"] != "todos os troços"].reset_index(drop=True)
    names = {"Q1": "Q1 Border", "Q2": "Q2 km 37-74", "Q3": "Q3 km 74-110", "Q4": "Q4 Magude", "Q5": "Q5 Xinavane", "Q6": "Q6 km 184-221",
             "Q7": "Q7 Manhiça", "Q8": "Q8 Marracuene", "Q9": "Q9 Mouth"}
    fig = figure(10, 4.8, top=0.77, bottom=0.2)
    header(fig, "Sentinel-2 and Landsat agree on the river's colour in seven of nine sections",
           f"Correlation of the colour index (NDTI) measured by Sentinel-2 and Landsat 8/9 on the same day. All sections: r = "
           f"{float(c.loc[c['troco'] == 'todos os troços', 'r_ndti'].iloc[0]):.2f} over {int(c.loc[c['troco'] == 'todos os troços', 'pares'].iloc[0])} pairs.")
    ax = fig.add_subplot(111)
    flagged = sec["r_ndti"] < 0.6
    ax.bar(sec.index, sec["r_ndti"], color=[QUIET if f else SERIES[0] for f in flagged], width=0.62)
    for i, r in sec.iterrows():
        ax.text(i, r["r_ndti"] + 0.02, f"{r['r_ndti']:.2f}\n{int(r['pares'])} pairs", ha="center", fontsize=7.8)
        if flagged[i]:
            ax.text(i, 0.06, "reduced\nreliability", ha="center", fontsize=7.6, color=INK, weight="bold")
    ax.set_xticks(sec.index, [names[k] for k in sec["troco"]], fontsize=8.4, rotation=0)
    ax.set_ylabel("Correlation r")
    ax.set_ylim(0, 1.12)
    tidy(ax)
    source(fig, "Q3 and Q6 are flagged: no water-quality warnings are raised there. Source: plataforma/dados/modelos/concordancia_entre_satelites.csv.")
    save(fig, "charts/satellite_agreement_by_section.png")


def chart_colour_and_flow():
    m = pd.read_csv(ROOT / "plataforma/dados/modelos/meses_resumo.csv")
    m["mes"] = pd.to_datetime(m["mes"])
    from ete.turbidity_map import CLASSES, STEPS

    fig = plt.figure(figsize=(10, 6.2), dpi=DPI)
    gs = fig.add_gridspec(2, 1, height_ratios=[2.2, 1.2], hspace=0.12, top=0.82, bottom=0.11, left=0.09, right=0.84)
    header(fig, "The colour of the river at Marracuene month by month, and the river flow",
           "Median colour index (NDTI) of the clear Sentinel-2 images of each month, section Q8. Bands: the five colour steps.")
    ax = fig.add_subplot(gs[0])
    edges = [-0.25, *STEPS, 0.12]
    names_en = ["very clear", "clear", "usual", "muddy", "very muddy"]
    for k, (_, colour) in enumerate(CLASSES):
        ax.axhspan(edges[k], edges[k + 1], color=colour, alpha=0.22, linewidth=0)
        ax.text(1.01, (max(edges[k], -0.24) + min(edges[k + 1], 0.11)) / 2, names_en[k], transform=ax.get_yaxis_transform(), fontsize=8.2, va="center")
    ax.plot(m["mes"], m["ndti_marracuene"], "-o", color=SERIES[0], linewidth=1.2, markersize=3.2)
    ax.set_ylabel("Colour index (NDTI)")
    ax.set_ylim(-0.24, 0.11)
    tidy(ax)
    plt.setp(ax.get_xticklabels(), visible=False)
    ax2 = fig.add_subplot(gs[1], sharex=ax)
    ax2.bar(m["mes"], m["caudal_m3s"], width=25, color=SERIES[0], alpha=0.55)
    ax2.set_ylabel("Mean flow (m³/s)")
    tidy(ax2)
    source(fig, "Muddiest water reads as land in some flood months, so a flood month can look 'clear' (e.g. Jan 2021). Source: plataforma/dados/modelos/meses_resumo.csv.")
    save(fig, "charts/water_colour_and_flow_monthly.png")


def chart_colour_forecast():
    t = pd.read_csv(ROOT / "plataforma/dados/modelos/teste_modelo_marracuene.csv")
    show = [("modelo (boosting)", "Forecast model (gradient boosting)", SERIES[0]), ("referência: época do ano", "Reference: time of year", SERIES[1]),
            ("referência: última medição", "Reference: latest measurement", SERIES[2])]
    fig = figure(10, 5.0, top=0.78, bottom=0.17, right=0.76)
    header(fig, "Forecasting the colour of the water up to 30 days ahead: a guide, not a certainty",
           "Share of days on which the forecast colour step at Marracuene was right or one step off. Each year left out of training in turn.")
    ax = fig.add_subplot(111)
    for key, label, colour in show:
        s = t[t["metodo"] == key].set_index("antecedencia_dias")["classe_vizinha"] * 100
        ax.plot(s.index, s.values, "-o", color=colour, linewidth=2, markersize=6, markeredgecolor="white")
        ax.annotate(f"{label}", (s.index[-1], s.values[-1]), xytext=(8, 0), textcoords="offset points", fontsize=8.4, va="center")
    ax.set_xticks(sorted(t["antecedencia_dias"].unique()))
    ax.set_xlabel("Days ahead")
    ax.set_ylabel("% right or one step off")
    ax.set_ylim(60, 90)
    tidy(ax)
    source(fig, "With five steps, 'one step off' is easy in the middle steps: compare the lines, not 100%. Source: plataforma/dados/modelos/teste_modelo_marracuene.csv.")
    save(fig, "charts/water_colour_forecast_skill.png")


# ----------------------------------------------------------------------------- maps
def map_radar():
    s1 = ROOT / "data/raw/radar/sentinel1"
    dry, ext = read_decimated(s1 / "2025/sentinel1_marracuene_2025-10_10m.tif", ["VH_p10"])
    wet, _ = read_decimated(s1 / "2026/sentinel1_marracuene_2026-01_10m.tif", ["VH_p10"])
    b, _ = read_decimated(ROOT / "data/processed/maps/modelo_b/agua_marracuene_2026-01_10m.tif", ["agua", "cheia"])
    d = district()
    fig = plt.figure(figsize=(12, 6.0), dpi=DPI)
    fig.subplots_adjust(top=0.78, bottom=0.11, left=0.02, right=0.98, wspace=0.04)
    header(fig, "Radar sees the flood through the clouds: Sentinel-1 and Model B",
           "Darkest radar return of each month (VH, 10th percentile). Smooth water reflects the radar away from the satellite and looks black.")
    panels = [("October 2025 (dry season)", dry["VH_p10"]), ("January 2026 (flood)", wet["VH_p10"])]
    for i, (title, img) in enumerate(panels):
        ax = fig.add_subplot(1, 3, i + 1)
        ax.imshow(img, extent=ext, cmap="gray", vmin=-28, vmax=-10, interpolation="nearest")
        ax.set_title(title, fontsize=10.5)
        map_axes(ax, ext, d)
    ax = fig.add_subplot(1, 3, 3)
    classes = np.full(b["agua"].shape, np.nan)
    classes[b["agua"] >= 0.5] = 1
    classes[b["cheia"] >= 0.5] = 2
    ax.set_facecolor(LAND)
    ax.imshow(classes, extent=ext, cmap=ListedColormap([WATER, FLOOD]), vmin=0.5, vmax=2.5, interpolation="nearest")
    ax.set_title("Model B, January 2026", fontsize=10.5)
    map_axes(ax, ext, d)
    ax.legend(handles=[Patch(color=WATER, label="usual water (river, lagoons)"), Patch(color=FLOOD, label="flood (water outside the usual)")],
              loc="lower right", fontsize=8, frameon=True, facecolor="white", edgecolor="#B9BBC6")
    fig.text(0.04, 0.058, "Black outline: Marracuene district. 30 m display of 10 m data. Model B over-flags flood in built-up areas and wet fields.",
             fontsize=8.2, color=MUTED)
    source(fig, "Sources: Copernicus Sentinel-1 GRD (ESA), monthly composites from Earth Engine; Model B = models/modelo_b_radar.joblib.")
    save(fig, "satellite/radar_dry_vs_flood_model_b.png")


def map_susceptibility():
    import rasterio
    from ete.platform import SUSCEPTIBILITY

    with rasterio.open(ROOT / "data/processed/maps/modelo_a/suscetibilidade_marracuene_30m.tif") as src:
        cls = src.read(2).astype("float32")
        cls[cls == src.nodata] = np.nan
        b = src.bounds
    ext = [b.left, b.right, b.bottom, b.top]
    with rasterio.open(ROOT / "data/processed/maps/zonas_de_aviso/zonas_de_aviso_marracuene_30m.tif") as src:
        zones = src.read(1)
    d = district()
    fig = plt.figure(figsize=(10, 7.4), dpi=DPI)
    fig.subplots_adjust(top=0.86, bottom=0.07, left=0.03, right=0.70)
    header(fig, "Model A: where the terrain favours flooding",
           "XGBoost on terrain only (height above the river, slope, wetness index, distances to water). Black line: the January 2026 flood.")
    ax = fig.add_subplot(111)
    ax.set_facecolor("white")
    names = {0: "permanent water", 1: "low", 2: "medium", 3: "high", 4: "very high"}
    ax.imshow(cls, extent=ext, cmap=ListedColormap([SUSCEPTIBILITY[k][1] for k in range(5)]), vmin=-0.5, vmax=4.5, interpolation="nearest")
    ax.contour(((zones == 1) | (zones == 2)).astype("float32"), levels=[0.5], colors=INK, linewidths=0.8, extent=ext, origin="upper")
    map_axes(ax, ext, None)
    d.boundary.plot(ax=ax, color=MUTED, linewidth=0.8, linestyle=(0, (4, 3)))
    label_places(ax, ["Marracuene", "Macaneta", "Machubo", "Mapelane", "Moveja"], ext)
    test = pd.read_csv(ROOT / "plataforma/dados/modelos/modelo_a_teste_2026.csv", index_col=0)
    en = {"baixa": "low", "média": "medium", "alta": "high", "muito alta": "very high"}
    handles = [Patch(color=SUSCEPTIBILITY[k][1], label=names[k]) for k in range(5)]
    fig.legend(handles=handles, loc="upper left", bbox_to_anchor=(0.71, 0.84), title="Susceptibility class", fontsize=9, title_fontsize=9.5,
               alignment="left")
    lines = ["Test on the 2026 flood", "(share of each class that flooded)"] + [f"{en[k]:<10} {v * 100:5.1f} %" for k, v in test["parte_da_classe_que_alagou"].items()]
    fig.text(0.715, 0.50, "\n".join(lines), fontsize=8.8, family="DejaVu Sans Mono", va="top")
    fig.text(0.715, 0.27, "ROC-AUC on the 2026 flood: 0.96\n(the model was trained on\nJRC water up to 2019 and\nnever saw this flood).\n\n"
             "Classes are broad: 'medium'\nholds tens of thousands of\nbuildings, so the public\nwarning zones use the\nmapped 2026 flood instead.",
             fontsize=8.6, va="top", color=INK)
    source(fig, "Sources: Copernicus DEM GLO-30, MERIT Hydro, JRC Global Surface Water; flood outline from Copernicus EMS EMSR857. Model: models/modelo_a_terreno.joblib.")
    save(fig, "maps/model_a_susceptibility.png")


def map_warning_zones():
    import geopandas as gpd
    import rasterio
    from ete.platform import ZONE_COLOURS

    with rasterio.open(ROOT / "data/processed/maps/zonas_de_aviso/zonas_de_aviso_marracuene_30m.tif") as src:
        z = src.read(1).astype("float32")
        b = src.bounds
    z[(z == 0) | (z == 255)] = np.nan
    ext = [b.left, b.right, b.bottom, b.top]
    places = gpd.read_file(ROOT / "data/processed/maps/zonas_de_aviso/lugares_marracuene.gpkg").to_crs(UTM)
    first = places[places["categoria"] == "alaga primeiro"].drop_duplicates("lugar")
    first = first.sort_values("lugar", key=lambda n: n != "Machubo")          # Machubo first: the place shown in the user guide
    large = places[places["categoria"] == "alaga em cheia grande"].drop_duplicates("lugar")
    d = district()
    dw, ds, de, dn = d.total_bounds
    ext_view = [dw - 1500, de + 1500, ds - 1500, dn + 1500]
    fig = plt.figure(figsize=(9, 8.4), dpi=DPI)
    fig.subplots_adjust(top=0.88, bottom=0.06, left=0.03, right=0.97)
    header(fig, "Warning zones: where the water arrived in January 2026",
           "Zone 1: flooded in the first Copernicus EMS maps. Zone 2: flooded at the largest extent. Dots: some named places.")
    ax = fig.add_subplot(111)
    ax.set_facecolor(LAND)
    ax.imshow(z, extent=ext, cmap=ListedColormap([ZONE_COLOURS[1], ZONE_COLOURS[2]]), vmin=0.5, vmax=2.5, interpolation="nearest")
    map_axes(ax, ext_view, d)
    placed = []
    for frame, colour, size in ((first, ZONE_COLOURS[1], 8.6), (large, INK, 7.8)):
        for _, r in frame.iterrows():
            x, y = r.geometry.x, r.geometry.y
            if any(abs(x - px) < 3500 and abs(y - py) < 1300 for px, py in placed):      # a label already sits there
                continue
            placed.append((x, y))
            ax.plot(x, y, "o", color=INK, markersize=3.4, markeredgecolor="white", markeredgewidth=0.7, zorder=9)
            ax.annotate(r["lugar"], (x, y), xytext=(4, 2), textcoords="offset points", fontsize=size, weight="bold",
                        color=colour, zorder=9, path_effects=halo())
    ax.legend(handles=[Patch(color=ZONE_COLOURS[1], label="zone 1: first to flood"), Patch(color=ZONE_COLOURS[2], label="zone 2: large flood")],
              loc="lower right", fontsize=9, frameon=True, facecolor="white", edgecolor="#B9BBC6")
    source(fig, "Sources: Copernicus EMS EMSR857 (AOI06 Palmeira) flood delineations; place names OpenStreetMap and GeoNames (not yet validated on the ground).")
    save(fig, "maps/warning_zones.png")


def map_module_q():
    import geopandas as gpd

    sections = gpd.read_file(ROOT / "plataforma/dados/vetores/trocos_modulo_q.geojson").to_crs(UTM)
    from ete.grid import load_aoi
    basin = load_aoi(cfg, "basin").to_crs(UTM)
    d = district()
    w, s, e, n = sections.total_bounds
    pad = 6000
    ext = [w - pad, e + pad, s - pad, n + pad]
    fig = plt.figure(figsize=(10, 7.2), dpi=DPI)
    fig.subplots_adjust(top=0.86, bottom=0.07, left=0.03, right=0.97)
    header(fig, "Module Q: the Incomati in Mozambique cut into nine sections, border to mouth",
           "Each section is the river's permanent water (Dynamic World, 10 m). Colour measured on every clear Sentinel-2 and Landsat image.")
    ax = fig.add_subplot(111)
    ax.set_facecolor(LAND)
    basin.boundary.plot(ax=ax, color=QUIET, linewidth=0.8)
    d.plot(ax=ax, color="#E7E5F0", zorder=1)
    flagged = sections["fiabilidade"] != "boa"
    sections[~flagged].plot(ax=ax, color=SERIES[0], linewidth=2.2, zorder=3)
    sections[flagged].plot(ax=ax, color="#9AA0A6", linewidth=2.2, zorder=3)
    for _, r in sections.iterrows():
        rep = r.geometry.representative_point()
        ax.annotate(r["troco"], (rep.x, rep.y), xytext=(0, 0), textcoords="offset points", fontsize=9, weight="bold", ha="center", va="center",
                    color="white", zorder=6, bbox=dict(boxstyle="circle,pad=0.25", fc=SERIES[0] if r["fiabilidade"] == "boa" else "#9AA0A6", ec="white"))
    map_axes(ax, ext, None, bar_km=20)
    from matplotlib.lines import Line2D
    ax.legend(handles=[Patch(color=SERIES[0], label="good agreement between satellites"), Patch(color="#9AA0A6", label="reduced reliability (Q3, Q6)"),
                       Patch(color="#E7E5F0", label="Marracuene district"), Line2D([], [], color=QUIET, label="Incomati basin boundary")],
              loc="upper left", fontsize=8.4, frameon=True, facecolor="white", edgecolor="#B9BBC6")
    names = ["Q1  border, Ressano Garcia", "Q2  km 37 to 74", "Q3  km 74 to 110", "Q4  Magude", "Q5  Xinavane", "Q6  km 184 to 221",
             "Q7  Manhiça", "Q8  Marracuene", "Q9  mouth / estuary"]
    ax.text(0.02, 0.10, "Sections (km from the border)\n" + "\n".join(names), transform=ax.transAxes, fontsize=8.2, va="bottom",
            bbox=dict(boxstyle="round,pad=0.4", fc="white", ec="#B9BBC6"))
    source(fig, "Q1-Q6 are 50-80 m wide (under 3 Landsat pixels): Sentinel-2 only, from 2017. Q7-Q9 have the 20-year record (Landsat from 2006).")
    save(fig, "maps/module_q_sections.png")


def map_water_colour():
    from ete import turbidity_map

    tif = ROOT / "data/processed/water_colour/cor_da_agua_2026-11-05.tif"
    jpg = ROOT / "data/processed/water_colour/cor_natural_2026-11-05.jpg"
    scratch = FIG / "_tmp"
    scratch.mkdir(parents=True, exist_ok=True)
    turbidity_map.render(cfg, tif, scratch / "colour.png", width_px=900, north_lat=turbidity_map.HOME_NORTH_LAT)
    turbidity_map.render(cfg, tif, scratch / "photo.jpg", width_px=900, north_lat=turbidity_map.HOME_NORTH_LAT, natural=jpg)
    photo, colour = Image.open(scratch / "photo.jpg"), Image.open(scratch / "colour.png").convert("RGB")
    for f in scratch.iterdir():
        f.unlink()
    scratch.rmdir()
    fig = plt.figure(figsize=(10, 8.4), dpi=DPI)
    fig.subplots_adjust(top=0.84, bottom=0.05, left=0.02, right=0.98, wspace=0.03)
    header(fig, "The colour of the water: satellite photograph and colour map",
           "Sentinel-2, 5 November 2026, from just north of Marracuene to the mouth. Each 10 m water pixel gets one of five fixed colour steps.")
    gs = fig.add_gridspec(1, 3, width_ratios=[1, 1, 0.62])
    for i, (img, title) in enumerate(((photo, "Satellite photograph (natural colour)"), (colour, "Water colour (NDTI) in five steps"))):
        ax = fig.add_subplot(gs[i])
        ax.imshow(img)
        ax.set_title(title, fontsize=10)
        ax.set_axis_off()
    from ete.turbidity_map import CLASSES, NO_READING, STEPS
    names = ["very clear", "clear", "usual", "muddy", "very muddy"]
    edges = (None,) + STEPS + (None,)
    ranges = [f"below {edges[1]:+.3f}"] + [f"{edges[k]:+.3f} to {edges[k + 1]:+.3f}" for k in range(1, 4)] + [f"above {edges[4]:+.3f}"]
    handles = [Patch(color=c, label=f"{names[k]}  ({ranges[k]})") for k, (_, c) in enumerate(CLASSES)]
    handles.append(Patch(color=NO_READING[1], label="no reading (cloud, shadow,\nplants, bank pixel)"))
    ax = fig.add_subplot(gs[2])
    ax.set_axis_off()
    ax.legend(handles=handles, loc="upper left", fontsize=8.6, title="Colour step (NDTI range)", title_fontsize=9.2, alignment="left")
    ax.text(0.0, 0.52, "Each step holds one fifth of ten\nyears of Sentinel-2 measurements\nof sections Q7-Q9, so the steps\n"
                       "compare today with the river's\nown history.\n\nThe colour says how much mud\nthe water carries. It does not\n"
                       "say whether the water is safe:\nriver water must always be\ntreated before drinking.", transform=ax.transAxes, fontsize=8.6, va="top")
    source(fig, "Sources: Copernicus Sentinel-2 L2A (ESA) through Earth Engine; src/ete/turbidity_map.py. Place names: OpenStreetMap.")
    save(fig, "satellite/water_colour_photo_and_map.jpg", photo=True)


# ----------------------------------------------------------------------------- reused figures and screenshots
PRESENTATION = {  # English presentation figures -> documentation (JPEG, 1600 px wide)
    "1_mapa_area_de_estudo.png": "maps/study_area.png",
    "2_cor_natural_legendas.png": "satellite/marracuene_natural_colour.jpg",
    "3_landsat_vs_sentinel2.png": "satellite/landsat_vs_sentinel2.jpg",
    "4_larguras_do_rio.png": "charts/river_width_by_section.png",
    "5_orbitas_e_revisitas.png": "charts/orbits_and_revisits.png",
    "6_antes_e_cheia_2026.png": "satellite/flood_2026_before_and_during.jpg",
    "7_zona_agricola_cheia.png": "satellite/farmland_before_flood_recession.jpg",
}


def presentation():
    folder = ROOT / "reports/apresentacao/en"
    for name, rel in PRESENTATION.items():
        image = Image.open(folder / name).convert("RGB")
        if image.width > 1600:
            image = image.resize((1600, round(image.height * 1600 / image.width)), Image.Resampling.LANCZOS)
        out = FIG / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        if out.suffix == ".jpg":
            image.save(out, "JPEG", quality=84, optimize=True, progressive=True)
        else:
            image.quantize(colors=128, method=Image.Quantize.MEDIANCUT, dither=Image.Dither.NONE).save(out, optimize=True)
        print(f"  {rel:<48} {out.stat().st_size / 1e3:6.0f} KB")


SCREENS = {  # output: (screenshot, top row, bottom row) in pixels of the 1280 px wide screenshots
    "platform/home_top.jpg": ("1280_inicio.png", 0, 830),
    "platform/home_water.jpg": ("1280_inicio.png", 860, 2010),
    "platform/home_floods.jpg": ("1280_inicio.png", 2050, 2690),
    "platform/home_doors.jpg": ("1280_inicio.png", 2690, 2990),        # not the curiosity cards: some of their labels are not translated yet
    "platform/water_today.jpg": ("1280_agua.png", 300, 1650),
    "platform/water_advice.jpg": ("1280_agua.png", 1690, 3460),
    "platform/water_coming_weeks.jpg": ("1280_agua.png", 3750, 4820),
    "platform/water_past_years.jpg": ("1280_agua.png", 5000, 6300),
    "platform/water_whole_river.jpg": ("1280_agua.png", 6340, 6930),
    "platform/water_how_we_measure.jpg": ("1280_agua.png", 6950, 7560),
    "platform/floods_ten_days.jpg": ("1280_cheias.png", 300, 1330),
    "platform/floods_colour_meanings.jpg": ("1280_cheias.png", 1400, 1800),
    "platform/floods_where_water_arrives.jpg": ("1280_cheias.png", 2010, 2930),
    "platform/floods_from_space.jpg": ("1280_cheias.png", 2990, 4110),
    "platform/floods_twenty_years.jpg": ("1280_cheias.png", 4140, 4990),
    "platform/alerts_sign_up.jpg": ("1280_alertas.png", 300, 1600),
    "platform/alerts_community_leaders.jpg": ("1280_alertas.png", 2200, 2760),
    "platform/project_top.jpg": ("1280_sobre.png", 300, 1650),
    "platform/project_how_it_works.jpg": ("1280_sobre.png", 2060, 2600),
    "platform/project_trust.jpg": ("1280_sobre.png", 4300, 4760),
    "platform/project_models.jpg": ("1280_sobre.png", 5470, 6360),
    "platform/place_page_top.jpg": ("1280_zona_Machubo.png", 0, 1520),
    "platform/place_page_from_space.jpg": ("1280_zona_Machubo.png", 2820, 3570),
    "platform/account.jpg": ("1280_conta.png", 300, 1290),
}
PHONES = ("390_inicio.png", "390_cheias.png", "390_zona_Machubo.png")


def screens():
    if not CAPTURES.exists():
        print(f"  no screenshots in {CAPTURES.relative_to(ROOT)}: run scripts/capturar_plataforma.py first (see the docstring)")
        return
    for rel, (name, top, bottom) in SCREENS.items():
        image = Image.open(CAPTURES / name).convert("RGB")
        crop = image.crop((0, top, image.width, min(bottom, image.height)))
        out = FIG / rel
        out.parent.mkdir(parents=True, exist_ok=True)
        crop.save(out, "JPEG", quality=82, optimize=True, progressive=True, subsampling=0)
        print(f"  {rel:<48} {out.stat().st_size / 1e3:6.0f} KB")
    # three phone screens side by side, at the size a phone shows them (390 px each)
    shots = [Image.open(CAPTURES / n).convert("RGB") for n in PHONES]
    height = 1500
    cut = [s.crop((0, 0, s.width, height * 2)).resize((390, height), Image.Resampling.LANCZOS) for s in shots]
    gap = 28
    sheet = Image.new("RGB", (len(cut) * 390 + (len(cut) + 1) * gap, height + 2 * gap), "#E2E1EA")
    for i, c in enumerate(cut):
        sheet.paste(c, (gap + i * (390 + gap), gap))
    out = FIG / "platform/phone_views.jpg"
    sheet.save(out, "JPEG", quality=82, optimize=True, progressive=True, subsampling=0)
    print(f"  {'platform/phone_views.jpg':<48} {out.stat().st_size / 1e3:6.0f} KB")


# ----------------------------------------------------------------------------- link check
def check() -> bool:
    pages = sorted(DOCS.glob("*.md"))
    used, problems = set(), []
    for page in pages:
        text = page.read_text()
        for link in re.findall(r"\]\(([^)#\s]+)(?:#[^)]*)?\)", text) + re.findall(r'src="([^"]+)"', text):
            if link.startswith(("http://", "https://", "mailto:")):
                continue
            target = (page.parent / link).resolve()
            if not target.exists() and "guias" in Path(link).parts:          # guias/ in the repository = docs/ in the project folder
                target = (page.parent / link.replace("guias", "docs", 1)).resolve()
            if target.is_relative_to(FIG.resolve()):
                used.add(target)
            if not target.exists():
                problems.append(f"{page.name}: broken link {link}")
    figures = {f.resolve() for f in FIG.rglob("*") if f.is_file()}
    for f in sorted(figures - used):
        problems.append(f"figure not used by any page: {f.relative_to(DOCS)}")
    size = sum(f.stat().st_size for f in figures) / 1e6
    print(f"\n{len(pages)} pages, {len(figures)} figures ({size:.1f} MB)")
    for p in problems:
        print("  PROBLEM:", p)
    print("LINKS OK" if not problems else f"{len(problems)} problem(s)")
    return not problems


GROUPS = {
    "charts": [chart_timeline, chart_discharge_history, chart_january_2026, chart_alert_days, chart_algorithms, chart_model_b_area, chart_model_c,
               chart_turbidity_skill, chart_tide_effect, chart_turbidity_by_discharge, chart_cross_satellite, chart_colour_and_flow,
               chart_colour_forecast],
    "maps": [map_susceptibility, map_warning_zones, map_module_q],
    "satellite": [map_radar, map_water_colour, presentation],
    "platform": [screens],
}

if __name__ == "__main__":
    p = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    p.add_argument("--only", nargs="*", choices=list(GROUPS), help="build only these groups")
    p.add_argument("--check", action="store_true", help="only check the links between pages and figures")
    a = p.parse_args()
    if not a.check:
        for group in a.only or GROUPS:
            print(group)
            for build in GROUPS[group]:
                result = build()
                if build is chart_alert_days:
                    print(f"  (orange or red in {result[0]} of {result[1]} hydrological years, red in {result[2]})")
    sys.exit(0 if check() else 1)
