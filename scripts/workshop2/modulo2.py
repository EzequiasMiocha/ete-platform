"""O Módulo 2 do Workshop 2 (Como uma máquina aprende), numa versão leve, para quem nunca ouviu falar de modelos de IA.

Um deck à parte (artefacto «Módulo 2: Como uma máquina aprende»), no mesmo estilo do deck principal (slides_base.py).
A ideia geral primeiro, com exemplos do dia-a-dia (cães e gatos, burlas no WhatsApp, o telemóvel); poucas ligações ao
projecto, mas bem escolhidas: a imagem de satélite, o mapa da água que a árvore da Aula 1 desenha, o caudal do rio e
as três perguntas da plataforma. Quase sem números e sem fórmulas: os algoritmos são ideias (perguntas de sim ou não,
árvores a votar, uma recta). Os dados dos jogos são inventados e isso está escrito no slide.
Escrever o deck:  .venv/bin/python scripts/build_workshop2_modulo2.py
Português de Portugal (ortografia anterior ao Acordo de 1990), sem emojis, uma ideia por slide.
"""

import json
import re

from . import slides_base as B
from .comum import FAC, ROOT
from .slides_base import (ACENTO, AGUA, BRANCO, CAIXA, LINHA, REALCE, SUAVE, TINTA, bloco, caixa, coluna, destaque,
                          divisoria, fmt, imagem, legenda, linha, lista, p, pergunta_abertura, seta, slide)

DECK = ROOT / "reports/apresentacao/workshop2_modulo2"
NUM = json.loads((FAC / "imagens_para_slides/modulo2/numeros.json").read_text(encoding="utf-8"))
IMAGENS = json.loads((DECK / "imagens.json").read_text(encoding="utf-8"))     # as imagens carregadas no artefacto
B.BLOB.clear()
B.BLOB.update({chave: v["blob"] for chave, v in IMAGENS.items()})

SENTINEL = "Copernicus Sentinel-2 (ESA)"
TERRA = "#8B5A2B"                       # a folha «sem cheia» da árvore (a mesma cor do solo no deck principal)
SECCAO = "Módulo 2: Como uma máquina aprende"

ORDEM = ["m2", "m2-exemplos", "m2-duas-maneiras", "m2-modelo", "m2-modelo-exemplos", "m2-ingredientes",
         "m2-treinar-prever", "m2-errar",
         "m2-tipos", "m2-classificacao-regressao", "m2-actividade-tipos",
         "m2-arvore", "m2-arvore-projecto", "m2-actividade-arvore", "m2-floresta", "m2-actividade-votar",
         "m2-regressao", "m2-projecto", "m2-resumo"]
SECCOES_DECK = {
    "s-ideia": ("m2", "Aprender com exemplos: o que é um modelo, de que dados precisa, treinar e prever"),
    "s-tipos": ("m2-tipos", "As três formas de aprender, e a classificação e a regressão"),
    "s-arvore": ("m2-arvore", "Dois algoritmos simples, com jogos: a árvore de decisão e a floresta"),
    "s-fim": ("m2-regressao", "Prever um número, o que a máquina faz no projecto EYES TO EARTH e o resumo"),
}
MINUTOS_DE_PERGUNTAS = 7                # 09:48–09:55: as perguntas da turma, antes do quiz

B.definir_ordem(ORDEM, {"m2": SECCAO})


class _NotasDepois(dict):
    """Aqui cada nota vem a seguir ao seu slide: o slide guarda um marcador, trocado pela nota em html() no fim."""

    def __missing__(self, sid):
        return f"§NOTA:{sid}§"


B.NOTAS = _NotasDepois()
B.ESCALA.clear()
B.ESCALA.update(dict.fromkeys(["m2-modelo", "m2-treinar-prever", "m2-classificacao-regressao", "m2-resumo",
                               "m2-duas-maneiras", "m2-projecto"], 1.1))
S, NOTAS = {}, B.NOTAS


def figura(chave, alt, w, texto, fonte=None, borda=True):
    """Uma figura com a largura dada e a altura certa para a proporção da imagem."""
    h = round(w * IMAGENS[chave]["altura"] / IMAGENS[chave]["largura"])
    return (f'<div style="width:{w}px;display:flex;flex-direction:column;gap:10px;align-self:center">'
            + imagem(chave, alt, w, h, borda) + legenda(texto, fonte) + "</div>")


def passos(itens, tam=28):
    """Blocos ligados por setas (um processo)."""
    filhos = []
    for i, (titulo, texto) in enumerate(itens):
        if i:
            filhos.append(seta(48, 26))
        filhos.append(bloco(titulo, texto, "flex:1", tam=tam))
    return linha(*filhos, gap=16, alinhar="center")


