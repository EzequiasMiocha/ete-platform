"""Gera os notebooks da Semana 2 (processamento, features e rótulos) em notebooks/semana_2/.

    python scripts/build_notebooks_semana2.py

Os notebooks são leves: os passos estão aqui, a lógica está em src/ete. Um
notebook cujas células não mudaram não é reescrito, para manter os resultados.
Nenhum notebook da Semana 2 precisa de internet.
"""

from pathlib import Path
from textwrap import dedent

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

OUT = Path(__file__).resolve().parents[1] / "notebooks" / "semana_2"

SETUP = """\
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config" / "config.yaml").exists())
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ete import config, drivers, features, rasters, series, training
from ete import grid as G

cfg = config.load_config()
P = cfg["processing"]
REPORTS = config.path(cfg, "reports", "semana_2")       # figuras e tabelas para o relatório
pd.set_option("display.float_format", "{:,.3f}".format)
"""


def header(title, task, what, inputs, outputs, notes=""):
    return ("md", f"""\
# {title}

| | |
|---|---|
| **Tarefa do plano** | {task} |
| **O que faz** | {what} |
| **Usa** | {inputs} |
| **Produz** | {outputs} |

{notes}""")


NB = {}

# =============================================================================
NB["20_indices_espectrais_e_radar"] = [
    header("20 - Índices espectrais e features de radar",
           "S2-02 (harmonização Landsat) e S2-03 (índices NDWI, MNDWI, NDVI, NDMI + ΔVV e rácio VV/VH)",
           "Transforma as bandas dos satélites em números que realçam a água",
           "Landsat, Sentinel-2 e Sentinel-1 mensais (Semana 1)",
           "`data/interim/features/` (referência seca do radar, rasters de índices dos meses escolhidos)",
           """\
**Ideia simples.** Uma imagem de satélite tem várias bandas (cores, incluindo
infravermelho). A água reflete pouco infravermelho, por isso combinar duas bandas
numa fração dá um número que separa bem a água do resto.

| Índice | Fórmula | Como ler |
|---|---|---|
| NDWI | (verde − NIR) / (verde + NIR) | acima de 0: água |
| MNDWI | (verde − SWIR1) / (verde + SWIR1) | acima de 0: água; melhor junto a zonas construídas |
| NDVI | (NIR − vermelho) / (NIR + vermelho) | alto: vegetação densa |
| NDMI | (NIR − SWIR1) / (NIR + SWIR1) | alto: vegetação ou solo húmidos |
| VV, VH | radar em dB | muito negativo (escuro): água calma |
| ΔVV | VV do mês − VV da época seca | muito negativo: apareceu água nova |
| VV − VH | rácio em dB | ajuda a separar água de vegetação alagada |

Os índices são contas rápidas. Por isso **não** se guardam para todos os meses
(duplicaria vários GB): são calculados na hora quando se monta a tabela de treino,
e exportados como raster só para os meses que se quer abrir no QGIS."""),
    ("code", SETUP),
    ("md", """\
## 1. Harmonização Landsat (S2-02): testada e não aplicada

O plano previa ajustar o Landsat 5/7 à escala do Landsat 8 com os coeficientes de
Roy et al. (2016). Foi testado sobre a área de estudo, no Earth Engine, comparando
Landsat 7 e Landsat 8 nos mesmos píxeis em duas épocas secas:

| Época seca | Zona | MNDWI Landsat 8 | MNDWI Landsat 7 sem harmonizar | MNDWI Landsat 7 harmonizado |
|---|---|---|---|---|
| 2013 | água | 0,68 | 0,68 | 0,16 |
| 2014 | água | 0,75 | 0,64 | 0,15 |
| 2013 | terra | −0,55 | −0,51 | −0,53 |
| 2014 | terra | −0,54 | −0,50 | −0,52 |

**Leitura.** Em terra a harmonização quase não muda nada. Na água estraga o
sinal: os coeficientes somam um valor fixo às bandas de infravermelho, que na
água são quase zero, e o índice de água cai de cerca de 0,68 para 0,16. Num
projeto de cheias isso é inaceitável, por isso as composições foram descarregadas
**sem** harmonização (`harmonize_tm_etm_to_oli: false` no config). Esta decisão
deve constar na metodologia do relatório OAD."""),
    ("md", """\
## 2. Referência seca do radar

Para cada píxel, a mediana do VV e do VH de todos os meses secos (junho a
setembro). É a imagem do "normal sem cheia" com que cada mês é comparado."""),
    ("code", """\
ref_file = rasters.s1_dry_reference_file(cfg)
if not ref_file.exists():
    rasters.build_s1_dry_reference(cfg)          # alguns minutos, só da primeira vez
ref = rasters.read_bands(ref_file)
print(ref_file.relative_to(ROOT), f"({ref_file.stat().st_size / 1e6:.0f} MB)")
print("meses secos usados por píxel (mediana):", int(np.nanmedian(ref["n_months"][ref["n_months"] > 0])))

fig, axes = plt.subplots(1, 2, figsize=(13, 7))
for ax, band, lim in zip(axes, ["VV", "VH"], [(-25, 0), (-30, -5)]):
    im = ax.imshow(ref[band][::4, ::4], cmap="gray", vmin=lim[0], vmax=lim[1])
    ax.set_title(f"{band} na época seca (dB)"); ax.axis("off"); plt.colorbar(im, ax=ax, shrink=0.6)
plt.tight_layout()
"""),
    ("md", """\
## 3. Um mês de cheia contra um mês seco

Fevereiro de 2023 foi o mês mais chuvoso dos 20 anos. Compara-se com agosto de
2022. No painel ΔVV, o azul mostra onde o radar ficou mais escuro do que o normal
da época seca, ou seja, onde apareceu água."""),
    ("code", """\
WET, DRY = "2023-02", "2022-08"

def month_panels(month):
    s2 = rasters.read_bands(rasters.monthly_file(cfg, "sentinel2", month), ["green", "swir1"])
    mndwi = features.optical_indices(s2["green"], s2["green"], s2["green"], s2["green"], s2["swir1"], s2["swir1"])["mndwi"][::4, ::4]
    s1 = rasters.read_bands(rasters.monthly_file(cfg, "sentinel1", month), ["VV"])
    return mndwi, s1["VV"][::4, ::4], (s1["VV"] - ref["VV"])[::4, ::4]

fig, axes = plt.subplots(2, 3, figsize=(17, 12))
for row, month in zip(axes, [WET, DRY]):
    mndwi, vv, dvv = month_panels(month)
    for ax, data, title, kw in zip(row, [mndwi, vv, dvv], ["MNDWI Sentinel-2 (azul = água)", "VV Sentinel-1 (escuro = água)", "ΔVV (azul = mais escuro que o normal)"],
                                   [dict(cmap="RdBu", vmin=-0.6, vmax=0.6), dict(cmap="gray", vmin=-25, vmax=0), dict(cmap="RdBu_r", vmin=-6, vmax=6)]):
        im = ax.imshow(data, **kw); ax.set_title(f"{month} - {title}", fontsize=10); ax.axis("off")
        plt.colorbar(im, ax=ax, shrink=0.6)
plt.tight_layout()
plt.savefig(REPORTS / "20_cheia_vs_seco.png", dpi=110)
"""),
    ("md", """\
## 4. Um limiar simples de radar não chega: o que os dados mostram

Tentativa: contar, em cada mês, a área onde o VV caiu pelo menos 3 dB em relação
à época seca **e** ficou tão escuro como água (−16 dB ou menos), fora da água
permanente. Antes disso retira-se o desvio geral do mês (`s1_offset_vv`), medido
em terreno alto que nunca inunda."""),
    ("code", """\
change_file = drivers.table(cfg, "s1_change_monthly")
if not change_file.exists():
    rasters.s1_change_series(cfg).round(4).to_csv(change_file)       # alguns minutos, só da primeira vez
change = pd.read_csv(change_file, index_col=0)

fig, axes = plt.subplots(2, 1, figsize=(14, 7), sharex=True)
change["s1_new_water_km2"].plot(ax=axes[0], marker=".", ylabel="km²", title="Área escura e mais escura do que na época seca (limiar simples)")
change["s1_offset_vv"].plot(ax=axes[1], marker=".", color="grey", ylabel="dB", title="Desvio geral do mês em terreno alto (solo húmido = positivo, solo seco = negativo)")
plt.tight_layout(); plt.savefig(REPORTS / "20_radar_limiar_simples.png", dpi=110)
change.groupby(change.index.str[:4])[["s1_offset_vv", "s1_new_water_km2"]].median().round(2).T
"""),
    ("md", """\
**Leitura honesta deste gráfico.** Os valores mais altos não são as cheias de
2021, 2023 ou 2026: são 2015 e 2016. Há duas razões, e ambas importam para o
Modelo B:

1. **Seca de 2015–2016.** Solo nu, seco e liso também reflete muito pouco o
   radar. Numa planície de inundação ressequida, o radar fica escuro como se
   fosse água. Um limiar de VV sozinho confunde seca com cheia.
2. **Duas órbitas misturadas.** Cada composição mensal junta passagens de duas
   órbitas (órbitas relativas 145 e 72), com cerca de 10° de diferença no ângulo
   de incidência. Em 2015 só existe a órbita 145 (ângulo de 44,6°, contra cerca
   de 38° nos outros anos), e superfícies lisas ficam mais escuras a ângulos
   maiores. A receita da Semana 1 fixou a **direção** da órbita (ascendente), mas
   não a **órbita relativa**.

**Consequências práticas**

- A deteção de água precisa de várias features em conjunto (VV, VH, rácio,
  ótico, terreno) e de rótulos: é isso que o Modelo B faz. Um limiar fixo de ΔVV
  não deve ser usado como detetor nem como gatilho de alertas.
- A tabela de treino inclui o ângulo (`s1_angle`) e a mudança sem o desvio do mês
  (`dvv_rel`, `dvh_rel`), para o modelo poder compensar.
- Os meses de 2015 devem ser tratados com cuidado no treino do Modelo B (ângulo
  diferente de todos os outros anos).
- A correção de fundo seria descarregar de novo o Sentinel-1 só com a órbita
  145 (cerca de 6,7 GB de internet). É uma decisão da equipa; ver o resumo.

## 5. Exportar os índices de meses escolhidos (para o QGIS)

Escreve os rasters de índices dos meses da lista em
`data/interim/features/indices/<mês>/`. Acrescentar à lista os meses que se quer
ver no QGIS ou usar no workshop."""),
    ("code", """\
EXPORT_MONTHS = ["2023-02", "2022-08"]
for month in EXPORT_MONTHS:
    for file in rasters.export_month_features(cfg, month):
        print(file.relative_to(ROOT), f"({file.stat().st_size / 1e6:.0f} MB)")
"""),
]

