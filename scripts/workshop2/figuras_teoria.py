"""Gráficos da teoria do Workshop 2 (como uma máquina aprende), em Workshop_2/0_facilitadores/imagens_para_slides/.

    cd scripts && ../.venv/bin/python -m workshop2.figuras_teoria

Os gráficos clássicos da teoria do Machine Learning. Sempre que possível com dados reais do Incomáti (píxeis da
cheia de 2026, os 24 píxeis da Parte A, o caudal do GloFAS); com dados inventados só onde o conceito o pede
(horas de estudo e nota; subajuste e sobreajuste), e isso fica escrito no slide.

Cores: as três primeiras da paleta de referência (azul, laranja, aqua), validadas para daltonismo com todos os
pares; texto em tinta escura; grelha recessiva; fundo branco, como os slides.
"""

import json
import os

import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402

from .aquecimento import PIXEIS  # noqa: E402
from .comum import FAC, HORIZONTE, K_GRUPOS, PISTAS_CAUDAL, PRATICA, ULTIMO_ANO_TREINO, ferramentas_namespace  # noqa: E402,F401

OUT = FAC / "imagens_para_slides"
AZUL, LARANJA, AQUA = "#2a78d6", "#eb6834", "#1baf7a"
TINTA, SUAVE, GRELHA, NEUTRO = "#1B1F24", "#4A5563", "#D9DEE4", "#9AA4AF"
PRETO_G, VERMELHO_G, CINZA_G = "#1A1A1A", "#A51C30", "#8C8C8C"  # gráficos sem água: preto, vermelho e cinzento (como os slides)
RAMPA = ["#E8A3A8", "#CF5A66", "#A51C30", "#5C0F1A"]          # vermelho, do claro ao escuro (passos do treino)
TINTAS = {AZUL: "#dbe9fa", LARANJA: "#fbe1d6", AQUA: "#d2f0e4"}   # fundos claros das regiões de cada classe
plt.rcParams.update({"font.family": ["Arial", "Liberation Sans", "DejaVu Sans"], "font.size": 20, "text.color": TINTA,
                     "axes.edgecolor": NEUTRO, "axes.labelcolor": SUAVE, "xtick.color": SUAVE, "ytick.color": SUAVE,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 22, "axes.titleweight": "bold",
                     "axes.titlecolor": TINTA, "legend.frameon": False, "savefig.facecolor": "white"})


def grelha(ax):
    ax.grid(color=GRELHA, lw=1)
    ax.set_axisbelow(True)