# ============================== APRENDER COM EXEMPLOS ==============================

S["m2"] = divisoria("m2", "Módulo 2", "Como uma máquina aprende", "09:05–09:55 | Facilitador 2",
                    pergunta_abertura("Como é que aprenderam a distinguir um cão de um gato? Alguém vos deu uma regra?"))
NOTAS["m2"] = """FACILITADOR 2, cerca de 1,5 minutos.

Mostrem a pergunta e deixem 3 ou 4 alunos responder. Vão aparecer respostas como «pelas orelhas», «pelo tamanho», «pelo focinho», «pelo miar».

"E quem vos ensinou essa regra? Ninguém a escreveu num quadro. Quando eram pequenos, viram muitos cães e muitos gatos, e alguém foi dizendo: 'olha, um cão', 'olha, um gato'. A regra, descobriram-na sozinhos.

Neste módulo vamos ver que os computadores podem aprender da mesma maneira. Chama-se Machine Learning, a aprendizagem automática." """

S["m2-exemplos"] = slide("m2-exemplos", "Aprendemos com exemplos", coluna(
    passos([("1. Vemos muitos exemplos", "cães e gatos, na rua, nos livros, na televisão"),
            ("2. Alguém diz a resposta", "«olha, um cão»; «olha, um gato»"),
            ("3. Descobrimos a regra", "as orelhas, o focinho, o tamanho")], tam=30),
    destaque("Ninguém nos deu uma regra escrita. Os computadores também podem aprender assim."), gap=56))
NOTAS["m2-exemplos"] = """FACILITADOR 2, cerca de 2,5 minutos.

"Vamos olhar para o que fizeram em criança, em três passos.
1. Viram MUITOS exemplos. Não um cão: centenas, de todos os tamanhos e cores.
2. Alguém disse a RESPOSTA CERTA de cada um: 'isto é um cão'.
3. Com o tempo, o vosso cérebro descobriu a REGRA sozinho. Hoje reconhecem um cão que nunca viram.

Uma pergunta: e se só vos tivessem mostrado cães pretos? (Talvez pensassem que um cão branco era outra coisa.) Os exemplos têm de ser variados. Guardem esta ideia: volta na prática, com as imagens de satélite de vários anos."

É a ideia mais importante do módulo. Vale a pena demorar aqui."""

S["m2-duas-maneiras"] = slide("m2-duas-maneiras", "Duas maneiras de ensinar um computador", linha(
    caixa("Um programa normal", p("<b>As pessoas</b> escrevem a regra.")
          + p("«Se a mensagem disser <i>ganhou um prémio</i>, é burla.»", 28, SUAVE), cor=SUAVE, extra="flex:1"),
    caixa("Machine Learning", p("<b>A máquina</b> descobre a regra, a partir de exemplos com a resposta certa.")
          + p("Mostramos milhares de mensagens já marcadas como burla ou normal.", 28, SUAVE), extra="flex:1"),
    gap=40, alinhar="stretch"))
NOTAS["m2-duas-maneiras"] = """FACILITADOR 2, cerca de 2 minutos.

"Há duas maneiras de pôr um computador a decidir.

À esquerda, a maneira de sempre: uma pessoa pensa na regra e escreve-a. 'Se a mensagem disser ganhou um prémio, é burla.' Funciona... até o burlão escrever 'foi premiado'. Seria preciso escrever milhares de regras.

À direita, o Machine Learning: em vez da regra, damos ao computador MILHARES de exemplos, mensagens que já sabemos se eram burla ou não. E ele descobre sozinho o que as burlas têm em comum.

Quando a regra é difícil de escrever (reconhecer uma cara, a água numa imagem de satélite, uma burla), é melhor aprender com exemplos." """

S["m2-modelo"] = slide("m2-modelo", "O que é um modelo?", coluna(
    linha(bloco("Entrada", "a informação que temos", "flex:1", tam=30), seta(),
          bloco("O modelo", "a regra que a máquina aprendeu", "flex:1", tam=30), seta(),
          bloco("Saída", "a resposta", "flex:1", tam=30), gap=20, alinhar="center"),
    destaque("O modelo é o que fica depois de aprender: uma regra que dá uma resposta."), gap=56))
NOTAS["m2-modelo"] = """FACILITADOR 2, cerca de 1,5 minutos.

"Ao que a máquina aprende chamamos MODELO. É uma caixa com uma regra lá dentro: entra a informação que temos, sai uma resposta.

A palavra 'modelo' vai aparecer muitas vezes hoje. Quando a ouvirem, pensem: a regra que a máquina aprendeu com os exemplos." """

