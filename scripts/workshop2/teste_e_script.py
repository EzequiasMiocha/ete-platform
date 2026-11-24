"""Teste do aluno (IA, 16 perguntas com correcção automática) e os scripts em Python puro da prática."""

import base64
import json
import pprint

from .comum import (ANOS_TESTE, FERRAMENTAS_IA, HORIZONTE, K_GRUPOS, LEGENDA, PISTAS_CAUDAL, PRATICA,
                    ULTIMO_ANO_TREINO, WS2, code, escrever, md)

PERGUNTAS = [
    ("Um filtro de spam aprende a reconhecer spam a partir de...\n\n"
     "a) regras escritas à mão por um programador  \nb) muitos exemplos de mensagens já marcadas como spam ou normal",
     "b", "letra", "Isto é Machine Learning: aprender com exemplos em vez de escrever as regras."),
    ("Em Machine Learning, o **rótulo** de um exemplo é...\n\na) a resposta certa (por exemplo, \"água\")  \nb) uma banda do satélite",
     "a", "letra", "O rótulo é a resposta certa que damos ao modelo para ele aprender. As bandas são características (as pistas)."),
    ("Uma árvore de decisão tem a pergunta \"NIR > 0,25?\". Se sim: vegetação. Se não: água. "
     "Um píxel tem NIR = 0,40. O que diz a árvore?\n\na) água  \nb) vegetação",
     "b", "letra", "0,40 é maior do que 0,25, por isso a resposta é \"sim\": vegetação."),
    ("Um Random Forest decide...\n\na) pela árvore mais antiga  \nb) pela votação de muitas árvores",
     "b", "letra", "Cada árvore vota; ganha a classe com mais votos. A parte dos votos é a probabilidade."),
    ("Prever o caudal do rio daqui a 3 dias (um número, em m³/s) é um problema de...\n\n"
     "a) classificação  \nb) regressão  \nc) agrupamento",
     "b", "letra", "A resposta é um número: regressão. A classificação dá uma categoria; o agrupamento junta coisas parecidas sem rótulos."),
    ("Um scanner de aeroporto aprendeu com milhares de malas marcadas como \"arma\" ou \"sem arma\". Isto é...\n\n"
     "a) classificação supervisionada  \nb) agrupamento não supervisionado",
     "a", "letra", "Há rótulos (as malas marcadas por pessoas) e a resposta é uma categoria: classificação supervisionada."),
    ("No Tema 3, uma floresta tentou prever a água turva com o caudal, a chuva e o mês, e acertou menos do que dizer sempre "
     "\"turva\". O que fez o acerto subir?\n\na) juntar a altura da maré às pistas  \nb) pôr mais árvores na floresta",
     "a", "letra", "A maré era a pista que faltava. Escolher as pistas certas vale mais do que o algoritmo."),
    ("No método dos **k vizinhos mais próximos**, com k = 5, um píxel novo tem 3 vizinhos \"água\" e 2 vizinhos \"terra\". "
     "O que diz o modelo?\n\na) água  \nb) terra",
     "a", "letra", "Ganha a classe da maioria dos vizinhos: 3 contra 2, água."),
    ("Num exame com 200 píxeis, o modelo acerta 184. Qual é o acerto, em percentagem?",
     92, "numero", "184 ÷ 200 = 0,92 = 92%."),
    ("O modelo prevê 80 ha de água; a água verdadeira tem 100 ha; os dois mapas coincidem em 70 ha. "
     "Qual é o **IoU**? (intersecção ÷ união; escreva com ponto, por exemplo 0.5)",
     0.64, "numero", "União = 80 + 100 − 70 = 110 ha. IoU = 70 ÷ 110 = 0,64."),
    ("Uma regressão prevê o caudal com um **erro médio (MAE)** de 26 m³/s. Isto quer dizer que...\n\n"
     "a) em média, a previsão fica a 26 m³/s do caudal verdadeiro  \nb) o modelo acerta 26% das vezes",
     "a", "letra", "O MAE é a média dos erros, nas mesmas unidades da resposta (m³/s). Quanto menor, melhor."),
    ("Um modelo acerta 100% nos exemplos de treino e 70% em dados novos. O que aconteceu?\n\n"
     "a) está óptimo  \nb) decorou os exemplos em vez de aprender (sobreajuste)",
     "b", "letra", "Acertar só no que já viu é decorar. A nota que conta é a dos dados novos."),
    ("A **regra de ouro** do teste diz que se deve testar com...\n\n"
     "a) rótulos feitos pelo próprio modelo  \nb) rótulos independentes, de dados que o modelo nunca viu",
     "b", "letra", "Testar com os rótulos do próprio modelo dá sempre nota alta e não prova nada."),
    ("O que o satélite **consegue** ver na água?\n\na) a turbidez (água barrenta)  \nb) as bactérias  \nc) o pH",
     "a", "letra", "O satélite vê a cor da água: turbidez, sedimentos, sinais de algas e plantas, temperatura. Bactérias e pH não."),
    ("A plataforma diz que a água do rio está \"normal\". Isso quer dizer que é própria para beber?\n\na) sim  \nb) não",
     "b", "letra", "Não. O satélite não mede bactérias, metais nem nutrientes. A água do rio deve ser sempre tratada antes de beber."),
    ("O **Deep Learning** é...\n\na) Machine Learning com redes neuronais de muitas camadas  \nb) um satélite novo",
     "a", "letra", "Redes neuronais com muitas camadas, que precisam de muitos exemplos; estão no reconhecimento facial e no ChatGPT."),
]


