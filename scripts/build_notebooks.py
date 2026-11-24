"""Gera os notebooks de aquisição de dados em notebooks/.

Os notebooks são leves: os parâmetros e os passos estão aqui, a lógica está em
src/ete. Voltar a correr este script depois de editar uma receita:

    python scripts/build_notebooks.py

O script reescreve os ficheiros .ipynb (incluindo os resultados), por isso as
alterações que devem ficar guardadas fazem-se aqui e não nos notebooks.
"""

from pathlib import Path
from textwrap import dedent

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

OUT = Path(__file__).resolve().parents[1] / "notebooks"

SETUP = """\
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config" / "config.yaml").exists())
sys.path.insert(0, str(ROOT / "src"))

import ee
import pandas as pd
import matplotlib.pyplot as plt

from ete import config, datasets, gee, series
from ete import grid as G

cfg = config.load_config()
gee.init(cfg)
"""

SETUP_AOI = SETUP + """
aoi = G.load_aoi(cfg)                       # AOI das imagens (EPSG:4326)
region = gee.ee_geometry(aoi)
grid30 = G.load_grid(cfg)                   # grelha do projeto a 30 m (EPSG:32736)
grid10 = G.load_grid(cfg, 10)               # grelha a 10 m, encaixada na de 30 m
climate_bounds = tuple(G.load_aoi(cfg, "aoi_climate").total_bounds)   # O, S, E, N
MASK = gee.ee_geometry(G.imagery_mask(cfg))  # distrito + margem: fora daqui as imagens mensais ficam sem dados
"""

MONTHLY_QC = """\
inv = series.monthly_inventory(OUT_DIR)
expected = [m.strftime("%Y-%m") for m in gee.month_starts(START, config.period_end(cfg))]
missing = sorted(set(expected) - set(inv["period"]))
print(f"{len(inv)} ficheiros, {inv['size_mb'].sum() / 1e3:.2f} GB em disco")
print(f"{len(missing)} de {len(expected)} meses sem ficheiro (ausentes na fonte ou com falha):")
print(missing)
"""


def header(title, task, variables, source, output, notes=""):
    text = f"""\
# {title}

| | |
|---|---|
| **Tarefa do plano** | {task} |
| **Variáveis (Parte I)** | {variables} |
| **Fonte** | {source} |
| **Saída** | `{output}` |

{notes}

Correr primeiro `00_setup_and_authentication` e `01_study_area_aoi`. Todos os
downloads podem ser retomados: os ficheiros que já existem são saltados, e cada
ficheiro fica registado em `data/metadata/download_manifest.csv`."""
    return ("md", text)


NOTEBOOKS = {}

# -----------------------------------------------------------------------------
NOTEBOOKS["00_setup_and_authentication"] = [
    ("md", """\
# 00 - Configuração e autenticação

Configuração inicial, feita uma única vez por cada membro da equipa. Cria a
árvore de pastas, verifica as credenciais e confirma que todos os IDs de
datasets do Earth Engine indicados no plano existem.

**Antes de correr**

1. Copiar `.env.example` para `.env` e preencher `EE_PROJECT` (o projeto Google
   Cloud registado no Earth Engine) e, para o GloFAS, `CDS_API_KEY`.
2. Num terminal: `earthengine authenticate` (abre o navegador uma vez)."""),
    ("code", """\
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config" / "config.yaml").exists())
sys.path.insert(0, str(ROOT / "src"))

import os
import pandas as pd
from ete import config

cfg = config.load_config()
print("Raiz do repositório:", ROOT)
print("EE_PROJECT         :", cfg["gee"]["project"] or "NÃO DEFINIDO -> editar o .env")
print("CDS_API_KEY        :", "definida" if os.getenv("CDS_API_KEY") or (Path.home() / ".cdsapirc").exists() else "NÃO DEFINIDA (só é necessária para o GloFAS)")
"""),
    ("md", "## 1. Criar a árvore de pastas"),
    ("code", """\
for key in cfg["paths"]:
    if key != "manifest":
        config.path(cfg, key)
print("\\n".join(sorted(v for k, v in cfg["paths"].items() if k != "manifest")))
"""),
    ("md", "## 2. Earth Engine"),
    ("code", """\
import ee
from ete import gee

gee.init(cfg)
print("Earth Engine OK:", ee.Number(1).add(1).getInfo() == 2)
"""),
    ("md", """\
## 3. Confirmar os IDs e as versões dos datasets

O plano pede que cada ID seja confirmado no catálogo antes de ser usado. As
colunas `first`/`last` mostram a cobertura temporal real de cada coleção (a nível
global, não apenas sobre Marracuene)."""),
    ("code", """\
ds = cfg["datasets"]
ids = {f"landsat {k}": v["id"] for k, v in ds["landsat"]["sensors"].items()}
ids |= {name: ds[name]["id"] for name in ["sentinel1", "sentinel2", "chirps", "imerg", "era5_land", "smap", "jrc_monthly", "dynamic_world"]}
ids |= {f"static {k}": v for k, v in ds["static"].items()}
ids |= {"worldpop": ds["exposure"]["worldpop"], "open_buildings": ds["exposure"]["open_buildings"]}
ids |= {"district": cfg["aoi"]["district_asset"], "basins": f"{cfg['aoi']['basins_asset_root']}/hybas_{cfg['aoi']['subbasin_level']}"}

rows = []
for name, asset_id in ids.items():
    try:
        rows.append({"dataset": name, **gee.describe_asset(asset_id), "status": "ok"})
    except Exception as err:
        rows.append({"dataset": name, "id": asset_id, "status": f"PROBLEMA: {str(err)[:80]}"})
catalogue = pd.DataFrame(rows)
catalogue.to_csv(config.path(cfg, "metadata", "gee_catalogue_check.csv"), index=False)
catalogue
"""),
    ("md", """\
Uma linha com `PROBLEMA` significa que o ID mudou ou foi substituído (por
exemplo, uma nova versão do SMAP). Corrigir o ID em `config/config.yaml`, e não
nos notebooks."""),
]

