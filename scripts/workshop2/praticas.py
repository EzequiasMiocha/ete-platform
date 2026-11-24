"""As 4 práticas do Workshop 2: os pares escrevem o código sozinhos, num caso novo, depois de cada aula guiada.

Cada prática existe em duas versões, geradas do mesmo texto:
  aluno        Workshop_2/2_pratica/N_Pratica_*.ipynb: em cada passo, uma célula para escreverem o código
               (com uma pista comentada) e uma célula que diz se está certo: verificar_passo("N.P")
  facilitador  Workshop_2/0_facilitadores/aulas_resolvidas/N_Pratica_*_RESOLVIDA.ipynb: o código escrito, as notas
               e uma célula que guarda os modelos treinados e as separações.
Português de Portugal (ortografia anterior ao Acordo de 1990), sem emojis.
"""

from .aulas import ERROS, PARES, _ficha, _fim, _guardar, _nota, _pt
from .comum import ANO_POR_PAR, code, md

HORARIO_PRATICA = {1: ("11:50", "12:05", 15), 2: ("12:17", "12:35", 18), 3: ("12:43", "12:55", 12), 4: ("13:05", "13:20", 15)}
TITULOS_PRATICA = {1: "A água no vosso ano", 2: "Treinar e testar, sozinhos", 3: "Juntar a maré ao modelo",
                   4: "Prever o caudal daqui a 7 dias"}
FICHEIROS_PRATICA = {1: "1_Pratica_a_agua_no_vosso_ano", 2: "2_Pratica_treinar_e_testar", 3: "3_Pratica_juntar_a_mare",
                     4: "4_Pratica_prever_7_dias"}

# Perguntas de escolha das práticas: (letra certa, explicação quando acertam, dica quando erram)
RESPOSTAS_PRATICA = {
    "P1.a": ("a", "Aprender com exemplos que já têm a resposta certa (os rótulos) é aprendizagem supervisionada.",
             "Pensem: a árvore recebeu as respostas certas durante o treino?"),
    "P1.b": ("b", "A regra muda com a água: cada imagem tem a sua cor de água, e o modelo aprende a desse dia.",
             "Comparem a vossa regra com a de 2026 (SWIR ≤ 0,04) e com a dos outros pares."),
    "P2.a": ("b", "O modelo já conhece os exemplos do treino: a nota sairia boa de mais e não provaria nada.",
             "Imaginem um exame com as mesmas perguntas que já viram resolvidas."),
    "P2.b": ("b", "Com uma só árvore, o acerto no teste desce. Muitas árvores a votar corrigem os erros umas das outras.",
             "Comparem o acerto no teste com 1 árvore e com 100 árvores."),
    "P2.c": ("b", "Água perdida quer dizer que havia água e o modelo não a viu: uma pessoa pode ficar sem aviso.",
             "Qual dos dois erros pode deixar uma família sem aviso de cheia?"),
    "P3.a": ("a", "Com a maré, o acerto sobe muito: era a pista que faltava. No projecto aconteceu o mesmo.",
             "Comparem a vossa nota do Passo 5 com a nota sem a maré da Aula 3."),
    "P3.b": ("a", "Na maré alta entra água do mar, mais limpa; na maré baixa sai a água barrenta do rio.",
             "Vejam o gráfico de barras da Aula 3 (Passo 5): na maré alta, quantas manhãs são turvas?"),
    "P3.c": ("a", "Um modelo só aprende o que está nos dados. Sem a maré, mais árvores não resolviam: faltava a informação.",
             "Na Aula 3, mais árvores resolviam? O que fez a diferença?"),
    "P4.a": ("a", "Um modelo de previsão vai ser usado no futuro. Por isso testa-se com anos que ele nunca viu.",
             "Para que serve uma previsão do caudal?"),
    "P4.b": ("a", "Quanto mais longe no futuro, mais coisas podem mudar: a previsão a 7 dias erra mais do que a 3.",
             "Comparem o vosso erro a 7 dias com o da Aula 4, a 3 dias (26,3 m³/s)."),
    "P4.c": ("a", "Sem o caudal de hoje, o erro sobe muito: o rio de amanhã parece-se muito com o rio de hoje.",
             "Comparem o erro com todas as pistas e só com a chuva."),
    "P4.d": ("a", "Sobreajuste: o modelo decora os exemplos do treino e falha nos dados novos.",
             "Lembrem-se da Aula 4: a árvore com profundidade 20."),
}

