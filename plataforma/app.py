"""Plataforma ETE: cheias e água do rio Incomáti, Marracuene.

    pip install -r plataforma/requirements.txt
    cd plataforma && streamlit run app.py

Estrutura
  app.py       páginas e navegação (este ficheiro)
  tema.py      sistema de desenho: paleta, estilo, cartões, botões de anterior e seguinte
  graficos.py  gráficos
  leitor.py    leitura do pacote de dados `dados/`

Princípios
  * Só lê o pacote `dados/`: não precisa dos dados do projecto, do Earth Engine nem dos modelos.
  * Segura por defeito: sem um boletim válido das últimas 36 horas, mostra "previsão
    indisponível" e nunca um nível de alerta.
  * Leve por defeito: os mapas aparecem como imagens pequenas; o mapa interactivo só é
    carregado quando a pessoa o pede.
  * Cada secção está protegida: se uma falhar, o resto da página aparece na mesma.
"""

import json

import pandas as pd
import streamlit as st

import graficos as G
import leitor
import tema as T

st.set_page_config(page_title="ETE · Incomáti, Marracuene", page_icon="🌊", layout="wide", initial_sidebar_state="collapsed")
T.html(T.CSS)

PAGINAS = {"inicio": "🏠 Início", "cheias": "🌧️ Cheias", "mapa": "🗺️ Mapa", "agua": "💧 Água do rio",
           "historico": "📅 Histórico", "lugares": "📍 Lugares", "sobre": "ℹ️ Como funciona"}
CORES_LUGARES = {"alaga primeiro": "#7b241c", "alaga em cheia grande": "#af601a", "na margem da cheia": "#566573", "fora das zonas de aviso": "#aab7b8"}


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
    st.error("A plataforma está temporariamente sem dados. Consulte os avisos oficiais do INGD, do INAM e da ARA-Sul.")
    st.stop()
VALIDO = bool(BOLETIM["seguro_mostrar"])
LIMITES = BOLETIM["estado"].get("limites_caudal", {})
CORES_LIMITES = {k: CORES[k] for k in LIMITES if k in CORES}
CONSELHOS = CATALOGO.get("conselhos", {})
HOJE = pd.Timestamp(BOLETIM["estado"].get("data_da_previsao", pd.Timestamp.now().date()))


def limites(identificador: str) -> None:
    texto = CAMADAS.get(identificador, {}).get("limites")
    if texto:
        st.caption("**Até onde confiar:** " + texto)


def ir_para(pagina: str) -> None:
    st.session_state["pagina"] = PAGINAS[pagina]


def num(valor, casas: int = 0) -> str:
    return "-" if valor is None or pd.isna(valor) else f"{valor:,.{casas}f}".replace(",", " ").replace(".", ",")


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
def pagina_inicio() -> None:
    if not VALIDO:
        T.hero_unavailable()
        st.button("Ver os mapas e o histórico", on_click=ir_para, args=("mapa",))
        return
    nivel = BOLETIM["nivel_maximo_provavel"]
    T.hero(nivel, BOLETIM["titulo"], CORES[nivel])
    dias = BOLETIM["previsao_diaria"]
    hoje, previsao = dias[0], tabela("previsao_alertas", V)
    maximo = max(dias, key=lambda d: d["caudal_mediana_m3s"])
    falta = LIMITES.get("amarelo", 0) - maximo["caudal_mediana_m3s"]
    T.kpis([
        {"rotulo": "Caudal do rio hoje", "valor": num(hoje["caudal_mediana_m3s"]), "unidade": "m³/s", "nota": "Incomáti em Marracuene"},
        {"rotulo": "Caudal mais alto em 10 dias", "valor": num(maximo["caudal_mediana_m3s"]), "unidade": "m³/s", "nota": "previsto para " + pd.Timestamp(maximo["data"]).strftime("%d/%m")},
        {"rotulo": "Distância ao limite amarelo", "valor": num(falta) if falta > 0 else "acima", "unidade": "m³/s" if falta > 0 else "", "nota": f"limite: {num(LIMITES.get('amarelo'))} m³/s"},
        {"rotulo": "Chuva na bacia, 7 dias", "valor": num(hoje["chuva_7d_mm"]), "unidade": "mm", "nota": "média em toda a bacia"},
        {"rotulo": "Boletim válido até", "valor": pd.Timestamp(BOLETIM["valido_ate"]).strftime("%d/%m"), "nota": "actualizado todas as manhãs"},
    ])

    T.card("O que fazer", f"<p style='margin:0;font-size:1.05rem'>{BOLETIM['conselho']}</p>", "Hoje")
    esquerda, direita = st.columns([3, 2], gap="medium")
    with esquerda:
        T.section("Os próximos dez dias", "Use os botões para andar de dia em dia.", "Previsão")
        escolhido = T.stepper("dia", list(range(len(dias))), lambda i: pd.Timestamp(dias[i]["data"]).strftime("%d/%m/%Y"), "dia escolhido")
        T.day_tiles(dias, CORES, escolhido)
        d = dias[escolhido]
        linha = previsao.iloc[escolhido] if escolhido < len(previsao) else None
        probabilidades = "" if linha is None else (f"<br>Probabilidade de passar o limite amarelo: <b>{100 * linha['prob_amarelo']:.0f} %</b> · laranja: <b>{100 * linha['prob_laranja']:.0f} %</b> · "
                                                   f"vermelho: <b>{100 * linha['prob_vermelho']:.0f} %</b>")
        T.card(f"{pd.Timestamp(d['data']).strftime('%d/%m')}: alerta {d['alerta']}",
               f"<span class='ete-ponto' style='background:{CORES[d['alerta']]}'></span>Caudal previsto: <b>{num(d['caudal_mediana_m3s'])} m³/s</b> "
               f"(entre {num(d['caudal_p10_m3s'])} e {num(d['caudal_p90_m3s'])}).{probabilidades}"
               + (f"<br>Alguns cenários chegam a <b>{d['alerta_possivel']}</b>." if d["alerta_possivel"] != d["alerta"] else ""))
        with T.guard("o gráfico da previsão"):
            grafico, fora = G.forecast(cenarios_do_boletim(), LIMITES, CORES_LIMITES, d["data"], 230)
            st.altair_chart(grafico, use_container_width=True)
            if fora:
                st.caption("O rio está longe dos limites de alerta: " + ", ".join(f"{k} a partir de {num(v)} m³/s" for k, v in fora.items()) + ".")
    with direita:
        T.section("Onde e como está a água", eyebrow="Em Marracuene")
        primeiro, grande = BOLETIM.get("lugares_que_alagam_primeiro") or [], BOLETIM.get("lugares_em_cheia_grande") or []
        if primeiro or grande:
            T.card("Lugares a avisar", ("<p><b>Alagam primeiro:</b> " + ", ".join(primeiro) + ".</p>" if primeiro else "")
                   + ("<p><b>Em cheia grande:</b> " + ", ".join(grande) + ".</p>" if grande else ""), "Onde")
        with T.guard("o estado da água do rio"):
            turbidez = tabela("turbidez", V)
            if len(turbidez):
                cores = {c["nome"]: c["cor"] for c in CAMADAS["trocos_do_rio"]["legenda"]}
                corpo = "".join(f"<span class='ete-chip'><span class='ete-ponto' style='background:{cores.get(l['estado'], '#bdc3c7')}'></span><b>{t}</b>: {l['estado']}</span>" for t, l in turbidez.iterrows())
                T.card("Água do rio em Marracuene", corpo + f"<p style='color:{T.MUTED};font-size:.82rem;margin:8px 0 0 0'>Cor da água vista por satélite nos últimos 20 dias. "
                       "Trate sempre a água do rio antes de beber.</p>", "Qualidade")
        a, b = st.columns(2)
        a.button("Abrir o mapa", on_click=ir_para, args=("mapa",), use_container_width=True, key="ir_mapa")
        b.button("Ver a água do rio", on_click=ir_para, args=("agua",), use_container_width=True, key="ir_agua")

    with T.guard("a mensagem para os líderes"):
        mensagem = leitor.caminho(CAMADAS["boletim"].get("mensagem", ""))
        if mensagem.is_file():
            with st.expander("📨 Mensagem pronta para enviar aos líderes comunitários (WhatsApp ou SMS)"):
                st.code(mensagem.read_text(), language=None)
                st.download_button("Descarregar a mensagem", mensagem.read_text().encode("utf-8"), "mensagem_ete.txt", "text/plain")


