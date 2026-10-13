"""Plataforma ETE: cheias (Quantidade) e água do rio (Qualidade), rio Incomáti, Marracuene.

    pip install -r plataforma/requirements.txt
    streamlit run plataforma/app.py

Lê apenas o pacote `plataforma/dados/` através de `leitor.py`. Não precisa dos dados do
projecto, do Earth Engine nem dos modelos. Páginas: Hoje, Quantidade, Qualidade, Sobre os dados.
"""

import folium
import pandas as pd
import streamlit as st
from streamlit_folium import st_folium

import leitor

st.set_page_config(page_title="ETE - Incomáti, Marracuene", page_icon="🌊", layout="wide", initial_sidebar_state="auto")
try:
    CATALOGO = leitor.catalogo()
    CORES = leitor.camada("boletim")["cores_dos_alertas"]
except Exception:                      # the data package is missing or broken: say so plainly, never show a blank page
    st.error("A plataforma está temporariamente sem dados. Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.")
    st.stop()
PAGINA_SIMPLES = CATALOGO.get("pagina_simples", "")       # address of the light static page, when published
MESES = ["jan", "fev", "mar", "abr", "mai", "jun", "jul", "ago", "set", "out", "nov", "dez"]


def tem(identificador: str) -> bool:
    return any(c["id"] == identificador for c in CATALOGO["camadas"])


def limites(identificador: str) -> None:
    texto = leitor.camada(identificador).get("limites")
    if texto:
        st.caption("Limites: " + texto)


def mapa_base(centro=(-25.68, 32.72), zoom=10) -> folium.Map:
    mapa = folium.Map(location=list(centro), zoom_start=zoom, tiles="OpenStreetMap")
    folium.GeoJson(leitor.geojson("distrito"), style_function=lambda f: {"color": "black", "weight": 2, "fill": False}).add_to(mapa)
    return mapa


def legenda(identificador: str) -> None:
    itens = leitor.camada(identificador).get("legenda", [])
    st.markdown(" &nbsp; ".join(f"<span style='background:{i['cor']};padding:2px 10px;border-radius:3px'>&nbsp;</span> {i['nome']}" for i in itens), unsafe_allow_html=True)


# ----------------------------------------------------------------------------- páginas
def pagina_hoje(boletim: dict) -> None:
    if not boletim["seguro_mostrar"]:
        st.error("Previsão indisponível ou desatualizada. Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.")
        return
    nivel = boletim["nivel_maximo_provavel"]
    texto = "black" if nivel == "amarelo" else "white"
    st.markdown(f"<div style='background:{CORES[nivel]};padding:18px;border-radius:10px;color:{texto};font-size:22px'>"
                f"<b>Alerta {nivel.upper()}</b><br>{boletim['titulo']}</div>", unsafe_allow_html=True)
    st.subheader("O que fazer")
    st.write(boletim["conselho"])
    primeiro, grande = boletim.get("lugares_que_alagam_primeiro") or [], boletim.get("lugares_em_cheia_grande") or []
    if primeiro:
        st.write("**Lugares que alagam primeiro:** " + ", ".join(primeiro))
    if grande:
        st.write("**Lugares atingidos numa cheia grande:** " + ", ".join(grande))
    esquerda, direita = st.columns(2)
    with esquerda:
        st.subheader("Próximos dias")
        dias = pd.DataFrame(boletim["previsao_diaria"])
        dias["data"] = pd.to_datetime(dias["data"]).dt.strftime("%d/%m")
        st.dataframe(dias[["data", "alerta", "caudal_mediana_m3s", "chuva_7d_mm"]].rename(
            columns={"data": "Dia", "alerta": "Alerta", "caudal_mediana_m3s": "Caudal previsto (m³/s)", "chuva_7d_mm": "Chuva 7 dias (mm)"}), hide_index=True, use_container_width=True)
    with direita:
        st.subheader("Água do rio")
        turbidez = leitor.tabela("turbidez")
        if len(turbidez):
            st.dataframe(turbidez[["estado", "previsao"]].rename(columns={"estado": "Últimos 20 dias", "previsao": "Mais turva nos próximos dias?"}), width="stretch")
        st.caption("A água do rio deve ser sempre tratada antes de beber. O satélite vê a cor da água; não mede se é segura.")
    mensagem = leitor.caminho(leitor.camada("boletim").get("mensagem", ""))
    if mensagem.is_file():
        with st.expander("Mensagem para os líderes comunitários (WhatsApp ou SMS)"):
            st.code(mensagem.read_text(), language=None)


