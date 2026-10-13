"""Plataforma ETE: cheias (Quantidade) e água do rio (Qualidade), rio Incomáti, Marracuene.

    pip install -r plataforma/requirements.txt
    cd plataforma && streamlit run app.py

Como está feita
  * Lê apenas o pacote `dados/` através de `leitor.py`: não precisa dos dados do projecto, do
    Earth Engine nem dos modelos.
  * Leve por defeito: os mapas aparecem primeiro como imagens pequenas; o mapa interactivo só é
    carregado quando a pessoa o pede.
  * Segura por defeito: sem um boletim válido das últimas 36 horas, mostra "previsão
    indisponível" e nunca um nível de alerta.
  * Cada secção está protegida: se uma falhar, o resto da página aparece na mesma.
"""

import pandas as pd
import streamlit as st

import leitor
import ui

st.set_page_config(page_title="ETE - Incomáti, Marracuene", page_icon="🌊", layout="wide", initial_sidebar_state="collapsed")
st.markdown(ui.CSS, unsafe_allow_html=True)

PAGINAS = {"hoje": "Hoje", "cheias": "Cheias", "agua": "Água do rio", "sobre": "Sobre os dados"}


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


V = _versao()
try:
    CATALOGO = catalogo(V)
    CAMADAS = {c["id"]: c for c in CATALOGO["camadas"]}
    CORES = CAMADAS["boletim"]["cores_dos_alertas"]
    BOLETIM = leitor.boletim()                       # not cached: its age is checked on every visit
except Exception:                                    # the data package is missing or broken: say so plainly
    st.error("A plataforma está temporariamente sem dados. Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.")
    st.stop()
VALIDO = bool(BOLETIM["seguro_mostrar"])
LIMITES = BOLETIM["estado"].get("limites_caudal", {})
CORES_LIMITES = {k: CORES[k] for k in LIMITES if k in CORES}


def limites(identificador: str) -> None:
    texto = CAMADAS.get(identificador, {}).get("limites")
    if texto:
        st.caption("Até onde confiar: " + texto)


def mapa_interativo(centro, zoom):
    import folium

    mapa = folium.Map(location=list(centro), zoom_start=zoom, tiles="OpenStreetMap", prefer_canvas=True)
    folium.GeoJson(geojson("distrito", V), style_function=lambda f: {"color": "black", "weight": 2, "fill": False}).add_to(mapa)
    return mapa, folium


def mostrar_mapa(mapa, altura: int = 520) -> None:
    from streamlit_folium import st_folium

    st_folium(mapa, height=altura, use_container_width=True, returned_objects=[])


# ----------------------------------------------------------------------------- pages
def pagina_hoje() -> None:
    if not VALIDO:
        ui.unavailable_banner()
        return
    nivel = BOLETIM["nivel_maximo_provavel"]
    ui.alert_banner(nivel, BOLETIM["titulo"], CORES[nivel])
    hoje = BOLETIM["previsao_diaria"][0]
    a, b, c = st.columns(3)
    a.metric("Caudal do rio hoje", f"{hoje['caudal_mediana_m3s']:.0f} m³/s", help="Caudal previsto do Incomáti em Marracuene (modelo GloFAS).")
    b.metric("Chuva na bacia, 7 dias", "-" if hoje["chuva_7d_mm"] is None else f"{hoje['chuva_7d_mm']:.0f} mm", help="Chuva média em toda a bacia do Incomáti nos últimos 7 dias.")
    c.metric("Boletim válido até", pd.Timestamp(BOLETIM["valido_ate"]).strftime("%d/%m"))

    st.subheader("O que fazer")
    st.write(BOLETIM["conselho"])
    primeiro, grande = BOLETIM.get("lugares_que_alagam_primeiro") or [], BOLETIM.get("lugares_em_cheia_grande") or []
    if primeiro:
        st.markdown("**Lugares que alagam primeiro:** " + ", ".join(primeiro))
    if grande:
        st.markdown("**Lugares atingidos numa cheia grande:** " + ", ".join(grande))
    if BOLETIM.get("nivel_maximo_possivel") not in (None, nivel):
        st.info(f"Alguns cenários chegam a {BOLETIM['nivel_maximo_possivel'].upper()}. É menos provável, mas possível.")

    st.subheader("Próximos dias")
    ui.day_strip(BOLETIM["previsao_diaria"], CORES)

    with ui.guard("o estado da água do rio"):
        turbidez = tabela("turbidez", V)
        if len(turbidez):
            st.subheader("Água do rio em Marracuene")
            cores = {c["nome"]: c["cor"] for c in CAMADAS["trocos_do_rio"]["legenda"]}
            ui.chips([(troco, linha["estado"], cores.get(linha["estado"], "#bdc3c7")) for troco, linha in turbidez.iterrows()])
            st.caption("Cor da água vista por satélite nos últimos 20 dias. A água do rio deve ser sempre tratada antes de beber: o satélite não mede se é segura.")

    with ui.guard("a mensagem para os líderes"):
        mensagem = leitor.caminho(CAMADAS["boletim"].get("mensagem", ""))
        if mensagem.is_file():
            with st.expander("Mensagem para enviar aos líderes comunitários (WhatsApp ou SMS)"):
                st.code(mensagem.read_text(), language=None)


