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
from pathlib import Path

import pandas as pd
import streamlit as st

import textos
import idioma as L
import inscricoes
import alertas_whatsapp
import conselhos
import graficos as G
import leitor
import tema as T

# A running server keeps the helper modules it first loaded. When one of them changes on disk it
# is loaded again here (translations first), so an update never leaves the app calling a function
# the old copy lacks.
# The modules are listed so that each comes after the ones it uses: once one is reloaded, all the
# following ones are reloaded too, so none keeps pieces of an old copy (for example translations).
_recarregar = False
for _modulo in (textos, L, inscricoes, alertas_whatsapp, conselhos, T, G):
    _alterado = Path(_modulo.__file__).stat().st_mtime
    if _recarregar or getattr(_modulo, "_carregado_em", None) != _alterado:
        importlib.reload(_modulo)
        _recarregar = True
    _modulo._carregado_em = _alterado
t = L.t

if st.session_state.get("lingua") not in L.LINGUAS:           # first visit: honour a shared address such as ?lang=en
    st.session_state["lingua"] = st.query_params.get("lang", "pt") if st.query_params.get("lang") in L.LINGUAS else "pt"
st.set_page_config(page_title=t("Eyes to Earth · Qualidade da água e cheias do Incomáti"), page_icon=str(Path(__file__).parent / "static" / "ete_icone.png"),
                   layout="wide", initial_sidebar_state="collapsed")
T.html(T.CSS)

PAGINAS = {"inicio": "Início", "agua": "Qualidade da água", "conselhos": "Conselhos", "cheias": "Cheias", "alertas": "Alertas", "mapa": "Mapa", "lugares": "Lugares", "historico": "Histórico",
           "modelos": "Modelos", "projecto": "O projecto", "sobre": "Como funciona"}
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


def ir_para(pagina: str) -> None:
    st.session_state["pagina"] = pagina


def num(valor, casas: int = 0) -> str:
    return L.numero(valor, casas)


def longe_dos_limites(fora: dict) -> str:
    return ", ".join(t("{nivel} a partir de {valor} m³/s", nivel=t(k), valor=num(v)) for k, v in fora.items())


def mapa_interativo(centro, zoom):
    import folium

    mapa = folium.Map(location=list(centro), zoom_start=zoom, tiles="CartoDB positron", prefer_canvas=True)
    folium.GeoJson(geojson("distrito", V), style_function=lambda f: {"color": T.NAVY, "weight": 2, "fill": False}).add_to(mapa)
    return mapa, folium


def mostrar_mapa(mapa, altura: int = 540) -> None:
    from streamlit_folium import st_folium

    st_folium(mapa, height=altura, use_container_width=True, returned_objects=[])


def cenarios_do_boletim() -> pd.DataFrame:
    cenarios = tabela("cenarios_caudal", V)
    dias = pd.to_datetime(cenarios.index)
    return cenarios[(dias >= HOJE) & (dias <= pd.Timestamp(BOLETIM["valido_ate"]))]


# ----------------------------------------------------------------------------- 1. home
def seccao_qualidade_inicio() -> None:
    """Water quality right after the alert: the project's main objective, easy to find."""
    with T.guard("a monitorização da água"):
        if "qualidade_estado" not in CAMADAS:
            return
        estado_agua = serie("qualidade_estado", V).set_index("troco")
        em_alta = int(estado_agua["classe"].isin(["elevada", "muito elevada"]).sum())
        T.section("Qualidade da água do rio, da fronteira à foz",
                  "Cada círculo é um troço do Incomáti. A cor diz como está a água no último mês medido por satélite, comparada com o que é costume nessa época.",
                  "Qualidade da água")
        T.river_tiles(estado_agua, {i["nome"]: i["cor"] for i in CAMADAS["trocos_modulo_q"]["legenda"]})
        T.legend(CAMADAS["trocos_modulo_q"]["legenda"])
        a, b = st.columns([3, 2], gap="medium")
        with a:
            T.note(t("Agora, <b>{n} de {total}</b> troços têm a água mais turva do que o costume para a época.", n=em_alta, total=len(estado_agua))
                   + " " + t("O satélite vê a cor da água (lama e plantas), não vê micróbios nem químicos. <b>Trate sempre a água do rio antes de beber.</b>"))
        with b:
            st.button(t("Abrir a qualidade da água"), on_click=ir_para, args=("agua",), key="ir_painel", type="primary", width="stretch")


def pagina_inicio() -> None:
    if not VALIDO:
        T.hero_unavailable()
        with st.container(key="accoes", horizontal=True, gap="small"):
            st.button(t("Ver a qualidade da água"), on_click=ir_para, args=("agua",), type="primary", key="ir_agua")
            st.button(t("Ver os mapas"), on_click=ir_para, args=("mapa",), key="ir_mapa")
            st.button(t("Conhecer o projecto"), on_click=ir_para, args=("projecto",), key="ir_projecto")
        T.section("O que fazer com a água hoje", "Conselhos práticos, conforme o que os dados mostram hoje.", "Conselhos")
        resumo_de_conselhos()
        seccao_qualidade_inicio()
        return
    nivel = BOLETIM["nivel_maximo_provavel"]
    T.hero(nivel, BOLETIM["titulo"], CORES[nivel], BOLETIM["conselho"], L.dia_mes(BOLETIM["valido_ate"]), f"{EMITIDO:%d/%m, %H:%M}", CORES, HOJE)
    with st.container(key="accoes", horizontal=True, gap="small"):
        st.button(t("Ver a previsão de cheias"), on_click=ir_para, args=("cheias",), type="primary", key="ir_cheias")
        st.button(t("Ver a qualidade da água"), on_click=ir_para, args=("agua",), key="ir_agua")
        st.button(t("Abrir o mapa"), on_click=ir_para, args=("mapa",), key="ir_mapa")
        st.button(t("Conhecer o projecto"), on_click=ir_para, args=("projecto",), type="tertiary", key="ir_projecto")

    T.section("O que fazer com a água hoje", "Conselhos práticos, conforme o que os dados mostram hoje.", "Conselhos")
    resumo_de_conselhos()
    seccao_qualidade_inicio()

    dias = BOLETIM["previsao_diaria"]
    hoje, previsao = dias[0], tabela("previsao_alertas", V)
    maximo = max(dias, key=lambda d: d["caudal_mediana_m3s"])
    falta = LIMITES.get("amarelo", 0) - maximo["caudal_mediana_m3s"]
    T.section("O rio em números", "O que os satélites e os modelos dizem esta manhã sobre o Incomáti em Marracuene.", "Hoje")
    T.kpis([
        {"rotulo": "Caudal do rio hoje", "valor": num(hoje["caudal_mediana_m3s"]), "unidade": "m³/s", "nota": "Incomáti em Marracuene"},
        {"rotulo": "Caudal mais alto em 10 dias", "valor": num(maximo["caudal_mediana_m3s"]), "unidade": "m³/s",
         "nota": t("previsto para {dia}", dia=pd.Timestamp(maximo["data"]).strftime("%d/%m"))},
        {"rotulo": "Distância ao limite amarelo", "valor": num(falta) if falta > 0 else t("acima"), "unidade": "m³/s" if falta > 0 else "",
         "nota": t("limite: {valor} m³/s", valor=num(LIMITES.get("amarelo")))},
        {"rotulo": "Chuva na bacia, 7 dias", "valor": num(hoje["chuva_7d_mm"]), "unidade": "mm", "nota": "média em toda a bacia"},
        {"rotulo": "Boletim válido até", "valor": pd.Timestamp(BOLETIM["valido_ate"]).strftime("%d/%m"), "nota": "actualizado todas as manhãs"},
    ])

    T.section("Os próximos dez dias", "Toque nas setas para andar de dia em dia. A barra de cor por baixo de cada dia é o nível de alerta.", "Previsão de cheias")
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
        with T.guard("o estado da água do rio"):
            turbidez = tabela("turbidez", V)
            if len(turbidez):
                cores = {c["nome"]: c["cor"] for c in CAMADAS["trocos_do_rio"]["legenda"]}
                corpo = "".join(f"<span class='ete-chip'>{T.dot(cores.get(l['estado'], '#bdc3c7'))}<b>{L.troco(nome)}</b>&nbsp;· {t(l['estado'])}</span>" for nome, l in turbidez.iterrows())
                T.card("Água do rio em Marracuene", corpo + f"<p class='ete-miudo' style='margin-top:10px'>{t('Cor da água vista por satélite nos últimos 20 dias.')}</p>", "Qualidade", "suave")

    with T.guard("a mensagem para os líderes"):
        mensagem = leitor.caminho(CAMADAS["boletim"].get("mensagem", ""))
        if mensagem.is_file():
            T.section("A mensagem de hoje, pronta a enviar", "Um texto curto para os líderes comunitários partilharem por WhatsApp ou SMS.", "Para as comunidades")
            a, b = st.columns([3, 2], gap="medium")
            with a:
                T.message(mensagem.read_text())
            with b:
                T.card("Como usar", f"<p>{t('Descarregue o texto e envie-o tal como está. Foi escrito para caber num SMS e para se perceber sem mapas nem gráficos.')}</p>"
                       f"<p class='ete-miudo'>{t('É actualizado todas as manhãs, com o boletim.')}</p>"
                       + (f"<p class='ete-miudo'>{t('A mensagem fica sempre em português, a língua das comunidades de Marracuene.')}</p>" if L.lingua() != "pt" else ""))
                st.download_button(t("Descarregar a mensagem"), mensagem.read_text().encode("utf-8"), "mensagem_ete.txt", "text/plain")
                T.card("Quer receber os alertas no seu WhatsApp?", "<p>" + t("Deixe o seu número e onde vive. Só escrevemos quando houver perigo de cheia.") + "</p>", kind="suave")
                st.button(t("Receber alertas no meu WhatsApp"), on_click=ir_para, args=("alertas",), key="ir_alertas_inicio", type="primary")


