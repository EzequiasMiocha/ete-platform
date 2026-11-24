"""Ferramentas da aula (as mesmas da Célula 0 dos notebooks)."""
import os                                   # os: encontrar ficheiros no computador
import json                                 # json: ler a lista de pontos da equipa
import numpy as np                          # numpy: contas com tabelas de números (uma imagem é uma tabela)
import matplotlib.pyplot as plt             # matplotlib: desenhar mapas e gráficos
from sklearn.ensemble import RandomForestClassifier   # scikit-learn: o modelo Random Forest
from sklearn import metrics                 # scikit-learn: as notas do modelo (acerto, IoU, F1, Kappa, ROC-AUC)

BANDAS = ["azul", "verde", "vermelho", "nir", "swir"]
INDICES = ["ndwi", "mndwi", "ndvi"]
TERRENO = ["hand", "altitude", "declive"]
RAIO = 2                                    # cada ponto marcado vale um quadrado de 5 x 5 píxeis (150 m x 150 m)


def encontrar(nome):
    """Procura um ficheiro de dados na pasta dados/ (ao lado do notebook, ou uma pasta acima)."""
    for pasta in ["dados", os.path.join("..", "dados"), "."]:
        caminho = os.path.join(pasta, nome)
        if os.path.exists(caminho):
            return caminho
    raise FileNotFoundError(f"Não encontrei {nome}. Abra o Jupyter na pasta Workshop_2/2_pratica: "
                            "os dados estão em 2_pratica/dados.")


def carregar(nome):
    """Abre uma imagem (.npz): as 5 bandas em reflectância (0 a 1) e os índices NDWI, MNDWI e NDVI."""
    z = np.load(encontrar(nome))
    img = {banda: z[banda] / 10000 for banda in BANDAS}
    with np.errstate(divide="ignore", invalid="ignore"):
        img["ndwi"] = (img["verde"] - img["nir"]) / (img["verde"] + img["nir"])
        img["mndwi"] = (img["verde"] - img["swir"]) / (img["verde"] + img["swir"])
        img["ndvi"] = (img["nir"] - img["vermelho"]) / (img["nir"] + img["vermelho"])
    img["nuvem"] = z["nuvem"]                   # True onde há nuvem, sombra ou falta de dados
    img["zona"] = z["zona"]                     # True dentro do distrito de Marracuene, fora do mar
    for chave in ["data", "satelite", "epoca"]:
        img[chave] = str(z[chave])
    img["caudal_m3s"] = float(z["caudal_m3s"])
    return img


def juntar_terreno(img, extra):
    """Acrescenta as camadas de terreno (iguais em todas as datas) às características da imagem."""
    for chave in TERRENO:
        img[chave] = extra[chave]
    return img


def cor_natural(img, brilho=0.15):
    """Junta vermelho, verde e azul numa imagem a cores."""
    return np.clip(np.dstack([img["vermelho"], img["verde"], img["azul"]]) / brilho, 0, 1)


def ver_imagem(img, titulo="", agua=(), nao_agua=(), grelha=100):
    """Mostra a imagem a cores com linhas e colunas numeradas, e os pontos marcados (círculo = água, quadrado = não água)."""
    plt.figure(figsize=(9, 12))
    plt.imshow(cor_natural(img))
    for linha, coluna in agua:
        plt.plot(coluna, linha, "o", ms=9, mfc="cyan", mec="black")
    for linha, coluna in nao_agua:
        plt.plot(coluna, linha, "s", ms=9, mfc="orange", mec="black")
    plt.xticks(range(0, img["verde"].shape[1], grelha))
    plt.yticks(range(0, img["verde"].shape[0], grelha))
    plt.grid(alpha=0.5, color="white")
    plt.xlabel("coluna")
    plt.ylabel("linha")
    plt.title(titulo)
    plt.show()


