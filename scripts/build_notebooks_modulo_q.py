"""Gera os notebooks do Módulo Q (qualidade da água por troço, da fronteira à foz).

    .venv/bin/python scripts/build_notebooks_modulo_q.py

    notebooks/semana_2/29_modulo_Q_trocos_e_parametros.ipynb       (W1-10, W2-12, W2-13, W2-15)
    notebooks/semana_3/36_modulo_Q_normais_anomalias_tendencias.ipynb   (W3-05)
    notebooks/semana_3/37_modulo_Q_turbidez_esperada_e_validacao.ipynb  (W3-06, W3-07)
    notebooks/semana_3/38_ficha_de_evidencia_do_problema.ipynb          (W3-09)

Os notebooks não são editados à mão: muda-se este ficheiro e gera-se de novo. Um notebook cujo
texto não mudou não é reescrito, para não perder os resultados já corridos.
"""

from pathlib import Path
from textwrap import dedent

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

ROOT = Path(__file__).resolve().parents[1]


def setup(week: str) -> str:
    return f"""\
import json
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config" / "config.yaml").exists())
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ete import config, module_q
from ete import module_q_analysis as Q

cfg = config.load_config()
REPORTS = config.path(cfg, "reports", "{week}")       # figuras e tabelas para o relatório
pd.set_option("display.float_format", "{{:,.3f}}".format)
pd.set_option("display.max_colwidth", 90)
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
NB["semana_2/29_modulo_Q_trocos_e_parametros"] = [
    header("29 - Módulo Q: troços do rio, água pura e parâmetros",
           "W1-10 (troços e largura), W2-12 (máscara de água pura), W2-13 (parâmetros 2006–2026), W2-15 (dataset do Módulo Q)",
           "Divide o Incomáti em troços da fronteira à foz, define onde se mede a cor da água e junta 20 anos de medições por troço e mês",
           "Rede de rios HydroSHEDS, Dynamic World (frequência de água), Landsat 5/7/8/9 e Sentinel-2 no Earth Engine (`scripts/update_module_q_series.py`)",
           "`data/interim/water_quality/trocos_rio.gpkg`, `largura_por_troco.csv`, `data/processed/training/qualidade_trocos.parquet`",
           """\
O notebook 34 mediu a cor da água em quatro troços dentro do distrito. O plano pede
mais: **o rio todo em Moçambique, da fronteira (Ressano Garcia) à foz**, para se
poder comparar montante com jusante, e **20 anos** de dados.

Este notebook não descarrega imagens. Os valores por imagem são calculados no
Earth Engine e chegam como tabelas pequenas. Se ainda não existirem, correr antes:
`.venv/bin/python scripts/update_module_q_series.py`

| Passo | O que se faz |
|---|---|
| 1 | Traçar o rio e cortá-lo em troços |
| 2 | Marcar a água pura de cada troço e medir a largura do rio |
| 3 | Ler as medições por imagem (2006–2026) |
| 4 | Ver se os dois satélites concordam |
| 5 | Calcular os parâmetros e montar a tabela por troço e mês |"""),
    ("code", setup("semana_2")),
    ("md", """\
## 1. Os troços, da fronteira à foz

O curso principal é seguido na rede de rios, da foz para montante, escolhendo em
cada confluência o braço com maior área drenada, até sair de Moçambique. É cortado
em oito partes iguais (Q1 a Q8). A rede de rios acaba antes do estuário, por isso o
estuário entra como nono troço (Q9), com o canal já usado no notebook 34.

Os nomes vêm das vilas mais conhecidas junto de cada troço. Onde não há nenhuma,
fica a distância à fronteira."""),
    ("code", """\
sections = module_q.load_sections(cfg)
lines = module_q.load_sections(cfg, "linhas")
basin = config.path(cfg, "interim", mkdir=False).parent / "raw" / "aoi" / "incomati_basin.geojson"
import geopandas as gpd
fig, ax = plt.subplots(figsize=(13, 7))
gpd.read_file(basin).boundary.plot(ax=ax, color="#bdc3c7", linewidth=0.8)
gpd.read_file(ROOT / "data" / "raw" / "aoi" / "marracuene_district.geojson").boundary.plot(ax=ax, color="black", linewidth=1)
colours = plt.cm.viridis(np.linspace(0, 0.95, len(sections)))
for (_, row), colour in zip(lines.iterrows(), colours):
    gpd.GeoSeries([row.geometry]).plot(ax=ax, color=colour, linewidth=3, markersize=60)
    point = row.geometry.interpolate(0.5, normalized=True) if row.geometry.geom_type == "LineString" else row.geometry
    ax.annotate(row["nome"], (point.x, point.y), xytext=(6, 6), textcoords="offset points", fontsize=9, fontweight="bold")
ax.set_xlim(31.8, 33.2); ax.set_ylim(-26.0, -24.85); ax.set_title("Troços do Incomáti em Moçambique (a preto, o distrito de Marracuene)")
plt.tight_layout(); plt.savefig(REPORTS / "29_trocos_do_rio.png", dpi=110)
sections.drop(columns="geometry")
"""),
    ("md", """\
## 2. Água pura e largura do rio

**Onde há água.** O mapa Dynamic World (10 m) diz, para cada píxel, em que parte
das imagens limpas de 2019 a 2025 havia água. Ficam os píxeis com água em pelo
menos 60 % das imagens, num corredor de 2,5 km à volta da linha do rio. As massas
de água arredondadas (lagoas, charcas) saem: o rio é comprido e estreito.

O mapa de água permanente do JRC (30 m), previsto no plano, foi experimentado
primeiro e quase não vê o rio a montante, que tem 50 a 80 m de largura.

**Água pura.** Em cada imagem só contam os píxeis de água que estão a pelo menos
um píxel de tudo o que não é água nesse dia (margens, areia, plantas). Assim a
margem acompanha o nível do rio.

**Largura.** Área de água a dividir pelo comprimento do troço. A regra do plano:
onde o rio tem menos de três píxeis Landsat de largura (90 m), só se usa o
Sentinel-2."""),
    ("code", """\
