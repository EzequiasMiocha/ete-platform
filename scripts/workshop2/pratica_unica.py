"""A prática única do Workshop 2: um só notebook (85 minutos, no máximo 90) em que os pares constroem o modelo da água turva.

Duas versões, geradas do mesmo texto:
  alunos        Workshop_2/2_pratica_unica/Pratica_agua_turva.ipynb: escrevem o código (tiram o # e trocam os ...)
  facilitador   Workshop_2/0_facilitadores/pratica_unica/Pratica_agua_turva_FACILITADOR.ipynb: resolvido, corrido, com notas
O notebook não precisa de nenhum outro ficheiro de código: as verificações estão na primeira célula. Só precisa do
cor_do_rio_e_mare.csv ao lado. O algoritmo final é o do projecto (Gradient Boosting, 300 árvores, profundidade 3).
Português de Portugal (ortografia anterior ao Acordo de 1990), sem emojis.
"""

import base64
import json
import re

from nbformat.v4 import new_code_cell, new_markdown_cell

TITULO = "Prática · Ensinar uma máquina a prever a água turva"

RESPOSTAS = {
    "P1": ["b", "O modelo já viu os exemplos do treino: a nota sairia boa de mais e não provaria nada.",
           "Imaginem um exame com as mesmas perguntas que já viram resolvidas."],
    "P2": ["b", "Com a maré, todos os algoritmos sobem. A pista certa vale mais do que trocar de algoritmo.",
           "Comparem as barras: o que mudou mais, trocar o algoritmo ou juntar a maré?"],
    "P3": ["b", "Turva perdida: a água estava barrenta e o modelo disse que estava limpa. Alguém pode confiar nessa resposta.",
           "Qual dos erros pode levar alguém a confiar numa água que está barrenta?"],
}