def guardar(fig, nome):
    fig.savefig(OUT / nome, dpi=100, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    return OUT / nome


def pontos_da_equipa(f, n_por_classe=180, semente=0):
    """Píxeis reais dos 15 + 15 pontos da equipa (cheia de 2026): NIR, SWIR e rótulo."""
    os.chdir(PRATICA / "dados")
    ex = json.load(open("exemplos_da_equipa.json"))
    cheia = f["carregar"]("incomati_2026_cheia.npz")
    X, y = f["exemplos"](cheia, ex["2026"]["agua"], ex["2026"]["nao_agua"], ["nir", "swir"])
    rng = np.random.default_rng(semente)
    idx = np.concatenate([rng.choice(np.flatnonzero(y == c), n_por_classe, replace=False) for c in (1, 0)])
    return X[idx], y[idx], cheia


def classificacao(f):
    from sklearn.linear_model import LogisticRegression
    X, y, _ = pontos_da_equipa(f)
    m = LogisticRegression(C=100).fit(X, y)
    fig, ax = plt.subplots(figsize=(10, 7.6))
    xx, yy = np.meshgrid(np.linspace(0, 0.55, 400), np.linspace(0, 0.5, 400))
    z = m.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    ax.contourf(xx, yy, z, levels=[-0.5, 0.5, 1.5], colors=[TINTAS[LARANJA], TINTAS[AZUL]])
    ax.contour(xx, yy, z, levels=[0.5], colors=[TINTA], linewidths=2.5)
    for c, cor, nome in [(1, AZUL, "água"), (0, LARANJA, "não água")]:
        ax.scatter(X[y == c, 0], X[y == c, 1], s=46, color=cor, edgecolor="white", linewidth=0.8, label=nome, zorder=3)
    novo = np.array([0.07, 0.06])
    ax.scatter(*novo, s=420, marker="*", color=TINTA, edgecolor="white", linewidth=1.5, zorder=5)
    ax.annotate("píxel novo: o modelo diz «água»", novo, xytext=(0.235, 0.022), fontsize=19, color=TINTA,
                arrowprops=dict(arrowstyle="->", color=TINTA, lw=1.5), va="center")
    w0, w1 = m.coef_[0]
    xf = 0.06
    ax.annotate("fronteira de decisão", (xf, -(m.intercept_[0] + w0 * xf) / w1), xytext=(0.012, 0.29), fontsize=19,
                color=TINTA, arrowprops=dict(arrowstyle="->", color=TINTA, lw=1.5))
    ax.set_xlim(0, 0.55)
    ax.set_ylim(0, 0.5)
    ax.set_xlabel("NIR (infravermelho próximo)")
    ax.set_ylabel("SWIR (infravermelho de onda curta)")
    ax.legend(loc="upper left", markerscale=1.6, fontsize=19)
    return guardar(fig, "ml_classificacao.png")


def dados_estudo(semente=3):
    rng = np.random.default_rng(semente)
    horas = np.sort(rng.uniform(0.5, 12, 26))
    nota = np.clip(5.6 + 1.05 * horas + rng.normal(0, 1.6, horas.size), 0, 20)
    return horas, nota


def regressao():
    from sklearn.linear_model import LinearRegression
    h, n = dados_estudo()
    m = LinearRegression().fit(h[:, None], n)
    a, b = m.coef_[0], m.intercept_
    fig, ax = plt.subplots(figsize=(10, 7.6))
    grelha(ax)
    for xi, yi in zip(h, n):
        ax.plot([xi, xi], [yi, a * xi + b], color=NEUTRO, lw=1.4, zorder=1)
    xs = np.linspace(0, 13, 50)
    ax.plot(xs, a * xs + b, color=VERMELHO_G, lw=3, label="a recta aprendida (o modelo)", zorder=2)
    ax.scatter(h, n, s=70, color=PRETO_G, edgecolor="white", linewidth=1, label="exemplos (alunos)", zorder=3)
    i = int(np.argmax(np.abs(n - (a * h + b))))
    ax.annotate("erro", (h[i], (n[i] + a * h[i] + b) / 2), xytext=(h[i] + 0.9, (n[i] + a * h[i] + b) / 2 + 1.4),
                fontsize=19, color=SUAVE, arrowprops=dict(arrowstyle="->", color=SUAVE, lw=1.2))
    prev = a * 10 + b
    ax.scatter([10], [prev], s=420, marker="*", color=TINTA, edgecolor="white", linewidth=1.5, zorder=5)
    ax.annotate(f"10 horas → nota prevista {prev:.0f}".replace(".", ","), (10, prev), xytext=(5.2, 19.6), fontsize=19,
                color=TINTA, arrowprops=dict(arrowstyle="->", color=TINTA, lw=1.5))
    ax.text(0.3, 17.2, f"nota = {a:.2f} × horas + {b:.1f}".replace(".", ","), fontsize=21, color=TINTA, weight="bold")
    ax.set_xlim(0, 13)
    ax.set_ylim(0, 20.5)
    ax.set_xlabel("Horas de estudo por semana")
    ax.set_ylabel("Nota do exame (0 a 20)")
    ax.legend(loc="lower right", fontsize=18, handles=[
        Line2D([], [], marker="o", ls="", color=PRETO_G, markersize=10, label="exemplos (alunos)"),
        Line2D([], [], color=VERMELHO_G, lw=3, label="a recta aprendida (o modelo)"),
        Line2D([], [], color=NEUTRO, lw=1.4, label="erro de cada exemplo")])
    return guardar(fig, "ml_regressao.png"), (a, b)


def treino_passo_a_passo():
    h, n = dados_estudo()
    hm, hs = h.mean(), h.std()
    xz = (h - hm) / hs
    w, c = -1.5, 4.0                                    # a primeira tentativa: uma recta muito errada
    historia, erros = {}, []
    for passo in range(61):
        prev = w * xz + c
        erros.append(np.mean((prev - n) ** 2))
        if passo in (0, 3, 10, 60):
            historia[passo] = (w, c)
        g = prev - n
        w -= 0.12 * 2 * np.mean(g * xz)
        c -= 0.12 * 2 * np.mean(g)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 6.6), gridspec_kw={"width_ratios": [1.15, 1]})
    grelha(a1)
    grelha(a2)
    a1.scatter(h, n, s=60, color=NEUTRO, edgecolor="white", linewidth=1, zorder=3)
    xs = np.linspace(0, 13, 50)
    for (passo, (w_, c_)), cor in zip(historia.items(), RAMPA):
        ys = w_ * (xs - hm) / hs + c_
        a1.plot(xs, ys, color=cor, lw=3, zorder=2)
        a1.text(13.15, ys[-1], f"passo {passo}", color=TINTA, fontsize=17, va="center")
    a1.set_xlim(0, 13)
    a1.set_ylim(-2, 21)
    a1.set_xlabel("Horas de estudo por semana")
    a1.set_ylabel("Nota do exame")
    a1.set_title("A recta melhora a cada passo", loc="left")
    a2.plot(range(len(erros)), erros, color=VERMELHO_G, lw=3)
    for passo, cor in zip(historia, RAMPA):
        a2.scatter([passo], [erros[passo]], s=110, color=cor, edgecolor="white", linewidth=1.5, zorder=3)
    a2.set_xlabel("Passo do treino")
    a2.set_ylabel("Erro médio (ao quadrado)")
    a2.set_title("O erro desce até quase não mudar", loc="left")
    a2.set_ylim(0, max(erros) * 1.05)
    fig.tight_layout(w_pad=4)
    return guardar(fig, "ml_treino.png")