# ----------------------------------------------------------------------------- 2. the project
def pagina_projecto() -> None:
    T.page_head("O projecto", "Olhos no céu para proteger quem vive junto ao rio",
                "O <b>Eyes to Earth</b> usa imagens de satélite e machine learning para vigiar a qualidade da água do rio Incomáti e avisar das cheias em Marracuene, província de Maputo. "
                "Transforma dados abertos, que já existem mas não chegam às pessoas, em alertas e mapas simples, actualizados todos os dias.")

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
            T.kpis([{"rotulo": "Estações públicas de qualidade da água", "valor": num(f["estacoes_publicas_de_qualidade_na_bacia"]), "nota": "na bacia (arquivo GEMStat)"},
                    {"rotulo": "Anos com alerta laranja ou vermelho", "valor": t("{n} em {total}", n=f"{f['anos_com_alerta_laranja_ou_vermelho']:.0f}", total=f"{f['anos_analisados']:.0f}"),
                     "nota": "2006 a 2026"},
                    {"rotulo": "Área alagada em janeiro de 2026", "valor": num(f["area_alagada_cheia_grande_km2"]), "unidade": "km²", "nota": "no distrito"},
                    {"rotulo": "Edifícios na zona alagada", "valor": num(f["edificios"])}, {"rotulo": "Terras agrícolas alagadas", "valor": num(f["terras_agricolas_km2"]), "unidade": "km²"}])

    T.section("O nosso objectivo", "Uma plataforma com dois módulos, que avisa de forma automática e em linguagem simples.", "Para quê")
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

    T.section("Para quem", "Quatro grupos de pessoas, a mesma informação, dita de maneira que sirva a cada um.", "Quem serve")
    T.feature_cards([
        {"icone": "casa", "titulo": "Famílias e líderes comunitários", "texto": "Saber, numa frase, se há perigo e o que fazer. A mensagem diária segue por WhatsApp ou SMS."},
        {"icone": "campo", "titulo": "Agricultores e pescadores", "texto": "Saber quando o rio vai subir e como está a água que usam."},
        {"icone": "escudo", "titulo": "Autoridades locais e protecção civil", "texto": "Mapas de onde a água chega primeiro e o que está exposto, como apoio aos avisos oficiais."},
        {"icone": "livro", "titulo": "Estudantes e investigadores", "texto": "Dados abertos, métodos explicados e resultados que se podem repetir."}])

    T.section("Como funciona", "Só com dados abertos e de acesso imediato: nenhuma informação depende de pedidos a instituições.", "O método")
    T.steps([("Satélites", "Sentinel-1 (radar), Sentinel-2 e Landsat (imagem), mais chuva, caudal e terreno: 20 anos de dados."),
             ("Machine learning", "Modelos que detectam água, mapeiam o risco do terreno, prevêem o caudal e a turbidez. Cada um foi comparado com alternativas e testado em dados que nunca viu."),
             ("Regras de alerta claras", "O nível de alerta compara o caudal e a chuva previstos com 25 anos de história."),
             ("Todos os dias", "Um boletim, uma mensagem curta e esta plataforma são actualizados de manhã, de forma automática.")])
    with st.container(key="accoes_proj", horizontal=True, gap="small"):
        st.button(t("Ver os modelos e os testes"), on_click=ir_para, args=("modelos",), key="proj_modelos")
        st.button(t("Ver até onde confiar"), on_click=ir_para, args=("sobre",), key="proj_sobre")

    T.section("Uma regra que não se quebra", eyebrow="Rigor")
    T.card("Nunca inventar dados.", "<p>" + t("Um mês sem imagem limpa fica vazio. Um satélite que não existia num ano fica marcado como ausente. "
           "Os testes que falharam estão publicados ao lado dos que passaram. E o que o satélite não vê (micróbios, químicos, pH) é dito com todas as letras.") + "</p>", kind="tinta")

    T.section("Com o apoio de", eyebrow="Apoio")
    T.card("", "<p>" + t("Projecto financiado pelo <b>IAU Office of Astronomy for Development (OAD)</b> e apoiado pelo <b>DARA (Development in Africa with Radio Astronomy)</b>: "
           "usar a ciência e as técnicas da observação do céu para resolver problemas na Terra.") + "</p>" + T.support_logos(dark_background=False), kind="suave")
    T.section("Fale connosco", "Para questões técnicas, parcerias ou para nos dizer o que falta na plataforma.", "Contactos")
    T.card("", T.social().replace("ete-redes", "ete-redes claras")
           + f"<p><b>{t('Questões técnicas')}:</b> <a href='mailto:{T.CONTACTOS['email']}'>{T.CONTACTOS['email']}</a></p>"
           + f"<p><b>WhatsApp:</b> <a href='{T.CONTACTOS['whatsapp']}' target='_blank' rel='noopener'>{T.CONTACTOS['telefone']}</a></p>")
    T.note("Serviço experimental. Não substitui os avisos oficiais do INGD, do INAM e da ARA-Sul. Se as autoridades derem uma ordem, siga a ordem.", "aviso")


# ----------------------------------------------------------------------------- 3. flood forecast
def pagina_cheias() -> None:
    T.page_head("Cheias", "Como vai estar o rio nos próximos dias", "A previsão do caudal do Incomáti, a chuva que caiu em toda a bacia e o que quer dizer cada nível de alerta.")
    proximos, chuva, niveis, anos = st.tabs([t("Próximos 10 dias"), t("Chuva na bacia"), t("Níveis de alerta"), t("Últimos 3 anos")])
    with proximos:
        if not VALIDO:
            T.note("Sem previsão válida para mostrar. Consulte os avisos oficiais.", "aviso")
        else:
            with T.guard("a previsão de caudal"):
                desenho, fora = G.forecast(cenarios_do_boletim(), LIMITES, CORES_LIMITES)
                grafico(desenho)
                nota = t("A linha é o cenário central; a faixa clara vai do mínimo ao máximo provável, entre 51 cenários do modelo europeu GloFAS.")
                T.caption(nota + (" " + t("O rio está longe dos limites: {limites}.", limites=longe_dos_limites(fora)) if fora else ""))
            with T.guard("a tabela da previsão"):
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
    with chuva:
        with T.guard("a chuva na bacia"):
            grafico(G.rain(tabela("chuva_bacia", V), HOJE))
            T.caption("Chuva média em toda a bacia do Incomáti, que inclui partes da África do Sul e de Essuatíni. É esta chuva que faz o rio subir em Marracuene, "
                      "dias depois. A chuva prevista só entra no alerta até 7 dias à frente.")
    with niveis:
        T.level_cards(LIMITES, CORES, CONSELHOS)
        T.caption("Os limites de caudal foram calculados com 25 anos de dados (1997 a 2021) e testados nos anos seguintes. Na cheia de janeiro de 2026, "
                  "estas regras teriam dado alerta laranja 4 a 5 dias antes do primeiro mapa de cheia.")
    with anos:
        with T.guard("o histórico de caudal"):
            grafico(G.history(serie("caudal_e_chuva", V), LIMITES, CORES_LIMITES))
            T.legend([{"nome": t("limite {nivel}: {valor} m³/s", nivel=t(k), valor=num(v)), "cor": CORES_LIMITES[k]} for k, v in LIMITES.items() if k in CORES_LIMITES])
            limites("caudal_e_chuva")


