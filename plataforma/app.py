"""Plataforma ETE: qualidade da água e cheias do rio Incomáti, Marracuene.

    pip install -r plataforma/requirements.txt
    cd plataforma && streamlit run app.py

Estrutura
  app.py       páginas e navegação (este ficheiro)
  tema.py      sistema de desenho: paleta, tipografia, barras do topo, cartões, tabelas, botões de anterior e seguinte
  graficos.py  gráficos
  idioma.py    línguas (português, inglês, francês), datas e números; as traduções estão em textos.py
  leitor.py    leitura do pacote de dados `dados/`
  static/      logótipos (feitos por scripts/build_platform_logos.py)

Princípios
  * Só lê o pacote `dados/`: não precisa dos dados do projecto, do Earth Engine nem dos modelos.
  * Segura por defeito: sem um boletim válido das últimas 36 horas, mostra "previsão
    indisponível" e nunca um nível de alerta.
  * Leve por defeito: os mapas aparecem como imagens pequenas; o mapa interactivo só é
    carregado quando a pessoa o pede.
  * Cada secção está protegida: se uma falhar, o resto da página aparece na mesma.
  * Escrita em português; cada texto passa por t() e aparece na língua escolhida (PT, EN, FR).
"""

import importlib
import json
import secrets
from pathlib import Path

import pandas as pd
import streamlit as st

import textos
import idioma as L
import inscricoes
import contas
import alertas_whatsapp
import conselhos
import curiosidades
import pesquisa
import graficos as G
import leitor
import tema as T

# A running server keeps the helper modules it first loaded. When one of them changes on disk it
# is loaded again here (translations first), so an update never leaves the app calling a function
# the old copy lacks.
# The modules are listed so that each comes after the ones it uses: once one is reloaded, all the
# following ones are reloaded too, so none keeps pieces of an old copy (for example translations).
_recarregar = False
for _modulo in (textos, L, inscricoes, contas, alertas_whatsapp, conselhos, curiosidades, pesquisa, T, G):
    _alterado = Path(_modulo.__file__).stat().st_mtime
    if _recarregar or getattr(_modulo, "_carregado_em", None) != _alterado:
        importlib.reload(_modulo)
        _recarregar = True
    _modulo._carregado_em = _alterado
t = L.t

if st.session_state.get("lingua") not in L.LINGUAS:           # first visit: honour a shared address such as ?lang=en
    st.session_state["lingua"] = st.query_params.get("lang", "pt") if st.query_params.get("lang") in L.LINGUAS else "pt"
if st.session_state.get("_lingua_da_conta") in L.LINGUAS:   # an account that has just signed in, or changed its language
    st.session_state["lingua"] = st.session_state.pop("_lingua_da_conta")
st.set_page_config(page_title=t("Eyes to Earth · Qualidade da água e cheias do Incomáti"), page_icon=str(Path(__file__).parent / "static" / "ete_icone.png"),
                   layout="wide", initial_sidebar_state="collapsed")
T.html(T.CSS)

# Five pages, each read from top to bottom without tabs: the answer of the day, the two objectives of the project
# (the water and the floods), the alerts on WhatsApp and the project itself.
PAGINAS = {"inicio": "Início", "agua": "Qualidade da água", "cheias": "Cheias", "alertas": "Alertas", "sobre": "O projecto"}
# The bar at the bottom of phones: the same five pages, with an icon each
MOVEL = {"inicio": ("home", "Início"), "agua": ("water_drop", "Água"), "cheias": ("flood", "Cheias"), "alertas": ("notifications_active", "Alertas"), "sobre": ("info", "Projecto")}
# A sixth page, "zona", is everything about one place; it is opened by the search bar (and by shared links ?p=zona&lugar=...),
# so it has no place in the bars.
# Pages that no longer exist, so that old links and shared addresses still work: where their content is now
ANTIGAS = {"conselhos": "agua", "mapa": "cheias", "lugares": "cheias", "historico": "cheias", "modelos": "sobre", "projecto": "sobre", "mais": "inicio"}
CORES_LUGARES = {"alaga primeiro": "#7b241c", "alaga em cheia grande": "#af601a", "na margem da cheia": "#566573", "fora das zonas de aviso": "#aab7b8"}
CORES_AGUA = {"normal": "#5dade2", "elevada": "#b9770e", "muito elevada": "#6e2c00", "sem dados": "#D9DED9", "sem medição recente": "#bdc3c7"}
CORES_SIM_NAO = {"Sim": "#27ae60", "Não": "#c0392b", "Não neste rio": "#c0392b", "Só nos troços largos": "#f1c40f", "Só por estimativa": "#f1c40f"}


# ----------------------------------------------------------------------------- data (cached; refreshed when the package changes)
def _versao() -> float:
    ficheiro = leitor.DADOS / "catalogo.json"
    return ficheiro.stat().st_mtime if ficheiro.exists() else 0.0


@st.cache_data(show_spinner=False)
def catalogo(versao: float) -> dict:
    return leitor.catalogo()


@st.cache_data(show_spinner=False)
def serie(identificador: str, versao: float) -> pd.DataFrame:
    return leitor.serie(identificador)


@st.cache_data(show_spinner=False)
def tabela(nome: str, versao: float) -> pd.DataFrame:
    return leitor.tabela(nome)


@st.cache_data(show_spinner=False)
def geojson(identificador: str, versao: float) -> dict:
    return leitor.geojson(identificador)


@st.cache_data(show_spinner=False)
def historico(versao: float) -> pd.DataFrame:
    """Daily alerts since 2006 with the hydrological year (October to September)."""
    dados = leitor.serie("alertas_historicos")
    dados["data"] = pd.to_datetime(dados["data"])
    dados["ano"] = dados["data"].dt.year + (dados["data"].dt.month >= 10)
    return dados


V = _versao()
try:
    CATALOGO = catalogo(V)
    CAMADAS = {c["id"]: c for c in CATALOGO["camadas"]}
    CORES = CAMADAS["boletim"]["cores_dos_alertas"]
    BOLETIM = leitor.boletim()                       # not cached: its age is checked on every visit
except Exception:                                    # the data package is missing or broken: say so plainly
    st.error(t("A plataforma está temporariamente sem dados. Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul."))
    st.stop()
VALIDO = bool(BOLETIM["seguro_mostrar"])
LIMITES = BOLETIM["estado"].get("limites_caudal", {})
CORES_LIMITES = {k: CORES[k] for k in LIMITES if k in CORES}
CONSELHOS = CATALOGO.get("conselhos", {})
HOJE = pd.Timestamp(BOLETIM["estado"].get("data_da_previsao", pd.Timestamp.now().date()))
EMITIDO = pd.Timestamp(BOLETIM["estado"]["emitido_utc"]).tz_convert("Africa/Maputo")


def limites(identificador: str) -> None:
    texto = CAMADAS.get(identificador, {}).get("limites")
    if texto:
        T.caption(f"<b>{t('Até onde confiar:')}</b> {t(texto)}")


def grafico(desenho) -> None:
    """A chart with the platform's own look (not Streamlit's chart theme)."""
    st.altair_chart(desenho, width="stretch", theme=None)


def ir_para(pagina: str, ancora: str = "") -> None:
    """Open a page (from a button or the bars); `ancora` opens it at that section instead of the top."""
    st.session_state["pagina"] = pagina
    st.session_state["_ancora"] = ancora

def num(valor, casas: int = 0) -> str:
    return L.numero(valor, casas)


def longe_dos_limites(fora: dict) -> str:
    return ", ".join(t("{nivel} a partir de {valor} m³/s", nivel=t(k), valor=num(v)) for k, v in fora.items())


def mapa_interativo(centro, zoom):
    import folium

    # OpenStreetMap: open, free, needs only the credit. (CARTO's basemaps now ask for a paid key and showed
    # "API KEY REQUIRED" over the map.)
    mapa = folium.Map(location=list(centro), zoom_start=zoom, tiles=None, prefer_canvas=True)
    folium.TileLayer("https://tile.openstreetmap.org/{z}/{x}/{y}.png", attr="© <a href='https://www.openstreetmap.org/copyright'>OpenStreetMap</a>",
                     name="OpenStreetMap", max_zoom=19).add_to(mapa)
    folium.GeoJson(geojson("distrito", V), style_function=lambda f: {"color": T.NAVY, "weight": 2, "fill": False}).add_to(mapa)
    return mapa, folium


def mostrar_mapa(mapa, altura: int = 540) -> None:
    from streamlit_folium import st_folium

    st_folium(mapa, height=altura, use_container_width=True, returned_objects=[])


def cenarios_do_boletim() -> pd.DataFrame:
    cenarios = tabela("cenarios_caudal", V)
    dias = pd.to_datetime(cenarios.index)
    return cenarios[(dias >= HOJE) & (dias <= pd.Timestamp(BOLETIM["valido_ate"]))]


# ----------------------------------------------------------------------------- 1. home: the answer of the day, then the two objectives
def seccao_qualidade_inicio() -> None:
    """The first objective: how the water is today, in one sentence and one picture, and what to do with it."""
    with T.guard("a monitorização da água"):
        camada = CAMADAS.get("cor_da_agua_mapa")
        T.section("Como está a água do rio?", "A cor da água vista por satélite, de Manhiça à foz, comparada com o costume de cada época.", "Qualidade da água")
        if not camada:
            resumo_de_conselhos(maximo=3)
            st.button(t("Ver a qualidade da água"), on_click=ir_para, args=("agua",), key="ir_agua", type="primary")
            return
        quando, frase, chips, velho = leitura_da_cor(camada)
        T.water_reading(quando, frase, chips, velho)
        a, b = st.columns([2, 3], gap="large")
        with a:
            foto_e_cor(camada, "mapa_cor_inicio")
        with b:
            T.water_scale(camada["legenda"])
            semanas_previstas()
            resumo_de_conselhos(maximo=3)
            st.button(t("Ver a qualidade da água"), on_click=ir_para, args=("agua",), key="ir_agua", type="primary")


def seccao_cheias_inicio() -> None:
    """The second objective: will the river flood in the next ten days, day by day."""
    T.section("O rio vai alagar nos próximos dias?", "Toque nas setas para andar de dia em dia. A barra de cor por baixo de cada dia é o nível de alerta.", "Cheias")
    if not VALIDO:
        T.note("Sem previsão válida para mostrar. Consulte os avisos oficiais.", "aviso")
        return
    dias = BOLETIM["previsao_diaria"]
    previsao = tabela("previsao_alertas", V)
    esquerda, direita = st.columns([3, 2], gap="medium")
    with esquerda:
        escolhido = T.stepper("dia", list(range(len(dias))), lambda i: L.dia_da_semana(dias[i]["data"]), "dia escolhido")
        T.day_tiles(dias, CORES, escolhido)
        d = dias[escolhido]
        with T.guard("o gráfico da previsão"):
            desenho, fora = G.forecast(cenarios_do_boletim(), LIMITES, CORES_LIMITES, d["data"], 230)
            grafico(desenho)
            if fora:
                T.caption(t("O rio está longe dos limites de alerta: {limites}.", limites=longe_dos_limites(fora)))
    with direita:
        linha = previsao.iloc[escolhido] if escolhido < len(previsao) else None
        probabilidades = "" if linha is None else (
            f"<p class='ete-miudo' style='margin-top:10px'>{t('Probabilidade de passar cada limite')}</p>"
            + "".join(T.chip(f"{t(k)} · <b>&nbsp;{100 * linha['prob_' + k]:.0f} %</b>", CORES[k]) for k in ("amarelo", "laranja", "vermelho")))
        T.card(T.dot(CORES[d["alerta"]]) + T.alert_name(d["alerta"]),
               "<p>" + t("Caudal previsto: <b>{caudal} m³/s</b> (entre {baixo} e {alto}).", caudal=num(d["caudal_mediana_m3s"]), baixo=num(d["caudal_p10_m3s"]), alto=num(d["caudal_p90_m3s"])) + "</p>"
               + ("<p>" + t("Alguns cenários chegam a <b>{nivel}</b>.", nivel=t(d["alerta_possivel"])) + "</p>" if d["alerta_possivel"] != d["alerta"] else "") + probabilidades,
               pd.Timestamp(d["data"]).strftime("%d/%m") + " · " + t("dia escolhido"))
        primeiro, grande = BOLETIM.get("lugares_que_alagam_primeiro") or [], BOLETIM.get("lugares_em_cheia_grande") or []
        if primeiro or grande:
            T.card("Lugares a avisar", (f"<p><b>{t('Alagam primeiro:')}</b> " + ", ".join(primeiro) + ".</p>" if primeiro else "")
                   + (f"<p><b>{t('Em cheia grande:')}</b> " + ", ".join(grande) + ".</p>" if grande else ""), "Onde")
        st.button(t("Ver a previsão de cheias"), on_click=ir_para, args=("cheias",), key="ir_cheias", type="primary")


def porta(chave: str, olho: str, titulo: str, texto: str, botao: str, destino: str, principal: bool = False) -> None:
    """A card that leads to another page, with its button inside."""
    with st.container(key=f"porta_{chave}"):
        T.html(f"<div class='ete-olho'>{t(olho)}</div><div class='cab'>{t(titulo)}</div><p>{t(texto)}</p>")
        st.button(t(botao), on_click=ir_para, args=(destino,), key=f"ir_{chave}", type="primary" if principal else "secondary")


def pagina_inicio() -> None:
    """The answer of the day, then the two objectives of the project (the water, the floods), then two doors: the alerts and the project."""
    if VALIDO:
        nivel = BOLETIM["nivel_maximo_provavel"]
        T.hero(nivel, BOLETIM["titulo"], CORES[nivel], BOLETIM["conselho"], L.dia_mes(BOLETIM["valido_ate"]), f"{EMITIDO:%d/%m, %H:%M}", CORES, HOJE,
               nome=primeiro_nome(conta_actual()) if conta_actual() else "")
    else:
        T.hero_unavailable()
    conta = conta_actual()
    if conta and conta.get("lugar") in lugares_unicos():   # signed in: one tap to the person's place
        with st.container(key="atalho_zona", horizontal=True, vertical_alignment="center", gap="small"):
            T.html(f"<div class='ete-atalho'>{t('O seu lugar')}: <b>{T.html_escape(conta['lugar'])}</b></div>", "content")
            st.button(t("Ver a página de {lugar}", lugar=conta["lugar"]), on_click=abrir, args=(f"lugar:{conta['lugar']}",), key="ir_minha_zona", type="tertiary",
                      icon=":material/arrow_forward:")
    seccao_qualidade_inicio()
    seccao_cheias_inicio()
    T.html("<div style='height:26px'></div>")
    a, b = st.columns(2, gap="medium")
    with a:
        porta("alertas_inicio", "Alertas no WhatsApp", "Receba os alertas no seu telefone",
              "Só escrevemos quando houver perigo de cheia no rio Incomáti, e quando o perigo passar. A mensagem diz que lugares podem alagar e o que fazer. É grátis.",
              "Receber alertas no meu WhatsApp", "alertas", principal=True)
    with b:
        porta("projecto", "O projecto", "O que é o Eyes to Earth",
              "Um projecto que usa satélites e machine learning para vigiar a água do rio Incomáti e avisar das cheias em Marracuene. Dados abertos, actualizados todas as manhãs.",
              "Conhecer o projecto", "sobre")
    curiosidades_do_dia()


# ----------------------------------------------------------------------------- 2. water quality: today, what to do, the next weeks, the past, the whole river
def leitura_da_cor(camada: dict) -> tuple[str, str, list, str]:
    """The map of the water colour in words: (date of the image, one sentence, a chip per section, a note when the image is old)."""
    data = pd.Timestamp(camada["data"])
    resumo = camada.get("resumo", {})
    cores = {s["nome"]: s["cor"] for s in camada["legenda"]}
    principal = resumo.get("Q8") or next(iter(resumo.values()), {})
    classe = principal.get("classe_da_mediana")
    frase = (t("Em {lugar}, a água está {como}.", lugar=principal["nome"], como=t(T.FRASES_AGUA[classe])) if classe
             else t("Na última imagem, as nuvens tapavam o rio em Marracuene."))
    chips = [(t(r["nome"]) if r["nome"] in ("Foz", "foz") else r["nome"], r["classe_da_mediana"], cores.get(r["classe_da_mediana"], "#B4B9BE"))
             for r in resumo.values() if r.get("classe_da_mediana")]
    dias = (HOJE.normalize() - data.normalize()).days
    velho = t("A imagem mais recente com o rio à vista tem {n} dias: as nuvens taparam as seguintes.", n=dias) if dias > 20 else ""
    return t("Satélite Sentinel-2 · {dia}", dia=L.data_longa(data)), frase, chips, velho


def foto_e_cor(camada: dict, chave: str) -> None:
    """The satellite photograph and the map of the water colour of the same day, to slide from one to the other."""
    if camada.get("foto_recorte") and leitor.caminho(camada["foto_recorte"]).is_file():
        T.compare(leitor.caminho(camada["foto_recorte"]), leitor.caminho(camada["recorte"]), t("Fotografia do satélite"), t("Cor da água"), chave, 50,
                  t("Arraste a barra branca: à esquerda o que o satélite viu, à direita a cor da água realçada."))
    else:
        with st.container(key=chave):
            st.image(str(leitor.caminho(camada.get("recorte") or camada["ficheiro"])), width="stretch")


def mapa_da_cor(chave: str = "mapa_cor", largura="stretch") -> None:
    camada = CAMADAS["cor_da_agua_mapa"]
    with st.container(key=chave):
        st.image(str(leitor.caminho(camada["ficheiro"])), width=largura)


def semanas_previstas() -> None:
    """The forecast of the water colour at Marracuene in four chips, one per week (home page)."""
    with T.guard("a previsão da cor da água"):
        import previsao_mapa as PM

        if not VALIDO or not PM.existe():
            return
        try:
            prevista = tabela("cor_prevista", V)
        except Exception:
            return
        if len(prevista) < 28:
            return
        prevista.index = pd.to_datetime(prevista.index)
        cores = dict(zip(PM.NOMES, PM.CORES))
        chips = ""
        for i in range(4):
            semana = prevista.iloc[i * 7:(i + 1) * 7]
            degrau = PM.classe(float(semana["ndti_semana" if "ndti_semana" in semana else "ndti_q8"].mean()))
            chips += f"<span class='ete-chip'>{T.dot(cores[degrau])}<b>{semana.index[0]:%d/%m}</b>&nbsp;· {t(degrau)}</span>"
        T.html(f"<div class='ete-olho' style='margin-top:14px'>{t('Previsão para as próximas 4 semanas')}</div><div style='display:flex;flex-wrap:wrap;gap:6px 8px;margin-top:8px'>{chips}</div>")



def previsao_da_cor() -> None:
    """The colour of the water in the coming four weeks: a forecast map per week and the 30 mornings of Marracuene."""
    with T.guard("a previsão da cor da água"):
        import previsao_mapa as PM

        if not VALIDO or not PM.existe():
            return
        try:
            prevista = tabela("cor_prevista", V)
        except Exception:
            return
        if len(prevista) < 28:
            return
        prevista.index = pd.to_datetime(prevista.index)
        T.section("A água nas próximas semanas",
                  "Previsão para as manhãs, feita com o caudal previsto, a maré e o que o rio fez em dez anos de imagens de satélite.", "Previsão", "previsao")
        semanas = [prevista.iloc[i * 7:(i + 1) * 7] for i in range(4)]
        quando = lambda i: f"{semanas[i].index[0]:%d/%m}–{semanas[i].index[-1]:%d/%m}"
        i = st.radio(t("Semana"), list(range(4)), horizontal=True, key="semana_cor", label_visibility="collapsed", format_func=quando)   # short: two per line on a phone
        semana = semanas[i]
        coluna = "ndti_semana" if "ndti_semana" in semana else "ndti_q8"          # the week whatever the hour: average tide
        valor, mare = float(semana[coluna].mean()), 0.0 if coluna == "ndti_semana" else float(semana["mare_m"].mean())
        degrau = PM.classe(valor)
        a, b = st.columns([2, 3], gap="large")
        with a, st.container(key="mapa_previsto"):
            st.image(PM.desenhar(valor, mare), width="stretch")
            T.caption(t("Mapa previsto para a semana de {semana}.", semana=quando(i)))
        with b:
            T.water_reading(t("Previsão · semana de {semana}", semana=quando(i)), t("Em Marracuene, a água deve estar {como}.", como=t(T.FRASES_AGUA[degrau])), [], "")
            grafico(G.colour_forecast(prevista, list(PM_STEPS()), list(PM.CORES), list(PM.NOMES), (semana.index[0], semana.index[-1])))
            T.caption("A linha é a cor mais provável em Marracuene, manhã a manhã; a faixa cinzenta é onde caíram 8 em cada 10 dias nos testes. "
                      "Os fundos coloridos são os cinco degraus do mapa.")
            confianca(i)
        with st.expander(t("Os próximos dias, manhã a manhã: a água vai estar mais turva do que o habitual?")):
            manhas_seguintes()
        st.button(t("Como foi feita esta previsão"), on_click=ir_para, args=("sobre", "modelos"), key="ir_modelos_cor", type="tertiary")


