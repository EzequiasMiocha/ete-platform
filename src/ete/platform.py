"""Data package for the platform (week 4): everything the web application shows, small and web-ready.

The application must not need the 43 GB of project data, Earth Engine or the trained models. This
module writes a folder of a few MB with:
  * maps as coloured PNG images with their corner coordinates (to lay over a web map), and
    vector layers as GeoJSON, all in latitude/longitude (EPSG:4326)
  * the latest bulletin and its tables
  * the time series behind the charts
  * `catalogo.json`: one entry per layer with its title, legend, date and limits, so the
    application can build its menus and legends without hard-coding anything

`export_package` rebuilds the whole folder; `refresh_daily` only rewrites what changes every day.
"""

from __future__ import annotations

import json
import shutil
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import __version__
from .config import path
from .grid import load_aoi, load_grid

SUSCEPTIBILITY = {0: ("água permanente", "#2e86c1"), 1: ("baixa", "#ffffb2"), 2: ("média", "#fecc5c"), 3: ("alta", "#fd8d3c"), 4: ("muito alta", "#e31a1c")}
WATER = {1: ("água habitual", "#2e86c1"), 2: ("cheia (água fora do habitual)", "#c0392b")}
ZONE_COLOURS = {1: "#c0392b", 2: "#e67e22"}
ALERT_COLOURS = {"verde": "#27ae60", "amarelo": "#f1c40f", "laranja": "#e67e22", "vermelho": "#c0392b"}
TURBIDITY_COLOURS = {"normal": "#5dade2", "elevada": "#b9770e", "muito elevada": "#6e2c00", "sem medição recente": "#bdc3c7"}
WATER_MAP_MONTHS = 12
DISCLAIMER = ("Produto experimental do projeto Eyes to Earth. Não substitui os avisos oficiais do INGD, do INAM e da ARA-Sul.")


def _rgba(hex_colour: str, alpha: int) -> tuple[int, int, int, int]:
    h = hex_colour.lstrip("#")
    return int(h[0:2], 16), int(h[2:4], 16), int(h[4:6], 16), alpha


def write_overlay(classes: np.ndarray, grid, colours: dict, file, step_deg: float, alpha: int = 200) -> list[list[float]]:
    """Write a class raster as a transparent PNG in latitude/longitude and return its corners
    [[south, west], [north, east]], the form web map libraries expect for an image overlay."""
    from PIL import Image
    from rasterio.transform import from_origin
    from rasterio.warp import Resampling, reproject, transform_bounds

    west, south, east, north = transform_bounds(grid.crs, "EPSG:4326", *grid.bounds)
    width, height = int(np.ceil((east - west) / step_deg)), int(np.ceil((north - south) / step_deg))
    out = np.zeros((height, width), "uint8")
    source = np.where(np.isfinite(classes), classes + 1, 0).astype("uint8")           # 0 = nothing to draw
    reproject(source, out, src_transform=grid.transform, src_crs=grid.crs, dst_transform=from_origin(west, north, step_deg, step_deg),
              dst_crs="EPSG:4326", resampling=Resampling.nearest, src_nodata=0, dst_nodata=0)
    image = np.zeros((height, width, 4), "uint8")
    for value, (_, colour) in colours.items():
        image[out == value + 1] = _rgba(colour, alpha)
    Image.fromarray(image, "RGBA").save(file, optimize=True)
    return [[round(north - height * step_deg, 6), round(west, 6)], [round(north, 6), round(west + width * step_deg, 6)]]


def _legend(colours: dict) -> list[dict]:
    return [{"valor": int(k), "nome": name, "cor": colour} for k, (name, colour) in colours.items()]


def _geojson(frame, file, tolerance_m: float = 0.0, decimals: int = 5) -> None:
    import shapely

    if tolerance_m:
        frame = frame.assign(geometry=frame.geometry.simplify(tolerance_m))
    frame = frame.to_crs(4326)
    frame = frame.assign(geometry=shapely.set_precision(frame.geometry.values, 10.0 ** -decimals))
    file.unlink(missing_ok=True)
    frame.to_file(file, driver="GeoJSON")


