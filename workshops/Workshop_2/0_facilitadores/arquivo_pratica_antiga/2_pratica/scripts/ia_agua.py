"""ia_agua.py · classificação supervisionada: treinar e testar a IA que encontra água, num só comando.

É o mesmo trabalho do notebook 2_ia_que_encontra_agua.ipynb, mas como um programa normal de Python, configurado
pelo ficheiro 2_pratica/configuracao.json (secção "classificacao"). Num terminal, a partir da pasta 2_pratica
(ou numa célula do Jupyter, com %run em vez de python):

    python scripts/ia_agua.py                               # com a configuração do ficheiro
    python scripts/ia_agua.py --modelo vizinhos             # outro algoritmo: floresta, arvore, vizinhos ou rede
    python scripts/ia_agua.py --pontos os_nossos_pontos.json --arvores 200 --limiar 0.3
    python scripts/ia_agua.py --ensinar 2021                # junta os pontos da equipa de 2021 e testa outra vez
    python scripts/ia_agua.py --terreno                     # junta o terreno (hand, altitude, declive) às pistas
    python scripts/ia_agua.py --caracteristicas nir swir mndwi   # só estas características
    python scripts/ia_agua.py --config outra_config.json    # outro ficheiro de configuração

Guarda em resultados/<data>_ia_agua/: o mapa, as notas (notas.json), o modelo (modelo.joblib) e a configuração usada.
"""
import argparse
import os
import sys

import matplotlib

if "ipykernel" not in sys.modules:                      # num terminal: desenha para ficheiro, sem janela
    matplotlib.use("Agg")                               # (no Jupyter, com %run, os gráficos aparecem no notebook)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import configuracao  # noqa: E402
from ferramentas_ia import (BANDAS, INDICES, TERRENO, RandomForestClassifier, carregar, encontrar, exemplos,  # noqa: E402
                            json, juntar_terreno, mostrar_notas, notas, np, plt, prever)

ANOS = [2014, 2021, 2022, 2024, 2025]
MODELOS = ["floresta", "arvore", "vizinhos", "rede"]


def criar_modelo(c):
    """Os quatro algoritmos de classificação da teoria, com os hiperparâmetros da configuração."""
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier
    if c["modelo"] == "arvore":
        return DecisionTreeClassifier(max_depth=c["profundidade_maxima"], min_samples_leaf=c["folhas_minimas"],
                                      class_weight=c["pesos_das_classes"], random_state=c["semente"])
    if c["modelo"] == "vizinhos":
        return make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5))
    if c["modelo"] == "rede":
        return make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16, 16), max_iter=800, random_state=c["semente"]))
    return RandomForestClassifier(n_estimators=c["n_arvores"], max_depth=c["profundidade_maxima"], min_samples_leaf=c["folhas_minimas"],
                                  class_weight=c["pesos_das_classes"], random_state=c["semente"], n_jobs=-1)


