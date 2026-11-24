"""O ficheiro ferramentas.py das aulas práticas do Workshop 2 (copiado para Workshop_2/2_pratica/ferramentas.py).

As respostas das perguntas de escolha entram codificadas (__RESPOSTAS__), para não se lerem sem querer.
"""

FERRAMENTAS = r'''"""Ferramentas das aulas práticas do Workshop 2 · projecto EYES TO EARTH.

Os notebooks usam este ficheiro com a linha:   from ferramentas import *
Não é preciso abri-lo nem mudá-lo. Tem as funções que abrem os dados da pasta dados/, desenham as
imagens e os mapas, fazem o exame com o mapa oficial e verificam os passos das práticas.
"""
import os
import json
import base64
import warnings

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch

warnings.filterwarnings("ignore")
pd.set_option("display.precision", 3)

BANDAS = ["azul", "verde", "vermelho", "nir", "swir"]   # as 5 "cores" que o satélite mede (de 0 a 1)
HECTARES_POR_PIXEL = 0.09                               # cada píxel tem 30 m x 30 m = 900 m² = 0,09 hectares
RAIO = 2                                                # cada ponto marcado vale um quadrado de 5 x 5 píxeis
AZUL_AGUA = "#1565C0"


# ---------------------------------------------------------------- abrir os dados

def encontrar(nome):
    """Procura um ficheiro na pasta dados/ (ao lado do notebook)."""
    for pasta in ["dados", os.path.join("..", "dados"), os.path.join("..", "..", "2_pratica", "dados")]:
        caminho = os.path.join(pasta, nome)
        if os.path.exists(caminho):
            return caminho
    raise FileNotFoundError("Não encontrei dados/" + nome + ". Vejam se o nome está certo e se abriram o notebook "
                            "a partir da pasta Workshop_2/2_pratica.")


def carregar(nome):
    """Abre uma imagem do satélite (.npz): as 5 bandas, onde há nuvens, a zona do distrito e a data."""
    z = np.load(encontrar(nome))
    img = {banda: z[banda] / 10000 for banda in BANDAS}
    img["nuvem"] = z["nuvem"]                 # True onde há nuvem ou sombra: aí o satélite não vê o chão
    img["zona"] = z["zona"]                   # True dentro do distrito de Marracuene (sem o mar)
    img["data"] = str(z["data"])
    img["dia"] = "/".join(reversed(img["data"].split("-")))     # a data à portuguesa: 24/01/2026
    img["satelite"] = str(z["satelite"])
    img["caudal_m3s"] = float(z["caudal_m3s"])
    return img


def pontos_da_equipa(ano):
    """Os pontos de exemplo que a equipa preparou para essa imagem: {"agua": [(linha, coluna), ...], "nao_agua": [...]}."""
    with open(encontrar("exemplos_da_equipa.json"), encoding="utf-8") as f:
        return json.load(f)[str(ano)]


# ---------------------------------------------------------------- tabelas

def tabela_de_exemplos(img, agua, nao_agua):
    """Uma linha por píxel à volta de cada ponto marcado: as 5 bandas e o rótulo (1 = água, 0 = não água)."""
    linhas = []
    for rotulo, pontos in ((1, agua), (0, nao_agua)):
        for linha, coluna in pontos:
            for l in range(max(linha - RAIO, 0), linha + RAIO + 1):
                for c in range(max(coluna - RAIO, 0), coluna + RAIO + 1):
                    if l < img["nuvem"].shape[0] and c < img["nuvem"].shape[1] and not img["nuvem"][l, c]:
                        linhas.append([img[b][l, c] for b in BANDAS] + [rotulo])
    return pd.DataFrame(linhas, columns=BANDAS + ["rótulo"])


def tabela_da_imagem(img):
    """A imagem inteira como tabela: uma linha por píxel, uma coluna por banda."""
    return pd.DataFrame({b: np.nan_to_num(img[b].ravel()) for b in BANDAS})


def prever_mapa(modelo, img):
    """O modelo diz, para cada píxel da imagem, 1 (água) ou 0 (não água). Devolve um mapa."""
    if not hasattr(modelo, "n_features_in_"):
        raise RuntimeError("O modelo ainda não foi treinado: corram primeiro a célula do treino, com .fit(...).")
    return modelo.predict(tabela_da_imagem(img)).reshape(img["verde"].shape).astype(int)


def numero(valor, casas=0):
    """Um número à portuguesa: espaço nos milhares e vírgula nas décimas (20 300 ou 26,3)."""
    return f"{valor:,.{casas}f}".replace(",", " ").replace(".", ",")


def percentagem(fraccao, casas=1):
    """Uma parte (de 0 a 1) em percentagem, à portuguesa: 0.982 dá 98,2 %."""
    return numero(100 * fraccao, casas) + " %"


def hectares(mapa, img):
    """Quantos hectares de água há no mapa, dentro do distrito e fora das nuvens."""
    return float(((mapa == 1) & img["zona"] & ~img["nuvem"]).sum() * HECTARES_POR_PIXEL)


# ---------------------------------------------------------------- desenhar

def cor_natural(img, brilho=0.15):
    """Junta vermelho, verde e azul numa imagem a cores, como a veríamos de um avião."""
    return np.clip(np.dstack([img["vermelho"], img["verde"], img["azul"]]) / brilho, 0, 1)


def ver_imagem(img, titulo="", agua=(), nao_agua=(), agua_teste=(), nao_agua_teste=()):
    """Mostra a imagem a cores e os pontos marcados: círculos = água, quadrados = não água.
    Os pontos de teste aparecem só com o contorno amarelo."""
    plt.figure(figsize=(7, 10))
    plt.imshow(cor_natural(img))
    legenda = []
    if len(agua):
        plt.plot([c for _, c in agua], [l for l, _ in agua], "o", ms=9, mfc="cyan", mec="black", ls="none")
        legenda.append("água (treino)" if len(agua_teste) else "água")
    if len(nao_agua):
        plt.plot([c for _, c in nao_agua], [l for l, _ in nao_agua], "s", ms=9, mfc="orange", mec="black", ls="none")
        legenda.append("não água (treino)" if len(nao_agua_teste) else "não água")
    if len(agua_teste):
        plt.plot([c for _, c in agua_teste], [l for l, _ in agua_teste], "o", ms=11, mfc="none", mec="yellow", mew=2.5, ls="none")
        legenda.append("água (teste)")
    if len(nao_agua_teste):
        plt.plot([c for _, c in nao_agua_teste], [l for l, _ in nao_agua_teste], "s", ms=11, mfc="none", mec="yellow", mew=2.5, ls="none")
        legenda.append("não água (teste)")
    if legenda:
        plt.legend(legenda, loc="lower left", fontsize=9)
    plt.title(titulo)
    plt.xlabel("coluna")
    plt.ylabel("linha")
    plt.show()


def ver_mapa(mapa, img, titulo=""):
    """Mostra o mapa do modelo dentro do distrito: azul = água; cinzento = nuvens (o satélite não viu).
    A linha preta é o limite do distrito: as contas dos hectares são só lá dentro (o mar não conta)."""
    fundo = cor_natural(img) * 0.5 + 0.5
    agua = (mapa == 1) & img["zona"] & ~img["nuvem"]
    nuvem = img["nuvem"] & img["zona"]
    plt.figure(figsize=(7, 10))
    plt.imshow(fundo)
    plt.imshow(np.ma.masked_where(~agua, agua), cmap=ListedColormap([AZUL_AGUA]), vmin=0, vmax=1)
    plt.imshow(np.ma.masked_where(~nuvem, nuvem), cmap=ListedColormap(["#9E9E9E"]), vmin=0, vmax=1)
    plt.contour(img["zona"].astype(int), levels=[0.5], colors="black", linewidths=0.8)
    plt.legend(handles=[Patch(color=AZUL_AGUA, label="água"), Patch(color="#9E9E9E", label="nuvem"),
                        Line2D([0], [0], color="black", lw=1, label="limite do distrito")], loc="lower left")
    plt.title(titulo)
    plt.axis("off")
    plt.show()


FAIXAS_DE_MARE = [-5, -0.5, 0.5, 5]          # metros: abaixo de -0,5 m é maré baixa; acima de 0,5 m é maré alta
NOMES_DAS_FAIXAS = ["maré baixa", "maré média", "maré alta"]


def turva_por_mare(tabela):
    """A parte das manhãs com a água turva (de 0 a 1) em cada faixa de maré."""
    faixa = pd.cut(tabela["altura_da_mare_m"], FAIXAS_DE_MARE, labels=NOMES_DAS_FAIXAS)
    return tabela.groupby(faixa, observed=False)["turva"].mean()


def ver_mare(tabela):
    """Dois gráficos: a turbidez (NDTI) de cada manhã contra a altura da maré, e a parte das manhãs turvas
    na maré baixa, média e alta."""
    parte = turva_por_mare(tabela)
    fig, (a, b) = plt.subplots(1, 2, figsize=(12, 4.3))
    a.scatter(tabela["altura_da_mare_m"], tabela["ndti"], s=6, alpha=0.35, color="#8D6E63")
    a.axvline(0, color="#9E9E9E", lw=1)
    a.set_xlabel("altura da maré à hora do satélite (m)")
    a.set_ylabel("NDTI (mais alto = mais barrenta)")
    a.set_title("Cada ponto é uma manhã num troço")
    b.bar(range(3), 100 * parte.values, color=["#8D6E63", "#BCAAA4", "#64B5F6"])
    b.set_xticks(range(3), ["maré baixa\n(abaixo de -0,5 m)", "maré média", "maré alta\n(acima de 0,5 m)"])
    for i, v in enumerate(parte.values):
        b.text(i, 100 * v + 2, percentagem(v, 0), ha="center", fontsize=12)
    b.set_ylim(0, 105)
    b.set_ylabel("manhãs com a água turva (%)")
    b.set_title("A água turva, por altura da maré")
    plt.tight_layout()
    plt.show()
    for nome, v in parte.items():
        print(f"{nome:11s} {percentagem(v, 0):>5s} das manhãs com a água turva")


# ---------------------------------------------------------------- exames

def acerto(verdade, previsto):
    """A parte das respostas certas (de 0 a 1)."""
    return float((np.asarray(verdade) == np.asarray(previsto)).mean())


def exame_mapa_oficial(modelo, img):
    """O mapa oficial da cheia de 24/01/2026 (Copernicus EMS): a verdade, píxel a píxel (1 = água, 0 = não água).
    Devolve a verdade e a resposta do modelo, só nos píxeis que o mapa oficial marca e sem nuvens."""
    oficial = np.load(encontrar("mapa_oficial_cheia_2026.npz"))["rotulo"]
    ok = (oficial >= 0) & ~img["nuvem"]
    previsto = prever_mapa(modelo, img)
    return oficial[ok], previsto[ok]


def matriz_de_confusao(verdade, previsto, titulo="A matriz de confusão"):
    """Conta os acertos e os dois tipos de erro, e desenha-os num quadro 2 x 2."""
    verdade, previsto = np.asarray(verdade), np.asarray(previsto)
    r = {"água certa": int(((verdade == 1) & (previsto == 1)).sum()),
         "água perdida": int(((verdade == 1) & (previsto == 0)).sum()),
         "falso alarme": int(((verdade == 0) & (previsto == 1)).sum()),
         "terra certa": int(((verdade == 0) & (previsto == 0)).sum())}
    numeros = [[r["água certa"], r["água perdida"]], [r["falso alarme"], r["terra certa"]]]
    nomes = [["água certa", "água perdida"], ["falso alarme", "terra certa"]]
    cores = [["#DCEFE3", "#F6D5D5"], ["#F6D5D5", "#DCEFE3"]]
    fig, ax = plt.subplots(figsize=(6, 4.2))
    for i in range(2):
        for j in range(2):
            ax.add_patch(plt.Rectangle((j, 1 - i), 1, 1, color=cores[i][j], ec="white", lw=3))
            ax.text(j + 0.5, 1.5 - i, f"{nomes[i][j]}\n{numeros[i][j]:,}".replace(",", " "), ha="center", va="center", fontsize=13)
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)
    ax.set_xticks([0.5, 1.5], ["o modelo disse ÁGUA", "o modelo disse NÃO ÁGUA"])
    ax.set_yticks([1.5, 0.5], ["era ÁGUA", "era NÃO ÁGUA"])
    ax.tick_params(length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.set_title(titulo + " (verde = certo, vermelho = erro)")
    plt.show()
    for nome, valor in r.items():
        print(f"{nome:14s} {valor:9,d} píxeis".replace(",", " "))
    return r


# ---------------------------------------------------------------- corrigir as perguntas «Para pensar»

_RESPOSTAS = json.loads(base64.b64decode("__RESPOSTAS__").decode())


def ano_do_par(ano):
    """Diz se o ANO é um dos anos dos pares (sem isto, um ano errado dava um erro de ficheiro em falta)."""
    if isinstance(ano, str):
        print("Ainda não: escrevam o ano sem aspas, por exemplo:  ANO = 2024")
        return False
    if ano not in ANOS_DOS_PARES:
        print("Ainda não: o ANO tem de ser um destes: 2024, 2021, 2022, 2014 ou 2025 (o do vosso par, na tabela).")
        return False
    return True


def pronto(*respostas):
    """Diz se a célula já foi preenchida (sem ...)."""
    if any(r is ... for r in respostas):
        print("Falta preencher: troquem os ... pela vossa resposta e corram a célula outra vez.")
        return False
    return True


def verificar(pergunta, resposta):
    """Corrige uma pergunta de escolha: a resposta é a letra entre aspas, por exemplo "a"."""
    if not pronto(resposta):
        return
    certa, explicacao, dica = _RESPOSTAS[pergunta]
    if str(resposta).strip().lower().startswith(certa):
        print("Certo! " + explicacao)
    else:
        print("Ainda não. " + dica)


# ---------------------------------------------------------------- corrigir os passos das práticas
# Cada verificação vai buscar as variáveis que os alunos criaram no notebook (não dá erro se ainda não existirem).

ANOS_DOS_PARES = [2024, 2021, 2022, 2014, 2025]
PISTAS_COM_MARE = ["caudal_m3s", "chuva_7d_mm", "mes", "altura_da_mare_m"]


def _vars():
    import __main__
    return vars(__main__)


def _falta(*nomes):
    g = _vars()
    em_falta = [n for n in nomes if n not in g or g[n] is ...]
    if em_falta:
        print("Ainda não: falta criar " + ", ".join(em_falta) + ". Escrevam o código na célula de cima e corram-na.")
        return True
    return False


def _tabela_ok(t, colunas):
    return isinstance(t, pd.DataFrame) and list(t.columns) == colunas


def verificar_passo(passo):
    """Corrige um passo de uma prática: diz se o que escreveram está certo, e dá uma pista se não estiver."""
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LinearRegression
    g = _vars()
    try:
        if passo == "1.2":
            if _falta("ANO"):
                return
            if not ano_do_par(g["ANO"]):
                return
            elif _falta("img", "pontos"):
                return
            elif g["img"]["data"][:4] != str(g["ANO"]):
                print("Ainda não: a imagem não é a do vosso ano. Corram outra vez a célula de cima, com o ANO certo.")
            else:
                print(f"Certo! A imagem do vosso ano é de {g['img']['dia']}, do satélite {g['img']['satelite']}.")
        elif passo == "1.3":
            if _falta("exemplos"):
                return
            esperado = tabela_de_exemplos(g["img"], g["pontos"]["agua"], g["pontos"]["nao_agua"])
            if _tabela_ok(g["exemplos"], BANDAS + ["rótulo"]) and len(g["exemplos"]) == len(esperado):
                e = g["exemplos"]
                print(f"Certo! {len(e)} exemplos: {(e['rótulo'] == 1).sum()} de água e {(e['rótulo'] == 0).sum()} de não água.")
            else:
                print("Ainda não. Pista: tabela_de_exemplos(img, pontos[\"agua\"], pontos[\"nao_agua\"]), com a imagem do vosso ano (img).")
        elif passo == "1.4":
            if _falta("X", "y"):
                return
            if _tabela_ok(g["X"], BANDAS) and len(g["y"]) == len(g["X"]) and getattr(g["y"], "name", None) == "rótulo":
                print("Certo! X tem as 5 bandas (as características) e y tem os rótulos (as respostas certas).")
            else:
                print("Ainda não. Pista: X = exemplos[BANDAS] e y = exemplos[\"rótulo\"].")
        elif passo == "1.5":
            if _falta("arvore"):
                return
            a = g["arvore"]
            if getattr(a, "n_features_in_", None) == len(BANDAS):
                from sklearn.tree import export_text
                print("Certo! A árvore foi treinada. Aprendeu esta regra:\n")
                print(export_text(a, feature_names=BANDAS).replace("class: 1", "ÁGUA").replace("class: 0", "NÃO ÁGUA"))
            else:
                print("Ainda não: a árvore ainda não foi treinada. Pista: arvore.fit(X, y)")
        elif passo == "1.6":
            if _falta("mapa"):
                return
            certo = prever_mapa(g["arvore"], g["img"])
            if isinstance(g["mapa"], np.ndarray) and g["mapa"].shape == certo.shape and (g["mapa"] == certo).all():
                print(f"Certo! Água no distrito, no vosso ano: {numero(hectares(certo, g['img']))} hectares.")
            else:
                print("Ainda não. Pista: mapa = prever_mapa(arvore, img)")
        elif passo == "2.2":
            if _falta("agua_treino", "agua_teste", "terra_treino", "terra_teste"):
                return
            p = pontos_da_equipa(2026)
            ok = (list(g["agua_teste"]) == p["agua"][:5] and list(g["agua_treino"]) == p["agua"][5:]
                  and list(g["terra_teste"]) == p["nao_agua"][:5] and list(g["terra_treino"]) == p["nao_agua"][5:])
            if ok:
                print("Certo! Treino: 10 + 10 pontos. Teste: os primeiros 5 + 5, que o modelo nunca vai ver no treino.")
            else:
                print("Ainda não. Pista: os primeiros 5 são o teste ([:5]) e os outros são o treino ([5:]).")
        elif passo == "2.3":
            if _falta("treino", "teste"):
                return
            if _tabela_ok(g["treino"], BANDAS + ["rótulo"]) and _tabela_ok(g["teste"], BANDAS + ["rótulo"]):
                print(f"Certo! {len(g['treino'])} exemplos de treino e {len(g['teste'])} de teste.")
            else:
                print("Ainda não. Pista: treino = tabela_de_exemplos(cheia, agua_treino, terra_treino), e o mesmo para o teste.")
        elif passo == "2.4":
            if _falta("floresta"):
                return
            ref = RandomForestClassifier(n_estimators=100, random_state=0).fit(g["treino"][BANDAS], g["treino"]["rótulo"])
            f = g["floresta"]
            if getattr(f, "n_features_in_", None) == len(BANDAS) and (f.predict(g["teste"][BANDAS]) == ref.predict(g["teste"][BANDAS])).all() and f.n_estimators == 100:
                print("Certo! A floresta de 100 árvores foi treinada só com o treino.")
            else:
                print("Ainda não. Pista: floresta = RandomForestClassifier(n_estimators=100, random_state=0) e depois floresta.fit(treino[BANDAS], treino[\"rótulo\"])")
        elif passo == "2.5":
            if _falta("nota_treino", "nota_teste"):
                return
            f, tr, te = g["floresta"], g["treino"], g["teste"]
            a, b = acerto(tr["rótulo"], f.predict(tr[BANDAS])), acerto(te["rótulo"], f.predict(te[BANDAS]))
            if abs(g["nota_treino"] - a) < 1e-9 and abs(g["nota_teste"] - b) < 1e-9:
                print(f"Certo! Acerto no treino {percentagem(a)}; no teste {percentagem(b)}.")
            else:
                print("Ainda não. Pista: nota_teste = acerto(teste[\"rótulo\"], floresta.predict(teste[BANDAS]))")
        elif passo == "2.6":
            if _falta("erros"):
                return
            v, p = exame_mapa_oficial(g["floresta"], g["cheia"])
            certo = {"falso alarme": int(((v == 0) & (p == 1)).sum()), "água perdida": int(((v == 1) & (p == 0)).sum())}
            if isinstance(g["erros"], dict) and all(g["erros"].get(k) == n for k, n in certo.items()):
                print(f"Certo! {numero(certo['falso alarme'])} falsos alarmes e {numero(certo['água perdida'])} píxeis de água perdida.")
            else:
                print("Ainda não. Pista: verdade, previsto = exame_mapa_oficial(floresta, cheia) e depois erros = matriz_de_confusao(verdade, previsto)")
        elif passo == "2.7":
            if _falta("nota_teste_1"):
                return
            uma = RandomForestClassifier(n_estimators=1, random_state=0).fit(g["treino"][BANDAS], g["treino"]["rótulo"])
            b = acerto(g["teste"]["rótulo"], uma.predict(g["teste"][BANDAS]))
            if abs(g["nota_teste_1"] - b) < 1e-9:
                print(f"Certo! Com uma só árvore, o acerto no teste é {percentagem(b)}.")
            else:
                print("Ainda não. Pista: treinem uma floresta com n_estimators=1 e calculem o acerto no teste, como no passo 5.")
        elif passo == "3.2":
            if _falta("rio", "treino", "teste"):
                return
            tr, te = g["treino"], g["teste"]
            if (isinstance(tr, pd.DataFrame) and isinstance(te, pd.DataFrame) and len(tr) and len(te)
                    and tr["ano"].max() == 2022 and te["ano"].min() == 2023 and len(tr) + len(te) == len(g["rio"])):
                print(f"Certo! {numero(len(tr))} manhãs de treino (2017 a 2022) e {numero(len(te))} de teste (2023 a 2026).")
            else:
                print("Ainda não. Pista: treino = rio[rio[\"ano\"] <= 2022] e teste = rio[rio[\"ano\"] >= 2023]")
        elif passo == "3.3":
            if _falta("PISTAS"):
                return
            if isinstance(g["PISTAS"], list) and sorted(g["PISTAS"]) == sorted(PISTAS_COM_MARE):
                print("Certo! Quatro pistas: as três da aula e a altura da maré.")
            elif isinstance(g["PISTAS"], list) and "altura_da_mare_m" not in g["PISTAS"]:
                print("Ainda não: falta a pista da maré, a coluna \"altura_da_mare_m\".")
            else:
                print("Ainda não. Pista: PISTAS = [\"caudal_m3s\", \"chuva_7d_mm\", \"mes\", \"altura_da_mare_m\"]")
        elif passo == "3.4":
            if _falta("floresta"):
                return
            P, f = g["PISTAS"], g["floresta"]
            ref = RandomForestClassifier(n_estimators=100, random_state=0).fit(g["treino"][P], g["treino"]["turva"])
            if (getattr(f, "n_features_in_", None) == len(P) and getattr(f, "n_estimators", None) == 100
                    and (f.predict(g["teste"][P]) == ref.predict(g["teste"][P])).all()):
                print("Certo! A floresta de 100 árvores foi treinada com as quatro pistas, só com o treino.")
            else:
                print("Ainda não. Pista: floresta = RandomForestClassifier(n_estimators=100, random_state=0) e depois floresta.fit(treino[PISTAS], treino[\"turva\"])")
        elif passo == "3.5":
            if _falta("nota_com_mare"):
                return
            P, te = g["PISTAS"], g["teste"]
            certo = acerto(te["turva"], g["floresta"].predict(te[P]))
            sem = [p for p in P if p != "altura_da_mare_m"]
            sem_mare = acerto(te["turva"], RandomForestClassifier(n_estimators=100, random_state=0)
                              .fit(g["treino"][sem], g["treino"]["turva"]).predict(te[sem]))
            if abs(float(g["nota_com_mare"]) - certo) < 1e-9:
                print(f"Certo! Com a maré, a floresta acerta {percentagem(certo)} das manhãs de teste. Sem a maré "
                      f"acertava {percentagem(sem_mare)}, e dizer sempre «turva» acerta {percentagem(te['turva'].mean())}.")
            else:
                print("Ainda não. Pista: nota_com_mare = acerto(teste[\"turva\"], floresta.predict(teste[PISTAS]))")
        elif passo == "3.6":
            if _falta("nota_medio"):
                return
            P, tr, te = g["PISTAS"], g["treino"], g["teste"]

            def nota_do_troco(troco):
                a, b = tr[tr["troco"] == troco], te[te["troco"] == troco]
                m = RandomForestClassifier(n_estimators=100, random_state=0).fit(a[P], a["turva"])
                return acerto(b["turva"], m.predict(b[P])), float(b["turva"].mean())

            medio, sempre = nota_do_troco("troço médio")
            if abs(float(g["nota_medio"]) - medio) < 1e-9:
                foz, _ = nota_do_troco("foz")
                print(f"Certo! No troço médio, longe do mar, a floresta acerta {percentagem(medio)} (dizer sempre «turva»: "
                      f"{percentagem(sempre)}). Na foz, junto ao mar, chega a {percentagem(foz)}: a maré conta mais perto do mar.")
            else:
                print("Ainda não. Pista: treinem a floresta com medio_treino e calculem o acerto em medio_teste, como nos passos 4 e 5.")
        elif passo == "4.2":
            if _falta("dias"):
                return
            d = g["dias"]
            certo = d["caudal_m3s"].shift(-7)
            if "caudal_daqui_a_7_dias" in d and np.allclose(d["caudal_daqui_a_7_dias"].values, certo.values, equal_nan=True):
                print("Certo! A coluna do alvo tem o caudal de 7 dias depois.")
            else:
                print("Ainda não. Pista: dias[\"caudal_daqui_a_7_dias\"] = dias[\"caudal_m3s\"].shift(-7)")
        elif passo == "4.3":
            if _falta("treino", "teste"):
                return
            tr, te = g["treino"], g["teste"]
            if tr["data"].dt.year.max() == 2018 and te["data"].dt.year.min() == 2019 and not tr["caudal_daqui_a_7_dias"].isna().any() and not te["caudal_daqui_a_7_dias"].isna().any():
                print(f"Certo! {numero(len(tr))} dias de treino (até 2018) e {numero(len(te))} de teste (de 2019 em diante).")
            else:
                print("Ainda não. Pista: tirem as linhas vazias (dias = dias.dropna()) e separem: treino até 2018, teste de 2019 em diante.")
        elif passo == "4.4":
            if _falta("linear"):
                return
            P, A = ["caudal_m3s", "chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"], "caudal_daqui_a_7_dias"
            ref = LinearRegression().fit(g["treino"][P], g["treino"][A])
            m = g["linear"]
            if getattr(m, "n_features_in_", None) == 4 and np.allclose(m.predict(g["teste"][P]), ref.predict(g["teste"][P])):
                print("Certo! A regressão linear foi treinada com o treino.")
            else:
                print("Ainda não. Pista: linear = LinearRegression() e depois linear.fit(treino[PISTAS], treino[ALVO])")
        elif passo == "4.5":
            if _falta("erro_teste"):
                return
            P, A = ["caudal_m3s", "chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"], "caudal_daqui_a_7_dias"
            certo = float((g["teste"][A] - g["linear"].predict(g["teste"][P])).abs().mean())
            if abs(float(g["erro_teste"]) - certo) < 0.05:
                print(f"Certo! A 7 dias, o modelo erra em média {numero(certo, 1)} m³/s.")
            else:
                print("Ainda não. Pista: erro_teste = (teste[ALVO] - linear.predict(teste[PISTAS])).abs().mean()")
        elif passo == "4.6":
            if _falta("erro_so_chuva"):
                return
            P, A = ["chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"], "caudal_daqui_a_7_dias"
            m = LinearRegression().fit(g["treino"][P], g["treino"][A])
            certo = float((g["teste"][A] - m.predict(g["teste"][P])).abs().mean())
            if abs(float(g["erro_so_chuva"]) - certo) < 0.05:
                print(f"Certo! Só com a chuva, o erro sobe para {numero(certo, 1)} m³/s.")
            else:
                print("Ainda não. Pista: treinem outra regressão com SO_CHUVA em vez de PISTAS e calculem o erro no teste.")
        else:
            print("Não conheço o passo " + str(passo) + ".")
    except Exception as erro:            # um passo anterior não ficou bem: dizer qual, sem assustar
        print("Ainda não: alguma coisa dos passos anteriores falta ou está errada (" + type(erro).__name__ + "). Voltem ao passo anterior.")
'''