def agrupamento(f):
    from sklearn.cluster import KMeans
    os.chdir(PRATICA / "dados")
    cheia = f["carregar"]("incomati_2026_cheia.npz")
    valido = (cheia["zona"] & ~cheia["nuvem"]).ravel()
    T = f["tabela"](cheia, ["nir", "swir"])[valido]
    rng = np.random.default_rng(1)
    T = T[rng.choice(len(T), 1500, replace=False)]
    escala = T.std(axis=0)
    km = KMeans(n_clusters=3, n_init=5, random_state=0).fit(T / escala)
    ordem = np.argsort(km.cluster_centers_[:, 0])          # do menor NIR (a água) ao maior
    cores = {int(ordem[0]): AZUL, int(ordem[1]): LARANJA, int(ordem[2]): AQUA}
    nomes = {int(ordem[0]): "grupo 1", int(ordem[1]): "grupo 2", int(ordem[2]): "grupo 3"}
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 7.2), sharex=True, sharey=True)
    for ax in (a1, a2):
        grelha(ax)
        ax.set_xlabel("NIR")
    a1.scatter(T[:, 0], T[:, 1], s=16, color=NEUTRO, alpha=0.8)
    a1.set_ylabel("SWIR")
    a1.set_title("Antes: píxeis sem rótulos", loc="left")
    for g in range(3):
        sel = km.labels_ == g
        a2.scatter(T[sel, 0], T[sel, 1], s=16, color=cores[g], alpha=0.85, label=nomes[g])
    centros = km.cluster_centers_ * escala
    a2.scatter(centros[:, 0], centros[:, 1], s=420, marker="X", color=TINTA, edgecolor="white", linewidth=2, zorder=4,
               label="centro do grupo")
    a2.set_title("Depois do K-means: 3 grupos", loc="left")
    a2.legend(loc="upper left", fontsize=18, handles=[
        *[Line2D([], [], marker="o", ls="", color=cores[g], markersize=10, label=nomes[g]) for g in ordem],
        Line2D([], [], marker="X", ls="", color=TINTA, markeredgecolor="white", markersize=16, label="centro do grupo")])
    a1.set_xlim(0, 0.6)
    a1.set_ylim(0, 0.55)
    fig.tight_layout(w_pad=3)
    return guardar(fig, "ml_agrupamento.png")