COMO_PRATICAR = """**Como praticar:** agora são vocês que escrevem o código. Em cada passo há uma célula com uma **pista**
(linhas que começam por `#`). Escrevam o código por baixo da pista (podem copiar a pista, tirar o `#` e trocar os
`...`), corram a célula com **Shift + Enter**, e depois corram a célula de verificação: diz «Certo!», ou
«Ainda não» com uma pista. A aula guiada que acabaram de ver tem os mesmos passos: usem-na como modelo."""


def _cabecalho_pratica(n, fac, missao, R):
    inicio, fim, minutos = HORARIO_PRATICA[n]
    titulo = f"# Prática {n} · {TITULOS_PRATICA[n]}"
    if fac:
        titulo += "\n\n**VERSÃO DO FACILITADOR: o código escrito, com notas.** Não copiar para os computadores dos alunos."
    return md(f"""{titulo}

**{minutos} minutos ({inicio}–{fim}) · em pares, sozinhos** · depois da Aula {n}

**A missão:** {missao}

{_ficha(f'pratica{n}', R)}

{COMO_PRATICAR}""")


def _escrever(fac, pista, solucao, extra=""):
    """A célula em que os alunos escrevem: a pista comentada (alunos) ou o código resolvido (facilitador)."""
    if fac:
        return code(solucao.strip())
    return code(("# Pista:\n" + "\n".join("# " + l for l in pista.strip().splitlines()) + "\n" + extra).strip())


def _verificar(passo):
    return code(f'verificar_passo("{passo}")      # a verificação: corram sem mudar nada')


def _pergunta(fac, chave, texto, certa):
    return [md(texto), code(f'resposta = "{certa}"\nverificar("{chave}", resposta)' if fac
                            else f'resposta = ...      # a letra entre aspas, por exemplo "a"\nverificar("{chave}", resposta)')]


def _passo(n, titulo, texto=""):
    return md(f"## Passo {n} · {titulo}" + (f"\n\n{texto}" if texto else ""))


def _ferramentas(fac, extra):
    if fac:
        texto = """import os, sys
for pasta in [".", os.path.join("..", "..", "2_pratica")]:          # a pasta onde está o ferramentas.py
    if os.path.exists(os.path.join(pasta, "ferramentas.py")):
        sys.path.insert(0, pasta)
        break
from ferramentas import *"""
    else:
        texto = "from ferramentas import *      # as ferramentas: corram sem mudar nada"
    return code(texto + "\n" + extra + '\nprint("Ferramentas prontas.")')


# ============================================================================ PRÁTICA 1