# ----------------------------------------------------------------------------- 2. flood forecast
def pagina_cheias() -> None:
    T.section("Previsão de cheias", "Como o rio deve evoluir, quanta chuva caiu e o que quer dizer cada nível de alerta.", "Quantidade")
    proximos, chuva, niveis, anos = st.tabs(["Próximos 10 dias", "Chuva na bacia", "Níveis de alerta", "Últimos 3 anos"])
    with proximos:
        if not VALIDO:
            st.warning("Sem previsão válida para mostrar. Consulte os avisos oficiais.")
        else:
            with T.guard("a previsão de caudal"):
                grafico, fora = G.forecast(cenarios_do_boletim(), LIMITES, CORES_LIMITES)
                st.altair_chart(grafico, use_container_width=True)
                nota = "A linha é o cenário central; a faixa clara vai do mínimo ao máximo provável, entre 51 cenários do modelo europeu GloFAS."
                st.caption(nota + (" O rio está longe dos limites: " + ", ".join(f"{k} a partir de {num(v)} m³/s" for k, v in fora.items()) + "." if fora else ""))
            with T.guard("a tabela da previsão"):
                previsao = tabela("previsao_alertas", V).iloc[:len(BOLETIM["previsao_diaria"])]
                mostra = pd.DataFrame({"Dia": pd.to_datetime(previsao.index).strftime("%d/%m"), "Alerta": previsao["alerta"].to_numpy(), "Alerta possível": previsao["alerta_possivel"].to_numpy(),
                                       "Caudal central (m³/s)": previsao["caudal_mediana"].round(0).to_numpy(), "Mínimo provável": previsao["caudal_p10"].round(0).to_numpy(),
                                       "Máximo provável": previsao["caudal_p90"].round(0).to_numpy(), "Passa o amarelo (%)": (100 * previsao["prob_amarelo"]).round(0).to_numpy(),
                                       "Passa o laranja (%)": (100 * previsao["prob_laranja"]).round(0).to_numpy(), "Passa o vermelho (%)": (100 * previsao["prob_vermelho"]).round(0).to_numpy(),
                                       "Chuva 7 dias (mm)": previsao["chuva_7d_mm"].round(0).to_numpy(), "Segunda opinião (m³/s)": previsao["caudal_modelo_c"].round(0).to_numpy()})
                st.dataframe(mostra, hide_index=True, width="stretch")
                st.caption("\"Alerta\" é o que metade ou mais dos cenários indica; \"alerta possível\" é o que pelo menos um em cada cinco indica. "
                           "A \"segunda opinião\" é um modelo próprio do projecto, que usa só a chuva já caída.")
                st.download_button("Descarregar a previsão (CSV)", tabela("previsao_alertas", V).to_csv().encode("utf-8"), "previsao_ete.csv", "text/csv")
    with chuva:
        with T.guard("a chuva na bacia"):
            st.altair_chart(G.rain(tabela("chuva_bacia", V), HOJE), use_container_width=True)
            st.caption("Chuva média em toda a bacia do Incomáti, que inclui partes da África do Sul e de Essuatíni. É esta chuva que faz o rio subir em Marracuene, "
                       "dias depois. A chuva prevista só entra no alerta até 7 dias à frente.")
    with niveis:
        T.level_cards(LIMITES, CORES, CONSELHOS)
        st.caption("Os limites de caudal foram calculados com 25 anos de dados (1997 a 2021) e testados nos anos seguintes. Na cheia de janeiro de 2026, "
                   "estas regras teriam dado alerta laranja 4 a 5 dias antes do primeiro mapa de cheia.")
    with anos:
        with T.guard("o histórico de caudal"):
            st.altair_chart(G.history(serie("caudal_e_chuva", V), LIMITES, CORES_LIMITES), use_container_width=True)
            T.legend([{"nome": f"limite {k}: {num(v)} m³/s", "cor": CORES_LIMITES[k]} for k, v in LIMITES.items() if k in CORES_LIMITES])
            limites("caudal_e_chuva")


