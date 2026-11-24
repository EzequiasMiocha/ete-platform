"""Gera os notebooks da Semana 3 (modelos, alertas e validação) em notebooks/semana_3/.

    python scripts/build_notebooks_semana3.py

Os notebooks são leves: os passos estão aqui, a lógica está em src/ete. Um
notebook cujas células não mudaram não é reescrito, para manter os resultados.
Nenhum notebook da Semana 3 precisa de internet.
"""

from pathlib import Path
from textwrap import dedent

import nbformat
from nbformat.v4 import new_code_cell, new_markdown_cell, new_notebook

OUT = Path(__file__).resolve().parents[1] / "notebooks" / "semana_3"

SETUP = """\
import sys
from pathlib import Path

ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config" / "config.yaml").exists())
sys.path.insert(0, str(ROOT / "src"))

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from ete import alerts, config, drivers, rasters
from ete import grid as G
from ete import models as M

cfg = config.load_config()
P = cfg["processing"]
REPORTS = config.path(cfg, "reports", "semana_3")       # figuras e tabelas para o relatório
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


METRICS_MD = """\
**Como ler as medidas** (todas entre 0 e 1; quanto mais alto, melhor)

| Medida | Pergunta a que responde |
|---|---|
| IoU | da área que o modelo **ou** a referência dizem ser água, que parte é comum aos dois? |
| F1 | equilíbrio entre não falhar água e não dar falsos alarmes |
| Kappa | concordância com a referência, descontando o que se acertaria por acaso |
| Precisão | do que o modelo chamou água, que parte era mesmo água? |
| Recall | da água que existia, que parte o modelo encontrou? |
| AUC | o modelo dá valores mais altos à água do que à não-água? (0,5 = acaso) |"""

NB = {}

# =============================================================================
NB["30_modelo_B_detecao_de_agua_e_cheia"] = [
    header("30 - Modelo B: deteção de água e cheia (10 m)",
           "S3-01 (Modelo B) e parte de S3-04 (validação por blocos espaciais e evento real) e S3-05 (pós-processamento)",
           "Compara features e algoritmos, escolhe o melhor com um critério definido à partida, e testa-o na cheia de Janeiro de 2026",
           "`train_recente.parquet` (notebook 28), Sentinel-1 mensal, referência seca do radar",
           "`models/modelo_b_radar.joblib`, mapas em `data/processed/maps/modelo_b/`, tabelas e figuras em `reports/semana_3/`",
           """\
**Ideia simples.** O radar vê através das nuvens e a água calma aparece muito
escura. O modelo aprende, com exemplos, que combinações de valores de radar
correspondem a água.

**Como o trabalho está organizado**

1. Que **features** usar? (secção 2)
2. Que **algoritmo** usar? Quatro candidatos, mesmos dados, mesmo teste. (secção 3)
3. O modelo escolhido visto de perto: erros, calibração, importância. (secções 4 e 5)
4. Mapas. (secções 6 a 8)

**De onde vêm os exemplos e como se testa sem fazer batota**

- Os rótulos JRC (2016–2021) ensinam a água "de todos os dias" (rio, lagoas, zonas
  húmidas), mas quase não têm cheias curtas. Os exemplos de cheia vêm do mapa
  oficial do Copernicus de Janeiro de 2026.
- A área é dividida em blocos de 3 km. O modelo é treinado com alguns blocos da
  cheia e testado nos outros, cinco vezes, até todos terem sido testados por um
  modelo que nunca os viu. É um teste em **sítios novos do mesmo evento**: mais
  fraco do que um teste noutra cheia, mas é o que um único evento com referência
  permite.

**Termo de comparação.** Uma regra de uma linha ("VH no momento mais escuro do mês
igual ou abaixo de −22 dB = água") é avaliada ao lado. Um modelo só se justifica
se for melhor do que ela.

""" + METRICS_MD),
    ("code", SETUP + """
from ete import plots
"""),
    ("md", "## 1. Os dados de treino e de teste"),
    ("code", """\
table = M.load_table(cfg, "train_recente")
train, check, event = M.model_b_sets(cfg, table)
print(f"JRC para treino  : {len(train):,} linhas ({P['model_b_start_year']}-2021), {100 * train['label_water'].mean():.0f} % água")
print(f"JRC de controlo  : {len(check):,} linhas, nunca usadas no treino")
print(f"Cheia de 2026    : {len(event):,} linhas em {event['block_id'].nunique()} blocos de 3 km, {100 * event['label_water'].mean():.0f} % alagado")
event.groupby("fold").agg(linhas=("label_water", "size"), blocos=("block_id", "nunique"), alagado=("label_water", "mean"))
"""),
    ("md", """\
## 2. Que features usar? Comparação por blocos espaciais

Cada linha da tabela é um conjunto de features, com o mesmo algoritmo (Random
Forest) e o mesmo teste.

- **só JRC**: treinado sem nenhum exemplo da cheia, para mostrar o que acontece.
- **radar**: mediana e momento mais escuro do mês, diferença para a época seca, ângulo.
- **radar + terreno**: acrescenta HAND, declive e TWI.
- **radar + óptico**: acrescenta os índices do Sentinel-2 (vazios quando há nuvens)."""),
    ("code", """\
rows = []
only_jrc = M.forest().fit(M._x(train, M.RADAR), train["label_water"])
p = only_jrc.predict_proba(M._x(event, M.RADAR))[:, 1]
rows.append({"features": "só JRC (radar)", **M.scores(event["label_water"], p >= P["water_probability"], event["weight"], p)})
for name, features in [("radar", M.RADAR), ("radar + terreno", M.RADAR + M.TERRAIN_B), ("radar + óptico", M.RADAR + M.OPTICAL)]:
    oof_f, check_p = M.spatial_cv_event(cfg, table, features)
    rows.append({"features": name, **M.scores(event["label_water"], oof_f >= P["water_probability"], event["weight"], oof_f),
                 "auc_agua_jrc": M.scores(check["label_water"], check_p >= 0.5, check["weight"], check_p)["auc"]})
rule = event["vh_p10"] <= M.VH_RULE_DB
rows.append({"features": f"regra simples (VH p10 <= {M.VH_RULE_DB:g} dB)", **M.scores(event["label_water"], rule, event["weight"])})
feature_sets = pd.DataFrame(rows).set_index("features").drop(columns="n")
feature_sets.round(3).to_csv(REPORTS / "30_modelo_b_features.csv")
feature_sets
"""),
    ("md", """\
**Como ler esta tabela**

- A linha **só JRC** tem AUC alto mas recall mais baixo: o modelo ordena bem os
  píxeis, mas, como nunca viu uma cheia curta, deixa escapar cerca de um terço
  da área alagada.
- A **regra simples** já é boa. É o valor a bater.
- `auc_agua_jrc` mede o outro trabalho do modelo: reconhecer a água de todos os
  dias nos rótulos JRC de controlo.

**Decisão:** usar as features de **radar**. Funcionam todos os meses, com ou sem
nuvens. O ótico melhora um pouco quando existe, mas falta precisamente nos meses
de cheia; o terreno quase não acrescenta nada.

## 3. Que algoritmo usar? Quatro candidatos, o mesmo teste

| Algoritmo | O que é | Porque entra na comparação |
|---|---|---|
| Regressão logística | uma fronteira reta entre as classes | o modelo mais simples: se chegasse, não era preciso mais |
| Random Forest | muitas árvores de decisão independentes, que votam | previsto no plano; robusto e fácil de explicar |
| Gradient Boosting (HistGB) | árvores em sequência, cada uma corrige a anterior | costuma ser o mais exato em tabelas |
| XGBoost | outra implementação de gradient boosting | previsto no plano; muito usado em deteção remota |

**Critério de escolha, definido antes de ver os resultados:** o algoritmo com o
IoU médio mais alto nos cinco grupos de blocos. Se a diferença para o segundo
for menor do que a variação entre grupos de blocos, considera-se empate e
prefere-se o que ganhar em mais grupos; se continuar empatado, o mais rápido.

Todos usam configurações razoáveis e **não afinadas**: com cinco grupos de blocos
de um só evento, afinar parâmetros seria ajustar o modelo ao teste."""),
    ("code", """\
import time

oof, per_fold, rows = {}, [], []
for name, make in M.algorithms().items():
    start = time.time()
    oof[name], check_p = M.spatial_cv_event(cfg, table, M.RADAR, make)
    seconds = time.time() - start
    rows.append({"algoritmo": name, **M.scores(event["label_water"], oof[name] >= P["water_probability"], event["weight"], oof[name]),
                 "auc_agua_jrc": M.scores(check["label_water"], check_p >= 0.5, check["weight"], check_p)["auc"], "segundos": round(seconds)})
    for fold, g in event.groupby("fold"):
        per_fold.append({"modelo": name, "fold": fold, **M.scores(g["label_water"], oof[name][g.index] >= P["water_probability"], g["weight"], oof[name][g.index])})
for fold, g in event.groupby("fold"):
    per_fold.append({"modelo": "regra simples", "fold": fold, **M.scores(g["label_water"], g["vh_p10"] <= M.VH_RULE_DB, g["weight"])})
per_fold = pd.DataFrame(per_fold)
algorithms = pd.DataFrame(rows).set_index("algoritmo").drop(columns="n")
algorithms["iou_desvio_entre_blocos"] = per_fold.groupby("modelo")["iou"].std()
algorithms.round(3).to_csv(REPORTS / "30_modelo_b_algoritmos.csv")
per_fold.round(4).to_csv(REPORTS / "30_modelo_b_por_bloco.csv", index=False)
algorithms
"""),
    ("code", """\
fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))
plots.fold_scores(axes[0], per_fold, "iou")
plots.roc_and_pr(axes[1], axes[2], event["label_water"], oof, event["weight"])
axes[1].set_xlim(0, 0.3); axes[1].set_ylim(0.7, 1.005)          # zoom: é aqui que os modelos se distinguem
plt.tight_layout(); plt.savefig(REPORTS / "30_modelo_b_algoritmos.png", dpi=110)
"""),
    ("md", """\
**Como ler os gráficos**

- **Esquerda:** cada barra é a média do IoU; cada ponto preto é um grupo de
  blocos. Pontos muito espalhados = resultado instável.
- **Centro (ROC, com zoom):** quanto mais a linha sobe junto ao eixo esquerdo,
  mais água o modelo encontra com poucos falsos alarmes.
- **Direita (precisão-recall):** quanto mais a linha se mantém em cima à medida
  que vai para a direita, melhor.

A célula seguinte aplica o critério de escolha."""),
    ("code", """\
wide = per_fold.pivot(index="fold", columns="modelo", values="iou")
ranking = algorithms["iou"].sort_values(ascending=False)
best, second = ranking.index[0], ranking.index[1]
gap, spread = ranking.iloc[0] - ranking.iloc[1], algorithms.loc[best, "iou_desvio_entre_blocos"]
if gap < spread:                                   # empate: quem ganha em mais grupos, depois o mais rápido
    tied = [n for n in ranking.index if ranking.iloc[0] - ranking[n] < spread]
    wins = {n: int(sum((wide[n] >= wide[tied].max(axis=1) - 1e-9))) for n in tied}
    best = sorted(tied, key=lambda n: (-wins[n], algorithms.loc[n, "segundos"]))[0]
    print(f"empate dentro da variação entre blocos ({spread:.3f}) entre: {', '.join(tied)}")
    print("grupos de blocos ganhos por cada um:", wins)
BEST = best
(REPORTS / "30_modelo_b_escolhido.txt").write_text(BEST)
print(f"\\nALGORITMO ESCOLHIDO: {BEST}  (IoU {algorithms.loc[BEST, 'iou']:.3f}, F1 {algorithms.loc[BEST, 'f1']:.3f}, Kappa {algorithms.loc[BEST, 'kappa']:.3f})")
print(f"ganho sobre a regra simples: {algorithms.loc[BEST, 'iou'] - feature_sets.iloc[-1]['iou']:+.3f} de IoU; "
      f"melhor do que a regra em {int((wide[BEST] > wide['regra simples']).sum())} de {len(wide)} grupos de blocos")