# ----------------------------------------------------------------------------- light static maps
def _figure(width: float = 6.4, height: float = 7.2):
    import matplotlib

    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, ax = plt.subplots(figsize=(width, height))
    ax.set_facecolor("#f7f5ef")
    ax.set_xticks([]), ax.set_yticks([])
    for side in ax.spines.values():
        side.set_color("#d5d8dc")
    return fig, ax, plt


def _save_light(fig, plt, file) -> None:
    fig.tight_layout(pad=0.4)
    fig.savefig(file, dpi=85)
    plt.close(fig)
    from PIL import Image

    Image.open(file).convert("P", palette=Image.ADAPTIVE, colors=64).save(file, optimize=True)        # a few tens of KB


def _light_zone_map(cfg: dict, zones, places, water, grid, file) -> None:
    """Small picture of the warning zones with the names of the places, for phones on little data."""
    import matplotlib.colors as mcolors
    import matplotlib.patheffects as effects

    fig, ax, plt = _figure()
    district = load_aoi(cfg, "district").to_crs(grid.crs)
    west, south, east, north = grid.bounds
    ax.imshow(water, extent=[west, east, south, north], cmap=mcolors.ListedColormap(["#7fb3d5"]), interpolation="nearest", zorder=2)
    for value, colour in ZONE_COLOURS.items():
        zones[zones["zona"] == value].plot(ax=ax, color=colour, alpha=0.75, zorder=3)
    district.boundary.plot(ax=ax, color="black", linewidth=1.1, zorder=5)
    inside = places[places.within(district.union_all().buffer(1000)) & places["categoria"].isin(["alaga primeiro", "alaga em cheia grande"])]
    inside = inside.sort_values("parte_alagada", ascending=False).head(16)
    inside.plot(ax=ax, color="#1c2833", markersize=14, zorder=6)
    for _, row in inside.iterrows():
        ax.annotate(row["lugar"], (row.geometry.x, row.geometry.y), xytext=(4, 3), textcoords="offset points", fontsize=7.5, zorder=7,
                    path_effects=[effects.withStroke(linewidth=2, foreground="white")])
    bounds = district.total_bounds
    ax.set_xlim(bounds[0] - 2000, bounds[2] + 2000), ax.set_ylim(bounds[1] - 2000, bounds[3] + 2000)
    ax.set_xlabel(""), ax.set_ylabel("")
    _save_light(fig, plt, file)


def _light_quality_map(cfg: dict, water, file) -> None:
    """Small picture of the river from the border to the mouth, each section in the colour of its state."""
    import matplotlib.patheffects as effects

    fig, ax, plt = _figure(7.0, 5.2)
    load_aoi(cfg, "district").to_crs(water.crs).boundary.plot(ax=ax, color="#7f8c8d", linewidth=0.9, zorder=2)
    for _, row in water.iterrows():
        type(water)([row], crs=water.crs).buffer(350).plot(ax=ax, color=row["cor"], zorder=3)
        point = row.geometry.representative_point()
        ax.annotate(row["troco"], (point.x, point.y), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold", zorder=5,
                    path_effects=[effects.withStroke(linewidth=2.2, foreground="white")])
    ax.set_xlabel(""), ax.set_ylabel("")
    ax.margins(0.06)
    _save_light(fig, plt, file)


