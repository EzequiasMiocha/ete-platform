"""As 4 aulas práticas do Workshop 2, em português de Portugal (ortografia anterior ao Acordo de 1990).

Cada aula existe em duas versões, geradas do mesmo texto:
  aluno        Workshop_2/2_pratica/N_Aula_*.ipynb: a aula guiada (os exercícios estão nas práticas, praticas.py)
  facilitador  Workshop_2/0_facilitadores/aulas_resolvidas/Aula_N_*_RESOLVIDA.ipynb: tudo resolvido, com notas
               (o que dizer, resultados esperados) e uma célula que guarda os modelos treinados e as separações.
Os números das notas (R) vêm de referencia(), que faz as mesmas contas com o mesmo ferramentas.py.
Sem emojis: os sinais são palavras.
"""

from .comum import ANO_POR_PAR, code, md

HORARIO = {1: ("11:40", "11:50", 10), 2: ("12:05", "12:17", 12), 3: ("12:35", "12:43", 8), 4: ("12:55", "13:05", 10)}
TITULOS = {1: "Ensinar a máquina com exemplos", 2: "Treinar e testar", 3: "A cor do rio e a maré",
           4: "Prever um número: o caudal do rio"}
FICHEIROS = {1: "1_Aula_ensinar_com_exemplos", 2: "2_Aula_treinar_e_testar", 3: "3_Aula_a_cor_do_rio_e_a_mare",
             4: "4_Aula_prever_o_caudal"}

COMO_TRABALHAR = """**Como trabalhar:** esta é a **aula guiada**: o facilitador mostra no projector e vocês acompanham.
Cliquem numa célula de código (as cinzentas) e carreguem em **Shift + Enter** para a correr, sempre **por ordem**, de
cima para baixo. A seguir vem a **prática**, em que são vocês a escrever o código. Guardem com **Ctrl + S**."""

ERROS = """## Se aparecer um erro

Leiam a **última linha** da mensagem vermelha.

| A última linha diz | O que fazer |
| --- | --- |
| `NameError: name '...' is not defined` | Saltaram uma célula. Corram as células por ordem, a partir do Passo 1. |
| `FileNotFoundError: Não encontrei ...` | Abram o notebook a partir da pasta `Workshop_2/2_pratica`. |
| `ModuleNotFoundError` | Falta uma biblioteca neste computador: chamem um facilitador. |
| `NotFittedError` ou «O modelo ainda não foi treinado» | Falta treinar o modelo: corram a célula com `.fit(...)`. |
| `SyntaxError` | Falta uma aspa, um parêntese ou uma vírgula. Comparem com o exemplo. |
| «Falta preencher» | Troquem os `...` pela vossa resposta. |

Se nada resultar: menu **Kernel**, depois **Restart Kernel and Run All Cells**."""

PARES = "\n".join(f"| {par} | {ano} |" for par, ano in ANO_POR_PAR.items())


# O resumo do topo de cada notebook: que dados usa, como separa o treino do teste e que algoritmo treina.
def _ficha(chave, R):
    fichas = {
        "aula1": ("`incomati_2026_cheia.npz` (a imagem do satélite da cheia de 24/01/2026) e `exemplos_da_equipa.json` "
                  "(15 pontos de água e 15 de não água, com a resposta certa)",
                  "ainda não separamos: a árvore aprende com todos os exemplos e medimos o acerto nos mesmos. "
                  "A Aula 2 mostra porque é que isso engana",
                  "árvore de decisão (classificação: água ou não água)"),
        "aula2": ("a mesma imagem e os mesmos pontos da Aula 1, e `mapa_oficial_cheia_2026.npz` (o mapa oficial da cheia, "
                  "para o exame)",
                  f"**treino** = os primeiros 10 pontos de água e 10 de não água ({_pt(R['a2_n_treino'], 0)} píxeis); "
                  f"**teste** = os outros 5 + 5 ({_pt(R['a2_n_teste'], 0)} píxeis); **exame** = o mapa oficial "
                  f"({_pt(R['a2_ems_n'], 0)} píxeis)",
                  "floresta aleatória com 100 árvores (classificação: água ou não água)"),
        "aula3": (f"`cor_do_rio_e_mare.csv` ({_pt(R['a3_n'], 0)} linhas: uma manhã num troço do rio, de 2017 a 2026)",
                  f"**treino** = as manhãs de 2017 a 2022 ({_pt(R['p3_n_treino'], 0)}); **teste** = as de 2023 a 2026 "
                  f"({_pt(R['p3_n_teste'], 0)})",
                  "floresta aleatória com 100 árvores (classificação: água turva ou não)"),
        "aula4": ("`caudal_e_chuva_diarios.csv` (uma linha por dia, de 2006 a 2026: o caudal do rio e a chuva)",
                  f"**treino** = os dias de 2006 a 2018 ({_pt(R['a4_n_treino'], 0)}); **teste** = os de 2019 a 2026 "
                  f"({_pt(R['a4_n_teste'], 0)})",
                  "regressão linear e árvore de regressão (regressão: prever um número)"),
        "pratica1": ("`incomati_ANO_chuvosa.npz` (a imagem do vosso ano) e os pontos desse ano em `exemplos_da_equipa.json` "
                     "(5 de água e 5 de não água)",
                     "como na Aula 1, ainda sem separação: a árvore aprende com todos os exemplos do vosso ano",
                     "árvore de decisão (classificação: água ou não água)"),
        "pratica2": ("os mesmos da Aula 2: a imagem da cheia, os pontos e o mapa oficial",
                     f"desta vez, **teste** = os primeiros 5 + 5 pontos ({_pt(R['p2_n_teste'], 0)} píxeis) e **treino** = os "
                     f"outros 10 + 10 ({_pt(R['p2_n_treino'], 0)} píxeis); **exame** = o mapa oficial",
                     "floresta aleatória com 100 árvores, e depois com uma só"),
        "pratica3": ("`cor_do_rio_e_mare.csv`, agora com a coluna da maré (`altura_da_mare_m`)",
                     "a mesma da Aula 3: **treino** = 2017 a 2022, **teste** = 2023 a 2026",
                     "floresta aleatória com 100 árvores (classificação: água turva ou não)"),
        "pratica4": ("`caudal_e_chuva_diarios.csv`",
                     "a mesma da Aula 4: **treino** = 2006 a 2018, **teste** = 2019 a 2026; o alvo é o caudal 7 dias depois",
                     "regressão linear (regressão: prever um número)"),
    }
    dados, separacao, algoritmo = fichas[chave]
    return f"**Os dados:** {dados}.  \n**Treino e teste:** {separacao}.  \n**O algoritmo:** {algoritmo}."