# =============================================================================
NB["21_stack_estatico_e_grelha_comum"] = [
    header("21 - Stack estático e grelha comum",
           "S2-04 - reprojeção e reamostragem de todas as camadas para a grelha comum",
           "Junta todas as camadas fixas num só ficheiro alinhado e confirma que tudo está na mesma grelha",
           "Camadas estáticas (notebook 02) e todos os rasters mensais",
           "`data/interim/features/static_stack_marracuene_30m.tif`",
           """\
**Ideia simples.** Para um modelo aprender, o píxel da linha 100, coluna 200 tem de
ser o mesmo pedaço de terreno em todas as camadas. Na Semana 1 todos os rasters
já foram descarregados diretamente na grelha do projeto (EPSG:32736), por isso
aqui não é preciso reprojetar: basta **confirmar** o alinhamento e juntar as
camadas fixas.

A grelha de 10 m encaixa na de 30 m: cada píxel de 30 m contém exatamente 3 × 3
píxeis de 10 m."""),
    ("code", SETUP),
    ("md", "## 1. Construir o stack estático (30 m)"),
    ("code", """\
stack_file = rasters.build_static_stack(cfg)
stack = rasters.read_bands(stack_file)
masks = rasters.study_masks(cfg)
print(stack_file.relative_to(ROOT), f"({stack_file.stat().st_size / 1e6:.0f} MB)")

inside = masks["study"]
resumo = pd.DataFrame({name: {"minimo": np.nanmin(v[inside]), "mediana": np.nanmedian(v[inside]), "maximo": np.nanmax(v[inside]),
                              "sem_dados_pct": 100 * np.isnan(v[inside]).mean()} for name, v in stack.items()}).T
resumo
"""),
    ("md", """\
**Notas sobre as camadas**

- `hand`, `upstream_area_km2`, `twi`: vêm do MERIT Hydro, que não tem valores sobre
  o mar. Esses cerca de 21 % sem dados são mar aberto e ficam fora do **domínio de
  modelação** (zona de estudo com dados de terreno).
- `distance_to_river_m`: distância ao **canal real do Incomáti**. As linhas de rio
  do HydroSHEDS são desenhadas a cerca de 500 m e não seguem os meandros (vê-se
  bem no QGIS). O canal é por isso obtido do próprio terreno (células do MERIT
  Hydro que drenam mais de 10 000 km²) alargado à água que os satélites veem (JRC).
- `distance_to_water_m`: distância a qualquer água permanente em terra (rio,
  lagoas). `distance_to_stream_m`: distância às linhas do HydroSHEDS, que incluem
  os pequenos afluentes mas são aproximadas.
- `twi`: índice topográfico de humidade, ln(área a montante / declive). Valores
  altos = terreno plano que recebe muita água.
- `land_cover`: WorldCover de 10 m reduzido para 30 m pela classe mais frequente.
- `jrc_occurrence`: percentagem do tempo em que o píxel foi água (1984–2021).
  Serve para separar água permanente de cheia. **Não deve entrar como feature do
  Modelo A**: é praticamente a resposta que o modelo tem de aprender."""),
    ("code", """\
show = ["elevation", "slope", "hand", "twi", "distance_to_river_m", "distance_to_water_m", "land_cover", "jrc_occurrence"]
fig, axes = plt.subplots(2, 4, figsize=(18, 10))
for ax, name in zip(axes.flat, show):
    data = np.where(inside, stack[name], np.nan)
    lo, hi = np.nanpercentile(data, [2, 98])
    im = ax.imshow(data, cmap="tab20" if name == "land_cover" else "viridis", vmin=lo, vmax=hi)
    ax.set_title(name); ax.axis("off"); plt.colorbar(im, ax=ax, shrink=0.6)
plt.tight_layout(); plt.savefig(REPORTS / "21_stack_estatico.png", dpi=110)
"""),
    ("md", """\
## 2. Confirmar o alinhamento de todos os rasters

Todos os GeoTIFF do projeto em UTM têm de ter a mesma extensão e um píxel de 10
ou 30 m. A tabela final deve estar vazia."""),
    ("code", """\
import rasterio

grid30 = G.load_grid(cfg)
problems, checked = [], 0
for f in (ROOT / "data").rglob("*.tif"):
    if ".part" in f.name:
        continue
    with rasterio.open(f) as src:
        if src.crs is None or src.crs.to_epsg() != 32736:
            continue
        checked += 1
        if not (np.allclose(tuple(src.bounds), grid30.bounds) and src.res[0] in (10, 30)):
            problems.append({"ficheiro": str(f.relative_to(ROOT)), "pixel": src.res[0]})
print(f"{checked} rasters verificados, {len(problems)} fora da grelha")
pd.DataFrame(problems)
"""),
    ("md", "## 3. Domínio de modelação e blocos espaciais"),
    ("code", """\
frame = training.sampling_frame(cfg)
km2 = lambda mask: mask.sum() * 900 / 1e6
print(f"retângulo descarregado : {grid30.width * grid30.height * 900 / 1e6:,.0f} km²")
print(f"zona de estudo         : {km2(masks['study']):,.0f} km² (distrito + {cfg['aoi']['imagery_buffer_km']} km)")
print(f"domínio de modelação   : {km2(frame['domain']):,.0f} km² (zona de estudo com dados de terreno)")
print(f"  dentro do distrito   : {km2(frame['domain'] & frame['district']):,.0f} km²")
print(f"  água permanente      : {km2(frame['domain'] & frame['permanent']):,.0f} km² (ocorrência JRC >= {P['permanent_water_occurrence']} %)")
print(f"  terreno baixo        : {km2(frame['domain'] & frame['low']):,.0f} km² (HAND <= {P['low_hand_m']} m)")
print(f"blocos de {P['block_size_m'] / 1000:.0f} km           : {len(frame['fold_of'])}, repartidos por {P['n_folds']} grupos")

folds = np.full(frame["block"].shape, np.nan)
for block, fold in frame["fold_of"].items():
    folds[(frame["block"] == block) & frame["domain"]] = fold
plt.figure(figsize=(6, 7)); plt.imshow(folds, cmap="tab10"); plt.axis("off")
plt.title("Blocos espaciais (uma cor por grupo de validação)")
plt.savefig(REPORTS / "21_blocos_espaciais.png", dpi=110)
"""),
    ("md", """\
Os blocos servem para a validação da Semana 3: píxeis vizinhos são quase iguais,
por isso treino e teste nunca devem ter píxeis do mesmo bloco."""),
]