# ----------------------------------------------------------------------------- 3. map
def pagina_mapa() -> None:
    T.section("Mapa", "Onde a água chega primeiro, o terreno que favorece cheias e o que o radar viu em cada mês.", "Quantidade")
    opcoes = {"Zonas de aviso": "zonas_de_aviso", "Terreno que favorece cheias": "suscetibilidade", "Água vista por radar, mês a mês": "agua_mensal"}
    controlo, vista = st.columns([1, 2.4], gap="medium")
    with controlo:
        escolha = opcoes[st.radio("Camada", list(opcoes), key="camada_mapa")]
        camada = CAMADAS[escolha]
        interativo = st.toggle("Mapa interactivo (gasta mais dados)", value=False, key="mapa_cheias")
        T.card("", f"<p style='margin:0 0 8px 0'>{camada.get('descricao', '')}</p>" + " ".join(
            f"<span class='ete-chip'><span class='ete-ponto' style='background:{i['cor']}'></span>{i['nome']}</span>" for i in camada.get("legenda", [])), "Legenda")
        nome = "(nenhum)"
        with T.guard("a pesquisa de lugares"):
            lugares = serie("lugares_por_ordem", V)
            nome = st.selectbox("Procurar um lugar", ["(nenhum)"] + sorted(lugares["lugar"].unique()), key="lugar_mapa")
            if nome != "(nenhum)":
                l = lugares[lugares["lugar"] == nome].iloc[0]
                posto = l["posto_administrativo"] if isinstance(l["posto_administrativo"], str) else ""
                T.card(nome, f"<span class='ete-ponto' style='background:{CORES_LUGARES.get(l['categoria'], '#aab7b8')}'></span><b>{l['categoria']}</b><br>"
                       + (f"Primeiro mapa com água: {pd.Timestamp(l['primeira_data']).strftime('%d/%m/%Y')} ({num(l['dias_apos_alerta'])} dias depois do alerta)<br>" if pd.notna(l["primeira_data"]) else "")
                       + f"Edifícios num raio de 500 m: {num(l['edificios'])}<br>Distância ao rio: {num(l['distancia_ao_rio_m'])} m<br>Altura acima do rio: {num(l['altura_acima_do_rio_m'], 1)} m"
                       + f"<br><span style='color:{T.MUTED};font-size:.8rem'>{posto} · nome de {l['fonte_do_nome']}, por validar</span>", "Lugar")
    with vista:
        with T.guard("o mapa"):
            mes = None
            if escolha == "agua_mensal":
                mes = T.stepper("mes_radar", camada["meses"], lambda m: f"{T.MESES_LONGOS[int(m[5:]) - 1].capitalize()} de {m[:4]}", "mês mostrado")
            if not interativo and camada.get("mapa_leve"):
                st.image(str(leitor.caminho(camada["mapa_leve"])), width=680)
            elif not interativo and escolha == "agua_mensal":
                ficheiro, _ = leitor.imagem("agua_mensal", mes)
                st.image(str(ficheiro), width=680)
                st.caption("Imagem do mês (azul: água habitual; vermelho: água fora do habitual). Ligue o mapa interactivo para a ver sobre o mapa de base.")
            else:
                if not interativo:
                    st.caption("Esta camada só existe em mapa interactivo.")
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
                                            tooltip=f"{p['lugar']}: {p['categoria']}").add_to(mapa)
                mostrar_mapa(mapa)
            limites(escolha)