# ----------------------------------------------------------------------------- 4. map
def pagina_mapa() -> None:
    T.page_head("Mapa", "Onde a água chega primeiro", "As zonas de aviso de Marracuene, o terreno que favorece cheias e o que o radar viu em cada mês.")
    opcoes = {"zonas_de_aviso": "Zonas de aviso", "suscetibilidade": "Terreno que favorece cheias", "agua_mensal": "Água vista por radar, mês a mês"}
    controlo, vista = st.columns([1, 2.4], gap="medium")
    with controlo:
        escolha = st.radio(t("Camada"), list(opcoes), key="camada_mapa", format_func=lambda k: t(opcoes[k]))
        camada = CAMADAS[escolha]
        interativo = st.toggle(t("Mapa interactivo (gasta mais dados)"), value=False, key="mapa_cheias")
        T.card("", f"<p style='margin:0 0 8px 0'>{t(camada.get('descricao', ''))}</p>" + " ".join(T.chip(i["nome"], i["cor"]) for i in camada.get("legenda", [])), "Legenda")
        nome = ""
        with T.guard("a pesquisa de lugares"):
            lugares = serie("lugares_por_ordem", V)
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
    with vista:
        with T.guard("o mapa"):
            mes = None
            if escolha == "agua_mensal":
                mes = T.stepper("mes_radar", camada["meses"], L.mes_ano, "mês mostrado")
            if not interativo and camada.get("mapa_leve"):
                st.image(str(leitor.caminho(camada["mapa_leve"])), width=720)
            elif not interativo and escolha == "agua_mensal":
                ficheiro, _ = leitor.imagem("agua_mensal", mes)
                st.image(str(ficheiro), width=680)
                T.caption("Imagem do mês (azul: água habitual; vermelho: água fora do habitual). Ligue o mapa interactivo para a ver sobre o mapa de base.")
            else:
                if not interativo:
                    T.caption("Esta camada só existe em mapa interactivo.")
                mapa, folium = mapa_interativo((-25.68, 32.72), 10)
                if escolha == "zonas_de_aviso":
                    ficheiro, cantos = (leitor.caminho(camada["imagem"]), camada["cantos"]) if camada.get("imagem") else (None, None)
                else:
                    ficheiro, cantos = leitor.imagem(escolha, mes)
                if ficheiro is not None:
                    folium.raster_layers.ImageOverlay(str(ficheiro), bounds=cantos, opacity=0.8).add_to(mapa)
                else:                                # older package without the light image: draw the polygons
                    folium.GeoJson(geojson("zonas_de_aviso", V), style_function=lambda f: {"color": f["properties"]["cor"], "weight": 1, "fillOpacity": 0.45}).add_to(mapa)
                for lugar in geojson("lugares", V)["features"]:
                    p = lugar["properties"]
                    if p["categoria"] in ("alaga primeiro", "alaga em cheia grande") or p["lugar"] == nome:
                        lon, lat = lugar["geometry"]["coordinates"]
                        folium.CircleMarker([lat, lon], radius=8 if p["lugar"] == nome else 4, color=CORES_LUGARES.get(p["categoria"], "#566573"), fill=True, fill_opacity=0.95,
                                            tooltip=f"{p['lugar']}: {t(p['categoria'])}").add_to(mapa)
                mostrar_mapa(mapa)
            limites(escolha)