S["m2-modelo-exemplos"] = slide("m2-modelo-exemplos", "Modelos à nossa volta", coluna(
    B.tabela(["Exemplo", "Entrada", "Saída"],
             [["Filtro de burlas", "uma mensagem de WhatsApp", "burla ou normal"],
              ["Desbloqueio do telemóvel", "a fotografia da cara", "é o dono ou não"],
              ["Músicas sugeridas", "as músicas que ouvimos", "uma música nova de que vamos gostar"],
              ["O nosso projecto", "uma imagem de satélite", "onde há água"]],
             [30, 34, 36], tam=30, cores=[None, CAIXA, None, REALCE]), gap=40))
NOTAS["m2-modelo-exemplos"] = """FACILITADOR 2, cerca de 2 minutos.

"Usamos modelos todos os dias sem dar por isso. O telemóvel reconhece a vossa cara: aprendeu com fotografias. O YouTube ou o Spotify sugerem músicas: aprenderam com o que milhões de pessoas ouviram.

E a última linha é o nosso projecto, EYES TO EARTH: entra uma imagem de satélite do rio Incomáti, em Marracuene, e sai um mapa de onde há água. É assim que vemos uma cheia a partir do espaço."

Pergunta à sala: "conhecem outro modelo que usem no telemóvel?" (o tradutor, o teclado que adivinha a palavra seguinte, os filtros de fotografia)."""

S["m2-ingredientes"] = slide("m2-ingredientes", "Os ingredientes: exemplos, pistas e respostas", coluna(
    p("Cada <b>linha</b> é um exemplo; cada <b>coluna</b>, uma pista; a última, a resposta certa: o <b>rótulo</b>."),
    coluna(linha(p("", 26, BRANCO, 700, "flex:16;padding:8px 16px"),
                 p("as pistas", 26, BRANCO, 700, f"flex:63;background:{SUAVE};padding:8px 16px"),
                 p("o rótulo", 26, BRANCO, 700, f"flex:21;background:{ACENTO};padding:8px 16px"), gap=0),
           B.tabela(["Mensagem", "Pede dinheiro?", "Tem um link?", "Contacto conhecido?", "Resposta"],
                    [["1", "sim", "sim", "não", "burla"], ["2", "não", "não", "sim", "normal"],
                     ["3", "sim", "não", "sim", "normal"], ["4", "não", "sim", "não", "burla"]],
                    [16, 21, 19, 23, 21], tam=30, alinh=["center", "center", "center", "center", "left"]),
           legenda("Exemplo inventado: quatro mensagens de WhatsApp.", tipo="Tabela"), gap=8), gap=36))
NOTAS["m2-ingredientes"] = """FACILITADOR 2, cerca de 2 minutos. Exemplo inventado (dizê-lo à turma).

"Para aprender, a máquina precisa de uma TABELA de exemplos. Cada linha é um EXEMPLO: aqui, uma mensagem. Cada coluna é uma PISTA: uma coisa que sabemos sobre a mensagem. A última coluna é a RESPOSTA CERTA, que se chama RÓTULO.

Reparem na mensagem 3: pede dinheiro, mas é de um contacto conhecido (a mãe a pedir para comprar pão). É normal. Por isso uma pista sozinha não chega: a máquina tem de olhar para várias ao mesmo tempo.

Na prática, os exemplos são píxeis de imagens de satélite, as pistas são as cores que o satélite mede, e o rótulo é 'água' ou 'não água'." """

S["m2-treinar-prever"] = slide("m2-treinar-prever", "Treinar e prever", coluna(
    linha(caixa("Treinar", p("Mostrar ao modelo muitos exemplos <b>com</b> a resposta certa."), extra="flex:1"),
          caixa("Prever", p("Dar ao modelo um caso novo, <b>sem</b> resposta. Ele responde."), extra="flex:1"),
          gap=40, alinhar="stretch"),
    p("Na prática, em Python, são duas palavras: <b>fit</b> (treinar) e <b>predict</b> (prever).", 30, SUAVE),
    gap=48))
NOTAS["m2-treinar-prever"] = """FACILITADOR 2, cerca de 1,5 minutos.

"Usar Machine Learning tem duas fases.
TREINAR: mostrar os exemplos com a resposta certa, para o modelo aprender. Como estudar com os exercícios resolvidos.
PREVER: dar ao modelo um caso novo, que ele nunca viu, e ver o que responde. Como o exame.

Em Python, cada fase é uma palavra: fit, que quer dizer 'ajustar', e predict, que quer dizer 'prever'. Vão escrevê-las vocês na Prática 1." """

