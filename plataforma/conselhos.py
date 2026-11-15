"""Conselhos sobre a água: o que fazer, para cada público, conforme o que os dados mostram hoje.

Como funciona
  1. detectar() olha para os dados do dia (boletim, cor da água por troço, plantas sobre a água,
     caudal e alertas dos últimos dias) e diz que situações estão activas e porquê, com os números.
  2. Cada situação tem conselhos próprios para cada público (CONSELHOS[situação][público]).
  3. A situação "sempre" está sempre activa: a água do rio nunca é segura para beber sem tratar.

Princípios
  * Os conselhos seguem as orientações da Organização Mundial da Saúde (OMS) e da UNICEF para o
    tratamento da água em casa, a água e o saneamento em emergências e o tratamento da diarreia.
  * O satélite vê a cor da água (lama e plantas), não vê micróbios nem químicos: nunca se diz que a
    água é segura. "Normal" quer dizer "como é costume", não "boa para beber".
  * Linguagem simples, frases curtas, uma acção por frase.
  * Não substituem as orientações do MISAU, do INGD, da ARA-Sul e dos serviços distritais.

Os textos estão em português; as traduções (inglês, francês) estão em textos.py.
"""

from __future__ import annotations

import pandas as pd

ORDEM_NIVEIS = ["verde", "amarelo", "laranja", "vermelho"]
TROCOS_MARRACUENE = ("Q7", "Q8", "Q9")          # Manhiça to the mouth: the water the district uses

PUBLICOS = {
    "familias": ("Famílias", "casa"),
    "agricultores": ("Agricultores e criadores de gado", "campo"),
    "pescadores": ("Pescadores", "onda"),
    "escolas": ("Escolas", "livro"),
    "saude": ("Unidades de saúde", "escudo"),
    "abastecimento": ("Quem trata e distribui água", "gota"),
    "autoridades": ("Autoridades e líderes comunitários", "pessoas"),
}

# situation -> (title, what it means, level: info | atencao | alto)
SITUACOES = {
    "cheia": ("Alerta de cheia", "O rio pode alagar as zonas baixas de Marracuene nos próximos dias.", "alto"),
    "pos_cheia": ("Depois da cheia", "A água baixou há pouco tempo. Poços, latrinas e comida podem ter ficado contaminados.", "alto"),
    "agua_turva": ("Água mais turva do que o costume", "A água do rio traz mais lama do que é habitual nesta época. Água barrenta é mais difícil de desinfectar.", "atencao"),
    "turbidez_prevista": ("Água turva nos próximos dias", "A previsão indica água mais turva do que o habitual nas próximas manhãs.", "atencao"),
    "plantas": ("Plantas a cobrir o rio", "O satélite vê plantas sobre a água (pode ser jacinto-de-água). Junto delas a água fica parada.", "atencao"),
    "caudal_baixo": ("Rio com pouca água para a época", "Com pouca água, a sujidade fica mais concentrada e, perto da foz, a água do mar pode subir pelo rio.", "atencao"),
    "sempre": ("Todos os dias", "A água do rio nunca é segura para beber sem tratar, mesmo quando parece limpa.", "info"),
}