# ----------------------------------------------------------------------------- 5. water quality
def pagina_agua() -> None:
    T.page_head("Qualidade da água", "Como está a água do Incomáti", "A cor da água vista por satélite em nove troços, da fronteira à foz, comparada com o que é costume em cada época do ano.")
    T.note("O satélite vê o que muda a cor da água: lama e plantas à superfície. Não vê micróbios nem químicos. "
           "Nada nesta página diz se a água é segura: **a água do rio deve ser sempre tratada antes de beber.**")
    if "trocos_modulo_q" not in CAMADAS:
        T.note("O pacote ainda não tem os dados por troço, da fronteira à foz.", "aviso")
        return
    resumo_de_conselhos(maximo=5)
    estado = serie("qualidade_estado", V).set_index("troco")
    mensal = serie("qualidade_mensal", V)
    cores = {i["nome"]: i["cor"] for i in CAMADAS["trocos_modulo_q"]["legenda"]}
    ordem = list(estado["nome"])
    with T.guard("os números da monitorização"):
        resumo = json.loads(leitor.caminho("qualidade/resumo.json").read_text())
        em_alta = int(estado["classe"].isin(["elevada", "muito elevada"]).sum())
        T.kpis([{"rotulo": "Troços vigiados", "valor": resumo["trocos"], "nota": "da fronteira à foz, 295 km"},
                {"rotulo": "Acima do normal agora", "valor": t("{n} de {total}", n=em_alta, total=len(estado)), "nota": "no último mês medido"},
                {"rotulo": "Dias com medição", "valor": num(resumo["dias_com_medicao"]), "nota": t("desde {ano}", ano=resumo["primeira_medicao"][:4])},
                {"rotulo": "Última medição", "valor": pd.Timestamp(resumo["ultima_medicao"]).strftime("%d/%m/%Y"), "nota": "por satélite"},
                {"rotulo": "Troços com medição fiável", "valor": t("{n} de {total}", n=resumo["trocos_fiaveis"], total=resumo["trocos"]), "nota": "dois satélites concordam"}])
    painel, manhas, rio, troco_tab, comparar, satelite = st.tabs([t("Painel de monitorização"), t("Próximas manhãs"), t("O rio todo"), t("Explorar um troço"),
                                                                  t("Comparar troços"), t("Como medimos")])

    with painel:
        T.subtitle("O rio agora, da fronteira (Q1) à foz (Q9)")
        T.river_tiles(estado, cores)
        T.legend(CAMADAS["trocos_modulo_q"]["legenda"])
        T.subtitle("O ano, mês a mês")
        with T.guard("o painel de monitorização"):
            anos = sorted(int(a) for a in mensal.loc[mensal["ndti"].notna(), "ano"].unique())
            ano = T.stepper("ano_agua", anos, lambda a: t("Ano de {ano}", ano=a), "cada quadrado é um troço num mês")
            cores_painel = {**cores, "sem dados": "#E6EBF1"}
            grafico(G.monitoring_matrix(mensal[mensal["ano"] == ano], cores_painel, ordem))
            T.caption("Cada linha é um troço do rio; cada coluna, um mês. Azul: água como é costume nessa época. Castanho: mais turva do que o costume. Cinzento: sem imagem limpa nesse mês "
                      "(nunca se preenche com estimativas). A montante de Manhiça só há medições desde 2017.")
        esquerda, direita = st.columns(2, gap="medium")
        with esquerda, T.guard("o perfil do rio"):
            T.subtitle("A cor da água ao longo do rio")
            perfil = mensal[(mensal["ano"] >= 2017) & mensal["ndti_s2"].notna()].assign(epoca=lambda d: "época " + d["epoca"])
            perfil = perfil.groupby(["troco", "nome", "epoca"]).agg(ndti=("ndti_s2", "median"), meses=("ndti_s2", "count")).reset_index()
            grafico(G.river_profile(perfil, list(estado.index)))
            T.caption("Mediana desde 2017, medida pelo mesmo satélite (Sentinel-2) em todos os troços. Mostra onde a água é habitualmente mais turva e quanto muda com as chuvas.")
        with direita, T.guard("os meses invulgares"):
            T.subtitle("Meses que fugiram ao normal")
            invulgares = pd.read_csv(leitor.caminho("qualidade/meses_invulgares.csv")).sort_values("month", ascending=False)
            T.table(invulgares[["nome", "month", "anomalia_ndti", "anomalia_vegetacao", "caudal_m3s"]].head(40).rename(
                columns={"nome": "Troço", "month": "Mês", "anomalia_ndti": "Desvio da cor", "anomalia_vegetacao": "Desvio das plantas", "caudal_m3s": "Caudal (m³/s)"}), height=320)
            T.caption("Apontados por um modelo (Isolation Forest) que olha para a cor, as plantas e o caudal em conjunto. Um mês apontado é um convite a ir ver, não um diagnóstico.")

    with manhas:
        with T.guard("a previsão para as próximas manhãs"):
            diaria = tabela("turbidez_diaria", V)
            if VALIDO and len(diaria):
                grafico(G.turbidity_heatmap(diaria))
                T.caption("Probabilidade (%) de a água estar mais turva do que o habitual por volta das 9h30, em três troços de Marracuene. Quanto mais escuro, mais provável. "
                          "A cor da água muda com o caudal e com a maré, por isso varia de dia para dia mesmo sem chuva.")
                turbidez = tabela("turbidez", V)
                T.table(turbidez[["estado", "medicoes_em_20_dias", "ultima_medicao", "previsao", "fiabilidade"]].rename(
                    columns={"estado": "Últimos 20 dias", "medicoes_em_20_dias": "Imagens usadas", "ultima_medicao": "Última medição", "previsao": "Mais turva nos próximos dias?",
                             "fiabilidade": "Fiabilidade"}).rename_axis("Troço").reset_index(), {"Últimos 20 dias": CORES_AGUA})
                T.card("", f"<p>{t(CONSELHOS.get('agua_turva', ''))}</p>", "Com água turva", "suave")
            else:
                T.note("Sem previsão válida para mostrar.", "aviso")

    with rio:
        T.subtitle("Da fronteira (Q1, à esquerda) à foz (Q9, à direita)")
        T.river_tiles(estado, cores)
        T.legend(CAMADAS["trocos_modulo_q"]["legenda"])
        alertas = estado[estado["alerta_de_qualidade"] == True]  # noqa: E712
        if len(alertas):
            T.note(t("A verificar em: {trocos}.", trocos=", ".join(L.troco(n) for n in alertas["nome"])) + " "
                   + t("A água está mais turva do que o normal para a época e do que a chuva e o caudal explicam. É um motivo para ir ver, não uma prova de poluição."), "aviso")
        interativo = st.toggle(t("Mapa interactivo (gasta mais dados)"), value=False, key="mapa_agua")
        with T.guard("o mapa dos troços"):
            camada = CAMADAS["trocos_modulo_q"]
            if not interativo and camada.get("mapa_leve"):
                st.image(str(leitor.caminho(camada["mapa_leve"])), width=640)
            else:
                mapa, folium = mapa_interativo((-25.45, 32.5), 9)
                folium.GeoJson(geojson("trocos_modulo_q", V),
                               tooltip=folium.GeoJsonTooltip(["nome", "classe", "mes", "fiabilidade"], aliases=[t("Troço"), t("Estado"), t("Mês medido"), t("Fiabilidade")]),
                               style_function=lambda f: {"color": f["properties"]["cor"], "weight": 5, "fillOpacity": 0.9}).add_to(mapa)
                mostrar_mapa(mapa, 480)
        with T.guard("a tabela dos troços"):
            colunas = {"nome": "Troço", "mes": "Mês medido", "classe": "Estado face ao normal", "fiabilidade": "Fiabilidade", "fonte": "Satélite",
                       "turbidez_fnu_estimada": "Turbidez estimada (FNU)", "vegetacao": "Plantas sobre a água (parte)", "alerta_de_qualidade": "A verificar"}
            T.table(estado[[c for c in colunas if c in estado]].rename(columns=colunas), {"Estado face ao normal": CORES_AGUA})
            limites("trocos_modulo_q")

    with troco_tab:
        codigos = list(estado.index)
        if "troco_i" not in st.session_state:
            st.session_state["troco_i"] = max(len(codigos) - 2, 0)
        escolhido = T.stepper("troco", codigos, lambda c: L.troco(estado.loc[c, "nome"]), "anterior = para montante · seguinte = para a foz")
        T.river_tiles(estado, cores, escolhido)
        linha = estado.loc[escolhido]
        T.kpis([{"rotulo": "Estado", "valor": t(linha["classe"]), "nota": t("mês medido: {mes}", mes=linha["mes"] if isinstance(linha["mes"], str) else "–")},
                {"rotulo": "Medido por", "valor": linha.get("fonte") if isinstance(linha.get("fonte"), str) else "–", "nota": t("fiabilidade {f}", f=t(linha.get("fiabilidade", "–")))},
                {"rotulo": "Turbidez estimada", "valor": num(linha.get("turbidez_fnu_estimada")), "unidade": "FNU", "nota": "sem calibração local"},
                {"rotulo": "Plantas sobre a água", "valor": num(100 * linha["vegetacao"]) if pd.notna(linha.get("vegetacao")) else "–", "unidade": "%", "nota": "parte do canal"}])
        parametros = {"ndti": ("Cor da água (índice): mais alto = mais turva", "Índice de cor"), "vegetacao": ("Plantas sobre a água (parte do canal)", "Parte do canal com plantas"),
                      "turbidez_fnu": ("Turbidez estimada (FNU, sem calibração local)", "Turbidez estimada (FNU)"),
                      "tss_mg_l": ("Sólidos suspensos estimados (mg/L, sem calibração local)", "Sólidos estimados (mg/L)"),
                      "secchi_m": ("Transparência estimada (m, sem calibração local)", "Transparência estimada (m)"), "temp_c": ("Temperatura da água (°C, só troços largos)", "Temperatura (°C)")}
        a, b = st.columns([2, 1])
        coluna = a.selectbox(t("O que ver"), list(parametros), key="parametro_agua", format_func=lambda k: t(parametros[k][0]))
        titulo = parametros[coluna][1]
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
                grafico(G.quality(do_troco, normais, coluna, titulo))
                if coluna == "ndti":
                    T.caption("Cada ponto é um mês. A faixa cinzenta é o intervalo habitual para esse mês do ano; a linha tracejada é o normal. "
                              "A montante de Manhiça o rio é estreito e só há medições desde 2017.")
                    if normais is not None and len(normais):
                        with st.expander(t("O normal de cada mês do ano neste troço")):
                            grafico(G.climatology(normais))
                elif coluna in ("turbidez_fnu", "tss_mg_l", "secchi_m"):
                    T.caption("Estimativa sem medições no rio: serve como ordem de grandeza, não como medição.")
            else:
                T.note("Sem medições deste parâmetro neste troço.", "neutra")
        with T.guard("as tendências"):
            if "qualidade_tendencias" in CAMADAS:
                tendencias = serie("qualidade_tendencias", V)
                tendencias = tendencias[(tendencias["troco"] == escolhido) & (tendencias["periodo"] == "registo completo")]
                if len(tendencias):
                    with st.expander(t("Está a mudar ao longo dos anos?")):
                        T.table(tendencias[["parametro", "tendencia", "leitura", "primeiro_mes", "ultimo_mes"]].rename(
                            columns={"parametro": "Parâmetro", "tendencia": "Tendência", "leitura": "Como ler", "primeiro_mes": "De", "ultimo_mes": "Até"}))
                        limites("qualidade_tendencias")

    with comparar:
        with T.guard("a comparação entre troços"):
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

    with satelite:
        T.steps([("Nove troços", "O rio é seguido da fronteira à foz e cortado em nove partes."), ("Só água pura", "Em cada imagem só contam os píxeis de água afastados das margens, da areia e das plantas."),
                 ("Cor da água", "A relação entre o vermelho e o verde diz quanto sedimento a água traz."), ("O normal de cada mês", "Cada troço é comparado consigo mesmo, na mesma época de outros anos."),
                 ("Dois satélites", "Onde o Sentinel-2 e o Landsat não concordam, a medição fica marcada como menos fiável.")])
        st.button(t("Ver os modelos e os testes em detalhe"), on_click=ir_para, args=("modelos",), key="ir_modelos_agua")
        T.subtitle("O que o satélite vê e o que não vê")
        T.table(pd.DataFrame([
            {"O que": "Lama e sedimentos (turbidez)", "O satélite vê?": "Sim", "Como é mostrado": "\"Normal\", \"elevada\" ou \"muito elevada\" face ao costume do troço"},
            {"O que": "Plantas sobre a água", "O satélite vê?": "Sim", "Como é mostrado": "Parte do canal coberta (mais fiável nos troços largos)"},
            {"O que": "Temperatura da água", "O satélite vê?": "Só nos troços largos", "Como é mostrado": "Graus, de Manhiça à foz"},
            {"O que": "Turbidez em números (FNU), sólidos (mg/L), transparência (m)", "O satélite vê?": "Só por estimativa", "Como é mostrado": "Ordem de grandeza, sem medições no rio"},
            {"O que": "Algas (clorofila)", "O satélite vê?": "Não neste rio", "Como é mostrado": "Não é mostrado: o sinal confunde-se com a lama"},
            {"O que": "Micróbios, pH, oxigénio, nutrientes, metais, pesticidas", "O satélite vê?": "Não", "Como é mostrado": "Só com análises de laboratório"}]), {"O satélite vê?": CORES_SIM_NAO})
        T.caption("Não há nenhuma estação pública de qualidade da água na bacia do Incomáti (arquivo mundial GEMStat), e o projecto não fez medições no rio. "
                  "Por isso tudo o que aqui se mostra é relativo: a água de hoje comparada com a água de costume.")