def PM_STEPS():
    import previsao_mapa as PM

    modelo, _, _ = PM._camadas((leitor.DADOS / "modelos" / "mapa_cor_modelo.npz").stat().st_mtime)
    return modelo["steps"]


def confianca(semana: int) -> None:
    """How often the forecast was right in the tests, at the distance of the chosen week."""
    ficheiro = leitor.DADOS / "modelos" / "teste_modelo_marracuene.csv"
    if not ficheiro.is_file():
        return
    teste = pd.read_csv(ficheiro)
    dias = {0: 7, 1: 14, 2: 21, 3: 30}[semana]
    linha = lambda metodo: teste[(teste["antecedencia_dias"] == dias) & (teste["metodo"] == metodo)].iloc[0]
    modelo, epoca = linha("modelo (boosting)"), linha("referência: época do ano")
    T.note(t("Nos testes, com {d} dias de antecedência, a cor prevista saiu certa ou no degrau ao lado em {p} % das manhãs; só com a época do ano, em {e} %. "
             "É uma indicação, não uma certeza.", d=dias, p=round(100 * modelo["classe_vizinha"]), e=round(100 * epoca["classe_vizinha"])), "neutra")


def passado_do_rio() -> None:
    """The river month by month since 2017: the observed map of a chosen month, and the same month in every year."""
    with T.guard("os mapas dos meses passados"):
        import previsao_mapa as PM

        if not PM.ha_meses():
            T.note("O pacote ainda não tem os mapas dos meses passados.", "neutra")
            return
        meses = PM.meses()
        resumo = pd.read_csv(leitor.DADOS / "modelos" / "meses_resumo.csv").set_index("mes")
        anos = sorted({m[:4] for m in meses})
        if "ano_passado_i" not in st.session_state:                     # first look: the same month one year ago
            st.session_state["ano_passado_i"] = anos.index(str(HOJE.year - 1)) if str(HOJE.year - 1) in anos else len(anos) - 1
        ano = T.stepper("ano_passado", anos, lambda a: a, "ano escolhido")
        disponiveis = [int(m[5:]) for m in meses if m[:4] == ano]
        if st.session_state.get("mes_passado") not in disponiveis:
            st.session_state["mes_passado"] = HOJE.month if HOJE.month in disponiveis else disponiveis[-1]
        mes = st.radio(t("Mês"), disponiveis, horizontal=True, key="mes_passado", label_visibility="collapsed", format_func=lambda k: L.meses()[k - 1])
        chave = f"{ano}-{mes:02d}"
        linha = resumo.loc[chave] if chave in resumo.index else None
        nome_mes = f"{L.meses_longos()[mes - 1]} {t('de') if L.lingua() == 'pt' else ''} {ano}".replace("  ", " ")
        if linha is not None and isinstance(linha["classe"], str) and linha["classe"]:
            frase = t("Em {mes}, em Marracuene, a água esteve {como}.", mes=nome_mes, como=t(T.FRASES_AGUA[linha["classe"]]))
        else:
            frase = t("Em {mes}, as nuvens não deixaram ver Marracuene.", mes=nome_mes)
        chips = []
        if linha is not None and pd.notna(linha["caudal_m3s"]):
            chips.append((t("Caudal médio"), f"{num(linha['caudal_m3s'])} m³/s", G.SERIES[0]))
        if linha is not None:
            chips.append((t("Rio lido"), f"{round(100 * linha['parte_lida'])} %", "#8A949E"))
        T.water_reading(t("O rio em {mes}", mes=nome_mes), frase, chips, "")              # the sentence first, as for today
        a, b = st.columns([2, 3], gap="large")
        with a, st.container(key="mapa_passado"):
            st.image(PM.desenhar_mes(chave), width="stretch")
            T.caption(t("A cor de cada ponto do rio em {mes}: a mediana de todas as imagens limpas do mês. Cinzento: sem leitura.", mes=nome_mes))
        with b:
            previsto, ano_previsto = None, None
            try:
                prevista = tabela("cor_prevista", V)
                prevista.index = pd.to_datetime(prevista.index)
                deste_mes = prevista[prevista.index.month == mes]
                if len(deste_mes) >= 7 and VALIDO:
                    previsto, ano_previsto = float(deste_mes["ndti_semana" if "ndti_semana" in deste_mes else "ndti_q8"].mean()), int(deste_mes.index[0].year)
            except Exception:
                pass
            T.subtitle(t("{mes_do_ano} em cada ano", mes_do_ano=L.meses_longos()[mes - 1].capitalize()))
            grafico(G.same_month(resumo, mes, chave, list(PM_STEPS()), list(PM.CORES), list(PM.NOMES), previsto, ano_previsto))
            T.caption("Cada ponto é a cor da água em Marracuene nesse mês de um ano; o círculo marca o ano escolhido e o losango tracejado a previsão para este ano."
                      if previsto is not None else "Cada ponto é a cor da água em Marracuene nesse mês de um ano; o círculo marca o ano escolhido.")
            if linha is not None and pd.notna(linha["caudal_m3s"]) and linha["caudal_m3s"] >= LIMITES.get("amarelo", 164):
                T.note(t("Neste mês o rio levou muita água ({q} m³/s em média). Nas cheias, a água mais barrenta pode confundir-se com terra molhada e ficar fora da leitura: "
                         "a cor pode parecer mais clara do que foi.", q=num(linha["caudal_m3s"])), "aviso")



def manhas_seguintes() -> None:
    """The turbidity model: the chance of muddier water than usual each morning, in three sections near Marracuene."""
    with T.guard("a previsão para as próximas manhãs"):
        diaria = tabela("turbidez_diaria", V)
        if not len(diaria):
            T.note("Sem previsão válida para mostrar.", "aviso")
            return
        grafico(G.turbidity_heatmap(diaria))
        T.caption("Probabilidade (%) de a água estar mais turva do que o habitual por volta das 9h30, em três troços de Marracuene. Quanto mais escuro, mais provável. "
                  "A cor da água muda com o caudal e com a maré, por isso varia de dia para dia mesmo sem chuva.")
        turbidez = tabela("turbidez", V)
        T.table(turbidez[["estado", "medicoes_em_20_dias", "ultima_medicao", "previsao"]].rename(
            columns={"estado": "Últimos 20 dias", "medicoes_em_20_dias": "Imagens usadas", "ultima_medicao": "Última medição", "previsao": "Mais turva nos próximos dias?"}
        ).rename_axis("Troço").reset_index(), {"Últimos 20 dias": CORES_AGUA})


def conselhos_da_agua() -> None:
    """What to do with the river water today, for each group of people, and how to treat it at home."""
    with T.guard("os conselhos de hoje"):
        situacoes = situacoes_de_hoje()
        T.section("O que fazer com a água", "Os conselhos mudam com o que os dados mostram hoje. Escolha o seu grupo.", "Conselhos", "conselhos")
        publico = st.radio(t("Quem é?"), list(conselhos.PUBLICOS), horizontal=True, key="publico_conselhos", label_visibility="collapsed",
                           format_func=lambda k: t(conselhos.PUBLICOS[k][0]))
        para_si = {s["chave"]: itens for s, itens in conselhos.para(publico, situacoes)}
        for situacao in situacoes:                         # one card per situation: what it means, what to do, what the data show
            T.advice_card(situacao["titulo"], para_si.get(situacao["chave"], []), situacao["nivel"], conselhos.PUBLICOS[publico][0], situacao["texto"], razoes(situacao))
        st.download_button(t("Descarregar estes conselhos para partilhar"), texto_para_partilhar(publico, situacoes).encode("utf-8"),
                           f"conselhos_ete_{publico}.txt", "text/plain", key="baixar_conselhos")
        T.anchor("tratar")
        T.subtitle("Como tratar a água em casa")
        T.steps(conselhos.GUIA_TRATAMENTO, colunas=3)
        diarreia = ("<div class='ete-diarreia'><div class='cab'>" + t("Diarreia: o que fazer") + "</div><ol>"
                    + "".join(f"<li>{t(i)}</li>" for i in conselhos.DIARREIA) + "</ol></div>")
        if any(s["nivel"] != "info" for s in situacoes):          # a problem today: the advice on diarrhoea in sight
            T.html(diarreia)
        else:
            with st.expander(t("Diarreia: o que fazer")):
                T.html(diarreia)
        T.caption(conselhos.FONTES)


def rio_inteiro() -> None:
    """The nine sections of the river, from the border to the mouth; their history in closed boxes."""
    if "trocos_modulo_q" not in CAMADAS:
        return
    estado = serie("qualidade_estado", V).set_index("troco")
    mensal = serie("qualidade_mensal", V)
    cores = {i["nome"]: i["cor"] for i in CAMADAS["trocos_modulo_q"]["legenda"]}
    ordem = list(estado["nome"])
    T.section("O rio inteiro, da fronteira à foz", "Nove troços do Incomáti, cada um comparado com a mesma época de outros anos.", "Monitorização", "rio")
    T.river_tiles(estado, cores)
    T.legend(CAMADAS["trocos_modulo_q"]["legenda"])
    alertas = estado[estado["alerta_de_qualidade"] == True]  # noqa: E712
    if len(alertas):
        T.note(t("A verificar em: {trocos}.", trocos=", ".join(L.troco(n) for n in alertas["nome"])) + " "
               + t("A água está mais turva do que o normal para a época e do que a chuva e o caudal explicam. É um motivo para ir ver, não uma prova de poluição."), "aviso")

    with st.expander(t("Os nove troços, em tabela e no mapa")), T.guard("a tabela dos troços"):
        colunas = {"nome": "Troço", "classe": "Estado face ao normal", "vegetacao": "Plantas sobre a água (parte)", "mes": "Mês medido"}
        T.table(estado[[c for c in colunas if c in estado]].rename(columns=colunas), {"Estado face ao normal": CORES_AGUA})
        T.caption("Plantas: só a mais de 20 m das margens, para as folhas das árvores e os caniços da margem não contarem, e só com o Sentinel-2 (píxeis de 10 m).")
        fracos = estado[estado["fiabilidade"] != "boa"]
        if len(fracos):
            T.caption(t("Medição menos fiável em {trocos}: os dois satélites nem sempre concordam, por isso estes troços não dão avisos.",
                        trocos=", ".join(L.troco(n) for n in fracos["nome"])))
        limites("trocos_modulo_q")
        if CAMADAS["trocos_modulo_q"].get("mapa_leve"):
            st.image(str(leitor.caminho(CAMADAS["trocos_modulo_q"]["mapa_leve"])), width=640)

    with st.expander(t("Cada troço mês a mês, desde 2006")):
        with T.guard("o painel de monitorização"):
            T.subtitle("O ano, mês a mês")
            anos = sorted(int(a) for a in mensal.loc[mensal["ndti"].notna(), "ano"].unique())
            ano = T.stepper("ano_agua", anos, lambda a: t("Ano de {ano}", ano=a), "cada quadrado é um troço num mês")
            grafico(G.monitoring_matrix(mensal[mensal["ano"] == ano], {**cores, "sem dados": "#E6EBF1"}, ordem))
            T.caption("Cada linha é um troço do rio; cada coluna, um mês. Azul: água como é costume nessa época. Castanho: mais turva do que o costume. Cinzento: sem imagem limpa nesse mês "
                      "(nunca se preenche com estimativas). A montante de Manhiça só há medições desde 2017.")
        T.subtitle("Um troço ao longo dos anos")
        codigos = list(estado.index)
        if "troco_i" not in st.session_state:
            st.session_state["troco_i"] = max(len(codigos) - 2, 0)
        escolhido = T.stepper("troco", codigos, lambda c: L.troco(estado.loc[c, "nome"]), "anterior = para montante · seguinte = para a foz")
        parametros = {"ndti": ("Cor da água (índice): mais alto = mais turva", "Índice de cor"), "vegetacao": ("Plantas sobre a água (longe das margens)", "Parte com plantas"),
                      "turbidez_fnu": ("Turbidez estimada (FNU, sem calibração local)", "Turbidez estimada (FNU)"),
                      "tss_mg_l": ("Sólidos suspensos estimados (mg/L, sem calibração local)", "Sólidos estimados (mg/L)"),
                      "secchi_m": ("Transparência estimada (m, sem calibração local)", "Transparência estimada (m)"), "temp_c": ("Temperatura da água (°C, só troços largos)", "Temperatura (°C)")}
        a, b = st.columns([2, 1])
        coluna = a.selectbox(t("O que ver"), list(parametros), key="parametro_agua", format_func=lambda k: t(parametros[k][0]))
        periodos = {10: "Últimos 10 anos", 5: "Últimos 5 anos", 99: "Desde 2006"}
        anos = b.radio(t("Período"), list(periodos), horizontal=True, key="periodo_agua", format_func=lambda k: t(periodos[k]))
        do_troco = mensal[mensal["troco"] == escolhido].assign(mes=lambda d: d["month"].str[5:].astype(int))
        do_troco = do_troco[do_troco["month"] >= str(pd.Timestamp(do_troco["month"].max()).year - anos + 1)]
        with T.guard("a série do troço"):
            if do_troco[coluna].notna().any():
                normais = None
                if coluna == "ndti" and "qualidade_normais" in CAMADAS:
                    todos = serie("qualidade_normais", V)
                    normais = todos[todos["troco"] == escolhido].set_index("mes")[["p25", "mediana", "p75"]]
                grafico(G.quality(do_troco, normais, coluna, parametros[coluna][1]))
                if coluna == "ndti":
                    T.caption("Cada ponto é um mês. A faixa cinzenta é o intervalo habitual para esse mês do ano; a linha tracejada é o normal. "
                              "A montante de Manhiça o rio é estreito e só há medições desde 2017.")
                elif coluna in ("turbidez_fnu", "tss_mg_l", "secchi_m"):
                    T.caption("Estimativa sem medições no rio: serve como ordem de grandeza, não como medição.")
            else:
                T.note("Sem medições deste parâmetro neste troço.", "neutra")
        with T.guard("a comparação entre troços"):
            T.subtitle("Comparar troços")
            largo = mensal.pivot(index="month", columns="nome", values="ndti")
            largo.index = pd.to_datetime(largo.index)
            defeito = [c for c in largo.columns if c.startswith(("Q1 ", "Q8 "))]
            escolha = st.multiselect(t("Até três troços"), list(largo.columns), default=defeito, max_selections=3, key="comparar_agua", placeholder=t("Escolha os troços"),
                                     format_func=L.troco)
            if escolha:
                grafico(G.compare(largo.loc["2017":, [c for c in largo.columns if c in escolha]].dropna(how="all")))
                T.caption("Desde 2017, quando há medições em todos os troços. A cor da água em Marracuene não acompanha, mês a mês, a da fronteira: "
                          "entre os dois pontos há 250 km de rio, afluentes, regadios e, no fim, a maré.")
        st.download_button(t("Descarregar a série mensal de todos os troços (CSV)"), mensal.to_csv(index=False).encode("utf-8"), "qualidade_por_troco.csv", "text/csv")

    with st.expander(t("Meses que fugiram ao normal e tendências")):
        with T.guard("os meses invulgares"):
            invulgares = pd.read_csv(leitor.caminho("qualidade/meses_invulgares.csv")).sort_values("month", ascending=False)
            T.table(invulgares[["nome", "month", "anomalia_ndti", "anomalia_vegetacao", "caudal_m3s"]].head(40).rename(
                columns={"nome": "Troço", "month": "Mês", "anomalia_ndti": "Desvio da cor", "anomalia_vegetacao": "Desvio das plantas", "caudal_m3s": "Caudal (m³/s)"}), height=320)
            T.caption("Apontados por um modelo (Isolation Forest) que olha para a cor, as plantas e o caudal em conjunto. Um mês apontado é um convite a ir ver, não um diagnóstico.")
        with T.guard("as tendências"):
            if "qualidade_tendencias" in CAMADAS:
                tendencias = serie("qualidade_tendencias", V)
                tendencias = tendencias[(tendencias["troco"] == escolhido) & (tendencias["periodo"] == "registo completo")]
                if len(tendencias):
                    T.subtitle(t("Está a mudar ao longo dos anos? ({troco})", troco=L.troco(estado.loc[escolhido, "nome"])))
                    T.table(tendencias[["parametro", "tendencia", "leitura", "primeiro_mes", "ultimo_mes"]].rename(
                        columns={"parametro": "Parâmetro", "tendencia": "Tendência", "leitura": "Como ler", "primeiro_mes": "De", "ultimo_mes": "Até"}))
                    limites("qualidade_tendencias")


def como_medimos() -> None:
    T.section("Como medimos", "Só com satélites e dados abertos, sem aparelhos no rio.", "Método")
    T.steps([("Nove troços", "O rio é seguido da fronteira à foz e cortado em nove partes."),
             ("Só a água conta", "Nuvens, sombras de árvores e de nuvens, plantas, folhas, areia e o píxel junto à margem nunca contam."),
             ("Cor da água", "A relação entre o vermelho e o verde diz quanto sedimento a água traz."), ("O normal de cada mês", "Cada troço é comparado consigo mesmo, na mesma época de outros anos."),
             ("Dois satélites", "Onde o Sentinel-2 e o Landsat não concordam, a medição fica marcada como menos fiável.")])
    T.caption("Plantas sobre a água: só se contam a mais de 20 m das margens e só dão aviso quando aparecem em pelo menos duas imagens do mês, num troço com medição fiável. "
              "Assim as folhas das árvores da margem e uma imagem má não dão falsos avisos.")
    with st.expander(t("O que o satélite vê e o que não vê")):
        T.table(pd.DataFrame([
            {"O que": "Lama e sedimentos (turbidez)", "O satélite vê?": "Sim", "Como é mostrado": "\"Normal\", \"elevada\" ou \"muito elevada\" face ao costume do troço"},
            {"O que": "Plantas sobre a água", "O satélite vê?": "Sim", "Como é mostrado": "Parte do canal coberta (mais fiável nos troços largos)"},
            {"O que": "Temperatura da água", "O satélite vê?": "Só nos troços largos", "Como é mostrado": "Graus, de Manhiça à foz"},
            {"O que": "Turbidez em números (FNU), sólidos (mg/L), transparência (m)", "O satélite vê?": "Só por estimativa", "Como é mostrado": "Ordem de grandeza, sem medições no rio"},
            {"O que": "Algas (clorofila)", "O satélite vê?": "Não neste rio", "Como é mostrado": "Não é mostrado: o sinal confunde-se com a lama"},
            {"O que": "Micróbios, pH, oxigénio, nutrientes, metais, pesticidas", "O satélite vê?": "Não", "Como é mostrado": "Só com análises de laboratório"}]), {"O satélite vê?": CORES_SIM_NAO})
        T.caption("Não há nenhuma estação pública de qualidade da água na bacia do Incomáti (arquivo mundial GEMStat), e o projecto não fez medições no rio. "
                  "Por isso tudo o que aqui se mostra é relativo: a água de hoje comparada com a água de costume.")
    st.button(t("Ver os modelos e os testes em detalhe"), on_click=ir_para, args=("sobre", "modelos"), key="ir_modelos_agua")


