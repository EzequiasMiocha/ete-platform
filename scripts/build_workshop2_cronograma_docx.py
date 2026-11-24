"""Cronograma das actividades do Workshop 2, em Word (.docx), só com a tabela do dia, a preto e branco, em Times New Roman.

    .venv/bin/python scripts/build_workshop2_cronograma_docx.py

Escreve Workshop_2/0_facilitadores/Workshop2_Cronograma.docx (A4 deitado, uma página). O .docx é escrito
directamente em WordprocessingML (ZIP + XML), sem bibliotecas extra. Os horários são os mesmos do plano do dia
e dos slides; os números dos slides vêm de scripts/workshop2/slides_ordem.py.
"""

import io
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from xml.sax.saxutils import escape

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workshop2.comum import FAC  # noqa: E402
from workshop2.slides_ordem import intervalo, numero  # noqa: E402   (os números dos slides vêm do deck)

DESTINO = FAC / "Workshop2_Cronograma.docx"
TINTA = LINHA = "000000"                          # só preto e branco: texto e linhas a preto, fundo branco
FONTE = "Times New Roman"

LINHAS = [
    ("08:00–08:15", "Registo (15 min)", "Presenças e crachás; formar os 5 pares; os computadores já têm o Jupyter Notebook aberto na pasta da prática", "Logística e Facilitador 6", str(numero("capa"))),
    ("08:15–08:35", "Abertura (20 min)", "Boas-vindas, objectivo e programa do dia (5 min); questionário OAD pré-workshop (5 min); revisão do Workshop 1 (10 min)", "Moderadora e Facilitador 1", intervalo("capa", "revisao-2024")),
    ("08:35–09:05", "Módulo 1 (30 min)", "O que é a Inteligência Artificial? Regras ou exemplos; IA, Machine Learning e Deep Learning; a IA no dia-a-dia, na segurança e na guerra", "Facilitador 1", intervalo("m1", "m1-gancho")),
    ("09:05–09:55", "Módulo 2 (50 min)", "Como uma máquina aprende: aprendizagem supervisionada (classificação e regressão), não supervisionada (só uma menção: o projecto não a usou) e por reforço; como se treina um modelo; quatro algoritmos", "Facilitador 2", intervalo("m2", "m2-actividade-votar")),
    ("09:55–10:05", "Quiz relâmpago (10 min)", "5 perguntas, uma por slide, em pares, com cartões A, B e C", "Moderadora", intervalo("quiz", "quiz-5")),
    ("10:05–10:35", "Módulo 3 (30 min)", "Como sabemos se o modelo é bom? Treino e teste, matriz de confusão, notas, subajuste e sobreajuste, hiperparâmetros", "Facilitador 5", intervalo("m3", "m3-verificacao")),
    ("10:35–11:00", "Módulo 4 (25 min)", "A IA e a qualidade da água: o que o satélite vê e o que não mede", "Facilitador 3", intervalo("m4", "m4-actividade")),
    ("11:00–11:20", "Módulo 5 (20 min)", "A plataforma EYES TO EARTH, do dado ao alerta, com demonstração ao vivo", "Facilitador 4", intervalo("m5", "m5-actividade")),
    ("11:20–11:40", "Intervalo (20 min)", "Matabicho; o Facilitador 6 confirma cada computador", "Logística e Facilitador 6", str(numero("intervalo"))),
    ("11:40–13:25", "Prática em pares (105 min)", "Quatro temas no Jupyter Notebook, cada um com uma aula guiada e uma prática em que os pares escrevem o código: ensinar com exemplos e treinar e testar (classificação), a cor do rio e a maré (classificação) e prever o caudal (regressão)", "Facilitador 5 e padrinhos dos pares", intervalo("pratica", "pratica-aula4")),
    ("13:25–13:40", "Apresentações (15 min)", "Cada par, 2 minutos: o mapa e a nota, o seu ano, o acerto com e sem a maré e o erro do caudal, uma lição", "Facilitador 5 e Moderadora", intervalo("apresentacoes", "resultados-modelos")),
    ("13:40–14:00", "Encerramento (20 min)", "Conclusões, perguntas, questionário OAD pós-workshop, avaliação do workshop, certificados e foto de grupo", "Moderadora", intervalo("licoes", "obrigado")),
]
CABECALHO = ("Hora", "Actividade", "Conteúdo", "Responsável", "Slides")
LARGURAS = [1500, 3000, 6850, 2738, 1050]          # DXA; soma = largura útil do A4 deitado com margens de 1,5 cm
LARGURA_TABELA = sum(LARGURAS)

