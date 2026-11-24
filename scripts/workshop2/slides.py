"""Os slides do Workshop 2 (104 slides, estilo académico, uma ideia por slide).

Cada slide é construído aqui; a ordem está em slides_ordem.py, as notas fixas em slides_notas.py e as notas com
números das respostas de referência são escritas aqui (mudam sozinhas se os dados mudarem).
Escrever o deck:  .venv/bin/python scripts/build_workshop2_slides.py
"""

import json
import re

from . import slides_base as B
from .comum import ANO_POR_PAR, FAC
from .slides_base import (ACENTO, AGUA, BANDA, BRANCO, CAB_TABELA, CAIXA, ERRO_FUNDO, LARANJA, LARANJA_CX, LINHA, NB,
                          NOTAS, PRETO, REALCE, SENTINEL, SERIE_TESTE, SERIE_TREINO, SUAVE, TINTA, TITULO, apoios, bloco,
                          bloco_codigo, caixa, codigo, coluna, definicao, destaque, divisoria, figura, fmt, grelha, h3, imagem,
                          lead, legenda, linha, lista, logo_ete, numero_grande, p, pergunta_abertura, qr, revelar, seta, slide)
from .slides_notas import NOTAS_FIXAS
from .slides_ordem import ORDEM, SECCOES

TEORIA = json.loads((FAC / "imagens_para_slides/figuras_teoria.json").read_text(encoding="utf-8"))
REF = json.loads((FAC / "resultados_de_referencia.json").read_text(encoding="utf-8"))
AR = json.loads((FAC / "aulas_resolvidas/resultados_de_referencia.json").read_text(encoding="utf-8"))   # as 4 aulas da prática
rg = REF["regressao"]
alg = REF["algoritmos"]
rede = alg["Rede neuronal (16 + 16)"]
ems = REF["ems_modelo"]
cv = REF["avancado"]["cv"]

B.definir_ordem(ORDEM, SECCOES)
NOTAS.clear()
NOTAS.update(NOTAS_FIXAS)
S = {}

# Os slides com pouco texto ficam com letra maior (mais fácil de ler ao fundo da sala, sem meia página vazia)
B.ESCALA.clear()
B.ESCALA.update(dict.fromkeys(
    ["inquerito", "m1-telemovel", "m1-todos-os-dias", "m1-seguranca", "m1-armas", "m1-aprende", "m1-gancho", "m2-modelo",
     "m2-python", "m2-supervisionada", "m2-floresta-porque", "m2-algoritmos", "m3-futuro", "m3-exame-erro",
     "m3-notas-regressao", "m5-oficiais", "licoes"], 1.15))
B.ESCALA.update(dict.fromkeys(
    ["missao", "dia-manha", "dia-tarde", "m1-regras", "m1-actividade", "m2-modelo-exemplos", "m2-supervisionada-exemplos",
     "m2-reforco", "m2-floresta", "m2-deep-learning", "m2-actividade-votar", "quiz", "quiz-1", "quiz-2", "quiz-3", "quiz-4",
     "quiz-5", "m3-fluxo", "m3-divisao", "m3-notas", "m3-hiperparametros", "m3-decorar", "m3-verificacao", "m4-o-que-ve",
     "m4-ia-turbidez", "m4-nao-mede", "pratica-config", "pratica-partes", "pratica-partes-2", "pratica-avancado",
     "continuar"], 1.1))


def par_de_imagens(a, alt_a, b, alt_b, w, h):
    return linha(imagem(a, alt_a, w, h), imagem(b, alt_b, w, h), gap=16)


# ============================== ABERTURA (08:00–08:35) ==============================
S["capa"] = (
    f'<section id="capa" data-transition="fade" style="background:{BRANCO};color:{TINTA};font-family:Arial, sans-serif;'
    f'padding:88px 128px 88px;display:flex;flex-direction:column;justify-content:space-between;gap:40px">\n' + BANDA
    + linha(logo_ete(150), coluna(p("Projecto EYES TO EARTH (ETE)", 30, ACENTO, 700), p("Workshop de Estudantes 2", 30, SUAVE), gap=4),
            gap=36, alinhar="center")
    + coluna(f'<h1 style="font-family:{TITULO};font-size:80px;font-weight:400;line-height:1.08;color:{PRETO}">'
             "Inteligência Artificial<br>para monitorizar a água<br>e avisar das cheias</h1>",
             f'<div style="width:200px;height:6px;background:{ACENTO}"></div>',
             coluna(p("Sábado, 21 de Novembro de 2026, das 08:00 às 14:00"), p("Maputo, Moçambique"), gap=4), gap=28)
    + apoios() + B.aside("capa"))

S["missao"] = slide("missao", "Objectivo do workshop", coluna(
    caixa("Objectivo geral", p("No fim do dia, cada par terá treinado os seus próprios modelos de Inteligência Artificial "
                               "para encontrar a água da cheia e prever o rio, e saberá dizer onde eles erram.")),
    coluna(h3("Objectivos específicos"), lista([
        "Perceber como uma máquina aprende com exemplos: classificação e regressão.",
        "Treinar e avaliar modelos em Python, no Jupyter Notebook.",
        "Comparar os resultados de todos os pares e saber onde cada modelo erra."], num=True), gap=12), gap=40))

S["dia-manha"] = slide("dia-manha", "Programa da manhã", B.tabela(
    ["Hora", "Actividade"],
    [["08:00", "Registo"],
     ["08:15", "Abertura, questionário e revisão do Workshop 1"],
     ["08:35", "Módulo 1: O que é a Inteligência Artificial?"],
     ["09:05", "Módulo 2: Como uma máquina aprende"],
     ["09:55", "Quiz relâmpago"],
     ["10:05", "Módulo 3: Como sabemos se o modelo é bom?"],
     ["10:35", "Módulo 4: A IA e a qualidade da água"],
     ["11:00", "Módulo 5: A plataforma EYES TO EARTH"]],
    [16, 84], tam=30, alinh=["center", "left"]))

S["dia-tarde"] = slide("dia-tarde", "Programa da tarde", coluna(B.tabela(
    ["Hora", "Actividade"],
    [["11:20", "Intervalo (matabicho)"],
     ["11:40", "Prática em pares: treinar os nossos modelos no Jupyter Notebook"],
     ["13:25", "Apresentação dos resultados dos pares"],
     ["13:40", "Perguntas, questionário final e certificados"],
     ["14:00", "Fim"]],
    [16, 84], tam=30, alinh=["center", "left"]),
    destaque("Cada par treina modelos de classificação e de regressão com os dados do nosso rio."), gap=40))

S["inquerito"] = slide("inquerito", "Questionário inicial da OAD", linha(
    coluna(p("Duração: 5 minutos.", 30, SUAVE), lead("Respondam sozinhos, no telemóvel ou em papel."),
           p("Não há respostas erradas: o questionário serve para medir o que aprendemos hoje. "
             "No fim do dia respondem outra vez."), gap=28, extra="flex:1"),
    qr("[QR do questionário OAD pré-workshop]", 400), gap=64))

S["revisao-luz"] = slide("revisao-luz", "Um satélite vê a luz que a Terra reflecte", linha(
    coluna(p("Revisão do Workshop 1, para quem não esteve.", 30, SUAVE),
           lista(["Os satélites Landsat e Sentinel-2 medem a luz em várias bandas, também no infravermelho (NIR e SWIR).",
                  f"Uma imagem é uma tabela de píxeis de 30{NB}m × 30{NB}m.",
                  "A água absorve o infravermelho: fica escura nessas bandas."], num=True),
           gap=24, extra="flex:1"),
    figura("seca", "Imagem Sentinel-2 em cor natural de Marracuene na época seca", 397, 600,
           "Marracuene na época seca, 23/10/2025, em cor natural.", SENTINEL), gap=56))

S["revisao-regra"] = slide("revisao-regra", "A regra do Workshop 1 e a cheia de 2026", linha(
    figura("cheia", "Imagem Sentinel-2 em cor natural de 24 de Janeiro de 2026, com a planície inundada", 371, 560,
           "Cheia de 24/01/2026, em cor natural.", SENTINEL),
    figura("mapa_ws1", "Mapa da água: o rio de sempre a azul escuro e a água nova da cheia a verde-água", 371, 560,
           "Água segundo a regra: azul escuro, o rio de sempre; verde-água, a água nova."),
    coluna(caixa("A regra", p("MNDWI = (Verde − SWIR) ÷ (Verde + SWIR)", 30, TINTA, 700) + p("Maior do que 0? Então é água.")),
           coluna(p("Resultado", 30, SUAVE),
                  f'<p style="font-family:{TITULO};font-size:84px;line-height:1.1;color:{ACENTO}">20{NB}244{NB}ha</p>',
                  p(f"de água nova na planície de Marracuene: cerca de 28{NB}000 campos de futebol."), gap=8),
           gap=40, extra="flex:1"), gap=40))

S["revisao-2021"] = slide("revisao-2021", "Uma regra fixa falha quando a água muda: 2021", linha(
    coluna(par_de_imagens("r2021_cor", "Recorte do rio em 30 de Janeiro de 2021, cor natural, com muita água barrenta",
                          "r2021_ndwi", "O mesmo recorte segundo a regra NDWI: só partes do rio aparecem a azul", 496, 600),
           legenda("Recorte do rio a 30/01/2021: cor natural (esquerda) e regra NDWI (direita).", SENTINEL), gap=10,
           extra="width:1008px"),
    coluna(h3("Água muito barrenta"), lead("A regra NDWI encontrou só <b>51%</b> do rio."),
           p("A azul, o que a regra viu. A cinzento, as nuvens.", 28, SUAVE), gap=24, extra="flex:1"), gap=56))

S["revisao-2024"] = slide("revisao-2024", "Uma regra fixa falha quando a água muda: 2024", linha(
    coluna(par_de_imagens("r2024_cor", "Recorte do rio em 20 de Janeiro de 2024, cor natural: o rio está muito escuro",
                          "r2024_mndwi", "O mesmo recorte segundo a regra MNDWI: o rio desapareceu", 496, 600),
           legenda("Recorte do rio a 20/01/2024: cor natural (esquerda) e regra MNDWI (direita).", SENTINEL), gap=10,
           extra="width:1008px"),
    coluna(h3("Água muito escura"), lead("A regra MNDWI não encontrou o rio: <b>0%</b>."), p("O rio continuava lá."),
           destaque("E se, em vez de escrever a regra, déssemos exemplos ao computador?"), gap=24, extra="flex:1"), gap=56))

# ============================== MÓDULO 1 (08:35–09:05) ==============================
S["m1"] = divisoria("m1", "Módulo 1", "O que é a Inteligência Artificial?", "08:35–09:05 | Facilitador 1",
                    pergunta_abertura("Como é que o telemóvel sabe que a cara é a sua, mesmo de óculos ou com outro penteado?"))


def esquema(a, b, resultado):
    return linha(B.ficha(a), p("+", 30, TINTA, 700), B.ficha(b), seta(), B.ficha(resultado, True), gap=12, alinhar="center")


S["m1-regras"] = slide("m1-regras", "Duas maneiras de ensinar um computador", coluna(
    linha(caixa("Programação clássica", p("Uma pessoa escreve as regras. O computador só as segue.")
                + esquema("Regras", "Dados", "Respostas")
                + p("Exemplo: “se o MNDWI for maior do que 0, é água”.", 28, SUAVE), extra="flex:1;gap:20px"),
          caixa("Machine Learning", p("O computador descobre as regras sozinho, a partir de exemplos.")
                + esquema("Exemplos", "Respostas", "O modelo")
                + p("Exemplo: mil píxeis marcados “água” ou “não água”.", 28, SUAVE), extra="flex:1;gap:20px"),
          gap=40, alinhar="stretch"),
    destaque("Machine Learning = aprender com exemplos."), gap=36))


def conjunto(nome, filho, h, fundo, cor_txt, borda):
    return (f'<div style="height:{h}px;background:{fundo};border:2px solid {borda};padding:24px;display:flex;'
            f'flex-direction:column;justify-content:space-between;gap:16px">' + p(nome, 30, cor_txt, 700) + filho + "</div>")


dl = (f'<div style="height:200px;background:{ACENTO};padding:24px;display:flex;flex-direction:column;gap:6px">'
      + p("Deep Learning", 30, BRANCO, 700) + p("redes neuronais", 24, BRANCO) + "</div>")
