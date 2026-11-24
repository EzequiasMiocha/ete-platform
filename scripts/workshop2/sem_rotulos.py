"""Partes E e F da prática: aprender sem rótulos (K-means) e prever um número (regressão do caudal).

Notebook 2_pratica/3_sem_rotulos_e_numeros.ipynb e a versão completa do facilitador.
"""

from .comum import (ERROS_COMUNS, FAC, FERRAMENTAS_IA, HORAS, HORIZONTE, K_GRUPOS, LEGENDA, PISTAS_CAUDAL, PRATICA,
                    TRABALHAR_NO_JUPYTER, ULTIMO_ANO_TREINO, code, escrever, fmt, md)


PAINEL = f"""
# ⚙️ PAINEL DE CONFIGURAÇÃO: mude os valores aqui e volte a correr as células da parte que quer ver
CONFIG = {{
    # Parte E · o K-means (agrupamento, sem rótulos)
    "caracteristicas": BANDAS + INDICES,     # as pistas de cada píxel (pode juntar TERRENO)
    "k_grupos": {K_GRUPOS},                           # quantos grupos (experimente 2, 3 ou 6)
    "inicializacoes": 3,                     # quantas vezes recomeça com centros diferentes (fica o melhor resultado)
    # Parte F · a regressão do caudal
    "dias_a_frente": {HORIZONTE},                      # prever o caudal daqui a quantos dias (experimente 1 ou 7)
    "pistas_caudal": {PISTAS_CAUDAL},
    "ultimo_ano_de_treino": {ULTIMO_ANO_TREINO},            # o treino vai até este ano; o exame é o que vem depois
    "profundidades": [1, 2, 3, 4, 5, 6, 8, 10, 12, 15, 20],   # as árvores de regressão da curva do sobreajuste
    "semente": 0,                            # o mesmo número dá sempre o mesmo resultado
}}
print("Configuração pronta:", ", ".join(f"{{chave}} = {{valor}}" for chave, valor in CONFIG.items() if chave != "caracteristicas"))
"""