def pratica1(fac, R):
    anos = R["p1_anos"]
    c = [_cabecalho_pratica(1, fac, "ensinar a máquina a reconhecer a água numa imagem de **outro ano**, com os exemplos "
                                    "desse ano, e descobrir que regra ela aprende. Cada par tem o seu ano.", R)]
    c += _nota(fac, "Objectivo: que escrevam sozinhos as quatro linhas centrais do Machine Learning: a tabela dos exemplos, "
                    "X e y, fit e predict. O padrinho aponta para o passo igual da Aula 1, mas não escreve por eles.")
    c += [_passo(1, "Abrir as ferramentas"),
          _ferramentas(fac, "from sklearn.tree import DecisionTreeClassifier"),
          _passo(2, "O vosso ano", "Escrevam o ano do vosso par em `ANO` e corram.\n\n| Par | Ano |\n| --- | --- |\n" + PARES),
          code(('ANO = 2021          # o ano do vosso par' if fac else 'ANO = ...          # o ano do vosso par (vejam a tabela)')
               + '\nif pronto(ANO) and ano_do_par(ANO):\n'
                 '    img = carregar(f"incomati_{ANO}_chuvosa.npz")\n'
                 '    pontos = pontos_da_equipa(ANO)\n'
                 '    ver_imagem(img, f"O vosso ano: {img[\'dia\']}", pontos["agua"], pontos["nao_agua"])'),
          _verificar("1.2"),
          _passo(3, "A tabela dos exemplos",
                 "Façam a tabela dos exemplos com os pontos do vosso ano. Na Aula 1 (Passo 4), a imagem chamava-se "
                 "`cheia`; aqui chama-se `img`."),
          _escrever(fac, 'exemplos = tabela_de_exemplos(..., pontos["agua"], pontos["nao_agua"])',
                    'exemplos = tabela_de_exemplos(img, pontos["agua"], pontos["nao_agua"])\nexemplos.head()'),
          _verificar("1.3"),
          _passo(4, "As características e os rótulos",
                 "`X` são as 5 bandas (a lista `BANDAS`) e `y` é a coluna `\"rótulo\"`. Vejam a Aula 1, Passo 6."),
          _escrever(fac, 'X = exemplos[...]\ny = exemplos[...]', 'X = exemplos[BANDAS]\ny = exemplos["rótulo"]'),
          _verificar("1.4"),
          _passo(5, "Treinar a árvore", "Criem a árvore e treinem-na com `X` e `y`. A verificação mostra a regra que ela aprendeu."),
          _escrever(fac, 'arvore = DecisionTreeClassifier(max_depth=2, random_state=0)\narvore.fit(..., ...)',
                    'arvore = DecisionTreeClassifier(max_depth=2, random_state=0)\narvore.fit(X, y)'),
          _verificar("1.5")]
    c += _nota(fac, "A regra aprendida em cada ano (primeira pergunta da árvore): " +
                    "; ".join(f"{a}: {v['banda'].upper()} ≤ {_pt(v['limite'], 3)}" for a, v in anos.items()) +
                    ". Em 2026 era SWIR ≤ 0,04. Em 2021 (água barrenta) o limite do SWIR sobe muito; em 2022 e 2024 a árvore "
                    "prefere a banda vermelha. Boa conversa para as apresentações.")
    c += [_passo(6, "Prever: o mapa da água", "Usem a árvore para desenhar o mapa da água do vosso ano (Aula 1, Passo 7)."),
          _escrever(fac, 'mapa = prever_mapa(..., ...)\nver_mapa(mapa, img, "Água segundo a nossa árvore")',
                    'mapa = prever_mapa(arvore, img)\nver_mapa(mapa, img, "Água segundo a nossa árvore")'),
          _verificar("1.6")]
    c += _nota(fac, "Hectares de água em cada ano: " + "; ".join(f"{a}: {_pt(v['hectares'], 0)}" for a, v in anos.items()) + ".")
    c += [md("## Para pensar")]
    c += _pergunta(fac, "P1.a", "A árvore aprendeu com exemplos que já tinham a resposta certa. Isto é aprendizagem...\n\n"
                   "a) supervisionada  \nb) não supervisionada  \nc) por reforço", "a")
    c += _pergunta(fac, "P1.b", "A regra que a árvore aprendeu no vosso ano é igual à de 2026 (SWIR ≤ 0,04)?\n\n"
                   "a) sim, a regra é sempre a mesma  \nb) não: muda com a cor da água de cada dia", "b")
    c += [md("**Para a apresentação:** anotem a regra do vosso ano (a banda e o limite).")]
    c += [_fim("- Escreveram sozinhos o caminho do Machine Learning: **exemplos**, **X e y**, **treinar** (fit) e "
               "**prever** (predict).\n- Cada imagem tem a sua cor de água: o modelo aprende a regra desse dia.")]
    c += _guardar(fac, """
joblib.dump(arvore, f"modelos_treinados/pratica1_arvore_{ANO}.joblib")
exemplos.to_csv(f"separacoes/pratica1_exemplos_{ANO}.csv", index=False)""")
    c.append(md(ERROS))
    return c


