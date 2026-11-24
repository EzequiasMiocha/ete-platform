"""Os 10 exercícios por ano (pasta 3_exercicios) e as soluções para os facilitadores.

Todos os anos têm a mesma estrutura (a do notebook guiado); mudam os dados, as respostas
e o desafio final. Cada ano gera:
  3_exercicios/ano_AAAA/exercicio_AAAA.ipynb     versão do estudante, com ... para preencher
  3_exercicios/ano_AAAA/ENUNCIADO.md             o problema em texto (para imprimir e pensar)
  0_facilitadores/solucoes/solucao_AAAA.ipynb    a mesma, preenchida e com respostas-modelo
"""

import numpy as np

from .comum import AULA, ERROS_COMUNS, FERRAMENTAS, HA_CAMPO, LEGENDA, code, escrever, fmt, md, verificador

MESES = ["janeiro", "fevereiro", "março", "abril", "maio", "junho", "julho", "agosto", "setembro",
         "outubro", "novembro", "dezembro"]


def data_pt(iso: str) -> str:
    a, m, d = iso.split("-")
    return f"{int(d)} de {MESES[int(m) - 1]} de {a}"


# Texto próprio de cada ano. {chaves} vêm das respostas de referência (respostas_de_referencia.json).
ANOS = {
    2014: dict(
        estrelas="★", titulo="A cheia de março de 2014",
        contexto=("Em março de 2014 o Incomáti subiu até {pico} m³/s ({dpico}). Nessa altura o Sentinel-2 "
                  "ainda não existia: só havia o **Landsat 8**, lançado em 2013. A imagem da estação chuvosa "
                  "é de {dchuv}, {dias} dias depois do pico."),
        desafio=("Calcule a água nova também com o **NDWI** (troque `INDICE_FINAL` no mapa final). Qual dos dois "
                 "índices encontra mais água nova? Olhe para a imagem em cor natural: a água da cheia é limpa "
                 "ou barrenta? Porque é que isso pode enganar o NDWI?"),
        resposta=("O MNDWI encontra cerca de {nova} ha e o NDWI cerca de {nova_ndwi} ha. A água da cheia é "
                  "barrenta (sedimentos) e há água pouco funda entre a vegetação: os dois reflectem bastante "
                  "NIR, por isso o NDWI fica negativo nesses píxeis. O SWIR continua baixo em quase toda a "
                  "água, e o MNDWI apanha-os. Para cheias barrentas, o MNDWI é mais fiável (Xu, 2006)."),
    ),
    2016: dict(
        estrelas="★★", titulo="O ano da seca (El Niño 2015-2016)",
        contexto=("Em 2015-2016 o sul de Moçambique teve uma das piores secas das últimas décadas, ligada ao "
                  "El Niño. O caudal máximo do ano foi só {pico} m³/s e, no dia da imagem da estação chuvosa "
                  "({dchuv}), o rio levava {qchuv} m³/s. Satélite: **Landsat 8**."),
        desafio=("Encontrou **menos** água na estação chuvosa do que na seca anterior. Como é possível? "
                 "Dê duas razões: pense na chuva desse ano e olhe para as nuvens."),
        resposta=("1) A estação chuvosa falhou: o rio e as lagoas encolheram em vez de crescer "
                  "(de {seca} ha para {chuv} ha). 2) Cerca de {nuvem}% da zona tem nuvens, que tapam parte "
                  "do rio e das lagoas. A \"água nova\" (cerca de {nova} ha) é só ruído do método."),
    ),
    2017: dict(
        estrelas="★", titulo="Uma estação chuvosa normal",
        contexto=("Em 2017 o pico do Incomáti foi de {pico} m³/s ({dpico}), **abaixo** do limite de alerta "
                  "laranja (376 m³/s). A imagem da estação chuvosa é de {dchuv} ({qchuv} m³/s). "
                  "Satélite: **Landsat 8**."),
        desafio=("O caudal nunca passou o limite laranja. Esperava encontrar uma cheia? O que diz o seu mapa? "
                 "Que parte da \"água nova\" pode ser erro? Procure-a no mapa e compare com as nuvens."),
        resposta=("Não houve cheia: só cerca de {nova} ha de água nova, espalhados em manchas pequenas. "
                  "Parte é ruído: sombras de nuvens ({nuvem}% de nuvens) parecem água escura, e pequenas "
                  "lagoas enchem com a chuva local."),
    ),
    2019: dict(
        estrelas="★", titulo="Um ano sem cheia: o nosso \"controlo\"",
        contexto=("Em 2019 o pico foi só {pico} m³/s ({dpico}). A imagem de {dchuv} ({qchuv} m³/s) está quase "
                  "sem nuvens ({nuvem}%). Um ano assim serve de **controlo**: mostra quanta \"água nova\" o "
                  "método encontra quando **não** há cheia. Satélite: **Sentinel-2** (passa a 30 m nesta aula)."),
        desafio=("Num ano sem cheia, o método ainda encontra alguma \"água nova\". Esse valor é o **ruído** do "
                 "método. Se noutro ano encontrar 150 ha de água nova, pode dizer que houve cheia? E 3 000 ha?"),
        resposta=("Cerca de {nova} ha é o nível de ruído: lagoas e campos que enchem com a chuva local, e "
                  "pequenas diferenças entre as duas datas. Com 150 ha não se pode afirmar que houve cheia; "
                  "com 3 000 ha sim (é cerca de 20 vezes o ruído, como em 2014)."),
    ),
    2020: dict(
        estrelas="★★", titulo="A cheia pequena de fevereiro de 2020",
        contexto=("Em fevereiro de 2020 o Incomáti chegou a {pico} m³/s ({dpico}), acima do limite laranja "
                  "(376 m³/s) mas abaixo do vermelho (970 m³/s). A imagem é de {dchuv}, com o rio a "
                  "{qchuv} m³/s e {nuvem}% de nuvens. Satélite: **Sentinel-2**."),
        desafio=("O caudal passou o limite laranja, mas o mapa mostra pouca água nova. O rio transbordou para "
                 "a planície? Compare com o \"controlo\" de 2019 (cerca de 130 ha de ruído)."),
        resposta=("Encontra cerca de {nova} ha, pouco acima do ruído de 2019. A água ficou quase toda no leito, "
                  "com pequenas extravasões. A planície de Marracuene alaga a sério quando o caudal passa o "
                  "limite vermelho (970 m³/s), como em 2023 e 2026."),
    ),
    2021: dict(
        estrelas="★★★", titulo="A cheia escondida pelas nuvens",
        contexto=("No fim de janeiro de 2021, depois das chuvas do ciclone tropical Eloise na região, o "
                  "Incomáti chegou a {pico} m³/s ({dpico}). A imagem mais próxima é de {dchuv} "
                  "({qchuv} m³/s), mas tem **{nuvem}%** da zona coberta de nuvens. Satélite: **Sentinel-2**."),
        desafio=("1) A água nova que encontrou é a resposta certa, um mínimo ou um máximo? Porquê? "
                 "2) Calcule também com o NDWI: dá muito menos. Use a célula \"investigar um píxel\": "
                 "compare o verde e o NIR do píxel do rio na estação chuvosa. Porque é que o NDWI falha aqui? "
                 "3) Que satélite usaria para mapear esta cheia?"),
        resposta=("1) É um **mínimo**: {nuvem}% da zona não se vê, e a cheia pode estar debaixo das nuvens. "
                  "2) A água da cheia é tão barrenta que reflecte mais NIR do que verde (no píxel do rio: verde "
                  "{p_verde}, NIR {p_nir}): o NDWI fica negativo e diz \"não é água\". O MNDWI usa o SWIR, que "
                  "continua baixo ({p_swir}), e funciona. 3) O radar Sentinel-1, que vê através das nuvens."),
    ),
    2022: dict(
        estrelas="★★", titulo="Uma imagem no dia do pico",
        contexto=("Em janeiro de 2022 o pico foi de {pico} m³/s a {dpico}, e há uma imagem Sentinel-2 desse "
                  "**mesmo dia**, com {nuvem}% de nuvens na zona."),
        desafio=("A imagem é do próprio dia do pico, mas o MNDWI encontra **menos** água do que na seca! "
                 "Investigue: 1) há nuvens sobre o rio? 2) Na célula \"investigar um píxel\", compare o verde e "
                 "o SWIR do píxel do rio nas duas datas. 3) Repita o mapa com o NDWI. O que conclui?"),
        resposta=("1) Sim: nuvens e sombras tapam parte do rio. 2) Na estação chuvosa a água ficou muito escura "
                  "(verde {p_verde}, SWIR {p_swir}): é um efeito da correcção atmosférica. Com o verde tão baixo, "
                  "o MNDWI fica perto de 0 e falha em parte do rio, enquanto o NDWI (verde contra NIR {p_nir}) "
                  "ainda funciona. 3) Com 440 m³/s (pouco acima do laranja) não houve cheia na planície: "
                  "a água nova é cerca de {nova} ha."),
    ),
    2023: dict(
        estrelas="★", titulo="A grande cheia de fevereiro de 2023",
        contexto=("Em fevereiro de 2023, depois de chuvas fortes no sul de Moçambique e nos países vizinhos, o "
                  "Incomáti chegou a {pico} m³/s ({dpico}), a segunda maior cheia dos últimos 20 anos. "
                  "A imagem Sentinel-2 de {dchuv} está quase sem nuvens ({nuvem}%)."),
        desafio=("Dez dias depois do pico, o caudal já tinha descido para {qchuv} m³/s, mas a planície "
                 "continuava alagada. Porquê? Quantos km² de água nova? Quantos campos de futebol?"),
        resposta=("A planície é baixa e plana: a água que sai do rio fica retida e só sai devagar (volta ao rio, "
                  "infiltra-se e evapora), por isso o mapa mostra a cheia muitos dias depois do pico. "
                  "Água nova: cerca de {nova} ha = {nova_km2} km² = cerca de {campos} campos de futebol."),
    ),
    2024: dict(
        estrelas="★★★", titulo="O mistério dos índices",
        contexto=("Em janeiro de 2024 o pico foi de {pico} m³/s ({dpico}), sem cheia. A imagem Sentinel-2 de "
                  "{dchuv} ({qchuv} m³/s) tem {nuvem}% de nuvens. Este ano esconde uma surpresa."),
        desafio=("O MNDWI diz que o rio quase desapareceu (de cerca de {seca} ha para {chuv} ha). "
                 "1) Olhe para a imagem em cor natural: o rio desapareceu mesmo? 2) Faça o mapa também com o NDWI. "
                 "3) Na célula \"investigar um píxel\", veja o verde, o NIR e o SWIR do píxel do rio nas duas "
                 "datas. O que está estranho?"),
        resposta=("1) Não: o rio está lá, muito escuro. 2) O NDWI encontra o rio. 3) A correcção atmosférica "
                  "deixou a água quase sem luz: verde {p_verde}, NIR {p_nir}, SWIR {p_swir}. Como o SWIR ficou "
                  "maior do que o verde, o MNDWI fica negativo; o NDWI (verde maior do que NIR) ainda diz "
                  "\"água\". Mas o NDWI dá 1,00, o máximo possível, só porque o NIR ficou a zero: também é um "
                  "sinal de que a imagem tem um problema. Lição: nunca confiar num número sem olhar para a "
                  "imagem, e comparar dois índices."),
    ),
    2025: dict(
        estrelas="★★", titulo="A cheia que fugiu",
        contexto=("Em janeiro de 2025 o Incomáti chegou a {pico} m³/s ({dpico}), acima do limite laranja. "
                  "A imagem Sentinel-2 mais limpa é de {dchuv} ({qchuv} m³/s), com {nuvem}% de nuvens."),
        desafio=("O pico passou o limite laranja, mas quase não há água nova. 1) Quantos dias passaram entre o "
                 "pico e a imagem? 2) Que caudal tinha o rio no dia da imagem? 3) O Sentinel-2 passa sobre "
                 "Marracuene a cada 2 dias, mais ou menos. Porque não usámos uma imagem mais perto do pico?"),
        resposta=("1) {dias} dias. 2) {qchuv} m³/s, já abaixo do limite laranja: a cheia tinha passado. "
                  "3) As passagens mais perto do pico (14, 17 e 19 de janeiro) tinham entre 37% e 93% da "
                  "planície com nuvens. Uma imagem óptica só vê a cheia se o céu estiver limpo no dia certo."),
    ),
}