def celulas():
    return [md(f"""
# Partes E e F · Aprender sem rótulos e prever números

**Workshop de Estudantes 2 · Projecto EYES TO EARTH (ETE) · 21 de Novembro de 2026**

Nas Partes B a D treinámos uma **classificação supervisionada**: exemplos com rótulos, resposta = uma categoria.
Agora vamos treinar os outros dois tipos de modelo que vimos na teoria:

| Parte | Tipo de aprendizagem | Pergunta | Tempo |
| --- | --- | --- | --- |
| E | **Não supervisionada** (agrupamento, K-means) | Sem nenhum rótulo, o computador consegue separar a água sozinho? | 15 min |
| F | **Supervisionada, regressão** | Conseguimos prever o **caudal** do rio daqui a {HORIZONTE} dias, um número em m³/s? | 15 min |

{LEGENDA}
{TRABALHAR_NO_JUPYTER}
"""),
            md("""
## As ferramentas (bibliotecas) que vamos usar

| Biblioteca | Para que serve |
| --- | --- |
| `numpy` (`np`), `matplotlib` (`plt`) | Contas com tabelas de números e gráficos (como no notebook 2) |
| `scikit-learn` (`sklearn`) | `KMeans` (agrupar), `LinearRegression` (a recta) e `DecisionTreeRegressor` (árvore que dá um número) |
| `pandas` (`pd`) | Tabelas com datas, como uma folha de Excel: os 20 anos de caudal e chuva |

## Célula 0 · Ligar as ferramentas ▶️

A mesma Célula 0 do notebook 2. Corra sem mudar nada.
"""),
            code(FERRAMENTAS_IA),
            md("""
## ⚙️ Painel de configuração ▶️

Todas as escolhas destas duas partes estão aqui: o número de grupos do K-means, quantos dias à frente queremos
prever o caudal, as pistas da regressão, o ano que separa o treino do exame. Na primeira vez, corra sem mudar nada.
Para experimentar, mude um valor, corra esta célula e volte a correr as células da parte que quer ver.
"""),
            code(PAINEL),
            md(f"""
---
# Parte E · Agrupar sem rótulos: o K-means (15 min)

Na aprendizagem **não supervisionada** não há respostas certas. O computador recebe só as características
(`X`) e procura **grupos de píxeis parecidos**. O **K-means** faz assim:

1. espalha **K** centros ao acaso;
2. cada píxel junta-se ao centro mais perto (o mais parecido);
3. cada centro muda-se para o meio do seu grupo;
4. repete os passos 2 e 3 até os grupos não mudarem.

No fim, o computador sabe que os píxeis do grupo 1 são parecidos entre si, mas **não sabe que se chamam "água"**.
Somos nós que damos o nome aos grupos.

### Passo E1 · A tabela, sem rótulos ▶️
"""),
            code("""
cheia = carregar("incomati_2026_cheia.npz")
extra = dict(np.load(encontrar("camadas_extra.npz")))
juntar_terreno(cheia, extra)                           # o terreno fica disponível como pista (ver o painel ⚙️)
CARACTERISTICAS = CONFIG["caracteristicas"]

X = tabela(cheia, CARACTERISTICAS)                     # uma linha por píxel, uma coluna por característica
valido = (cheia["zona"] & ~cheia["nuvem"]).ravel()     # só os píxeis do distrito, sem nuvens
print("A tabela tem", X.shape[0], "píxeis e", X.shape[1], "características.")
print("Píxeis usados para aprender:", valido.sum())
print("Rótulos: nenhum! Ninguém disse ao computador o que é cada píxel.")
"""),
            md(f"""
### Passo E2 · Treinar o K-means ✏️

Repare: `fit(X)` **sem** `y`. É isso que quer dizer "não supervisionada". O `StandardScaler` põe todas as
características na mesma escala, porque o K-means mede distâncias entre píxeis.
"""),
            code(f"""
from sklearn.cluster import KMeans                     # o K-means: junta os píxeis parecidos em K grupos
from sklearn.preprocessing import StandardScaler       # pôr todas as características na mesma escala
from sklearn.pipeline import make_pipeline             # encadear os dois passos num só modelo

K = CONFIG["k_grupos"]                                 # ✏️ quantos grupos? Mude no painel ⚙️ (experimente 2, 3 ou 6)
agrupador = make_pipeline(StandardScaler(), KMeans(n_clusters=K, n_init=CONFIG["inicializacoes"],
                                                   random_state=CONFIG["semente"]))
agrupador.fit(X[valido])                               # APRENDER SEM RÓTULOS: só há X, não há y

grupos = agrupador.predict(X).reshape(cheia["verde"].shape)      # o número do grupo de cada píxel
contagem = np.bincount(grupos.ravel()[valido], minlength=K)
for g in range(K):
    print(f"Grupo {{g}}: {{100 * contagem[g] / contagem.sum():4.1f}}% dos píxeis")
"""),
            md("""
### Passo E3 · O mapa dos grupos ▶️

Cada cor é um grupo. Compare com a cor natural: que grupo parece ser a água? E a vegetação? E a areia?
"""),
            code("""
from matplotlib.colors import ListedColormap

cores = ListedColormap(plt.get_cmap("tab10").colors[:K])                   # uma cor por grupo
mapa_grupos = np.where(cheia["zona"] & ~cheia["nuvem"], grupos, np.nan)     # sem nuvens nem fora do distrito

fig, eixos = plt.subplots(1, 2, figsize=(14, 9))
eixos[0].imshow(cor_natural(cheia))
eixos[0].set_title("Cor natural, 24 jan 2026")
figura = eixos[1].imshow(mapa_grupos, cmap=cores, vmin=-0.5, vmax=K - 0.5, interpolation="nearest")
eixos[1].set_title(f"Os {K} grupos do K-means (sem rótulos)")
fig.colorbar(figura, ax=eixos[1], ticks=range(K), shrink=0.6, label="número do grupo")
for e in eixos:
    e.axis("off")
plt.tight_layout()
plt.show()
"""),
            md("""
### Passo E4 · Dar nome aos grupos ✏️

O computador não sabe os nomes. **Vocês** decidem que grupo é a água, olhando para o mapa. Se a água ficou em
dois grupos (por exemplo, a água barrenta e a água escura), escrevam os dois: `[0, 3]`.
"""),
            code("""
GRUPOS_AGUA = None          # ✏️ escrevam o número do grupo da água, por exemplo [1]

g_validos = grupos.ravel()[valido]
mndwi_validos = cheia["mndwi"].ravel()[valido]          # o MNDWI só ajuda a dar nome aos grupos (o K-means não o precisa)
mndwi_medio = [np.nanmean(mndwi_validos[g_validos == g]) for g in range(K)]
for g in range(K):
    print(f"Grupo {g}: MNDWI médio {mndwi_medio[g]:+.2f}")
if GRUPOS_AGUA is None:
    GRUPOS_AGUA = [g for g in range(K) if mndwi_medio[g] > 0]
    print(f"\\n✏️ Ainda não escolheram. Por agora uso a regra do Workshop 1 (MNDWI médio maior do que 0): {GRUPOS_AGUA}")
print("Grupos a que chamamos 'água':", GRUPOS_AGUA)
"""),
            md("""
### Passo E5 · O exame: o K-means encontrou a água? ▶️

O mesmo exame do notebook 2: as amostras do Copernicus EMS. O K-means nunca viu um rótulo, nem do exame nem nosso.
"""),
            code("""
ems = extra["ems_2026"]                                 # 1 água, 0 não água, -1 sem rótulo
teste = (ems >= 0) & ~cheia["nuvem"]
verdade = ems[teste]
agua_kmeans = np.isin(grupos, GRUPOS_AGUA)

mostrar_notas("K-means (sem rótulos)", notas(verdade, agua_kmeans[teste].astype(int)))
mostrar_notas("Regra MNDWI > 0 (Workshop 1)", notas(verdade, (cheia["mndwi"][teste] > 0).astype(int)))
r = notas(verdade, agua_kmeans[teste].astype(int))
area = (agua_kmeans & cheia["zona"] & ~cheia["nuvem"]).sum() * 0.09
print(f"\\nQUADRO DA TURMA -> K-means | K = {K} | grupos de água {GRUPOS_AGUA} | IoU {r['IoU']:.3f} | {area:.0f} ha de água")

plt.figure(figsize=(7, 10))
plt.imshow(agua_kmeans & cheia["zona"] & ~cheia["nuvem"], cmap="Blues")
plt.title(f"A água segundo o K-means: {area:.0f} ha")
plt.axis("off")
plt.show()
"""),
            md(f"""
✍️ **Perguntas:** o K-means nunca viu um rótulo. Como é que conseguiu separar a água? Quem lhe deu o nome "água"?
Experimentem `"k_grupos": 2`, `3` e `6` no painel ⚙️ e corram outra vez do E2 ao E5: o que muda?

*Resposta:*

✍️ **Pergunta:** que **vantagem** e que **desvantagem** tem aprender sem rótulos?

*Resposta:*

---
# Parte F · Prever um número: o caudal daqui a {HORIZONTE} dias (15 min)

Uma **regressão** é aprendizagem supervisionada em que a resposta é um **número**. Aqui: o caudal do Incomáti
em Marracuene daqui a {HORIZONTE} dias, em m³/s. As pistas são o caudal de hoje e a chuva na bacia nos últimos
7, 14 e 30 dias. Os rótulos vêm... do futuro: o caudal que o rio teve, de facto, {HORIZONTE} dias depois.

Os dados (pasta `dados/`): caudal diário do **GloFAS** (Copernicus) e chuva diária na bacia do **CHIRPS**, de 2006 a 2026.

### Passo F1 · Vinte anos de caudal e chuva ▶️
"""),
            code(f"""
import pandas as pd                                    # pandas: tabelas com datas, como uma folha de Excel

serie = pd.read_csv(encontrar("caudal_e_chuva_diarios.csv"), parse_dates=["data"])
DIAS = CONFIG["dias_a_frente"]                         # prever o caudal daqui a DIAS dias (mude no painel ⚙️)
serie["caudal_futuro"] = serie["caudal_m3s"].shift(-DIAS)       # o rótulo: o caudal que o rio teve DIAS dias depois
serie = serie.dropna()
print(len(serie), "dias, de", serie["data"].min().date(), "a", serie["data"].max().date())

fig, eixos = plt.subplots(2, 1, figsize=(14, 6), sharex=True)   # dois gráficos, um por cima do outro
eixos[0].plot(serie["data"], serie["caudal_m3s"], color="steelblue", lw=0.8)
eixos[0].set_ylabel("Caudal (m³/s)")
eixos[0].set_title("O Incomáti em Marracuene: o caudal (em cima) e a chuva na bacia (em baixo)")
eixos[1].plot(serie["data"], serie["chuva_7d_mm"], color="gray", lw=0.8)
eixos[1].set_ylabel("Chuva de 7 dias (mm)")
plt.tight_layout()
plt.show()
serie.tail()
"""),
            md(f"""
### Passo F2 · Treino e exame: o exame é o futuro ✏️

Quando o tempo importa, **não** se escolhem dias ao acaso para o exame: um dia e o dia seguinte são quase
iguais, e seria como copiar. Treinamos com o passado (2006 a {ULTIMO_ANO_TREINO}) e fazemos o exame com o futuro
({ULTIMO_ANO_TREINO + 1} a 2026), que o modelo nunca viu. Inclui a grande cheia de janeiro de 2026.
"""),
            code(f"""
PISTAS = CONFIG["pistas_caudal"]                       # ✏️ mude no painel ⚙️ (experimente tirar "caudal_m3s")
ULTIMO = CONFIG["ultimo_ano_de_treino"]
treino = serie[serie["data"].dt.year <= ULTIMO]        # aprender com o passado
exame = serie[serie["data"].dt.year > ULTIMO]          # o exame é o FUTURO
print(f"Treino: {{len(treino)}} dias (até {{ULTIMO}}) | Exame: {{len(exame)}} dias (de {{ULTIMO + 1}} em diante)")
print(f"Maior caudal no treino: {{treino['caudal_m3s'].max():.0f}} m³/s | no exame: {{exame['caudal_m3s'].max():.0f}} m³/s")
"""),
            md("""
### Passo F3 · A regressão linear: a equação que melhor passa pelos pontos ▶️

O modelo aprende um número para cada pista (o **coeficiente**). As notas de uma regressão são diferentes das da
classificação:
- **erro médio (MAE)**: em média, quantos m³/s a previsão erra (quanto menor, melhor);
- **R²**: quanto do sobe e desce do rio o modelo explica (1 = tudo, 0 = nada).
"""),
            code("""
from sklearn.linear_model import LinearRegression      # regressão linear: a recta (ou o plano) que melhor passa pelos pontos

recta = LinearRegression()
recta.fit(treino[PISTAS], treino["caudal_futuro"])      # APRENDER: X = as pistas, y = o caudal DIAS dias depois

print("A equação que o modelo aprendeu (o sinal + ou - diz se a pista faz subir ou descer a previsão):")
equacao = " ".join(f"{c:+.2f} × {p}" for c, p in zip(recta.coef_, PISTAS))   # :+ mostra sempre o sinal
print(f"  caudal daqui a {DIAS} dias = {equacao} {recta.intercept_:+.1f}")

previsto = recta.predict(exame[PISTAS])                 # PREVER os dias do exame
erro_medio = metrics.mean_absolute_error(exame["caudal_futuro"], previsto)
r2 = metrics.r2_score(exame["caudal_futuro"], previsto)
igual_a_hoje = metrics.mean_absolute_error(exame["caudal_futuro"], exame["caudal_m3s"])
print(f"\\nNo exame: erro médio (MAE) {erro_medio:.0f} m³/s | R² {r2:.2f}")
print(f"Para comparar, dizer 'daqui a {DIAS} dias fica igual a hoje' erra em média {igual_a_hoje:.0f} m³/s")
"""),
            md("""
### Passo F4 · O exame em gráficos ▶️

À esquerda, a cheia de janeiro de 2026: o que aconteceu e o que o modelo tinha previsto DIAS dias antes, com os
limites de alerta. À direita, todos os dias do exame: se o modelo fosse perfeito, os pontos ficavam em cima da linha.
"""),
            code("""
janela = ((exame["data"] >= "2025-12-20") & (exame["data"] <= "2026-02-15")).to_numpy()
dia_previsto = exame["data"][janela] + pd.Timedelta(days=DIAS)          # o dia a que a previsão se refere

fig, eixos = plt.subplots(1, 2, figsize=(16, 6))
eixos[0].plot(dia_previsto, exame["caudal_futuro"][janela], color="black", lw=2, label="o que aconteceu")
eixos[0].plot(dia_previsto, previsto[janela], color="tab:blue", lw=2, label=f"o que o modelo previu {DIAS} dias antes")
for limite, nome, cor in [(164, "amarelo", "goldenrod"), (376, "laranja", "darkorange"), (970, "vermelho", "firebrick")]:
    eixos[0].axhline(limite, color=cor, ls="--", lw=1)
    eixos[0].text(dia_previsto.iloc[0], limite + 40, f"alerta {nome}", color=cor)
eixos[0].set_ylabel("Caudal (m³/s)")
eixos[0].set_title("A cheia de janeiro de 2026")
eixos[0].legend(loc="upper right")
fig.autofmt_xdate()

eixos[1].scatter(exame["caudal_futuro"], previsto, s=6, alpha=0.4)
maximo = exame["caudal_futuro"].max()
eixos[1].plot([0, maximo], [0, maximo], color="black", lw=1, label="previsão perfeita")
eixos[1].set_xlabel("Caudal que aconteceu (m³/s)")
eixos[1].set_ylabel("Caudal previsto (m³/s)")
eixos[1].set_title(f"Todos os dias do exame: erro médio {erro_medio:.0f} m³/s")
eixos[1].legend()
plt.tight_layout()
plt.show()
"""),
            md("""
### Passo F5 · Uma árvore de regressão e o sobreajuste ▶️

Uma árvore também pode dar um número: em vez de "água" ou "terra", cada folha tem um caudal. Quanto mais
**profunda** (mais perguntas seguidas), mais o modelo se ajusta ao treino. Vamos desenhar o gráfico clássico
da teoria, com os nossos dados: a nota no treino e a nota no exame, para cada profundidade.
"""),
            code("""
from sklearn.tree import DecisionTreeRegressor         # árvore de regressão: perguntas de sim ou não que acabam num número

profundidades = CONFIG["profundidades"]                # as árvores da curva (mude no painel ⚙️)
nota_treino, nota_exame = [], []
for prof in profundidades:
    arvore = DecisionTreeRegressor(max_depth=prof, random_state=CONFIG["semente"]).fit(treino[PISTAS], treino["caudal_futuro"])
    nota_treino.append(metrics.r2_score(treino["caudal_futuro"], arvore.predict(treino[PISTAS])))
    nota_exame.append(metrics.r2_score(exame["caudal_futuro"], arvore.predict(exame[PISTAS])))

plt.figure(figsize=(9, 5))
plt.plot(profundidades, nota_treino, "o-", label="nota no treino (o que já viu)")
plt.plot(profundidades, nota_exame, "o-", label="nota no exame (o futuro)")
plt.axhline(r2, color="gray", ls=":", label=f"regressão linear no exame ({r2:.2f})")
plt.xlabel("Profundidade da árvore (quantas perguntas seguidas)")
plt.ylabel("R² (1 = perfeito)")
plt.title("Sobreajuste: a nota do treino sobe sempre, a do exame não")
plt.legend()
plt.grid(alpha=0.3)
plt.show()

melhor = profundidades[int(np.argmax(nota_exame))]
print(f"Melhor profundidade no exame: {melhor} (R² {max(nota_exame):.2f}). "
      f"Com 20 perguntas: treino {nota_treino[-1]:.2f}, exame {nota_exame[-1]:.2f}.")
print(f"\\nQUADRO DA TURMA -> regressão | erro médio da recta {erro_medio:.0f} m³/s | R² {r2:.2f} | melhor árvore: profundidade {melhor}")
"""),
            md("""
✍️ **Pergunta:** a recta previu a subida da cheia de janeiro de 2026 a tempo de dar um alerta laranja? Porquê?

*Resposta:*

✍️ **Pergunta:** no gráfico do Passo F5, a partir de que profundidade a árvore começa a **decorar** o treino?
Porque é que a nota do exame desce?

*Resposta:*

---
## O que aprendemos

1. **Não supervisionada:** o K-means encontra **grupos** de píxeis parecidos, sem rótulos. O nome dos grupos
   é dado por uma pessoa.
2. **Classificação** dá uma categoria ("água"); **regressão** dá um número (o caudal em m³/s).
3. Na regressão, as notas são o **erro médio (MAE)** e o **R²**.
4. Quando o tempo importa, **o exame é o futuro**: treina-se com o passado e testa-se com anos que o modelo nunca viu.
5. Mais complexo não é sempre melhor: uma árvore muito profunda **decora** o treino (sobreajuste) e erra mais no exame.

**Por último:** a Parte G, com a ficha `4_ficha_da_plataforma.md`, e a plataforma EYES TO EARTH.
"""),
            md(ERROS_COMUNS)]