# ----------------------------------------------------------------------------- 6. history
def pagina_historico() -> None:
    T.page_head("Histórico · 2006 a 2026", "Vinte anos do rio Incomáti", "Quando o rio passou os limites de alerta e como foi cada ano, dia a dia.")
    dados = historico(V)
    por_ano = dados.groupby("ano")["alerta"].value_counts().unstack(fill_value=0).reindex(columns=G.LEVELS, fill_value=0)
    completos = por_ano[por_ano.sum(axis=1) >= 300]
    with T.guard("os números do histórico"):
        maior = dados.loc[dados["caudal_m3s"].idxmax()]
        T.kpis([{"rotulo": "Anos com alerta laranja ou vermelho", "valor": t("{n} em {total}", n=int(((completos["laranja"] + completos["vermelho"]) > 0).sum()), total=len(completos)),
                 "nota": "anos de outubro a setembro"},
                {"rotulo": "Anos com alerta vermelho", "valor": t("{n} em {total}", n=int((completos["vermelho"] > 0).sum()), total=len(completos))},
                {"rotulo": "Dias em laranja ou vermelho", "valor": num(completos["laranja"].sum() + completos["vermelho"].sum()), "nota": "em todo o período"},
                {"rotulo": "Maior caudal", "valor": num(maior["caudal_m3s"]), "unidade": "m³/s", "nota": maior["data"].strftime("%d/%m/%Y")}])
    resumo, calendario, ano_tab, radar = st.tabs([t("Dias de alerta por ano"), t("Calendário"), t("Um ano em detalhe"), t("Água vista por radar")])
    with resumo:
        with T.guard("os dias de alerta por ano"):
            grafico(G.alert_days(completos[["amarelo", "laranja", "vermelho"]], CORES))
            T.caption("Dias em que as regras de alerta teriam dado cada nível. São dias em que o sistema teria avisado, não cheias confirmadas uma a uma no terreno. "
                      "O caudal vem de um modelo mundial (GloFAS), não de uma estação no rio.")
    with calendario:
        with T.guard("o calendário de alertas"):
            mensal = dados.assign(ano_civil=dados["data"].dt.year, mes=dados["data"].dt.month, nivel=dados["alerta"].map({k: i for i, k in enumerate(G.LEVELS)}))
            mensal = mensal.groupby(["ano_civil", "mes"]).agg(nivel=("nivel", "max"), caudal=("caudal_m3s", "max")).reset_index().dropna(subset=["nivel"])
            mensal["alerta"], mensal["ano"] = mensal["nivel"].astype(int).map(dict(enumerate(G.LEVELS))), mensal["ano_civil"]
            grafico(G.level_calendar(mensal, CORES))
            T.caption("O alerta mais alto de cada mês, ano a ano.")
    with ano_tab:
        anos = [int(a) for a in por_ano.index if por_ano.loc[a].sum() >= 200]
        ano = T.stepper("ano_hist", anos, lambda a: t("Ano hidrológico {inicio}/{fim}", inicio=a - 1, fim=a), "de outubro a setembro")
        do_ano = dados[dados["ano"] == ano]
        with T.guard("o ano em detalhe"):
            pico = do_ano.loc[do_ano["caudal_m3s"].idxmax()]
            T.kpis([{"rotulo": "Caudal máximo", "valor": num(pico["caudal_m3s"]), "unidade": "m³/s", "nota": pico["data"].strftime("%d/%m/%Y")},
                    {"rotulo": "Dias em amarelo", "valor": int((do_ano["alerta"] == "amarelo").sum())}, {"rotulo": "Dias em laranja", "valor": int((do_ano["alerta"] == "laranja").sum())},
                    {"rotulo": "Dias em vermelho", "valor": int((do_ano["alerta"] == "vermelho").sum())}])
            grafico(G.year_detail(do_ano, LIMITES, CORES))
            T.caption("A linha é o caudal de cada dia; a fita por baixo é o alerta desse dia; as linhas tracejadas são os limites amarelo, laranja e vermelho.")
    with radar:
        with T.guard("a água vista por radar"):
            grafico(G.flood_area(serie("area_de_agua", V)))
            T.caption("Área com água fora do sítio habitual dentro do distrito, em cada mês, vista pelo radar Sentinel-1 (desde 2015). "
                      "Os primeiros meses de 2015 têm poucas passagens do satélite e devem ser lidos com cuidado; em zonas construídas o modelo marca água a mais.")
            limites("agua_mensal")


# ----------------------------------------------------------------------------- 7. places
def pagina_lugares() -> None:
    T.page_head("Lugares", "Que lugares a água alcança, e por que ordem", "Os lugares de Marracuene dentro das zonas de aviso e o que existe em cada zona: casas, campos, estradas, escolas.")
    exposicao = serie("exposicao", V).set_index("zona")
    lugares = serie("lugares_por_ordem", V)
    with T.guard("a exposição por zona"):
        for zona, linha in exposicao.iterrows():
            T.subtitle(t(zona).capitalize())
            T.kpis([{"rotulo": "Área", "valor": num(linha["area_km2"]), "unidade": "km²"}, {"rotulo": "Terras agrícolas", "valor": num(linha["area_agricola_km2"]), "unidade": "km²"},
                    {"rotulo": "Edifícios", "valor": num(linha["edificios"])}, {"rotulo": "Estradas e caminhos", "valor": num(linha["estradas_km"]), "unidade": "km"},
                    {"rotulo": "Escolas", "valor": num(linha["escolas"])}, {"rotulo": "Unidades de saúde", "valor": num(linha["unidades_de_saude"])}])
        T.caption("Dentro do distrito de Marracuene. As zonas são onde a água chegou na cheia de janeiro de 2026 (mapas do Copernicus EMS). "
                  "As escolas e unidades de saúde vêm do OpenStreetMap, que pode estar incompleto.")
    esquerda, direita = st.columns([1, 1.25], gap="medium")
    with esquerda:
        with T.guard("o mapa dos lugares"):
            st.image(str(leitor.caminho(CAMADAS["zonas_de_aviso"]["mapa_leve"])), width="stretch")
            T.legend(CAMADAS["zonas_de_aviso"]["legenda"])
            st.button(t("Abrir o mapa completo"), on_click=ir_para, args=("mapa",), key="ir_mapa_lugares")
    with direita:
        with T.guard("os edifícios por lugar"):
            cores = {k: v for k, v in CORES_LUGARES.items() if k in set(lugares["categoria"])}
            grafico(G.buildings_by_place(lugares, cores))
    with T.guard("a tabela dos lugares"):
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
                {"Situação": CORES_LUGARES}, height=520)
        T.caption(t("{n} lugares.", n=len(filtrados)) + " " + t("Cada lugar é um ponto com um círculo de 500 m, não um limite oficial de bairro. Os nomes ainda não foram validados no terreno."))
        st.download_button(t("Descarregar a lista de lugares (CSV)"), lugares.to_csv(index=False).encode("utf-8"), "lugares_por_ordem_de_alagamento.csv", "text/csv")


# ----------------------------------------------------------------------------- 8. machine learning
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