def kmeans_passos():
    rng = np.random.default_rng(4)
    centros_reais = np.array([[2, 2], [7, 3], [4.5, 7.5]])
    P = np.concatenate([c + rng.normal(0, 0.95, (55, 2)) for c in centros_reais])
    C = np.array([[0.5, 5.5], [6.5, 0.0], [9.5, 9.5]])     # três centros ao acaso, mal colocados
    cores = [VERMELHO_G, PRETO_G, CINZA_G]

    def atribuir(C):
        return np.argmin(((P[:, None, :] - C[None]) ** 2).sum(-1), axis=1)

    fig, eixos = plt.subplots(1, 4, figsize=(18, 5.0), sharex=True, sharey=True)
    lab = atribuir(C)
    assert all((lab == k).any() for k in range(3)), "um centro inicial ficou sem pontos"
    novo = np.array([P[lab == k].mean(0) for k in range(3)])
    final = novo.copy()
    for _ in range(20):
        lf = atribuir(final)
        final = np.array([P[lf == k].mean(0) for k in range(3)])
    lf = atribuir(final)
    paineis = [("1. Centros ao acaso", None, C, None), ("2. Cada ponto vai para\no centro mais perto", lab, C, None),
               ("3. Cada centro vai para\no meio do seu grupo", lab, novo, C), ("4. Repetir até não mudar", lf, final, None)]
    for ax, (titulo, rotulos, centros, antigos) in zip(eixos, paineis):
        if rotulos is None:
            ax.scatter(P[:, 0], P[:, 1], s=22, color=NEUTRO)
        else:
            for k in range(3):
                ax.scatter(P[rotulos == k, 0], P[rotulos == k, 1], s=22, color=cores[k], alpha=0.9)
        if antigos is not None:
            for a_, b_ in zip(antigos, centros):
                ax.annotate("", b_, xytext=a_, arrowprops=dict(arrowstyle="->", color=TINTA, lw=2))
        for k in range(3):
            ax.scatter(*centros[k], s=330, marker="X", color=cores[k], edgecolor=TINTA, linewidth=1.8, zorder=5)
        ax.set_title(titulo, loc="left", fontsize=19)
        ax.set_xticks([])
        ax.set_yticks([])
        for lado in ("left", "bottom"):
            ax.spines[lado].set_color(GRELHA)
        ax.set_xlim(-1.5, 10.5)
        ax.set_ylim(-1.5, 10.5)
    fig.tight_layout(w_pad=1.5)
    return guardar(fig, "ml_kmeans_passos.png")


def kmeans_mapa(f):
    """A imagem da cheia agrupada pelo K-means (K = 3, as 8 pistas), sem nenhum rótulo."""
    from PIL import Image
    from sklearn.cluster import KMeans
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    os.chdir(PRATICA / "dados")
    cheia = f["carregar"]("incomati_2026_cheia.npz")
    car = f["BANDAS"] + f["INDICES"]
    X = f["tabela"](cheia, car)
    valido = (cheia["zona"] & ~cheia["nuvem"]).ravel()
    km = make_pipeline(StandardScaler(), KMeans(n_clusters=3, n_init=3, random_state=0)).fit(X[valido])
    g = km.predict(X)
    nir = [X[valido][g[valido] == k, car.index("nir")].mean() for k in range(3)]
    ordem = np.argsort(nir)                                   # menor NIR = água; maior NIR = vegetação
    cor = {int(ordem[0]): AZUL, int(ordem[1]): LARANJA, int(ordem[2]): AQUA}
    rgb = np.full(g.shape + (3,), 255, "uint8")
    for k, c in cor.items():
        rgb[(g == k) & valido] = [int(c[i:i + 2], 16) for i in (1, 3, 5)]
    rgb[(cheia["zona"] & cheia["nuvem"]).ravel()] = (229, 232, 236)
    img = rgb.reshape(cheia["verde"].shape + (3,))
    Image.fromarray(img).save(OUT / "ml_kmeans_mapa.png", optimize=True)
    return OUT / "ml_kmeans_mapa.png"