NS = ('xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main" '
      'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships" '
      'xmlns:wp="http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing" '
      'xmlns:a="http://schemas.openxmlformats.org/drawingml/2006/main" '
      'xmlns:pic="http://schemas.openxmlformats.org/drawingml/2006/picture"')


def run(texto, tam=22, cor=TINTA, negrito=False, italico=False, fonte=FONTE):
    rpr = (f'<w:rFonts w:ascii="{fonte}" w:hAnsi="{fonte}" w:cs="{fonte}"/>' + ("<w:b/>" if negrito else "")
           + ("<w:i/>" if italico else "") + f'<w:color w:val="{cor}"/><w:sz w:val="{tam}"/><w:szCs w:val="{tam}"/>')
    return f'<w:r><w:rPr>{rpr}</w:rPr><w:t xml:space="preserve">{escape(texto)}</w:t></w:r>'


def paragrafo(runs, depois=0, antes=0, estilo=None, alinhar=None, borda_baixo=None, manter=False):
    ppr = (f'<w:pStyle w:val="{estilo}"/>' if estilo else "") + ("<w:keepNext/>" if manter else "")
    if borda_baixo:
        ppr += f'<w:pBdr><w:bottom w:val="single" w:sz="12" w:space="6" w:color="{borda_baixo}"/></w:pBdr>'
    ppr += f'<w:spacing w:before="{antes}" w:after="{depois}"/>' + (f'<w:jc w:val="{alinhar}"/>' if alinhar else "")
    return f"<w:p><w:pPr>{ppr}</w:pPr>{''.join(runs)}</w:p>"


def logotipo(cm=2.0):
    emu = int(cm * 360000)
    return (f'<w:r><w:drawing><wp:inline distT="0" distB="0" distL="0" distR="0"><wp:extent cx="{emu}" cy="{emu}"/>'
            '<wp:docPr id="1" name="Logótipo ETE" descr="Logótipo do projecto EYES TO EARTH"/>'
            '<wp:cNvGraphicFramePr><a:graphicFrameLocks noChangeAspect="1"/></wp:cNvGraphicFramePr>'
            '<a:graphic><a:graphicData uri="http://schemas.openxmlformats.org/drawingml/2006/picture">'
            '<pic:pic><pic:nvPicPr><pic:cNvPr id="1" name="logo_ete.png"/><pic:cNvPicPr/></pic:nvPicPr>'
            '<pic:blipFill><a:blip r:embed="rIdLogo"/><a:stretch><a:fillRect/></a:stretch></pic:blipFill>'
            f'<pic:spPr><a:xfrm><a:off x="0" y="0"/><a:ext cx="{emu}" cy="{emu}"/></a:xfrm>'
            '<a:prstGeom prst="rect"><a:avLst/></a:prstGeom></pic:spPr></pic:pic>'
            '</a:graphicData></a:graphic></wp:inline></w:drawing></w:r>')


def celula(conteudo, largura, fundo=None, alinhar_v="center", linha_baixo=None):
    tcpr = f'<w:tcW w:w="{largura}" w:type="dxa"/>'
    if linha_baixo:
        tcpr += f'<w:tcBorders><w:bottom w:val="single" w:sz="{linha_baixo}" w:space="0" w:color="{LINHA}"/></w:tcBorders>'
    if fundo:
        tcpr += f'<w:shd w:val="clear" w:color="auto" w:fill="{fundo}"/>'
    tcpr += f'<w:vAlign w:val="{alinhar_v}"/>'
    return f"<w:tc><w:tcPr>{tcpr}</w:tcPr>{conteudo}</w:tc>"


