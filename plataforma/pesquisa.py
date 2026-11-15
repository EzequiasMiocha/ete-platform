"""A pesquisa da plataforma: os lugares e as perguntas mais comuns, numa só barra.

A barra (st.selectbox em app.py) mostra os temas e os lugares e filtra-os enquanto se escreve. Se a
pessoa escrever outra coisa e carregar em Enter, `procurar` encontra o que mais se parece com o texto,
sem ligar a acentos, maiúsculas nem pequenos erros: «agua» encontra «água», «satelite» encontra
«satélite», «machubu» encontra «Machubo».

Cada tema abre uma página numa secção (a âncora tem de existir na página, ver app.py).
"""

from __future__ import annotations

import difflib
import re
import unicodedata

# (chave, grupo, texto em português, página, secção, palavras que também o encontram, em PT, EN e FR)
TEMAS = [
    ("beber", "agua", "Posso beber a água do rio?", "agua", "conselhos",
     "beber bebe potavel consumir consumo segura seguro saude doenca diarreia colera drink drinking safe health boire potable sante"),
    ("tratar", "agua", "Como tratar a água em casa", "agua", "tratar",
     "tratar tratamento ferver fervura cloro lixivia certeza filtrar coar limpar desinfectar treat boil chlorine filter clean traiter bouillir chlore filtrer"),
    ("agua_hoje", "agua", "Como está a água do rio hoje?", "agua", "",
     "agua cor turva turbidez lama barro sedimentos qualidade hoje suja water colour color quality muddy today eau couleur qualite boue"),
    ("agua_semanas", "agua", "A cor da água nas próximas semanas", "agua", "previsao",
     "previsao semanas proximas futuro mes amanha forecast weeks next future prevision semaines prochaines"),
    ("agua_passado", "agua", "A água nos anos passados", "agua", "passado",
     "passado anos anteriores historico mapas meses antigamente past years history maps passe annees historique cartes"),
    ("cheia_dias", "cheias", "O rio vai alagar nos próximos 10 dias?", "cheias", "dez_dias",
     "cheia cheias alagar alagamento inundacao inundar enchente enchentes previsao alerta perigo dias flood flooding forecast alert danger crue inondation alerte"),
    ("caudal", "cheias", "O caudal do rio (vazão)", "cheias", "dez_dias",
     "caudal vazao volume nivel subir rio m3 quantidade flow discharge level debit niveau"),
    ("onde", "cheias", "Onde a água chega primeiro", "cheias", "lugares",
     "onde zona zonas aviso lugares bairros mapa mapas primeiro edificios casas where zones warning places map houses ou zones lieux carte maisons"),
    ("cores", "cheias", "O que fazer em cada nível de alerta", "cheias", "cores",
     "fazer verde amarelo laranja vermelho cores nivel niveis conselhos evacuar what to do green yellow orange red levels que faire vert jaune rouge niveaux"),
    ("satelite", "satelite", "Imagens de satélite: o rio visto do espaço", "cheias", "espaco",
     "satelite satelites imagens imagem fotografias fotos espaco radar sentinel antes depois satellite images photos space espace"),
    ("historico", "cheias", "Vinte anos de cheias do Incomáti", "cheias", "historico",
     "historico vinte anos passado 2000 2013 2023 2026 grandes cheias history twenty years past historique vingt ans"),
    ("alertas", "alertas", "Receber alertas no WhatsApp", "alertas", "",
     "whatsapp alertas alerta receber inscrever inscricao mensagem mensagens telefone numero sms avisar alerts subscribe message phone recevoir message telephone"),
    ("sair", "alertas", "Deixar de receber os alertas", "alertas", "sair",
     "sair cancelar parar deixar remover stop unsubscribe cancel arreter annuler"),
    ("curiosidades", "projecto", "Curiosidades: o rio e os satélites", "sobre", "curiosidades",
     "curiosidades curiosidade sabia factos ciencia satelites rio curiosities facts science curiosites science"),
    ("modelos", "projecto", "Os modelos de machine learning", "sobre", "modelos",
     "modelo modelos machine learning inteligencia artificial ia algoritmo treino testes models artificial intelligence ai modeles"),
    ("conta", "conta", "A minha conta: entrar ou criar conta", "conta", "",
     "conta entrar login senha registar registo criar utilizador perfil dados sessao account sign password register profile compte connexion mot passe inscrire profil"),
    ("perguntas", "projecto", "Perguntas frequentes", "sobre", "perguntas",
     "perguntas duvidas ajuda frequentes faq questions help aide"),
]
CHAVES = [t[0] for t in TEMAS]
POR_CHAVE = {t[0]: t for t in TEMAS}
_CURTAS = {"a", "o", "e", "de", "do", "da", "dos", "das", "em", "no", "na", "nos", "nas", "um", "uma", "que", "se", "eu", "meu", "minha", "por", "para", "com",
           "the", "of", "in", "is", "to", "my", "can", "la", "le", "les", "des", "du", "un", "une", "est", "et", "je", "mon", "ma"}


