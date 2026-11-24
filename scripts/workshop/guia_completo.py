"""Versão completa do notebook guiado para o facilitador: interpretação de cada resultado e respostas-modelo.

Gera 0_facilitadores/aula_guiada_COMPLETA_facilitador.ipynb a partir das mesmas células do notebook dos
estudantes (guia.celulas), acrescentando depois de cada resultado:
  🔎 Interpretação   o que o resultado mostra, com os números reais
  🗣️ Dizer à turma   a frase ou pergunta para a sala
  ⏱️ Tempo           onde devemos estar no relógio
e trocando cada "*Resposta:*" pela resposta-modelo. Os números vêm das respostas de referência e de
contas feitas aqui com os mesmos dados (nada é escrito à mão).
"""

import numpy as np

from .comum import AULA, HA_CAMPO, escrever, fmt, md
from .guia import PIXEIS, celulas


def numeros(r):
    """As contas que a interpretação cita, feitas com os mesmos ficheiros dos estudantes."""
    d = AULA / "2_aula_guiada/dados"
    s, c = np.load(d / "incomati_2026_seca.npz"), np.load(d / "incomati_2026_cheia.npz")
    bs = {k: s[k] / 10000 for k in ("verde", "vermelho", "nir", "swir")}
    bc = {k: c[k] / 10000 for k in ("verde", "vermelho", "nir", "swir")}
    with np.errstate(divide="ignore", invalid="ignore"):
        ms = (bs["verde"] - bs["swir"]) / (bs["verde"] + bs["swir"])
        mc = (bc["verde"] - bc["swir"]) / (bc["verde"] + bc["swir"])
        nc = (bc["verde"] - bc["nir"]) / (bc["verde"] + bc["nir"])
    zona = s["zona"]
    vistos = zona & ~c["nuvem"]
    lim = {l: float(((mc > l) & vistos).sum() * 0.09) for l in (-0.2, 0.0, 0.2)}
    h, e = np.histogram(mc[vistos], bins=100, range=(-1, 1))
    terra, agua = e[np.argmax(h[:50])], e[50 + np.argmax(h[50:])]
    vale = e[40 + np.argmin(h[40:60])]
    nuvem = c["nuvem"] & zona & (c["verde"] > 0)
    pix = {nome: {k: float(bs[k][l, col]) for k in ("verde", "vermelho", "nir", "swir")} for nome, (l, col) in PIXEIS.items()}
    return dict(
        lim=lim, terra=terra + 0.01, agua=agua + 0.01, vale=vale + 0.01,
        entre=100 * ((mc[vistos] > -0.2) & (mc[vistos] < 0.2)).mean(),
        nuvem_mndwi=float(np.nanmedian(mc[nuvem])), nuvem_pos=100 * float((mc[nuvem] > 0).mean()),
        ndwi_cheia=float(((nc > 0) & vistos).sum() * 0.09),
        mar=float(((ms > 0) & ~zona).sum() * 0.09),
        zona=float(zona.sum() * 0.09), vista=100 * float(vistos.sum() / zona.sum()),
        pix=pix, mrio=float(ms[PIXEIS["Água (rio)"]]), mveg=float(ms[PIXEIS["Vegetação"]]),
        pixeis=int(zona.size),
    )