# -----------------------------------------------------------------------------
NOTEBOOKS["01_study_area_aoi"] = [
    ("md", """\
# 01 - Área de estudo e grelha comum

| | |
|---|---|
| **Tarefa do plano** | S1-03 - definir a área de estudo (bacia + Marracuene) e a projeção EPSG:32736 |
| **Variáveis (Parte I)** | #1 bacia do Incomáti, #2 distrito de Marracuene |
| **Fonte** | HydroBASINS e FAO GAUL 2015, via Earth Engine |
| **Saída** | `data/raw/aoi/` |

Ficheiros criados:

- `marracuene_district.geojson` - área-alvo dos alertas
- `incomati_basin.geojson` - bacia completa do Incomáti (todas as unidades HydroBASINS que partilham a mesma foz)
- `incomati_lower_subbasin.geojson` - a unidade de nível 6 que contém Marracuene
- `aoi.geojson` - **AOI das imagens**: retângulo envolvente do distrito + margem, usado para todos os dados de 10-30 m
- `aoi_climate.geojson` - retângulo envolvente da bacia + margem, usado para os dados de baixa resolução (chuva, humidade do solo, caudal)
- `grid.json` - a grelha de píxeis de 30 m em EPSG:32736 na qual todos os rasters são descarregados

Usam-se duas extensões de propósito: as cheias em Marracuene são causadas pela
chuva em toda a bacia, mas 20 anos de imagens de 10-30 m só são comportáveis
sobre o distrito."""),
    ("code", SETUP + """
import geopandas as gpd
from shapely.geometry import box

a = cfg["aoi"]
out = lambda name: config.path(cfg, "aoi", G.AOI_FILES[name])
"""),
    ("md", "## 1. Distrito de Marracuene"),
    ("code", """\
districts = ee.FeatureCollection(a["district_asset"]).filter(ee.Filter.eq("ADM0_NAME", a["country"]))
district_fc = districts.filter(ee.Filter.eq("ADM2_NAME", a["district"]))
if district_fc.size().getInfo() != 1:
    raise ValueError(f"o distrito não foi encontrado exatamente uma vez; nomes disponíveis: {sorted(districts.aggregate_array('ADM2_NAME').getInfo())}")
gee.download_vector(district_fc, out("district"))
district = gpd.read_file(out("district"))
print(f"área do distrito: {district.to_crs(cfg['grid']['crs']).area.sum() / 1e6:,.0f} km2")
"""),
    ("md", """\
## 2. Bacia do Incomáti

A bacia é encontrada a partir de um ponto sobre o rio (`aoi.river_point` no
config): todas as unidades de nível 12 com o mesmo `MAIN_BAS` formam a bacia
completa. A área publicada da bacia do Incomáti é de cerca de 46 000 km2 - se o
número impresso abaixo for muito diferente, o ponto não está sobre o Incomáti:
movê-lo e voltar a correr."""),
    ("code", """\
point = ee.Geometry.Point(a["river_point"])
units = ee.FeatureCollection(f"{a['basins_asset_root']}/hybas_{a['basin_level']}")
main_bas = units.filterBounds(point).first().get("MAIN_BAS")
gee.download_vector(units.filter(ee.Filter.eq("MAIN_BAS", main_bas)), out("basin"))
basin = gpd.read_file(out("basin")).dissolve()[["geometry"]]
basin["name"] = "Incomati basin"
basin.to_file(out("basin"), driver="GeoJSON")

sub_units = ee.FeatureCollection(f"{a['basins_asset_root']}/hybas_{a['subbasin_level']}")
gee.download_vector(sub_units.filterBounds(point), out("subbasin"))
subbasin = gpd.read_file(out("subbasin"))

km2 = lambda gdf: gdf.to_crs(cfg["grid"]["crs"]).area.sum() / 1e6
print(f"bacia completa   : {km2(basin):,.0f} km2 (esperado cerca de 46 000)")
print(f"sub-bacia baixa  : {km2(subbasin):,.0f} km2 (HydroBASINS nível {a['subbasin_level']})")
print("o distrito intersecta a bacia:", bool(district.intersects(basin.union_all()).any()))
"""),
    ("md", "## 3. AOI das imagens, AOI climática e grelha comum"),
    ("code", """\
g = cfg["grid"]
buffered = district.to_crs(g["crs"]).buffer(a["imagery_buffer_km"] * 1000)
grid30 = G.snapped_grid(buffered.total_bounds, g["crs"], g["res_historical_m"], g["snap_m"])
G.save_grid(cfg, grid30)

aoi = gpd.GeoDataFrame({"name": ["imagery AOI"]}, geometry=[box(*grid30.bounds)], crs=g["crs"]).to_crs(4326)
aoi.to_file(out("aoi"), driver="GeoJSON")

w, s, e, n = basin.total_bounds
d = a["climate_buffer_deg"]
aoi_climate = gpd.GeoDataFrame({"name": ["climate AOI"]}, geometry=[box(w - d, s - d, e + d, n + d)], crs=4326)
aoi_climate.to_file(out("aoi_climate"), driver="GeoJSON")

grid10 = grid30.with_res(g["res_recent_m"])
print(grid30)
for label, gr, bands in [("30 m (Landsat, 7 bandas)", grid30, 7), ("10 m (Sentinel-2, 8 bandas)", grid10, 8)]:
    print(f"{label}: {gr.width} x {gr.height} px, cerca de {gr.width * gr.height * bands * 4 / 1e6:,.0f} MB por mês antes da compressão")
"""),
    ("md", "## 4. Verificar no mapa"),
    ("code", """\
fig, axes = plt.subplots(1, 2, figsize=(13, 6))
basin.boundary.plot(ax=axes[0], color="tab:blue", label="bacia do Incomáti")
subbasin.boundary.plot(ax=axes[0], color="tab:cyan", linestyle="--", label="sub-bacia baixa")
aoi_climate.boundary.plot(ax=axes[0], color="grey", label="AOI climática")
aoi.boundary.plot(ax=axes[0], color="tab:red", label="AOI das imagens")
axes[0].legend(loc="lower left"); axes[0].set_title("Escala da bacia")

district.boundary.plot(ax=axes[1], color="black", label="distrito de Marracuene")
aoi.boundary.plot(ax=axes[1], color="tab:red", label="AOI das imagens")
axes[1].plot(*a["river_point"], "b*", markersize=12, label="ponto do rio")
axes[1].legend(loc="lower left"); axes[1].set_title("Escala do distrito")
plt.tight_layout()
"""),
    ("md", """\
**A validar (Agostinho):** abrir o `aoi.geojson` e os ficheiros da bacia no QGIS
sobre um mapa de base. Se a AOI das imagens dever seguir a bacia baixa em vez do
retângulo do distrito, alterar `aoi.imagery_buffer_km` ou substituir a geometria
aqui - mas fazê-lo **antes** de descarregar qualquer imagem, porque o `grid.json`
fixa a grelha de píxeis de todos os ficheiros seguintes."""),
]

