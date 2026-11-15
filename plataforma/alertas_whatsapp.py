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
NIVEIS = {"pt": {"amarelo": "AMARELO", "laranja": "LARANJA", "vermelho": "VERMELHO", "verde": "VERDE"},
          "en": {"amarelo": "YELLOW", "laranja": "ORANGE", "vermelho": "RED", "verde": "GREEN"},
          "fr": {"amarelo": "JAUNE", "laranja": "ORANGE", "vermelho": "ROUGE", "verde": "VERTE"}}
CODIGO_META = {"pt": "pt_PT", "en": "en", "fr": "fr"}            # language codes of the approved templates

# The texts below are the WhatsApp templates. If one changes here, the template submitted to Meta must change too.
TEXTOS_MENSAGEM = {
    "alerta": {
        "pt": "Atenção, {nome}: ALERTA {nivel} de cheia no rio Incomáti, a partir de {dia}.\n\nLugares que podem alagar: {lugares}.\nO que fazer: {conselho}\n"
              "Próximos 10 dias: {linha_cheia}.\nÁgua do rio: {agua}\n\nSiga sempre as ordens do INGD e das autoridades. Detalhes e mapa na plataforma.",
        "en": "Attention, {nome}: FLOOD ALERT {nivel} on the Incomati River, from {dia}.\n\nPlaces that may flood: {lugares}.\nWhat to do: {conselho}\n"
              "Next 10 days: {linha_cheia}.\nRiver water: {agua}\n\nAlways follow the orders of INGD and the authorities. Details and map on the platform.",
        "fr": "Attention, {nome} : ALERTE {nivel} de crue sur le fleuve Incomati, à partir du {dia}.\n\nLieux qui peuvent être inondés : {lugares}.\nQue faire : {conselho}\n"
              "10 prochains jours : {linha_cheia}.\nEau du fleuve : {agua}\n\nSuivez toujours les ordres de l'INGD et des autorités. Détails et carte sur la plateforme."},
    "fim": {
        "pt": "Boas notícias, {nome}: terminou o alerta de cheia no rio Incomáti ({data}). O boletim de hoje já não prevê cheia.\n\nÁgua do rio: {agua}\n"
              "Depois de uma cheia a água fica mais suja durante semanas: trate-a sempre antes de beber.\n\nContinue atento às autoridades.",
        "en": "Good news, {nome}: the flood alert on the Incomati River has ended ({data}). Today's bulletin no longer forecasts a flood.\n\nRiver water: {agua}\n"
              "After a flood the water stays dirtier for weeks: always treat it before drinking.\n\nKeep listening to the authorities.",
        "fr": "Bonne nouvelle, {nome} : l'alerte de crue sur le fleuve Incomati est terminée ({data}). Le bulletin du jour ne prévoit plus de crue.\n\nEau du fleuve : {agua}\n"
              "Après une crue, l'eau reste plus sale pendant des semaines : traitez-la toujours avant de la boire.\n\nRestez attentifs aux autorités."},
    "boas_vindas": {
        "pt": "Olá, {nome}! A sua inscrição nos alertas do rio Incomáti para {lugar} está feita.\n\nCheias nos próximos 10 dias: {cheia}\nÁgua do rio em Marracuene: {agua}\n"
              "{pessoal}\n\nVamos escrever-lhe sempre que houver perigo de cheia, e quando o perigo passar. Para deixar de receber, use o botão em baixo.",
        "en": "Hello, {nome}! You are now signed up for the Incomati River alerts for {lugar}.\n\nFloods in the next 10 days: {cheia}\nRiver water at Marracuene: {agua}\n"
              "{pessoal}\n\nWe will write to you whenever there is a danger of flooding, and when the danger is over. To stop these messages, use the button below.",
        "fr": "Bonjour, {nome} ! Votre inscription aux alertes du fleuve Incomati pour {lugar} est faite.\n\nCrues dans les 10 prochains jours : {cheia}\nEau du fleuve à Marracuene : {agua}\n"
              "{pessoal}\n\nNous vous écrirons à chaque danger de crue, et quand le danger sera passé. Pour ne plus recevoir ces messages, utilisez le bouton ci-dessous."},
}
PARAMETROS = {"alerta": ["nome", "nivel", "dia", "lugares", "conselho", "linha_cheia", "agua"], "fim": ["nome", "data", "agua"],
              "boas_vindas": ["nome", "lugar", "cheia", "agua", "pessoal"]}