def _cabecalho(n, fac, objectivo, palavras, R):
    inicio, fim, minutos = HORARIO[n]
    titulo = f"# Aula {n} · {TITULOS[n]}"
    if fac:
        titulo += "\n\n**VERSÃO DO FACILITADOR: tudo resolvido, com notas.** Não copiar para os computadores dos alunos."
    linhas = "\n".join(f"| **{p}** | {s} |" for p, s in palavras)
    return md(f"""{titulo}

**{minutos} minutos ({inicio}–{fim}) · aula guiada, em pares** · a seguir: a Prática {n}

**O que vamos fazer:** {objectivo}

{_ficha(f'aula{n}', R)}

| Palavra nova | O que quer dizer |
| --- | --- |
{linhas}

{COMO_TRABALHAR}""")


def _nota(fac, texto):
    return [md(f"> **Nota para o facilitador.** {texto}")] if fac else []


def _passo(n, titulo, texto=""):
    return md(f"## Passo {n} · {titulo}" + (f"\n\n{texto}" if texto else ""))


def _ferramentas(fac, extra=""):
    if fac:
        texto = """import os, sys
for pasta in [".", os.path.join("..", "..", "2_pratica")]:          # a pasta onde está o ferramentas.py
    if os.path.exists(os.path.join(pasta, "ferramentas.py")):
        sys.path.insert(0, pasta)
        break
from ferramentas import *      # as ferramentas da aula"""
    else:
        texto = "from ferramentas import *      # as ferramentas da aula: corram sem mudar nada"
    return code(texto + (("\n" + extra) if extra else "") + '\nprint("Ferramentas prontas.")')


def _guardar(fac, texto):
    """Célula só do facilitador: guarda os modelos treinados e as separações (pastas ao lado do notebook)."""
    if not fac:
        return []
    return [md("## Guardar os modelos e as separações (só na versão do facilitador)\n\nFicam nas pastas "
               "`modelos_treinados/` e `separacoes/`, ao lado deste notebook. Para usar um modelo noutro notebook: "
               "`modelo = joblib.load(\"modelos_treinados/...joblib\")`."),
            code('import joblib\nos.makedirs("modelos_treinados", exist_ok=True)\nos.makedirs("separacoes", exist_ok=True)\n'
                 + texto.strip() + '\nprint("Guardado em modelos_treinados/ e separacoes/.")')]


def _fim(texto):
    return md("## O que aprendemos\n\n" + texto)


def _pt(valor, casas=1):
    return f"{valor:,.{casas}f}".replace(",", " ").replace(".", ",")


# ============================================================================ AULA 1

