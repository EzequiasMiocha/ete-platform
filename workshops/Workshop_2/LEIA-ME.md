# Workshop de Estudantes 2 · Inteligência Artificial para monitorizar a água e avisar das cheias

**Sábado, 21 de Novembro de 2026 · 08:00–14:00 · Maputo** · Projecto EYES TO EARTH (ETE)

## O que há em cada pasta

| Pasta | Para quem | O que tem |
| --- | --- | --- |
| `0_facilitadores/` | Equipa ETE (não copiar para os computadores dos alunos) | Plano do workshop, manual dos facilitadores, cronograma, as 4 aulas resolvidas com os modelos treinados e as separações, imagens dos slides, certificados, e o arquivo da prática antiga |
| `1_preparacao_python/` | Alunos, antes do dia (opcional) | Os 3 notebooks de introdução ao Python do Workshop 1 |
| `2_pratica_unica/` | **Alunos, na aula** | **A prática única: um só notebook** (`Pratica_agua_turva.ipynb`) e os seus dados. A versão resolvida está em `0_facilitadores/pratica_unica/` |
| `2_pratica/` | Versão anterior (8 notebooks) | `0_verificar_computador.ipynb`, as 4 aulas guiadas e as 4 práticas, `ferramentas.py`, `dados/` (o `dados/LEIA-ME.md` explica cada ficheiro e como cada aula separa o treino do teste) e `requirements.txt` |
| `3_teste_do_aluno/` | Alunos | 16 perguntas sobre IA, com correcção automática |
| `jupyter_env/` | Só este computador (não copiar) | O ambiente Python do workshop: o Jupyter Notebook e as bibliotecas das aulas |
| `criar_ambiente.sh`, `abrir_aulas.sh`, `testar_aulas.py` | Equipa ETE | Criar o ambiente, abrir as aulas no Jupyter Notebook e testar todas as aulas de uma vez |

Os slides da parte teórica estão no artefacto "Workshop 2: IA para monitorizar a água e avisar das cheias" (link em
`0_facilitadores/SLIDES.md`).

## A prática única (85 minutos, no máximo 90)

Um só notebook, em que os pares constroem do princípio ao fim um modelo que prevê se a água do rio vai estar turva: abrir
os dados, escolher as pistas e o rótulo, separar o treino e o teste, treinar uma árvore, uma floresta e um Gradient
Boosting, juntar a maré, ver os erros e prever uma manhã nova. No fim, vêem tudo num único script.

| Para quem | Ficheiro |
| --- | --- |
| Alunos | `2_pratica_unica/Pratica_agua_turva.ipynb` (com o `cor_do_rio_e_mare.csv` ao lado) |
| Facilitadores | `0_facilitadores/pratica_unica/Pratica_agua_turva_FACILITADOR.ipynb` (resolvido, corrido, com notas e tempos) |

**Para os computadores dos alunos basta copiar a pasta `2_pratica_unica`** (menos de 1 MB). Precisam do Jupyter Notebook,
pandas, matplotlib e scikit-learn (o Anaconda já os traz). O próprio notebook confirma tudo no Passo 0: tem de dizer
**PRONTO**. Se só houver 60 minutos, a nota no início da versão dos facilitadores diz o que fazer.

Para refazer os dois notebooks: `.venv/bin/python scripts/build_workshop2_pratica_unica.py`.

## Preparar os computadores (uma vez, antes do workshop)

A prática corre no **Jupyter Notebook**, em cada computador, sem precisar de Internet.

1. **Instalar o Python com o Jupyter.** O mais simples é o **Anaconda** (traz Python, Jupyter Notebook, numpy, pandas,
   matplotlib e scikit-learn). O instalador tem cerca de 1 GB: descarreguem-no **uma só vez** e copiem-no para os outros
   computadores no pen drive. Se o computador já tem Python 3.10 ou mais recente:
   `pip install -r Workshop_2/2_pratica/requirements.txt` (cerca de 150 MB de Internet por computador), ou criar um
   ambiente só para o workshop (secção seguinte).
2. **Copiar a pasta** `Workshop_2` para cada computador, **sem** `0_facilitadores` e **sem** `jupyter_env`
   (cerca de 40 MB, pelo pen drive). As pastas escondidas `.ipynb_checkpoints` e `__pycache__`, se aparecerem, não fazem
   falta: são criadas pelo Jupyter e pelo Python no computador onde se abriram os notebooks.
