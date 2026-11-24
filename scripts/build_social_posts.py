"""Imagens para LinkedIn/Facebook com o ponto de situação do ETE (dados das semanas 1 e 2), em inglês
(público internacional; a versão anterior em português ficou em reports/redes_sociais/pt/).

    .venv/bin/python scripts/build_social_posts.py

Escreve em reports/redes_sociais/ cinco imagens 1080 x 1350 (formato 4:5, o que ocupa mais
espaço no feed das duas redes), feitas a partir dos dados reais já descarregados:
  1_capa.png              Sentinel-2 em cor verdadeira do distrito de Marracuene
  2_radar_cheia.png       Sentinel-1: estação seca vs cheia de janeiro de 2026
  3_caudal_20_anos.png    caudal diário do Incomáti 2006-2026 (GloFAS)
  4_terreno.png           altitude e altura acima do rio (HAND)
  5_trocos_do_rio.png     os nove troços do rio seguidos para a qualidade da água
Todas levam o logótipo do ETE e, no rodapé, os da IAU-OAD e da DARA.
Não descarrega nada.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib import patheffects
from matplotlib.colors import LinearSegmentedColormap
from PIL import Image, ImageDraw
from rasterio.enums import Resampling

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "redes_sociais"
W, H, DPI = 1080, 1350, 120  # pixels; figsize = W/DPI x H/DPI

TEAL_DARK, TEAL, FOAM, SAND, INK = "#082f2c", "#0f766e", "#2bb5a0", "#f7f3ea", "#10231f"
ORANGE, RED = "#e8893a", "#c8432b"
MESES = "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split()
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK, "axes.edgecolor": "#8aa29d"})


# ---------- logótipos ----------
def _logo_ete() -> np.ndarray:
    im = Image.open(ROOT / "logos" / "ETE_Log.jpeg").convert("RGB")
    w, h = im.size
    r = min(w, h) / 2 - 30
    mask = Image.new("L", (w * 4, h * 4), 0)
    ImageDraw.Draw(mask).ellipse([(w / 2 - r) * 4, (h / 2 - r) * 4, (w / 2 + r) * 4, (h / 2 + r) * 4], fill=255)
    im = im.convert("RGBA")
    im.putalpha(mask.resize((w, h), Image.LANCZOS))
    return np.asarray(im.crop((int(w / 2 - r), int(h / 2 - r), int(w / 2 + r), int(h / 2 + r))))


def _logo_dara() -> np.ndarray:
    """DARA original, mas com o preto (África e texto) passado a creme para ler sobre o rodapé escuro."""
    a = np.asarray(Image.open(ROOT / "logos" / "DARA_logo.avif").convert("RGBA")).copy()
    rgb = a[..., :3].astype(int)
    dark = (rgb.max(axis=2) < 90) & (rgb.max(axis=2) - rgb.min(axis=2) < 40)
    a[dark, :3] = (247, 243, 234)
    return a


def _logo_oad() -> np.ndarray:
    im = Image.open(ROOT / "logos" / "01_IAU-OAD_transparent.png").convert("RGBA")
    return np.asarray(im.crop(im.getchannel("A").getbbox()))


LOGOS = {"ete": _logo_ete(), "dara": _logo_dara(), "oad": _logo_oad()}


def _place(fig, img, x, y, h_px):
    """Põe uma imagem com canto inferior esquerdo em (x, y) px e altura h_px."""
    w_px = h_px * img.shape[1] / img.shape[0]
    ax = fig.add_axes([x / W, y / H, w_px / W, h_px / H])
    ax.imshow(img)
    ax.axis("off")
    return w_px


def frame(title: str, subtitle: str, step: str):
    """Figura com cabeçalho (logo ETE + título) e rodapé (apoios). Devolve a figura."""
    fig = plt.figure(figsize=(W / DPI, H / DPI), dpi=DPI, facecolor=SAND)
    # cabeçalho
    _place(fig, LOGOS["ete"], 40, H - 150, 110)
    fig.text(170 / W, (H - 58) / H, title, fontsize=21, fontweight="bold", color=TEAL_DARK, va="center")
    fig.text(170 / W, (H - 108) / H, subtitle, fontsize=12.5, color="#3d5752", va="center", linespacing=1.35)
    fig.text(170 / W, (H - 24) / H, step, fontsize=10.5, color=TEAL, va="center", fontweight="bold")
    # rodapé escuro com os apoios
    bar = fig.add_axes([0, 0, 1, 120 / H])
    bar.set_facecolor(TEAL_DARK)
    bar.set_xticks([]), bar.set_yticks([])
    for s in bar.spines.values():
        s.set_visible(False)
    fig.text(40 / W, 60 / H, "Eyes to Earth (ETE)\nMarracuene · Incomati River · Mozambique",
             fontsize=11, color=SAND, va="center", linespacing=1.5)
    fig.text(510 / W, 60 / H, "Supported by", fontsize=10, color="#b9d8d2", va="center")
    x = 650
    x += _place(fig, LOGOS["oad"], x, 18, 84) + 30
    _place(fig, LOGOS["dara"], x, 22, 76)
    return fig


def body_axes(fig, top_px=170, bottom_px=140, left=40, right=40):
    return [left / W, bottom_px / H, (W - left - right) / W, (H - top_px - bottom_px) / H]


def note(fig, text, y_px=150):
    fig.text(40 / W, y_px / H, text, fontsize=11, color="#3d5752", va="bottom", linespacing=1.4)


def save(fig, name):
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / name, dpi=DPI, facecolor=fig.get_facecolor())
    plt.close(fig)
    print(f"{name:24s} {(OUT / name).stat().st_size / 1024:6.0f} KB")


# ---------- dados ----------
def read(file, bands, factor=4):
    """Bandas em unidades físicas, reduzidas 'factor' vezes (poupa memória)."""
    with rasterio.open(file) as src:
        names = list(src.descriptions)
        shape = (src.height // factor, src.width // factor)
        out = {}
        for b in bands:
            i = names.index(b) + 1 if b in names else 1
            raw = src.read(i, out_shape=shape, resampling=Resampling.average if factor > 1 else Resampling.nearest)
            d = raw.astype("float32") * np.float32(src.scales[i - 1])
            if src.nodata is not None:
                d[raw == src.nodata] = np.nan
            out[b] = d
        return out, src.bounds


def clean_ax(ax):
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_xlabel(""), ax.set_ylabel("")
    ax.set_facecolor("none")
    for s in ax.spines.values():
        s.set_visible(False)


def district():
    return gpd.read_file(ROOT / "data/raw/aoi/marracuene_district.geojson")


# ---------- 1. capa ----------
def best_s2_month(candidates):
    best = None
    for m in candidates:
        f = ROOT / f"data/raw/optical/sentinel2/{m[:4]}/sentinel2_marracuene_{m}_10m.tif"
        if not f.exists():
            continue
        d, _ = read(f, ["red"], 16)
        gap = np.isnan(d["red"]).mean()
        if best is None or gap < best[1]:
            best = (m, gap)
    return best[0]


def slide_capa():
    month = best_s2_month(["2025-06", "2025-07", "2025-08", "2025-09", "2026-06", "2026-07", "2026-08"])
    f = ROOT / f"data/raw/optical/sentinel2/{month[:4]}/sentinel2_marracuene_{month}_10m.tif"
    d, b = read(f, ["red", "green", "blue"], 4)
    rgb = np.dstack([d["red"], d["green"], d["blue"]])
    lo, hi = np.nanpercentile(rgb, 2), np.nanpercentile(rgb, 98)
    rgb = np.clip((rgb - lo) / (hi - lo), 0, 1) ** 0.8
    rgb = np.dstack([np.nan_to_num(rgb, nan=0.0), (~np.isnan(rgb).any(axis=2)).astype(float)])

    fig = frame("Eyes to Earth (ETE)", "Machine Learning for water monitoring\nand flood alerts on the Incomati River",
                "PROJECT UPDATE")
    ax = fig.add_axes(body_axes(fig, top_px=170, bottom_px=250))
    ax.imshow(rgb, extent=(b.left, b.right, b.bottom, b.top))
    district().to_crs(32736).boundary.plot(ax=ax, color="white", lw=1.6, ls="--")
    clean_ax(ax)
    ax.text(0.02, 0.02, f"Sentinel-2 · true colour · {month} · Marracuene district (dashed)",
            transform=ax.transAxes, fontsize=10, color="white",
            path_effects=[patheffects.withStroke(linewidth=3, foreground="black")])
    fig.text(40 / W, 205 / H, "Weeks 1 and 2 completed: data collection and processing", fontsize=15,
             fontweight="bold", color=TEAL_DARK)
    fig.text(40 / W, 140 / H, "20 years of satellite data (Landsat, Sentinel-1 and 2), rainfall, soil moisture,\n"
             "river discharge and terrain, all on one grid and ready for the models.",
             fontsize=12, color="#3d5752", linespacing=1.45)
    save(fig, "1_capa.png")


# ---------- 2. radar ----------
def slide_radar():
    def vh(month):
        f = ROOT / f"data/raw/radar/sentinel1/{month[:4]}/sentinel1_marracuene_{month}_10m.tif"
        d, b = read(f, ["VH_p10"], 4)
        return d["VH_p10"], b

    dry, b = vh("2025-08")
    wet, _ = vh("2026-01")
    grey = LinearSegmentedColormap.from_list("g", ["#0b0f0e", "#f2efe6"])
    # água "nova": escura (<= -22 dB, a regra simples testada no notebook 20) em janeiro e não no mês seco
    new = (wet <= -22) & ~(dry <= -22)
    mask = district().to_crs(32736)

    fig = frame("Radar sees the flood through the clouds", "Sentinel-1 (radar): calm water appears dark.\n"
                "Same area, dry season vs the January 2026 flood", "WEEK 2 · PROCESSING")
    for i, (arr, lab) in enumerate([(dry, "August 2025 (dry)"), (wet, "January 2026 (flood)")]):
        ax = fig.add_axes([(40 + i * 510) / W, 270 / H, 490 / W, 900 / H])
        ax.imshow(arr, cmap=grey, vmin=-28, vmax=-10, extent=(b.left, b.right, b.bottom, b.top))
        if i == 1:
            over = np.zeros(new.shape + (4,))
            over[new] = (0.17, 0.71, 0.63, 0.85)
            ax.imshow(over, extent=(b.left, b.right, b.bottom, b.top))
        mask.boundary.plot(ax=ax, color=ORANGE, lw=1.2)
        ax.set_xlim(b.left + 12000, b.right - 4000)
        clean_ax(ax)
        ax.set_title(lab, fontsize=14, fontweight="bold", color=TEAL_DARK, pad=8)
    km2 = new[~np.isnan(wet)].sum() * (40 * 40) / 1e6
    fig.text(40 / W, 215 / H, f"In teal: about {km2:,.0f} km² of new water in the study area",
             fontsize=13.5, fontweight="bold", color=TEAL)
    note(fig, "Orange: district boundary. Checked against the official flood map (Copernicus EMS, EMSR857).", 160)
    save(fig, "2_radar_cheia.png")


# ---------- 3. caudal ----------
def slide_caudal():
    s = pd.read_csv(ROOT / "data/processed/series/hydromet_daily.csv", parse_dates=["date"],
                    usecols=["date", "discharge_m3s"]).dropna().set_index("date")["discharge_m3s"]
    fig = frame("20 years of the Incomati River", "Daily discharge at Marracuene, 2006 to 2026 (GloFAS).\n"
                "Each peak is a flood that reached the district", "WEEK 1 · DATA")
    ax = fig.add_axes([110 / W, 330 / H, 920 / W, 800 / H], facecolor=SAND)
    ax.fill_between(s.index, s.values, color=FOAM, alpha=0.35, lw=0)
    ax.plot(s.index, s.values, color=TEAL, lw=0.9)
    for lim, lab, c in [(376, "orange", ORANGE), (970, "red", RED)]:
        ax.axhline(lim, color=c, lw=1.2, ls="--")
        ax.text(s.index[-1], lim + 40, f"{lab} alert threshold ({lim} m³/s)", color=c, fontsize=10, ha="right",
                bbox=dict(facecolor=SAND, edgecolor="none", pad=1))
    for year in (2013, 2023, 2026):
        y = s[str(year)]
        d = y.idxmax()
        ax.annotate(f"{MESES[d.month - 1]} {d.year}\n{y.max():,.0f} m³/s", (d, y.max()), xytext=(-70, 10),
                    textcoords="offset points", fontsize=11, fontweight="bold", color=TEAL_DARK,
                    arrowprops=dict(arrowstyle="-", color=TEAL_DARK, lw=0.8))
    ax.set_ylabel("m³/s", fontsize=12)
    ax.set_ylim(0, s.max() * 1.18)
    ax.margins(x=0.01)
    for sp in ("top", "right"):
        ax.spines[sp].set_visible(False)
    ax.tick_params(labelsize=11)
    ax.grid(axis="y", color="#d9d3c4", lw=0.6)
    fig.text(40 / W, 215 / H, "The three largest floods: 2013, 2023 and 2026", fontsize=13.5, fontweight="bold", color=TEAL)
    note(fig, "We also gathered daily rainfall (CHIRPS and IMERG), soil moisture (ERA5-Land\n"
              "and SMAP) and temperature to train the alert system.", 145)
    save(fig, "3_caudal_20_anos.png")


# ---------- 4. terreno ----------
def slide_terreno():
    t = ROOT / "data/raw/static/terrain"
    dem, b = read(t / "dem_marracuene_30m.tif", ["x"], 2)
    hand, _ = read(t / "hand_marracuene_30m.tif", ["x"], 2)
    dem, hand = dem["x"], hand["x"]
    with rasterio.open(t / "dem_marracuene_30m.tif") as src:
        crs = src.crs
    mask = district().to_crs(crs)
    fig = frame("Terrain decides where the water goes", "30 m digital elevation model and height above\n"
                "the nearest drainage (HAND)", "WEEK 2 · PROCESSING")
    items = [(dem, "Elevation (m)", "terrain", 0, 60), (hand, "Height above the river (m)", "YlGnBu_r", 0, 15)]
    for i, (arr, lab, cmap, lo, hi) in enumerate(items):
        ax = fig.add_axes([(40 + i * 510) / W, 345 / H, 490 / W, 800 / H])
        im = ax.imshow(arr, cmap=cmap, vmin=lo, vmax=hi, extent=(b.left, b.right, b.bottom, b.top))
        mask.boundary.plot(ax=ax, color="black", lw=1)
        ax.set_xlim(b.left, b.right - 15000)
        clean_ax(ax)
        ax.set_title(lab, fontsize=14, fontweight="bold", color=TEAL_DARK, pad=8)
        cax = fig.add_axes([(90 + i * 510) / W, 305 / H, 390 / W, 14 / H])
        cb = fig.colorbar(im, cax=cax, orientation="horizontal")
        cb.ax.tick_params(labelsize=10)
        cb.outline.set_visible(False)
    fig.text(40 / W, 215 / H, "Dark blue = only a few metres above the river: the first areas to flood",
             fontsize=13, fontweight="bold", color=TEAL)
    note(fig, "Six more static layers: slope, wetness index (TWI), distance to river, distance\n"
              "to water, land cover (ESA WorldCover) and historical water frequency (JRC).", 145)
    save(fig, "4_terreno.png")


# ---------- 5. troços ----------
def slide_trocos():
    gpkg = ROOT / "data/interim/water_quality/trocos_rio.gpkg"
    lines = gpd.read_file(gpkg, layer="linhas").to_crs(4326)
    basin = gpd.read_file(ROOT / "data/raw/aoi/incomati_basin.geojson").to_crs(4326)
    rivers = gpd.read_file(ROOT / "data/raw/static/hydrography/rivers_incomati.geojson").to_crs(4326)
    dist = district().to_crs(4326)
    fig = frame("Water quality: 9 river sections", "From Ressano Garcia (border) to the river mouth,\n"
                "we track water turbidity from space, section by section", "WEEK 2 · PROCESSING")
    ax = fig.add_axes([40 / W, 270 / H, 1000 / W, 880 / H])
    basin.plot(ax=ax, color="#e3ebe2", edgecolor="#b8c8bd", lw=0.8)
    rivers.cx[31.8:33.2, -26.0:-24.8].plot(ax=ax, color="#9fbfc4", lw=0.6)
    dist.plot(ax=ax, color=ORANGE, alpha=0.18, edgecolor=ORANGE, lw=1.4)
    cmap = plt.get_cmap("viridis")
    for _, r in lines.iterrows():
        c = cmap((r.numero - 1) / 8)
        if r.geometry.geom_type.endswith("Point"):
            ax.scatter(r.geometry.x, r.geometry.y, s=180, color=c, zorder=5, edgecolor="white", lw=1.5)
            p = r.geometry
        else:
            gpd.GeoSeries([r.geometry]).plot(ax=ax, color=c, lw=5, zorder=4)
            p = r.geometry.interpolate(0.5, normalized=True)
        ax.text(p.x + 0.03, p.y, r.troco, fontsize=13, fontweight="bold", color=TEAL_DARK, zorder=6,
                path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])
    ax.set_xlim(31.85, 33.15)
    ax.set_ylim(-25.95, -24.9)
    ax.set_aspect(1 / np.cos(np.radians(25.4)))
    clean_ax(ax)
    ax.text(32.42, -25.72, "Marracuene", fontsize=12, color="#9a4f12", fontweight="bold",
            path_effects=[patheffects.withStroke(linewidth=3, foreground="white")])
    fig.text(40 / W, 215 / H, "Every Sentinel-2 (since 2017) and Landsat image, section by section", fontsize=13.5,
             fontweight="bold", color=TEAL)
    note(fig, "Turbidity index (NDTI) as a relative indicator: compares months and sections.\n"
              "Orange: Marracuene district.", 145)
    save(fig, "5_trocos_do_rio.png")


if __name__ == "__main__":
    slide_capa()
    slide_radar()
    slide_caudal()
    slide_terreno()
    slide_trocos()