# ----------------------------------------------------------------------------- 4. river water
def pagina_agua() -> None:
    T.section("Água do rio", "A cor da água do Incomáti, da fronteira à foz, comparada com o que é costume em cada época.", "Qualidade")
    st.info("O satélite vê o que muda a cor da água: lama e plantas à superfície. Não vê micróbios nem químicos. "
            "Nada nesta página diz se a água é segura: **a água do rio deve ser sempre tratada antes de beber.**", icon="💧")
    if "trocos_modulo_q" not in CAMADAS:
        st.warning("O pacote ainda não tem os dados por troço, da fronteira à foz.")
        return
    estado = serie("qualidade_estado", V).set_index("troco")
    mensal = serie("qualidade_mensal", V)
    cores = {i["nome"]: i["cor"] for i in CAMADAS["trocos_modulo_q"]["legenda"]}
    manhas, rio, troco_tab, comparar, satelite = st.tabs(["Próximas manhãs", "O rio todo", "Explorar um troço", "Comparar troços", "O que o satélite vê"])

    with manhas:
        with T.guard("a previsão para as próximas manhãs"):
            diaria = tabela("turbidez_diaria", V)
            if VALIDO and len(diaria):
                st.altair_chart(G.turbidity_heatmap(diaria), use_container_width=True)
                st.caption("Probabilidade (%) de a água estar mais turva do que o habitual por volta das 9h30, em três troços de Marracuene. Quanto mais escuro, mais provável. "
                           "A cor da água muda com o caudal e com a maré, por isso varia de dia para dia mesmo sem chuva.")
                turbidez = tabela("turbidez", V)
                st.dataframe(turbidez[["estado", "medicoes_em_20_dias", "ultima_medicao", "previsao", "fiabilidade"]].rename(
                    columns={"estado": "Últimos 20 dias", "medicoes_em_20_dias": "Imagens usadas", "ultima_medicao": "Última medição", "previsao": "Mais turva nos próximos dias?",
                             "fiabilidade": "Fiabilidade"}).rename_axis("Troço"), width="stretch")
                T.card("", f"<p style='margin:0'>{CONSELHOS.get('agua_turva', '')}</p>", "Com água turva")
            else:
                st.warning("Sem previsão válida para mostrar.")

    with rio:
        st.markdown("**Da fronteira (Q1, à esquerda) à foz (Q9, à direita).** A cor no topo de cada cartão é o estado do último mês medido.")
        T.river_tiles(estado, cores)
        T.legend(CAMADAS["trocos_modulo_q"]["legenda"])
        alertas = estado[estado["alerta_de_qualidade"] == True]  # noqa: E712
        if len(alertas):
            st.warning("A verificar em: " + ", ".join(alertas["nome"]) + ". A água está mais turva do que o normal para a época e do que a chuva e o caudal explicam. "
                       "É um motivo para ir ver, não uma prova de poluição.")
        interativo = st.toggle("Mapa interactivo (gasta mais dados)", value=False, key="mapa_agua")
        with T.guard("o mapa dos troços"):
            camada = CAMADAS["trocos_modulo_q"]
            if not interativo and camada.get("mapa_leve"):
                st.image(str(leitor.caminho(camada["mapa_leve"])), width=640)
            else:
                mapa, folium = mapa_interativo((-25.45, 32.5), 9)
                folium.GeoJson(geojson("trocos_modulo_q", V), tooltip=folium.GeoJsonTooltip(["nome", "classe", "mes", "fiabilidade"], aliases=["Troço", "Estado", "Mês medido", "Fiabilidade"]),
                               style_function=lambda f: {"color": f["properties"]["cor"], "weight": 5, "fillOpacity": 0.9}).add_to(mapa)
                mostrar_mapa(mapa, 480)
        with T.guard("a tabela dos troços"):
            colunas = {"nome": "Troço", "mes": "Mês medido", "classe": "Estado face ao normal", "fiabilidade": "Fiabilidade", "fonte": "Satélite",
                       "turbidez_fnu_estimada": "Turbidez estimada (FNU)", "vegetacao": "Plantas sobre a água (parte)", "alerta_de_qualidade": "A verificar"}
            st.dataframe(estado[[c for c in colunas if c in estado]].rename(columns=colunas), hide_index=True, width="stretch")
            limites("trocos_modulo_q")

    with troco_tab:
        codigos = list(estado.index)
        if "troco_i" not in st.session_state:
            st.session_state["troco_i"] = max(len(codigos) - 2, 0)
        escolhido = T.stepper("troco", codigos, lambda c: estado.loc[c, "nome"], "anterior = para montante · seguinte = para a foz")
        T.river_tiles(estado, cores, escolhido)
        linha = estado.loc[escolhido]
        T.kpis([{"rotulo": "Estado", "valor": linha["classe"], "nota": f"mês medido: {linha['mes'] if isinstance(linha['mes'], str) else '-'}"},
                {"rotulo": "Medido por", "valor": linha.get("fonte") if isinstance(linha.get("fonte"), str) else "-", "nota": f"fiabilidade {linha.get('fiabilidade', '-')}"},
                {"rotulo": "Turbidez estimada", "valor": num(linha.get("turbidez_fnu_estimada")), "unidade": "FNU", "nota": "sem calibração local"},
                {"rotulo": "Plantas sobre a água", "valor": num(100 * linha["vegetacao"]) if pd.notna(linha.get("vegetacao")) else "-", "unidade": "%", "nota": "parte do canal"}])
        parametros = {"Cor da água (índice): mais alto = mais turva": ("ndti", "Índice de cor"), "Plantas sobre a água (parte do canal)": ("vegetacao", "Parte do canal com plantas"),
                      "Turbidez estimada (FNU, sem calibração local)": ("turbidez_fnu", "Turbidez estimada (FNU)"),
                      "Sólidos suspensos estimados (mg/L, sem calibração local)": ("tss_mg_l", "Sólidos estimados (mg/L)"),
                      "Transparência estimada (m, sem calibração local)": ("secchi_m", "Transparência estimada (m)"), "Temperatura da água (°C, só troços largos)": ("temp_c", "Temperatura (°C)")}
        a, b = st.columns([2, 1])
        coluna, titulo = parametros[a.selectbox("O que ver", list(parametros), key="parametro_agua")]
        periodos = {"Últimos 10 anos": 10, "Últimos 5 anos": 5, "Desde 2006": 99}
        anos = periodos[b.radio("Período", list(periodos), horizontal=True, key="periodo_agua")]
        do_troco = mensal[mensal["troco"] == escolhido].assign(mes=lambda d: d["month"].str[5:].astype(int))
        do_troco = do_troco[do_troco["month"] >= str(pd.Timestamp(do_troco["month"].max()).year - anos + 1)]
        with T.guard("a série do troço"):
            if do_troco[coluna].notna().any():
                normais = None
                if coluna == "ndti" and "qualidade_normais" in CAMADAS:
                    todos = serie("qualidade_normais", V)
                    normais = todos[todos["troco"] == escolhido].set_index("mes")[["p25", "mediana", "p75"]]
                st.altair_chart(G.quality(do_troco, normais, coluna, titulo), use_container_width=True)
                if coluna == "ndti":
                    st.caption("Cada ponto é um mês. A faixa cinzenta é o intervalo habitual para esse mês do ano; a linha tracejada é o normal. "
                               "A montante de Manhiça o rio é estreito e só há medições desde 2017.")
                    if normais is not None and len(normais):
                        with st.expander("O normal de cada mês do ano neste troço"):
                            st.altair_chart(G.climatology(normais), use_container_width=True)
                elif coluna in ("turbidez_fnu", "tss_mg_l", "secchi_m"):
                    st.caption("Estimativa sem medições no rio: serve como ordem de grandeza, não como medição.")
            else:
                st.info("Sem medições deste parâmetro neste troço.")
        with T.guard("as tendências"):
            if "qualidade_tendencias" in CAMADAS:
                tendencias = serie("qualidade_tendencias", V)
                tendencias = tendencias[(tendencias["troco"] == escolhido) & (tendencias["periodo"] == "registo completo")]
                if len(tendencias):
                    with st.expander("Está a mudar ao longo dos anos?"):
                        st.dataframe(tendencias[["parametro", "tendencia", "leitura", "primeiro_mes", "ultimo_mes"]].rename(
                            columns={"parametro": "Parâmetro", "tendencia": "Tendência", "leitura": "Como ler", "primeiro_mes": "De", "ultimo_mes": "Até"}), hide_index=True, width="stretch")
                        limites("qualidade_tendencias")

    with comparar:
        with T.guard("a comparação entre troços"):
            largo = mensal.pivot(index="month", columns="nome", values="ndti")
            largo.index = pd.to_datetime(largo.index)
            defeito = [c for c in largo.columns if c.startswith(("Q1 ", "Q8 "))]
            escolha = st.multiselect("Até três troços", list(largo.columns), default=defeito, max_selections=3, key="comparar_agua")
            if escolha:
                st.altair_chart(G.compare(largo.loc["2017":, [c for c in largo.columns if c in escolha]].dropna(how="all")), use_container_width=True)
                st.caption("Desde 2017, quando há medições em todos os troços. A cor da água em Marracuene não acompanha, mês a mês, a da fronteira: "
                           "entre os dois pontos há 250 km de rio, afluentes, regadios e, no fim, a maré.")
        st.download_button("Descarregar a série mensal de todos os troços (CSV)", mensal.to_csv(index=False).encode("utf-8"), "qualidade_por_troco.csv", "text/csv")

    with satelite:
        st.dataframe(pd.DataFrame([
            {"O que": "Lama e sedimentos (turbidez)", "O satélite vê?": "Sim", "Como é mostrado": "\"Normal\", \"elevada\" ou \"muito elevada\" face ao costume do troço"},
            {"O que": "Plantas sobre a água", "O satélite vê?": "Sim", "Como é mostrado": "Parte do canal coberta (mais fiável nos troços largos)"},
            {"O que": "Temperatura da água", "O satélite vê?": "Só nos troços largos", "Como é mostrado": "Graus, de Manhiça à foz"},
            {"O que": "Turbidez em números (FNU), sólidos (mg/L), transparência (m)", "O satélite vê?": "Só por estimativa", "Como é mostrado": "Ordem de grandeza, sem medições no rio"},
            {"O que": "Algas (clorofila)", "O satélite vê?": "Não neste rio", "Como é mostrado": "Não é mostrado: o sinal confunde-se com a lama"},
            {"O que": "Micróbios, pH, oxigénio, nutrientes, metais, pesticidas", "O satélite vê?": "Não", "Como é mostrado": "Só com análises de laboratório"}]),
            hide_index=True, width="stretch")
        st.caption("Não há nenhuma estação pública de qualidade da água na bacia do Incomáti (arquivo mundial GEMStat), e o projecto não fez medições no rio. "
                   "Por isso tudo o que aqui se mostra é relativo: a água de hoje comparada com a água de costume.")