def pagina_agua() -> None:
    """The first objective, read from top to bottom: today, what to do, the next weeks, the past, the whole river, how it is measured."""
    T.page_head("Qualidade da água", "Como está a água do rio Incomáti",
                "A cor da água vista por satélite, hoje, nas próximas semanas e nos anos passados, e o que fazer com a água do rio.")
    camada = CAMADAS.get("cor_da_agua_mapa")
    if camada:
        with T.guard("o mapa da cor da água"):
            quando, frase, chips, velho = leitura_da_cor(camada)
            T.water_reading(quando, frase, chips, velho)
            esquerda, direita = st.columns([2, 3], gap="large")
            with esquerda:
                foto_e_cor(camada, "mapa_cor")
                if camada.get("recorte"):
                    with st.expander(t("O rio desde Manhiça (mapa completo)")):
                        mapa_da_cor("mapa_cor_completo")
            with direita:
                T.water_scale(camada["legenda"])
                T.caption("Cada cor compara a água com dez anos de imagens deste troço do rio. **Muito turva** quer dizer com mais lama do que em quatro de cada cinco imagens.")
                T.note("O satélite vê a lama, não vê micróbios nem químicos. Nada nesta página diz se a água é segura: **a água do rio deve ser sempre tratada antes de beber.**")
                if st.toggle(t("Mapa interactivo (gasta mais dados)"), value=False, key="mapa_cor_interactivo"):
                    mapa, folium = mapa_interativo((-25.68, 32.72), 11)
                    folium.raster_layers.ImageOverlay(str(leitor.caminho(camada["sobreposicao"])), bounds=camada["cantos"], opacity=1.0).add_to(mapa)
                    mostrar_mapa(mapa, 520)
    else:
        T.note("O satélite vê o que muda a cor da água: lama e plantas à superfície. Não vê micróbios nem químicos. "
               "Nada nesta página diz se a água é segura: **a água do rio deve ser sempre tratada antes de beber.**")
    conselhos_da_agua()
    previsao_da_cor()
    T.section("A água nos anos passados", "Escolha o ano e o mês: o mapa mostra a cor do rio nesse mês e o gráfico, o mesmo mês em todos os anos.", "Passado", "passado")
    passado_do_rio()
    rio_inteiro()
    como_medimos()


# ----------------------------------------------------------------------------- advice on the water (home and water pages)
def situacoes_de_hoje() -> list[dict]:
    """What the data show today (water colour, plants, floods, flow), most serious first."""
    try:
        turbidez = tabela("turbidez", V)
        turbidez = turbidez.rename_axis("troco").reset_index() if "troco" not in turbidez.columns else turbidez
    except Exception:
        turbidez = None
    estado_q = serie("qualidade_estado", V) if "qualidade_estado" in CAMADAS else None
    try:
        diaria = tabela("turbidez_diaria", V)
    except Exception:
        diaria = None
    return conselhos.detectar(BOLETIM, turbidez, estado_q, historico(V), diaria)


def razoes(situacao: dict) -> str:
    """Why a situation is on, in the reader's language (numbers from the data)."""
    linhas = []
    for modelo, valores in situacao["porque"]:
        traduzidos = {k: (L.troco(v) if k == "nome" else v if k in ("mes", "p", "caudal", "p25", "dia") else t(v)) for k, v in valores.items()}
        linhas.append(t(modelo, **traduzidos))
    return "<br>".join(linhas)


def texto_para_partilhar(publico: str, situacoes: list[dict]) -> str:
    """Plain text of the advice for one audience, to forward by WhatsApp or print."""
    linhas = [f"Eyes to Earth · {t('Conselhos sobre a água')} · {t(conselhos.PUBLICOS[publico][0])} · {pd.Timestamp.now(tz='Africa/Maputo'):%d/%m/%Y}", ""]
    for situacao, itens in conselhos.para(publico, situacoes):
        linhas.append(t(situacao["titulo"]).upper())
        linhas += [f"- {t(i)}" for i in itens] + [""]
    linhas += [t("Como tratar a água em casa").upper()] + [f"{n}. {t(a)}: {t(b)}" for n, (a, b) in enumerate(conselhos.GUIA_TRATAMENTO, 1)] + [""]
    linhas += [t(CATALOGO["aviso"])]
    return "\n".join(linhas)



def resumo_de_conselhos(publico: str = "familias", maximo: int = 4) -> None:
    """A short version for the home page: today's situations and the first pieces of advice."""
    with T.guard("os conselhos de hoje"):
        situacoes = situacoes_de_hoje()
        problemas = [s for s in situacoes if s["chave"] != "sempre"]
        itens, nivel = [], "info"
        for situacao, lista in conselhos.para(publico, situacoes):
            if not itens:
                nivel = situacao["nivel"]
            itens += [i for i in lista if i not in itens]
        titulo = t("Hoje: {situacoes}", situacoes=", ".join(t(s["titulo"]).lower() for s in problemas)) if problemas else t("Hoje não há nenhum problema especial")
        T.advice_card(titulo, itens[:maximo], nivel, t(conselhos.PUBLICOS[publico][0]))


# ----------------------------------------------------------------------------- 3. floods: the next ten days, where the water arrives, from space, twenty years
def proximos_dez_dias() -> None:
    T.section("Os próximos dez dias", "O caudal previsto do rio em Marracuene e o nível de alerta de cada dia.", "Previsão", "dez_dias")
    if not VALIDO:
        T.note("Sem previsão válida para mostrar. Consulte os avisos oficiais.", "aviso")
    else:
        T.day_tiles(BOLETIM["previsao_diaria"], CORES, -1)
        with T.guard("a previsão de caudal"):
            desenho, fora = G.forecast(cenarios_do_boletim(), LIMITES, CORES_LIMITES)
            grafico(desenho)
            nota = t("A linha é o cenário central; a faixa clara vai do mínimo ao máximo provável, entre 51 cenários do modelo europeu GloFAS.")
            T.caption(nota + (" " + t("O rio está longe dos limites: {limites}.", limites=longe_dos_limites(fora)) if fora else ""))
    T.anchor("cores")
    T.subtitle("O que quer dizer cada cor")
    T.level_cards(LIMITES, CORES, CONSELHOS)
    T.caption("Os limites de caudal foram calculados com 25 anos de dados (1997 a 2021) e testados nos anos seguintes. Na cheia de Janeiro de 2026, "
              "estas regras teriam dado alerta laranja 4 a 5 dias antes do primeiro mapa de cheia.")
    if VALIDO:
        with st.expander(t("A previsão dia a dia, em tabela")), T.guard("a tabela da previsão"):
            previsao = tabela("previsao_alertas", V).iloc[:len(BOLETIM["previsao_diaria"])]
            mostra = pd.DataFrame({"Dia": pd.to_datetime(previsao.index).strftime("%d/%m"), "Alerta": previsao["alerta"].to_numpy(), "Alerta possível": previsao["alerta_possivel"].to_numpy(),
                                   "Caudal central (m³/s)": previsao["caudal_mediana"].round(0).to_numpy(), "Mínimo provável": previsao["caudal_p10"].round(0).to_numpy(),
                                   "Máximo provável": previsao["caudal_p90"].round(0).to_numpy(), "Passa o amarelo (%)": (100 * previsao["prob_amarelo"]).round(0).to_numpy(),
                                   "Passa o laranja (%)": (100 * previsao["prob_laranja"]).round(0).to_numpy(), "Passa o vermelho (%)": (100 * previsao["prob_vermelho"]).round(0).to_numpy(),
                                   "Chuva 7 dias (mm)": previsao["chuva_7d_mm"].round(0).to_numpy(), "Segunda opinião (m³/s)": previsao["caudal_modelo_c"].round(0).to_numpy()})
            T.table(mostra, {"Alerta": CORES, "Alerta possível": CORES})
            T.caption("\"Alerta\" é o que metade ou mais dos cenários indica; \"alerta possível\" é o que pelo menos um em cada cinco indica. "
                      "A \"segunda opinião\" é um modelo próprio do projecto, que usa só a chuva já caída.")
            st.download_button(t("Descarregar a previsão (CSV)"), tabela("previsao_alertas", V).to_csv().encode("utf-8"), "previsao_ete.csv", "text/csv")
    with st.expander(t("A chuva na bacia, que faz o rio subir")), T.guard("a chuva na bacia"):
        grafico(G.rain(tabela("chuva_bacia", V), HOJE))
        T.caption("Chuva média em toda a bacia do Incomáti, que inclui partes da África do Sul e de Essuatíni. É esta chuva que faz o rio subir em Marracuene, "
                  "dias depois. A chuva prevista só entra no alerta até 7 dias à frente.")


def onde_a_agua_chega() -> None:
    """The warning zones of the 2026 flood, the places in them and what is exposed; a place can be searched."""
    camada = CAMADAS.get("zonas_de_aviso")
    if not camada:
        return
    T.section("Onde a água chega primeiro", "As zonas de aviso mostram onde a água chegou na cheia de Janeiro de 2026. Procure o seu lugar.", "Lugares", "lugares")
    lugares = serie("lugares_por_ordem", V)
    vista, lado = st.columns([1.15, 1], gap="large")
    with lado:                                          # drawn first (the map needs the place and the switch), shown on the right
        nome = ""
        with T.guard("a pesquisa de lugares"):
            nome = st.selectbox(t("Procurar um lugar"), [""] + sorted(lugares["lugar"].unique()), key="lugar_mapa", format_func=lambda v: v or t("(nenhum)"))
            if nome:
                l = lugares[lugares["lugar"] == nome].iloc[0]
                posto = l["posto_administrativo"] if isinstance(l["posto_administrativo"], str) else ""
                T.card(nome, f"{T.dot(CORES_LUGARES.get(l['categoria'], '#aab7b8'))}<b>{t(l['categoria'])}</b><br>"
                       + (t("Primeiro mapa com água: {dia} ({n} dias depois do alerta)", dia=pd.Timestamp(l["primeira_data"]).strftime("%d/%m/%Y"), n=num(l["dias_apos_alerta"])) + "<br>"
                          if pd.notna(l["primeira_data"]) else "")
                       + t("Edifícios num raio de 500 m: {n}", n=num(l["edificios"])) + "<br>" + t("Distância ao rio: {n} m", n=num(l["distancia_ao_rio_m"])) + "<br>"
                       + t("Altura acima do rio: {n} m", n=num(l["altura_acima_do_rio_m"], 1))
                       + f"<br><span class='ete-miudo'>{posto} · {t('nome de {fonte}, por validar', fonte=l['fonte_do_nome'])}</span>", "Lugar")
                st.button(t("Ver tudo sobre {lugar}", lugar=nome), on_click=abrir, args=(f"lugar:{nome}",), key="ir_zona_mapa", type="secondary")
        T.card("", f"<p style='margin:0 0 8px 0'>{t(camada.get('descricao', ''))}</p>" + " ".join(T.chip(i["nome"], i["cor"]) for i in camada.get("legenda", [])), "Legenda")
        with T.guard("a exposição por zona"):
            exposicao = serie("exposicao", V)
            grande, primeira = exposicao.iloc[-1], exposicao.iloc[0]
            T.note(t("Na cheia de Janeiro de 2026, a água cobriu {area} km² do distrito: {edificios} edifícios e {campos} km² de campos ficaram dentro da zona alagada. "
                     "A zona 1, onde a água chegou primeiro, tem {area1} km² e {edificios1} edifícios.", area=num(grande["area_km2"]), edificios=num(grande["edificios"]),
                     campos=num(grande["area_agricola_km2"]), area1=num(primeira["area_km2"]), edificios1=num(primeira["edificios"])), "neutra")
        interativo = st.toggle(t("Mapa interactivo (gasta mais dados)"), value=False, key="mapa_cheias")
    with vista, T.guard("o mapa das zonas"):
        if interativo:
            mapa, folium = mapa_interativo((-25.68, 32.72), 10)
            if camada.get("imagem"):
                folium.raster_layers.ImageOverlay(str(leitor.caminho(camada["imagem"])), bounds=camada["cantos"], opacity=0.8).add_to(mapa)
            else:                                    # older package without the light image: draw the polygons
                folium.GeoJson(geojson("zonas_de_aviso", V), style_function=lambda f: {"color": f["properties"]["cor"], "weight": 1, "fillOpacity": 0.45}).add_to(mapa)
            for lugar in geojson("lugares", V)["features"]:
                p = lugar["properties"]
                if p["categoria"] in ("alaga primeiro", "alaga em cheia grande") or p["lugar"] == nome:
                    lon, lat = lugar["geometry"]["coordinates"]
                    folium.CircleMarker([lat, lon], radius=8 if p["lugar"] == nome else 4, color=CORES_LUGARES.get(p["categoria"], "#566573"), fill=True, fill_opacity=0.95,
                                        tooltip=f"{p['lugar']}: {t(p['categoria'])}").add_to(mapa)
            mostrar_mapa(mapa)
        elif camada.get("mapa_leve"):
            with st.container(key="mapa_zonas"):
                st.image(str(leitor.caminho(camada["mapa_leve"])), width="stretch")
        limites("zonas_de_aviso")
    with st.expander(t("Todos os lugares, por ordem de alagamento")), T.guard("a tabela dos lugares"):
        a, b = st.columns(2)
        categorias = a.multiselect(t("Situação"), list(CORES_LUGARES), default=["alaga primeiro", "alaga em cheia grande"], key="categoria_lugares", placeholder=t("Todas"), format_func=t)
        postos = sorted(p for p in lugares["posto_administrativo"].dropna().unique() if p)
        posto = b.multiselect(t("Posto administrativo"), postos, key="posto_lugares", placeholder=t("Todos"))
        filtrados = lugares[lugares["categoria"].isin(categorias or list(CORES_LUGARES))]
        if posto:
            filtrados = filtrados[filtrados["posto_administrativo"].isin(posto)]
        T.table(filtrados[["lugar", "posto_administrativo", "categoria", "primeira_data", "dias_apos_alerta", "parte_alagada", "edificios", "edificios_alagados",
                           "distancia_ao_rio_m", "altura_acima_do_rio_m", "fonte_do_nome"]].rename(columns={
                               "lugar": "Lugar", "posto_administrativo": "Posto administrativo", "categoria": "Situação", "primeira_data": "Primeiro mapa com água",
                               "dias_apos_alerta": "Dias depois do alerta", "parte_alagada": "Parte alagada", "edificios": "Edifícios (500 m)", "edificios_alagados": "Edifícios na zona",
                               "distancia_ao_rio_m": "Distância ao rio (m)", "altura_acima_do_rio_m": "Altura acima do rio (m)", "fonte_do_nome": "Fonte do nome"}),
                {"Situação": CORES_LUGARES}, height=420)
        T.caption(t("{n} lugares.", n=len(filtrados)) + " " + t("Cada lugar é um ponto com um círculo de 500 m, não um limite oficial de bairro. Os nomes ainda não foram validados no terreno."))
        T.subtitle("O que existe em cada zona")
        exposicao = serie("exposicao", V)
        T.table(exposicao[["zona", "area_km2", "area_agricola_km2", "edificios", "escolas", "unidades_de_saude", "estradas_km"]].rename(columns={
            "zona": "Zona", "area_km2": "Área (km²)", "area_agricola_km2": "Terras agrícolas (km²)", "edificios": "Edifícios", "escolas": "Escolas",
            "unidades_de_saude": "Unidades de saúde", "estradas_km": "Estradas e caminhos (km)"}))
        T.caption("Dentro do distrito de Marracuene. As zonas são onde a água chegou na cheia de Janeiro de 2026 (mapas do Copernicus EMS). "
                  "As escolas e unidades de saúde vêm do OpenStreetMap, que pode estar incompleto.")
        st.download_button(t("Descarregar a lista de lugares (CSV)"), lugares.to_csv(index=False).encode("utf-8"), "lugares_por_ordem_de_alagamento.csv", "text/csv")


def rio_visto_do_espaco() -> None:
    """Real photographs of the 2026 flood (before and during) and the radar, month by month, in the same frame as the zone map."""
    fotos, radar = CAMADAS.get("imagens_satelite"), CAMADAS.get("agua_mensal")
    if not fotos and not radar:
        return
    T.section("O rio visto do espaço", "Fotografias reais do satélite e mapas do radar, que vê através das nuvens.", "Satélite", "espaco")
    a, b = st.columns(2, gap="large")
    if fotos:
        with a, T.guard("as fotografias da cheia"):
            par = fotos["pares"][0]
            T.subtitle(par["titulo"])
            data = lambda d: t("{dia} de {ano}", dia=L.dia_mes(d), ano=d[:4])
            T.compare(leitor.caminho(par["antes"]["ficheiro"]), leitor.caminho(par["depois"]["ficheiro"]), data(par["antes"]["data"]), data(par["depois"]["data"]), "cheia_2026", 50,
                      t("Arraste a barra branca para ver a mesma zona antes e durante a cheia.") + " " + t(par["texto"]))
            T.caption("Fotografias do satélite Copernicus Sentinel-2 (ESA), em cor natural.")
    if radar:
        with b, T.guard("a água vista por radar"):
            T.subtitle("Mês a mês, pelo radar")
            meses = radar["meses"]
            if "mes_radar_i" not in st.session_state:          # first look: the month in which the radar saw most water out of its place
                try:
                    area = serie("area_de_agua", V).set_index("month")["cheia_distrito_km2"].reindex(meses)
                    st.session_state["mes_radar_i"] = meses.index(area.idxmax())
                except Exception:
                    pass
            mes = T.stepper("mes_radar", meses, L.mes_ano, "mês mostrado")
            with st.container(key="mapa_radar"):
                st.image(str(leitor.imagem_leve("agua_mensal", mes) or leitor.imagem("agua_mensal", mes)[0]), width="stretch")
            T.legend(radar["legenda"])
            T.caption("O radar Sentinel-1 vê através das nuvens. Cada mapa junta as passagens de um mês inteiro, lidas pelo modelo do projecto (Modelo B). "
                      "Em zonas construídas o modelo marca água a mais.")


def anos_completos() -> tuple[pd.DataFrame, pd.DataFrame]:
    """Days at each alert level per hydrological year: all the years, and only the whole ones (the series starts in January 2006).
    Every page counts the alert years from here, so they all give the same numbers."""
    dados = historico(V)
    por_ano = dados.groupby("ano")["alerta"].value_counts().unstack(fill_value=0).reindex(columns=G.LEVELS, fill_value=0)
    return por_ano, por_ano[por_ano.sum(axis=1) >= 300]


def vinte_anos() -> None:
    """Twenty years of the river: how many days a year the alert rules would have warned."""
    dados = historico(V)
    por_ano, completos = anos_completos()
    T.section("Vinte anos do rio", "Quantos dias por ano as regras de alerta teriam avisado, de 2006 a 2026.", "Histórico", "historico")
    with T.guard("os números do histórico"):
        maior = dados.loc[dados["caudal_m3s"].idxmax()]
        T.kpis([{"rotulo": "Anos com alerta laranja ou vermelho", "valor": t("{n} em {total}", n=int(((completos["laranja"] + completos["vermelho"]) > 0).sum()), total=len(completos)),
                 "nota": "anos de Outubro a Setembro"},
                {"rotulo": "Anos com alerta vermelho", "valor": t("{n} em {total}", n=int((completos["vermelho"] > 0).sum()), total=len(completos))},
                {"rotulo": "Maior caudal", "valor": num(maior["caudal_m3s"]), "unidade": "m³/s", "nota": maior["data"].strftime("%d/%m/%Y")}])
    with T.guard("os dias de alerta por ano"):
        grafico(G.alert_days(completos[["amarelo", "laranja", "vermelho"]], CORES))
        T.caption("Dias em que as regras de alerta teriam dado cada nível. São dias em que o sistema teria avisado, não cheias confirmadas uma a uma no terreno. "
                  "O caudal vem de um modelo mundial (GloFAS), não de uma estação no rio.")
    with st.expander(t("Um ano em detalhe")):
        anos = [int(a) for a in por_ano.index if por_ano.loc[a].sum() >= 200]
        ano = T.stepper("ano_hist", anos, lambda a: t("Ano hidrológico {inicio}/{fim}", inicio=a - 1, fim=a), "de Outubro a Setembro")
        do_ano = dados[dados["ano"] == ano]
        with T.guard("o ano em detalhe"):
            pico = do_ano.loc[do_ano["caudal_m3s"].idxmax()]
            T.kpis([{"rotulo": "Caudal máximo", "valor": num(pico["caudal_m3s"]), "unidade": "m³/s", "nota": pico["data"].strftime("%d/%m/%Y")},
                    {"rotulo": "Dias em amarelo", "valor": int((do_ano["alerta"] == "amarelo").sum())}, {"rotulo": "Dias em laranja", "valor": int((do_ano["alerta"] == "laranja").sum())},
                    {"rotulo": "Dias em vermelho", "valor": int((do_ano["alerta"] == "vermelho").sum())}])
            grafico(G.year_detail(do_ano, LIMITES, CORES))
            T.caption("A linha é o caudal de cada dia; a fita por baixo é o alerta desse dia; as linhas tracejadas são os limites amarelo, laranja e vermelho.")
    with st.expander(t("O caudal e a chuva nos últimos três anos")), T.guard("o histórico de caudal"):
        grafico(G.history(serie("caudal_e_chuva", V), LIMITES, CORES_LIMITES))
        T.legend([{"nome": t("limite {nivel}: {valor} m³/s", nivel=t(k), valor=num(v)), "cor": CORES_LIMITES[k]} for k, v in LIMITES.items() if k in CORES_LIMITES])
        limites("caudal_e_chuva")
    with st.expander(t("A área alagada mês a mês, vista por radar (desde 2015)")), T.guard("a água vista por radar"):
        grafico(G.flood_area(serie("area_de_agua", V)))
        T.caption("Área com água fora do sítio habitual dentro do distrito, em cada mês, vista pelo radar Sentinel-1 (desde 2015). "
                  "Os primeiros meses de 2015 têm poucas passagens do satélite e devem ser lidos com cuidado; em zonas construídas o modelo marca água a mais.")
        limites("agua_mensal")


