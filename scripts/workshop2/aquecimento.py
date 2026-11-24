"""Parte A da prática: «O meu primeiro modelo» (aquecimento, 15 minutos, sem ficheiros de dados)."""

from .comum import LEGENDA, PRATICA, TRABALHAR_NO_JUPYTER, code, escrever, md

# 24 píxeis reais da imagem Sentinel-2 de 23 out 2025 (época seca), Marracuene: verde, vermelho, NIR, SWIR
PIXEIS = [
    (0.063, 0.061, 0.030, 0.016, "água"), (0.055, 0.058, 0.033, 0.013, "água"), (0.066, 0.068, 0.037, 0.016, "água"),
    (0.051, 0.043, 0.011, 0.013, "água"), (0.068, 0.067, 0.031, 0.017, "água"), (0.059, 0.063, 0.032, 0.012, "água"),
    (0.059, 0.060, 0.027, 0.013, "água"), (0.056, 0.049, 0.018, 0.014, "água"),
    (0.064, 0.043, 0.342, 0.199, "vegetação"), (0.072, 0.047, 0.381, 0.212, "vegetação"), (0.070, 0.057, 0.325, 0.225, "vegetação"),
    (0.084, 0.066, 0.337, 0.227, "vegetação"), (0.063, 0.039, 0.331, 0.190, "vegetação"), (0.087, 0.062, 0.369, 0.234, "vegetação"),
    (0.080, 0.051, 0.322, 0.209, "vegetação"), (0.068, 0.045, 0.313, 0.172, "vegetação"),
    (0.115, 0.147, 0.193, 0.369, "solo"), (0.150, 0.189, 0.251, 0.428, "solo"), (0.111, 0.144, 0.202, 0.348, "solo"),
    (0.110, 0.147, 0.210, 0.359, "solo"), (0.120, 0.154, 0.203, 0.377, "solo"), (0.088, 0.117, 0.164, 0.317, "solo"),
    (0.156, 0.202, 0.253, 0.395, "solo"), (0.127, 0.161, 0.221, 0.351, "solo"),
]