width = pd.read_csv(config.path(cfg, "sections", "largura_por_troco.csv", mkdir=False)).set_index("troco")
width["satelites"] = np.where(width["largura_media_m"].fillna(1000) >= Q.LANDSAT_MIN_WIDTH_M, "Landsat (2006+) e Sentinel-2 (2017+)", "só Sentinel-2 (2017+)")
ax = width["largura_media_m"].plot.bar(figsize=(11, 3.6), color=np.where(width["largura_media_m"].fillna(1000) >= Q.LANDSAT_MIN_WIDTH_M, "#2e86c1", "#e59866"))
ax.axhline(Q.LANDSAT_MIN_WIDTH_M, color="black", linestyle=":"); ax.set_ylabel("largura média (m)"); ax.set_xlabel("")
ax.set_title("Largura média do rio por troço (linha: 90 m, três píxeis Landsat). O estuário não tem valor: é largo")
plt.tight_layout(); plt.savefig(REPORTS / "29_largura_por_troco.png", dpi=110)
width[["nome", "comprimento_km", "largura_media_m", "area_pura_sentinel2_ha", "area_pura_landsat_ha", "satelites"]]
"""),
    ("md", """\
**Leitura.** Da fronteira até perto de Manhiça o rio é estreito de mais para o
Landsat: aí a série tem só os anos do Sentinel-2 (2017 em diante). Os 20 anos
completos existem nos três troços de jusante.

Isto é um limite real dos dados, e está previsto no plano. Não se preenche o
período em falta com estimativas.

A máscara é automática. Deve ser vista no QGIS por quem conhece o rio (camadas
`agua_permanente`, `agua_pura_sentinel2` e `agua_pura_landsat` do ficheiro
`trocos_rio.gpkg`).

## 3. As medições por imagem"""),
    ("code", """\
images = Q.load_images(cfg)
measured = images.dropna(subset=["ndti"])
names = {"landsat57": "Landsat 5/7", "landsat89": "Landsat 8/9", "sentinel2": "Sentinel-2"}
per_year = measured.assign(ano=measured["date"].dt.year, satelite=measured["sensor"].map(names)).groupby(["ano", "satelite"])["date"].nunique().unstack(fill_value=0)
ax = per_year.plot.bar(stacked=True, figsize=(13, 3.6), color=["#7f8c8d", "#34495e", "#2980b9"], ylabel="dias com medição")
ax.set_title("Dias com pelo menos um troço medido, por ano e satélite"); ax.set_xlabel("")
plt.tight_layout(); plt.savefig(REPORTS / "29_dias_com_medicao.png", dpi=110)
table = measured.assign(satelite=measured["sensor"].map(names)).groupby(["troco", "satelite"]).agg(dias=("date", "nunique"), pixeis_tipicos=("pixeis", "median")).unstack("satelite")
table.round(0)
"""),
    ("md", """\
**Leitura.** `pixeis_tipicos` é o número de píxeis de água pura numa imagem típica.
No Landsat, a montante, são poucas dezenas ou nenhum: confirma a regra da largura.

## 4. Os dois satélites concordam?

No mesmo dia e no mesmo troço, o Sentinel-2 e o Landsat 8/9 deviam dar o mesmo
valor. São instrumentos e correções atmosféricas independentes."""),
    ("code", """\
agreement = Q.cross_sensor(images)
agreement.round(3).to_csv(REPORTS / "29_concordancia_entre_satelites.csv")
display(agreement.round(2))
Q.section_reliability(images).to_frame("fiabilidade").T
"""),
    ("md", """\
**Como ler**

- `r_ndti`: correlação do índice de cor. Perto de 1 = os satélites concordam.
- `fator_tipico_turbidez`: por quanto diferem tipicamente as duas estimativas de
  turbidez. 1,5 quer dizer que uma pode ser 50 % maior do que a outra.

**Leitura.** No conjunto, o índice de cor (NDTI) é repetível. A turbidez em FNU
concorda menos: serve como ordem de grandeza, não como medição.

**Os troços não são todos iguais.** Onde a correlação do índice fica abaixo de
0,7, ou há menos de 15 pares, o troço fica marcado com **fiabilidade reduzida**
(tabela seguinte): os seus valores são mostrados, mas não dão origem a alertas.
A causa mais provável é a máscara de água apanhar coisas diferentes do rio
(bancos de areia, charcas), e é aí que a revisão no QGIS deve começar.

## 5. Parâmetros e tabela por troço e mês

| Parâmetro do plano | Como é calculado aqui | O que vale |
|---|---|---|
| Índice de cor (NDTI) | (vermelho − verde) / (vermelho + verde) | **base de todas as análises**; repetível entre satélites |
| Turbidez (FNU) | Dogliotti et al. (2015), banda do vermelho | estimativa sem calibração local |
| Sólidos suspensos (mg/L) | Nechad et al. (2010), banda do vermelho | estimativa; a mesma informação da turbidez |
| Transparência (Secchi, m) | relação ajustada às medições globais GLORIA | estimativa larga, até haver medições no rio |
| Clorofila-a (NDCI) | (B5 − B4) / (B5 + B4), só Sentinel-2 | **não reportada como clorofila**: no Incomáti segue o sedimento |
| Vegetação sobre a água | parte da água permanente com NDVI acima de 0,4 | fiável nos troços largos; a montante mistura a margem |
| Temperatura da água | banda térmica do Landsat (píxel de 100 m) | só nos troços com mais de 300 m de largura |

Os coeficientes dos algoritmos foram conferidos nos ficheiros distribuídos com o
ACOLITE. A versão de Dogliotti com a banda do infravermelho próximo foi rejeitada
no notebook 35 (os satélites não concordam); a do vermelho concorda melhor."""),
    ("code", """\
data = Q.monthly_dataset(cfg)
print(f"qualidade_trocos.parquet: {len(data):,} linhas = {data['troco'].nunique()} troços x {data['month'].nunique()} meses ({data['month'].min()} a {data['month'].max()})")
summary = data.groupby(["troco", "nome"]).agg(fonte=("fonte", lambda s: s[s != ""].mode().iloc[0] if (s != "").any() else ""), primeiro_mes=("month", lambda m: m[data.loc[m.index, "ndti"].notna()].min()),
                                               meses_com_cor=("ndti", "count"), meses_com_vegetacao=("vegetacao", "count"), meses_com_temperatura=("temp_c", "count"),
                                               turbidez_fnu_mediana=("turbidez_fnu", "median"), tss_mg_l_mediana=("tss_mg_l", "median"), secchi_m_mediana=("secchi_m", "median"))
summary["meses_sem_medicao_%"] = 100 * (1 - summary["meses_com_cor"] / data.groupby(["troco", "nome"])["month"].apply(lambda m: (m >= summary.loc[m.name, "primeiro_mes"]).sum()))
summary.round(1).to_csv(REPORTS / "29_resumo_do_dataset.csv")
summary.round(1)
"""),
    ("code", """\
fig, axes = plt.subplots(3, 3, figsize=(17, 9), sharex=True)
for ax, (section, group) in zip(axes.ravel(), data.groupby("troco")):
    series = group.set_index(pd.to_datetime(group["month"]))
    series["ndti_landsat"].plot(ax=ax, style=".", color="#34495e", markersize=4, label="Landsat")
    series["ndti_s2"].plot(ax=ax, style=".", color="#2980b9", markersize=4, label="Sentinel-2")
    ax.set_title(group["nome"].iloc[0], fontsize=10); ax.set_xlabel("")
axes[0, 0].legend(); fig.supylabel("NDTI (mais alto = mais turva)")
plt.suptitle("Índice de cor por troço e mês, 2006–2026"); plt.tight_layout(); plt.savefig(REPORTS / "29_series_por_troco.png", dpi=110)
"""),
    ("md", """\
**Leitura.** Cada ponto é a mediana das imagens limpas de um mês. Os meses sem
ponto não tiveram imagem limpa com água pura suficiente: ficam vazios (regra de
ouro do projecto, nunca inventar dados). A época das chuvas tem mais falhas,
porque há mais nuvens.

## Dicionário do ficheiro `qualidade_trocos.parquet`

| Coluna | Significado |
|---|---|
| `troco`, `nome`, `month` | troço (Q1 fronteira … Q9 foz) e mês |
| `ndti`, `turbidez_fnu`, `tss_mg_l`, `secchi_m`, `vegetacao` | valor do mês: do Landsat nos troços largos, do Sentinel-2 nos estreitos |
| `fonte` | de que satélite veio esse valor |
| `fiabilidade` | `boa` ou `reduzida`: os dois satélites concordam neste troço? |
| `…_landsat`, `…_s2` | o mesmo, separado por satélite |
| `ndci` | índice do Sentinel-2 (não é clorofila neste rio) |
| `temp_c` | temperatura da água, só troços largos |
| `n_imagens_landsat`, `n_imagens_s2` | imagens usadas no mês |
| `chuva_mm`, `caudal_m3s` (e `_m1`, `_m2`) | chuva na bacia e caudal em Marracuene no mês e nos dois anteriores |
| `ano`, `mes`, `epoca` | metadados de tempo |

## O que falta (para a equipa)

- **ACOLITE (tarefas W1-11 e W2-14).** A correção atmosférica própria para água não
  foi feita neste computador: exige descarregar imagens de nível 1 (cerca de 1 GB
  cada). Em sua vez, a repetibilidade foi testada com dois satélites (secção 4) e
  as fórmulas com o GLORIA (notebook 37).
- **Medições com disco de Secchi (W2-16, W3-08).** A equipa decidiu, a 12 de
  Outubro de 2026, não fazer medições no local nesta fase. O Módulo Q fica, por
  isso, como um indicador relativo (a cor da água face ao seu normal), sem
  valores absolutos validados. O protocolo fica guardado em
  `docs/protocolo_de_campo_qualidade_da_agua.md` para uma fase futura."""),
]