# ============================================================================ PRÁTICA 2

def pratica2(fac, R):
    c = [_cabecalho_pratica(2, fac, "fazer vocês a separação em treino e teste, treinar a floresta, calcular as duas notas e "
                                    "fazer o exame com o mapa oficial. Desta vez, o teste são os **primeiros** 5 + 5 pontos "
                                    "(na aula eram os últimos).", R)]
    c += _nota(fac, f"Resultados esperados com esta separação: {R['p2_n_treino']} exemplos de treino e {R['p2_n_teste']} de "
                    f"teste; treino {_pt(100 * R['p2_treino'])} %, teste {_pt(100 * R['p2_teste'])} %; no mapa oficial "
                    f"{_pt(100 * R['p2_ems'])} %, com {_pt(R['p2_falsos'], 0)} falsos alarmes e {_pt(R['p2_perdida'], 0)} píxeis "
                    f"de água perdida; com 1 árvore, {_pt(100 * R['p2_1arvore_teste'])} % no teste.")
    c += [_passo(1, "Abrir as ferramentas e a imagem da cheia"),
          _ferramentas(fac, 'from sklearn.ensemble import RandomForestClassifier\n'
                            'cheia = carregar("incomati_2026_cheia.npz")\npontos = pontos_da_equipa(2026)'),
          _passo(2, "Separar: treino e teste",
                 "Cada lista tem 15 pontos. Os **primeiros 5** (`[:5]`) ficam para o teste; os **outros 10** (`[5:]`) "
                 "para o treino. Façam o mesmo para a terra (`pontos[\"nao_agua\"]`)."),
          _escrever(fac, 'agua_teste = pontos["agua"][...]\nagua_treino = pontos["agua"][...]\n'
                         'terra_teste = pontos["nao_agua"][...]\nterra_treino = pontos["nao_agua"][...]',
                    'agua_teste = pontos["agua"][:5]\nagua_treino = pontos["agua"][5:]\n'
                    'terra_teste = pontos["nao_agua"][:5]\nterra_treino = pontos["nao_agua"][5:]\n'
                    'ver_imagem(cheia, "Treino (cheios) e teste (contorno amarelo)", agua_treino, terra_treino, agua_teste, terra_teste)'),
          _verificar("2.2"),
          _passo(3, "As tabelas do treino e do teste", "Uma tabela para cada lado (Aula 2, Passo 2)."),
          _escrever(fac, 'treino = tabela_de_exemplos(cheia, ..., ...)\nteste = tabela_de_exemplos(cheia, ..., ...)',
                    'treino = tabela_de_exemplos(cheia, agua_treino, terra_treino)\nteste = tabela_de_exemplos(cheia, agua_teste, terra_teste)'),
          _verificar("2.3"),
          _passo(4, "Treinar a floresta", "Uma floresta de 100 árvores, treinada **só com o treino** (Aula 2, Passo 3)."),
          _escrever(fac, 'floresta = RandomForestClassifier(n_estimators=100, random_state=0)\nfloresta.fit(treino[BANDAS], ...)',
                    'floresta = RandomForestClassifier(n_estimators=100, random_state=0)\nfloresta.fit(treino[BANDAS], treino["rótulo"])'),
          _verificar("2.4"),
          _passo(5, "As duas notas", "Calculem o acerto no treino e no teste (Aula 2, Passo 4)."),
          _escrever(fac, 'nota_treino = acerto(treino["rótulo"], floresta.predict(treino[BANDAS]))\nnota_teste = acerto(..., ...)',
                    'nota_treino = acerto(treino["rótulo"], floresta.predict(treino[BANDAS]))\n'
                    'nota_teste = acerto(teste["rótulo"], floresta.predict(teste[BANDAS]))\n'
                    'print("Treino:", percentagem(nota_treino), "   Teste:", percentagem(nota_teste))'),
          _verificar("2.5"),
          _passo(6, "O exame com o mapa oficial e a matriz de confusão", "Aula 2, Passos 5 e 6."),
          _escrever(fac, 'verdade, previsto = exame_mapa_oficial(..., cheia)\nerros = matriz_de_confusao(verdade, previsto)',
                    'verdade, previsto = exame_mapa_oficial(floresta, cheia)\nprint("Acerto no exame:", percentagem(acerto(verdade, previsto)))\n'
                    'erros = matriz_de_confusao(verdade, previsto, "O nosso exame com o mapa oficial")'),
          _verificar("2.6"),
          _passo(7, "E com uma só árvore?", "Treinem uma floresta com `n_estimators=1` e calculem o acerto no teste em `nota_teste_1`."),
          _escrever(fac, 'uma = RandomForestClassifier(n_estimators=..., random_state=0)\numa.fit(treino[BANDAS], treino["rótulo"])\n'
                         'nota_teste_1 = acerto(teste["rótulo"], uma.predict(...))',
                    'uma = RandomForestClassifier(n_estimators=1, random_state=0)\numa.fit(treino[BANDAS], treino["rótulo"])\n'
                    'nota_teste_1 = acerto(teste["rótulo"], uma.predict(teste[BANDAS]))\nprint("Com uma só árvore, no teste:", percentagem(nota_teste_1))'),
          _verificar("2.7"),
          md("## Para pensar")]
    c += _pergunta(fac, "P2.a", "Porque é que não se avalia um modelo com os exemplos do treino?\n\na) porque demora mais tempo  \n"
                   "b) porque o modelo já os viu: a nota sai boa de mais  \nc) porque o computador não deixa", "b")
    c += _pergunta(fac, "P2.b", "Com uma só árvore, o acerto no teste...\n\na) sobe  \nb) desce  \nc) fica igual", "b")
    c += _pergunta(fac, "P2.c", "Num aviso de cheias, qual dos erros é mais perigoso?\n\na) o falso alarme (era terra e disse água)  \n"
                   "b) a água perdida (era água e disse terra)", "b")
    c += [md("**Para a apresentação:** anotem o acerto no teste e o número de falsos alarmes.")]
    c += [_fim("- Fizeram sozinhos a **separação** em treino e teste, o treino, as duas notas e o exame.\n"
               "- Com outra separação, os números mudam um pouco, mas a lição é a mesma: a nota que conta é a do teste.")]
    c += _guardar(fac, """
joblib.dump(floresta, "modelos_treinados/pratica2_floresta_100_arvores.joblib")
pd.DataFrame([(l, c, 1) for l, c in agua_treino] + [(l, c, 0) for l, c in terra_treino],
             columns=["linha", "coluna", "rótulo"]).to_csv("separacoes/pratica2_pontos_treino.csv", index=False)
pd.DataFrame([(l, c, 1) for l, c in agua_teste] + [(l, c, 0) for l, c in terra_teste],
             columns=["linha", "coluna", "rótulo"]).to_csv("separacoes/pratica2_pontos_teste.csv", index=False)""")
    c.append(md(ERROS))
    return c