PREPARAR = r'''# PREPARAR A AULA: corram esta célula sem mudar nada (Shift + Enter).
import base64, json, os, sys, warnings
from IPython.display import display
warnings.filterwarnings("ignore")

FICHEIRO = "cor_do_rio_e_mare.csv"
_pronto = True
try:
    import numpy as np
    import pandas as pd
    import matplotlib.pyplot as plt
    from sklearn.tree import DecisionTreeClassifier
    from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
    from sklearn.metrics import accuracy_score
except ImportError as _erro:
    _pronto = False
    print("FALTA A BIBLIOTECA " + str(_erro.name) + " neste Python: " + sys.executable)
    print()
    print("COMO RESOLVER (escolham uma):")
    print("  1. Menu Kernel > Change Kernel, e escolham o Python do workshop: «Python (Workshop 2 - jupyter_env)».")
    print("  2. Fechem este Jupyter e abram-no pelo Anaconda (Anaconda Navigator > Jupyter Notebook).")
    print("Depois corram esta célula outra vez. Se não resultar, chamem um facilitador.")
    print()
if not os.path.exists(FICHEIRO):
    _pronto = False
    print("FALTA O FICHEIRO " + FICHEIRO + ". Abram este notebook na pasta onde ele está, ao lado dos dados.")

_SEM_MARE = ["caudal_m3s", "chuva_7d_mm", "mes"]
_COM_MARE = _SEM_MARE + ["altura_da_mare_m"]
_RESPOSTAS = json.loads(base64.b64decode("__RESPOSTAS__").decode())
_CASTANHO, _CARMIM, _CINZENTO = "#8D6E63", "#A51C30", "#6B6B6B"


def _pc(x, casas=1):
    return f"{100 * x:.{casas}f}".replace(".", ",") + " %"


def _n(x):
    return f"{int(x):,d}".replace(",", " ")


def _falta(*nomes):
    g = globals()
    em_falta = [n for n in nomes if n not in g or g[n] is ...]
    if em_falta:
        print("Ainda não: falta criar " + ", ".join(em_falta) + ". Tirem o # do início das linhas, troquem os ... e corram a célula.")
        return True
    return False


def _treinado(m, n):
    return getattr(m, "n_features_in_", None) == n


def _boosting():
    return GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)


def _p1():
    if _falta("rio"):
        return
    if not isinstance(rio, pd.DataFrame) or "turva" not in rio:
        print('Ainda não. Pista: rio = pd.read_csv("cor_do_rio_e_mare.csv")')
        return
    print(f"Certo! A tabela tem {_n(len(rio))} linhas e {rio.shape[1]} colunas. Cada linha é uma manhã num troço do rio.")
    display(rio.head())


def _p2():
    if _falta("parte_turva"):
        return
    if abs(float(parte_turva) - rio["turva"].mean()) > 1e-9:
        print('Ainda não. Pista: parte_turva = rio["turva"].mean()')
        return
    print(f"Certo! A água estava turva em {_pc(parte_turva)} das manhãs.")
    parte = rio.groupby("mes")["turva"].mean()
    plt.figure(figsize=(9, 3.6))
    plt.bar(parte.index, 100 * parte.values, color=_CASTANHO)
    plt.xticks(range(1, 13), ["Jan", "Fev", "Mar", "Abr", "Mai", "Jun", "Jul", "Ago", "Set", "Out", "Nov", "Dez"])
    plt.ylabel("manhãs turvas (%)")
    plt.title("A água turva em cada mês")
    plt.show()


def _p3():
    if _falta("PISTAS", "ROTULO"):
        return
    if ROTULO != "turva":
        print('Ainda não: o rótulo é a coluna "turva".')
    elif "turva" in PISTAS or "ndti" in PISTAS:
        print("Ainda não: a resposta não pode ser uma pista. Seria dar ao modelo a solução do exame.")
    elif not isinstance(PISTAS, list) or sorted(PISTAS) != sorted(_SEM_MARE):
        print('Ainda não. Pista: PISTAS = ["caudal_m3s", "chuva_7d_mm", "mes"]')
    else:
        print('Certo! Três pistas (X) e um rótulo (y). A maré fica de fora, por agora.')


def _p4():
    if _falta("treino", "teste"):
        return
    if treino["ano"].max() == 2022 and teste["ano"].min() == 2023 and len(treino) + len(teste) == len(rio):
        print(f"Certo! {_n(len(treino))} manhãs para treinar (2017 a 2022) e {_n(len(teste))} para o exame (2023 a 2026).")
    else:
        print('Ainda não. Pista: treino = rio[rio["ano"] <= 2022] e teste = rio[rio["ano"] >= 2023]')


def _p5():
    if _falta("sempre_turva"):
        return
    if abs(float(sempre_turva) - teste[ROTULO].mean()) > 1e-9:
        print("Ainda não. Pista: sempre_turva = teste[ROTULO].mean()")
        return
    print(f"Certo! Quem disser sempre «turva», sem modelo nenhum, acerta {_pc(sempre_turva)}. É esta a nota a bater.")


def _p6():
    if _falta("arvore", "nota_arvore"):
        return
    certa = accuracy_score(teste[ROTULO], arvore.predict(teste[PISTAS]))
    if not _treinado(arvore, 3) or abs(float(nota_arvore) - certa) > 1e-9:
        print("Ainda não. Pista: arvore.fit(treino[PISTAS], treino[ROTULO]) e nota_arvore = accuracy_score(teste[ROTULO], arvore.predict(teste[PISTAS]))")
        return
    ganhou = "ganha a" if certa > sempre_turva else "não ganha a"
    print(f"Certo! A árvore acerta {_pc(certa)} no teste: {ganhou} «dizer sempre turva» ({_pc(sempre_turva)}).")


def _p7a():
    if _falta("floresta", "nota_floresta"):
        return
    certa = accuracy_score(teste[ROTULO], floresta.predict(teste[PISTAS]))
    if not _treinado(floresta, 3) or abs(float(nota_floresta) - certa) > 1e-9:
        print("Ainda não. Pista: floresta.fit(treino[PISTAS], treino[ROTULO]) e calculem a nota no teste, como no Passo 6.")
        return
    print(f"Certo! A floresta de 100 árvores acerta {_pc(certa)} no teste.")


def _p7b():
    if _falta("boosting", "nota_boosting"):
        return
    certa = accuracy_score(teste[ROTULO], boosting.predict(teste[PISTAS]))
    if not _treinado(boosting, 3) or abs(float(nota_boosting) - certa) > 1e-9:
        print("Ainda não. Pista: boosting.fit(treino[PISTAS], treino[ROTULO]) e calculem a nota no teste, como no Passo 6.")
        return
    print(f"Certo! O Gradient Boosting acerta {_pc(certa)} no teste.")
    nomes = ["Árvore", "Floresta", "Gradient Boosting"]
    notas = [nota_arvore, nota_floresta, nota_boosting]
    plt.figure(figsize=(9, 3.4))
    plt.barh(nomes[::-1], [100 * n for n in notas[::-1]], color=_CINZENTO)
    plt.axvline(100 * sempre_turva, color=_CARMIM, lw=2.5)
    plt.text(100 * sempre_turva + 1.5, 1, f"dizer sempre\n«turva»: {_pc(sempre_turva)}", color=_CARMIM, va="center", fontweight="bold")
    for i, n in enumerate(notas[::-1]):
        plt.text(100 * n - 1, i, _pc(n), va="center", ha="right", color="white", fontweight="bold")
    plt.xlim(0, 100)
    plt.xlabel("acerto no teste (%)")
    plt.title("Três algoritmos, sem a maré")
    plt.show()
    if max(notas) <= sempre_turva:
        print("Nenhum passa da linha vermelha: mudar de algoritmo não resolve. Falta uma pista.")
    else:
        print("Quase não passam da linha vermelha: mudar de algoritmo ajuda muito pouco. Falta uma pista.")


def ver_mare():
    if _falta("rio"):
        return
    faixa = pd.cut(rio["altura_da_mare_m"], [-5, -0.5, 0.5, 5], labels=["maré baixa", "maré média", "maré alta"])
    parte = rio.groupby(faixa, observed=False)["turva"].mean()
    plt.figure(figsize=(7, 3.8))
    plt.bar(parte.index.astype(str), 100 * parte.values, color=[_CASTANHO, "#BCAAA4", "#D7CCC8"])
    for i, v in enumerate(parte.values):
        plt.text(i, 100 * v + 2, _pc(v, 0), ha="center", fontsize=12)
    plt.ylim(0, 105)
    plt.ylabel("manhãs turvas (%)")
    plt.title("A água turva, conforme a maré à hora do satélite")
    plt.show()


def _p8():
    if _falta("PISTAS_COM_MARE", "modelo", "nota_com_mare"):
        return
    if sorted(PISTAS_COM_MARE) != sorted(_COM_MARE):
        print('Ainda não. Pista: PISTAS_COM_MARE = PISTAS + ["altura_da_mare_m"]')
        return
    certa = accuracy_score(teste[ROTULO], modelo.predict(teste[PISTAS_COM_MARE]))
    if not _treinado(modelo, 4) or abs(float(nota_com_mare) - certa) > 1e-9:
        print("Ainda não. Pista: modelo.fit(treino[PISTAS_COM_MARE], treino[ROTULO]) e calculem a nota com teste[PISTAS_COM_MARE].")
        return
    print(f"Certo! Com a maré, o Gradient Boosting acerta {_pc(certa)} no teste (sem a maré: {_pc(nota_boosting)}).")
    criar = {"Árvore": lambda: DecisionTreeClassifier(max_depth=3, random_state=42),
             "Floresta": lambda: RandomForestClassifier(n_estimators=100, random_state=42), "Gradient Boosting": _boosting}
    sem, com = [], []
    for fazer in criar.values():
        sem.append(100 * accuracy_score(teste[ROTULO], fazer().fit(treino[_SEM_MARE], treino[ROTULO]).predict(teste[_SEM_MARE])))
        com.append(100 * accuracy_score(teste[ROTULO], fazer().fit(treino[_COM_MARE], treino[ROTULO]).predict(teste[_COM_MARE])))
    x = np.arange(3)
    plt.figure(figsize=(9, 3.8))
    plt.bar(x - 0.2, sem, 0.38, color=_CINZENTO, label="sem a maré")
    plt.bar(x + 0.2, com, 0.38, color=_CARMIM, label="com a maré")
    for i in range(3):
        plt.text(i - 0.2, sem[i] - 3, f"{sem[i]:.1f}".replace(".", ","), ha="center", va="top", color="white", fontweight="bold")
        plt.text(i + 0.2, com[i] - 3, f"{com[i]:.1f}".replace(".", ","), ha="center", va="top", color="white", fontweight="bold")
    plt.axhline(100 * sempre_turva, color="#1A1A1A", lw=1.5, ls="--", label="dizer sempre «turva»")
    plt.xticks(x, list(criar))
    plt.ylim(0, 118)
    plt.yticks(range(0, 101, 20))
    plt.ylabel("acerto no teste (%)")
    plt.title("O que muda mais: o algoritmo ou a pista?")
    plt.legend(loc="upper center", ncol=3, fontsize=10)
    plt.show()


def _p9():
    if _falta("previsto"):
        return
    certo = modelo.predict(teste[PISTAS_COM_MARE])
    if not np.array_equal(np.asarray(previsto), certo):
        print("Ainda não. Pista: previsto = modelo.predict(teste[PISTAS_COM_MARE])")
        return
    v, p = teste[ROTULO].to_numpy(), np.asarray(previsto)
    r = [[int(((v == 1) & (p == 1)).sum()), int(((v == 1) & (p == 0)).sum())],
         [int(((v == 0) & (p == 1)).sum()), int(((v == 0) & (p == 0)).sum())]]
    nomes = [["turva certa", "turva perdida"], ["falso alarme", "limpa certa"]]
    cores = [["#DCEFE3", "#F6D5D5"], ["#F6D5D5", "#DCEFE3"]]
    fig, ax = plt.subplots(figsize=(6, 4.2))
    for i in range(2):
        for j in range(2):
            ax.add_patch(plt.Rectangle((j, 1 - i), 1, 1, color=cores[i][j], ec="white", lw=3))
            ax.text(j + 0.5, 1.5 - i, f"{nomes[i][j]}\n{_n(r[i][j])}", ha="center", va="center", fontsize=13)
    ax.set_xlim(0, 2)
    ax.set_ylim(0, 2)
    ax.set_xticks([0.5, 1.5])
    ax.set_xticklabels(["o modelo disse TURVA", "o modelo disse LIMPA"])
    ax.set_yticks([1.5, 0.5])
    ax.set_yticklabels(["era TURVA", "era LIMPA"])
    ax.tick_params(length=0)
    for lado in ax.spines.values():
        lado.set_visible(False)
    ax.set_title("A matriz de confusão (verde = certo, vermelho = erro)")
    plt.show()
    print(f"Certo! Em {_n(len(v))} manhãs de teste: {_n(r[1][0])} falsos alarmes e {_n(r[0][1])} manhãs turvas perdidas.")


def _p10():
    if _falta("altura_da_mare", "probabilidade"):
        return
    manha_certa = pd.DataFrame({"caudal_m3s": [20], "chuva_7d_mm": [5], "mes": [6], "altura_da_mare_m": [altura_da_mare]})
    certa = modelo.predict_proba(manha_certa[PISTAS_COM_MARE])[0, 1]
    if abs(float(probabilidade) - certa) > 1e-9:
        print("Ainda não. Pista: probabilidade = modelo.predict_proba(manha[PISTAS_COM_MARE])[0, 1]")
        return
    print(f"Certo! Com a maré a {str(altura_da_mare).replace('.', ',')} m, a probabilidade de a água estar turva é {_pc(certa, 0)}.")
    print("Mudem a altura da maré na célula e corram outra vez.")


_PASSOS = {1: _p1, 2: _p2, 3: _p3, 4: _p4, 5: _p5, 6: _p6, "7a": _p7a, "7b": _p7b, 8: _p8, 9: _p9, 10: _p10}


def verificar(passo):
    """Diz se o passo está certo e mostra o resultado. Nunca dá erro vermelho."""
    try:
        _PASSOS[passo]()
    except Exception as erro:
        print("Ainda não: alguma coisa falta ou está errada (" + type(erro).__name__ + "). Confirmem esta célula e o passo anterior.")


def responder(pergunta, resposta):
    """Corrige uma pergunta de escolha: a resposta é a letra entre aspas, por exemplo "a"."""
    if resposta is ...:
        print('Falta responder: troquem os ... pela letra entre aspas, por exemplo "a".')
        return
    certa, explicacao, dica = _RESPOSTAS[pergunta]
    print(("Certo! " + explicacao) if str(resposta).strip().lower().startswith(certa) else ("Ainda não. " + dica))


if _pronto:
    plt.rcParams.update({"font.size": 12, "axes.spines.top": False, "axes.spines.right": False})
    print("PRONTO. Podem começar pelo Passo 1.")
else:
    print("AINDA NÃO ESTÁ PRONTO: sigam as instruções acima.")'''