def pagina_quantidade(boletim: dict) -> None:
    st.header("Quantidade: cheias")
    opcoes = {"Zonas de aviso": "zonas_de_aviso", "Suscetibilidade a cheias": "suscetibilidade", "Água vista por radar (por mês)": "agua_mensal"}
    escolha = opcoes[st.radio("Camada do mapa", list(opcoes), horizontal=True)]
    mapa = mapa_base()
    if escolha == "zonas_de_aviso":
        folium.GeoJson(leitor.geojson("zonas_de_aviso"), tooltip=folium.GeoJsonTooltip(["nome"]),
                       style_function=lambda f: {"color": f["properties"]["cor"], "weight": 1, "fillOpacity": 0.45}).add_to(mapa)
    else:
        meses = leitor.camada("agua_mensal")["meses"]
        mes = st.select_slider("Mês", meses, value=meses[-1]) if escolha == "agua_mensal" else None
        ficheiro, cantos = leitor.imagem(escolha, mes)
        folium.raster_layers.ImageOverlay(str(ficheiro), bounds=cantos, opacity=0.75).add_to(mapa)
    for lugar in leitor.geojson("lugares")["features"]:
        p = lugar["properties"]
        if p["categoria"] in ("alaga primeiro", "alaga em cheia grande"):
            lon, lat = lugar["geometry"]["coordinates"]
            folium.CircleMarker([lat, lon], radius=4, color="#7b241c" if p["categoria"] == "alaga primeiro" else "#af601a", fill=True,
                                tooltip=f"{p['lugar']}: {p['categoria']}").add_to(mapa)
    st_folium(mapa, height=540, use_container_width=True, returned_objects=[])
    legenda(escolha)
    limites(escolha)

    st.subheader("Caudal previsto do Incomáti em Marracuene (m³/s)")
    cenarios = leitor.tabela("cenarios_caudal")
    if boletim["seguro_mostrar"] and len(cenarios):
        resumo = pd.DataFrame({"mediana": cenarios.median(axis=1), "mínimo provável (10 %)": cenarios.quantile(0.1, axis=1), "máximo provável (90 %)": cenarios.quantile(0.9, axis=1)})
        st.line_chart(resumo)
        st.caption("Limites de alerta (m³/s): " + ", ".join(f"{k} {v:.0f}" for k, v in boletim["estado"]["limites_caudal"].items()))
    else:
        st.warning("Sem previsão de caudal válida para mostrar.")

    st.subheader("Caudal e chuva dos últimos 3 anos")
    historia = leitor.serie("caudal_e_chuva").set_index("data")
    st.line_chart(historia["caudal_m3s"])
    limites("caudal_e_chuva")

    st.subheader("O que está em cada zona de aviso")
    exposicao = leitor.serie("exposicao").set_index("zona")
    st.dataframe(exposicao.drop(columns=[c for c in exposicao if c.startswith("pessoas")]), width="stretch")
    limites("exposicao")
    with st.expander("Lugares por ordem de alagamento (cheia de janeiro de 2026)"):
        lugares = leitor.serie("lugares_por_ordem")
        st.dataframe(lugares[["lugar", "posto_administrativo", "categoria", "primeira_data", "dias_apos_alerta", "edificios"]], hide_index=True, width="stretch")
        limites("lugares")