def pagina_modelos() -> None:
    T.page_head("Os modelos", "Machine learning para vigiar a água e avisar das cheias", "Que modelos a plataforma usa, com que dados foram treinados, como foram testados e até onde se pode confiar neles.")
    if "modelos_ml" not in CAMADAS:
        T.note("O pacote ainda não tem as fichas dos modelos.", "aviso")
        return
    dados = fichas(V)["dados_de_treino"]
    imagens = dados.get("imagens_modulo_q", {})
    T.kpis([{"rotulo": "Modelos treinados", "valor": "4", "nota": "mais 2 métodos de análise"}, {"rotulo": "Algoritmos comparados", "valor": "4", "nota": "em cada modelo de cheias"},
            {"rotulo": "Linhas nas tabelas de treino", "valor": num(dados.get("train_historico", {}).get("linhas", 0) + dados.get("train_recente", {}).get("linhas", 0)), "nota": "píxeis rotulados, 2006 a 2026"},
            {"rotulo": "Imagens da água analisadas", "valor": num(imagens.get("imagens")), "nota": "três famílias de satélites"},
            {"rotulo": "Anos de dados", "valor": "20", "nota": "2006 a 2026"}])
    geral, agua_b, risco, caudal, turbidez, modulo_q, qualidade, rejeitado = st.tabs(
        [t("Visão geral"), t("Detectar água"), t("Risco do terreno"), t("Prever o caudal"), t("Prever a turbidez"), t("Vigiar a qualidade"), t("Qualidade dos dados"), t("O que rejeitámos")])

    with geral:
        T.subtitle("Do satélite ao aviso")
        T.steps([("Dados abertos", "Radar e imagens ópticas de satélite, chuva, caudal e terreno: 20 anos, sempre com a contagem de observações por píxel."),
                 ("Rótulos independentes", "A \"resposta certa\" vem de fora: água mensal do JRC e os mapas da cheia de 2026 do Copernicus. Um modelo nunca é testado com rótulos feitos por ele."),
                 ("Vários algoritmos", "Regressão logística, Random Forest, Gradient Boosting e XGBoost, com as regras de escolha escritas antes de ver os resultados."),
                 ("Testes exigentes", "Blocos de 3 km para que píxeis vizinhos não entrem no treino e no teste; anos inteiros deixados de fora; um segundo satélite como juiz."),
                 ("Produção", "Os modelos escolhidos correm todos os dias e alimentam o alerta, os mapas e a previsão da água.")])
        T.subtitle("Os modelos, de relance")
        T.feature_cards([
            {"olho": "Turbidez · Gradient Boosting", "titulo": "Prever a turbidez", "texto": "A água vai estar mais turva do que o habitual nas próximas manhãs?", "resultado": "AUC 0,87 a 0,89",
             "nota": "ano deixado de fora; outro satélite como juiz", "chips": ["Qualidade da água", "Início"]},
            {"olho": "Módulo Q · Isolation Forest", "titulo": "Meses invulgares", "texto": "Que meses fogem ao normal de cada troço?", "resultado": "5 % dos meses",
             "nota": "sem rótulos: aponta, não decide", "chips": ["Qualidade da água"]},
            {"olho": "Módulo Q · Mann-Kendall sazonal", "titulo": "Tendências", "texto": "A água está a mudar em 20 anos?", "resultado": "Nenhuma confirmada",
             "nota": "repetido por era de satélite", "chips": ["Qualidade da água"]},
            {"olho": "Modelo B · XGBoost", "titulo": "Detectar água por radar", "texto": "Onde está a água neste mês, mesmo com nuvens?", "resultado": "IoU 0,91 · F1 0,95",
             "nota": "cheia de janeiro de 2026, blocos de 3 km", "chips": ["Mapa", "Histórico"]},
            {"olho": "Modelo A · XGBoost", "titulo": "Risco do terreno", "texto": "Onde o terreno favorece cheias?", "resultado": "AUC 0,96",
             "nota": "anos 2020-21 e a cheia de 2026, nunca vista", "chips": ["Mapa"]},
            {"olho": "Modelo C · XGBoost", "titulo": "Prever o caudal", "texto": "Que caudal terá o rio daqui a 1 a 7 dias?", "resultado": "Melhor do que repetir hoje",
             "nota": "testado em 2022 a 2026", "chips": ["Cheias: segunda opinião"]}])
        T.note("**O nível de alerta em si não é machine learning.** Vem de regras simples e transparentes: o caudal e a chuva previstos comparados com 25 anos de história. "
               "Foi uma escolha: um alerta tem de se poder explicar numa frase.")

    with agua_b:
        ficha_do_modelo("modelo_b_radar", "onde há água em cada mês, mesmo com nuvens?", "Mapa → Água vista por radar; Histórico → Água vista por radar")
        a, b = st.columns(2, gap="medium")
        with a, T.guard("a comparação de algoritmos"):
            T.subtitle("Quatro algoritmos, o mesmo teste")
            grafico(G.ranked_bars(ml("modelo_b_algoritmos", V), "algoritmo", "iou", "IoU na cheia de janeiro de 2026 (1 = perfeito)", "XGBoost"))
        with b, T.guard("o teste das entradas"):
            T.subtitle("Que dados ajudam o modelo")
            grafico(G.ranked_bars(ml("modelo_b_entradas", V), "features", "iou", "IoU na cheia de janeiro de 2026"))
        T.caption("IoU: da área que o modelo ou a referência dizem ser água, que parte é comum aos dois. A referência são os mapas do Copernicus EMS, feitos por analistas. "
                  "Uma regra simples (um só limiar de radar) já chega a 0,88: o modelo acrescenta pouco, mas de forma consistente em todos os blocos.")
        with st.expander(t("Tabela completa dos algoritmos")):
            T.table(ml("modelo_b_algoritmos", V))
        T.note("Limite: validado numa única cheia. Em zonas construídas marca água a mais; por isso os avisos usam as zonas da cheia real, não este mapa.", "aviso")

    with risco:
        ficha_do_modelo("modelo_a_terreno", "que zonas o terreno torna mais fáceis de alagar?", "Mapa → Terreno que favorece cheias")
        a, b = st.columns(2, gap="medium")
        with a, T.guard("a comparação de algoritmos"):
            T.subtitle("Quatro algoritmos, o mesmo teste")
            grafico(G.ranked_bars(ml("modelo_a_algoritmos", V), "algoritmo", "auc_cheia_2026", "AUC na cheia de 2026 (0,5 = acaso)", "XGBoost", (0.5, 1)))
        with b, T.guard("o teste por classe"):
            T.subtitle("As classes de risco batem com a cheia real?")
            classes = ml("modelo_a_teste_2026", V)
            classes = classes.rename(columns={classes.columns[0]: "classe"})
            grafico(G.ranked_bars(classes, "classe", "parte_da_classe_que_alagou", "Parte da classe que alagou em janeiro de 2026"))
        T.caption("O modelo foi treinado com dados até 2019, afinado em 2020-21 e testado numa cheia que nunca viu. Na classe \"muito alta\" alagou quase tudo; na \"baixa\", quase nada. "
                  "A chuva e o caudal foram deixados de fora deste modelo de propósito, para ele descrever só o terreno.")
        with st.expander(t("Tabela completa dos algoritmos e das entradas")):
            T.table(ml("modelo_a_algoritmos", V))
            T.table(ml("modelo_a_entradas", V))

    with caudal:
        ficha_do_modelo("modelo_c_caudal", "que caudal terá o rio nos próximos dias, só com a chuva que já caiu?", "Cheias → coluna \"Segunda opinião\"")
        with T.guard("o acerto do modelo de caudal"):
            acerto = pd.DataFrame(fichas(V)["modelos"].get("modelo_c_caudal", {}).get("skill") or [])
            if len(acerto):
                grafico(G.lead_skill(acerto))
                T.caption("Testado em 2022 a 2026, anos que o modelo não viu. Ganha a quem repete o valor de hoje em todos os prazos, mas reage tarde ao início das cheias: "
                          "por isso é uma segunda opinião, e o alerta usa os 51 cenários do GloFAS.")
                with st.expander(t("Tabela completa")):
                    T.table(acerto)

    with turbidez:
        ficha_do_modelo("modelo_turbidez", "nas próximas manhãs, a água vai estar mais turva do que o habitual?", "Qualidade da água → Próximas manhãs; Início")
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
        T.note("Limites: prevê a cor da água à hora de passagem do satélite (cerca das 9h30); é um índice relativo, sem medições no rio; a maré é calculada, não medida.", "aviso")

    with modulo_q:
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

    with qualidade:
        T.subtitle("Cinco garantias sobre os dados")
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
        with st.expander(t("Fórmulas de turbidez testadas com medições reais (GLORIA)")):
            T.table(ml("validacao_gloria", V))
            T.caption("fator_tipico 2,5 quer dizer que uma estimativa isolada pode ser duas vezes e meia maior ou menor do que a medição. Por isso a plataforma mostra classes, não números.")
        with st.expander(t("Humidade do solo: calibração entre duas fontes")):
            T.table(ml("humidade_do_solo_calibracao", V))

    with rejeitado:
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
        with T.guard("as entradas testadas"):
            with st.expander(t("Entradas testadas no modelo de turbidez")):
                T.table(ml("turbidez_entradas_testadas", V))