def ajuste_e_complexidade():
    rng = np.random.default_rng(7)

    def verdade(x):
        return np.sin(2 * np.pi * x) * 0.9 + 0.6 * x

    x = np.sort(rng.uniform(0, 1, 16))
    y = verdade(x) + rng.normal(0, 0.22, x.size)
    xs = np.linspace(0, 1, 400)
    fig, eixos = plt.subplots(1, 3, figsize=(18, 5.6), sharey=True)
    for ax, (grau, titulo) in zip(eixos, [(1, "Subajuste: simples demais"), (4, "Bom ajuste"), (14, "Sobreajuste: decorou os pontos")]):
        grelha(ax)
        coef = np.polyfit(x, y, grau)
        ax.plot(xs, np.clip(np.polyval(coef, xs), -2.2, 2.2), color=VERMELHO_G, lw=3, zorder=2)
        ax.scatter(x, y, s=70, color=PRETO_G, edgecolor="white", linewidth=1, zorder=3)
        ax.set_title(titulo, loc="left")
        ax.set_xticks([])
        ax.set_ylim(-1.7, 1.9)
        ax.set_xlabel("pista (x)")
    eixos[0].set_ylabel("resposta (y)")
    eixos[0].set_yticks([])
    fig.tight_layout(w_pad=2)
    f1 = guardar(fig, "ml_ajuste.png")

    from sklearn.tree import DecisionTreeRegressor
    xt = rng.uniform(0, 1, 3000)
    yt = verdade(xt) + rng.normal(0, 0.3, xt.size)
    graus = list(range(1, 13))                          # aqui: a profundidade da árvore de regressão
    erro_treino, erro_teste = [], []
    for prof in graus:
        tr, te = [], []
        for _ in range(200):                            # 200 turmas diferentes de 40 exemplos: a curva média
            xa = rng.uniform(0, 1, 40)
            ya = verdade(xa) + rng.normal(0, 0.3, xa.size)
            arv = DecisionTreeRegressor(max_depth=prof, random_state=0).fit(xa[:, None], ya)
            tr.append(np.sqrt(np.mean((arv.predict(xa[:, None]) - ya) ** 2)))
            te.append(np.sqrt(np.mean((arv.predict(xt[:, None]) - yt) ** 2)))
        erro_treino.append(np.mean(tr))
        erro_teste.append(np.mean(te))
    melhor = graus[int(np.argmin(erro_teste))]
    topo = max(erro_teste) * 1.25
    fig, ax = plt.subplots(figsize=(12, 6.6))
    grelha(ax)
    ax.axvspan(0.5, melhor - 0.5, color="#F4F6F9", zorder=0)
    ax.axvspan(melhor + 1.5, graus[-1] + 0.5, color="#F4F6F9", zorder=0)
    ax.plot(graus, erro_treino, "o-", color=PRETO_G, lw=3, markersize=9, label="erro no treino (o que já viu)")
    ax.plot(graus, erro_teste, "o-", color=VERMELHO_G, lw=3, markersize=9, label="erro no teste (o que nunca viu)")
    ax.text((0.5 + melhor - 0.5) / 2, topo * 0.92, "subajuste", fontsize=20, color=SUAVE, ha="center")
    ax.text(melhor + 0.5, topo * 0.80, "bom ajuste", fontsize=20, color=TINTA, weight="bold", ha="center")
    ax.text((melhor + 1.5 + graus[-1] + 0.5) / 2, topo * 0.92, "sobreajuste", fontsize=20, color=SUAVE, ha="center")
    ax.text(graus[-1] + 0.3, erro_treino[-1], "treino", fontsize=19, color=PRETO_G, va="center", weight="bold")
    ax.text(graus[-1] + 0.3, erro_teste[-1], "teste", fontsize=19, color=VERMELHO_G, va="center", weight="bold")
    ax.set_ylim(0, topo)
    ax.set_xlim(0.5, graus[-1] + 1.4)
    ax.set_xticks(graus)
    ax.set_xlabel("Complexidade do modelo (profundidade da árvore)")
    ax.set_ylabel("Erro (quanto menor, melhor)")
    ax.legend(loc="lower left", fontsize=19)
    f2 = guardar(fig, "ml_complexidade.png")
    return f1, f2, melhor


def pixeis_parte_a():
    nir = np.array([p[2] for p in PIXEIS])
    swir = np.array([p[3] for p in PIXEIS])
    rotulo = np.array([p[4] for p in PIXEIS])
    return np.c_[nir, swir], rotulo


CORES_CLASSE = {"água": AZUL, "solo": LARANJA, "vegetação": AQUA}


