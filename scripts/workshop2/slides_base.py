"""Peças dos slides do Workshop 2 (estilo académico: fundo branco, títulos a preto, destaques a carmim, sem azul).

O deck é do tipo Claude Slides: cada slide é uma <section> com CSS inline, num quadro de 1920 x 1080 px. As imagens
estão no repositório de ficheiros do artefacto (/_blob/...). Aqui ficam só as peças; o conteúdo está em slides.py.
"""

import re

BRANCO, TINTA, SUAVE, ACENTO = "#FFFFFF", "#1A1A1A", "#555555", "#A51C30"   # ACENTO = o carmim dos destaques
PRETO, CAB_TABELA = "#1A1A1A", "#262626"                                        # títulos e cabeçalhos das tabelas
CAIXA, LINHA, REALCE = "#F4F4F4", "#CCCCCC", "#EDEDED"
LARANJA, LARANJA_CX = "#1A1A1A", "#EDEDED"                  # avisos: barra preta em fundo cinzento (sem cor de alerta)
ERRO_FUNDO = "#F9ECEC"
SERIE_TREINO, SERIE_TESTE = "#444444", "#A51C30"
AGUA = "#1F5FA8"                                            # o azul só quer dizer ÁGUA (folha da árvore, mapas)
TITULO = "'Archivo Black', Arial, sans-serif"               # o Arial Black não existe no visualizador: Archivo Black
CODIGO = "'Courier New', monospace"
NB = " "                                               # espaço que não parte (20 244 ha)
SENTINEL = "Copernicus Sentinel-2 (ESA)"

BLOB = {
    "ete": "/_blob/e9749d3be602387c624be31fe951d98c", "oad": "/_blob/ee570e4e7a7857f8069df817829e1be3",
    "dara": "/_blob/6b795ac7a238c0c4964368c3dd6f9039", "seca": "/_blob/eb6f7f961584459423ce8aba9c5edd25",
    "cheia": "/_blob/b4ed7731e120ee834ac1beb71655cca0", "mapa_ws1": "/_blob/cd5a87a12d6e599ae9dbf11e93a5437c",
    "r2024_cor": "/_blob/3535609c0b2ccb6280e865fb7331e720", "r2024_mndwi": "/_blob/f2730439364c67e379b4315d5ff271fc",
    "r2021_cor": "/_blob/141b8b7808baf16fc58dff7cd7e84995", "r2021_ndwi": "/_blob/3ec6c96e152fffc04fc9253c56e9633a",
    "rotulos": "/_blob/4eb067e9cc9de6b55740bef818760420", "erros": "/_blob/3251e2ef2fd334e4c4e1bea67f968286",
    "exame": "/_blob/a23519a693a7ace72f43c0970f39954f", "anos": "/_blob/7e0d703eaf47d68ee303e76984ef0452",
    "caudal": "/_blob/530cdd67c9d65e216bd9ccb63cce5551", "ndti": "/_blob/9a4d6ff48ecaf21fa09438c3c76d1623",
    "trocos": "/_blob/05ec724533989380c5d3c36f2d4d04aa", "foz_cheia": "/_blob/179430d916ba43624f27d69aae8994a9",
    "foz_seca": "/_blob/07cfbe639714e2a5c7154e625226a929", "p_inicio": "/_blob/b99e2f560ca248bfc369c5170cac12f9",
    "p_cheias": "/_blob/76f543fadffe8376d3616094322864d6", "p_agua": "/_blob/05c3bd0f1f4833a448757503d65b0fbb",
    "p_alertas": "/_blob/158d964e342791ee800c862000dccd10", "m2024": "/_blob/66a6512c39011701cc683e296a3bfbe7",
    "ml_class": "/_blob/2c6b3f279256bd52ba33d4b85b8b480a", "ml_regr": "/_blob/9cac9ec4a00429ade7196fb46bdd63d2",
    "ml_treino": "/_blob/654c047beb6f5a1b7efe242152e821e7", "ml_agrup": "/_blob/09b2fadb7af8259b798a21b8f4ff7d25",
    "ml_kpassos": "/_blob/2c9d0c4a495d6f808ba2d5ece19f18bb", "ml_kmapa": "/_blob/aa5a99909814d3c0146bb22efa1d0093",
    "ml_ajuste": "/_blob/7c9e0f7be910143c9984d16680cf7c78", "ml_complex": "/_blob/862a1172e0e6ffb7ffa38d917881ba9c",
    "ml_caixas": "/_blob/27b4f39790d5a752cce4db66ae2d4aa0", "ml_knn": "/_blob/6ba33623414063e004b88a591c0220b7",
    "ml_rede": "/_blob/1e51a90bc21916bff0d462ca1bcc26ac", "regr_rio": "/_blob/36457cf0b8d3502b1074ceb7afc29a1e",
}

