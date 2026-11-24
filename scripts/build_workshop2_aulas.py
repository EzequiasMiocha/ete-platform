"""Gera e testa as 4 aulas práticas do Workshop 2 (versão dos alunos e versão resolvida dos facilitadores).

    .venv/bin/python scripts/build_workshop2_aulas.py

1. escreve Workshop_2/2_pratica/ferramentas.py, as 4 aulas dos alunos, o notebook de verificação e o teste do aluno;
2. faz as contas de referência (os números das notas dos facilitadores) com o mesmo ferramentas.py;
3. escreve as 4 aulas resolvidas em Workshop_2/0_facilitadores/aulas_resolvidas/;
4. corre tudo como no dia: as aulas dos alunos sem preencher nada (não pode haver erros) e as resolvidas (todas as
   respostas têm de dar «Certo!»). Guarda as resolvidas já corridas, com os modelos treinados e as separações.
Os textos das aulas estão em scripts/workshop2/aulas.py. Não edite os notebooks à mão.
"""

import base64
import sys as _sys
_sys.dont_write_bytecode = True                  # sem __pycache__ na pasta dos alunos
import importlib.util
import json
import os
import re
import shutil
import sys
import tempfile
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workshop2.aulas import AULAS, FICHEIROS, HORARIO, TITULOS  # noqa: E402
from workshop2.comum import ANO_POR_PAR, FAC, PRATICA, WS2, code, escrever, md  # noqa: E402
from workshop2.ferramentas_aulas import FERRAMENTAS  # noqa: E402
from workshop2.praticas import FICHEIROS_PRATICA, PRATICAS, RESPOSTAS_PRATICA  # noqa: E402
from workshop2.teste_e_script import PERGUNTAS  # noqa: E402

RESOLVIDAS = FAC / "aulas_resolvidas"
# Os dados das aulas: todos são usados (main() falha se aparecer na pasta dados/ um ficheiro que nenhuma aula usa)
DADOS = ["incomati_2026_cheia.npz", "incomati_2014_chuvosa.npz", "incomati_2021_chuvosa.npz", "incomati_2022_chuvosa.npz",
         "incomati_2024_chuvosa.npz", "incomati_2025_chuvosa.npz", "exemplos_da_equipa.json", "mapa_oficial_cheia_2026.npz",
         "cor_do_rio_e_mare.csv", "caudal_e_chuva_diarios.csv"]
PROFUNDIDADES = [1, 3, 5, 10, 20]             # as profundidades da árvore de regressão na Aula 4
EMOJIS = re.compile("[\U0001F300-\U0001FAFF☀-➿⬀-⯿️]")


# ---------------------------------------------------------------- 1. ferramentas.py

def escrever_ferramentas():
    pacote = base64.b64encode(json.dumps(RESPOSTAS_PRATICA, ensure_ascii=False).encode()).decode()
    destino = PRATICA / "ferramentas.py"
    destino.write_text(FERRAMENTAS.replace("__RESPOSTAS__", pacote), encoding="utf-8")
    return destino


# ---------------------------------------------------------------- 2. as contas de referência

