"""As figuras do Módulo 2 (como uma máquina aprende), feitas com os dados e os modelos das aulas práticas.

    cd scripts && ../.venv/bin/python -m workshop2.figuras_modulo2

Tudo com dados reais do Incomáti e, sempre que possível, com os MODELOS QUE AS AULAS TREINARAM (guardados em
Workshop_2/0_facilitadores/aulas_resolvidas/modelos_treinados/): a árvore da Aula 1, a floresta da Aula 2 e a
regressão linear da Aula 4. Escreve os PNG em Workshop_2/0_facilitadores/imagens_para_slides/modulo2/ e os números
que os slides citam em numeros.json, na mesma pasta.

Cores como nas outras figuras da teoria: azul só para a água, laranja para a não água, preto para o treino e
carmim para o teste; letra Arial (Liberation Sans) grande, para se ler ao fundo da sala.
"""

import importlib.util
import json
import os

import joblib
import matplotlib
import numpy as np
import pandas as pd

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch, Rectangle  # noqa: E402

from .comum import FAC, PRATICA  # noqa: E402

OUT = FAC / "imagens_para_slides" / "modulo2"
MODELOS = FAC / "aulas_resolvidas" / "modelos_treinados"
AZUL, LARANJA = "#2a78d6", "#eb6834"
TINTA, SUAVE, GRELHA, NEUTRO = "#1B1F24", "#4A5563", "#D9DEE4", "#9AA4AF"
PRETO_G, VERMELHO_G = "#1A1A1A", "#A51C30"
RAMPA = ["#E8A3A8", "#CF5A66", "#A51C30", "#5C0F1A"]          # passos do treino, do claro ao escuro
FUNDO_AGUA, FUNDO_TERRA = "#dbe9fa", "#fbe1d6"
plt.rcParams.update({"font.family": ["Liberation Sans", "Arial", "DejaVu Sans"], "font.size": 20, "text.color": TINTA,
                     "axes.edgecolor": NEUTRO, "axes.labelcolor": SUAVE, "xtick.color": SUAVE, "ytick.color": SUAVE,
                     "axes.spines.top": False, "axes.spines.right": False, "axes.titlesize": 22, "axes.titleweight": "bold",
                     "axes.titlecolor": TINTA, "legend.frameon": False, "savefig.facecolor": "white"})
PISTAS = ["caudal_m3s", "chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"]       # as pistas da Aula 4


def pt(x, casas=2):
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",")


def grelha(ax):
    ax.grid(color=GRELHA, lw=1)
    ax.set_axisbelow(True)


def guardar(fig, nome, dpi=100):
    fig.savefig(OUT / nome, dpi=dpi, bbox_inches="tight", pad_inches=0.15)
    plt.close(fig)
    print("  ", nome)


def ferramentas():
    """O ferramentas.py dos alunos: as mesmas funções (e os mesmos números) das aulas."""
    spec = importlib.util.spec_from_file_location("ferramentas", PRATICA / "ferramentas.py")
    F = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(F)
    return F


def cor_natural(img, brilho=0.15):
    return np.clip(np.dstack([img["vermelho"], img["verde"], img["azul"]]) / brilho, 0, 1)


# ---------------------------------------------------------------- Aula 1: os rótulos, o SWIR, o corte e o mapa

def rotulos(F, cheia, pontos):
    fig, ax = plt.subplots(figsize=(7.4, 10.4))
    ax.imshow(cor_natural(cheia))
    ax.contour(cheia["zona"].astype(int), levels=[0.5], colors="white", linewidths=1.2)
    for chave, marca, cor, nome in [("agua", "o", AZUL, "água (15 pontos)"), ("nao_agua", "s", LARANJA, "não água (15 pontos)")]:
        ls, cs = zip(*pontos[chave])
        ax.plot(cs, ls, marca, ms=15, mfc=cor, mec="white", mew=2, ls="none", label=nome)
    ax.legend(loc="lower left", fontsize=20, frameon=True, facecolor="white", edgecolor="white", framealpha=0.92)
    ax.set_axis_off()
    guardar(fig, "rotulos_2026.png", dpi=130)       # as imagens do satélite com mais pormenor


