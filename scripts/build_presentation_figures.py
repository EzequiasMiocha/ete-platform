"""Figuras de apresentação (16:9) sobre a área de estudo, os satélites e o rio.

    .venv/bin/python scripts/build_presentation_figures.py

Escreve em reports/apresentacao/pt/ e reports/apresentacao/en/ (e um PDF por língua com todas):
  1_mapa_area_de_estudo.png     aoi.geojson, distrito, bacia, rio e localização em Moçambique
  2_cor_natural_legendas.png    Sentinel-2 em cor natural com rio, planície, campos e vila
  3_landsat_vs_sentinel2.png    a mesma zona agrícola de Marracuene a 30 m (Landsat) e a 10 m (Sentinel-2)
  4_larguras_do_rio.png         tabela de larguras do Incomáti por troço (largura_por_troco.csv)
  5_orbitas_e_revisitas.png     revisitas oficiais vs passagens reais medidas sobre Marracuene
  6_antes_e_cheia_2026.png      Sentinel-2 de um só dia: 23 out 2025 (seco) vs 24 jan 2026 (cheia) + água detectada
  7_zona_agricola_cheia.png     zona agrícola em Landsat e Sentinel-2: antes, cheia e recuo (cenas de um só dia)

As figuras 6 e 7 usam as cenas de scripts/download_flood_scenes.py (data/raw/optical/cenas_cheia_2026/).

A figura 5 lê reports/apresentacao/passagens_2025_2026.csv (datas de cada passagem sobre o ponto
32.70 E, 25.70 S, tiradas do Earth Engine; só metadados, menos de 1 MB). Se o ficheiro não
existir, é pedido ao Earth Engine. As outras figuras não descarregam nada.
"""

from pathlib import Path

import geopandas as gpd
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import rasterio
from matplotlib import patheffects
from matplotlib.lines import Line2D
from matplotlib.patches import FancyArrow, Rectangle
from pyproj import Transformer
from rasterio.enums import Resampling
from rasterio.windows import from_bounds

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "reports" / "apresentacao"
PASSES = OUT / "passagens_2025_2026.csv"
POINT = (32.70, -25.70)                      # planície do Incomáti, onde se contam as passagens
SCENE_DIR = ROOT / "data/raw/optical/cenas_cheia_2026"   # cenas de um só dia (scripts/download_flood_scenes.py)
S2_DRY = SCENE_DIR / "sentinel2_antes_2025-10-23_30m.tif"                 # Sentinel-2A, 0% de nuvens no distrito
S2_DRY_FIELDS = SCENE_DIR / "sentinel2_antes_2025-10-23_zona_agricola_10m.tif"
LS_DRY = SCENE_DIR / "landsat_antes_2025-09-22_30m.tif"                   # Landsat 9, 0% de nuvens no distrito
FIELDS = (32.765, -25.515, 32.815, -25.470)  # zona agrícola (talhões) na planície, ~5 x 5 km
TOWN = (32.6763, -25.7400)                   # Vila de Marracuene (OpenStreetMap, place=town), junto à ponte
MAPUTO = (32.5627, -25.9509)                 # Cidade de Maputo (OpenStreetMap)
UTM = "EPSG:32736"
TO_UTM = Transformer.from_crs(4326, UTM, always_xy=True)

INK, TEAL_DARK, TEAL, FOAM, ORANGE, RED, GREY = "#10231f", "#082f2c", "#0f766e", "#2bb5a0", "#e8893a", "#c8432b", "#6b7f7a"
plt.rcParams.update({"font.family": "DejaVu Sans", "text.color": INK, "axes.edgecolor": "#9fb2ad"})
W, H, DPI = 16, 9, 120

