"""Alertas de cheia no WhatsApp para as pessoas inscritas na plataforma.

Corre todas as manhãs, depois do boletim (scripts/send_whatsapp_alerts.py, também chamado pelo
pipeline diário). Decide se há que avisar, escreve a mensagem de cada pessoa na língua dela e envia.

Quando se avisa
  * só com um boletim válido (nunca com dados antigos);
  * alerta LARANJA ou VERMELHO (o nível que metade ou mais dos cenários indica): mensagem de alerta;
  * de novo se o nível subir, ou como lembrete se o alerta durar (por defeito, de 2 em 2 dias);
  * quando o nível desce abaixo de laranja: mensagem de fim de alerta;
  * quem se inscreve recebe uma mensagem de boas-vindas (e o alerta, se houver um em curso).
Cada mensagem diz pelo menos dois lugares que podem alagar: o lugar da pessoa primeiro, se estiver
em risco, depois os que a água alcançou primeiro na cheia de 2026.

Como se envia
  * API oficial do WhatsApp (WhatsApp Business Cloud API, da Meta), quando WHATSAPP_TOKEN e
    WHATSAPP_PHONE_ID estão definidos. As mensagens usam modelos aprovados pela Meta (ver
    docs/alertas_whatsapp.md: os textos estão lá, prontos a submeter).
  * Envio assistido, quando a API ainda não está pronta: escreve uma página em
    data/private/caixa_de_saida/ com um botão por pessoa que abre o WhatsApp com a mensagem já
    escrita; alguém da equipa carrega em cada botão. Nunca nos servidores do GitHub (os números
    ficariam expostos), só no computador do projecto.

O registo do que foi enviado (dados/boletim/avisos_whatsapp.json) tem datas, níveis e quantidades,
nunca números de telefone.
"""

from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import quote

import pandas as pd

import inscricoes
from textos import TEXTOS

AQUI = Path(__file__).resolve().parent
DADOS = AQUI / "dados"
ESTADO = DADOS / "boletim" / "avisos_whatsapp.json"
CAIXA = inscricoes.RAIZ / "data" / "private" / "caixa_de_saida"
ORDEM = ["verde", "amarelo", "laranja", "vermelho"]
EMOJI = {"verde": "🟢", "amarelo": "🟡", "laranja": "🟠", "vermelho": "🔴"}
NIVEIS = {"pt": {"amarelo": "AMARELO", "laranja": "LARANJA", "vermelho": "VERMELHO", "verde": "VERDE"},
          "en": {"amarelo": "YELLOW", "laranja": "ORANGE", "vermelho": "RED", "verde": "GREEN"},
          "fr": {"amarelo": "JAUNE", "laranja": "ORANGE", "vermelho": "ROUGE", "verde": "VERTE"}}
CODIGO_META = {"pt": "pt_PT", "en": "en", "fr": "fr"}            # language codes of the approved templates