def referencia():
    """As mesmas contas das aulas, com o mesmo ferramentas.py: os números das notas dos facilitadores."""
    import matplotlib
    matplotlib.use("Agg")
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LinearRegression
    from sklearn.tree import DecisionTreeClassifier, DecisionTreeRegressor

    antes = os.getcwd()
    os.chdir(PRATICA)
    try:
        spec = importlib.util.spec_from_file_location("ferramentas", PRATICA / "ferramentas.py")
        F = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(F)
        R = {}
        cheia = F.carregar("incomati_2026_cheia.npz")
        pontos = F.pontos_da_equipa(2026)
        # Aula 1
        l, c = pontos["agua"][0]
        l2, c2 = pontos["nao_agua"][0]
        R["a1_swir_agua"], R["a1_swir_terra"] = float(cheia["swir"][l, c]), float(cheia["swir"][l2, c2])
        ex = F.tabela_de_exemplos(cheia, pontos["agua"], pontos["nao_agua"])
        R["a1_n"], R["a1_n_agua"] = len(ex), int((ex["rótulo"] == 1).sum())
        R["a1_regra_010"] = F.acerto(ex["rótulo"], (ex["swir"] < 0.10).astype(int))
        R["a1_regra_005"] = F.acerto(ex["rótulo"], (ex["swir"] < 0.05).astype(int))
        arvore = DecisionTreeClassifier(max_depth=2, random_state=0).fit(ex[F.BANDAS], ex["rótulo"])
        R["a1_limiar_arvore"] = float(arvore.tree_.threshold[0])
        R["a1_acerto_arvore"] = F.acerto(ex["rótulo"], arvore.predict(ex[F.BANDAS]))
        R["a1_ha_cheia"] = F.hectares(F.prever_mapa(arvore, cheia), cheia)
        # Aula 2
        tr = F.tabela_de_exemplos(cheia, pontos["agua"][:10], pontos["nao_agua"][:10])
        te = F.tabela_de_exemplos(cheia, pontos["agua"][10:], pontos["nao_agua"][10:])
        R["a2_n_treino"], R["a2_n_teste"] = len(tr), len(te)
        floresta = RandomForestClassifier(n_estimators=100, random_state=0).fit(tr[F.BANDAS], tr["rótulo"])
        R["a2_treino"] = F.acerto(tr["rótulo"], floresta.predict(tr[F.BANDAS]))
        R["a2_teste"] = F.acerto(te["rótulo"], floresta.predict(te[F.BANDAS]))
        uma = RandomForestClassifier(n_estimators=1, random_state=0).fit(tr[F.BANDAS], tr["rótulo"])
        R["a2_1arvore_treino"] = F.acerto(tr["rótulo"], uma.predict(tr[F.BANDAS]))
        R["a2_1arvore_teste"] = F.acerto(te["rótulo"], uma.predict(te[F.BANDAS]))
        v, p = F.exame_mapa_oficial(floresta, cheia)
        R["a2_ems"], R["a2_ems_n"] = F.acerto(v, p), len(v)
        R["a2_falsos"] = int(((v == 0) & (p == 1)).sum())
        R["a2_perdida"] = int(((v == 1) & (p == 0)).sum())
        # Aula 3: a cor do rio e a maré (o mesmo código da aula)
        rio = pd.read_csv(F.encontrar("cor_do_rio_e_mare.csv"))
        tr3, te3 = rio[rio["ano"] <= 2022], rio[rio["ano"] >= 2023]
        sem = ["caudal_m3s", "chuva_7d_mm", "mes"]
        f3 = RandomForestClassifier(n_estimators=100, random_state=0).fit(tr3[sem], tr3["turva"])
        R.update({"a3_n": len(rio), "a3_turva": float(rio["turva"].mean()),
                  "a3_nota_sem_mare": F.acerto(te3["turva"], f3.predict(te3[sem])), "a3_sempre_turva": float(te3["turva"].mean()),
                  "a3_turva_mare": {k: float(v) for k, v in F.turva_por_mare(rio).items()}})
        # Aula 4
        dias = pd.read_csv(F.encontrar("caudal_e_chuva_diarios.csv"), parse_dates=["data"])
        dias["caudal_daqui_a_3_dias"] = dias["caudal_m3s"].shift(-3)
        dias = dias.dropna()
        P, A = ["caudal_m3s", "chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"], "caudal_daqui_a_3_dias"
        treino, teste = dias[dias["data"].dt.year <= 2018], dias[dias["data"].dt.year >= 2019]
        R["a4_n_treino"], R["a4_n_teste"] = len(treino), len(teste)
        linear = LinearRegression().fit(treino[P], treino[A])
        R["a4_erro_treino"] = float((treino[A] - linear.predict(treino[P])).abs().mean())
        R["a4_erro_teste"] = float((teste[A] - linear.predict(teste[P])).abs().mean())
        R["a4_igual_a_hoje"] = float((teste[A] - teste["caudal_m3s"]).abs().mean())
        R["a4_profundidades"] = {}
        for prof in PROFUNDIDADES:
            t = DecisionTreeRegressor(max_depth=prof, random_state=0).fit(treino[P], treino[A])
            R["a4_profundidades"][prof] = {"treino": float((treino[A] - t.predict(treino[P])).abs().mean()),
                                           "teste": float((teste[A] - t.predict(teste[P])).abs().mean())}
        R["a4_melhor_profundidade"] = min(R["a4_profundidades"], key=lambda k: R["a4_profundidades"][k]["teste"])
        # Prática 1: a árvore de cada ano, com os pontos desse ano
        R["p1_anos"] = {}
        for ano in ANO_POR_PAR.values():
            img = F.carregar(f"incomati_{ano}_chuvosa.npz")
            pa = F.pontos_da_equipa(ano)
            ex = F.tabela_de_exemplos(img, pa["agua"], pa["nao_agua"])
            arv = DecisionTreeClassifier(max_depth=2, random_state=0).fit(ex[F.BANDAS], ex["rótulo"])
            R["p1_anos"][str(ano)] = {"dia": img["dia"], "satelite": img["satelite"], "exemplos": len(ex),
                                      "banda": F.BANDAS[arv.tree_.feature[0]], "limite": float(arv.tree_.threshold[0]),
                                      "hectares": F.hectares(F.prever_mapa(arv, img), img)}
        # Prática 2: a outra separação (os primeiros 5 + 5 pontos são o teste)
        tr2 = F.tabela_de_exemplos(cheia, pontos["agua"][5:], pontos["nao_agua"][5:])
        te2 = F.tabela_de_exemplos(cheia, pontos["agua"][:5], pontos["nao_agua"][:5])
        f2 = RandomForestClassifier(n_estimators=100, random_state=0).fit(tr2[F.BANDAS], tr2["rótulo"])
        v2, p2 = F.exame_mapa_oficial(f2, cheia)
        uma2 = RandomForestClassifier(n_estimators=1, random_state=0).fit(tr2[F.BANDAS], tr2["rótulo"])
        R.update({"p2_n_treino": len(tr2), "p2_n_teste": len(te2), "p2_treino": F.acerto(tr2["rótulo"], f2.predict(tr2[F.BANDAS])),
                  "p2_teste": F.acerto(te2["rótulo"], f2.predict(te2[F.BANDAS])), "p2_ems": F.acerto(v2, p2),
                  "p2_falsos": int(((v2 == 0) & (p2 == 1)).sum()), "p2_perdida": int(((v2 == 1) & (p2 == 0)).sum()),
                  "p2_1arvore_teste": F.acerto(te2["rótulo"], uma2.predict(te2[F.BANDAS]))})
        # Prática 3: juntar a maré (o mesmo código da prática)
        com = F.PISTAS_COM_MARE

        def nota3(a, b):
            m = RandomForestClassifier(n_estimators=100, random_state=0).fit(a[com], a["turva"])
            return F.acerto(b["turva"], m.predict(b[com]))

        def troco(nome):
            return tr3[tr3["troco"] == nome], te3[te3["troco"] == nome]

        R.update({"p3_n_treino": len(tr3), "p3_n_teste": len(te3), "p3_nota_com_mare": nota3(tr3, te3),
                  "p3_nota_medio": nota3(*troco("troço médio")), "p3_sempre_medio": float(troco("troço médio")[1]["turva"].mean()),
                  "p3_nota_foz": nota3(*troco("foz"))})
        # Prática 4: o caudal daqui a 7 dias
        d7 = pd.read_csv(F.encontrar("caudal_e_chuva_diarios.csv"), parse_dates=["data"])
        d7["alvo"] = d7["caudal_m3s"].shift(-7)
        d7 = d7.dropna()
        tr7, te7 = d7[d7["data"].dt.year <= 2018], d7[d7["data"].dt.year >= 2019]
        so = ["chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"]
        R.update({"p4_erro_7": float((te7["alvo"] - LinearRegression().fit(tr7[P], tr7["alvo"]).predict(te7[P])).abs().mean()),
                  "p4_igual_7": float((te7["alvo"] - te7["caudal_m3s"]).abs().mean()),
                  "p4_so_chuva_7": float((te7["alvo"] - LinearRegression().fit(tr7[so], tr7["alvo"]).predict(te7[so])).abs().mean())})
        return R
    finally:
        os.chdir(antes)