def teste():
    gabarito = [[r, t, e] for _, r, t, e in PERGUNTAS]
    pacote = base64.b64encode(json.dumps(gabarito, ensure_ascii=False).encode()).decode()
    c = [md(f"""
# Teste do aluno · Inteligência Artificial para a água ({len(PERGUNTAS)} perguntas)

Responda trocando os `...` e corra a célula: aparece logo ✅ ou ❌ com a explicação. No fim, a sua nota.

{LEGENDA}
"""),
         code(f"""
# Célula 0 · corrector: corra sem mudar nada ▶️
import base64, json
_GABARITO = json.loads(base64.b64decode("{pacote}").decode())
_NOTAS = {{}}


def corrigir(numero, resposta):
    certa, tipo, explicacao = _GABARITO[numero - 1]
    if resposta is ...:
        print("✏️ Ainda não respondeu.")
        return
    if tipo == "numero":
        acertou = abs(float(resposta) - certa) <= 0.01 * max(1, abs(certa))
    else:
        acertou = str(resposta).strip().lower().startswith(certa)
    _NOTAS[numero] = acertou
    print(("✅ Certo! " if acertou else f"❌ Não. A resposta é {{certa}}. ") + explicacao)


def resultado():
    certas = sum(_NOTAS.values())
    print(f"Respondeu a {{len(_NOTAS)}} de {{len(_GABARITO)}} perguntas e acertou {{certas}}.")
    if len(_NOTAS) == len(_GABARITO):
        print(f"Nota: {{20 * certas / len(_GABARITO):.0f}} valores em 20.")


print("Corrector pronto.")
""")]
    for i, (pergunta, _, tipo, _) in enumerate(PERGUNTAS, start=1):
        c.append(md(f"### Pergunta {i}\n\n{pergunta}"))
        dica = "# um número, por exemplo 12 ou 0.5" if tipo == "numero" else '# a letra entre aspas, por exemplo "a"'
        c.append(code(f"resposta_{i} = ...      {dica}\ncorrigir({i}, resposta_{i})"))
    c.append(md("## A sua nota ▶️"))
    c.append(code("resultado()"))
    return c


# ---------- os scripts em Python puro: configurados por configuracao.json, resultados guardados em resultados/ ----------

TODAS = ["azul", "verde", "vermelho", "nir", "swir", "ndwi", "mndwi", "ndvi"]
SEMENTE = "número da sorte: o mesmo número dá sempre o mesmo resultado (null = um resultado diferente de cada vez)"
CONFIGURACAO = {
    "_leia_me": ("Configuração dos scripts da prática (pasta scripts/). Mude um valor, guarde (Ctrl + S) e corra o script outra vez. "
                 "As opções da linha de comandos (por exemplo --arvores 300) têm prioridade sobre este ficheiro. "
                 "Regras do JSON: texto entre aspas duplas, vírgula entre os valores, null = sem valor, true/false = sim/não. "
                 "Cada secção tem uma _ajuda que explica as opções; os scripts ignoram tudo o que começa por _."),
    "classificacao": {
        "_ajuda": {
            "modelo": "o algoritmo: floresta, arvore, vizinhos ou rede",
            "pontos": "ficheiro .json com os pontos marcados, por exemplo os_nossos_pontos.json (null = os pontos da equipa)",
            "caracteristicas": "o que o modelo vê em cada píxel: azul, verde, vermelho, nir, swir, ndwi, mndwi, ndvi, hand, altitude, declive",
            "terreno": "true = juntar o terreno (hand, altitude e declive) às características",
            "raio_do_ponto": "cada ponto marcado vale um quadrado de (2 x raio + 1) x (2 x raio + 1) píxeis",
            "n_arvores": "número de árvores do Random Forest (mais árvores = votação mais estável, mas mais lenta)",
            "profundidade_maxima": "quantas perguntas seguidas cada árvore pode fazer (null = sem limite)",
            "folhas_minimas": "quantos exemplos, no mínimo, em cada folha da árvore (mais = árvore mais simples)",
            "pesos_das_classes": "null ou \"balanced\" (dar o mesmo peso à água e à terra, mesmo com mais pontos de uma delas)",
            "limiar": "probabilidade a partir da qual o modelo diz água, de 0 a 1 (mais baixo = encontra mais água, mas com mais falsos alarmes)",
            "ensinar_ano": "null ou um ano (2014, 2021, 2022, 2024, 2025): junta os pontos da equipa desse ano e treina outra vez",
            "semente": SEMENTE},
        "modelo": "floresta", "pontos": None, "caracteristicas": TODAS, "terreno": False, "raio_do_ponto": 2,
        "n_arvores": 100, "profundidade_maxima": None, "folhas_minimas": 1, "pesos_das_classes": None, "limiar": 0.5,
        "ensinar_ano": None, "semente": 0},
    "agrupamento": {
        "_ajuda": {
            "k_grupos": "em quantos grupos o K-means divide os píxeis (de 2 a 10)",
            "inicializacoes": "quantas vezes o K-means recomeça com centros diferentes (fica com a melhor)",
            "caracteristicas": "o que o K-means compara em cada píxel: azul, verde, vermelho, nir, swir, ndwi, mndwi, ndvi",
            "semente": SEMENTE},
        "k_grupos": K_GRUPOS, "inicializacoes": 3, "caracteristicas": TODAS, "semente": 0},
    "regressao": {
        "_ajuda": {
            "dias_a_frente": "prever o caudal daqui a quantos dias (de 1 a 30)",
            "pistas": "colunas da tabela usadas como pistas: caudal_m3s, chuva_dia_mm, chuva_7d_mm, chuva_14d_mm, chuva_30d_mm",
            "ultimo_ano_de_treino": "o treino vai até este ano; o exame são os anos seguintes (o exame é o futuro)",
            "modelo": "linear (a recta) ou arvore (árvore de regressão)",
            "profundidade": "perguntas seguidas da árvore de regressão (null = sem limite)",
            "semente": SEMENTE},
        "dias_a_frente": HORIZONTE, "pistas": PISTAS_CAUDAL, "ultimo_ano_de_treino": ULTIMO_ANO_TREINO, "modelo": "linear",
        "profundidade": None, "semente": 0},
    "saida": {
        "_ajuda": {
            "pasta": "pasta dos resultados, dentro de 2_pratica (cada execução cria lá uma pasta nova com a data e a hora)",
            "guardar_modelo": "true = guardar também o modelo treinado (modelo.joblib), para o usar depois sem treinar outra vez"},
        "pasta": "resultados", "guardar_modelo": True},
}