def swir(F, ex, limite):
    rng = np.random.default_rng(1)
    fig, ax = plt.subplots(figsize=(15, 5.6))
    grelha(ax)
    for linha, (rot, cor, nome) in enumerate([(1, AZUL, "água"), (0, LARANJA, "não água")]):
        v = ex.loc[ex["rótulo"] == rot, "swir"].to_numpy()
        ax.scatter(v, linha + rng.uniform(-0.28, 0.28, v.size), s=34, color=cor, alpha=0.7, edgecolor="white", linewidth=0.4)
    ax.axvline(limite, color=VERMELHO_G, lw=3.5)
    ax.text(limite + 0.006, 1.47, f"o limite que a árvore aprendeu: SWIR = {pt(limite)}", color=VERMELHO_G, fontsize=22,
            weight="bold", va="center")
    ax.set_yticks([0, 1], ["água\n(375 píxeis)", "não água\n(363 píxeis)"], fontsize=21)
    ax.set_ylim(-0.6, 1.75)
    ax.set_xlim(0, ex["swir"].max() * 1.03)
    ax.set_xlabel("SWIR (infravermelho de onda curta), de 0 a 1")
    guardar(fig, "swir_2026.png")


def mapa(F, cheia, arvore):
    m = F.prever_mapa(arvore, cheia)
    agua = (m == 1) & cheia["zona"] & ~cheia["nuvem"]
    nuvem = cheia["nuvem"] & cheia["zona"]
    fundo = cor_natural(cheia) * 0.45 + 0.55
    fig, ax = plt.subplots(figsize=(7.4, 10.4))
    ax.imshow(fundo)
    ax.imshow(np.ma.masked_where(~agua, agua), cmap=matplotlib.colors.ListedColormap([AZUL]), vmin=0, vmax=1)
    ax.imshow(np.ma.masked_where(~nuvem, nuvem), cmap=matplotlib.colors.ListedColormap(["#9E9E9E"]), vmin=0, vmax=1)
    ax.contour(cheia["zona"].astype(int), levels=[0.5], colors=TINTA, linewidths=1.2)
    ax.legend(handles=[Patch(color=AZUL, label="água, segundo a árvore"), Patch(color="#9E9E9E", label="nuvem"),
                       Line2D([0], [0], color=TINTA, lw=1.5, label="limite do distrito")],
              loc="lower left", fontsize=20, frameon=True, facecolor="white", edgecolor="white", framealpha=0.92)
    ax.set_axis_off()
    guardar(fig, "mapa_2026.png", dpi=130)
    return F.hectares(m, cheia)


def tabela_dos_dados(F, cheia, pontos):
    """Quatro píxeis reais da cheia de 2026 (o centro de 4 pontos da equipa), para a tabela «exemplos, pistas e rótulo»."""
    escolhidos = [("água: cheia barrenta", "agua", 0), ("água: lagoa", "agua", 12),
                  ("não água: vegetação", "nao_agua", 0), ("não água: areia", "nao_agua", 10)]
    linhas = []
    for nome, chave, i in escolhidos:
        l, c = pontos[chave][i]
        assert not cheia["nuvem"][l, c]
        linhas.append({"pixel": nome, "rotulo": "água" if chave == "agua" else "não água",
                       **{b: round(float(cheia[b][l, c]), 3) for b in F.BANDAS}})
    return linhas


def pixeis_da_actividade(F):
    """Píxeis reais de 2021 (água barrenta) para «sejam uma árvore» e «a turma é uma floresta»: NIR, SWIR e rótulo.
    Os índices são linhas da tabela de exemplos da Prática 1 com o ano 2021 (sempre a mesma, os pontos não mudam)."""
    img = F.carregar("incomati_2021_chuvosa.npz")
    p = F.pontos_da_equipa(2021)
    ex = F.tabela_de_exemplos(img, p["agua"], p["nao_agua"])

    def px(i, rot):
        assert int(ex.loc[i, "rótulo"]) == rot, (i, rot)
        return {"nir": round(float(ex.loc[i, "nir"]), 3), "swir": round(float(ex.loc[i, "swir"]), 3),
                "rotulo": "água" if rot else "não água"}

    oito = [px(14, 1), px(136, 0), px(121, 1), px(168, 0), px(94, 1), px(220, 0), px(99, 1), px(154, 0)]
    agua = [x["swir"] for x in oito if x["rotulo"] == "água"]
    terra = [x["swir"] for x in oito if x["rotulo"] == "não água"]
    nir_agua = [x["nir"] for x in oito if x["rotulo"] == "água"]
    nir_terra = [x["nir"] for x in oito if x["rotulo"] == "não água"]
    assert max(agua) < min(terra), "a actividade tem de ter uma resposta com o SWIR"
    assert max(nir_agua) > min(nir_terra), "o NIR sozinho não deve chegar (é a lição da actividade)"
    return {"oito": oito, "x": px(111, 1), "y": px(97, 1), "swir_max_agua": max(agua), "swir_min_terra": min(terra)}