T = {
    "pt": {
        "map_title": "Área de estudo: distrito de Marracuene e baixo Incomáti",
        "map_sub": "Rectângulo = área das imagens (aoi.geojson, distrito + 5 km), 52 x 54 km, UTM 36S",
        "aoi": "Área das imagens (aoi.geojson)", "district": "Distrito de Marracuene", "basin": "Bacia do Incomáti",
        "river": "Rio Incomáti e afluentes", "outside": "Fora da área das imagens", "town": "Vila de Marracuene", "maputo": "Maputo", "ocean": "Oceano\nÍndico",
        "moz": "Moçambique", "sa": "África do Sul", "esw": "Essuatíni", "inset": "Localização",
        "nat_title": "Marracuene vista pelo Sentinel-2 (cor natural)",
        "nat_sub": "Imagem de 23 out 2025 (estação seca, antes da cheia), Sentinel-2A, bandas vermelho-verde-azul",
        "lab_river": "Rio Incomáti", "lab_plain": "Planície de\ninundação", "lab_fields": "Campos agrícolas\n(talhões)",
        "lab_town": "Vila de\nMarracuene", "lab_dunes": "Dunas costeiras", "lab_urban": "Zimpeto e Magoanine\n(norte de Maputo)",
        "lab_box": "Zona da figura 3",
        "pair_title": "A mesma zona agrícola de Marracuene em dois satélites",
        "pair_sub": "Imagens de um só dia sem nuvens, antes da cheia, mesma escala. A névoa no canto superior direito é provavelmente fumo de queimadas.",
        "landsat": "Landsat 9 (22 set 2025): píxel de 30 m", "s2": "Sentinel-2A (23 out 2025): píxel de 10 m",
        "pair_note": "Um píxel Landsat = 9 píxeis Sentinel-2. Os limites dos talhões e os canais de rega só se lêem a 10 m.",
        "w_title": "Largura do rio Incomáti por troço",
        "w_sub": "Água permanente (Dynamic World 2019-2025) a dividir pelo comprimento do troço",
        "w_cols": ["Troço", "Nome", "Compr.\n(km)", "Água perm.\n(ha)", "Largura\nmédia (m)",
                   "Píxeis\nLandsat", "Píxeis\nSentinel-2", "Landsat\nutilizável"],
        "w_note": ("Píxeis = largura / tamanho do píxel (30 m e 10 m). Abaixo de ~3 píxeis, quase todos tocam a margem.\n"
                   "Landsat utilizável = sobram pelo menos 5 ha depois de tirar 30 m junto às margens. "
                   "Q9 é o estuário: não tem largura de canal."),
        "yes": "sim", "no": "não", "estuary": "estuário",
        "o_title": "Órbitas e revisitas: o que dizem as agências e o que medimos",
        "o_sub": "Passagens reais sobre a planície de Marracuene (32,70° E, 25,70° S), Earth Engine, {period}",
        "o_cols": ["", "Oficial", "Medido em Marracuene"],
        "o_rows": [
            ("Landsat 8: revisita", "16 dias", "l8"), ("Landsat 9: revisita", "16 dias", "l9"),
            ("Landsat 8 + 9 em conjunto", "8 dias", "l89"), ("Altitude Landsat 8 e 9", "705 km", "-"),
            ("Sentinel-2: cada satélite", "10 dias", "s2one"), ("Sentinel-2 par (2B + 2C)", "5 dias", "s2pair"),
            ("Sentinel-2A (campanha prolongada)", "parcial", "s2a"), ("Órbitas Sentinel-2 sobre Marracuene", "-", "orbits"),
            ("Sentinel-2: todas as passagens", "-", "s2all"),
        ],
        "days": "dias", "median": "mediana", "of": "de", "intervals": "intervalos",
        "tl_title": "Passagens de {start} a {end} (cheio = menos de 20% de nuvens)",
        "orbit": "órbita relativa", "not_measured": "não se mede aqui",
        "f_title": "A cheia de janeiro de 2026 vista pelo Sentinel-2",
        "f_sub": "Imagens de um só dia (não compósitos mensais). Água = índice MNDWI > 0, só dentro do distrito, sem nuvens",
        "f_before": "23 out 2025: sem cheia", "f_flood": "24 jan 2026: cheia", "f_water": "Água detectada",
        "q": "caudal", "cloud": "sem dados no distrito", "water_km2": "água no distrito",
        "f_leg_perm": "Água antes (rio, lagoas)", "f_leg_new": "Água nova na cheia", "f_leg_cloud": "Sem dados (nuvens ou fora da imagem)",
        "f_note": ("Pico do caudal a 19 jan 2026 (2 987 m³/s, GloFAS). Antes: Landsat 31,5 km² e Sentinel-2 30,8 km² de água, quase iguais.\n"
                   "Na cheia a área é um mínimo: as nuvens tapam parte do distrito. A água nova ({new:.0f} km²) bate com o radar Sentinel-1 (~214 km²)."),
        "z_title": "Zona agrícola de Marracuene: antes, durante e depois da cheia",
        "z_sub": "Cenas de um só dia, cor natural, mesma escala e mesma zona da figura 3",
        "z_cols": ["Antes", "Cheia", "Recuo"],
        "z_rows": ["Landsat 8/9\n30 m", "Sentinel-2\n10 m"],
        "z_note": ("O Landsat de 28 jan tinha 65% do distrito com nuvens; esta zona ficou visível, mas com neblina. O Sentinel-2 passa a cada ~2 dias\n"
                   "e apanhou um dia mais limpo (24 jan). Com céu fechado, o radar Sentinel-1 continua a ser a fonte principal. Caudal: GloFAS (modelo)."),
        "o_note": ("Fontes: NASA/USGS (Landsat 9: órbita de 705 km, revisita combinada de 8 dias); ESA/Copernicus "
                   "\n(Sentinel-2C substituiu o 2A em 21/01/2025; o 2A continua numa campanha prolongada até ao fim de 2027)."),
    },
    "en": {
        "map_title": "Study area: Marracuene district and the lower Incomati",
        "map_sub": "Rectangle = imagery area (aoi.geojson, district + 5 km), 52 x 54 km, UTM 36S",
        "aoi": "Imagery area (aoi.geojson)", "district": "Marracuene district", "basin": "Incomati basin",
        "river": "Incomati River and tributaries", "outside": "Outside the imagery area", "town": "Marracuene town", "maputo": "Maputo", "ocean": "Indian\nOcean",
        "moz": "Mozambique", "sa": "South Africa", "esw": "Eswatini", "inset": "Location",
        "nat_title": "Marracuene seen by Sentinel-2 (natural colour)",
        "nat_sub": "Image of 23 Oct 2025 (dry season, before the flood), Sentinel-2A, red-green-blue bands",
        "lab_river": "Incomati River", "lab_plain": "Floodplain", "lab_fields": "Farm fields\n(plots)",
        "lab_town": "Marracuene\ntown", "lab_dunes": "Coastal dunes", "lab_urban": "Zimpeto and Magoanine\n(northern Maputo)",
        "lab_box": "Area of figure 3",
        "pair_title": "The same farmland in Marracuene from two satellites",
        "pair_sub": "Cloud-free single-day images before the flood, same scale. The haze at top right is most likely smoke from field burning.",
        "landsat": "Landsat 9 (22 Sep 2025): 30 m pixel", "s2": "Sentinel-2A (23 Oct 2025): 10 m pixel",
        "pair_note": "One Landsat pixel = 9 Sentinel-2 pixels. Plot boundaries and irrigation canals are only readable at 10 m.",
        "w_title": "Width of the Incomati River by section",
        "w_sub": "Permanent water (Dynamic World 2019-2025) divided by section length",
        "w_cols": ["Section", "Name", "Length\n(km)", "Perm. water\n(ha)", "Mean\nwidth (m)",
                   "Landsat\npixels", "Sentinel-2\npixels", "Landsat\nusable"],
        "w_note": ("Pixels = width / pixel size (30 m and 10 m). Below ~3 pixels, almost every pixel touches a bank.\n"
                   "Landsat usable = at least 5 ha left after removing 30 m along the banks. "
                   "Q9 is the estuary: it has no channel width."),
        "yes": "yes", "no": "no", "estuary": "estuary",
        "o_title": "Orbits and revisits: what the agencies state and what we measured",
        "o_sub": "Actual passes over the Marracuene floodplain (32.70° E, 25.70° S), Earth Engine, {period}",
        "o_cols": ["", "Official", "Measured at Marracuene"],
        "o_rows": [
            ("Landsat 8: revisit", "16 days", "l8"), ("Landsat 9: revisit", "16 days", "l9"),
            ("Landsat 8 + 9 combined", "8 days", "l89"), ("Altitude Landsat 8 and 9", "705 km", "-"),
            ("Sentinel-2: each satellite", "10 days", "s2one"), ("Sentinel-2 pair (2B + 2C)", "5 days", "s2pair"),
            ("Sentinel-2A (extended campaign)", "partial", "s2a"), ("Sentinel-2 orbits over Marracuene", "-", "orbits"),
            ("Sentinel-2: all passes", "-", "s2all"),
        ],
        "days": "days", "median": "median", "of": "of", "intervals": "intervals",
        "tl_title": "Passes from {start} to {end} (filled = less than 20% cloud)",
        "orbit": "relative orbit", "not_measured": "not measurable here",
        "f_title": "The January 2026 flood seen by Sentinel-2",
        "f_sub": "Single-day images (not monthly composites). Water = MNDWI > 0, inside the district only, clouds removed",
        "f_before": "23 Oct 2025: no flood", "f_flood": "24 Jan 2026: flood", "f_water": "Detected water",
        "q": "discharge", "cloud": "no data in district", "water_km2": "water in district",
        "f_leg_perm": "Water before (river, lagoons)", "f_leg_new": "New flood water", "f_leg_cloud": "No data (cloud or outside the image)",
        "f_note": ("Discharge peaked on 19 Jan 2026 (2,987 m³/s, GloFAS). Before: Landsat 31.5 km² and Sentinel-2 30.8 km² of water, almost equal.\n"
                   "The flood area is a minimum: clouds cover part of the district. The new water ({new:.0f} km²) matches Sentinel-1 radar (~214 km²)."),
        "z_title": "Marracuene farmland: before, during and after the flood",
        "z_sub": "Single-day scenes, natural colour, same scale and same area as figure 3",
        "z_cols": ["Before", "Flood", "Recession"],
        "z_rows": ["Landsat 8/9\n30 m", "Sentinel-2\n10 m"],
        "z_note": ("The 28 Jan Landsat scene had 65% of the district under cloud; this area stayed visible, but hazy. Sentinel-2 passes every ~2 days\n"
                   "and caught a clearer day (24 Jan). Under closed skies, Sentinel-1 radar remains the main source. Discharge: GloFAS (model)."),
        "o_note": ("Sources: NASA/USGS (Landsat 9: 705 km orbit, 8-day combined revisit); ESA/Copernicus "
                   "\n(Sentinel-2C replaced 2A on 21 Jan 2025; 2A continues in an extended campaign until the end of 2027)."),
    },
}