MODULO_CONFIGURACAO = '''"""configuracao.py · ler a configuração dos scripts e preparar a pasta dos resultados.

A configuração está em 2_pratica/configuracao.json. Cada script lê a sua secção (classificacao, agrupamento ou
regressao); as opções da linha de comandos têm prioridade. Cada execução guarda tudo numa pasta nova dentro de
2_pratica/resultados/: as figuras, as notas (notas.json), o modelo treinado (modelo.joblib) e a configuração usada.
"""

import json
import os
import sys
from datetime import datetime

PASTA_SCRIPTS = os.path.dirname(os.path.abspath(__file__))
PASTA_PRATICA = os.path.dirname(PASTA_SCRIPTS)
# Os valores de origem: usados quando configuracao.json não existe ou não tem uma opção.
PADRAO = __PADRAO__


def ler(seccao, caminho=None):
    """A secção pedida da configuração: os valores do ficheiro por cima dos valores de origem.
    Avisa quando uma opção está mal escrita (em vez de a ignorar em silêncio)."""
    config = json.loads(json.dumps(PADRAO))
    dado = caminho is not None
    caminho = caminho or os.path.join(PASTA_PRATICA, "configuracao.json")
    if not os.path.exists(caminho):
        if dado:
            sys.exit(f"Não encontrei o ficheiro de configuração {caminho}.")
        print("Configuração: valores de origem (não encontrei", os.path.relpath(caminho) + ")")
        return config[seccao], config["saida"]
    with open(caminho, encoding="utf-8") as ficheiro:
        try:
            do_ficheiro = json.load(ficheiro)
        except json.JSONDecodeError as erro:
            sys.exit(f"Erro no ficheiro {caminho}, linha {erro.lineno}, coluna {erro.colno}: {erro.msg}.\\n"
                     'Veja as vírgulas e as aspas: o JSON usa aspas duplas ("...") e escreve null, true e false em minúsculas.')
    for chave, valores in do_ficheiro.items():
        if chave.startswith("_"):
            continue
        if chave not in config or not isinstance(valores, dict):
            print(f"Atenção: '{chave}' não é uma secção da configuração e foi ignorada.")
            continue
        for nome, valor in valores.items():
            if nome.startswith("_"):
                continue
            if nome in config[chave]:
                config[chave][nome] = valor
            else:
                print(f"Atenção: '{nome}' não é uma opção da secção '{chave}' (está bem escrito?) e foi ignorado. "
                      f"Opções: {', '.join(config[chave])}.")
    print("Configuração:", os.path.relpath(caminho))
    return config[seccao], config["saida"]


def escolha(config, nome, opcoes):
    """Confirma que o valor (ou cada valor, se for uma lista) é uma das opções permitidas."""
    valores = config[nome] if isinstance(config[nome], list) else [config[nome]]
    if not valores or any(v not in opcoes or isinstance(v, bool) != isinstance(opcoes[-1], bool) for v in valores):
        sys.exit(f"Configuração: '{nome}' = {json.dumps(config[nome], ensure_ascii=False)} não é válido. "
                 f"Opções: {json.dumps(opcoes, ensure_ascii=False)}.")


def numero(config, nome, minimo, maximo=None, inteiro=True, nulo=False):
    """Confirma que o valor é um número dentro dos limites (ou null, quando nulo=True)."""
    v = config[nome]
    if v is None and nulo:
        return
    tipo_certo = isinstance(v, int) if inteiro else isinstance(v, (int, float))
    if isinstance(v, bool) or not tipo_certo or v < minimo or (maximo is not None and v > maximo):
        limites = f"de {minimo} a {maximo}" if maximo is not None else f"maior ou igual a {minimo}"
        sys.exit(f"Configuração: '{nome}' = {json.dumps(v, ensure_ascii=False)} tem de ser um número "
                 f"{'inteiro ' if inteiro else ''}{limites}{' (ou null)' if nulo else ''}.")


def juntar(config, opcoes):
    """As opções da linha de comandos que foram dadas (não None) substituem as da configuração."""
    for chave, valor in vars(opcoes).items():
        if valor is not None and chave in config:
            config[chave] = valor
    return config


def pasta_de_resultados(nome, saida):
    """Uma pasta nova para esta execução, por exemplo resultados/2026-11-21_121500_ia_agua."""
    base = os.path.join(PASTA_PRATICA, saida["pasta"], datetime.now().strftime("%Y-%m-%d_%H%M%S") + "_" + nome)
    pasta, n = base, 1
    while os.path.exists(pasta):                        # duas execuções no mesmo segundo: _2, _3, ...
        n += 1
        pasta = f"{base}_{n}"
    os.makedirs(pasta)
    return pasta


def guardar(pasta, notas, config, modelo=None, saida=None):
    """Guarda as notas, a configuração usada e (se pedido) o modelo treinado."""
    with open(os.path.join(pasta, "notas.json"), "w", encoding="utf-8") as ficheiro:
        json.dump(notas, ficheiro, ensure_ascii=False, indent=1, default=float)
    with open(os.path.join(pasta, "configuracao_usada.json"), "w", encoding="utf-8") as ficheiro:
        json.dump(config, ficheiro, ensure_ascii=False, indent=1)
    if modelo is not None and (saida or {}).get("guardar_modelo", True):
        import joblib
        joblib.dump(modelo, os.path.join(pasta, "modelo.joblib"))
    print("Resultados guardados em", os.path.relpath(pasta), "->", ", ".join(sorted(os.listdir(pasta))))
'''