# ----------------------------------------------------------------------------- 5. history
def pagina_historico() -> None:
    T.section("Histórico", "Vinte anos do rio: quando passou os limites, e como foi cada ano.", "2006 a 2026")
    dados = historico(V)
    por_ano = dados.groupby("ano")["alerta"].value_counts().unstack(fill_value=0).reindex(columns=G.LEVELS, fill_value=0)
    completos = por_ano[por_ano.sum(axis=1) >= 300]
    with T.guard("os números do histórico"):
        maior = dados.loc[dados["caudal_m3s"].idxmax()]
        T.kpis([{"rotulo": "Anos com alerta laranja ou vermelho", "valor": f"{int(((completos['laranja'] + completos['vermelho']) > 0).sum())} em {len(completos)}", "nota": "anos de outubro a setembro"},
                {"rotulo": "Anos com alerta vermelho", "valor": f"{int((completos['vermelho'] > 0).sum())} em {len(completos)}"},
                {"rotulo": "Dias em laranja ou vermelho", "valor": num(completos["laranja"].sum() + completos["vermelho"].sum()), "nota": "em todo o período"},
                {"rotulo": "Maior caudal", "valor": num(maior["caudal_m3s"]), "unidade": "m³/s", "nota": maior["data"].strftime("%d/%m/%Y")}])
    resumo, calendario, ano_tab, radar = st.tabs(["Dias de alerta por ano", "Calendário", "Um ano em detalhe", "Água vista por radar"])
    with resumo:
        with T.guard("os dias de alerta por ano"):
            st.altair_chart(G.alert_days(completos[["amarelo", "laranja", "vermelho"]], CORES), use_container_width=True)
            st.caption("Dias em que as regras de alerta teriam dado cada nível. São dias em que o sistema teria avisado, não cheias confirmadas uma a uma no terreno. "
                       "O caudal vem de um modelo mundial (GloFAS), não de uma estação no rio.")
    with calendario:
        with T.guard("o calendário de alertas"):
            mensal = dados.assign(ano_civil=dados["data"].dt.year, mes=dados["data"].dt.month, nivel=dados["alerta"].map({k: i for i, k in enumerate(G.LEVELS)}))
            mensal = mensal.groupby(["ano_civil", "mes"]).agg(nivel=("nivel", "max"), caudal=("caudal_m3s", "max")).reset_index().dropna(subset=["nivel"])
            mensal["alerta"], mensal["mes_nome"], mensal["ano"] = mensal["nivel"].astype(int).map(dict(enumerate(G.LEVELS))), mensal["mes"].map(lambda m: G.MESES[m - 1]), mensal["ano_civil"]
            st.altair_chart(G.level_calendar(mensal, CORES), use_container_width=True)
            st.caption("O alerta mais alto de cada mês, ano a ano.")
    with ano_tab:
        anos = [int(a) for a in por_ano.index if por_ano.loc[a].sum() >= 200]
        ano = T.stepper("ano_hist", anos, lambda a: f"Ano hidrológico {a - 1}/{a}", "de outubro a setembro")
        do_ano = dados[dados["ano"] == ano]
        with T.guard("o ano em detalhe"):
            pico = do_ano.loc[do_ano["caudal_m3s"].idxmax()]
            T.kpis([{"rotulo": "Caudal máximo", "valor": num(pico["caudal_m3s"]), "unidade": "m³/s", "nota": pico["data"].strftime("%d/%m/%Y")},
                    {"rotulo": "Dias em amarelo", "valor": int((do_ano["alerta"] == "amarelo").sum())}, {"rotulo": "Dias em laranja", "valor": int((do_ano["alerta"] == "laranja").sum())},
                    {"rotulo": "Dias em vermelho", "valor": int((do_ano["alerta"] == "vermelho").sum())}])
            st.altair_chart(G.year_detail(do_ano, LIMITES, CORES), use_container_width=True)
            st.caption("A linha é o caudal de cada dia; a fita por baixo é o alerta desse dia; as linhas tracejadas são os limites amarelo, laranja e vermelho.")
    with radar:
        with T.guard("a água vista por radar"):
            st.altair_chart(G.flood_area(serie("area_de_agua", V)), use_container_width=True)
            st.caption("Área com água fora do sítio habitual dentro do distrito, em cada mês, vista pelo radar Sentinel-1 (desde 2015). "
                       "Os primeiros meses de 2015 têm poucas passagens do satélite e devem ser lidos com cuidado; em zonas construídas o modelo marca água a mais.")
            limites("agua_mensal")