def arvore_caixas():
    from sklearn.tree import DecisionTreeClassifier
    X, r = pixeis_parte_a()
    arv = DecisionTreeClassifier(max_depth=2, random_state=0).fit(X, r)
    t = arv.tree_
    fig, ax = plt.subplots(figsize=(10, 7.6))
    xx, yy = np.meshgrid(np.linspace(0, 0.45, 500), np.linspace(0, 0.47, 500))
    z = arv.predict(np.c_[xx.ravel(), yy.ravel()]).reshape(xx.shape)
    classes = list(arv.classes_)
    zi = np.vectorize(classes.index)(z)
    from matplotlib.colors import ListedColormap
    ax.contourf(xx, yy, zi, levels=[-0.5, 0.5, 1.5, 2.5], colors=[TINTAS[CORES_CLASSE[c]] for c in classes])
    ax.contour(xx, yy, zi, levels=[0.5, 1.5], colors=[TINTA], linewidths=2.2)
    for c in classes:
        sel = r == c
        ax.scatter(X[sel, 0], X[sel, 1], s=130, color=CORES_CLASSE[c], edgecolor="white", linewidth=1.5, label=c, zorder=3)
    nomes = ["NIR", "SWIR"]
    perguntas = []
    for no in range(t.node_count):
        if t.children_left[no] != -1:
            perguntas.append(f"{nomes[t.feature[no]]} ≤ {t.threshold[no]:.2f}?".replace(".", ","))
    ax.text(0.442, 0.012, "Perguntas que a árvore aprendeu:\n" + "\n".join(f"{i + 1}. {q}" for i, q in enumerate(perguntas)),
            fontsize=18, color=TINTA, va="bottom", ha="right", bbox=dict(boxstyle="square,pad=0.5", facecolor="white", edgecolor=GRELHA))
    ax.set_xlim(0, 0.45)
    ax.set_ylim(0, 0.47)
    ax.set_xlabel("NIR (infravermelho próximo)")
    ax.set_ylabel("SWIR (infravermelho de onda curta)")
    ax.legend(loc="upper right", fontsize=18, markerscale=1.1)
    _ = ListedColormap
    return guardar(fig, "ml_arvore_caixas.png"), perguntas


def knn():
    X, r = pixeis_parte_a()
    novo = np.array([0.25, 0.27])
    d = np.sqrt(((X - novo) ** 2).sum(1))
    viz = np.argsort(d)[:5]
    fig, ax = plt.subplots(figsize=(10, 7.6))
    grelha(ax)
    raio = d[viz].max() * 1.06
    ax.add_patch(plt.Circle(novo, raio, fill=False, ls="--", lw=2, color=SUAVE))
    for i in viz:
        ax.plot([novo[0], X[i, 0]], [novo[1], X[i, 1]], color=SUAVE, lw=1.4, zorder=1)
    for c in ["água", "vegetação", "solo"]:
        sel = r == c
        ax.scatter(X[sel, 0], X[sel, 1], s=130, color=CORES_CLASSE[c], edgecolor="white", linewidth=1.5, label=c, zorder=3)
    ax.scatter(*novo, s=520, marker="*", color=TINTA, edgecolor="white", linewidth=1.5, zorder=5)
    votos = pd.Series(r[viz]).value_counts()
    texto = " + ".join(f"{v} {k}" for k, v in votos.items())
    ax.annotate(f"píxel novo: os 5 vizinhos votam\n{texto} → «{votos.index[0]}»", novo, xytext=(0.06, 0.07), fontsize=19,
                color=TINTA, va="bottom", arrowprops=dict(arrowstyle="->", color=TINTA, lw=1.5))
    ax.set_aspect("equal")
    ax.set_xlim(0, 0.45)
    ax.set_ylim(0, 0.45)
    ax.set_xlabel("NIR (infravermelho próximo)")
    ax.set_ylabel("SWIR (infravermelho de onda curta)")
    ax.legend(loc="upper right", fontsize=18)
    return guardar(fig, "ml_knn.png"), votos.to_dict()


def rede():
    entradas = ["azul", "verde", "vermelho", "NIR", "SWIR", "NDWI", "MNDWI", "NDVI"]
    camadas = [8, 6, 6, 2]
    xs = [0, 1.25, 2.5, 3.75]
    fig, ax = plt.subplots(figsize=(14, 8))
    pos = []
    for x, n in zip(xs, camadas):
        ys = np.linspace(0.5, 7.5, n) if n > 2 else np.array([2.8, 5.2])
        pos.append([(x, y) for y in ys])
    for a, b in zip(pos[:-1], pos[1:]):
        for p in a:
            for q in b:
                ax.plot([p[0], q[0]], [p[1], q[1]], color=NEUTRO, lw=0.9, alpha=0.55, zorder=1)
    for i, (x, y) in enumerate(pos[0]):
        ax.scatter(x, y, s=900, color="#dbe9fa", edgecolor=AZUL, linewidth=2, zorder=3)
        ax.text(x - 0.17, y, entradas[i], ha="right", va="center", fontsize=19)
    for camada in pos[1:3]:
        for x, y in camada:
            ax.scatter(x, y, s=900, color="#EEF1F4", edgecolor=SUAVE, linewidth=2, zorder=3)
    for (x, y), cor, nome in zip(pos[3], [LARANJA, AZUL], ["não água", "água"]):
        ax.scatter(x, y, s=1300, color=cor, edgecolor="white", linewidth=2, zorder=3)
        ax.text(x + 0.2, y, nome, ha="left", va="center", fontsize=20, weight="bold")
    for x, titulo in zip([0, 1.875, 3.75], ["Entrada:\nas 8 pistas", "Camadas escondidas:\n16 + 16 neurónios (aqui, 6 + 6)", "Saída:\na resposta"]):
        ax.text(x, 8.55, titulo, ha="center", va="bottom", fontsize=19, color=SUAVE)
    ax.set_xlim(-1.3, 4.9)
    ax.set_ylim(-0.2, 9.6)
    ax.axis("off")
    return guardar(fig, "ml_rede.png")