CABECALHO_SCRIPT = '''
import argparse
import os
import sys

import matplotlib

if "ipykernel" not in sys.modules:                      # num terminal: desenha para ficheiro, sem janela
    matplotlib.use("Agg")                               # (no Jupyter, com %run, os gráficos aparecem no notebook)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import configuracao  # noqa: E402
'''

SCRIPT = '''"""ia_agua.py · classificação supervisionada: treinar e testar a IA que encontra água, num só comando.

É o mesmo trabalho do notebook 2_ia_que_encontra_agua.ipynb, mas como um programa normal de Python, configurado
pelo ficheiro 2_pratica/configuracao.json (secção "classificacao"). Num terminal, a partir da pasta 2_pratica
(ou numa célula do Jupyter, com %run em vez de python):

    python scripts/ia_agua.py                               # com a configuração do ficheiro
    python scripts/ia_agua.py --modelo vizinhos             # outro algoritmo: floresta, arvore, vizinhos ou rede
    python scripts/ia_agua.py --pontos os_nossos_pontos.json --arvores 200 --limiar 0.3
    python scripts/ia_agua.py --ensinar 2021                # junta os pontos da equipa de 2021 e testa outra vez
    python scripts/ia_agua.py --terreno                     # junta o terreno (hand, altitude, declive) às pistas
    python scripts/ia_agua.py --caracteristicas nir swir mndwi   # só estas características
    python scripts/ia_agua.py --config outra_config.json    # outro ficheiro de configuração

Guarda em resultados/<data>_ia_agua/: o mapa, as notas (notas.json), o modelo (modelo.joblib) e a configuração usada.
"""
__CABECALHO__from ferramentas_ia import (BANDAS, INDICES, TERRENO, RandomForestClassifier, carregar, encontrar, exemplos,  # noqa: E402
                            json, juntar_terreno, mostrar_notas, notas, np, plt, prever)

ANOS = __ANOS__
MODELOS = ["floresta", "arvore", "vizinhos", "rede"]


def criar_modelo(c):
    """Os quatro algoritmos de classificação da teoria, com os hiperparâmetros da configuração."""
    from sklearn.neighbors import KNeighborsClassifier
    from sklearn.neural_network import MLPClassifier
    from sklearn.pipeline import make_pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.tree import DecisionTreeClassifier
    if c["modelo"] == "arvore":
        return DecisionTreeClassifier(max_depth=c["profundidade_maxima"], min_samples_leaf=c["folhas_minimas"],
                                      class_weight=c["pesos_das_classes"], random_state=c["semente"])
    if c["modelo"] == "vizinhos":
        return make_pipeline(StandardScaler(), KNeighborsClassifier(n_neighbors=5))
    if c["modelo"] == "rede":
        return make_pipeline(StandardScaler(), MLPClassifier(hidden_layer_sizes=(16, 16), max_iter=800, random_state=c["semente"]))
    return RandomForestClassifier(n_estimators=c["n_arvores"], max_depth=c["profundidade_maxima"], min_samples_leaf=c["folhas_minimas"],
                                  class_weight=c["pesos_das_classes"], random_state=c["semente"], n_jobs=-1)


def principal():
    p = argparse.ArgumentParser(description="Treina e testa um modelo que encontra água (Incomáti, 2026).")
    p.add_argument("--config", metavar="FICHEIRO", help="ficheiro de configuração (por omissão, 2_pratica/configuracao.json)")
    p.add_argument("--modelo", choices=MODELOS, help="o algoritmo")
    p.add_argument("--pontos", metavar="FICHEIRO", help="ficheiro .json com {\\"agua\\": [[linha, coluna], ...], \\"nao_agua\\": [...]}")
    p.add_argument("--arvores", dest="n_arvores", type=int, metavar="N", help="número de árvores do Random Forest")
    p.add_argument("--profundidade", dest="profundidade_maxima", type=int, metavar="N", help="profundidade máxima das árvores")
    p.add_argument("--limiar", type=float, metavar="P", help="probabilidade a partir da qual se diz água (por omissão 0.5)")
    p.add_argument("--ensinar", dest="ensinar_ano", type=int, choices=ANOS, metavar="ANO", help="juntar os pontos da equipa deste ano (2014, 2021, 2022, 2024 ou 2025) e treinar outra vez")
    p.add_argument("--terreno", action="store_true", default=None, help="usar também o terreno como característica")
    p.add_argument("--caracteristicas", nargs="+", metavar="NOME", help="as características (por exemplo: nir swir mndwi)")
    a = p.parse_args()
    c, saida = configuracao.ler("classificacao", a.config)
    c = configuracao.juntar(c, a)
    configuracao.escolha(c, "modelo", MODELOS)
    configuracao.escolha(c, "caracteristicas", BANDAS + INDICES + TERRENO)
    configuracao.escolha(c, "pesos_das_classes", [None, "balanced"])
    configuracao.escolha(c, "ensinar_ano", [None] + ANOS)
    configuracao.escolha(c, "terreno", [False, True])
    configuracao.numero(c, "n_arvores", 1, 2000)
    configuracao.numero(c, "profundidade_maxima", 1, 100, nulo=True)
    configuracao.numero(c, "folhas_minimas", 1, 1000)
    configuracao.numero(c, "raio_do_ponto", 0, 10)
    configuracao.numero(c, "limiar", 0, 1, inteiro=False)
    configuracao.numero(c, "semente", 0, nulo=True)

    with open(encontrar("exemplos_da_equipa.json"), encoding="utf-8") as ficheiro:
        equipa = json.load(ficheiro)
    if c["pontos"]:
        if not os.path.exists(c["pontos"]):
            sys.exit(f"Não encontrei o ficheiro de pontos {c['pontos']} (o caminho conta a partir da pasta onde corre o script).")
        with open(c["pontos"], encoding="utf-8") as ficheiro:
            pontos = json.load(ficheiro)
        if not {"agua", "nao_agua"} <= set(pontos):
            sys.exit('O ficheiro de pontos tem de ter as duas listas: "agua" e "nao_agua".')
    else:
        pontos = equipa["2026"]
    extra = dict(np.load(encontrar("camadas_extra.npz")))
    cheia = carregar("incomati_2026_cheia.npz")
    car = list(c["caracteristicas"]) + [t for t in TERRENO if c["terreno"] and t not in c["caracteristicas"]]
    usa_terreno = any(t in car for t in TERRENO)
    if usa_terreno:
        juntar_terreno(cheia, extra)

    X, y = exemplos(cheia, pontos["agua"], pontos["nao_agua"], car, raio=c["raio_do_ponto"])
    if c["ensinar_ano"]:
        img = carregar(f"incomati_{c['ensinar_ano']}_chuvosa.npz")
        if usa_terreno:
            juntar_terreno(img, extra)
        xa, ya = exemplos(img, equipa[str(c["ensinar_ano"])]["agua"], equipa[str(c["ensinar_ano"])]["nao_agua"], car,
                          raio=c["raio_do_ponto"])
        X, y = np.concatenate([X, xa]), np.concatenate([y, ya])
    modelo = criar_modelo(c).fit(X, y)
    limiar = c["limiar"]
    print(f"Modelo: {c['modelo']} | treino: {len(y)} píxeis | limiar {limiar} | características: {', '.join(car)}")
    print(f"Acerto nos exemplos de treino: {100 * (modelo.predict(X) == y).mean():.1f}% (não conta: o modelo já os viu)\\n")

    prob = prever(modelo, cheia, car)
    teste = (extra["ems_2026"] >= 0) & ~cheia["nuvem"]
    verdade = extra["ems_2026"][teste]
    nota_exame = notas(verdade, (prob[teste] > limiar).astype(int), prob[teste])
    mostrar_notas("Modelo (exame EMS 2026)", nota_exame)
    mostrar_notas("Regra MNDWI > 0", notas(verdade, (cheia["mndwi"][teste] > 0).astype(int)))
    print()
    rios = {}
    for ano in ANOS:
        img = carregar(f"incomati_{ano}_chuvosa.npz")
        if usa_terreno:
            juntar_terreno(img, extra)
        pa = prever(modelo, img, car)
        rio, terra = extra["verif_agua"] & ~img["nuvem"], extra["verif_terra"] & ~img["nuvem"]
        rios[ano] = 100 * (pa[rio] > limiar).mean()
        print(f"{ano} ({img['satelite']}): modelo encontra {rios[ano]:5.1f}% do rio certo"
              f" | regra MNDWI {100 * (img['mndwi'][rio] > 0).mean():5.1f}%"
              f" | falsos alarmes em terra alta {100 * (pa[terra] > limiar).mean():4.1f}%")

    pasta = configuracao.pasta_de_resultados("ia_agua", saida)
    plt.figure(figsize=(7, 10))
    plt.imshow((prob > limiar) & cheia["zona"] & ~cheia["nuvem"], cmap="Blues")
    plt.title(f"Água segundo o modelo ({c['modelo']}) · 24 jan 2026")
    plt.axis("off")
    mapa = os.path.join(pasta, "mapa_ia_2026.png")
    plt.savefig(mapa, dpi=120, bbox_inches="tight")
    print("\\nMapa guardado em", os.path.relpath(mapa))
    configuracao.guardar(pasta, {"exame_ems_2026": nota_exame, "rio_encontrado_por_ano": rios, "pixeis_treino": int(len(y))},
                         c, modelo, saida)


if __name__ == "__main__":
    principal()
'''