S["m2-errar"] = slide("m2-errar", "Treinar é errar e corrigir", coluna(
    passos([("1. Adivinhar", "a primeira resposta é quase ao acaso"),
            ("2. Ver o erro", "comparar com a resposta certa"),
            ("3. Corrigir", "mudar a regra um pouco"),
            ("4. Repetir", "milhares de vezes")], tam=28),
    destaque("Como aprender a lançar uma bola ao cesto: cada lançamento falhado ensina a corrigir a força."), gap=56))
NOTAS["m2-errar"] = """FACILITADOR 2, cerca de 2 minutos.

"Como é que a máquina descobre a regra? Por tentativa e erro, como nós.
1. Começa por adivinhar: a primeira regra é muito má.
2. Compara as respostas dela com as respostas certas dos exemplos: vê quanto errou.
3. Corrige a regra um pouco, na direcção que faz o erro diminuir.
4. Repete, milhares de vezes, muito depressa.

É como aprender a lançar ao cesto: lançam, a bola fica curta, lançam com mais força, passa por cima, lançam um pouco mais leve... até acertar. Treinar um modelo é exactamente isto, feito por um computador." """


# ============================== AS FORMAS DE APRENDER ==============================

def tipo_caixa(titulo, subtitulo, exemplo, cor):
    return coluna(f'<div style="background:{cor};padding:16px 20px">' + p(titulo, 30, BRANCO, 700) + p(subtitulo, 26, BRANCO) + "</div>",
                  f'<div style="width:4px;height:24px;background:{LINHA};align-self:center"></div>',
                  bloco("Exemplo", exemplo, "", cor), gap=10, extra="flex:1")


S["m2-tipos"] = slide("m2-tipos", "Três formas de aprender", coluna(
    linha(tipo_caixa("Supervisionada", "com as respostas certas, como um aluno com um professor que corrige",
                     "burla ou normal; água ou não água", ACENTO),
          tipo_caixa("Não supervisionada", "sem respostas: junta o que é parecido",
                     "arrumar músicas por estilo, sem saber os nomes dos estilos", SUAVE),
          tipo_caixa("Por reforço", "tentativa, erro e recompensa",
                     "um robô que aprende a andar; os jogos", TINTA),
          gap=32, alinhar="stretch"),
    destaque("Nas aulas de hoje e no projecto usamos a <b>supervisionada</b>."), gap=36))
NOTAS["m2-tipos"] = """FACILITADOR 2, cerca de 2,5 minutos.

"Há três grandes formas de uma máquina aprender.

1. SUPERVISIONADA: com as respostas certas, como um aluno com um professor que corrige os exercícios. É a dos cães e gatos, e a das burlas.

2. NÃO SUPERVISIONADA: sem respostas. A máquina junta o que é parecido, sozinha. Imaginem arrumar 1000 músicas em grupos parecidos sem saber o nome dos estilos.

3. POR REFORÇO: a máquina tenta, erra, e ganha pontos quando acerta. É como treinar um cão com biscoitos. Foi assim que um computador venceu o campeão mundial do jogo Go, em 2016.

Hoje, nas aulas e no projecto, usamos sempre a SUPERVISIONADA, porque temos as respostas certas: os pontos marcados pela equipa nas imagens, os mapas oficiais das cheias, o caudal medido no passado."

Esta pergunta volta no quiz."""

S["m2-classificacao-regressao"] = slide("m2-classificacao-regressao", "Com respostas certas: uma categoria ou um número?", linha(
    caixa("Classificação", p("A resposta é uma <b>categoria</b>.")
          + lista(["burla ou normal", "cão ou gato", "água ou não água (o projecto)"], 30), extra="flex:1"),
    caixa("Regressão", p("A resposta é um <b>número</b>.")
          + lista(["a temperatura de amanhã", "o preço de uma casa", "quanta água vai passar no rio (o projecto)"], 30),
          extra="flex:1"),
    gap=40, alinhar="stretch"))
NOTAS["m2-classificacao-regressao"] = """FACILITADOR 2, cerca de 2 minutos.

"A aprendizagem supervisionada tem dois tipos, conforme a resposta.

Se a resposta é uma CATEGORIA, um nome de uma lista (burla ou normal, cão ou gato, água ou não água), chama-se CLASSIFICAÇÃO.

Se a resposta é um NÚMERO, uma medida (a temperatura em graus, o preço em meticais, a água do rio em metros cúbicos por segundo), chama-se REGRESSÃO.

Uma regra simples: se a resposta tem unidades, é regressão."

Pergunta rápida: "a idade de uma pessoa numa fotografia?" (regressão: um número). "Se a fruta está madura ou não?" (classificação)."""