HALO = [patheffects.withStroke(linewidth=3.5, foreground="black")]
HALO_W = [patheffects.withStroke(linewidth=3, foreground="white")]


def utm(lon, lat):
    return TO_UTM.transform(lon, lat)


def header(fig, title, sub):
    fig.text(0.03, 0.955, title, fontsize=22, fontweight="bold", color=TEAL_DARK, va="top")
    fig.text(0.03, 0.895, sub, fontsize=13, color=GREY, va="top")


def save(fig, lang, name):
    out = OUT / lang
    out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / name, dpi=DPI, facecolor="white")
    plt.close(fig)
    print(f"{lang}/{name:30s} {(out / name).stat().st_size / 1024:6.0f} KB")


def clean(ax):
    ax.set_xticks([]), ax.set_yticks([])
    ax.set_xlabel(""), ax.set_ylabel("")


def scalebar(ax, x, y, km, color="white", halo=HALO):
    """Barra de escala em coordenadas UTM (metros), canto esquerdo em (x, y)."""
    ax.add_patch(Rectangle((x, y), km * 1000, km * 1000 * 0.04, color=color, zorder=10))
    ax.text(x + km * 500, y + km * 1000 * 0.08, f"{km:g} km", color=color, ha="center", va="bottom",
            fontsize=12, fontweight="bold", path_effects=halo, zorder=10)


def north(ax, x, y, size, color="white", halo=HALO):
    ax.add_patch(FancyArrow(x, y, 0, size, width=size * 0.18, head_width=size * 0.45, head_length=size * 0.4,
                            length_includes_head=True, color=color, zorder=10))
    ax.text(x, y + size * 1.1, "N", ha="center", va="bottom", fontsize=14, fontweight="bold", color=color,
            path_effects=halo, zorder=10)