SCRIPT_FINAL = '''import pandas as pd
from sklearn.ensemble import GradientBoostingClassifier
from sklearn.metrics import accuracy_score

# 1. Abrir os dados
tabela = pd.read_csv("cor_do_rio_e_mare.csv")

# 2. Escolher as pistas e o rótulo
pistas = ["caudal_m3s", "chuva_7d_mm", "mes", "altura_da_mare_m"]
rotulo = "turva"

# 3. Separar no tempo: treino com o passado, teste com o futuro
parte_treino = tabela[tabela["ano"] <= 2022]
parte_teste = tabela[tabela["ano"] >= 2023]

# 4. Treinar
modelo_final = GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)
modelo_final.fit(parte_treino[pistas], parte_treino[rotulo])

# 5. Avaliar com dados que o modelo nunca viu
nota_final = accuracy_score(parte_teste[rotulo], modelo_final.predict(parte_teste[pistas]))
print("Acerto no teste:", round(100 * nota_final, 1), "%")'''

COMO = """## Como trabalhar

1. Cliquem numa célula de código (as cinzentas).
2. **Tirem o `#`** do início das linhas e **troquem os `...`** pela resposta.
3. Carreguem em **Shift + Enter**.
4. Leiam a resposta: **«Certo!»**, ou **«Ainda não»** com uma pista.

Corram as células **por ordem**, de cima para baixo. Guardem com **Ctrl + S**.

| Se a última linha do erro disser | O que fazer |
| --- | --- |
| `ellipsis`, `Ellipsis` ou `'...'` | Ainda há `...` por trocar |
| `NameError` | Saltaram uma célula: corram as células por ordem |
| `SyntaxError` | Falta uma aspa ou um parêntese, ou ficou mal tirado um `#` |
| `KeyError` | O nome de uma coluna está mal escrito |
| `FileNotFoundError` | O nome do ficheiro está mal escrito |
| `ValueError` | Escreveram um número com vírgula? Em Python as décimas têm ponto: `0.7` |
| `NotFittedError` | Falta treinar o modelo: `.fit(...)` |

Se nada resultar: menu **Kernel**, **Restart Kernel and Run All Cells**."""