# ---------------------------------------------------------------- 3. notebooks auxiliares

def verificar_computador():
    return [md("""# Verificar o computador · Workshop 2

Corram a célula de baixo (**Shift + Enter**). Em cerca de 30 segundos diz se este computador está pronto para as aulas:
o Python e as bibliotecas, os dados, as ferramentas e um treino de teste de cada tipo de modelo."""),
            code(f'''import os, sys, time, platform
problemas, faltam = [], []
print("Python", sys.version.split()[0], "em", platform.system(), platform.release())
print("Python em uso:", sys.executable)
if sys.version_info < (3, 9):
    problemas.append("Python antigo: instalem o Anaconda (Python 3.10 ou mais recente)")
for nome in ["numpy", "pandas", "matplotlib", "sklearn", "joblib"]:
    try:
        modulo = __import__(nome)
        print("OK     ", nome, modulo.__version__)
    except ImportError:
        problemas.append("falta a biblioteca " + nome)
        faltam.append("scikit-learn" if nome == "sklearn" else nome)
        print("FALTA  ", nome)
if os.path.exists("ferramentas.py"):
    print("OK      ferramentas.py")
else:
    problemas.append("falta o ficheiro ferramentas.py: copiem outra vez a pasta 2_pratica")
    print("FALTA   ferramentas.py")
for ficheiro in {DADOS}:
    caminho = os.path.join("dados", ficheiro)
    if os.path.exists(caminho):
        print("OK      dados/" + ficheiro, f"({{os.path.getsize(caminho) / 1e6:.1f}} MB)")
    else:
        problemas.append("falta dados/" + ficheiro + ": copiem outra vez a pasta 2_pratica")
        print("FALTA   dados/" + ficheiro)
if not problemas:
    import numpy as np
    import pandas as pd
    from sklearn.ensemble import RandomForestClassifier
    from sklearn.linear_model import LinearRegression
    inicio = time.time()
    z = np.load(os.path.join("dados", "incomati_2026_cheia.npz"))
    X = np.stack([z[b] / 10000 for b in ["azul", "verde", "vermelho", "nir", "swir"]], axis=-1).reshape(-1, 5)
    y = (X[:, 4] < 0.04).astype(int)
    RandomForestClassifier(n_estimators=100, random_state=0).fit(X[::200], y[::200]).predict(X)
    rio = pd.read_csv(os.path.join("dados", "cor_do_rio_e_mare.csv"))
    RandomForestClassifier(n_estimators=100, random_state=0).fit(rio[["caudal_m3s", "chuva_7d_mm", "mes", "altura_da_mare_m"]], rio["turva"])
    LinearRegression().fit(X[:, :4], X[:, 4])
    segundos = time.time() - inicio
    print(f"OK      treino de teste (classificação e regressão) em {{segundos:.0f}} s")
    if segundos > 60:
        problemas.append("o computador é lento: avisem um facilitador (as aulas vão demorar mais)")
print()
if problemas:
    print("AINDA NÃO ESTÁ PRONTO:")
    for p in problemas:
        print("   -", p)
    if faltam:
        print()
        print("COMO RESOLVER AS BIBLIOTECAS (escolham uma):")
        print("   1. Com Anaconda: fechem este Jupyter e abram-no pelo Anaconda Navigator")
        print("      (Jupyter Notebook > Launch). O Anaconda já traz todas as bibliotecas.")
        print("   2. Com Internet (cerca de 60 MB): numa célula nova escrevam e corram")
        print("         %pip install " + " ".join(faltam))
        print("      Depois: menu Kernel > Restart Kernel, e corram esta célula outra vez.")
        print("   Se aparecer «externally-managed-environment», chamem um facilitador.")
else:
    print("ESTE COMPUTADOR ESTÁ PRONTO PARA AS AULAS.")''')]


