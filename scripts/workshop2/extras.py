"""Desafios extra da prática (pasta 2_pratica/extras): rede neuronal e IA na qualidade da água."""

import pandas as pd

from .comum import ANOS_TESTE, FERRAMENTAS_IA, LEGENDA, PRATICA, ROOT, code, escrever, md


def rede_neuronal():
    return [md(f"""
# Extra A · Uma rede neuronal: a ideia do Deep Learning

Na teoria vimos que o **Deep Learning** (aprendizagem profunda) usa **redes neuronais**: camadas de
"neurónios" artificiais, cada um faz uma conta simples e passa o resultado à camada seguinte. Com muitas
camadas e **muitíssimos exemplos**, estas redes reconhecem caras, vozes e texto (é o que está dentro do
ChatGPT, do Google Tradutor ou do desbloqueio facial do telemóvel).

Aqui treinamos uma rede **pequena** (2 camadas de 16 neurónios) com os mesmos pontos da equipa e comparamos
com o Random Forest. Pergunta: **quem precisa de mais exemplos?**

{LEGENDA}
"""),
            code(FERRAMENTAS_IA),
            code("""
from sklearn.neural_network import MLPClassifier      # uma rede neuronal (perceptrão multicamada)
from sklearn.pipeline import make_pipeline            # encadear passos
from sklearn.preprocessing import StandardScaler      # pôr todas as características na mesma escala (as redes precisam)

cheia = carregar("incomati_2026_cheia.npz")
extra = dict(np.load(encontrar("camadas_extra.npz")))
equipa = json.load(open(encontrar("exemplos_da_equipa.json")))
CARACTERISTICAS = BANDAS + INDICES
X, y = exemplos(cheia, equipa["2026"]["agua"], equipa["2026"]["nao_agua"], CARACTERISTICAS)
teste = (extra["ems_2026"] >= 0) & ~cheia["nuvem"]
verdade = extra["ems_2026"][teste]
print("Exemplos de 2026:", len(y), "píxeis")
"""),
            md("""
## Passo 1 · Treinar os dois modelos só com 2026 ▶️
"""),
            code("""
def treinar_os_dois(X, y):
    rede = make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16, 16), max_iter=800, random_state=0))
    floresta = RandomForestClassifier(n_estimators=100, random_state=0, n_jobs=-1)
    return {"Rede neuronal": rede.fit(X, y), "Random Forest": floresta.fit(X, y)}


def exame(modelos):
    for nome, m in modelos.items():
        p = m.predict_proba(tabela(cheia, CARACTERISTICAS))[:, 1].reshape(cheia["verde"].shape)
        linha = f"{nome:14s} IoU no exame EMS 2026: {notas(verdade, (p[teste] > 0.5).astype(int))['IoU']:.3f}"
        for ano in [2021, 2024]:
            img = carregar(f"incomati_{ano}_chuvosa.npz")
            pa = m.predict_proba(tabela(img, CARACTERISTICAS))[:, 1].reshape(img["verde"].shape)
            linha += f" | {ano}: encontra {100 * (pa[extra['verif_agua'] & ~img['nuvem']] > 0.5).mean():3.0f}% do rio"
        print(linha)


exame(treinar_os_dois(X, y))
"""),
            md("""
✍️ **Pergunta:** em 2026 as duas empatam. E em 2024 (água muito escura)? Qual generaliza melhor com poucos exemplos?

*Resposta:*

## Passo 2 · Dar exemplos de todos os anos ▶️

Juntamos os 5 + 5 pontos da equipa de cada um dos anos 2014, 2021, 2022, 2024 e 2025.
"""),
            code(f"""
Xs, ys = [X], [y]
for ano in {ANOS_TESTE}:
    img = carregar(f"incomati_{{ano}}_chuvosa.npz")
    xa, ya = exemplos(img, equipa[str(ano)]["agua"], equipa[str(ano)]["nao_agua"], CARACTERISTICAS)
    Xs.append(xa)
    ys.append(ya)
X_todos, y_todos = np.concatenate(Xs), np.concatenate(ys)
print("Exemplos de todos os anos:", len(y_todos), "píxeis")
exame(treinar_os_dois(X_todos, y_todos))
"""),
            md("""
## O que aprendemos

- Com **poucos exemplos e pouca variedade**, a rede neuronal aprende uma regra frágil e falha nos casos que nunca viu.
- Com **exemplos variados**, a rede e o Random Forest ficam parecidos, e **os dois melhoram** no exame de 2026.
- É por isso que o Deep Learning a sério usa **milhares ou milhões** de exemplos marcados por pessoas. Por exemplo,
  o mapa mundial de água e uso do solo **Dynamic World** (Google), que o projecto ETE usa, é uma rede neuronal treinada
  com dezenas de milhares de imagens marcadas à mão.
- Para poucos exemplos, o **Random Forest** é muitas vezes a melhor escolha: rápido, robusto e fácil de explicar.
""")]