print(f"ganho sobre a regressão logística: {algorithms.loc[BEST, 'iou'] - algorithms.loc['Regressão logística', 'iou']:+.3f} de IoU")
(wide.sub(wide["regra simples"], axis=0).drop(columns="regra simples")).round(3).rename_axis("diferença de IoU para a regra simples, por grupo de blocos", axis=1)
"""),
    ("md", """\
**O que a comparação mostra**

- A **regressão logística** fica claramente atrás: a relação entre o radar e a
  água não é uma linha reta, por isso um modelo de árvores justifica-se.
- Os três modelos de árvores ficam **muito próximos uns dos outros**. A diferença
  entre eles é da ordem da variação entre grupos de blocos: com um só evento,
  não se pode afirmar que um é realmente melhor do que os outros.
- A escolha segue o critério definido à partida. Seria igualmente defensável
  qualquer dos três.

## 4. O modelo escolhido visto de perto"""),
    ("code", """\
p_best = oof[BEST]
fig, axes = plt.subplots(1, 3, figsize=(19, 5.2))
# cada linha representa `weight` píxeis de 30 m: área em km² = peso x 900 m² / 1e6
plots.confusion(axes[0], event["label_water"], p_best >= P["water_probability"], event["weight"], 900 / 1e6)
plots.calibration(axes[1], event["label_water"], p_best, event["weight"])
thresholds = np.linspace(0.05, 0.95, 19)
curve = pd.DataFrame([M.scores(event["label_water"], p_best >= t, event["weight"]) for t in thresholds], index=thresholds)
curve[["iou", "precisao", "recall"]].plot(ax=axes[2]); axes[2].axvline(P["water_probability"], color="black", linestyle=":")
axes[2].set_xlabel("limiar de probabilidade"); axes[2].set_title("Efeito do limiar (linha pontilhada = limiar usado)")
plt.tight_layout(); plt.savefig(REPORTS / "30_modelo_b_escolhido.png", dpi=110)
M.scores(event["label_water"], p_best >= P["water_probability"], event["weight"], p_best)
"""),
    ("md", """\
**Como ler**

- **Matriz de confusão:** a diagonal são os acertos. O canto inferior esquerdo é
  a cheia que o modelo não viu; o superior direito são os falsos alarmes.
- **Calibração:** se os pontos estão sobre a diagonal, uma probabilidade de 0,8
  quer mesmo dizer "água em 80 % dos casos".
- **Efeito do limiar:** mostra que o resultado não depende de um limiar escolhido
  ao milímetro. Se o IoU se mantém alto numa faixa larga, o modelo é robusto.

## 5. Modelo final e o que ele usa

O modelo final é treinado com todas as linhas e guardado. A importância é medida
por permutação: baralha-se uma feature e vê-se quanto o AUC desce. Serve para
qualquer algoritmo."""),
    ("code", """\
model = M.fit_model_b(cfg, table, M.RADAR, "modelo_b_radar", make=M.algorithms()[BEST])
sample = pd.concat([check.sample(15000, random_state=0), event.sample(15000, random_state=0)])
imp = M.importance(model, M.RADAR, M._x(sample, M.RADAR), sample["label_water"])
ax = imp.sort_values().plot.barh(figsize=(8, 4), title=f"Importância por permutação - Modelo B ({BEST})", color="#2980b9")
ax.set_xlabel("queda do AUC quando a feature é baralhada")
plt.tight_layout(); plt.savefig(REPORTS / "30_modelo_b_importancia.png", dpi=110)
print(f"guardado em models/modelo_b_radar.joblib ({BEST})")
"""),
    ("md", """\
As features do **momento mais escuro do mês** (`vh_p10`, `vv_p10`) dominam: foi por
isso que essas bandas foram acrescentadas ao Sentinel-1.

## 6. Mapa da cheia de Janeiro de 2026 e comparação com o Copernicus

O modelo final é aplicado a todos os píxeis de 10 m. Manchas com menos de 25
píxeis (0,25 ha) são removidas como ruído. "Cheia" é a água fora da água
permanente."""),
    ("code", """\
EVENT = "2026-01"
map_file = M.water_map(cfg, model, M.RADAR, EVENT, overwrite=True)
layers = rasters.read_bands(map_file)
reference = M.reference_raster(cfg, EVENT)

km2 = lambda mask: mask.sum() * 100 / 1e6
labelled = (reference > 0) & np.isfinite(layers["agua"])
truth, predicted = reference == 2, layers["agua"] == 1
print(f"água prevista: {km2(predicted):.0f} km² | cheia (fora da água permanente): {km2(layers['cheia'] == 1):.0f} km²")
print(f"na área com referência: acertos {km2(labelled & truth & predicted):.0f} km², cheia não detetada {km2(labelled & truth & ~predicted):.0f} km², falso alarme {km2(labelled & ~truth & predicted):.1f} km²")

agreement = np.full(reference.shape, np.nan)
agreement[labelled & ~truth & ~predicted] = 0     # seco nos dois
agreement[labelled & truth & predicted] = 1       # água nos dois
agreement[labelled & truth & ~predicted] = 2      # cheia não detetada
agreement[labelled & ~truth & predicted] = 3      # falso alarme
from matplotlib.colors import ListedColormap
fig, axes = plt.subplots(1, 2, figsize=(15, 8))
axes[0].imshow(np.where(np.isfinite(layers["probabilidade"]), layers["probabilidade"], np.nan)[::4, ::4], cmap="Blues", vmin=0, vmax=1)
axes[0].set_title(f"Probabilidade de água, {EVENT} (Modelo B)"); axes[0].axis("off")
axes[1].imshow(agreement[::4, ::4], cmap=ListedColormap(["#e8e4d8", "#1f78b4", "#e31a1c", "#ff7f00"]), vmin=0, vmax=3, interpolation="nearest")
axes[1].set_title("Contra o Copernicus: azul = acerto, vermelho = cheia não detetada, laranja = falso alarme"); axes[1].axis("off")
plt.tight_layout(); plt.savefig(REPORTS / "30_modelo_b_mapa_2026-01.png", dpi=110)
"""),
    ("md", """\
Este mapa é feito com o modelo final, que já viu a cheia toda no treino. Serve
para **ver onde** estão os erros; os números honestos de desempenho são os das
secções 3 e 4, feitos por blocos.

## 7. Polígonos da cheia para o QGIS e para a plataforma"""),
    ("code", """\
polygons = M.vectorise(cfg, map_file, "cheia", config.path(cfg, "maps", "modelo_b", f"cheia_{cfg['project']['aoi_name']}_{EVENT}.gpkg"))
import geopandas as gpd
zones = gpd.read_file(polygons)
print(f"{len(zones)} zonas de cheia com mais de 0,5 ha, {zones['area_ha'].sum() / 100:.0f} km² no total -> {polygons.relative_to(ROOT)}")
"""),
    ("md", """\
## 8. Outros meses

O mesmo modelo aplicado a meses sem mapa oficial. Não há referência para
confirmar estes números: servem para ver se o comportamento é plausível
(mais cheia nos meses de chuva e caudal extremos, quase nenhuma num mês seco)."""),
    ("code", """\
rows = []
for month in ["2021-02", "2023-02", "2023-03", "2026-02", "2022-08"]:
    d = rasters.read_bands(M.water_map(cfg, model, M.RADAR, month, overwrite=True), ["agua", "cheia"])
    rows.append({"mês": month, "água_km2": np.nansum(d["agua"]) / 1e4, "cheia_km2": np.nansum(d["cheia"]) / 1e4})
outros = pd.DataFrame(rows).set_index("mês").join(drivers.load_monthly_drivers(cfg)[["rain_basin_mm", "q_max"]])
ax = outros["cheia_km2"].plot.bar(figsize=(8, 3.5), color="#2980b9", ylabel="km²", title="Cheia estimada pelo Modelo B em meses escolhidos")
plt.tight_layout(); plt.savefig(REPORTS / "30_modelo_b_outros_meses.png", dpi=110)
outros.round(1)
"""),
    ("md", """\
**Atenção ao valor do mês seco.** Mesmo em Agosto de 2022, sem chuva, o modelo dá
algumas dezenas de km² de "cheia". Não é cheia: são zonas húmidas e solos que o
radar vê escuros e que o JRC não conta como água permanente. É o nível de fundo
do método. Uma cheia lê-se pela diferença em relação a esse fundo, e não pelo
valor absoluto.

## As métricas são boas? Leitura de especialista

- **IoU perto de 0,9 e F1 perto de 0,95 são valores altos** para mapas de cheia
  com Sentinel-1. Em comparações publicadas com dados de referência
  independentes, é comum ver IoU entre 0,6 e 0,85.
- **Mas este número é otimista por duas razões**, que devem ser ditas sempre que
  for citado: (1) o teste é em sítios novos do mesmo evento, não noutra cheia;
  (2) metade dos mapas de referência do Copernicus também foi feita com
  Sentinel-1, ou seja, com o mesmo tipo de sensor.
- **O ganho do modelo sobre a regra simples é pequeno.** O que realmente fez a
  diferença foi a decisão de usar o momento mais escuro do mês, e não o
  algoritmo. Isto é um resultado honesto e útil: a plataforma pode até arrancar
  com a regra simples e usar o modelo como refinamento.
- **A precisão é muito alta e o recall um pouco menor**: quando o modelo diz
  "água", quase sempre é; o que falha é alguma água nas margens da cheia.
  Para um sistema de alertas, é o lado mais seguro para errar em área, mas
  significa que a extensão real pode ser um pouco maior do que a mapeada.

## Limites do Modelo B

- **Um só evento com referência.** O desempenho foi medido em sítios novos da
  cheia de Janeiro de 2026. Não se sabe como se comporta em cheias mais pequenas
  ou com outro padrão.
- **A referência também é radar.** Dois dos quatro mapas do Copernicus foram
  feitos com Sentinel-1. Concordar com eles não prova que haja água debaixo de
  vegetação densa ou entre casas, onde nenhum radar a vê bem.
- **Resolução temporal mensal.** O modelo diz que houve água em algum momento do
  mês, não em que dia.
- **O mar fica de fora** do domínio; solo nu muito seco pode ser confundido com
  água (visto em 2015–2016, notebook 20)."""),
]