def pagina_cheias() -> None:
    st.header("Cheias")
    st.markdown("<p class='ete-sub'>Onde a água chega primeiro, e como o rio deve evoluir.</p>", unsafe_allow_html=True)
    opcoes = {"Zonas de aviso": "zonas_de_aviso", "Terreno que favorece cheias": "suscetibilidade", "Água vista por radar": "agua_mensal"}
    escolha = opcoes[st.radio("Mapa", list(opcoes), horizontal=True, key="camada_cheias")]
    interativo = st.toggle("Mapa interactivo (gasta mais dados)", value=False, key="mapa_cheias")
    with ui.guard("o mapa"):
        camada = CAMADAS[escolha]
        if not interativo and camada.get("mapa_leve"):
            st.image(str(leitor.caminho(camada["mapa_leve"])), width=560)
        else:
            if not interativo:
                st.caption("Esta camada só existe em mapa interactivo.")
            mapa, folium = mapa_interativo((-25.68, 32.72), 10)
            if escolha == "agua_mensal":
                mes = st.select_slider("Mês", camada["meses"], value=camada["meses"][-1])
                ficheiro, cantos = leitor.imagem("agua_mensal", mes)
            elif escolha == "zonas_de_aviso":
                ficheiro, cantos = (leitor.caminho(camada["imagem"]), camada["cantos"]) if camada.get("imagem") else (None, None)
            else:
                ficheiro, cantos = leitor.imagem(escolha)
            if ficheiro is not None:
                folium.raster_layers.ImageOverlay(str(ficheiro), bounds=cantos, opacity=0.8).add_to(mapa)
            else:                                    # older package without the light image: draw the polygons
                folium.GeoJson(geojson("zonas_de_aviso", V), style_function=lambda f: {"color": f["properties"]["cor"], "weight": 1, "fillOpacity": 0.45}).add_to(mapa)
            for lugar in geojson("lugares", V)["features"]:
                p = lugar["properties"]
                if p["categoria"] in ("alaga primeiro", "alaga em cheia grande"):
                    lon, lat = lugar["geometry"]["coordinates"]
                    folium.CircleMarker([lat, lon], radius=4, color="#1c2833", fill=True, fill_opacity=0.9, tooltip=f"{p['lugar']}: {p['categoria']}").add_to(mapa)
            mostrar_mapa(mapa)
        ui.legend(camada.get("legenda", []))
        st.caption(camada.get("descricao", ""))
        limites(escolha)

    st.subheader("Caudal previsto para os próximos dias")
    with ui.guard("a previsão de caudal"):
        cenarios = tabela("cenarios_caudal", V)
        if VALIDO and len(cenarios):
            dias = pd.to_datetime(cenarios.index)
            cenarios = cenarios[(dias >= pd.Timestamp(BOLETIM["estado"]["data_da_previsao"])) & (dias <= pd.Timestamp(BOLETIM["valido_ate"]))]      # the bulletin's ten days
            grafico, fora = ui.forecast_chart(cenarios, LIMITES, CORES_LIMITES)
            st.altair_chart(grafico, use_container_width=True)
            nota = "A linha é o cenário central; a faixa clara vai do mínimo ao máximo provável (51 cenários)."
            if fora:
                nota += " O rio está longe dos limites de alerta: " + ", ".join(f"{k} a partir de {v:.0f} m³/s" for k, v in fora.items()) + "."
            st.caption(nota)
        else:
            st.warning("Sem previsão de caudal válida para mostrar.")

    st.subheader("O rio nos últimos três anos")
    with ui.guard("o histórico de caudal"):
        st.altair_chart(ui.history_chart(serie("caudal_e_chuva", V), LIMITES, CORES_LIMITES), use_container_width=True)
        ui.legend([{"nome": f"limite {k}: {v:.0f} m³/s", "cor": CORES_LIMITES[k]} for k, v in LIMITES.items() if k in CORES_LIMITES])
        limites("caudal_e_chuva")

    st.subheader("O que está em cada zona de aviso")
    with ui.guard("a exposição"):
        exposicao = serie("exposicao", V).set_index("zona").rename_axis("Zona")
        nomes = {"area_km2": "Área (km²)", "area_agricola_km2": "Terras agrícolas (km²)", "edificios": "Edifícios", "escolas": "Escolas",
                 "unidades_de_saude": "Unidades de saúde", "estradas_km": "Estradas (km)"}
        st.dataframe(exposicao[[c for c in nomes if c in exposicao]].rename(columns=nomes), width="stretch")
        st.caption("Dentro do distrito de Marracuene. Zonas feitas a partir da cheia de janeiro de 2026.")
        with st.expander("Lugares por ordem de alagamento na cheia de janeiro de 2026"):
            lugares = serie("lugares_por_ordem", V)
            st.dataframe(lugares[["lugar", "posto_administrativo", "categoria", "primeira_data", "dias_apos_alerta", "edificios"]].rename(
                columns={"lugar": "Lugar", "posto_administrativo": "Posto administrativo", "categoria": "Situação", "primeira_data": "Primeiro mapa com água",
                         "dias_apos_alerta": "Dias depois do alerta", "edificios": "Edifícios (500 m)"}), hide_index=True, width="stretch")
            limites("lugares")
            st.download_button("Descarregar a tabela (CSV)", lugares.to_csv(index=False).encode("utf-8"), "lugares_por_ordem_de_alagamento.csv", "text/csv")