# The texts below are the WhatsApp templates. If one changes here, the template submitted to Meta must change too.
TEXTOS_MENSAGEM = {
    "alerta": {
        "pt": "⚠️ Eyes to Earth · ALERTA {nivel} de cheia no rio Incomáti, a partir de {dia}.\n📍 Lugares que podem alagar: {lugares}.\n✅ O que fazer: {conselho}\n"
              "ℹ️ Mais informação: {link}\nPara deixar de receber: {sair}\nSiga sempre as ordens do INGD e das autoridades.",
        "en": "⚠️ Eyes to Earth · {nivel} flood ALERT on the Incomati River, from {dia}.\n📍 Places that may flood: {lugares}.\n✅ What to do: {conselho}\n"
              "ℹ️ More information: {link}\nTo stop these messages: {sair}\nAlways follow the orders of INGD and the authorities.",
        "fr": "⚠️ Eyes to Earth · ALERTE {nivel} de crue sur le fleuve Incomati, à partir du {dia}.\n📍 Lieux qui peuvent être inondés : {lugares}.\n✅ Que faire : {conselho}\n"
              "ℹ️ Plus d'informations : {link}\nPour ne plus recevoir ces messages : {sair}\nSuivez toujours les ordres de l'INGD et des autorités."},
    "fim": {
        "pt": "🟢 Eyes to Earth · Fim do alerta de cheia no rio Incomáti ({data}). O boletim de hoje já não prevê cheia.\nMais informação: {link}\nContinue atento às autoridades.",
        "en": "🟢 Eyes to Earth · End of the flood alert on the Incomati River ({data}). Today's bulletin no longer forecasts a flood.\nMore information: {link}\nKeep listening to the authorities.",
        "fr": "🟢 Eyes to Earth · Fin de l'alerte de crue sur le fleuve Incomati ({data}). Le bulletin du jour ne prévoit plus de crue.\nPlus d'informations : {link}\nRestez attentifs aux autorités."},
    "boas_vindas": {
        "pt": "👋 Olá! Está inscrito nos alertas de cheia do Eyes to Earth para {lugar}. Só lhe escrevemos quando houver perigo de cheia no rio Incomáti (alerta laranja ou vermelho) "
              "e quando o perigo passar.\nPlataforma: {link}\nPara deixar de receber: {sair}\nObrigado!",
        "en": "👋 Hello! You are signed up for Eyes to Earth flood alerts for {lugar}. We only write when there is a danger of flooding on the Incomati River (orange or red alert) "
              "and when the danger is over.\nPlatform: {link}\nTo stop these messages: {sair}\nThank you!",
        "fr": "👋 Bonjour ! Vous êtes inscrit aux alertes de crue d'Eyes to Earth pour {lugar}. Nous n'écrivons qu'en cas de danger de crue sur le fleuve Incomati (alerte orange ou rouge) "
              "et quand le danger est passé.\nPlateforme : {link}\nPour ne plus recevoir ces messages : {sair}\nMerci !"},
}
PARAMETROS = {"alerta": ["nivel", "dia", "lugares", "conselho", "link", "sair"], "fim": ["data", "link"], "boas_vindas": ["lugar", "link", "sair"]}
# one extra piece of advice in the alert, chosen from the person's age group first, then occupation
DICAS = {
    "60_mais": {"pt": "Se precisar de ajuda para sair de casa, combine já com um vizinho ou familiar.",
                "en": "If you need help to leave home, arrange it now with a neighbour or relative.",
                "fr": "Si vous avez besoin d'aide pour quitter votre maison, organisez-le dès maintenant avec un voisin ou un proche."},
    "menos_18": {"pt": "Fique junto da sua família e siga as instruções dos adultos e das autoridades.",
                 "en": "Stay with your family and follow the instructions of adults and the authorities.",
                 "fr": "Restez avec votre famille et suivez les consignes des adultes et des autorités."},
    "agricultor": {"pt": "Leve o gado e guarde as sementes e a colheita em lugar alto.", "en": "Move livestock and store seeds and harvest in a high place.",
                   "fr": "Déplacez le bétail et mettez semences et récoltes en hauteur."},
    "pescador": {"pt": "Não vá ao rio de barco enquanto durar o alerta.", "en": "Do not go on the river by boat while the alert lasts.",
                 "fr": "N'allez pas sur le fleuve en bateau tant que l'alerte dure."},
    "comerciante": {"pt": "Guarde a mercadoria em lugar alto.", "en": "Store your goods in a high place.", "fr": "Mettez vos marchandises en hauteur."},
    "professor": {"pt": "Combine com a escola como avisar as famílias dos alunos.", "en": "Agree with the school how to warn the pupils' families.",
                  "fr": "Convenez avec l'école de la façon de prévenir les familles des élèves."},
    "transporte": {"pt": "Não atravesse estradas nem pontes cobertas de água.", "en": "Do not drive across roads or bridges covered by water.",
                   "fr": "Ne traversez pas les routes ni les ponts recouverts d'eau."},
    "lider": {"pt": "Partilhe este aviso com a sua comunidade.", "en": "Share this warning with your community.", "fr": "Partagez cet avis avec votre communauté."},
    "protecao_civil": {"pt": "Partilhe este aviso com a sua equipa e a comunidade.", "en": "Share this warning with your team and the community.",
                       "fr": "Partagez cet avis avec votre équipe et la communauté."},
}


def dica(pessoa: dict, lingua: str) -> str:
    for chave in (pessoa.get("faixa_etaria", ""), pessoa.get("profissao", "")):
        if chave in DICAS:
            return DICAS[chave][lingua]
    return ""


ONDE_VIVE = {"pt": "onde vive", "en": "where you live", "fr": "chez vous"}


def traduzir(texto: str, lingua: str) -> str:
    if lingua == "pt" or texto not in TEXTOS:
        return texto
    return TEXTOS[texto][0 if lingua == "en" else 1]