SCRIPT_KMEANS = '''"""agrupar_pixeis.py · aprendizagem não supervisionada: o K-means junta os píxeis parecidos em K grupos.

É o mesmo trabalho da Parte E do notebook 3_sem_rotulos_e_numeros.ipynb, configurado pelo ficheiro
2_pratica/configuracao.json (secção "agrupamento"). A partir da pasta 2_pratica:

    python scripts/agrupar_pixeis.py            # K da configuração
    python scripts/agrupar_pixeis.py --k 6
    python scripts/agrupar_pixeis.py --k 3 --caracteristicas nir swir

Não usa nenhum rótulo para aprender. No fim, chama "água" aos grupos com MNDWI médio maior do que 0 (a regra do
Workshop 1), compara com o exame EMS e guarda em resultados/<data>_agrupar_pixeis/ o mapa, as notas e o modelo.
"""
__CABECALHO__from ferramentas_ia import BANDAS, INDICES, carregar, encontrar, mostrar_notas, notas, np, plt, tabela  # noqa: E402
from matplotlib.colors import ListedColormap  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.pipeline import make_pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402


def principal():
    p = argparse.ArgumentParser(description="Agrupa os píxeis da imagem da cheia com o K-means, sem rótulos.")
    p.add_argument("--config", metavar="FICHEIRO", help="ficheiro de configuração (por omissão, 2_pratica/configuracao.json)")
    p.add_argument("--k", dest="k_grupos", type=int, choices=range(2, 11), metavar="K", help="número de grupos, de 2 a 10")
    p.add_argument("--caracteristicas", nargs="+", metavar="NOME", help="as características (por exemplo: nir swir mndwi)")
    a = p.parse_args()
    c, saida = configuracao.ler("agrupamento", a.config)
    c = configuracao.juntar(c, a)
    configuracao.numero(c, "k_grupos", 2, 10)
    configuracao.numero(c, "inicializacoes", 1, 50)
    configuracao.numero(c, "semente", 0, nulo=True)
    configuracao.escolha(c, "caracteristicas", BANDAS + INDICES)

    cheia = carregar("incomati_2026_cheia.npz")
    extra = dict(np.load(encontrar("camadas_extra.npz")))
    car = list(c["caracteristicas"])
    X = tabela(cheia, car)
    valido = (cheia["zona"] & ~cheia["nuvem"]).ravel()
    k = c["k_grupos"]
    agrupador = make_pipeline(StandardScaler(), KMeans(n_clusters=k, n_init=c["inicializacoes"], random_state=c["semente"]))
    agrupador.fit(X[valido])
    grupos = agrupador.predict(X).reshape(cheia["verde"].shape)

    g_validos = grupos.ravel()[valido]
    mndwi_validos = cheia["mndwi"].ravel()[valido]      # o MNDWI só serve para dar nome aos grupos, não para os formar
    agua, por_grupo = [], {}
    for g in range(k):
        mndwi = float(np.nanmean(mndwi_validos[g_validos == g]))
        por_grupo[g] = {"percentagem": float(100 * (g_validos == g).mean()), "mndwi_medio": mndwi}
        print(f"Grupo {g}: {por_grupo[g]['percentagem']:4.1f}% dos píxeis | MNDWI médio {mndwi:+.2f}")
        if mndwi > 0:
            agua.append(g)
    teste = (extra["ems_2026"] >= 0) & ~cheia["nuvem"]
    verdade = extra["ems_2026"][teste]
    print()
    nota_exame = notas(verdade, np.isin(grupos[teste], agua).astype(int))
    mostrar_notas(f"K-means (K = {k}), água = {agua}", nota_exame)
    mostrar_notas("Regra MNDWI > 0", notas(verdade, (cheia["mndwi"][teste] > 0).astype(int)))

    pasta = configuracao.pasta_de_resultados("agrupar_pixeis", saida)
    plt.figure(figsize=(7, 10))
    plt.imshow(np.where(cheia["zona"] & ~cheia["nuvem"], grupos, np.nan), cmap=ListedColormap(plt.get_cmap("tab10").colors[:k]),
               vmin=-0.5, vmax=k - 0.5, interpolation="nearest")
    plt.colorbar(ticks=range(k), shrink=0.6, label="número do grupo")
    plt.title(f"Os {k} grupos do K-means · 24 jan 2026")
    plt.axis("off")
    mapa = os.path.join(pasta, "mapa_grupos_kmeans.png")
    plt.savefig(mapa, dpi=120, bbox_inches="tight")
    print("\\nMapa guardado em", os.path.relpath(mapa))
    configuracao.guardar(pasta, {"exame_ems_2026": nota_exame, "grupos_de_agua": agua, "grupos": por_grupo}, c, agrupador, saida)


if __name__ == "__main__":
    principal()
'''