def rio_para_investigar(ano: int):
    """Um píxel do rio, visto nas duas datas, que mostra bem o que se passa nesse ano."""
    pasta = AULA / f"3_exercicios/ano_{ano}/dados"
    s, w = np.load(pasta / f"incomati_{ano}_seca.npz"), np.load(pasta / f"incomati_{ano}_chuvosa.npz")
    bs = {k: s[k] / 10000 for k in ("verde", "nir", "swir")}
    bw = {k: w[k] / 10000 for k in ("verde", "nir", "swir")}
    with np.errstate(divide="ignore", invalid="ignore"):
        md0 = (bs["verde"] - bs["swir"]) / (bs["verde"] + bs["swir"])
        md1 = (bw["verde"] - bw["swir"]) / (bw["verde"] + bw["swir"])
        nd1 = (bw["verde"] - bw["nir"]) / (bw["verde"] + bw["nir"])
    from scipy import ndimage
    rio = ndimage.binary_erosion((md0 > 0.3) & s["zona"] & ~s["nuvem"] & ~w["nuvem"], iterations=1)
    if ano == 2021:
        caso = rio & (md1 > 0.1) & (nd1 < 0)                      # o NDWI falha e o MNDWI não
    elif ano in (2022, 2024):
        caso = rio & (nd1 > 0.2) & (md1 < 0) & (bw["verde"] > 0.003)  # o MNDWI falha e o NDWI não
    else:
        caso = rio & (md1 > 0.3)                                  # rio limpo nas duas datas
    if not caso.any():
        caso = rio
    # o píxel mais típico do caso: o mais perto da mediana do verde, do NIR e do SWIR
    mediana = {k: np.median(bw[k][caso]) for k in ("verde", "nir", "swir")}
    distancia = sum((bw[k] - mediana[k]) ** 2 for k in mediana)
    lin, col = np.unravel_index(np.argmin(np.where(caso, distancia, np.inf)), caso.shape)
    valores = {k: round(float(bw[k][lin, col]), 3) for k in ("verde", "nir", "swir")}
    return int(lin), int(col), valores