S["m1-ia-ml-dl"] = slide("m1-ia-ml-dl", "IA, Machine Learning e Deep Learning", linha(
    '<div style="width:620px">' + conjunto("Inteligência Artificial", conjunto("Machine Learning", dl, 400, CAIXA, ACENTO, ACENTO),
                                           600, BRANCO, ACENTO, ACENTO) + "</div>",
    coluna(definicao("Inteligência Artificial", "Computadores a fazer tarefas que pareciam precisar de inteligência humana: "
                     "ver, ouvir, traduzir, decidir."),
           definicao("Machine Learning", "Uma forma de fazer IA: o computador aprende com exemplos, em vez de seguir "
                     "regras escritas por nós."),
           definicao("Deep Learning", "Machine Learning com redes neuronais de muitas camadas. Precisa de milhões de "
                     "exemplos. Está no tradutor e no ChatGPT."), gap=28, extra="flex:1"), gap=64))

S["m1-telemovel"] = slide("m1-telemovel", "A IA já está no seu telemóvel", coluna(
    grelha([definicao(a, b, 30) for a, b in [
        ("Filtro de spam", "Aprende com as mensagens marcadas como lixo."),
        ("Assistente de voz", "Transforma a sua voz em texto e responde."),
        ("Desbloqueio facial", "Reconhece a sua cara, mesmo de óculos."),
        ("Tradutor", "Traduz frases entre muitas línguas.")]], 2, "40px 64px"),
    destaque("Todos aprenderam com exemplos."), gap=48))

S["m1-todos-os-dias"] = slide("m1-todos-os-dias", "E em todo o lado, todos os dias", coluna(
    grelha([definicao(a, b, 30) for a, b in [
        ("Vídeos e música", "Escolhe o próximo vídeo no TikTok ou no YouTube."),
        ("Mapas e trânsito", "Prevê quanto tempo vai demorar a viagem."),
        ("ChatGPT e outros", "Escrevem textos e respondem a perguntas."),
        ("Saúde", "Ajuda os médicos a ler raios-X e análises.")]], 2, "40px 64px"),
    destaque("Também aprenderam com exemplos: milhões deles."), gap=48))

S["m1-seguranca"] = slide("m1-seguranca", "A IA também está na segurança", coluna(
    linha(caixa("Aeroportos", p("Os scanners de bagagem usam IA para assinalar armas e explosivos. Um agente confirma."),
                extra="flex:1"),
          caixa("Câmaras de vigilância", p("Reconhecem caras numa multidão. Podem errar e invadir a privacidade."),
                extra="flex:1"), gap=40, alinhar="stretch"),
    destaque("A IA ajuda; quem decide abrir a mala é uma pessoa."), gap=48))

S["m1-armas"] = slide("m1-armas", "E na guerra: quem decide?", coluna(
    caixa("Drones e armas autónomas", p("Sistemas que escolhem alvos sozinhos. A ONU discute regras para estas armas "
                                        "há mais de 10 anos.")),
    f'<div style="background:{REALCE};padding:28px 36px;display:flex;flex-direction:column;gap:12px">'
    + p("Quem deve tomar a decisão final: a máquina ou uma pessoa?", 40, ACENTO, 700)
    + p("A mesma ideia que encontra água numa imagem encontra um carro ou uma pessoa. Por isso a IA precisa de "
        "regras e de pessoas responsáveis.") + "</div>", gap=40))


def passo(n, titulo, texto):
    return (f'<div style="flex:1;border:1px solid {LINHA};padding:28px;display:flex;flex-direction:column;gap:10px">'
            + h3(f"{n}. {titulo}") + p(texto, 28) + "</div>")


S["m1-aprende"] = slide("m1-aprende", "Como aprende uma criança, e uma máquina", coluna(
    linha(passo(1, "Ver muitos exemplos", "Cães grandes, pequenos, de várias cores."), seta(48, 24, SUAVE),
          passo(2, "Ouvir a resposta certa", "Um adulto diz: “isto é um cão”."), seta(48, 24, SUAVE),
          passo(3, "Reconhecer o que é novo", "Um cão que nunca tinha visto."), gap=20, alinhar="center"),
    destaque("A máquina aprende da mesma forma, mas precisa de muitos mais exemplos, e só sabe o que viu."), gap=56))

S["m1-actividade"] = slide("m1-actividade", "Actividade: regra ou exemplos?", coluna(
    p("5 minutos, em pares. Para cada tarefa: é mais fácil escrever uma regra, ou dar exemplos à máquina?", 30, SUAVE),
    B.tabela(["Tarefa", "Regra ou exemplos?"],
             [["1. Calcular o troco numa loja", ""], ["2. Reconhecer a voz da avó ao telefone", ""],
              ["3. Pôr uma lista de nomes por ordem alfabética", ""], ["4. Separar as mensagens de spam", ""],
              ["5. Converter metros em quilómetros", ""], ["6. Encontrar água barrenta numa imagem de satélite", ""]],
             [68, 32], tam=30), gap=28))

S["m1-gancho"] = slide("m1-gancho", "Do Workshop 1 para hoje", coluna(
    lead("No Workshop 1 <b>escrevemos uma regra</b>. Hoje vamos <b>dar exemplos</b> ao computador e deixá-lo "
         "descobrir a regra sozinho."),
    caixa("Pergunta de verificação", p("Qual é a diferença entre escrever uma regra e treinar um modelo?")), gap=48))

# ============================== MÓDULO 2 (09:05–09:55) ==============================
S["m2"] = divisoria("m2", "Módulo 2", "Como uma máquina aprende", "09:05–09:55 | Facilitador 2",
                    pergunta_abertura("Como é que o scanner de um aeroporto aprende a reconhecer uma arma dentro de uma mala?"))

S["m2-modelo"] = slide("m2-modelo", "O que é um modelo?", coluna(
    linha(bloco("Entrada", "as pistas (números)", "flex:1", tam=30), seta(),
          bloco("O modelo", "aprendido com exemplos", "flex:1", tam=30), seta(),
          bloco("Saída", "a resposta", "flex:1", tam=30), gap=20, alinhar="center"),
    linha(caixa("Treinar", p("Ajustar o modelo aos exemplos, até as respostas ficarem certas."), extra="flex:1"),
          caixa("Prever", p("Usar o modelo, já treinado, em casos novos."), extra="flex:1"), gap=40, alinhar="stretch"),
    gap=56))

S["m2-modelo-exemplos"] = slide("m2-modelo-exemplos", "Três modelos, a mesma ideia", coluna(
    B.tabela(["Exemplo", "Entrada (as pistas)", "Saída (a resposta)"],
             [["Mapa de água", "Os números de um píxel: verde, NIR, SWIR...", "“água” ou “não água”"],
              ["Scanner de aeroporto", "A imagem de raio-X de uma mala", "“arma” ou “sem arma”"],
              ["Previsão do rio", "O caudal de hoje e a chuva dos últimos dias", "o caudal daqui a 3 dias (m³/s)"]],
             [24, 44, 32], tam=30),
    destaque("Entra uma lista de números; sai uma resposta."), gap=48))

S["m2-dados"] = slide("m2-dados", "Os dados: exemplos, características e rótulos", coluna(
    p("Cada <b>linha</b> é um exemplo; cada <b>coluna</b>, uma pista; a última coluna é o <b>rótulo</b>, a resposta certa."),
    coluna(linha(p("X: as características (as pistas)", 26, BRANCO, 700, f"flex:78;background:{SUAVE};padding:8px 16px"),
                 p("y: o rótulo", 26, BRANCO, 700, f"flex:22;background:{ACENTO};padding:8px 16px"), gap=0),
           B.tabela(["Verde", "Vermelho", "NIR", "SWIR", "MNDWI", "NDVI", "Rótulo"],
                    [["0,063", "0,061", "0,030", "0,016", "0,59", "−0,34", "água"],
                     ["0,064", "0,043", "0,342", "0,199", "−0,51", "0,78", "não água"],
                     ["0,115", "0,147", "0,193", "0,369", "−0,52", "0,14", "não água"]],
                    [13, 13, 13, 13, 13, 13, 22], tam=30, alinh=["center"] * 7),
           legenda("Três píxeis de Marracuene (23/10/2025): as bandas, dois índices e o rótulo.", tipo="Tabela"),
           gap=8), gap=36))

S["m2-python"] = slide("m2-python", "Em Python: aprender e prever", coluna(
    linha(coluna(codigo("modelo.fit(X, y)", 40), p("<b>Aprender</b> com os exemplos: X são as pistas e y os rótulos."),
                 gap=20, extra="flex:1"),
          coluna(codigo("modelo.predict(X_novo)", 40), p("<b>Prever</b> a resposta para casos novos."), gap=20, extra="flex:1"),
          gap=56, alinhar="stretch"),
    destaque("As mesmas duas linhas servem para todos os algoritmos do dia."), gap=56))


def tipo_caixa(titulo, subtitulo, folhas, cor=ACENTO):
    return coluna(f'<div style="background:{cor};padding:16px 20px">' + p(titulo, 30, BRANCO, 700) + p(subtitulo, 24, BRANCO) + "</div>",
                  f'<div style="width:4px;height:24px;background:{LINHA};align-self:center"></div>',
                  *[bloco(t, d, "", cor) for t, d in folhas], gap=10, extra="flex:1")


S["m2-tipos"] = slide("m2-tipos", "Os três tipos de aprendizagem", coluna(
    coluna(p("Machine Learning", 30, BRANCO, 700, f"background:{TINTA};padding:12px 24px;align-self:center"),
           f'<div style="width:1200px;height:4px;background:{LINHA};align-self:center"></div>', gap=0),
    linha(tipo_caixa("Supervisionada", "com rótulos: aprende com a resposta certa",
                     [("Classificação", "a resposta é uma categoria: água ou não água; arma ou sem arma"),
                      ("Regressão", "a resposta é um número: o caudal em m³/s; uma nota de 0 a 20")]),
          tipo_caixa("Não supervisionada", "sem rótulos: encontra grupos sozinha",
                     [("Agrupamento (K-means)", "píxeis parecidos; clientes ou músicas parecidas")], SUAVE),
          tipo_caixa("Por reforço", "tentativa, erro e recompensa",
                     [("Jogos e robôs", "xadrez, Go, robôs que aprendem a andar")], LARANJA),
          gap=32, alinhar="stretch"), gap=20))

S["m2-supervisionada"] = slide("m2-supervisionada", "Supervisionada: aprender com a resposta certa", coluna(
    lead("Damos ao computador exemplos com o rótulo certo. Ele aprende a ligar as pistas à resposta."),
    linha(caixa("Classificação", p("A resposta é uma <b>categoria</b>.") + p("água ou não água; arma ou sem arma", 28, SUAVE),
                extra="flex:1"),
          caixa("Regressão", p("A resposta é um <b>número</b>.") + p("o caudal em m³/s; uma nota de 0 a 20", 28, SUAVE),
                extra="flex:1"), gap=40, alinhar="stretch"), gap=48))

S["m2-supervisionada-exemplos"] = slide("m2-supervisionada-exemplos", "Classificação ou regressão?", B.tabela(
    ["Tarefa", "Resposta (saída)", "Tipo"],
    [["Filtro de spam", "spam ou normal", "Classificação"],
     ["Scanner de aeroporto", "arma ou sem arma", "Classificação"],
     ["Desbloqueio facial", "é o dono ou não", "Classificação"],
     ["Mapa de água", "água ou não água", "Classificação"],
     ["Preço de uma casa", "o preço em meticais", "Regressão"],
     ["Caudal do Incomáti", "m³/s daqui a 3 dias", "Regressão"]],
    [36, 38, 26], tam=30))

S["m2-classificacao"] = slide("m2-classificacao", "Classificação: traçar uma fronteira", linha(
    figura("ml_class", "Gráfico de pontos: píxeis de água a azul no canto de baixo e de não água a laranja; uma linha separa as duas cores", 760, 595,
           "Píxeis da cheia de 24/01/2026 (pontos da equipa), com duas pistas. Fronteira: regressão logística.", SENTINEL),
    coluna(p("Cada ponto é um píxel da cheia de 2026: <b>azul</b> = água, <b>laranja</b> = não água."),
           p("Treinar é encontrar a <b>fronteira</b> que melhor separa as duas cores."),
           destaque("Um píxel novo (a estrela) recebe a resposta do lado onde cai."), gap=28, extra="flex:1"), gap=48))