def bloco_titulo():
    """Uma tabela sem contornos: o logótipo à esquerda, o título e os dados do dia à direita."""
    esquerda = paragrafo([logotipo(1.8)])
    direita = (paragrafo([run("Cronograma das actividades", 40, TINTA, True)], depois=60, estilo="Title")
               + paragrafo([run("Workshop de Estudantes 2 | Inteligência Artificial para monitorizar a água e avisar das cheias", 24, TINTA, True)], depois=40)
               + paragrafo([run("Sábado, 21 de Novembro de 2026 | 08:00–14:00 | Maputo | Projecto EYES TO EARTH (ETE)", 22, TINTA)]))
    sem_borda = "".join(f'<w:{lado} w:val="nil"/>' for lado in ("top", "left", "bottom", "right", "insideH", "insideV"))
    return (f'<w:tbl><w:tblPr><w:tblW w:w="{LARGURA_TABELA}" w:type="dxa"/>'
            f'<w:tblBorders>{sem_borda}</w:tblBorders><w:tblLayout w:type="fixed"/>'
            '<w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="0" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="160" w:type="dxa"/></w:tblCellMar>'
            '<w:tblLook w:val="0000" w:firstRow="0" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="1" w:noVBand="1"/></w:tblPr>'
            f'<w:tblGrid><w:gridCol w:w="1400"/><w:gridCol w:w="{LARGURA_TABELA - 1400}"/></w:tblGrid>'
            f'<w:tr>{celula(esquerda, 1400)}{celula(direita, LARGURA_TABELA - 1400)}</w:tr></w:tbl>')


def tabela_cronograma():
    bordas = "".join(f'<w:{lado} w:val="single" w:sz="4" w:space="0" w:color="{LINHA}"/>'
                     for lado in ("top", "left", "bottom", "right", "insideH", "insideV"))
    xml = [f'<w:tbl><w:tblPr><w:tblW w:w="{LARGURA_TABELA}" w:type="dxa"/>'
           f'<w:tblBorders>{bordas}</w:tblBorders><w:tblLayout w:type="fixed"/>'
           '<w:tblCellMar><w:top w:w="50" w:type="dxa"/><w:left w:w="110" w:type="dxa"/><w:bottom w:w="50" w:type="dxa"/><w:right w:w="110" w:type="dxa"/></w:tblCellMar>'
           '<w:tblLook w:val="0420" w:firstRow="1" w:lastRow="0" w:firstColumn="0" w:lastColumn="0" w:noHBand="0" w:noVBand="1"/></w:tblPr>',
           "<w:tblGrid>" + "".join(f'<w:gridCol w:w="{l}"/>' for l in LARGURAS) + "</w:tblGrid>"]
    cab = "".join(celula(paragrafo([run(t, 22, TINTA, True)], alinhar="center" if t == "Slides" else None), l, linha_baixo=12)
                  for t, l in zip(CABECALHO, LARGURAS))
    xml.append(f'<w:tr><w:trPr><w:cantSplit/><w:tblHeader/></w:trPr>{cab}</w:tr>')
    for i, (hora, actividade, conteudo, quem, slides) in enumerate(LINHAS):
        pausa = actividade.startswith("Intervalo")             # o intervalo em itálico (sem cores)
        celulas = [celula(paragrafo([run(hora, 22, TINTA, True)]), LARGURAS[0]),
                   celula(paragrafo([run(actividade, 22, TINTA, True, pausa)]), LARGURAS[1]),
                   celula(paragrafo([run(conteudo, 22, italico=pausa)]), LARGURAS[2]),
                   celula(paragrafo([run(quem, 22, italico=pausa)]), LARGURAS[3]),
                   celula(paragrafo([run(slides, 22, italico=pausa)], alinhar="center"), LARGURAS[4])]
        xml.append(f'<w:tr><w:trPr><w:cantSplit/></w:trPr>{"".join(celulas)}</w:tr>')
    xml.append("</w:tbl>")
    return "".join(xml)


def documento():
    corpo = (bloco_titulo()
             + paragrafo([], depois=120, borda_baixo=LINHA)
             + tabela_cronograma()
             + paragrafo([run("Duração total: 360 minutos (6 horas): registo 15, abertura 20, teoria 155 (5 módulos e o quiz), "
                              "intervalo 20, prática 105, apresentações 15 e encerramento 20.", 20)], antes=160, depois=40)
             + paragrafo([run("Moderadora: Armenia Machava. Os Facilitadores 1 a 7 e os papéis de cada um estão no Plano do Workshop 2.", 20)]))
    sect = ('<w:sectPr><w:pgSz w:w="16838" w:h="11906" w:orient="landscape"/>'
            '<w:pgMar w:top="850" w:right="850" w:bottom="850" w:left="850" w:header="425" w:footer="425" w:gutter="0"/></w:sectPr>')
    return f'<?xml version="1.0" encoding="UTF-8" standalone="yes"?>\n<w:document {NS}><w:body>{corpo}{sect}</w:body></w:document>'