S["m2-actividade-tipos"] = slide("m2-actividade-tipos", "Actividade: que tipo de aprendizagem é?", coluna(
    p("3 minutos, em pares: classificação, regressão, sem respostas ou por reforço?", 30, SUAVE),
    B.tabela(["Tarefa", "Tipo"],
             [["1. A temperatura máxima de amanhã", ""],
              ["2. Uma mensagem: “burla” ou “normal”", ""],
              ["3. Clientes de uma loja em grupos parecidos, sem saber os grupos", ""],
              ["4. Um robô aprende a andar, caindo e levantando-se", ""],
              ["5. Uma fotografia: “cão” ou “gato”", ""],
              ["6. Quanta água vai passar no rio daqui a 3 dias", ""],
              ["7. Uma imagem de satélite: onde há água", ""],
              ["8. A nota de um aluno, pelas horas de estudo", ""]], [76, 24], tam=28), gap=24))
NOTAS["m2-actividade-tipos"] = """FACILITADOR 2. Actividade em pares, cerca de 3,5 minutos (2 para responder, 1,5 para corrigir em voz alta).

Respostas:
1. A temperatura de amanhã: REGRESSÃO (um número, em graus).
2. Burla ou normal: CLASSIFICAÇÃO.
3. Clientes em grupos, sem saber os grupos: SEM RESPOSTAS (não supervisionada).
4. O robô que aprende a andar: POR REFORÇO.
5. Cão ou gato: CLASSIFICAÇÃO.
6. A água do rio daqui a 3 dias: REGRESSÃO (é a Aula 4).
7. Onde há água numa imagem de satélite: CLASSIFICAÇÃO (cada píxel é água ou não água: são as Aulas 1 e 2).
8. A nota pelas horas de estudo: REGRESSÃO.

Corrijam perguntando a pares diferentes. Se houver dúvida entre classificação e regressão, voltem à regra: categoria, ou número com unidades?"""


# ============================== A ÁRVORE E A FLORESTA ==============================

def no(left, top, w, texto, fundo, borda, h=100):
    return (f'<div style="position:absolute;left:{left}px;top:{top}px;width:{w}px;height:{h}px;background:{fundo};'
            f'border:2px solid {borda};display:flex;flex-direction:column;align-items:center;justify-content:center">'
            + texto + "</div>")


def ramo(x1, y1, x2, y2):
    return f'<x-connector x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" head="end" style="color:{SUAVE};border-width:3px"></x-connector>'


def etiqueta(left, top, texto):
    return f'<p style="position:absolute;left:{left}px;top:{top}px;width:120px;font-size:30px;font-weight:700;color:{SUAVE}">{texto}</p>'


def pergunta(left, top, w, texto):
    return no(left, top, w, p(texto, 30, ACENTO, 700, "text-align:center"), BRANCO, ACENTO)


def folha(left, top, w, texto, cor):
    return no(left, top, w, p(texto, 32, BRANCO, 700, "text-align:center"), cor, cor)


arvore = ('<div style="position:relative;width:1664px;height:470px">'
          + pergunta(532, 0, 600, "Choveu muito esta semana?")
          + ramo(700, 100, 330, 190) + ramo(964, 100, 1250, 190) + etiqueta(420, 112, "não") + etiqueta(1130, 112, "sim")
          + folha(130, 190, 400, "SEM CHEIA", TERRA)
          + pergunta(990, 190, 520, "O rio já está alto?")
          + ramo(1130, 290, 900, 370) + ramo(1370, 290, 1520, 370) + etiqueta(930, 300, "não") + etiqueta(1470, 300, "sim")
          + folha(700, 370, 400, "SEM CHEIA", TERRA)
          + folha(1300, 370, 364, "CHEIA", AGUA) + "</div>")
S["m2-arvore"] = slide("m2-arvore", "A árvore de decisão: perguntas de sim ou não", coluna(
    arvore,
    p("Como o jogo das 20 perguntas. A máquina escolhe sozinha as perguntas, olhando para os exemplos."),
    p("Um exemplo simples, inventado.", 26, SUAVE), gap=28))
NOTAS["m2-arvore"] = """FACILITADOR 2, cerca de 2 minutos. Exemplo inventado (dizê-lo à turma: as cheias verdadeiras dependem de muito mais coisas).

"Vamos ver um ALGORITMO, uma receita para aprender. O mais fácil de entender é a ÁRVORE DE DECISÃO: uma sequência de perguntas de sim ou não, como o jogo das 20 perguntas.

Lê-se de cima para baixo. Choveu muito esta semana? Se não, sem cheia. Se sim, outra pergunta: o rio já está alto? Se sim, cheia.

A parte mágica: ninguém escreve estas perguntas. A máquina olha para os exemplos e escolhe sozinha as perguntas e os números (quanta chuva é 'muita'? que altura é 'alto'?) que melhor separam os dias com cheia dos dias sem cheia."

Na actividade daqui a pouco, são vocês a árvore."""