# Every message speaks to the person by the full name given at sign-up. For someone who signed up before the name
# was asked (a template parameter can never be empty):
SEM_NOME = {"pt": "amigo(a)", "en": "friend", "fr": "ami(e)"}
# the footer and the two buttons of every template (approved together with the text)
RODAPE = {"pt": "Eyes to Earth · não substitui os avisos do INGD", "en": "Eyes to Earth · does not replace INGD warnings",
          "fr": "Eyes to Earth · ne remplace pas les alertes de l'INGD"}
BOTOES = {"pt": ("Ver a previsão completa", "Deixar de receber"), "en": ("See the full forecast", "Stop these messages"),
          "fr": ("Voir la prévision complète", "Ne plus recevoir")}
# the next ten days in words, without symbols: days in a row with the same level make one period
PERIODO = {"pt": ("{nome} até {fim}", "{nome} de {inicio} a {fim}", "{nome} a {dia}"),
           "en": ("{nome} until {fim}", "{nome} from {inicio} to {fim}", "{nome} on {dia}"),
           "fr": ("{nome} jusqu'au {fim}", "{nome} du {inicio} au {fim}", "{nome} le {dia}")}
CATEGORIAS_DO_LUGAR = {
    "alaga primeiro": {"pt": "{lugar} foi dos primeiros lugares a alagar na cheia de 2026.", "en": "{lugar} was among the first places to flood in 2026.",
                       "fr": "{lugar} a été parmi les premiers lieux inondés en 2026."},
    "alaga em cheia grande": {"pt": "{lugar} alagou na cheia grande de 2026.", "en": "{lugar} flooded in the big flood of 2026.", "fr": "{lugar} a été inondé lors de la grande crue de 2026."},
    "na margem da cheia": {"pt": "{lugar} ficou na margem da cheia de 2026.", "en": "{lugar} was at the edge of the 2026 flood.", "fr": "{lugar} était au bord de la crue de 2026."},
    "fora das zonas de aviso": {"pt": "{lugar} ficou fora das zonas de aviso em 2026.", "en": "{lugar} was outside the warning zones in 2026.",
                                "fr": "{lugar} était hors des zones d'alerte en 2026."},
}
SE_HOUVER_ALERTA = {"pt": "Se houver alerta: {dica}", "en": "If there is an alert: {dica}", "fr": "En cas d'alerte : {dica}"}
SEM_PERFIL = {"pt": "Guarde este número: é por aqui que avisamos.", "en": "Save this number: this is where we will warn you.",
              "fr": "Enregistrez ce numéro : c'est par ici que nous vous préviendrons."}
BOTAO_SAIR = {"pt": " Para deixar de receber, use o botão em baixo.", "en": " To stop these messages, use the button below.",
              "fr": " Pour ne plus recevoir ces messages, utilisez le bouton ci-dessous."}           # only true in the approved template, which has the buttons
LIGACOES_TEXTO = {"pt": "Mais detalhes e o mapa: {link}\nPara deixar de receber: {sair}", "en": "More details and the map: {link}\nTo stop these messages: {sair}",
                  "fr": "Plus de détails et la carte : {link}\nPour ne plus recevoir ces messages : {sair}"}
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
def _do_lugar(lugar: str) -> str:
    """The part of an address that opens the page of a place on the platform (nothing when no place was chosen)."""
    from urllib.parse import quote

    return f"p=zona&lugar={quote(lugar)}&" if lugar else ""


def ligacoes(lingua: str, lugar: str = "") -> tuple[str, str]:
    """Link to the platform (in the person's language; the page of their place, if they chose one) and to the
    page where one can stop the messages."""
    catalogo = json.loads((DADOS / "catalogo.json").read_text())
    base = (os.environ.get("ETE_APP_URL") or catalogo.get("aplicacao") or catalogo.get("pagina_simples") or "").rstrip("/")
    if not base:
        return "", ""
    if not catalogo.get("aplicacao") and not os.environ.get("ETE_APP_URL"):            # only the light page exists
        return base, base
    return f"{base}/?{_do_lugar(lugar)}lang={lingua}", f"{base}/?p=alertas&lang={lingua}"


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