def pt(x, casas=1):
    return f"{x:,.{casas}f}".replace(",", " ").replace(".", ",")


# O que os pares lêem no início de cada passo: o que vão fazer agora e porquê
AGORA = {
    0: ("confirmar que o computador tem tudo o que a aula precisa.", "Assim, nenhum problema técnico nos interrompe a meio."),
    1: ("abrir a tabela com os dados do rio e ver o que tem cada coluna.", "Um modelo aprende com exemplos, e esta tabela são os nossos exemplos."),
    2: ("ver em que parte das manhãs a água estava turva, e em que meses.", "Antes de treinar, olha-se sempre para os dados, para perceber o problema."),
    3: ("dizer ao computador com que informação vai adivinhar (as **pistas**, X) e qual é a resposta certa (o **rótulo**, y).",
        "O modelo só aprende com o que lhe damos."),
    4: ("dividir a tabela em duas: o **treino** (2017 a 2022) e o **teste** (2023 a 2026).",
        "O modelo aprende com o treino e faz o exame com o teste, em manhãs que nunca viu."),
    5: ("calcular a nota de quem não usa modelo nenhum e diz sempre «turva».", "Um modelo só vale a pena se fizer melhor do que isto."),
    6: ("treinar o primeiro modelo, uma **árvore de decisão**, e dar-lhe uma nota.",
        "É o modelo mais fácil de perceber: faz perguntas de sim ou não. Vamos ver se bate a nota do Passo 5."),
    7: ("treinar dois algoritmos mais fortes e comparar os três.", "Se a árvore não chegou, talvez o problema seja o algoritmo."),
    8: ("olhar para a maré e juntá-la às pistas.", "Se trocar de algoritmo não resolveu, talvez falte informação. O rio chega ao mar, e o mar pode mudar a cor da água."),
    9: ("ver que erros faz o modelo.", "A nota diz quanto ele errou, mas não como, e nem todos os erros são igualmente graves."),
    10: ("usar o modelo numa manhã que ele nunca viu.", "É para isto que se treina um modelo: responder a casos novos."),
    11: ("ver tudo o que fizeram num só script e corrê-lo.", "Para perceberem que os passos de hoje são um programa curto, que serve de base para outros problemas."),
}


def _dia(texto):
    return "/".join(reversed(str(texto).split("-")))