CONSELHOS = {
    "sempre": {
        "familias": ["Trate sempre a água do rio ou de poços abertos antes de beber ou cozinhar: ferva-a ou use cloro (por exemplo, Certeza).",
                     "Guarde a água tratada num recipiente limpo, tapado e de boca estreita. Tire a água com uma caneca só para isso, sem meter as mãos.",
                     "Lave as mãos com água e sabão (ou cinza) depois de usar a latrina e antes de comer ou preparar comida.",
                     "Evite tomar banho, nadar ou lavar roupa em água parada ou com plantas: pode apanhar bilharziose."],
        "agricultores": ["Dê aos animais água limpa; evite que bebam em charcos e água parada.",
                         "Não use água do rio sem tratar para lavar legumes que se comem crus.",
                         "Use botas quando trabalhar na água ou na lama dos canais (bilharziose)."],
        "pescadores": ["Leve água tratada para beber no barco; não beba água do rio.",
                       "Limpe o peixe com água tratada e cozinhe-o bem.",
                       "Use botas e evite ficar muito tempo dentro de água parada (bilharziose)."],
        "escolas": ["Dê aos alunos água tratada para beber (fervida ou com cloro), em recipientes tapados e com torneira.",
                    "Tenha um ponto de lavagem das mãos com sabão perto das latrinas.",
                    "Ensine os passos para tratar a água em casa: os alunos levam a mensagem às famílias."],
        "saude": ["Distribua cloro e explique como tratar a água em casa; reforce a lavagem das mãos.",
                  "Registe e comunique os casos de diarreia: um aumento súbito pode indicar cólera.",
                  "Siga o programa nacional de desparasitação e de tratamento da bilharziose nas comunidades junto ao rio."],
        "abastecimento": ["Meça o cloro residual nas torneiras todos os dias: a OMS recomenda pelo menos 0,2 mg/L no ponto de entrega.",
                          "Proteja as captações e os furos: vedação, tampa, drenagem e longe de latrinas."],
        "autoridades": ["Partilhe estes conselhos nas reuniões, na rádio comunitária e nos grupos de WhatsApp.",
                        "Saiba quem são as famílias mais vulneráveis (idosos, pessoas com deficiência, grávidas, crianças) e quem as ajuda em caso de alerta."],
    },
    "agua_turva": {
        "familias": ["Água barrenta é mais difícil de desinfectar. Primeiro deixe-a repousar algumas horas, tapada, e passe a parte de cima para outro recipiente.",
                     "Depois coe a água por um pano limpo dobrado várias vezes.",
                     "Só depois desinfecte: ferva (fervura forte durante pelo menos 1 minuto) ou ponha cloro na dose do frasco e espere 30 minutos antes de beber.",
                     "Se a água continuar turva depois de coada, ferva-a ou use a dose de cloro indicada para água turva.",
                     "Não use a garrafa ao sol (método SODIS) com água turva: só funciona com água límpida."],
        "agricultores": ["A água turva serve para regar a maior parte das culturas, mas entope bombas, filtros e gotejadores: limpe-os mais vezes.",
                         "Se puder, deixe a água assentar num tanque antes de regar.",
                         "Evite regar viveiros e sementeiras com água muito barrenta: a lama cobre as plantas jovens."],
        "pescadores": ["Com água barrenta vê-se mal o fundo e os troncos que a corrente arrasta: navegue devagar e com cuidado."],
        "escolas": ["Deixe assentar e coe a água antes de a desinfectar, e confirme que a água de beber da escola está tratada."],
        "saude": ["Água mais turva costuma trazer mais micróbios: aumente a vigilância das diarreias nas comunidades junto ao rio.",
                  "Lembre às famílias que água turva tem de ser coada antes do cloro ou da fervura."],
        "abastecimento": ["Ajuste a dose de coagulante com ensaios de jarros e prolongue a decantação; filtre antes de clorar.",
                          "A turvação protege os micróbios do cloro: o ideal é a água chegar à desinfecção com menos de 1 NTU. Confirme o cloro residual.",
                          "Se não conseguir garantir água segura, avise os utentes para ferverem ou clorarem a água em casa."],
        "autoridades": ["Peça aos serviços de saúde que distribuam cloro (Certeza) nos bairros que usam água do rio.",
                        "Lembre nas comunidades que a água turva tem de ser coada antes de ser tratada."],
    },
    "turbidez_prevista": {
        "familias": ["Nos próximos dias a água deve ficar mais turva: se puder, recolha e trate já a água de que vai precisar."],
        "agricultores": ["Nos próximos dias a água deve vir mais barrenta: planeie as regas e limpe os filtros."],
        "abastecimento": ["Prepare coagulante e cloro para os próximos dias de água mais turva."],
        "saude": ["Prepare stock de cloro para distribuir se a água ficar mais turva."],
    },
    "cheia": {
        "familias": ["Guarde água tratada para pelo menos 3 dias, em recipientes fechados.",
                     "Tenha à mão cloro (Certeza), sabão, sais de reidratação oral (SRO) e os documentos num saco de plástico.",
                     "Não deixe as crianças brincar na água da cheia e não atravesse água a correr: pouca água a correr pode derrubar uma pessoa.",
                     "Se a água da cheia chegar à latrina ou ao poço, não use essa água sem a tratar."],
        "agricultores": ["Leve o gado, as sementes, os adubos e os pesticidas para lugar alto: pesticidas na água da cheia contaminam poços e campos.",
                         "Retire as bombas e os motores das margens.",
                         "Se for seguro, colha já o que estiver maduro."],
        "pescadores": ["Não saia de barco enquanto durar o alerta. Prenda os barcos e as redes em lugar alto.",
                       "Use colete salva-vidas sempre que estiver na água."],
        "escolas": ["Siga as indicações do INGD e da direcção distrital de educação sobre as aulas e a evacuação.",
                    "Combine com as famílias como avisar e onde se encontrar se for preciso sair.",
                    "Guarde os documentos e os materiais escolares em lugar alto."],
        "saude": ["Prepare stocks de sais de reidratação oral, soros, cloro e testes rápidos de malária e de cólera.",
                  "Proteja medicamentos, vacinas e registos da água; tenha um plano para continuar a funcionar ou mudar de lugar."],
        "abastecimento": ["Proteja ou desligue as bombas e os quadros eléctricos que podem ficar debaixo de água; tenha combustível e peças de reserva.",
                          "Prepare água de emergência (camiões-cisterna, tanques) para os centros de acomodação."],
        "autoridades": ["Siga e divulgue as ordens do INGD; prepare os centros de acomodação com água potável, latrinas e pontos de lavagem das mãos.",
                        "Retire primeiro as pessoas dos lugares que alagam primeiro (ver a página Lugares)."],
    },
    "pos_cheia": {
        "familias": ["Não beba água de poços ou furos que ficaram debaixo de água sem a tratar; peça aos serviços distritais que limpem e desinfectem o poço.",
                     "Deite fora a comida que esteve em contacto com a água da cheia.",
                     "Lave a casa e os recipientes da água com água e lixívia antes de os voltar a usar.",
                     "Tape as feridas e use botas ou chinelos na lama: a água da cheia transmite doenças.",
                     "Se alguém tiver diarreia, comece logo os sais de reidratação e vá à unidade sanitária: pode ser cólera."],
        "agricultores": ["Não dê aos animais água estagnada da cheia; vigie sinais de doença e chame os serviços de veterinária.",
                         "Lave com água tratada e cozinhe bem os produtos que estiveram debaixo de água antes de os comer ou vender.",
                         "Espere que os campos sequem antes de voltar a semear; a lama deixada pela cheia é fértil."],
        "pescadores": ["Volte ao rio só quando as autoridades disserem que é seguro: a corrente e os destroços continuam perigosos.",
                       "Não venda nem coma peixe encontrado morto na água ou nas margens."],
        "escolas": ["Antes de reabrir, limpe e desinfecte as salas, as latrinas e os depósitos de água.",
                    "Esteja atento a alunos com diarreia ou febre e encaminhe-os para a unidade sanitária."],
        "saude": ["Nas semanas seguintes espere mais diarreias (incluindo cólera), malária, infecções de pele e leptospirose: vigie e comunique depressa.",
                  "Apoie a desinfecção dos poços e a distribuição de cloro nos bairros afectados."],
        "abastecimento": ["Antes de repor o serviço, lave e desinfecte depósitos, condutas e furos (cloragem de choque) e confirme o cloro residual.",
                          "Analise a água (pelo menos coliformes e cloro residual) antes de dizer aos utentes que é segura."],
        "autoridades": ["Organize a limpeza e a desinfecção dos poços e a recolha do lixo; não deixe água parada (mosquitos).",
                        "Coordene com a saúde a vigilância das diarreias e a distribuição de cloro e de sais de reidratação."],
    },
    "caudal_baixo": {
        "familias": ["Com pouca água no rio, a sujidade fica mais concentrada: trate sempre a água antes de beber.",
                     "Perto da foz, a água do mar pode subir pelo rio. Água salgada não fica boa com cloro nem a ferver: procure outra fonte para beber.",
                     "Poupe água: guarde-a tapada e use a água de lavar para regar."],
        "agricultores": ["Antes de regar com água do rio perto da foz, confirme que não está salgada (pergunte à ARA-Sul ou aos serviços distritais): água salgada estraga as culturas e o solo.",
                         "Regue de manhã cedo ou ao fim do dia e cubra o solo com palha.",
                         "Partilhe a água de forma justa com os vizinhos e respeite as regras da ARA-Sul para as captações."],
        "pescadores": ["Com pouca água, o peixe junta-se nos poços e é fácil pescar demais: deixe os peixes pequenos crescer."],
        "escolas": ["Guarde uma reserva de água tratada para os dias de aulas."],
        "saude": ["Com pouca água, as famílias podem usar fontes inseguras: reforce a mensagem de tratar a água."],
        "abastecimento": ["Em Marracuene e perto da foz, meça a condutividade (sal) na captação; com água salgada, pare a captação ou misture com outra fonte.",
                          "Reduza as perdas e organize turnos de distribuição se a água não chegar para todos."],
        "autoridades": ["Coordene com a ARA-Sul a partilha da água entre rega, gado e consumo humano, com prioridade para a água de beber."],
    },
    "plantas": {
        "familias": ["Junto das plantas a água fica parada: é onde vivem os caracóis da bilharziose e os mosquitos. Não tome banho nem lave roupa nesses sítios.",
                     "Recolha a água para casa num sítio com corrente e sem plantas, e trate-a sempre."],
        "agricultores": ["As plantas entopem bombas e canais: proteja as captações com uma rede e limpe-as com frequência.",
                         "As plantas retiradas do rio podem servir para fazer composto, longe da margem para não voltarem à água."],
        "pescadores": ["As plantas prendem as hélices e as redes: evite as zonas cobertas."],
        "escolas": ["Lembre aos alunos que não devem tomar banho no rio, sobretudo onde há plantas (bilharziose)."],
        "saude": ["Água parada junto às plantas favorece a bilharziose e a malária: reforce a prevenção nessas comunidades."],
        "abastecimento": ["Limpe as grelhas das captações com mais frequência e proteja-as com barreiras flutuantes."],
        "autoridades": ["Organize com a ARA-Sul e as comunidades a retirada das plantas junto às captações e às zonas de pesca."],
    },
}