# Preenchido por slides.py antes de construir os slides: a secção e o número de cada slide, e as notas do orador
SECCAO, NUM, NOTAS = {}, {}, {}


def definir_ordem(ordem, seccoes):
    SECCAO.clear()
    NUM.clear()
    atual = ""
    for i, sid in enumerate(ordem, start=1):
        atual = seccoes.get(sid, atual)
        SECCAO[sid] = atual
        NUM[sid] = i


def fmt(x, casas=0):
    """Número à portuguesa, com espaço que não parte nos milhares: 20 244 ou 0,96."""
    return f"{x:,.{casas}f}".replace(",", NB).replace(".", ",")


# ---------- texto ----------

def p(texto, tam=30, cor=TINTA, peso=None, extra=""):
    w = f"font-weight:{peso};" if peso else ""
    lh = 1.4 if tam < 40 else 1.25
    return f'<p style="font-size:{tam}px;line-height:{lh};color:{cor};{w}{extra}">{texto}</p>'


def lead(texto, cor=TINTA, peso=None):
    return p(texto, 40, cor, peso)


def h3(texto, cor=ACENTO, tam=30):
    return f'<h3 style="font-family:Arial, sans-serif;font-size:{tam}px;font-weight:700;line-height:1.2;color:{cor}">{texto}</h3>'


def lista(itens, tam=30, num=False, cor=TINTA):
    tag = "ol" if num else "ul"
    return (f'<{tag} style="font-size:{tam}px;line-height:1.45;color:{cor}">'
            + "".join(f"<li>{i}</li>" for i in itens) + f"</{tag}>")


def caixa(titulo, conteudo, cor=ACENTO, fundo=CAIXA, extra=""):
    return (f'<div style="background:{fundo};border-left:6px solid {cor};padding:24px 32px;display:flex;'
            f'flex-direction:column;gap:10px;{extra}">' + (h3(titulo, cor) if titulo else "") + conteudo + "</div>")


def destaque(texto, tam=30):
    return (f'<div style="background:{REALCE};padding:22px 32px">'
            f'<p style="font-size:{tam}px;line-height:1.35;font-weight:700;color:{ACENTO}">{texto}</p></div>')


def codigo(texto, tam=30):
    return (f'<p style="font-family:{CODIGO};font-size:{tam}px;line-height:1.3;color:{TINTA};background:{BRANCO};'
            f'border:1px solid {LINHA};padding:10px 18px">{texto}</p>')


def bloco_codigo(linhas, tam=26):
    """Várias linhas de código num quadro (os espaços do início contam)."""
    texto = "<br>".join(l.replace("  ", NB * 2) for l in linhas)
    return (f'<p style="font-family:{CODIGO};font-size:{tam}px;line-height:1.45;color:{TINTA};background:{CAIXA};'
            f'border-left:6px solid {SUAVE};padding:18px 24px">{texto}</p>')


def logo_ete(tam=80, extra=""):
    return (f'<img src="{BLOB["ete"]}" alt="Logótipo do projecto EYES TO EARTH" '
            f'style="width:{tam}px;height:{tam}px;object-fit:contain;{extra}">')


def legenda(texto, fonte=None, tipo="Figura"):
    """A legenda numerada. O número (§N§) só é posto no fim, pela ordem dos slides (build_workshop2_slides.py)."""
    return p(f"<b>{tipo} §N§.</b> {texto}" + (f" Fonte: {fonte}." if fonte else ""), 24, SUAVE)


def numerar_legendas(htmls):
    """Recebe os slides pela ordem e põe os números das figuras e das tabelas (1, 2, 3...)."""
    conta = {"Figura": 0, "Tabela": 0}

    def trocar(m):
        conta[m.group(1)] += 1
        return f"{m.group(1)} {conta[m.group(1)]}"

    return [re.sub(r"(Figura|Tabela) §N§", trocar, h) for h in htmls], conta


# ---------- imagens, tabelas e arrumação ----------

def imagem(chave, alt, w, h, borda=True):
    b = f"border:1px solid {LINHA};" if borda else ""
    return f'<img src="{BLOB[chave]}" alt="{alt}" style="width:{w}px;height:{h}px;object-fit:contain;{b}">'


