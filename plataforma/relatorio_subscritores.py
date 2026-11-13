"""Ficheiro Excel com a base de dados `subscritores`, para a equipa acompanhar quem recebe os alertas.

Quatro folhas:
  Subscritores  uma linha por pessoa, com todas as variáveis (respostas escritas por extenso)
  Resumo        totais e contagens por sexo, idade, profissão, lugar e língua (só inscrições activas), com gráficos
  Envios        histórico dos alertas enviados (datas, níveis, quantas pessoas)
  Dicionário    o que quer dizer cada coluna

O ficheiro tem números de telefone: é só para a equipa, fica em data/private/ e não deve ser partilhado.
Gerado por: python scripts/ver_subscritores.py --excel
"""

from __future__ import annotations

import json
from collections import Counter
from pathlib import Path

import pandas as pd
from openpyxl import Workbook
from openpyxl.chart import BarChart, Reference
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter

import inscricoes as I

TINTA, ESPUMA, LINHA = "10231F", "E3F1EC", "E8E1D2"
CABECALHO = Font(bold=True, color="FFFFFF")
FUNDO = PatternFill("solid", fgColor=TINTA)
SUAVE = PatternFill("solid", fgColor=ESPUMA)
FINA = Border(bottom=Side(style="thin", color=LINHA))
LINGUAS = {"pt": "Português", "en": "Inglês", "fr": "Francês"}
ESTADOS = {"activa": "Activa", "removido": "Saiu"}

# column in the database -> (heading in Excel, what it means, possible values)
DICIONARIO = {
    "id": ("Inscrição", "Identificador da inscrição", "12 letras e números"),
    "criado_utc": ("Data de inscrição", "Quando a pessoa se inscreveu (hora de Maputo)", "data e hora"),
    "nome": ("Nome", "Nome dado pela pessoa", "opcional"),
    "telefone": ("Telefone (WhatsApp)", "Número para onde vão os alertas", "+258 8x xxx xxxx ou outro país"),
    "lugar": ("Lugar onde vive", "Bairro ou lugar escolhido na lista", "nomes de lugares; vazio = outro lugar / não sabe"),
    "lingua": ("Língua", "Língua das mensagens", ", ".join(LINGUAS.values())),
    "sexo": ("Sexo", "Sexo indicado pela pessoa", ", ".join(I.OPCOES["sexo"].values()) + ", " + I.NAO_DIZ),
    "faixa_etaria": ("Idade", "Faixa etária indicada pela pessoa", ", ".join(I.OPCOES["faixa_etaria"].values()) + ", " + I.NAO_DIZ),
    "profissao": ("Profissão / ocupação", "Profissão ou ocupação indicada pela pessoa", ", ".join(I.OPCOES["profissao"].values()) + ", " + I.NAO_DIZ),
    "consentimento": ("Aceitou em", "Quando marcou «Aceito receber alertas»", "data e hora"),
    "estado": ("Estado", "Se ainda recebe os alertas", ", ".join(ESTADOS.values())),
    "boas_vindas_utc": ("Boas-vindas enviadas em", "Quando recebeu a mensagem de boas-vindas", "data e hora; vazio = ainda não"),
    "envios": ("Alertas recebidos", "Quantos alertas e fins de alerta já recebeu", "número"),
    "ultimo_envio_utc": ("Último alerta em", "Quando recebeu o último alerta ou fim de alerta", "data e hora"),
    "removido_utc": ("Saiu em", "Quando pediu para deixar de receber", "data e hora"),
}
ORDEM = ["id", "criado_utc", "nome", "telefone", "lugar", "lingua", "sexo", "faixa_etaria", "profissao", "consentimento", "estado",
         "boas_vindas_utc", "envios", "ultimo_envio_utc", "removido_utc"]


def _data(texto: str):
    """ISO time in UTC -> Maputo time without zone (Excel has no time zones)."""
    if not texto:
        return None
    try:
        return pd.Timestamp(texto).tz_convert("Africa/Maputo").tz_localize(None).to_pydatetime()
    except (ValueError, TypeError):
        return None