a, b = TEORIA["regressao_estudo"]["a"], TEORIA["regressao_estudo"]["b"]
NOTAS["m2-regressao"] = f"""FACILITADOR 2, cerca de 2 minutos. Dados inventados, para aprender: dizê-lo à turma.

"Agora a resposta é um número: a nota do exame, de 0 a 20. Cada ponto é um aluno: quantas horas estudou por semana e que nota teve.

O modelo mais simples de regressão é uma RECTA: nota = {fmt(a, 2)} × horas + {fmt(b, 1)}. Os dois números ({fmt(a, 2)} e {fmt(b, 1)}) não foram escritos por ninguém: foram APRENDIDOS com os 26 exemplos.

Os traços cinzentos são o ERRO de cada exemplo: a distância entre a nota verdadeira e a recta. Treinar uma regressão é encontrar a recta com o menor erro total.

Depois, para um aluno novo que estuda 10 horas, o modelo prevê cerca de 16 valores."

Pergunta à sala: "o modelo garante que esse aluno tem 16?" Não: é uma previsão, com erro. Na prática (Aula 4) fazemos o mesmo com o caudal do rio: o 'aluno' é o dia de hoje e a 'nota' é o caudal daqui a 3 dias."""
S["m2-regressao"] = slide("m2-regressao", "Regressão: prever um número", linha(
    figura("ml_regr", "Gráfico de pontos: horas de estudo e nota de 26 alunos, a preto, com a recta aprendida a vermelho e os erros a cinzento", 760, 575,
           "Dados inventados para o exemplo."),
    coluna(p("Cada ponto é um aluno: horas de estudo por semana e nota do exame."),
           p(f"O modelo é uma recta, <b>nota = {fmt(a, 2)} × horas + {fmt(b, 1)}</b>, aprendida com os exemplos."),
           p("Treinar é encontrar a recta com o menor <b>erro</b> total (os traços cinzentos)."),
           destaque("Um aluno que estuda 10 horas: o modelo prevê 16 valores."), gap=24, extra="flex:1"), gap=48))

S["m2-treinar"] = slide("m2-treinar", "Treinar é errar menos, passo a passo", coluna(
    p("O ciclo do treino: <b>1.</b> adivinhar; <b>2.</b> medir o erro; <b>3.</b> corrigir um pouco; <b>4.</b> repetir."),
    coluna(imagem("ml_treino", "À esquerda, rectas de cada passo do treino a aproximarem-se dos pontos; à direita, o erro a descer até estabilizar", 1400, 562),
           legenda("O treino da recta do slide anterior, passo a passo (dados inventados)."), gap=10, extra="align-self:center"),
    gap=32))

NOTAS["m2-regressao-rio"] = f"""FACILITADOR 2, cerca de 1,5 minutos. Dados reais: o caudal diário do GloFAS e a chuva na bacia do CHIRPS, de 2006 a 2026.

"Agora a mesma ideia no nosso rio. As pistas: o caudal de hoje e a chuva na bacia nos últimos 7, 14 e 30 dias. A resposta: o caudal daqui a 3 dias. Treinámos com 2006 a 2018 e fizemos o exame com 2019 a 2026, anos que o modelo nunca viu.

No exame, a recta erra em média {fmt(rg['linear']['MAE'])} m³/s (R² {fmt(rg['linear']['R2'], 2)}). Nos dias normais acerta bem. Mas olhem para a cheia de Janeiro de 2026: a linha cinzenta sobe DEPOIS da preta. A recta só previu 'laranja' quando o rio já estava a passar esse limite. Não anteviu a subida: o caudal passou de 255 para {fmt(rg['cheia_2026']['pico'])} m³/s em 8 dias, mais do que tudo o que o modelo viu no treino (máximo {fmt(rg['max_treino'])} m³/s)."

Mensagem: um modelo simples aprende o comportamento médio e falha nos extremos. Para avisar a tempo, a plataforma usa as previsões do GloFAS, feitas com modelos do tempo e de toda a bacia. Os estudantes treinam esta recta na Aula 4."""
S["m2-regressao-rio"] = slide("m2-regressao-rio", "Regressão no nosso rio: o caudal daqui a 3 dias", coluna(
    p("Pistas: o caudal de hoje e a chuva na bacia nos últimos 7, 14 e 30 dias. Treino: 2006–2018. Exame: 2019–2026."),
    coluna(imagem("regr_rio", "Gráfico da cheia de Janeiro de 2026: o caudal verdadeiro a preto e a previsão da recta a cinzento, que sobe com atraso", 1350, 548),
           legenda(f"A cheia de Janeiro de 2026: o que aconteceu e o que a recta previu 3 dias antes. Erro médio no exame: "
                   f"{fmt(rg['linear']['MAE'])} m³/s (R² {fmt(rg['linear']['R2'], 2)}).", "GloFAS, Copernicus (caudal) e CHIRPS (chuva)"),
           gap=10, extra="align-self:center"), gap=32))

S["m2-nao-supervisionada"] = slide("m2-nao-supervisionada", "Não supervisionada: encontrar grupos sem rótulos", coluna(
    p("Sem rótulos, o computador junta os píxeis parecidos. Ninguém lhe disse o que é cada grupo."),
    coluna(imagem("ml_agrup", "À esquerda, píxeis cinzentos sem rótulos; à direita, os mesmos píxeis em três grupos coloridos com os seus centros", 1100, 483),
           legenda("1 500 píxeis da cheia de 24/01/2026 (NIR e SWIR), antes e depois do K-means com 3 grupos.", SENTINEL),
           gap=10, extra="align-self:center"),
    p("No projecto não a usámos: tínhamos rótulos, os mapas oficiais das cheias.", 28, SUAVE), gap=28))

S["m2-reforco"] = slide("m2-reforco", "Por reforço: aprender com recompensas", coluna(
    linha(bloco("Agente", "o programa ou o robô", "flex:1"),
          coluna(linha(p("acção", 26, SUAVE, 700), seta(70, 30), gap=10, alinhar="center"),
                 linha(f'<x-shape kind="arrow-left" style="width:70px;height:30px;background:{LARANJA}"></x-shape>',
                       p("recompensa: mais ou menos pontos", 26, LARANJA, 700), gap=10, alinhar="center"), gap=16),
          bloco("Ambiente", "o jogo, o simulador, o mundo", "flex:1"), gap=28, alinhar="center"),
    lista(["<b>Jogos:</b> o AlphaGo venceu o campeão mundial de Go em 2016.",
           "<b>Robôs</b> que aprendem a andar, a cair e a levantar-se.",
           "<b>Drones e carros autónomos</b>, treinados primeiro em simulação."], 30),
    p("Não o usamos na prática: precisa de errar milhões de vezes num simulador.", 28, SUAVE), gap=32))

S["m2-actividade-tipos"] = slide("m2-actividade-tipos", "Actividade: que tipo de aprendizagem é?", coluna(
    p("4 minutos, em pares: classificação, regressão, agrupamento ou por reforço?", 30, SUAVE),
    B.tabela(["Tarefa", "Tipo"],
             [["1. A temperatura máxima de amanhã", ""],
              ["2. Uma mensagem de WhatsApp: “burla” ou “normal”", ""],
              ["3. Clientes em grupos parecidos, sem saber os grupos", ""],
              ["4. Um robô aprende a andar, caindo e levantando-se", ""],
              ["5. Um scanner: “arma” ou “sem arma”", ""],
              ["6. O caudal do Incomáti daqui a 3 dias", ""],
              ["7. Os píxeis de uma imagem em grupos parecidos", ""],
              ["8. A nota de um aluno, pelas horas de estudo", ""]], [74, 26], tam=28), gap=24))

S["m2-algoritmos"] = slide("m2-algoritmos", "Quatro algoritmos de classificação", coluna(
    grelha([caixa("Árvore de decisão", p("Perguntas de sim ou não. Fácil de ler.")),
            caixa("Random Forest", p("Muitas árvores a votar. Robusto e rápido.")),
            caixa("k vizinhos mais próximos", p("Segue a maioria dos exemplos mais parecidos.")),
            caixa("Rede neuronal", p("Camadas de neurónios. A base do Deep Learning."))]),
    destaque("Na prática (Aula 2), comparamos uma floresta de 100 árvores com uma só árvore."), gap=40))


def no(left, top, w, texto, fundo, cor, borda):
    return (f'<div style="position:absolute;left:{left}px;top:{top}px;width:{w}px;height:100px;background:{fundo};'
            f'border:2px solid {borda};display:flex;align-items:center;justify-content:center">'
            + p(texto, 30, cor, 700, "text-align:center") + "</div>")


def ramo(x1, y1, x2, y2):
    return f'<x-connector x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" head="end" style="color:{SUAVE};border-width:3px"></x-connector>'


def etiqueta(left, top, texto):
    return f'<p style="position:absolute;left:{left}px;top:{top}px;width:120px;font-size:28px;font-weight:700;color:{SUAVE}">{texto}</p>'


arvore = ('<div style="position:relative;width:1664px;height:470px">'
          + no(592, 0, 480, "MNDWI maior do que 0?", BRANCO, ACENTO, ACENTO)
          + ramo(740, 100, 340, 190) + ramo(924, 100, 1250, 190) + etiqueta(430, 110, "sim") + etiqueta(1130, 110, "não")
          + no(160, 190, 360, "ÁGUA", AGUA, BRANCO, AGUA)
          + no(1010, 190, 480, "NIR maior do que 0,25?", BRANCO, ACENTO, ACENTO)
          + ramo(1160, 290, 900, 370) + ramo(1340, 290, 1520, 370) + etiqueta(930, 296, "sim") + etiqueta(1460, 296, "não")
          + no(700, 370, 400, "VEGETAÇÃO", "#2E7D32", BRANCO, "#2E7D32")
          + no(1330, 370, 334, "SOLO", "#8B5A2B", BRANCO, "#8B5A2B") + "</div>")
S["m2-arvore"] = slide("m2-arvore", "Árvore de decisão: perguntas de sim ou não", coluna(
    arvore, p("O computador escolhe sozinho as perguntas e os números, olhando para os exemplos. É como o jogo das 20 perguntas."),
    gap=40))

perg = TEORIA["arvore_perguntas"]
NOTAS["m2-arvore-caixas"] = f"""FACILITADOR 2, cerca de 1,5 minutos. Dados reais: 24 píxeis da imagem de 23/10/2025 (água, vegetação e solo), só com duas pistas para se poder desenhar.

"Cada pergunta da árvore é um CORTE DIREITO no gráfico. A primeira pergunta que a árvore aprendeu foi '{perg[0]}': o corte horizontal separa a água (em baixo) do resto. A segunda, '{perg[1]}', é o corte vertical: à esquerda o solo, à direita a vegetação.

O gráfico fica dividido em CAIXAS. Cada caixa é uma folha da árvore: todos os píxeis que lá caem recebem a mesma resposta. É a 'fronteira' da árvore: feita de cortes direitos, como uma escada."

Ligação à prática: na Aula 1, a árvore aprende com os pontos da cheia de 2026 e as 5 bandas; escolhe uma só pergunta, «SWIR ≤ 0,04», e o notebook mostra-a."""
S["m2-arvore-caixas"] = slide("m2-arvore-caixas", "A árvore divide o espaço em caixas", linha(
    figura("ml_caixas", "Gráfico de pontos dos 24 píxeis com o espaço dividido em três caixas coloridas por dois cortes direitos", 800, 598,
           "24 píxeis reais (Sentinel-2, 23/10/2025) e as caixas de uma árvore com 2 perguntas."),
    coluna(p("24 píxeis reais, só com duas pistas: NIR e SWIR."),
           p(f"Cada pergunta é um <b>corte direito</b>: primeiro <b>{perg[0]}</b>, depois <b>{perg[1]}</b>."),
           destaque("Cada caixa é uma folha da árvore: tudo o que lá cai recebe a mesma resposta."),
           gap=28, extra="flex:1"), gap=48))

votos = ["água", "água", "terra", "água", "água", "terra", "água"]
S["m2-floresta"] = slide("m2-floresta", "Random Forest: muitas árvores a votar", coluna(
    p("Um Random Forest (“floresta aleatória”) junta muitas árvores de decisão. Cada árvore vota no mesmo píxel:"),
    B.tabela(["Árvore"] + [str(i) for i in range(1, 8)], [["Voto"] + votos], [16] + [12] * 7, tam=30,
             alinh=["left"] + ["center"] * 7),
    destaque("5 votos “água” contra 2 votos “terra”: a decisão é ÁGUA. Probabilidade de ser água = 5 ÷ 7 = 0,71."),
    gap=40))

S["m2-floresta-porque"] = slide("m2-floresta-porque", "Porque é que a floresta erra menos", coluna(
    linha(bloco("Aleatória", "Cada árvore aprende com uma parte diferente dos exemplos, escolhida ao acaso.", "flex:1", tam=30),
          bloco("Como um júri", "Um jurado pode errar; a maioria de muitos jurados raramente erra.", "flex:1", tam=30),
          gap=40, alinhar="stretch"),
    destaque("Na prática usamos 100 árvores: um número que nós escolhemos antes de treinar."), gap=48))