def contexto(R):
    """A contextualização do início do notebook: o problema, o que vão fazer e os dados (números lidos da tabela)."""
    anos = sorted(R["por_ano"], key=int)
    cab = " | ".join(a + ("*" if a == anos[-1] else "") for a in anos)
    manhas = " | ".join(str(R["por_ano"][a]) for a in anos)
    papel = " | ".join("treino" if int(a) <= 2022 else "teste" for a in anos)
    separador = " | ".join("---" for _ in anos)
    e = R["exemplo"]
    problema = f"""## Antes de começar: o que vamos fazer (5 min)

Leiam esta parte com calma, em pares.

### O problema

O rio **Incomáti** atravessa o distrito de Marracuene e chega ao mar, na baía de Maputo. A cor da sua água muda de dia para
dia: umas vezes está mais limpa, outras está **turva** (barrenta), cheia de terra fina. Para quem usa o rio, para regar,
pescar ou buscar água, é útil saber como vai estar a água.

O satélite consegue ver a cor do rio, mas só temos imagens limpas em cerca de **90 manhãs por ano**. Nos outros dias, o
satélite não passou ou havia nuvens.

### A pergunta de hoje

> **Será que um computador consegue aprender, com exemplos do passado, a prever se a água do rio vai estar turva?**

### O que vão fazer

Vão ser **vocês** a ensinar o computador, em cinco etapas:

1. **Conhecer os dados** (Passos 0 a 2): abrir a tabela e perceber o que ela mostra.
2. **Preparar o exame** (Passos 3 a 5): escolher as pistas, separar o treino do teste e encontrar a nota a bater.
3. **Treinar** (Passos 6 e 7): ensinar três algoritmos e ver quanto acertam.
4. **Descobrir o que faltava** (Passo 8): encontrar a pista que faz o modelo funcionar.
5. **Usar o modelo** (Passos 9 a 11): ver os erros, prever uma manhã nova e juntar tudo num só script.

**No fim**, terão um modelo treinado por vocês e saberão dizer quanto ele acerta e onde erra. Não é preciso saber
programar: cada passo traz uma pista, e o computador diz se está certo."""
    dados = f"""## Os dados que vamos usar

Tudo está numa só tabela, o ficheiro `cor_do_rio_e_mare.csv`:

- **{pt(R['n'], 0)} linhas**. Cada linha é **uma manhã num troço do rio**.
- **{R['manhas']} manhãs** diferentes, de **{_dia(R['inicio'])} a {_dia(R['fim'])}**: quase 10 anos.
- **3 troços do rio** em Marracuene: o **troço médio** (o mais longe do mar), **jusante** e **foz** (onde o rio chega ao mar).

### Quantas manhãs há em cada ano

| Ano | {cab} |
| --- | {separador} |
| **Manhãs** | {manhas} |
| **Serve para** | {papel} |

\\* Até {_dia(R['fim'])}. Em 2017 e 2018 há menos manhãs porque havia menos imagens desta zona.

### De onde vem cada informação

| Informação | Coluna | De onde vem |
| --- | --- | --- |
| **A cor da água** | `ndti` | **Medida pelo satélite Sentinel-2** (programa europeu Copernicus), por volta das 9h30. Compara a luz vermelha com a verde: quanto mais alto, mais barrenta |
| **A água que passa no rio** | `caudal_m3s` | Modelo **GloFAS** (Copernicus), para Marracuene. É **calculada** por computador, não medida no rio |
| **A chuva** | `chuva_7d_mm` | **ERA5** (centro europeu ECMWF): a chuva média em toda a bacia do Incomáti, somada nos 7 dias que acabam nesse dia |
| **A maré** | `altura_da_mare_m` | **Calculada** pelo projecto para a baía de Maputo, à hora do satélite. 0 é o nível médio do mar |
| **A resposta certa** | `turva` | **Calculada por nós** a partir do `ndti`: 1 se a água estava mais barrenta do que o normal nesse troço (a mediana de 2017 a 2022); 0 se estava mais limpa |

### Como se lê uma linha

No dia **{_dia(e['data'])}**, no meio da grande cheia, na **{e['troco']}**: passavam **{pt(e['caudal_m3s'], 0)} m³/s** de água,
tinham caído **{pt(e['chuva_7d_mm'], 0)} mm** de chuva em 7 dias, a maré estava a **{pt(e['altura_da_mare_m'], 2)} m** e a água
estava **turva** (`turva` = {e['turva']}).

### Um cuidado importante

Estes dados mostram a **cor** da água. **Não dizem se a água é segura para beber:** o satélite não vê bactérias nem produtos
químicos, e ninguém recolheu amostras no rio para esta tabela."""
    return problema, dados