# =============================================================================
NB["22_features_de_precipitacao"] = [
    header("22 - Features de precipitação",
           "S2-05 - acumulados de 3/7/14/30 dias e anomalias (2006–2026)",
           "Transforma a chuva diária em indicadores de risco de cheia",
           "CHIRPS e IMERG diários (notebooks 03 e 04)",
           "`data/processed/series/rain_daily.csv` e `rain_monthly.csv`",
           """\
**Ideia simples.** Uma cheia raramente vem de um só dia de chuva: vem da chuva
acumulada em vários dias, sobre solo já molhado. Por isso calcula-se:

- **Acumulados** de 3, 7, 14 e 30 dias (`p3`, `p7`, `p14`, `p30`).
- **Anomalia em percentil**: compara o acumulado de hoje com o da mesma altura do
  ano em todos os anos. 50 = normal; acima de 90 = raro; perto de 100 = extremo.

Tudo é calculado para duas áreas: a **bacia** inteira (a água que chega pelo rio) e
o **distrito** (a chuva local)."""),
    ("code", SETUP),
    ("code", """\
daily, monthly = drivers.build_rain_tables(cfg)
print("diário :", daily.shape, "|", daily.index.min().date(), "a", daily["rain_basin"].last_valid_index().date(), "(CHIRPS)")
print("mensal :", monthly.shape)
daily.loc["2023-02-06":"2023-02-13", ["rain_basin", "p3_basin", "p7_basin", "p30_basin", "p7_pct_basin", "p30_pct_basin"]].round(1)
"""),
    ("md", "## 1. Os episódios de chuva mais fortes na bacia (acumulado de 7 dias)"),
    ("code", """\
p7 = daily["p7_basin"].dropna()
peaks = p7[(p7 == p7.rolling(31, center=True, min_periods=1).max())].nlargest(12)     # picos separados por 15 dias
eventos = pd.DataFrame({"chuva_7_dias_mm": peaks.round(0), "percentil": daily.loc[peaks.index, "p7_pct_basin"].round(1),
                        "chuva_30_dias_mm": daily.loc[peaks.index, "p30_basin"].round(0)})
eventos.index = eventos.index.strftime("%Y-%m-%d"); eventos.index.name = "fim do episódio"
eventos.to_csv(REPORTS / "22_maiores_episodios_de_chuva.csv")
eventos
"""),
    ("md", "## 2. Como ler os indicadores num ano"),
    ("code", """\
YEAR = "2023"
fig, axes = plt.subplots(3, 1, figsize=(14, 9), sharex=True)
daily.loc[YEAR, "rain_basin"].plot.area(ax=axes[0], color="tab:blue"); axes[0].set_ylabel("mm/dia"); axes[0].set_title(f"Chuva diária na bacia, {YEAR}")
daily.loc[YEAR, ["p7_basin", "p30_basin"]].plot(ax=axes[1]); axes[1].set_ylabel("mm"); axes[1].set_title("Acumulados de 7 e 30 dias")
daily.loc[YEAR, ["p7_pct_basin", "p30_pct_basin"]].plot(ax=axes[2]); axes[2].axhline(90, color="red", linestyle="--")
axes[2].set_ylabel("percentil"); axes[2].set_title("Anomalia (acima da linha vermelha = entre os 10 % mais chuvosos para a época)")
plt.tight_layout(); plt.savefig(REPORTS / "22_chuva_indicadores.png", dpi=110)
"""),
    ("md", """\
## 3. Chuva mensal: anos e meses fora do normal

Cada quadrado é um mês; a cor é o percentil da chuva desse mês face ao mesmo mês
nos outros anos (vermelho escuro = muito acima do normal)."""),
    ("code", """\
pct = monthly["rain_basin_pct"].copy()
pct.index = pd.MultiIndex.from_tuples([(m[:4], int(m[5:])) for m in pct.index], names=["ano", "mês"])
grid_pct = pct.unstack("mês")
fig, ax = plt.subplots(figsize=(12, 7))
im = ax.imshow(grid_pct.values, cmap="RdYlBu_r", vmin=0, vmax=100, aspect="auto")
ax.set_xticks(range(12), range(1, 13)); ax.set_yticks(range(len(grid_pct)), grid_pct.index)
ax.set_xlabel("mês"); ax.set_title("Percentil da chuva mensal na bacia (CHIRPS)"); plt.colorbar(im, ax=ax, label="percentil")
plt.tight_layout(); plt.savefig(REPORTS / "22_chuva_mensal_percentil.png", dpi=110)
monthly["rain_basin_mm"].nlargest(8).round(0).to_frame("chuva na bacia (mm)")
"""),
    ("md", """\
**Limites a ter em conta**

- O CHIRPS é publicado com cerca de um mês de atraso: o último mês pode estar em
  falta. Para o tempo quase real usa-se o IMERG, guardado ao lado (`imerg_*`).
- O percentil é calculado com os próprios 20 anos, incluindo o ano em causa. Com
  só 20 anos, "percentil 100" significa "o maior destes 20 anos", não um período
  de retorno."""),
]

# =============================================================================
NB["23_series_hidrometeorologicas"] = [
    header("23 - Séries de humidade do solo, escoamento e caudal",
           "S2-06 - ERA5-Land (2006–2026), SMAP (2015–2026) e GloFAS (2006–2026)",
           "Resume as grelhas diárias em séries diárias e mensais para a bacia e para o distrito",
           "ERA5-Land e SMAP (notebook 08), GloFAS (notebook 09)",
           "`data/processed/series/hydromet_daily.csv` e `hydromet_monthly.csv`",
           """\
**Ideia simples.** A mesma chuva causa mais cheia quando o solo já está saturado e
o rio já vai cheio. Estas séries medem essas condições:

| Coluna | O que é | Fonte |
|---|---|---|
| `sm_era5_l1`, `sm_era5_l2` | água no solo, camadas 0–7 cm e 7–28 cm | ERA5-Land |
| `smap_surface`, `smap_rootzone` | humidade do solo medida por satélite | SMAP L4 |
| `runoff_mm` | água que escorre à superfície | ERA5-Land |
| `evap_mm`, `temp_c` | evaporação e temperatura | ERA5-Land |
| `discharge_m3s`, `q_mean`, `q_max`, `q_pct` | caudal do Incomáti em Marracuene | GloFAS |

Cada variável do ERA5-Land e do SMAP tem duas colunas: `_basin` e `_district`."""),
    ("code", SETUP),
    ("code", """\
daily, monthly = drivers.build_hydromet_tables(cfg)
lat, lon = monthly.attrs["glofas_cell"]
print("diário :", daily.shape, "| mensal :", monthly.shape)
print(f"célula GloFAS usada para o caudal em Marracuene: lat {lat:.3f}, lon {lon:.3f}")

cobertura = pd.DataFrame({"primeiro": daily.apply(lambda s: s.first_valid_index()), "ultimo": daily.apply(lambda s: s.last_valid_index()),
                          "dias": daily.count()})
cobertura
"""),
    ("md", "## 1. As séries na bacia"),
    ("code", """\
fig, axes = plt.subplots(4, 1, figsize=(14, 12), sharex=True)
daily[["sm_era5_l1_basin", "smap_surface_basin"]].plot(ax=axes[0], linewidth=0.6); axes[0].set_ylabel("m³/m³"); axes[0].set_title("Humidade do solo à superfície (ERA5-Land e SMAP)")
monthly_dt = monthly.set_axis(pd.to_datetime(monthly.index))
monthly_dt["runoff_mm_basin"].plot(ax=axes[1], color="tab:brown"); axes[1].set_ylabel("mm/mês"); axes[1].set_title("Escoamento superficial")
daily["temp_c_district"].rolling(30).mean().plot(ax=axes[2], color="tab:red"); axes[2].set_ylabel("°C"); axes[2].set_title("Temperatura no distrito (média de 30 dias)")
daily["discharge_m3s"].plot(ax=axes[3], color="tab:blue", linewidth=0.6); axes[3].set_ylabel("m³/s"); axes[3].set_title("Caudal do Incomáti em Marracuene (GloFAS)")
plt.tight_layout(); plt.savefig(REPORTS / "23_series_hidromet.png", dpi=110)
"""),
    ("md", "## 2. Maiores caudais mensais"),
    ("code", """\
top = monthly.nlargest(10, "q_max")[["q_mean", "q_max", "q_pct", "q_provisional"]].round(1)
top.to_csv(REPORTS / "23_maiores_caudais.csv")
top
"""),
    ("md", """\
**Limites a ter em conta**

- O GloFAS é um **modelo** hidrológico global, não uma medição no rio. Serve para
  comparar meses e anos entre si; os valores absolutos podem diferir do caudal
  real, sobretudo num rio com barragens a montante como o Incomáti. Se a equipa
  conseguir dados de uma estação (ARA-Sul), devem ser usados para o verificar.
- `q_provisional = 1` marca meses do produto intermédio, que ainda vai ser revisto.
- ERA5-Land e SMAP têm células de cerca de 9–10 km: o distrito inteiro cabe em
  poucas células. Descrevem o estado geral do solo, não diferenças entre bairros."""),
]