def rgb(file, bounds_utm=None, factor=1, gain=0.18):
    """Cor natural (vermelho, verde, azul) com o mesmo esticamento para os dois satélites."""
    with rasterio.open(file) as src:
        names = list(src.descriptions)
        idx = [names.index(b) + 1 for b in ("red", "green", "blue")]
        if bounds_utm:
            win = from_bounds(*bounds_utm, src.transform).round_offsets().round_lengths()
            raw = src.read(idx, window=win)
            ext = rasterio.windows.bounds(win, src.transform)
        else:
            raw = src.read(idx, out_shape=(3, src.height // factor, src.width // factor), resampling=Resampling.average)
            ext = src.bounds
        bad = raw == src.nodata if src.nodata is not None else np.zeros(raw.shape, bool)
        data = raw.astype("float32") * np.float32(src.scales[0])
    img = np.clip(np.moveaxis(data, 0, 2) / gain, 0, 1) ** 0.85
    alpha = (~bad.any(axis=0)).astype("float32")
    return np.dstack([img, alpha]), (ext[0], ext[2], ext[1], ext[3])


OUTSIDE = "#e9ecea"


def sea_mask():
    """Mar dentro da área das imagens, em graus. Água = MNDWI > 0 no Sentinel-2 de 23 out 2025 (cobre todo
    o rectângulo do lado do mar), ligada à borda leste; o estuário e o canal do rio entram também."""
    from rasterio.warp import Resampling as WR, calculate_default_transform, reproject
    from scipy import ndimage
    with rasterio.open(S2_DRY) as src:
        b = {n: src.read(i + 1).astype("float32") * np.float32(src.scales[i]) for i, n in enumerate(src.descriptions)}
        nodata = src.read(1) == src.nodata
        mndwi = (b["green"] - b["swir1"]) / (b["green"] + b["swir1"] + 1e-6)
        water = (mndwi > 0) & ~nodata
        lab, _ = ndimage.label(water)
        edge = np.unique(lab[:, -1][lab[:, -1] > 0])
        sea = ndimage.binary_closing(np.isin(lab, edge), iterations=2).astype("uint8")
        tr, w, h = calculate_default_transform(src.crs, "EPSG:4326", src.width, src.height, *src.bounds)
        out = np.zeros((h, w), "uint8")
        reproject(sea, out, src_transform=src.transform, src_crs=src.crs, dst_transform=tr, dst_crs="EPSG:4326",
                  resampling=WR.nearest)
    rgba = np.zeros((h, w, 4), "float32")
    rgba[out == 1] = (0.86, 0.92, 0.94, 1)
    ext = (tr.c, tr.c + tr.a * w, tr.f + tr.e * h, tr.f)
    return rgba, ext


# ---------- 1. mapa da área de estudo ----------
def fig_mapa(lang):
    t = T[lang]
    aoi = gpd.read_file(ROOT / "data/raw/aoi/aoi.geojson").to_crs(4326)
    dist = gpd.read_file(ROOT / "data/raw/aoi/marracuene_district.geojson").to_crs(4326)
    basin = gpd.read_file(ROOT / "data/raw/aoi/incomati_basin.geojson").to_crs(4326)
    rivers = gpd.read_file(ROOT / "data/raw/static/hydrography/rivers_incomati.geojson").to_crs(4326)
    world = gpd.read_file(ROOT / ".venv/lib/python3.14/site-packages/pyogrio/tests/fixtures/naturalearth_lowres/naturalearth_lowres.shp")

    fig = plt.figure(figsize=(W, H), dpi=DPI)
    header(fig, t["map_title"], t["map_sub"])
    ax = fig.add_axes([0.03, 0.05, 0.60, 0.80])
    # a costa do Natural Earth (baixa resolução) é grosseira a esta escala: dentro da área das imagens
    # o mar vem do Sentinel-2 (30 m); fora dela o fundo fica neutro (não cartografado)
    ax.set_facecolor(OUTSIDE)
    land = world[world.continent == "Africa"]
    aoi.plot(ax=ax, color="#f4f1e8", lw=0)
    basin.plot(ax=ax, color="#e3eee6", edgecolor="#9db8a6", lw=1, alpha=0.85)
    sea, sea_ext = sea_mask()
    ax.imshow(sea, extent=sea_ext, interpolation="nearest", zorder=1.5)
    rivers.plot(ax=ax, color="#7fb0c0", lw=0.7)
    dist.plot(ax=ax, color=ORANGE, alpha=0.25, edgecolor=ORANGE, lw=2)
    aoi.boundary.plot(ax=ax, color=RED, lw=2.5)
    ax.scatter(*TOWN, s=70, color=INK, zorder=6)
    ax.text(TOWN[0] - 0.02, TOWN[1] + 0.012, t["town"], fontsize=12, fontweight="bold", ha="right", path_effects=HALO_W, zorder=7)
    ax.scatter(*MAPUTO, s=70, color=INK, marker="s", zorder=6)
    ax.text(MAPUTO[0] - 0.018, MAPUTO[1] - 0.006, t["maputo"], fontsize=12, fontweight="bold", ha="right", va="top", path_effects=HALO_W, zorder=7)
    ax.text(32.92, -25.78, t["ocean"], fontsize=13, color="#3f7486", style="italic", ha="center", zorder=3)
    ax.set_xlim(32.25, 33.30)
    ax.set_ylim(-26.10, -25.25)
    ax.set_aspect(1 / np.cos(np.radians(25.7)))
    for lon in np.arange(32.4, 33.31, 0.2):
        ax.axvline(lon, color="white", lw=0.5, zorder=0.5)
    ax.set_xticks(np.arange(32.4, 33.31, 0.2), [f"{v:.1f}° E" for v in np.arange(32.4, 33.31, 0.2)])
    ax.set_yticks(np.arange(-26.0, -25.25, 0.2), [f"{-v:.1f}° S" for v in np.arange(-26.0, -25.25, 0.2)])
    ax.tick_params(labelsize=10, colors=GREY)
    ax.set_xlabel(""), ax.set_ylabel("")
    # barra de escala: 10 km a 25.9 S
    km = 10 / (111.32 * np.cos(np.radians(25.9)))
    ax.plot([32.30, 32.30 + km], [-26.05, -26.05], color=INK, lw=4, solid_capstyle="butt")
    ax.text(32.30 + km / 2, -26.04, "10 km", ha="center", va="bottom", fontsize=11, fontweight="bold")
    ax.annotate("", xy=(33.25, -25.30), xytext=(33.25, -25.38), arrowprops=dict(arrowstyle="-|>", color=INK, lw=2))
    ax.text(33.25, -25.295, "N", ha="center", va="bottom", fontsize=13, fontweight="bold")
    handles = [Line2D([], [], color=RED, lw=2.5, label=t["aoi"]),
               Rectangle((0, 0), 1, 1, facecolor=ORANGE, alpha=0.4, edgecolor=ORANGE, label=t["district"]),
               Rectangle((0, 0), 1, 1, facecolor="#e3eee6", edgecolor="#9db8a6", label=t["basin"]),
               Line2D([], [], color="#7fb0c0", lw=1.5, label=t["river"]),
               Rectangle((0, 0), 1, 1, facecolor=OUTSIDE, edgecolor="#c9cfcb", label=t["outside"])]
    ax.legend(handles=handles, loc="upper left", fontsize=11, frameon=True, framealpha=0.95)

    # localização em Moçambique
    ins = fig.add_axes([0.66, 0.10, 0.31, 0.74])
    ins.set_facecolor("#dcebf0")
    land.plot(ax=ins, color="#f4f1e8", edgecolor="#b6aa92", lw=0.8)
    world[world.name == "Mozambique"].plot(ax=ins, color="#cfe3d6", edgecolor=TEAL, lw=1.2)
    basin.plot(ax=ins, color=FOAM, alpha=0.5, lw=0)
    x0, y0, x1, y1 = aoi.total_bounds
    ins.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor=RED, lw=2.5))
    ins.set_xlim(28.5, 41.5)
    ins.set_ylim(-27.5, -10)
    ins.set_aspect(1 / np.cos(np.radians(19)))
    clean(ins)
    ins.set_title(t["inset"], fontsize=14, fontweight="bold", color=TEAL_DARK)
    ins.text(36.5, -16.5, t["moz"], fontsize=13, fontweight="bold", color=TEAL_DARK, ha="center")
    ins.text(29.8, -26.3, t["sa"], fontsize=10, color=GREY, ha="center")
    ins.text(33.5, -23.0, t["basin"], fontsize=9.5, color=TEAL, ha="left", path_effects=HALO_W)
    ins.annotate("", xy=(32.4, -25.9), xytext=(33.4, -23.3), arrowprops=dict(arrowstyle="-", color=TEAL, lw=0.8))
    save(fig, lang, "1_mapa_area_de_estudo.png")