def pagina_agua() -> None:
    st.header("Água do rio")
    st.markdown("<p class='ete-sub'>A cor da água do Incomáti, da fronteira à foz, comparada com o que é costume em cada época.</p>", unsafe_allow_html=True)
    st.info("O satélite vê o que muda a cor da água: lama e plantas à superfície. Não vê micróbios nem químicos. "
            "Nada nesta página diz se a água é segura: **a água do rio deve ser sempre tratada antes de beber.**")

    with ui.guard("a previsão para as próximas manhãs"):
        diaria = tabela("turbidez_diaria", V)
        if VALIDO and len(diaria):
            st.subheader("Próximas manhãs em Marracuene")
            st.altair_chart(ui.turbidity_heatmap(diaria), use_container_width=True)
            st.caption("Probabilidade (%) de a água estar mais turva do que o habitual por volta das 9h30. Quanto mais escuro, mais provável. "
                       "A cor da água muda com o caudal e com a maré.")

    if "trocos_modulo_q" not in CAMADAS:
        st.warning("O pacote ainda não tem os dados por troço, da fronteira à foz.")
        return
    estado = serie("qualidade_estado", V).set_index("troco")
    st.subheader("O rio todo, da fronteira à foz")
    alertas = estado[estado["alerta_de_qualidade"] == True]  # noqa: E712
    if len(alertas):
        st.warning("A verificar em: " + ", ".join(alertas["nome"]) + ". A água está mais turva do que o normal para a época e do que a chuva e o caudal explicam. "
                   "É um motivo para ir ver, não uma prova de poluição.")
    interativo = st.toggle("Mapa interactivo (gasta mais dados)", value=False, key="mapa_agua")
    with ui.guard("o mapa dos troços"):
        camada = CAMADAS["trocos_modulo_q"]
        if not interativo and camada.get("mapa_leve"):
            st.image(str(leitor.caminho(camada["mapa_leve"])), width=560)
        else:
            mapa, folium = mapa_interativo((-25.45, 32.5), 9)
            folium.GeoJson(geojson("trocos_modulo_q", V), tooltip=folium.GeoJsonTooltip(["nome", "classe", "mes", "fiabilidade"], aliases=["Troço", "Estado", "Mês medido", "Fiabilidade"]),
                           style_function=lambda f: {"color": f["properties"]["cor"], "weight": 5, "fillOpacity": 0.9}).add_to(mapa)
            mostrar_mapa(mapa, 460)
        ui.legend(camada.get("legenda", []))

    with ui.guard("o estado de cada troço"):
        cores = {i["nome"]: i["cor"] for i in CAMADAS["trocos_modulo_q"]["legenda"]}
        ui.chips([(linha["nome"], linha["classe"] + (" (medição menos fiável)" if linha.get("fiabilidade") == "reduzida" else ""), cores.get(linha["classe"], "#bdc3c7"))
                  for _, linha in estado.iterrows()])
        st.caption("Estado do último mês medido, face ao normal desse troço para a época do ano. Q1 é a fronteira; Q9 é a foz.")
        limites("trocos_modulo_q")

    st.subheader("Um troço ao longo dos anos")
    mensal = serie("qualidade_mensal", V)
    nomes = dict(zip(estado["nome"], estado.index))
    escolhido = nomes[st.selectbox("Troço", list(nomes), index=max(len(nomes) - 2, 0))]
    parametros = {"Cor da água (índice): mais alto = mais turva": ("ndti", "Índice de cor"),
                  "Plantas sobre a água (parte do canal)": ("vegetacao", "Parte do canal com plantas"),
                  "Turbidez estimada (FNU, sem calibração local)": ("turbidez_fnu", "Turbidez estimada (FNU)"),
                  "Sólidos suspensos estimados (mg/L, sem calibração local)": ("tss_mg_l", "Sólidos estimados (mg/L)"),
                  "Transparência estimada (m, sem calibração local)": ("secchi_m", "Transparência estimada (m)"),
                  "Temperatura da água (°C, só troços largos)": ("temp_c", "Temperatura (°C)")}
    coluna, titulo = parametros[st.selectbox("O que ver", list(parametros))]
    periodos = {"Últimos 10 anos": 10, "Últimos 5 anos": 5, "Desde 2006": 99}
    anos = periodos[st.radio("Período", list(periodos), horizontal=True, key="periodo_agua")]
    do_troco = mensal[mensal["troco"] == escolhido].assign(mes=lambda d: d["month"].str[5:].astype(int))
    do_troco = do_troco[do_troco["month"] >= str(pd.Timestamp(do_troco["month"].max()).year - anos + 1)]
    with ui.guard("a série do troço"):
        if do_troco[coluna].notna().any():
            normais = None
            if coluna == "ndti" and "qualidade_normais" in CAMADAS:
                todos = serie("qualidade_normais", V)
                normais = todos[todos["troco"] == escolhido].set_index("mes")[["p25", "mediana", "p75"]]
            st.altair_chart(ui.quality_chart(do_troco, normais, coluna, titulo), use_container_width=True)
            if coluna == "ndti":
                st.caption("Cada ponto é um mês. A faixa cinzenta é o intervalo habitual para esse mês do ano; a linha tracejada é o normal. "
                           "A montante de Manhiça o rio é estreito e só há medições desde 2017.")
            elif coluna in ("turbidez_fnu", "tss_mg_l", "secchi_m"):
                st.caption("Estimativa sem medições no rio: serve como ordem de grandeza, não como medição.")
            if coluna == "ndti" and normais is not None and len(normais):
                with st.expander("O normal de cada mês do ano neste troço"):
                    st.altair_chart(ui.climatology_chart(normais), use_container_width=True)
        else:
            st.write("Sem medições deste parâmetro neste troço.")
    with ui.guard("as tendências"):
        if "qualidade_tendencias" in CAMADAS:
            tendencias = serie("qualidade_tendencias", V)
            tendencias = tendencias[(tendencias["troco"] == escolhido) & (tendencias["periodo"] == "registo completo")]
            if len(tendencias):
                with st.expander("Está a mudar ao longo dos anos?"):
                    st.dataframe(tendencias[["parametro", "tendencia", "leitura", "primeiro_mes", "ultimo_mes"]].rename(
                        columns={"parametro": "Parâmetro", "tendencia": "Tendência", "leitura": "Como ler", "primeiro_mes": "De", "ultimo_mes": "Até"}), hide_index=True, width="stretch")
                    limites("qualidade_tendencias")

    st.subheader("Comparar troços")
    with ui.guard("a comparação entre troços"):
        largo = mensal.pivot(index="month", columns="nome", values="ndti")
        largo.index = pd.to_datetime(largo.index)
        defeito = [c for c in largo.columns if c.startswith(("Q1 ", "Q8 "))]
        escolha = st.multiselect("Até três troços", list(largo.columns), default=defeito, max_selections=3)
        if escolha:
            st.altair_chart(ui.compare_chart(largo.loc["2017":, [c for c in largo.columns if c in escolha]].dropna(how="all")), use_container_width=True)
            st.caption("Desde 2017, quando há medições em todos os troços.")
    st.download_button("Descarregar a série mensal de todos os troços (CSV)", mensal.to_csv(index=False).encode("utf-8"), "qualidade_por_troco.csv", "text/csv")