# ----------------------------------------------------------------------------- static layers
def export_static(cfg: dict, folder) -> list[dict]:
    """Layers that only change when the models or the reference data change."""
    import geopandas as gpd

    from .rasters import read_bands
    from .water_quality import reach_polygons

    grid = load_grid(cfg)
    name = cfg["project"]["aoi_name"]
    maps, vectors = folder / "mapas", folder / "vetores"
    maps.mkdir(parents=True, exist_ok=True), vectors.mkdir(parents=True, exist_ok=True)
    entries = []

    classes = read_bands(path(cfg, "maps", "modelo_a", f"suscetibilidade_{name}_30m.tif", mkdir=False), ["classe"])["classe"]
    corners = write_overlay(classes, grid, SUSCEPTIBILITY, maps / "suscetibilidade.png", 0.00027)
    entries.append({"id": "suscetibilidade", "titulo": "Suscetibilidade a cheias", "tipo": "imagem", "ficheiro": "mapas/suscetibilidade.png", "cantos": corners,
                    "legenda": _legend(SUSCEPTIBILITY), "resolucao_m": 30, "atualizacao": "quando o Modelo A é treinado de novo",
                    "descricao": "Onde o terreno favorece a acumulação de água (Modelo A, treinado com 20 anos de dados).",
                    "limites": "As classes são faixas relativas dentro da área de estudo. Para avisar a população usam-se as zonas de aviso, não este mapa."})

    zones = gpd.read_file(path(cfg, "maps", "zonas_de_aviso", f"zonas_de_aviso_{name}.gpkg", mkdir=False))
    zones["cor"] = zones["zona"].map(ZONE_COLOURS)
    _geojson(zones, vectors / "zonas_de_aviso.geojson", tolerance_m=20)
    entries.append({"id": "zonas_de_aviso", "titulo": "Zonas de aviso", "tipo": "vetor", "ficheiro": "vetores/zonas_de_aviso.geojson",
                    "legenda": [{"valor": 1, "nome": "zona 1: primeiras a alagar", "cor": ZONE_COLOURS[1]}, {"valor": 2, "nome": "zona 2: cheia grande", "cor": ZONE_COLOURS[2]}],
                    "atualizacao": "quando houver uma nova cheia mapeada",
                    "descricao": "Onde a água chegou na cheia de janeiro de 2026 (mapas do Copernicus EMS): zona 1 nos primeiros mapas, zona 2 na maior extensão.",
                    "limites": "Baseadas numa única cheia. Fora da área analisada pelo Copernicus, as zonas são estimadas pelo Modelo A."})

    # the same zones as a small image: the web map draws this instead of the heavy polygons
    zone_raster = read_bands(path(cfg, "maps", "zonas_de_aviso", f"zonas_de_aviso_{name}_30m.tif", mkdir=False), ["zona"])["zona"]
    zone_corners = write_overlay(np.where(zone_raster > 0, zone_raster, np.nan), grid, {1: ("zona 1", ZONE_COLOURS[1]), 2: ("zona 2", ZONE_COLOURS[2])},
                                 maps / "zonas_de_aviso.png", 0.00027, alpha=170)
    entries[-1].update({"imagem": "mapas/zonas_de_aviso.png", "cantos": zone_corners})
    places = gpd.read_file(path(cfg, "maps", "zonas_de_aviso", f"lugares_{name}.gpkg", mkdir=False))
    _light_zone_map(cfg, zones, places, np.where(classes == 0, 1.0, np.nan), grid, maps / "mapa_leve_zonas.png")
    entries[-1]["mapa_leve"] = "mapas/mapa_leve_zonas.png"
    _geojson(places, vectors / "lugares.geojson")
    entries.append({"id": "lugares", "titulo": "Lugares e ordem de alagamento", "tipo": "vetor", "ficheiro": "vetores/lugares.geojson",
                    "campos": {"lugar": "nome", "categoria": "alaga primeiro / alaga em cheia grande / na margem da cheia / fora das zonas de aviso",
                               "primeira_data": "primeiro mapa de 2026 em que o lugar aparece alagado", "dias_apos_alerta": "dias entre o alerta laranja e esse mapa",
                               "edificios": "edifícios num raio de 500 m", "validado": "vazio até ser confirmado no terreno"},
                    "atualizacao": "quando os nomes forem validados",
                    "descricao": "Nomes de lugares (OpenStreetMap e GeoNames) com a ordem em que a água chegou na cheia de 2026.",
                    "limites": "Cada lugar é um ponto com um círculo de 500 m, não um limite oficial de bairro. Os nomes ainda não foram validados no terreno."})

    district = load_aoi(cfg, "district")[["geometry"]]
    _geojson(district.to_crs(grid.crs), vectors / "distrito.geojson", tolerance_m=30)
    entries.append({"id": "distrito", "titulo": "Distrito de Marracuene", "tipo": "vetor", "ficheiro": "vetores/distrito.geojson", "descricao": "Limite do distrito.", "atualizacao": "fixo"})
    _geojson(reach_polygons(cfg).to_crs(grid.crs), vectors / "trocos_do_rio.geojson")
    entries.append({"id": "trocos_do_rio", "titulo": "Troços do rio (qualidade da água)", "tipo": "vetor", "ficheiro": "vetores/trocos_do_rio.geojson",
                    "descricao": "Os quatro troços do Incomáti em que a cor da água é medida. O estado de cada um está em boletim/turbidez.csv (coluna `estado`).",
                    "legenda": [{"valor": k, "nome": k, "cor": v} for k, v in TURBIDITY_COLOURS.items()], "atualizacao": "fixo"})
    return entries