def normalizar(texto: str) -> str:
    """Minúsculas, sem acentos e sem pontuação: «Água?» -> «agua»."""
    texto = unicodedata.normalize("NFKD", str(texto))
    texto = "".join(c for c in texto if not unicodedata.combining(c)).lower()
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", texto)).strip()


def _palavras(texto: str) -> list[str]:
    return [p for p in normalizar(texto).split() if p not in _CURTAS and len(p) >= 2]


def _parecida(palavra: str, alvo: set[str]) -> bool:
    """A palavra está no alvo, começa uma palavra do alvo, ou tem um pequeno erro (só palavras de 4 letras ou mais)."""
    if palavra in alvo:
        return True
    if len(palavra) >= 4 and any(a.startswith(palavra) for a in alvo):
        return True
    return len(palavra) >= 5 and bool(difflib.get_close_matches(palavra, alvo, n=1, cutoff=0.8))


def _pontuar(texto: str, lugares: list[str], rotulos: dict[str, str] | None = None) -> list[tuple[float, str]]:
    """Every option that looks like the text, with points (100 = the exact name of a place), best first."""
    pedido = normalizar(texto)
    palavras = _palavras(texto)
    if not pedido:
        return []
    achados: list[tuple[float, str]] = []
    for nome in lugares:
        n = normalizar(nome)
        if not n:
            continue
        do_nome = set(n.split())
        if n == pedido:
            pontos = 100.0
        elif n.startswith(pedido) or (len(pedido) >= 3 and pedido in n):
            pontos = 85.0
        elif any(len(p) >= 4 and _parecida(p, do_nome) for p in palavras):       # the name among other words: "machubo cheia"
            pontos = 70.0
        else:
            semelhanca = difflib.SequenceMatcher(None, pedido, n).ratio()
            pontos = 70.0 * semelhanca if semelhanca >= 0.78 else 0.0
        if pontos:
            achados.append((pontos, f"lugar:{nome}"))
    for chave, _, rotulo, _, _, extra in TEMAS:
        do_rotulo, de_mais = set(_palavras(rotulo + " " + (rotulos or {}).get(chave, ""))), set(_palavras(extra))
        pontos = 0.0
        for p in palavras:
            pontos += 16 if p in do_rotulo else 12 if p in de_mais else 8 if _parecida(p, do_rotulo | de_mais) else 0
        if pontos:
            achados.append((40.0 + pontos, f"tema:{chave}"))
    achados.sort(key=lambda a: -a[0])
    vistos, saida = set(), []
    for pontos, opcao in achados:
        if opcao not in vistos:
            vistos.add(opcao)
            saida.append((pontos, opcao))
    return saida


def procurar(texto: str, lugares: list[str], rotulos: dict[str, str] | None = None, maximo: int = 6) -> list[str]:
    """The options of the bar that look most like a free text, best first: "lugar:<nome>" or "tema:<chave>".
    `rotulos` are the texts of the topics in the reader's language."""
    return [opcao for _, opcao in _pontuar(texto, lugares, rotulos)[:maximo]]


def decidir(texto: str, lugares: list[str], rotulos: dict[str, str] | None = None) -> str | None:
    """Open the result at once when there is no doubt: the exact name of a place, a single result, or one clearly
    better than the next (a whole question such as «posso beber agua?»). Otherwise None: the page lists them."""
    achados = _pontuar(texto, lugares, rotulos)
    if not achados:
        return None
    if achados[0][0] >= 100 or len(achados) == 1 or achados[0][0] - achados[1][0] >= 8:
        return achados[0][1]
    return None