def passos_de_cor() -> list[float]:
    """The four limits of the colour steps of the maps (the same everywhere: dados/modelos/mapa_cor_modelo.npz)."""
    import numpy as np

    ficheiro = DADOS / "modelos" / "mapa_cor_modelo.npz"
    return [float(v) for v in np.load(ficheiro)["steps"]] if ficheiro.exists() else [-0.099, -0.058, -0.030, 0.002]


def prevista_da_cor() -> pd.DataFrame | None:
    """The 30-day forecast of the water colour at Marracuene (boletim/cor_prevista.csv), or None."""
    ficheiro = DADOS / "boletim" / "cor_prevista.csv"
    if not ficheiro.exists():
        return None
    tabela = pd.read_csv(ficheiro, index_col=0, parse_dates=True)
    return tabela if len(tabela) else None


def periodos(serie: pd.Series, nomes: dict, lingua: str) -> str:
    """Days in a row with the same value, in words: «verde até 18/11, laranja de 19/11 a 24/11»."""
    from itertools import groupby

    ate, de_a, so = PERIODO.get(lingua, PERIODO["pt"])
    blocos = []
    for valor, grupo in groupby(serie.items(), key=lambda par: par[1]):
        datas = [d for d, _ in grupo]
        blocos.append((nomes.get(valor, str(valor)), datas[0], datas[-1]))
    partes = []
    for n, (nome, inicio, fim) in enumerate(blocos):
        if n == 0:
            partes.append(ate.format(nome=nome, fim=f"{fim:%d/%m}"))
        elif inicio == fim:
            partes.append(so.format(nome=nome, dia=f"{inicio:%d/%m}"))
        else:
            partes.append(de_a.format(nome=nome, inicio=f"{inicio:%d/%m}", fim=f"{fim:%d/%m}"))
    return ", ".join(partes)


def situacao(boletim: dict, prevista: pd.DataFrame | None, lingua: str) -> dict:
    """The next 10 days in words (the card that goes with the message shows them in colour):
    cheia (level, until when, what it means, the flow, and the periods when the level changes),
    linha_cheia (the periods alone), agua (the colour of the water and the advice)."""
    import cartao_whatsapp as C

    tx = C.TEXTOS.get(lingua, C.TEXTOS["pt"])
    dias = C.dias(boletim, prevista)
    if not boletim.get("seguro_mostrar") or dias.empty:
        return {"cheia": tx["indisponivel"], "linha_cheia": tx["indisponivel"], "agua": tx["beber"]}
    nivel = boletim.get("nivel_maximo_provavel", "verde")
    nomes = {k: v.lower() for k, v in tx["niveis"].items()}
    linha_cheia = periodos(dias["alerta"], nomes, lingua)
    caudal = {"pt": "caudal de {a} a {b} m³/s", "en": "flow {a} to {b} m³/s", "fr": "débit de {a} à {b} m³/s"}[lingua].format(
        a=f"{dias['caudal_mediana_m3s'].min():.0f}", b=f"{dias['caudal_mediana_m3s'].max():.0f}")
    ate = {"pt": "até", "en": "until", "fr": "jusqu'au"}[lingua]
    cheia = f"{tx['niveis'][nivel].lower()} {ate} {dias.index[-1]:%d/%m}, {tx['frases'][nivel].lower()} ({caudal})"
    if dias["alerta"].nunique() > 1:                     # the level changes: say when
        cheia += f": {linha_cheia}"
    cheia += "."
    agua = tx["beber"]
    if "indice_agua" in dias and dias["indice_agua"].notna().any():
        geral = C.degrau(float(dias["indice_agua"].mean()), passos_de_cor())
        agua = f"{tx['agua_frases'][geral].lower()}. {tx['beber']}"
    return {"cheia": cheia, "linha_cheia": linha_cheia, "agua": agua}