def aula1(fac, R):
    c = [_cabecalho(1, fac,
                    "ensinar o computador a reconhecer a água numa imagem de satélite. Não vamos escrever a regra: "
                    "damos-lhe **exemplos com a resposta certa** e ele descobre a regra sozinho. É isto o Machine Learning.",
                    [("exemplo", "um caso que mostramos ao computador (aqui, um píxel da imagem)"),
                     ("característica", "o que se mede em cada exemplo (aqui, as 5 cores medidas pelo satélite)"),
                     ("rótulo", "a resposta certa de cada exemplo (aqui, 1 = água e 0 = não água)"),
                     ("modelo", "a regra que o computador aprende com os exemplos"),
                     ("treinar", "dar os exemplos ao modelo para ele aprender"),
                     ("prever", "usar o modelo para dar a resposta num caso novo")], R)]
    c += _nota(fac, f"Objectivo: que os alunos percebam as seis palavras da tabela. Leiam a tabela em voz alta com a "
                    f"turma antes de começar. Tempo: 10 minutos, no projector; os pares correm as células ao mesmo tempo. A seguir, a Prática 1, em que escrevem o código sozinhos.")
    c += [_passo(1, "Abrir as ferramentas", "As ferramentas abrem as imagens, desenham os mapas e corrigem os exercícios."),
          _ferramentas(fac),
          _passo(2, "A imagem do satélite",
                 "O satélite **Sentinel-2** fotografou o rio Incomáti, em Marracuene, a **24 de Janeiro de 2026**, no meio "
                 "da cheia. Cada quadradinho da imagem é um **píxel** de 30 m × 30 m. Os círculos são pontos de **água** "
                 "marcados pela equipa; os quadrados são pontos de **não água** (terra, plantas, casas)."),
          code('cheia = carregar("incomati_2026_cheia.npz")\n'
               'pontos = pontos_da_equipa(2026)\n'
               'ver_imagem(cheia, "Marracuene, 24 de Janeiro de 2026", pontos["agua"], pontos["nao_agua"])'),
          _passo(3, "Uma imagem é uma tabela de números",
                 "O computador não vê cores: vê números. Em cada píxel, o satélite mede 5 bandas: azul, verde, vermelho "
                 "e dois infravermelhos que os nossos olhos não vêem, o **NIR** e o **SWIR**. Comparemos um píxel de "
                 "água com um de terra."),
          code('l, c = pontos["agua"][0]            # um ponto de água: linha e coluna\n'
               'l2, c2 = pontos["nao_agua"][0]      # um ponto de terra\n'
               'pd.DataFrame({"píxel de água": [cheia[b][l, c] for b in BANDAS],\n'
               '              "píxel de terra": [cheia[b][l2, c2] for b in BANDAS]}, index=BANDAS)'),
          md("Olhem para a última linha, o **SWIR**: na água é quase 0, porque a água absorve este infravermelho; "
             "na terra é muito maior. Guardem esta ideia.")]
    c += _nota(fac, f"Resultado esperado: SWIR da água {_pt(R['a1_swir_agua'], 3)} e da terra {_pt(R['a1_swir_terra'], 3)}. "
                    "Pergunte à turma: «qual das linhas separa melhor a água da terra?» e deixe-os descobrir o SWIR.")
    c += [_passo(4, "Os exemplos, com os rótulos",
                 "À volta de cada ponto marcado tiramos 25 píxeis (um quadrado de 5 × 5). Fica uma tabela: uma linha "
                 "por exemplo, as 5 **características** e o **rótulo** (1 = água, 0 = não água)."),
          code('exemplos = tabela_de_exemplos(cheia, pontos["agua"], pontos["nao_agua"])\n'
               'print("Número de exemplos:", len(exemplos))\n'
               'print("De água:", (exemplos["rótulo"] == 1).sum(), "   De não água:", (exemplos["rótulo"] == 0).sum())\n'
               'exemplos.sample(8, random_state=1)        # 8 linhas da tabela, ao acaso')]
    c += _nota(fac, f"Resultado esperado: {R['a1_n']} exemplos, {R['a1_n_agua']} de água e {R['a1_n'] - R['a1_n_agua']} de "
                    "não água. Mostre que cada linha é um píxel e que a última coluna é a resposta certa.")
    c += [_passo(5, "Uma regra feita por nós",
                 "Antes da máquina, tentemos nós. A nossa regra: **se o SWIR for menor do que 0,10, é água**. "
                 "Quantos exemplos acerta? (Em Python, as décimas escrevem-se com ponto: 0.10.)"),
          code('limite = 0.10\n'
               'resposta_da_regra = (exemplos["swir"] < limite).astype(int)      # 1 = água, 0 = não água\n'
               'print("A regra acerta", percentagem(acerto(exemplos["rótulo"], resposta_da_regra)), "dos exemplos.")'),
          _passo(6, "A máquina aprende a regra sozinha",
                 "Agora damos os exemplos a uma **árvore de decisão**. Ela procura a pergunta que melhor separa a água "
                 "da não água. Isto é **treinar** o modelo. `X` são as características e `y` são os rótulos."),
          code('from sklearn.tree import DecisionTreeClassifier, export_text\n\n'
               'X = exemplos[BANDAS]            # as características\n'
               'y = exemplos["rótulo"]          # as respostas certas\n'
               'arvore = DecisionTreeClassifier(max_depth=2, random_state=0)\n'
               'arvore.fit(X, y)                # treinar: aprender com os exemplos\n'
               'print(export_text(arvore, feature_names=BANDAS).replace("class: 1", "ÁGUA").replace("class: 0", "NÃO ÁGUA"))\n'
               'print("A árvore acerta", percentagem(acerto(y, arvore.predict(X))), "dos exemplos.")'),
          md("A árvore escolheu sozinha o **SWIR**, como nós, mas encontrou um limite melhor. Ninguém lhe disse que o "
             "SWIR era importante: aprendeu com os exemplos.")]
    c += _nota(fac, f"A regra feita à mão acerta {_pt(100 * R['a1_regra_010'])} %. A árvore aprende «SWIR ≤ "
                    f"{_pt(R['a1_limiar_arvore'], 2)} → água» e acerta {_pt(100 * R['a1_acerto_arvore'])} %. Ligue ao slide "
                    "da árvore de decisão (Módulo 2). Avise já: este acerto é nos mesmos exemplos do treino; a Aula 2 "
                    "explica porque é que isso não chega.")
    c += [_passo(7, "Prever: o mapa da água",
                 "O modelo treinado pode responder para **todos** os píxeis da imagem, também os que nunca viu. "
                 "Isto é **prever**."),
          code('mapa_cheia = prever_mapa(arvore, cheia)\n'
               'ver_mapa(mapa_cheia, cheia, "Água segundo o modelo, 24 de Janeiro de 2026")\n'
               'print("Água no distrito:", numero(hectares(mapa_cheia, cheia)), "hectares")')]
    c += _nota(fac, f"Resultado esperado: cerca de {_pt(R['a1_ha_cheia'], 0)} hectares de água. O distrito tem cerca de "
                    "70 600 hectares (706 km²): a cheia cobriu perto de um terço.")
    c += [_fim("- O computador aprende com **exemplos** que têm a resposta certa (os **rótulos**).\n"
               "- Em cada exemplo, olha para as **características**: aqui, as 5 bandas do satélite.\n"
               "- Ao **treinar**, o **modelo** encontra a regra sozinho: aqui, «SWIR baixo é água».\n"
               "- Depois **prevê** a resposta em casos que nunca viu: todos os píxeis da imagem.\n"
               "- Atenção: medimos o acerto nos **mesmos** exemplos do treino. Na Aula 2 vemos porque é que isso não chega.")]
    c += _guardar(fac, """
joblib.dump(arvore, "modelos_treinados/aula1_arvore_de_decisao.joblib")
exemplos.to_csv("separacoes/aula1_exemplos_2026.csv", index=False)""")
    c.append(md(ERROS))
    return c