def textos(r, n):
    lim = n["lim"]
    p = n["pix"]
    nova, seca, cheia = r["agua_nova_ha"], r["agua_seca_ha"], r["agua_chuvosa_ha"]
    variacao = 100 * (lim[-0.2] - lim[0.2]) / 2 / lim[0.0]
    i = {}   # interpretações, depois da célula de código que contém a chave
    i["seca = carregar("] = f"""
🔎 **Interpretação.** Temos duas imagens do Sentinel-2. A da seca é de {r['data_seca']}, com o rio a
{fmt(r['caudal_seca'], 1)} m³/s. A da cheia é de {r['data_chuvosa']}, com {fmt(r['caudal_chuvosa'])} m³/s: cinco dias
depois do pico de {fmt(r['caudal_pico'])} m³/s ({r['data_pico']}). O caudal na cheia é cerca de
{fmt(r['caudal_chuvosa'] / max(r['caudal_seca'], 0.1))} vezes o da seca. O dicionário tem 14 gavetas: 5 bandas, 2 máscaras
(`nuvem` e `zona`) e 7 informações (data, satélite, caudal...).

🗣️ **Dizer à turma:** "Um dicionário é como uma mochila com bolsos com nome: `seca['verde']` é o bolso da
banda verde da imagem da seca."

⏱️ **Tempo:** Passos 0 e 1 entre as 12:25 e as 12:32. Se um par tiver `FileNotFoundError`, ver o Problema 1 do manual.
"""
    i["linhas, colunas = seca"] = f"""
🔎 **Interpretação.** Cada banda é uma tabela de 1 110 linhas × 735 colunas = {fmt(n['pixeis'])} píxeis. Cada píxel
cobre 30 m × 30 m = 900 m², e a imagem cobre 22 km × 33 km da planície. O píxel do rio devolve só
{fmt(p['Água (rio)']['verde'] * 100, 1)}% da luz verde que recebe (reflectância 0,058): a água é escura.

🗣️ **Dizer à turma:** "Uma fotografia de telemóvel tem mais píxeis do que isto, mas cada píxel do telemóvel
mostra uns milímetros. Aqui cada píxel mostra um quadrado de 30 por 30 metros: um terço de um campo de futebol
ao comprido."
"""
    i["eixo.imshow(cor_natural(img))"] = f"""
🔎 **Interpretação.**
- **Seca:** o rio é uma faixa estreita e sinuosa. A planície é verde e castanha, com campos em talhões a
  nordeste. As manchas cinzentas esbatidas são fumo de queimadas (outubro é época de queimadas).
- **Cheia:** a planície inteira, da vila até ao limite norte, está coberta de **água castanha**. Só ficam secas
  as dunas da costa e a terra alta a oeste. O castanho vem dos **sedimentos** que o rio arrasta: é turbidez alta,
  o mesmo indicador de qualidade da água que a plataforma ETE acompanha.
- As **manchas brancas** são nuvens, com as sombras escuras ao lado. A faixa preta no canto superior esquerdo
  fica fora da passagem do satélite (sem dados).
- A linha amarela é a zona em estudo: o distrito de Marracuene **sem o mar**.

⏱️ **Tempo:** Passo 2 (cor natural e falsa cor) entre as 12:32 e as 12:38.
"""
    i["plt.imshow(falsa_cor(seca))"] = """
🔎 **Interpretação.** Na falsa cor, a vegetação viva aparece **vermelha**: a planície e os campos regados a nordeste
estão vermelho vivo, porque as folhas reflectem muito infravermelho próximo (NIR). O rio e o mar ficam
**quase pretos**: a água absorve o NIR. A vila e o solo nu a oeste ficam acinzentados ou azulados.

🗣️ **Dizer à turma:** "O olho humano não vê o NIR, mas o satélite vê. É aqui que a água se distingue de tudo o resto."
"""
    agua, veg, solo = p["Água (rio)"], p["Vegetação"], p["Solo nu"]
    i["pixeis = {"] = f"""
🔎 **Interpretação.**
- **Água (rio):** verde {fmt(agua['verde'], 3)}, NIR {fmt(agua['nir'], 3)}, SWIR {fmt(agua['swir'], 3)}. Pouca luz em
  tudo, e cada vez menos para o infravermelho: a água absorve o NIR e ainda mais o SWIR. O vermelho
  ({fmt(agua['vermelho'], 3)}) é um pouco maior do que o verde: o Incomáti tem sedimentos mesmo na seca.
- **Vegetação:** o vermelho é muito baixo ({fmt(veg['vermelho'], 3)}), porque a clorofila o absorve para a
  fotossíntese, e o NIR é muito alto ({fmt(veg['nir'], 3)}), porque a estrutura das folhas o reflecte. É o "salto"
  da vegetação.
- **Solo nu:** sobe devagar do verde ({fmt(solo['verde'], 3)}) até ao SWIR ({fmt(solo['swir'], 3)}).

As três curvas são as **assinaturas espectrais** do Módulo 3, medidas em Marracuene.

⏱️ **Tempo:** Passo 3 entre as 12:38 e as 12:42.
"""
    i["ndwi_seca   = "] = f"""
🔎 **Interpretação.** O píxel do rio tem MNDWI = {fmt(n['mrio'], 2)} (positivo, água) e o píxel de vegetação
tem {fmt(n['mveg'], 2)} (negativo, não é água). O numpy fez esta conta para os {fmt(n['pixeis'])} píxeis de cada
imagem, quatro vezes, em menos de um segundo.

🗣️ **Dizer à turma:** "É a mesma conta que fizeram à mão para os píxeis A, B e C, mas para 800 mil píxeis de uma vez."
"""
    i['(ndwi_seca, "NDWI · seca")'] = f"""
🔎 **Interpretação.**
- **Seca:** só o rio (uma linha azul fina), algumas lagoas e o mar estão azuis. O resto é amarelo ou vermelho
  (vegetação e solo, índice negativo).
- **Cheia:** a planície inteira fica azul. O NDWI e o MNDWI concordam nesta cheia: com o limiar 0, o NDWI dá
  {fmt(n['ndwi_cheia'])} ha de água na zona e o MNDWI dá {fmt(cheia)} ha. Noutros anos não concordam (ver os
  exercícios de 2021 e 2024).
- **O mar** está azul nas duas datas. Se o contássemos, juntaríamos cerca de {fmt(n['mar'])} ha de "água" às duas
  datas e a cheia ficaria escondida nas contas. Por isso usamos a zona.
- **As nuvens** têm um MNDWI perto de 0 (mediana {fmt(n['nuvem_mndwi'], 2)}) e cerca de {fmt(n['nuvem_pos'])}% delas
  passariam por "água" com o limiar 0. Por isso tiramos as nuvens com a máscara `nuvem`.
"""
    i["plt.hist(valores"] = f"""
🔎 **Interpretação.** O histograma tem dois montes bem separados: a **terra**, com o pico perto de
{fmt(n['terra'], 2)}, e a **água**, com o pico perto de +{fmt(n['agua'], 2)}. Há poucos píxeis no meio: só
{fmt(n['entre'], 1)}% dos píxeis vistos ficam entre −0,2 e +0,2. O vale mais fundo fica perto de
{fmt(n['vale'], 2)}. Qualquer limiar entre −0,2 e +0,2 dá quase o mesmo mapa.

🗣️ **Dizer à turma:** "Quando os dois montes estão bem separados, o limiar quase não importa. Quando estão
colados (água barrenta, sombras, vegetação alagada), a escolha do limiar muda muito o resultado."
"""
    i["LIMIARES = [-0.2, 0.0, 0.2]"] = f"""
🔎 **Interpretação.** Limiar −0,2: {fmt(lim[-0.2])} ha. Limiar 0: {fmt(lim[0.0])} ha. Limiar +0,2: {fmt(lim[0.2])} ha.
Entre o limiar mais baixo e o mais alto, a área muda só cerca de ±{fmt(variacao, 0)}%. Com o limiar baixo aparecem
mais píxeis nas margens e nas sombras; com o alto perdem-se margens pouco fundas. Para esta cheia, o
**limiar 0 é uma boa escolha** e fácil de justificar: fica perto do vale do histograma.

⏱️ **Tempo:** Passos 4 e 5 entre as 12:42 e as 12:53. A barra deslizante (célula seguinte) é opcional: usar só
se houver tempo e se funcionar no Colab do par.
"""
    i["ver_limiar(limiar=0.0)"] = """
🔎 **Como usar.** Arrastar a barra para a esquerda (limiar baixo) e para a direita (limiar alto) e ver a área no
título. Se a barra não aparecer (alguns ambientes não mostram widgets), não há problema: a célula anterior
faz o mesmo com três limiares fixos.
"""
    i["LIMIAR = 0.0"] = f"""
🔎 **Interpretação.**
- **Zona em estudo:** {fmt(n['zona'])} ha (cerca de {fmt(n['zona'] / 100)} km²). Na cheia, {fmt(r['nuvem_chuvosa_pct'], 1)}%
  da zona não se vê (nuvens ou fora da imagem); vemos {fmt(n['vista'])}%.
- **Água na seca:** {fmt(seca)} ha: o leito do rio e as lagoas.
- **Água na cheia:** pelo menos {fmt(cheia)} ha.
- **Água nova:** {fmt(nova)} ha = {fmt(nova / 100)} km² = cerca de {fmt(nova / HA_CAMPO)} campos de futebol.
  É mais ou menos **metade da zona em estudo** ({fmt(100 * nova / n['zona'])}%).
- A cheia multiplicou a água da planície por cerca de {fmt(cheia / seca)}.

🗣️ **Dizer à turma:** "Vinte mil hectares: é como se 28 mil campos de futebol ficassem debaixo de água."
"""
    i["mapa = np.ones(zona.shape"] = """
🔎 **Interpretação do mapa.** A água nova (verde-água) cobre a planície desde a vila até ao limite norte do
distrito, dos dois lados do rio. O azul escuro é o leito normal do rio e as lagoas: a cheia saiu do leito e
espalhou-se. O cinzento (sem dados) fica sobretudo nas dunas da costa, na terra alta a oeste e na faixa fora da
imagem. A maior parte da planície alagada está à vista, por isso o mínimo calculado deve estar perto do valor real
na planície.

⏱️ **Tempo:** Passos 6 e 7 entre as 12:53 e as 13:03. Cada par muda `NOME_PAR` e escreve a sua `JUSTIFICACAO`.
"""
    i['z = np.load(encontrar("zona_agricola'] = """
🔎 **Interpretação.** A 10 m vêem-se os talhões um a um, os caminhos entre eles, os canais de rega e as duas
margens do rio. A 30 m só se distinguem os blocos grandes, e o rio aparece "aos degraus". Na mesma zona de
5 km × 5 km há 250 498 píxeis a 10 m e 27 722 a 30 m: 9 vezes mais, porque (30 ÷ 10)² = 9.

⏱️ **Tempo:** o Passo 9 é extra. Só se às 13:06 ainda houver tempo; senão, mostrar só a figura e passar aos exercícios.
"""
    a = {}   # respostas-modelo, na célula de texto que contém a chave
    a["o que mudou entre as duas imagens"] = (
        "Na cheia, a água saiu do leito e cobriu a planície entre a vila e o limite norte do distrito. A água é "
        "castanha porque leva muitos sedimentos em suspensão (turbidez alta, Módulo 3). As manchas brancas são "
        "nuvens, e as manchas escuras ao lado delas são as suas sombras.")
    a["Qual dos nossos três píxeis se parece com A"] = (
        f"O rio parece-se com o A (pouca luz em todas as bandas, verde maior do que NIR e SWIR). A vegetação "
        f"parece-se com o B (NIR muito alto: {fmt(veg['nir'], 2)} contra 0,45). O solo nu parece-se com o C (sobe do "
        f"verde até ao SWIR). A água tem o verde maior porque absorve quase toda a luz infravermelha (NIR e SWIR), "
        f"enquanto ainda devolve um pouco de luz verde.")
    a["onde aparece mais azul, na seca ou na cheia"] = (
        "Na cheia: a planície inteira fica azul. O mar é azul nas duas datas e fica fora da zona. As nuvens ficam "
        f"perto de 0 (mediana {fmt(n['nuvem_mndwi'], 2)}) e cerca de metade passaria por água: por isso as tiramos "
        "com a máscara de nuvens.")
    a['porque dizemos "pelo menos"'] = (
        f"Porque {fmt(r['nuvem_chuvosa_pct'])}% da zona não se vê. Debaixo das nuvens pode haver mais água; só contamos "
        "o que vemos. O resultado é um **mínimo**.")
    a["O desafio do analista"] = (
        "Com o **radar do Sentinel-1**, que envia a sua própria onda e atravessa as nuvens: a água lisa reflecte a "
        "onda para longe e aparece escura. É o que a plataforma ETE usa nos dias nublados (cerca de 214 km² de água "
        "nova em janeiro de 2026, parecido com os nossos 202 km²).")
    a["quantos talhões consegue contar"] = (
        "A 10 m contam-se dezenas de talhões, com os caminhos e os canais; a 30 m só os blocos maiores. Para a cheia "
        "de janeiro de 2013 não havia Sentinel-2 (começou em 2015) nem Landsat 8 operacional (abril de 2013), e o "
        "Landsat 5 já tinha parado. Restava o **Landsat 7, com riscas sem dados** (avaria de 2003), ou o MODIS, que "
        "passa todos os dias mas com píxeis de 250 m.")
    return i, a