def teste_do_aluno():
    gabarito = [[r, t, e] for _, r, t, e in PERGUNTAS]
    pacote = base64.b64encode(json.dumps(gabarito, ensure_ascii=False).encode()).decode()
    c = [md(f"""# Teste do aluno · Inteligência Artificial para a água ({len(PERGUNTAS)} perguntas)

Respondam trocando os `...` e corram a célula (**Shift + Enter**): aparece logo «Certo!» ou «Não» com a explicação. No
fim, corram a última célula para ver a nota. Nas perguntas de escolha, escrevam a letra entre aspas, por exemplo `"a"`.
Nas perguntas com números, escrevam o número com ponto, por exemplo `0.5`.

Comecem por correr a célula do corrector."""),
         code(f'''# O corrector: corram sem mudar nada
import base64, json
_GABARITO = json.loads(base64.b64decode("{pacote}").decode())
_NOTAS = {{}}


def corrigir(numero, resposta):
    certa, tipo, explicacao = _GABARITO[numero - 1]
    if resposta is ...:
        print("Ainda não respondeu: troque os ... pela resposta.")
        return
    if tipo == "numero":
        acertou = abs(float(resposta) - certa) <= 0.01 * max(1, abs(certa))
    else:
        acertou = str(resposta).strip().lower().startswith(certa)
    _NOTAS[numero] = acertou
    print(("Certo! " if acertou else f"Não. A resposta é {{certa}}. ") + explicacao)


def resultado():
    certas = sum(_NOTAS.values())
    print(f"Respondeu a {{len(_NOTAS)}} de {{len(_GABARITO)}} perguntas e acertou {{certas}}.")
    if len(_NOTAS) == len(_GABARITO):
        print(f"Nota: {{20 * certas / len(_GABARITO):.0f}} valores em 20.")


print("Corrector pronto.")''')]
    for i, (pergunta, _, tipo, _) in enumerate(PERGUNTAS, start=1):
        c.append(md(f"### Pergunta {i}\n\n{pergunta}"))
        dica = "# um número, por exemplo 12 ou 0.5" if tipo == "numero" else '# a letra entre aspas, por exemplo "a"'
        c.append(code(f"resposta_{i} = ...      {dica}\ncorrigir({i}, resposta_{i})"))
    c.append(md("## A sua nota"))
    c.append(code("resultado()"))
    return c


# ---------------------------------------------------------------- 4. correr como no dia