def campos(r, ano, lin, col, valores):
    from datetime import date
    dias = (date.fromisoformat(r["data_chuvosa"]) - date.fromisoformat(r["data_pico"])).days
    return dict(pico=fmt(r["caudal_pico"]), dpico=data_pt(r["data_pico"]), dchuv=data_pt(r["data_chuvosa"]),
                dseca=data_pt(r["data_seca"]), qchuv=fmt(r["caudal_chuvosa"]), qseca=fmt(r["caudal_seca"], 1),
                nuvem=fmt(r["nuvem_chuvosa_pct"]), seca=fmt(r["agua_seca_ha"]), chuv=fmt(r["agua_chuvosa_ha"]),
                nova=fmt(r["agua_nova_ha"]), nova_ndwi=fmt(r["ndwi_agua_nova_ha"]),
                nova_km2=fmt(r["agua_nova_ha"] / 100, 1), campos=fmt(r["agua_nova_ha"] / HA_CAMPO),
                dias=dias, p_verde=fmt(valores["verde"], 3), p_nir=fmt(valores["nir"], 3), p_swir=fmt(valores["swir"], 3))


def respostas_codificadas(r):
    def margem(v):
        return max(5.0, 0.01 * v)
    return {
        "area_pixel_ha": [0.09, 0.0005, "Um píxel tem 30 m x 30 m = 900 m². Divida os m² por 10 000."],
        "nuvem_pct": [r["nuvem_chuvosa_pct"], 0.6,
                      "Use 100 * chuvosa[\"nuvem\"][zona].mean(): a média de True/False é a fracção de True."],
        "agua_seca_ha": [r["agua_seca_ha"], margem(r["agua_seca_ha"]),
                         "Conte os True de agua_seca com .sum() e multiplique por area_pixel_ha (e use LIMIAR = 0)."],
        "agua_chuvosa_ha": [r["agua_chuvosa_ha"], margem(r["agua_chuvosa_ha"]),
                            "Conte os True de agua_chuvosa com .sum() e multiplique por area_pixel_ha (LIMIAR = 0)."],
        "agua_nova_ha": [r["agua_nova_ha"], margem(r["agua_nova_ha"]),
                         "Conte os True de nova com .sum() e multiplique por area_pixel_ha (LIMIAR = 0)."],
    }