# ----------------------------------------------------------------------------- 6. places
def pagina_lugares() -> None:
    T.section("Lugares", "Que lugares a água alcança, por que ordem, e o que existe em cada zona de aviso.", "Exposição")
    exposicao = serie("exposicao", V).set_index("zona")
    lugares = serie("lugares_por_ordem", V)
    with T.guard("a exposição por zona"):
        for zona, linha in exposicao.iterrows():
            st.markdown(f"**{zona.capitalize()}**")
            T.kpis([{"rotulo": "Área", "valor": num(linha["area_km2"]), "unidade": "km²"}, {"rotulo": "Terras agrícolas", "valor": num(linha["area_agricola_km2"]), "unidade": "km²"},
                    {"rotulo": "Edifícios", "valor": num(linha["edificios"])}, {"rotulo": "Estradas e caminhos", "valor": num(linha["estradas_km"]), "unidade": "km"},
                    {"rotulo": "Escolas", "valor": num(linha["escolas"])}, {"rotulo": "Unidades de saúde", "valor": num(linha["unidades_de_saude"])}])
        st.caption("Dentro do distrito de Marracuene. As zonas são onde a água chegou na cheia de janeiro de 2026 (mapas do Copernicus EMS). "
                   "As escolas e unidades de saúde vêm do OpenStreetMap, que pode estar incompleto.")
    esquerda, direita = st.columns([1, 1.25], gap="medium")
    with esquerda:
        with T.guard("o mapa dos lugares"):
            st.image(str(leitor.caminho(CAMADAS["zonas_de_aviso"]["mapa_leve"])), use_container_width=True)
            T.legend(CAMADAS["zonas_de_aviso"]["legenda"])
            st.button("Abrir o mapa completo", on_click=ir_para, args=("mapa",), key="ir_mapa_lugares")
    with direita:
        with T.guard("os edifícios por lugar"):
            cores = {k: v for k, v in CORES_LUGARES.items() if k in set(lugares["categoria"])}
            st.altair_chart(G.buildings_by_place(lugares, cores), use_container_width=True)
    with T.guard("a tabela dos lugares"):
        a, b = st.columns(2)
        categorias = a.multiselect("Situação", list(CORES_LUGARES), default=["alaga primeiro", "alaga em cheia grande"], key="categoria_lugares")
        postos = sorted(p for p in lugares["posto_administrativo"].dropna().unique() if p)
        posto = b.multiselect("Posto administrativo", postos, key="posto_lugares")
        filtrados = lugares[lugares["categoria"].isin(categorias or list(CORES_LUGARES))]
        if posto:
            filtrados = filtrados[filtrados["posto_administrativo"].isin(posto)]
        st.dataframe(filtrados[["lugar", "posto_administrativo", "categoria", "primeira_data", "dias_apos_alerta", "parte_alagada", "edificios", "edificios_alagados",
                                "distancia_ao_rio_m", "altura_acima_do_rio_m", "fonte_do_nome"]].rename(columns={
                                    "lugar": "Lugar", "posto_administrativo": "Posto administrativo", "categoria": "Situação", "primeira_data": "Primeiro mapa com água",
                                    "dias_apos_alerta": "Dias depois do alerta", "parte_alagada": "Parte alagada", "edificios": "Edifícios (500 m)", "edificios_alagados": "Edifícios na zona",
                                    "distancia_ao_rio_m": "Distância ao rio (m)", "altura_acima_do_rio_m": "Altura acima do rio (m)", "fonte_do_nome": "Fonte do nome"}),
                     hide_index=True, width="stretch")
        st.caption(f"{len(filtrados)} lugares. Cada lugar é um ponto com um círculo de 500 m, não um limite oficial de bairro. Os nomes ainda não foram validados no terreno.")
        st.download_button("Descarregar a lista de lugares (CSV)", lugares.to_csv(index=False).encode("utf-8"), "lugares_por_ordem_de_alagamento.csv", "text/csv")