def pagina_cheias() -> None:
    """The second objective, read from top to bottom: the answer, the next ten days, where the water arrives, the river from space, twenty years."""
    T.page_head("Cheias", "O rio vai alagar nos próximos dias?",
                "A previsão do caudal do Incomáti para dez dias, os lugares onde a água chega primeiro e o que o rio fez nos últimos vinte anos.")
    if VALIDO:
        hoje, nivel = BOLETIM.get("nivel_hoje", BOLETIM["previsao_diaria"][0]["alerta"]), BOLETIM["nivel_maximo_provavel"]
        quando = t("Boletim de {data}", data=f"{EMITIDO:%d/%m}") + " · " + t("válido até {dia}", dia=L.dia_mes(BOLETIM["valido_ate"]))
        T.water_reading(quando, L.titulo_boletim(BOLETIM["titulo"]),
                        [(t("Hoje"), hoje, CORES[hoje]), (t("Até {dia}", dia=pd.Timestamp(BOLETIM["valido_ate"]).strftime("%d/%m")), nivel, CORES[nivel])], "")
    proximos_dez_dias()
    onde_a_agua_chega()
    rio_visto_do_espaco()
    vinte_anos()


# ----------------------------------------------------------------------------- 4. WhatsApp alerts
def _lugares_para_escolher() -> list[str]:
    try:
        return sorted(serie("lugares_por_ordem", V)["lugar"].dropna().unique())
    except Exception:
        return []


def formulario_inscricao(chave: str) -> bool:
    """The sign-up form, written for people who are not technical: a phone number, where they live, a
    language and a clear 'I agree'. Returns True once the person is signed up."""
    if not inscricoes.permanente():
        T.note("As inscrições abrem em breve. Até lá, siga os alertas nesta plataforma.", "neutra")
        return False
    outro = "__outro__"
    conta = conta_actual()
    if conta:                                             # signed in: the form starts with the account's details
        lugares_do_formulario = _lugares_para_escolher()
        for campo, valor in (("telefone", inscricoes.mostrar_telefone(conta["telefone"]) if conta.get("telefone") else ""), ("nome", conta.get("nome", "")),
                             ("lugar", conta.get("lugar") if conta.get("lugar") in lugares_do_formulario else "")):
            if valor and f"{chave}_{campo}" not in st.session_state:
                st.session_state[f"{chave}_{campo}"] = valor
    with st.form(f"form_{chave}", clear_on_submit=False, border=False):
        telefone = st.text_input(t("O seu número de WhatsApp"), placeholder="84 123 4567", key=f"{chave}_telefone", max_chars=20)
        lugar = st.selectbox(t("Onde vive?"), [""] + _lugares_para_escolher() + [outro], key=f"{chave}_lugar",
                             format_func=lambda v: t("Escolha o seu bairro ou lugar") if v == "" else t("Outro lugar / não sei") if v == outro else v)
        nome = st.text_input(t("O seu nome completo"), key=f"{chave}_nome", max_chars=60, placeholder=t("Nome e apelido"),
                             help=t("As mensagens tratam-no pelo nome."))
        escolher = lambda campo: (lambda v: t(inscricoes.NAO_DIZ) if v == "" else t(inscricoes.OPCOES[campo][v]))
        coluna_a, coluna_b = st.columns(2)
        sexo = coluna_a.selectbox(t("Sexo (opcional)"), [""] + list(inscricoes.OPCOES["sexo"]), key=f"{chave}_sexo", format_func=escolher("sexo"))
        idade = coluna_b.selectbox(t("Idade (opcional)"), [""] + list(inscricoes.OPCOES["faixa_etaria"]), key=f"{chave}_idade", format_func=escolher("faixa_etaria"))
        profissao = st.selectbox(t("Profissão ou ocupação (opcional)"), [""] + list(inscricoes.OPCOES["profissao"]), key=f"{chave}_profissao",
                                 format_func=escolher("profissao"))
        T.html(f"<div class='ete-miudo' style='margin:-4px 0 6px 0'>{t('Sexo, idade e profissão são opcionais. Ajudam-nos a dar o conselho certo a cada pessoa (por exemplo, a quem tem 60 anos ou mais, ou a quem pesca no rio) e a saber quem estamos a avisar.')}</div>")
        lingua = st.radio(t("Língua das mensagens"), list(L.LINGUAS), index=list(L.LINGUAS).index(L.lingua()), horizontal=True, key=f"{chave}_lingua",
                          format_func=lambda k: L.NOMES[k])
        aceito = st.checkbox(t("Aceito receber alertas de cheia do Eyes to Earth no WhatsApp. O meu número só é usado para isto e posso sair quando quiser."), key=f"{chave}_aceito")
        enviado = st.form_submit_button(t("Quero receber os alertas"), type="primary", width="stretch")
    if not enviado:
        return False
    if not lugar:
        T.note("Escolha onde vive (ou «Outro lugar / não sei»).", "aviso")
        return False
    erro_no_nome = contas.erro_no_nome(nome)
    if erro_no_nome:                                      # the messages speak to the person by the full name
        aviso_da_conta(erro_no_nome)
        return False
    try:
        resultado, numero = inscricoes.inscrever(telefone, "" if lugar == outro else lugar, lingua, contas.limpar_nome(nome), aceito, sexo=sexo, faixa_etaria=idade,
                                                 profissao=profissao)
    except Exception:
        T.note("Não foi possível guardar agora. Tente de novo mais tarde.", "aviso")
        return False
    if resultado == "sem_consentimento":
        T.note("Para receber os alertas, marque a caixa «Aceito».", "aviso")
    elif resultado == "numero_invalido":
        T.note("Este número não parece certo. Escreva o número de WhatsApp com 9 algarismos, por exemplo 84 123 4567.", "aviso")
    elif resultado == "ja_inscrito":
        T.note(t("O número {numero} já está inscrito. Não precisa de fazer mais nada.", numero=numero))
        return True
    else:
        enviada = False
        try:                                              # the welcome at once, with the situation of the next 10 days (official API only)
            enviada, _ = alertas_whatsapp.boas_vindas_agora(inscricoes.normalizar_telefone(telefone) or "")
        except Exception:
            enviada = False
        frase = ("Acabámos de lhe enviar uma mensagem com a situação dos próximos 10 dias." if enviada
                 else "Em breve recebe uma mensagem de boas-vindas, com a situação dos próximos 10 dias.")
        T.card(t("Pronto! Está inscrito."), "<p>" + t("Vamos escrever para <b>{numero}</b> só quando houver perigo de cheia, e quando o perigo passar.", numero=numero)
               + " " + t(frase) + "</p>", "WhatsApp", "suave")
        return True
    return False


def convite_alertas() -> None:
    """On the first visit: a friendly invitation to receive the alerts. It can always be closed
    (the alert itself stays visible to everyone, signed up or not)."""
    def fechar() -> None:
        st.session_state["_convite_visto"] = True

    @st.dialog(t("Receba os alertas de cheia no seu WhatsApp"), width="medium", on_dismiss=fechar)
    def janela() -> None:
        T.html(f"<div class='ete-convite'><div class='ic'>{T.icon('mensagem', 30)}</div><ul>"
               f"<li>{t('Só escrevemos quando houver <b>perigo de cheia</b> no rio Incomáti, e quando o perigo passar.')}</li>"
               f"<li>{t('A mensagem diz <b>que lugares podem alagar</b> e o que fazer.')}</li>"
               f"<li>{t('É grátis e pode sair quando quiser.')}</li></ul></div>")
        # A click inside a dialog only reruns the dialog itself, which would draw it again: the whole page
        # is rerun instead, and the invitation (now marked as seen) is no longer drawn, so the dialog closes.
        inscrito = formulario_inscricao("convite")
        if st.button(t("Fechar") if inscrito else t("Agora não"), key="convite_fechar" if inscrito else "convite_agora_nao",
                     type="primary" if inscrito else "tertiary", width="stretch"):
            fechar()
            st.rerun()

    janela()


@st.cache_data(show_spinner=False, ttl=6 * 3600)
def _cartao(lingua: str, emitido: str, versao: float) -> bytes | None:
    return alertas_whatsapp.cartao(BOLETIM, alertas_whatsapp.prevista_da_cor(), lingua)


def cartao_do_dia(lingua: str) -> bytes | None:
    """The situation card of today's bulletin (drawn once per bulletin and language)."""
    return _cartao(lingua, str(BOLETIM.get("emitido_utc", "")), V)



def mensagem_para_os_lideres() -> None:
    """Today's short message for community leaders, ready to forward by WhatsApp or SMS to people without internet."""
    with T.guard("a mensagem para os líderes"):
        mensagem = leitor.caminho(CAMADAS["boletim"].get("mensagem", "")) if CAMADAS["boletim"].get("mensagem") else None
        if mensagem is None or not mensagem.is_file():
            return
        T.section("A mensagem de hoje, para os líderes comunitários", "Um texto curto para partilhar por WhatsApp ou SMS com quem não tem internet.", "Para as comunidades", "lideres")
        import re

        # plain text: a message written before 2026-11-15 began with a coloured circle (one emoji makes an SMS go in many more parts)
        texto = re.sub("[\U0001F300-\U0001FAFF\u2600-\u27BF\u2B00-\u2BFF\uFE0F]", "", mensagem.read_text()).lstrip()
        a, b = st.columns([3, 2], gap="medium")
        with a:
            T.message(texto)
        with b:
            T.card("Como usar", f"<p>{t('Descarregue o texto e envie-o tal como está. Foi escrito para caber num SMS e para se perceber sem mapas nem gráficos.')}</p>"
                   f"<p class='ete-miudo'>{t('É actualizado todas as manhãs, com o boletim.')}</p>"
                   + (f"<p class='ete-miudo'>{t('A mensagem fica sempre em português, a língua das comunidades de Marracuene.')}</p>" if L.lingua() != "pt" else ""))
            st.download_button(t("Descarregar a mensagem"), texto.encode("utf-8"), "mensagem_ete.txt", "text/plain")


def pagina_alertas() -> None:
    T.page_head("Alertas no WhatsApp", "Avisamos no seu telefone quando houver perigo de cheia",
                "Deixe o seu número e onde vive. Quando o rio Incomáti estiver perto de alagar Marracuene, recebe uma mensagem curta no WhatsApp.")
    T.steps([("Inscreva-se", "Escreva o seu número de WhatsApp e escolha onde vive. Demora um minuto."),
             ("Logo a seguir", "Recebe uma mensagem com a situação dos próximos 10 dias: cheias e cor da água, dia a dia."),
             ("Só em caso de perigo", "Depois só escrevemos quando o alerta for laranja ou vermelho, e outra vez quando o perigo passar."),
             ("Lugares e conselhos", "Cada mensagem diz que lugares podem alagar, o que fazer e traz a ligação para esta plataforma.")])
    esquerda, direita = st.columns([1.15, 1], gap="large")
    with esquerda:
        with st.container(key="caixa_inscricao"):
            T.subtitle("Quero receber os alertas")
            formulario_inscricao("pagina")
    with direita:
        T.subtitle("A mensagem que recebe ao inscrever-se")
        with T.guard("o exemplo de mensagem"):
            lingua = L.lingua()
            prevista = alertas_whatsapp.prevista_da_cor()
            texto, _ = alertas_whatsapp.mensagem("boas_vindas", {"lugar": "Marracuene", "lingua": lingua}, BOLETIM, serie("lugares_por_ordem", V), CONSELHOS,
                                                 prevista, como_no_modelo=True)
            T.whatsapp_preview(cartao_do_dia(lingua), texto, alertas_whatsapp.RODAPE[lingua], list(alertas_whatsapp.BOTOES[lingua]), f"{EMITIDO:%H:%M}")
            T.caption("Com os números de hoje. A mensagem chega na língua que escolher, com o seu lugar e um conselho para o seu perfil.")
        T.card("O seu número está protegido", "<p>" + t("Fica guardado só para enviar estes alertas. Não aparece na plataforma, não é partilhado nem vendido, "
               "e é apagado da lista quando pede para sair.") + "</p><p>" + t("O sexo, a idade e a profissão, se os indicar, só servem para escolher o conselho da mensagem "
               "e para a equipa saber, em números, que pessoas estão a ser avisadas.") + "</p>", "Privacidade", "suave")
    T.section("Deixar de receber", "Escreva o número inscrito. As mensagens param no envio seguinte.", "Sair", "sair")
    with st.container(key="caixa_sair"), st.form("form_sair", border=False):
        numero = st.text_input(t("O seu número de WhatsApp"), placeholder="84 123 4567", key="sair_telefone", max_chars=20)
        sair = st.form_submit_button(t("Deixar de receber os alertas"))
    if sair:
        try:
            resultado = inscricoes.cancelar(numero)
        except Exception:
            resultado = "erro"
        T.note({"ok": "Pronto. Este número já não vai receber alertas.", "nao_encontrado": "Este número não está na lista de alertas.",
                "numero_invalido": "Este número não parece certo. Escreva o número de WhatsApp com 9 algarismos, por exemplo 84 123 4567.",
                "erro": "Não foi possível guardar agora. Tente de novo mais tarde."}[resultado], "info" if resultado == "ok" else "aviso")
    mensagem_para_os_lideres()
    T.note("Serviço experimental. Não substitui os avisos oficiais do INGD, do INAM e da ARA-Sul. Se as autoridades derem uma ordem, siga a ordem.", "aviso")


# ----------------------------------------------------------------------------- 5. the project: objectives, trust, machine learning, data
ENTRADAS = {"vv": "radar VV", "vh": "radar VH", "vv_p10": "VV mais escuro do mês", "vh_p10": "VH mais escuro do mês", "vv_vh_ratio": "razão VV/VH", "ratio_p10": "razão nos dias mais escuros",
            "dvv_p10": "VV face à época seca", "dvh_p10": "VH face à época seca", "s1_angle": "ângulo do radar", "hand": "altura acima do rio (HAND)", "slope": "declive",
            "twi": "índice de humidade do terreno", "elevation": "altitude", "log_upstream_area": "área drenada a montante", "distance_to_river_m": "distância ao rio",
            "distance_to_water_m": "distância à água permanente", "distance_to_stream_m": "distância à linha de água", "lq": "caudal do dia", "lq_mean7": "caudal médio de 7 dias",
            "lq_max7": "caudal máximo de 7 dias", "dq3": "variação do caudal em 3 dias", "p3": "chuva de 3 dias", "p7": "chuva de 7 dias", "p30": "chuva de 30 dias",
            "sin": "época do ano", "cos": "época do ano", "t_h": "altura da maré", "t_dh": "maré a encher ou a vazar", "t_range": "amplitude da maré",
            "last_ndti": "última medição por satélite", "last_age": "idade dessa medição", "last_t_h": "maré nessa medição", "last_lq": "caudal nessa medição", "has_last": "há medição recente"}


@st.cache_data(show_spinner=False)
def ml(nome: str, versao: float) -> pd.DataFrame:
    ficheiro = CAMADAS["modelos_ml"]["tabelas"].get(nome)
    return pd.read_csv(leitor.caminho(ficheiro)) if ficheiro else pd.DataFrame()


@st.cache_data(show_spinner=False)
def fichas(versao: float) -> dict:
    return json.loads(leitor.caminho(CAMADAS["modelos_ml"]["ficheiro"]).read_text())


def ficha_do_modelo(chave: str, pergunta: str, onde: str) -> None:
    m = fichas(V)["modelos"].get(chave, {})
    entradas = list(dict.fromkeys(ENTRADAS.get(f, f) for f in m.get("features", []) if not str(f).startswith("troco=")))
    parametros = ", ".join(f"{k} = {v}" for k, v in (m.get("params") or {}).items())
    corpo = f"<p style='margin:0 0 8px 0'><b>{t('Pergunta:')}</b> {t(pergunta)}</p>"
    if m.get("algorithm") or parametros:
        corpo += f"<p style='margin:0 0 8px 0'><b>{t('Algoritmo:')}</b> {m.get('algorithm', 'gradient boosting')}" + (f" ({parametros})" if parametros else "") + "</p>"
    if m.get("rows"):
        corpo += f"<p style='margin:0 0 8px 0'><b>{t('Exemplos de treino:')}</b> {num(m['rows'])}</p>"
    if entradas:
        corpo += f"<p style='margin:0 0 6px 0'><b>{t('O que o modelo recebe:')}</b></p>" + "".join(T.chip(e) for e in entradas)
    corpo += (f"<p class='ete-miudo' style='margin:10px 0 0 0'><b>{t('Onde aparece na plataforma:')}</b> {t(onde)}"
              + (f" · {t('treinado em {dia}', dia=str(m['created_utc'])[:10])}" if m.get("created_utc") else "") + "</p>")
    T.card("", corpo, "Ficha do modelo")


def modelos_dos_mapas() -> None:
    """The two models behind the forecast maps of the water colour, and how they did in their tests."""
    pasta = leitor.DADOS / "modelos"
    T.steps([("Modelo de Marracuene", "Prevê a cor da água em Marracuene, manhã a manhã, até 30 dias: usa o caudal previsto, a maré calculada, a época do ano e a última imagem."),
             ("Modelo do mapa", "Para cada ponto do rio (píxeis de 20 m), aprendeu com as imagens de 2017 a 2025 como a sua cor acompanha a de Marracuene e a maré."),
             ("Mapa previsto", "A cor prevista para Marracuene entra no modelo do mapa e cada ponto do rio é pintado com a sua cor."),
             ("Sempre testado", "Cada ano é previsto por modelos que nunca o viram; o mapa é testado em 2026, que ficou de fora do treino.")])
    with T.guard("os testes do modelo de Marracuene"):
        ficheiro = pasta / "teste_modelo_marracuene.csv"
        if ficheiro.is_file():
            teste = pd.read_csv(ficheiro)
            T.subtitle("Quantas vezes acertou, conforme a antecedência")
            quadro = teste.pivot(index="metodo", columns="antecedencia_dias", values="classe_vizinha").mul(100).round(0)
            quadro.columns = [t("{d} dia", d=c) if c == 1 else t("{d} dias", d=c) for c in quadro.columns]
            T.table(quadro.rename_axis(t("Método")).reset_index())
            T.caption("Percentagem de manhãs em que a cor prevista saiu certa ou no degrau ao lado (os cinco degraus do mapa), em todos os anos de teste. "
                      "«Sem saber o caudal» mostra o que resta se a previsão do caudal falhar por completo.")
    with T.guard("o teste do modelo do mapa"):
        ficheiro = pasta / "teste_modelo_mapa.json"
        if ficheiro.is_file():
            teste = json.loads(ficheiro.read_text())
            T.subtitle("O modelo do mapa, testado em 2026")
            T.table(pd.DataFrame(teste["metodos"]).rename(columns={"metodo": "Método", "classe_certa": "Cor certa (%)", "classe_vizinha": "Certa ou ao lado (%)", "mae": "Erro típico (índice)"}))
            T.caption(t("{dias} imagens de 2026, que o modelo nunca viu. Com a cor real de Marracuene em cada imagem, o modelo pinta cada ponto do rio; "
                        "compara-se com o que o satélite mediu nesse ponto.", dias=teste["dias"]))