# -----------------------------------------------------------------------------
NOTEBOOKS["02_static_layers"] = [
    header("02 - Camadas estáticas",
           "S1-05 - DEM, HAND, WorldCover, JRC GSW, HydroRIVERS (pasta `static/` completa)",
           "#3 rede hidrográfica, #33 elevação, #34 declive, #35 HAND, #36 distância ao rio, #37 acumulação de fluxo, #39 aspeto, #40 WorldCover, #41 ocorrência de água JRC",
           "Copernicus DEM GLO-30, MERIT Hydro, ESA WorldCover v200, JRC GSW v1.4, HydroSHEDS - via Earth Engine",
           "data/raw/static/",
           "Todos os rasters são descarregados na grelha do projeto, por isso já ficam alinhados."),
    ("code", SETUP_AOI + """
s = cfg["datasets"]["static"]
"""),
    ("md", """\
## 1. Terreno (30 m)

O declive e o aspeto são calculados pelo Earth Engine sobre o DEM nativo. O MERIT
Hydro é um produto de 90 m: o HAND e a área a montante são reamostrados (vizinho
mais próximo) para 30 m."""),
    ("code", """\
dem_col = ee.ImageCollection(s["dem"]).select("DEM")
dem = dem_col.mosaic().setDefaultProjection(dem_col.first().projection())
terrain = (dem.rename("elevation")
           .addBands(ee.Terrain.slope(dem).rename("slope"))
           .addBands(ee.Terrain.aspect(dem).rename("aspect")))
gee.download_static(cfg, "dem", s["dem"], terrain, ["elevation"], grid30, "static_terrain")
gee.download_static(cfg, "slope", s["dem"], terrain, ["slope"], grid30, "static_terrain")
gee.download_static(cfg, "aspect", s["dem"], terrain, ["aspect"], grid30, "static_terrain")

merit = ee.Image(s["merit_hydro"]).select(["hnd", "upa"], ["hand", "upstream_area"])
hand_file = gee.download_static(cfg, "hand", s["merit_hydro"], merit, ["hand"], grid30, "static_terrain")
gee.download_static(cfg, "flow_accumulation", s["merit_hydro"], merit, ["upstream_area"], grid30, "static_terrain")
"""),
    ("md", "## 2. Cobertura do solo (10 m) e histórico de água superficial (30 m)"),
    ("code", """\
worldcover = ee.ImageCollection(s["worldcover"]).first().select(["Map"], ["land_cover"])
gee.download_static(cfg, "worldcover", s["worldcover"], worldcover, ["land_cover"], grid10, "static_land_cover", dtype="uint8")

jrc_bands = ["occurrence", "seasonality", "recurrence", "transition", "max_extent"]
jrc_file = gee.download_static(cfg, "jrc_gsw", s["jrc_gsw"], ee.Image(s["jrc_gsw"]), jrc_bands, grid30, "static_surface_water", dtype="uint8")
"""),
    ("md", """\
## 3. Rede hidrográfica (vetor) e distância ao rio

Os rios são obtidos para toda a AOI climática. O raster de distância é calculado
localmente numa grelha alargada em 10 km, para que os rios logo fora da AOI
também contem; é uma camada derivada e fica em `data/interim/static/`."""),
    ("code", """\
import geopandas as gpd
import numpy as np
import rasterio
from rasterio.features import rasterize
from scipy.ndimage import distance_transform_edt
from shapely.geometry import box

rivers_file = config.path(cfg, "static_hydrography", "rivers_incomati.geojson")
if not rivers_file.exists():
    rivers_fc = ee.FeatureCollection(s["rivers"]).filterBounds(ee.Geometry.Rectangle(list(climate_bounds)))
    gee.download_vector(rivers_fc, rivers_file)
rivers = gpd.read_file(rivers_file).to_crs(grid30.crs)
print(len(rivers), "troços de rio")

pad = round(10_000 / grid30.res)
padded = G.Grid(grid30.crs, grid30.res, grid30.x0 - pad * grid30.res, grid30.y0 + pad * grid30.res,
                grid30.width + 2 * pad, grid30.height + 2 * pad)
near = rivers[rivers.intersects(box(*padded.bounds))]
if near.empty:
    raise ValueError("nenhum troço de rio a menos de 10 km da AOI das imagens - verificar a camada de rios")
river_px = rasterize(near.geometry, out_shape=(padded.height, padded.width), transform=padded.transform, all_touched=True)
distance = (distance_transform_edt(river_px == 0) * grid30.res)[pad:-pad, pad:-pad].astype("float32")

dist_file = config.path(cfg, "interim", "static", f"distance_to_river_{cfg['project']['aoi_name']}_30m.tif")
with rasterio.open(hand_file) as src:
    profile = src.profile
profile.update(count=1, dtype="float32", nodata=-9999.0)
with rasterio.open(dist_file, "w", **profile) as dst:
    dst.write(distance, 1)
    dst.set_band_description(1, "distance_to_river_m")
print("escrito", dist_file.relative_to(ROOT))
"""),
    ("md", "## 4. Controlo de qualidade"),
    ("code", """\
terrain_dir = config.path(cfg, "static_terrain")
name = cfg["project"]["aoi_name"]
fig, axes = plt.subplots(2, 3, figsize=(16, 12))
series.show_raster(terrain_dir / f"dem_{name}_30m.tif", ax=axes[0, 0], cmap="terrain")
series.show_raster(terrain_dir / f"slope_{name}_30m.tif", ax=axes[0, 1], cmap="magma", vmax=15)
series.show_raster(hand_file, ax=axes[0, 2], cmap="viridis_r", vmax=30)
series.show_raster(jrc_file, band="occurrence", ax=axes[1, 0], cmap="Blues")
series.show_raster(config.path(cfg, "static_land_cover") / f"worldcover_{name}_10m.tif", ax=axes[1, 1], cmap="tab20")
series.show_raster(dist_file, ax=axes[1, 2], cmap="cividis")
for ax in axes.flat:
    near.plot(ax=ax, color="red", linewidth=0.6)
    ax.set_xlim(grid30.bounds[0], grid30.bounds[2]); ax.set_ylim(grid30.bounds[1], grid30.bounds[3])
plt.tight_layout()
"""),
    ("md", """\
Verificar se a linha vermelha do rio segue o corredor de HAND baixo e a água do
JRC. A linha de rio do HydroSHEDS tem uma exatidão de algumas centenas de metros;
se estiver visivelmente fora do canal real, a distância ao rio deve mais tarde
ser recalculada a partir da água permanente do JRC (semana 2)."""),
]

# -----------------------------------------------------------------------------
def daily_notebook(number_title, task, variables, source, key, notes, body):
    return [
        header(number_title, task, variables, source, f"data/raw/{key}", notes),
        ("code", SETUP_AOI),
        *body,
    ]


NOTEBOOKS["03_precipitation_chirps"] = daily_notebook(
    "03 - Precipitação: CHIRPS diário", "S1-06 - CHIRPS 2006-2026 recortado à área de estudo (série diária)",
    "#23 precipitação diária (base para #24-#26, derivadas na semana 2)",
    "CHIRPS (CHC/UCSB) via Earth Engine `UCSB-CHG/CHIRPS/DAILY`",
    "precipitation/chirps/",
    "Descarregado na grelha nativa de 0,05 graus sobre toda a bacia (AOI climática), um NetCDF por ano.",
    [
        ("md", "## 1. Download"),
        ("code", """\
ds = cfg["datasets"]["chirps"]
OUT_DIR = config.path(cfg, "chirps")
grid = gee.collection_grid(ee.ImageCollection(ds["id"]), ds["band"], climate_bounds, fallback_res=0.05)
print(grid)

log = gee.download_daily_netcdf(cfg, "chirps", ds["id"], ds["band"], grid, OUT_DIR,
                                start=ds["start"], freq="YS", units="mm/day")
log
"""),
        ("md", "## 2. Controlo de qualidade e série da bacia"),
        ("code", """\
rain = series.open_series(cfg, "chirps", ds["band"])
print("período:", str(rain.time.values[0])[:10], "a", str(rain.time.values[-1])[:10], "|", rain.sizes)
print("dias em falta:", series.missing_days(rain))
print("intervalo (mm/dia):", float(rain.min()), "a", float(rain.max()))

daily = pd.DataFrame({
    "basin_mm": series.area_mean(rain, G.load_aoi(cfg, "basin")),
    "district_mm": series.area_mean(rain, G.load_aoi(cfg, "district")),
})
csv = config.path(cfg, "interim", "precipitation", "chirps_daily_area_mean.csv")
daily.to_csv(csv, index_label="date")
print("escrito", csv.relative_to(ROOT))

fig, axes = plt.subplots(2, 1, figsize=(13, 7))
daily.resample("YS").sum().set_axis(daily.resample("YS").sum().index.year).plot.bar(ax=axes[0])
axes[0].set_ylabel("mm / ano"); axes[0].set_title("Precipitação anual (o último ano pode estar incompleto)")
daily["basin_mm"].plot(ax=axes[1], linewidth=0.5)
axes[1].set_ylabel("mm / dia"); axes[1].set_title("Precipitação diária média da bacia")
plt.tight_layout()
"""),
    ])

NOTEBOOKS["04_precipitation_imerg"] = daily_notebook(
    "04 - Precipitação: GPM IMERG diário", "Apoia a S1-06 e a verificação de sobreposição CHIRPS x IMERG (semana 2)",
    "#27 precipitação GPM IMERG",
    "GPM IMERG V07 (NASA) via Earth Engine `NASA/GPM_L3/IMERG_V07`",
    "precipitation/imerg/",
    "A fonte é de meia em meia hora (mm/h). Cada dia é a taxa média do dia UTC vezes 24, "
    "o que dá mm/dia. Um NetCDF por mês, grelha nativa de 0,1 graus. Os dias são dias UTC, "
    "enquanto os dias do CHIRPS são dias locais dos pluviómetros: comparar os dois em somas de vários dias.",
    [
        ("md", "## 1. Download"),
        ("code", """\
ds = cfg["datasets"]["imerg"]
OUT_DIR = config.path(cfg, "imerg")
grid = gee.collection_grid(ee.ImageCollection(ds["id"]), ds["band"], climate_bounds, fallback_res=0.1)
print(grid)

log = gee.download_daily_netcdf(cfg, "imerg", ds["id"], ds["band"], grid, OUT_DIR,
                                start=ds["start"], freq="MS", multiply=24, units="mm/day")
log["status"].value_counts()
"""),
        ("md", "## 2. Controlo de qualidade"),
        ("code", """\
rain = series.open_series(cfg, "imerg", ds["band"])
print("período:", str(rain.time.values[0])[:10], "a", str(rain.time.values[-1])[:10], "|", rain.sizes)
print("dias em falta:", series.missing_days(rain))

daily = series.area_mean(rain, G.load_aoi(cfg, "basin")).rename("basin_mm")
csv = config.path(cfg, "interim", "precipitation", "imerg_daily_area_mean.csv")
daily.to_csv(csv, index_label="date")
daily.resample("MS").sum().plot(figsize=(13, 3.5), title="IMERG - precipitação mensal média da bacia (mm)")
"""),
    ])