def ver_zona(img, linha, coluna, tamanho=60):
    """Lupa: mostra uma zona pequena à volta de (linha, coluna), com grelha fina, para escolher pontos certos."""
    l0, c0 = max(linha - tamanho, 0), max(coluna - tamanho, 0)
    recorte = cor_natural(img)[l0:linha + tamanho, c0:coluna + tamanho]
    plt.figure(figsize=(7, 7))
    plt.imshow(recorte, extent=(c0 - 0.5, c0 + recorte.shape[1] - 0.5, l0 + recorte.shape[0] - 0.5, l0 - 0.5))
    plt.plot(coluna, linha, "+", ms=20, color="red")
    plt.grid(alpha=0.5, color="white")
    plt.xlabel("coluna")
    plt.ylabel("linha")
    plt.title(f"Lupa à volta da linha {linha}, coluna {coluna}")
    plt.show()


def tabela(img, caracteristicas):
    """Uma linha por píxel e uma coluna por característica: é assim que o modelo lê a imagem."""
    pilha = np.stack([img[c] for c in caracteristicas], axis=-1)
    return np.nan_to_num(pilha.reshape(-1, len(caracteristicas)))


def exemplos(img, agua, nao_agua, caracteristicas, raio=RAIO, grupos=False):
    """Transforma os pontos marcados em exemplos: X (as características) e y (1 = água, 0 = não água).
    raio: cada ponto vale um quadrado de (2 x raio + 1)² píxeis. grupos=True devolve também o número do ponto
    de cada píxel (para a validação cruzada por pontos, no nível avançado)."""
    pilha = np.nan_to_num(np.stack([img[c] for c in caracteristicas], axis=-1))
    X, y, g, nas_nuvens = [], [], [], 0
    for classe, pontos in ((1, agua), (0, nao_agua)):
        for linha, coluna in pontos:
            janela = (slice(max(linha - raio, 0), linha + raio + 1), slice(max(coluna - raio, 0), coluna + raio + 1))
            limpo = ~img["nuvem"][janela]
            if not limpo.any():
                nas_nuvens += 1
                continue
            X.append(pilha[janela][limpo])
            y.append(np.full(limpo.sum(), classe))
            g.append(np.full(limpo.sum(), len(g)))
    if nas_nuvens:
        print(f"Atenção: {nas_nuvens} ponto(s) caíram em nuvens ou fora da imagem e foram ignorados.")
    if grupos:
        return np.concatenate(X), np.concatenate(y), np.concatenate(g)
    return np.concatenate(X), np.concatenate(y)


def prever(modelo, img, caracteristicas):
    """A probabilidade de ser água (0 a 1), para cada píxel da imagem."""
    probabilidade = modelo.predict_proba(tabela(img, caracteristicas))[:, 1]
    return probabilidade.reshape(img["verde"].shape)


def notas(verdade, previsto, probabilidade=None):
    """As notas do modelo comparado com a verdade (1 = água, 0 = não água)."""
    r = {"acerto": metrics.accuracy_score(verdade, previsto),
         "IoU": metrics.jaccard_score(verdade, previsto),
         "F1": metrics.f1_score(verdade, previsto),
         "Kappa": metrics.cohen_kappa_score(verdade, previsto)}
    if probabilidade is not None:
        r["ROC-AUC"] = metrics.roc_auc_score(verdade, probabilidade)
    return r


def mostrar_notas(nome, r):
    print(f"{nome:28s}", "  ".join(f"{k} {v:.3f}" for k, v in r.items()))


def contar_erros(verdade, previsto):
    """A matriz de confusão em palavras: o que acertou e o que errou."""
    agua_certa = int(((verdade == 1) & (previsto == 1)).sum())
    terra_certa = int(((verdade == 0) & (previsto == 0)).sum())
    falso_alarme = int(((verdade == 0) & (previsto == 1)).sum())
    agua_perdida = int(((verdade == 1) & (previsto == 0)).sum())
    print(f"Água que o modelo encontrou (certo):      {agua_certa:8d} píxeis")
    print(f"Terra que o modelo disse terra (certo):   {terra_certa:8d} píxeis")
    print(f"Falsos alarmes (terra que disse água):    {falso_alarme:8d} píxeis")
    print(f"Água perdida (água que disse terra):      {agua_perdida:8d} píxeis")
    return agua_certa, terra_certa, falso_alarme, agua_perdida