3. **Abrir o Jupyter na pasta da prática:** Anaconda Navigator → Jupyter Notebook e navegar até `Workshop_2/2_pratica`;
   ou num terminal: `cd Workshop_2/2_pratica` e depois `jupyter notebook`.
4. **Abrir `0_verificar_computador.ipynb` e correr a célula.** Tem de aparecer
   "ESTE COMPUTADOR ESTÁ PRONTO PARA AS AULAS".

## Correr as aulas com o ambiente `jupyter_env` (sem Anaconda)

A pasta `Workshop_2/jupyter_env/` é um ambiente Python **só para o workshop**: tem o Jupyter Notebook e as bibliotecas
das aulas, separado do resto do projecto. Já está criado e testado no computador do coordenador técnico (Ubuntu,
Python 3.14).

| Biblioteca | Versão instalada |
| --- | --- |
| Jupyter Notebook | 7.6.5 |
| numpy | 2.5.3 |
| pandas | 3.0.6 |
| matplotlib | 3.11.2 |
| scikit-learn | 1.9.1 |
| joblib | 1.6.0 |

### Abrir as aulas

Num terminal:

```bash
cd Workshop_2
./abrir_aulas.sh                                    # abre a prática única no navegador
./abrir_aulas.sh 0_facilitadores/pratica_unica      # ou a versão resolvida
```

1. O navegador abre sozinho com a lista dos notebooks.
2. Abram primeiro `0_verificar_computador.ipynb` e corram a célula com **Shift + Enter**. Tem de aparecer
   "ESTE COMPUTADOR ESTÁ PRONTO PARA AS AULAS", e a linha "Python em uso" tem de terminar em
   `Workshop_2/jupyter_env/bin/python`.
3. Depois abram as aulas por ordem (1_Aula, 1_Pratica, 2_Aula, ...).
4. Para fechar: guardem os notebooks (**Ctrl + S**) e carreguem **Ctrl + C** duas vezes no terminal.

**No VS Code**, em vez do navegador: abram o notebook, carreguem em **Select Kernel** (canto superior direito) →
**Jupyter Kernel...** → **Python (Workshop 2 - jupyter_env)**.

### Testar todas as aulas de uma vez

```bash
cd Workshop_2
jupyter_env/bin/python testar_aulas.py
```

Corre todos os notebooks (os dos alunos, a preparação, o teste do aluno e as aulas resolvidas) e a Prática 1 com o ano
de cada par. Trabalha numa cópia, por isso não muda os notebooks. Demora cerca de 1 minuto e tem de terminar com
"TODAS AS AULAS CORREM SEM ERROS".

### Criar o ambiente de novo

Se a pasta `jupyter_env` for apagada, ou se a pasta `Workshop_2` mudar de sítio (o ambiente guarda o caminho completo e
deixa de funcionar), apaguem `jupyter_env` e corram:

```bash
cd Workshop_2
./criar_ambiente.sh
```

Gasta cerca de 150 MB de Internet (menos se o pip já tiver as bibliotecas guardadas: no computador do coordenador
técnico gastou 45 MB) e ocupa cerca de 700 MB no disco. Também regista o kernel "Python (Workshop 2 - jupyter_env)".
Para apagar tudo: `rm -rf jupyter_env` e `jupyter kernelspec remove workshop2`.

Num computador com **Windows** e Python 3.10 ou mais recente, os comandos equivalentes são (não testados):

```bat
cd Workshop_2
py -m venv jupyter_env
jupyter_env\Scripts\python -m pip install -r 2_pratica\requirements.txt
cd 2_pratica
..\jupyter_env\Scripts\jupyter notebook
```

### O que é normal e o que fazer se algo correr mal

- **Nas práticas**, antes de os pares escreverem o código, as células mostram "Falta preencher" e as verificações
  "Ainda não". É assim mesmo: não são erros.
- **No terminal** pode aparecer `WARNING | Kernel is running over TCP without encryption`. É normal e pode ser ignorado:
  o Jupyter só comunica dentro do próprio computador.
- **"Python em uso" não termina em `jupyter_env/bin/python`**: o notebook está noutro kernel. Menu **Kernel → Change
  Kernel** → **Python (Workshop 2 - jupyter_env)**.