def pessoal(pessoa: dict, lugares: pd.DataFrame, lingua: str) -> str:
    """What the 2026 flood did to the person's place, and the advice for their age or occupation."""
    partes = []
    lugar = pessoa.get("lugar") or ""
    if lugar and lugares is not None and len(lugares) and lugar in set(lugares["lugar"]):
        categoria = lugares.loc[lugares["lugar"] == lugar, "categoria"].iloc[0]
        if categoria in CATEGORIAS_DO_LUGAR:
            partes.append(CATEGORIAS_DO_LUGAR[categoria][lingua].format(lugar=lugar))
    extra = dica(pessoa, lingua)
    if extra:
        partes.append(SE_HOUVER_ALERTA[lingua].format(dica=extra[:1].lower() + extra[1:]))
    return " ".join(partes) or SEM_PERFIL[lingua]


def sufixos(lingua: str, lugar: str = "") -> list[str]:
    """The end of the two button addresses: the platform (the page of the person's place, if they chose one)
    and the page to stop the messages. The approved templates take any ending (https://.../{{1}})."""
    return [f"?{_do_lugar(lugar)}lang={lingua}" if lugar else f"?p=inicio&lang={lingua}", f"?p=alertas&lang={lingua}"]


def mensagem(tipo: str, pessoa: dict, boletim: dict, lugares: pd.DataFrame, conselhos: dict, prevista: pd.DataFrame | None = None,
             como_no_modelo: bool = False) -> tuple[str, list[str]]:
    """The message for one person: (full text, with the links at the end, for sending by hand; template
    parameters in order, for the approved template, whose buttons carry the links). With
    `como_no_modelo` the text is the one the approved template shows (buttons instead of links)."""
    lingua = pessoa.get("lingua") if pessoa.get("lingua") in CODIGO_META else "pt"
    link, sair = ligacoes(lingua, pessoa.get("lugar") or "")
    nivel = boletim.get("nivel_maximo_provavel", "verde")
    nome = " ".join(str(pessoa.get("nome") or "").split())[:60] or SEM_NOME[lingua]
    valores = {"nome": nome, "nivel": NIVEIS[lingua].get(nivel, nivel.upper()), "dia": primeiro_dia(boletim, nivel), "lugar": pessoa.get("lugar") or "Marracuene",
               "data": pd.Timestamp(boletim.get("emitido_utc", datetime.now(timezone.utc))).strftime("%d/%m"),
               "conselho": traduzir(conselhos.get(nivel, ""), lingua), **situacao(boletim, prevista, lingua)}
    if tipo == "alerta":
        extra = dica(pessoa, lingua)
        valores["conselho"] = f"{valores['conselho']} {extra}".strip()
        nomes = lugares_em_risco(boletim, lugares, pessoa.get("lugar", ""))
        valores["lugares"] = ", ".join(f"{n} ({ONDE_VIVE[lingua]})" if n == pessoa.get("lugar") else n for n in nomes)
    if tipo == "boas_vindas":
        valores["pessoal"] = pessoal(pessoa, lugares, lingua)
    texto = TEXTOS_MENSAGEM[tipo][lingua].format(**valores)
    if link and not como_no_modelo:                       # sent by hand there are no buttons: the links go at the end
        texto = texto.replace(BOTAO_SAIR[lingua], "") + "\n\n" + LIGACOES_TEXTO[lingua].format(link=link, sair=sair)
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
    """WhatsApp Business Cloud API (Meta): one approved template message per person, with the situation
    card as header image and two link buttons (the platform; stop the messages)."""

    def __init__(self, token: str, phone_id: str, versao: str = "v21.0", modelos: dict | None = None):
        import requests

        self.requests, self.base = requests, f"https://graph.facebook.com/{versao}/{phone_id}"
        self.url = self.base + "/messages"
        self.cabecalho = {"Authorization": f"Bearer {token}"}
        self.modelos = modelos or {"alerta": "ete_alerta_cheia_v2", "fim": "ete_fim_alerta_v2", "boas_vindas": "ete_boas_vindas_v2"}
        self.modo = "api"
        self._imagens = {}

    def carregar_imagem(self, png: bytes, chave: str) -> str | None:
        """Send the card to Meta once (it keeps it 30 days) and remember its id for this run."""
        if chave in self._imagens:
            return self._imagens[chave]
        try:
            resposta = self.requests.post(self.base + "/media", headers=self.cabecalho, files={"file": ("situacao.png", png, "image/png")},
                                          data={"messaging_product": "whatsapp", "type": "image/png"}, timeout=60)
            self._imagens[chave] = resposta.json().get("id") if resposta.ok else None
        except Exception:
            self._imagens[chave] = None
        return self._imagens[chave]

    def enviar(self, numero: str, tipo: str, lingua: str, texto: str, parametros: list[str], imagem: bytes | None = None,
               chave_imagem: str = "", botoes: list[str] | None = None) -> tuple[bool, str]:
        componentes = []
        imagem_id = self.carregar_imagem(imagem, chave_imagem or lingua) if imagem else None
        if imagem_id:
            componentes.append({"type": "header", "parameters": [{"type": "image", "image": {"id": imagem_id}}]})
        componentes.append({"type": "body", "parameters": [{"type": "text", "text": p} for p in parametros]})
        for i, sufixo in enumerate(botoes or []):
            componentes.append({"type": "button", "sub_type": "url", "index": str(i), "parameters": [{"type": "text", "text": sufixo}]})
        corpo = {"messaging_product": "whatsapp", "to": numero, "type": "template",
                 "template": {"name": self.modelos[tipo], "language": {"code": CODIGO_META.get(lingua, "pt_PT")}, "components": componentes}}
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
    """No API yet: a page with one button per person that opens WhatsApp with the message written,
    and the situation card beside it (to attach by hand: a link cannot carry a picture)."""

    def __init__(self, pasta: Path = CAIXA):
        self.pasta, self.linhas, self.modo = pasta, [], "assistido"

    def enviar(self, numero: str, tipo: str, lingua: str, texto: str, parametros: list[str], imagem: bytes | None = None,
               chave_imagem: str = "", botoes: list[str] | None = None) -> tuple[bool, str]:
        self.linhas.append((numero, tipo, texto, imagem))
        return True, ""

    def concluir(self) -> str:
        import base64

        if not self.linhas:
            return ""
        self.pasta.mkdir(parents=True, exist_ok=True)
        ficheiro = self.pasta / f"{datetime.now():%Y-%m-%d_%H%M}_mensagens.html"
        imagem = lambda png: (f"<img src='data:image/png;base64,{base64.b64encode(png).decode()}' alt='cartão'>"
                              "<div class='d'>Guarde esta imagem e envie-a primeiro, depois a mensagem.</div>") if png else ""
        cartoes = "".join(
            f"<div class='c'><div class='n'>{inscricoes.mostrar_telefone(n)} · {html.escape(tipo)}</div>{imagem(png)}<pre>{html.escape(texto)}</pre>"
            f"<a href='https://wa.me/{n}?text={quote(texto)}' target='_blank'>Abrir no WhatsApp e enviar</a></div>" for n, tipo, texto, png in self.linhas)
        ficheiro.write_text("<!doctype html><meta charset='utf-8'><meta name='viewport' content='width=device-width,initial-scale=1'><title>ETE · mensagens para enviar</title>"
                            "<style>body{font-family:system-ui,sans-serif;background:#F7F3EA;color:#10231F;margin:0;padding:20px;max-width:720px;margin:auto}"
                            "h1{font-size:1.3rem}.c{background:#fff;border:1px solid #E8E1D2;border-radius:16px;padding:14px 16px;margin:12px 0}"
                            ".n{font-weight:700;margin-bottom:6px}img{width:100%;border-radius:10px;border:1px solid #E8E1D2}.d{font-size:.8rem;color:#5C6B66;margin:4px 0 8px}"
                            "pre{white-space:pre-wrap;font:inherit;background:#E9F7EF;border-radius:6px 16px 16px 16px;padding:10px 12px}"
                            "a{display:inline-block;background:#10231F;color:#fff;text-decoration:none;border-radius:999px;padding:9px 16px;font-weight:600}</style>"
                            f"<h1>Mensagens para enviar ({len(self.linhas)})</h1><p>Carregue em cada botão: o WhatsApp abre com a mensagem já escrita; confirme o envio. "
                            "Esta página tem números de telefone: não a partilhe e apague-a depois de enviar.</p>" + cartoes, encoding="utf-8")
        os.chmod(ficheiro, 0o600)
        return str(ficheiro)