# ---------- 2. cor natural com legendas ----------
def fig_cor_natural(lang):
    t = T[lang]
    img, ext = rgb(S2_DRY)
    dist = gpd.read_file(ROOT / "data/raw/aoi/marracuene_district.geojson").to_crs(UTM)
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    header(fig, t["nat_title"], t["nat_sub"])
    ax = fig.add_axes([0.0, 0.02, 1.0, 0.85])
    ax.imshow(img, extent=ext)
    dist.boundary.plot(ax=ax, color="white", lw=1.2, ls="--", alpha=0.8)
    ax.set_xlim(ext[0] - 22000, ext[1] + 2000)
    ax.set_ylim(ext[2], ext[3])
    ax.axis("off")

    def label(lon, lat, text, tlon, tlat, color="white"):
        x, y = utm(lon, lat)
        tx, ty = utm(tlon, tlat)
        ax.annotate(text, (x, y), (tx, ty), fontsize=15, fontweight="bold", color=color, ha="center", va="center",
                    path_effects=HALO, arrowprops=dict(arrowstyle="-|>", color="white", lw=1.8,
                                                       path_effects=[patheffects.withStroke(linewidth=3.5, foreground="black")]))

    label(32.690, -25.665, t["lab_river"], 32.575, -25.640)
    label(32.735, -25.610, t["lab_plain"], 32.860, -25.660)
    label(32.790, -25.495, t["lab_fields"], 32.640, -25.470)
    label(*TOWN, t["lab_town"], 32.575, -25.760)
    label(32.845, -25.560, t["lab_dunes"], 32.985, -25.620)
    label(32.590, -25.835, t["lab_urban"], 32.460, -25.875)
    x0, y0 = utm(FIELDS[0], FIELDS[1])
    x1, y1 = utm(FIELDS[2], FIELDS[3])
    ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, edgecolor="#ffd166", lw=2.5))
    ax.text(x1 + 600, y1, t["lab_box"], color="#ffd166", fontsize=12, fontweight="bold", va="top", path_effects=HALO)
    sx, sy = utm(32.86, -25.90)
    scalebar(ax, sx, sy, 10, color=INK, halo=HALO_W)
    nx, ny = utm(33.00, -25.76)
    north(ax, nx, ny, 3500, color=INK, halo=HALO_W)
    save(fig, lang, "2_cor_natural_legendas.png")


# ---------- 3. Landsat vs Sentinel-2 ----------
def fig_par(lang):
    t = T[lang]
    x0, y0 = utm(FIELDS[0], FIELDS[1])
    x1, y1 = utm(FIELDS[2], FIELDS[3])
    box = (x0, y0, x1, y1)
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    header(fig, t["pair_title"], t["pair_sub"])
    for i, (file, lab) in enumerate([(LS_DRY, t["landsat"]), (S2_DRY_FIELDS, t["s2"])]):
        img, ext = rgb(file, bounds_utm=box)
        ax = fig.add_axes([0.03 + i * 0.49, 0.10, 0.45, 0.72])
        ax.imshow(img, extent=ext, interpolation="nearest")
        ax.set_xlim(x0, x1)
        ax.set_ylim(y0, y1)
        clean(ax)
        ax.set_title(lab, fontsize=17, fontweight="bold", color=TEAL_DARK, pad=10)
        scalebar(ax, x0 + 250, y0 + 250, 1)
    fig.text(0.03, 0.035, t["pair_note"], fontsize=13, color=INK)
    save(fig, lang, "3_landsat_vs_sentinel2.png")