# =============================================================================
NB["24_quantile_mapping_humidade_do_solo"] = [
    header("24 - Correção de viés da humidade do solo (quantile mapping)",
           "S2-07 - ajustar o ERA5-Land à escala do SMAP (calibração 2015–2021)",
           "Cria uma série de humidade do solo de 20 anos na escala do melhor sensor disponível",
           "`hydromet_daily.csv` (notebook 23)",
           "`data/processed/series/soil_moisture_calibrated_daily.csv` e `_monthly.csv`",
           """\
**O problema.** O ERA5-Land cobre os 20 anos, mas é um modelo. O SMAP é um
satélite feito para medir humidade do solo, mas só existe desde 2015. Os dois
sobem e descem juntos, só que em escalas diferentes.

**A solução (quantile mapping).** No período em que os dois existem, aprende-se
a correspondência entre eles: "quando o ERA5-Land está no seu valor dos 10 % mais
secos, o SMAP está em tal valor", e assim para todos os níveis. Depois aplica-se
essa tabela de conversão ao ERA5-Land dos 20 anos.

**Como se prova que funciona.** A conversão é aprendida só com 2015–2021 e
testada em 2022 em diante, anos que ela nunca viu."""),
    ("code", SETUP),
    ("code", """\
daily = drivers.read_table(cfg, "hydromet_daily")
cal = slice(P["calibration"]["start"], P["calibration"]["end"])
test = slice(str(int(P["calibration"]["end"][:4]) + 1), None)

# pares: série longa (ERA5-Land) -> série de referência (SMAP)
PAIRS = {"sm_cal": ("sm_era5_l1", "smap_surface"), "sm_root_cal": ("sm_era5_l2", "smap_rootzone")}

calibrated, rows = pd.DataFrame(index=daily.index), []
for out_name, (source, target) in PAIRS.items():
    for area in drivers.AREAS:
        s, t = daily[f"{source}_{area}"], daily[f"{target}_{area}"]
        qm = features.QuantileMapping().fit(s[cal], t[cal])
        calibrated[f"{out_name}_{area}"] = qm.transform(s.dropna()).reindex(daily.index)
        for period, label in [(cal, "calibração 2015-2021"), (test, "teste 2022+")]:
            for series_name, values in [("ERA5-Land original", s), ("ERA5-Land calibrado", calibrated[f"{out_name}_{area}"])]:
                rows.append({"variável": target, "área": area, "período": label, "série": series_name,
                             **features.agreement(t[period], values[period])})
resultado = pd.DataFrame(rows).set_index(["variável", "área", "período", "série"])
resultado.to_csv(REPORTS / "24_quantile_mapping_validacao.csv")
resultado
"""),
    ("md", """\
**Como ler a tabela.** `bias` é a diferença média em relação ao SMAP (ideal: 0),
`rmse` o erro típico e `r2` o quanto as duas séries se acompanham (ideal: 1). O
que conta são as linhas de **teste**: se o viés e o erro baixam nos anos que não
entraram na calibração, a correção é fiável. O `r2` quase não muda, e é esperado:
a correção ajusta a escala, não a ordem dos valores."""),
    ("code", """\
fig, axes = plt.subplots(1, 2, figsize=(15, 4.5), width_ratios=[2.3, 1])
window = slice("2020", "2024")
daily.loc[window, "smap_surface_basin"].plot(ax=axes[0], color="black", linewidth=0.8, label="SMAP (referência)")
daily.loc[window, "sm_era5_l1_basin"].plot(ax=axes[0], color="tab:orange", linewidth=0.6, label="ERA5-Land original")
calibrated.loc[window, "sm_cal_basin"].plot(ax=axes[0], color="tab:green", linewidth=0.6, label="ERA5-Land calibrado")
axes[0].axvline(pd.Timestamp(P["calibration"]["end"]), color="red", linestyle="--"); axes[0].legend(); axes[0].set_ylabel("m³/m³")
axes[0].set_title("Humidade do solo na bacia (à direita da linha vermelha: anos de teste)")
q = np.linspace(0.01, 0.99, 50)
ref_q = daily.loc[test, "smap_surface_basin"].quantile(q)
axes[1].plot(ref_q, daily.loc[test, "sm_era5_l1_basin"].quantile(q), "o", color="tab:orange", markersize=3, label="original")
axes[1].plot(ref_q, calibrated.loc[test, "sm_cal_basin"].quantile(q), "o", color="tab:green", markersize=3, label="calibrado")
axes[1].plot(ref_q, ref_q, color="black", linewidth=0.8); axes[1].legend()
axes[1].set_xlabel("SMAP"); axes[1].set_ylabel("ERA5-Land"); axes[1].set_title("Quantis nos anos de teste (ideal: sobre a linha)")
plt.tight_layout(); plt.savefig(REPORTS / "24_quantile_mapping.png", dpi=110)
"""),
    ("code", """\
calibrated.round(5).to_csv(drivers.table(cfg, "soil_moisture_calibrated_daily"))
monthly = features.month_index(calibrated.resample("MS").mean().where(calibrated.resample("MS").count() >= 25))
monthly.round(5).to_csv(drivers.table(cfg, "soil_moisture_calibrated_monthly"))
print("série calibrada:", calibrated["sm_cal_basin"].first_valid_index().date(), "a", calibrated["sm_cal_basin"].last_valid_index().date())
monthly.tail(3)
"""),
    ("md", """\
**Limites a ter em conta**

- A correção é feita sobre a **média da área** (bacia e distrito), não célula a
  célula: as duas grelhas não coincidem e o distrito cabe em poucas células.
- `sm_root_cal` liga a camada 7–28 cm do ERA5-Land à zona radicular do SMAP
  (0–100 cm). As profundidades não são as mesmas, por isso é uma aproximação;
  a coluna principal a usar nos modelos é `sm_cal` (superfície).
- A correção assume que a relação entre os dois produtos em 2015–2021 também
  valia em 2006–2014. Não há forma de o verificar com estes dados."""),
]