# ============================================================================ PRÁTICA 3

def pratica3(fac, R):
    c = [_cabecalho_pratica(3, fac, "juntar a **maré** às pistas da floresta e ver se ela passa a prever a água turva. "
                                    "Depois, ver se a maré ajuda tanto longe do mar, no troço médio.", R)]
    c += _nota(fac, f"Resultados esperados: {_pt(R['p3_n_treino'], 0)} manhãs de treino e {_pt(R['p3_n_teste'], 0)} de teste; "
                    f"com a maré, {_pt(100 * R['p3_nota_com_mare'])} % no teste (sem a maré, na aula: "
                    f"{_pt(100 * R['a3_nota_sem_mare'])} %; dizer sempre «turva»: {_pt(100 * R['a3_sempre_turva'])} %). "
                    f"No troço médio, {_pt(100 * R['p3_nota_medio'])} % (dizer sempre «turva» lá: "
                    f"{_pt(100 * R['p3_sempre_medio'])} %); na foz, {_pt(100 * R['p3_nota_foz'])} %. A maré conta mais perto "
                    "do mar. É a lição do projecto: as pistas certas valem mais do que o algoritmo.")
    c += [_passo(1, "Abrir as ferramentas e os dados"),
          _ferramentas(fac, 'from sklearn.ensemble import RandomForestClassifier\n'
                            'rio = pd.read_csv(encontrar("cor_do_rio_e_mare.csv"))'),
          _passo(2, "Separar no tempo", "Como na Aula 3 (Passo 3): **treino de 2017 a 2022**, **teste de 2023 em diante**."),
          _escrever(fac, 'treino = rio[rio["ano"] <= ...]\nteste = rio[rio["ano"] >= ...]',
                    'treino = rio[rio["ano"] <= 2022]\nteste = rio[rio["ano"] >= 2023]'),
          _verificar("3.2"),
          _passo(3, "As pistas, agora com a maré",
                 "Escrevam a lista `PISTAS` com as três pistas da aula e a coluna da maré, `altura_da_mare_m`."),
          _escrever(fac, 'PISTAS = ["caudal_m3s", "chuva_7d_mm", "mes", "..."]',
                    'PISTAS = ["caudal_m3s", "chuva_7d_mm", "mes", "altura_da_mare_m"]'),
          _verificar("3.3"),
          _passo(4, "Treinar a floresta", "Aula 3, Passo 4, mas com as `PISTAS` novas. O rótulo é a coluna `turva`."),
          _escrever(fac, 'floresta = RandomForestClassifier(n_estimators=100, random_state=0)\nfloresta.fit(treino[...], treino["turva"])',
                    'floresta = RandomForestClassifier(n_estimators=100, random_state=0)\nfloresta.fit(treino[PISTAS], treino["turva"])'),
          _verificar("3.4"),
          _passo(5, "A nota no teste", "Calculem o acerto no teste em `nota_com_mare`."),
          _escrever(fac, 'nota_com_mare = acerto(teste["turva"], floresta.predict(teste[...]))\nprint("Acerto no teste, com a maré:", percentagem(nota_com_mare))',
                    'nota_com_mare = acerto(teste["turva"], floresta.predict(teste[PISTAS]))\nprint("Acerto no teste, com a maré:", percentagem(nota_com_mare))'),
          _verificar("3.5"),
          _passo(6, "Longe do mar", "O **troço médio** é o mais longe do mar. Separem só as linhas desse troço, treinem outra "
                 "floresta e calculem o acerto no teste em `nota_medio`. A pista tem quase tudo: troquem os `...`."),
          _escrever(fac, 'medio_treino = treino[treino["troco"] == "troço médio"]\nmedio_teste = teste[teste["troco"] == "troço médio"]\n'
                         'floresta_medio = RandomForestClassifier(n_estimators=100, random_state=0).fit(medio_treino[PISTAS], medio_treino["turva"])\n'
                         'nota_medio = acerto(medio_teste["turva"], floresta_medio.predict(medio_teste[...]))\n'
                         'print("No troço médio, com a maré:", percentagem(nota_medio))',
                    'medio_treino = treino[treino["troco"] == "troço médio"]\nmedio_teste = teste[teste["troco"] == "troço médio"]\n'
                    'floresta_medio = RandomForestClassifier(n_estimators=100, random_state=0).fit(medio_treino[PISTAS], medio_treino["turva"])\n'
                    'nota_medio = acerto(medio_teste["turva"], floresta_medio.predict(medio_teste[PISTAS]))\n'
                    'print("No troço médio, com a maré:", percentagem(nota_medio))'),
          _verificar("3.6"),
          md("## Para pensar")]
    c += _pergunta(fac, "P3.a", f"Sem a maré, a floresta acertou {_pt(100 * R['a3_nota_sem_mare'])} % (Aula 3). Com a maré, "
                   "o acerto...\n\na) subiu muito: a maré era a pista que faltava  \nb) ficou igual  \nc) desceu", "a")
    c += _pergunta(fac, "P3.b", "Perto da foz, quando a maré está **alta**, a água do rio costuma estar...\n\n"
                   "a) mais limpa  \nb) mais barrenta", "a")
    c += _pergunta(fac, "P3.c", "Qual é a grande lição desta prática?\n\na) um modelo só aprende o que está nos dados: escolher "
                   "as pistas certas vale mais do que o algoritmo  \nb) basta pôr mais árvores na floresta", "a")
    c += [md("**Para a apresentação:** anotem o acerto sem a maré e com a maré, e o que acontece longe do mar.")]
    c += [_fim("- Treinaram sozinhos uma **classificação** com os dados da qualidade da água.\n"
               "- A **maré** fez o acerto subir: foi a mesma descoberta do projecto EYES TO EARTH.\n"
               "- Longe do mar a maré conta menos: as pistas certas dependem do lugar.")]
    c += _guardar(fac, """
joblib.dump(floresta, "modelos_treinados/pratica3_floresta_com_mare.joblib")
joblib.dump(floresta_medio, "modelos_treinados/pratica3_floresta_troco_medio.joblib")
treino.to_csv("separacoes/pratica3_treino_2017_a_2022.csv", index=False)
teste.to_csv("separacoes/pratica3_teste_2023_a_2026.csv", index=False)""")
    c.append(md(ERROS))
    return c