def monthly_notebook(title, task, variables, source, key, notes, config_cell, test_month, preview, extra=()):
    return [
        header(title, task, variables, source, f"data/raw/{key}", notes),
        ("code", SETUP_AOI),
        *extra,
        ("md", """\
## Parâmetros

**Formato dos ficheiros.** Os valores são guardados como inteiros (`DTYPE`), multiplicados
por `SCALE`, para ocupar menos disco e menos internet sem perda relevante de precisão.
O fator fica gravado dentro do GeoTIFF: ler sempre com `series.read_scaled(ficheiro)`,
que devolve os valores físicos. As bandas `n_obs` e `label_mode` não são multiplicadas.
Com `MASK`, os píxeis fora do distrito + margem ficam sem dados (-9999)."""),
        ("code", config_cell),
        ("md", f"""\
## Teste com um mês

Correr sempre um mês primeiro e observá-lo antes de lançar o período completo.
`{test_month}` está na época chuvosa, quando as nuvens e as cheias são mais prováveis."""),
        ("code", f"""\
TEST_MONTH = "{test_month}"
test = gee.download_monthly(cfg, DATASET, SOURCE_ID, builder, BANDS, GRID, OUT_DIR,
                            start=f"{{TEST_MONTH}}-01", end=f"{{TEST_MONTH}}-28", dtype=DTYPE, scale=SCALE, mask=MASK)
test
"""),
        ("code", preview),
        ("md", """\
## Período completo

Demora bastante (horas para os datasets de 10 m). Pode ser interrompido e
retomado a qualquer momento; os meses já concluídos são saltados."""),
        ("code", """\
log = gee.download_monthly(cfg, DATASET, SOURCE_ID, builder, BANDS, GRID, OUT_DIR, start=START, dtype=DTYPE, scale=SCALE, mask=MASK)
log["status"].value_counts()
"""),
        ("md", "## Inventário"),
        ("code", MONTHLY_QC),
    ]


PREVIEW_OPTICAL = """\
import numpy as np
import rasterio

test_file = next(OUT_DIR.rglob(f"*_{TEST_MONTH}_*.tif"))
with rasterio.open(test_file) as src:
    print(src.descriptions, src.dtypes[0], src.crs, src.res, src.shape)
print(f"tamanho em disco: {test_file.stat().st_size / 1e6:.0f} MB")
data, _ = series.read_scaled(test_file)      # valores físicos (refletância 0-1)
rgb = np.clip(np.ma.filled(data[[2, 1, 0]], 0).transpose(1, 2, 0) / 0.25, 0, 1)
green, swir1, n_obs = data[BANDS.index("green")], data[BANDS.index("swir1")], data[-1]
mndwi = (green - swir1) / (green + swir1)

fig, axes = plt.subplots(1, 3, figsize=(17, 7))
axes[0].imshow(rgb); axes[0].set_title("cor verdadeira (preto = sem observação limpa)")
im = axes[1].imshow(mndwi, cmap="RdBu", vmin=-0.6, vmax=0.6); axes[1].set_title("MNDWI (azul = água)"); plt.colorbar(im, ax=axes[1], shrink=0.6)
im = axes[2].imshow(n_obs, cmap="viridis"); axes[2].set_title("n_obs (observações limpas)"); plt.colorbar(im, ax=axes[2], shrink=0.6)
print(f"píxeis sem nenhuma observação limpa: {(n_obs == 0).mean():.1%}")
"""

NOTEBOOKS["05_landsat_monthly_composites"] = monthly_notebook(
    "05 - Composições mensais Landsat 5/7/8/9 (30 m)",
    "S1-07 - composições mensais Landsat 2006-2026 com máscara de nuvens + contagem de observações válidas",
    "#4-#7 Landsat 5, 7, 8, 9 (bandas para os índices #12-#16, derivados na semana 2)",
    "USGS Landsat Collection 2 Level-2 (refletância de superfície) via Earth Engine",
    "optical/landsat/<ano>/",
    """\
Receita (`ete.datasets.landsat_builder`):

- máscara `QA_PIXEL`: preenchimento, nuvem dilatada, cirros, nuvem, sombra de nuvem; mais a saturação `QA_RADSAT`
- conversão para refletância de superfície (0-1)
- harmonização de Roy et al. (2016) **desligada** (`harmonize_tm_etm_to_oli: false` no config): medida sobre a AOI, baixava o MNDWI da água do Landsat 7 de 0,68 para 0,16; sem ela, Landsat 7 e 8 concordam sobre a água
- **mediana** mensal de todos os píxeis limpos, com cada sensor limitado ao seu intervalo de pesquisa no plano
- banda `n_obs` = número de observações limpas por píxel

Bandas: `blue, green, red, nir, swir1, swir2, n_obs`. Os píxeis nunca observados
num mês ficam como nodata (-9999): não são preenchidos.""",
    """\
ds = cfg["datasets"]["landsat"]
DATASET, SOURCE_ID = "landsat", "LANDSAT/{LT05,LE07,LC08,LC09}/C02/T1_L2"
BANDS = ds["bands"] + ["n_obs"]
GRID, DTYPE, START = grid30, "int16", ds["start"]
SCALE = 10000                               # refletância guardada como inteiro (x10000)
OUT_DIR = config.path(cfg, "landsat")
builder = datasets.landsat_builder(cfg, region)
print("harmonizado para OLI:", ds["harmonize_tm_etm_to_oli"])
""",
    "2013-01", PREVIEW_OPTICAL)