# =============================================================================
NB["25_analise_de_sobreposicao"] = [
    header("25 - Análise de sobreposição 2017–2021",
           "S2-08 - Landsat×S2, ERA5×SMAP, CHIRPS×IMERG, JRC×S1 (R² e viés)",
           "Prova de coerência: mede se fontes independentes dizem o mesmo quando existem ao mesmo tempo",
           "Todos os dados da Semana 1 e as séries dos notebooks 22–24",
           "`reports/semana_2/25_sobreposicao_resumo.csv` e figuras",
           """\
**Porque é importante.** O projeto junta satélites que começaram em anos
diferentes. Entre 2017 e 2021 todos existem ao mesmo tempo. Se nesse período
concordam entre si, pode-se confiar em usá-los em conjunto nos outros anos. Estes
números são o pilar 1 da confiabilidade e entram no relatório OAD.

| Medida | Significado | Ideal |
|---|---|---|
| R² | quanto as duas fontes sobem e descem juntas | 1 |
| viés (bias) | diferença média sistemática (segunda − primeira) | 0 |
| RMSE | erro típico entre as duas | 0 |
| AUC | capacidade de um valor contínuo separar duas classes | 1 (0,5 = acaso) |"""),
    ("code", SETUP + """
from sklearn.metrics import roc_auc_score
from ete import overlap

start, end = P["overlap"]["start"][:7], P["overlap"]["end"][:7]
months = [m for m in pd.period_range(start, end, freq="M").strftime("%Y-%m")]
summary = []
"""),
    ("md", """\
## 1. Landsat × Sentinel-2 (índices espectrais)

Mesmos píxeis, mesmo mês. O Sentinel-2 (10 m) é primeiro reduzido ao píxel de 30 m
do Landsat. Só entram píxeis vistos sem nuvens pelos dois."""),
    ("code", """\
ls2 = overlap.landsat_vs_sentinel2(cfg, months)
print(f"{len(ls2):,} pares de píxeis em {ls2['month'].nunique()} meses")
for name in ["ndwi", "mndwi", "ndvi", "ndmi"]:
    summary.append({"par": "Landsat × Sentinel-2", "variável": name.upper(), **features.agreement(ls2[f"{name}_landsat"], ls2[f"{name}_s2"])})
land = ls2[~ls2["often_water"]]
summary.append({"par": "Landsat × Sentinel-2", "variável": "NDMI (só em terra)", **features.agreement(land["ndmi_landsat"], land["ndmi_s2"])})

fig, axes = plt.subplots(1, 4, figsize=(18, 4.6))
for ax, name in zip(axes, ["ndwi", "mndwi", "ndvi", "ndmi"]):
    ax.hexbin(ls2[f"{name}_landsat"], ls2[f"{name}_s2"], gridsize=60, bins="log", cmap="viridis", extent=(-1, 1, -1, 1))
    ax.plot([-1, 1], [-1, 1], color="red", linewidth=0.8)
    stats = summary[["ndwi", "mndwi", "ndvi", "ndmi"].index(name)]
    ax.set_title(f"{name.upper()}  R²={stats['r2']:.2f}  viés={stats['bias']:+.3f}"); ax.set_xlabel("Landsat"); ax.set_ylabel("Sentinel-2")
plt.tight_layout(); plt.savefig(REPORTS / "25_landsat_vs_sentinel2.png", dpi=110)
pd.DataFrame(summary)
"""),
    ("md", """\
**Nota sobre o NDMI.** O NDMI divide pela soma de duas bandas de infravermelho.
Sobre a água as duas são quase zero, e dividir por quase zero dá valores
instáveis, diferentes de satélite para satélite. Por isso o NDMI é também
medido só em terra, onde é usado."""),
    ("md", "## 2. ERA5-Land × SMAP (humidade do solo, diária, bacia)"),
    ("code", """\
hyd = drivers.read_table(cfg, "hydromet_daily").loc[P["overlap"]["start"]:P["overlap"]["end"]]
cal = drivers.read_table(cfg, "soil_moisture_calibrated_daily").loc[P["overlap"]["start"]:P["overlap"]["end"]]
summary.append({"par": "SMAP × ERA5-Land original", "variável": "humidade superfície (bacia)", **features.agreement(hyd["smap_surface_basin"], hyd["sm_era5_l1_basin"])})
summary.append({"par": "SMAP × ERA5-Land calibrado", "variável": "humidade superfície (bacia)", **features.agreement(hyd["smap_surface_basin"], cal["sm_cal_basin"])})
pd.DataFrame(summary[-2:])
"""),
    ("md", """\
Nota: o período de sobreposição coincide com o período de calibração do notebook
24, por isso a linha "calibrado" é otimista. A prova independente da correção é o
teste em 2022+ desse notebook.

## 3. CHIRPS × IMERG (chuva na bacia)

Compara-se por mês e por períodos de 5 dias. Dia a dia não faz sentido: os dois
produtos não contam o "dia" à mesma hora."""),
    ("code", """\
rain = drivers.read_table(cfg, "rain_daily").loc[P["overlap"]["start"]:P["overlap"]["end"]]
five = rain[["rain_basin", "imerg_basin"]].resample("5D").sum()
month_sum = rain[["rain_basin", "imerg_basin"]].resample("MS").sum()
summary.append({"par": "CHIRPS × IMERG", "variável": "chuva mensal (bacia, mm)", **features.agreement(month_sum["rain_basin"], month_sum["imerg_basin"])})
summary.append({"par": "CHIRPS × IMERG", "variável": "chuva de 5 dias (bacia, mm)", **features.agreement(five["rain_basin"], five["imerg_basin"])})

fig, axes = plt.subplots(1, 2, figsize=(15, 4.5), width_ratios=[1, 2.2])
axes[0].scatter(month_sum["rain_basin"], month_sum["imerg_basin"], s=14); lim = month_sum.max().max()
axes[0].plot([0, lim], [0, lim], color="red", linewidth=0.8); axes[0].set_xlabel("CHIRPS (mm/mês)"); axes[0].set_ylabel("IMERG (mm/mês)")
month_sum.plot(ax=axes[1]); axes[1].set_ylabel("mm/mês"); axes[1].legend(["CHIRPS", "IMERG"])
plt.tight_layout(); plt.savefig(REPORTS / "25_chirps_vs_imerg.png", dpi=110)
pd.DataFrame(summary[-2:])
"""),
    ("md", """\
## 4. JRC × Sentinel-1 (água)

O JRC diz "água / não água" (a partir do Landsat); o Sentinel-1 dá um valor de
radar. Aqui não se calcula R²: mede-se se o radar separa as duas classes do JRC
(AUC) e quanto mais escura é a água. São dois sensores que veem a água de formas
completamente diferentes, por isso a concordância é uma prova forte."""),
    ("code", """\
js = overlap.jrc_vs_sentinel1(cfg, months)
print(f"{len(js):,} píxeis em {js['month'].nunique()} meses com JRC e Sentinel-1")
vv_water, vv_land = js.loc[js["jrc_water"], "vv"].median(), js.loc[~js["jrc_water"], "vv"].median()
summary.append({"par": "JRC × Sentinel-1", "variável": "VV separa água de não-água (AUC)", "n": len(js), "r2": np.nan,
                "bias": vv_water - vv_land, "rmse": np.nan, "slope": np.nan, "auc": roc_auc_score(js["jrc_water"], -js["vv"])})
flood = js[~js["permanent"]]
summary.append({"par": "JRC × Sentinel-1", "variável": "só fora da água permanente (AUC)", "n": len(flood), "r2": np.nan,
                "bias": flood.loc[flood["jrc_water"], "vv"].median() - flood.loc[~flood["jrc_water"], "vv"].median(),
                "rmse": np.nan, "slope": np.nan, "auc": roc_auc_score(flood["jrc_water"], -flood["vv"])})

fig, ax = plt.subplots(figsize=(8, 4))
bins = np.linspace(-30, 0, 61)
ax.hist(js.loc[~js["jrc_water"], "vv"], bins, alpha=0.6, label="JRC: não é água", density=True)
ax.hist(js.loc[js["jrc_water"], "vv"], bins, alpha=0.6, label="JRC: água", density=True)
ax.set_xlabel("VV Sentinel-1 (dB)"); ax.legend(); ax.set_title(f"Mediana: água {vv_water:.1f} dB, não-água {vv_land:.1f} dB")
plt.tight_layout(); plt.savefig(REPORTS / "25_jrc_vs_sentinel1.png", dpi=110)
pd.DataFrame(summary[-2:])
"""),
    ("md", """\
Na linha JRC × Sentinel-1, a coluna `bias` é a diferença de VV entre água e
não-água (em dB): quanto mais negativa, mais clara a separação.

## 5. Resumo para o relatório"""),
    ("code", """\
resumo = pd.DataFrame(summary).set_index(["par", "variável"])
resumo.round(3).to_csv(REPORTS / "25_sobreposicao_resumo.csv")
resumo
"""),
    ("md", """\
**Como interpretar**

- R² alto com viés pequeno: as duas fontes podem ser usadas em conjunto.
- R² alto com viés grande: concordam na forma mas não na escala; é o caso que o
  quantile mapping resolve.
- R² baixo: as fontes medem coisas diferentes ou uma delas tem ruído; essa
  variável deve ser usada com cuidado e o motivo explicado no relatório."""),
]