def figura(chave, alt, w, h, texto, fonte=None, borda=True):
    return (f'<div style="width:{w}px;display:flex;flex-direction:column;gap:10px">'
            + imagem(chave, alt, w, h, borda) + legenda(texto, fonte) + "</div>")


def tabela(cab, linhas, larg, tam=28, alinh=None, cores=None, largura=None):
    alinh = alinh or ["left"] * len(cab)
    w = f"width:{largura}px;" if largura else ""
    out = [f'<table style="{w}font-size:{tam}px;line-height:1.3;color:{TINTA};border:1px solid {LINHA}">',
           f'<tr style="background:{CAB_TABELA}">' + "".join(
               f'<th style="width:{l}%;color:#FFFFFF;font-weight:700;text-align:{a}">{c}</th>'
               for c, l, a in zip(cab, larg, alinh)) + "</tr>"]
    for i, ln in enumerate(linhas):
        bg = cores[i] if cores else (CAIXA if i % 2 == 1 else None)
        st = f' style="background:{bg}"' if bg else ""
        out.append(f"<tr{st}>" + "".join(f"<td>{c}</td>" for c in ln) + "</tr>")
    return "".join(out) + "</table>"


def linha(*filhos, gap=40, alinhar="flex-start", extra=""):
    return (f'<div style="display:flex;flex-direction:row;gap:{gap}px;align-items:{alinhar};{extra}">'
            + "".join(filhos) + "</div>")


def coluna(*filhos, gap=24, extra=""):
    return f'<div style="display:flex;flex-direction:column;gap:{gap}px;{extra}">' + "".join(filhos) + "</div>"


def grelha(filhos, colunas=2, gap="24px 32px"):
    return (f'<div style="display:grid;grid-template-columns:repeat({colunas}, 1fr);gap:{gap}">'
            + "".join(filhos) + "</div>")


def seta(w=56, h=28, cor=ACENTO):
    return f'<x-shape kind="arrow-right" style="width:{w}px;height:{h}px;background:{cor}"></x-shape>'


def ficha(texto, cheio=False):
    cor, fundo = (BRANCO, ACENTO) if cheio else (ACENTO, BRANCO)
    return f'<p style="font-size:28px;font-weight:700;color:{cor};background:{fundo};border:2px solid {ACENTO};padding:8px 16px">{texto}</p>'


def bloco(titulo, texto, extra="", cor=ACENTO, tam=26):
    """Um quadrado com contorno: título a negrito e texto (diagramas e passos)."""
    return (f'<div style="border:2px solid {cor};background:{BRANCO};padding:20px 24px;display:flex;flex-direction:column;'
            f'gap:8px;{extra}">' + h3(titulo, cor, 28) + (p(texto, tam) if texto else "") + "</div>")


def numero_grande(valor, texto, extra="", tam=120):
    return coluna(f'<p style="font-family:{TITULO};font-size:{tam}px;line-height:1.05;color:{ACENTO}">{valor}</p>',
                  p(texto), gap=8, extra=f"flex:1;{extra}")


def definicao(termo, texto, tam=28):
    return coluna(h3(termo), p(texto, tam), gap=6, extra=f"border-top:1px solid {LINHA};padding:16px 0 0 0")


def qr(texto, tam=360):
    return (f'<div style="width:{tam}px;height:{tam}px;border:3px dashed {SUAVE};display:flex;flex-direction:column;'
            f'align-items:center;justify-content:center;padding:24px">'
            + p(texto, 28, SUAVE, 700, "text-align:center") + "</div>")


def apoios():
    return (linha(p("Com o apoio de", 24, SUAVE),
                  f'<img src="{BLOB["oad"]}" alt="IAU Office of Astronomy for Development (IAU-OAD)" style="width:101px;height:110px;object-fit:contain">',
                  f'<img src="{BLOB["dara"]}" alt="DARA, Development in Africa with Radio Astronomy" style="width:198px;height:110px;object-fit:contain">',
                  gap=48, alinhar="center"))


def pergunta_abertura(texto):
    return caixa("Pergunta de abertura", lead(texto))


def revelar(conteudo, topo, altura=None, extra=""):
    """Uma caixa que aparece no clique seguinte (resposta do quiz, da pergunta de verificação)."""
    h = f"height:{altura}px;" if altura else ""
    return (f'<div data-build-in="fade" style="position:absolute;left:128px;top:{topo}px;width:1664px;{h}background:{REALCE};'
            f'border-left:6px solid {ACENTO};padding:28px 36px;display:flex;flex-direction:column;gap:10px;{extra}">'
            + conteudo + "</div>")