def principal():
    p = argparse.ArgumentParser(description="Treina e testa um modelo que encontra água (Incomáti, 2026).")
    p.add_argument("--config", metavar="FICHEIRO", help="ficheiro de configuração (por omissão, 2_pratica/configuracao.json)")
    p.add_argument("--modelo", choices=MODELOS, help="o algoritmo")
    p.add_argument("--pontos", metavar="FICHEIRO", help="ficheiro .json com {\"agua\": [[linha, coluna], ...], \"nao_agua\": [...]}")
    p.add_argument("--arvores", dest="n_arvores", type=int, metavar="N", help="número de árvores do Random Forest")
    p.add_argument("--profundidade", dest="profundidade_maxima", type=int, metavar="N", help="profundidade máxima das árvores")
    p.add_argument("--limiar", type=float, metavar="P", help="probabilidade a partir da qual se diz água (por omissão 0.5)")
    p.add_argument("--ensinar", dest="ensinar_ano", type=int, choices=ANOS, metavar="ANO", help="juntar os pontos da equipa deste ano (2014, 2021, 2022, 2024 ou 2025) e treinar outra vez")
    p.add_argument("--terreno", action="store_true", default=None, help="usar também o terreno como característica")
    p.add_argument("--caracteristicas", nargs="+", metavar="NOME", help="as características (por exemplo: nir swir mndwi)")
    a = p.parse_args()
    c, saida = configuracao.ler("classificacao", a.config)
    c = configuracao.juntar(c, a)
    configuracao.escolha(c, "modelo", MODELOS)
    configuracao.escolha(c, "caracteristicas", BANDAS + INDICES + TERRENO)
    configuracao.escolha(c, "pesos_das_classes", [None, "balanced"])
    configuracao.escolha(c, "ensinar_ano", [None] + ANOS)
    configuracao.escolha(c, "terreno", [False, True])
    configuracao.numero(c, "n_arvores", 1, 2000)
    configuracao.numero(c, "profundidade_maxima", 1, 100, nulo=True)
    configuracao.numero(c, "folhas_minimas", 1, 1000)
    configuracao.numero(c, "raio_do_ponto", 0, 10)
    configuracao.numero(c, "limiar", 0, 1, inteiro=False)
    configuracao.numero(c, "semente", 0, nulo=True)

    with open(encontrar("exemplos_da_equipa.json"), encoding="utf-8") as ficheiro:
        equipa = json.load(ficheiro)
    if c["pontos"]:
        if not os.path.exists(c["pontos"]):
            sys.exit(f"Não encontrei o ficheiro de pontos {c['pontos']} (o caminho conta a partir da pasta onde corre o script).")
        with open(c["pontos"], encoding="utf-8") as ficheiro:
            pontos = json.load(ficheiro)
        if not {"agua", "nao_agua"} <= set(pontos):
            sys.exit('O ficheiro de pontos tem de ter as duas listas: "agua" e "nao_agua".')
    else:
        pontos = equipa["2026"]
    extra = dict(np.load(encontrar("camadas_extra.npz")))
    cheia = carregar("incomati_2026_cheia.npz")
    car = list(c["caracteristicas"]) + [t for t in TERRENO if c["terreno"] and t not in c["caracteristicas"]]
    usa_terreno = any(t in car for t in TERRENO)
    if usa_terreno:
        juntar_terreno(cheia, extra)

    X, y = exemplos(cheia, pontos["agua"], pontos["nao_agua"], car, raio=c["raio_do_ponto"])
    if c["ensinar_ano"]:
        img = carregar(f"incomati_{c['ensinar_ano']}_chuvosa.npz")
        if usa_terreno:
            juntar_terreno(img, extra)
        xa, ya = exemplos(img, equipa[str(c["ensinar_ano"])]["agua"], equipa[str(c["ensinar_ano"])]["nao_agua"], car,
                          raio=c["raio_do_ponto"])
        X, y = np.concatenate([X, xa]), np.concatenate([y, ya])
    modelo = criar_modelo(c).fit(X, y)
    limiar = c["limiar"]
    print(f"Modelo: {c['modelo']} | treino: {len(y)} píxeis | limiar {limiar} | características: {', '.join(car)}")
    print(f"Acerto nos exemplos de treino: {100 * (modelo.predict(X) == y).mean():.1f}% (não conta: o modelo já os viu)\n")

    prob = prever(modelo, cheia, car)
    teste = (extra["ems_2026"] >= 0) & ~cheia["nuvem"]
    verdade = extra["ems_2026"][teste]
    nota_exame = notas(verdade, (prob[teste] > limiar).astype(int), prob[teste])
    mostrar_notas("Modelo (exame EMS 2026)", nota_exame)
    mostrar_notas("Regra MNDWI > 0", notas(verdade, (cheia["mndwi"][teste] > 0).astype(int)))
    print()
    rios = {}
    for ano in ANOS:
        img = carregar(f"incomati_{ano}_chuvosa.npz")
        if usa_terreno:
            juntar_terreno(img, extra)
        pa = prever(modelo, img, car)
        rio, terra = extra["verif_agua"] & ~img["nuvem"], extra["verif_terra"] & ~img["nuvem"]
        rios[ano] = 100 * (pa[rio] > limiar).mean()
        print(f"{ano} ({img['satelite']}): modelo encontra {rios[ano]:5.1f}% do rio certo"
              f" | regra MNDWI {100 * (img['mndwi'][rio] > 0).mean():5.1f}%"
              f" | falsos alarmes em terra alta {100 * (pa[terra] > limiar).mean():4.1f}%")

    pasta = configuracao.pasta_de_resultados("ia_agua", saida)
    plt.figure(figsize=(7, 10))
    plt.imshow((prob > limiar) & cheia["zona"] & ~cheia["nuvem"], cmap="Blues")
    plt.title(f"Água segundo o modelo ({c['modelo']}) · 24 jan 2026")
    plt.axis("off")
    mapa = os.path.join(pasta, "mapa_ia_2026.png")
    plt.savefig(mapa, dpi=120, bbox_inches="tight")
    print("\nMapa guardado em", os.path.relpath(mapa))
    configuracao.guardar(pasta, {"exame_ems_2026": nota_exame, "rio_encontrado_por_ano": rios, "pixeis_treino": int(len(y))},
                         c, modelo, saida)


if __name__ == "__main__":
    principal()