# =============================================================================
NB["31_modelo_A_suscetibilidade"] = [
    header("31 - Modelo A: suscetibilidade a cheias (30 m)",
           "S3-02 (Modelo A + mapa de risco) e parte de S3-04 (validação temporal)",
           "Compara features e algoritmos, escolhe o melhor na validação, e testa o mapa na cheia de Janeiro de 2026",
           "`train_historico.parquet` (notebook 27), stack estático (notebook 21)",
           "`models/modelo_a_terreno.joblib`, `data/processed/maps/modelo_a/suscetibilidade_*.tif`, tabelas e figuras",
           """\
**Ideia simples.** A água vai sempre para os mesmos sítios: os mais baixos e mais
próximos do rio. O modelo aprende, com 14 anos de água observada (2006–2019),
que características do terreno têm os sítios que alagam, e dá a cada píxel uma
nota de 0 a 1.

**Três conjuntos de dados, cada um com o seu papel**

| Conjunto | Anos | Para quê |
|---|---|---|
| Treino | 2006–2019 | ensinar o modelo |
| Validação | 2020–2021 (inclui a cheia de Fevereiro de 2021) | **escolher** features e algoritmo |
| Teste | cheia de Janeiro de 2026 (Copernicus) | medir o resultado final, **sem influenciar nenhuma escolha** |

**O que não entra como feature**, para o modelo não copiar a resposta: a
frequência histórica de água do JRC e as bandas Landsat do próprio mês.

""" + METRICS_MD),
    ("code", SETUP + """
from sklearn.metrics import roc_auc_score
from ete import plots
"""),
    ("md", "## 1. Dados"),
    ("code", """\
table = M.load_table(cfg, "train_historico")
train, val, event = M.model_a_sets(table)
real = lambda g: 100 * np.average(g["label_flood"], weights=g["weight"])
print(f"treino     : {len(train):,} linhas (até 2019); água não permanente em {real(train):.2f} % da área")
print(f"validação  : {len(val):,} linhas (2020-2021); {real(val):.2f} %")
print(f"teste 2026 : {len(event):,} linhas (Copernicus EMS); {100 * np.average(event['label_water'], weights=event['weight']):.0f} % alagado na área analisada")

def auc_pair(model, features):
    pv = model.predict_proba(M._x(val, features))[:, 1]
    pe = model.predict_proba(M._x(event, features))[:, 1]
    return pv, pe, {"auc_validacao_2020_21": roc_auc_score(val["label_flood"], pv, sample_weight=val["weight"]),
                    "auc_cheia_2026": roc_auc_score(event["label_water"], pe, sample_weight=event["weight"])}
"""),
    ("md", """\
## 2. Que informação é precisa? Comparação de features

Mesmo algoritmo (Random Forest), features diferentes. O AUC mede se o modelo dá
notas mais altas aos sítios que alagaram."""),
    ("code", """\
variants = {
    "terreno": M.TERRAIN_A,
    "terreno sem distâncias à água": [f for f in M.TERRAIN_A if f not in ("distance_to_water_m", "distance_to_river_m")],
    "terreno + chuva, caudal e humidade": M.TERRAIN_A + M.HYDROMET,
    "só HAND (modelo)": ["hand"],
}
rows = []
for name, features in variants.items():
    rows.append({"features": name, **auc_pair(M.fit_model_a(cfg, table, features), features)[2]})
rows.append({"features": "HAND sozinho, sem modelo", "auc_validacao_2020_21": roc_auc_score(val["label_flood"], -val["hand"], sample_weight=val["weight"]),
             "auc_cheia_2026": roc_auc_score(event["label_water"], -event["hand"], sample_weight=event["weight"])})
feature_sets = pd.DataFrame(rows).set_index("features")
feature_sets.round(3).to_csv(REPORTS / "31_modelo_a_features.csv")
feature_sets
"""),
    ("md", """\
**Como ler**

- O **terreno** sozinho já ordena muito bem os sítios que alagam.
- Juntar a **chuva, o caudal e a humidade** melhora pouco. Era esperado: os
  rótulos têm poucas cheias (notebook 27), por isso o modelo aprende sobretudo
  **onde** e não **quando**. O "quando" fica a cargo do motor de alertas.
- O **HAND sozinho** fica bastante abaixo: a distância à água e a altitude
  acrescentam informação real.

**Decisão:** o mapa usa só o **terreno**, que não depende do mês.

## 3. Que algoritmo usar? Quatro candidatos

Os mesmos quatro algoritmos do Modelo B, com as mesmas linhas de treino e as
features de terreno.

**Critério de escolha, definido antes de ver os resultados:** o AUC mais alto na
**validação** (2020–2021). O teste de 2026 não entra na escolha; é mostrado ao
lado só para confirmar. Em caso de empate (diferença inferior a 0,005), prefere-se
o mais rápido."""),
    ("code", """\
import time

rows, p_val, p_event, fitted = [], {}, {}, {}
for name, make in M.algorithms().items():
    start = time.time()
    fitted[name] = M.fit_model_a(cfg, table, M.TERRAIN_A, make=make)
    p_val[name], p_event[name], aucs = auc_pair(fitted[name], M.TERRAIN_A)
    rows.append({"algoritmo": name, **aucs, "segundos": round(time.time() - start)})
algorithms = pd.DataFrame(rows).set_index("algoritmo")
algorithms.round(3).to_csv(REPORTS / "31_modelo_a_algoritmos.csv")

top = algorithms["auc_validacao_2020_21"].max()
tied = algorithms[algorithms["auc_validacao_2020_21"] >= top - 0.005]
BEST = tied["segundos"].idxmin()
(REPORTS / "31_modelo_a_escolhido.txt").write_text(BEST)
print(f"empatados na validação (a menos de 0,005 do melhor): {', '.join(tied.index)}")
print(f"ALGORITMO ESCOLHIDO: {BEST}  (AUC validação {algorithms.loc[BEST, 'auc_validacao_2020_21']:.3f}; AUC na cheia de 2026 {algorithms.loc[BEST, 'auc_cheia_2026']:.3f})")
algorithms
"""),
    ("code", """\
fig, axes = plt.subplots(1, 3, figsize=(20, 5.5))
algorithms[["auc_validacao_2020_21", "auc_cheia_2026"]].plot.bar(ax=axes[0], color=["#95a5a6", "#2980b9"], rot=12)
axes[0].set_ylim(0.8, 1.0); axes[0].set_ylabel("AUC"); axes[0].set_title("AUC por algoritmo"); axes[0].legend(["validação 2020-2021", "cheia de 2026 (teste)"])
for name in algorithms.index:
    plots.capture_curve(axes[1], event["label_water"], p_event[name], event["weight"], label=name, colour=plots.COLOURS.get(name))
plots.capture_curve(axes[1], event["label_water"], -event["hand"], event["weight"], label="HAND sozinho", colour="black")
axes[1].plot([0, 1], [0, 1], color="grey", linestyle=":"); axes[1].legend(); axes[1].set_title("Cheia de 2026: quanta cheia se encontra a percorrer o mapa")
from sklearn.metrics import roc_curve
for name in algorithms.index:
    fpr, tpr, _ = roc_curve(event["label_water"], p_event[name], sample_weight=event["weight"])
    axes[2].plot(fpr, tpr, label=name, color=plots.COLOURS.get(name))
axes[2].plot([0, 1], [0, 1], color="grey", linestyle=":"); axes[2].legend(); axes[2].set_title("Curva ROC na cheia de 2026")
axes[2].set_xlabel("parte da área não alagada com nota alta"); axes[2].set_ylabel("parte da área alagada com nota alta")
plt.tight_layout(); plt.savefig(REPORTS / "31_modelo_a_algoritmos.png", dpi=110)
"""),
    ("md", """\
**Como ler os gráficos**

- **Esquerda:** AUC de cada algoritmo, na validação (cinzento) e no teste (azul).
- **Centro (curva de captura):** imagina percorrer o território do sítio com nota
  mais alta para o mais baixo. A curva mostra que parte da cheia de 2026 já foi
  encontrada. Uma curva que sobe depressa = o mapa põe a cheia nos sítios certos.
  A linha pontilhada seria um mapa ao acaso.
- **Direita:** curva ROC na cheia de 2026.

**O que a comparação mostra:** a regressão logística fica atrás; os modelos de
árvores ficam próximos entre si. Tal como no Modelo B, o algoritmo importa menos
do que os dados que lhe são dados.

## 4. Modelo final, importância das features e mapa"""),
    ("code", """\
model = M.fit_model_a(cfg, table, M.TERRAIN_A, "modelo_a_terreno", make=M.algorithms()[BEST])
sample = val.sample(30000, random_state=0)
imp = M.importance(model, M.TERRAIN_A, M._x(sample, M.TERRAIN_A), sample["label_flood"], sample["weight"])
ax = imp.sort_values().plot.barh(figsize=(8, 4), title=f"Importância por permutação - Modelo A ({BEST})", color="#c0392b")
ax.set_xlabel("queda do AUC na validação quando a feature é baralhada")
plt.tight_layout(); plt.savefig(REPORTS / "31_modelo_a_importancia.png", dpi=110)
"""),
    ("md", """\
O rio e as lagoas (água permanente) ficam numa classe à parte: não são "zona de
cheia", já são água. A nota do resto do terreno é dividida em quatro classes,
por posição entre todos os píxeis de terra: **baixa** (a metade com notas mais
baixas), **média** (os 30 % seguintes), **alta** (15 %) e **muito alta** (os 5 % com
nota mais alta)."""),
    ("code", """\
map_file = M.susceptibility_map(cfg, model, M.TERRAIN_A)
layers = rasters.read_bands(map_file)
names = {1: "baixa", 2: "média", 3: "alta", 4: "muito alta"}

from matplotlib.colors import ListedColormap
fig, axes = plt.subplots(1, 2, figsize=(14, 8))
axes[0].imshow(layers["suscetibilidade"], cmap="YlOrRd", vmin=0, vmax=1); axes[0].set_title("Nota de suscetibilidade (0-1)"); axes[0].axis("off")
axes[1].imshow(layers["classe"], cmap=ListedColormap(["#2b6cb0", "#ffffcc", "#fed976", "#fd8d3c", "#bd0026"]), vmin=0, vmax=4, interpolation="nearest")
axes[1].set_title("Classes: amarelo claro = baixa ... vermelho escuro = muito alta; azul = água permanente"); axes[1].axis("off")
plt.tight_layout(); plt.savefig(REPORTS / "31_modelo_a_mapa.png", dpi=110)
print(map_file.relative_to(ROOT))
"""),
    ("md", """\
## 5. O mapa acerta? Teste com a cheia de Janeiro de 2026

Para cada classe: que parte dela alagou em 2026, e que parte de toda a área
alagada caiu nessa classe. Só conta a área analisada pelo Copernicus."""),
    ("code", """\
reference = M.reference_raster(cfg, "2026-01", res=30)
labelled = (reference > 0) & np.isfinite(layers["classe"])
flooded = reference == 2
test = pd.DataFrame({
    "area_com_referencia_km2": [((layers["classe"] == k) & labelled).sum() * 900 / 1e6 for k in names],
    "parte_da_classe_que_alagou": [flooded[(layers["classe"] == k) & labelled].mean() for k in names],
    "parte_da_cheia_nesta_classe": [((layers["classe"] == k) & labelled & flooded).sum() / (labelled & flooded).sum() for k in names],
}, index=list(names.values()))
test.round(3).to_csv(REPORTS / "31_modelo_a_teste_2026.csv")

fig, axes = plt.subplots(1, 2, figsize=(13, 4))
colours = ["#ffffcc", "#fed976", "#fd8d3c", "#bd0026"]
(100 * test["parte_da_classe_que_alagou"]).plot.bar(ax=axes[0], color=colours, edgecolor="grey", rot=0, ylabel="%", title="Parte de cada classe que alagou em Janeiro de 2026")
(100 * test["parte_da_cheia_nesta_classe"]).plot.bar(ax=axes[1], color=colours, edgecolor="grey", rot=0, ylabel="%", title="Onde caiu a cheia: parte da área alagada em cada classe")
plt.tight_layout(); plt.savefig(REPORTS / "31_modelo_a_teste_2026.png", dpi=110)
test
"""),
    ("md", """\
**Como ler.** Um bom mapa tem o gráfico da esquerda a subir de "baixa" para "muito
alta", e quase nada da cheia na classe "baixa".

A classe "média" também alagou em grande parte: Janeiro de 2026 foi a maior
cheia dos 20 anos e cobriu cerca de um terço do distrito. Numa cheia normal, a
água fica sobretudo nas classes "alta" e "muito alta".

## As métricas são boas? Leitura de especialista

- **Um AUC perto de 0,95 numa cheia que o modelo nunca viu é um bom resultado.**
  Estudos de suscetibilidade costumam publicar valores entre 0,85 e 0,95, muitas
  vezes medidos em pontos sorteados dos mesmos eventos usados no treino, o que
  os torna otimistas. Aqui o teste é de outro ano e de outra fonte.
- **O número que mais interessa a quem decide** não é o AUC, é a tabela por
  classes: quase nada alagou na classe "baixa" e quase tudo na "alta" e "muito
  alta". É isso que torna o mapa utilizável para priorizar zonas.
- **O limite está nos dados, não no algoritmo:** os quatro algoritmos de árvores
  dão resultados parecidos. Para melhorar seria preciso um modelo de elevação
  mais fino (o atual é de 30 m) e mais cheias com referência.

## Limites do Modelo A

- **Diz onde, não quando.** É um mapa fixo. Não muda com a chuva.
- **Aprendeu com água sazonal e poucas cheias.** Os rótulos JRC veem mal as cheias
  (nuvens). O teste de 2026 mostra que, mesmo assim, o mapa ordena bem o risco.
- **Terreno a 30 m com dados de 30–90 m.** Diques, valas e aterros pequenos não
  aparecem no modelo de elevação; ruas e bairros concretos podem estar mal
  classificados. O mapa serve para planear por zonas, não casa a casa.
- **Um só evento de teste**, e só na parte do distrito analisada pelo Copernicus."""),
]

