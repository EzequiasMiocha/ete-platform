"""configuracao.py · ler a configuração dos scripts e preparar a pasta dos resultados.

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
PADRAO = {'classificacao': {'modelo': 'floresta',
                            'pontos': None,
                            'caracteristicas': ['azul', 'verde', 'vermelho', 'nir', 'swir', 'ndwi', 'mndwi', 'ndvi'],
                            'terreno': False,
                            'raio_do_ponto': 2,
                            'n_arvores': 100,
                            'profundidade_maxima': None,
                            'folhas_minimas': 1,
                            'pesos_das_classes': None,
                            'limiar': 0.5,
                            'ensinar_ano': None,
                            'semente': 0},
          'agrupamento': {'k_grupos': 4,
                          'inicializacoes': 3,
                          'caracteristicas': ['azul', 'verde', 'vermelho', 'nir', 'swir', 'ndwi', 'mndwi', 'ndvi'],
                          'semente': 0},
          'regressao': {'dias_a_frente': 3,
                        'pistas': ['caudal_m3s', 'chuva_7d_mm', 'chuva_14d_mm', 'chuva_30d_mm'],
                        'ultimo_ano_de_treino': 2018,
                        'modelo': 'linear',
                        'profundidade': None,
                        'semente': 0},
          'saida': {'pasta': 'resultados', 'guardar_modelo': True}}


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
            sys.exit(f"Erro no ficheiro {caminho}, linha {erro.lineno}, coluna {erro.colno}: {erro.msg}.\n"
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