def modelos_em_detalhe() -> None:
    """The machine learning of the platform: the models at a glance, then each one in a closed box (data, tests, limits)."""
    if "modelos_ml" not in CAMADAS:
        T.note("O pacote ainda não tem as fichas dos modelos.", "aviso")
        return
    T.note("**O nível de alerta em si não é machine learning.** Vem de regras simples e transparentes: o caudal e a chuva previstos comparados com 25 anos de história. "
           "Foi uma escolha: um alerta tem de se poder explicar numa frase.")
    T.feature_cards([
        {"olho": "Cor da água · Gradient Boosting", "titulo": "Prever a cor da água", "texto": "Como vai estar a água nas próximas 4 semanas, em cada ponto do rio?",
         "resultado": "77 a 84 % certo ou no degrau ao lado", "nota": "cada ano previsto por modelos que nunca o viram", "chips": ["Qualidade da água", "Início"]},
        {"olho": "Turbidez · Gradient Boosting", "titulo": "Prever a turbidez", "texto": "A água vai estar mais turva do que o habitual nas próximas manhãs?", "resultado": "AUC 0,87 a 0,89",
         "nota": "ano deixado de fora; outro satélite como juiz", "chips": ["Qualidade da água", "Início"]},
        {"olho": "Módulo Q · Isolation Forest", "titulo": "Meses invulgares", "texto": "Que meses fogem ao normal de cada troço?", "resultado": "5 % dos meses",
         "nota": "sem rótulos: aponta, não decide", "chips": ["Qualidade da água"]},
        {"olho": "Módulo Q · Mann-Kendall sazonal", "titulo": "Tendências", "texto": "A água está a mudar em 20 anos?", "resultado": "Nenhuma confirmada",
         "nota": "repetido por era de satélite", "chips": ["Qualidade da água"]},
        {"olho": "Modelo B · XGBoost", "titulo": "Detectar água por radar", "texto": "Onde está a água neste mês, mesmo com nuvens?", "resultado": "IoU 0,91 · F1 0,95",
         "nota": "cheia de Janeiro de 2026, blocos de 3 km", "chips": ["Cheias"]},
        {"olho": "Modelo C · XGBoost", "titulo": "Prever o caudal", "texto": "Que caudal terá o rio daqui a 1 a 7 dias?", "resultado": "Melhor do que repetir hoje",
         "nota": "testado em 2022 a 2026", "chips": ["Cheias: segunda opinião"]},
        {"olho": "Modelo A · XGBoost", "titulo": "Risco do terreno", "texto": "Onde o terreno favorece cheias?", "resultado": "AUC 0,96",
         "nota": "completa as zonas de aviso fora da área do Copernicus; o mapa não é mostrado", "chips": []}])
    with st.expander(t("Como os modelos foram treinados e testados")):
        dados = fichas(V)["dados_de_treino"]
        imagens = dados.get("imagens_modulo_q", {})
        T.kpis([{"rotulo": "Modelos treinados", "valor": "6", "nota": "mais 2 métodos de análise"}, {"rotulo": "Algoritmos comparados", "valor": "4", "nota": "em cada modelo de cheias"},
                {"rotulo": "Linhas nas tabelas de treino", "valor": num(dados.get("train_historico", {}).get("linhas", 0) + dados.get("train_recente", {}).get("linhas", 0)), "nota": "píxeis rotulados, 2006 a 2026"},
                {"rotulo": "Imagens da água analisadas", "valor": num(imagens.get("imagens")), "nota": "três famílias de satélites"},
                {"rotulo": "Anos de dados", "valor": "20", "nota": "2006 a 2026"}])
        T.steps([("Dados abertos", "Radar e imagens ópticas de satélite, chuva, caudal e terreno: 20 anos, sempre com a contagem de observações por píxel."),
                 ("Rótulos independentes", "A \"resposta certa\" vem de fora: água mensal do JRC e os mapas da cheia de 2026 do Copernicus. Um modelo nunca é testado com rótulos feitos por ele."),
                 ("Vários algoritmos", "Regressão logística, Random Forest, Gradient Boosting e XGBoost, com as regras de escolha escritas antes de ver os resultados."),
                 ("Testes exigentes", "Blocos de 3 km para que píxeis vizinhos não entrem no treino e no teste; anos inteiros deixados de fora; um segundo satélite como juiz."),
                 ("Produção", "Os modelos escolhidos correm todos os dias e alimentam o alerta, os mapas e a previsão da água.")])

    with st.expander(t("Prever a cor da água até 30 dias (os mapas)")):
        modelos_dos_mapas()

    with st.expander(t("Prever a turbidez das próximas manhãs")):
        ficha_do_modelo("modelo_turbidez", "nas próximas manhãs, a água vai estar mais turva do que o habitual?", "Qualidade da água → As próximas semanas")
        with T.guard("o caminho até ao modelo de turbidez"):
            passos = ml("turbidez_modelo", V)
            curtos = {"modelo final: última medição há 1 dia ou mais": "modelo final, medição de ontem", "modelo final: última medição há 3 dias ou mais": "modelo final, medição de há 3 dias",
                      "modelo final: última medição há 5 dias ou mais": "modelo final, medição de há 5 dias", "modelo final: última medição há 10 dias ou mais": "modelo final, medição de há 10 dias",
                      "modelo final: sem medição recente": "modelo final, sem medição recente", "passo anterior: maré só pela fase M2": "só com a fase da maré",
                      "sem maré": "caudal e chuva, sem maré", "referência: época do ano": "só a época do ano",
                      "modelo final no Landsat 8/9 (outro satélite): todos os anos": "modelo final, noutro satélite", "modelo final no Landsat antes de 2017 (outro satélite e outros anos)": "modelo final, noutro satélite e noutros anos"}
            passos = passos.assign(modelo=passos["modelo"].map(lambda m: curtos.get(m, m)))
            ordem = ["só a época do ano", "caudal e chuva, sem maré", "só com a fase da maré", "modelo final, sem medição recente", "modelo final, medição de há 10 dias",
                     "modelo final, medição de há 5 dias", "modelo final, medição de há 3 dias", "modelo final, medição de ontem", "modelo final, noutro satélite",
                     "modelo final, noutro satélite e noutros anos"]
            passos = passos.set_index("modelo").reindex([o for o in ordem if o in set(passos["modelo"])]).reset_index()
            passos["modelo"] = passos["modelo"].map(t)
            T.subtitle("Como se chegou a este modelo")
            grafico(G.ranked_bars(passos, "modelo", "auc", "AUC para \"mais turva do que o habitual\" (0,5 = acaso)", t("modelo final"), (0.5, 1), 0.5))
            T.caption("De cima para baixo: só a época do ano; juntando caudal e chuva (pouco ganho); juntando a maré (o salto); e por fim a maré completa e a última medição por satélite. "
                      "As duas últimas linhas são o teste mais duro: o modelo foi treinado só com o Sentinel-2 e acerta igualmente nas medições de outro satélite, incluindo anos anteriores.")
            habilidade = pd.DataFrame(CATALOGO["modelos"].get("turbidez", {}).get("skill") or [])
            if len(habilidade):
                T.subtitle("Medidas de acerto")
                T.table(habilidade.rename(columns={"modelo": "Modelo", "dias": "Dias", "r2": "R²", "mae": "Erro típico", "auc": "AUC", "bss": "Ganho face à época do ano"}))
        T.note("Limites: prevê a cor da água à hora de passagem do satélite (cerca das 9h30); é um índice relativo, sem medições no rio; a maré é calculada, não medida.", "aviso")

    with st.expander(t("Vigiar a qualidade do rio (Módulo Q)")):
        T.card("", "<p style='margin:0'>" + t("O Módulo Q acompanha nove troços do rio, da fronteira à foz. Sem medições no rio não se pode treinar um modelo que \"saiba\" a qualidade da água. "
               "Por isso a inteligência aqui é de outro tipo: <b>aprender o que é normal</b> em cada troço e em cada mês, e <b>apontar o que foge ao normal</b>.") + "</p>",
               "Como o machine learning entra na qualidade")
        T.steps([("Normal de cada troço", "Mediana e percentis de cada mês do ano, com todos os anos disponíveis."), ("Meses invulgares", "Isolation Forest sobre a cor, as plantas e o desvio face ao esperado."),
                 ("Tendências", "Mann-Kendall sazonal, repetido por era de satélite para não confundir mudança de sensor com mudança do rio."),
                 ("Esperado pela chuva e caudal", "Gradient Boosting imagem a imagem. Só tem acerto útil na foz; nos outros troços não é usado para avisos.")])
        with T.guard("o modelo de turbidez esperada"):
            esperado = ml("turbidez_esperada_por_troco", V)
            if len(esperado):
                T.subtitle("A chuva e o caudal explicam a cor da água? Depende do troço")
                grafico(G.ranked_bars(esperado.assign(r2=esperado["r2_chuva_caudal_mare"].clip(lower=0)), "nome", "r2", "Parte da variação explicada em anos não vistos (R²)", None, (0, 1), 0.3))
                T.caption("Só acima da linha tracejada (0,3) o modelo explica o suficiente para se poder dizer \"esta turbidez não vem da chuva\". Hoje isso só acontece na foz. "
                          "É um resultado negativo, e fica aqui escrito: a ideia inicial do plano não se confirmou na maior parte do rio.")

    with st.expander(t("Detectar água por radar (Modelo B)")):
        ficha_do_modelo("modelo_b_radar", "onde há água em cada mês, mesmo com nuvens?", "Cheias → O rio visto do espaço; Vinte anos do rio")
        a, b = st.columns(2, gap="medium")
        with a, T.guard("a comparação de algoritmos"):
            T.subtitle("Quatro algoritmos, o mesmo teste")
            grafico(G.ranked_bars(ml("modelo_b_algoritmos", V), "algoritmo", "iou", "IoU na cheia de Janeiro de 2026 (1 = perfeito)", "XGBoost"))
        with b, T.guard("o teste das entradas"):
            T.subtitle("Que dados ajudam o modelo")
            grafico(G.ranked_bars(ml("modelo_b_entradas", V), "features", "iou", "IoU na cheia de Janeiro de 2026"))
        T.caption("IoU: da área que o modelo ou a referência dizem ser água, que parte é comum aos dois. A referência são os mapas do Copernicus EMS, feitos por analistas. "
                  "Uma regra simples (um só limiar de radar) já chega a 0,88: o modelo acrescenta pouco, mas de forma consistente em todos os blocos.")
        with T.guard("a validação dos modelos"):
            if "validacao_cheias" in CAMADAS:
                T.subtitle("Medidas de acerto dos modelos de cheias")
                T.table(serie("validacao_cheias", V))
                T.caption("IoU, F1 e Kappa vão de 0 a 1 (quanto mais alto, melhor). ROC-AUC: 0,5 é acaso, 1 é perfeito.")
        T.note("Limite: validado numa única cheia. Em zonas construídas marca água a mais; por isso os avisos usam as zonas da cheia real, não este mapa.", "aviso")

    with st.expander(t("Prever o caudal (Modelo C)")):
        ficha_do_modelo("modelo_c_caudal", "que caudal terá o rio nos próximos dias, só com a chuva que já caiu?", "Cheias → tabela da previsão, coluna «Segunda opinião»")
        with T.guard("o acerto do modelo de caudal"):
            acerto = pd.DataFrame(fichas(V)["modelos"].get("modelo_c_caudal", {}).get("skill") or [])
            if len(acerto):
                grafico(G.lead_skill(acerto))
                T.caption("Testado em 2022 a 2026, anos que o modelo não viu. Ganha a quem repete o valor de hoje em todos os prazos, mas reage tarde ao início das cheias: "
                          "por isso é uma segunda opinião, e o alerta usa os 51 cenários do GloFAS.")

    with st.expander(t("Risco do terreno (Modelo A)")):
        ficha_do_modelo("modelo_a_terreno", "que zonas o terreno torna mais fáceis de alagar?",
                        "completa as zonas de aviso fora da área mapeada pelo Copernicus; o mapa em si não é mostrado, porque as classes são largas de mais para avisar")
        a, b = st.columns(2, gap="medium")
        with a, T.guard("a comparação de algoritmos"):
            T.subtitle("Quatro algoritmos, o mesmo teste")
            grafico(G.ranked_bars(ml("modelo_a_algoritmos", V), "algoritmo", "auc_cheia_2026", "AUC na cheia de 2026 (0,5 = acaso)", "XGBoost", (0.5, 1)))
        with b, T.guard("o teste por classe"):
            T.subtitle("As classes de risco batem com a cheia real?")
            classes = ml("modelo_a_teste_2026", V)
            classes = classes.rename(columns={classes.columns[0]: "classe"})
            grafico(G.ranked_bars(classes, "classe", "parte_da_classe_que_alagou", "Parte da classe que alagou em Janeiro de 2026"))
        T.caption("O modelo foi treinado com dados até 2019, afinado em 2020-21 e testado numa cheia que nunca viu. Na classe \"muito alta\" alagou quase tudo; na \"baixa\", quase nada. "
                  "A chuva e o caudal foram deixados de fora deste modelo de propósito, para ele descrever só o terreno.")

    with st.expander(t("Qualidade dos dados")):
        T.steps([("Nunca inventar dados", "Um mês sem imagem limpa fica vazio. Um satélite que não existia num ano fica marcado como ausente."),
                 ("Fontes comparadas entre si", "No período em que todas existem (2017 a 2021), cada par de fontes foi comparado."),
                 ("Contagem de observações", "Cada composição mensal guarda quantas imagens limpas viu cada píxel."),
                 ("Dois satélites como juízes", "A cor da água só é usada onde o Sentinel-2 e o Landsat concordam no mesmo dia."),
                 ("Fórmulas testadas com medições reais", "As fórmulas de turbidez foram testadas no GLORIA, com medições em centenas de massas de água.")])
        a, b = st.columns(2, gap="medium")
        with a, T.guard("a sobreposição entre fontes"):
            T.subtitle("Fontes diferentes concordam? (2017 a 2021)")
            pares = ml("sobreposicao_entre_fontes", V)
            pares = pares.assign(par_variavel=pares["par"] + " · " + pares["variável"]).dropna(subset=["r2"])
            grafico(G.ranked_bars(pares, "par_variavel", "r2", "R² entre as duas fontes (1 = concordância total)"))
        with b, T.guard("a concordância entre satélites"):
            T.subtitle("A cor da água: dois satélites no mesmo dia")
            pares = ml("concordancia_entre_satelites", V).dropna(subset=["r_ndti"])
            grafico(G.ranked_bars(pares, "troco", "r_ndti", "Correlação do índice de cor entre os dois satélites", None, (0, 1), 0.7))
            T.caption("Abaixo da linha tracejada (0,7) o troço fica marcado com fiabilidade reduzida e não gera avisos.")
        with T.guard("as fórmulas de turbidez"):
            T.subtitle("Fórmulas de turbidez testadas com medições reais (GLORIA)")
            T.table(ml("validacao_gloria", V))
            T.caption("fator_tipico 2,5 quer dizer que uma estimativa isolada pode ser duas vezes e meia maior ou menor do que a medição. Por isso a plataforma mostra classes, não números.")

    with st.expander(t("O que testámos e rejeitámos")):
        T.note("Um sistema é tão sério quanto os testes que deixa falhar. Estes foram feitos e <b>não passaram</b>, e por isso não estão na plataforma.", "neutra")
        T.table(pd.DataFrame([
            {"O que se tentou": "Harmonizar o Landsat 5/7 com os coeficientes publicados", "Resultado": "A água deixava de se distinguir (índice de água de 0,68 para 0,16)", "Decisão": "Desligado"},
            {"O que se tentou": "Radar pela mediana do mês", "Resultado": "Perdia as cheias curtas (AUC 0,75 contra 0,97 com os dias mais escuros)", "Decisão": "Usar os dias mais escuros do mês"},
            {"O que se tentou": "Turbidez em FNU pela banda do infravermelho", "Resultado": "Os dois satélites não concordam (correlação 0,21)", "Decisão": "Rejeitada; a banda do vermelho fica só como estimativa"},
            {"O que se tentou": "Clorofila pelo índice NDCI", "Resultado": "Segue o sedimento, não as algas (correlação 0,81 com a turbidez)", "Decisão": "Não é reportada"},
            {"O que se tentou": "Prever a turbidez só com caudal, chuva e época", "Resultado": "Não ganhava à simples época do ano", "Decisão": "Só passou com a maré"},
            {"O que se tentou": "Juntar vento, chuva local e chuva por sub-bacia", "Resultado": "Ganho de 0,003 em AUC", "Decisão": "Fora: mais uma coisa que pode falhar"},
            {"O que se tentou": "Turbidez esperada mês a mês (ideia do plano)", "Resultado": "Pior do que a época do ano em todos os troços", "Decisão": "Substituída por imagem a imagem; só usada na foz"},
            {"O que se tentou": "Tendências de 20 anos na cor da água", "Resultado": "Desaparecem quando se testa a mudança de satélite de 2013", "Decisão": "Nenhuma é afirmada"},
            {"O que se tentou": "Usar as classes do Modelo A para avisar", "Resultado": "Largas de mais (53 mil edifícios em risco \"médio\")", "Decisão": "Avisos pelas zonas da cheia real"}]))