def celulas():
    linhas = ",\n    ".join(f"[{g}, {r}, {n}, {s}, \"{c}\"]" for g, r, n, s, c in PIXEIS)
    return [md(f"""
# Parte A · O meu primeiro modelo de Inteligência Artificial (15 minutos)

**Workshop de Estudantes 2 · Projecto EYES TO EARTH (ETE) · 21 de Novembro de 2026**

Na teoria vimos a grande ideia do Machine Learning: **em vez de escrevermos as regras, damos exemplos e
o computador descobre as regras sozinho.** Aqui vamos ver isso a acontecer, em 6 passos curtos.

É **aprendizagem supervisionada** (cada exemplo traz a resposta certa, o **rótulo**) e é uma **classificação**
(a resposta é uma categoria: água, vegetação ou solo).

Não precisa de ficheiros de dados: os exemplos estão escritos no próprio notebook.

{LEGENDA}
{TRABALHAR_NO_JUPYTER}
"""),
            md("""
## As ferramentas (bibliotecas) ▶️

| Biblioteca | Para que serve |
| --- | --- |
| `pandas` (`pd`) | Mostrar os exemplos numa tabela bonita, como numa folha de Excel |
| `matplotlib` (`plt`) | Desenhar (aqui, desenhar a árvore de decisão) |
| `scikit-learn` (`sklearn`) | A caixa de ferramentas de Machine Learning mais usada no mundo. Daqui vêm a **árvore de decisão** e a **floresta aleatória (Random Forest)** |

Já estão instaladas nos computadores do workshop (vêm com o Anaconda; ou `pip install pandas matplotlib scikit-learn`).
"""),
            code("""
import pandas as pd                                   # tabelas
import matplotlib.pyplot as plt                       # desenhos
from sklearn.tree import DecisionTreeClassifier, plot_tree    # uma árvore de decisão
from sklearn.ensemble import RandomForestClassifier           # muitas árvores a votar
print("Ferramentas prontas.")
"""),
            md("""
## Passo 1 · Os exemplos ▶️

São 24 píxeis **reais** da imagem do satélite Sentinel-2 de Marracuene (23 de outubro de 2025).
Para cada píxel temos 4 **características** (a luz reflectida no verde, no vermelho, no NIR e no SWIR)
e o **rótulo**: a resposta certa, escrita por uma pessoa que olhou para a imagem.
"""),
            code(f"""
exemplos = pd.DataFrame([
    {linhas},
], columns=["verde", "vermelho", "nir", "swir", "rotulo"])

print("Quantos exemplos de cada tipo:")
print(exemplos["rotulo"].value_counts())
exemplos.sample(8, random_state=1)        # mostra 8 exemplos ao acaso
"""),
            md("""
✍️ **Olhe para a tabela:** o que distingue a água? E a vegetação? (Pista: compare as colunas `nir` e `swir`.)

*Resposta:*

## Passo 2 · Seja você o programador: escreva uma regra ✏️

Antes da IA, um programador escrevia as regras à mão. Tente! Complete a função com `if` e corra a célula.
A célula diz quantos dos 24 exemplos a sua regra acerta.
"""),
            code("""
def minha_regra(verde, vermelho, nir, swir):
    # ✏️ troque os números e as condições, e corra outra vez
    if nir > 0.25:
        return "vegetação"
    elif swir > 0.30:
        return "solo"
    else:
        return "água"


certos = sum(minha_regra(l.verde, l.vermelho, l.nir, l.swir) == l.rotulo for l in exemplos.itertuples())
print(f"A minha regra acerta {certos} de {len(exemplos)} exemplos.")
"""),
            md("""
Neste caso é fácil: três tipos bem diferentes. Mas pense em **milhões** de píxeis, água barrenta, água muito
escura, sombras, nuvens, vila... As regras escritas à mão começam a falhar (vimos isso no Workshop 1:
o NDWI falhou em 2021 e o MNDWI em 2024). É aqui que entra o Machine Learning.

## Passo 3 · A máquina aprende as regras sozinha: árvore de decisão ▶️

Uma **árvore de decisão** é um jogo de "perguntas de sim ou não", como o jogo das 20 perguntas.
O computador escolhe sozinho as melhores perguntas, olhando para os exemplos. `fit` quer dizer **aprender**.
"""),
            code("""
X = exemplos[["verde", "vermelho", "nir", "swir"]]     # as características (as pistas)
y = exemplos["rotulo"]                                # os rótulos (as respostas certas)

arvore = DecisionTreeClassifier(max_depth=2, random_state=0)   # no máximo 2 perguntas seguidas
arvore.fit(X, y)                                               # APRENDER com os exemplos

plt.figure(figsize=(10, 5))
plot_tree(arvore, feature_names=list(X.columns), class_names=list(arvore.classes_), filled=True, rounded=True, fontsize=10)
plt.title("As perguntas que a máquina aprendeu sozinha")
plt.show()
"""),
            md("""
✍️ **Leia a árvore de cima para baixo:** qual é a primeira pergunta? Parece-se com a sua regra do Passo 2?

*Resposta:*

## Passo 4 · Prever píxeis que a árvore nunca viu ▶️

`predict` quer dizer **prever**. Damos à árvore os três "píxeis misteriosos" do Workshop 1 (A, B, C) e um
píxel da **cheia de janeiro de 2026**: água castanha, cheia de sedimentos, diferente de todos os exemplos.
"""),
            code("""
novos = pd.DataFrame([
    [0.06, 0.04, 0.02, 0.01],      # A do Workshop 1
    [0.10, 0.05, 0.45, 0.20],      # B do Workshop 1
    [0.15, 0.20, 0.28, 0.35],      # C do Workshop 1
    [0.095, 0.114, 0.048, 0.010],  # água barrenta da cheia de 2026
], columns=["verde", "vermelho", "nir", "swir"], index=["A", "B", "C", "cheia 2026"])

novos["previsão da árvore"] = arvore.predict(novos)
novos
"""),
            md("""
✍️ **A árvore acertou o píxel da cheia, que é diferente de todos os exemplos?** Porquê? (Pista: qual foi a pergunta da árvore?)

*Resposta:*

## Passo 5 · Random Forest: muitas árvores a votar ▶️

Uma só árvore pode enganar-se. Uma **floresta aleatória (Random Forest)** treina muitas árvores, cada uma com
uma parte diferente dos exemplos, e no fim **cada árvore vota**. Ganha a classe com mais votos.
Vamos ver os votos de 25 árvores para o píxel da cheia.
"""),
            code("""
floresta = RandomForestClassifier(n_estimators=25, random_state=0)     # 25 árvores
floresta.fit(X, y)

pixel = novos.loc[["cheia 2026"], ["verde", "vermelho", "nir", "swir"]]
votos = [floresta.classes_[int(a.predict(pixel.to_numpy())[0])] for a in floresta.estimators_]
print("Votos das 25 árvores:", pd.Series(votos).value_counts().to_dict())
print("Decisão da floresta:", floresta.predict(pixel)[0])
print("Probabilidades:", dict(zip(floresta.classes_, floresta.predict_proba(pixel)[0].round(2))))
"""),
            md("""
A **probabilidade** é a parte dos votos: se 24 de 25 árvores dizem "água", a probabilidade de água é 0,96.
É isto que vamos usar na Parte B para fazer o mapa de água do Incomáti.

## Passo 6 · O mesmo método serve para tudo: um filtro de spam ▶️

O filtro de spam do seu email ou do WhatsApp aprende da mesma maneira: exemplos de mensagens marcadas como
"spam" ou "normal". As características são outras (quantos links, palavras como "prémio" ou "grátis",
se conhece quem enviou, pontos de exclamação), mas o código é **o mesmo**. (Exemplo inventado, para aprender.)
"""),
            code("""
mensagens = pd.DataFrame([
    # links, palavras de prémio, remetente conhecido (1 sim, 0 não), pontos de exclamação, rótulo
    [0, 0, 1, 0, "normal"], [1, 0, 1, 1, "normal"], [0, 0, 1, 2, "normal"], [2, 0, 1, 0, "normal"],
    [0, 1, 1, 1, "normal"], [1, 0, 0, 0, "normal"],
    [3, 2, 0, 4, "spam"], [2, 3, 0, 3, "spam"], [1, 2, 0, 5, "spam"], [4, 1, 0, 2, "spam"],
    [2, 2, 0, 0, "spam"], [5, 0, 0, 3, "spam"],
], columns=["links", "palavras_premio", "remetente_conhecido", "exclamacoes", "rotulo"])

filtro = DecisionTreeClassifier(max_depth=2, random_state=0)
filtro.fit(mensagens.drop(columns="rotulo"), mensagens["rotulo"])          # aprender

nova = pd.DataFrame([[3, 2, 0, 3], [0, 0, 1, 1]], columns=["links", "palavras_premio", "remetente_conhecido", "exclamacoes"],
                    index=["'GANHOU um PRÉMIO!!! Clique aqui'", "'Chego às 18h!'"])
nova["previsão"] = filtro.predict(nova)                                    # prever
nova
"""),
            md("""
## O que aprendemos

1. **Exemplos + rótulos** → o computador **aprende** (`fit`) as regras sozinho.
2. Depois **prevê** (`predict`) casos novos que nunca viu.
3. Uma **árvore de decisão** faz perguntas de sim ou não; um **Random Forest** junta muitas árvores a votar.
4. O mesmo código serve para água, spam, fotografias, voz... muda só o tipo de exemplos.

**Próximo:** `2_ia_que_encontra_agua.ipynb` (Partes B a D), onde **vocês** marcam os exemplos no mapa e treinam o modelo.
""")]


def construir():
    return [escrever(celulas(), PRATICA / "1_o_meu_primeiro_modelo.ipynb", "ETE WS2 · Parte A · O meu primeiro modelo")]