# ---------- o slide ----------

BANDA = f'<div style="position:absolute;left:0px;top:0px;width:28px;height:1080px;background:{ACENTO}"></div>'


def cabecalho(titulo):
    return (f'<div style="display:flex;flex-direction:row;align-items:center;gap:40px;'
            f'border-bottom:3px solid {ACENTO};padding:0 0 20px 0">'
            f'<h2 style="flex:1;font-family:{TITULO};font-size:52px;font-weight:400;line-height:1.1;color:{PRETO}">{titulo}</h2>'
            + logo_ete(80) + "</div>")


def rodape(sid):
    return (f'<div style="position:absolute;left:128px;bottom:52px;width:1664px;display:flex;flex-direction:row;'
            f'justify-content:space-between;align-items:center;gap:32px;border-top:1px solid {LINHA};padding:12px 0 0 0">'
            f'<p style="font-size:24px;color:{SUAVE}">EYES TO EARTH | Workshop de Estudantes 2 | {SECCAO[sid]}</p>'
            f'<p style="font-size:24px;color:{SUAVE}">{NUM[sid]}</p></div>')


def aside(sid):
    return f"\n<aside>{NOTAS[sid]}</aside>\n</section>\n"


# Slides com pouco texto: letra maior (por exemplo 1.15 = mais 15%). Preenchido por slides.py.
ESCALA = {}


def ampliar(html, escala):
    return re.sub(r"font-size:(\d+)px", lambda m: f"font-size:{round(int(m.group(1)) * escala)}px", html)


def slide(sid, titulo, corpo, gap=32, transicao=None, extra_fim=""):
    """Um slide normal: título, conteúdo e rodapé. O conteúdo fica centrado na vertical (sem meia página vazia),
    excepto quando há uma caixa em posição fixa (extra_fim: a resposta que aparece depois)."""
    if ESCALA.get(sid, 1) != 1:
        corpo = ampliar(corpo, ESCALA[sid])
    if not extra_fim:
        corpo = (f'<div style="flex:1;display:flex;flex-direction:column;justify-content:center;gap:{gap}px">'
                 + corpo + "</div>")
    t = f' data-transition="{transicao}"' if transicao else ""
    return (f'<section id="{sid}"{t} style="background:{BRANCO};color:{TINTA};font-family:Arial, sans-serif;'
            f'padding:64px 128px 160px;display:flex;flex-direction:column;gap:{gap}px">\n'
            + cabecalho(titulo) + "\n" + corpo + "\n" + extra_fim + rodape(sid) + aside(sid))


def divisoria(sid, rotulo, titulo, info, corpo=""):
    logo = logo_ete(80, "position:absolute;right:128px;top:64px")
    return (f'<section id="{sid}" data-transition="fade" style="background:{BRANCO};color:{TINTA};'
            f'font-family:Arial, sans-serif;padding:128px 128px 160px;display:flex;flex-direction:column;'
            f'justify-content:center;gap:28px">\n' + BANDA + logo + "\n"
            + p(rotulo, 30, ACENTO, 700)
            + f'<h1 style="font-family:{TITULO};font-size:84px;font-weight:400;line-height:1.08;color:{PRETO}">{titulo}</h1>'
            + f'<div style="width:200px;height:6px;background:{ACENTO}"></div>'
            + (p(info, 30, SUAVE) if info else "") + "\n" + corpo + "\n" + rodape(sid) + aside(sid))


# ---------- verificações ----------

def larg_titulo(t, tam):
    """Largura aproximada de um título em Archivo Black (para avisar quando passa para 2 linhas)."""
    w = 0
    for c in t:
        if c in " .,:;!|'’ilj()-":
            w += 0.34
        elif c in "frt":
            w += 0.45
        elif c in "mwMW":
            w += 0.98
        elif c.isupper() or c.isdigit():
            w += 0.74
        else:
            w += 0.64
    return w * tam


def palavras_visiveis(html):
    """As palavras que se vêem no slide (sem notas e sem rodapé): para não haver slides cansativos."""
    import html as h
    t = re.sub(r"<aside>.*?</aside>", "", html, flags=re.S)
    t = re.sub(r'<p style="font-size:24px;color:#555555">EYES TO EARTH \| Workshop de Estudantes 2 \|.*?</p>', "", t)
    return len(re.findall(r"\w+", h.unescape(re.sub(r"<[^>]+>", " ", t))))