def pagina_sobre() -> None:
    """The project, read from top to bottom: the two objectives, why, for whom, how it works, how far to trust it, the models, the data, the supporters."""
    T.page_head("O projecto", "Olhos no céu para proteger quem vive junto ao rio",
                "O <b>Eyes to Earth</b> usa imagens de satélite e machine learning para vigiar a qualidade da água do rio Incomáti e avisar das cheias em Marracuene, província de Maputo. "
                "Transforma dados abertos, que já existem mas não chegam às pessoas, em alertas e mapas simples, actualizados todos os dias.")

    T.section("Os nossos dois objectivos", "Uma plataforma com dois módulos, que avisa de forma automática e em linguagem simples.", "Para quê")
    a, b = st.columns(2, gap="medium")
    with a:
        T.card("Qualidade: vigiar a água do rio", "<p>" + t("Acompanhar por satélite o que muda a cor da água (sedimentos e plantas à superfície) em nove troços, "
               "da fronteira à foz, e dizer quando a água está mais turva do que é costume.") + "</p>"
               + T.chip("9 troços") + T.chip("20 anos de imagens") + T.chip("previsão das próximas manhãs"), "Módulo 1")
        st.button(t("Ver a qualidade da água"), on_click=ir_para, args=("agua",), key="proj_agua", type="primary")
    with b:
        T.card("Quantidade: avisar das cheias", "<p>" + t("Prever o caudal do rio com dias de avanço, dar um nível de alerta (verde, amarelo, laranja, vermelho) "
               "e mostrar que lugares a água alcança primeiro.") + "</p>"
               + T.chip("alerta para 10 dias") + T.chip("zonas de aviso com nomes") + T.chip("mensagem para os líderes"), "Módulo 2")
        st.button(t("Ver a previsão de cheias"), on_click=ir_para, args=("cheias",), key="proj_cheias", type="primary")

    T.section("O problema", "Duas coisas faltam a quem vive no Baixo Incomáti.", "Porquê")
    T.feature_cards([
        {"icone": "gota", "titulo": "Água que ninguém acompanha", "texto": "A água do rio é usada todos os dias para regar, pescar e para as casas. "
         "Na bacia do Incomáti não há nenhuma estação pública de qualidade da água num arquivo mundial que possa ser consultado por todos."},
        {"icone": "onda", "titulo": "Cheias sem aviso", "texto": "As comunidades do Baixo Incomáti (agricultores, pescadores, famílias) vivem numa planície que alaga. "
         "Quando o rio sobe, a informação que existe nos satélites e nos modelos não chega a tempo a quem precisa dela."}])
    with T.guard("os números do problema"):
        if "factos" in CAMADAS:
            bruto = serie("factos", V)
            f = bruto.set_index(bruto.columns[0])["valor"]
            _, completos = anos_completos()
            T.kpis([{"rotulo": "Estações públicas de qualidade da água", "valor": num(f["estacoes_publicas_de_qualidade_na_bacia"]), "nota": "na bacia (arquivo GEMStat)"},
                    {"rotulo": "Anos com alerta laranja ou vermelho", "valor": t("{n} em {total}", n=int(((completos["laranja"] + completos["vermelho"]) > 0).sum()), total=len(completos)),
                     "nota": "anos de Outubro a Setembro"},
                    {"rotulo": "Área alagada em Janeiro de 2026", "valor": num(f["area_alagada_cheia_grande_km2"]), "unidade": "km²", "nota": "no distrito"},
                    {"rotulo": "Edifícios na zona alagada", "valor": num(f["edificios"])}, {"rotulo": "Terras agrícolas alagadas", "valor": num(f["terras_agricolas_km2"]), "unidade": "km²"}])

    T.section("Para quem", "Quatro grupos de pessoas, a mesma informação, dita de maneira que sirva a cada um.", "Quem serve")
    T.feature_cards([
        {"icone": "casa", "titulo": "Famílias e líderes comunitários", "texto": "Saber, numa frase, se há perigo e o que fazer. A mensagem diária segue por WhatsApp ou SMS."},
        {"icone": "campo", "titulo": "Agricultores e pescadores", "texto": "Saber quando o rio vai subir e como está a água que usam."},
        {"icone": "escudo", "titulo": "Autoridades locais e protecção civil", "texto": "Mapas de onde a água chega primeiro e o que está exposto, como apoio aos avisos oficiais."},
        {"icone": "livro", "titulo": "Estudantes e investigadores", "texto": "Dados abertos, métodos explicados e resultados que se podem repetir."}])

    T.section("Como funciona", "Só com dados abertos e de acesso imediato: nenhuma informação depende de pedidos a instituições.", "O método")
    T.steps([("Satélites", "Sentinel-1 (radar), Sentinel-2 e Landsat (imagem), mais chuva, caudal e terreno: 20 anos de dados."),
             ("Machine learning", "Modelos que detectam água, prevêem o caudal, a turbidez e a cor da água. Cada um foi comparado com alternativas e testado em dados que nunca viu."),
             ("Regras de alerta claras", "O nível de alerta compara o caudal e a chuva previstos com 25 anos de história."),
             ("Todos os dias", "Um boletim, uma mensagem curta e esta plataforma são actualizados de manhã, de forma automática.")])
    T.card("Nunca inventar dados.", "<p>" + t("Um mês sem imagem limpa fica vazio. Um satélite que não existia num ano fica marcado como ausente. "
           "Os testes que falharam estão publicados ao lado dos que passaram. E o que o satélite não vê (micróbios, químicos, pH) é dito com todas as letras.") + "</p>",
           "Uma regra que não se quebra", "tinta")

    todas_as_curiosidades()

    T.section("Até onde confiar", "O que está provado, o que ainda não está e as perguntas mais comuns.", "Confiança")
    a, b = st.columns(2, gap="medium")
    lista = lambda itens: "<ul style='margin:0;padding-left:1.100rem'>" + "".join(f"<li>{t(i)}</li>" for i in itens) + "</ul>"
    with a:
        T.card("O que está provado", lista([
            "Na cheia de Janeiro de 2026, as regras de alerta teriam dado laranja 4 a 5 dias antes do primeiro mapa de cheia.",
            "O modelo que detecta água por radar acerta 91 % da área alagada nessa cheia (IoU 0,91), comparado com os mapas do Copernicus.",
            "A cor da água medida por dois satélites diferentes no mesmo dia concorda (correlação 0,85)."]), "Sim", "suave")
    with b:
        T.card("O que ainda não está provado", lista([
            "Tudo o que diz respeito a cheias foi testado com <b>uma única cheia</b>. Outras cheias podem comportar-se de outra maneira.",
            "O acerto da previsão no dia-a-dia está a ser medido desde Outubro de 2026, guardando todas as previsões.",
            "Os nomes dos lugares vêm de mapas públicos e não foram confirmados no terreno.",
            "A qualidade da água é um indicador de cor, sem medições no rio."]), "Ainda não")
    T.anchor("perguntas")
    T.subtitle("Perguntas frequentes")
    for pergunta, resposta in (
            ("O alerta está verde, mas está a chover muito aqui.", "O alerta é para a cheia do rio, que depende da chuva em toda a bacia, incluindo na África do Sul e em Essuatíni. "
             "A chuva forte no local pode alagar ruas sem o rio subir."),
            ("O meu bairro não aparece.", "Os nomes vêm de mapas públicos e ainda não foram todos confirmados. Veja no mapa se a sua casa fica dentro de uma zona vermelha ou laranja."),
            ("Com quantos dias de avanço avisa?", "Na cheia de Janeiro de 2026, o sistema teria dado alerta laranja 4 a 5 dias antes. Só foi testado com essa cheia."),
            ("Posso confiar no número do caudal?", "Vem de um modelo mundial, não de um aparelho no rio. Serve para saber se o rio vai subir muito, não para saber o valor exacto."),
            ("A água está \"normal\". Posso bebê-la?", "Não sem a tratar. O satélite vê a cor da água; não vê micróbios nem químicos. Ferva a água ou use cloro."),
            ("O que quer dizer \"previsão indisponível\"?", "Que a plataforma não tem um boletim das últimas 36 horas. Não quer dizer que não há perigo: nesse caso, ouça os avisos oficiais."),
            ("Isto substitui os avisos do INGD?", "Não. É um serviço experimental. Se as autoridades derem uma ordem, siga a ordem."),
            ("Como posso falar com a equipa?", "Para questões técnicas, escreva para o email no fim da página ou envie uma mensagem por WhatsApp. Também estamos no Facebook e no LinkedIn.")):
        with st.expander(t(pergunta)):
            T.html(f"<p>{t(resposta)}</p>")

    T.section("Os modelos de machine learning", "Que modelos a plataforma usa, com que dados foram treinados, como foram testados e até onde se pode confiar neles.",
              "Machine learning", "modelos")
    modelos_em_detalhe()

    T.section("Os dados e o sistema", "Todos os dados são abertos. O sistema corre sozinho todas as manhãs.", "Dados")
    with st.expander(t("De onde vem cada informação")):
        T.table(pd.DataFrame([
            {"Informação": "Previsão de caudal do rio", "Fonte": "GloFAS, Copernicus (via Open-Meteo)", "Actualização": "diária"},
            {"Informação": "Chuva prevista e chuva caída na bacia", "Fonte": "ECMWF IFS e ERA5 (via Open-Meteo)", "Actualização": "diária"},
            {"Informação": "Zonas de aviso", "Fonte": "Copernicus EMS, activação EMSR857 (cheia de Janeiro de 2026)", "Actualização": "quando houver nova cheia mapeada"},
            {"Informação": "Água vista por radar", "Fonte": "Sentinel-1 (Copernicus) e Modelo B do projecto", "Actualização": "mensal"},
            {"Informação": "Cor da água do rio", "Fonte": "Sentinel-2 (Copernicus) e Landsat 5, 7, 8 e 9 (USGS e NASA)", "Actualização": "semanal em Marracuene; mensal no rio todo"},
            {"Informação": "Fotografias de satélite", "Fonte": "Sentinel-2 (Copernicus), em cor natural", "Actualização": "semanal"},
            {"Informação": "Maré", "Fonte": "calculada a partir do nível do mar na Baía de Maputo (Open-Meteo)", "Actualização": "fixa"},
            {"Informação": "Edifícios, estradas, escolas e unidades de saúde", "Fonte": "Google Open Buildings e OpenStreetMap", "Actualização": "fixa"},
            {"Informação": "Nomes dos lugares", "Fonte": "OpenStreetMap e GeoNames", "Actualização": "por validar no terreno"},
            {"Informação": "Limite do distrito e da bacia", "Fonte": "FAO GAUL e HydroSHEDS", "Actualização": "fixa"}]))
        T.caption("Todos os dados são abertos. O projecto não depende de pedidos a instituições.")
        T.subtitle("Até onde confiar em cada camada")
        T.table(pd.DataFrame([{"Camada": c["titulo"], "Actualização": c.get("atualizacao", ""), "Até onde confiar": c.get("limites", "")}
                              for c in CATALOGO["camadas"] if c.get("limites") and c["id"] != "suscetibilidade"]))
    with st.expander(t("Glossário")):
        T.table(pd.DataFrame([
            {"Palavra": "Caudal", "Quer dizer": "A quantidade de água que passa no rio em cada segundo (m³/s)."},
            {"Palavra": "Bacia", "Quer dizer": "Toda a área de onde a chuva escorre para o rio. A do Incomáti estende-se pela África do Sul, Essuatíni e Moçambique."},
            {"Palavra": "Cenários", "Quer dizer": "51 previsões ligeiramente diferentes do mesmo modelo. Se quase todas concordam, a previsão é mais certa."},
            {"Palavra": "Zona de aviso", "Quer dizer": "Área onde a água chegou na cheia de Janeiro de 2026. Zona 1: chegou primeiro. Zona 2: chegou na cheia grande."},
            {"Palavra": "Turbidez", "Quer dizer": "Quanto a água está barrenta."},
            {"Palavra": "Troço", "Quer dizer": "Uma parte do rio. O Incomáti foi dividido em nove, da fronteira (Q1) à foz (Q9)."},
            {"Palavra": "Radar", "Quer dizer": "Satélite que vê através das nuvens. A água calma aparece muito escura."},
            {"Palavra": "Ano hidrológico", "Quer dizer": "De Outubro a Setembro, para a época das chuvas ficar inteira no mesmo ano."}]))
    with st.expander(t("O estado do sistema hoje")):
        estado = BOLETIM["estado"]
        T.kpis([{"rotulo": "Boletim", "valor": t("em dia") if VALIDO else t("desactualizado"), "nota": t("emitido há {h} h", h=f"{BOLETIM['horas_desde_a_emissao']:.0f}")},
                {"rotulo": "Cenários recebidos", "valor": estado.get("cenarios", "–"), "nota": "de 51"},
                {"rotulo": "Origem dos dados", "valor": t("internet") if estado.get("fonte") == "online" else t("cópia guardada")},
                {"rotulo": "Versão do código", "valor": CATALOGO.get("versao_codigo", "–")}])
        with T.guard("o estado do pipeline"):
            ficheiro = leitor.caminho("pipeline.json")
            if ficheiro.is_file():
                passos = json.loads(ficheiro.read_text())
                T.table(pd.DataFrame(passos["passos"]).rename(columns={"passo": "Passo", "estado": "Estado", "detalhe": "Detalhe", "segundos": "Segundos"}))
                T.caption(t("Última execução do pipeline: {quando} (hora de Maputo).", quando=f"{pd.Timestamp(passos['executado_utc']).tz_convert('Africa/Maputo'):%d/%m/%Y, %H:%M}"))
        if estado.get("problemas"):
            T.note(t("Avisos da última execução: {lista}", lista="; ".join(estado["problemas"])), "aviso")
        T.subtitle(t("Boletim de hoje, completo") + ("" if L.lingua() == "pt" else " " + t("(em português)")))
        st.markdown(BOLETIM["texto"])

    T.section("Com o apoio de", eyebrow="Apoio")
    T.card("", "<p>" + t("Projecto financiado pelo <b>IAU Office of Astronomy for Development (OAD)</b> e apoiado pelo <b>DARA (Development in Africa with Radio Astronomy)</b>: "
           "usar a ciência e as técnicas da observação do céu para resolver problemas na Terra.") + "</p>" + T.support_logos(dark_background=False), kind="suave")
    T.section("Fale connosco", "Para questões técnicas, parcerias ou para nos dizer o que falta na plataforma.", "Contactos", "contactos")
    T.card("", T.social().replace("ete-redes", "ete-redes claras")
           + f"<p><b>{t('Questões técnicas')}:</b> <a href='mailto:{T.CONTACTOS['email']}'>{T.CONTACTOS['email']}</a></p>"
           + f"<p><b>WhatsApp:</b> <a href='{T.CONTACTOS['whatsapp']}' target='_blank' rel='noopener'>{T.CONTACTOS['telefone']}</a></p>")
    T.note("Serviço experimental. Não substitui os avisos oficiais do INGD, do INAM e da ARA-Sul. Se as autoridades derem uma ordem, siga a ordem.", "aviso")


# ----------------------------------------------------------------------------- 6. curiosities (three on the home page, all of them in O projecto)
def valores_das_curiosidades() -> dict:
    """The numbers of the curiosities, taken from the data package so that they never go out of date."""
    valores = {"bacia": num(curiosidades.AREA_DA_BACIA_KM2)}
    try:
        dados = historico(V)
        maior = dados.loc[dados["caudal_m3s"].idxmax()]
        valores.update(caudal=num(round(float(maior["caudal_m3s"]), -1)), dia=t("{dia} de {ano}", dia=L.dia_mes(maior["data"]), ano=maior["data"].year),
                       segundos=num(curiosidades.PISCINA_OLIMPICA_M3 / float(maior["caudal_m3s"]), 1))
    except Exception:
        pass
    try:
        bruto = serie("factos", V)
        area = float(bruto.set_index(bruto.columns[0])["valor"]["area_alagada_cheia_grande_km2"])
        valores.update(area=num(area), parte=num(100 * area / curiosidades.AREA_DO_DISTRITO_KM2))
    except Exception:
        pass
    try:
        datas = pd.to_datetime(serie("cor_da_agua", V)["data"]).drop_duplicates()
        meses = max((datas.max() - datas.min()).days / 30.44, 1.0)
        valores.update(imagens=num(len(datas)), por_mes=num(round(len(datas) / meses)))
    except Exception:
        pass
    return valores


def curiosidade_pronta(c: dict, valores: dict) -> dict | None:
    """A curiosity in the reader's language with its numbers filled in, or None when a number is missing."""
    try:
        texto = t(c["texto"], **valores)
    except (KeyError, IndexError):
        return None
    try:
        figura = t(c["figura"], **valores)
    except (KeyError, IndexError):
        return None
    return {"figura": figura, "legenda": t(c["legenda"]), "titulo": t(c["titulo"]), "texto": texto, "fonte": t("Fonte: {fonte}", fonte=t(c["fonte"]))}


def curiosidades_do_dia() -> None:
    """Home page: three curiosities, one of each kind, changing every day. All of them are in O projecto."""
    with T.guard("as curiosidades"):
        valores = valores_das_curiosidades()
        itens = [c for c in (curiosidade_pronta(c, valores) for c in curiosidades.do_dia(int(HOJE.dayofyear))) if c]
        if not itens:
            return
        T.section("Sabia que…?", "Curiosidades sobre o nosso rio e os satélites que o vigiam. Mudam todos os dias.", "Curiosidades")
        T.curiosities(itens)
        st.button(t("Ver todas as curiosidades"), on_click=ir_para, args=("sobre", "curiosidades"), key="ir_curiosidades")


def todas_as_curiosidades() -> None:
    """O projecto: every curiosity, in three groups (the river, the satellites, a science still being built)."""
    with T.guard("as curiosidades"):
        valores = valores_das_curiosidades()
        T.section("Curiosidades", "Ver rios, cheias e a cor da água a partir do espaço é uma ciência recente, que ainda está em desenvolvimento. "
                  "Algumas curiosidades sobre o nosso rio, os satélites e o que aí vem.", "Sabia que…?", "curiosidades")
        for grupo, titulo in curiosidades.GRUPOS:
            itens = [c for c in (curiosidade_pronta(c, valores) for c in curiosidades.CURIOSIDADES if c["grupo"] == grupo) if c]
            if itens:
                T.subtitle(titulo)
                T.curiosities(itens)


# ----------------------------------------------------------------------------- 7. the search bar and the page of a place
def lugares_unicos() -> dict[str, int]:
    """Each place name once, with its row in the list of places: the first row, the most exposed, when two points share a name."""
    try:
        nomes = serie("lugares_por_ordem", V)["lugar"]
    except Exception:
        return {}
    unicos: dict[str, int] = {}
    for i, nome in enumerate(nomes):
        if isinstance(nome, str) and nome.strip():
            unicos.setdefault(nome, i)
    return unicos


@st.cache_data(show_spinner=False)
def fichas_dos_lugares(versao: float) -> dict:
    """The pictures and the nearest river section of each place (lugares/lugares.json), by row."""
    try:
        dados = json.loads(leitor.caminho("lugares/lugares.json").read_text())
    except Exception:
        return {"lugares": {}}
    return {**dados, "lugares": {r["id"]: r for r in dados["lugares"]}}


def rotulo_da_pesquisa(opcao) -> str:
    """How an option of the search bar reads: the name of a place, or the question of a topic (plain text, no symbols)."""
    opcao = str(opcao)
    if opcao.startswith("lugar:"):
        return opcao[6:]
    tema = pesquisa.POR_CHAVE.get(opcao[5:]) if opcao.startswith("tema:") else None
    return t(tema[2]) if tema else opcao


def abrir(opcao: str) -> None:
    """Open a choice of the search bar (or of its results): the page of a place, or a page at the right section."""
    st.session_state.pop("_pesquisa", None)
    if opcao.startswith("lugar:"):
        st.session_state["zona"] = opcao[6:]
        ir_para("zona")
    elif opcao.startswith("tema:") and opcao[5:] in pesquisa.POR_CHAVE:
        _, _, _, pagina, ancora, _ = pesquisa.POR_CHAVE[opcao[5:]]
        ir_para(pagina, ancora)


def ao_pesquisar() -> None:
    """A choice in the search bar opens at once. Free text opens the result when there is no doubt; otherwise the best ones are listed."""
    valor = st.session_state.get("pesquisa")
    st.session_state["pesquisa"] = None                  # the bar is empty again after each search
    if not valor:
        return
    valor = str(valor).strip()
    if valor.startswith(("lugar:", "tema:")):
        abrir(valor)
        return
    nomes, rotulos = list(lugares_unicos()), {k: t(r) for k, _, r, *_ in pesquisa.TEMAS}
    achados = pesquisa.procurar(valor, nomes, rotulos)
    escolha = pesquisa.decidir(valor, nomes, rotulos)
    if escolha:
        abrir(escolha)
    else:
        st.session_state["_pesquisa"] = {"texto": valor[:60], "achados": achados}


def barra_de_pesquisa(pagina: str) -> None:
    """The search bar with the magnifier, under the navigation of every page: the places and the questions people ask."""
    nomes = sorted(lugares_unicos(), key=pesquisa.normalizar)
    opcoes = [f"tema:{k}" for k in pesquisa.CHAVES] + [f"lugar:{n}" for n in nomes]
    with st.container(key="busca"):
        T.html(f"<style>[data-key='__creatable__'] > div::before {{content: '{t('Procurar este texto')}';}}</style>")
        st.selectbox(t("Pesquisar"), opcoes, index=None, key="pesquisa", label_visibility="collapsed", accept_new_options=True,
                     placeholder=t("Procure o seu lugar ou uma pergunta"), format_func=rotulo_da_pesquisa, on_change=ao_pesquisar)
        if pagina == "inicio" and not st.session_state.get("_pesquisa"):
            T.html(f"<div class='ete-busca-dica'>{t('Escreva o nome do seu bairro ou aldeia, por exemplo <b>Machubo</b> ou <b>Macaneta</b>, para ver as cheias, a água do rio, as imagens de satélite e o que fazer na sua zona.')}</div>")
    caixa = st.session_state.get("_pesquisa")
    if caixa:
        with st.container(key="pesquisa_resultados"):
            if caixa["achados"]:
                T.html(f"<div class='ete-busca-cab'>{t('Resultados para «{pedido}»', pedido=T.html_escape(caixa['texto']))}</div>")
                for i, opcao in enumerate(caixa["achados"]):
                    st.button(rotulo_da_pesquisa(opcao), key=f"resultado_{i}", on_click=abrir, args=(opcao,), type="tertiary")
            else:
                T.html(f"<div class='ete-busca-nada'>{t('Não encontrámos «{pedido}».', pedido=T.html_escape(caixa['texto']))} "
                       f"{t('Escreva o nome de um bairro ou aldeia de Marracuene, ou uma palavra como água, cheia, caudal ou satélite. Se o seu lugar não aparecer, escolha o mais perto: os nomes vêm de mapas públicos.')}</div>")
            st.button(t("Fechar"), key="pesquisa_fechar", on_click=lambda: st.session_state.pop("_pesquisa", None), type="tertiary", icon=":material/close:")


# What the alert of the next ten days means for a place, from what the 2026 flood did there
CHEIA_NO_LUGAR = {
    "amarelo": {"alaga primeiro": "Acompanhe os boletins e combine já para onde ir se a água subir.",
                "alaga em cheia grande": "Acompanhe os boletins: numa cheia grande, a água chega aqui.",
                "na margem da cheia": "Acompanhe os boletins.",
                "fora das zonas de aviso": "Mesmo assim, evite as zonas baixas junto ao rio."},
    "laranja": {"alaga primeiro": "Em 2026, a água chegou aqui {n} dias depois do alerta laranja. Ponha os documentos e os bens em lugar alto e combine para onde ir.",
                "alaga em cheia grande": "Se o alerta passar a vermelho, a água pode chegar aqui. Prepare-se já.",
                "na margem da cheia": "A água pode chegar perto. Evite as zonas baixas.",
                "fora das zonas de aviso": "Evite as zonas baixas e não atravesse o rio."},
    "vermelho": {"alaga primeiro": "Este lugar pode alagar. Siga já as ordens das autoridades, incluindo a de sair de casa.",
                 "alaga em cheia grande": "Este lugar pode alagar. Siga já as ordens das autoridades, incluindo a de sair de casa.",
                 "na margem da cheia": "A água pode chegar perto. Esteja pronto para sair e siga as ordens das autoridades.",
                 "fora das zonas de aviso": "Os caminhos e os campos à volta podem alagar. Não atravesse zonas alagadas."},
}
RESPOSTA_CHEIA = {"verde": "Não há sinais de cheia", "amarelo": "Atenção ao rio", "laranja": "Prepare-se", "vermelho": "Perigo de cheia"}
CLASSES_MODULO_Q = {"normal": "habitual", "elevada": "turva", "muito elevada": "muito turva"}      # monthly state of a section, in the words of the colour map