# ---------- 4. larguras ----------
def fig_larguras(lang):
    t = T[lang]
    d = pd.read_csv(ROOT / "data/interim/water_quality/largura_por_troco.csv")
    rows = []
    for _, r in d.iterrows():
        name = r.nome.split(" ", 1)[1]
        if r.troco == "Q9":
            name = name.replace("foz / estuário", "foz / estuário" if lang == "pt" else "mouth / estuary")
        if lang == "en":
            name = name.replace("fronteira", "border").replace(" a ", " to ")
        has_w = pd.notna(r.largura_media_m)
        rows.append([r.troco, name,
                     f"{r.comprimento_km:.1f}" if has_w else "-",
                     f"{r.area_agua_permanente_ha:,.0f}".replace(",", " " if lang == "pt" else ","),
                     f"{r.largura_media_m:.0f}" if has_w else t["estuary"],
                     f"{r.largura_media_m / 30:.1f}" if has_w else "-",
                     f"{r.largura_media_m / 10:.1f}" if has_w else "-",
                     t["yes"] if r.landsat_utilizavel else t["no"]])
    if lang == "pt":
        rows = [[c.replace(".", ",") if j in (2, 5, 6) else c for j, c in enumerate(row)] for row in rows]
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    header(fig, t["w_title"], t["w_sub"])
    ax = fig.add_axes([0.03, 0.15, 0.94, 0.70])
    ax.axis("off")
    tab = ax.table(cellText=rows, colLabels=t["w_cols"], loc="upper center", cellLoc="center",
                   colWidths=[0.07, 0.24, 0.08, 0.11, 0.11, 0.10, 0.11, 0.10])
    tab.auto_set_font_size(False)
    tab.set_fontsize(13)
    tab.scale(1, 2.55)
    for (r, c), cell in tab.get_celld().items():
        cell.set_edgecolor("#d8e2df")
        if r == 0:
            cell.set_facecolor(TEAL_DARK)
            cell.set_text_props(color="white", fontweight="bold", fontsize=12)
            cell.set_height(cell.get_height() * 1.5)
        else:
            row = d.iloc[r - 1]
            cell.set_facecolor("#fff4e6" if row.troco in ("Q8", "Q9") else ("#f4f8f7" if r % 2 else "white"))
            if c == 1:
                cell.set_text_props(ha="left")
                cell._loc = "left"
            if c == 5 and pd.notna(row.largura_media_m) and row.largura_media_m / 30 < 3:
                cell.set_text_props(color=RED, fontweight="bold")
            if c in (0, 4):
                cell.set_text_props(fontweight="bold")
    fig.text(0.03, 0.27, t["w_note"], fontsize=11.5, color=GREY, va="top", linespacing=1.5)
    save(fig, lang, "4_larguras_do_rio.png")


# ---------- 5. órbitas e revisitas ----------
def fetch_passes():
    import sys
    sys.path.insert(0, str(ROOT / "src"))
    import ee
    from ete.config import load_config
    from ete.gee import init
    init(load_config())
    pt = ee.Geometry.Point(*POINT)
    rows = []
    for cid, sat, cloud, orbit in [("LANDSAT/LC08/C02/T1_L2", "SPACECRAFT_ID", "CLOUD_COVER", "WRS_PATH"),
                                   ("LANDSAT/LC09/C02/T1_L2", "SPACECRAFT_ID", "CLOUD_COVER", "WRS_PATH"),
                                   ("COPERNICUS/S2_HARMONIZED", "SPACECRAFT_NAME", "CLOUDY_PIXEL_PERCENTAGE", "SENSING_ORBIT_NUMBER")]:
        col = ee.ImageCollection(cid).filterBounds(pt).filterDate("2025-01-01", pd.Timestamp.now().strftime("%Y-%m-%d"))
        for ms, s, c, o in col.reduceColumns(ee.Reducer.toList(4), ["system:time_start", sat, cloud, orbit]).get("list").getInfo():
            rows.append((pd.to_datetime(ms, unit="ms"), s, c, o))
    df = pd.DataFrame(rows, columns=["hora_utc", "satelite", "nuvens_pct", "orbita"])
    df["data"] = df.hora_utc.dt.date
    df = df.drop_duplicates(["satelite", "data", "orbita"]).sort_values("hora_utc")
    df.to_csv(PASSES, index=False)


def gaps(times):
    days = pd.Series(sorted(set(pd.to_datetime(times).dt.normalize()))).diff().dt.days.dropna()
    return days


def measured(df, lang):
    t = T[lang]
    out = {}

    def fmt(days, nominal):
        hit = int((days == nominal).sum())
        return f"{days.median():.0f} {t['days']} ({t['median']}; {hit} {t['of']} {len(days)} {t['intervals']})"

    ls = df[df.satelite.str.startswith("LANDSAT")]
    s2 = df[df.satelite.str.startswith("Sentinel")]
    out["l8"] = fmt(gaps(ls[ls.satelite == "LANDSAT_8"].hora_utc), 16)
    out["l9"] = fmt(gaps(ls[ls.satelite == "LANDSAT_9"].hora_utc), 16)
    out["l89"] = fmt(gaps(ls.hora_utc), 8)
    out["-"] = t["not_measured"]
    one = pd.concat([gaps(s2[(s2.satelite == s) & (s2.orbita == o)].hora_utc)
                     for s in ("Sentinel-2B", "Sentinel-2C") for o in (49, 92)])
    out["s2one"] = fmt(one, 10)
    pair = pd.concat([gaps(s2[s2.satelite.isin(["Sentinel-2B", "Sentinel-2C"]) & (s2.orbita == o)].hora_utc) for o in (49, 92)])
    out["s2pair"] = fmt(pair, 5)
    a = pd.concat([gaps(s2[(s2.satelite == "Sentinel-2A") & (s2.orbita == o) & (s2.hora_utc >= "2025-03-01")].hora_utc) for o in (49, 92)])
    out["s2a"] = fmt(a, 20)
    out["orbits"] = "49 + 92" + (" (2 órbitas)" if lang == "pt" else " (2 orbits)")
    al = gaps(s2.hora_utc)
    out["s2all"] = f"{al.median():.0f} {t['days']} ({t['median']}; " + (
        f"intervalo de 1 a {al.max():.0f} dias)" if lang == "pt" else f"range 1 to {al.max():.0f} days)")
    return out