# ============================================================================ AULA 2

def aula2(fac, R):
    c = [_cabecalho(2, fac,
                    "aprender a **avaliar** um modelo a sério. Separamos os exemplos em dois montes: um para **treinar** e "
                    "outro para **testar**. Depois fazemos um grande exame com o mapa oficial da cheia e vemos que erros "
                    "o modelo faz.",
                    [("treino", "os exemplos com que o modelo aprende"),
                     ("teste", "exemplos guardados à parte, que o modelo nunca viu, para o avaliar"),
                     ("acerto", "a parte das respostas certas (100 % = acertou tudo)"),
                     ("floresta aleatória", "muitas árvores de decisão que votam (em inglês, Random Forest)"),
                     ("matriz de confusão", "um quadro com os acertos e os dois tipos de erro"),
                     ("falso alarme", "era terra e o modelo disse água"),
                     ("água perdida", "era água e o modelo disse terra")], R)]
    c += _nota(fac, "Objectivo: a regra de ouro (nunca avaliar com o treino) e ler uma matriz de confusão. "
                    "Tempo: 12 minutos, no projector. A seguir, a Prática 2, com outra separação dos pontos.")
    c += [_passo(1, "Abrir as ferramentas"),
          _ferramentas(fac, "from sklearn.ensemble import RandomForestClassifier"),
          _passo(2, "Separar os exemplos em treino e teste",
                 "A **regra de ouro**: nunca se avalia um modelo com os exemplos que ele usou para aprender. Seria como "
                 "fazer um exame com as perguntas que já vimos resolvidas. Por isso separamos os pontos da equipa: "
                 "**10 de água e 10 de não água para treinar**; os outros **5 + 5 ficam guardados para o teste**."),
          code('cheia = carregar("incomati_2026_cheia.npz")\n'
               'pontos = pontos_da_equipa(2026)\n'
               'agua_treino, agua_teste = pontos["agua"][:10], pontos["agua"][10:]\n'
               'terra_treino, terra_teste = pontos["nao_agua"][:10], pontos["nao_agua"][10:]\n'
               'ver_imagem(cheia, "Treino (pontos cheios) e teste (contorno amarelo)", agua_treino, terra_treino, agua_teste, terra_teste)\n'
               'treino = tabela_de_exemplos(cheia, agua_treino, terra_treino)\n'
               'teste = tabela_de_exemplos(cheia, agua_teste, terra_teste)\n'
               'print("Exemplos de treino:", len(treino), "   Exemplos de teste:", len(teste))')]
    c += _nota(fac, f"Resultado esperado: {R['a2_n_treino']} exemplos de treino e {R['a2_n_teste']} de teste. "
                    "Os pontos de teste estão espalhados pela imagem, longe dos de treino.")
    c += [_passo(3, "Treinar uma floresta aleatória",
                 "Uma **floresta aleatória** são muitas árvores de decisão, cada uma treinada com uma parte diferente "
                 "dos exemplos. Para cada píxel, as árvores **votam**: ganha a resposta com mais votos. Usamos 100 árvores, "
                 "treinadas **só com o treino**."),
          code('floresta = RandomForestClassifier(n_estimators=100, random_state=0)   # 100 árvores\n'
               'floresta.fit(treino[BANDAS], treino["rótulo"])                       # treinar só com o treino\n'
               'print("Floresta treinada com", len(treino), "exemplos.")'),
          _passo(4, "Duas notas: a do treino e a do teste"),
          code('nota_treino = acerto(treino["rótulo"], floresta.predict(treino[BANDAS]))\n'
               'nota_teste = acerto(teste["rótulo"], floresta.predict(teste[BANDAS]))\n'
               'print("Acerto no TREINO (exemplos que já viu):", percentagem(nota_treino))\n'
               'print("Acerto no TESTE (exemplos novos):      ", percentagem(nota_teste))'),
          md("A nota do treino é quase sempre perfeita: o modelo já conhecia aquelas respostas. **A nota que conta é a "
             "do teste.**")]
    c += _nota(fac, f"Resultado esperado: treino {_pt(100 * R['a2_treino'])} %, teste {_pt(100 * R['a2_teste'])} %. "
                    "Pergunte: «qual das duas notas poríamos num relatório?»")
    c += [_passo(5, "O grande exame: o mapa oficial da cheia",
                 "O serviço europeu **Copernicus EMS** desenhou, a 24 de Janeiro de 2026, onde estava a água da cheia. "
                 "São mais de 300 000 píxeis que o nosso modelo nunca viu: um exame muito maior e feito por outros."),
          code('verdade, previsto = exame_mapa_oficial(floresta, cheia)\n'
               'print("Píxeis no exame:", numero(len(verdade)))\n'
               'print("Acerto no exame:", percentagem(acerto(verdade, previsto)))'),
          _passo(6, "A matriz de confusão: que erros fez?",
                 "O acerto diz quanto o modelo errou, mas não **como** errou. A **matriz de confusão** separa os dois tipos "
                 "de erro: o **falso alarme** (era terra e disse água) e a **água perdida** (era água e disse terra)."),
          code('erros = matriz_de_confusao(verdade, previsto, "O exame com o mapa oficial")')]
    c += _nota(fac, f"Resultado esperado: acerto {_pt(100 * R['a2_ems'])} % em {_pt(R['a2_ems_n'], 0)} píxeis; "
                    f"{_pt(R['a2_falsos'], 0)} falsos alarmes e {_pt(R['a2_perdida'], 0)} píxeis de água perdida. "
                    "A maior parte da água perdida fica nas margens e na água com plantas ou muita lama. Pergunte qual "
                    "dos erros é mais grave num aviso de cheias (a pergunta volta na Prática 2).")
    c += [_fim("- Separamos os exemplos: o **treino** para aprender e o **teste** para avaliar. Nunca se avalia com o treino.\n"
               "- A nota do treino engana; a do **teste** diz a verdade.\n"
               "- A **matriz de confusão** mostra os dois tipos de erro: o falso alarme e a água perdida.\n"
               "- Uma **floresta aleatória** junta os votos de muitas árvores e erra menos do que uma só.\n"
               "- Um modelo pode funcionar bem num ano e pior noutro: testa-se onde e quando vai ser usado.")]
    c += _guardar(fac, """
joblib.dump(floresta, "modelos_treinados/aula2_floresta_100_arvores.joblib")
pd.DataFrame([(l, c, 1) for l, c in agua_treino] + [(l, c, 0) for l, c in terra_treino],
             columns=["linha", "coluna", "rótulo"]).to_csv("separacoes/aula2_pontos_treino.csv", index=False)
pd.DataFrame([(l, c, 1) for l, c in agua_teste] + [(l, c, 0) for l, c in terra_teste],
             columns=["linha", "coluna", "rótulo"]).to_csv("separacoes/aula2_pontos_teste.csv", index=False)
treino.to_csv("separacoes/aula2_pixeis_treino.csv", index=False)
teste.to_csv("separacoes/aula2_pixeis_teste.csv", index=False)""")
    c.append(md(ERROS))
    return c