# =============================================================================
NB["26_rotulos"] = [
    header("26 - Rótulos (ground truth)",
           "S2-09 - JRC mensal (2006–2021) + EMS/UNOSAT + amostras digitalizadas no QGIS (2022–2026)",
           "Organiza as 'respostas certas' que ensinam e avaliam os modelos",
           "JRC mensal (notebook 10), séries de chuva e caudal, radar",
           "`data/raw/labels/manual/labels.gpkg` (modelo), `reports/semana_2/26_meses_candidatos.csv`",
           """\
**Ideia simples.** Um modelo aprende com exemplos em que a resposta é conhecida:
"este píxel, neste mês, era água". Essas respostas são os rótulos. O projeto usa
três fontes:

| Fonte | Período | Papel |
|---|---|---|
| JRC mensal (automático, do Landsat) | 2006–2021 | treino dos dois modelos |
| Mapas públicos Copernicus EMS / UNOSAT | por evento | confirmar eventos, validar |
| Polígonos desenhados no QGIS pela equipa | 2022–2026 | validação **independente** |

**Regra de ouro.** Um modelo nunca é avaliado com rótulos que ele próprio gerou.
Por isso os anos 2022–2026 só podem ser avaliados com rótulos desenhados à mão
ou com mapas EMS/UNOSAT."""),
    ("code", SETUP + """
import rasterio
frame = training.sampling_frame(cfg)
"""),
    ("md", """\
## 1. O que o JRC mensal consegue ver

Para cada mês: que parte do domínio foi observada e quanta água havia fora da
água permanente. Em meses de muitas nuvens o JRC vê pouco, mesmo havendo cheia."""),
    ("code", """\
rows = []
domain, permanent = frame["domain"], frame["permanent"]
for month in rasters.available_months(cfg, "jrc_monthly"):
    with rasterio.open(rasters.monthly_file(cfg, "jrc_monthly", month)) as src:
        water = src.read(1)
    observed = domain & ((water == 1) | (water == 2))
    rows.append({"month": month, "jrc_observed_fraction": observed.sum() / domain.sum(),
                 "jrc_flood_km2": (observed & (water == 2) & ~permanent).sum() * 900 / 1e6})
jrc = pd.DataFrame(rows).set_index("month")
jrc.round(4).to_csv(drivers.table(cfg, "jrc_monthly_summary"))

fig, axes = plt.subplots(2, 1, figsize=(14, 6), sharex=True)
jrc["jrc_observed_fraction"].plot(ax=axes[0], color="grey"); axes[0].set_ylabel("fração"); axes[0].set_title("Parte do domínio observada pelo JRC em cada mês")
jrc["jrc_flood_km2"].plot(ax=axes[1], color="tab:blue"); axes[1].set_ylabel("km²"); axes[1].set_title("Água fora da água permanente (JRC)")
plt.tight_layout(); plt.savefig(REPORTS / "26_jrc_cobertura_e_agua.png", dpi=110)
print(f"meses com menos de metade do domínio observado: {(jrc['jrc_observed_fraction'] < 0.5).sum()} de {len(jrc)}")
"""),
    ("md", """\
## 2. Meses candidatos a evento de cheia

Junta quatro sinais independentes. Um mês é candidato quando pelo menos um deles
é extremo:

- chuva mensal na bacia entre os 10 % de meses mais chuvosos dos 20 anos;
- caudal máximo do mês entre os 10 % maiores dos 20 anos;
- área de água JRC fora da água permanente entre os 10 % maiores (até 2021).

O radar **não** entra como sinal: o notebook 20 mostrou que um limiar simples de
VV confunde seca com cheia. A coluna `s1_new_water_km2` fica na tabela só como
informação."""),
    ("code", """\
drv = drivers.load_monthly_drivers(cfg)
change = pd.read_csv(drivers.table(cfg, "s1_change_monthly"), index_col=0)[["s1_new_water_km2", "s1_offset_vv"]]
cand = drv[["rain_basin_mm", "rain_basin_pct", "q_mean", "q_max", "q_pct"]].join(jrc).join(change)
# limiares sobre todos os meses dos 20 anos (não por mês do calendário): um agosto
# "muito chuvoso para agosto" continua a ter pouca chuva e não é candidato a cheia
signals = pd.DataFrame({
    "chuva": cand["rain_basin_mm"] >= cand["rain_basin_mm"].quantile(0.9),
    "caudal": cand["q_max"] >= cand["q_max"].quantile(0.9),
    "jrc": cand["jrc_flood_km2"] >= cand["jrc_flood_km2"].quantile(0.9),
})
cand["sinais"] = signals.apply(lambda r: "+".join(k for k, v in r.items() if v), axis=1)
cand["n_sinais"] = signals.sum(axis=1)
for key in ["landsat", "sentinel1", "sentinel2"]:
    cand[f"tem_{key}"] = cand.index.isin(rasters.available_months(cfg, key))
cand["rotulo_disponivel"] = np.where(cand.index <= "2021-12", "JRC mensal", "desenhar no QGIS / EMS")
candidatos = cand[cand["n_sinais"] >= 1].sort_values(["n_sinais", "rain_basin_mm"], ascending=False)
candidatos.round(2).to_csv(REPORTS / "26_meses_candidatos.csv")
print(f"{len(candidatos)} meses candidatos, {int((candidatos['n_sinais'] >= 2).sum())} com dois ou mais sinais")
candidatos[candidatos["n_sinais"] >= 2].round(1)
"""),
    ("md", """\
Esta lista é uma **sugestão calculada**, não uma lista de eventos confirmados.
Cada evento tem de ser confirmado numa fonte pública (Copernicus EMS Rapid
Mapping, UNOSAT, relatórios do INGD) e registado em
`data/raw/labels/flood_events/flood_events_catalogue.csv` com a referência.

## 3. Meses a digitalizar no QGIS (2022 em diante)

Depois de 2021 não há JRC mensal. Para avaliar os modelos nesses anos são
precisos polígonos desenhados à mão. A tabela indica os meses prioritários e que
imagens existem para os desenhar."""),
    ("code", """\
a_digitalizar = candidatos[candidatos.index >= "2022-01"][["sinais", "rain_basin_mm", "q_max", "s1_new_water_km2", "tem_sentinel1", "tem_sentinel2"]].round(1)
secos = cand[(cand.index >= "2022-01") & (cand["rain_basin_pct"] <= 30) & cand["tem_sentinel2"]].nsmallest(3, "rain_basin_mm")
print("Meses de cheia a digitalizar:"); display(a_digitalizar)
print("Meses secos de controlo (para ter exemplos de 'não é água' sem ambiguidade):", list(secos.index))
"""),
    ("md", """\
## 4. Ficheiro de rótulos manuais (`labels.gpkg`)

A célula cria o ficheiro vazio, com os campos certos, se ainda não existir.

**Como digitalizar (Agostinho)**

1. No QGIS, abrir a imagem do mês: o Sentinel-1 (`data/raw/radar/sentinel1/...`,
   banda VV, água a escuro) e, se não tiver nuvens, o Sentinel-2. Os rasters de
   índices exportados pelo notebook 20 também ajudam.
2. Abrir `data/raw/labels/manual/labels.gpkg`, camada `amostras`, e ativar a edição.
3. Desenhar polígonos **pequenos e seguros**: só onde a classe é evidente. Deixar
   as margens e as zonas duvidosas de fora.
4. Preencher os campos de cada polígono (tabela abaixo).
5. Desenhar as duas classes em cada mês, incluindo "não é água" em terreno baixo
   junto ao rio, que é o caso difícil.

| Campo | Valores |
|---|---|
| `class` | `water` ou `non_water` |
| `month` | mês da imagem, formato `AAAA-MM` |
| `event_id` | código do evento no catálogo, se houver |
| `source` | imagem usada (ex.: `S1 VV 2023-02`) |
| `author` | quem desenhou |
| `confidence` | `alta` ou `media` |
| `notes` | observações |

Os notebooks 27 e 28 leem este ficheiro sozinhos: quando houver polígonos, basta
voltar a corrê-los e as linhas entram na tabela com `label_source = manual`."""),
    ("code", """\
import geopandas as gpd

labels_file = config.path(cfg, "labels_manual", "labels.gpkg")
if not labels_file.exists():
    empty = gpd.GeoDataFrame({c: pd.Series(dtype="str") for c in ["class", "month", "event_id", "source", "author", "confidence", "notes"]},
                             geometry=gpd.GeoSeries([], crs=cfg["grid"]["crs"]))
    empty.to_file(labels_file, layer="amostras", driver="GPKG", geometry_type="Polygon")
    print("ficheiro vazio criado:", labels_file.relative_to(ROOT))
labels = gpd.read_file(labels_file, layer="amostras")
print(f"{len(labels)} polígonos em labels.gpkg")
labels.groupby(["month", "class"]).size().unstack(fill_value=0) if len(labels) else "ainda sem polígonos"
"""),
    ("md", """\
## 5. Rótulos de referência do Copernicus EMS (cheia de janeiro de 2026)

O serviço de emergência do Copernicus mapeou a cheia de janeiro de 2026
(ativação **EMSR857**). A área "AOI06 Palmeira" cobre 58 % do distrito de
Marracuene, com quatro mapas de delineação entre 17 e 24 de janeiro, feitos com
Sentinel-1, COSMO-SkyMed e ICEYE. Os dois últimos são satélites que este projeto
não usa: é uma referência **independente**, feita por um serviço operacional.

Os pacotes estão em `data/raw/labels/ems_unosat/EMSR857_AOI06_Palmeira/`. A
célula transforma-os em polígonos de duas classes:

- `water`: alagado em pelo menos uma das datas, encolhido 30 m para deixar de
  fora a margem incerta;
- `non_water`: dentro da área analisada pelo EMS e a mais de 100 m de qualquer
  cheia observada ou modelada.

A faixa entre as duas fica sem rótulo de propósito: o radar pode não ver água
debaixo de vegetação ou entre casas."""),
    ("code", """\
from ete import labels as ems

products = sorted((config.path(cfg, "ems_unosat", mkdir=False) / "EMSR857_AOI06_Palmeira").glob("EMSR857_AOI06_DEL_*/"))
if products:
    polygons = ems.ems_reference_polygons(cfg, products, month="2026-01", event_id="EMSR857")
    ems.write_ems_labels(cfg, polygons)
    display(polygons.assign(km2=polygons.area / 1e6).groupby("class")["km2"].agg(["count", "sum"]).round(1))

    district = G.load_aoi(cfg, "district").to_crs(cfg["grid"]["crs"])
    ax = district.boundary.plot(color="black", linewidth=0.8, figsize=(7, 8))
    polygons[polygons["class"] == "non_water"].plot(ax=ax, color="tab:orange", alpha=0.5)
    polygons[polygons["class"] == "water"].plot(ax=ax, color="tab:blue")
    ax.set_title("Referência EMSR857, janeiro de 2026 (azul = alagado, laranja = não alagado)"); ax.set_axis_off()
    plt.savefig(REPORTS / "26_ems_emsr857_referencia.png", dpi=110)
else:
    print("pacotes EMSR857 não encontrados: descarregar de https://rapidmapping.emergency.copernicus.eu/EMSR857")
"""),
    ("md", """\
**Limites desta referência**

- Vale para janeiro de 2026 e só para a parte do distrito dentro da área
  analisada pelo EMS (a planície do Incomáti; o sul do distrito fica de fora).
- "Alagado" significa alagado em alguma data entre 17 e 24 de janeiro. As
  composições mensais do projeto são a mediana do mês inteiro; metade das
  passagens de janeiro são anteriores à cheia. Esta referência mede portanto
  também o que se perde por trabalhar com composições mensais.
- A ativação de fevereiro de 2023 (**EMSR650**) cobre o distrito, mas os mapas de
  12 a 14 de fevereiro não mostram nenhuma área alagada dentro da zona de
  estudo: nessas datas a cheia estava a montante (Boane, Moamba). Não dá rótulos
  para Marracuene."""),
    ("md", """\
## 6. Estado dos rótulos

| Período | Rótulo | Estado |
|---|---|---|
| 2006–2021 | JRC mensal | pronto (192 meses) |
| janeiro de 2026 | Copernicus EMS (EMSR857) | pronto: referência independente |
| outros meses de 2022–2026 | polígonos QGIS | por fazer |

O teste independente dos modelos em 2022–2026 assenta, para já, num único
evento: janeiro de 2026. É o maior dos 20 anos, o que o torna um bom teste, mas
um evento só não chega para afirmar que o modelo funciona sempre."""),
]