# =============================================================================
NB["32_motor_de_alertas"] = [
    header("32 - Motor de alertas",
           "S3-03 - risco (A) × água atual (B) × gatilhos (chuva anómala + caudal GloFAS)",
           "Define as regras de alerta, testa-as nos 20 anos e mostra o que está exposto em cada zona de risco",
           "Séries diárias de chuva e caudal (notebooks 22 e 23), mapa do Modelo A, mapas do Modelo B, edifícios e equipamentos",
           "`reports/semana_3/32_*.csv` (regras, episódios, exposição) e figuras",
           """\
**A lógica, em três perguntas**

| Pergunta | Quem responde | Com que frequência |
|---|---|---|
| **Quando** pode haver cheia? | Gatilhos: chuva acumulada e caudal do rio | todos os dias |
| **Onde**? | Modelo A: classes de suscetibilidade | fixo |
| **Quem** está exposto? | Edifícios, escolas e unidades de saúde em cada classe | fixo |
| A água chegou mesmo? | Modelo B: mapa de água por satélite | depois, por mês |

**Níveis**

| Nível | Chuva (7 dias, bacia) | Caudal em Marracuene |
|---|---|---|
| amarelo | entre os 5 % mais altos para a época | acima do percentil 90 |
| laranja | entre o 1 % mais alto para a época | acima do percentil 97 |
| vermelho | laranja na chuva **e** laranja no caudal | acima do percentil 99,5 |

O nível do dia é o mais alto dos dois gatilhos. A chuva só conta se o total de 7
dias passar de 50 mm, para um aguaceiro na época seca não disparar o alerta.

**Teste honesto das regras.** Os limites do caudal são calculados só com os
dados até 2021. Os anos de 2022 a 2026 servem para ver se as regras teriam
funcionado em eventos que não ajudaram a defini-las."""),
    ("code", SETUP),
    ("md", "## 1. Os limites em números"),
    ("code", """\
limits = alerts.thresholds(cfg)
tabela = pd.DataFrame({"chuva: percentil dos 7 dias": limits["rain_pct"], "caudal (m³/s)": limits["discharge_m3s"]}).reindex(["amarelo", "laranja", "vermelho"])
tabela.to_csv(REPORTS / "32_limites_dos_alertas.csv")
print(f"mínimo de chuva em 7 dias para contar: {limits['rain_p7_min_mm']} mm")
tabela
"""),
    ("md", "## 2. Alertas dia a dia, 2006–2026"),
    ("code", """\
daily = alerts.daily_alerts(cfg)
daily.to_csv(drivers.table(cfg, "alertas_diarios"))
dias = daily.groupby(daily.index.year)["level"].value_counts().unstack(fill_value=0).rename(columns=alerts.LEVELS)
ax = dias[["amarelo", "laranja", "vermelho"]].plot.bar(stacked=True, figsize=(13, 4), color=["#f1c40f", "#e67e22", "#c0392b"],
                                                      title="Dias em alerta por ano", ylabel="dias")
plt.tight_layout(); plt.savefig(REPORTS / "32_dias_em_alerta_por_ano.png", dpi=110)
daily["alerta"].value_counts().to_frame("dias em 20 anos")
"""),
    ("md", """\
## 3. Um episódio visto de perto: a cheia de Janeiro de 2026

As linhas verticais marcam as datas em que o Copernicus mapeou a cheia em
Marracuene (17 e 24 de Janeiro)."""),
    ("code", """\
window = daily.loc["2025-12-01":"2026-03-15"]
colours = {0: "#2ecc71", 1: "#f1c40f", 2: "#e67e22", 3: "#c0392b"}
fig, axes = plt.subplots(3, 1, figsize=(13, 8), sharex=True, height_ratios=[3, 3, 0.6])
window["p7_basin"].plot(ax=axes[0], color="tab:blue"); axes[0].axhline(limits["rain_p7_min_mm"], color="grey", linestyle=":")
axes[0].set_ylabel("mm"); axes[0].set_title("Chuva acumulada em 7 dias na bacia")
window["discharge_m3s"].plot(ax=axes[1], color="tab:brown")
for name, value in limits["discharge_m3s"].items():
    axes[1].axhline(value, color={"amarelo": "#f1c40f", "laranja": "#e67e22", "vermelho": "#c0392b"}[name], linestyle="--")
axes[1].set_ylabel("m³/s"); axes[1].set_title("Caudal em Marracuene (GloFAS) e limites dos níveis")
axes[2].bar(window.index, 1, width=1, color=[colours[v] for v in window["level"]]); axes[2].set_yticks([]); axes[2].set_title("Nível de alerta do dia")
for ax in axes[:2]:
    for day in ["2026-01-17", "2026-01-24"]:
        ax.axvline(pd.Timestamp(day), color="black", linewidth=0.8)
plt.tight_layout(); plt.savefig(REPORTS / "32_alerta_janeiro_2026.png", dpi=110)
"""),
    ("md", "## 4. Teriam as regras avisado a tempo?"),
    ("code", """\
events = {
    "jan 2026: primeira cheia mapeada em Marracuene (Copernicus)": "2026-01-17",
    "jan 2026: maior extensão mapeada (Copernicus)": "2026-01-24",
    "fev 2023: ativação do Copernicus para a província de Maputo": "2023-02-11",
}
antecedencia = pd.DataFrame({name: alerts.lead_time(daily, day) for name, day in events.items()}).T
antecedencia.to_csv(REPORTS / "32_antecedencia_dos_alertas.csv")
antecedencia
"""),
    ("md", """\
`dias_de_antecedencia` conta os dias entre o primeiro alerta laranja ou vermelho
e a data do evento. Os dois eventos são posteriores a 2021, por isso não
influenciaram os limites.

## 5. Todos os episódios de alerta laranja ou vermelho"""),
    ("code", """\
ep = alerts.episodes(daily)
ep.to_csv(REPORTS / "32_episodios_de_alerta.csv", index=False)
print(f"{len(ep)} episódios em 20 anos, {int((ep['nivel_maximo'] == 'vermelho').sum())} chegaram a vermelho")
ep[ep["nivel_maximo"] == "vermelho"]
"""),
    ("md", """\
## 6. Os alertas coincidem com a água vista por satélite?

Para cada mês desde 2015: o nível de alerta mais alto do mês e a área de cheia
medida pelo Modelo B. Se os gatilhos fazem sentido, os meses em vermelho devem
ter mais água."""),
    ("code", """\
area_file = drivers.table(cfg, "modelo_b_area_mensal")
if area_file.exists():
    area = pd.read_csv(area_file, index_col=0)
    # 2015 fica de fora: só tem uma órbita de radar (ângulo diferente), o modelo não foi treinado
    # com esse ano e os seus mapas dão água a mais
    area = area[area.index >= f"{P['model_b_start_year']}-01"]
    monthly_level = daily["level"].resample("MS").max()
    monthly_level.index = monthly_level.index.strftime("%Y-%m")
    both = area.join(monthly_level.rename("nivel")).dropna()
    both["alerta"] = both["nivel"].map(alerts.LEVELS)
    resumo = both.groupby("alerta")["cheia_distrito_km2"].agg(["count", "median", "max"]).reindex(["verde", "amarelo", "laranja", "vermelho"])
    resumo.columns = ["meses", "cheia mediana no distrito (km²)", "cheia máxima (km²)"]
    resumo.round(1).to_csv(REPORTS / "32_alerta_vs_agua_por_satelite.csv")
    ax = both["cheia_distrito_km2"].plot(figsize=(13, 3.5), color="tab:blue", ylabel="km²", title="Cheia no distrito medida pelo Modelo B, mês a mês")
    plt.tight_layout(); plt.savefig(REPORTS / "32_cheia_mensal_modelo_b.png", dpi=110)
    display(resumo.round(1))
else:
    print("correr primeiro: .venv/bin/python scripts/run_model_b_maps.py (mapas mensais do Modelo B)")
"""),
    ("md", """\
**Leitura honesta.** A relação existe mas é fraca: a cheia máxima é claramente
maior nos meses em vermelho, mas a mediana pouco muda de nível para nível. Há
duas razões. Primeiro, o Modelo B tem um nível de fundo de algumas dezenas de
km² (zonas húmidas que o radar vê escuras), que está presente em todos os meses.
Segundo, o alerta mede a **causa** (chuva e caudal na bacia) e o satélite mede o
**efeito** no distrito, que pode chegar dias ou semanas depois e cair no mês
seguinte. Os gatilhos servem para avisar; o mapa de satélite serve para
confirmar onde a água chegou. Um não substitui o outro.

## 7. Onde e quem: exposição por classe de suscetibilidade

Dentro do distrito de Marracuene. As colunas "em zona alagada" contam o que
ficou dentro da cheia de Janeiro de 2026 mapeada pelo Copernicus."""),
    ("code", """\
flooded_2026 = M.reference_raster(cfg, "2026-01", res=30) == 2
exposure = alerts.exposure_by_class(cfg, flooded=flooded_2026)
exposure.round(1).to_csv(REPORTS / "32_exposicao_por_classe.csv")
exposure.round(1)
"""),
    ("md", """\
**Como usar esta tabela num alerta.** Quando os gatilhos passam a laranja ou
vermelho, as zonas a avisar primeiro são as de classe **alta** e **muito alta**;
a tabela diz quantos edifícios lá estão.

## Limites do motor de alertas

- **O caudal usado aqui é uma reanálise.** O GloFAS histórico é publicado com
  atraso. Em operação, o gatilho de caudal tem de usar a **previsão** do GloFAS
  (até 30 dias) e a chuva tem de vir do IMERG, que é quase em tempo real. A
  ligação a essas fontes é trabalho da Semana 4.
- **Não há lista oficial de cheias para contar falsos alarmes.** Sabe-se que os
  maiores episódios coincidem com cheias conhecidas; para os mais pequenos não
  há como confirmar se houve água.
- **Dois eventos de teste** posteriores a 2021. É pouco para garantir uma
  antecedência.
- **A contagem de edifícios vem do Google Open Buildings** e a de escolas e
  unidades de saúde do OpenStreetMap, que é incompleto nas zonas rurais: são
  valores mínimos.
- **O alerta é para a bacia e o distrito inteiros**, não bairro a bairro."""),
]