def fig_orbitas(lang):
    t = T[lang]
    if not PASSES.exists():
        fetch_passes()
    df = pd.read_csv(PASSES, parse_dates=["hora_utc"])
    m = measured(df, lang)
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    first, last = df.hora_utc.min(), df.hora_utc.max()
    names = (["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"] if lang == "pt"
             else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    period = (f"{names[first.month - 1]} {first.year} a {last.day} {names[last.month - 1]} {last.year}" if lang == "pt"
              else f"{names[first.month - 1]} {first.year} to {last.day} {names[last.month - 1]} {last.year}")
    header(fig, t["o_title"], t["o_sub"].format(period=period))

    ax = fig.add_axes([0.03, 0.40, 0.94, 0.47])
    ax.axis("off")
    rows = [[name, off, m[key]] for name, off, key in t["o_rows"]]
    tab = ax.table(cellText=rows, colLabels=t["o_cols"], loc="upper center", cellLoc="left", colWidths=[0.30, 0.13, 0.50])
    tab.auto_set_font_size(False)
    tab.set_fontsize(12.5)
    tab.scale(1, 1.75)
    for (r, c), cell in tab.get_celld().items():
        cell.set_edgecolor("#d8e2df")
        if r == 0:
            cell.set_facecolor(TEAL_DARK)
            cell.set_text_props(color="white", fontweight="bold")
        else:
            cell.set_facecolor("#f4f8f7" if r % 2 else "white")
            if c == 1:
                cell.set_text_props(fontweight="bold")

    # linha do tempo mai-ago 2026
    tl = fig.add_axes([0.16, 0.12, 0.81, 0.25])
    tl_end = last.normalize() + pd.Timedelta(days=2)
    tl_start = tl_end - pd.Timedelta(days=120)          # os últimos 4 meses com dados
    sel = df[(df.hora_utc >= tl_start) & (df.hora_utc < tl_end)]
    lanes = [("LANDSAT_8", "Landsat 8"), ("LANDSAT_9", "Landsat 9"), ("Sentinel-2A", "Sentinel-2A"),
             ("Sentinel-2B", "Sentinel-2B"), ("Sentinel-2C", "Sentinel-2C")]
    colors = {"LANDSAT_8": "#3d6fb6", "LANDSAT_9": "#5b8fd6", "Sentinel-2A": "#9aa9a5", "Sentinel-2B": TEAL, "Sentinel-2C": FOAM}
    for y, (sat, lab) in enumerate(lanes[::-1]):
        s = sel[sel.satelite == sat]
        for _, r in s.iterrows():
            clear = r.nuvens_pct < 20
            mk = "o" if not str(sat).startswith("Sentinel") or r.orbita == 49 else "D"
            tl.scatter(r.hora_utc, y, s=70, marker=mk, color=colors[sat] if clear else "white",
                       edgecolor=colors[sat], lw=1.6, zorder=3)
        tl.text(tl_start - pd.Timedelta(days=3), y, lab, ha="right", va="center", fontsize=12, fontweight="bold", color=colors[sat])
        tl.axhline(y, color="#e6ecea", lw=1, zorder=1)
    tl.set_yticks([])
    tl.set_ylim(-0.7, len(lanes) - 0.3)
    tl.set_xlim(tl_start, tl_end)
    months = pd.date_range(tl_start, tl_end, freq="MS")
    tl.set_xticks(months, [f"1 {names[m.month - 1]}" for m in months])
    for mth in months:
        tl.axvline(mth, color="#d8e2df", lw=1)
    for s in ("top", "right", "left"):
        tl.spines[s].set_visible(False)
    tl.tick_params(labelsize=12)
    tl.set_title(t["tl_title"].format(start=f"{tl_start.day} {names[tl_start.month - 1]}", end=f"{last.day} {names[last.month - 1]} {last.year}") + ("   ● " + t["orbit"] + " 49   ◆ " + t["orbit"] + " 92"), fontsize=12.5, color=INK, loc="left")
    fig.text(0.03, 0.015, t["o_note"], fontsize=10.5, color=GREY, linespacing=1.4)
    save(fig, lang, "5_orbitas_e_revisitas.png")


# ---------- 6 e 7. cenas de um só dia: antes e durante a cheia de 2026 ----------
SCENES = ROOT / "data/raw/optical/cenas_cheia_2026"


def discharge(day):
    q = pd.read_csv(ROOT / "data/processed/series/hydromet_daily.csv", parse_dates=["date"],
                    usecols=["date", "discharge_m3s"]).set_index("date")["discharge_m3s"]
    return float(q.loc[day])


def scene_water(file, district_mask):
    """Água (MNDWI > 0), nuvens e máscara do distrito numa cena de 30 m."""
    with rasterio.open(file) as src:
        b = {n: src.read(i + 1).astype("float32") * np.float32(src.scales[i]) for i, n in enumerate(src.descriptions)}
        nodata = src.read(1) == src.nodata
    mndwi = (b["green"] - b["swir1"]) / (b["green"] + b["swir1"] + 1e-6)
    cloud = (b["nuvem"] > 0) | nodata
    return (mndwi > 0) & ~cloud & district_mask, cloud & district_mask


def num(v, lang, fmt=None):
    text = (fmt or ("{:,.1f}" if v < 10 else "{:,.0f}")).format(v)
    return text.replace(",", " ").replace(".", ",") if lang == "pt" else text


def fig_cheia(lang):
    t = T[lang]
    before, flood = SCENES / "sentinel2_antes_2025-10-23_30m.tif", SCENES / "sentinel2_cheia_2026-01-24_30m.tif"
    dist = gpd.read_file(ROOT / "data/raw/aoi/marracuene_district.geojson").to_crs(UTM)
    with rasterio.open(before) as src:
        from rasterio.features import geometry_mask
        inside = geometry_mask(dist.geometry, (src.height, src.width), src.transform, invert=True)
    w0, c0 = scene_water(before, inside)
    w1, c1 = scene_water(flood, inside)
    px = 900 / 1e6
    new = w1 & ~w0 & ~c0
    left, bottom, right, top = dist.total_bounds
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    header(fig, t["f_title"], t["f_sub"])
    panels = [(before, t["f_before"], "2025-10-23", w0, c0), (flood, t["f_flood"], "2026-01-24", w1, c1)]
    for i, (file, title, day, w, c) in enumerate(panels):
        img, ext = rgb(file)
        ax = fig.add_axes([0.02 + i * 0.325, 0.20, 0.31, 0.62])
        ax.imshow(img, extent=ext)
        dist.boundary.plot(ax=ax, color="white", lw=1.2, ls="--")
        ax.set_xlim(left - 1500, right + 1500), ax.set_ylim(bottom - 1500, top + 1500)
        clean(ax)
        ax.set_title(title, fontsize=16, fontweight="bold", color=TEAL_DARK, pad=8)
        info = (f"{t['q']}: {num(discharge(day), lang)} m³/s\n{t['cloud']}: {num(c.sum() / inside.sum() * 100, lang)}%\n"
                f"{t['water_km2']}: {'≥ ' if c.sum() / inside.sum() > 0.05 else ''}{num(w.sum() * px, lang)} km²")
        ax.text(0.03, 0.03, info, transform=ax.transAxes, fontsize=12, color="white", fontweight="bold",
                va="bottom", linespacing=1.5, path_effects=HALO)
    with rasterio.open(flood) as src:
        ext = (src.bounds.left, src.bounds.right, src.bounds.bottom, src.bounds.top)
    m = np.zeros(w1.shape + (4,), "float32")
    m[inside] = (0.93, 0.92, 0.88, 1)
    m[c1 | c0] = (0.78, 0.78, 0.80, 1)
    m[w0] = (0.03, 0.18, 0.40, 1)
    m[new] = (0.17, 0.71, 0.63, 1)
    ax = fig.add_axes([0.67, 0.20, 0.31, 0.62])
    ax.imshow(m, extent=ext, interpolation="nearest")
    dist.boundary.plot(ax=ax, color=INK, lw=1)
    ax.set_xlim(left - 1500, right + 1500), ax.set_ylim(bottom - 1500, top + 1500)
    clean(ax)
    ax.set_title(t["f_water"], fontsize=16, fontweight="bold", color=TEAL_DARK, pad=8)
    handles = [Rectangle((0, 0), 1, 1, color=c, label=l) for c, l in
               [((0.03, 0.18, 0.40), t["f_leg_perm"]), ((0.17, 0.71, 0.63), t["f_leg_new"]), ((0.78, 0.78, 0.80), t["f_leg_cloud"])]]
    ax.legend(handles=handles, loc="lower left", fontsize=11, frameon=True, framealpha=0.95)
    sx, sy = left + 500, top - 3500
    scalebar(ax, sx, sy, 10, color=INK, halo=HALO_W)
    fig.text(0.03, 0.15, t["f_note"].format(new=new.sum() * px), fontsize=12,
             color=INK, va="top", linespacing=1.6)
    save(fig, lang, "6_antes_e_cheia_2026.png")


def fig_zona_cheia(lang):
    t = T[lang]
    x0, y0 = utm(FIELDS[0], FIELDS[1])
    x1, y1 = utm(FIELDS[2], FIELDS[3])
    box = (x0, y0, x1, y1)
    grid = [  # (linha, coluna, ficheiro, data, satélite)
        (0, 0, "landsat_antes_2025-09-22_30m.tif", "2025-09-22", "Landsat 9"),
        (0, 1, "landsat_depois_2026-01-28_30m.tif", "2026-01-28", "Landsat 8"),
        (0, 2, "landsat_recuo_2026-02-13_30m.tif", "2026-02-13", "Landsat 8"),
        (1, 0, "sentinel2_antes_2025-10-23_zona_agricola_10m.tif", "2025-10-23", "Sentinel-2A"),
        (1, 1, "sentinel2_cheia_2026-01-24_zona_agricola_10m.tif", "2026-01-24", "Sentinel-2B"),
        (1, 2, "sentinel2_recuo_2026-02-08_zona_agricola_10m.tif", "2026-02-08", "Sentinel-2C"),
    ]
    months = (["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"] if lang == "pt"
              else ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"])
    fig = plt.figure(figsize=(W, H), dpi=DPI)
    header(fig, t["z_title"], t["z_sub"])
    size, gap, x_start = 0.235, 0.012, 0.21
    for c, name in enumerate(t["z_cols"]):
        fig.text(x_start + c * (size + gap) + size / 2, 0.83, name, ha="center", fontsize=17, fontweight="bold", color=TEAL_DARK)
    for r, name in enumerate(t["z_rows"]):
        fig.text(0.19, 0.475 - r * 0.36 + 0.167, name, ha="right", va="center", fontsize=15, fontweight="bold", color=TEAL_DARK)
    for r, c, fname, day, sat in grid:
        img, ext = rgb(SCENES / fname, bounds_utm=box)
        ax = fig.add_axes([x_start + c * (size + gap), 0.475 - r * 0.36, size, 0.335])
        ax.imshow(img, extent=ext, interpolation="nearest")
        ax.set_xlim(x0, x1), ax.set_ylim(y0, y1)
        ax.set_aspect("equal")
        clean(ax)
        d = pd.Timestamp(day)
        label = f"{sat} · {d.day} {months[d.month - 1]} {d.year} · {num(discharge(day), lang)} m³/s"
        ax.text(0.02, 0.02, label, transform=ax.transAxes, fontsize=10.5, color="white", fontweight="bold", path_effects=HALO)
        if r == 1 and c == 0:
            scalebar(ax, x0 + 250, y1 - 600, 1)
    fig.text(0.03, 0.065, t["z_note"], fontsize=11.5, color=INK, va="top", linespacing=1.5)
    save(fig, lang, "7_zona_agricola_cheia.png")


def write_pdf(lang):
    """As figuras de uma língua num só PDF, para enviar de uma vez."""
    from PIL import Image
    pages = [Image.open(f).convert("RGB") for f in sorted((OUT / lang).glob("*.png"))]
    out = OUT / f"ETE_figuras_apresentacao_{lang}.pdf"
    pages[0].save(out, save_all=True, append_images=pages[1:], resolution=DPI)
    print(f"{out.name:36s} {out.stat().st_size / 1024:6.0f} KB ({len(pages)} páginas)")


if __name__ == "__main__":
    for lang in ("pt", "en"):
        fig_mapa(lang)
        fig_cor_natural(lang)
        fig_par(lang)
        fig_larguras(lang)
        fig_orbitas(lang)
        fig_cheia(lang)
        fig_zona_cheia(lang)
        write_pdf(lang)