# =============================================================================
NB["semana_3/36_modulo_Q_normais_anomalias_tendencias"] = [
    header("36 - Módulo Q: o normal de cada troço, anomalias e tendências",
           "W3-05",
           "Calcula o valor normal de cada troço em cada mês do ano, aponta os meses fora do normal e testa se há tendência em 20 anos",
           "`data/processed/training/qualidade_trocos.parquet` (notebook 29)",
           "Tabelas e figuras em `reports/semana_3/` (prefixo 36)",
           """\
| Pergunta | Método |
|---|---|
| Qual é o normal de cada troço em cada mês? | mediana e percentis dos anos com dados |
| Que meses fugiram ao normal? | comparação com o normal; e Isolation Forest para meses invulgares |
| A água está a ficar mais turva ao longo dos anos? | teste de Mann-Kendall sazonal e inclinação de Sen |

Todas as análises usam o **índice de cor (NDTI)**, que é o valor mais repetível.
A turbidez em FNU é só uma tradução aproximada desse índice."""),
    ("code", setup("semana_3")),
    ("md", "## 1. O normal de cada troço em cada mês do ano"),
    ("code", """\
data, skill, _ = Q.expected_turbidity(cfg, Q.monthly_dataset(cfg))
normal = Q.climatology(data, "ndti")
normal.round(4).to_csv(REPORTS / "36_normais_por_troco_e_mes.csv")
grid = normal["mediana"].unstack("mes").reindex(sorted(data["troco"].unique()))
names = data.drop_duplicates("troco").set_index("troco")["nome"]
fig, ax = plt.subplots(figsize=(12, 4.6))
im = ax.imshow(grid.values, cmap="YlOrBr", aspect="auto")
ax.set_xticks(range(12), ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"]); ax.set_yticks(range(len(grid)), [names[t] for t in grid.index])
for (i, j), v in np.ndenumerate(grid.values):
    if np.isfinite(v):
        ax.text(j, i, f"{v:.2f}", ha="center", va="center", fontsize=8)
plt.colorbar(im, ax=ax, label="NDTI normal (mais alto = mais turva)"); ax.set_title("Valor normal do índice de cor, por troço e mês do ano")
plt.tight_layout(); plt.savefig(REPORTS / "36_normais.png", dpi=110)
normal.groupby("troco")["anos"].agg(["min", "max"]).rename(columns={"min": "anos_com_dados_min", "max": "anos_com_dados_max"}).T
"""),
    ("md", """\
**Leitura.** Cada linha é um troço, da fronteira (em cima) à foz (em baixo). Lê-se
em duas direções: ao longo do ano (a água é mais turva na época das chuvas) e ao
longo do rio (onde é mais turva).

Os troços estreitos têm menos anos (só Sentinel-2). Um mês do ano com menos de
quatro anos de dados fica sem valor normal.

## 2. Meses fora do normal

Um mês é **elevado** se ficar acima de três quartos dos mesmos meses dos outros
anos, e **muito elevado** se ficar acima de nove décimos."""),
    ("code", """\
anomaly = Q.anomalies(data, "ndti")
anomaly.round(4).to_csv(REPORTS / "36_anomalias.csv", index=False)
order = ["normal", "elevada", "muito elevada"]
counts = anomaly[anomaly["classe"] != "sem dados"].groupby(["ano", "classe"]).size().unstack(fill_value=0).reindex(columns=order, fill_value=0)
fig, axes = plt.subplots(1, 2, figsize=(17, 4.2), gridspec_kw={"width_ratios": [1.5, 1]})
counts.plot.bar(stacked=True, ax=axes[0], color=["#d5dbdb", "#e59866", "#a04000"]); axes[0].set_ylabel("meses x troços"); axes[0].set_xlabel("")
axes[0].set_title("Meses por classe em cada ano (todos os troços)")
share = anomaly[anomaly["classe"] != "sem dados"].assign(alto=lambda d: d["classe"] != "normal").groupby("ano")["alto"].mean()
(100 * share).plot(ax=axes[1], marker="o", color="#a04000"); axes[1].axhline(25, color="grey", linestyle=":"); axes[1].set_ylabel("% de meses acima do normal"); axes[1].set_xlabel("")
axes[1].set_title("Parte dos meses acima do normal (25 % = o esperado)")
plt.tight_layout(); plt.savefig(REPORTS / "36_anomalias_por_ano.png", dpi=110)
worst = anomaly[anomaly["classe"] == "muito elevada"].sort_values("anomalia_padronizada", ascending=False).head(15)
worst[["nome", "month", "ndti", "mediana", "anomalia", "anomalia_padronizada"]]
"""),
    ("md", """\
**Leitura.** O gráfico da direita mostra, ano a ano, que parte dos meses medidos
ficou acima do normal. A tabela mostra os quinze meses mais fora do normal de
todo o registo.

**Cuidado ao comparar anos.** Até 2013 os valores dos troços largos vêm do
Landsat 5 e 7; depois, do Landsat 8 e 9. As bandas não são iguais, e em 2012 só
havia o Landsat 7, com faixas sem dados. Um ano antigo "muito turvo" pode ser em
parte efeito do satélite. As comparações seguras são dentro da mesma era, e é
por isso que a ficha de evidência (notebook 38) só usa os anos desde 2013.

## 3. Meses invulgares (Isolation Forest)

O método anterior olha para uma coisa de cada vez. O Isolation Forest olha para
várias em conjunto (a cor, as plantas sobre a água e, onde existe, o desvio face
ao que a chuva e o caudal explicam) e aponta os 5 % de meses mais invulgares de
cada troço. Um mês apontado é um convite a ir ver, não um diagnóstico."""),
    ("code", """\
unusual = Q.isolation_forest(cfg, data)
unusual.round(4).to_csv(REPORTS / "36_meses_invulgares.csv", index=False)
flagged = unusual[unusual["invulgar"]].merge(data[["troco", "month", "nome", "caudal_m3s", "chuva_mm"]], on=["troco", "month"])
per_year = flagged.assign(ano=flagged["month"].str[:4]).groupby("ano").size()
ax = per_year.plot.bar(figsize=(12, 3.2), color="#8e44ad", ylabel="meses invulgares"); ax.set_xlabel(""); ax.set_title("Meses apontados como invulgares, por ano (todos os troços)")
plt.tight_layout(); plt.savefig(REPORTS / "36_meses_invulgares.png", dpi=110)
print(f"{len(flagged)} meses apontados em {len(unusual)} medidos")
flagged.sort_values("pontuacao").head(15)[["nome", "month", "anomalia_ndti", "anomalia_vegetacao", "caudal_m3s", "chuva_mm", "pontuacao"]]
"""),
    ("md", """\
## 4. Tendências em 20 anos

O teste de Mann-Kendall sazonal compara cada mês do ano só consigo mesmo ao longo
dos anos, para o ciclo anual não criar uma tendência falsa. A inclinação de Sen dá
a variação por década.

**O cuidado principal.** Em 2013 os satélites mudaram (Landsat 5/7 para Landsat
8/9), e as bandas não são exatamente iguais. Uma tendência que aparece no registo
completo mas não aparece dentro da era Landsat 8/9 pode ser só essa mudança. Por
isso o teste é feito três vezes: registo completo e cada era. Só conta como
**confirmada** a tendência que também se vê, no mesmo sentido, de 2013 em diante."""),
    ("code", """\
trend = Q.trends(data)
trend.round(5).to_csv(REPORTS / "36_tendencias.csv", index=False)
full = trend[trend["periodo"] == "registo completo"]
pivot = full.pivot(index="nome", columns="parametro", values="leitura").reindex([names[t] for t in sorted(data["troco"].unique())]).fillna("sem tendência")
display(pivot)
shown = full[full["parametro"] == "ndti"].set_index("nome").reindex(pivot.index)
colours = np.where(shown["leitura"].fillna("").str.startswith("confirmada") | shown["leitura"].fillna("").str.startswith("um só"), "#a04000", "#bdc3c7")
ax = shown["inclinacao_por_decada"].plot.barh(figsize=(10, 4), color=colours); ax.invert_yaxis(); ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("variação do NDTI por década (positivo = mais turva)"); ax.set_ylabel("")
ax.set_title("Tendência do índice de cor (a cor forte: tendência que passa no teste)")
plt.tight_layout(); plt.savefig(REPORTS / "36_tendencias.png", dpi=110)
trend[trend["tendencia"].isin(["sobe", "desce"])][["nome", "parametro", "periodo", "tendencia", "inclinacao_por_decada", "p", "n", "leitura"]]
"""),
    ("md", """\
**Como ler**

- `tendencia`: sobe, desce ou sem tendência (ao nível de 5 %).
- `leitura`: "confirmada" quando a era Landsat 8/9 mostra o mesmo; "não confirmada"
  quando só aparece no registo completo; "um só satélite" nos troços estreitos,
  onde a série é só do Sentinel-2 e por isso mais curta (desde 2017).

**O que se pode dizer.** Só as tendências confirmadas. As dos troços estreitos
valem para nove anos (2017 a 2026), não para vinte. Esses nove anos começam em
anos de seca (2017 a 2019) e acabam em anos de muita água e numa grande cheia
(2026). É o que se espera ver: mais caudal, água mais turva e menos plantas
paradas sobre a água. Devem ser lidas como "os últimos anos foram mais turvos do
que os primeiros", não como uma mudança permanente do rio. Nos troços com
fiabilidade reduzida, nem isso.

**O que o teste não corrige.** Meses seguidos parecem-se uns com os outros, o que
torna o teste um pouco otimista. E a temperatura vem de duas bandas térmicas
diferentes antes e depois de 2013.

## O que este notebook entrega

- `36_normais_por_troco_e_mes.csv`: o normal usado pela plataforma para dizer
  "normal / elevada / muito elevada".
- `36_anomalias.csv` e `36_meses_invulgares.csv`: os meses a olhar.
- `36_tendencias.csv`: tendências com a sua leitura."""),
]