def qualidade_da_agua():
    return [md(f"""
# Extra B · A IA e a qualidade da água

O satélite não mede a qualidade da água directamente, mas mede a **cor** da água. Com o índice **NDTI**
(verde contra vermelho) vemos quando a água fica mais **barrenta** (turbidez, sedimentos). A plataforma ETE
acompanha 9 troços do rio, todos os meses, desde 2006.

Aqui vamos: 1) ver 20 anos de turbidez em Marracuene; 2) calcular o "normal" de cada mês e as **anomalias**;
3) tentar **prever** os meses com água mais barrenta do que o normal com Machine Learning... e descobrir
porque é que isso falha.

{LEGENDA}
"""),
            code("""
import os
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from sklearn.ensemble import RandomForestClassifier
from sklearn import metrics


def encontrar(nome):                                   # procura o ficheiro na pasta dados/ (ao lado, ou uma pasta acima)
    for pasta in ["dados", os.path.join("..", "dados"), "."]:
        if os.path.exists(os.path.join(pasta, nome)):
            return os.path.join(pasta, nome)
    raise FileNotFoundError(f"Não encontrei {nome}. Abra o Jupyter na pasta Workshop_2/2_pratica.")


serie = pd.read_csv(encontrar("qualidade_agua_mensal.csv"))
print(serie["nome"].unique())
"""),
            md("""
## Passo 1 · 20 anos de turbidez em Marracuene ▶️

`ndti` mais alto = água mais barrenta. Por baixo, o caudal do rio no mesmo mês (dois gráficos separados, com o mesmo
eixo do tempo: dois eixos verticais no mesmo gráfico enganam o olho).
"""),
            code("""
TROCO = "Q8"                                  # ✏️ experimente "Q1" (fronteira) ou "Q9" (foz)
q = serie[(serie["troco"] == TROCO)].dropna(subset=["ndti"]).copy()
q["data"] = pd.to_datetime(q["month"])

fig, eixos = plt.subplots(2, 1, figsize=(12, 6), sharex=True)
eixos[0].plot(q["data"], q["ndti"], ".-", color="saddlebrown")
eixos[0].set_ylabel("NDTI (turbidez)")
eixos[0].set_title(f"{q['nome'].iloc[0]}: turbidez medida por satélite (em cima) e caudal do rio (em baixo)")
eixos[1].plot(q["data"], q["caudal_m3s"], color="steelblue")
eixos[1].set_ylabel("Caudal (m³/s)")
plt.tight_layout()
plt.show()
print(len(q), "meses com medição, de", q["month"].min(), "a", q["month"].max())
"""),
            md("""
## Passo 2 · O "normal" de cada mês e as anomalias ▶️

A água é naturalmente mais barrenta na época das chuvas. Por isso comparamos cada mês com **o mesmo mês nos
outros anos** (a mediana). A diferença é a **anomalia**: positiva = mais barrenta do que o habitual.
"""),
            code("""
normal = q.groupby("mes_do_ano")["ndti"].median()
q["anomalia"] = q["ndti"] - q["mes_do_ano"].map(normal)

fig, eixos = plt.subplots(1, 2, figsize=(14, 4))
eixos[0].bar(normal.index, normal.values, color="saddlebrown")
eixos[0].set_title("O normal de cada mês (mediana do NDTI)")
eixos[0].set_xlabel("mês")
eixos[1].bar(q["data"], q["anomalia"], width=25, color=np.where(q["anomalia"] > 0, "saddlebrown", "steelblue"))
eixos[1].set_title("Anomalia: castanho = mais barrenta do que o normal")
plt.tight_layout()
plt.show()
print("Os 5 meses mais barrentos em relação ao normal:")
print(q.nlargest(5, "anomalia")[["month", "ndti", "anomalia", "caudal_m3s", "chuva_mm"]].round(3).to_string(index=False))
"""),
            md("""
## Passo 3 · A IA consegue prever os meses mais barrentos? ▶️

Rótulo: o mês teve água **mais barrenta do que o normal** (classe "elevada" ou "muito elevada" na plataforma).
Características: o caudal, a chuva e o mês. Treinamos com 2006–2018 e testamos com 2019–2026 (**anos que o modelo nunca viu**).
"""),
            code("""
d = q.dropna(subset=["caudal_m3s", "chuva_mm"]).copy()
d["barrenta"] = d["classe"].isin(["elevada", "muito elevada"]).astype(int)
d["log_caudal"] = np.log1p(d["caudal_m3s"])
CARACTERISTICAS = ["log_caudal", "chuva_mm", "mes_do_ano"]
treino, teste = d[d["ano"] <= 2018], d[d["ano"] >= 2019]

modelo = RandomForestClassifier(n_estimators=300, random_state=0, min_samples_leaf=3).fit(treino[CARACTERISTICAS], treino["barrenta"])
p = modelo.predict_proba(teste[CARACTERISTICAS])[:, 1]
print(f"Meses de treino: {len(treino)} · meses de teste: {len(teste)} ({teste['barrenta'].sum()} barrentos)")
print(f"ROC-AUC no teste: {metrics.roc_auc_score(teste['barrenta'], p):.2f}   (0,5 = ao calhas; 1 = perfeito)")
print(f"Acerto: {metrics.accuracy_score(teste['barrenta'], p > 0.5):.2f}  · acerto de quem diz sempre 'normal': {1 - teste['barrenta'].mean():.2f}")
print("Importâncias:", dict(zip(CARACTERISTICAS, modelo.feature_importances_.round(2))))
"""),
            md("""
✍️ **Pergunta:** o modelo é melhor do que dizer sempre "normal"? O que pode estar a faltar?

*Resposta:*

## O que aprendemos

- **A IA não faz milagres.** Sem as pistas certas, não aprende nada útil, por mais árvores que tenha.
- Em Marracuene, perto da foz, a cor da água depende muito da **maré** (a água do mar entra e sai do rio).
  No projecto ETE, juntar a maré no momento da imagem fez o modelo de turbidez passar de quase inútil para
  uma boa previsão (ROC-AUC perto de 0,9).
- O satélite mede a **cor** da água (turbidez, sedimentos, um sinal de algas e plantas flutuantes, temperatura
  da superfície). **Não** mede pH, oxigénio, nutrientes, metais nem bactérias, e nunca diz se a água é **própria
  para beber**.
""")]


def construir():
    pasta = PRATICA / "extras"
    serie = pd.read_csv(ROOT / "plataforma/dados/qualidade/serie_mensal.csv")
    colunas = ["troco", "nome", "month", "ano", "mes_do_ano", "fonte", "fiabilidade", "ndti", "vegetacao", "temp_c",
               "chuva_mm", "caudal_m3s", "classe"]
    serie[colunas].to_csv(PRATICA / "dados/qualidade_agua_mensal.csv", index=False)
    return [escrever(rede_neuronal(), pasta / "A_rede_neuronal_deep_learning.ipynb", "ETE WS2 · Extra A · rede neuronal"),
            escrever(qualidade_da_agua(), pasta / "B_ia_e_qualidade_da_agua.ipynb", "ETE WS2 · Extra B · qualidade da água")]