# =============================================================================
NB["33_validacao_e_resumo"] = [
    header("33 - Validação e resumo da Semana 3",
           "S3-04 - relatório de validação (IoU, F1, Kappa, ROC-AUC)",
           "Junta num só sítio os resultados dos modelos e dos alertas, com o que está provado e o que não está",
           "Tabelas produzidas pelos notebooks 30, 31 e 32",
           "`reports/semana_3/33_relatorio_de_validacao.csv`",
           METRICS_MD),
    ("code", SETUP),
    ("md", "## 1. Modelo B (deteção de água e cheia, 10 m)"),
    ("code", """\
b = pd.read_csv(REPORTS / "30_modelo_b_algoritmos.csv", index_col=0)
b_features = pd.read_csv(REPORTS / "30_modelo_b_features.csv", index_col=0)
display(b_features[["iou", "f1", "kappa", "precisao", "recall", "auc"]])
b[["iou", "f1", "kappa", "precisao", "recall", "auc", "iou_desvio_entre_blocos", "segundos"]]
"""),
    ("md", "## 2. Modelo A (suscetibilidade, 30 m)"),
    ("code", """\
a = pd.read_csv(REPORTS / "31_modelo_a_algoritmos.csv", index_col=0)
display(pd.read_csv(REPORTS / "31_modelo_a_features.csv", index_col=0))
display(a)
pd.read_csv(REPORTS / "31_modelo_a_teste_2026.csv", index_col=0)
"""),
    ("md", "## 3. Alertas"),
    ("code", """\
display(pd.read_csv(REPORTS / "32_antecedencia_dos_alertas.csv", index_col=0))
pd.read_csv(REPORTS / "32_exposicao_por_classe.csv", index_col=0)
"""),
    ("md", "## 4. Relatório de validação"),
    ("code", """\
best_b = (REPORTS / "30_modelo_b_escolhido.txt").read_text().strip()
best_a = (REPORTS / "31_modelo_a_escolhido.txt").read_text().strip()
rule = b_features[b_features.index.str.startswith("regra simples")].iloc[0]
mark = lambda name, best: f"{name} (escolhido)" if name == best else name
rows = [{"modelo": "B - " + mark(n, best_b), "teste": "cheia de Janeiro de 2026, blocos espaciais de 3 km (Copernicus EMS)",
         "IoU": r["iou"], "F1": r["f1"], "Kappa": r["kappa"], "ROC-AUC": r["auc"]} for n, r in b.iterrows()]
rows.append({"modelo": "B - regra simples VH", "teste": "cheia de Janeiro de 2026 (Copernicus EMS)", "IoU": rule["iou"], "F1": rule["f1"], "Kappa": rule["kappa"], "ROC-AUC": np.nan})
rows.append({"modelo": "B - " + mark(best_b, best_b), "teste": "água JRC de controlo 2016-2021", "IoU": np.nan, "F1": np.nan, "Kappa": np.nan, "ROC-AUC": b.loc[best_b, "auc_agua_jrc"]})
for n, r in a.iterrows():
    rows.append({"modelo": "A - " + mark(n, best_a), "teste": "validação temporal 2020-2021 (JRC)", "IoU": np.nan, "F1": np.nan, "Kappa": np.nan, "ROC-AUC": r["auc_validacao_2020_21"]})
    rows.append({"modelo": "A - " + mark(n, best_a), "teste": "cheia de Janeiro de 2026 (Copernicus EMS)", "IoU": np.nan, "F1": np.nan, "Kappa": np.nan, "ROC-AUC": r["auc_cheia_2026"]})
report = pd.DataFrame(rows).set_index(["modelo", "teste"])
report.round(3).to_csv(REPORTS / "33_relatorio_de_validacao.csv")
print(f"Modelo B escolhido: {best_b} | Modelo A escolhido: {best_a}")
report.round(3)
"""),
    ("md", """\
O Modelo A só tem AUC porque produz uma nota de risco, não um mapa de "água /
não água": IoU, F1 e Kappa não se aplicam a uma nota contínua.

## 5. O que está provado e o que não está

| Afirmação | Estado | Base |
|---|---|---|
| O Modelo B encontra a cheia de Janeiro de 2026 em sítios que não viu | provado, um evento | blocos espaciais, referência Copernicus |
| O Modelo B é melhor do que uma regra simples de radar | sim, por pouco | mesma referência |
| O algoritmo escolhido é o melhor dos quatro testados | empate técnico entre os três de árvores | diferença menor do que a variação entre blocos |
| O Modelo B funciona noutras cheias | **por provar** | não há outra cheia com referência |
| O mapa de suscetibilidade ordena bem o risco | provado, um evento | cheia de 2026, que o modelo nunca viu |
| As regras de alerta teriam avisado antes da cheia de 2026 | sim, com dados de reanálise | limites calculados até 2021 |
| As regras funcionam em tempo real | **por provar** | falta ligar à previsão do GloFAS e ao IMERG |
| Taxa de falsos alarmes | **desconhecida** | não há lista oficial de cheias |
| O indicador de turbidez (NDTI) segue o caudal e a estação | sim | 116 meses de Sentinel-2, notebook 34 |
| O indicador de turbidez corresponde a valores reais (NTU) | **por provar** | faltam amostras recolhidas no rio |
| O indicador de clorofila (NDCI) mede algas | **não**, neste rio | fica dominado pelos sedimentos |

## 6. O que fica pronto para a plataforma (Semana 4)

| Produto | Ficheiro |
|---|---|
| Mapa de suscetibilidade (30 m) | `data/processed/maps/modelo_a/suscetibilidade_marracuene_30m.tif` |
| Mapas mensais de água e cheia (10 m) | `data/processed/maps/modelo_b/agua_marracuene_<mês>_10m.tif` |
| Polígonos da cheia de Janeiro de 2026 | `data/processed/maps/modelo_b/cheia_marracuene_2026-01.gpkg` |
| Alertas diários 2006–2026 | `data/processed/series/alertas_diarios.csv` |
| Área de cheia por mês | `data/processed/series/modelo_b_area_mensal.csv` |
| Modelos treinados | `models/modelo_a_terreno.joblib`, `models/modelo_b_radar.joblib` |
| Exposição por classe de risco | `reports/semana_3/32_exposicao_por_classe.csv` |
| Indicadores de qualidade da água por troço e mês | `data/processed/series/qualidade_agua_mensal.csv` |"""),
]