# ============================================================================ PRÁTICA 4

def pratica4(fac, R):
    c = [_cabecalho_pratica(4, fac, "prever o caudal **daqui a 7 dias** (na aula eram 3), escrevendo vocês o alvo, a separação "
                                    "no tempo, o treino e o erro. Depois, ver o que acontece sem o caudal de hoje.", R)]
    c += _nota(fac, f"Resultados esperados: erro médio no teste a 7 dias {_pt(R['p4_erro_7'])} m³/s (a 3 dias era "
                    f"{_pt(R['a4_erro_teste'])}); «fica igual a hoje» a 7 dias erra {_pt(R['p4_igual_7'])}; só com a chuva, "
                    f"{_pt(R['p4_so_chuva_7'])} m³/s.")
    c += [_passo(1, "Abrir as ferramentas e os dados"),
          _ferramentas(fac, 'from sklearn.linear_model import LinearRegression\n'
                            'dias = pd.read_csv(encontrar("caudal_e_chuva_diarios.csv"), parse_dates=["data"])\n'
                            'PISTAS = ["caudal_m3s", "chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"]\n'
                            'ALVO = "caudal_daqui_a_7_dias"'),
          _passo(2, "O alvo: o caudal daqui a 7 dias", "Na Aula 4 (Passo 3), o alvo era `shift(-3)`. Aqui são 7 dias."),
          _escrever(fac, 'dias["caudal_daqui_a_7_dias"] = dias["caudal_m3s"].shift(...)',
                    'dias["caudal_daqui_a_7_dias"] = dias["caudal_m3s"].shift(-7)'),
          _verificar("4.2"),
          _passo(3, "Separar no tempo", "Tirem as linhas vazias e separem: **treino até 2018**, **teste de 2019 em diante** (Aula 4, Passo 4)."),
          _escrever(fac, 'dias = dias.dropna()\ntreino = dias[dias["data"].dt.year <= ...]\nteste = dias[dias["data"].dt.year >= ...]',
                    'dias = dias.dropna()\ntreino = dias[dias["data"].dt.year <= 2018]\nteste = dias[dias["data"].dt.year >= 2019]'),
          _verificar("4.3"),
          _passo(4, "Treinar a regressão linear", "Aula 4, Passo 5."),
          _escrever(fac, 'linear = LinearRegression()\nlinear.fit(treino[...], treino[...])',
                    'linear = LinearRegression()\nlinear.fit(treino[PISTAS], treino[ALVO])'),
          _verificar("4.4"),
          _passo(5, "O erro no teste", "Calculem o erro médio no teste em `erro_teste`."),
          _escrever(fac, 'erro_teste = (teste[ALVO] - linear.predict(teste[...])).abs().mean()\nprint("Erro médio a 7 dias:", numero(erro_teste, 1), "m³/s")',
                    'erro_teste = (teste[ALVO] - linear.predict(teste[PISTAS])).abs().mean()\nprint("Erro médio a 7 dias:", numero(erro_teste, 1), "m³/s")'),
          _verificar("4.5"),
          _passo(6, "Sem o caudal de hoje", "Treinem outra regressão só com a chuva (`SO_CHUVA`) e calculem o erro no teste em `erro_so_chuva`."),
          _escrever(fac, 'SO_CHUVA = ["chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"]\nso_chuva = LinearRegression().fit(treino[SO_CHUVA], treino[ALVO])\n'
                         'erro_so_chuva = (teste[ALVO] - so_chuva.predict(teste[...])).abs().mean()',
                    'SO_CHUVA = ["chuva_7d_mm", "chuva_14d_mm", "chuva_30d_mm"]\nso_chuva = LinearRegression().fit(treino[SO_CHUVA], treino[ALVO])\n'
                    'erro_so_chuva = (teste[ALVO] - so_chuva.predict(teste[SO_CHUVA])).abs().mean()\nprint("Só com a chuva:", numero(erro_so_chuva, 1), "m³/s")'),
          _verificar("4.6"),
          md("## Para pensar")]
    c += _pergunta(fac, "P4.a", "Porque é que o teste usa os anos 2019 a 2026 e não dias escolhidos ao acaso?\n\n"
                   "a) porque queremos saber se o modelo prevê o futuro, que ele nunca viu  \nb) por acaso", "a")
    c += _pergunta(fac, "P4.b", "Prever 7 dias à frente, comparado com 3 dias (Aula 4: 26,3 m³/s), é...\n\n"
                   "a) mais difícil: o erro é maior  \nb) mais fácil", "a")
    c += _pergunta(fac, "P4.c", "Qual é a pista mais importante para prever o caudal?\n\na) o caudal de hoje  \nb) a chuva de 30 dias", "a")
    c += _pergunta(fac, "P4.d", "Na Aula 4, a árvore com profundidade 20 tinha erro quase 0 no treino e maior no teste. Como se chama isto?\n\n"
                   "a) sobreajuste  \nb) subajuste  \nc) agrupamento", "a")
    c += [_fim("- Escreveram sozinhos uma **regressão**: o alvo, a separação no **tempo**, o treino e o **erro médio**.\n"
               "- Quanto mais longe no futuro, maior o erro; e o caudal de hoje é a pista mais importante."),
          md("## Fim da prática: preparar a apresentação (13:20–13:25)\n\nGuardem o trabalho (**Ctrl + S**). Na "
             "apresentação, cada par diz em 1 minuto:\n\n1. a **regra** que a árvore aprendeu no vosso ano (Prática 1);\n"
             "2. o **acerto no teste** e os **falsos alarmes** (Prática 2);\n3. o **acerto sem e com a maré** "
             "(Prática 3);\n4. o **erro a 7 dias** e sem o caudal de hoje (Prática 4);\n5. uma coisa que vos surpreendeu.")]
    c += _guardar(fac, """
joblib.dump(linear, "modelos_treinados/pratica4_regressao_7_dias.joblib")
treino.to_csv("separacoes/pratica4_treino_2006_a_2018.csv", index=False)
teste.to_csv("separacoes/pratica4_teste_2019_a_2026.csv", index=False)""")
    c.append(md(ERROS))
    return c


PRATICAS = {1: pratica1, 2: pratica2, 3: pratica3, 4: pratica4}