NOTEBOOKS["06_sentinel1_monthly_composites"] = monthly_notebook(
    "06 - Composições mensais Sentinel-1 (10 m)",
    "S1-08 - composições mensais Sentinel-1 2014-2026, órbita fixa + contagem de observações",
    "#17 VV, #18 VH, #21 ângulo de incidência, #22 direção da órbita (#19 rácio e #20 delta-VV são derivados na semana 2)",
    "Copernicus Sentinel-1 GRD (IW) via Earth Engine `COPERNICUS/S1_GRD`",
    "radar/sentinel1/<ano>/",
    """\
Receita (`ete.datasets.sentinel1_builder`): modo IW, cenas VV+VH de **uma só**
direção de órbita, mediana mensal da retrodifusão em dB, ângulo de incidência
médio e `n_obs`. Bandas: `VV, VH, angle, n_obs`. São esperadas menos passagens em
2022-2025 (perda do Sentinel-1B); a banda `n_obs` mostra isso.""",
    """\
ds = cfg["datasets"]["sentinel1"]
ORBIT_PASS = ds["orbit_pass"]
if ORBIT_PASS == "auto":
    ORBIT_PASS = max(passes, key=passes.get)
print("direção da órbita usada:", ORBIT_PASS)

DATASET, SOURCE_ID = "sentinel1", ds["id"]
BANDS = ds["bands"] + ["n_obs"]
GRID, DTYPE, START = grid10, "int16", ds["start"]
SCALE = 100                                 # dB e ângulo guardados como inteiro (x100 = 0,01 dB)
OUT_DIR = config.path(cfg, "sentinel1")
builder = datasets.sentinel1_builder(cfg, region, ORBIT_PASS)
""",
    "2023-02",
    """\
test_file = next(OUT_DIR.rglob(f"*_{TEST_MONTH}_*.tif"))
fig, axes = plt.subplots(1, 3, figsize=(17, 7))
series.show_raster(test_file, band="VV", ax=axes[0], cmap="gray", vmin=-25, vmax=0)
series.show_raster(test_file, band="VH", ax=axes[1], cmap="gray", vmin=-30, vmax=-5)
series.show_raster(test_file, band="n_obs", ax=axes[2], cmap="viridis")
""",
    extra=[
        ("md", """\
## Escolher a direção da órbita

Cenas por direção de órbita e por ano sobre a AOI. Com `orbit_pass: auto` usa-se
a direção com mais cenas em todo o período; escrever a escolha em
`config/config.yaml` assim que a equipa concordar, para que nunca mude entre
execuções."""),
        ("code", """\
s1 = datasets.sentinel1_collection(cfg, region)
passes = s1.aggregate_histogram("orbitProperties_pass").getInfo()
print("cenas por direção de órbita:", passes)

per_year = s1.map(lambda i: i.set("key", ee.String(i.get("orbitProperties_pass")).cat("_").cat(i.date().format("YYYY"))))
counts = pd.Series(per_year.aggregate_histogram("key").getInfo())
counts.index = pd.MultiIndex.from_tuples([k.split("_") for k in counts.index], names=["pass", "year"])
counts.unstack("pass").fillna(0).astype(int)
"""),
    ])

NOTEBOOKS["07_sentinel2_monthly_composites"] = monthly_notebook(
    "07 - Composições mensais Sentinel-2 (10 m)",
    "Dados óticos da Camada 2 (plano: Sentinel-2 L2A, 2017-2026)",
    "#8 B2/B3/B4, #9 B8/B8A, #10 B11/B12, #11 máscara SCL",
    "Copernicus Sentinel-2 L2A via Earth Engine `COPERNICUS/S2_SR_HARMONIZED`",
    "optical/sentinel2/<ano>/",
    """\
Receita (`ete.datasets.sentinel2_builder`): máscara SCL (sem dados, saturado,
sombra de nuvem, nuvem média/alta, cirros), refletância convertida para 0-1,
mediana mensal, `n_obs`. Bandas: `blue, green, red, nir, nir_narrow, swir1, swir2,
n_obs`; as bandas de 20 m são reamostradas para 10 m.

O arquivo L2A no Earth Engine não começa na mesma data em todo o lado. Os meses
sem nenhuma cena L2A sobre Marracuene ficam registados como `absent` no manifesto
e não geram ficheiro - verificar o primeiro mês disponível no inventário abaixo.""",
    """\
ds = cfg["datasets"]["sentinel2"]
DATASET, SOURCE_ID = "sentinel2", ds["id"]
BANDS = list(ds["bands"].values()) + ["n_obs"]
GRID, DTYPE, START = grid10, "int16", ds["start"]
SCALE = 10000                               # refletância guardada como inteiro (x10000), como no produto original
OUT_DIR = config.path(cfg, "sentinel2")
builder = datasets.sentinel2_builder(cfg, region)
""",
    "2023-02", PREVIEW_OPTICAL)

# -----------------------------------------------------------------------------
NOTEBOOKS["08_soil_moisture_era5land_smap"] = [
    header("08 - Humidade do solo e hidrometeorologia: ERA5-Land e SMAP",
           "Humidade do solo da Camada 1 para os 20 anos + reforço SMAP (verificação de sobreposição e correção de viés na semana 2)",
           "#28 água no solo camadas 1-2, #29 escoamento superficial, #30 temperatura e evaporação, #31 SMAP superficial, #32 SMAP zona radicular",
           "Agregados diários ERA5-Land (ECMWF) e SMAP L4 (NASA), via Earth Engine",
           "data/raw/hydromet/",
           "Valores diários sobre toda a bacia, na grelha nativa de cada produto. ERA5-Land: um "
           "NetCDF por variável e por ano. O SMAP é de 3 em 3 horas na fonte: cada dia é a média "
           "do dia UTC, um NetCDF por variável e por mês."),
    ("code", SETUP_AOI),
    ("md", "## 1. ERA5-Land (2006-2026)"),
    ("code", """\
era = cfg["datasets"]["era5_land"]
UNITS = {"volumetric_soil_water_layer_1": "m3/m3", "volumetric_soil_water_layer_2": "m3/m3",
         "surface_runoff_sum": "m/day", "temperature_2m": "K", "total_evaporation_sum": "m/day"}
era_grid = gee.collection_grid(ee.ImageCollection(era["id"]), era["bands"][0], climate_bounds, fallback_res=0.1)
print(era_grid)

for band in era["bands"]:
    log = gee.download_daily_netcdf(cfg, "era5land", era["id"], band, era_grid, config.path(cfg, "era5_land"),
                                    start=era["start"], freq="YS", units=UNITS.get(band, ""))
    print(band, log["status"].value_counts().to_dict())
"""),
    ("md", "## 2. SMAP L4 (2015-2026)"),
    ("code", """\
smap = cfg["datasets"]["smap"]
smap_grid = gee.collection_grid(ee.ImageCollection(smap["id"]), smap["bands"][0], climate_bounds, fallback_res=0.1)
print(smap_grid)

for band in smap["bands"]:
    log = gee.download_daily_netcdf(cfg, "smap", smap["id"], band, smap_grid, config.path(cfg, "smap"),
                                    start=smap["start"], freq="MS", units="m3/m3")
    print(band, log["status"].value_counts().to_dict())
"""),
    ("md", "## 3. Controlo de qualidade"),
    ("code", """\
basin = G.load_aoi(cfg, "basin")
era_sm = series.open_series(cfg, "era5_land", "volumetric_soil_water_layer_1")
smap_sm = series.open_series(cfg, "smap", "sm_surface")
print("ERA5-Land dias em falta:", len(series.missing_days(era_sm)), "| SMAP dias em falta:", len(series.missing_days(smap_sm)))

moisture = pd.DataFrame({"era5land_swvl1": series.area_mean(era_sm, basin),
                         "smap_sm_surface": series.area_mean(smap_sm, basin)})
csv = config.path(cfg, "interim", "hydromet", "soil_moisture_daily_basin_mean.csv")
moisture.to_csv(csv, index_label="date")
moisture.plot(figsize=(13, 4), linewidth=0.6, ylabel="m3/m3", title="Humidade superficial do solo, média da bacia (dados brutos, antes da correção de viés)")
"""),
]