GUIA_TRATAMENTO = [
    ("Recolha", "Tire a água de um sítio com corrente, longe de latrinas, do gado e das plantas, com um recipiente limpo."),
    ("Deixe assentar", "Deixe a água repousar algumas horas, tapada, para a lama ir ao fundo."),
    ("Coe", "Passe a parte de cima por um pano limpo dobrado várias vezes, sem mexer o fundo."),
    ("Desinfecte", "Ferva (fervura forte durante pelo menos 1 minuto) ou ponha cloro na dose do frasco e espere 30 minutos."),
    ("Guarde bem", "Num recipiente limpo, tapado e de boca estreita. Tire a água com uma caneca só para isso."),
    ("Mãos limpas", "Lave as mãos com sabão antes de mexer na água e na comida."),
]

DIARREIA = [
    "Dê logo sais de reidratação oral (SRO) da unidade sanitária, aos golinhos, depois de cada dejecção.",
    "Se não tiver: 1 litro de água tratada, 6 colheres de chá rasas de açúcar e meia colher de chá rasa de sal. Faça uma nova mistura todos os dias.",
    "Continue a dar de comer; aos bebés, continue a dar o peito.",
    "Vá logo à unidade sanitária se houver muitas fezes líquidas, vómitos, sangue nas fezes, muita sede, olhos encovados ou pouca urina, sobretudo em crianças, idosos e grávidas.",
]

