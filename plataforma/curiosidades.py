"""Curiosidades sobre o rio Incomáti, os satélites e uma ciência que ainda está a crescer.

Cada curiosidade foi verificada (fonte no fim de cada uma) e abre com um número em destaque (a «figura»),
sem ícones nem emojis. As que têm números entre chavetas são calculadas pela aplicação a partir do pacote
de dados, para nunca ficarem desactualizadas:
    caudal, dia, segundos        o dia de maior caudal desde 2006 (series/alertas_historicos.csv)
    area, parte                  a área alagada em Janeiro de 2026 (sobre/factos.csv) e a parte do distrito
    imagens, por_mes             as imagens do Sentinel-2 em que se via o rio em Marracuene (series/cor_da_agua_por_imagem.csv)
    bacia                        a área da bacia (46 624 km², arredondada a 46 600), escrita à maneira de cada língua
As outras áreas foram calculadas uma vez pelo projecto, em EPSG:32736: a bacia do Incomáti
(data/raw/aoi/incomati_basin.geojson, HydroSHEDS) tem 46 624 km² e o distrito de Marracuene
(data/raw/aoi/marracuene_district.geojson, FAO GAUL) 706 km².
"""

from __future__ import annotations

AREA_DO_DISTRITO_KM2 = 706
AREA_DA_BACIA_KM2 = 46600
PISCINA_OLIMPICA_M3 = 2500                     # 50 m x 25 m x 2 m

GRUPOS = [("rio", "O nosso rio"), ("ceu", "Olhos no céu"), ("ciencia", "Uma ciência ainda em desenvolvimento")]