# ----------------------------------------------------------------------------- what to say
def ligacoes(lingua: str) -> tuple[str, str]:
    """Link to the platform (in the person's language) and to the page where one can stop the messages."""
    catalogo = json.loads((DADOS / "catalogo.json").read_text())
    base = (os.environ.get("ETE_APP_URL") or catalogo.get("aplicacao") or catalogo.get("pagina_simples") or "").rstrip("/")
    if not base:
        return "", ""
    if not catalogo.get("aplicacao") and not os.environ.get("ETE_APP_URL"):            # only the light page exists
        return base, base
    return f"{base}/?lang={lingua}", f"{base}/?p=alertas&lang={lingua}"


def lugares_em_risco(boletim: dict, lugares: pd.DataFrame, lugar_da_pessoa: str = "", minimo: int = 2, maximo: int = 3) -> list[str]:
    """At least two places that may flood: the bulletin's own list, completed with the places the water
    reached first in the 2026 flood; the person's place first when it is one of them."""
    nivel = boletim.get("nivel_maximo_provavel", "verde")
    nomes = list(boletim.get("lugares_que_alagam_primeiro") or []) + (list(boletim.get("lugares_em_cheia_grande") or []) if nivel == "vermelho" else [])
    categorias = ["alaga primeiro", "alaga em cheia grande"] if nivel == "vermelho" else ["alaga primeiro"]
    ordem = lugares[lugares["categoria"].isin(["alaga primeiro", "alaga em cheia grande"])].assign(
        _cat=lambda d: d["categoria"].map({"alaga primeiro": 0, "alaga em cheia grande": 1})).sort_values(["_cat", "primeira_data", "edificios"], ascending=[True, True, False])
    reserva = list(ordem.loc[ordem["categoria"].isin(categorias), "lugar"]) + list(ordem["lugar"])
    todos_em_risco = set(nomes) | set(ordem.loc[ordem["categoria"].isin(categorias), "lugar"])
    escolhidos = [lugar_da_pessoa] if lugar_da_pessoa and lugar_da_pessoa in todos_em_risco else []
    for nome in nomes + reserva:
        if nome not in escolhidos:
            escolhidos.append(nome)
        if len(escolhidos) >= max(minimo, maximo):
            break
    return escolhidos


def primeiro_dia(boletim: dict, nivel: str) -> str:
    for dia in boletim.get("previsao_diaria", []):
        if ORDEM.index(dia["alerta"]) >= ORDEM.index(nivel):
            return pd.Timestamp(dia["data"]).strftime("%d/%m")
    return pd.Timestamp(boletim.get("dia_mais_critico", datetime.now())).strftime("%d/%m")


def mensagem(tipo: str, pessoa: dict, boletim: dict, lugares: pd.DataFrame, conselhos: dict) -> tuple[str, list[str]]:
    """The message for one person: (full text, template parameters in order)."""
    lingua = pessoa.get("lingua") if pessoa.get("lingua") in CODIGO_META else "pt"
    link, sair = ligacoes(lingua)
    nivel = boletim.get("nivel_maximo_provavel", "verde")
    valores = {"link": link or "—", "sair": sair or "—", "emoji": EMOJI.get(nivel, "⚠️"), "nivel": NIVEIS[lingua].get(nivel, nivel.upper()),
               "dia": primeiro_dia(boletim, nivel), "data": pd.Timestamp(boletim.get("emitido_utc", datetime.now(timezone.utc))).strftime("%d/%m"),
               "conselho": traduzir(conselhos.get(nivel, ""), lingua), "lugar": pessoa.get("lugar") or "Marracuene"}
    if tipo == "alerta":
        extra = dica(pessoa, lingua)
        valores["conselho"] = f"{valores['conselho']} {extra}".strip()
        nomes = lugares_em_risco(boletim, lugares, pessoa.get("lugar", ""))
        valores["lugares"] = ", ".join(f"{n} ({ONDE_VIVE[lingua]})" if n == pessoa.get("lugar") else n for n in nomes)
    texto = TEXTOS_MENSAGEM[tipo][lingua].format(**valores)
    if not link:                                          # no public address yet: leave the link sentences out rather than show a dash
        texto = "\n".join(linha for linha in texto.split("\n") if not linha.rstrip().endswith("—"))
        texto = re.sub(r"\n{2,}", "\n", texto).strip()
    # template parameters cannot contain line breaks
    parametros = [" ".join(str(valores[p]).split()) for p in PARAMETROS[tipo]]
    return texto, parametros


# ----------------------------------------------------------------------------- when to say it
def ler_estado() -> dict:
    return json.loads(ESTADO.read_text()) if ESTADO.exists() else {"activo": False, "nivel": "", "enviado_utc": "", "historico": []}