FONTES = ("Conselhos baseados nas orientações da Organização Mundial da Saúde (OMS) e da UNICEF sobre o tratamento da água em casa, a água e o "
          "saneamento em emergências e o tratamento da diarreia. Não substituem as orientações do MISAU, do INGD, da ARA-Sul e dos serviços distritais.")


# ----------------------------------------------------------------------------- what the data show today
PLANTAS_PARTE = 0.30         # share of the river core covered by plants that counts as "plants covering the river"
PLANTAS_IMAGENS = 2          # ... seen in at least this many images of the month (one image can be a passing mat or a bad image)
MESES_RECENTES = 1           # a section's colour counts for "today" only if measured this month or the month before


def _recentes(estado_q: pd.DataFrame, hoje: pd.Timestamp) -> pd.DataFrame:
    """Sections measured recently enough to speak about today (never an old month presented as today)."""
    if "mes" not in estado_q:
        return estado_q.iloc[0:0]
    primeiro = (hoje.to_period("M") - MESES_RECENTES).strftime("%Y-%m")
    return estado_q[estado_q["mes"].astype(str) >= primeiro]


def detectar(boletim: dict, turbidez: pd.DataFrame | None, estado_q: pd.DataFrame | None, historico: pd.DataFrame | None,
             turbidez_diaria: pd.DataFrame | None = None) -> list[dict]:
    """Active situations, most serious first: [{chave, titulo, texto, nivel, porque: [(template, values)]}].
    Each reason is a Portuguese template with {gaps} so it can be translated."""
    activas = []

    def juntar(chave: str, porque: list[tuple[str, dict]], nivel: str | None = None):
        titulo, texto, nivel_base = SITUACOES[chave]
        activas.append({"chave": chave, "titulo": titulo, "texto": texto, "nivel": nivel or nivel_base, "porque": porque})

    valido = bool(boletim.get("seguro_mostrar"))
    nivel = boletim.get("nivel_maximo_provavel", "verde") if valido else "verde"

    # floods (quantity)
    if valido and nivel in ("amarelo", "laranja", "vermelho"):
        juntar("cheia", [("O boletim de hoje dá alerta {nivel} para os próximos 10 dias.", {"nivel": nivel})], "alto" if nivel != "amarelo" else "atencao")

    # just after a flood: an orange or red day in the last 3 weeks and the level is now lower
    if historico is not None and len(historico) and nivel in ("verde", "amarelo"):
        dados = historico.assign(data=pd.to_datetime(historico["data"]))
        recentes = dados[dados["data"] >= dados["data"].max() - pd.Timedelta(days=21)]
        graves = recentes[recentes["alerta"].isin(["laranja", "vermelho"])]
        if len(graves):
            juntar("pos_cheia", [("Houve alerta {nivel} a {dia}.", {"nivel": graves.iloc[-1]["alerta"], "dia": graves.iloc[-1]["data"].strftime("%d/%m")})])

    # water colour (quality): Marracuene reaches in the bulletin (last 20 days) and Module Q sections Q7 to Q9 (last month measured)
    porque, muito = [], False
    if turbidez is not None and len(turbidez):
        elevados = turbidez[turbidez["estado"].isin(["elevada", "muito elevada"])]
        for _, linha in elevados.iterrows():
            nome = str(linha.get("troco", "")).split(" ", 1)[-1]           # "2 troço médio" -> "troço médio"
            porque.append(("Marracuene, {troco}: turbidez {estado} nos últimos 20 dias.", {"troco": nome, "estado": linha["estado"]}))
            muito |= linha["estado"] == "muito elevada"
    hoje = pd.Timestamp(boletim.get("estado", {}).get("data_da_previsao") or pd.Timestamp.now().date())
    recentes = _recentes(estado_q, hoje) if estado_q is not None and len(estado_q) else None
    if recentes is not None and len(recentes):
        q = recentes[recentes["troco"].isin(TROCOS_MARRACUENE) & recentes["classe"].isin(["elevada", "muito elevada"])]
        for _, linha in q.iterrows():
            porque.append(("{nome}: turbidez {classe} face ao costume da época ({mes}).", {"nome": linha["nome"], "classe": linha["classe"], "mes": str(linha.get("mes", ""))}))
            muito |= linha["classe"] == "muito elevada"
    if porque:
        juntar("agua_turva", porque, "alto" if muito else "atencao")

    if turbidez_diaria is not None and len(turbidez_diaria) and valido:
        maximo = float(turbidez_diaria.max().max())
        if maximo >= 0.5:
            juntar("turbidez_prevista", [("Probabilidade de água mais turva do que o habitual numa das próximas manhãs: {p} %.", {"p": f"{100 * maximo:.0f}"})])

    # plants on the water: share of the river core covered (leaves and reeds of the banks are left out),
    # in a section measured with good reliability, seen in at least two images of a recent month
    if recentes is not None and "vegetacao" in recentes:
        plantas = recentes[(recentes["vegetacao"] >= PLANTAS_PARTE) & (recentes["fiabilidade"] == "boa")]
        if "imagens_plantas" in plantas:
            plantas = plantas[plantas["imagens_plantas"] >= PLANTAS_IMAGENS]
        if len(plantas):
            juntar("plantas", [("{nome}: plantas em cerca de {p} % do canal ({mes}).", {"nome": linha["nome"], "p": f"{100 * linha['vegetacao']:.0f}", "mes": str(linha.get("mes", ""))})
                               for _, linha in plantas.iterrows()])

    # little water for the season: today's forecast flow below the 25th percentile of the same month in 2006-2025
    if historico is not None and len(historico) and valido and boletim.get("previsao_diaria"):
        dados = historico.assign(data=pd.to_datetime(historico["data"]))
        hoje = pd.Timestamp(boletim["previsao_diaria"][0]["data"])
        mes = dados[(dados["data"].dt.month == hoje.month) & (dados["data"].dt.year < hoje.year)]["caudal_m3s"].dropna()
        caudal = boletim["previsao_diaria"][0]["caudal_mediana_m3s"]
        if len(mes) > 100 and mes.quantile(0.25) > 0 and caudal < mes.quantile(0.25):
            juntar("caudal_baixo", [("Caudal de hoje: {caudal} m³/s; em {mes} é costume ter mais de {p25} m³/s.",
                                     {"caudal": f"{caudal:.0f}", "mes": hoje.strftime("%m"), "p25": f"{mes.quantile(0.25):.0f}"})])

    juntar("sempre", [])
    peso = {"alto": 0, "atencao": 1, "info": 2}
    return sorted(activas, key=lambda s: peso[s["nivel"]])


def para(publico: str, situacoes: list[dict]) -> list[tuple[dict, list[str]]]:
    """The advice for one audience, situation by situation (most serious first)."""
    return [(s, CONSELHOS[s["chave"]].get(publico, [])) for s in situacoes if CONSELHOS[s["chave"]].get(publico)]