CABECALHO = """
# VERSÃO COMPLETA DO FACILITADOR · com interpretação de cada resultado

Este notebook é o mesmo que os estudantes recebem, já executado, com três acrescentos:

| Sinal | Quer dizer |
| --- | --- |
| 🔎 **Interpretação** | O que o resultado mostra, com os números reais desta execução |
| 🗣️ **Dizer à turma** | A frase ou a pergunta para a sala |
| ⏱️ **Tempo** | Onde devemos estar no relógio (aula guiada das 12:25 às 13:10) |

As perguntas ✍️ já têm a **resposta-modelo**. Use-o no seu portátil, ao lado do notebook projectado.
**Não partilhar com os estudantes.**
"""


def construir(respostas: dict):
    r = respostas["2026"]
    n = numeros(r)
    interp, resp = textos(r, n)
    base = celulas(r)
    saida = [md(CABECALHO)]
    for cel in base:
        if cel.cell_type == "markdown":
            for chave, texto in resp.items():
                if chave in cel.source:
                    cel.source = cel.source.replace("*Resposta:*", f"**Resposta-modelo:** {texto}", 1)
        saida.append(cel)
        if cel.cell_type == "code":
            for chave, texto in interp.items():
                if chave in cel.source:
                    saida.append(md(texto))
                    break
    usadas = sum(any(k in c.source for c in base if c.cell_type == "code") for k in interp)
    assert usadas == len(interp), f"só {usadas} de {len(interp)} interpretações encontraram a sua célula"
    assert not any("*Resposta:*" in c.source for c in saida), "ficou uma pergunta sem resposta-modelo"
    destino = AULA / "0_facilitadores/aula_guiada_COMPLETA_facilitador.ipynb"
    return [escrever(saida, destino, "ETE · Aula guiada · versão completa do facilitador")]