# =============================================================================
QC_CELLS = [
    ("md", "## 2. Controlo de qualidade da tabela"),
    ("code", """\
print(f"{len(table):,} linhas x {table.shape[1]} colunas | {table['month'].nunique()} meses | ficheiro {out.stat().st_size / 1e6:.0f} MB")
display(table.groupby(["split", "stratum"], observed=True).size().unstack(fill_value=0))
resumo = table.groupby("split", observed=True).apply(lambda g: pd.Series({
    "linhas": len(g), "água_pct": 100 * g["label_water"].mean(), "cheia_pct": 100 * g["label_flood"].mean(),
    "cheia_pct_real": 100 * np.average(g["label_flood"], weights=g["weight"])}), include_groups=False)
resumo
"""),
    ("md", """\
`cheia_pct` é a proporção na amostra (as cheias foram sorteadas de propósito em
maior número). `cheia_pct_real` usa os pesos e dá a proporção verdadeira no
terreno: mostra quão raro é o que o modelo tem de aprender.

## 3. Dicionário de dados e valores em falta"""),
    ("code", """\
dicionario = training.data_dictionary(table)
dicionario.to_csv(out.with_name(out.stem + "_dicionario.csv"), index=False)
display(dicionario.groupby("grupo").agg(colunas=("coluna", "count"), em_falta_pct_medio=("em_falta_pct", "mean")).round(1))
dicionario[dicionario["em_falta_pct"] > 0].sort_values("em_falta_pct", ascending=False).head(15)
"""),
]

NB["27_dataset_camada1_historico"] = [
    header("27 - Dataset da Camada 1 (histórico, 30 m) para o Modelo A",
           "S2-10 - `train_historico.parquet`",
           "Monta a tabela de treino do modelo de suscetibilidade a cheias",
           "Stack estático (21), séries mensais (22–24), Landsat e JRC mensais, `labels.gpkg` (26)",
           "`data/processed/training/train_historico.parquet` + dicionário + metadados",
           """\
**Ideia simples.** Cada linha da tabela é **um píxel de 30 m num mês**, com:

- a resposta (rótulo): era água? era cheia?
- o terreno desse píxel (altitude, declive, HAND, distância ao rio...);
- as condições desse mês (chuva, humidade do solo, caudal) e do mês anterior;
- o que o Landsat viu (bandas e índices), quando viu.

**Porque é uma amostra.** O domínio tem 1,3 milhões de píxeis; vezes 192 meses
seriam 259 milhões de linhas. Em cada mês sorteiam-se até 4 000 píxeis, por
grupos (estratos), para garantir exemplos de todos os casos:

| Estrato | O que é | Por mês |
|---|---|---|
| `flood` | água fora da água permanente | até 1 500 |
| `permanent` | água permanente (rio, lagoas) | até 300 |
| `dry_low` | seco em terreno baixo (o caso difícil) | até 1 500 |
| `dry_other` | seco no resto | até 700 |

A coluna `weight` diz quantos píxeis reais cada linha representa. Píxeis que o
JRC não observou nesse mês (nuvens) nunca entram: não se inventa a resposta."""),
    ("code", SETUP),
    ("md", "## 1. Construir a tabela"),
    ("code", """\
table = training.build_historical(cfg)
out = config.path(cfg, "training", "train_historico.parquet")
print("escrito:", out.relative_to(ROOT))
table.head(3).T
"""),
    *QC_CELLS,
    ("md", "## 4. Os dados fazem sentido?"),
    ("code", """\
fig, axes = plt.subplots(1, 4, figsize=(18, 4))
for ax, col in zip(axes, ["hand", "distance_to_river_m", "mndwi", "rain_basin_mm"]):
    data = [table.loc[table["label_flood"] == v, col].dropna() for v in (0, 1)]
    ax.boxplot(data, tick_labels=["não cheia", "cheia"], showfliers=False); ax.set_title(col)
plt.suptitle("Valores por classe (caixa = metade central dos dados)"); plt.tight_layout()
plt.savefig(REPORTS / "27_features_por_classe.png", dpi=110)
table.groupby("label_flood")[["hand", "distance_to_river_m", "twi", "mndwi", "rain_basin_mm", "q_mean", "sm_cal_basin"]].median().round(2)
"""),
    ("md", """\
**O que se espera ver:** a água não permanente em terreno mais baixo (HAND menor),
mais perto do rio, com MNDWI mais alto.

**Atenção ao significado de `label_flood`.** É "água fora da água permanente".
Inclui as cheias, mas também a água sazonal normal (zonas húmidas e margens que
enchem todos os anos). Por isso há linhas `flood` em todos os meses, mesmo nos
secos. A chuva mediana das duas classes é igual por essa razão e porque a
amostra tira o mesmo número de linhas em cada mês. O que varia com a chuva é a
**área** de água, que se vê com os pesos:"""),
    ("code", """\
area = table.groupby("month", observed=True).apply(lambda g: pd.Series({
    "agua_nao_permanente_pct": 100 * np.average(g["label_flood"], weights=g["weight"]),
    "chuva_bacia_mm": g["rain_basin_mm"].iloc[0], "caudal_medio": g["q_mean"].iloc[0]}), include_groups=False)
fig, axes = plt.subplots(1, 2, figsize=(13, 4))
for ax, col in zip(axes, ["chuva_bacia_mm", "caudal_medio"]):
    ax.scatter(area[col], area["agua_nao_permanente_pct"], s=12); ax.set_xlabel(col); ax.set_ylabel("% do domínio observado com água não permanente")
plt.tight_layout(); plt.savefig(REPORTS / "27_area_de_agua_vs_chuva.png", dpi=110)
area.corr(method="spearman").round(2)
"""),
    ("md", """\
**Resultado medido: a correlação é praticamente zero** (cerca de −0,05). A área
de água do JRC não sobe e desce com a chuva nem com o caudal mês a mês. A água
de cheia aparece só em poucos meses, e quase sempre no mês da chuva forte ou no
seguinte (quando as nuvens já abriram):"""),
    ("code", """\
jrc = drivers.read_table(cfg, "jrc_monthly_summary")
drv = drivers.load_monthly_drivers(cfg)
top = jrc[jrc["jrc_observed_fraction"] >= 0.9].nlargest(8, "jrc_flood_km2").join(
    drv[["rain_basin_mm", "rain_basin_mm_lag1", "q_max"]]).rename(columns={"rain_basin_mm_lag1": "chuva_mes_anterior_mm"})
top.round(1)
"""),
    ("md", """\
**O que isto significa para o Modelo A**

- Em 16 anos de rótulos há apenas cerca de meia dúzia de meses com cheia
  claramente visível (2021, 2014, 2012, 2006). Eventos grandes como janeiro de
  2013 não aparecem, porque o JRC só observou 10 % da área nesse mês.
- Com tão poucos exemplos de cheia, o modelo vai aprender sobretudo **onde** a
  água costuma estar (terreno), e pouco sobre **quando** (chuva e caudal). O
  resultado realista é um mapa de suscetibilidade baseado no terreno, com uma
  componente dinâmica fraca.
- A parte "quando" do sistema de alertas deve apoiar-se nos gatilhos de chuva e
  caudal (notebooks 22 e 23) e no Modelo B, e não no Modelo A.

## Aviso importante para o Modelo A (Semana 3)

Esta tabela tem todas as colunas previstas no plano, mas **nem todas devem ser
usadas como features do Modelo A**:

- `jrc_occurrence`: é a frequência histórica do próprio rótulo. Usá-la seria
  dar a resposta ao modelo.
- Bandas e índices Landsat do **mesmo mês**: o rótulo JRC é calculado a partir
  dessas mesmas imagens Landsat. Com elas, o modelo aprende "MNDWI alto = água",
  o que é deteção e não suscetibilidade, e os resultados parecem ótimos sem o
  serem.

Para responder à pergunta do Modelo A ("que zonas inundam, e em que condições de
chuva e caudal?"), as features honestas são o **terreno** e as **condições
hidrometeorológicas**. As colunas Landsat ficam na tabela para análise e para
comparação, e a decisão final é tomada na Semana 3.

Outra limitação: a tabela só tem linhas com rótulo, ou seja, até 2021. O teste em
2022–2026 só existirá quando houver polígonos em `labels.gpkg`."""),
]

