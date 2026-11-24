"""Mapas para imprimir em A3 (tarefas W4-09 e B-03): zonas de aviso com os nomes dos lugares,
e suscetibilidade a cheias.

    .venv/bin/python scripts/build_print_maps.py

Sem internet: usa só as camadas do projecto (não há imagem de fundo). Escreve PDF e PNG em
reports/mapas_para_impressao/. São rascunhos técnicos correctos; o arranjo gráfico final
(logótipo, cores da identidade visual) é da equipa de comunicação.
"""

import sys
from pathlib import Path

import geopandas as gpd
import matplotlib

matplotlib.use("Agg")
import matplotlib.patches as mpatches  # noqa: E402
import matplotlib.patheffects  # noqa: E402,F401
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ete import config  # noqa: E402
from ete.grid import load_aoi, load_grid  # noqa: E402
from ete.rasters import read_bands  # noqa: E402

cfg = config.load_config()
grid = load_grid(cfg)
name = cfg["project"]["aoi_name"]
out = config.path(cfg, "reports", "mapas_para_impressao")
A3 = (16.54, 11.69)                                    # inches, landscape
west, south, east, north = grid.bounds
extent = [west, east, south, north]
district = load_aoi(cfg, "district").to_crs(grid.crs)
zones = gpd.read_file(config.path(cfg, "maps", "zonas_de_aviso", f"zonas_de_aviso_{name}.gpkg", mkdir=False))
places = gpd.read_file(config.path(cfg, "maps", "zonas_de_aviso", f"lugares_{name}.gpkg", mkdir=False))
roads = gpd.read_file(config.path(cfg, "osm", f"osm_roads_{name}.gpkg", mkdir=False)).to_crs(grid.crs)
main_roads = roads[roads["highway"].astype(str).str.contains("motorway|trunk|primary|secondary")] if "highway" in roads else roads.iloc[:0]
susceptibility = read_bands(config.path(cfg, "maps", "modelo_a", f"suscetibilidade_{name}_30m.tif", mkdir=False), ["classe"])["classe"]
water = np.where(susceptibility == 0, 1.0, np.nan)
DISCLAIMER = "Produto experimental do projecto Eyes to Earth. Não substitui os avisos oficiais do INGD, do INAM e da ARA-Sul."


def frame(title: str, subtitle: str):
    fig, ax = plt.subplots(figsize=A3)
    ax.set_facecolor("#f7f5ef")
    ax.imshow(water, extent=extent, cmap=matplotlib.colors.ListedColormap(["#7fb3d5"]), interpolation="nearest", zorder=2)
    if len(main_roads):
        main_roads.plot(ax=ax, color="#8d8d8d", linewidth=0.7, zorder=3)
    district.boundary.plot(ax=ax, color="black", linewidth=1.4, zorder=6)
    bounds = district.total_bounds
    pad = 2500
    ax.set_xlim(bounds[0] - pad, bounds[2] + pad), ax.set_ylim(bounds[1] - pad, bounds[3] + pad)
    ax.set_xticks([]), ax.set_yticks([]), ax.set_xlabel(""), ax.set_ylabel("")
    ax.set_title(title, fontsize=22, fontweight="bold", loc="left", pad=28)
    ax.text(0, 1.012, subtitle, transform=ax.transAxes, fontsize=12)
    # scale bar (the map is in metres) and north arrow
    x0, y0 = bounds[0] - pad + 1500, bounds[1] - pad + 1500
    ax.plot([x0, x0 + 5000], [y0, y0], color="black", linewidth=4, solid_capstyle="butt", zorder=9)
    ax.text(x0 + 2500, y0 + 500, "5 km", ha="center", fontsize=11, zorder=9)
    ax.annotate("N", xy=(0.975, 0.96), xytext=(0.975, 0.90), xycoords="axes fraction", ha="center", fontsize=14, fontweight="bold",
                arrowprops=dict(arrowstyle="-|>", color="black", lw=2))
    fig.text(0.012, 0.012, DISCLAIMER + "  Dados: Copernicus EMS (EMSR857), Copernicus/ESA, USGS, OpenStreetMap, GeoNames.", fontsize=8.5)
    return fig, ax