def decidir(boletim: dict, estado: dict, niveis: list[str], lembrar_dias: float) -> tuple[str | None, str]:
    """('alerta' | 'fim' | None, reason)."""
    if not boletim.get("seguro_mostrar"):
        return None, "boletim inválido ou antigo: nada é enviado"
    nivel = boletim.get("nivel_maximo_provavel", "verde")
    if nivel in niveis:
        if not estado.get("activo"):
            return "alerta", f"novo alerta {nivel}"
        if ORDEM.index(nivel) > ORDEM.index(estado.get("nivel") or "verde"):
            return "alerta", f"o alerta subiu para {nivel}"
        idade = (datetime.now(timezone.utc) - datetime.fromisoformat(estado["enviado_utc"])).total_seconds() / 86400 if estado.get("enviado_utc") else 99
        if idade >= lembrar_dias:
            return "alerta", f"lembrete: alerta {nivel} continua"
        return None, f"alerta {nivel} já enviado há {idade:.1f} dias"
    if estado.get("activo"):
        return "fim", f"o nível desceu para {nivel}"
    return None, f"nível {nivel}: sem alerta"


# ----------------------------------------------------------------------------- how to send it
class EnvioAPI:
    """WhatsApp Business Cloud API (Meta): one approved template message per person."""

    def __init__(self, token: str, phone_id: str, versao: str = "v21.0", modelos: dict | None = None):
        import requests

        self.requests, self.url = requests, f"https://graph.facebook.com/{versao}/{phone_id}/messages"
        self.cabecalho = {"Authorization": f"Bearer {token}"}
        self.modelos = modelos or {"alerta": "ete_alerta_cheia", "fim": "ete_fim_alerta", "boas_vindas": "ete_boas_vindas"}
        self.modo = "api"

    def enviar(self, numero: str, tipo: str, lingua: str, texto: str, parametros: list[str]) -> tuple[bool, str]:
        corpo = {"messaging_product": "whatsapp", "to": numero, "type": "template",
                 "template": {"name": self.modelos[tipo], "language": {"code": CODIGO_META.get(lingua, "pt_PT")},
                              "components": [{"type": "body", "parameters": [{"type": "text", "text": p} for p in parametros]}]}}
        try:
            resposta = self.requests.post(self.url, headers=self.cabecalho, json=corpo, timeout=30)
        except Exception as erro:
            return False, type(erro).__name__
        if resposta.ok:
            return True, ""
        try:
            return False, resposta.json().get("error", {}).get("message", "")[:160]
        except ValueError:
            return False, f"HTTP {resposta.status_code}"

    def concluir(self) -> str:
        return ""


class EnvioAssistido:
    """No API yet: a page with one button per person that opens WhatsApp with the message written."""

    def __init__(self, pasta: Path = CAIXA):
        self.pasta, self.linhas, self.modo = pasta, [], "assistido"

    def enviar(self, numero: str, tipo: str, lingua: str, texto: str, parametros: list[str]) -> tuple[bool, str]:
        self.linhas.append((numero, tipo, texto))
        return True, ""

    def concluir(self) -> str:
        if not self.linhas:
            return ""
        self.pasta.mkdir(parents=True, exist_ok=True)
        ficheiro = self.pasta / f"{datetime.now():%Y-%m-%d_%H%M}_mensagens.html"
        cartoes = "".join(
            f"<div class='c'><div class='n'>{inscricoes.mostrar_telefone(n)} · {html.escape(tipo)}</div><pre>{html.escape(texto)}</pre>"
            f"<a href='https://wa.me/{n}?text={quote(texto)}' target='_blank'>Abrir no WhatsApp e enviar</a></div>" for n, tipo, texto in self.linhas)
        ficheiro.write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>ETE · mensagens para enviar</title>"
                            "<style>body{font-family:system-ui,sans-serif;background:#F7F3EA;color:#10231F;margin:0;padding:20px;max-width:720px;margin:auto}"
                            "h1{font-size:1.3rem}.c{background:#fff;border:1px solid #E8E1D2;border-radius:16px;padding:14px 16px;margin:12px 0}"
                            ".n{font-weight:700;margin-bottom:6px}pre{white-space:pre-wrap;font:inherit;background:#E9F7EF;border-radius:6px 16px 16px 16px;padding:10px 12px}"
                            "a{display:inline-block;background:#10231F;color:#fff;text-decoration:none;border-radius:999px;padding:9px 16px;font-weight:600}</style>"
                            f"<h1>Mensagens para enviar ({len(self.linhas)})</h1><p>Carregue em cada botão: o WhatsApp abre com a mensagem já escrita; confirme o envio. "
                            "Esta página tem números de telefone: não a partilhe e apague-a depois de enviar.</p>" + cartoes, encoding="utf-8")
        os.chmod(ficheiro, 0o600)
        return str(ficheiro)