kv = TEORIA["knn_votos"]
S["m2-knn"] = slide("m2-knn", "k vizinhos mais próximos: diz-me com quem andas", linha(
    figura("ml_knn", "Gráfico dos 24 píxeis com um píxel novo em estrela, um círculo à volta dos seus 5 vizinhos mais próximos e linhas até eles", 640, 623,
           "24 píxeis reais e um píxel novo, com k = 5."),
    coluna(p("Para um píxel novo, o modelo procura os <b>k</b> exemplos mais parecidos: os mais perto no gráfico."),
           p(f"Aqui k = 5: <b>{kv.get('vegetação', 0)} são vegetação</b> e {kv.get('solo', 0)} são solo. Ganha a maioria: vegetação."),
           destaque("Com k = 1, segue um só vizinho e decora o ruído. O k também se escolhe com o exame."),
           gap=28, extra="flex:1"), gap=48))

NOTAS["m2-rede"] = """FACILITADOR 2, cerca de 1,5 minutos.

"A REDE NEURONAL inspira-se no cérebro. À esquerda entram as 8 pistas de um píxel. Cada círculo do meio é um 'neurónio': faz uma conta simples com os números que recebe e passa o resultado à camada seguinte. À direita sai a resposta: água ou não água.

Cada linha tem um PESO, um número. Treinar a rede é ajustar todos esses pesos, passo a passo, para o erro descer: é a mesma curva de treino que vimos com a recta, mas com centenas de números em vez de dois." """
S["m2-rede"] = slide("m2-rede", "Rede neuronal: neurónios ligados por pesos", linha(
    figura("ml_rede", "Diagrama de uma rede neuronal: 8 pistas à esquerda, duas camadas escondidas de neurónios ao meio e a resposta água ou não água à direita", 1000, 580,
           "Uma rede neuronal pequena, como a da prática (desenhada com 6 + 6 neurónios).", borda=False),
    coluna(p("Cada neurónio faz uma conta simples e passa o resultado à camada seguinte."),
           p("Cada ligação tem um <b>peso</b>. Treinar é ajustar os pesos, passo a passo, para o erro descer."),
           gap=32, extra="flex:1"), gap=48))

NOTAS["m2-deep-learning"] = f"""FACILITADOR 2, cerca de 1,5 minutos.

"Com MUITAS camadas, a rede neuronal chama-se DEEP LEARNING (aprendizagem profunda). É o que reconhece caras, vozes, traduz e está no ChatGPT, treinado com milhões de exemplos.

O perigo: com poucos exemplos, a rede pode aprender uma regra frágil. Na prática, a rede treinada só com a cheia de 2026 tem uma nota excelente nesse exame (IoU {fmt(rede['IoU'], 2)}), mas em 2024, com água muito escura, encontra {fmt(rede['rio_2024'])}% do rio."

A solução, nos testes da equipa: com exemplos de todos os anos, a rede passa a encontrar o rio de 2024."""
S["m2-deep-learning"] = slide("m2-deep-learning", "Muitas camadas: o Deep Learning", coluna(
    linha(*[bloco(t, d, "flex:1", tam=28) for t, d in [("Caras", "o desbloqueio facial"), ("Vozes", "os assistentes de voz"),
                                                        ("Línguas", "os tradutores"), ("Texto", "o ChatGPT")]],
          gap=24, alinhar="stretch"),
    p("Redes com muitas camadas aprendem com <b>milhões</b> de exemplos."),
    caixa("Cuidado", p(f"Com poucos exemplos, a rede aprende uma regra frágil: a da prática, treinada só com a cheia de 2026, "
                       f"encontra {fmt(rede['rio_2024'])}% do rio de 2024."), LARANJA, LARANJA_CX), gap=36))

pixeis = [["1", "0,030", "0,016", "água"], ["2", "0,011", "0,013", "água"], ["3", "0,037", "0,016", "água"],
          ["4", "0,342", "0,199", "vegetação"], ["5", "0,381", "0,212", "vegetação"], ["6", "0,313", "0,172", "vegetação"],
          ["7", "0,193", "0,369", "solo"], ["8", "0,251", "0,428", "solo"]]
S["m2-actividade"] = slide("m2-actividade", "Actividade: sejam uma árvore de decisão", linha(
    coluna(p("6 minutos, em pares.", 30, SUAVE),
           lista(["Escrevam 2 perguntas de sim ou não, com números, que separem água, vegetação e solo.",
                  "Testem as perguntas nos 8 píxeis."], num=True), gap=24, extra="flex:1"),
    B.tabela(["Píxel", "NIR", "SWIR", "Rótulo"], pixeis, [18, 24, 24, 34], tam=28,
             alinh=["center", "center", "center", "left"], largura=700), gap=56))

S["m2-actividade-votar"] = slide("m2-actividade-votar", "Actividade: a turma é uma floresta", linha(
    coluna(lista(["Usem as vossas perguntas nos píxeis X e Y, que ninguém marcou.",
                  "Cada par vota: X é água, vegetação ou solo? E Y?",
                  "Contamos os votos: ganha a maioria, como no Random Forest."]), gap=24, extra="flex:1"),
    B.tabela(["Píxel", "NIR", "SWIR", "Rótulo"], [["X", "0,048", "0,010", "?"], ["Y", "0,164", "0,317", "?"]],
             [18, 24, 24, 34], tam=30, alinh=["center", "center", "center", "left"], largura=700), gap=56, alinhar="center"))

# ============================== QUIZ (09:55–10:05) ==============================


def cartao(letra):
    return (f'<div style="flex:1;border:3px solid {ACENTO};padding:32px;display:flex;justify-content:center">'
            f'<p style="font-family:{TITULO};font-size:120px;line-height:1;color:{ACENTO}">{letra}</p></div>')


S["quiz"] = slide("quiz", "Quiz relâmpago", coluna(
    lead("5 perguntas sobre os Módulos 1 e 2, em pares."),
    linha(*[cartao(letra) for letra in "ABC"], gap=48),
    p("Contamos até 5 e todos levantam o cartão ao mesmo tempo. Um ponto por resposta certa; o par vencedor é "
      "anunciado no encerramento.", 30, SUAVE), gap=40))

QUIZ = [("Na aprendizagem supervisionada, o computador aprende com…",
         ["regras escritas por uma pessoa", "exemplos com a resposta certa", "grupos que encontra sozinho"],
         "B", "Aprende com exemplos e com as respostas certas: os rótulos."),
        ("Prever o caudal do rio daqui a 3 dias é…", ["classificação", "regressão", "agrupamento"],
         "B", "A resposta é um número (m³/s): regressão."),
        ("Os mapas oficiais da cheia, usados para treinar os nossos modelos, são…", ["as pistas", "os rótulos", "o algoritmo"],
         "B", "São as respostas certas, marcadas por especialistas: aprendizagem supervisionada."),
        ("Um scanner que marca as malas como “arma” ou “sem arma” faz…", ["classificação", "regressão", "agrupamento"],
         "A", "A resposta é uma categoria e há malas marcadas por pessoas: classificação."),
        ("Nos k vizinhos com k = 5, um píxel tem 4 vizinhos “água” e 1 “terra”. O modelo diz…",
         ["água", "terra", "não decide"], "A", "Ganha a maioria dos vizinhos: 4 contra 1.")]


def opcao(letra, texto):
    return (f'<div style="flex:1;border:2px solid {LINHA};padding:24px 28px;display:flex;flex-direction:row;gap:24px;align-items:center">'
            f'<p style="font-family:{TITULO};font-size:56px;line-height:1;color:{ACENTO}">{letra}</p>' + p(texto, 30) + "</div>")


for n, (pergunta, opcoes, certa, porque) in enumerate(QUIZ, start=1):
    resposta = revelar(p(f"Resposta: {certa}) {opcoes['ABC'.index(certa)]}", 36, ACENTO, 700) + p(porque), 640)
    S[f"quiz-{n}"] = slide(f"quiz-{n}", f"Quiz: pergunta {n} de 5", coluna(
        lead(pergunta, TINTA, 700), linha(*[opcao(l, t) for l, t in zip("ABC", opcoes)], gap=24, alinhar="stretch"), gap=48),
        extra_fim=resposta)

# ============================== MÓDULO 3 (10:05–10:35) ==============================
S["m3"] = divisoria("m3", "Módulo 3", "Como sabemos se o modelo é bom?", "10:05–10:35 | Facilitador 5",
                    pergunta_abertura("Como é que um professor sabe se um aluno aprendeu a matéria, ou se só decorou as respostas?"))


def passo_fluxo(n, titulo, texto):
    return (f'<div style="flex:1;background:{CAIXA};border-top:6px solid {ACENTO};padding:18px 20px;display:flex;flex-direction:column;gap:6px">'
            + p(f"Passo {n}", 24, SUAVE, 700) + h3(titulo, ACENTO, 28) + p(texto, 26) + "</div>")


passos = [("Pergunta", "O que queremos prever?"), ("Dados", "Imagens, séries, tabelas."), ("Rótulos", "As respostas certas (só na supervisionada)."),
          ("Características", "As pistas de cada exemplo."), ("Dividir", "Treino de um lado, teste do outro."),
          ("Treinar", "modelo.fit(X, y)"), ("Avaliar", "As notas no teste."), ("Usar", "modelo.predict(X_novo)")]


def fila(itens, inicio):
    filhos = []
    for i, (t, d) in enumerate(itens):
        if i:
            filhos.append(seta(36, 22, SUAVE))
        filhos.append(passo_fluxo(inicio + i, t, d))
    return linha(*filhos, gap=10, alinhar="stretch")


S["m3-fluxo"] = slide("m3-fluxo", "O caminho completo do treino", coluna(
    fila(passos[:4], 1), fila(passos[4:], 5),
    destaque("Se a nota do teste for má, volta-se atrás: mais exemplos, outras pistas, outro algoritmo."), gap=28))

S["m3-divisao"] = slide("m3-divisao", "Treino e teste: estudar e fazer o exame", coluna(
    linha(p("Treino, cerca de 70%: o modelo aprende", 28, BRANCO, 700, f"flex:70;background:{SERIE_TREINO};padding:20px 24px"),
          p("Teste, cerca de 30%: fechado à chave", 28, BRANCO, 700, f"flex:30;background:{SERIE_TESTE};padding:20px 24px"), gap=4),
    linha(caixa("Treino = estudar", p("Os exemplos com rótulo. O modelo aprende com eles.") + codigo("modelo.fit(X, y)"),
                extra="flex:1;gap:16px"),
          caixa("Teste = o exame", p("Dados que o modelo NUNCA viu. Servem só para dar a nota.") + codigo("modelo.predict(X_teste)"),
                extra="flex:1;gap:16px"), gap=40, alinhar="stretch"), gap=40))

S["m3-futuro"] = slide("m3-futuro", "Quando o tempo importa, o exame é o futuro", coluna(
    coluna(linha(p("Treino: 2006–2018", 30, BRANCO, 700, f"flex:13;background:{SERIE_TREINO};padding:24px"),
                 p("Exame: 2019–2026", 30, BRANCO, 700, f"flex:8;background:{SERIE_TESTE};padding:24px"), gap=4),
           linha(p("2006", 26, SUAVE), p("2026", 26, SUAVE), extra="justify-content:space-between"), gap=8),
    p("Na previsão do caudal (Aula 4), o modelo aprende com o passado e é avaliado com anos que nunca viu, "
      "incluindo a cheia de 2026."),
    destaque("Misturar os dias ao acaso seria copiar: um dia e o seguinte são quase iguais."), gap=40))

S["m3-rotulos"] = slide("m3-rotulos", "No nosso rio: os rótulos são pontos marcados", linha(
    coluna(p("Uma pessoa olha para a imagem e marca pontos: <b>círculos azuis = água</b>, <b>quadrados laranja = não "
             "água</b>. Cada ponto vale 25 píxeis à sua volta."),
           caixa("Bons rótulos são variados", p("Água barrenta, rio, lagoa escura. Mato, campos, areia, vila. "
                                                 "Longe das nuvens e das bordas.", 28)),
           destaque("Rótulos errados ensinam coisas erradas."), gap=32, extra="flex:1"),
    figura("rotulos", "A imagem da cheia de 24 de Janeiro de 2026 com 15 círculos azuis na água e 15 quadrados laranja em terra",
           384, 580, "Os 15 + 15 pontos da equipa na imagem da cheia (24/01/2026).", SENTINEL), gap=56))