# ---------- versão completa do facilitador ----------

def interpretacoes(ref):
    km = ref["kmeans"]
    k4 = km[str(K_GRUPOS)]
    g = ref["regressao"]
    lin, ap = g["linear"], g["arvore_por_profundidade"]
    melhor = max(ap, key=lambda p: ap[p]["R2_exame"])
    coef = lin["coeficientes"]

    def sinal(v, casas):
        return ("+ " if v >= 0 else "− ") + fmt(abs(v), casas)

    i = {}
    i['cheia = carregar("incomati_2026_cheia.npz")'] = f"""
⏱️ **Tempo:** Parte E entre as {HORAS['E']} e as {HORAS['F']}.

🔎 **Interpretação.** A tabela tem 815 850 píxeis e 8 características; cerca de 600 mil estão no distrito e sem nuvens.
🗣️ **Dizer à turma:** "Até agora demos sempre a resposta certa. Agora não damos nada: só os números de cada píxel."
"""
    i["agrupador.fit(X[valido])"] = f"""
🔎 **Interpretação.** Com K = {K_GRUPOS}, os grupos ficam com {", ".join(f"{p}%" for p in k4['pct_por_grupo'])} dos píxeis. O grupo
grande ({max(k4['pct_por_grupo'])}%) é a água da cheia, que cobre quase toda a planície. Demora cerca de 1 segundo.
🗣️ **Dizer à turma:** "Repararam? `fit(X)`, sem `y`. É a única diferença no código, e muda tudo."
"""
    i["mapa_grupos = np.where"] = """
🔎 **Interpretação.** Um grupo cobre a água da cheia (a planície castanha e o rio); os outros separam tipos de terra, por
exemplo vegetação mais densa e menos densa, e solo mais claro. Peçam aos estudantes que comparem cada cor com a cor natural.
Os números dos grupos são arbitrários: com outro K ou outra versão do scikit-learn, a água pode ser o grupo 0 ou o 3.
Por isso o nome tem de ser dado por uma pessoa.
"""
    i["GRUPOS_AGUA = None"] = f"""
🔎 **Interpretação.** O grupo da água tem o MNDWI médio positivo (perto de +0,7); os outros são negativos. Com K = 6, a água
divide-se em dois grupos (por exemplo, água barrenta e água mais escura): os dois têm de entrar na lista. Grupos de água na referência: K = 2: {km['2']['grupos_agua']};
K = 3: {km['3']['grupos_agua']}; K = {K_GRUPOS}: {k4['grupos_agua']}; K = 6: {km['6']['grupos_agua']}.
"""
    i['mostrar_notas("K-means (sem rótulos)"'] = f"""
🔎 **Interpretação.** IoU do K-means no exame: K = 2: {fmt(km['2']['IoU'], 3)}; K = 3: {fmt(km['3']['IoU'], 3)}; K = {K_GRUPOS}: {fmt(k4['IoU'], 3)};
K = 6: {fmt(km['6']['IoU'], 3)}. **Sem um único rótulo, o K-means fica ao nível do Random Forest ({fmt(ref['ems_modelo']['IoU'], 3)}) e da regra MNDWI
({fmt(ref['ems_mndwi']['IoU'], 3)}).** Funciona porque, nesta imagem, a água é muito diferente de tudo o resto. Numa imagem difícil
(água barrenta como em 2021, sombras, nuvens), os grupos misturam-se e é preciso a aprendizagem supervisionada.

🗣️ **Dizer à turma:** "O K-means não sabe o que é água. Descobriu que estes píxeis são parecidos entre si; fomos nós que lhes demos o nome."
"""
    i["serie = pd.read_csv"] = f"""
⏱️ **Tempo:** Parte F entre as {HORAS['F']} e as {HORAS['G']}.

🔎 **Interpretação.** {g['dias_treino'] + g['dias_exame']} dias, de 2006 a 2026. O caudal passa a maior parte do tempo abaixo de 200 m³/s,
com cheias curtas: 2012, 2013, 2023 e a grande cheia de janeiro de 2026 (pico de {fmt(g['cheia_2026']['pico'])} m³/s a 19/01).
Gráficos separados (caudal em cima, chuva em baixo), nunca dois eixos no mesmo gráfico: dois eixos enganam.
"""
    i["treino = serie["] = f"""
🔎 **Interpretação.** Treino: {fmt(g['dias_treino'])} dias; exame: {fmt(g['dias_exame'])} dias. O maior caudal do treino é {fmt(g['max_treino'])} m³/s, o do exame
{fmt(g['max_exame'])} m³/s: o exame tem uma cheia **maior do que tudo o que o modelo viu**. É o caso mais difícil para qualquer modelo.
🗣️ **Dizer à turma:** "Na previsão do tempo, o exame é sempre o futuro. Se misturássemos os dias ao acaso, o modelo copiava o dia ao lado."
"""
    i["recta.fit(treino[PISTAS]"] = f"""
🔎 **Interpretação (pistas completas).** Equação: caudal daqui a {HORIZONTE} dias = {fmt(coef['caudal_m3s'], 2)} × caudal de hoje {sinal(coef['chuva_7d_mm'], 2)} × chuva de 7 dias
{sinal(coef['chuva_14d_mm'], 2)} × chuva de 14 dias {sinal(coef['chuva_30d_mm'], 2)} × chuva de 30 dias {sinal(lin['intercepto'], 1)}. O sinal diz se a pista faz
subir (+) ou descer (−) a previsão. No exame: erro médio
**{fmt(lin['MAE'])} m³/s**, R² **{fmt(lin['R2'], 2)}**. Dizer "fica igual a hoje" erra {fmt(g['igual_a_hoje']['MAE'])} m³/s (R² {fmt(g['igual_a_hoje']['R2'], 2)}): o modelo é um pouco
melhor. Sem o caudal de hoje (só chuva): erro {fmt(g['so_chuva']['MAE'])} m³/s, R² {fmt(g['so_chuva']['R2'], 2)}. **As pistas certas valem mais do que o algoritmo.**

🗣️ **Dizer à turma:** "Cada número da equação diz quanto pesa cada pista. O caudal de hoje pesa muito: o rio não muda de um dia para o outro."
"""
    c26 = g["cheia_2026"]
    i["janela = ((exame"] = f"""
🔎 **Interpretação.** A recta só previu "laranja" (376 m³/s para daqui a 3 dias) a {c26['primeiro_dia_previsao_laranja']}, quando o rio já estava a passar
esse limite. Não anteviu a subida: o caudal passou de 255 m³/s (11/01) para {fmt(c26['pico'])} m³/s (19/01) em 8 dias, e a maior previsão
foi {fmt(c26['maior_previsao'])} m³/s. Uma subida assim quase não existe no treino. À direita, os pontos seguem a linha nos dias normais e ficam
abaixo dela nas cheias grandes.

🗣️ **Dizer à turma:** "A regressão aprende o comportamento médio. Para avisar a tempo, a plataforma usa as previsões de caudal do
GloFAS para 10 dias, feitas com modelos do tempo e do rio inteiro."
"""
    i["profundidades = CONFIG"] = f"""
🔎 **Interpretação.** Melhor profundidade no exame: **{melhor}** (R² {fmt(ap[melhor]['R2_exame'], 2)}). Com 20 perguntas, o treino chega a
{fmt(ap['20']['R2_treino'], 2)} e o exame cai para {fmt(ap['20']['R2_exame'], 2)}. É exactamente o gráfico da teoria (subajuste, bom ajuste,
sobreajuste), com dados reais. A curva do exame não é lisa (os dados reais têm ruído), mas a tendência é clara. A recta
(R² {fmt(lin['R2'], 2)}) ganha a todas as árvores: aqui, o modelo simples é o melhor.
"""
    return i