def export_water_maps(cfg: dict, folder) -> list[dict]:
    """The latest monthly water maps of Model B (10 m, drawn at about 20 m)."""
    from .rasters import read_bands

    grid = load_grid(cfg, 10)
    out = folder / "mapas" / "agua"
    out.mkdir(parents=True, exist_ok=True)
    files = sorted(path(cfg, "maps", "modelo_b", mkdir=False).glob("agua_*_10m.tif"))[-WATER_MAP_MONTHS:]
    keep, months, corners = set(), [], None
    for file in files:
        month = file.stem.split("_")[-2]
        target = out / f"agua_{month}.png"
        keep.add(target.name)
        if not target.exists() or target.stat().st_mtime < file.stat().st_mtime or corners is None:
            b = read_bands(file, ["agua", "cheia"])
            classes = np.where(b["cheia"] == 1, 2.0, np.where(b["agua"] == 1, 1.0, np.nan))
            corners = write_overlay(classes, grid, WATER, target, 0.00018)
        months.append(month)
    for old in out.glob("agua_*.png"):
        if old.name not in keep:
            old.unlink()
    return [{"id": "agua_mensal", "titulo": "Água e cheia vistas por radar, por mês", "tipo": "imagem_mensal", "ficheiro": "mapas/agua/agua_{mes}.png", "meses": months,
             "cantos": corners, "legenda": _legend(WATER), "resolucao_m": 20, "atualizacao": "mensal (precisa de descarregar o Sentinel-1 do mês)",
             "descricao": "Onde o radar Sentinel-1 viu água em cada mês (Modelo B). A vermelho, a água fora do sítio habitual.",
             "limites": "É a imagem de um mês inteiro, não de um dia. Em zonas construídas o modelo marca água a mais."}]


# ----------------------------------------------------------------------------- series and daily products
def export_series(cfg: dict, folder) -> list[dict]:
    from .forecast import load_history, load_limits
    from .water_quality import load_scene_series

    out = folder / "series"
    out.mkdir(parents=True, exist_ok=True)
    series = path(cfg, "series", mkdir=False)
    history = load_history(cfg).dropna(subset=["q"])
    history.loc[history.index >= history.index.max() - pd.Timedelta(days=3 * 365), ["q", "rain"]].round(2).rename(
        columns={"q": "caudal_m3s", "rain": "chuva_bacia_mm"}).rename_axis("data").to_csv(out / "caudal_e_chuva_diario.csv")
    alerts = pd.read_csv(series / "alertas_diarios.csv", parse_dates=["date"])
    alerts.loc[alerts["date"] >= "2015-01-01", ["date", "p7_basin", "discharge_m3s", "alerta"]].rename(
        columns={"date": "data", "p7_basin": "chuva_7d_mm", "discharge_m3s": "caudal_m3s"}).to_csv(out / "alertas_historicos.csv", index=False)
    shutil.copy2(series / "modelo_b_area_mensal.csv", out / "area_de_agua_mensal.csv")
    shutil.copy2(series / "vegetacao_no_rio_mensal.csv", out / "vegetacao_no_rio_mensal.csv")
    measured = load_scene_series(cfg, "sentinel2")[["date", "troco", "ndti", "pixeis"]]
    measured.assign(ndti=measured["ndti"].round(4)).rename(columns={"date": "data"}).to_csv(out / "cor_da_agua_por_imagem.csv", index=False)
    limits = load_limits(cfg)["discharge_m3s"]
    return [
        {"id": "caudal_e_chuva", "titulo": "Caudal e chuva dos últimos 3 anos", "tipo": "serie", "ficheiro": "series/caudal_e_chuva_diario.csv",
         "limites_de_alerta_m3s": limits, "descricao": "Caudal do Incomáti em Marracuene (modelo GloFAS) e chuva média na bacia (ERA5).",
         "limites": "O caudal vem de um modelo global, não de uma estação de medição."},
        {"id": "alertas_historicos", "titulo": "Alertas dia a dia desde 2015", "tipo": "serie", "ficheiro": "series/alertas_historicos.csv",
         "legenda": [{"valor": k, "nome": k, "cor": v} for k, v in ALERT_COLOURS.items()], "descricao": "O nível de alerta que as regras teriam dado em cada dia."},
        {"id": "area_de_agua", "titulo": "Área com água por mês", "tipo": "serie", "ficheiro": "series/area_de_agua_mensal.csv",
         "descricao": "Área de água e de cheia vista pelo radar em cada mês (km²)."},
        {"id": "cor_da_agua", "titulo": "Cor da água por imagem de satélite", "tipo": "serie", "ficheiro": "series/cor_da_agua_por_imagem.csv",
         "descricao": "Índice de cor NDTI de cada troço em cada imagem do Sentinel-2 (mais alto = mais turva).",
         "limites": "Índice relativo: não é turbidez em unidades reais nem diz se a água é segura."},
        {"id": "vegetacao_no_rio", "titulo": "Vegetação sobre a água", "tipo": "serie", "ficheiro": "series/vegetacao_no_rio_mensal.csv",
         "descricao": "Parte do canal do rio coberta por plantas, por troço e por mês.", "limites": "Só tem expressão no troço a montante. Por confirmar no terreno."}]