S["m3-regra-de-ouro"] = slide("m3-regra-de-ouro", "Regra de ouro: um exame independente", linha(
    coluna(lead("Nunca dar a nota com rótulos feitos pelo próprio modelo.", ACENTO, 700),
           p("O nosso exame: as amostras da cheia de Janeiro de 2026 do <b>Copernicus EMS</b>, o serviço europeu de mapas "
             "de emergência. O modelo nunca as viu."),
           p("<b>Azul</b> = água; <b>laranja</b> = não água.", 28, SUAVE), gap=32, extra="flex:1"),
    figura("exame", "A imagem da cheia esbatida, com as amostras do exame Copernicus EMS: água a azul e não água a laranja",
           384, 580, "As amostras do exame sobre a imagem da cheia.", "Copernicus EMS (EMSR857) e JRC Global Surface Water"),
    gap=56))

S["m3-exame-erro"] = slide("m3-exame-erro", "Até o exame tinha um erro", coluna(
    linha(caixa("O problema", p("O EMS só marca a água da cheia, não o rio de sempre: algumas amostras de “não água” "
                                "estavam em cima do rio."), LARANJA, LARANJA_CX, "flex:1"),
          caixa("A correcção", p("Juntámos 38 anos de água vista pelo Landsat (arquivo JRC): o rio de sempre passou a "
                                 "contar como água."), extra="flex:1"), gap=40, alinhar="stretch"),
    destaque("Um exame também pode errar. Quando o modelo e o exame discordam, vale a pena ir ver quem tem razão."), gap=48))


def celula(texto, fundo=CAB_TABELA, cor=BRANCO):
    return f'<div style="background:{fundo};padding:16px 20px;display:flex;align-items:center">' + p(texto, 28, cor, 700) + "</div>"


def resultado(nome, valor, certo):
    fundo, cor = (REALCE, PRETO) if certo else (ERRO_FUNDO, ACENTO)
    return (f'<div style="background:{fundo};padding:20px 24px;display:flex;flex-direction:column;gap:6px">'
            + p(nome, 28, TINTA, 700) + p(valor, 40, cor, 700) + "</div>")


matriz = ('<div style="display:grid;grid-template-columns:220px 1fr 1fr;gap:6px">'
          + f'<div style="background:{BRANCO}"></div>' + celula("O modelo disse água") + celula("O modelo disse terra")
          + celula("Era água") + resultado("Água certa", f"242{NB}297", True) + resultado("Água perdida", f"9{NB}657", False)
          + celula("Era terra") + resultado("Falso alarme", "29", False) + resultado("Terra certa", f"87{NB}426", True)
          + "</div>")
S["m3-matriz"] = slide("m3-matriz", "A matriz de confusão: os quatro resultados", linha(
    coluna(matriz, p("Píxeis do exame da cheia de 2026. A cinzento, os acertos; a vermelho, os erros. O erro que conta é a "
                     "água perdida, nas bordas da cheia.", 28), gap=28, extra="flex:1"),
    figura("erros", "Mapa dos erros do modelo no exame: quase tudo azul (água certa), com pouca água perdida nas bordas",
           384, 580, "Os erros no exame: azul, água certa; cinzento, terra certa; laranja, água perdida; vermelho, falso alarme."),
    gap=56))

S["m3-notas"] = slide("m3-notas", "Cinco notas, em palavras simples", coluna(
    B.tabela(["Nota", "Valor", "O que quer dizer"],
             [["Acerto", fmt(ems["acerto"], 2), f"{round(100 * ems['acerto'])} em cada 100 píxeis certos"],
              ["IoU", fmt(ems["IoU"], 2), "quanto os mapas coincidem"],
              ["F1", fmt(ems["F1"], 2), "poucos falsos alarmes e pouca água perdida"],
              ["Kappa", fmt(ems["Kappa"], 2), "acerto acima da sorte (0 = moeda ao ar)"],
              ["ROC-AUC", fmt(ems["ROC-AUC"], 2), "a água recebe notas mais altas do que a terra"]],
             [20, 14, 66], tam=30, alinh=["left", "center", "left"]),
    legenda("O modelo da equipa (Random Forest, 100 árvores) no exame da cheia de 2026 (Copernicus EMS).", tipo="Tabela"), gap=10))

venn = ('<div style="position:relative;width:800px;height:560px">'
        '<x-shape kind="ellipse" style="position:absolute;left:40px;top:80px;width:440px;height:440px;background:#555555;opacity:0.35"></x-shape>'
        '<x-shape kind="ellipse" style="position:absolute;left:320px;top:80px;width:440px;height:440px;background:#A51C30;opacity:0.35"></x-shape>'
        '<p style="position:absolute;left:20px;top:0px;width:360px;font-size:30px;font-weight:700;color:#555555">Previsto: 80 ha</p>'
        f'<p style="position:absolute;left:440px;top:0px;width:360px;font-size:30px;font-weight:700;color:{ACENTO};text-align:right">Verdade: 100 ha</p>'
        f'<p style="position:absolute;left:330px;top:270px;width:140px;font-size:40px;font-weight:700;color:{TINTA};text-align:center">70</p>'
        "</div>")
S["m3-iou"] = slide("m3-iou", "IoU: quanto os dois mapas coincidem", linha(
    venn, coluna(caixa(None, p("IoU = intersecção ÷ união", 30, ACENTO, 700) + p("= 70 ÷ (80 + 100 − 70)") + p("= 70 ÷ 110 = <b>0,64</b>")),
                 p("1 = os dois mapas são iguais. 0 = não se tocam."),
                 p(f"O modelo da equipa no exame da cheia: <b>IoU {fmt(ems['IoU'], 2)}</b>."),
                 gap=28, extra="flex:1"), gap=64, alinhar="center"))

NOTAS["m3-notas-regressao"] = f"""FACILITADOR 5, cerca de 1 minuto.

"Na regressão a resposta é um número, por isso não há 'certo' ou 'errado': há erros maiores ou menores. Duas notas:
- ERRO MÉDIO (MAE, em inglês): em média, quanto a previsão falha, nas unidades da resposta (m³/s). Quanto menor, melhor.
- R²: quanto do sobe e desce do rio o modelo explica: 1 = tudo, 0 = nada. Os hidrólogos chamam-lhe NSE.

A recta da Aula 4 erra em média {fmt(rg['linear']['MAE'])} m³/s no exame (R² {fmt(rg['linear']['R2'], 2)}). Dizer 'daqui a 3 dias fica igual a hoje' erra {fmt(rg['igual_a_hoje']['MAE'])} m³/s: um modelo só vale a pena se ganhar a esta resposta simples." """
S["m3-notas-regressao"] = slide("m3-notas-regressao", "E na regressão? Outras notas", coluna(
    linha(caixa("Erro médio (MAE)", p("Em média, quanto a previsão falha, nas unidades da resposta (m³/s).")
                + p("Quanto menor, melhor.", 30, ACENTO, 700), extra="flex:1"),
          caixa("R²", p("Quanto do sobe e desce do rio o modelo explica.") + p("1 = tudo; 0 = nada.", 30, ACENTO, 700),
                extra="flex:1"), gap=40, alinhar="stretch"),
    destaque(f"A recta da Aula 4, no exame 2019–2026: erro médio de {fmt(rg['linear']['MAE'])} m³/s e R² de "
             f"{fmt(rg['linear']['R2'], 2)}."), gap=48))

S["m3-ajuste"] = slide("m3-ajuste", "Subajuste, bom ajuste e sobreajuste", coluna(
    coluna(imagem("ml_ajuste", "Três gráficos com os mesmos pontos: uma recta que não os acompanha, uma curva suave que segue a forma, e uma curva louca que passa por todos", 1664, 498, False),
           legenda("Os mesmos 16 pontos e três modelos, do mais simples ao mais complexo (dados inventados)."), gap=10),
    linha(p("Simples demais: erra nos exemplos e nos casos novos.", 28, extra="flex:1"),
          p("Apanha a forma geral: erra pouco nos casos novos.", 28, extra="flex:1"),
          p("Passa por todos os pontos, até pelo ruído: erra muito nos casos novos.", 28, extra="flex:1"), gap=48),
    gap=20))

NOTAS["m3-complexidade"] = f"""FACILITADOR 5, cerca de 2,5 minutos. Um dos gráficos mais importantes de todo o Machine Learning.

"No eixo horizontal, a complexidade do modelo: aqui, a profundidade de uma árvore (quantas perguntas seguidas). Duas curvas:
- O erro no TREINO (preto) desce sempre: quanto mais complexo, mais o modelo decora os exemplos, até chegar a zero.
- O erro no TESTE (vermelho) desce até um ponto, o BOM AJUSTE (aqui, {TEORIA['grau_melhor']} perguntas), e depois volta a subir: o modelo começou a decorar o ruído do treino.

Conclusão: escolhe-se a complexidade com o erro no TESTE, nunca com o erro no treino. Se olhássemos só para o treino, escolhíamos sempre o modelo mais complexo, que é o pior."

Na Aula 4 da prática, os pares fazem o mesmo com o caudal real do Incomáti (erro médio, em m³/s): a melhor profundidade é {AR['a4_melhor_profundidade']} (erro no teste {fmt(AR['a4_profundidades'][str(AR['a4_melhor_profundidade'])]['teste'], 1)}); com 20 perguntas, o erro no treino cai para {fmt(AR['a4_profundidades']['20']['treino'], 1)} e no teste sobe para {fmt(AR['a4_profundidades']['20']['teste'], 1)}."""
S["m3-complexidade"] = slide("m3-complexidade", "Mais complexo não é sempre melhor", linha(
    figura("ml_complex", "Gráfico: o erro no treino desce sempre com a profundidade da árvore; o erro no teste desce até 3 e depois sobe", 1000, 592,
           "Árvores de regressão em dados inventados (média de 200 amostras)."),
    coluna(p("No <b>treino</b>, o erro desce sempre: o modelo decora cada vez mais."),
           p("No <b>teste</b>, desce até ao bom ajuste e depois sobe: é o sobreajuste."),
           destaque("Escolhe-se a complexidade com o erro no teste, nunca com o do treino."), gap=28, extra="flex:1"), gap=48))

S["m3-hiperparametros"] = slide("m3-hiperparametros", "Hiperparâmetros: os botões que nós escolhemos", coluna(
    B.tabela(["Algoritmo", "Hiperparâmetro", "Na prática"],
             [["Random Forest", "o número de árvores e a profundidade", "100; sem limite"],
              ["k vizinhos", "k, o número de vizinhos", "5"],
              ["Árvore de decisão", "a profundidade: quantas perguntas seguidas", "1 a 20"],
              ["Todos os classificadores", "o limiar: a partir de que probabilidade é água", "0,5"]],
             [28, 50, 22], tam=30, alinh=["left", "left", "center"]),
    destaque("Escolhem-se com o exame, nunca com o treino. Na prática: o número de árvores e a profundidade."),
    gap=40))

S["m3-decorar"] = slide("m3-decorar", "Decorar não é aprender", coluna(
    linha(numero_grande("100%", "de acerto nos exemplos que o modelo estudou (treino)"),
          numero_grande(f"{round(100 * ems['acerto'])}%", "de acerto no exame, com mapas da cheia que nunca viu",
                        f"border-left:2px solid {LINHA};padding:0 0 0 56px"),
          gap=56, alinhar="stretch"),
    destaque("Se um modelo só acerta no que já viu, decorou: os cientistas chamam-lhe sobreajuste (em inglês, "
             "overfitting). A nota que conta é a do exame."), gap=56))

S["m3-verificacao"] = slide("m3-verificacao", "Pergunta de verificação",
                            lead("Um modelo acerta 100% nos exemplos que estudou. <b>Está pronto para usar?</b>"), gap=48,
                            extra_fim=revelar(p("Resposta: ainda não! Tem de passar no exame, com dados que nunca viu e "
                                                "rótulos independentes.", 30, ACENTO, 700), 460))

# ============================== MÓDULO 4 (10:35–11:00) ==============================
S["m4"] = divisoria("m4", "Módulo 4", "A IA e a qualidade da água", "10:35–11:00 | Facilitador 3",
                    pergunta_abertura("Depois da cheia, o rio ficou castanho. O que é que essa cor nos diz sobre a água?"))
S["m4-o-que-ve"] = slide("m4-o-que-ve", "O que o satélite consegue ver na água", coluna(
    B.tabela(["O que vê", "Como", "No Incomáti"],
             [["Turbidez e sedimentos", "A água barrenta reflecte mais vermelho", "Vê bem"],
              ["Clorofila-a (algas)", "Os tons verdes da água", "Com cuidado: a lama engana"],
              ["Plantas flutuantes", "Jacintos-de-água em cima do rio", "Vê, nos troços largos"],
              ["Temperatura", "A banda térmica do Landsat", "Vê, em píxeis de 100 m"]], [28, 40, 32], tam=30),
    destaque("O satélite vê a cor e a temperatura da superfície. O resto mede-se no terreno."), gap=40))