def pagina_sobre() -> None:
    st.header("Sobre os dados")
    st.info(CATALOGO["aviso"])
    st.markdown("""
**O que a plataforma faz.** Todos os dias de manhã lê a previsão de caudal do rio Incomáti e a chuva na bacia, compara-as com 25 anos de
história e dá um nível de alerta para os próximos dez dias. Também acompanha a cor da água do rio por satélite.

**De onde vem a informação.** Previsão de caudal: GloFAS (Copernicus), 51 cenários. Chuva: ECMWF e ERA5. Zonas de aviso: mapas da cheia de janeiro
de 2026 (Copernicus EMS). Cor da água: satélites Sentinel-2 e Landsat. Edifícios, estradas e lugares: Google Open Buildings, OpenStreetMap e GeoNames.

**O que ainda não está provado.** O sistema de cheias foi testado com uma única cheia (janeiro de 2026), em que teria avisado 4 a 5 dias antes.
O acerto das previsões no dia-a-dia está a ser medido desde outubro de 2026. Os nomes dos lugares ainda não foram todos confirmados no terreno.
A qualidade da água é um indicador de cor, sem medições no rio.
""")
    if VALIDO:
        with st.expander("Boletim de hoje, completo"):
            st.markdown(BOLETIM["texto"])
    st.subheader("Camadas e até onde confiar em cada uma")
    st.dataframe(pd.DataFrame([{"Camada": c["titulo"], "Actualização": c.get("atualizacao", ""), "Até onde confiar": c.get("limites", "")} for c in CATALOGO["camadas"]]),
                 hide_index=True, width="stretch")