def export_daily(cfg: dict, folder) -> list[dict]:
    """Copy the latest bulletin and its tables, the exposure and the place list."""
    from .operations import exposure

    out = folder / "boletim"
    out.mkdir(parents=True, exist_ok=True)
    latest = path(cfg, "forecast", "latest", mkdir=False)
    for file in latest.iterdir():
        shutil.copy2(file, out / file.name)
    extra = folder / "exposicao"
    extra.mkdir(parents=True, exist_ok=True)
    exposure(cfg).to_csv(extra / "exposicao_por_zona.csv")
    name = cfg["project"]["aoi_name"]
    shutil.copy2(path(cfg, "maps", "zonas_de_aviso", f"lugares_por_ordem_de_alagamento_{name}.csv", mkdir=False), extra / "lugares_por_ordem_de_alagamento.csv")
    return [
        {"id": "boletim", "titulo": "Boletim de hoje", "tipo": "boletim", "ficheiro": "boletim/boletim.json", "texto": "boletim/boletim.md", "estado": "boletim/estado.json",
         "mensagem": "boletim/mensagem_whatsapp.txt",
         "tabelas": {"previsao_alertas": "boletim/previsao_alertas.csv", "cenarios_caudal": "boletim/cenarios_caudal.csv", "chuva_bacia": "boletim/chuva_bacia.csv",
                     "turbidez": "boletim/turbidez.csv", "turbidez_diaria": "boletim/turbidez_diaria.csv"},
         "cores_dos_alertas": ALERT_COLOURS, "atualizacao": "diária",
         "descricao": "Nível de alerta de cheia para os próximos 10 dias e previsão de turbidez para as manhãs.",
         "limites": "Se `estado.json` disser `previsao_indisponivel` ou `desatualizado: true`, a aplicação deve dizê-lo e nunca mostrar verde."},
        {"id": "exposicao", "titulo": "O que está em cada zona de aviso", "tipo": "tabela", "ficheiro": "exposicao/exposicao_por_zona.csv",
         "descricao": "Área, terras agrícolas, edifícios, escolas, unidades de saúde, estradas e pessoas em cada zona de aviso, dentro do distrito.",
         "limites": "As pessoas vêm do WorldPop 2020, que espalha a população por todo o terreno: numa planície com poucas casas é uma estimativa por cima. O número de edifícios é mais fiável."},
        {"id": "lugares_por_ordem", "titulo": "Lugares por ordem de alagamento", "tipo": "tabela", "ficheiro": "exposicao/lugares_por_ordem_de_alagamento.csv",
         "descricao": "A mesma informação da camada de lugares, em tabela."}]


QUALITY_COLOURS = {"normal": "#5dade2", "elevada": "#b9770e", "muito elevada": "#6e2c00", "sem dados": "#bdc3c7", "sem medição recente": "#bdc3c7"}