def agua_perto(ficha: dict) -> dict | None:
    """How the water is in the river section nearest a place: the weekly map of the colour when it covers that
    section, otherwise the monthly state of the section. {classe, cor, quando, troco, velho}"""
    troco = ficha.get("troco")
    nome_troco = L.troco(ficha.get("troco_nome", troco or ""))
    camada = CAMADAS.get("cor_da_agua_mapa")
    if camada and (camada.get("resumo", {}).get(troco) or {}).get("classe_da_mediana"):
        classe = camada["resumo"][troco]["classe_da_mediana"]
        cores = {s["nome"]: s["cor"] for s in camada["legenda"]}
        dias = (HOJE.normalize() - pd.Timestamp(camada["data"]).normalize()).days
        return {"classe": classe, "cor": cores.get(classe, "#B4B9BE"), "troco": nome_troco,
                "quando": t("Satélite Sentinel-2 · {dia}", dia=L.data_longa(camada["data"])),
                "velho": t("A imagem mais recente com o rio à vista tem {n} dias: as nuvens taparam as seguintes.", n=dias) if dias > 20 else ""}
    if troco and "qualidade_estado" in CAMADAS:
        estado = serie("qualidade_estado", V).set_index("troco")
        if troco in estado.index and estado.loc[troco, "classe"] in CLASSES_MODULO_Q:
            linha = estado.loc[troco]
            return {"classe": CLASSES_MODULO_Q[linha["classe"]], "cor": CORES_AGUA.get(linha["classe"], "#B4B9BE"), "troco": nome_troco,
                    "quando": t("Satélites Sentinel-2 e Landsat · {mes}", mes=L.mes_ano(str(linha["mes"]))), "velho": ""}
    return None


def alertas_para(nome: str) -> None:
    """The sign-up form opens with the place already chosen."""
    if nome in _lugares_para_escolher():
        st.session_state["pagina_lugar"] = nome
    ir_para("alertas")


def escolher_zona(lugares: pd.DataFrame) -> None:
    """The page of a place before a place is chosen: how to find it, and the places most exposed to floods."""
    T.page_head("A sua zona", "Procure o seu lugar",
                "Escreva o nome do seu bairro ou aldeia na barra de pesquisa, em cima, ou escolha um dos lugares abaixo. Vê as cheias, a água do rio, "
                "as imagens de satélite e o que fazer, só para esse lugar.")
    T.subtitle("Os lugares mais expostos às cheias")
    expostos = lugares.loc[lugares["categoria"].isin(["alaga primeiro", "alaga em cheia grande"]), "lugar"].drop_duplicates()
    with st.container(key="lista_lugares", horizontal=True, gap="small"):
        for n, nome in enumerate(expostos):
            st.button(nome, key=f"escolher_lugar_{n}", on_click=abrir, args=(f"lugar:{nome}",))
    T.caption("Os nomes vêm de mapas públicos (OpenStreetMap e GeoNames) e ainda não foram todos confirmados no terreno.")


def pagina_zona() -> None:
    """Everything about one place, read from top to bottom: three short answers, the floods, the river flow,
    the water, the place seen from space, and the alerts for it."""
    lugares = serie("lugares_por_ordem", V)
    nomes = lugares_unicos()
    nome = st.session_state.get("zona")
    if nome not in nomes:
        escolher_zona(lugares)
        return
    i = nomes[nome]
    l = lugares.iloc[i]
    ficha = fichas_dos_lugares(V)["lugares"].get(i, {})
    categoria = l["categoria"]
    lingua = L.lingua()
    posto = l["posto_administrativo"] if isinstance(l["posto_administrativo"], str) and l["posto_administrativo"] else ""
    onde = (t("Posto administrativo de {posto}", posto=posto) + " · " if posto else "") + t("distrito de Marracuene")
    T.zone_head(nome, onde, T.chip(categoria, CORES_LUGARES.get(categoria)) + (T.chip(t("Troço do rio mais perto: {troco}", troco=L.troco(ficha["troco_nome"])))
                                                                                if ficha.get("troco_nome") else ""))

    # 1. three short answers
    agua = agua_perto(ficha) if ficha else None
    nivel = BOLETIM["nivel_maximo_provavel"] if VALIDO else None
    if VALIDO:
        primeiro = next((d["data"] for d in BOLETIM["previsao_diaria"] if d["alerta"] == nivel), None)
        detalhe = T.alert_name(nivel) + (" · " + t("a partir de {dia}", dia=pd.Timestamp(primeiro).strftime("%d/%m")) if nivel != "verde" and primeiro else "")
        detalhe += " · " + t("até {dia}", dia=pd.Timestamp(BOLETIM["valido_ate"]).strftime("%d/%m"))
        cheia = {"icone": "onda", "pergunta": t("Cheia nos próximos 10 dias?"), "resposta": t(RESPOSTA_CHEIA[nivel]), "detalhe": detalhe, "cor": CORES[nivel]}
    else:
        cheia = {"icone": "onda", "pergunta": t("Cheia nos próximos 10 dias?"), "resposta": t("Previsão indisponível"),
                 "detalhe": t("Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul."), "cor": "#56656C"}
    if agua:
        frase = t(T.FRASES_AGUA[agua["classe"]])
        cor_da_agua = {"icone": "gota", "pergunta": t("Como está a água do rio?"), "resposta": frase[:1].upper() + frase[1:],
                       "detalhe": agua["troco"] + " · " + agua["quando"], "cor": agua["cor"]}
    else:
        cor_da_agua = {"icone": "gota", "pergunta": t("Como está a água do rio?"), "resposta": t("Sem leitura recente"),
                       "detalhe": t("As nuvens taparam o rio nas últimas imagens."), "cor": "#B4B9BE"}
    beber = {"icone": "escudo", "pergunta": t("Posso beber a água do rio?"), "resposta": t("Só depois de tratada"),
             "detalhe": t("O satélite vê a lama, não vê micróbios. Ferva a água ou use cloro."), "cor": T.LAGOA}
    T.answers([cheia, cor_da_agua, beber])

    # 2. the floods here
    T.section("Cheias: o que esperar aqui", "O alerta dos próximos 10 dias e o que a cheia de Janeiro de 2026 fez neste lugar.", "Cheias", "zona_cheias")
    esquerda, direita = st.columns([3, 2], gap="large")
    with esquerda:
        with T.guard("a previsão para este lugar"):
            historia = alertas_whatsapp.CATEGORIAS_DO_LUGAR.get(categoria, {}).get(lingua, "").format(lugar=nome)
            if VALIDO:
                T.day_tiles(BOLETIM["previsao_diaria"], CORES, -1)
                aqui = ""
                modelo = CHEIA_NO_LUGAR.get(nivel, {}).get(categoria, "")
                if "{n}" in modelo and pd.isna(l["dias_apos_alerta"]):
                    modelo = CHEIA_NO_LUGAR[nivel]["alaga em cheia grande"]
                if modelo:
                    aqui = t(modelo, n=num(l["dias_apos_alerta"])) if "{n}" in modelo else t(modelo)
                T.card(T.dot(CORES[nivel]) + T.alert_name(nivel), f"<p><b>{historia}</b> {aqui}</p>"
                       f"<p><b>{t('O que fazer:')}</b> {t(CONSELHOS.get(nivel, ''))}</p>", t("Próximos 10 dias, neste lugar"))
            else:
                T.card(t("Previsão indisponível"), f"<p><b>{historia}</b></p><p>{t('Não há um boletim das últimas 36 horas. Isto não quer dizer que não há perigo.')} "
                       f"{t('Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.')}</p>", t("Próximos 10 dias, neste lugar"))
            distancia = float(l["distancia_ao_rio_m"]) if pd.notna(l["distancia_ao_rio_m"]) else None
            linhas = []
            if pd.notna(l["primeira_data"]):
                linhas.append((t("Primeiro mapa com água em 2026"), pd.Timestamp(l["primeira_data"]).strftime("%d/%m/%Y")
                               + (" · " + t("{n} dias depois do alerta", n=num(l["dias_apos_alerta"])) if pd.notna(l["dias_apos_alerta"]) else "")))
            if pd.notna(l["parte_alagada"]) and l["parte_alagada"] > 0:
                linhas.append((t("Parte do círculo de 500 m que alagou em 2026"), f"{num(100 * l['parte_alagada'])}\u00a0%"))
            linhas.append((t("Edifícios num raio de 500 m"), num(l["edificios"])))
            if distancia is not None:
                linhas.append((t("Distância ao rio"), f"{num(distancia / 1000, 1)}\u00a0km" if distancia >= 1000 else f"{num(distancia)}\u00a0m" if distancia >= 50 else t("junto ao rio")))
            if pd.notna(l["altura_acima_do_rio_m"]):
                linhas.append((t("Altura acima do rio"), f"{num(l['altura_acima_do_rio_m'], 1)}\u00a0m"))
            T.card("", T.facts(linhas), t("Este lugar em números"))
    with direita:
        with T.guard("o mapa das zonas à volta do lugar"):
            ficheiro = leitor.caminho(ficha["ficheiros"]["zonas"]) if ficha.get("ficheiros") else None
            if ficheiro is not None and ficheiro.is_file():
                lado = fichas_dos_lugares(V).get("lado_m", 6000)
                T.picture(ficheiro, t("Zonas de aviso à volta de {lugar}", lugar=nome), t("Zonas de aviso"), ring=1000 / lado, km=1000 / lado,
                          note=t("O círculo marca 500 m à volta de {lugar}. A vermelho, onde a água chegou primeiro em 2026; a laranja, onde chegou na cheia grande.",
                                 lugar=nome))
                T.legend(CAMADAS["zonas_de_aviso"]["legenda"])

    # 3. the river flow (the same river for every place)
    T.section("O caudal do rio", "A quantidade de água que passa no rio Incomáti em cada segundo, prevista para os próximos 10 dias em Marracuene. "
              "É o caudal que decide o alerta.", "Caudal (vazão)")
    if not VALIDO:
        T.note("Sem previsão válida para mostrar. Consulte os avisos oficiais.", "aviso")
    else:
        with T.guard("a previsão de caudal"):
            hoje = BOLETIM["previsao_diaria"][0]
            T.html(f"<p class='ete-sub'>{t('Hoje passam cerca de {q} m³/s no rio em Marracuene. O alerta amarelo começa nos {a} m³/s.', q=num(hoje['caudal_mediana_m3s']), a=num(LIMITES.get('amarelo')))}</p>")
            desenho, fora = G.forecast(cenarios_do_boletim(), LIMITES, CORES_LIMITES, None, 240)
            grafico(desenho)
            T.caption(t("A linha é o cenário central; a faixa clara vai do mínimo ao máximo provável, entre 51 cenários do modelo europeu GloFAS.")
                      + (" " + t("O rio está longe dos limites: {limites}.", limites=longe_dos_limites(fora)) if fora else ""))

    # 4. the water of the river near the place
    T.section("A água do rio perto de si", "A cor da água vista por satélite no troço do rio mais perto deste lugar, e o que fazer com ela.", "Qualidade da água", "zona_agua")
    esquerda, direita = st.columns([3, 2], gap="large")
    with esquerda:
        with T.guard("a água perto do lugar"):
            if agua:
                T.water_reading(agua["quando"], t("No troço {troco}, a água está {como}.", troco=agua["troco"], como=t(T.FRASES_AGUA[agua["classe"]])), [], agua["velho"])
            else:
                T.note("Não há uma leitura recente da cor da água neste troço: as nuvens taparam o rio nas últimas imagens.", "neutra")
            semanas_previstas()
            T.caption("A previsão das próximas semanas é calculada para o rio em Marracuene.")
    with direita:
        with T.guard("os conselhos sobre a água"):
            situacoes = situacoes_de_hoje()
            itens, prioridade = [], "info"
            for situacao, lista in conselhos.para("familias", situacoes):
                prioridade = situacao["nivel"] if not itens else prioridade
                itens += [i for i in lista if i not in itens]
            T.advice_card("Posso beber a água do rio?", itens[:4], prioridade, conselhos.PUBLICOS["familias"][0],
                          "Não sem a tratar. O satélite vê a lama, não vê micróbios nem químicos: a água do rio deve ser sempre tratada antes de beber.")
            st.button(t("Como tratar a água em casa"), on_click=ir_para, args=("agua", "tratar"), key="zona_tratar")

    # 5. the place seen from space: before and during the flood
    fotos = ficha.get("ficheiros", {})
    if fotos and all(leitor.caminho(fotos[k]).is_file() for k in ("antes", "cheia")):
        with T.guard("as imagens de satélite do lugar"):
            T.section("A sua zona vista do espaço", "Um quadrado de 6 km à volta do lugar, visto pelo satélite antes e durante a cheia de Janeiro de 2026.", "Satélite", "zona_espaco")
            lado = fichas_dos_lugares(V).get("lado_m", 6000)
            antes = fichas_dos_lugares(V).get("antes", {}).get("data", "2025-10-23")
            radar = ficha["cheia"]["tipo"] != "foto"
            if not radar:
                direita_rotulo = t("Cheia · {dia}", dia=pd.Timestamp(ficha["cheia"]["data"]).strftime("%d/%m/%Y"))
                nota = t("Arraste a barra branca: à esquerda, a zona antes da cheia; à direita, a mesma zona durante a cheia. A água da cheia aparece castanha, cor de lama.")
            else:
                mes = ficha["cheia"]["mes"]
                direita_rotulo = t("Cheia · radar, {mes}", mes=f"{L.meses()[int(mes[5:7]) - 1]} {mes[:4]}")
                nota = t("As nuvens tapavam esta zona nas fotografias da cheia. À direita, o que o radar viu em Janeiro de 2026, através das nuvens: "
                         "a vermelho, a água da cheia; a azul, a água de sempre. Junto à praia, o radar pode confundir a areia molhada com água.")
            a, b = st.columns([3, 2], gap="large")
            with a:
                T.compare(leitor.caminho(fotos["antes"]), leitor.caminho(fotos["cheia"]), t("Antes · {dia}", dia=pd.Timestamp(antes).strftime("%d/%m/%Y")),
                          direita_rotulo, f"zona_{i}", 50, nota, ring=1000 / lado, km=1000 / lado)
            with b:
                T.card("O que está a ver", "<p>" + (t("À esquerda, uma fotografia real do satélite Sentinel-2, em cor natural. À direita, a água vista pelo radar Sentinel-1 "
                                                       "e lida pelo modelo do projecto (Modelo B).") if radar else
                                                     t("Fotografias reais do satélite Sentinel-2, em cor natural, de 30 m em 30 m.")) + " "
                       + t("O círculo marca 500 m à volta do lugar e o ponto, o lugar.") + "</p>"
                       + ("<p>" + t("Em 2026, a água cobriu {p} % deste círculo.", p=num(100 * l["parte_alagada"])) + "</p>" if pd.notna(l["parte_alagada"]) and l["parte_alagada"] > 0 else "")
                       + "<p class='ete-miudo'>" + t("Imagens de 30 m: mostram a zona, não cada casa.") + "</p>", "Satélite")
                st.button(t("Ver o rio inteiro visto do espaço"), on_click=ir_para, args=("cheias", "espaco"), key="zona_espaco_rio", type="tertiary")

    # 6. the alerts for this place, and sharing the page
    T.html("<div style='height:22px'></div>")
    a, b = st.columns(2, gap="medium")
    with a, st.container(key="porta_zona_alertas"):
        T.html(f"<div class='ete-olho'>{t('Alertas no WhatsApp')}</div><div class='cab'>{t('Receba os alertas para este lugar')}</div>"
               f"<p>{t('Só escrevemos quando houver perigo de cheia, e quando o perigo passar. Se {lugar} estiver entre os lugares que podem alagar, a mensagem di-lo primeiro.', lugar=nome)}</p>")
        st.button(t("Receber alertas para {lugar}", lugar=nome), on_click=alertas_para, args=(nome,), key="ir_alertas_zona", type="primary")
    with b, st.container(key="porta_zona_partilhar"):
        endereco = CATALOGO.get("aplicacao", "")
        T.html(f"<div class='ete-olho'>{t('Partilhar')}</div><div class='cab'>{t('Envie esta página a quem vive aqui')}</div>"
               f"<p>{t('Uma ligação directa para a página de {lugar}, com a previsão de cada dia. Funciona em qualquer telefone com internet.', lugar=nome)}</p>")
        if endereco:
            from urllib.parse import quote

            ligacao = f"{endereco.rstrip('/')}/?p=zona&lugar={quote(nome)}&lang={lingua}"
            texto = f"Eyes to Earth · {nome}: {cheia['resposta']}. {t('Água do rio')}: {cor_da_agua['resposta'].lower()}. {ligacao}"
            st.link_button(t("Partilhar no WhatsApp"), f"https://wa.me/?text={quote(texto)}", icon=":material/share:")
    repetidos = int((lugares["lugar"] == nome).sum())
    T.caption(t("Nome de {fonte}, ainda por confirmar no terreno. Cada lugar é um ponto com um círculo de 500 m, não um limite oficial de bairro.", fonte=l["fonte_do_nome"])
              + (" " + t("Há {n} pontos com este nome nos mapas públicos: mostramos o mais exposto às cheias.", n=repetidos) if repetidos > 1 else ""))


# ----------------------------------------------------------------------------- 8. accounts: sign in, open an account, my account
# The account is optional: alerts, maps and advice stay open to everybody. It keeps the person's full name,
# place, WhatsApp number and language, and the WhatsApp messages use the name. Rules and security: contas.py.
COOKIE = "ete_sessao"                                     # the device ticket of "stay signed in" (30 days)
MENSAGENS_CONTA = {
    "errado": "O nome de utilizador ou a senha não estão certos.",
    "fechada": "Demasiadas tentativas erradas. Por segurança, a conta fica fechada durante {minutos} minutos.",
    "utilizador_invalido": "O nome de utilizador deve ter de 3 a 30 letras sem acentos ou algarismos (pode ter ponto, hífen e sublinhado), sem espaços.",
    "utilizador_existe": "Este nome de utilizador já existe. Escolha outro.",
    "nome_invalido": "Escreva o nome só com letras (pode ter espaços e hífens).",
    "nome_incompleto": "Escreva o seu nome completo: o nome e o apelido.",
    "telefone_invalido": "Este número não parece certo. Escreva o número de WhatsApp com 9 algarismos, por exemplo 84 123 4567.",
    "senhas_diferentes": "As duas senhas não são iguais.",
    "senha_curta": "A senha deve ter pelo menos 8 caracteres.",
    "senha_longa": "A senha é demasiado longa (no máximo 128 caracteres).",
    "senha_fraca": "Essa senha é fácil de adivinhar. Misture palavras, algarismos e sinais, e não use o seu nome de utilizador.",
    "sem_consentimento": "Para criar a conta, marque a caixa «Aceito».",
    "erro": "Não foi possível guardar agora. Tente de novo mais tarde.",
}


def conta_actual() -> dict | None:
    return st.session_state.get("conta")


def primeiro_nome(conta: dict) -> str:
    return (conta.get("nome") or conta.get("utilizador") or "").split(" ")[0]


def aviso_da_conta(resultado: str, extra: dict | None = None) -> None:
    T.note(t(MENSAGENS_CONTA.get(resultado, MENSAGENS_CONTA["erro"]), **(extra or {})), "aviso")


def restaurar_sessao() -> None:
    """A device that asked to stay signed in brings its ticket in a cookie: the account opens by itself (checked once per visit)."""
    if conta_actual() or st.session_state.get("_sessao_vista"):
        return
    st.session_state["_sessao_vista"] = True
    try:
        bilhete = st.context.cookies.get(COOKIE)
    except Exception:
        bilhete = None
    if not contas.bilhete_valido(bilhete) or not contas.permanente():
        return
    try:
        conta = contas.conta_da_sessao(bilhete)
    except Exception:
        return
    if conta:
        st.session_state["conta"], st.session_state["_bilhete"] = conta, bilhete
    else:
        st.session_state["_cookie"] = ""                  # an old ticket: clear it from the device