def _valor(coluna: str, registo: dict):
    v = registo.get(coluna, "")
    if coluna in ("criado_utc", "consentimento", "boas_vindas_utc", "ultimo_envio_utc", "removido_utc"):
        return _data(v)
    if coluna == "telefone":
        return I.mostrar_telefone(v) if v else ""
    if coluna in I.OPCOES:
        return I.OPCOES[coluna].get(v, I.NAO_DIZ)
    if coluna == "lingua":
        return LINGUAS.get(v, v)
    if coluna == "estado":
        return ESTADOS.get(v, v)
    if coluna == "lugar":
        return v or "Outro lugar / não sabe"
    if coluna == "envios":
        return int(v or 0)
    return v


def _cabecalho(folha, linha: int, titulos: list[str]) -> None:
    for i, titulo in enumerate(titulos, start=1):
        celula = folha.cell(row=linha, column=i, value=titulo)
        celula.font, celula.fill = CABECALHO, FUNDO
        celula.alignment = Alignment(vertical="center", wrap_text=True)


def _larguras(folha, larguras: list[int]) -> None:
    for i, largura in enumerate(larguras, start=1):
        folha.column_dimensions[get_column_letter(i)].width = largura


def exportar(registos: list[dict], destino: Path, historico: list[dict] | None = None, onde: str = "") -> Path:
    livro = Workbook()

    # 1. one row per person
    folha = livro.active
    folha.title = "Subscritores"
    _cabecalho(folha, 1, [DICIONARIO[c][0] for c in ORDEM])
    for registo in registos:
        folha.append([_valor(c, registo) for c in ORDEM])
    for linha in folha.iter_rows(min_row=2):
        for celula in linha:
            celula.border = FINA
            if hasattr(celula.value, "year"):
                celula.number_format = "dd/mm/yyyy hh:mm"
    folha.freeze_panes = "B2"
    folha.auto_filter.ref = folha.dimensions
    folha.row_dimensions[1].height = 32
    _larguras(folha, [14, 17, 22, 19, 22, 11, 18, 17, 30, 17, 9, 17, 10, 17, 17])

    # 2. summary of the active sign-ups
    activos = I.activas(registos)
    resumo = livro.create_sheet("Resumo")
    resumo["A1"] = "Subscritores dos alertas no WhatsApp"
    resumo["A1"].font = Font(bold=True, size=14, color=TINTA)
    resumo["A2"] = f"Gerado em {pd.Timestamp.now(tz='Africa/Maputo'):%d/%m/%Y %H:%M} (hora de Maputo)" + (f" · base de dados: {onde}" if onde else "")
    resumo["A2"].font = Font(italic=True, color="5C6B66")
    totais = [("Inscrições activas", len(activos)), ("Pessoas que saíram", len(registos) - len(activos)),
              ("À espera das boas-vindas", sum(1 for r in activos if not r.get("boas_vindas_utc"))),
              ("Alertas enviados (soma de todas as pessoas)", sum(int(r.get("envios") or 0) for r in registos))]
    for i, (rotulo, valor) in enumerate(totais, start=4):
        resumo.cell(row=i, column=1, value=rotulo).fill = SUAVE
        resumo.cell(row=i, column=2, value=valor).font = Font(bold=True)
    linha = 4 + len(totais) + 1
    graficos = []
    for coluna, titulo in (("sexo", "Por sexo"), ("faixa_etaria", "Por idade"), ("profissao", "Por profissão"), ("lugar", "Por lugar onde vive"), ("lingua", "Por língua")):
        contagem = Counter(_valor(coluna, r) for r in activos)
        if coluna in I.OPCOES:                            # every answer appears, even with zero people, in the order of the form
            ordem = list(I.OPCOES[coluna].values()) + [I.NAO_DIZ]
            itens = [(nome, contagem.get(nome, 0)) for nome in ordem]
        else:
            itens = contagem.most_common()
        resumo.cell(row=linha, column=1, value=titulo).font = Font(bold=True, size=12, color=TINTA)
        _cabecalho(resumo, linha + 1, ["Resposta", "Pessoas", "%"])
        inicio = linha + 2
        for j, (nome, n) in enumerate(itens):
            resumo.cell(row=inicio + j, column=1, value=nome).border = FINA
            resumo.cell(row=inicio + j, column=2, value=n).border = FINA
            percentagem = resumo.cell(row=inicio + j, column=3, value=(n / len(activos)) if activos else 0)
            percentagem.number_format, percentagem.border = "0%", FINA
        if coluna in ("faixa_etaria", "profissao") and itens:
            graficos.append((titulo, inicio, inicio + len(itens) - 1))
        linha = inicio + len(itens) + 1
    _larguras(resumo, [44, 10, 8])
    for k, (titulo, primeira, ultima) in enumerate(graficos):
        grafico = BarChart()
        grafico.type, grafico.title, grafico.legend = "bar", titulo, None
        grafico.add_data(Reference(resumo, min_col=2, min_row=primeira, max_row=ultima), titles_from_data=False)
        grafico.set_categories(Reference(resumo, min_col=1, min_row=primeira, max_row=ultima))
        grafico.y_axis.majorGridlines = None
        grafico.series[0].graphicalProperties.solidFill = "0F766E"
        grafico.height, grafico.width = 7.5 + 0.45 * (ultima - primeira), 22
        resumo.add_chart(grafico, f"E{4 + k * 24}")

    # 3. what was sent
    envios = livro.create_sheet("Envios")
    _cabecalho(envios, 1, ["Data", "Tipo", "Nível", "Pessoas inscritas", "Mensagens enviadas", "Modo"])
    tipos = {"alerta": "Alerta", "fim": "Fim de alerta"}
    for h in historico or []:
        envios.append([_data(h.get("data_utc", "")), tipos.get(h.get("tipo"), h.get("tipo")), (h.get("nivel") or "").upper(), h.get("pessoas"), h.get("enviadas"),
                       {"api": "Automático (API)", "assistido": "Assistido (botões)"}.get(h.get("modo"), h.get("modo"))])
    for celula in envios["A"][1:]:
        celula.number_format = "dd/mm/yyyy hh:mm"
    envios.freeze_panes = "A2"
    _larguras(envios, [17, 15, 11, 17, 19, 20])
    if not historico:
        envios["A2"] = "Ainda não foi enviado nenhum alerta."

    # 4. what each column means
    dicionario = livro.create_sheet("Dicionário")
    _cabecalho(dicionario, 1, ["Coluna no Excel", "Coluna na base de dados", "O que quer dizer", "Valores possíveis"])
    for coluna in ORDEM:
        titulo, explicacao, valores = DICIONARIO[coluna]
        dicionario.append([titulo, coluna, explicacao, valores])
    for linha in dicionario.iter_rows(min_row=2):
        for celula in linha:
            celula.alignment, celula.border = Alignment(wrap_text=True, vertical="top"), FINA
    dicionario.append([])
    dicionario.append(["Atenção: este ficheiro tem números de telefone. É só para a equipa; não o partilhe nem o envie por email aberto."])
    _larguras(dicionario, [24, 20, 48, 60])

    for pagina in livro.worksheets:                       # printing: each sheet fits the width of an A4 page
        pagina.page_setup.orientation = "landscape" if pagina.title == "Subscritores" else "portrait"
        pagina.page_setup.paperSize = pagina.PAPERSIZE_A4
        pagina.page_setup.fitToWidth, pagina.page_setup.fitToHeight = 1, 0
        pagina.sheet_properties.pageSetUpPr.fitToPage = True
        pagina.print_title_rows = "1:1" if pagina.title in ("Subscritores", "Envios", "Dicionário") else None

    destino.parent.mkdir(parents=True, exist_ok=True)
    livro.save(destino)
    destino.chmod(0o600)
    return destino


def historico_de_envios() -> list[dict]:
    ficheiro = Path(__file__).resolve().parent / "dados" / "boletim" / "avisos_whatsapp.json"
    return json.loads(ficheiro.read_text()).get("historico", []) if ficheiro.exists() else []