def correr(caminho, pasta_saida=None):
    """Corre um notebook numa pasta temporária com dados/ e ferramentas.py. Devolve (notebook corrido, texto, erro)."""
    nb = nbformat.read(caminho, as_version=4)
    with tempfile.TemporaryDirectory() as tmp:
        shutil.copytree(PRATICA / "dados", Path(tmp) / "dados")
        shutil.copy(PRATICA / "ferramentas.py", Path(tmp) / "ferramentas.py")
        erro = None
        try:
            NotebookClient(nb, timeout=900, kernel_name="python3", resources={"metadata": {"path": tmp}}).execute()
        except CellExecutionError as e:
            erro = str(e)[-800:]
        if pasta_saida:
            for sub in ["modelos_treinados", "separacoes"]:
                if (Path(tmp) / sub).exists():
                    destino = pasta_saida / sub
                    destino.mkdir(parents=True, exist_ok=True)
                    for f in (Path(tmp) / sub).iterdir():
                        shutil.copy(f, destino / f.name)
    partes = []
    for c in nb.cells:
        for o in c.get("outputs", []):
            if o.get("output_type") == "stream":
                partes.append(o["text"])
            elif o.get("output_type") == "error":
                partes.append(f"ERRO {o['ename']}: {o['evalue']}")
            elif o.get("output_type") in ("execute_result", "display_data") and "text/plain" in o.get("data", {}):
                partes.append(o["data"]["text/plain"])
    return nb, "\n".join(partes), erro


def leia_me_resolvidas(R):
    m = R["a4_melhor_profundidade"]
    return f"""# As 4 aulas resolvidas (só para os facilitadores)

Não copiar esta pasta para os computadores dos alunos.

| Ficheiro | O que é |
| --- | --- |
| `1_Aula_..._RESOLVIDA.ipynb` a `4_Aula_..._RESOLVIDA.ipynb` | As 4 aulas guiadas, já corridas, com uma «Nota para o facilitador» a seguir a cada passo |
| `1_Pratica_..._RESOLVIDA.ipynb` a `4_Pratica_..._RESOLVIDA.ipynb` | As 4 práticas com o código escrito e as perguntas respondidas, já corridas, com notas e os resultados esperados (a Prática 1 está feita com o ano 2021; os outros anos estão na nota) |
| `modelos_treinados/aula1_arvore_de_decisao.joblib` | A árvore da Aula 1 (5 bandas, profundidade 2), treinada com os {R['a1_n']} exemplos da cheia de 24/01/2026 |
| `modelos_treinados/aula2_floresta_100_arvores.joblib` | A floresta da Aula 2, treinada só com os {R['a2_n_treino']} exemplos de treino (10 + 10 pontos) |
| `modelos_treinados/aula3_floresta_sem_mare.joblib` | A floresta da Aula 3 (turva ou não) com o caudal, a chuva e o mês, sem a maré, treinada com 2017 a 2022 |
| `modelos_treinados/aula4_regressao_linear.joblib` | A regressão linear do caudal daqui a 3 dias, treinada com 2006 a 2018 |
| `modelos_treinados/aula4_arvore_profundidade_{m}.joblib` | A árvore de regressão com o menor erro no teste |
| `separacoes/aula1_exemplos_2026.csv` | Os exemplos da Aula 1: as 5 bandas e o rótulo de cada píxel |
| `separacoes/aula2_pontos_treino.csv`, `aula2_pontos_teste.csv` | Os pontos de treino (10 + 10) e de teste (5 + 5): linha, coluna e rótulo |
| `separacoes/aula2_pixeis_treino.csv`, `aula2_pixeis_teste.csv` | Os píxeis de treino ({R['a2_n_treino']}) e de teste ({R['a2_n_teste']}) |
| `separacoes/aula3_treino_2017_a_2022.csv`, `aula3_teste_2023_a_2026.csv` | A separação no tempo da Aula 3: {R['p3_n_treino']} manhãs de treino e {R['p3_n_teste']} de teste |
| `separacoes/aula4_treino_2006_a_2018.csv`, `aula4_teste_2019_a_2026.csv` | A separação no tempo: {R['a4_n_treino']} dias de treino e {R['a4_n_teste']} de teste |
| `modelos_treinados/pratica1_arvore_2021.joblib` | A árvore da Prática 1, treinada com os pontos de 2021 |
| `modelos_treinados/pratica2_floresta_100_arvores.joblib` | A floresta da Prática 2 (teste = os primeiros 5 + 5 pontos) |
| `modelos_treinados/pratica3_floresta_com_mare.joblib`, `pratica3_floresta_troco_medio.joblib` | As florestas da Prática 3, com a maré: nos três troços e só no troço médio |
| `modelos_treinados/pratica4_regressao_7_dias.joblib` | A regressão do caudal daqui a 7 dias |
| `separacoes/pratica1_...`, `pratica2_...`, `pratica3_...`, `pratica4_...` | Os exemplos, os pontos de treino e de teste e as separações no tempo de cada prática |
| `resultados_de_referencia.json` | Os números de referência (usados no manual e nos slides) |

Para usar um modelo noutro notebook, nesta pasta:

```python
import joblib
modelo = joblib.load("modelos_treinados/aula2_floresta_100_arvores.joblib")
```

Para refazer tudo: `.venv/bin/python scripts/build_workshop2_aulas.py` (na pasta do projecto).
"""