def fazer(fac, R):
    """As células do notebook: fac=False para os alunos, fac=True para os facilitadores."""
    c = []

    def texto(t):
        m = re.match(r"## Passo (\d+) · [^\n]*\n\n", t)
        if m:                                       # cada passo começa por dizer o que se vai fazer e porquê
            o_que, porque = AGORA[int(m.group(1))]
            t = t[:m.end()] + f"**O que vamos fazer agora:** {o_que}  \n**Porquê:** {porque}\n\n" + t[m.end():]
        t = re.sub(r"(?m)^\|( --- \|)+$", lambda s: s.group(0).replace("---", ":---"), t)     # as tabelas alinhadas à esquerda
        c.append(new_markdown_cell(t))

    def nota(t):
        if fac:
            c.append(new_markdown_cell(f"> **Nota para o facilitador.** {t}"))

    def passo(passo_id, pista, solucao):
        """A célula em que os pares escrevem: a pista comentada (alunos) ou o código (facilitador)."""
        chave = f'"{passo_id}"' if isinstance(passo_id, str) else str(passo_id)
        if fac:
            c.append(new_code_cell(solucao.strip() + f"\n\nverificar({chave})"))
        else:
            linhas = "\n".join("# " + l for l in pista.strip().splitlines())
            c.append(new_code_cell(f"{linhas}\n\nverificar({chave})"))

    def pergunta(chave, enunciado):
        texto(enunciado)
        certa = RESPOSTAS[chave][0]
        c.append(new_code_cell(f'resposta = "{certa}"\nresponder("{chave}", resposta)' if fac else
                               f'resposta = ...      # a letra entre aspas, por exemplo "a"\nresponder("{chave}", resposta)'))

    pacote = base64.b64encode(json.dumps(RESPOSTAS, ensure_ascii=False).encode()).decode()
    aviso = "\n\n**VERSÃO DO FACILITADOR: resolvida, corrida e com notas.** Não copiar para os computadores dos alunos." if fac else ""
    texto(f"""# {TITULO}{aviso}

**85 minutos, em pares** · Workshop 2 · Projecto EYES TO EARTH

**A missão:** construir, do princípio ao fim, um modelo que prevê se a água do rio Incomáti vai estar **turva** (barrenta).
É o mesmo tipo de modelo que o projecto usa: um **Gradient Boosting**.""")
    problema, dados = contexto(R)
    texto(problema)
    texto(dados)
    if fac:
        texto(f"""> **Nota para o facilitador: a contextualização (5 min).** Dêem tempo para lerem, ou leiam em voz alta. Depois perguntem:
> «o que é uma linha da tabela?», «de que anos são os dados?», «o caudal foi medido no rio?» (não: é calculado pelo GloFAS).
> **Não digam ainda que a maré é a solução:** é a surpresa do Passo 8.
>
> Para quem perguntar: o troço de montante ficou de fora porque aí os dois satélites concordam mal. As medianas que definem
> `turva` (2017 a 2022) são: {", ".join(f"{k} {pt(v, 3)}" for k, v in R["medianas"].items())}.""")
    texto(f"""## O plano da aula

| Passo | O que vão fazer | Minutos |
| --- | --- | --- |
| Início | Ler o que vamos fazer e conhecer os dados | 5 |
| 0 | Preparar o computador | 5 |
| 1 | Abrir os dados | 5 |
| 2 | Olhar para os dados | 5 |
| 3 | Escolher as pistas e o rótulo | 7 |
| 4 | Separar o treino e o teste | 8 |
| 5 | Encontrar a nota a bater | 3 |
| 6 | Treinar uma árvore de decisão | 10 |
| 7 | Treinar uma floresta e um Gradient Boosting | 10 |
| 8 | Juntar a pista que faltava: a maré | 10 |
| 9 | Ver os erros do modelo | 7 |
| 10 | Prever uma manhã nova | 5 |
| 11 | O script inteiro | 5 |

{COMO}""")
    if fac:
        texto(f"""> **Nota para o facilitador: como conduzir.** Cada passo: explicar 1 minuto no projector, os pares escrevem, e só
> depois se mostra a solução. Total: 85 minutos, com 5 de margem até aos 90.
>
> **Se só houver 60 minutos:** leiam o início em voz alta (3 minutos em vez de 5), façam os Passos 1 a 5 todos juntos no projector (10 minutos em vez de 28) e saltem o Passo 10.
>
> **A ideia a levar:** sem a maré, nenhum algoritmo bate «dizer sempre turva» ({pt(100 * R['sempre'])} %). Com a maré, todos sobem
> para {pt(100 * min(R['com'].values()), 0)} a {pt(100 * max(R['com'].values()), 0)} %. **A pista certa vale mais do que o algoritmo.**
>
> **Dados:** {pt(R['n'], 0)} linhas (uma manhã num troço), de 2017 a 2026. `turva` = o índice de cor NDTI acima da mediana desse troço em 2017 a 2022.
>
> **Os números destas notas** foram obtidos com o scikit-learn 1.9. Noutra versão (por exemplo, no Anaconda) podem mudar umas décimas: a lição é a mesma.""")

    texto("## Passo 0 · Preparar o computador (5 min)\n\nCorram a célula de baixo sem mudar nada. Tem de aparecer **PRONTO**.")
    c.append(new_code_cell(PREPARAR.replace("__RESPOSTAS__", pacote),
                           metadata={"jupyter": {"source_hidden": True}, "collapsed": False}))
    nota("Se aparecer FALTA A BIBLIOTECA, o notebook está no Python errado: abram-no pelo Anaconda ou com `./abrir_aulas.sh`. "
         "A célula está escondida de propósito: tem as verificações e os gráficos.")

    texto("""## Passo 1 · Abrir os dados (5 min)

As colunas são as do quadro **«De onde vem cada informação»**, lá em cima, mais o dia (`data`, `ano`, `mes`) e o pedaço do rio (`troco`).""")
    passo(1, 'rio = pd.read_csv("cor_do_rio_e_mare.csv")', 'rio = pd.read_csv("cor_do_rio_e_mare.csv")')
    nota(f"Resultado: {pt(R['n'], 0)} linhas e 9 colunas. Mostrem que a tabela é igual à do Módulo 2: linhas = exemplos, colunas = pistas, última = rótulo.")

    texto("## Passo 2 · Olhar para os dados (5 min)\n\nA média de uma coluna de 0 e 1 dá a parte das linhas em que ela vale 1: "
          "aqui, a parte das manhãs em que a água estava turva.")
    passo(2, 'parte_turva = rio["..."].mean()', 'parte_turva = rio["turva"].mean()')
    nota(f"Resultado: {pt(100 * R['turva'])} %. O gráfico mostra a época do ano. Perguntem: «o que acham que faz a água ficar barrenta?» "
         "Vão dizer a chuva. Guardem a resposta para o Passo 7.")

    texto("""## Passo 3 · Escolher as pistas e o rótulo (7 min)

Vamos começar com o que parece lógico: o caudal, a chuva e o mês.""")
    passo(3, 'PISTAS = ["caudal_m3s", "chuva_7d_mm", "..."]\nROTULO = "..."', 'PISTAS = ["caudal_m3s", "chuva_7d_mm", "mes"]\nROTULO = "turva"')
    nota("Se alguém puser `ndti` nas pistas, a verificação explica: `turva` é calculada a partir do `ndti`, por isso seria dar a solução ao modelo.")

    texto("""## Passo 4 · Separar o treino e o teste (8 min)

**A regra de ouro:** nunca se avalia um modelo com os exemplos com que ele aprendeu. Queremos um modelo para o futuro: por
isso o treino é o **passado** e o teste é o **futuro**.""")
    passo(4, 'treino = rio[rio["ano"] <= ...]\nteste = rio[rio["ano"] >= ...]', 'treino = rio[rio["ano"] <= 2022]\nteste = rio[rio["ano"] >= 2023]')
    nota(f"Resultado: {pt(R['n_treino'], 0)} manhãs de treino e {pt(R['n_teste'], 0)} de teste.")
    pergunta("P1", "**Para pensar.** Porque é que não se avalia um modelo com os exemplos do treino?\n\n"
                   "a) porque demora mais tempo  \nb) porque o modelo já os viu: a nota sai boa de mais  \nc) porque o computador não deixa")

    texto("## Passo 5 · Encontrar a nota a bater (3 min)\n\nSe disséssemos **sempre «turva»**, acertaríamos a parte das manhãs de "
          "teste que foram mesmo turvas.")
    passo(5, 'sempre_turva = teste[...].mean()', 'sempre_turva = teste[ROTULO].mean()')
    nota(f"Resultado: {pt(100 * R['sempre'])} %. Escrevam este número no quadro: é a linha a ultrapassar.")

    texto("""## Passo 6 · Treinar uma árvore de decisão (10 min)

Três linhas, sempre as mesmas: **criar** o modelo, **treinar** (`fit`) só com o treino, e **avaliar** (`predict`) com o teste.""")
    passo(6, 'arvore = DecisionTreeClassifier(max_depth=3, random_state=42)\narvore.fit(treino[PISTAS], treino[...])\n'
             'nota_arvore = accuracy_score(teste[ROTULO], arvore.predict(teste[...]))',
          'arvore = DecisionTreeClassifier(max_depth=3, random_state=42)\narvore.fit(treino[PISTAS], treino[ROTULO])\n'
          'nota_arvore = accuracy_score(teste[ROTULO], arvore.predict(teste[PISTAS]))')
    nota(f"Resultado: {pt(100 * R['sem']['arvore'])} %, abaixo de {pt(100 * R['sempre'])} %. Não é erro de código: com estas pistas, a árvore não chega lá.")

    texto("""## Passo 7 · Treinar uma floresta e um Gradient Boosting (10 min)

Os dois algoritmos:

- **Floresta aleatória:** 100 árvores **lado a lado**, que votam.
- **Gradient Boosting:** 300 árvores **em fila**, cada uma corrige os erros das anteriores. É o algoritmo do projecto.""")
    passo("7a", 'floresta = RandomForestClassifier(n_estimators=100, random_state=42)\nfloresta.fit(treino[PISTAS], treino[ROTULO])\n'
                'nota_floresta = accuracy_score(teste[ROTULO], floresta.predict(teste[...]))',
          'floresta = RandomForestClassifier(n_estimators=100, random_state=42)\nfloresta.fit(treino[PISTAS], treino[ROTULO])\n'
          'nota_floresta = accuracy_score(teste[ROTULO], floresta.predict(teste[PISTAS]))')
    passo("7b", 'boosting = GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)\n'
                'boosting.fit(treino[PISTAS], treino[ROTULO])\nnota_boosting = accuracy_score(teste[ROTULO], boosting.predict(teste[...]))',
          'boosting = GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)\n'
          'boosting.fit(treino[PISTAS], treino[ROTULO])\nnota_boosting = accuracy_score(teste[ROTULO], boosting.predict(teste[PISTAS]))')
    nota(f"Resultados: floresta {pt(100 * R['sem']['floresta'])} %, Gradient Boosting {pt(100 * R['sem']['boosting'])} %. Nenhum passa de "
         f"{pt(100 * R['sempre'])} %. Perguntem: «o que pode mudar a cor da água perto do mar, de um dia para o outro?» Deixem-nos pensar.")

    texto("""## Passo 8 · A pista que faltava: a maré (10 min)

O mar sobe e desce duas vezes por dia. Corram a célula e vejam o gráfico.""")
    c.append(new_code_cell("ver_mare()"))
    texto("Com a **maré baixa**, a água está quase sempre turva; com a **maré alta**, quase sempre mais limpa. Agora juntem a coluna da maré "
          "às pistas e treinem outra vez o Gradient Boosting.")
    passo(8, 'PISTAS_COM_MARE = PISTAS + ["..."]\n'
             'modelo = GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)\n'
             'modelo.fit(treino[PISTAS_COM_MARE], treino[ROTULO])\nnota_com_mare = accuracy_score(teste[ROTULO], modelo.predict(teste[...]))',
          'PISTAS_COM_MARE = PISTAS + ["altura_da_mare_m"]\n'
          'modelo = GradientBoostingClassifier(n_estimators=300, max_depth=3, learning_rate=0.05, subsample=0.8, random_state=42)\n'
          'modelo.fit(treino[PISTAS_COM_MARE], treino[ROTULO])\nnota_com_mare = accuracy_score(teste[ROTULO], modelo.predict(teste[PISTAS_COM_MARE]))')
    nota(f"Com a maré: árvore {pt(100 * R['com']['arvore'])} %, floresta {pt(100 * R['com']['floresta'])} %, Gradient Boosting "
         f"{pt(100 * R['com']['boosting'])} %. Atenção: aqui o Gradient Boosting não é o melhor, e não faz mal dizê-lo. A diferença entre "
         "algoritmos é pequena; a diferença entre ter e não ter a maré é grande. Foi a descoberta do projecto. "
         f"Turva por maré: baixa {pt(100 * R['mare'][0], 0)} %, média {pt(100 * R['mare'][1], 0)} %, alta {pt(100 * R['mare'][2], 0)} %.")
    pergunta("P2", "**Para pensar.** O que fez o acerto subir mais?\n\na) trocar a árvore por um algoritmo mais forte  \nb) juntar a pista certa: a maré")

    texto("""## Passo 9 · Ver os erros do modelo (7 min)

A **matriz de confusão** separa os dois tipos de erro:

- **Falso alarme:** estava limpa e o modelo disse turva.
- **Turva perdida:** estava turva e o modelo disse limpa.""")
    passo(9, 'previsto = modelo.predict(teste[...])', 'previsto = modelo.predict(teste[PISTAS_COM_MARE])')
    nota(f"Resultado: {pt(R['falsos'], 0)} falsos alarmes e {pt(R['perdidas'], 0)} manhãs turvas perdidas, em {pt(R['n_teste'], 0)} manhãs de teste.")
    pergunta("P3", "**Para pensar.** Se alguém usar o modelo para decidir se vai buscar água ao rio, qual dos erros é mais perigoso?\n\n"
                   "a) o falso alarme  \nb) a turva perdida")

    texto("""## Passo 10 · Prever uma manhã nova (5 min)

Uma manhã de Junho, com pouco caudal (20 m³/s) e pouca chuva (5 mm). O modelo não diz só «sim» ou «não»: dá uma
**probabilidade**. Experimentem a maré a **-1**, depois a **0** e depois a **0.7** (em Python, as décimas têm ponto).""")
    passo(10, 'altura_da_mare = ...\nmanha = pd.DataFrame({"caudal_m3s": [20], "chuva_7d_mm": [5], "mes": [6], "altura_da_mare_m": [altura_da_mare]})\n'
              'probabilidade = modelo.predict_proba(manha[PISTAS_COM_MARE])[0, 1]',
          'altura_da_mare = -1\nmanha = pd.DataFrame({"caudal_m3s": [20], "chuva_7d_mm": [5], "mes": [6], "altura_da_mare_m": [altura_da_mare]})\n'
          'probabilidade = modelo.predict_proba(manha[PISTAS_COM_MARE])[0, 1]')
    nota(f"Resultados: maré a -1 m: {pt(100 * R['prob'][0], 0)} %; a 0 m: {pt(100 * R['prob'][1], 0)} %; a 0,7 m: {pt(100 * R['prob'][2], 0)} %. "
         "É uma probabilidade da cor da água, não diz se a água é segura para beber.")

    texto("""## Passo 11 · O script inteiro (5 min)

Leiam-no de cima para baixo: já conhecem cada linha. Depois corram-no.""")
    c.append(new_code_cell(SCRIPT_FINAL))
    nota(f"Resultado: {pt(100 * R['com']['boosting'])} % (o Python escreve as décimas com ponto). Peçam a um par que explique cada um dos 5 blocos.")

    texto("""## O que aprenderam

- O caminho do Machine Learning: **dados, pistas e rótulo, treino e teste, treinar, avaliar, prever**.
- Um modelo tem de bater uma nota simples, como «dizer sempre turva».
- **A pista certa vale mais do que o algoritmo:** sem a maré, nenhum modelo aprendeu nada útil.
- O acerto não chega: é preciso ver **que erros** o modelo faz.

**E no projecto?** O modelo verdadeiro é também um Gradient Boosting de 300 árvores, mas usa 20 pistas (o caudal, a chuva, a época do
ano, a maré e a última medição do satélite). Prevê a **cor** da água por volta das 9h30. **Não diz se a água é segura para beber.**""")
    nota("Para fechar, peçam a 2 ou 3 pares que digam em 1 minuto: o acerto sem e com a maré, e uma coisa que os surpreendeu. "
         "No projecto, o AUC do modelo final é de 0,85 a 0,89, em anos que nunca viu.")
    return c