S["m2-arvore-projecto"] = slide("m2-arvore-projecto", "A árvore no nosso projecto", linha(
    figura("mapa", "Mapa de Marracuene com a água da cheia a azul, segundo a árvore da Aula 1, as nuvens a cinzento e o limite do distrito a preto",
           420, "A água a 24/01/2026, segundo a árvore da Aula 1.", SENTINEL),
    coluna(p("Na Aula 1, damos à árvore exemplos de água e de terra, tirados de uma imagem da cheia."),
           p("Ela descobre sozinha <b>uma só pergunta</b>: o chão devolve luz infravermelha? A água quase não devolve."),
           destaque("Com essa pergunta, desenha o mapa da água: cerca de um terço do distrito."),
           gap=28, extra="flex:1"), gap=56))
NOTAS["m2-arvore-projecto"] = f"""FACILITADOR 2, cerca de 2,5 minutos. A árvore verdadeira da Aula 1.

"Agora com o nosso projecto. A 24 de Janeiro de 2026, o satélite Sentinel-2 fotografou o Incomáti no meio da cheia. A equipa marcou na imagem pontos de água e pontos de terra: são os exemplos, com a resposta certa.

O satélite mede cores que os nossos olhos não vêem, como o infravermelho. A árvore experimentou todas e descobriu sozinha que bastava uma pergunta: quanto infravermelho (o SWIR) devolve o chão? A água absorve-o quase todo; a terra devolve muito.

Depois, a árvore fez essa pergunta a todos os píxeis da imagem, mais de 800 000, e desenhou este mapa. A azul, a água: cerca de {fmt(NUM['aula1']['hectares'], 0)} hectares, perto de um terço do distrito de Marracuene."

Na Aula 1, os pares vão ver esta árvore e este mapa no ecrã deles. Não é preciso explicar mais aqui."""

dias = [("1", "20", "1,5", "não"), ("2", "150", "4,0", "sim"), ("3", "180", "2,0", "não"), ("4", "40", "3,5", "não"),
        ("5", "120", "3,8", "sim"), ("6", "90", "2,5", "não"), ("7", "200", "4,5", "sim"), ("8", "60", "1,8", "não")]
S["m2-actividade-arvore"] = slide("m2-actividade-arvore", "Actividade: sejam uma árvore de decisão", linha(
    coluna(p("4 minutos, em pares. Dados inventados para o jogo.", 30, SUAVE),
           lista(["Escrevam 1 ou 2 perguntas de sim ou não, com números, que separem os dias com cheia dos dias sem cheia.",
                  "Testem-nas nos 8 dias. Acertam todos?"], num=True), gap=24, extra="flex:1"),
    B.tabela(["Dia", "Chuva na semana (mm)", "Nível do rio (m)", "Houve cheia?"],
             [list(d) for d in dias], [12, 33, 28, 27], tam=28, alinh=["center", "center", "center", "center"],
             largura=820), gap=48))
NOTAS["m2-actividade-arvore"] = """FACILITADOR 2. Actividade em pares, cerca de 4 minutos. Dados INVENTADOS para o jogo (os números não são limites verdadeiros de cheia).

Deixem os pares tentar 2 minutos. Depois perguntem a 2 ou 3 pares que perguntas escreveram e testem-nas em voz alta.

Uma resposta certa (há várias):
1. «Choveu mais de 100 mm?» Se não: sem cheia.
2. Se sim: «O rio está acima de 3 m?» Se sim: cheia; se não: sem cheia.

Uma só pergunta não chega:
- só com a chuva, o dia 3 (180 mm) dava cheia, mas não houve (o rio estava baixo);
- só com o rio, o dia 4 (3,5 m) dava cheia, mas não houve (quase não choveu).

Mensagem: "Vocês acabaram de fazer à mão o que a máquina faz no treino: procurar as perguntas e os números que melhor separam os exemplos. A máquina faz isto com milhares de exemplos, em menos de um segundo."

Peçam aos pares que guardem as perguntas: servem para a actividade seguinte."""