def leia_me_dados(R):
    """O LEIA-ME da pasta dados/, para os pares: o que tem cada ficheiro e como cada aula separa o treino do teste."""
    import numpy as np
    import pandas as pd
    d = PRATICA / "dados"

    def dia(texto):
        return "/".join(reversed(str(texto).split("-")))

    def pt(valor):
        return f"{valor:,.0f}".replace(",", " ")

    caudal = pd.read_csv(d / "caudal_e_chuva_diarios.csv")
    rio = pd.read_csv(d / "cor_do_rio_e_mare.csv")
    oficial = np.load(d / "mapa_oficial_cheia_2026.npz")["rotulo"]
    imagens = []
    for nome, quem in [("incomati_2026_cheia.npz", "todos (Aulas 1 e 2, Prática 2)")] + [
            (f"incomati_{ano}_chuvosa.npz", f"{par} (Prática 1)") for par, ano in ANO_POR_PAR.items()]:
        z = np.load(d / nome)
        imagens.append(f"| `{nome}` | {z['satelite']} | {dia(z['data'])} | {pt(float(z['caudal_m3s']))} m³/s | {quem} |")
    mb = sum(f.stat().st_size for f in d.iterdir() if f.name != "LEIA-ME.md") / 1e6
    tabela_imagens = "\n".join(imagens)
    return f"""# Os dados das aulas

Esta pasta tem os dados das 4 aulas e das 4 práticas (cerca de {mb:.0f} MB). **Não é preciso abrir estes ficheiros:** os
notebooks abrem-nos sozinhos. Todos são usados: não apaguem nenhum.

| Ficheiro | O que tem | Onde se usa |
| --- | --- | --- |
| `incomati_2026_cheia.npz` | A imagem do satélite da cheia de 24/01/2026, em Marracuene | Aulas 1 e 2, Prática 2 |
| `incomati_2014_chuvosa.npz` a `incomati_2025_chuvosa.npz` | A imagem de um dia de chuvas de cada ano (uma por par) | Prática 1 |
| `exemplos_da_equipa.json` | Os pontos de exemplo de cada imagem, com a resposta certa: água ou não água | Aulas 1 e 2, Práticas 1 e 2 |
| `mapa_oficial_cheia_2026.npz` | O mapa oficial da cheia de 24/01/2026: o exame | Aula 2, Prática 2 |
| `cor_do_rio_e_mare.csv` | {pt(len(rio))} linhas (uma manhã num troço do rio): a cor do rio, o caudal, a chuva e a maré | Aula 3, Prática 3 |
| `caudal_e_chuva_diarios.csv` | {pt(len(caudal))} dias: o caudal do rio e a chuva | Aula 4, Prática 4 |

## Treino e teste em cada aula

Para aprender, o modelo precisa de exemplos com a resposta certa: é o **treino**. Para saber se aprendeu bem, faz-se um
exame com exemplos que ele nunca viu: é o **teste**.

| Aula | O algoritmo | Treino (o modelo aprende) | Teste (o modelo é avaliado) |
| --- | --- | --- | --- |
| Aula 1 | árvore de decisão | todos os pontos de 2026 | os mesmos pontos (por isso esta nota engana) |
| Prática 1 | árvore de decisão | todos os pontos do ano do par | os mesmos pontos |
| Aula 2 | floresta aleatória | os primeiros 10 + 10 pontos de 2026 ({pt(R['a2_n_treino'])} píxeis) | os outros 5 + 5 pontos ({pt(R['a2_n_teste'])} píxeis) e o mapa oficial |
| Prática 2 | floresta aleatória | os últimos 10 + 10 pontos ({pt(R['p2_n_treino'])} píxeis) | os primeiros 5 + 5 pontos ({pt(R['p2_n_teste'])} píxeis) e o mapa oficial |
| Aula 3 e Prática 3 | floresta aleatória | as manhãs de 2017 a 2022 ({pt(R['p3_n_treino'])}) | as manhãs de 2023 a 2026 ({pt(R['p3_n_teste'])}) |
| Aula 4 e Prática 4 | regressão linear (e, na Aula 4, a árvore de regressão) | os dias de 2006 a 2018 | os dias de 2019 a 2026 |

## As imagens do satélite (`incomati_*.npz`)

- Cada imagem é uma tabela de 1110 linhas por 735 colunas: 33 km por 22 km do vale do Incomáti, em Marracuene.
- Cada casa da tabela é um **píxel**: um quadrado de 30 m por 30 m no chão.
- Em cada píxel, o satélite mede 5 **bandas**: azul, verde, vermelho, nir e swir (as duas últimas são infravermelhos que
  os olhos não vêem). Cada número diz quanta luz o chão devolve, de 0 (nada) a 1 (tudo). A água devolve muito pouco swir.
- `nuvem` marca os píxeis com nuvem ou sombra (aí o satélite não vê o chão) e `zona` marca o distrito de Marracuene,
  sem o mar.

| Imagem | Satélite | Dia | Caudal do rio nesse dia | Quem a usa |
| --- | --- | --- | --- | --- |
{tabela_imagens}

## Os pontos de exemplo (`exemplos_da_equipa.json`)

Para cada imagem, a equipa ETE preparou pontos onde se sabe a resposta: **água** ou **não água**. Cada ponto é uma linha
e uma coluna da imagem, e conta como o quadrado de 5 por 5 píxeis à volta dele (até 25 exemplos por ponto; os píxeis com
nuvem ficam de fora).

- 2026: 15 pontos de água (cheia barrenta, rio e lagoas) e 15 de não água (plantas, campos, areia e casas).
- 2014, 2021, 2022, 2024 e 2025: 5 pontos de água (no rio) e 5 de não água (terra baixa com plantas), em cada ano.

## O mapa oficial da cheia (`mapa_oficial_cheia_2026.npz`)

Especialistas do serviço europeu **Copernicus EMS** desenharam onde estava a água a 24/01/2026. Para cada píxel, `rotulo`
diz 1 (água), 0 (não água) ou -1 (sem resposta). São {pt((oficial >= 0).sum())} píxeis com resposta: um exame muito maior
do que os nossos pontos, e feito por outros. No exame só contam os que não estão debaixo de nuvens.

## A cor do rio e a maré (`cor_do_rio_e_mare.csv`)

Uma linha por manhã em que o satélite viu o rio sem nuvens, em cada um de 3 troços, de {dia(rio['data'].min())} a
{dia(rio['data'].max())}.

| Coluna | O que é |
| --- | --- |
| `data`, `ano`, `mes` | o dia |
| `troco` | o pedaço do rio: troço médio, jusante ou foz (onde o rio chega ao mar) |
| `ndti` | a turbidez medida pelo satélite: mais alto = água mais barrenta |
| `caudal_m3s` | quanta água passa no rio, em metros cúbicos por segundo |
| `chuva_7d_mm` | a chuva na bacia do rio nos últimos 7 dias, em milímetros |
| `altura_da_mare_m` | a maré à hora do satélite (cerca das 9:30), em metros acima (+) ou abaixo (-) do nível médio do mar |
| `turva` | **o rótulo** (a resposta certa): 1 = mais barrenta do que o normal nesse troço, 0 = mais limpa |

## O caudal e a chuva (`caudal_e_chuva_diarios.csv`)

Uma linha por dia, de {dia(caudal['data'].min())} a {dia(caudal['data'].max())}.

| Coluna | O que é |
| --- | --- |
| `data` | o dia |
| `caudal_m3s` | o caudal do Incomáti em Marracuene, em m³/s (calculado pelo modelo europeu GloFAS) |
| `chuva_dia_mm` | a chuva desse dia na bacia do rio, em milímetros |
| `chuva_7d_mm`, `chuva_14d_mm`, `chuva_30d_mm` | a chuva somada nos últimos 7, 14 e 30 dias, contando com esse dia |

Na Aula 4 e na Prática 4, o **alvo** (o número a prever) é criado no próprio notebook: o caudal 3 ou 7 dias depois.
"""