# =============================================================================
NB["semana_3/37_modulo_Q_turbidez_esperada_e_validacao"] = [
    header("37 - Módulo Q: turbidez esperada, montante e jusante, e validação",
           "W3-06 (turbidez esperada e comparação montante/jusante), W3-07 (validação)",
           "Testa se a chuva e o caudal explicam a cor da água em cada troço, compara a fronteira com Marracuene, e valida as fórmulas com medições reais (GLORIA)",
           "`qualidade_trocos.parquet`, medições por imagem, histórico de caudal e chuva, GLORIA (PANGAEA), lista de estações do GEMStat",
           "`models/secchi_gloria.json`, tabelas e figuras em `reports/semana_3/` (prefixo 37)",
           """\
A ideia do plano: se soubermos a turbidez que a chuva e o caudal explicam, o que
sobra pode ser outra coisa (uma descarga, obras no rio). Este notebook testa se
essa ideia funciona aqui, troço a troço, e diz onde funciona e onde não."""),
    ("code", setup("semana_3")),
    ("md", """\
## 1. A chuva e o caudal explicam a cor da água?

Primeira tentativa, a do plano: mês a mês. **Não funcionou**: com uma ou duas
imagens por mês, o valor do mês não se explica pela chuva do mês (o modelo ficou
pior do que usar só a época do ano, em todos os troços).

Segunda tentativa, a que fica: **imagem a imagem**. Cada imagem recebe o caudal
do dia e dos dias anteriores, a chuva dos últimos 3, 7 e 30 dias, a época do ano
e a maré à hora do satélite. Um modelo por troço; cada ano é previsto por um
modelo que nunca o viu."""),
    ("code", """\
data, skill, images = Q.expected_turbidity(cfg, Q.monthly_dataset(cfg))
skill.round(3).to_csv(REPORTS / "37_turbidez_esperada_desempenho.csv")
ax = skill[["r2_chuva_caudal_mare", "r2_epoca_do_ano"]].set_index(skill["nome"]).plot.barh(figsize=(11, 4.4), color=["#1e8449", "#bdc3c7"])
ax.invert_yaxis(); ax.axvline(Q.MIN_SKILL, color="black", linestyle=":"); ax.axvline(0, color="black", linewidth=0.8); ax.set_ylabel("")
ax.set_xlabel("R²: parte da variação explicada em anos não vistos (linha pontilhada: mínimo para o modelo contar)")
ax.legend(["chuva, caudal e maré", "só a época do ano"]); plt.tight_layout(); plt.savefig(REPORTS / "37_turbidez_esperada.png", dpi=110)
skill.round(2)
"""),
    ("md", """\
**Como ler.** `r2_chuva_caudal_mare` é a parte da variação da cor que o modelo
explica em anos que não viu. Abaixo de 0,2 o modelo explica pouco de mais, e dizer
"esta turbidez não se explica pela chuva" não teria significado: nesses troços a
plataforma **não** dá esse aviso.

**Leitura.** Só perto da foz o modelo explica uma parte útil da variação. No resto
do rio fica perto de zero: com estes dados, a ideia "turbidez esperada pela
chuva e pelo caudal" não se sustenta troço a troço.

**Porque falha na maior parte dos troços** (hipóteses, por ordem de probabilidade):

1. O caudal usado é o de Marracuene, de um modelo global. A montante, o caudal
   real depende das barragens e de afluentes que esse número não mostra.
2. Nos troços estreitos há poucas imagens e só desde 2017.
3. O troço Q8 junta 37 km de rio com e sem maré.

Para os troços de Marracuene, o modelo de produção (notebook 35), que usa também
a última medição por satélite, explica cerca de dois terços da variação.

## 2. Meses com turbidez acima do explicado

Só nos troços onde o modelo conta."""),
    ("code", """\
reliable = skill[skill["modelo_fiavel"]].index
unexplained = data[data["nao_explicada"] == True][["nome", "month", "ndti", "esperado", "residuo", "caudal_m3s", "chuva_mm"]]
unexplained.round(4).to_csv(REPORTS / "37_meses_acima_do_explicado.csv", index=False)
print("troços com modelo fiável:", ", ".join(skill.loc[reliable, "nome"]) or "nenhum")
if len(reliable):
    fig, axes = plt.subplots(len(reliable), 1, figsize=(15, 3.2 * len(reliable)), squeeze=False)
    for ax, section in zip(axes[:, 0], reliable):
        group = images[images["troco"] == section].set_index("date")
        group["ndti"].plot(ax=ax, style=".", color="black", markersize=3, label="medido"); group["esperado"].plot(ax=ax, color="#1e8449", linewidth=0.8, label="esperado")
        ax.set_title(skill.loc[section, "nome"]); ax.set_xlabel(""); ax.legend(loc="upper left")
    plt.tight_layout(); plt.savefig(REPORTS / "37_medido_e_esperado.png", dpi=110)
unexplained.sort_values("residuo", ascending=False).head(12)
"""),
    ("md", """\
**Leitura.** A tabela lista os meses em que a água esteve mais turva do que o
modelo esperava. Antes de qualquer conclusão, cada caso deve ser visto: imagem do
dia, notícias, registos de descargas de barragens. O modelo aponta, não acusa.

## 3. Montante e jusante: a água já chega turva à fronteira?

Comparação entre o troço da fronteira (Q1) e o de Marracuene (Q8), nos meses em
que os dois foram medidos pelo Sentinel-2."""),
    ("code", """\
result = Q.upstream_downstream(data, "Q1", "Q8")
if result.get("meses", 0) >= 12:
    both = result.pop("tabela")
    fig, axes = plt.subplots(1, 2, figsize=(16, 4.2), gridspec_kw={"width_ratios": [1.8, 1]})
    both.index = pd.to_datetime(both.index)
    both[["Q1", "Q8"]].plot(ax=axes[0], marker=".", color=["#8e44ad", "#2980b9"]); axes[0].legend(["Q1 fronteira", "Q8 Marracuene"]); axes[0].set_ylabel("NDTI"); axes[0].set_xlabel("")
    axes[0].set_title("Índice de cor na fronteira e em Marracuene (Sentinel-2)")
    axes[1].plot(both["Q1"], both["Q8"], ".", color="#34495e"); lims = [both.min().min(), both.max().max()]; axes[1].plot(lims, lims, color="grey", linewidth=0.8)
    axes[1].set_xlabel("Q1 fronteira"); axes[1].set_ylabel("Q8 Marracuene"); axes[1].set_title("Cada ponto é um mês")
    plt.tight_layout(); plt.savefig(REPORTS / "37_montante_e_jusante.png", dpi=110)
pd.Series(result).to_frame("valor").to_csv(REPORTS / "37_montante_e_jusante.csv")
between = data.pivot(index="month", columns="troco", values="ndti_s2").corr(min_periods=24)
between.round(2).to_csv(REPORTS / "37_correlacao_entre_trocos.csv")
fig, ax = plt.subplots(figsize=(6.2, 5.2)); im = ax.imshow(between.values, cmap="RdYlBu_r", vmin=-1, vmax=1)
ax.set_xticks(range(len(between)), between.columns); ax.set_yticks(range(len(between)), between.index)
for (i, j), v in np.ndenumerate(between.values):
    if np.isfinite(v):
        ax.text(j, i, f"{v:.1f}", ha="center", va="center", fontsize=8)
plt.colorbar(im, ax=ax, label="correlação"); ax.set_title("Os troços sobem e descem juntos?"); plt.tight_layout(); plt.savefig(REPORTS / "37_correlacao_entre_trocos.png", dpi=110)
along = data.groupby(["troco", "nome", "epoca"])["ndti_s2"].median().unstack("epoca")
along.round(3).to_csv(REPORTS / "37_cor_ao_longo_do_rio.csv")
display(pd.Series(result).to_frame("valor")); along.round(3)
"""),
    ("md", """\
**Como ler**

- `correlacao`: se os dois troços sobem e descem juntos, a turbidez de Marracuene
  vem em boa parte de montante.
- `meses_mais_turva_a_jusante`: em que parte dos meses a água está mais turva em
  Marracuene do que na fronteira.
- O quadro colorido mostra a correlação entre todos os pares de troços: troços
  vizinhos parecem-se, troços afastados quase não.
- A segunda tabela mostra a cor mediana ao longo do rio, na época seca e na
  chuvosa.

**Leitura.** A cor da água em Marracuene não acompanha, mês a mês, a cor na
fronteira. A resposta à pergunta transfronteiriça, com estes dados, é: **não se
vê o sinal da fronteira em Marracuene**. Entre os dois pontos há 250 km de rio,
afluentes, regadios e, no fim, a maré, que domina a cor a jusante.

**Cuidados.** O índice compara cores, não cargas de sedimento: dois troços com
fundos e profundidades diferentes podem ter cores diferentes com a mesma água. E
em Q1 o rio é estreito, com poucos píxeis por imagem. A pergunta "de onde vem o
sedimento" só fica respondida com medições no rio nos dois pontos.

## 4. Validação das fórmulas com medições reais (GLORIA)

O GLORIA junta reflectância medida à superfície da água com turbidez, sólidos
suspensos, clorofila-a e disco de Secchi, em centenas de lagos, rios e costas do
mundo. Serve para testar as **fórmulas**. Não testa as nossas imagens."""),
    ("code", """\
validation, samples = Q.gloria_validation(cfg)
validation.round(3).to_csv(REPORTS / "37_validacao_gloria.csv")
fig, axes = plt.subplots(1, 3, figsize=(17, 4.6))
for ax, measured, estimate, title in ((axes[0], "Turbidity", "fnu_dogliotti", "Turbidez (FNU): Dogliotti 2015"), (axes[1], "TSS", "tss_nechad", "Sólidos suspensos (mg/L): Nechad 2010")):
    ok = samples[measured].gt(0) & samples[estimate].gt(0)
    ax.loglog(samples.loc[ok, measured], samples.loc[ok, estimate], ".", color="#7f8c8d", alpha=0.4, markersize=3)
    ax.plot([0.1, 1000], [0.1, 1000], color="black", linewidth=0.8); ax.set_xlabel("medido"); ax.set_ylabel("estimado pela fórmula"); ax.set_title(title)
secchi = json.loads((ROOT / "models" / "secchi_gloria.json").read_text())
ok = samples["Secchi_depth"].gt(0)
axes[2].loglog(samples.loc[ok, "rho_665"], samples.loc[ok, "Secchi_depth"], ".", color="#7f8c8d", alpha=0.4, markersize=3)
x = np.logspace(-3.5, -0.7, 50); axes[2].plot(x, 10 ** (secchi["intercept"] + secchi["slope"] * np.log10(x)), color="#c0392b")
axes[2].set_xlabel("reflectância no vermelho"); axes[2].set_ylabel("disco de Secchi (m)"); axes[2].set_title("Transparência: relação ajustada")
plt.tight_layout(); plt.savefig(REPORTS / "37_validacao_gloria.png", dpi=110)
validation.round(2)
"""),
    ("md", """\
**Como ler**

- `r2_log` e `correlacao_log`: quanto a fórmula acompanha a medição (em escala
  logarítmica, porque os valores vão de menos de 1 a mais de 1000).
- `fator_tipico`: o erro típico. 2,5 quer dizer que a estimativa pode ser duas
  vezes e meia maior ou menor do que a medição.
- `razao_mediana`: perto de 1 = sem desvio sistemático.

**Leitura honesta.** As fórmulas publicadas acertam em média e ordenam bem as
águas, mas uma estimativa isolada pode falhar por um fator de 2 a 3, mesmo com
reflectância medida à superfície, em condições ideais. Com imagens de satélite
corrigidas para terra, o erro é maior. Por isso a plataforma usa a turbidez em
FNU e os sólidos em mg/L só como **ordem de grandeza**, e baseia os alertas no
índice de cor comparado com o seu próprio normal.

## 5. Medições no local: GEMStat e disco de Secchi"""),
    ("code", """\
import geopandas as gpd
stations = pd.read_csv(config.path(cfg, "water_quality", "validacao", "gemstat", "GEMStat_station_metadata.csv", mkdir=False), sep=None, engine="python", encoding="latin-1", on_bad_lines="skip")
points = gpd.GeoDataFrame(stations, geometry=gpd.points_from_xy(pd.to_numeric(stations["Longitude"], errors="coerce"), pd.to_numeric(stations["Latitude"], errors="coerce")), crs=4326)
basin = gpd.read_file(ROOT / "data" / "raw" / "aoi" / "incomati_basin.geojson").union_all()
inside = points[points.within(basin)]
print(f"GEMStat (arquivo de Fevereiro de 2026): {len(stations):,} estações no mundo; dentro da bacia do Incomáti: {len(inside)}")
field = pd.read_csv(config.path(cfg, "water_quality", "campo", "medicoes_secchi.csv", mkdir=False))
print(f"medições próprias (disco de Secchi / turbidímetro) registadas: {len(field)}")
"""),
    ("md", """\
**Leitura.** O arquivo mundial do GEMStat não tem nenhuma estação na bacia do
Incomáti. Não há, portanto, medições públicas no rio para validar valores
absolutos. A equipa decidiu, a 12 de Outubro de 2026, não fazer medições no
local nesta fase (tarefas W2-16 e W3-08). **Não haverá, portanto, validação
local:** os valores em FNU, mg/L e metros de transparência ficam como estimativas
e não devem ser apresentados ao público como medições.

## O que está validado e o que não está

| Afirmação | Estado | Base |
|---|---|---|
| O índice de cor é repetível entre dois satélites independentes | **validado** | notebooks 29 e 35 |
| As fórmulas de turbidez e sólidos acertam em média em águas reais | **validado**, com erro típico de um fator 2 a 3 | secção 4 (GLORIA) |
| Os valores em FNU e mg/L estão certos no Incomáti | **não validado, e não será nesta fase** | sem medições no rio (decisão da equipa) |
| A transparência estimada está certa no Incomáti | **não validado, e não será nesta fase** | sem disco de Secchi (decisão da equipa) |
| A turbidez acima do explicado indica poluição | **não se pode afirmar** | o modelo aponta meses a verificar |
| A clorofila-a pode ser medida aqui pelo NDCI | **não** | segue o sedimento (notebook 34) |
| pH, oxigénio, nutrientes, metais, bactérias | **fora do alcance do satélite** | plano, Parte I |"""),
]