votos = ["sim", "sim", "não", "sim", "sim", "não", "sim"]
S["m2-floresta"] = slide("m2-floresta", "Muitas árvores a votar: a floresta", coluna(
    p("Uma árvore sozinha pode enganar-se. Uma <b>floresta aleatória</b> (Random Forest) junta muitas árvores, "
      "cada uma aprendida com exemplos um pouco diferentes. Todas votam:"),
    B.tabela(["Árvore"] + [str(i) for i in range(1, 8)], [["Cheia?"] + votos], [16] + [12] * 7, tam=30,
             alinh=["left"] + ["center"] * 7),
    destaque("5 votos contra 2: a resposta é «sim». Como pedir a opinião a vários amigos."),
    p("Na Aula 2, a floresta tem 100 árvores.", 28, SUAVE), gap=32))
NOTAS["m2-floresta"] = """FACILITADOR 2, cerca de 2,5 minutos.

"Uma árvore sozinha pode enganar-se, sobretudo nos casos difíceis. A solução: muitas árvores. Uma FLORESTA ALEATÓRIA (em inglês, Random Forest) treina muitas árvores, cada uma com uma parte diferente dos exemplos, escolhida ao acaso. Por isso cada árvore aprende perguntas um pouco diferentes.

Para um caso novo, todas votam. Aqui, 5 árvores dizem 'cheia' e 2 dizem 'sem cheia': ganha a maioria.

É como quando têm uma dúvida e perguntam a vários amigos: um pode enganar-se, mas a maioria engana-se menos. E se quase todas concordam, temos mais confiança na resposta."

Na Aula 2, a floresta tem 100 árvores, e erra muito menos do que uma árvore sozinha."""

S["m2-actividade-votar"] = slide("m2-actividade-votar", "Actividade: a turma é uma floresta", linha(
    coluna(lista(["Usem as vossas perguntas nos dias X e Y, que não estavam na tabela.",
                  "Cada par vota: houve cheia no dia X? E no dia Y?",
                  "Contamos os votos: ganha a maioria."], num=True), gap=24, extra="flex:1"),
    B.tabela(["Dia", "Chuva na semana (mm)", "Nível do rio (m)", "Houve cheia?"],
             [["X", "160", "3,6", "?"], ["Y", "110", "2,9", "?"]], [12, 33, 28, 27], tam=30,
             alinh=["center", "center", "center", "center"], largura=820), gap=48, alinhar="center"))
NOTAS["m2-actividade-votar"] = """FACILITADOR 2. Actividade com a turma toda, cerca de 3 minutos. Os mesmos dados inventados.

1. Cada par aplica as suas perguntas aos dias X e Y (30 segundos).
2. Mãos no ar: "quem diz que houve cheia no dia X?" Contem. "E no dia Y?" Contem.
3. Ganha a maioria.

O que deve acontecer:
- Dia X (160 mm, 3,6 m): quase todos dizem CHEIA. Votação clara: muita confiança.
- Dia Y (110 mm, 2,9 m): os votos dividem-se, porque cada par escolheu números diferentes (uns dizem que 2,9 m é alto, outros não). No jogo, não houve cheia.

Mensagem: "Cada par é uma árvore diferente, porque escolheu perguntas diferentes. Quando quase todos concordam, a floresta está segura; quando se dividem, o caso é difícil. A floresta da Aula 2 faz isto com 100 árvores." """


# ============================== PREVER UM NÚMERO E O PROJECTO ==============================

S["m2-regressao"] = slide("m2-regressao", "Prever um número: a regressão", linha(
    figura("regr_estudo", "Gráfico de pontos: horas de estudo e nota de 26 alunos, a preto, com a recta aprendida a vermelho", 780,
           "Dados inventados para o exemplo."),
    coluna(p("Cada ponto é um aluno: as horas de estudo por semana e a nota do exame."),
           p("O modelo é uma <b>recta</b> que passa pelo meio dos pontos. A máquina aprende onde a pôr."),
           destaque("Na Aula 4: quanta água vai passar no rio daqui a 3 dias."), gap=28, extra="flex:1"), gap=48))
NOTAS["m2-regressao"] = """FACILITADOR 2, cerca de 2,5 minutos. Dados inventados (dizê-lo à turma).

"Agora a resposta é um NÚMERO: a nota do exame, de 0 a 20. Cada ponto é um aluno: quantas horas estudou por semana e que nota teve.

O modelo mais simples é uma RECTA que passa pelo meio dos pontos. Treinar é encontrar a recta que fica mais perto de todos: a máquina começa com uma recta qualquer e vai-a corrigindo (lembrem-se do cesto). Os traços cinzentos são o erro de cada aluno.

Depois, para um aluno novo que estuda 10 horas, a recta prevê cerca de 16 valores. É uma previsão: pode errar.

Na Aula 4 fazemos o mesmo com o rio Incomáti: as pistas são a água que passa hoje e a chuva dos últimos dias; a resposta é a água que vai passar daqui a 3 dias."

Pergunta à sala: "o modelo garante que esse aluno tem 16?" (Não: é uma previsão, com erro.)"""