def dados_sem_uso(alunos):
    """Confirma que a pasta dados/ tem exactamente os ficheiros que as aulas usam (nem a mais, nem a menos)."""
    usados = PRATICA.joinpath("ferramentas.py").read_text(encoding="utf-8")
    usados += "".join(f.read_text(encoding="utf-8") for f in alunos)
    problemas = []
    for nome in DADOS:
        ano = re.fullmatch(r"incomati_(\d{4})_chuvosa\.npz", nome)
        usado = nome in usados or (ano and 'incomati_{ANO}_chuvosa.npz' in usados and int(ano.group(1)) in ANO_POR_PAR.values())
        if not (PRATICA / "dados" / nome).exists():
            problemas.append(f"falta dados/{nome}")
        elif not usado:
            problemas.append(f"dados/{nome}: nenhuma aula o usa")
    for f in (PRATICA / "dados").iterdir():
        if f.name not in DADOS and f.name != "LEIA-ME.md":
            problemas.append(f"dados/{f.name}: está na pasta, mas nenhuma aula o usa (tirem-no ou acrescentem-no a DADOS)")
    return problemas


def sem_colab(caminho):
    dados = json.loads(caminho.read_text(encoding="utf-8"))
    dados.get("metadata", {}).pop("colab", None)
    caminho.write_text(json.dumps(dados, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")


def main():
    falhas = []
    print("1. ferramentas.py")
    escrever_ferramentas()
    print("2. contas de referência (cerca de 1 minuto)")
    R = referencia()
    (RESOLVIDAS).mkdir(parents=True, exist_ok=True)
    (RESOLVIDAS / "resultados_de_referencia.json").write_text(json.dumps(R, ensure_ascii=False, indent=1) + "\n", encoding="utf-8")
    print("3. notebooks")
    velhos = ["3_Aula_agrupar_sem_rotulos", "3_Pratica_agrupar_a_seca"]             # o Tema 3 era o K-means
    for velho in (list(PRATICA.glob("Aula_*.ipynb")) + list(RESOLVIDAS.glob("Aula_*_RESOLVIDA.ipynb"))
                  + [PRATICA / f"{v}.ipynb" for v in velhos] + [RESOLVIDAS / f"{v}_RESOLVIDA.ipynb" for v in velhos]):
        if not velho.exists():
            continue
        velho.unlink()                                   # os nomes da primeira versão (Aula_N_..., sem a prática)
    alunos, resolvidas = {}, {}
    for n, fazer in AULAS.items():
        alunos[n] = escrever(fazer(False, R), PRATICA / f"{FICHEIROS[n]}.ipynb", f"ETE WS2 · Aula {n}")
        resolvidas[n] = escrever(fazer(True, R), RESOLVIDAS / f"{FICHEIROS[n]}_RESOLVIDA.ipynb", f"ETE WS2 · Aula {n} resolvida")
        alunos[f"P{n}"] = escrever(PRATICAS[n](False, R), PRATICA / f"{FICHEIROS_PRATICA[n]}.ipynb", f"ETE WS2 · Prática {n}")
        resolvidas[f"P{n}"] = escrever(PRATICAS[n](True, R), RESOLVIDAS / f"{FICHEIROS_PRATICA[n]}_RESOLVIDA.ipynb", f"ETE WS2 · Prática {n} resolvida")
    (PRATICA / "dados" / "LEIA-ME.md").write_text(leia_me_dados(R), encoding="utf-8")
    falhas += dados_sem_uso([f for n, f in alunos.items()])
    verificar = escrever(verificar_computador(), PRATICA / "0_verificar_computador.ipynb", "ETE WS2 · Verificar")
    teste = escrever(teste_do_aluno(), WS2 / "3_teste_do_aluno/teste_ia.ipynb", "ETE WS2 · Teste do aluno")
    for f in [*alunos.values(), *resolvidas.values(), verificar, teste]:
        sem_colab(f)
        if EMOJIS.search(f.read_text(encoding="utf-8")):
            falhas.append(f"{f.name}: tem emojis")
    print("4. correr como no dia")
    _, texto, erro = correr(verificar)
    if erro or "ESTE COMPUTADOR ESTÁ PRONTO" not in texto:
        falhas.append(f"verificação do computador: {erro or texto[-300:]}")
    for shutil_dir in ["modelos_treinados", "separacoes"]:
        if (RESOLVIDAS / shutil_dir).exists():
            shutil.rmtree(RESOLVIDAS / shutil_dir)
    for n in alunos:
        nome = f"Prática {n[1:]}" if str(n).startswith("P") else f"Aula {n}"
        _, texto, erro = correr(alunos[n])
        if erro or "ERRO " in texto:
            falhas.append(f"{nome} (alunos, sem preencher): {erro or texto[-300:]}")
        print(f"   {nome} dos alunos, sem preencher: {'sem erros' if not erro else 'ERRO'}; "
              f"{texto.count('Falta preencher') + texto.count('Ainda não')} avisos para preencher")
        nb, texto, erro = correr(resolvidas[n], RESOLVIDAS)
        certos, ainda = texto.count("Certo!"), texto.count("Ainda não") + texto.count("Falta preencher")
        if erro or ainda:
            falhas.append(f"{nome} (resolvida): {erro or texto[-600:]}")
        nbformat.write(nb, resolvidas[n])
        sem_colab(resolvidas[n])
        print(f"   {nome} resolvida: {certos} respostas certas, {ainda} por corrigir, {'sem erros' if not erro else 'ERRO'}")
    (RESOLVIDAS / "LEIA-ME.md").write_text(leia_me_resolvidas(R), encoding="utf-8")
    print("   modelos:", sorted(p.name for p in (RESOLVIDAS / "modelos_treinados").iterdir()))
    print("   separações:", sorted(p.name for p in (RESOLVIDAS / "separacoes").iterdir()))
    if falhas:
        print("\nFALHAS:")
        for f in falhas:
            print(" -", f)
        return 1
    print("\nAULAS SEM ERROS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