# ----------------------------------------------------------------------------- 7. how it works
def pagina_sobre() -> None:
    T.section("Como funciona", "De onde vem a informação, até onde se pode confiar nela e como está o sistema hoje.", "Sobre a plataforma")
    st.info(CATALOGO["aviso"], icon="⚠️")
    resumo, fontes, confianca, perguntas, sistema, glossario = st.tabs(["Em poucas palavras", "Fontes de dados", "Até onde confiar", "Perguntas frequentes", "Estado do sistema", "Glossário"])
    with resumo:
        T.steps([("Satélites e modelos", "Todos os dias chegam a previsão de caudal do rio (51 cenários) e a chuva em toda a bacia."),
                 ("Comparação com 25 anos", "O caudal e a chuva previstos são comparados com o que aconteceu desde 1997."),
                 ("Nível de alerta", "Verde, amarelo, laranja ou vermelho para cada um dos próximos dez dias."),
                 ("Onde", "As zonas de aviso mostram onde a água chegou primeiro na cheia de janeiro de 2026, com os nomes dos lugares."),
                 ("Mensagem", "Um boletim e uma mensagem curta, prontos para enviar aos líderes comunitários."),
                 ("Água do rio", "A cor da água é medida por satélite, da fronteira à foz, e comparada com o costume de cada época.")])
        with T.guard("os factos do problema"):
            if "factos" in CAMADAS:
                bruto = serie("factos", V)
                f = bruto.set_index(bruto.columns[0])["valor"]
                st.markdown("##### O problema, em números")
                T.kpis([{"rotulo": "Anos com alerta laranja ou vermelho", "valor": f"{f['anos_com_alerta_laranja_ou_vermelho']:.0f} em {f['anos_analisados']:.0f}"},
                        {"rotulo": "Área alagada em janeiro de 2026", "valor": num(f["area_alagada_cheia_grande_km2"]), "unidade": "km²", "nota": "no distrito"},
                        {"rotulo": "Edifícios na zona alagada", "valor": num(f["edificios"])}, {"rotulo": "Terras agrícolas alagadas", "valor": num(f["terras_agricolas_km2"]), "unidade": "km²"},
                        {"rotulo": "Estações públicas de qualidade da água na bacia", "valor": num(f["estacoes_publicas_de_qualidade_na_bacia"]), "nota": "arquivo mundial GEMStat"},
                        {"rotulo": "Troços do rio acompanhados", "valor": num(f["trocos_analisados"]), "nota": "da fronteira à foz"}])
    with fontes:
        st.dataframe(pd.DataFrame([
            {"Informação": "Previsão de caudal do rio", "Fonte": "GloFAS, Copernicus (via Open-Meteo)", "Actualização": "diária"},
            {"Informação": "Chuva prevista e chuva caída na bacia", "Fonte": "ECMWF IFS e ERA5 (via Open-Meteo)", "Actualização": "diária"},
            {"Informação": "Zonas de aviso", "Fonte": "Copernicus EMS, activação EMSR857 (cheia de janeiro de 2026)", "Actualização": "quando houver nova cheia mapeada"},
            {"Informação": "Água vista por radar", "Fonte": "Sentinel-1 (Copernicus) e Modelo B do projecto", "Actualização": "mensal"},
            {"Informação": "Terreno que favorece cheias", "Fonte": "Landsat, CHIRPS, ERA5-Land, Copernicus DEM, MERIT Hydro e Modelo A do projecto", "Actualização": "quando o modelo é treinado"},
            {"Informação": "Cor da água do rio", "Fonte": "Sentinel-2 (Copernicus) e Landsat 5, 7, 8 e 9 (USGS e NASA)", "Actualização": "semanal em Marracuene; mensal no rio todo"},
            {"Informação": "Maré", "Fonte": "calculada a partir do nível do mar na Baía de Maputo (Open-Meteo)", "Actualização": "fixa"},
            {"Informação": "Edifícios, estradas, escolas e unidades de saúde", "Fonte": "Google Open Buildings e OpenStreetMap", "Actualização": "fixa"},
            {"Informação": "Nomes dos lugares", "Fonte": "OpenStreetMap e GeoNames", "Actualização": "por validar no terreno"},
            {"Informação": "Limite do distrito e da bacia", "Fonte": "FAO GAUL e HydroSHEDS", "Actualização": "fixa"}]), hide_index=True, width="stretch")
        st.caption("Todos os dados são abertos. O projecto não depende de pedidos a instituições.")
    with confianca:
        st.markdown("""
**O que está provado**
- Na cheia de janeiro de 2026, as regras de alerta teriam dado laranja 4 a 5 dias antes do primeiro mapa de cheia.
- O modelo que detecta água por radar acerta 91 % da área alagada nessa cheia (IoU 0,91), comparado com os mapas do Copernicus.
- A cor da água medida por dois satélites diferentes no mesmo dia concorda (correlação 0,85).

**O que ainda não está provado**
- Tudo o que diz respeito a cheias foi testado com **uma única cheia**. Outras cheias podem comportar-se de outra maneira.
- O acerto da previsão no dia-a-dia está a ser medido desde outubro de 2026, guardando todas as previsões.
- Os nomes dos lugares vêm de mapas públicos e não foram confirmados no terreno.
- A qualidade da água é um indicador de cor, sem medições no rio.
""")
        with T.guard("a validação dos modelos"):
            if "validacao_cheias" in CAMADAS:
                with st.expander("Medidas de acerto dos modelos de cheias"):
                    st.dataframe(serie("validacao_cheias", V), hide_index=True, width="stretch")
                    st.caption("IoU, F1 e Kappa vão de 0 a 1 (quanto mais alto, melhor). ROC-AUC: 0,5 é acaso, 1 é perfeito.")
            habilidade = pd.DataFrame(CATALOGO["modelos"].get("turbidez", {}).get("skill") or [])
            if len(habilidade):
                with st.expander("Medidas de acerto da previsão de turbidez"):
                    st.dataframe(habilidade.rename(columns={"modelo": "Modelo", "dias": "Dias", "r2": "R²", "mae": "Erro típico", "auc": "AUC", "bss": "Ganho face à época do ano"}), hide_index=True, width="stretch")
        with st.expander("Até onde confiar em cada camada"):
            st.dataframe(pd.DataFrame([{"Camada": c["titulo"], "Actualização": c.get("atualizacao", ""), "Até onde confiar": c.get("limites", "")} for c in CATALOGO["camadas"] if c.get("limites")]),
                         hide_index=True, width="stretch")
    with perguntas:
        for pergunta, resposta in (
                ("O alerta está verde, mas está a chover muito aqui.", "O alerta é para a cheia do rio, que depende da chuva em toda a bacia, incluindo na África do Sul e em Essuatíni. "
                 "A chuva forte no local pode alagar ruas sem o rio subir."),
                ("O meu bairro não aparece.", "Os nomes vêm de mapas públicos e ainda não foram todos confirmados. Veja no mapa se a sua casa fica dentro de uma zona vermelha ou laranja."),
                ("Com quantos dias de avanço avisa?", "Na cheia de janeiro de 2026, o sistema teria dado alerta laranja 4 a 5 dias antes. Só foi testado com essa cheia."),
                ("Posso confiar no número do caudal?", "Vem de um modelo mundial, não de um aparelho no rio. Serve para saber se o rio vai subir muito, não para saber o valor exacto."),
                ("A água está \"normal\". Posso bebê-la?", "Não sem a tratar. O satélite vê a cor da água; não vê micróbios nem químicos. Ferva a água ou use cloro."),
                ("O que quer dizer \"previsão indisponível\"?", "Que a plataforma não tem um boletim das últimas 36 horas. Não quer dizer que não há perigo: nesse caso, ouça os avisos oficiais."),
                ("Isto substitui os avisos do INGD?", "Não. É um serviço experimental. Se as autoridades derem uma ordem, siga a ordem.")):
            with st.expander(pergunta):
                st.write(resposta)
    with sistema:
        estado = BOLETIM["estado"]
        T.kpis([{"rotulo": "Boletim", "valor": "em dia" if VALIDO else "desactualizado", "nota": f"emitido há {BOLETIM['horas_desde_a_emissao']:.0f} h"},
                {"rotulo": "Cenários recebidos", "valor": estado.get("cenarios", "-"), "nota": "de 51"},
                {"rotulo": "Origem dos dados", "valor": "internet" if estado.get("fonte") == "online" else "cópia guardada"},
                {"rotulo": "Versão do código", "valor": CATALOGO.get("versao_codigo", "-")}])
        with T.guard("o estado do pipeline"):
            ficheiro = leitor.caminho("pipeline.json")
            if ficheiro.is_file():
                passos = json.loads(ficheiro.read_text())
                st.dataframe(pd.DataFrame(passos["passos"]).rename(columns={"passo": "Passo", "estado": "Estado", "detalhe": "Detalhe", "segundos": "Segundos"}), hide_index=True, width="stretch")
                st.caption(f"Última execução do pipeline: {pd.Timestamp(passos['executado_utc']).tz_convert('Africa/Maputo'):%d/%m/%Y, %H:%M} (hora de Maputo).")
        if estado.get("problemas"):
            st.warning("Avisos da última execução: " + "; ".join(estado["problemas"]))
        with st.expander("Boletim de hoje, completo"):
            st.markdown(BOLETIM["texto"])
    with glossario:
        st.dataframe(pd.DataFrame([
            {"Palavra": "Caudal", "Quer dizer": "A quantidade de água que passa no rio em cada segundo (m³/s)."},
            {"Palavra": "Bacia", "Quer dizer": "Toda a área de onde a chuva escorre para o rio. A do Incomáti estende-se pela África do Sul, Essuatíni e Moçambique."},
            {"Palavra": "Cenários", "Quer dizer": "51 previsões ligeiramente diferentes do mesmo modelo. Se quase todas concordam, a previsão é mais certa."},
            {"Palavra": "Zona de aviso", "Quer dizer": "Área onde a água chegou na cheia de janeiro de 2026. Zona 1: chegou primeiro. Zona 2: chegou na cheia grande."},
            {"Palavra": "Turbidez", "Quer dizer": "Quanto a água está barrenta."},
            {"Palavra": "Troço", "Quer dizer": "Uma parte do rio. O Incomáti foi dividido em nove, da fronteira (Q1) à foz (Q9)."},
            {"Palavra": "Radar", "Quer dizer": "Satélite que vê através das nuvens. A água calma aparece muito escura."},
            {"Palavra": "Ano hidrológico", "Quer dizer": "De outubro a setembro, para a época das chuvas ficar inteira no mesmo ano."}]), hide_index=True, width="stretch")