S["m4-cor"] = slide("m4-cor", "A cor da água conta uma história", coluna(
    linha(figura("foz_seca", "A foz do Incomáti e o mar na época seca: a água do rio é escura e limpa", 800, 377,
                 "A foz do Incomáti na época seca (23/10/2025).", SENTINEL),
          figura("foz_cheia", "A foz do Incomáti na cheia: uma enorme mancha de água castanha entra no mar", 800, 377,
                 "A mesma zona na cheia (24/01/2026): a água barrenta entra no mar.", SENTINEL), gap=64),
    caixa("Índice de turbidez", p("NDTI = (Vermelho − Verde) ÷ (Vermelho + Verde)", 30, TINTA, 700)
          + p("Mais vermelho → mais sedimentos → água mais barrenta.")), gap=32))
S["m4-trocos"] = slide("m4-trocos", "Os 9 troços do rio, da fronteira à foz", linha(
    figura("trocos", "Mapa da bacia do Incomáti em Moçambique com o rio dividido em 9 troços coloridos, de Q1 a Q9", 868, 620,
           "Os 9 troços do Incomáti em Moçambique, de Ressano Garcia (Q1) à foz (Q9). A laranja, o distrito de Marracuene.", "projecto ETE"),
    coluna(lista(["Cerca de 37 km cada, de Ressano Garcia (Q1) à foz (Q9). <b>Q8 = Marracuene.</b>",
                  "Todos os meses desde 2006: a cor da água, as plantas e a temperatura.",
                  "Cada troço compara-se com o seu próprio normal."], 30),
           extra="flex:1"), gap=48))
S["m4-anomalias"] = slide("m4-anomalias", "Anomalias: quando o rio sai do normal", figura(
    "ndti", "Gráfico de barras de 2006 a 2026 do troço de Marracuene: barras castanhas quando a água esteve mais barrenta "
            "do que o normal e azuis quando esteve mais limpa", 1560, 624,
    "Anomalia mensal da turbidez (NDTI) no troço de Marracuene (Q8), 2006–2026. Castanho: água mais barrenta do que o normal "
    "desse mês; azul: mais limpa.", "Landsat e Sentinel-2, processamento do projecto ETE"))
NOTAS["m4-ia-turbidez"] = f"""FACILITADOR 3, cerca de 3 minutos. Este slide responde à pergunta do plano: "aplicação da IA na turbidez".

"Tentámos ensinar uma floresta aleatória a prever as manhãs em que a água está mais barrenta do que o normal, com o caudal do rio, a chuva e o mês. Parece lógico: depois da chuva, o rio traz terra. Treinámos com 2017 a 2022 e testámos com 2023 a 2026. Resultado: {fmt(100 * AR['a3_nota_sem_mare'], 1)} %, menos do que dizer sempre «turva» ({fmt(100 * AR['a3_sempre_turva'], 1)} %). Mais árvores não resolvem.

Porquê? Faltava a pista principal: a maré. Perto da foz, o mar sobe e desce duas vezes por dia. Com a maré alta entra água do mar, mais limpa; com a maré baixa sai a água barrenta do rio. Quando juntámos a altura da maré à hora do satélite, o acerto subiu para {fmt(100 * AR['p3_nota_com_mare'], 1)} %. No projecto, o modelo final (com a maré e a última medição do satélite) chega a ROC-AUC 0,88, e a plataforma usa-o para dar a probabilidade de água barrenta nos próximos 10 dias."

Lição: a escolha das pistas vale mais do que o algoritmo. Na prática, no Tema 3, os pares fazem isto com as próprias mãos.

Ligação ao Módulo 2: é uma CLASSIFICAÇÃO (a manhã é ou não mais barrenta do que o normal)."""
S["m4-ia-turbidez"] = slide("m4-ia-turbidez", "A IA consegue prever a água barrenta?", coluna(
    coluna(B.tabela(["Random Forest com…", "Acerto em 2023–2026"],
                    [["o caudal, a chuva e o mês", f"{fmt(100 * AR['a3_nota_sem_mare'], 1)} %"],
                     ["as mesmas e a maré", f"{fmt(100 * AR['p3_nota_com_mare'], 1)} %"],
                     ["nenhum modelo: dizer sempre «turva»", f"{fmt(100 * AR['a3_sempre_turva'], 1)} %"]],
                    [62, 38], tam=30, alinh=["left", "center"]),
           legenda("Manhãs de 2023 a 2026, que o modelo nunca viu (3 troços do rio, Sentinel-2). No Tema 3 da prática, "
                   "fazem isto vocês.", "projecto ETE", tipo="Tabela"), gap=10),
    destaque("A IA não faz milagres: precisa das pistas certas."), gap=40))


def rotulo_caixa(texto):
    return (f'<div style="flex:1;border:2px solid {ACENTO};padding:28px 16px;display:flex;justify-content:center">'
            + p(texto, 30, ACENTO, 700, "text-align:center") + "</div>")


S["m4-nao-mede"] = slide("m4-nao-mede", "O que o satélite NÃO mede", coluna(
    linha(*[rotulo_caixa(t) for t in ["pH", "Oxigénio", "Nutrientes", "Metais", "Bactérias"]], gap=24),
    lead("Por isso, a plataforma nunca diz que a água é “própria para beber”.", ACENTO, 700),
    caixa("Atenção", p("A água do rio deve ser sempre fervida ou tratada com cloro (Certeza) antes de beber."), LARANJA, LARANJA_CX), gap=48))
S["m4-actividade"] = slide("m4-actividade", "Actividade: verdade ou mito?", coluna(
    p("5 minutos, em pares. Escrevam V (verdade) ou M (mito).", 30, SUAVE),
    B.tabela(["Afirmação", "V ou M?"],
             [["1. O satélite consegue ver quando o rio fica mais barrento.", ""], ["2. Se a turbidez está normal, a água é boa para beber.", ""],
              ["3. O satélite mede as bactérias da água.", ""], ["4. Cada troço do rio deve ser comparado com o seu próprio normal.", ""],
              ["5. Com mais árvores, a IA acerta sempre, mesmo sem as pistas certas.", ""], ["6. As nuvens podem impedir a medição da água nesse dia.", ""]],
             [80, 20], tam=30), gap=28))

# ============================== MÓDULO 5 (11:00–11:20) ==============================
S["m5"] = divisoria("m5", "Módulo 5", "A plataforma EYES TO EARTH: do dado ao alerta", "11:00–11:20 | Facilitador 4",
                    pergunta_abertura("Se o rio vai encher daqui a 4 dias, como avisamos quem vive na planície?"))


def etapa(n, titulo, texto):
    return (f'<div style="flex:1;background:{CAIXA};border-top:6px solid {ACENTO};padding:20px;display:flex;flex-direction:column;gap:8px">'
            + p(f"Passo {n}", 24, SUAVE, 700) + h3(titulo, ACENTO, 28) + p(texto, 28) + "</div>")


etapas = [("Satélites", "Onde está a água hoje"), ("Previsões", "Chuva e caudal para 10 dias"),
          ("Modelos e regras", "Comparam com 20 anos do rio"), ("Nível de alerta", "Verde, amarelo, laranja ou vermelho"),
          ("Avisos", "Na página e por WhatsApp")]
fluxo = []
for i, (t, d) in enumerate(etapas, start=1):
    if i > 1:
        fluxo.append(seta(40, 24, SUAVE))
    fluxo.append(etapa(i, t, d))
S["m5-dado-alerta"] = slide("m5-dado-alerta", "Do dado ao alerta, em cinco passos", coluna(
    linha(*fluxo, gap=10, alinhar="center"),
    p("Quantidade (cheias) e qualidade (cor da água) usam os mesmos satélites. O sistema corre sozinho, todas as manhãs."),
    gap=48))
S["m5-gatilhos"] = slide("m5-gatilhos", "Os gatilhos: o caudal do rio e a chuva", coluna(
    linha(figura("caudal", "Gráfico do caudal do Incomáti entre Dezembro de 2025 e Fevereiro de 2026, com o pico de 2987 m³/s a 19 de Janeiro "
                 "e as linhas dos limites amarelo, laranja e vermelho", 1000, 437,
                 "Caudal diário em Marracuene, de Dezembro de 2025 a Fevereiro de 2026, e os limites de alerta.",
                 "GloFAS (Copernicus)"),
          coluna(h3("Limites de caudal"), lista(["Amarelo: acima de 164 m³/s", "Laranja: acima de 376 m³/s", "Vermelho: acima de 970 m³/s"], 28),
                 h3("Chuva anómala"), p("Chuva de 7 dias muito acima do normal.", 28), gap=12, extra="flex:1"), gap=48),
    destaque("Em Janeiro de 2026: alerta laranja 4 a 5 dias antes do primeiro mapa da cheia."), gap=28))
S["m5-niveis"] = slide("m5-niveis", "Os quatro níveis de alerta", coluna(
    B.tabela(["Nível", "Significado", "Caudal do rio", "O que fazer"],
             [["Verde", "Rio normal", "abaixo de 164 m³/s", "Siga a informação."],
              ["Amarelo", "Atenção", "acima de 164 m³/s", "Fique atento: o rio está a subir."],
              ["Laranja", "Cheia provável", "acima de 376 m³/s", "Prepare-se para sair; proteja os documentos."],
              ["Vermelho", "Cheia grave", "acima de 970 m³/s", "Siga as autoridades; vá para zonas altas."]],
             [15, 21, 24, 40], tam=28, cores=["#E8F3EA", "#FFF6D6", "#FDEBD9", "#FADBD8"]),
    destaque("O WhatsApp só envia mensagens em laranja ou vermelho: quem recebe sabe que é a sério."), gap=40))


def pagina(chave, alt, titulo, texto):
    return coluna(imagem(chave, alt, 520, 292), h3(titulo, ACENTO, 30), p(texto, 28), gap=10, extra="flex:1")


S["m5-paginas"] = slide("m5-paginas", "Quantidade, qualidade e alertas", coluna(
    linha(pagina("p_cheias", "Página Cheias da plataforma: o gráfico da previsão do caudal para 10 dias", "Cheias",
                 "O caudal previsto para 10 dias."),
          pagina("p_agua", "Página Qualidade da água da plataforma: indicadores dos troços do rio", "Qualidade da água",
                 "A cor da água nos 9 troços."),
          pagina("p_alertas", "Página Alertas da plataforma: inscrição para receber avisos no WhatsApp", "Alertas",
                 "Receber avisos no WhatsApp."), gap=52),
    p("E ainda: o Início, a pesquisa com uma página para cada lugar, e O projecto. Em português, inglês e francês.", 28),
    legenda("Três páginas da plataforma EYES TO EARTH (capturas de ecrã)."), gap=24))
S["m5-demo"] = slide("m5-demo", "Demonstração da plataforma", linha(
    figura("p_inicio", "Página de início da plataforma Eyes to Earth, com a saudação e o alerta de hoje", 1000, 562,
           "A página de início da plataforma EYES TO EARTH."),
    coluna(p("Demonstração ao vivo, 5 minutos.", 28, SUAVE),
           p("ete-platform.streamlit.app", 30, ACENTO, 700, f"border:2px solid {ACENTO};padding:14px 20px"),
           lista(["<b>Início:</b> o alerta de hoje", "<b>Cheias:</b> os próximos 10 dias", "<b>Mapa:</b> onde a água chega primeiro",
                  "<b>Qualidade da água:</b> os 9 troços", "<b>Alertas:</b> receber avisos no WhatsApp"], 28, num=True),
           gap=24, extra="flex:1"), gap=48))
S["m5-oficiais"] = slide("m5-oficiais", "Para nunca esquecer", coluna(
    lead("Os alertas da plataforma <b>complementam</b> os avisos oficiais. <b>Não os substituem.</b>", ACENTO),
    caixa("Em caso de cheia", p("Sigam sempre o INGD, a ARA-Sul, a administração do distrito e a rádio comunitária."),
          LARANJA, LARANJA_CX), gap=48))
S["m5-actividade"] = slide("m5-actividade", "Actividade: que alerta daria?", coluna(
    p("4 minutos, em pares. Limites: amarelo 164, laranja 376 e vermelho 970 m³/s.", 30, SUAVE),
    B.tabela(["Cenário", "Maior caudal previsto para os próximos dias", "O vosso alerta"],
             [["A", "120 m³/s", ""], ["B", "250 m³/s", ""], ["C", "600 m³/s", ""], ["D", f"1{NB}500 m³/s", ""],
              ["E", "300 m³/s, mas o máximo provável é 450 m³/s", ""]], [14, 56, 30], tam=30, alinh=["center", "left", "left"]), gap=28))