# ----------------------------------------------------------------------------- 9. how it works
def pagina_sobre() -> None:
    T.page_head("Como funciona", "De onde vem a informação e até onde confiar nela", "As fontes, os limites de cada mapa e de cada número, as perguntas mais comuns e o estado do sistema hoje.")
    T.note(CATALOGO["aviso"], "aviso")
    resumo, fontes, confianca, perguntas, sistema, glossario = st.tabs([t("Em poucas palavras"), t("Fontes de dados"), t("Até onde confiar"), t("Perguntas frequentes"),
                                                                        t("Estado do sistema"), t("Glossário")])
    with resumo:
        T.steps([("Satélites e modelos", "Todos os dias chegam a previsão de caudal do rio (51 cenários) e a chuva em toda a bacia."),
                 ("Comparação com 25 anos", "O caudal e a chuva previstos são comparados com o que aconteceu desde 1997."),
                 ("Nível de alerta", "Verde, amarelo, laranja ou vermelho para cada um dos próximos dez dias."),
                 ("Onde", "As zonas de aviso mostram onde a água chegou primeiro na cheia de janeiro de 2026, com os nomes dos lugares."),
                 ("Mensagem", "Um boletim e uma mensagem curta, prontos para enviar aos líderes comunitários."),
                 ("Qualidade da água", "A cor da água é medida por satélite, da fronteira à foz, e comparada com o costume de cada época.")])
        with T.guard("os factos do problema"):
            if "factos" in CAMADAS:
                bruto = serie("factos", V)
                f = bruto.set_index(bruto.columns[0])["valor"]
                T.subtitle("O problema, em números")
                T.kpis([{"rotulo": "Anos com alerta laranja ou vermelho", "valor": t("{n} em {total}", n=f"{f['anos_com_alerta_laranja_ou_vermelho']:.0f}", total=f"{f['anos_analisados']:.0f}")},
                        {"rotulo": "Área alagada em janeiro de 2026", "valor": num(f["area_alagada_cheia_grande_km2"]), "unidade": "km²", "nota": "no distrito"},
                        {"rotulo": "Edifícios na zona alagada", "valor": num(f["edificios"])}, {"rotulo": "Terras agrícolas alagadas", "valor": num(f["terras_agricolas_km2"]), "unidade": "km²"},
                        {"rotulo": "Estações públicas de qualidade da água na bacia", "valor": num(f["estacoes_publicas_de_qualidade_na_bacia"]), "nota": "arquivo mundial GEMStat"},
                        {"rotulo": "Troços do rio acompanhados", "valor": num(f["trocos_analisados"]), "nota": "da fronteira à foz"}])
    with fontes:
        T.table(pd.DataFrame([
            {"Informação": "Previsão de caudal do rio", "Fonte": "GloFAS, Copernicus (via Open-Meteo)", "Actualização": "diária"},
            {"Informação": "Chuva prevista e chuva caída na bacia", "Fonte": "ECMWF IFS e ERA5 (via Open-Meteo)", "Actualização": "diária"},
            {"Informação": "Zonas de aviso", "Fonte": "Copernicus EMS, activação EMSR857 (cheia de janeiro de 2026)", "Actualização": "quando houver nova cheia mapeada"},
            {"Informação": "Água vista por radar", "Fonte": "Sentinel-1 (Copernicus) e Modelo B do projecto", "Actualização": "mensal"},
            {"Informação": "Terreno que favorece cheias", "Fonte": "Landsat, CHIRPS, ERA5-Land, Copernicus DEM, MERIT Hydro e Modelo A do projecto", "Actualização": "quando o modelo é treinado"},
            {"Informação": "Cor da água do rio", "Fonte": "Sentinel-2 (Copernicus) e Landsat 5, 7, 8 e 9 (USGS e NASA)", "Actualização": "semanal em Marracuene; mensal no rio todo"},
            {"Informação": "Maré", "Fonte": "calculada a partir do nível do mar na Baía de Maputo (Open-Meteo)", "Actualização": "fixa"},
            {"Informação": "Edifícios, estradas, escolas e unidades de saúde", "Fonte": "Google Open Buildings e OpenStreetMap", "Actualização": "fixa"},
            {"Informação": "Nomes dos lugares", "Fonte": "OpenStreetMap e GeoNames", "Actualização": "por validar no terreno"},
            {"Informação": "Limite do distrito e da bacia", "Fonte": "FAO GAUL e HydroSHEDS", "Actualização": "fixa"}]))
        T.caption("Todos os dados são abertos. O projecto não depende de pedidos a instituições.")
    with confianca:
        a, b = st.columns(2, gap="medium")
        lista = lambda itens: "<ul style='margin:0;padding-left:1.100rem'>" + "".join(f"<li>{t(i)}</li>" for i in itens) + "</ul>"
        with a:
            T.card("O que está provado", lista([
                "Na cheia de janeiro de 2026, as regras de alerta teriam dado laranja 4 a 5 dias antes do primeiro mapa de cheia.",
                "O modelo que detecta água por radar acerta 91 % da área alagada nessa cheia (IoU 0,91), comparado com os mapas do Copernicus.",
                "A cor da água medida por dois satélites diferentes no mesmo dia concorda (correlação 0,85)."]), "Sim", "suave")
        with b:
            T.card("O que ainda não está provado", lista([
                "Tudo o que diz respeito a cheias foi testado com <b>uma única cheia</b>. Outras cheias podem comportar-se de outra maneira.",
                "O acerto da previsão no dia-a-dia está a ser medido desde outubro de 2026, guardando todas as previsões.",
                "Os nomes dos lugares vêm de mapas públicos e não foram confirmados no terreno.",
                "A qualidade da água é um indicador de cor, sem medições no rio."]), "Ainda não")
        with T.guard("a validação dos modelos"):
            if "validacao_cheias" in CAMADAS:
                with st.expander(t("Medidas de acerto dos modelos de cheias")):
                    T.table(serie("validacao_cheias", V))
                    T.caption("IoU, F1 e Kappa vão de 0 a 1 (quanto mais alto, melhor). ROC-AUC: 0,5 é acaso, 1 é perfeito.")
            habilidade = pd.DataFrame(CATALOGO["modelos"].get("turbidez", {}).get("skill") or [])
            if len(habilidade):
                with st.expander(t("Medidas de acerto da previsão de turbidez")):
                    T.table(habilidade.rename(columns={"modelo": "Modelo", "dias": "Dias", "r2": "R²", "mae": "Erro típico", "auc": "AUC", "bss": "Ganho face à época do ano"}))
        with st.expander(t("Até onde confiar em cada camada")):
            T.table(pd.DataFrame([{"Camada": c["titulo"], "Actualização": c.get("atualizacao", ""), "Até onde confiar": c.get("limites", "")} for c in CATALOGO["camadas"] if c.get("limites")]))
    with perguntas:
        for pergunta, resposta in (
                ("O alerta está verde, mas está a chover muito aqui.", "O alerta é para a cheia do rio, que depende da chuva em toda a bacia, incluindo na África do Sul e em Essuatíni. "
                 "A chuva forte no local pode alagar ruas sem o rio subir."),
                ("O meu bairro não aparece.", "Os nomes vêm de mapas públicos e ainda não foram todos confirmados. Veja no mapa se a sua casa fica dentro de uma zona vermelha ou laranja."),
                ("Com quantos dias de avanço avisa?", "Na cheia de janeiro de 2026, o sistema teria dado alerta laranja 4 a 5 dias antes. Só foi testado com essa cheia."),
                ("Posso confiar no número do caudal?", "Vem de um modelo mundial, não de um aparelho no rio. Serve para saber se o rio vai subir muito, não para saber o valor exacto."),
                ("A água está \"normal\". Posso bebê-la?", "Não sem a tratar. O satélite vê a cor da água; não vê micróbios nem químicos. Ferva a água ou use cloro."),
                ("O que quer dizer \"previsão indisponível\"?", "Que a plataforma não tem um boletim das últimas 36 horas. Não quer dizer que não há perigo: nesse caso, ouça os avisos oficiais."),
                ("Isto substitui os avisos do INGD?", "Não. É um serviço experimental. Se as autoridades derem uma ordem, siga a ordem."),
                ("Como posso falar com a equipa?", "Para questões técnicas, escreva para o email no fim da página ou envie uma mensagem por WhatsApp. Também estamos no Facebook e no LinkedIn.")):
            with st.expander(t(pergunta)):
                T.html(f"<p>{t(resposta)}</p>")
    with sistema:
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
        with st.expander(t("Boletim de hoje, completo") + ("" if L.lingua() == "pt" else " " + t("(em português)"))):
            st.markdown(BOLETIM["texto"])
    with glossario:
        T.table(pd.DataFrame([
            {"Palavra": "Caudal", "Quer dizer": "A quantidade de água que passa no rio em cada segundo (m³/s)."},
            {"Palavra": "Bacia", "Quer dizer": "Toda a área de onde a chuva escorre para o rio. A do Incomáti estende-se pela África do Sul, Essuatíni e Moçambique."},
            {"Palavra": "Cenários", "Quer dizer": "51 previsões ligeiramente diferentes do mesmo modelo. Se quase todas concordam, a previsão é mais certa."},
            {"Palavra": "Zona de aviso", "Quer dizer": "Área onde a água chegou na cheia de janeiro de 2026. Zona 1: chegou primeiro. Zona 2: chegou na cheia grande."},
            {"Palavra": "Turbidez", "Quer dizer": "Quanto a água está barrenta."},
            {"Palavra": "Troço", "Quer dizer": "Uma parte do rio. O Incomáti foi dividido em nove, da fronteira (Q1) à foz (Q9)."},
            {"Palavra": "Radar", "Quer dizer": "Satélite que vê através das nuvens. A água calma aparece muito escura."},
            {"Palavra": "Ano hidrológico", "Quer dizer": "De outubro a setembro, para a época das chuvas ficar inteira no mesmo ano."}]))