# ---------------------------------------------------------------- Aula 2: os votos da floresta

def votos(F, cheia, floresta):
    """Um píxel real da margem da cheia em que as 100 árvores da Aula 2 não estão todas de acordo."""
    oficial = np.load(F.encontrar("mapa_oficial_cheia_2026.npz"))["rotulo"]
    ok = (oficial == 1) & ~cheia["nuvem"] & cheia["zona"]
    linhas, colunas = np.nonzero(ok)
    X = F.tabela_da_imagem(cheia).to_numpy()
    idx = linhas * cheia["verde"].shape[1] + colunas
    rng = np.random.default_rng(3)
    amostra = rng.choice(idx, 60000, replace=False)
    prob = floresta.predict_proba(pd.DataFrame(X[amostra], columns=F.BANDAS))[:, 1]
    alvo = amostra[np.argmin(np.abs(prob - 0.72))]
    x = pd.DataFrame(X[[alvo]], columns=F.BANDAS)
    v = np.array([int(e.predict(x.to_numpy())[0]) for e in floresta.estimators_])
    n_agua = int(v.sum())
    fig, ax = plt.subplots(figsize=(10, 6.4))
    ordem = np.sort(v)[::-1]
    for i, voto in enumerate(ordem):
        lin, col = divmod(i, 20)
        ax.add_patch(Rectangle((col, 4 - lin), 0.86, 0.86, color=AZUL if voto else LARANJA))
    ax.set_xlim(-0.2, 20)
    ax.set_ylim(-0.2, 5)
    ax.set_aspect("equal")
    ax.set_axis_off()
    ax.legend(handles=[Patch(color=AZUL, label=f"{n_agua} árvores votam «água»"),
                       Patch(color=LARANJA, label=f"{100 - n_agua} árvores votam «não água»")],
              loc="upper center", bbox_to_anchor=(0.5, -0.02), ncol=2, fontsize=22)
    guardar(fig, "votos_floresta.png")
    l, c = divmod(int(alvo), cheia["verde"].shape[1])
    return {"agua": n_agua, "linha": int(l), "coluna": int(c), "bandas": {b: round(float(cheia[b][l, c]), 3) for b in F.BANDAS},
            "profundidade_min": min(e.get_depth() for e in floresta.estimators_),
            "profundidade_max": max(e.get_depth() for e in floresta.estimators_)}


# ---------------------------------------------------------------- Aula 4: a regressão do caudal

def dias_da_aula4(F, horizonte=3):
    d = pd.read_csv(F.encontrar("caudal_e_chuva_diarios.csv"), parse_dates=["data"])
    d["alvo"] = d["caudal_m3s"].shift(-horizonte)
    d = d.dropna()
    return d[d["data"].dt.year <= 2018], d[d["data"].dt.year >= 2019]


def regressao(F, treino):
    from sklearn.linear_model import LinearRegression
    m = LinearRegression().fit(treino[["caudal_m3s"]], treino["alvo"])
    a, b = float(m.coef_[0]), float(m.intercept_)
    fig, ax = plt.subplots(figsize=(10, 7.6))
    grelha(ax)
    ax.scatter(treino["caudal_m3s"], treino["alvo"], s=16, color=PRETO_G, alpha=0.35, edgecolor="none", zorder=3)
    xs = np.linspace(0, 2000, 50)
    ax.plot(xs, a * xs + b, color=VERMELHO_G, lw=3.5, zorder=4)
    hoje = 1000
    ax.scatter([hoje], [a * hoje + b], s=520, marker="*", color=TINTA, edgecolor="white", linewidth=1.5, zorder=5)
    ax.annotate(f"hoje {hoje} m³/s → daqui a 3 dias ≈ {a * hoje + b:.0f} m³/s", (hoje, a * hoje + b),
                xytext=(120, 1880), fontsize=20, color=TINTA, arrowprops=dict(arrowstyle="->", color=TINTA, lw=1.6))
    ax.text(1000, 180, f"a recta aprendida:\ndaqui a 3 dias ≈ {pt(a)} × hoje + {pt(b, 1)}", fontsize=21, color=VERMELHO_G,
            weight="bold")
    ax.set_xlim(0, 2000)
    ax.set_ylim(0, 2100)
    ax.set_xlabel("Caudal hoje (m³/s)")
    ax.set_ylabel("Caudal 3 dias depois (m³/s)")
    guardar(fig, "regressao_caudal.png")
    return a, b