def export_quality(cfg: dict, folder) -> list[dict]:
    """Module Q for the Quality page: the sections from the border to the mouth with their
    current state, the monthly series since 2006, the normal values and the trends."""
    import geopandas as gpd

    from . import module_q_analysis as analysis

    if not any(path(cfg, "module_q_raw").glob("*.csv")):
        return []
    out = folder / "qualidade"
    out.mkdir(parents=True, exist_ok=True)
    data, skill, _ = analysis.expected_turbidity(cfg, analysis.monthly_dataset(cfg))
    state = analysis.section_state(cfg, data)
    state.round(4).to_csv(out / "estado_por_troco.csv")
    classes = analysis.anomalies(data, "ndti").set_index(["troco", "month"])["classe"]
    monthly = data.join(classes, on=["troco", "month"])
    columns = ["troco", "nome", "month", "fonte", "fiabilidade", "ndti", "turbidez_fnu", "tss_mg_l", "secchi_m", "vegetacao", "temp_c", "esperado", "residuo", "nao_explicada",
               "classe", "chuva_mm", "caudal_m3s", "n_imagens_landsat", "n_imagens_s2"]
    monthly[columns].round(4).to_csv(out / "serie_mensal.csv", index=False)
    analysis.climatology(data, "ndti").round(4).to_csv(out / "normais_por_mes.csv")
    analysis.trends(data).round(5).to_csv(out / "tendencias.csv", index=False)
    skill.round(3).to_csv(out / "modelo_turbidez_esperada.csv")
    water = gpd.read_file(path(cfg, "sections", "trocos_rio.gpkg", mkdir=False), layer="agua_permanente")
    water = water.assign(geometry=water.buffer(25)).join(state[["mes", "classe", "fiabilidade", "alerta_de_qualidade"]], on="troco")      # widened a little so narrow reaches show on the map
    water["cor"] = water["classe"].map(QUALITY_COLOURS).fillna("#bdc3c7")
    _geojson(water, folder / "vetores" / "trocos_modulo_q.geojson", tolerance_m=20)
    _light_quality_map(cfg, water, folder / "mapas" / "mapa_leve_qualidade.png")
    limits = ("Índice de cor da água visto por satélite, comparado com o normal de cada troço para o mês. A turbidez em FNU e os sólidos em mg/L são "
              "ESTIMATIVAS sem calibração local (os dois satélites diferem tipicamente por um fator de 1,5). Não mede se a água é segura.")
    return [
        {"id": "trocos_modulo_q", "titulo": "Qualidade da água por troço, da fronteira à foz", "tipo": "vetor", "ficheiro": "vetores/trocos_modulo_q.geojson",
         "legenda": [{"valor": k, "nome": k, "cor": v} for k, v in QUALITY_COLOURS.items() if k != "sem dados"], "atualizacao": "mensal",
         "mapa_leve": "mapas/mapa_leve_qualidade.png",
         "descricao": "Os nove troços do Incomáti em Moçambique, coloridos pelo estado do último mês medido.", "limites": limits},
        {"id": "qualidade_estado", "titulo": "Estado de cada troço", "tipo": "tabela", "ficheiro": "qualidade/estado_por_troco.csv", "atualizacao": "mensal",
         "descricao": "Último mês medido de cada troço: classe face ao normal, e se a cor está acima do que a chuva e o caudal explicam (alerta de qualidade).",
         "limites": "Um alerta de qualidade é um motivo para ir ver, não uma prova de poluição."},
        {"id": "qualidade_mensal", "titulo": "Série mensal por troço desde 2006", "tipo": "serie", "ficheiro": "qualidade/serie_mensal.csv", "atualizacao": "mensal",
         "descricao": "Cor da água, turbidez e sólidos estimados, transparência estimada, vegetação sobre a água e temperatura, por troço e mês.", "limites": limits},
        {"id": "qualidade_normais", "titulo": "Valor normal de cada troço em cada mês do ano", "tipo": "tabela", "ficheiro": "qualidade/normais_por_mes.csv",
         "descricao": "Mediana e percentis do índice de cor ao longo dos anos com dados.", "atualizacao": "anual"},
        {"id": "qualidade_tendencias", "titulo": "Tendências por troço", "tipo": "tabela", "ficheiro": "qualidade/tendencias.csv", "atualizacao": "anual",
         "descricao": "Teste de Mann-Kendall sazonal por parâmetro e troço, para o registo completo e para cada era de satélites.",
         "limites": "Uma tendência que só aparece no registo completo pode vir da mudança de satélite em 2013."}]