# ----------------------------------------------------------------------------- 10. WhatsApp alerts
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
    with st.form(f"form_{chave}", clear_on_submit=False, border=False):
        telefone = st.text_input(t("O seu número de WhatsApp"), placeholder="84 123 4567", key=f"{chave}_telefone", max_chars=20)
        lugar = st.selectbox(t("Onde vive?"), [""] + _lugares_para_escolher() + [outro], key=f"{chave}_lugar",
                             format_func=lambda v: t("Escolha o seu bairro ou lugar") if v == "" else t("Outro lugar / não sei") if v == outro else v)
        nome = st.text_input(t("O seu nome (opcional)"), key=f"{chave}_nome", max_chars=60)
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
    try:
        resultado, numero = inscricoes.inscrever(telefone, "" if lugar == outro else lugar, lingua, nome, aceito, sexo=sexo, faixa_etaria=idade, profissao=profissao)
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
        T.card(t("Pronto! Está inscrito."), "<p>" + t("Vamos escrever para <b>{numero}</b> só quando houver perigo de cheia, e quando o perigo passar. "
               "Em breve recebe uma mensagem de boas-vindas.", numero=numero) + "</p>", "WhatsApp", "suave")
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
        if formulario_inscricao("convite"):
            st.button(t("Fechar"), on_click=fechar, key="convite_fechar", width="stretch")
        else:
            st.button(t("Agora não"), on_click=fechar, key="convite_agora_nao", type="tertiary", width="stretch")

    janela()


def pagina_alertas() -> None:
    T.page_head("Alertas no WhatsApp", "Avisamos no seu telefone quando houver perigo de cheia",
                "Deixe o seu número e onde vive. Quando o rio Incomáti estiver perto de alagar Marracuene, recebe uma mensagem curta no WhatsApp.")
    T.steps([("Inscreva-se", "Escreva o seu número de WhatsApp e escolha onde vive. Demora um minuto."),
             ("Só em caso de perigo", "Só escrevemos quando o alerta for laranja ou vermelho, e outra vez quando o perigo passar."),
             ("Lugares e conselhos", "A mensagem diz que lugares podem alagar, o que fazer e traz a ligação para esta plataforma.")])
    esquerda, direita = st.columns([1.15, 1], gap="large")
    with esquerda:
        with st.container(key="caixa_inscricao"):
            T.subtitle("Quero receber os alertas")
            formulario_inscricao("pagina")
    with direita:
        T.subtitle("Exemplo de mensagem")
        with T.guard("o exemplo de mensagem"):
            exemplo = {**BOLETIM, "nivel_maximo_provavel": "laranja", "seguro_mostrar": True}
            texto, _ = alertas_whatsapp.mensagem("alerta", {"lugar": "", "lingua": L.lingua()}, exemplo, serie("lugares_por_ordem", V), CONSELHOS)
            T.message(texto.replace("\n", "<br>"))
            T.caption("Exemplo com o alerta laranja. A mensagem chega na língua que escolher.")
        T.card("O seu número está protegido", "<p>" + t("Fica guardado só para enviar estes alertas. Não aparece na plataforma, não é partilhado nem vendido, "
               "e é apagado da lista quando pede para sair.") + "</p><p>" + t("O sexo, a idade e a profissão, se os indicar, só servem para escolher o conselho da mensagem "
               "e para a equipa saber, em números, que pessoas estão a ser avisadas.") + "</p>", "Privacidade", "suave")
    T.section("Deixar de receber", "Escreva o número inscrito. As mensagens param no envio seguinte.", "Sair")
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
    T.note("Serviço experimental. Não substitui os avisos oficiais do INGD, do INAM e da ARA-Sul. Se as autoridades derem uma ordem, siga a ordem.", "aviso")


# ----------------------------------------------------------------------------- 11. advice on water
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
    """A short version for the home and water pages: today's situations and the first pieces of advice."""
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
        st.button(t("Ver os conselhos para cada público"), on_click=ir_para, args=("conselhos",), key=f"ir_conselhos_{publico}_{maximo}", type="primary")


def pagina_conselhos() -> None:
    T.page_head("Conselhos", "O que fazer com a água, hoje",
                "Todos os dias a plataforma olha para a água do rio e para a previsão de cheias, e diz o que cada pessoa e cada instituição deve fazer.")
    situacoes = situacoes_de_hoje()
    T.section("A situação hoje", "O que os dados mostram e porquê. Os conselhos abaixo mudam com a situação.", "Hoje")
    T.situation_cards(situacoes, razoes)
    T.section("Os conselhos para si", "Escolha o seu grupo.", "Para cada público")
    publico = st.radio(t("Quem é?"), list(conselhos.PUBLICOS), horizontal=True, key="publico_conselhos", label_visibility="collapsed",
                       format_func=lambda k: t(conselhos.PUBLICOS[k][0]))
    for situacao, itens in conselhos.para(publico, situacoes):
        T.advice_card(situacao["titulo"], itens, situacao["nivel"], conselhos.PUBLICOS[publico][0])
    st.download_button(t("Descarregar estes conselhos para partilhar"), texto_para_partilhar(publico, situacoes).encode("utf-8"),
                       f"conselhos_ete_{publico}.txt", "text/plain", key="baixar_conselhos")
    T.section("Como tratar a água em casa", "Seis passos simples para ter água segura para beber, mesmo quando a água do rio vem barrenta.", "Passo a passo")
    T.steps(conselhos.GUIA_TRATAMENTO, colunas=3)
    T.html("<div class='ete-diarreia'><div class='cab'>" + t("Diarreia: o que fazer") + "</div><ol>"
           + "".join(f"<li>{t(i)}</li>" for i in conselhos.DIARREIA) + "</ol></div>")
    T.caption(conselhos.FONTES)
    T.note("O satélite vê a cor da água (lama e plantas), não vê micróbios nem químicos. Por isso a água do rio deve ser sempre tratada antes de beber, "
           "mesmo quando a plataforma diz que está «normal».", "neutra")


# ----------------------------------------------------------------------------- shell
if st.session_state.get("pagina") not in PAGINAS:     # first visit (or an old session): honour a shared address such as ?p=agua
    st.session_state["pagina"] = st.query_params.get("p") if st.query_params.get("p") in PAGINAS else "inicio"

with st.container(key="utilidades", horizontal=True, vertical_alignment="center", gap="small"):
    T.status(f"{EMITIDO:%d/%m, %H:%M}", VALIDO, pd.Timestamp(BOLETIM["valido_ate"]).strftime("%d/%m") if VALIDO else "")
    st.button(t("Receber alertas no WhatsApp"), on_click=ir_para, args=("alertas",), key="ir_alertas", icon="🔔")
    T.html(T.social(small=True), "content")
    st.radio("Língua · Language · Langue", list(L.LINGUAS), key="lingua", horizontal=True, label_visibility="collapsed", format_func=lambda k: L.LINGUAS[k])
with st.container(key="cabecalho", horizontal=True, vertical_alignment="center", gap="small"):
    T.brand()
    pagina = st.radio(t("Página"), list(PAGINAS), horizontal=True, key="pagina", label_visibility="collapsed", format_func=lambda k: t(PAGINAS[k]))
st.query_params["p"] = pagina
st.query_params["lang"] = L.lingua()
if st.session_state.get("_pagina_mostrada") != pagina:     # a new page starts at the top, as on any website
    st.session_state["_pagina_mostrada"] = pagina
    st.html(f"<script>/* {pagina} */ (document.querySelector('[data-testid=\"stMain\"]') || window).scrollTo({{top: 0}});</script>", unsafe_allow_javascript=True)

{"inicio": pagina_inicio, "projecto": pagina_projecto, "cheias": pagina_cheias, "mapa": pagina_mapa, "agua": pagina_agua, "historico": pagina_historico, "lugares": pagina_lugares,
 "modelos": pagina_modelos, "sobre": pagina_sobre, "alertas": pagina_alertas, "conselhos": pagina_conselhos}[pagina]()
if pagina == "inicio" and not st.session_state.get("_convite_visto") and st.query_params.get("convite") != "0":
    convite_alertas()

T.footer(CATALOGO["aviso"], CATALOGO.get("pagina_simples", ""))