def treino_passo_a_passo(treino, a_final, b_final):
    """A mesma recta, treinada passo a passo (descida do gradiente), com os dias de treino da Aula 4."""
    x, y = treino["caudal_m3s"].to_numpy(), treino["alvo"].to_numpy()
    xm, xs_ = x.mean(), x.std()
    z = (x - xm) / xs_
    w, c = 0.0, 0.0                                        # a primeira tentativa: «daqui a 3 dias é sempre 0»
    historia, erros = {}, []
    for passo in range(61):
        prev = w * z + c
        erros.append(float(np.mean(np.abs(prev - y))))
        if passo in (0, 3, 10, 60):
            historia[passo] = (w, c)
        g = prev - y
        w -= 0.05 * 2 * np.mean(g * z)
        c -= 0.05 * 2 * np.mean(g)
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 6.6), gridspec_kw={"width_ratios": [1.15, 1]})
    grelha(a1)
    grelha(a2)
    a1.scatter(x, y, s=10, color=NEUTRO, alpha=0.5, edgecolor="none", zorder=1)
    xs = np.linspace(0, 2000, 50)
    ultimo_y = None
    for (passo, (w_, c_)), cor in zip(historia.items(), RAMPA):
        ys = w_ * (xs - xm) / xs_ + c_
        a1.plot(xs, ys, color=cor, lw=3.2, zorder=2)
        y_txt = min(ys[-1], 2050)
        if ultimo_y is not None and abs(y_txt - ultimo_y) < 120:      # as legendas não se tocam
            y_txt = ultimo_y + 120
        a1.text(2030, y_txt, f"passo {passo}", color=TINTA, fontsize=18, va="center")
        ultimo_y = y_txt
    a1.set_xlim(0, 2000)
    a1.set_ylim(-50, 2100)
    a1.set_xlabel("Caudal hoje (m³/s)")
    a1.set_ylabel("Caudal 3 dias depois (m³/s)")
    a1.set_title("A recta melhora a cada passo", loc="left")
    a2.plot(range(len(erros)), erros, color=VERMELHO_G, lw=3.2)
    for passo, cor in zip(historia, RAMPA):
        a2.scatter([passo], [erros[passo]], s=120, color=cor, edgecolor="white", linewidth=1.5, zorder=3)
    a2.set_xlabel("Passo do treino")
    a2.set_ylabel("Erro médio (m³/s)")
    a2.set_title("O erro desce até quase não mudar", loc="left")
    a2.set_ylim(0, max(erros) * 1.08)
    fig.tight_layout(w_pad=5)
    guardar(fig, "treino_caudal.png")
    return erros[0], erros[-1]


def cheia_2026(teste, linear):
    j = teste[(teste["data"] >= "2026-01-01") & (teste["data"] <= "2026-02-15")]
    dia = j["data"] + pd.Timedelta(days=3)
    prev = linear.predict(j[PISTAS])
    fig, ax = plt.subplots(figsize=(15, 6.2))
    grelha(ax)
    ax.plot(dia, j["alvo"], color=PRETO_G, lw=3.5, label="o caudal que aconteceu")
    ax.plot(dia, prev, color=VERMELHO_G, lw=3.5, ls="--", label="o que a regressão previu 3 dias antes")
    ax.set_ylabel("Caudal (m³/s)")
    ax.xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%d/%m"))
    ax.legend(loc="upper right", fontsize=21)
    guardar(fig, "cheia_2026_previsao.png")
    pico = int(np.argmax(j["alvo"].to_numpy()))
    return {"pico": float(j["alvo"].iloc[pico]), "dia_pico": dia.iloc[pico].strftime("%d/%m"),
            "previsto_no_pico": float(prev[pico]), "previsto_max": float(prev.max()),
            "dia_previsto_max": dia.iloc[int(np.argmax(prev))].strftime("%d/%m")}


# ---------------------------------------------------------------- o projecto: árvores em fila (Gradient Boosting)