def resposta_cell(sol: bool, modelo: str):
    if sol:
        return md(f"**Resposta-modelo (facilitadores):** {modelo}")
    return md("*✍️ A vossa resposta (duplo clique para escrever):*")


def celulas(ano: int, r: dict, sol: bool):
    info = ANOS[ano]
    lin, col, valores = rio_para_investigar(ano)
    k = campos(r, ano, lin, col, valores)
    seca_f, chuv_f = f"incomati_{ano}_seca.npz", f"incomati_{ano}_chuvosa.npz"
    sat = r["satelite"]

    def v(solucao, vazio="..."):
        return solucao if sol else vazio

    c = [md(f"""
# Exercício {ano} · {info['titulo']} {info['estrelas']}
{"**VERSÃO DOS FACILITADORES (com soluções)**" if sol else ""}

{info['contexto'].format(**k)}

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | {k['dseca']} | {k['dchuv']} |
| Caudal nesse dia | {k['qseca']} m³/s | {k['qchuv']} m³/s |
| Satélite | {sat} | {sat} |

Pico do caudal neste ano hidrológico: **{k['pico']} m³/s a {k['dpico']}** (modelo GloFAS).
Limites de alerta do ETE: laranja 376 m³/s, vermelho 970 m³/s.

**A vossa missão:** descobrir quanta água nova apareceu na planície de Marracuene nesta estação chuvosa,
fazer o mapa e explicar o resultado. Os passos são os mesmos do notebook guiado de 2026.

**Dificuldade:** {info['estrelas']} (★ directo, ★★ precisa de interpretação, ★★★ tem uma armadilha para investigar)

{LEGENDA}
"""),
         md("## Passo 0 · Ferramentas ▶️\n\nCorra as duas células seguintes sem mudar nada."),
         code(FERRAMENTAS),
         code(verificador(respostas_codificadas(r))),
         md(f"""
## Passo 1 · Pensar antes de programar ✍️

1. Que satélite tirou estas imagens? Nesta aula, cada píxel tem 30 m × 30 m. Quantos hectares tem um píxel?
2. **Previsão:** olhe para o caudal no dia da imagem e para o pico do ano. Espera ver uma cheia na planície?
   Muita ou pouca água nova? Escreva a sua previsão **antes** de calcular.
"""),
         resposta_cell(sol, f"{sat}. Um píxel = 30 x 30 = 900 m² = 0,09 ha. Previsão: comparar o caudal no dia "
                            f"da imagem ({k['qchuv']} m³/s) e o pico ({k['pico']} m³/s) com os limites 376 e 970 m³/s."),
         code(f"""
# ✏️ Quantos hectares tem um píxel de 30 m x 30 m? (1 ha = 10 000 m²)
area_pixel_ha = {v("30 * 30 / 10000")}
verificar("area_pixel_ha", area_pixel_ha)
"""),
         md("## Passo 2 · Abrir e ver as imagens ▶️"),
         code(f"""
seca = carregar("{seca_f}")
chuvosa = carregar("{chuv_f}")
zona = seca["zona"]                   # distrito de Marracuene, sem o mar

for img in [seca, chuvosa]:
    print(f"{{img['epoca']:8s}} {{img['data']}}  {{img['satelite']}}  caudal {{img['caudal_m3s']:.0f}} m³/s")
print("Tamanho:", seca["verde"].shape, "píxeis")
"""),
         code("""
fig, eixos = plt.subplots(1, 2, figsize=(12, 9))
for eixo, img in zip(eixos, [seca, chuvosa]):
    eixo.imshow(cor_natural(img))
    eixo.contour(zona, levels=[0.5], colors="yellow", linewidths=1)
    eixo.set_title(f"{img['epoca'].upper()} · {img['data']} · {img['caudal_m3s']:.0f} m³/s")
    eixo.axis("off")
plt.tight_layout()
plt.show()
"""),
         md("✍️ **Pergunta:** o que mudou entre as duas imagens? Há nuvens? De que cor é a água?"),
         resposta_cell(sol, "Comparar a largura do rio, as manchas de água na planície, a cor da água "
                            "(castanha = sedimentos) e as nuvens (manchas brancas) e as suas sombras."),
         md("""
### ✏️ Quanta zona está tapada por nuvens?

`chuvosa["nuvem"][zona]` dá só os valores de nuvem **dentro da zona** (True ou False).
A média de True/False é a fracção de True. Multiplique por 100 para ter a percentagem.
"""),
         code(f"""
nuvem_pct = {v('100 * chuvosa["nuvem"][zona].mean()')}     # ✏️
verificar("nuvem_pct", nuvem_pct)
"""),
         md("""
## Passo 3 · Os índices de água ✏️

O NDWI já está feito. **Escreva o MNDWI** para as duas datas, seguindo o exemplo:

MNDWI = (Verde − SWIR) / (Verde + SWIR)
"""),
         code(f"""
with np.errstate(divide="ignore", invalid="ignore"):
    ndwi_seca     = (seca["verde"] - seca["nir"]) / (seca["verde"] + seca["nir"])
    ndwi_chuvosa  = (chuvosa["verde"] - chuvosa["nir"]) / (chuvosa["verde"] + chuvosa["nir"])
    mndwi_seca    = {v('(seca["verde"] - seca["swir"]) / (seca["verde"] + seca["swir"])')}       # ✏️
    mndwi_chuvosa = {v('(chuvosa["verde"] - chuvosa["swir"]) / (chuvosa["verde"] + chuvosa["swir"])')}    # ✏️

preenchido(mndwi_seca, mndwi_chuvosa)
print("Índices calculados.")
"""),
         code("""
preenchido(mndwi_seca, mndwi_chuvosa)
fig, eixos = plt.subplots(2, 2, figsize=(11, 15))
mapas = [(ndwi_seca, "NDWI · seca"), (ndwi_chuvosa, "NDWI · chuvosa"),
         (mndwi_seca, "MNDWI · seca"), (mndwi_chuvosa, "MNDWI · chuvosa")]
for eixo, (indice, titulo) in zip(eixos.ravel(), mapas):
    figura = eixo.imshow(indice, cmap="RdYlBu", vmin=-1, vmax=1)
    eixo.set_title(titulo)
    eixo.axis("off")
fig.colorbar(figura, ax=eixos, shrink=0.5, label="Valor do índice (azul = água)")
plt.show()
"""),
         md("✍️ **Pergunta:** o NDWI e o MNDWI mostram a mesma água? Onde diferem?"),
         resposta_cell(sol, info["resposta"].format(**k) if ano in (2014, 2021, 2022, 2024)
                       else "Nos anos sem problemas especiais, os dois índices mostram quase a mesma água; "
                            "o MNDWI separa melhor a água da vila e do solo escuro."),
         md("""
## Passo 4 · Limiar e área ✏️

Primeiro o histograma do MNDWI na estação chuvosa (só zona e sem nuvens). Depois conte a água.
Use **LIMIAR = 0** para verificar as respostas; no Passo 6 pode escolher o seu limiar.
"""),
         code("""
preenchido(mndwi_chuvosa)
vistos = zona & ~chuvosa["nuvem"]
plt.figure(figsize=(9, 4))
plt.hist(mndwi_chuvosa[vistos], bins=100, range=(-1, 1), color="steelblue")
plt.axvline(0, color="red", linestyle="--")
plt.xlabel("MNDWI na estação chuvosa (zona, sem nuvens)")
plt.ylabel("Número de píxeis")
plt.show()
"""),
         code(f"""
LIMIAR = 0.0

agua_seca    = (mndwi_seca > LIMIAR) & zona & ~seca["nuvem"]
agua_chuvosa = (mndwi_chuvosa > LIMIAR) & zona & ~chuvosa["nuvem"]
valido = zona & ~seca["nuvem"] & ~chuvosa["nuvem"]                      # vistos nas duas datas
nova = (mndwi_chuvosa > LIMIAR) & ~(mndwi_seca > LIMIAR) & valido      # água que não estava lá antes

# ✏️ Conte os píxeis de cada mapa (.sum()) e multiplique pela área de um píxel
ha_seca    = {v("agua_seca.sum() * area_pixel_ha")}
ha_chuvosa = {v("agua_chuvosa.sum() * area_pixel_ha")}
ha_nova    = {v("nova.sum() * area_pixel_ha")}

if LIMIAR == 0:
    verificar("agua_seca_ha", ha_seca)
    verificar("agua_chuvosa_ha", ha_chuvosa)
    verificar("agua_nova_ha", ha_nova)
else:
    print("A verificação só funciona com LIMIAR = 0.")
"""),
         code(f"""
preenchido(ha_nova, nuvem_pct)
print(f"Água nova: {{ha_nova:.0f}} ha = {{ha_nova / 100:.1f}} km² = cerca de {{ha_nova / {HA_CAMPO}:.0f}} campos de futebol")
print(f"Atenção: {{nuvem_pct:.0f}}% da zona tem nuvens. Debaixo delas não sabemos.")
"""),
         md("✍️ **Pergunta:** o resultado confirma a sua previsão do Passo 1? Porquê?"),
         resposta_cell(sol, f"Água nova (MNDWI > 0): cerca de {k['nova']} ha. " + info["resposta"].format(**k)),
         md(f"""
## Passo 5 · Investigar um píxel do rio ▶️

Escolhemos um píxel do rio (linha {lin}, coluna {col}) que se vê nas duas datas.
A célula mostra as reflectâncias e os índices nesse píxel. É aqui que se descobrem as "armadilhas".
"""),
         code(f"""
lin, col = {lin}, {col}
print(f"{{'':10s}}{{'verde':>8s}}{{'nir':>8s}}{{'swir':>8s}}{{'NDWI':>8s}}{{'MNDWI':>8s}}")
for nome, img in [("seca", seca), ("chuvosa", chuvosa)]:
    g, n, s = img["verde"][lin, col], img["nir"][lin, col], img["swir"][lin, col]
    print(f"{{nome:10s}}{{g:8.3f}}{{n:8.3f}}{{s:8.3f}}{{(g - n) / (g + n):8.2f}}{{(g - s) / (g + s):8.2f}}")
"""),
         md("✍️ **Pergunta:** o píxel é água nas duas datas, segundo cada índice? O que mudou nas bandas?"),
         resposta_cell(sol, f"No píxel do rio, na estação chuvosa: verde {k['p_verde']}, NIR {k['p_nir']}, "
                            f"SWIR {k['p_swir']}. Ver o desafio."),
         md("""
## Passo 6 · O vosso mapa final ✏️

Escolham o índice e o limiar, escrevam a justificação e corram. O mapa fica guardado num ficheiro PNG.
A última linha é o vosso resultado para o **quadro da turma**.
"""),
         code(f"""
NOME_PAR = "{v('Facilitadores', 'Par ?')}"       # ✏️ o nome do par
INDICE_FINAL = "MNDWI"                 # ✏️ "MNDWI" ou "NDWI"
LIMIAR_FINAL = 0.0                     # ✏️ o vosso limiar
JUSTIFICACAO = "{v('MNDWI com limiar 0, como no guia.', 'Escrevam aqui porque escolheram este índice e este limiar.')}"   # ✏️

preenchido(mndwi_seca, mndwi_chuvosa, area_pixel_ha)
indices = {{"MNDWI": (mndwi_seca, mndwi_chuvosa), "NDWI": (ndwi_seca, ndwi_chuvosa)}}
ind_seca, ind_chuv = indices[INDICE_FINAL]
a_seca = (ind_seca > LIMIAR_FINAL) & zona & ~seca["nuvem"]
a_nova = (ind_chuv > LIMIAR_FINAL) & ~(ind_seca > LIMIAR_FINAL) & valido
ha_s, ha_n = a_seca.sum() * area_pixel_ha, a_nova.sum() * area_pixel_ha

mapa = np.ones(zona.shape + (3,))
mapa[zona] = [0.93, 0.92, 0.88]                                       # zona: bege
mapa[a_seca] = [0.03, 0.18, 0.40]                                     # água antes: azul escuro
mapa[a_nova] = [0.17, 0.71, 0.63]                                     # água nova: verde-água
mapa[zona & (seca["nuvem"] | chuvosa["nuvem"])] = [0.72, 0.72, 0.75]  # sem dados: cinzento

from matplotlib.patches import Patch
legenda = [Patch(color=[0.03, 0.18, 0.40], label=f"Água na seca ({{ha_s:.0f}} ha)"),
           Patch(color=[0.17, 0.71, 0.63], label=f"Água nova ({{ha_n:.0f}} ha)"),
           Patch(color=[0.72, 0.72, 0.75], label="Sem dados (nuvens ou fora da imagem)")]
plt.figure(figsize=(8, 11))
plt.imshow(mapa)
plt.legend(handles=legenda, loc="lower right")
plt.title(f"Incomáti, Marracuene · {{chuvosa['data']}} · {{NOME_PAR}}\\n{{INDICE_FINAL}}, limiar {{LIMIAR_FINAL}}")
plt.figtext(0.5, 0.04, "Justificação: " + JUSTIFICACAO, ha="center", fontsize=9, wrap=True)
plt.axis("off")
ficheiro = f"mapa_{ano}_" + NOME_PAR.replace(" ", "_").replace("?", "") + ".png"
plt.savefig(ficheiro, dpi=150, bbox_inches="tight")
plt.show()
print("Mapa guardado:", ficheiro)
print(f"QUADRO DA TURMA -> ano {ano} | {{INDICE_FINAL}} > {{LIMIAR_FINAL}} | água nova {{ha_n:.0f}} ha | nuvens {{100 * chuvosa['nuvem'][zona].mean():.0f}}%")
try:
    from google.colab import files
    files.download(ficheiro)
except ImportError:
    pass
"""),
         md(f"""
## Passo 7 · Conclusões e desafio ✍️

**Conclusões (3 frases):** quanta água nova houve? Confirmou a previsão? Quanto confia no resultado (nuvens, data)?

**Desafio {info['estrelas']}:** {info['desafio'].format(**k)}
"""),
         resposta_cell(sol, info["resposta"].format(**k)),
         md(ERROS_COMUNS)]
    return c, k, (lin, col, valores)