def pagina_qualidade() -> None:
    st.header("Qualidade: a cor da água do rio")
    st.info("O satélite mede o que muda a cor da água: sedimento (turbidez) e plantas à superfície. Não mede pH, oxigénio, nutrientes, "
            "metais nem bactérias. Nada nesta página diz se a água é segura para beber.")
    if not tem("trocos_modulo_q"):
        st.warning("O pacote ainda não tem os dados do Módulo Q (qualidade por troço).")
        return
    estado = leitor.serie("qualidade_estado").set_index("troco")
    alertas = estado[estado["alerta_de_qualidade"] == True]  # noqa: E712
    if len(alertas):
        st.warning("Alerta de qualidade em: " + ", ".join(alertas["nome"]) + ". A água está mais turva do que o normal para a época e do que a chuva e o caudal explicam. É um motivo para ir ver, não uma prova de poluição.")
    mapa = mapa_base(centro=(-25.45, 32.5), zoom=9)
    folium.GeoJson(leitor.geojson("trocos_modulo_q"), tooltip=folium.GeoJsonTooltip(["nome", "classe", "mes", "fiabilidade"], aliases=["Troço", "Estado", "Mês medido", "Fiabilidade"]),
                   style_function=lambda f: {"color": f["properties"]["cor"], "weight": 5, "fillOpacity": 0.9}).add_to(mapa)
    st_folium(mapa, height=460, use_container_width=True, returned_objects=[])
    legenda("trocos_modulo_q")
    limites("trocos_modulo_q")

    st.subheader("Estado de cada troço, da fronteira à foz")
    colunas = {"nome": "Troço", "mes": "Mês medido", "classe": "Estado face ao normal", "fiabilidade": "Fiabilidade da medição", "fonte": "Satélite", "turbidez_fnu_estimada": "Turbidez estimada (FNU)",
               "vegetacao": "Plantas sobre a água (parte)", "alerta_de_qualidade": "Alerta de qualidade"}
    st.dataframe(estado[[c for c in colunas if c in estado]].rename(columns=colunas), hide_index=True, width="stretch")
    limites("qualidade_estado")

    mensal = leitor.serie("qualidade_mensal")
    nomes = dict(zip(estado["nome"], estado.index))
    escolhido = nomes[st.selectbox("Troço", list(nomes), index=len(nomes) - 2)]
    parametros = {"Índice de cor (NDTI): mais alto = mais turva": "ndti", "Turbidez estimada (FNU)": "turbidez_fnu", "Sólidos suspensos estimados (mg/L)": "tss_mg_l",
                  "Transparência estimada (m)": "secchi_m", "Plantas sobre a água (parte do canal)": "vegetacao", "Temperatura da água (°C, só troços largos)": "temp_c"}
    parametro = parametros[st.selectbox("Parâmetro", list(parametros))]
    serie = mensal[mensal["troco"] == escolhido].assign(data=lambda d: pd.to_datetime(d["month"])).set_index("data")
    st.subheader("Série mensal desde 2006")
    if serie[parametro].notna().any():
        grafico = serie[[parametro]].rename(columns={parametro: "medido"})
        if parametro == "ndti" and serie["esperado"].notna().any():
            grafico["esperado pela chuva e pelo caudal"] = serie["esperado"]
        st.line_chart(grafico)
    else:
        st.write("Sem medições deste parâmetro neste troço.")
    if tem("qualidade_normais") and parametro == "ndti":
        normais = leitor.serie("qualidade_normais")
        normais = normais[normais["troco"] == escolhido].set_index("mes")[["p25", "mediana", "p75"]]
        if len(normais):
            normais.index = [MESES[int(m) - 1] for m in normais.index]
            st.subheader("O normal de cada mês do ano neste troço")
            st.line_chart(normais.rename(columns={"p25": "quartil inferior", "mediana": "normal", "p75": "limite de 'elevada'"}))
    if tem("qualidade_tendencias"):
        tendencias = leitor.serie("qualidade_tendencias")
        tendencias = tendencias[tendencias["troco"] == escolhido]
        if len(tendencias):
            st.subheader("Tendências neste troço")
            st.dataframe(tendencias[["parametro", "periodo", "tendencia", "inclinacao_por_decada", "p", "n"]], hide_index=True, width="stretch")
            limites("qualidade_tendencias")

    st.subheader("Montante e jusante")
    comparacao = mensal.pivot(index="month", columns="nome", values="ndti").dropna(how="all")
    escolha = st.multiselect("Troços a comparar", list(comparacao.columns), default=[c for c in comparacao.columns if c.startswith(("Q1 ", "Q8 "))])
    if escolha:
        comparacao.index = pd.to_datetime(comparacao.index)
        st.line_chart(comparacao.loc["2017":, escolha])

    st.subheader("Previsão para as próximas manhãs (troços de Marracuene)")
    diaria = leitor.tabela("turbidez_diaria")
    if len(diaria):
        st.bar_chart(diaria)
        st.caption("Probabilidade de a água estar mais turva do que o habitual por volta das 9h30. " + leitor.camada("cor_da_agua")["limites"])


def pagina_sobre(boletim: dict) -> None:
    st.header("Sobre os dados")
    st.info(CATALOGO["aviso"])
    st.markdown(boletim["texto"])
    st.subheader("Camadas e os seus limites")
    st.dataframe(pd.DataFrame([{"Camada": c["titulo"], "Atualização": c.get("atualizacao", ""), "Limites": c.get("limites", "")} for c in CATALOGO["camadas"]]),
                 hide_index=True, use_container_width=True)
    st.caption(f"Pacote gerado em {CATALOGO['gerado_utc']} (código {CATALOGO['versao_codigo']}). Fontes: Copernicus, NASA, USGS, ESA, JRC, ECMWF, CHC/UCSB, OpenStreetMap, GeoNames.")


st.title("Eyes to Earth: o rio Incomáti em Marracuene")
BOLETIM = leitor.boletim()
pagina = st.sidebar.radio("Página", ["Hoje", "Quantidade (cheias)", "Qualidade (água do rio)", "Sobre os dados"])
st.sidebar.caption(f"Boletim emitido há {BOLETIM['horas_desde_a_emissao']:.0f} h. " + CATALOGO["aviso"])
if PAGINA_SIMPLES:
    st.sidebar.markdown(f"[Versão leve do boletim (pouca rede)]({PAGINA_SIMPLES})")
if pagina == "Hoje":
    pagina_hoje(BOLETIM)
elif pagina.startswith("Quantidade"):
    pagina_quantidade(BOLETIM)
elif pagina.startswith("Qualidade"):
    pagina_qualidade()
else:
    pagina_sobre(BOLETIM)