# -----------------------------------------------------------------------------
NOTEBOOKS["09_river_discharge_glofas"] = [
    header("09 - Caudal do rio: reanálise GloFAS",
           "Série para o gatilho de alertas e para validação (apoia a S1-09)",
           "#44 caudal do rio",
           "GloFAS histórico (Copernicus EMS) através da API do CEMS Early Warning Data Store",
           "data/raw/discharge/glofas/",
           """\
**Antes de correr**

1. Entrar em <https://ewds.climate.copernicus.eu/> com a conta Copernicus/ECMWF,
   abrir o dataset *GloFAS historical* e aceitar a licença (uma vez).
2. Colocar o token pessoal da API no `.env` como `CDS_API_KEY`.

As chaves do pedido foram confirmadas com o servidor em outubro de 2026. Se o
servidor voltar a rejeitar o pedido, abrir o separador *Download* do dataset,
carregar em *Show API request* e alinhar as chaves no dicionário `request`."""),
    ("code", """\
import os
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config" / "config.yaml").exists())
sys.path.insert(0, str(ROOT / "src"))

import cdsapi
import pandas as pd
from datetime import date
from ete import config
from ete import grid as G

cfg = config.load_config()
ds = cfg["datasets"]["glofas"]
OUT_DIR = config.path(cfg, "glofas")
west, south, east, north = G.load_aoi(cfg, "aoi_climate").total_bounds
client = cdsapi.Client(url=ds["api_url"], key=os.environ["CDS_API_KEY"])
"""),
    ("md", "## 1. Download (um NetCDF por ano)"),
    ("code", """\
VARIABLE = "average_river_discharge_in_the_last_24_hours"
this_year = date.today().year

def fetch(year, product_type, months, out):
    request = {
        "system_version": [ds["system_version"]],
        "hydrological_model": [ds["hydrological_model"]],
        "product_type": [product_type],
        "timespan": ["time_mean"],
        "variable": [VARIABLE],
        "year": [str(year)],
        "month": months,
        "day": [f"{d:02d}" for d in range(1, 32)],
        "data_format": "netcdf",
        "download_format": "unarchived",
        "area": [float(north), float(west), float(south), float(east)],   # N, O, S, E
    }
    row = dict(dataset="glofas", source_id=f"{ds['dataset']} {ds['system_version']} {product_type}",
               period=str(year), bands="dis24", crs="EPSG:4326", resolution=0.05)
    try:
        client.retrieve(ds["dataset"], request, str(out))
        config.log_manifest(cfg, status="downloaded", file=out, n_images=len(months), **row)
    except Exception as err:
        config.log_manifest(cfg, status="failed", note=repr(err)[:300], **row)
        print(year, product_type, "FALHOU:", repr(err)[:300])

def months_available(year, product_type):
    # o servidor diz que meses existem para cada ano e tipo de produto
    valid = client.client.apply_constraints(ds["dataset"], {
        "system_version": [ds["system_version"]], "product_type": [product_type],
        "variable": [VARIABLE], "year": [str(year)]})
    return sorted(valid.get("month", []))

name = cfg["project"]["aoi_name"]
for year in range(ds["start_year"], this_year + 1):
    out = OUT_DIR / f"glofas_discharge_{name}_{year}.nc"
    # o ano corrente é atualizado em cada execução; ficheiros vazios (pedido interrompido) são refeitos
    if out.exists() and out.stat().st_size > 0 and year < this_year:
        continue
    consolidated = months_available(year, "consolidated")
    if consolidated:
        fetch(year, "consolidated", consolidated, out)
    # meses recentes ainda sem produto consolidado: produto intermédio, em ficheiro à parte
    recent = [m for m in months_available(year, "intermediate") if m not in consolidated] if year >= this_year - 1 else []
    if recent:
        fetch(year, "intermediate", recent, OUT_DIR / f"glofas_discharge_{name}_{year}_intermediate.nc")
sorted(p.name for p in OUT_DIR.glob("*.nc"))
"""),
    ("md", """\
O produto *consolidated* tem um atraso de alguns meses em relação ao tempo real.
Os meses mais recentes vêm do produto *intermediate* e ficam num ficheiro à parte
(`..._intermediate.nc`), porque são provisórios e mais tarde são substituídos.

## 2. Série de caudal em Marracuene

A série é retirada da célula com o maior caudal médio dentro do retângulo
envolvente do distrito, ou seja, o curso principal do Incomáti. Confirmar a
localização no mapa antes de usar a série como gatilho de alertas."""),
    ("code", """\
import xarray as xr
import matplotlib.pyplot as plt

files = sorted(OUT_DIR.glob("glofas_discharge_*.nc"))
parts = [xr.open_dataset(f) for f in files]
var = [v for v in parts[0].data_vars if parts[0][v].ndim >= 3][0]
time_dim = [d for d in parts[0][var].dims if "time" in d][0]
dis = xr.concat([p[var] for p in parts], dim=time_dim).squeeze(drop=True).sortby(time_dim)
print(var, dict(dis.sizes), dis.attrs.get("units"))

lat, lon = [d for d in dis.dims if "lat" in d][0], [d for d in dis.dims if "lon" in d][0]
w, s, e, n = G.load_aoi(cfg, "district").total_bounds
local = dis.where((dis[lat] >= s) & (dis[lat] <= n) & (dis[lon] >= w) & (dis[lon] <= e), drop=True)
mean = local.mean(time_dim)
cell = mean.where(mean == mean.max(), drop=True)
cell_lat, cell_lon = float(cell[lat][0]), float(cell[lon][0])
print(f"célula do curso principal: lat {cell_lat:.3f}, lon {cell_lon:.3f}")

q = dis.sel({lat: cell_lat, lon: cell_lon}).to_series().rename("discharge_m3s")
csv = config.path(cfg, "interim", "discharge", "glofas_daily_marracuene.csv")
q.to_csv(csv, index_label="date")

fig, axes = plt.subplots(1, 2, figsize=(15, 4), width_ratios=[1, 2.5])
dis.mean(time_dim).plot(ax=axes[0], cmap="Blues"); axes[0].plot(cell_lon, cell_lat, "r*", markersize=12)
q.plot(ax=axes[1], linewidth=0.6, ylabel="m3/s", title="GloFAS - caudal diário em Marracuene")
plt.tight_layout()
"""),
]

# -----------------------------------------------------------------------------
NOTEBOOKS["10_surface_water_jrc_and_flood_events"] = monthly_notebook(
    "10 - Histórico mensal de água JRC e identificação de eventos de cheia",
    "S1-09 - identificar eventos de cheia 2006-2026 (JRC mensal + mapas públicos EMS/UNOSAT)",
    "#42 histórico mensal de água JRC (rótulos), #45 mapas públicos de eventos de cheia",
    "JRC Global Surface Water v1.4 Monthly History via Earth Engine; Copernicus EMS e UNOSAT (manual)",
    "labels/jrc_monthly_history/<ano>/",
    """\
Banda `water`: **0 = sem observação, 1 = não é água, 2 = água**. O produto termina
em dezembro de 2021. O valor 0 é informação (nuvem, sem passagem do Landsat), não
é terra seca - nunca deve ser lido como "não é água".

Precisa do `02_static_layers` (ocorrência JRC) para a análise de eventos no fim.""",
    """\
ds = cfg["datasets"]["jrc_monthly"]
DATASET, SOURCE_ID = "jrcmonthly", ds["id"]
BANDS = ["water"]
GRID, DTYPE, START = grid30, "uint8", ds["start"]
SCALE, MASK = 1, None                       # classes 0/1/2, retângulo completo (ficheiros pequenos)
OUT_DIR = config.path(cfg, "jrc_monthly")
builder = datasets.jrc_monthly_builder(cfg)
""",
    "2013-01",
    """\
test_file = next(OUT_DIR.rglob(f"*_{TEST_MONTH}_*.tif"))
series.show_raster(test_file, cmap="viridis", vmin=0, vmax=2)
""")
# o produto JRC tem uma data de fim fixa, ao contrário das coleções ainda em curso
NOTEBOOKS["10_surface_water_jrc_and_flood_events"] = [
    (kind, src.replace("start=START, dtype=DTYPE,", "start=START, end=ds[\"end\"], dtype=DTYPE,")
              .replace("config.period_end(cfg))]", "ds[\"end\"])]"))
    for kind, src in NOTEBOOKS["10_surface_water_jrc_and_flood_events"]
] + [
    ("md", """\
## Meses candidatos a cheia (a partir dos dados)

Para cada mês: a área observada, a área de água e a área de água **fora da água
permanente** (ocorrência JRC abaixo de 75 %). Os meses em que menos de metade da
AOI foi observada ficam assinalados, porque um mês de cheia com nuvens pode
mostrar pouca água."""),
    ("code", """\
import numpy as np
import rasterio

name = cfg["project"]["aoi_name"]
with rasterio.open(config.path(cfg, "static_surface_water") / f"jrc_gsw_{name}_30m.tif") as src:
    occurrence = src.read(src.descriptions.index("occurrence") + 1)
permanent = (occurrence >= 75) & (occurrence <= 100)
px_km2 = (grid30.res ** 2) / 1e6

rows = []
for f in sorted(OUT_DIR.rglob("*.tif")):
    with rasterio.open(f) as src:
        water = src.read(1)
    observed, is_water = np.isin(water, [1, 2]), water == 2
    rows.append({"month": f.stem.split("_")[2],
                 "observed_fraction": observed.mean(),
                 "water_km2": is_water.sum() * px_km2,
                 "flood_water_km2": (is_water & ~permanent).sum() * px_km2})
water_area = pd.DataFrame(rows).set_index("month")
water_area["well_observed"] = water_area["observed_fraction"] >= 0.5
csv = config.path(cfg, "flood_events", "jrc_monthly_water_area.csv")
water_area.to_csv(csv)

ax = water_area["flood_water_km2"].plot(figsize=(14, 4), ylabel="km2", title="Água fora dos corpos de água permanentes (JRC mensal)")
water_area[water_area["well_observed"]].nlargest(15, "flood_water_km2")
"""),
    ("md", """\
## Catálogo de eventos (a preencher à mão)

A tabela acima apenas sugere meses **candidatos**. Cada evento tem de ser
confirmado numa fonte pública antes de ser usado como rótulo, e nada entra aqui
sem uma referência:

- Copernicus EMS Rapid Mapping, filtro de país *Mozambique*: <https://rapidmapping.emergency.copernicus.eu/>
- UNOSAT: <https://unosat.org/>
- cruzar com as séries do CHIRPS (notebook 03) e do GloFAS (notebook 09)

Os mapas de eventos descarregados ficam em `data/raw/labels/ems_unosat/<event_id>/`.
Depois de 2021 não há dados JRC mensais, por isso os eventos vêm apenas dessas
fontes e dos picos de chuva e de caudal."""),
    ("code", """\
catalogue = config.path(cfg, "flood_events", "flood_events_catalogue.csv")
if not catalogue.exists():
    pd.DataFrame(columns=["event_id", "start_date", "end_date", "description", "source", "activation_code",
                          "source_url", "covers_aoi", "map_folder", "confirmed_by", "notes"]).to_csv(catalogue, index=False)
    print("modelo vazio criado:", catalogue.relative_to(ROOT))
pd.read_csv(catalogue)
"""),
]