CURIOSIDADES = [
    {"chave": "tres_paises", "grupo": "rio", "figura": "3", "legenda": "países", "titulo": "Um rio de três países",
     "texto": "O Incomáti nasce na África do Sul, em Mpumalanga, atravessa Essuatíni e entra em Moçambique em Ressano Garcia. "
              "Depois de mais de 400 km, chega ao mar na Baía de Maputo, junto a Marracuene.",
     "fonte": "Saraiva Okello e outros, Hydrology and Earth System Sciences (2015); Global Water Partnership"},
    {"chave": "bacia", "grupo": "rio", "figura": "{bacia}", "legenda": "km² de bacia", "titulo": "Uma bacia 66 vezes maior do que o distrito",
     "texto": "A chuva que cai em cerca de 46 600 km² escorre para o Incomáti: 66 vezes a área do distrito de Marracuene. "
              "Por isso o rio pode subir aqui sem chover em Marracuene.",
     "fonte": "Limites da bacia (HydroSHEDS) e do distrito (FAO GAUL), áreas calculadas pelo projecto"},
    {"chave": "piscina", "grupo": "rio", "figura": "{segundos}", "legenda": "segundos", "titulo": "Uma piscina olímpica em menos de um segundo",
     "texto": "A {dia}, o dia de maior caudal desde 2006, passavam em Marracuene cerca de {caudal} m³ de água por segundo. "
              "Chegava para encher uma piscina olímpica (2 500 m³) em {segundos} segundos.",
     "fonte": "Caudal estimado pelo modelo GloFAS (Copernicus), não medido no rio"},
    {"chave": "terco", "grupo": "rio", "figura": "{parte} %", "legenda": "do distrito", "titulo": "Um terço do distrito debaixo de água",
     "texto": "Na cheia de Janeiro de 2026, a água cobriu {area} km² do distrito de Marracuene: {parte} % da sua área.",
     "fonte": "Mapas da cheia do Copernicus EMS (activação EMSR857), calculado pelo projecto"},
    {"chave": "radar", "grupo": "ceu", "figura": "Dia e noite", "legenda": "com ou sem nuvens", "titulo": "O radar vê através das nuvens",
     "texto": "O Sentinel-1 não tira fotografias: envia ondas de radar e mede o eco, de dia e de noite, com ou sem nuvens. "
              "A água calma devolve o sinal para longe, como um espelho, e aparece negra. É assim que o projecto encontra as cheias.",
     "fonte": "Agência Espacial Europeia (ESA)"},
    {"chave": "pixel", "grupo": "ceu", "figura": "10 m", "legenda": "por píxel", "titulo": "Cada ponto mede 10 metros",
     "texto": "Nas imagens do Sentinel-2, cada ponto da imagem (o píxel) cobre 10 m por 10 m de terreno. "
              "Um campo de futebol ocupa cerca de 70 pontos. Dois satélites iguais passam pelo mesmo sítio de 5 em 5 dias.",
     "fonte": "Copernicus, Sentinel-2: resolução e revisita"},
    {"chave": "nuvens", "grupo": "ceu", "figura": "{imagens}", "legenda": "imagens limpas", "titulo": "As nuvens são o maior obstáculo",
     "texto": "Desde 2017, o Sentinel-2 deu {imagens} imagens em que se via a água do rio em Marracuene: cerca de {por_mes} por mês, "
              "porque as nuvens tapam muitas passagens. Por isso a plataforma diz sempre a data da última imagem limpa.",
     "fonte": "Imagens do Sentinel-2 usadas pelo projecto"},
    {"chave": "gratis", "grupo": "ceu", "figura": "1972", "legenda": "primeiro Landsat", "titulo": "Imagens grátis para todos",
     "texto": "As imagens dos satélites Sentinel (programa Copernicus, da União Europeia) e Landsat (Estados Unidos) são gratuitas e abertas a qualquer pessoa. "
              "O primeiro Landsat foi lançado em 1972: é o registo mais longo da Terra vista do espaço.",
     "fonte": "Comissão Europeia e ESA; NASA e USGS"},
    {"chave": "swot", "grupo": "ciencia", "figura": "100 m", "legenda": "de largura mínima", "titulo": "Medir a altura dos rios a partir do espaço",
     "texto": "O satélite SWOT, lançado em Dezembro de 2022 pela NASA e pela agência espacial francesa, é o primeiro a medir a altura da água "
              "em quase todos os rios com mais de 100 m de largura. Os cientistas ainda estão a aprender a usar estas medições para seguir as cheias.",
     "fonte": "NASA JPL e CNES, missão SWOT"},
    {"chave": "radares", "grupo": "ciencia", "figura": "12 dias", "legenda": "duas imagens da Terra", "titulo": "Mais radares no céu",
     "texto": "O Sentinel-1C (Dezembro de 2024) e o Sentinel-1D (Novembro de 2025) voam na mesma órbita, em lados opostos da Terra. "
              "O NISAR, da NASA e da agência espacial indiana, lançado em Julho de 2025, vê quase toda a terra do planeta duas vezes em cada 12 dias. "
              "Mais radares quer dizer cheias vistas mais vezes, mesmo com nuvens.",
     "fonte": "ESA; NASA JPL e ISRO"},
    {"chave": "ia", "grupo": "ciencia", "figura": "100", "legenda": "países com previsão", "titulo": "Inteligência artificial contra as cheias",
     "texto": "Em 2024, a previsão de cheias de rios feita com inteligência artificial pela Google chegou a mais de 100 países, onde vivem 700 milhões de pessoas. "
              "Estes modelos aprendem com o passado: quanto mais medições houver nos rios, melhores ficam.",
     "fonte": "Google, Flood Hub (Novembro de 2024)"},
    {"chave": "qualidade", "grupo": "ciencia", "figura": "0", "legenda": "estações públicas", "titulo": "A cor da água ainda não diz tudo",
     "texto": "Do espaço já se vê a lama e as plantas na água, mas não se vêem micróbios nem químicos. "
              "Na bacia do Incomáti não há nenhuma estação pública de qualidade da água no arquivo mundial GEMStat: medir a água no rio é o passo que falta.",
     "fonte": "GEMStat (Programa das Nações Unidas para o Ambiente); método do projecto"},
]
POR_CHAVE = {c["chave"]: c for c in CURIOSIDADES}


def do_dia(dia_do_ano: int, quantas: int = 3) -> list[dict]:
    """Uma curiosidade de cada grupo, a mudar todos os dias (a primeira página mostra três)."""
    escolhidas = []
    for grupo, _ in GRUPOS[:quantas]:
        do_grupo = [c for c in CURIOSIDADES if c["grupo"] == grupo]
        escolhidas.append(do_grupo[dia_do_ano % len(do_grupo)])
    return escolhidas