NB["28_dataset_camada2_recente"] = [
    header("28 - Dataset da Camada 2 (recente, 10 m) para o Modelo B",
           "S2-11 - `train_recente.parquet`",
           "Monta a tabela de treino do modelo de deteção de água atual",
           "Sentinel-1, Sentinel-2, Dynamic World, referência seca do radar (20), stack estático (21), JRC mensal",
           "`data/processed/training/train_recente.parquet` + dicionário + metadados",
           """\
**Ideia simples.** Cada linha é **um píxel de 10 m num mês**, com o que o radar
(Sentinel-1) e o ótico (Sentinel-2) viram, e a resposta: era água?

- O rótulo vem do JRC mensal (30 m). Para cada célula de 30 m sorteada usa-se o
  píxel de 10 m do **centro**, o menos afetado pelas margens da célula.
- O JRC é calculado com o Landsat, um satélite diferente dos dois Sentinel. O
  rótulo é por isso independente das features, o que não acontece no Modelo A.
- Linhas sem valor de Sentinel-1 são retiradas: o Modelo B é um modelo de radar,
  que tem de funcionar com nuvens. As colunas do Sentinel-2 podem estar vazias
  (nuvens, ou meses antes de 2017).
- Os meses vão de 2015 a 2021: quando existem ao mesmo tempo Sentinel-1 e JRC."""),
    ("code", SETUP),
    ("md", "## 1. Construir a tabela"),
    ("code", """\
table = training.build_recent(cfg)          # lê os rasters de 10 m mês a mês: demora vários minutos
out = config.path(cfg, "training", "train_recente.parquet")
print("escrito:", out.relative_to(ROOT))
table.head(3).T
"""),
    *QC_CELLS,
    ("md", "## 4. Os dados fazem sentido?"),
    ("code", """\
fig, axes = plt.subplots(1, 4, figsize=(18, 4))
for ax, col in zip(axes, ["vv", "dvv", "vv_vh_ratio", "s2_mndwi"]):
    data = [table.loc[table["label_water"] == v, col].dropna() for v in (0, 1)]
    ax.boxplot(data, tick_labels=["não é água", "água"], showfliers=False); ax.set_title(col)
plt.suptitle("Valores por classe (caixa = metade central dos dados)"); plt.tight_layout()
plt.savefig(REPORTS / "28_features_por_classe.png", dpi=110)

from sklearn.metrics import roc_auc_score
rows = []
for col in ["vv", "vh", "vv_p10", "vh_p10", "dvv", "dvv_p10", "dvh_p10", "vv_vh_ratio", "s2_mndwi", "s2_ndwi", "dw_water", "hand"]:
    ok = table[col].notna()
    auc = roc_auc_score(table.loc[ok, "label_water"], table.loc[ok, col], sample_weight=table.loc[ok, "weight"])
    rows.append({"feature": col, "linhas": int(ok.sum()), "AUC": max(auc, 1 - auc), "água tem valores": "mais altos" if auc > 0.5 else "mais baixos"})
pd.DataFrame(rows).sort_values("AUC", ascending=False)
"""),
    ("md", """\
**Como ler a tabela.** O AUC mede quão bem cada feature, sozinha, separa água de
não-água (0,5 = não ajuda, 1 = separa perfeitamente). É um primeiro olhar, não um
modelo: serve para confirmar que os dados têm sinal antes da Semana 3.

## 5. Teste independente: a cheia de janeiro de 2026 (Copernicus EMS)

As linhas com `label_source = ems` vêm do mapa oficial da cheia de janeiro de
2026 (notebook 26) e nunca entram no treino. A tabela compara, só nessas linhas,
a mediana do mês com o momento mais escuro do mês (`_p10`)."""),
    ("code", """\
ems = table[table["label_source"] == "ems"]
rows = []
for col in ["vv", "vh", "vv_p10", "vh_p10", "dvv_p10", "dvh_p10", "s2_mndwi", "dw_water", "hand"]:
    ok = ems[col].notna()
    if ok.sum() > 100:
        auc = roc_auc_score(ems.loc[ok, "label_water"], ems.loc[ok, col])
        rows.append({"feature": col, "linhas": int(ok.sum()), "AUC": max(auc, 1 - auc),
                     "mediana alagado": ems.loc[ok & (ems["label_water"] == 1), col].median(),
                     "mediana não alagado": ems.loc[ok & (ems["label_water"] == 0), col].median()})
teste = pd.DataFrame(rows).sort_values("AUC", ascending=False)
teste.round(3).to_csv(REPORTS / "28_teste_ems_janeiro_2026.csv", index=False)
teste
"""),
    ("md", """\
**Leitura.** A cheia durou poucos dias no fim do mês. A mediana mensal (`vv`,
`vh`) fica com a imagem de antes da cheia e quase não a vê; o percentil 10
(`vv_p10`, `vh_p10`) guarda o momento mais escuro e separa bem as duas classes.
Foi por isto que as bandas `_p10` foram acrescentadas ao Sentinel-1. O Modelo B
deve usá-las.

**Porque é que `dvv` separa mal.** A mudança em relação à época seca só é grande
onde a água é **nova**. A maior parte da água desta tabela (rio, lagoas, zonas
húmidas) também lá está na época seca, por isso quase não muda. O `dvv` é útil
para encontrar cheias, não para dizer se um píxel é água.

**Limites a ter em conta**

- O rótulo JRC diz "houve água em algum momento do mês"; as features são a
  mediana do mês. Numa cheia de poucos dias, a mediana pode não mostrar a água.
  É uma fonte de erro conhecida das composições mensais.
- `dw_water` (Dynamic World) é o resultado de outro modelo treinado com
  Sentinel-2. Pode ser usado como feature, nunca como rótulo.
- A tabela só tem linhas com rótulo, ou seja, até 2021. A validação com eventos
  de 2022–2026 depende dos polígonos em `labels.gpkg`."""),
]


def build():
    OUT.mkdir(parents=True, exist_ok=True)
    for name, cells in NB.items():
        target = OUT / f"{name}.ipynb"
        sources = [dedent(source).strip("\n") for _, source in cells]
        if target.exists() and [c.source for c in nbformat.read(target, 4).cells] == sources:
            print("sem alterações", target.name)
            continue
        nb = new_notebook()
        nb.metadata["kernelspec"] = {"display_name": "Python 3 (ete)", "language": "python", "name": "python3"}
        nb.metadata["language_info"] = {"name": "python"}
        for (kind, _), source in zip(cells, sources):
            nb.cells.append(new_markdown_cell(source) if kind == "md" else new_code_cell(source))
        nbformat.write(nb, target)
        print("escrito", f"notebooks/semana_2/{name}.ipynb")


if __name__ == "__main__":
    build()