def _model_summary(cfg: dict) -> dict:
    models = path(cfg, "models", mkdir=False)
    read = lambda name: json.loads((models / name).read_text()) if (models / name).exists() else {}
    turbidity = read("modelo_turbidez.json")
    return {"limites_de_alerta": {k: read("limites_previsao.json").get(k) for k in ("discharge_m3s", "calibration", "created_utc")},
            "turbidez": {k: turbidity.get(k) for k in ("created_utc", "valid_for", "reaches", "skill")},
            "caudal_modelo_proprio": {k: read("modelo_c_caudal.json").get(k) for k in ("created_utc", "skill")},
            "mare": {k: read("mare_maputo.json").get(k) for k in ("source", "period", "test_last_12_months")}}


def _write_catalogue(cfg: dict, folder, entries: list[dict]) -> dict:
    file = folder / "catalogo.json"
    old = {e["id"]: e for e in json.loads(file.read_text())["camadas"]} if file.exists() else {}
    old.update({e["id"]: e for e in entries})
    status = json.loads((folder / "boletim" / "estado.json").read_text()) if (folder / "boletim" / "estado.json").exists() else {}
    catalogue = {"projeto": "Eyes to Earth (ETE): cheias e água do rio Incomáti, Marracuene", "versao_codigo": __version__,
                 "gerado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "sistema_de_coordenadas": "EPSG:4326 (latitude, longitude)",
                 "aviso": DISCLAIMER, "aplicacao": cfg.get("publication", {}).get("app_url", ""), "pagina_simples": cfg.get("publication", {}).get("page_url", ""),
                 "estado_da_previsao": {k: status.get(k) for k in ("estado", "data_da_previsao", "desatualizado", "fonte")},
                 "modelos": _model_summary(cfg), "camadas": list(old.values())}
    file.write_text(json.dumps(catalogue, indent=1, ensure_ascii=False))
    return catalogue


PAGE = """<!doctype html>
<html lang="pt">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>ETE - Rio Incomáti, Marracuene</title>
<style>
  body{{font-family:system-ui,-apple-system,"Segoe UI",Roboto,sans-serif;margin:0;background:#f4f6f6;color:#1c2833;line-height:1.45}}
  main{{max-width:640px;margin:0 auto;padding:14px}}
  h1{{font-size:1.15rem;margin:.3rem 0}} h2{{font-size:1rem;margin:1.2rem 0 .4rem}}
  .alerta{{border-radius:10px;padding:16px;color:{text};background:{colour};font-size:1.15rem}}
  .alerta b{{font-size:1.5rem;display:block}}
  .caixa{{background:#fff;border-radius:10px;padding:12px 14px;margin-top:10px}}
  table{{border-collapse:collapse;width:100%;font-size:.92rem}} td,th{{padding:5px 6px;border-bottom:1px solid #e5e8e8;text-align:left}}
  .ponto{{display:inline-block;width:.8em;height:.8em;border-radius:50%;margin-right:.35em;vertical-align:middle}}
  small,.nota{{color:#566573;font-size:.82rem}} a{{color:#1f618d}}
</style>
</head>
<body><main>
<h1>Eyes to Earth: rio Incomáti, Marracuene</h1>
<small>Boletim de {issued}</small>
<div id="alerta" class="alerta"><b>ALERTA {level}</b>{headline}</div>
<div id="corpo">
<div class="caixa"><h2 style="margin-top:0">O que fazer</h2>{advice}{places}</div>
<div class="caixa"><h2 style="margin-top:0">Próximos dias</h2><table><tr><th>Dia</th><th>Alerta</th><th>Caudal (m³/s)</th></tr>{days}</table></div>
{water}
</div>
<p class="nota">{disclaimer}{app_link}</p>
</main>
<script>
// never show an old bulletin as if it were today's: after {stale} hours the alert is replaced
var emitido = new Date("{issued_iso}");
if ((Date.now() - emitido.getTime()) / 36e5 > {stale}) {{
  var a = document.getElementById("alerta");
  a.style.background = "#566573"; a.style.color = "white";
  a.innerHTML = "<b>PREVISÃO INDISPONÍVEL</b>O último boletim tem mais de {stale} horas. Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.";
  document.getElementById("corpo").style.display = "none";
}}
</script>
</body></html>
"""