def remetente():
    token, telefone = os.environ.get("WHATSAPP_TOKEN", ""), os.environ.get("WHATSAPP_PHONE_ID", "")
    if token and telefone:
        modelos = {"alerta": os.environ.get("ETE_WA_MODELO_ALERTA", "ete_alerta_cheia"), "fim": os.environ.get("ETE_WA_MODELO_FIM", "ete_fim_alerta"),
                   "boas_vindas": os.environ.get("ETE_WA_MODELO_BOAS_VINDAS", "ete_boas_vindas")}
        return EnvioAPI(token, telefone, os.environ.get("WHATSAPP_API_VERSION", "v21.0"), modelos)
    if os.environ.get("GITHUB_ACTIONS") == "true":
        return None                                       # never write phone numbers on a shared server
    return EnvioAssistido()


# ----------------------------------------------------------------------------- the daily run
def executar(niveis: list[str] | None = None, lembrar_dias: float = 2, loja=None, envio=None, boletim: dict | None = None, gravar_estado: bool = True) -> dict:
    """Decide, write and send. Returns a summary without any phone number."""
    import leitor

    niveis = niveis or ["laranja", "vermelho"]
    boletim = boletim or leitor.boletim()
    catalogo = json.loads((DADOS / "catalogo.json").read_text())
    conselhos = catalogo.get("conselhos", {})
    lugares = leitor.serie("lugares_por_ordem")
    estado = ler_estado()
    decisao, motivo = decidir(boletim, estado, niveis, lembrar_dias)
    resumo = {"decisao": decisao or "nada", "motivo": motivo, "enviadas": 0, "falharam": 0, "boas_vindas": 0, "modo": "", "ficheiro": "", "erros": []}
    envio = envio if envio is not None else remetente()
    if envio is None:
        resumo["modo"] = "não configurado"
        resumo["motivo"] += " · WhatsApp não configurado (faltam WHATSAPP_TOKEN e WHATSAPP_PHONE_ID)"
        return resumo
    resumo["modo"] = envio.modo
    loja = loja or inscricoes.loja()
    pessoas = inscricoes.activas(loja.listar())
    alerta_em_curso = decisao == "alerta" or (decisao is None and estado.get("activo") and boletim.get("seguro_mostrar"))

    for pessoa in pessoas:
        nova = not pessoa.get("boas_vindas_utc")
        if nova:                                          # a new person: welcome, plus the alert if one is under way (never an "end" they did not see start)
            tipos = ["boas_vindas"] + (["alerta"] if alerta_em_curso else [])
        else:
            tipos = [decisao] if decisao else []
        for tipo in tipos:
            texto, parametros = mensagem(tipo, pessoa, boletim, lugares, conselhos)
            ok, erro = envio.enviar(pessoa["telefone"], tipo, pessoa.get("lingua", "pt"), texto, parametros)
            if tipo == "boas_vindas":
                resumo["boas_vindas"] += ok
                if ok:
                    loja.actualizar(pessoa["id"], {"boas_vindas_utc": inscricoes.agora_utc()})
            else:
                resumo["enviadas" if ok else "falharam"] += 1
                if ok:                                    # per-person record: how many alerts and when the last one went out
                    envios = int(pessoa.get("envios") or 0) + 1
                    pessoa["envios"] = str(envios)
                    loja.actualizar(pessoa["id"], {"ultimo_envio_utc": inscricoes.agora_utc(), "envios": str(envios)})
            if not ok and erro and erro not in resumo["erros"]:
                resumo["erros"].append(erro)
    resumo["ficheiro"] = envio.concluir()

    # the state only moves on when something went out (if every message failed, try again tomorrow)
    if decisao and gravar_estado and (resumo["enviadas"] or not resumo["falharam"]):
        agora = inscricoes.agora_utc()
        novo = {"activo": decisao == "alerta", "nivel": boletim.get("nivel_maximo_provavel", "") if decisao == "alerta" else "", "enviado_utc": agora}
        historico = (estado.get("historico") or [])[-29:] + [{"data_utc": agora, "tipo": decisao, "nivel": boletim.get("nivel_maximo_provavel", ""),
                                                               "pessoas": len(pessoas), "enviadas": resumo["enviadas"], "modo": envio.modo}]
        ESTADO.write_text(json.dumps({**novo, "historico": historico}, indent=1, ensure_ascii=False))
    return resumo
