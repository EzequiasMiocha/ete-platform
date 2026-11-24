"""A ordem dos slides do Workshop 2: a ÚNICA fonte dos números dos slides.

Os slides (slides.py), o plano do dia e o manual (build_workshop2_docs.py) e o cronograma em Word
(build_workshop2_cronograma_docx.py) leem daqui. Se um slide mudar de lugar, os números mudam em todo o lado.
"""

ORDEM = [
    # Abertura (08:00–08:35)
    "capa", "missao", "dia-manha", "dia-tarde", "inquerito", "revisao-luz", "revisao-regra", "revisao-2021", "revisao-2024",
    # Módulo 1 (08:35–09:05)
    "m1", "m1-regras", "m1-ia-ml-dl", "m1-telemovel", "m1-todos-os-dias", "m1-seguranca", "m1-armas", "m1-aprende",
    "m1-actividade", "m1-gancho",
    # Módulo 2 (09:05–09:55)
    "m2", "m2-modelo", "m2-modelo-exemplos", "m2-dados", "m2-python", "m2-tipos", "m2-supervisionada",
    "m2-supervisionada-exemplos", "m2-classificacao", "m2-regressao", "m2-treinar", "m2-regressao-rio",
    "m2-nao-supervisionada", "m2-reforco", "m2-actividade-tipos", "m2-algoritmos",
    "m2-arvore", "m2-arvore-caixas", "m2-floresta", "m2-floresta-porque", "m2-knn", "m2-rede", "m2-deep-learning",
    "m2-actividade", "m2-actividade-votar",
    # Quiz (09:55–10:05)
    "quiz", "quiz-1", "quiz-2", "quiz-3", "quiz-4", "quiz-5",
    # Módulo 3 (10:05–10:35)
    "m3", "m3-fluxo", "m3-divisao", "m3-futuro", "m3-rotulos", "m3-regra-de-ouro", "m3-exame-erro", "m3-matriz",
    "m3-notas", "m3-iou", "m3-notas-regressao", "m3-ajuste", "m3-complexidade", "m3-hiperparametros", "m3-decorar",
    "m3-verificacao",
    # Módulo 4 (10:35–11:00)
    "m4", "m4-o-que-ve", "m4-cor", "m4-trocos", "m4-anomalias", "m4-ia-turbidez", "m4-nao-mede", "m4-actividade",
    # Módulo 5 (11:00–11:20)
    "m5", "m5-dado-alerta", "m5-gatilhos", "m5-niveis", "m5-paginas", "m5-demo", "m5-oficiais", "m5-actividade",
    # Intervalo e prática (11:20–13:25)
    "intervalo", "pratica", "pratica-jupyter", "pratica-aulas", "pratica-aula1", "pratica-aula2", "pratica-anos",
    "pratica-aula3", "pratica-aula4",
    # Apresentações e resultados (13:25–13:40)
    "apresentacoes", "resultados", "resultados-2024", "resultados-modelos",
    # Encerramento (13:40–14:00)
    "licoes", "continuar", "inquerito-final", "obrigado",
]

# O texto do rodapé de cada parte (começa no slide indicado)
SECCOES = {"capa": "Abertura", "m1": "Módulo 1: O que é a Inteligência Artificial?", "m2": "Módulo 2: Como uma máquina aprende",
           "quiz": "Quiz relâmpago", "m3": "Módulo 3: Como sabemos se o modelo é bom?",
           "m4": "Módulo 4: A IA e a qualidade da água", "m5": "Módulo 5: A plataforma EYES TO EARTH",
           "intervalo": "Prática em pares", "apresentacoes": "Apresentações e resultados", "licoes": "Encerramento"}

# As secções do deck (o índice do visualizador de slides)
SECCOES_DECK = {
    "s-abertura": ("capa", "Abertura: o objectivo e o programa do dia, o questionário OAD e a revisão do Workshop 1"),
    "s-m1": ("m1", "Módulo 1: o que são a Inteligência Artificial, o Machine Learning e o Deep Learning"),
    "s-m2": ("m2", "Módulo 2: como uma máquina aprende: com rótulos (classificação e regressão), sem rótulos "
                   "e por reforço, e quatro algoritmos"),
    "s-quiz": ("quiz", "Quiz relâmpago sobre os Módulos 1 e 2, uma pergunta por slide"),
    "s-m3": ("m3", "Módulo 3: treino e teste, a matriz de confusão, as notas, subajuste e sobreajuste, hiperparâmetros"),
    "s-m4": ("m4", "Módulo 4: o que o satélite vê na água, os 9 troços do rio e o que não mede"),
    "s-m5": ("m5", "Módulo 5: a plataforma EYES TO EARTH, do dado ao alerta"),
    "s-pratica": ("intervalo", "Intervalo e prática em pares no Jupyter Notebook: quatro temas (classificação, treino e teste, "
                               "a qualidade da água e a maré, e regressão), cada um com uma aula guiada e uma prática em que os pares escrevem o código"),
    "s-resultados": ("apresentacoes", "Apresentações dos pares e todos os modelos lado a lado"),
    "s-fecho": ("licoes", "Encerramento: conclusões, questionário final e certificados"),
}

NUM = {sid: i for i, sid in enumerate(ORDEM, start=1)}


def numero(sid):
    """O número do slide (1, 2, 3...)."""
    return NUM[sid]


def intervalo(primeiro, ultimo):
    """'16–41': do primeiro ao último slide de uma parte do dia."""
    a, b = NUM[primeiro], NUM[ultimo]
    return str(a) if a == b else f"{a}–{b}"


def ultimo_antes(sid):
    """O slide imediatamente antes de sid (para os intervalos de cada parte)."""
    return ORDEM[NUM[sid] - 2]