ESTILOS = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<w:styles xmlns:w="http://schemas.openxmlformats.org/wordprocessingml/2006/main">
<w:docDefaults><w:rPrDefault><w:rPr><w:rFonts w:ascii="{FONTE}" w:hAnsi="{FONTE}" w:eastAsia="{FONTE}" w:cs="{FONTE}"/><w:color w:val="{TINTA}"/><w:sz w:val="22"/><w:szCs w:val="22"/><w:lang w:val="pt-PT" w:eastAsia="pt-PT" w:bidi="ar-SA"/></w:rPr></w:rPrDefault>
<w:pPrDefault><w:pPr><w:spacing w:after="0" w:line="252" w:lineRule="auto"/></w:pPr></w:pPrDefault></w:docDefaults>
<w:style w:type="paragraph" w:default="1" w:styleId="Normal"><w:name w:val="Normal"/><w:qFormat/></w:style>
<w:style w:type="paragraph" w:styleId="Title"><w:name w:val="Title"/><w:basedOn w:val="Normal"/><w:next w:val="Normal"/><w:qFormat/>
<w:pPr><w:keepNext/><w:spacing w:before="0" w:after="60"/></w:pPr><w:rPr><w:rFonts w:ascii="{FONTE}" w:hAnsi="{FONTE}" w:cs="{FONTE}"/><w:b/><w:color w:val="{TINTA}"/><w:sz w:val="40"/><w:szCs w:val="40"/></w:rPr></w:style>
<w:style w:type="table" w:default="1" w:styleId="TableNormal"><w:name w:val="Normal Table"/><w:uiPriority w:val="99"/><w:semiHidden/><w:unhideWhenUsed/>
<w:tblPr><w:tblInd w:w="0" w:type="dxa"/><w:tblCellMar><w:top w:w="0" w:type="dxa"/><w:left w:w="108" w:type="dxa"/><w:bottom w:w="0" w:type="dxa"/><w:right w:w="108" w:type="dxa"/></w:tblCellMar></w:tblPr></w:style>
</w:styles>'''

TIPOS = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">
<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/>
<Default Extension="xml" ContentType="application/xml"/>
<Default Extension="png" ContentType="image/png"/>
<Override PartName="/word/document.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.document.main+xml"/>
<Override PartName="/word/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.wordprocessingml.styles+xml"/>
<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>
<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/>
</Types>'''

RELACOES = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="word/document.xml"/>
<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>
<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/>
</Relationships>'''

RELACOES_DOC = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">
<Relationship Id="rIdEstilos" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/>
<Relationship Id="rIdLogo" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/image" Target="media/logo_ete.png"/>
</Relationships>'''


def propriedades():
    agora = datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    core = f'''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:dcmitype="http://purl.org/dc/dcmitype/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">
<dc:title>Cronograma das actividades · Workshop de Estudantes 2</dc:title><dc:creator>Projecto EYES TO EARTH (ETE)</dc:creator><dc:language>pt-PT</dc:language>
<dcterms:created xsi:type="dcterms:W3CDTF">{agora}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{agora}</dcterms:modified>
</cp:coreProperties>'''
    app = '''<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties"><Application>Projecto ETE</Application></Properties>'''
    return core, app


def logo_png():
    im = Image.open(FAC / "imagens_para_slides/logo_ete.png").convert("LA").resize((240, 240), Image.LANCZOS)   # em tons de cinzento
    buf = io.BytesIO()
    im.save(buf, format="PNG", optimize=True)
    return buf.getvalue()


def main():
    core, app = propriedades()
    with zipfile.ZipFile(DESTINO, "w", zipfile.ZIP_DEFLATED) as z:      # só ficheiros, sem entradas de pastas
        z.writestr("[Content_Types].xml", TIPOS)
        z.writestr("_rels/.rels", RELACOES)
        z.writestr("word/document.xml", documento())
        z.writestr("word/styles.xml", ESTILOS)
        z.writestr("word/_rels/document.xml.rels", RELACOES_DOC)
        z.writestr("word/media/logo_ete.png", logo_png())
        z.writestr("docProps/core.xml", core)
        z.writestr("docProps/app.xml", app)
    print(DESTINO.relative_to(ROOT), f"{DESTINO.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