# ============================== INTERVALO E PRÁTICA (11:20–13:25) ==============================
S["intervalo"] = divisoria("intervalo", "Intervalo, 11:20–11:40", "Matabicho", None, caixa(
    "Antes de voltar, em cada par:", lista(["Portátil ligado ao carregador.", "Jupyter Notebook aberto na pasta <b>Workshop_2/2_pratica</b>.",
                                            "Notebook <b>1_Aula_ensinar_com_exemplos</b> aberto."])))

TEMAS_PRATICA = [("Tema 1", "11:40", "Ensinar a máquina com exemplos"), ("Tema 2", "12:05", "Treinar e testar"),
                 ("Tema 3", "12:35", "A cor do rio e a maré"), ("Tema 4", "12:55", "Prever o caudal")]
NOTAS["pratica"] = """FACILITADOR 5 conduz a prática, das 11:40 às 13:25. Cada par tem um padrinho (Facilitadores 1, 2, 3, 4 e 7, dos Pares 1 a 5); o Facilitador 6 resolve os problemas técnicos.

"Agora vamos treinar, com os nossos dados, os modelos que vimos de manhã. São quatro temas. Em cada um, primeiro uma AULA GUIADA curta: eu mostro no projector e vocês acompanham. Depois a PRÁTICA: são vocês a escrever o código, sozinhos, num caso novo. Cada passo diz logo se está certo."

As versões resolvidas (aulas e práticas), com as notas para os facilitadores, os modelos treinados e as separações de treino e teste, estão em 0_facilitadores/aulas_resolvidas.

Regra dos padrinhos: o estudante é que escreve; o padrinho aponta e pergunta, mas não toca no teclado. Na prática, apontar para o passo igual da aula guiada."""
S["pratica"] = divisoria("pratica", "Prática em pares", "Treinar os nossos modelos", "11:40–13:25 | Facilitador 5 e equipa | Jupyter Notebook",
                         linha(*[coluna(p(a_, 30, ACENTO, 700), p(h_, 24, SUAVE), p(t_, 28), p("Aula guiada + prática", 24, SUAVE), gap=6,
                                        extra=f"flex:1;border-top:4px solid {ACENTO};padding:14px 0 0 0") for a_, h_, t_ in TEMAS_PRATICA], gap=20))

NOTAS["pratica-jupyter"] = """FACILITADOR 5, 2 minutos, no projector (11:40).

Mostrar no projector o Jupyter aberto na pasta 2_pratica e a Aula 1. Correr o Passo 1 com Shift + Enter e mostrar o [*] e depois o número.

Depois abrir a Prática 1 e mostrar como se trabalha: em cada passo há uma PISTA (linhas com #). Escreve-se o código por baixo (pode-se copiar a pista, tirar o # e trocar os ...), corre-se, e depois corre-se a célula de verificação: diz «Certo!», ou «Ainda não» com uma pista. Guardar com Ctrl + S.

Erros: ler sempre a última linha da mensagem vermelha. O mais comum é saltar uma célula: correr por ordem. Se o Python parar (Kernel died): menu Kernel, Restart Kernel and Run All Cells."""
S["pratica-jupyter"] = slide("pratica-jupyter", "Como trabalhar no Jupyter Notebook", coluna(
    grelha([caixa("1. Abrir", p("Jupyter Notebook, pasta Workshop_2 › 2_pratica, e o notebook do tema.", 28)),
            caixa("2. Na aula guiada", p("Shift + Enter, sempre por ordem. Acompanhem o projector.", 28)),
            caixa("3. Na prática", p("Escrevam o código por baixo da pista (#) e corram a verificação: «Certo!» ou «Ainda não».", 28)),
            caixa("4. Erro vermelho?", p("Leiam a última linha. Se nada resultar: Kernel › Restart Kernel and Run All Cells.", 28))]),
    destaque("Ctrl + S guarda o trabalho no computador."), gap=36))

NOTAS["pratica-aulas"] = """FACILITADOR 5, 1 minuto. Deixar este slide no projector enquanto os pares trabalham, quando não houver nada para mostrar.

Tempos-limite (o condutor avisa em voz alta): 11:50 Prática 1; 12:05 Aula 2; 12:17 Prática 2; 12:35 Aula 3; 12:43 Prática 3; 12:55 Aula 4; 13:05 Prática 4; 13:20 guardar e preparar a apresentação. Quem não acabar uma prática passa ao tema seguinte na mesma: a prática pode ser acabada em casa.

Cada aula guiada começa com uma tabela de palavras novas: lê-la em voz alta com a turma."""
S["pratica-aulas"] = slide("pratica-aulas", "Cada tema: aula guiada e prática", B.tabela(
    ["Tema", "Aula guiada", "Prática: vocês escrevem o código", "Modelo"],
    [["1", "11:40 · exemplos e rótulos", "11:50 · a água no vosso ano", "Classificação"],
     ["2", "12:05 · treino e teste", "12:17 · outra separação e o exame", "Classificação"],
     ["3", "12:35 · a cor do rio e a maré", "12:43 · juntar a maré ao modelo", "Classificação"],
     ["4", "12:55 · o caudal a 3 dias", "13:05 · o caudal a 7 dias", "Regressão"]],
    [9, 30, 40, 21], tam=28, alinh=["center", "left", "left", "left"]))

anos_p1 = AR["p1_anos"]
NOTAS["pratica-aula1"] = f"""FACILITADOR 5. Aula 1 às 11:40 (10 minutos, no projector) e Prática 1 às 11:50 (15 minutos, sozinhos).

Aula 1: "Vamos ensinar o computador a reconhecer a água. Não escrevemos a regra: damos-lhe exemplos com a resposta certa." Resultados: SWIR da água {fmt(AR['a1_swir_agua'], 3)} e da terra {fmt(AR['a1_swir_terra'], 3)}; a regra feita à mão (SWIR menor do que 0,10) acerta {fmt(100 * AR['a1_regra_010'], 1)} %; a árvore aprende «SWIR ≤ {fmt(AR['a1_limiar_arvore'], 2)} é água»; cerca de {fmt(AR['a1_ha_cheia'])} hectares de água na cheia.

Prática 1: cada par faz o mesmo com os pontos do seu ano e escreve as linhas da tabela, de X e y, do fit e do predict. A regra aprendida muda de ano para ano: """ + "; ".join(
    f"{a}: {v['banda'].upper()} ≤ {fmt(v['limite'], 3)}" for a, v in anos_p1.items()) + ". Respostas das perguntas: a (supervisionada) e b (a regra muda com a água)."
S["pratica-aula1"] = slide("pratica-aula1", "Tema 1: ensinar a máquina com exemplos", coluna(
    lista(["<b>Aula guiada.</b> A imagem da cheia, os exemplos com os rótulos, a nossa regra e a árvore que aprende sozinha.",
           "<b>Prática, sozinhos.</b> O mesmo com os pontos do vosso ano: a tabela, X e y, fit e predict."], 30),
    caixa("Para a apresentação", p("A regra que a árvore aprendeu no vosso ano: a banda e o limite.")), gap=28))

NOTAS["pratica-aula2"] = f"""FACILITADOR 5. Aula 2 às 12:05 (12 minutos, no projector) e Prática 2 às 12:17 (18 minutos, sozinhos).

Aula 2: "A regra de ouro: nunca se avalia um modelo com os exemplos com que ele aprendeu." Resultados: treino {fmt(100 * AR['a2_treino'], 1)} % e teste {fmt(100 * AR['a2_teste'], 1)} %; no mapa oficial {fmt(100 * AR['a2_ems'], 1)} %, com {fmt(AR['a2_falsos'])} falsos alarmes e {fmt(AR['a2_perdida'])} píxeis de água perdida.

Prática 2: os pares fazem a separação ao contrário (o teste são os primeiros 5 + 5 pontos), treinam, calculam as duas notas, fazem o exame e treinam uma floresta de uma só árvore. Resultados: treino {fmt(100 * AR['p2_treino'], 1)} %, teste {fmt(100 * AR['p2_teste'], 1)} %; mapa oficial {fmt(100 * AR['p2_ems'], 1)} %, {fmt(AR['p2_falsos'])} falsos alarmes e {fmt(AR['p2_perdida'])} de água perdida; uma só árvore, {fmt(100 * AR['p2_1arvore_teste'], 1)} % no teste. Respostas: b, b, b."""
S["pratica-aula2"] = slide("pratica-aula2", "Tema 2: treinar e testar", coluna(
    lista(["<b>Aula guiada.</b> Separar treino e teste, as duas notas, o exame com o mapa oficial e a matriz de confusão.",
           "<b>Prática, sozinhos.</b> Outra separação: o teste são os primeiros 5 + 5 pontos. E uma floresta com uma só árvore."], 30),
    caixa("Para a apresentação", p("O acerto no teste e os falsos alarmes.")), gap=28))

NOTAS["pratica-anos"] = """FACILITADOR 5, às 11:50, 1 minuto (Prática 1).

"Na prática, cada par treina a árvore com os pontos de um ano diferente. A imagem de cada ano tem a sua água: muito escura, muito barrenta, de outro satélite. A árvore aprende a regra desse dia."

Dar o ano mais difícil (2021) ao par mais confiante."""
S["pratica-anos"] = slide("pratica-anos", "Prática 1: cada par treina com o seu ano", coluna(
    B.tabela(["Par", "Ano", "O que a imagem tem de especial"],
             [["Par 1", "2024", "Água muito escura"], ["Par 2", "2021", "Água muito barrenta e muitas nuvens"],
              ["Par 3", "2022", "O dia do pico da cheia"], ["Par 4", "2014", "Outro satélite: Landsat 8"],
              ["Par 5", "2025", "8 dias depois do pico"]], [16, 14, 70], tam=30, alinh=["left", "center", "left"]),
    caixa("Para a apresentação", p("A regra que a árvore aprendeu: a banda e o limite.")), gap=32))

NOTAS["pratica-aula3"] = f"""FACILITADOR 5. Aula 3 às 12:35 (8 minutos, no projector) e Prática 3 às 12:43 (12 minutos, sozinhos).

Aula 3: "Agora a qualidade da água, como no projecto. Vamos tentar prever se o rio está turvo de manhã." Com o caudal, a chuva e o mês, a floresta acerta {fmt(100 * AR['a3_nota_sem_mare'], 1)} %, menos do que dizer sempre «turva» ({fmt(100 * AR['a3_sempre_turva'], 1)} %): não aprendeu nada útil. O gráfico da maré mostra a pista que falta: água turva em {fmt(100 * AR['a3_turva_mare']['maré baixa'], 0)} % das manhãs de maré baixa e só {fmt(100 * AR['a3_turva_mare']['maré alta'], 0)} % na maré alta.

Prática 3: os pares juntam a maré às pistas e escrevem a separação, a floresta e a nota. Com a maré: {fmt(100 * AR['p3_nota_com_mare'], 1)} %. Longe do mar, no troço médio, {fmt(100 * AR['p3_nota_medio'], 1)} % (na foz, {fmt(100 * AR['p3_nota_foz'], 1)} %): a maré conta mais perto do mar. Respostas: a, a, a.

É a descoberta do projecto: o modelo de turbidez só funcionou quando lhe demos a maré (Módulo 4)."""
S["pratica-aula3"] = slide("pratica-aula3", "Tema 3: a cor do rio e a maré", coluna(
    lista(["<b>Aula guiada.</b> Prever a água turva com o caudal, a chuva e o mês. Resultado: não aprende. Que pista falta?",
           "<b>Prática, sozinhos.</b> Juntar a maré às pistas, treinar e testar. E longe do mar?"], 30),
    caixa("Para a apresentação", p("O acerto sem a maré e com a maré.")), gap=28))

NOTAS["pratica-aula4"] = f"""FACILITADOR 5. Aula 4 às 12:55 (10 minutos, no projector) e Prática 4 às 13:05 (15 minutos, sozinhos).

Aula 4: "Uma regressão: a resposta é um número, o caudal daqui a 3 dias. O exame é o futuro." Resultados: erro médio no teste {fmt(AR['a4_erro_teste'], 1)} m³/s («fica igual a hoje»: {fmt(AR['a4_igual_a_hoje'], 1)}); na árvore de regressão, a melhor profundidade é {AR['a4_melhor_profundidade']} e a de 20 decora o treino.

Prática 4: os pares escrevem o alvo a 7 dias, a separação no tempo, o treino e o erro. Resultados: {fmt(AR['p4_erro_7'], 1)} m³/s a 7 dias; só com a chuva, {fmt(AR['p4_so_chuva_7'], 1)}. Respostas: a, a, a, a.

Às 13:20, todos guardam (Ctrl + S) e preparam a apresentação: o último quadro da Prática 4 diz o que apresentar."""
S["pratica-aula4"] = slide("pratica-aula4", "Tema 4: prever o caudal", coluna(
    lista(["<b>Aula guiada.</b> O caudal daqui a 3 dias: o teste no futuro, o erro médio e o sobreajuste.",
           "<b>Prática, sozinhos.</b> O caudal daqui a 7 dias, e sem o caudal de hoje."], 30),
    caixa("Para a apresentação", p("O erro a 7 dias e sem o caudal de hoje.")), gap=28))