def respostas(ref):
    km = ref["kmeans"]
    g = ref["regressao"]
    ap = g["arvore_por_profundidade"]
    melhor = max(ap, key=lambda p: ap[p]["R2_exame"])
    return {
        "Como é que conseguiu separar a água": f"Porque a água tem números muito diferentes do resto (NIR e SWIR baixos, MNDWI alto): os píxeis de água ficam juntos e longe dos outros. O nome \"água\" foi dado por nós, ao olhar para o mapa. Com K = 2 a 6 a nota quase não muda (IoU entre {fmt(min(v['IoU'] for v in km.values()), 3)} e {fmt(max(v['IoU'] for v in km.values()), 3)}); com K = 6 a água fica em dois grupos.",
        "que **vantagem** e que **desvantagem**": "Vantagem: não precisa de ninguém a marcar exemplos, que é a parte mais cara e lenta. Desvantagem: não sabe o nome dos grupos e pode juntar coisas diferentes (sombras com água escura) ou separar a mesma coisa em dois grupos. Também não tem nota sem um exame com rótulos.",
        "a tempo de dar um alerta laranja": f"Não. Só previu laranja a {g['cheia_2026']['primeiro_dia_previsao_laranja']}, quando o rio já estava a passar o limite. A subida foi rapidíssima e maior do que tudo o que o modelo viu no treino; a recta aprende o comportamento médio. Por isso a plataforma usa previsões do GloFAS.",
        "a partir de que profundidade a árvore começa a **decorar**": f"A partir de {melhor} ou {int(melhor) + 1} perguntas: a nota do treino continua a subir (até {fmt(ap['20']['R2_treino'], 2)}), mas a do exame desce (para {fmt(ap['20']['R2_exame'], 2)} com 20). A árvore começa a decorar os dias do treino, com o seu ruído, em vez da regra geral.",
    }