NOTEBOOKS["11_dynamic_world_monthly"] = monthly_notebook(
    "11 - Probabilidade mensal de água Dynamic World (10 m)",
    "Reforço da Camada 2 (P2)",
    "#43 cobertura do solo quase em tempo real, classe `water`",
    "Dynamic World V1 (Google/WRI) via Earth Engine `GOOGLE/DYNAMICWORLD/V1`",
    "land_cover/dynamic_world/<ano>/",
    """\
Bandas: probabilidade média mensal de `water` e `flooded_vegetation`, a classe
mais frequente (`label_mode`, 0-8) e `n_obs`. O Dynamic World é produzido a partir
do Sentinel-2 por um modelo, por isso é uma **feature**, não um rótulo
independente para o Modelo B.""",
    """\
ds = cfg["datasets"]["dynamic_world"]
DATASET, SOURCE_ID = "dynamicworld", ds["id"]
BANDS = ["water", "flooded_vegetation", "label_mode", "n_obs"]
GRID, DTYPE, START = grid10, "int16", ds["start"]
SCALE = 10000                               # probabilidades guardadas como inteiro (x10000)
OUT_DIR = config.path(cfg, "dynamic_world")
builder = datasets.dynamic_world_builder(cfg, region)
""",
    "2023-02",
    """\
test_file = next(OUT_DIR.rglob(f"*_{TEST_MONTH}_*.tif"))
fig, axes = plt.subplots(1, 3, figsize=(17, 7))
series.show_raster(test_file, band="water", ax=axes[0], cmap="Blues", vmin=0, vmax=1)
series.show_raster(test_file, band="flooded_vegetation", ax=axes[1], cmap="Greens", vmin=0, vmax=1)
series.show_raster(test_file, band="n_obs", ax=axes[2], cmap="viridis")
""")

# -----------------------------------------------------------------------------
NOTEBOOKS["12_exposure_population_buildings_osm"] = [
    header("12 - Exposição: população, edifícios, estradas e equipamentos",
           "Dados de entrada do motor de alertas (P2, necessários na semana 4)",
           "#48 população, #49 edifícios, #50 estradas, escolas, centros de saúde",
           "WorldPop e Google Open Buildings v3 via Earth Engine; OpenStreetMap via Overpass (osmnx)",
           "data/raw/exposure/",
           "Todas as camadas estão limitadas à AOI das imagens."),
    ("code", SETUP_AOI + """
import geopandas as gpd
ex = cfg["datasets"]["exposure"]
"""),
    ("md", """\
## 1. População (WorldPop, grelha nativa de ~100 m)

Mantida na grelha nativa lat/lon para que a contagem de pessoas por píxel não
seja alterada pela reamostragem."""),
    ("code", """\
pop = (ee.ImageCollection(ex["worldpop"])
       .filter(ee.Filter.eq("country", "MOZ")).filter(ee.Filter.eq("year", ex["worldpop_year"]))
       .first().select("population"))
pop_grid = G.native_latlon_grid(pop.projection().getInfo()["transform"], tuple(aoi.total_bounds))
pop_file = gee.download_static(cfg, f"worldpop_{ex['worldpop_year']}", ex["worldpop"], pop, ["population"], pop_grid, "population")

import rasterio
with rasterio.open(pop_file) as src:
    print(f"pessoas dentro da AOI das imagens: {src.read(1, masked=True).sum():,.0f}")
series.show_raster(pop_file, cmap="inferno", vmax=50)
"""),
    ("md", """\
## 2. Edifícios (Google Open Buildings v3)

Descarregados em mosaicos (a tabela é grande) e depois unidos; os duplicados nas
fronteiras dos mosaicos são removidos com o plus code do edifício. Só se pedem os
mosaicos que tocam no distrito + margem. Se o servidor recusar um mosaico por ser
demasiado pesado, ele é dividido em quatro e pedido de novo; a célula pode ser
interrompida e retomada."""),
    ("code", """\
import numpy as np
from tqdm.auto import tqdm

buildings_file = config.path(cfg, "buildings", f"open_buildings_{cfg['project']['aoi_name']}.gpkg")
if not buildings_file.exists():
    from shapely.geometry import box
    fc = ee.FeatureCollection(ex["open_buildings"]).filter(ee.Filter.gte("confidence", ex["open_buildings_min_confidence"]))
    mask_polygon = G.imagery_mask(cfg).union_all()                      # distrito + margem
    inside = lambda w, s, e, n: box(w, s, e, n).intersects(mask_polygon)   # salta mar e cantos fora do distrito
    w, s, e, n = aoi.total_bounds
    # mosaicos de cerca de 0,025 graus (2,5 km): pedidos pequenos, a que o servidor responde em segundos
    nx, ny = int(np.ceil((e - w) / 0.025)), int(np.ceil((n - s) / 0.025))
    xs, ys = np.linspace(w, e, nx + 1), np.linspace(s, n, ny + 1)
    tiles_dir = config.path(cfg, "buildings", "tiles")
    files = []
    for i in tqdm(range(nx), desc="edifícios"):
        for j in range(ny):
            # um mosaico cujo pedido falha é dividido em quatro mais pequenos, automaticamente
            files += gee.download_vector_tiled(fc, (xs[i], ys[j], xs[i + 1], ys[j + 1]), tiles_dir,
                                               keep=inside, name=f"tile_{i:02d}_{j:02d}")
    parts = [part for part in (gpd.read_file(f) for f in files) if len(part)]
    buildings = gpd.GeoDataFrame(pd.concat(parts), crs=4326).drop_duplicates("full_plus_code")
    buildings = buildings[buildings.intersects(mask_polygon)][["full_plus_code", "confidence", "area_in_meters", "geometry"]]
    buildings.to_file(buildings_file, driver="GPKG")
    config.log_manifest(cfg, dataset="open_buildings", source_id=ex["open_buildings"], period="static",
                        status="downloaded", n_images=len(buildings), file=buildings_file, crs="EPSG:4326")
buildings = gpd.read_file(buildings_file)
print(f"{len(buildings):,} edifícios com confiança >= {ex['open_buildings_min_confidence']}")
"""),
    ("md", "## 3. Estradas, escolas e unidades de saúde (OpenStreetMap)"),
    ("code", """\
import osmnx as ox

polygon = aoi.union_all()
layers = {
    "roads": {"highway": ["motorway", "trunk", "primary", "secondary", "tertiary", "unclassified", "residential", "track"]},
    "schools": {"amenity": ["school", "kindergarten", "college", "university"]},
    "health": {"amenity": ["hospital", "clinic", "doctors", "pharmacy"], "healthcare": True},
}
for layer, tags in layers.items():
    out = config.path(cfg, "osm", f"osm_{layer}_{cfg['project']['aoi_name']}.gpkg")
    if not out.exists():
        feats = ox.features_from_polygon(polygon, tags).reset_index()
        keep = [c for c in ["id", "name", "highway", "amenity", "healthcare", "surface", "geometry"] if c in feats.columns]
        feats = feats[keep]
        for col in feats.columns.drop("geometry"):
            feats[col] = feats[col].astype(str)
        feats.to_file(out, driver="GPKG")
        config.log_manifest(cfg, dataset=f"osm_{layer}", source_id="OpenStreetMap (Overpass)", period=str(pd.Timestamp.today().date()),
                            status="downloaded", n_images=len(feats), file=out, crs="EPSG:4326")
    print(layer, len(gpd.read_file(out)), "elementos")
"""),
    ("md", """\
A cobertura do OpenStreetMap para escolas e centros de saúde nas zonas rurais de
Moçambique é incompleta: tratar estas camadas como um limite inferior e dizê-lo
na plataforma."""),
]