SCRIPT_REGRESSAO = '''"""prever_caudal.py · regressão: prever o caudal do Incomáti em Marracuene daqui a alguns dias.

É o mesmo trabalho da Parte F do notebook 3_sem_rotulos_e_numeros.ipynb, configurado pelo ficheiro
2_pratica/configuracao.json (secção "regressao"). A partir da pasta 2_pratica:

    python scripts/prever_caudal.py                       # a recta (regressão linear), com a configuração do ficheiro
    python scripts/prever_caudal.py --dias 7
    python scripts/prever_caudal.py --profundidade 3       # uma árvore de regressão com 3 perguntas seguidas
    python scripts/prever_caudal.py --pistas chuva_7d_mm chuva_30d_mm   # só a chuva (sem o caudal de hoje)
    python scripts/prever_caudal.py --ultimo-ano 2022      # treinar até 2022 e fazer o exame com 2023-2026

Pistas: o caudal de hoje (GloFAS) e a chuva na bacia (CHIRPS). Treina até ao último ano de treino e faz o exame com
os anos seguintes (o exame é o futuro). Guarda em resultados/<data>_prever_caudal/ o gráfico da cheia de 2026, as notas
e o modelo.
"""
__CABECALHO__import pandas as pd  # noqa: E402
from ferramentas_ia import encontrar, metrics, plt  # noqa: E402
from sklearn.linear_model import LinearRegression  # noqa: E402
from sklearn.tree import DecisionTreeRegressor  # noqa: E402


def principal():
    p = argparse.ArgumentParser(description="Prevê o caudal do Incomáti daqui a N dias (regressão).")
    p.add_argument("--config", metavar="FICHEIRO", help="ficheiro de configuração (por omissão, 2_pratica/configuracao.json)")
    p.add_argument("--dias", dest="dias_a_frente", type=int, metavar="N", help="quantos dias à frente")
    p.add_argument("--profundidade", type=int, metavar="N", help="usar uma árvore de regressão com esta profundidade, em vez da recta")
    p.add_argument("--pistas", nargs="+", metavar="COLUNA", help="as pistas (colunas da tabela caudal_e_chuva_diarios.csv)")
    p.add_argument("--ultimo-ano", dest="ultimo_ano_de_treino", type=int, metavar="ANO", help="último ano do treino; o exame são os anos seguintes")
    a = p.parse_args()
    c, saida = configuracao.ler("regressao", a.config)
    c = configuracao.juntar(c, a)
    if a.profundidade:
        c["modelo"] = "arvore"
    serie = pd.read_csv(encontrar("caudal_e_chuva_diarios.csv"), parse_dates=["data"])
    configuracao.escolha(c, "modelo", ["linear", "arvore"])
    configuracao.escolha(c, "pistas", [coluna for coluna in serie.columns if coluna != "data"])
    configuracao.numero(c, "dias_a_frente", 1, 30)
    configuracao.numero(c, "ultimo_ano_de_treino", 2006, 2025)
    configuracao.numero(c, "profundidade", 1, 50, nulo=True)
    configuracao.numero(c, "semente", 0, nulo=True)
    pistas, dias, ultimo = list(c["pistas"]), c["dias_a_frente"], c["ultimo_ano_de_treino"]

    serie["caudal_futuro"] = serie["caudal_m3s"].shift(-dias)
    serie = serie.dropna()
    treino = serie[serie["data"].dt.year <= ultimo]
    exame = serie[serie["data"].dt.year > ultimo]

    if c["modelo"] == "arvore":
        modelo = DecisionTreeRegressor(max_depth=c["profundidade"], random_state=c["semente"])
        nome = f"árvore de regressão (profundidade {c['profundidade']})"
    else:
        modelo = LinearRegression()
        nome = "regressão linear"
    modelo.fit(treino[pistas], treino["caudal_futuro"])
    if c["modelo"] != "arvore":
        equacao = " ".join(f"{coef:+.2f} × {pista}" for coef, pista in zip(modelo.coef_, pistas))
        print(f"Equação: caudal daqui a {dias} dias = {equacao} {modelo.intercept_:+.1f}")
    resultados = {}
    for parte, d in [(f"treino (até {ultimo})", treino), (f"exame ({ultimo + 1} em diante)", exame)]:
        prev = modelo.predict(d[pistas])
        mae, r2 = metrics.mean_absolute_error(d["caudal_futuro"], prev), metrics.r2_score(d["caudal_futuro"], prev)
        resultados[parte] = {"MAE": float(mae), "R2": float(r2)}
        print(f"{nome} · {parte}: erro médio {mae:5.1f} m³/s | R² {r2:.2f}")
    igual = metrics.mean_absolute_error(exame["caudal_futuro"], exame["caudal_m3s"])
    print(f"Dizer 'fica igual a hoje' · exame: erro médio {igual:5.1f} m³/s")

    pasta = configuracao.pasta_de_resultados("prever_caudal", saida)
    janela = exame[(exame["data"] >= "2025-12-20") & (exame["data"] <= "2026-02-15")]
    dia = janela["data"] + pd.Timedelta(days=dias)
    plt.figure(figsize=(11, 5))
    plt.plot(dia, janela["caudal_futuro"], color="black", lw=2, label="o que aconteceu")
    plt.plot(dia, modelo.predict(janela[pistas]), color="dimgray", lw=2, ls="--", label=f"previsto {dias} dias antes")
    for limite, cor in [(164, "goldenrod"), (376, "darkorange"), (970, "firebrick")]:
        plt.axhline(limite, color=cor, ls=":", lw=1)
    plt.ylabel("Caudal (m³/s)")
    plt.title(f"Cheia de Janeiro de 2026 · {nome}")
    plt.legend()
    grafico = os.path.join(pasta, "previsao_caudal_2026.png")
    plt.savefig(grafico, dpi=120, bbox_inches="tight")
    print("\\nGráfico guardado em", os.path.relpath(grafico))
    configuracao.guardar(pasta, {"notas": resultados, "igual_a_hoje_MAE_exame": float(igual)}, c, modelo, saida)


if __name__ == "__main__":
    principal()
'''