# ============================== APRESENTAÇÕES E RESULTADOS (13:25–13:40) ==============================
NOTAS["apresentacoes"] = """FACILITADOR 5 conduz; a MODERADORA controla o tempo (2 minutos por par, aviso aos 90 segundos; 13:25–13:40).

Ordem sugerida: Par 4 (2014), Par 5 (2025), Par 1 (2024), Par 3 (2022), Par 2 (2021): a regra de cada ano vai mudando, até à de 2021, a mais diferente.

Enquanto cada par fala, o Facilitador 6 escreve no quadro a regra de cada ano (a banda e o limite).

Depois das 5 apresentações, mostrar os slides seguintes (os resultados de referência) e perguntar: "Porque é que a regra muda de ano para ano?\""""
S["apresentacoes"] = divisoria("apresentacoes", "Apresentações", "O que os nossos modelos aprenderam", "13:25–13:40 | 2 minutos por par",
                               caixa("Cada par mostra:", lista(["A regra do nosso ano (Prática 1).", "O acerto no teste e os falsos alarmes (Prática 2).",
                                                                 "A maré e o erro a 7 dias (Práticas 3 e 4).", "Uma coisa que nos surpreendeu."], num=True)))

NOTAS["resultados"] = """FACILITADOR 5, 2 minutos, depois das apresentações.

Ler a tabela ano a ano: em 2014, 2025 e 2026 a árvore escolhe o SWIR, com limites parecidos; em 2021, com a água muito barrenta, o SWIR da água sobe e o limite também; em 2022 e 2024 a água ficou tão escura que a árvore prefere a banda vermelha.

Três frases para a turma:
1. Um modelo só sabe o que viu: aprende a água daquele dia.
2. Uma regra fixa (como a do Workshop 1) falha quando a água muda; um modelo treinado com exemplos novos adapta-se.
3. Casos novos precisam de exemplos novos.

Os números dos pares devem ser iguais aos da tabela, porque todos usam os pontos da equipa."""
S["resultados"] = slide("resultados", "Cada ano, a sua regra", coluna(
    B.tabela(["Par", "Ano", "A regra da água"],
             [[par, str(ano), f"{anos_p1[str(ano)]['banda'].upper()} ≤ {fmt(anos_p1[str(ano)]['limite'], 3)}"]
              for par, ano in ANO_POR_PAR.items()],
             [22, 18, 60], tam=28, alinh=["left", "center", "left"]),
    destaque(f"Em 2026 era SWIR ≤ {fmt(AR['a1_limiar_arvore'], 2)}. A regra muda com a cor da água."),
    legenda("A primeira pergunta da árvore da Prática 1, em cada ano.", "resultados de referência da equipa ETE", tipo="Tabela"),
    gap=24))


def painel(chave, alt, texto):
    return coluna(imagem(chave, alt, 470, 569), p(texto, 28, TINTA, 700, "text-align:center"), gap=10)


S["resultados-2024"] = slide("resultados-2024", "2024: a regra apagou o rio, a IA não", coluna(
    linha(painel("r2024_cor", "O rio em 20 de Janeiro de 2024 em cor natural, muito escuro", "Cor natural"),
          painel("r2024_mndwi", "A regra MNDWI maior do que zero: quase nada a azul, o rio desapareceu", "Regra MNDWI: 0% do rio"),
          painel("m2024", "A IA treinada só com a cheia de 2026: o rio aparece inteiro a azul",
                 f"Random Forest: {fmt(alg['Random Forest (100 árvores)']['rio_2024'])}% do rio"),
          gap=40, extra="justify-content:center"),
    legenda("Recorte do rio a 20/01/2024 (Sentinel-2). Modelo de referência da equipa, com 8 pistas, treinado só com a cheia de 2026.",
            "resultados de referência da equipa ETE"), gap=16))

NOTAS["resultados-modelos"] = f"""FACILITADOR 5, 2 minutos, depois das apresentações dos pares.

"Juntemos tudo. Na Prática 1, a árvore aprendeu uma regra diferente em cada ano. Na Prática 2, com outra separação, a floresta acertou {fmt(100 * AR['p2_ems'], 1)} % no mapa oficial. Na Prática 3, a floresta da água barrenta passou de {fmt(100 * AR['a3_nota_sem_mare'], 1)} % para {fmt(100 * AR['p3_nota_com_mare'], 1)} % quando lhe demos a maré. Na Prática 4, a previsão a 7 dias erra {fmt(AR['p4_erro_7'], 1)} m³/s, mais do que a 3 dias ({fmt(AR['a4_erro_teste'], 1)})."

Lição: a nota de um exame só vale para aquele tipo de dados; um bom cientista testa o modelo em casos diferentes e diz onde ele erra."""
S["resultados-modelos"] = slide("resultados-modelos", "As quatro práticas, lado a lado", coluna(
    B.tabela(["Prática", "Modelo", "O que descobrimos"],
             [["1", "Árvore de decisão", "Cada ano, a sua regra"],
              ["2", "Floresta aleatória", f"{fmt(100 * AR['p2_ems'], 1)} % certo no mapa oficial"],
              ["3", "Floresta da água turva", f"de {fmt(100 * AR['a3_nota_sem_mare'], 0)} % para {fmt(100 * AR['p3_nota_com_mare'], 0)} % com a maré"],
              ["4", "Regressão a 7 dias", f"erro médio de {fmt(AR['p4_erro_7'], 1)} m³/s"]],
             [14, 38, 48], tam=28, alinh=["center", "left", "left"]),
    destaque("Cada modelo foi avaliado com dados que nunca viu."),
    legenda("Resultados de referência da equipa, iguais aos que os pares obtêm.", tipo="Tabela"), gap=24))

# ============================== ENCERRAMENTO (13:40–14:00) ==============================
S["licoes"] = slide("licoes", "Conclusões: o que levamos para casa", grelha([
    caixa("1. As pistas certas", p("Sem a maré, o modelo não aprendia. Os dados contam mais do que o algoritmo.")),
    caixa("2. A nota a sério é a do exame", p("Com dados que o modelo nunca viu. No tempo, o exame é o futuro.")),
    caixa("3. Simples ou complexo?", p("Um modelo que decora o treino erra no teste.")),
    caixa("4. As pessoas decidem", p("Um modelo honesto mostra onde erra. Os avisos oficiais vêm primeiro."))], 2, "28px 32px"))

NOTAS["continuar"] = """MODERADORA, 1 minuto.

Lembrar que cada participante pode levar a pasta Workshop_2 (sem a pasta 0_facilitadores) num pen drive e continuar em casa, em qualquer computador com o Jupyter Notebook (o LEIA-ME explica como instalar). As práticas que ficaram por acabar corrigem-se sozinhas, passo a passo. Os notebooks de introdução ao Python (1_preparacao_python) são os mesmos do Workshop 1."""
S["continuar"] = slide("continuar", "Para continuar em casa", coluna(
    B.tabela(["Material", "O que é"],
             [["As 4 aulas e as 4 práticas", "As práticas que ficaram por acabar, com correcção em cada passo."],
              ["Teste do aluno", "16 perguntas, com nota automática."],
              ["Introdução ao Python", "Os 3 notebooks do Workshop 1."],
              ["A plataforma", "ete-platform.streamlit.app: os modelos a trabalhar todos os dias."]], [34, 66], tam=28),
    p("Tudo na pasta <b>Workshop_2</b>, para levar num pen drive e abrir no Jupyter Notebook.", 28), gap=32))

S["inquerito-final"] = slide("inquerito-final", "Antes de sairmos", coluna(
    p("Encerramento, 13:40–14:00.", 30, SUAVE),
    linha(coluna(h3("1. Questionário final OAD"), qr("[QR do questionário OAD pós-workshop]", 320), p("O mesmo da manhã: mede o que aprendemos.", 28), gap=16, extra="flex:1"),
          coluna(h3("2. Avaliação do workshop"), qr("[QR do formulário de avaliação]", 320), p("5 minutos: o que gostaram e o que mudariam.", 28), gap=16, extra="flex:1"),
          coluna(h3("3. Certificados"), p("Entrega dos certificados de participação.", 28), p("E a foto de grupo!", 28), gap=16, extra="flex:1"), gap=48), gap=28))

S["obrigado"] = (
    f'<section id="obrigado" data-transition="fade" style="background:{BRANCO};color:{TINTA};font-family:Arial, sans-serif;'
    f'padding:88px 128px 88px;display:flex;flex-direction:column;justify-content:space-between;gap:40px">\n' + BANDA
    + linha(logo_ete(150), coluna(p("Projecto EYES TO EARTH (ETE)", 30, ACENTO, 700), p("Marracuene, rio Incomáti", 30, SUAVE), gap=4),
            gap=36, alinhar="center")
    + coluna(f'<h1 style="font-family:{TITULO};font-size:96px;font-weight:400;line-height:1.08;color:{PRETO}">Obrigado!</h1>',
             f'<div style="width:200px;height:6px;background:{ACENTO}"></div>', p("Continuem a olhar para o rio, do chão e do espaço."),
             p("ete-platform.streamlit.app | [contacto do projecto]", 30, SUAVE), gap=28)
    + apoios() + B.aside("obrigado"))


# ---------- verificações ----------

CORES_PERMITIDAS = {c.upper() for c in [BRANCO, TINTA, SUAVE, ACENTO, PRETO, CAB_TABELA, CAIXA, LINHA, REALCE, ERRO_FUNDO,
                                        SERIE_TREINO, SERIE_TESTE, "#444444", "#E8F3EA", "#FFF6D6", "#FDEBD9", "#FADBD8"]}
CORES_SO_NA_ARVORE = {AGUA.upper(), "#2E7D32", "#8B5A2B"}      # as folhas da árvore: água, vegetação, solo
EMOJI = re.compile("[\U0001F300-\U0001FAFF☀-➿]")


def verificar():
    """Confirma as regras do deck. Devolve os avisos (não fatais); levanta AssertionError nos erros."""
    avisos = []
    assert len(ORDEM) == len(set(ORDEM)), "slide repetido na ordem"
    assert not [s for s in ORDEM if s not in S], [s for s in ORDEM if s not in S]
    assert not [s for s in S if s not in ORDEM], [s for s in S if s not in ORDEM]
    assert not [s for s in NOTAS if s not in ORDEM], ("notas sem slide", [s for s in NOTAS if s not in ORDEM])
    proibido = re.compile(r"margin:|z-index|var\(|class=")
    for sid in ORDEM:
        html = S[sid]
        assert html.count("<section") == 1 and html.rstrip().endswith("</section>"), sid
        assert html.count("<aside>") == 1 and NOTAS.get(sid), sid
        assert len(NOTAS[sid]) <= 4000, (sid, len(NOTAS[sid]))
        for texto in (NOTAS[sid], html):
            assert "Colab" not in texto and "Google Drive" not in texto, sid
        tamanhos = [int(x) for x in re.findall(r"font-size:(\d+)px", html)]
        assert min(tamanhos) >= 24, (sid, min(tamanhos))
        elementos = len(re.findall(r"<(?!/|br|b>|i>|u>|span)[a-z][a-z0-9-]*", html))
        assert elementos <= 200, (sid, elementos)
        assert not proibido.search(html), (sid, proibido.search(html))
        for src in re.findall(r'src="([^"]+)"', html):
            assert src.startswith("/_blob/"), (sid, src)
        corpo = re.sub(r"<aside>.*?</aside>", "", html, flags=re.S)
        for cor in {c.upper() for c in re.findall(r"#[0-9A-Fa-f]{6}\b", corpo)}:
            assert cor in CORES_PERMITIDAS or (cor in CORES_SO_NA_ARVORE and sid == "m2-arvore"), (sid, cor)
        visivel = re.sub(r"<[^>]+>", " ", corpo)
        if EMOJI.search(visivel):
            raise AssertionError((sid, "emoji no slide", EMOJI.findall(visivel)))
        assert "§N§" not in corpo or re.search(r"(Figura|Tabela) §N§", corpo), sid
        m = re.search(r"<h2[^>]*>(.*?)</h2>", html)
        if m and B.larg_titulo(re.sub("<[^>]+>", "", m.group(1)), 52) > 1544:
            avisos.append(f"título em 2 linhas: {sid}: {m.group(1)}")
        n = B.palavras_visiveis(html)
        if n > 80:
            avisos.append(f"{n} palavras: {sid}")
    return avisos