# ============================================================================ AULA 3

def aula3(fac, R):
    c = [_cabecalho(3, fac,
                    "usar o que aprenderam num assunto novo: a **qualidade da água**. Vamos tentar prever se a água do rio "
                    "está **turva** (barrenta) de manhã, a partir de dados. Foi isto que fizemos no projecto EYES TO EARTH.",
                    [("turbidez", "a água barrenta, cheia de terra fina (sedimentos)"),
                     ("NDTI", "o índice de turbidez que o satélite mede (Módulo 4): mais alto = água mais barrenta"),
                     ("troço", "um pedaço do rio; aqui há três: o troço médio, a jusante e a foz (onde o rio chega ao mar)"),
                     ("turva", "o rótulo: 1 = mais barrenta do que o normal nesse troço; 0 = mais limpa"),
                     ("maré", "o mar sobe e desce duas vezes por dia; mede-se em metros (0 = o nível médio do mar)")], R)]
    c += _nota(fac, "Objectivo: uma classificação com os dados da qualidade da água, e a lição do projecto: sem a pista "
                    "certa (a maré), o modelo não aprende nada útil. Tempo: 8 minutos, no projector. Ligue ao slide do "
                    "Módulo 4 «A IA consegue prever a água barrenta?». A seguir, a Prática 3: os pares juntam a maré.")
    c += [_passo(1, "Abrir as ferramentas"),
          _ferramentas(fac, "from sklearn.ensemble import RandomForestClassifier"),
          _passo(2, "Dez anos de manhãs no rio",
                 "Cada linha é uma manhã em que o satélite Sentinel-2 viu o rio sem nuvens, num dos três troços, de 2017 "
                 "a 2026. `ndti` é a turbidez medida; `caudal_m3s` e `chuva_7d_mm` são o caudal e a chuva dos últimos 7 "
                 "dias; `altura_da_mare_m` é a maré à hora do satélite. A coluna `turva` é o **rótulo**."),
          code('rio = pd.read_csv(encontrar("cor_do_rio_e_mare.csv"))\n'
               'print("Linhas na tabela:", numero(len(rio)), "(manhãs de 2017 a 2026, em 3 troços)")\n'
               'print("Manhãs com a água turva:", percentagem(rio["turva"].mean()))\n'
               'rio.head()'),
          _passo(3, "Separar no tempo: o exame são os anos mais recentes",
                 "Queremos um modelo para o futuro. Por isso treinamos com **2017 a 2022** e fazemos o exame com **2023 a "
                 "2026**, anos que o modelo nunca vê no treino."),
          code('treino = rio[rio["ano"] <= 2022]\n'
               'teste = rio[rio["ano"] >= 2023]\n'
               'print("Manhãs de treino (2017 a 2022):", numero(len(treino)))\n'
               'print("Manhãs de teste (2023 a 2026): ", numero(len(teste)))'),
          _passo(4, "Primeira tentativa: o caudal, a chuva e o mês",
                 "Parece lógico: depois de muita chuva, o rio traz mais terra. Damos à floresta aleatória (Tema 2) três "
                 "pistas: o caudal, a chuva dos últimos 7 dias e o mês."),
          code('PISTAS_SEM_MARE = ["caudal_m3s", "chuva_7d_mm", "mes"]\n'
               'floresta = RandomForestClassifier(n_estimators=100, random_state=0)\n'
               'floresta.fit(treino[PISTAS_SEM_MARE], treino["turva"])\n'
               'nota_sem_mare = acerto(teste["turva"], floresta.predict(teste[PISTAS_SEM_MARE]))\n'
               'sempre_turva = teste["turva"].mean()        # a nota de quem diz sempre «turva», sem modelo nenhum\n'
               'print("Acerto no teste, sem a maré:   ", percentagem(nota_sem_mare))\n'
               'print("Se disséssemos sempre «turva»: ", percentagem(sempre_turva))'),
          md("A floresta acerta **menos** do que dizer sempre «turva». Com estas pistas, a máquina **não aprendeu nada "
             "útil**, e mais árvores não resolvem. **Falta uma pista.**")]
    c += _nota(fac, f"Resultado esperado: {_pt(100 * R['a3_nota_sem_mare'])} % sem a maré, contra "
                    f"{_pt(100 * R['a3_sempre_turva'])} % de «dizer sempre turva». Pergunte à turma: \"o que pode mudar a "
                    "cor da água perto do mar, de um dia para o outro?\" Deixe-os pensar antes do Passo 5.")
    c += [_passo(5, "A pista que faltava: a maré",
                 "A foz do Incomáti fica no mar, e o mar sobe e desce duas vezes por dia. A tabela tem a altura da maré à "
                 "hora em que o satélite passou (cerca das 9:30). Vejamos a turbidez em cada altura da maré."),
          code('ver_mare(rio)'),
          md("Com a **maré baixa**, a água está quase sempre turva; com a **maré alta**, quase sempre mais limpa. Uma "
             "explicação simples: na maré alta entra água do mar, mais limpa; na maré baixa sai a água barrenta do rio.\n\n"
             "No projecto EYES TO EARTH aconteceu o mesmo: o modelo da água barrenta só começou a funcionar quando lhe "
             "demos a maré. **Na Prática 3, são vocês que juntam a maré ao modelo.**")]
    baixa, media, alta = (R["a3_turva_mare"][k] for k in ("maré baixa", "maré média", "maré alta"))
    c += _nota(fac, f"Resultado esperado: água turva em {_pt(100 * baixa, 0)} % das manhãs de maré baixa, "
                    f"{_pt(100 * media, 0)} % na maré média e {_pt(100 * alta, 0)} % na maré alta. A maré é calculada para a "
                    "baía de Maputo à hora do satélite (o modelo de marés do projecto). No projecto, o modelo final da "
                    "turbidez (com a maré e a última medição do satélite) chega a ROC-AUC 0,88 e é o que a plataforma usa.")
    c += [_fim("- Treinámos uma **classificação** (turva ou não) com os dados de um assunto novo: a qualidade da água.\n"
               "- Com o caudal, a chuva e o mês, o modelo acerta **menos** do que «dizer sempre turva». Comparem sempre o "
               "modelo com «não fazer nada».\n"
               "- O gráfico mostrou a pista que faltava: a **maré**. Escolher as pistas certas vale mais do que o algoritmo.")]
    c += _guardar(fac, """
joblib.dump(floresta, "modelos_treinados/aula3_floresta_sem_mare.joblib")
treino.to_csv("separacoes/aula3_treino_2017_a_2022.csv", index=False)
teste.to_csv("separacoes/aula3_teste_2023_a_2026.csv", index=False)""")
    c.append(md(ERROS))
    return c