def cartao(boletim: dict, prevista: pd.DataFrame | None, lingua: str) -> bytes | None:
    """The situation card of the day in a language (None if it cannot be drawn: the text goes alone)."""
    try:
        import cartao_whatsapp as C

        link, _ = ligacoes(lingua)
        return C.desenhar(boletim, prevista, passos_de_cor(), lingua, link.split("/?")[0] if link else "")
    except Exception:
        return None


def remetente():
    token, telefone = os.environ.get("WHATSAPP_TOKEN", ""), os.environ.get("WHATSAPP_PHONE_ID", "")
    if token and telefone:
        modelos = {"alerta": os.environ.get("ETE_WA_MODELO_ALERTA", "ete_alerta_cheia_v2"), "fim": os.environ.get("ETE_WA_MODELO_FIM", "ete_fim_alerta_v2"),
                   "boas_vindas": os.environ.get("ETE_WA_MODELO_BOAS_VINDAS", "ete_boas_vindas_v2")}
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
    prevista = prevista_da_cor()
    cartoes = {}                                          # one card per language, drawn once for everybody

    def cartao_de(lingua):
        if lingua not in cartoes:
            cartoes[lingua] = cartao(boletim, prevista, lingua)
        return cartoes[lingua]

    for pessoa in pessoas:
        nova = not pessoa.get("boas_vindas_utc")
        if nova:                                          # a new person: welcome, plus the alert if one is under way (never an "end" they did not see start)
            tipos = ["boas_vindas"] + (["alerta"] if alerta_em_curso else [])
        else:
            tipos = [decisao] if decisao else []
        for tipo in tipos:
            lingua = pessoa.get("lingua") if pessoa.get("lingua") in CODIGO_META else "pt"
            texto, parametros = mensagem(tipo, pessoa, boletim, lugares, conselhos, prevista)
            ok, erro = envio.enviar(pessoa["telefone"], tipo, lingua, texto, parametros, imagem=cartao_de(lingua), chave_imagem=f"{lingua}-{boletim.get('emitido_utc', '')}",
                                    botoes=sufixos(lingua, pessoa.get("lugar") or ""))
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