def regressao_caudal(ref):
    from sklearn.linear_model import LinearRegression
    d = pd.read_csv(PRATICA / "dados/caudal_e_chuva_diarios.csv", parse_dates=["data"])
    d["futuro"] = d["caudal_m3s"].shift(-HORIZONTE)
    d = d.dropna()
    treino = d[d["data"].dt.year <= ULTIMO_ANO_TREINO]
    m = LinearRegression().fit(treino[PISTAS_CAUDAL], treino["futuro"])
    j = d[(d["data"] >= "2025-12-20") & (d["data"] <= "2026-02-12")].copy()
    j["dia"] = j["data"] + pd.Timedelta(days=HORIZONTE)
    j["previsto"] = m.predict(j[PISTAS_CAUDAL])
    fig, ax = plt.subplots(figsize=(16, 6.4))
    grelha(ax)
    for lim, nome, c in [(164, "amarelo", "#B88A00"), (376, "laranja", "#E07B00"), (970, "vermelho", "#C0392B")]:
        ax.axhline(lim, color=c, lw=2, ls="--", zorder=1)
        if nome == "amarelo":                            # à direita, onde as curvas já passaram por cima
            ax.text(j["dia"].iloc[-1], lim + 40, f"alerta {nome} ({lim} m³/s)", color=c, fontsize=17, weight="bold", ha="right")
        else:
            ax.text(j["dia"].iloc[0], lim + 45, f"alerta {nome} ({lim} m³/s)", color=c, fontsize=17, weight="bold")
    ax.plot(j["dia"], j["futuro"], color=TINTA, lw=3, label="o que aconteceu")
    ax.plot(j["dia"], j["previsto"], color=CINZA_G, lw=3.5, label=f"o que a recta previu {HORIZONTE} dias antes")
    import matplotlib.dates as mdates
    ax.xaxis.set_major_locator(mdates.DayLocator(bymonthday=[1, 15]))
    ax.xaxis.set_major_formatter(mdates.DateFormatter("%d/%m"))
    ax.set_ylabel("Caudal (m³/s)")
    ax.set_ylim(0, 3300)
    ax.legend(loc="upper right", fontsize=19)
    return guardar(fig, "regressao_caudal_2026.png")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    ref = json.loads((FAC / "resultados_de_referencia.json").read_text(encoding="utf-8"))
    f = ferramentas_namespace()
    feitos = [classificacao(f)]
    p, (a, b) = regressao()
    feitos += [p, treino_passo_a_passo(), agrupamento(f), kmeans_passos(), kmeans_mapa(f)]
    f1, f2, melhor = ajuste_e_complexidade()
    feitos += [f1, f2]
    p, perguntas = arvore_caixas()
    feitos.append(p)
    p, votos = knn()
    feitos += [p, rede(), regressao_caudal(ref)]
    info = {"regressao_estudo": {"a": round(float(a), 2), "b": round(float(b), 1)}, "grau_melhor": melhor,
            "arvore_perguntas": perguntas, "knn_votos": votos}
    (OUT / "figuras_teoria.json").write_text(json.dumps(info, ensure_ascii=False, indent=1), encoding="utf-8")
    from PIL import Image
    for p in feitos:
        im = Image.open(p)
        print(f"{p.name:32s} {im.size[0]:5d} x {im.size[1]:5d}  {p.stat().st_size / 1024:5.0f} KB")
    print(json.dumps(info, ensure_ascii=False))


if __name__ == "__main__":
    main()