def save(fig, stem: str) -> None:
    fig.tight_layout(rect=(0, 0.02, 1, 1))
    fig.savefig(out / f"{stem}.pdf")
    fig.savefig(out / f"{stem}.png", dpi=130)
    plt.close(fig)
    print("escrito", out / f"{stem}.pdf")


# 1. warning zones with place names
fig, ax = frame("Onde a água chega primeiro: rio Incomáti, Marracuene", "Zonas de aviso feitas a partir da cheia de janeiro de 2026 (mapas do Copernicus EMS). Os nomes ainda não foram validados no terreno.")
colours = {1: "#c0392b", 2: "#e67e22"}
for value, colour in colours.items():
    zones[zones["zona"] == value].plot(ax=ax, color=colour, alpha=0.75, zorder=4)
styles = {"alaga primeiro": ("#7b241c", 60), "alaga em cheia grande": ("#af601a", 45), "na margem da cheia": ("#566573", 22)}
inside = places[places.within(district.union_all().buffer(1000))]
for category, (colour, size) in styles.items():
    part = inside[inside["categoria"] == category]
    part.plot(ax=ax, color=colour, markersize=size, edgecolor="white", linewidth=0.6, zorder=7)
    if category != "na margem da cheia":
        for _, row in part.iterrows():
            ax.annotate(row["lugar"], (row.geometry.x, row.geometry.y), xytext=(5, 4), textcoords="offset points", fontsize=9.5, fontweight="bold", zorder=8,
                        path_effects=[matplotlib.patheffects.withStroke(linewidth=2.5, foreground="white")])
ax.legend(handles=[mpatches.Patch(color=colours[1], alpha=0.75, label="Zona 1: as primeiras a alagar (laranja e vermelho)"),
                   mpatches.Patch(color=colours[2], alpha=0.75, label="Zona 2: cheia grande (vermelho)"),
                   mpatches.Patch(color="#7fb3d5", label="Rio e água permanente"),
                   plt.Line2D([], [], marker="o", color="w", markerfacecolor="#7b241c", markersize=10, label="Lugar que alaga primeiro"),
                   plt.Line2D([], [], marker="o", color="w", markerfacecolor="#af601a", markersize=9, label="Lugar atingido em cheia grande"),
                   plt.Line2D([], [], color="#8d8d8d", label="Estradas principais"), plt.Line2D([], [], color="black", label="Limite do distrito")],
          loc="lower right", fontsize=11, framealpha=0.95, title="Legenda", title_fontsize=12)
save(fig, "mapa_zonas_de_aviso_A3")

# 2. susceptibility
import matplotlib.patheffects  # noqa: E402,F401

fig, ax = frame("Suscetibilidade a cheias: distrito de Marracuene", "Onde o terreno favorece a acumulação de água (Modelo A, 20 anos de dados). Para avisar a população usam-se as zonas de aviso.")
classes = {1: ("baixa", "#ffffb2"), 2: ("média", "#fecc5c"), 3: ("alta", "#fd8d3c"), 4: ("muito alta", "#e31a1c")}
inside_district = ~np.isnan(susceptibility)
shown = np.where(inside_district & (susceptibility > 0), susceptibility, np.nan)
ax.imshow(shown, extent=extent, cmap=matplotlib.colors.ListedColormap([c for _, c in classes.values()]), vmin=0.5, vmax=4.5, interpolation="nearest", zorder=1, alpha=0.9)
ax.legend(handles=[mpatches.Patch(color=c, label=f"Suscetibilidade {n}") for n, c in classes.values()] + [mpatches.Patch(color="#7fb3d5", label="Rio e água permanente"),
                   plt.Line2D([], [], color="black", label="Limite do distrito")], loc="lower right", fontsize=11, framealpha=0.95, title="Legenda", title_fontsize=12)
save(fig, "mapa_suscetibilidade_A3")