S["m2-projecto"] = slide("m2-projecto", "E no projecto EYES TO EARTH?", coluna(
    linha(bloco("Onde está a água?", "com as imagens de satélite", "flex:1", tam=30),
          bloco("Vai haver cheia nos próximos dias?", "com a água do rio e a chuva", "flex:1", tam=30),
          bloco("A água do rio está turva?", "com a cor da água e a maré", "flex:1", tam=30),
          gap=32, alinhar="stretch"),
    destaque("Os mesmos passos de hoje: exemplos com respostas, treinar, prever e testar."), gap=48))
NOTAS["m2-projecto"] = """FACILITADOR 2, cerca de 2 minutos.

"No projecto EYES TO EARTH, a máquina ajuda a responder a três perguntas sobre o rio Incomáti, em Marracuene:
1. Onde está a água agora? Com as imagens de satélite, como na Aula 1.
2. Vai haver cheia nos próximos dias? Com a água que o rio leva e a chuva, como na Aula 4.
3. A água do rio está turva (barrenta)? Com a cor da água vista do satélite e a maré, como na Aula 3.

E os passos são os mesmos que acabámos de ver: juntar exemplos com as respostas certas, treinar, prever, e testar com casos que o modelo nunca viu. As respostas aparecem na plataforma, que vão conhecer no Módulo 5."

Se perguntarem que algoritmo o projecto usa: muitas árvores, como a floresta, mas em fila, cada árvore a corrigir os erros da anterior (chama-se XGBoost). Não é preciso entrar em detalhes."""

S["m2-resumo"] = slide("m2-resumo", "O que aprendemos neste módulo", coluna(
    lista(["A máquina aprende com <b>exemplos</b> que têm a resposta certa: o <b>rótulo</b>.",
           "<b>Treinar</b> é errar e corrigir; <b>prever</b> é responder num caso novo.",
           "<b>Classificação</b> dá uma categoria; <b>regressão</b> dá um número.",
           "<b>Árvore</b>: perguntas de sim ou não. <b>Floresta</b>: muitas árvores a votar."], 32),
    p("A seguir: o quiz, e como sabemos se um modelo é bom (Módulo 3).", 30, SUAVE), gap=36))
NOTAS["m2-resumo"] = f"""FACILITADOR 2, cerca de 1,5 minutos. Depois, {MINUTOS_DE_PERGUNTAS} minutos de perguntas da turma, até às 09:55.

"Quatro ideias para levar:
1. A máquina aprende com exemplos que têm a resposta certa, como vocês aprenderam a distinguir um cão de um gato.
2. Treinar é errar e corrigir, muitas vezes; prever é responder num caso novo.
3. Se a resposta é uma categoria, é classificação; se é um número, é regressão.
4. A árvore faz perguntas de sim ou não; a floresta junta muitas árvores a votar.

Na prática, vão fazer tudo isto com as vossas mãos, no Jupyter Notebook."

Perguntas da turma: abram {MINUTOS_DE_PERGUNTAS} minutos. Se ninguém perguntar, perguntem vocês: "o que é um rótulo?", "porque é que a floresta erra menos do que uma árvore?". A seguir, o quiz relâmpago (09:55)."""


def tipografia(texto, sid=""):
    """As aspas à portuguesa nas notas: "fala" passa a «fala» e 'citação' a “citação” (os pares têm de fechar)."""
    for recta, (abre, fecha) in (('"', ("«", "»")), ("'", ("“", "”"))):
        partes = texto.split(recta)
        assert len(partes) % 2 == 1, (sid, f"aspas {recta} desemparelhadas")
        texto = "".join(parte + (abre if i % 2 == 0 else fecha) for i, parte in enumerate(partes[:-1])) + partes[-1]
    return texto


def html(sid):
    """O slide pronto, já com a nota do facilitador (com as aspas à portuguesa) no lugar do marcador."""
    marcador = f"<aside>§NOTA:{sid}§</aside>"
    assert S[sid].count(marcador) == 1, sid
    assert not any(c in NOTAS[sid] for c in "<>&"), (sid, "a nota tem um carácter de HTML")
    return S[sid].replace(marcador, f"<aside>{tipografia(NOTAS[sid].strip(), sid)}</aside>")


def minutos(nota):
    """Os minutos que a nota diz (o primeiro «cerca de N minutos»)."""
    m = re.search(r"cerca de (\d+(?:,\d+)?) minutos?", nota)
    return float(m.group(1).replace(",", ".")) if m else 0.0