# ============================================================================ AULA 4

def aula4(fac, R):
    c = [_cabecalho(4, fac,
                    "**prever um número**: quanta água vai passar no rio daqui a 3 dias, a partir do caudal de hoje e da "
                    "chuva dos últimos dias. Treinamos com o passado e testamos com o futuro.",
                    [("regressão", "prever um número (e não uma categoria como água ou não água)"),
                     ("caudal", "quanta água passa no rio por segundo, em metros cúbicos por segundo (m³/s)"),
                     ("alvo", "o número que queremos prever: aqui, o caudal daqui a 3 dias"),
                     ("erro médio", "quanto a previsão falha, em média, em m³/s (em inglês, MAE)"),
                     ("profundidade", "o número de perguntas seguidas de uma árvore de decisão"),
                     ("sobreajuste", "o modelo decora o treino e falha nos dados novos")], R)]
    c += _nota(fac, "Objectivo: a regressão, a separação no tempo e o sobreajuste. Tempo: 10 minutos, no projector. "
                    "A seguir, a Prática 4, a 7 dias. Ligue à plataforma (Módulo 5): o caudal é o que decide o nível de alerta.")
    c += [_passo(1, "Abrir as ferramentas"),
          _ferramentas(fac, "from sklearn.linear_model import LinearRegression\nfrom sklearn.tree import DecisionTreeRegressor"),
          _passo(2, "Vinte anos de caudal e de chuva",
                 "Uma linha por dia, de 2006 a 2026. `caudal_m3s` é o caudal do Incomáti em Marracuene; `chuva_7d_mm`, "
                 "`chuva_14d_mm` e `chuva_30d_mm` são a chuva que caiu na bacia do rio nos últimos 7, 14 e 30 dias."),
          code('dias = pd.read_csv(encontrar("caudal_e_chuva_diarios.csv"), parse_dates=["data"])\n'
               'print("Dias na tabela:", numero(len(dias)), "de", dias["data"].min().strftime("%d/%m/%Y"), "a", dias["data"].max().strftime("%d/%m/%Y"))\n'
               'plt.figure(figsize=(10, 3.5))\n'
               'plt.plot(dias["data"], dias["caudal_m3s"], lw=0.8)\n'
               'plt.ylabel("caudal (m³/s)")\n'
               'plt.title("O caudal do Incomáti em Marracuene, 2006 a 2026")\n'
               'plt.show()\n'
               'dias[["data", "caudal_m3s", "chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"]].tail()'),
          _passo(3, "A pergunta: o caudal daqui a 3 dias",
                 "Queremos **prever um número**: isto é **regressão**. A coluna com a resposta certa chama-se **alvo**. "
                 "As **pistas** (as características) são o caudal de hoje e a chuva."),
          code('dias["caudal_daqui_a_3_dias"] = dias["caudal_m3s"].shift(-3)    # o alvo: o caudal 3 dias depois\n'
               'dias = dias.dropna()\n'
               'PISTAS = ["caudal_m3s", "chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"]\n'
               'ALVO = "caudal_daqui_a_3_dias"\n'
               'dias[["data"] + PISTAS + [ALVO]].head()'),
          _passo(4, "Separar no tempo: o exame é o futuro",
                 "Para saber se o modelo prevê o futuro, treinamos com os anos **2006 a 2018** e testamos com **2019 a "
                 "2026**, anos que ele nunca viu."),
          code('treino = dias[dias["data"].dt.year <= 2018]\n'
               'teste = dias[dias["data"].dt.year >= 2019]\n'
               'print("Dias de treino:", len(treino), "   Dias de teste:", len(teste))\n'
               'plt.figure(figsize=(10, 3.5))\n'
               'plt.plot(treino["data"], treino["caudal_m3s"], lw=0.8, label="treino (2006 a 2018)")\n'
               'plt.plot(teste["data"], teste["caudal_m3s"], lw=0.8, color="#C62828", label="teste (2019 a 2026)")\n'
               'plt.ylabel("caudal (m³/s)")\n'
               'plt.legend()\n'
               'plt.show()'),
          _passo(5, "A regressão linear",
                 "A **regressão linear** aprende um peso para cada pista: caudal daqui a 3 dias ≈ peso 1 × caudal de hoje "
                 "+ peso 2 × chuva de 7 dias + ... Os pesos são o que o modelo aprende com o treino."),
          code('linear = LinearRegression()\n'
               'linear.fit(treino[PISTAS], treino[ALVO])\n'
               'for pista, peso in zip(PISTAS, linear.coef_):\n'
               '    print(pista, "peso", numero(peso, 2))\n'
               'erro_treino = (treino[ALVO] - linear.predict(treino[PISTAS])).abs().mean()\n'
               'erro_teste = (teste[ALVO] - linear.predict(teste[PISTAS])).abs().mean()\n'
               'igual_a_hoje = (teste[ALVO] - teste["caudal_m3s"]).abs().mean()\n'
               'print()\n'
               'print("Erro médio no TREINO:", numero(erro_treino, 1), "m³/s")\n'
               'print("Erro médio no TESTE: ", numero(erro_teste, 1), "m³/s")\n'
               'print("Se disséssemos sempre «fica igual a hoje», o erro no teste seria", numero(igual_a_hoje, 1), "m³/s")'),
          md("O **erro médio** é quanto a previsão falha, em média, em m³/s. Quanto menor, melhor. O modelo erra mais no "
             "teste do que no treino: é normal, os anos de teste são novos para ele.")]
    c += _nota(fac, f"Resultado esperado: erro no treino {_pt(R['a4_erro_treino'])} m³/s, no teste {_pt(R['a4_erro_teste'])} m³/s; "
                    f"«igual a hoje» {_pt(R['a4_igual_a_hoje'])} m³/s. O modelo é melhor do que não fazer nada, mas pouco. "
                    "O peso maior é o do caudal de hoje: o rio de amanhã parece-se com o de hoje.")
    c += [_passo(6, "A cheia de Janeiro de 2026"),
          code('janeiro = teste[(teste["data"] >= "2026-01-01") & (teste["data"] <= "2026-02-15")]\n'
               'dia_previsto = janeiro["data"] + pd.Timedelta(days=3)\n'
               'plt.figure(figsize=(10, 3.8))\n'
               'plt.plot(dia_previsto, janeiro[ALVO], lw=2, label="caudal verdadeiro")\n'
               'plt.plot(dia_previsto, linear.predict(janeiro[PISTAS]), lw=2, ls="--", label="previsão feita 3 dias antes")\n'
               'plt.ylabel("caudal (m³/s)")\n'
               'plt.title("A cheia de Janeiro de 2026")\n'
               'plt.legend()\n'
               'plt.show()'),
          md("O modelo vê a subida, mas **chega tarde e fica abaixo**: só conhece a chuva que já caiu. Por isso a plataforma "
             "EYES TO EARTH usa também as previsões do modelo europeu **GloFAS**, que entram com a chuva prevista para os "
             "próximos dias.")]
    c += _nota(fac, "Mostre no gráfico o dia 13 de Janeiro: o modelo prevê muito menos do que o caudal que veio. Esta é a "
                    "melhor ponte para o Módulo 5: as previsões de chuva dão dias de avanço.")
    profs = R["a4_profundidades"]
    c += [_passo(7, "A árvore de regressão e o sobreajuste",
                 "Uma árvore de decisão também prevê números. Quanto mais funda (mais perguntas seguidas), melhor "
                 "decora o treino. Mas o que interessa é o erro no **teste**."),
          code('for profundidade in [1, 3, 5, 10, 20]:\n'
               '    arvore = DecisionTreeRegressor(max_depth=profundidade, random_state=0).fit(treino[PISTAS], treino[ALVO])\n'
               '    e_treino = (treino[ALVO] - arvore.predict(treino[PISTAS])).abs().mean()\n'
               '    e_teste = (teste[ALVO] - arvore.predict(teste[PISTAS])).abs().mean()\n'
               '    print(f"Profundidade {profundidade}: erro no treino", numero(e_treino, 1), "m³/s, erro no teste", numero(e_teste, 1), "m³/s")'),
          md("Com profundidade 20, o erro no treino é quase 0, mas no teste é maior: a árvore **decorou** o treino. "
             "Chama-se **sobreajuste**.")]
    c += _nota(fac, "Resultados esperados (erro no treino / no teste, em m³/s): " +
                    "; ".join(f"profundidade {p}: {_pt(v['treino'])} / {_pt(v['teste'])}" for p, v in profs.items()) +
                    f". A melhor é {R['a4_melhor_profundidade']}.")
    c += [_fim("- **Regressão**: prever um número (o caudal), não uma categoria.\n"
               "- Num modelo de previsão, separa-se no **tempo**: treina-se com o passado e testa-se com o futuro.\n"
               "- O **erro médio** diz quanto o modelo falha, nas unidades do alvo (m³/s).\n"
               "- Uma árvore muito funda **decora** o treino (**sobreajuste**) e erra mais nos dados novos.\n"
               "- Um modelo só sabe o que está nos dados: sem a chuva prevista, chega tarde à cheia.")]
    c += _guardar(fac, f"""
joblib.dump(linear, "modelos_treinados/aula4_regressao_linear.joblib")
melhor = DecisionTreeRegressor(max_depth={R['a4_melhor_profundidade']}, random_state=0).fit(treino[PISTAS], treino[ALVO])
joblib.dump(melhor, "modelos_treinados/aula4_arvore_profundidade_{R['a4_melhor_profundidade']}.joblib")
treino.to_csv("separacoes/aula4_treino_2006_a_2018.csv", index=False)
teste.to_csv("separacoes/aula4_teste_2019_a_2026.csv", index=False)""")
    c.append(md(ERROS))
    return c


AULAS = {1: aula1, 2: aula2, 3: aula3, 4: aula4}