def gravar_cookie() -> None:
    """Write (or clear) the device ticket. Streamlit cannot set cookies, so the page's own script does it."""
    if "_cookie" not in st.session_state:
        return
    bilhete = st.session_state.pop("_cookie")
    seguro = " + (location.protocol === 'https:' ? '; Secure' : '')"
    if bilhete:
        js = f"document.cookie = '{COOKIE}=' + {json.dumps(bilhete)} + '; Max-Age={contas.DIAS_DE_SESSAO * 86400}; Path=/; SameSite=Lax'{seguro};"
    else:
        js = f"document.cookie = '{COOKIE}=; Max-Age=0; Path=/; SameSite=Lax'{seguro};"
    st.html(f"<script>/* {secrets.token_hex(4)} */ {js}</script>", unsafe_allow_javascript=True)


def iniciar(conta: dict, manter: bool) -> None:
    """The account is open in this visit; with `manter`, also on this device for 30 days."""
    st.session_state["conta"] = conta
    st.session_state["_lingua_da_conta"] = conta.get("lingua") if conta.get("lingua") in L.LINGUAS else L.lingua()
    if manter:
        bilhete = contas.abrir_sessao(conta["id"])
        st.session_state["_bilhete"] = st.session_state["_cookie"] = bilhete


def terminar() -> None:
    """Sign out on this device."""
    try:
        contas.fechar_sessao(st.session_state.get("_bilhete", ""))
    except Exception:
        pass
    for chave in ("conta", "_bilhete", "_codigo_novo"):
        st.session_state.pop(chave, None)
    st.session_state["_cookie"] = ""
    ir_para("inicio")


def formulario_entrar() -> None:
    T.subtitle("Entrar")
    with st.form("form_entrar", border=False):
        utilizador = st.text_input(t("Nome de utilizador"), key="entrar_utilizador", max_chars=30, autocomplete="username")
        senha = st.text_input(t("Senha"), type="password", key="entrar_senha", max_chars=128, autocomplete="current-password")
        manter = st.checkbox(t("Manter a sessão iniciada neste aparelho (30 dias)"), value=True, key="entrar_manter")
        enviado = st.form_submit_button(t("Entrar"), type="primary", width="stretch", key="entrar_enviar")
    if enviado:
        try:
            resultado, dados = contas.entrar(utilizador, senha)
        except Exception:
            resultado, dados = "erro", {}
        if resultado == "ok":
            iniciar(dados["conta"], manter)
            st.rerun()
        aviso_da_conta(resultado, dados)
    with st.expander(t("Esqueceu a senha?")):
        T.html(f"<p class='ete-miudo'>{t('Use o código de recuperação que recebeu ao criar a conta. Depois recebe um código novo.')}</p>")
        with st.form("form_recuperar", border=False):
            utilizador = st.text_input(t("Nome de utilizador"), key="recuperar_utilizador", max_chars=30)
            codigo = st.text_input(t("Código de recuperação"), key="recuperar_codigo", max_chars=20, placeholder="ABCD-EFGH-JKLM")
            nova = st.text_input(t("Senha nova"), type="password", key="recuperar_nova", max_chars=128, autocomplete="new-password")
            repetida = st.text_input(t("Repita a senha nova"), type="password", key="recuperar_repetida", max_chars=128, autocomplete="new-password")
            mudar = st.form_submit_button(t("Mudar a senha"), width="stretch", key="recuperar_enviar")
        if mudar:
            try:
                resultado, dados = contas.recuperar(utilizador, codigo, nova, repetida)
            except Exception:
                resultado, dados = "erro", {}
            if resultado == "ok":
                st.session_state["_codigo_novo"] = dados["codigo"]
                T.note("Pronto: a senha foi mudada. Entre com a senha nova. Guarde o código de recuperação novo, mostrado em baixo.")
                T.html(f"<div class='ete-codigo'>{T.html_escape(dados['codigo'])}</div>")
            else:
                aviso_da_conta("errado" if resultado == "errado" else resultado, dados)
    T.caption("Se perdeu também o código, fale com a equipa pelo WhatsApp que está no fundo da página.")


def formulario_criar() -> None:
    T.subtitle("Criar conta")
    outro = "__outro__"
    with st.form("form_criar", border=False):
        nome = st.text_input(t("O seu nome completo"), key="criar_nome", max_chars=80, placeholder=t("Nome e apelido"), autocomplete="name")
        utilizador = st.text_input(t("Nome de utilizador"), key="criar_utilizador", max_chars=30, autocomplete="username",
                                   help=t("De 3 a 30 letras sem acentos ou algarismos; pode ter ponto, hífen e sublinhado. Por exemplo: ana.cossa"))
        a, b = st.columns(2)
        senha = a.text_input(t("Senha"), type="password", key="criar_senha", max_chars=128, autocomplete="new-password", help=t("Pelo menos 8 caracteres."))
        repetida = b.text_input(t("Repita a senha"), type="password", key="criar_repetida", max_chars=128, autocomplete="new-password")
        lugar = st.selectbox(t("Onde vive? (opcional)"), [""] + _lugares_para_escolher() + [outro], key="criar_lugar",
                             format_func=lambda v: t("Escolha o seu bairro ou lugar") if v == "" else t("Outro lugar / não sei") if v == outro else v)
        telefone = st.text_input(t("O seu número de WhatsApp (opcional)"), placeholder="84 123 4567", key="criar_telefone", max_chars=20)
        manter = st.checkbox(t("Manter a sessão iniciada neste aparelho (30 dias)"), value=True, key="criar_manter")
        aceito = st.checkbox(t("Aceito que o Eyes to Earth guarde estes dados para a minha conta. Posso mudá-los ou apagar a conta quando quiser."), key="criar_aceito")
        enviado = st.form_submit_button(t("Criar conta"), type="primary", width="stretch", key="criar_enviar")
    if enviado:
        try:
            resultado, dados = contas.criar(utilizador, nome, senha, repetida, "" if lugar == outro else lugar, telefone, L.lingua(), aceito)
        except Exception:
            resultado, dados = "erro", {}
        if resultado == "ok":
            iniciar(dados["conta"], manter)
            st.session_state["_codigo_novo"] = dados["codigo"]
            st.rerun()
        aviso_da_conta(resultado, dados)


def a_minha_conta(conta: dict) -> None:
    """The person's own page: the place, the WhatsApp alerts, the details, security, signing out and deleting the account."""
    T.page_head("A minha conta", t("Olá, {nome}", nome=T.html_escape(primeiro_nome(conta))),
                t("Conta {utilizador}, criada a {dia}. Os seus dados só servem para a sua conta e para os alertas que pedir.",
                  utilizador=f"<b>{T.html_escape(conta['utilizador'])}</b>", dia=L.dia_mes(conta.get("criado_utc", "")[:10]) if conta.get("criado_utc") else "–"))
    codigo = st.session_state.get("_codigo_novo")
    if codigo:                                            # shown once, right after the account was created
        with st.container(key="caixa_codigo"):
            T.html(f"<div class='ete-olho'>{t('Código de recuperação')}</div><div class='cab'>{t('Guarde este código')}</div>"
                   f"<div class='ete-codigo'>{T.html_escape(codigo)}</div><p>{t('Se esquecer a senha, é com este código que escolhe uma nova. Escreva-o num papel ou guarde-o no telefone: por segurança, não o mostramos outra vez.')}</p>")
            st.button(t("Já guardei o código"), key="codigo_guardado", type="primary", on_click=lambda: st.session_state.pop("_codigo_novo", None))

    # 1. the place
    T.section("O meu lugar", "A página com as cheias, a água e as imagens de satélite do seu lugar.", "Lugar")
    lugar = conta.get("lugar")
    if lugar and lugar in lugares_unicos():
        T.html(f"<p class='ete-sub'>{t('O seu lugar é <b>{lugar}</b>.', lugar=T.html_escape(lugar))}</p>")
        st.button(t("Ver a página de {lugar}", lugar=lugar), on_click=abrir, args=(f"lugar:{lugar}",), key="conta_ir_lugar", type="primary")
    else:
        T.note("Ainda não escolheu o seu lugar. Escolha-o em «Os meus dados», em baixo.", "neutra")

    # 2. WhatsApp alerts on the account's number
    T.section("Alertas no WhatsApp", "Recebe uma mensagem com o seu nome quando houver perigo de cheia, e quando o perigo passar.", "Alertas")
    telefone = conta.get("telefone")
    if not telefone:
        T.note("Acrescente o seu número de WhatsApp em «Os meus dados», em baixo, para receber os alertas.", "neutra")
    elif not inscricoes.permanente():
        T.note("As inscrições abrem em breve. Até lá, siga os alertas nesta plataforma.", "neutra")
    else:
        with T.guard("os alertas desta conta"):
            inscrita = next((r for r in inscricoes.activas(inscricoes.loja().listar()) if r["telefone"] == telefone), None)
            numero = inscricoes.esconder_telefone(telefone)
            if inscrita:
                T.card(t("Está inscrito"), "<p>" + t("Os alertas vão para o número {numero}, em nome de {nome}.", numero=numero, nome=T.html_escape(inscrita.get("nome") or conta["nome"]))
                       + "</p>", "WhatsApp", "suave")
                if st.button(t("Deixar de receber os alertas"), key="conta_sair_alertas"):
                    inscricoes.cancelar(telefone)
                    st.rerun()
            else:
                T.html(f"<p class='ete-sub'>{t('O número {numero} ainda não recebe os alertas.', numero=numero)}</p>")
                aceito = st.checkbox(t("Aceito receber alertas de cheia do Eyes to Earth no WhatsApp. O meu número só é usado para isto e posso sair quando quiser."), key="conta_aceito")
                if st.button(t("Receber os alertas neste número"), key="conta_receber", type="primary"):
                    resultado, _ = inscricoes.inscrever(telefone, conta.get("lugar", ""), conta.get("lingua", "pt"), conta["nome"], aceito)
                    if resultado == "sem_consentimento":
                        T.note("Para receber os alertas, marque a caixa «Aceito».", "aviso")
                    else:
                        try:
                            alertas_whatsapp.boas_vindas_agora(telefone)
                        except Exception:
                            pass
                        st.rerun()

    # 3. the details
    T.section("Os meus dados", "O nome completo é o que aparece nas mensagens do WhatsApp.", "Dados")
    outro = "__outro__"
    opcoes = [""] + _lugares_para_escolher() + [outro]
    with st.container(key="caixa_dados"), st.form("form_dados", border=False):
        nome = st.text_input(t("O seu nome completo"), value=conta.get("nome", ""), key="dados_nome", max_chars=80)
        lugar = st.selectbox(t("Onde vive?"), opcoes, index=opcoes.index(conta["lugar"]) if conta.get("lugar") in opcoes else 0, key="dados_lugar",
                             format_func=lambda v: t("Escolha o seu bairro ou lugar") if v == "" else t("Outro lugar / não sei") if v == outro else v)
        telefone = st.text_input(t("O seu número de WhatsApp"), value=inscricoes.mostrar_telefone(conta["telefone"]) if conta.get("telefone") else "",
                                 placeholder="84 123 4567", key="dados_telefone", max_chars=20)
        lingua = st.radio(t("Língua"), list(L.LINGUAS), index=list(L.LINGUAS).index(conta.get("lingua")) if conta.get("lingua") in L.LINGUAS else 0,
                          horizontal=True, key="dados_lingua", format_func=lambda k: L.NOMES[k])
        guardar = st.form_submit_button(t("Guardar os meus dados"), type="primary", key="dados_enviar")
    if guardar:
        try:
            resultado, nova = contas.actualizar_dados(conta["id"], nome, "" if lugar == outro else lugar, telefone, lingua)
        except Exception:
            resultado, nova = "erro", {}
        if resultado == "ok":
            st.session_state["conta"] = nova
            st.session_state["_lingua_da_conta"] = lingua
            st.rerun()
        aviso_da_conta(resultado)

    # 4. security
    T.section("Segurança", "A sua senha nunca é guardada: guardamos só uma impressão digital dela, que ninguém consegue ler, nem a equipa.", "Segurança")
    a, b = st.columns(2, gap="large")
    with a:
        T.subtitle("Mudar a senha")
        with st.form("form_senha", border=False):
            actual = st.text_input(t("Senha actual"), type="password", key="senha_actual", max_chars=128, autocomplete="current-password")
            nova = st.text_input(t("Senha nova"), type="password", key="senha_nova", max_chars=128, autocomplete="new-password")
            repetida = st.text_input(t("Repita a senha nova"), type="password", key="senha_repetida", max_chars=128, autocomplete="new-password")
            mudar = st.form_submit_button(t("Mudar a senha"), key="senha_enviar")
        if mudar:
            try:
                resultado = contas.mudar_senha(conta["id"], actual, nova, repetida)
            except Exception:
                resultado = "erro"
            if resultado == "ok":
                if st.session_state.get("_bilhete"):          # the other devices were signed out; this one keeps a new ticket
                    st.session_state["_bilhete"] = st.session_state["_cookie"] = contas.abrir_sessao(conta["id"])
                T.note("Pronto: a senha foi mudada. Nos outros aparelhos, vai ser preciso entrar com a senha nova.")
            else:
                aviso_da_conta("errado" if resultado == "errado" else resultado)
    with b:
        T.subtitle("Sair")
        T.html(f"<p class='ete-sub'>{t('Termina a sessão neste aparelho. Os seus dados ficam guardados.')}</p>")
        st.button(t("Sair da conta"), on_click=terminar, key="conta_sair", icon=":material/logout:")
        with st.expander(t("Apagar a minha conta")):
            T.html(f"<p>{t('Apaga a conta e todos os dados dela, para sempre. Escreva a senha para confirmar.')}</p>")
            with st.form("form_apagar", border=False):
                senha = st.text_input(t("Senha"), type="password", key="apagar_senha", max_chars=128, autocomplete="current-password")
                parar = st.checkbox(t("Também deixar de receber os alertas no WhatsApp"), value=True, key="apagar_alertas") if conta.get("telefone") else False
                apagar = st.form_submit_button(t("Apagar a conta para sempre"), key="apagar_enviar")
            if apagar:
                try:
                    resultado = contas.apagar(conta["id"], senha)
                except Exception:
                    resultado = "erro"
                if resultado == "ok":
                    if parar and conta.get("telefone"):
                        try:
                            inscricoes.cancelar(conta["telefone"])
                        except Exception:
                            pass
                    terminar()
                    st.rerun()
                aviso_da_conta(resultado)
    T.note("Os seus dados ficam numa base de dados protegida e só servem para a sua conta e para os alertas que pedir. Não são mostrados a ninguém, "
           "não são partilhados nem vendidos. Pode mudá-los ou apagar a conta quando quiser.", "neutra")


def pagina_conta() -> None:
    """Sign in or open an account (side by side, no tabs); signed in, the person's own page."""
    conta = conta_actual()
    if conta:
        a_minha_conta(conta)
        return
    if not contas.permanente():
        T.page_head("A minha conta", "As contas abrem em breve",
                    "Estamos a preparar a base de dados segura onde as contas vão ficar. Até lá, toda a plataforma está aberta, sem conta.")
        return
    T.page_head("A minha conta", "Entre ou crie a sua conta",
                "Com uma conta, a plataforma lembra-se de si: o seu nome, o seu lugar e os seus alertas. Tudo o resto continua aberto a todos, sem conta.")
    esquerda, direita = st.columns([1, 1.15], gap="large")
    with esquerda, st.container(key="caixa_entrar"):
        formulario_entrar()
    with direita, st.container(key="caixa_criar"):
        formulario_criar()
    T.note("A senha nunca é guardada: guardamos só uma impressão digital dela, que ninguém consegue ler, nem a equipa. "
           "Os seus dados só servem para a sua conta e para os alertas que pedir, e pode apagá-los quando quiser.", "neutra")


# ----------------------------------------------------------------------------- shell
ESCONDIDAS = {"zona", "conta"}                           # pages opened from the search bar and the account button, not from the bars
if st.session_state.get("pagina") not in {*PAGINAS, *ESCONDIDAS}:     # first visit, an old session or an old address (?p=mapa): the page that has it now
    pedida = st.session_state.get("pagina") or st.query_params.get("p")
    pedida = ANTIGAS.get(pedida, pedida)
    if pedida == "zona" and not st.session_state.get("zona"):        # a shared page of a place: ?p=zona&lugar=Machubo
        st.session_state["zona"] = st.query_params.get("lugar", "")
    st.session_state["pagina"] = pedida if pedida in PAGINAS or pedida in ESCONDIDAS else "inicio"
pagina = st.session_state["pagina"]
restaurar_sessao()

with st.container(key="utilidades", horizontal=True, vertical_alignment="center", gap="small"):
    T.status(f"{EMITIDO:%d/%m, %H:%M}", VALIDO, pd.Timestamp(BOLETIM["valido_ate"]).strftime("%d/%m") if VALIDO else "")
    st.button(t("Receber alertas no WhatsApp"), on_click=ir_para, args=("alertas",), key="ir_alertas", icon=":material/notifications:")
    T.html(T.social(small=True), "content")
    st.radio("Língua · Language · Langue", list(L.LINGUAS), key="lingua", horizontal=True, label_visibility="collapsed", format_func=lambda k: L.LINGUAS[k])
# The two bars show where the reader is (none is lit on the page of a place, which is not in them) and open a page when tapped.
with st.container(key="cabecalho", horizontal=True, vertical_alignment="center", gap="small"):
    T.brand()
    st.session_state["nav_topo"] = pagina if pagina in PAGINAS else None
    st.radio(t("Página"), list(PAGINAS), index=None, horizontal=True, key="nav_topo", label_visibility="collapsed", format_func=lambda k: t(PAGINAS[k]),
             on_change=lambda: ir_para(st.session_state["nav_topo"]) if st.session_state.get("nav_topo") else None)
    if conta_actual() or contas.permanente():            # the account button: "Entrar", or the person's first name
        st.button(primeiro_nome(conta_actual()) if conta_actual() else t("Entrar"), on_click=ir_para, args=("conta",), key="ir_conta",
                  icon=":material/account_circle:")
gravar_cookie()
st.session_state["nav_movel"] = pagina if pagina in MOVEL else None
st.radio(t("Navegação"), list(MOVEL), index=None, horizontal=True, key="nav_movel", label_visibility="collapsed",
         format_func=lambda k: f":material/{MOVEL[k][0]}: {t(MOVEL[k][1])}",
         on_change=lambda: ir_para(st.session_state["nav_movel"]) if st.session_state.get("nav_movel") else None)
barra_de_pesquisa(pagina)
st.query_params["p"] = pagina
st.query_params["lang"] = L.lingua()
if pagina == "zona" and st.session_state.get("zona"):
    st.query_params["lugar"] = st.session_state["zona"]
elif "lugar" in st.query_params:
    del st.query_params["lugar"]
# A new page starts at the top, as on any website, or at the section a button or the search asked for (also on the same page).
ancora = st.session_state.pop("_ancora", None)
if st.session_state.get("_pagina_mostrada") != pagina or ancora is not None:
    st.session_state["_pagina_mostrada"] = pagina
    vez = st.session_state["_rolagens"] = st.session_state.get("_rolagens", 0) + 1
    st.html(f"<script>/* {pagina} {ancora or ''} {vez} */ (() => {{ (document.querySelector('[data-testid=\"stMain\"]') || window).scrollTo({{top: 0}}); const id = '{ancora or ''}';"
            " if (!id) return; let n = 0; const ir = () => { const el = document.getElementById(id); if (el) { el.scrollIntoView({block: 'start'});"
            " setTimeout(() => el.scrollIntoView({block: 'start'}), 900); } else if (n++ < 60) setTimeout(ir, 150); }; setTimeout(ir, 150); })();</script>",
            unsafe_allow_javascript=True)

{"inicio": pagina_inicio, "agua": pagina_agua, "cheias": pagina_cheias, "alertas": pagina_alertas, "sobre": pagina_sobre, "zona": pagina_zona,
 "conta": pagina_conta}[pagina]()
if pagina == "inicio" and not st.session_state.get("_convite_visto") and st.query_params.get("convite") != "0":
    convite_alertas()

T.footer(CATALOGO["aviso"], CATALOGO.get("pagina_simples", ""))