# -----------------------------------------------------------------------------
NOTEBOOKS["99_data_inventory_and_qc"] = [
    ("md", """\
# 99 - Inventário de dados e controlo de qualidade

Pode ser corrido a qualquer momento (não precisa do Earth Engine). Resume o que
está em disco, verifica se todos os GeoTIFF estão na grelha do projeto e mostra
que meses existem para cada dataset mensal. Usar os resultados na apresentação
de progresso de sábado e para atualizar a coluna *Status download* do plano."""),
    ("code", """\
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config" / "config.yaml").exists())
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import rasterio
import matplotlib.pyplot as plt

from ete import config, series
from ete import grid as G

cfg = config.load_config()
grid30 = G.load_grid(cfg)
"""),
    ("md", "## 1. O que está em disco"),
    ("code", """\
rows = []
for key, rel in cfg["paths"].items():
    folder = ROOT / rel
    if key in ("manifest", "metadata") or not folder.is_dir():
        continue
    files = [f for f in folder.rglob("*") if f.is_file() and ".part" not in f.name]
    rows.append({"dataset": key, "folder": rel, "files": len(files),
                 "size_gb": round(sum(f.stat().st_size for f in files) / 1e9, 3)})
inventory = pd.DataFrame(rows)
inventory.to_csv(config.path(cfg, "metadata", "inventory.csv"), index=False)
print(f"total: {inventory['size_gb'].sum():.2f} GB")
inventory
"""),
    ("md", """\
## 2. Alinhamento da grelha

Todos os rasters UTM têm de usar EPSG:32736, ter a extensão do projeto e um
tamanho de píxel de 10 ou 30 m com a mesma origem. Qualquer linha listada aqui é
um problema."""),
    ("code", """\
problems = []
tifs = [f for f in (ROOT / "data").rglob("*.tif") if ".part" not in f.name]
for f in tifs:
    with rasterio.open(f) as src:
        if src.crs is None or src.crs.to_epsg() != 32736:
            continue                                    # camadas na grelha nativa lat/lon (ex.: WorldPop)
        left, bottom, right, top = src.bounds
        ok = (np.allclose([left, bottom, right, top], grid30.bounds) and src.res[0] in (10, 30))
        if not ok:
            problems.append({"file": str(f.relative_to(ROOT)), "res": src.res, "bounds": tuple(src.bounds)})
print(f"{len(tifs)} GeoTIFF verificados, {len(problems)} fora da grelha")
pd.DataFrame(problems)
"""),
    ("md", "## 3. Cobertura mensal"),
    ("code", """\
monthly = {"landsat": "landsat", "sentinel1": "sentinel1", "sentinel2": "sentinel2",
           "jrc_monthly": "jrc_monthly", "dynamic_world": "dynamic_world"}
months = pd.period_range(cfg["period"]["start"], config.period_end(cfg), freq="M").strftime("%Y-%m")
coverage = pd.DataFrame(
    {name: months.isin(series.monthly_inventory(config.path(cfg, key))["period"]) for name, key in monthly.items()},
    index=months)

fig, ax = plt.subplots(figsize=(14, 2.8))
ax.imshow(coverage.T.values, aspect="auto", cmap="Greens", vmin=0, vmax=1.3, interpolation="none")
ax.set_yticks(range(len(coverage.columns)), coverage.columns)
ticks = [i for i, m in enumerate(months) if m.endswith("-01")]
ax.set_xticks(ticks, [months[i][:4] for i in ticks], rotation=90)
ax.set_title("Meses com ficheiro em disco (verde = presente)")
plt.tight_layout()
coverage.groupby(coverage.index.str[:4]).sum().T
"""),
    ("md", """\
## 4. Manifesto de downloads

`absent` = a fonte não tinha nenhuma imagem para esse período (fica como em
falta, nunca é preenchido). `failed` = o pedido falhou; voltar a correr o
notebook do dataset. `downloaded` = descarregado com sucesso."""),
    ("code", """\
manifest_file = ROOT / cfg["paths"]["manifest"]
if manifest_file.exists():
    # um período pode ficar registado em várias execuções: manter o estado mais recente
    manifest = pd.read_csv(manifest_file).drop_duplicates(["dataset", "period", "bands"], keep="last")
    display(manifest.pivot_table(index="dataset", columns="status", values="period", aggfunc="count", fill_value=0))
    display(manifest[manifest["status"] == "failed"].tail(20))
else:
    print("ainda não há downloads registados")
"""),
]


def build():
    OUT.mkdir(exist_ok=True)
    for name, cells in NOTEBOOKS.items():
        target = OUT / f"{name}.ipynb"
        sources = [dedent(source).strip("\n") for _, source in cells]
        # notebooks whose cells did not change are left alone, so their outputs are kept
        if target.exists() and [c.source for c in nbformat.read(target, 4).cells] == sources:
            print("sem alterações", target.name)
            continue
        nb = new_notebook()
        nb.metadata["kernelspec"] = {"display_name": "Python 3 (ete)", "language": "python", "name": "python3"}
        nb.metadata["language_info"] = {"name": "python"}
        for kind, source in cells:
            source = dedent(source).strip("\n")
            nb.cells.append(new_markdown_cell(source) if kind == "md" else new_code_cell(source))
        nbformat.write(nb, OUT / f"{name}.ipynb")
        print("escrito", f"notebooks/{name}.ipynb")


if __name__ == "__main__":
    build()
