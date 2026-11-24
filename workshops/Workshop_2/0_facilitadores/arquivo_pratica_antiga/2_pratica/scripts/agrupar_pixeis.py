"""agrupar_pixeis.py · aprendizagem não supervisionada: o K-means junta os píxeis parecidos em K grupos.

É o mesmo trabalho da Parte E do notebook 3_sem_rotulos_e_numeros.ipynb, configurado pelo ficheiro
2_pratica/configuracao.json (secção "agrupamento"). A partir da pasta 2_pratica:

    python scripts/agrupar_pixeis.py            # K da configuração
    python scripts/agrupar_pixeis.py --k 6
    python scripts/agrupar_pixeis.py --k 3 --caracteristicas nir swir

Não usa nenhum rótulo para aprender. No fim, chama "água" aos grupos com MNDWI médio maior do que 0 (a regra do
Workshop 1), compara com o exame EMS e guarda em resultados/<data>_agrupar_pixeis/ o mapa, as notas e o modelo.
"""
import argparse
import os
import sys

import matplotlib

if "ipykernel" not in sys.modules:                      # num terminal: desenha para ficheiro, sem janela
    matplotlib.use("Agg")                               # (no Jupyter, com %run, os gráficos aparecem no notebook)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import configuracao  # noqa: E402
from ferramentas_ia import BANDAS, INDICES, carregar, encontrar, mostrar_notas, notas, np, plt, tabela  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402


def principal():
    p = argparse.ArgumentParser(description="Agrupa os píxeis da imagem da cheia com o K-means, sem rótulos.")
    p.add_argument("--config", metavar="FICHEIRO", help="ficheiro de configuração (por omissão, 2_pratica/configuracao.json)")
    p.add_argument("--k", dest="k_grupos", type=int, choices=range(2, 11), metavar="K", help="número de grupos, de 2 a 10")
    p.add_argument("--caracteristicas", nargs="+", metavar="NOME", help="as características (por exemplo: nir swir mndwi)")
    a = p.parse_args()
    c, saida = configuracao.ler("agrupamento", a.config)
    c = configuracao.juntar(c, a)
    configuracao.numero(c, "k_grupos", 2, 10)
    configuracao.numero(c, "inicializacoes", 1, 50)
    configuracao.numero(c, "semente", 0, nulo=True)
    configuracao.escolha(c, "caracteristicas", BANDAS + INDICES)

    cheia = carregar("incomati_2026_cheia.npz")
    extra = dict(np.load(encontrar("camadas_extra.npz")))
    car = list(c["caracteristicas"])
    X = tabela(cheia, car)
    valido = (cheia["zona"] & ~cheia["nuvem"]).ravel()
    k = c["k_grupos"]
    agrupador = make_pipeline(StandardScaler(), KMeans(n_clusters=k, n_init=c["inicializacoes"], random_state=c["semente"]))
    agrupador.fit(X[valido])
    grupos = agrupador.predict(X).reshape(cheia["verde"].shape)

    g_validos = grupos.ravel()[valido]
    mndwi_validos = cheia["mndwi"].ravel()[valido]      # o MNDWI só serve para dar nome aos grupos, não para os formar
    agua, por_grupo = [], {}
    for g in range(k):
        mndwi = float(np.nanmean(mndwi_validos[g_validos == g]))
        por_grupo[g] = {"percentagem": float(100 * (g_validos == g).mean()), "mndwi_medio": mndwi}
        print(f"Grupo {g}: {por_grupo[g]['percentagem']:4.1f}% dos píxeis | MNDWI médio {mndwi:+.2f}")
        if mndwi > 0:
            agua.append(g)
    teste = (extra["ems_2026"] >= 0) & ~cheia["nuvem"]
    verdade = extra["ems_2026"][teste]
    print()
    nota_exame = notas(verdade, np.isin(grupos[teste], agua).astype(int))
    mostrar_notas(f"K-means (K = {k}), água = {agua}", nota_exame)
    mostrar_notas("Regra MNDWI > 0", notas(verdade, (cheia["mndwi"][teste] > 0).astype(int)))

    pasta = configuracao.pasta_de_resultados("agrupar_pixeis", saida)
    plt.figure(figsize=(7, 10))
    plt.imshow(np.where(cheia["zona"] & ~cheia["nuvem"], grupos, np.nan), cmap=ListedColormap(plt.get_cmap("tab10").colors[:k]),
               vmin=-0.5, vmax=k - 0.5, interpolation="nearest")
    plt.colorbar(ticks=range(k), shrink=0.6, label="número do grupo")
    plt.title(f"Os {k} grupos do K-means · 24 jan 2026")
    plt.axis("off")
    mapa = os.path.join(pasta, "mapa_grupos_kmeans.png")
    plt.savefig(mapa, dpi=120, bbox_inches="tight")
    print("\nMapa guardado em", os.path.relpath(mapa))
    configuracao.guardar(pasta, {"exame_ems_2026": nota_exame, "grupos_de_agua": agua, "grupos": por_grupo}, c, agrupador, saida)


if __name__ == "__main__":
    principal()