# =============================================================================
NB["semana_3/38_ficha_de_evidencia_do_problema"] = [
    header("38 - Ficha de evidência do problema",
           "W3-09",
           "Mede o problema com os nossos dados: meses de alerta e de cheia em 20 anos, o que está exposto, e a evolução da cor da água",
           "Alertas diários 2006–2026, zonas de aviso, exposição, Módulo Q",
           "`docs/ficha_de_evidencia_do_problema.md`, `reports/semana_3/38_*.csv`",
           """\
O projecto existe porque as comunidades do Baixo Incomáti têm cheias sem aviso e
usam água cuja qualidade ninguém acompanha. Esta ficha põe números nisso, só com
dados que temos, e diz de onde vem cada número."""),
    ("code", setup("semana_3") + """
from ete import operations
"""),
    ("md", "## 1. Cheias: quantas vezes o rio passou os limites em 20 anos"),
    ("code", """\
alerts = pd.read_csv(config.path(cfg, "series", "alertas_diarios.csv", mkdir=False), parse_dates=["date"])
alerts = alerts[alerts["date"] < "2026-10-01"]
alerts["ano_hidrologico"] = np.where(alerts["date"].dt.month >= 10, alerts["date"].dt.year + 1, alerts["date"].dt.year)
monthly = alerts.assign(month=alerts["date"].dt.to_period("M").astype(str)).groupby("month")["level"].max()
yearly = alerts.groupby("ano_hidrologico").agg(dias_laranja_ou_vermelho=("level", lambda s: int((s >= 2).sum())), dias_vermelho=("level", lambda s: int((s >= 3).sum())),
                                                caudal_maximo_m3s=("discharge_m3s", "max"), nivel_maximo=("level", "max"))
yearly.round(0).to_csv(REPORTS / "38_alertas_por_ano.csv")
facts = {"meses_analisados": len(monthly), "meses_com_alerta_laranja_ou_vermelho": int((monthly >= 2).sum()), "meses_com_alerta_vermelho": int((monthly >= 3).sum()),
         "anos_analisados": len(yearly), "anos_com_alerta_laranja_ou_vermelho": int((yearly["nivel_maximo"] >= 2).sum()), "anos_com_alerta_vermelho": int((yearly["nivel_maximo"] >= 3).sum()),
         "maior_caudal_m3s": float(yearly["caudal_maximo_m3s"].max()), "ano_do_maior_caudal": int(yearly["caudal_maximo_m3s"].idxmax())}
ax = yearly["dias_laranja_ou_vermelho"].plot.bar(figsize=(13, 3.6), color="#e67e22", label="laranja ou vermelho")
yearly["dias_vermelho"].plot.bar(ax=ax, color="#c0392b", label="vermelho"); ax.legend(); ax.set_ylabel("dias"); ax.set_xlabel("ano hidrológico (Outubro a Setembro)")
ax.set_title("Dias em que as regras de alerta teriam dado laranja ou vermelho")
plt.tight_layout(); plt.savefig(REPORTS / "38_dias_de_alerta_por_ano.png", dpi=110)
pd.Series(facts).to_frame("valor")
"""),
    ("md", """\
**De onde vêm os números.** As regras de alerta do projecto (notebook 32) aplicadas
ao caudal do GloFAS e à chuva na bacia, dia a dia. São "dias em que o sistema
teria avisado", não cheias confirmadas no terreno: antes de 2014 não há radar
para as confirmar.

## 2. Quem e o que está no caminho da água"""),
    ("code", """\
exposure = operations.exposure(cfg)
exposure.round(1).to_csv(REPORTS / "38_exposicao_por_zona.csv")
places = pd.read_csv(config.path(cfg, "maps", "zonas_de_aviso", f"lugares_por_ordem_de_alagamento_{cfg['project']['aoi_name']}.csv", mkdir=False))
big = exposure.loc["zonas 1 e 2 (cheia grande)"]
facts.update({"area_alagada_cheia_grande_km2": float(big["area_km2"]), "terras_agricolas_km2": float(big["area_agricola_km2"]), "edificios": int(big["edificios"]),
              "estradas_km": float(big["estradas_km"]), "pessoas_worldpop_limite_superior": int(round(big["pessoas_worldpop_2020"], -2)),
              "lugares_que_alagam_primeiro": int((places["categoria"] == "alaga primeiro").sum()), "lugares_em_cheia_grande": int((places["categoria"] == "alaga em cheia grande").sum())})
exposure.T
"""),
    ("md", """\
**De onde vêm os números.** A zona é onde a água chegou na cheia de Janeiro de 2026
(mapas do Copernicus EMS). Os edifícios vêm do Google Open Buildings, as estradas
do OpenStreetMap.

**As pessoas são um limite superior.** O WorldPop espalha a população por todo o
terreno, e numa planície com poucas casas dá gente a mais. O número de edifícios
é o dado mais sólido.

## 3. A água do rio: está a mudar?"""),
    ("code", """\
data, skill, _ = Q.expected_turbidity(cfg, Q.monthly_dataset(cfg))
trend = Q.trends(data, values=("ndti",))
full = trend[trend["periodo"] == "registo completo"].set_index("troco")
recent = data[data["month"] >= "2013-04"]            # one satellite family (Landsat 8/9), so years can be compared
anomaly = Q.anomalies(recent, "ndti")
high = anomaly[(anomaly["classe"] != "sem dados") & (anomaly["ano"] >= 2014)].assign(alto=lambda d: d["classe"] != "normal")
by_year = high[high["troco"].isin(["Q7", "Q8", "Q9"])].groupby("ano")["alto"].mean()
facts.update({"trocos_analisados": int(data["troco"].nunique()), "trocos_com_20_anos": int(data.groupby("troco")["landsat_utilizavel"].first().sum()),
              "trocos_com_tendencia_confirmada_de_subida": int(((full["tendencia"] == "sobe") & full["leitura"].str.startswith("confirmada")).sum()),
              "trocos_com_tendencia_confirmada_de_descida": int(((full["tendencia"] == "desce") & full["leitura"].str.startswith("confirmada")).sum()),
              "ano_com_mais_meses_turvos_a_jusante": int(by_year.idxmax()), "parte_dos_meses_turvos_nesse_ano": float(by_year.max()),
              "estacoes_publicas_de_qualidade_na_bacia": 0})
ax = (100 * by_year).plot.bar(figsize=(13, 3.4), color="#a04000"); ax.axhline(25, color="grey", linestyle=":"); ax.set_ylabel("% de meses acima do normal"); ax.set_xlabel("")
ax.set_title("Troços de jusante (Manhiça à foz), desde 2014: parte dos meses com água mais turva do que o normal")
plt.tight_layout(); plt.savefig(REPORTS / "38_meses_turvos_por_ano.png", dpi=110)
full[["nome", "tendencia", "inclinacao_por_decada", "p", "leitura"]]
"""),
    ("md", "## 4. A ficha"),
    ("code", """\
pd.Series(facts).to_frame("valor").to_csv(REPORTS / "38_factos.csv")
n = lambda v: f"{v:,.0f}".replace(",", " ")
sheet = f\"\"\"# Ficha de evidência do problema

Projecto Eyes to Earth (tarefa W3-09). Gerada pelo notebook 38 em {pd.Timestamp.now():%d/%m/%Y}.
Todos os números vêm dos dados do projecto; a origem de cada um está indicada.

## Cheias sem aviso

| Facto | Número | Origem |
|---|---|---|
| Anos (de Outubro a Setembro) em que o rio passou o limite laranja | **{facts['anos_com_alerta_laranja_ou_vermelho']} em {facts['anos_analisados']}** | regras de alerta sobre o caudal GloFAS e a chuva, 2006–2026 |
| Anos em que passou o limite vermelho | **{facts['anos_com_alerta_vermelho']} em {facts['anos_analisados']}** | idem |
| Meses com alerta laranja ou vermelho | **{facts['meses_com_alerta_laranja_ou_vermelho']} em {facts['meses_analisados']}** | idem |
| Maior caudal do período | **{n(facts['maior_caudal_m3s'])} m³/s em {facts['ano_do_maior_caudal']}** | GloFAS (modelo, não estação) |
| Antecedência que o sistema teria dado em Janeiro de 2026 | **4 a 5 dias** antes do primeiro mapa de cheia | notebook 32 |

## O que está no caminho da água (cheia de Janeiro de 2026, dentro do distrito)

| Facto | Número | Origem |
|---|---|---|
| Área alagada | **{n(facts['area_alagada_cheia_grande_km2'])} km²** | Copernicus EMS (EMSR857) |
| Terras agrícolas alagadas | **{n(facts['terras_agricolas_km2'])} km²** | ESA WorldCover |
| Edifícios na zona alagada | **{n(facts['edificios'])}** | Google Open Buildings |
| Estradas e caminhos na zona alagada | **{n(facts['estradas_km'])} km** | OpenStreetMap |
| Pessoas na zona alagada | **até cerca de {n(facts['pessoas_worldpop_limite_superior'])}** (limite superior) | WorldPop 2020; ver nota |
| Lugares com nome que alagam primeiro / em cheia grande | **{facts['lugares_que_alagam_primeiro']} / {facts['lugares_em_cheia_grande']}** | OpenStreetMap e GeoNames, por validar |

## Água cuja qualidade ninguém acompanha

| Facto | Número | Origem |
|---|---|---|
| Estações públicas de qualidade da água na bacia do Incomáti | **{facts['estacoes_publicas_de_qualidade_na_bacia']}** | arquivo mundial GEMStat (UNEP), Fevereiro de 2026 |
| Troços do rio agora acompanhados por satélite | **{facts['trocos_analisados']}**, da fronteira à foz | Módulo Q |
| Troços com 20 anos de registo | **{facts['trocos_com_20_anos']}** (os de jusante; a montante o rio é estreito e só há dados desde 2017) | notebook 29 |
| Ano com mais meses de água turva a jusante, desde 2014 | **{facts['ano_com_mais_meses_turvos_a_jusante']}** ({100 * facts['parte_dos_meses_turvos_nesse_ano']:.0f} % dos meses acima do normal) | notebook 36 |
| Troços com tendência de 20 anos confirmada de água mais turva | **{facts['trocos_com_tendencia_confirmada_de_subida']}** (os dados não mostram que o rio esteja a ficar mais turvo) | Mann-Kendall sazonal, notebook 36 |

## Notas para usar estes números

- "Anos em que o rio passou o limite" são anos em que o sistema teria avisado. Não são
  cheias confirmadas uma a uma no terreno.
- As pessoas vêm de um mapa que espalha a população por todo o terreno. Numa planície com
  poucas casas dá gente a mais; dizer sempre "até cerca de".
- A área alagada é a da zona que o Copernicus analisou (58 % do distrito), mais a zona
  estimada pelo Modelo A fora dela.
- O satélite vê a cor da água. Não diz se a água é segura.
\"\"\"
(ROOT / "docs" / "ficha_de_evidencia_do_problema.md").write_text(sheet)
print(sheet)
"""),
]


def build():
    for name, cells in NB.items():
        target = ROOT / "notebooks" / f"{name}.ipynb"
        target.parent.mkdir(parents=True, exist_ok=True)
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
        print("escrito", target.relative_to(ROOT))


if __name__ == "__main__":
    build()