# ----------------------------------------------------------------------------- shell
st.title("Eyes to Earth: rio Incomáti, Marracuene")
emitido = pd.Timestamp(BOLETIM["estado"]["emitido_utc"]).tz_convert("Africa/Maputo")
st.markdown(f"<p class='ete-sub'>Cheias e água do rio. Boletim de {emitido:%d/%m/%Y, %H:%M} (hora de Maputo).</p>", unsafe_allow_html=True)

inicial = st.query_params.get("p", "hoje")
rotulo = st.radio("Página", list(PAGINAS.values()), index=list(PAGINAS).index(inicial) if inicial in PAGINAS else 0, horizontal=True, key="pagina", label_visibility="collapsed")
pagina = next(k for k, v in PAGINAS.items() if v == rotulo)
st.query_params["p"] = pagina                      # so a page can be shared by its address

{"hoje": pagina_hoje, "cheias": pagina_cheias, "agua": pagina_agua, "sobre": pagina_sobre}[pagina]()

leve = CATALOGO.get("pagina_simples", "")
ui.footer(CATALOGO["aviso"] + (f" &nbsp;|&nbsp; <a href='{leve}'>Versão leve do boletim, para pouca rede</a>" if leve else "")
          + " &nbsp;|&nbsp; Projecto Eyes to Earth, com o apoio do IAU Office of Astronomy for Development.")