# =============================================================================
NB["34_qualidade_da_agua"] = [
    header("34 - Qualidade da água do Incomáti (indicadores por satélite)",
           "Variáveis #51 (turbidez, NDTI) e #52 (clorofila, NDCI) da Parte I; componente de qualidade da água da plataforma",
           "Mede, mês a mês desde 2017, a cor da água do rio em quatro troços e transforma-a em indicadores de turbidez e de algas",
           "Sentinel-2 mensal (notebook 07, com a banda B5), canal real do rio (notebook 21), caudal e chuva (notebooks 22 e 23)",
           "`data/processed/series/qualidade_agua_mensal.csv`, mapas em `data/processed/maps/qualidade_agua/`, figuras em `reports/semana_3/`",
           """\
**O que um satélite consegue ver da qualidade da água: a cor.**

| O que está na água | Efeito na cor | Índice | Fórmula |
|---|---|---|---|
| Sedimentos em suspensão (água barrenta) | reflete mais vermelho do que verde | **NDTI** (turbidez) | (vermelho − verde) / (vermelho + verde) |
| Algas (clorofila-a) | reflete mais na banda B5 ("red edge") do que no vermelho | **NDCI** (clorofila) | (B5 − vermelho) / (B5 + vermelho) |

Quanto mais alto o índice, mais turva (NDTI) ou mais verde de algas (NDCI) está
a água. Os dois variam entre −1 e 1; na prática, no Incomáti, entre −0,25 e 0,10.

**O que o satélite NÃO consegue ver:** bactérias, esgoto, metais, pesticidas,
salinidade, oxigénio. Isso só com amostras recolhidas no rio.

**Como se mede aqui**

- Só entram píxeis do **canal do rio**, encolhido 20 m para deixar as margens de
  fora, e só quando o Sentinel-2 os viu como água aberta nesse mês.
- O rio é dividido em **quatro troços** com o mesmo número de píxeis, de norte
  (montante) para sul (foz).
- Para cada troço e mês guarda-se a **mediana** dos píxeis: um valor robusto, que
  não se deixa levar por um barco, uma nuvem mal mascarada ou um banco de areia."""),
    ("code", SETUP + """
from ete import water_quality as W
"""),
    ("md", "## 1. Onde se mede: o canal e os quatro troços"),
    ("code", """\
frame = W.river_frame(cfg)
print(f"área medida: {frame['core'].sum() * 100 / 1e6:.1f} km² de rio, em {frame['core'].sum():,} píxeis de 10 m")
from matplotlib.colors import ListedColormap
fig, ax = plt.subplots(figsize=(4.5, 9))
ax.imshow(np.where(frame["reach"] > 0, frame["reach"], np.nan)[::3, ::3], cmap=ListedColormap(["#1b9e77", "#d95f02", "#7570b3", "#e7298a"]), interpolation="nearest")
ax.set_title("Troços: verde = 1 montante, laranja = 2 médio,\\nroxo = 3 jusante, rosa = 4 foz"); ax.axis("off")
plt.tight_layout(); plt.savefig(REPORTS / "34_trocos_do_rio.png", dpi=110)
"""),
    ("md", "## 2. Série mensal 2017–2026"),
    ("code", """\
series_file = drivers.table(cfg, "qualidade_agua_mensal")
quality = W.monthly_series(cfg)                       # lê os 116 meses de Sentinel-2: cerca de 2 minutos
quality.round(5).to_csv(series_file, index=False)
river = quality[quality["troco"] == "rio inteiro"].set_index("month")
print(f"{river['ndti'].notna().sum()} de {len(river)} meses com medição; em média {100 * river['parte_do_troco_observada'].mean():.0f} % do canal observado como água")
river[["ndti", "ndci", "red", "pixeis_de_agua", "n_obs"]].describe().loc[["min", "25%", "50%", "75%", "max"]].round(3)
"""),
    ("code", """\
wide = lambda col: quality[quality["troco"] != "rio inteiro"].pivot(index="month", columns="troco", values=col).set_axis(
    pd.to_datetime(sorted(quality["month"].unique())), axis=0)
fig, axes = plt.subplots(2, 1, figsize=(14, 8), sharex=True)
wide("ndti").plot(ax=axes[0], color=["#1b9e77", "#d95f02", "#7570b3", "#e7298a"], linewidth=1)
axes[0].set_ylabel("NDTI"); axes[0].set_title("Turbidez (NDTI) por troço: mais alto = água mais barrenta")
wide("ndci").plot(ax=axes[1], color=["#1b9e77", "#d95f02", "#7570b3", "#e7298a"], linewidth=1, legend=False)
axes[1].set_ylabel("NDCI"); axes[1].set_title("Indicador de clorofila (NDCI) por troço: mais alto = mais verde de algas")
plt.tight_layout(); plt.savefig(REPORTS / "34_series_por_troco.png", dpi=110)
"""),
    ("md", """\
## 3. O padrão ao longo do ano

Mediana de cada mês do calendário, com todos os anos juntos. A faixa mostra a
metade central dos valores."""),
    ("code", """\
river["mes"] = river.index.str[5:].astype(int)
fig, axes = plt.subplots(1, 2, figsize=(14, 4))
for ax, col, colour in zip(axes, ["ndti", "ndci"], ["#b9770e", "#1e8449"]):
    g = river.groupby("mes")[col]
    ax.fill_between(range(1, 13), g.quantile(0.25), g.quantile(0.75), color=colour, alpha=0.25)
    ax.plot(range(1, 13), g.median(), color=colour, marker="o")
    ax.set_xticks(range(1, 13)); ax.set_xlabel("mês"); ax.set_ylabel(col.upper())
axes[0].set_title("Turbidez ao longo do ano"); axes[1].set_title("Indicador de clorofila ao longo do ano")
plt.tight_layout(); plt.savefig(REPORTS / "34_sazonalidade.png", dpi=110)
river.groupby("mes")[["ndti", "ndci"]].median().round(3).T
"""),
    ("md", """\
## 4. Os indicadores fazem sentido? Comparação com o caudal e a chuva

Não há medições no rio para confirmar os índices. Mas há uma verificação física:
quando o rio leva mais água, arrasta mais sedimentos, e a turbidez tem de subir.
Se o NDTI acompanhar o caudal, é sinal de que está a medir algo real."""),
    ("code", """\
drv = drivers.load_monthly_drivers(cfg)
both = river.join(drv[["q_mean", "q_max", "rain_basin_mm"]]).dropna(subset=["ndti", "q_mean"])
corr = both[["ndti", "ndci", "red", "q_mean", "q_max", "rain_basin_mm"]].corr(method="spearman").loc[["ndti", "ndci", "red"], ["q_mean", "q_max", "rain_basin_mm", "ndti"]]
corr.round(2).to_csv(REPORTS / "34_correlacao_com_caudal.csv")

fig, axes = plt.subplots(1, 3, figsize=(18, 4.6))
axes[0].scatter(both["q_mean"], both["ndti"], s=16, color="#b9770e"); axes[0].set_xscale("log")
axes[0].set_xlabel("caudal médio do mês (m³/s, escala logarítmica)"); axes[0].set_ylabel("NDTI"); axes[0].set_title(f"Turbidez e caudal (Spearman {corr.loc['ndti', 'q_mean']:.2f})")
axes[1].scatter(both["q_mean"], both["ndci"], s=16, color="#1e8449"); axes[1].set_xscale("log")
axes[1].set_xlabel("caudal médio do mês (m³/s, escala logarítmica)"); axes[1].set_ylabel("NDCI"); axes[1].set_title(f"Indicador de clorofila e caudal (Spearman {corr.loc['ndci', 'q_mean']:.2f})")
axes[2].scatter(both["ndti"], both["ndci"], s=16, color="#566573"); axes[2].set_xlabel("NDTI"); axes[2].set_ylabel("NDCI")
axes[2].set_title(f"Os dois índices um contra o outro (Spearman {corr.loc['ndci', 'ndti']:.2f})")
plt.tight_layout(); plt.savefig(REPORTS / "34_indices_vs_caudal.png", dpi=110)
corr.round(2)
"""),
    ("md", """\
**Leitura de especialista**

- **O NDTI acompanha o caudal.** A turbidez sobe nos meses de caudal alto e na
  época chuvosa, como a física manda. Sem medições no rio, esta é a melhor prova
  disponível de que o indicador de turbidez é fiável como medida **relativa**.
- **O NDCI não pode ser lido como "algas" neste rio.** Ele sobe e desce quase em
  conjunto com o NDTI (terceiro gráfico) e com o caudal. Em água barrenta, os
  sedimentos também aumentam a reflexão na banda B5, e o índice de clorofila fica
  contaminado. Um aumento do NDCI aqui quer dizer sobretudo "água mais turva",
  não "mais algas". Só seria um sinal de algas se subisse **sem** o NDTI subir,
  o que se pode vigiar (secção 6).

## 5. Mapas: um mês seco e o mês da cheia"""),
    ("code", """\
fig, axes = plt.subplots(1, 4, figsize=(15, 9))
for k, month in enumerate(["2022-08", "2026-01"]):
    file, ind, _ = W.quality_map(cfg, month)
    for ax, col, cmap, lim in [(axes[2 * k], "ndti", "YlOrBr", (-0.15, 0.08)), (axes[2 * k + 1], "ndci", "YlGn", (-0.10, 0.06))]:
        im = ax.imshow(ind[col][::3, ::3], cmap=cmap, vmin=lim[0], vmax=lim[1], interpolation="nearest")
        ax.set_facecolor("#dfe6e9"); ax.set_xticks([]); ax.set_yticks([])
        ax.set_title(f"{col.upper()} {month}"); plt.colorbar(im, ax=ax, shrink=0.5)
    print(file.relative_to(ROOT))
plt.tight_layout(); plt.savefig(REPORTS / "34_mapas_seco_vs_cheia.png", dpi=110)
"""),
    ("md", """\
Os mapas mostram só o canal do rio. Em Janeiro de 2026 (cheia) a água está mais
castanha em todo o rio do que em Agosto de 2022 (época seca).

## 6. Indicador para a plataforma: normal, elevado, muito elevado

Como não há valores em unidades reais, cada troço é comparado **com o seu próprio
histórico**: "elevado" = entre os 25 % de meses mais altos desse troço; "muito
elevado" = entre os 10 % mais altos. A última coluna assinala os meses em que o
indicador de clorofila está alto **sem** a turbidez estar: os únicos em que um
sinal de algas é plausível."""),
    ("code", """\
quality = quality.sort_values(["troco", "month"])
quality["turbidez"] = quality.groupby("troco")["ndti"].transform(W.relative_class)
quality["clorofila_ind"] = quality.groupby("troco")["ndci"].transform(W.relative_class)
quality["possivel_sinal_de_algas"] = quality["clorofila_ind"].isin(["elevado", "muito elevado"]) & (quality["turbidez"] == "normal")
quality.round(5).to_csv(series_file, index=False)

recent = quality[quality["month"] >= "2025-10"].pivot(index="month", columns="troco", values="turbidez")
print("Turbidez nos últimos 12 meses, por troço:"); display(recent)
algas = quality[quality["possivel_sinal_de_algas"] & (quality["troco"] != "rio inteiro")]
print(f"meses e troços com possível sinal de algas (clorofila alta, turbidez normal): {len(algas)}")
algas.groupby("troco").size().to_frame("meses")
"""),
    ("code", """\
order = ["normal", "elevado", "muito elevado"]
counts = quality[quality["troco"] == "rio inteiro"].assign(ano=lambda d: d["month"].str[:4]).groupby(["ano", "turbidez"]).size().unstack(fill_value=0).reindex(columns=order, fill_value=0)
ax = counts.plot.bar(stacked=True, figsize=(12, 3.8), color=["#d5dbdb", "#e59866", "#a04000"], ylabel="meses", title="Rio inteiro: meses por classe de turbidez em cada ano")
plt.tight_layout(); plt.savefig(REPORTS / "34_turbidez_por_ano.png", dpi=110)
"""),
    ("md", """\
## 7. Vegetação sobre a água

O canal do rio é onde há água quase sempre. Se um píxel do canal aparece verde
na imagem do mês, há plantas sobre a água: plantas flutuantes (como o
jacinto-de-água) ou plantas a crescer em bancos de areia descobertos. O satélite
não distingue a espécie. O indicador é a parte do canal coberta, por troço."""),
    ("code", """\
plants = W.channel_vegetation_series(cfg)
cover = 100 * plants.pivot(index="month", columns="troco", values="vegetacao")
cover.index = pd.PeriodIndex(cover.index, freq="M").to_timestamp()
fig, axes = plt.subplots(1, 2, figsize=(17, 4), gridspec_kw={"width_ratios": [2.2, 1]})
cover.plot(ax=axes[0], color=["#1e8449", "#2980b9", "#8e44ad", "#7f8c8d"]); axes[0].set_ylabel("% do canal com vegetação"); axes[0].set_xlabel("")
axes[0].set_title("Vegetação sobre a água, por troço e por mês")
cover.groupby(cover.index.year).mean().plot.bar(ax=axes[1], color=["#1e8449", "#2980b9", "#8e44ad", "#7f8c8d"], legend=False)
axes[1].set_ylabel("% do canal (média do ano)"); axes[1].set_xlabel(""); axes[1].set_title("Média por ano")
plt.tight_layout(); plt.savefig(REPORTS / "34_vegetacao_no_rio.png", dpi=110)
summary = pd.DataFrame({"mediana_%": cover.median(), "máximo_%": cover.max(), "mês_do_máximo": cover.idxmax().dt.strftime("%Y-%m"),
                        "área_máxima_ha": plants.groupby("troco")["area_ha"].max()})
summary.round(1).to_csv(REPORTS / "34_vegetacao_no_rio.csv")
summary.round(1)
"""),
    ("md", """\
**Leitura.** A vegetação sobre a água existe quase só no **troço a montante**.
Nos troços com maré praticamente não há: a água salobra não deixa crescer as
plantas flutuantes de água doce, o que é coerente.

Duas cautelas ao ler o gráfico:

- Os 4 a 5 % que se mantêm todos os anos no troço a montante são, muito
  provavelmente, vegetação fixa (ilhas e bancos dentro do canal). O que
  interessa são as **subidas acima desse nível**.
- O pico de 2018 (um terço do canal) é o sinal mais forte da série, mas em 2017
  e 2018 há menos imagens por mês do que nos anos seguintes. Deve ser confirmado
  com quem conhece o rio antes de ser apresentado como um episódio de plantas
  flutuantes.

Isto explica duas coisas vistas antes: o sinal de clorofila mais alto no troço a
montante, e a medição de turbidez menos fiável aí (notebook 35), porque as
plantas mudam de sítio e tapam partes diferentes do troço de imagem para imagem.

**Para a plataforma:** este indicador pode ser mostrado para o troço a montante
como "parte do rio coberta por plantas". Antes disso, uma visita ao local deve
confirmar de que plantas se trata.

## O que isto vale e o que não vale: leitura de especialista

**O que se pode afirmar com estes dados**

- Quando e em que troço a água esteve **mais turva do que o habitual**, mês a mês
  desde 2017. É um indicador sólido: segue o caudal e a estação, como esperado.
- A turbidez sobe com as cheias. Depois de uma cheia, é quando o tratamento de
  água para consumo fica mais difícil e os pontos de captação devem ser vigiados.

**Um sinal a verificar no terreno.** O troço 1 (montante) tem o indicador de
clorofila mais alto do que os outros desde 2022, muitas vezes sem a turbidez
subir. Pode ser real (algas ou plantas aquáticas flutuantes, como o jacinto-de-água),
mas esse troço é o mais estreito, e as margens e a vegetação podem estar a
entrar nos píxeis. Só uma visita ao local distingue as duas hipóteses.

**O que não se pode afirmar**

- **Valores absolutos.** Sem amostras do rio, não se sabe a quantos NTU (turbidez)
  ou mg/L (sedimentos, clorofila) corresponde um NDTI de 0,03.
- **Se a água é segura para beber, regar ou tomar banho.** A cor não mostra
  bactérias nem poluentes químicos.
- **Algas**, enquanto o NDCI estiver dominado pelos sedimentos.

**Fontes de erro conhecidas**

- A correção atmosférica do Sentinel-2 (L2A) foi feita para terra; sobre água,
  que reflete pouco, o erro relativo é maior.
- No troço da foz, a maré, a ondulação e o fundo visível em água rasa alteram a cor.
- A mediana mensal junta dias diferentes; um episódio de dois dias pode não aparecer.
- Nos meses de cheia há menos imagens sem nuvens (coluna `n_obs`).

**Como transformar o indicador em medição (proposta para a equipa)**

1. Recolher amostras em 3 ou 4 pontos fixos do rio, um por troço, em dias de
   passagem do Sentinel-2 (de 5 em 5 dias) e com céu limpo.
2. Medir no local a turbidez (turbidímetro portátil, em NTU) e a transparência
   (disco de Secchi); se possível, clorofila-a em laboratório.
3. Com 20 a 30 pares "amostra + imagem do mesmo dia" já se pode ajustar uma reta
   entre o NDTI e a turbidez em NTU, e testar se o NDCI responde à clorofila.
4. Até lá, a plataforma deve mostrar as classes relativas (normal / elevado /
   muito elevado) e dizer claramente que são indicadores de cor da água."""),
]