def enunciado(ano: int, r: dict, k: dict) -> str:
    info = ANOS[ano]
    return f"""# Exercício {ano} · {info['titulo']} {info['estrelas']}

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

{info['contexto'].format(**k)}

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | {k['dseca']} | {k['dchuv']} |
| Caudal do rio nesse dia | {k['qseca']} m³/s | {k['qchuv']} m³/s |
| Satélite | {r['satelite']} | {r['satelite']} |

Pico do caudal no ano: **{k['pico']} m³/s a {k['dpico']}**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_{ano}.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

{info['desafio'].format(**k)}

## O que o par entrega

- O mapa PNG (`mapa_{ano}_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
"""


def construir(respostas: dict):
    feitos, sondas = [], {}
    for ano in ANOS:
        r = respostas[str(ano)]
        aluno, k, sonda = celulas(ano, r, sol=False)
        solucao, *_ = celulas(ano, r, sol=True)
        pasta = AULA / f"3_exercicios/ano_{ano}"
        feitos.append(escrever(aluno, pasta / f"exercicio_{ano}.ipynb", f"ETE · Exercício {ano}"))
        feitos.append(escrever(solucao, AULA / f"0_facilitadores/solucoes/solucao_{ano}.ipynb", f"ETE · Solução {ano}"))
        (pasta / "ENUNCIADO.md").write_text(enunciado(ano, r, k), encoding="utf-8")
        sondas[ano] = sonda
    return feitos, sondas