# ----------------------------------------------------------------------------- the welcome, at once
def boas_vindas_agora(numero: str, loja=None, envio=None, boletim: dict | None = None) -> tuple[bool, str]:
    """Send the welcome (with the situation of the next 10 days) to someone who has just signed up.
    Only through the official API: by hand, or with WhatsApp not configured, the daily run sends it.
    Returns (sent, reason); never writes the phone number anywhere."""
    import leitor

    envio = envio if envio is not None else remetente()
    if not isinstance(envio, EnvioAPI) and getattr(envio, "modo", "") != "teste":
        return False, "não configurado"
    loja = loja or inscricoes.loja()
    pessoa = next((p for p in inscricoes.activas(loja.listar()) if p["telefone"] == numero), None)
    if pessoa is None or pessoa.get("boas_vindas_utc"):
        return False, "já recebeu" if pessoa else "não encontrado"
    boletim = boletim or leitor.boletim()
    catalogo = json.loads((DADOS / "catalogo.json").read_text())
    prevista = prevista_da_cor()
    lingua = pessoa.get("lingua") if pessoa.get("lingua") in CODIGO_META else "pt"
    texto, parametros = mensagem("boas_vindas", pessoa, boletim, leitor.serie("lugares_por_ordem"), catalogo.get("conselhos", {}), prevista)
    ok, erro = envio.enviar(numero, "boas_vindas", lingua, texto, parametros, imagem=cartao(boletim, prevista, lingua),
                            chave_imagem=f"{lingua}-{boletim.get('emitido_utc', '')}", botoes=sufixos(lingua, pessoa.get("lugar") or ""))
    if ok:
        loja.actualizar(pessoa["id"], {"boas_vindas_utc": inscricoes.agora_utc()})
    return ok, erro