# =============================================================================
NB["35_qualidade_da_agua_validacao"] = [
    header("35 - Qualidade da água: o que é fiável e o que não é",
           "Validação da componente de qualidade da água (variáveis #51 e #52)",
           "Testa a sério os indicadores de turbidez: dois satélites independentes, um método em unidades reais, modelos de previsão",
           "Séries imagem a imagem do Sentinel-2 (2017–2026) e do Landsat 8/9 (2013–2026), extraídas com `scripts/update_water_quality_scenes.py`; histórico de caudal e chuva",
           "`models/modelo_turbidez.joblib`, `models/mare_maputo.json`, `models/turbidez_por_caudal.json`, tabelas e figuras em `reports/semana_3/`",
           """\
O notebook 34 construiu um indicador mensal. Este notebook responde a uma
pergunta mais exigente: **o que disto se pode mostrar a um público internacional
sem que um especialista o desmonte?** São feitos sete testes, e três deles
falham. Os que falham ficam aqui documentados, como a harmonização do Landsat.

| Teste | Pergunta | Resultado |
|---|---|---|
| 1 | A turbidez em unidades reais (FNU), por um método publicado, é repetível entre satélites? | **Não.** Rejeitada |
| 2 | O índice de cor NDTI é repetível entre satélites? | **Sim** |
| 3 | A turbidez acompanha o caudal? | **Sim**, de forma clara |
| 4 | Um modelo de IA só com caudal, chuva e época do ano prevê a turbidez? | **Não** |
| 5 | Juntando a maré, o modelo passa a prever? | **Sim** |
| 6 | A maré completa e a última medição por satélite melhoram a previsão? | **Sim** |
| 7 | Vento, chuva local, chuva por parte da bacia, treinar com os dois satélites? | **Não** melhoram: ficam de fora |

**Porque dois satélites.** Não há medições de turbidez feitas no Incomáti. A
melhor prova disponível é comparar dois instrumentos independentes: o Sentinel-2
(europeu) e o Landsat 8/9 (americano) têm sensores diferentes e correções
atmosféricas diferentes. Se, no mesmo dia e no mesmo troço, derem o mesmo valor,
a medição é repetível. Não prova que o valor esteja certo em absoluto, mas é a
condição mínima para ser levado a sério."""),
    ("code", SETUP + """
import json

from ete import forecast, forecast_models
from ete import water_quality as W
"""),
    ("md", """\
## 1. Os dados: uma medição por imagem

Em vez da mediana do mês, cada imagem de satélite dá uma medição por troço: a
mediana dos píxeis de água aberta, depois de retirar nuvens, bruma, reflexos do
sol e plantas flutuantes. Um troço só conta num dia se pelo menos um quarto dele
foi visto limpo."""),
    ("code", """\
s2, ls = W.load_scene_series(cfg, "sentinel2"), W.load_scene_series(cfg, "landsat89")
print(f"Sentinel-2 : {s2['date'].nunique()} dias com medição, {s2['date'].min().date()} a {s2['date'].max().date()}")
print(f"Landsat 8/9: {ls['date'].nunique()} dias com medição, {ls['date'].min().date()} a {ls['date'].max().date()}")
per_year = pd.DataFrame({"Sentinel-2": s2.groupby(s2["date"].dt.year)["date"].nunique(), "Landsat 8/9": ls.groupby(ls["date"].dt.year)["date"].nunique()}).fillna(0).astype(int)
ax = per_year.plot.bar(figsize=(12, 3.4), color=["#2980b9", "#7f8c8d"], ylabel="dias com medição", title="Dias com medição por ano")
plt.tight_layout(); plt.savefig(REPORTS / "35_dias_com_medicao.png", dpi=110)
"""),
    ("md", """\
## 2. Teste 1: turbidez em unidades reais (FNU). Rejeitada

Método de Dogliotti et al. (2011): turbidez = A × ρ / (1 − ρ / C), com a
reflectância ρ no infravermelho próximo (cerca de 860 nm), A = 3078,9 FNU e
C = 0,211. Os coeficientes foram conferidos na tabela 2 do artigo original. É um
método usado em estuários muito turvos de todo o mundo.

A comparação junta as medições dos dois satélites feitas com um dia de diferença
no máximo, no mesmo troço."""),
    ("code", """\
pairs = W.cross_sensor_pairs(s2, ls, max_days=1)
fnu = W.log_agreement(pairs["turbidez_fnu_s2"], pairs["turbidez_fnu_landsat"])
nir_r = np.corrcoef(pairs["nir_s2"], pairs["nir_landsat"])[0, 1]
print(f"{fnu['n']} pares | correlação {fnu['r']:.2f} | os dois satélites diferem tipicamente por um fator de {fnu['fator_tipico']:.1f}")
print(f"correlação da reflectância no infravermelho próximo entre satélites: {nir_r:.2f}")

fig, ax = plt.subplots(figsize=(5.5, 5.2))
ax.loglog(pairs["turbidez_fnu_s2"].clip(lower=1), pairs["turbidez_fnu_landsat"].clip(lower=1), ".", color="#c0392b", alpha=0.5)
ax.plot([1, 1000], [1, 1000], color="black", linewidth=0.8); ax.set_xlabel("Sentinel-2 (FNU)"); ax.set_ylabel("Landsat 8/9 (FNU)")
ax.set_title(f"Turbidez em FNU: os satélites não concordam (r = {fnu['r']:.2f})")
plt.tight_layout(); plt.savefig(REPORTS / "35_fnu_entre_satelites.png", dpi=110)
"""),
    ("md", """\
**Leitura.** Os pontos deviam estar sobre a linha. Não estão: o mesmo troço, no
mesmo dia, dá valores que diferem várias vezes entre os dois satélites.

**Porquê.** A água reflete muito pouco no infravermelho próximo. Num rio estreito
entre margens com vegetação, o que o satélite mede aí é sobretudo luz das margens
espalhada pela atmosfera e erro da correção atmosférica, não o sedimento. O
método funciona em estuários largos e muito turvos; no Incomáti, com estas
imagens, não.

**Decisão: a plataforma não mostra turbidez em FNU.** Um número com unidades dá
uma impressão de exatidão que os dados não sustentam.

## 3. Teste 2: o índice de cor NDTI. Aprovado

NDTI = (vermelho − verde) / (vermelho + verde). É uma razão entre duas bandas
do visível, onde a água reflete bem. Os erros que afetam as duas bandas por
igual anulam-se na divisão."""),
    ("code", """\
same_day = W.cross_sensor_pairs(s2, ls, max_days=0)
stats = lambda g: pd.Series({"pares": len(g), "correlação": np.corrcoef(g["ndti_s2"], g["ndti_landsat"])[0, 1],
                             "diferença_média": (g["ndti_landsat"] - g["ndti_s2"]).mean(),
                             "diferença_típica": np.sqrt(((g["ndti_landsat"] - g["ndti_s2"]) ** 2).mean())})
agreement = pd.concat([stats(same_day).to_frame("todos os troços, mesmo dia").T, pairs.groupby("troco").apply(stats, include_groups=False)])
agreement.round(3).to_csv(REPORTS / "35_ndti_entre_satelites.csv")

fig, ax = plt.subplots(figsize=(5.5, 5.2))
ax.plot(same_day["ndti_s2"], same_day["ndti_landsat"], ".", color="#1e8449", alpha=0.6)
ax.plot([-0.4, 0.15], [-0.4, 0.15], color="black", linewidth=0.8); ax.set_xlabel("Sentinel-2 (NDTI)"); ax.set_ylabel("Landsat 8/9 (NDTI)")
ax.set_title(f"NDTI no mesmo dia: os satélites concordam (r = {agreement.iloc[0]['correlação']:.2f})")
plt.tight_layout(); plt.savefig(REPORTS / "35_ndti_entre_satelites.png", dpi=110)
agreement.round(3)
"""),
    ("md", """\
**Leitura.** Dois satélites independentes dão praticamente o mesmo NDTI no mesmo
dia, sem desvio sistemático entre eles. A medição é repetível.

**Uma exceção:** no troço 1 (montante), o mais estreito, a concordância é mais
fraca. As medições desse troço são marcadas na plataforma como de fiabilidade
reduzida, e ele fica fora das contas seguintes.

**O que este teste não prova:** que o NDTI corresponda a tantas unidades de
turbidez. Isso só com amostras recolhidas no rio.

## 4. Teste 3: a turbidez acompanha o caudal. Aprovado

Para cada classe de caudal: em que parte dos dias medidos a turbidez esteve
"elevada" (entre os 25 % de dias mais turvos desse troço). As barras de erro são
o intervalo de 90 %: quanto menos dias, maior a incerteza."""),
    ("code", """\
table, skill, days = forecast_models.fit_turbidity_table(cfg)
table.round(3).to_csv(REPORTS / "35_turbidez_por_caudal.csv")
skill.round(3).to_csv(REPORTS / "35_turbidez_por_caudal_desempenho.csv")

fig, ax = plt.subplots(figsize=(10, 4.2))
share = 100 * table["turbidez_elevada"]
ax.bar(range(len(table)), share, color=["#d5dbdb", "#e8c9a0", "#e59866", "#ca6f1e", "#a04000"],
       yerr=[share - 100 * table["intervalo_min"], 100 * table["intervalo_max"] - share], capsize=5)
for i, (v, n) in enumerate(zip(share, table["dias_medidos"])):
    ax.text(i, 3, f"{v:.0f} %\\n({n} dias)", ha="center", fontsize=10)
ax.axhline(25, color="grey", linestyle=":"); ax.set_xticks(range(len(table)), table.index, rotation=8)
ax.set_ylabel("% dos dias com turbidez elevada"); ax.set_xlabel("caudal do dia em Marracuene (m³/s)")
ax.set_title("Quanto mais caudal, mais vezes a água está turva (linha pontilhada = 25 %, a média)")
plt.tight_layout(); plt.savefig(REPORTS / "35_turbidez_por_caudal.png", dpi=110)
table.round(2)
"""),
    ("md", """\
**Leitura.** A relação é clara e sobe sempre: com o rio baixo, a água raramente
está turva; com o caudal no nível laranja, está turva na grande maioria dos dias
medidos. É física simples (mais água arrasta mais sedimento) e os dados
confirmam-na.

É esta tabela que a plataforma usa para dizer o que esperar da turbidez quando
há previsão de caudal alto.

## 5. Teste 4: um modelo de IA sem a maré. Não chega

Um modelo de gradient boosting com o caudal de hoje e dos últimos dias, a chuva
acumulada e a época do ano, comparado com duas previsões simples. Cada ano é
previsto por um modelo que nunca o viu."""),
    ("code", """\
benchmark = forecast_models.turbidity_ml_benchmark(cfg)
benchmark.round(3).to_csv(REPORTS / "35_turbidez_modelo_de_ia.csv")
display(benchmark.round(3))
skill.round(3)
"""),
    ("md", """\
**Leitura honesta**

- O modelo de IA explica pouco mais da variação do NDTI do que a simples média
  do mês. A diferença não justifica um modelo mais complexo, e não melhora
  quando testado noutro satélite e noutros anos.
- A segunda tabela mostra o mesmo para a pergunta "vai estar elevada?": a tabela
  por caudal e a época do ano têm desempenhos próximos (`bss` perto de zero).
- A turbidez de um dia concreto depende de coisas que estes dados não veem:
  onde choveu, descargas de barragens, marés na foz, dragagens, vento. Nos
  troços de jusante e da foz, o valor muda bastante de uma imagem para a
  seguinte mesmo com o caudal estável, o que aponta para a maré. Por isso a
  plataforma mostra a mediana de várias imagens e não uma imagem isolada.

**Conclusão deste teste:** com caudal, chuva e época do ano não chega. Falta
uma causa. A secção seguinte testa a mais provável.

## 6. Teste 5: a maré. Aprovado

Nos troços de jusante e da foz, a cor da água muda muito de uma imagem para a
seguinte com o caudal estável. A hipótese: a maré. Quando a maré enche e vaza,
levanta sedimento do fundo e empurra água do estuário rio acima.

A fase da maré principal (a componente lunar M2, com período de 12,42 horas) é
conhecida com exatidão para qualquer momento, passado ou futuro, só a partir da
data e da hora. O gráfico mostra o índice de
cor de cada imagem contra a fase da maré à hora em que foi tirada."""),
    ("code", """\
skill, days, other = forecast_models.fit_turbidity_model(cfg)
skill.round(3).to_csv(REPORTS / "35_modelo_com_mare.csv")

phase = (np.degrees(np.arctan2(days["m2_sin"], days["m2_cos"])) + 360) % 360
fig, axes = plt.subplots(1, 3, figsize=(18, 4.4), sharey=True)
for ax, (reach, g) in zip(axes, days.groupby("troco")):
    ax.plot(phase[g.index], g["ndti"], ".", color="#7f8c8d", alpha=0.45, markersize=4)
    binned = g.groupby(pd.cut(phase[g.index], np.arange(0, 361, 30)), observed=True)["ndti"].median()
    ax.plot([i.mid for i in binned.index], binned, color="#c0392b", linewidth=2.2, marker="o")
    ax.set_title(reach); ax.set_xlabel("fase da maré M2 à hora da imagem (graus)"); ax.set_xticks(range(0, 361, 90))
axes[0].set_ylabel("NDTI (mais alto = mais turva)")
plt.suptitle("A cor da água segue a maré: cada ponto é uma imagem; a linha vermelha é a mediana"); plt.tight_layout()
plt.savefig(REPORTS / "35_ndti_e_mare.png", dpi=110)
"""),
    ("md", """\
**Leitura.** A linha vermelha desenha uma onda: a turbidez sobe e desce com a fase
da maré. A onda é maior na foz e no troço de jusante e menor no troço médio,
exatamente o que se espera de um efeito de maré, que se atenua rio acima.

Só a fase da maré já faz o modelo passar de 0,19 para 0,60 de variação explicada
(tabela mais abaixo, linhas "sem maré" e "maré só pela fase M2").

## 7. Teste 6: maré completa e última medição. Aprovado

Dois aperfeiçoamentos, cada um testado em separado antes de entrar:

- **Maré completa.** Em vez de uma só componente, a maré é calculada com 22
  componentes, ajustadas ao nível do mar hora a hora na Baía de Maputo (serviço
  Open-Meteo, 2023 a 2026). O modelo passa a conhecer a altura da maré, se está a
  encher ou a vazar, e se é maré viva ou maré morta.
- **Última medição.** O que o modelo não explica num dia tende a repetir-se nos
  dias e semanas seguintes. Por isso o modelo recebe também a última medição por
  satélite desse troço (do Sentinel-2 ou do Landsat) e a idade dela."""),
    ("code", """\
tide = json.loads((ROOT / "models" / "mare_maputo.json").read_text())
print(f"maré calculada contra o nível do mar dos últimos 12 meses (não usados no ajuste): R² = {tide['test_last_12_months']['r2']:.3f}, erro típico = {100 * tide['test_last_12_months']['rmse_m']:.0f} cm")

res = days["ndti"] - days["ndti_m2"]
rows = []
for reach, g in days.assign(res=res).groupby("troco"):
    g = g.set_index("date")["res"]
    for lag in (2, 3, 5, 10, 15, 20, 30):
        before = g.reindex(g.index - pd.Timedelta(days=lag)); ok = before.notna().to_numpy()
        rows.append({"troco": reach, "dias_antes": lag, "correlação": np.corrcoef(g.to_numpy()[ok], before.to_numpy()[ok])[0, 1]})
memory = pd.DataFrame(rows).pivot(index="dias_antes", columns="troco", values="correlação")

fig, axes = plt.subplots(1, 3, figsize=(18, 4.4))
week = pd.date_range("2026-01-10", "2026-01-17", freq="10min")
axes[0].plot(week, forecast_models.tide_height(cfg, week), color="#2980b9")
at = pd.date_range("2026-01-10", "2026-01-16") + pd.Timedelta(forecast_models.OVERPASS_UTC + ":00")
axes[0].plot(at, forecast_models.tide_height(cfg, at), "o", color="#c0392b", label="hora do satélite")
axes[0].set_ylabel("maré calculada (m)"); axes[0].legend(); axes[0].set_title("O satélite apanha a maré num ponto diferente em cada dia")
axes[0].set_xticks(pd.date_range("2026-01-10", "2026-01-17"), pd.date_range("2026-01-10", "2026-01-17").strftime("%d/%m"))
memory.plot(ax=axes[1], marker="o"); axes[1].set_ylim(0, 1); axes[1].set_xlabel("dias entre as duas medições"); axes[1].set_ylabel("correlação")
axes[1].set_title("O erro de um dia repete-se nos dias seguintes")
for ax, col, title in ((axes[2], "t_h", "Altura da maré à hora da imagem (m)"),):
    for reach, g in days.groupby("troco"):
        binned = g.groupby(pd.cut(g[col], 8), observed=True)["ndti"].median()
        ax.plot([i.mid for i in binned.index], binned, marker="o", label=reach)
    ax.set_xlabel(title); ax.set_ylabel("NDTI (mediana)"); ax.legend(); ax.set_title("Maré baixa de manhã: água mais turva")
plt.tight_layout(); plt.savefig(REPORTS / "35_mare_completa_e_memoria.png", dpi=110)
memory.round(2)
"""),
    ("md", """\
**Leitura**

- À esquerda: uma semana de maré calculada. Os pontos vermelhos são a hora de
  passagem do satélite: em cada dia apanha a maré numa altura diferente.
- Ao centro: o erro do modelo num dia está correlacionado com o erro de dias
  antes, e isso ainda se nota um mês depois. Há algo lento que o caudal e a maré
  não mostram (por exemplo, sedimento que ficou no rio depois de uma cheia, ou
  descargas de barragens). A última medição traz essa informação para o modelo.
- À direita: a relação direta entre a altura da maré e a cor da água.

A tabela seguinte tem o desempenho do modelo final e dos passos anteriores."""),
    ("code", """\
fig, axes = plt.subplots(1, 3, figsize=(19, 5))
colour = ["#1e8449" if n.startswith("modelo final:") else "#2980b9" if "Landsat" in n else "#95a5a6" for n in skill.index]
skill["auc"].plot.barh(ax=axes[0], color=colour); axes[0].invert_yaxis(); axes[0].axvline(0.5, color="grey", linestyle=":")
axes[0].set_xlim(0.4, 1); axes[0].set_ylabel(""); axes[0].set_xlabel("AUC para 'água mais turva do que o habitual' (0,5 = acaso)")
bins = pd.cut(days["prob_modelo_5d"], [0, 0.1, 0.25, 0.5, 0.75, 1.0], include_lowest=True)
rel = days.groupby(bins, observed=True)["elevada"].agg(["mean", "size"])
axes[1].bar(range(len(rel)), 100 * rel["mean"], color="#b9770e")
axes[1].set_xticks(range(len(rel)), [f"{i.left:.2f}-{i.right:.2f}\\n({n} dias)" for i, n in zip(rel.index, rel["size"])])
axes[1].set_xlabel("probabilidade dada pelo modelo"); axes[1].set_ylabel("% de dias que foram mesmo turvos"); axes[1].set_title("Quando o modelo diz X %, quantas vezes acontece?")
one = days[(days["troco"] == days["troco"].max()) & (days["date"] >= "2025-10-01")].set_index("date")
one["ndti"].plot(ax=axes[2], style="o", color="black", markersize=4, label="medido"); one["ndti_modelo_5d"].plot(ax=axes[2], color="#1e8449", label="modelo final")
one["ndti_sem"].plot(ax=axes[2], color="#95a5a6", linestyle="--", label="sem maré"); axes[2].legend(); axes[2].set_ylabel("NDTI")
axes[2].set_title(f"{days['troco'].max()}: último ano"); axes[2].set_xlabel("")
plt.tight_layout(); plt.savefig(REPORTS / "35_modelo_com_mare.png", dpi=110)
per_reach = pd.DataFrame({reach: {"dias": len(g), "r2": 1 - ((g["ndti"] - g["ndti_modelo_5d"]) ** 2).sum() / ((g["ndti"] - g["ndti"].mean()) ** 2).sum()}
                          for reach, g in days.groupby("troco")}).T
per_reach.round(3).to_csv(REPORTS / "35_modelo_por_troco.csv")
display(per_reach.round(3))
skill.round(3)
"""),
    ("md", """\
**Como ler a tabela**

- `r2`: parte da variação da cor da água que o modelo explica.
- `auc`: ao comparar um dia turvo com um dia normal, em quantos casos o modelo dá
  maior probabilidade ao dia turvo (0,5 = acaso; 1 = sempre).
- `bss`: quanto o modelo reduz o erro da probabilidade face à época do ano.
- As quatro primeiras linhas são o modelo final, conforme a idade da última
  medição. Quanto mais recente a medição, melhor. A linha "sem medição recente"
  é o que o modelo vale quando há mais de 30 dias de nuvens.
- As linhas a cinzento são os passos anteriores, para se ver de onde vem o ganho.
- As duas últimas linhas são o teste mais exigente: o modelo foi treinado só com
  o Sentinel-2 e é posto a prever os dias medidos pelo **Landsat**, outro
  satélite. Na última, além de outro satélite, são **outros anos** (2013 a 2016,
  antes de o Sentinel-2 existir), e a "última medição" é também do Landsat.

**As métricas são boas?** Para um indicador ambiental obtido só por satélite,
são sólidas: o modelo explica cerca de dois terços da variação, acerta a ordem
entre um dia turvo e um dia normal em quase 9 de cada 10 casos, e mantém o
desempenho num sensor e em anos que nunca viu, o que afasta a hipótese de ter
decorado os dados. Não são métricas de um instrumento de medição: cerca de um
terço da variação fica por explicar. O troço médio é o mais difícil. No gráfico
do meio vê-se também que, nas probabilidades mais altas, o modelo é um pouco
confiante demais: quando diz mais de 75 %, a água esteve mesmo turva em cerca de
três de cada quatro dias.

## 8. Teste 7: o que foi experimentado e não entrou

Foram testadas mais entradas, com o mesmo teste (ano deixado de fora). A regra,
decidida antes: uma entrada só fica se melhorar a probabilidade de "turbidez
elevada" (AUC ou erro da probabilidade), porque é isso que o boletim mostra, e
cada entrada a mais é mais uma coisa que pode falhar em produção.

O teste demora cerca de 15 minutos e corre à parte:
`.venv/bin/python scripts/experimento_turbidez_entradas.py`"""),
    ("code", """\
tested = pd.read_csv(REPORTS / "35_entradas_testadas.csv", index_col=0)
tested["ganho_r2"], tested["ganho_auc"] = tested["r2"] - tested["r2"].iloc[0], tested["auc"] - tested["auc"].iloc[0]
tested.round(3)
"""),
    ("md", """\
**Leitura.** Nenhuma destas entradas melhora a probabilidade de forma que se
note. O vento explica um pouco mais da variação do índice (`r2`), mas não muda o
acerto da previsão "vai estar mais turva". Treinar com os dois satélites juntos
também não ajuda; o Landsat fica melhor empregue como teste independente e como
fonte da última medição. Ficam todas de fora.

**E o troço a montante?** Com a regra "só contam as imagens que viram pelo menos
metade do troço", os dois satélites concordam melhor (tabela seguinte), mas menos
do que nos outros troços. O modelo, experimentado nesse troço, explicou apenas
cerca de 20 % da variação. Continua com a medição marcada como de fiabilidade
reduzida e sem previsão. O notebook 34 mostra uma causa provável: é o único
troço com vegetação sobre a água."""),
    ("code", """\
rows = []
for reach in sorted(s2["troco"].unique()):
    a, b = s2[s2["troco"] == reach], ls[ls["troco"] == reach]
    m = a.merge(b, on="date", suffixes=("", "_landsat"))
    for share in (0.0, 0.5, 0.7):
        keep = (m["pixeis"] >= share * a["pixeis"].quantile(0.95)) & (m["pixeis_landsat"] >= share * b["pixeis"].quantile(0.95))
        rows.append({"troco": reach, "parte_do_troço_vista": f"pelo menos {share:.0%}" if share else "qualquer", "pares": int(keep.sum()),
                     "correlação": np.corrcoef(m.loc[keep, "ndti"], m.loc[keep, "ndti_landsat"])[0, 1]})
coverage = pd.DataFrame(rows).pivot(index="troco", columns="parte_do_troço_vista", values="correlação")[["qualquer", "pelo menos 50%", "pelo menos 70%"]]
coverage.round(2).to_csv(REPORTS / "35_ndti_entre_satelites_por_cobertura.csv")
coverage.round(2)
"""),
    ("md", """\
## Limites do modelo, a dizer sempre

- Prevê a cor da água **à hora de passagem do satélite** (cerca das 9h30 locais).
  A maré faz a turbidez mudar ao longo do dia, e os satélites só veem essa hora.
- Prevê um **índice relativo**, não turbidez em unidades reais (secção 2).
- A maré é **calculada**, a partir de um modelo do nível do mar na Baía de Maputo,
  não de um marégrafo. As constantes são fixas: a variação lenta da maré ao longo
  de 18,6 anos não está incluída. Não inclui o efeito do vento e da pressão no
  nível do mar.
- Depende de a série de imagens estar atualizada
  (`scripts/update_water_quality_scenes.py`). Sem imagem nos últimos 30 dias, o
  modelo continua a funcionar, com menos acerto (linha "sem medição recente").
- O troço a montante fica sem previsão.

## Decisão para a plataforma

1. **A medição** de cada troço: mediana das imagens dos últimos 20 dias.
2. **A previsão** para as manhãs dos próximos 10 dias, com o modelo final
   (caudal, chuva, época do ano, maré completa e última medição), nos três
   troços em que a medição é fiável.
3. A tabela por nível de caudal (secção 4) fica como explicação simples do
   efeito das cheias.

## O que se pode dizer em público

| Afirmação | Pode dizer-se? | Base |
|---|---|---|
| "Medimos a cor da água do Incomáti por satélite, a cada 5 dias quando não há nuvens" | sim | secção 1 |
| "A medição é repetível: dois satélites independentes concordam" | sim | secção 3 |
| "A água fica mais turva quando o rio sobe, e sabemos quanto" | sim | secção 4 |
| "A cor da água no troço final do rio segue a maré" | sim | secções 6 e 7 |
| "Prevemos, para os próximos dias, as manhãs em que a água deve estar mais turva, com acerto medido" | sim, com os limites acima | secção 7 |
| "A turbidez é de X FNU" | **não** como medição; só "cerca de X, estimativa" em páginas técnicas | secção 2 e notebook 29 (a versão com a banda do vermelho concorda melhor entre satélites, mas não tem calibração local) |
| "A água é (ou não é) segura" | **não** | a cor não mostra bactérias nem químicos |
| "Detetamos algas" | **não** | notebook 34: o índice de clorofila é dominado pelos sedimentos |

**O passo que falta para subir de nível:** amostras de turbidez recolhidas no rio
em dias de passagem do satélite (20 a 30 chegam para começar). Com elas, o índice
pode ser convertido em unidades reais e este notebook volta a ser corrido. O
protocolo está em `docs/protocolo_de_campo_qualidade_da_agua.md`."""),
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
        print("escrito", f"notebooks/semana_3/{name}.ipynb")


if __name__ == "__main__":
    build()