def write_static_page(cfg: dict) -> "Path":
    """Write the light page of the bulletin: one small HTML file with no external files, readable
    on any phone with very little network. It is the fallback when the application is asleep,
    slow or down. The page checks its own age in the browser and hides an old alert."""
    import html

    latest = path(cfg, "forecast", "latest", mkdir=False)
    data = json.loads((latest / "boletim.json").read_text())
    status = json.loads((latest / "estado.json").read_text())
    publication = cfg.get("publication", {})
    day = lambda text: pd.Timestamp(text).strftime("%d/%m")
    esc = html.escape
    if "nivel_maximo_provavel" not in data:
        level, colour, headline, advice, places, days = "INDISPONÍVEL", "#566573", "Hoje não foi possível fazer a previsão.", "<p>Siga os avisos do INGD, do INAM e da ARA-Sul.</p>", "", ""
    else:
        level, colour = data["nivel_maximo_provavel"].upper(), ALERT_COLOURS[data["nivel_maximo_provavel"]]
        headline, advice = esc(data["titulo"]), f"<p>{esc(data['conselho'])}</p>"
        first, large = data.get("lugares_que_alagam_primeiro") or [], data.get("lugares_em_cheia_grande") or []
        places = (f"<p><b>Alagam primeiro:</b> {esc(', '.join(first))}.</p>" if first else "") + (f"<p><b>Em cheia grande:</b> {esc(', '.join(large))}.</p>" if large else "")
        days = "".join(f"<tr><td>{day(d['data'])}</td><td><span class='ponto' style='background:{ALERT_COLOURS[d['alerta']]}'></span>{d['alerta']}</td><td>{d['caudal_mediana_m3s']:.0f}</td></tr>"
                       for d in data["previsao_diaria"])
    rows = "".join(f"<tr><td>{esc(str(t['troco']))}</td><td>{esc(str(t.get('estado', '')))}</td><td>{esc(str(t.get('previsao', '')))}</td></tr>" for t in data.get("turbidez", []))
    water = (f"<div class='caixa'><h2 style='margin-top:0'>Água do rio</h2><table><tr><th>Troço</th><th>Últimos 20 dias</th><th>Mais turva nos próximos dias?</th></tr>{rows}</table>"
             "<p class='nota'>A água do rio deve ser sempre tratada antes de beber. O satélite vê a cor da água; não mede se é segura.</p></div>") if rows else ""
    app = publication.get("app_url", "")
    page = PAGE.format(text="black" if level == "AMARELO" else "white", colour=colour, level=level, headline=headline, advice=advice, places=places, days=days, water=water,
                       issued=pd.Timestamp(status["emitido_utc"]).strftime("%d/%m/%Y, %H:%M UTC"), issued_iso=status["emitido_utc"], stale=int(publication.get("stale_after_hours", 36)),
                       disclaimer=esc(DISCLAIMER), app_link=f' <a href="{esc(app)}">Mapas e mais detalhe na plataforma</a>.' if app else "")
    folder = path(cfg, "static_page")
    (folder / "index.html").write_text(page)
    shutil.copy2(latest / "boletim.json", folder / "boletim.json")
    return folder / "index.html"


def export_package(cfg: dict) -> dict:
    """Rebuild the whole package (about a minute)."""
    folder = path(cfg, "platform")
    entries = export_static(cfg, folder) + export_water_maps(cfg, folder) + export_series(cfg, folder) + export_quality(cfg, folder) + export_daily(cfg, folder)
    return _write_catalogue(cfg, folder, entries)


def refresh_daily(cfg: dict) -> dict:
    """Rewrite only what changes every day (bulletin, tables, series). Builds the rest if missing."""
    folder = path(cfg, "platform")
    if not (folder / "catalogo.json").exists():
        return export_package(cfg)
    entries = export_series(cfg, folder) + export_daily(cfg, folder)
    raw = list(path(cfg, "module_q_raw").glob("*.csv"))
    state = folder / "qualidade" / "estado_por_troco.csv"
    if raw and (not state.exists() or state.stat().st_mtime < max(f.stat().st_mtime for f in raw)):     # new Module Q images since the last export
        entries += export_quality(cfg, folder)
    return _write_catalogue(cfg, folder, entries)