def construir():
    pasta = PRATICA / "scripts"
    pasta.mkdir(parents=True, exist_ok=True)
    ferramentas = FERRAMENTAS_IA.replace("# Célula 0 · ferramentas da aula: corra sem mudar nada ▶️",
                                         '"""Ferramentas da aula (as mesmas da Célula 0 dos notebooks)."""')
    ferramentas = ferramentas.replace('print("Ferramentas prontas.")', "")
    (pasta / "ferramentas_ia.py").write_text(ferramentas.strip() + "\n", encoding="utf-8")
    padrao = {seccao: {nome: valor for nome, valor in opcoes.items() if not nome.startswith("_")}
              for seccao, opcoes in CONFIGURACAO.items() if not seccao.startswith("_")}
    texto = pprint.pformat(padrao, width=110, sort_dicts=False).replace("\n", "\n" + " " * len("PADRAO = "))
    (pasta / "configuracao.py").write_text(MODULO_CONFIGURACAO.replace("__PADRAO__", texto), encoding="utf-8")
    for nome, texto in [("ia_agua.py", SCRIPT), ("agrupar_pixeis.py", SCRIPT_KMEANS), ("prever_caudal.py", SCRIPT_REGRESSAO)]:
        texto = texto.replace("__CABECALHO__", CABECALHO_SCRIPT.lstrip("\n")).replace("__ANOS__", repr(ANOS_TESTE))
        (pasta / nome).write_text(texto, encoding="utf-8")
    (PRATICA / "configuracao.json").write_text(json.dumps(CONFIGURACAO, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    exemplo = {"agua": [[366, 322], [937, 280], [412, 411]], "nao_agua": [[832, 85], [538, 454], [376, 667]]}
    (pasta / "os_nossos_pontos_exemplo.json").write_text(json.dumps(exemplo, indent=1), encoding="utf-8")
    return [pasta / "ferramentas_ia.py", pasta / "configuracao.py", pasta / "ia_agua.py", pasta / "agrupar_pixeis.py",
            pasta / "prever_caudal.py", pasta / "os_nossos_pontos_exemplo.json", PRATICA / "configuracao.json",
            escrever(teste(), WS2 / "3_teste_do_aluno/teste_ia.ipynb", "ETE WS2 · Teste do aluno")]