def completo(ref):
    base = celulas()
    interp = interpretacoes(ref)
    saida = [md("""
# VERSÃO COMPLETA DO FACILITADOR · Partes E e F com interpretação

O mesmo notebook dos estudantes, já executado, com: 🔎 interpretação de cada resultado · 🗣️ o que dizer à turma ·
⏱️ tempo · respostas-modelo. Não precisa de pontos marcados: os números dos pares são os mesmos, se não mudarem K
nem as pistas. **Não partilhar.**
""")]
    usadas = set()
    for cel in base:
        if cel.cell_type == "markdown":
            for chave, texto in respostas(ref).items():
                if chave in cel.source:
                    cel.source = cel.source.replace("*Resposta:*", f"**Resposta-modelo:** {texto}", 1)
        saida.append(cel)
        if cel.cell_type == "code":
            for chave, texto in interp.items():
                if chave in cel.source and chave not in usadas:
                    saida.append(md(texto))
                    usadas.add(chave)
                    break
    falta = set(interp) - usadas
    assert not falta, f"interpretações sem célula: {falta}"
    assert not any("*Resposta:*" in c.source for c in saida), "pergunta sem resposta-modelo"
    return saida


def construir(ref):
    return [escrever(celulas(), PRATICA / "3_sem_rotulos_e_numeros.ipynb", "ETE WS2 · Partes E-F · Sem rótulos e regressão"),
            escrever(completo(ref), FAC / "COMPLETO_3_sem_rotulos_e_numeros.ipynb", "ETE WS2 · Partes E-F · versão completa do facilitador")]
