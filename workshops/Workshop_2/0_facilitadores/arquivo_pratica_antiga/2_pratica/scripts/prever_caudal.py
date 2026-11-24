"""prever_caudal.py · regressão: prever o caudal do Incomáti em Marracuene daqui a alguns dias.

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
import argparse
import os
import sys

import matplotlib

if "ipykernel" not in sys.modules:                      # num terminal: desenha para ficheiro, sem janela
    matplotlib.use("Agg")                               # (no Jupyter, com %run, os gráficos aparecem no notebook)
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import configuracao  # noqa: E402
import pandas as pd  # noqa: E402
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
    plt.title(f"Cheia de janeiro de 2026 · {nome}")
    plt.legend()
    grafico = os.path.join(pasta, "previsao_caudal_2026.png")
    plt.savefig(grafico, dpi=120, bbox_inches="tight")
    print("\nGráfico guardado em", os.path.relpath(grafico))
    configuracao.guardar(pasta, {"notas": resultados, "igual_a_hoje_MAE_exame": float(igual)}, c, modelo, saida)


if __name__ == "__main__":
    principal()