def boosting(treino):
    """Gradient Boosting (a família do XGBoost dos Modelos A, B e C): árvores em fila, cada uma corrige o erro que ficou.
    Com uma pista (o caudal de hoje) e os dias de treino da Aula 4, para se poder desenhar."""
    from sklearn.ensemble import GradientBoostingRegressor
    X, y = treino[["caudal_m3s"]], treino["alvo"].to_numpy()
    g = GradientBoostingRegressor(n_estimators=100, max_depth=1, learning_rate=0.3, random_state=0).fit(X, y)
    grade = pd.DataFrame({"caudal_m3s": np.linspace(0, 2000, 800)})
    marcas = {1: None, 3: None, 10: None, 100: None}
    for n, p in enumerate(g.staged_predict(grade), start=1):
        if n in marcas:
            marcas[n] = p
    erros = [float(np.mean(np.abs(p - y))) for p in g.staged_predict(X)]
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(16, 6.6), gridspec_kw={"width_ratios": [1.15, 1]})
    grelha(a1)
    grelha(a2)
    a1.scatter(X["caudal_m3s"], y, s=10, color=NEUTRO, alpha=0.5, edgecolor="none", zorder=1)
    ultimo_y = None
    for (n, p), cor in zip(marcas.items(), RAMPA):
        a1.plot(grade["caudal_m3s"], p, color=cor, lw=3.2, zorder=2, drawstyle="steps-post")
        y_txt = min(p[-1], 2050)
        if ultimo_y is not None and abs(y_txt - ultimo_y) < 120:
            y_txt = ultimo_y + 120
        a1.text(2030, y_txt, f"{n} árvore" + ("s" if n > 1 else ""), color=TINTA, fontsize=18, va="center")
        ultimo_y = y_txt
    a1.set_xlim(0, 2000)
    a1.set_ylim(-50, 2100)
    a1.set_xlabel("Caudal hoje (m³/s)")
    a1.set_ylabel("Caudal 3 dias depois (m³/s)")
    a1.set_title("Cada árvore nova corrige o que ficou mal", loc="left")
    a2.plot(range(1, len(erros) + 1), erros, color=VERMELHO_G, lw=3.2)
    for n, cor in zip(marcas, RAMPA):
        a2.scatter([n], [erros[n - 1]], s=120, color=cor, edgecolor="white", linewidth=1.5, zorder=3)
    a2.set_xlabel("Número de árvores na fila")
    a2.set_ylabel("Erro médio no treino (m³/s)")
    a2.set_title("O erro desce a cada árvore", loc="left")
    a2.set_ylim(0, max(erros) * 1.08)
    fig.tight_layout(w_pad=5)
    guardar(fig, "boosting_caudal.png")
    return {"arvores": len(erros), "erro_1_arvore": erros[0], "erro_10_arvores": erros[9], "erro_100_arvores": erros[-1]}


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    antes = os.getcwd()
    os.chdir(PRATICA)
    try:
        F = ferramentas()
        cheia = F.carregar("incomati_2026_cheia.npz")
        pontos = F.pontos_da_equipa(2026)
        ex = F.tabela_de_exemplos(cheia, pontos["agua"], pontos["nao_agua"])
        arvore = joblib.load(MODELOS / "aula1_arvore_de_decisao.joblib")
        floresta = joblib.load(MODELOS / "aula2_floresta_100_arvores.joblib")
        linear = joblib.load(MODELOS / "aula4_regressao_linear.joblib")
        limite = float(arvore.tree_.threshold[0])
        print("Figuras do Módulo 2 em", OUT)
        rotulos(F, cheia, pontos)
        swir(F, ex, limite)
        ha = mapa(F, cheia, arvore)
        v = votos(F, cheia, floresta)
        treino, teste = dias_da_aula4(F)
        a, b = regressao(F, treino)
        e0, e1 = treino_passo_a_passo(treino, a, b)
        c26 = cheia_2026(teste, linear)
        bo = boosting(treino)
        numeros = {
            "aula1": {"exemplos": len(ex), "agua": int((ex["rótulo"] == 1).sum()), "limite_swir": limite,
                      "folhas": [int(x) for x in arvore.tree_.n_node_samples[1:]], "hectares": ha,
                      "pixeis_imagem": int(cheia["verde"].size)},
            "votos": v,
            "regressao_1_pista": {"a": a, "b": b, "erro_passo_0": e0, "erro_final": e1, "passos": 60},
            "tabela_dados": tabela_dos_dados(F, cheia, pontos),
            "actividade": pixeis_da_actividade(F),
            "linear_aula4": {"pesos": dict(zip(linear.feature_names_in_, map(float, linear.coef_))),
                             "intercepto": float(linear.intercept_), "dias_treino": len(treino), "dias_teste": len(teste)},
            "cheia_2026": c26,
            "boosting": bo,
        }
        (OUT / "numeros.json").write_text(json.dumps(numeros, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
        print(json.dumps(numeros, ensure_ascii=False, indent=1))
    finally:
        os.chdir(antes)


if __name__ == "__main__":
    main()