# ----------------------------------------------------------------------------- shell
emitido = pd.Timestamp(BOLETIM["estado"]["emitido_utc"]).tz_convert("Africa/Maputo")
T.top_bar(f"{emitido:%d/%m/%Y, %H:%M}", VALIDO)

if "pagina" not in st.session_state:                 # first visit: honour a shared address such as ?p=agua
    st.session_state["pagina"] = PAGINAS.get(st.query_params.get("p", "inicio"), PAGINAS["inicio"])
rotulo = st.radio("Página", list(PAGINAS.values()), horizontal=True, key="pagina", label_visibility="collapsed")
pagina = next(k for k, v in PAGINAS.items() if v == rotulo)
st.query_params["p"] = pagina

{"inicio": pagina_inicio, "cheias": pagina_cheias, "mapa": pagina_mapa, "agua": pagina_agua, "historico": pagina_historico, "lugares": pagina_lugares, "sobre": pagina_sobre}[pagina]()

leve = CATALOGO.get("pagina_simples", "")
T.footer(CATALOGO["aviso"] + (f" &nbsp;·&nbsp; <a href='{leve}'>Versão leve do boletim, para pouca rede</a>" if leve else "")
         + " &nbsp;·&nbsp; Projecto Eyes to Earth, com o apoio do IAU Office of Astronomy for Development. Dados abertos: Copernicus, NASA, USGS, ESA, ECMWF, OpenStreetMap, GeoNames.")