- **"falta a biblioteca ..."**: corram `./criar_ambiente.sh` outra vez (só instala o que faltar).
- **Tudo parou ou os resultados estão estranhos**: menu **Kernel → Restart Kernel and Run All Cells**.
- **Não copiem `jupyter_env`** para o pen drive nem para outros computadores: só funciona neste computador e nesta
  pasta. Nos outros computadores usem o Anaconda, ou criem lá o ambiente com os comandos acima.

## Versão anterior da prática: 4 aulas guiadas e 4 práticas (pasta `2_pratica`)

Para cada um dos 4 temas há dois notebooks: primeiro a **aula guiada** (o facilitador mostra no projector e os pares
acompanham), depois a **prática**, em que os pares **escrevem o código sozinhos** num caso novo.

| Tema | Aula guiada | Prática (sozinhos) | Tipo de modelo |
| --- | --- | --- | --- |
| 1 | 11:40 `1_Aula_ensinar_com_exemplos` (10 min) | 11:50 `1_Pratica_a_agua_no_vosso_ano` (15 min): treinar a árvore com os pontos do ano do par | Classificação |
| 2 | 12:05 `2_Aula_treinar_e_testar` (12 min) | 12:17 `2_Pratica_treinar_e_testar` (18 min): outra separação, as duas notas, o exame, a matriz de confusão | Classificação |
| 3 | 12:35 `3_Aula_a_cor_do_rio_e_a_mare` (8 min) | 12:43 `3_Pratica_juntar_a_mare` (12 min): juntar a maré às pistas da água turva | Classificação |
| 4 | 12:55 `4_Aula_prever_o_caudal` (10 min) | 13:05 `4_Pratica_prever_7_dias` (15 min): a regressão do caudal a 7 dias | Regressão |
| — | 13:20–13:25 | Guardar e preparar a apresentação | — |

**Nas práticas**, cada passo tem uma célula com uma **pista** (linhas que começam por `#`). Os pares escrevem o código
(podem copiar a pista, tirar o `#` e trocar os `...`), correm a célula, e depois correm a célula de verificação, que
diz «Certo!», ou «Ainda não» com uma pista. No fim de cada prática há perguntas para pensar, também corrigidas.

Ano de cada par na Prática 1:

| Par | Ano |
| --- | --- |
| Par 1 | 2024 |
| Par 2 | 2021 |
| Par 3 | 2022 |
| Par 4 | 2014 |
| Par 5 | 2025 |

## Na aula

- Abrir os notebooks **a partir da pasta `2_pratica`** (os dados e o `ferramentas.py` estão lá).
- Correr por ordem com **Shift + Enter**; guardar com **Ctrl + S**. Se tudo parar: menu **Kernel → Restart Kernel and Run All Cells**.

## Para os facilitadores: `0_facilitadores/aulas_resolvidas/`

- As 4 aulas guiadas e as 4 práticas **resolvidas e já corridas**, com uma nota para o facilitador a seguir a cada
  passo (o que dizer e os resultados esperados), o código das práticas escrito e as perguntas respondidas.
- `modelos_treinados/`: os modelos de cada aula, guardados com o joblib (`modelo = joblib.load("...")`).
- `separacoes/`: os dados exactos de treino e de teste de cada aula (CSV).
- `resultados_de_referencia.json`: os números de referência, usados no manual e nos slides.

## Como foi feito (para refazer)

```bash
.venv/bin/python scripts/build_workshop2_data.py               # os dados
.venv/bin/python scripts/build_workshop2.py                    # LEIA-ME e preparação; chama o seguinte
.venv/bin/python scripts/build_workshop2_aulas.py              # as 4 aulas, corridas e testadas (cerca de 5 minutos)
.venv/bin/python scripts/build_workshop2_slides.py             # os slides (deck em reports/apresentacao/workshop2_slides)
.venv/bin/python scripts/build_workshop2_docs.py               # o plano e o manual (PDF)
.venv/bin/python scripts/build_workshop2_cronograma_docx.py    # o cronograma (Word)
.venv/bin/python scripts/build_workshop2_certificados.py       # os certificados
```

Os textos das aulas estão em `scripts/workshop2/aulas.py` e as ferramentas em `scripts/workshop2/ferramentas_aulas.py`.
A prática antiga (Partes A a H, scripts e nível avançado) está guardada em `0_facilitadores/arquivo_pratica_antiga/`.
