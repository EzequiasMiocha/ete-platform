"""Manual dos facilitadores da aula prática do Workshop 1, em PDF.

    .venv/bin/python scripts/build_workshop_manual.py

Escreve Pratica_Workshop_1/0_facilitadores/Manual_dos_Facilitadores_Aula_Pratica.pdf (via HTML e LibreOffice,
sem instalar nada). Os números vêm de respostas_de_referencia.json e as figuras dos notebooks já executados
por scripts/test_workshop.py (corra-o antes, para as figuras estarem actualizadas).
"""

import base64
import html
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import nbformat

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from workshop.comum import AULA, HA_CAMPO, fmt  # noqa: E402
from workshop.documentos import PARES  # noqa: E402
from workshop.exercicios import ANOS, campos, data_pt, rio_para_investigar  # noqa: E402

FAC = AULA / "0_facilitadores"
SAIDA = FAC / "Manual_dos_Facilitadores_Aula_Pratica.pdf"

CSS = """
body { font-family: 'DejaVu Sans', sans-serif; font-size: 10pt; color: #10231f; line-height: 1.35; }
h1 { font-size: 22pt; color: #082f2c; margin: 0 0 6pt 0; }
h2 { font-size: 15pt; color: #082f2c; border-bottom: 2pt solid #0f766e; padding-bottom: 2pt; margin-top: 14pt; }
h3 { font-size: 11.5pt; color: #0f766e; margin: 10pt 0 3pt 0; }
p { margin: 3pt 0 5pt 0; }
table { border-collapse: collapse; width: 100%; margin: 4pt 0 8pt 0; }
th { background: #082f2c; color: #ffffff; font-size: 9pt; padding: 3pt 4pt; text-align: left; }
td { border: 0.5pt solid #b9c9c5; font-size: 9pt; padding: 3pt 4pt; vertical-align: top; }
.caixa { background: #eef6f4; border: 1pt solid #0f766e; padding: 6pt 8pt; margin: 6pt 0; }
.alerta { background: #fff4e6; border: 1pt solid #e8893a; padding: 6pt 8pt; margin: 6pt 0; }
.capa { text-align: left; }
.pequeno { font-size: 8.5pt; color: #4b5f5b; }
.hora { font-weight: bold; color: #0f766e; white-space: nowrap; }
"""


def esc(t: str) -> str:
    return html.escape(t, quote=False)


def tabela(cabecalho, linhas, larguras=None):
    th = "".join(f"<th{f' width={larguras[i]}' if larguras else ''}>{c}</th>" for i, c in enumerate(cabecalho))
    trs = "".join("<tr>" + "".join(f"<td>{c}</td>" for c in linha) + "</tr>" for linha in linhas)
    return f"<table><tr>{th}</tr>{trs}</table>"


def caixa(conteudo, cor="#eef6f4", borda="#0f766e"):
    """Caixa de destaque como tabela de uma célula (o LibreOffice parte as div com borda linha a linha)."""
    return (f'<table cellpadding="6"><tr><td style="background:{cor}; border:1pt solid {borda}">'
            f'{conteudo}</td></tr></table>')


def quebra():
    return '<p style="page-break-before: always"></p>'


def figuras(pasta: Path):
    """Extrai as figuras dos notebooks executados: (natural, histograma, limiares, mapa, quadro)."""
    def pngs(nb_path):
        nb = nbformat.read(nb_path, as_version=4)
        out = []
        for c in nb.cells:
            for o in c.get("outputs", []):
                if "data" in o and "image/png" in o["data"]:
                    out.append((c.source, base64.b64decode(o["data"]["image/png"])))
        return out

    escolhas = {"natural": "eixo.imshow(cor_natural(img))", "histograma": "plt.hist(valores",
                "limiares": "LIMIARES = [-0.2, 0.0, 0.2]", "mapa": "mapa = np.ones(zona.shape"}
    guiado = pngs(FAC / "aula_guiada_COMPLETA_facilitador.ipynb")
    feitas = {}
    for nome, chave in escolhas.items():
        for fonte, dados in guiado:
            if chave in fonte:
                (pasta / f"{nome}.png").write_bytes(dados)
                feitas[nome] = pasta / f"{nome}.png"
                break
    quadro = pngs(FAC / "solucoes/quadro_da_turma_preenchido.ipynb")
    if quadro:
        (pasta / "quadro.png").write_bytes(quadro[-1][1])
        feitas["quadro"] = pasta / "quadro.png"
    return feitas


def img(fig, nome, largura_cm, legenda):
    if nome not in fig:
        return f'<p class="pequeno">[figura {nome} em falta: corra scripts/test_workshop.py]</p>'
    from PIL import Image
    largura_px = int(largura_cm / 2.54 * 96)          # o LibreOffice usa o tamanho real do PNG a 96 ppp
    original = Image.open(fig[nome])
    altura_px = int(original.height * largura_px / original.width)
    reduzida = fig[nome].with_name(f"{nome}_{largura_px}.png")
    original.convert("RGB").resize((largura_px * 2, altura_px * 2), Image.LANCZOS).save(reduzida, dpi=(192, 192))
    return (f'<p style="text-align:center"><img src="{reduzida.as_uri()}" width="{largura_px}" height="{altura_px}"></p>'
            f'<p class="pequeno" style="text-align:center">{legenda}</p>')


def conteudo(r: dict, fig: dict) -> str:
    r26 = r["2026"]
    nova26 = r26["agua_nova_ha"]
    partes = []
    a = partes.append

    # ---------- capa ----------
    a(f"""
<div class="capa">
<p class="pequeno">PROJECTO EYES TO EARTH (ETE) · WORKSHOP DE ESTUDANTES 1</p>
<h1>Manual dos facilitadores<br>Aula prática: ver a água a partir do espaço</h1>
<p><b>Sábado, 31 de Outubro de 2026 · 12:00–14:00 · 5 pares (10 estudantes) · Google Colab</b></p>
{caixa('\n<p><b>Para quem é este manual:</b> para toda a equipa ETE que vai estar na sala durante a prática. Explica\no que há na pasta <code>Pratica_Workshop_1</code>, o papel de cada pessoa e o que fazer em cada minuto das\nduas horas. Não é para os estudantes.</p>\n<p><b>Como ler:</b> a secção 1 dá a aula numa página. As secções 2 e 3 explicam o material. A secção 5 é o\ncronograma minuto a minuto, para levar impresso. A última página é um cartão de bolso.</p>\n')}
<h3>Índice</h3>
<p>1. A aula numa página<br>2. O que está na pasta e para que serve<br>3. Como funcionam os notebooks<br>
4. Quem faz o quê<br>5. Cronograma minuto a minuto (12:00–14:00)<br>6. A aula guiada passo a passo<br>
7. Os exercícios por pares<br>8. Apresentações e quadro da turma<br>9. Como ajudar um par<br>
10. Se o tempo apertar, ou se sobrar<br>11. Problemas frequentes<br>12. Antes do dia<br>
13. Glossário<br>14. Cartão de bolso</p>
</div>
""")

    # ---------- 1 ----------
    a(quebra())
    a(f"""
<h2>1. A aula numa página</h2>
<p><b>Objectivo.</b> No fim da prática, cada par consegue abrir imagens de satélite em Python, calcular os índices
de água NDWI e MNDWI, escolher um limiar, medir a área alagada em hectares e fazer o seu próprio mapa de água do
Incomáti. É o objectivo 4 do plano do workshop (e treina os objectivos 2 e 3).</p>
<p><b>O ponto de partida dos estudantes.</b> Não sabem Python. Por isso a aula tem três camadas, sempre com o
mesmo código, para que cada camada prepare a seguinte:</p>
{tabela(["Camada", "Quando", "O que é", "Quem conduz"], [
        ["1. Introdução ao Python", "Em casa (1 hora) e 15 min na aula", "3 notebooks curtos: Python, NumPy, Matplotlib, com exemplos do rio", "Estudantes; revisão por Ezequias"],
        ["2. Aula guiada", "12:25–13:10", "A equipa resolve no projector o problema da cheia de janeiro de 2026; os pares correm as mesmas células", "Ezequias"],
        ["3. Exercícios por pares", "13:10–13:40", "Cada par repete os mesmos passos para um ano diferente, com um desafio próprio", "Pares, com um padrinho cada"],
    ])}
<p><b>O problema da aula guiada.</b> <i>"Em janeiro de 2026 o Incomáti chegou a {fmt(r26['caudal_pico'])} m³/s. Quantos
hectares da planície de Marracuene ficaram debaixo de água? E onde?"</i></p>
{caixa(f"<p><b>Números a saber de cor (cheia de 2026):</b> água na seca {fmt(r26['agua_seca_ha'])} ha · água na cheia\npelo menos {fmt(r26['agua_chuvosa_ha'])} ha · <b>água nova {fmt(nova26)} ha = {fmt(nova26 / 100)} km² ≈ {fmt(nova26 / HA_CAMPO)} campos de\nfutebol</b> · nuvens {fmt(r26['nuvem_chuvosa_pct'])}% · o radar do ETE deu cerca de 214 km². Um píxel = 0,09 ha.</p>")}
<p><b>A ideia que queremos que levem para casa:</b> um número tirado de uma imagem de satélite só vale com o
contexto. A planície alaga a sério acima de 970 m³/s (2023 e 2026). Os anos que fogem à regra têm explicação:
nuvens (2021), imagem tirada tarde (2025) ou índice que falha (2022 e 2024).</p>
<p><b>Porque refizemos o material original.</b> O notebook inicial dava <b>−26 ha</b> de diferença entre a seca e
a cheia, ou seja, "não houve cheia". Havia três razões: a área começava a norte da vila e deixava de fora a planície;
o mar contava como água (cerca de 14 000 ha); e a "cheia" era de 8 de fevereiro, já em recuo. Agora a área cobre a
planície, o mar e as nuvens ficam de fora, e a imagem é de 24 de janeiro, cinco dias depois do pico.</p>
""")

    # ---------- 2 ----------
    a(quebra())
    a(f"""
<h2>2. O que está na pasta e para que serve</h2>
<p>Tudo está em <code>Pratica_Workshop_1/</code>. Os ficheiros originais do colega (<code>Aula_pratica_1_.ipynb</code>,
<code>ETE_Atividade_30m_vs_10m.ipynb</code> e o plano em PDF) ficam lá, sem alterações.</p>
{tabela(["Pasta / ficheiro", "Para quem", "O que é e quando se usa"], [
        ["<b>LEIA-ME.md</b>", "Todos", "Mapa da pasta e como abrir no Colab"],
        ["<b>0_facilitadores/</b>", "Só a equipa. <b>Não partilhar</b>", "Tudo o que é para nós"],
        ["  Manual_dos_Facilitadores_Aula_Pratica.pdf", "Equipa", "Este manual"],
        ["  aula_guiada_COMPLETA_facilitador.ipynb", "Condutor", "O notebook guiado já executado, com interpretação de cada resultado, frases para a turma, horas e respostas-modelo. Aberto no portátil do condutor, ao lado do notebook projectado"],
        ["  GUIA_DO_FACILITADOR.md", "Equipa", "Resumo em texto (respostas, desafios, correcções ao plano)"],
        ["  solucoes/solucao_AAAA.ipynb", "Padrinhos", "Os 10 exercícios resolvidos e executados, com respostas-modelo"],
        ["  solucoes/quadro_da_turma_preenchido.ipynb", "Condutor", "O gráfico final com as respostas de referência, para comparar"],
        ["  respostas_de_referencia.json", "Técnico", "Os números certos de cada ano (usados pelos verificadores)"],
        ["  imagens_para_slides/", "Módulos 3 e 4", "Falsa cor de Marracuene; seca e cheia com NDWI e MNDWI"],
        ["<b>1_introducao_python/</b>", "Estudantes, antes do dia", "1 Python (variáveis, listas, if, for, funções) · 2 NumPy (uma imagem é uma tabela) · 3 Matplotlib (desenhar). Cerca de 20 min cada"],
        ["<b>2_aula_guiada/</b>", "Todos, 12:25–13:10", "aula_guiada_cheia_2026.ipynb e a pasta dados/ (seca, cheia e o recorte 10 m vs 30 m)"],
        ["<b>3_exercicios/</b>", "Pares, 13:10–13:40", "COMO_TRABALHAR.md, quadro_da_turma.ipynb e 10 pastas ano_AAAA, cada uma com ENUNCIADO.md, exercicio_AAAA.ipynb e dados/"],
        ["<b>4_teste_do_aluno/</b>", "Estudantes (ou a equipa, para experimentar)", "12 perguntas com correcção automática e nota em 20"],
    ], ["32%", "18%", "50%"])}
<h3>Os dados</h3>
<p>Cada imagem é um ficheiro <code>.npz</code> (cerca de 6 MB) com 5 bandas (azul, verde, vermelho, NIR e SWIR), a
máscara <code>nuvem</code> (nuvem, sombra ou sem dados) e a máscara <code>zona</code> (distrito de Marracuene, sem o mar).
A área é a planície do Incomáti em Marracuene, 22 km × 33 km, a 30 m. Vêm do Google Earth Engine (Landsat 8 e
Sentinel-2) e as datas foram escolhidas medindo as nuvens só nesta área. <b>Na aula não se descarrega nada</b>:
cada par só precisa de uma pasta de cerca de 12 MB e das bibliotecas numpy e matplotlib, que já vêm no Colab.</p>
""")

    # ---------- 3 ----------
    a(f"""
<h2>3. Como funcionam os notebooks</h2>
<p>Todos os notebooks têm a mesma organização, para os estudantes reconhecerem o caminho:</p>
{tabela(["Sinal no notebook", "Quer dizer", "O que o estudante faz"], [
        ["▶", "Correr", "Clicar na célula e premir Shift + Enter"],
        ["✏ e os <code>...</code>", "Editar", "Trocar os três pontos pela conta ou pelo valor, e correr"],
        ["✍", "Responder por escrito", "Duplo clique na célula de texto por baixo e escrever"],
        ["✅ / ❌", "Verificação", "A célula diz se a resposta está certa (com 1% de margem) e dá uma dica se não estiver"],
    ])}
<h3>As três células de cada notebook que convém conhecer</h3>
<p><b>Célula 0 · ferramentas.</b> Chama as bibliotecas (numpy, matplotlib, os, glob) e cria as funções
<code>encontrar()</code> (procura o ficheiro de dados ao lado do notebook, na pasta dados/, no Colab ou no Drive; se
não o encontrar, abre a janela para o carregar), <code>carregar()</code> (abre o .npz e divide por 10 000 para ter a
reflectância entre 0 e 1), <code>cor_natural()</code> e <code>falsa_cor()</code>. É igual em todos os notebooks.</p>
<p><b>Célula 0b · verificador</b> (só nos exercícios). Tem as respostas certas codificadas e a função
<code>verificar()</code>. Também cria <code>preenchido()</code>: se um estudante saltar uma célula ✏, a seguinte pára
com a mensagem <i>"✏ Volte à célula anterior e troque os ... pela sua resposta"</i>. <b>É de propósito, não é um
erro do material.</b></p>
<p><b>A tabela "Se aparecer um erro"</b>, no fim de cada notebook, explica os 6 erros mais comuns em linguagem simples.</p>
<h3>Os passos são sempre os mesmos</h3>
{tabela(["Passo", "Aula guiada (2026)", "Exercício (cada ano)"], [
        ["0", "Ligar as ferramentas", "Ferramentas + verificador"],
        ["1", "Abrir as imagens", "Pensar antes de programar: tamanho do píxel e previsão"],
        ["2", "Ver em cor natural e falsa cor", "Abrir, ver e medir as nuvens"],
        ["3", "Assinatura espectral de 3 píxeis", "Escrever a fórmula do MNDWI"],
        ["4", "Calcular NDWI e MNDWI", "Limiar e área (seca, chuvosa, água nova)"],
        ["5", "Escolher o limiar (histograma)", "Investigar um píxel do rio"],
        ["6", "Contar a água em hectares", "O mapa final do par"],
        ["7", "O mapa final", "Conclusões e desafio do ano"],
        ["8–9", "Confirmar com outras fontes; 10 m contra 30 m", ""],
    ])}
""")

    # ---------- 4 ----------
    a(quebra())
    a(f"""
<h2>4. Quem faz o quê</h2>
<p>Proposta de papéis, a confirmar pela equipa no ensaio de quinta-feira, 29 de Outubro.</p>
{tabela(["Papel", "Quem (proposta)", "O que faz durante a prática"], [
        ["<b>Condutor</b>", "Ezequias Miocha", "Projecta e conduz a revisão de Python e a aula guiada; faz as perguntas à turma; tem a versão COMPLETA aberta no seu portátil; conduz as apresentações"],
        ["<b>Assistente técnico</b>", "Mussa Abdala", "Resolve problemas de Colab, Drive e ficheiros sem parar a aula; escreve os números dos pares no quadro da turma; tem o pen drive do plano B"],
        ["<b>Padrinhos de par</b> (1 por par)", "Agostinho Oliveira, Irene Timana, Gervásio Mate, Nilza Taide, Amilton Docole", "Ficam junto do seu par; ajudam sem tocar no teclado; dão o sinal (mão no ar) quando o par está pronto ou bloqueado"],
        ["<b>Cronometrista</b>", "Armenia Machava (moderadora)", "Avisa o condutor 5 minutos antes do fim de cada bloco; segura o tempo das apresentações (2,5 min por par)"],
        ["<b>Logística</b>", "Glads Sitoe", "Tomadas, extensões, Wi-Fi, enunciados impressos, água"],
    ], ["20%", "27%", "53%"])}
{caixa('<p><b>Regra de ouro dos padrinhos:</b> o estudante é que escreve. O padrinho aponta, pergunta e\nexplica, mas não faz por ele. Um estudante que corrige o seu próprio erro aprende mais do que em toda a teoria.</p>', "#fff4e6", "#e8893a")}
<h3>Distribuição dos anos pelos pares (na aula)</h3>
{tabela(["Par", "Ano", "Tema", "Dificuldade", "Resposta (água nova, MNDWI &gt; 0)"],
        [[p, str(ano), ANOS[ano]['titulo'], ANOS[ano]['estrelas'], fmt(r[str(ano)]['agua_nova_ha']) + " ha"] for p, ano in PARES],
        ["11%", "10%", "42%", "13%", "24%"])}
<p>Escolham o par mais confiante para 2021 (★★★). Os outros cinco anos (2017, 2019, 2020, 2022 e 2024) são para pares
que acabem cedo e para casa. O melhor ano extra para curiosos é o 2024 (★★★, o "mistério dos índices").</p>
""")

    # ---------- 5 ----------
    a(quebra())
    blocos = [
        ["<span class=hora>11:30–12:00</span>", "Durante o intervalo",
         "Ligar o projector e testar o som. Abrir no portátil do condutor: o notebook guiado (projectado) e a versão COMPLETA (só para ele). Correr a Célula 0 do guiado para confirmar. Padrinhos: confirmar que o seu par tem portátil, carregador, conta Google e Wi-Fi.",
         "Assistente: confirmar que a pasta partilhada no Drive abre num portátil de estudante."],
        ["<span class=hora>12:00–12:10</span>", "Arranque (10 min)",
         "Condutor: \"A missão: no fim, cada par entrega o seu mapa de água do Incomáti.\" Os pares abrem no Drive <code>2_aula_guiada/aula_guiada_cheia_2026.ipynb</code> com o Google Colaboratory e correm a Célula 0.",
         "Sinal de pronto: cada par vê \"Ferramentas prontas.\" Padrinhos levantam a mão quando o seu par chega lá."],
        ["<span class=hora>12:10–12:25</span>", "Python em 15 minutos",
         "No projector, só estas células: notebook 1 secções 2 (variáveis), 3 (listas), 4 (if) e 6 (funções); notebook 2 secções 2 (True/False e .sum()) e 3 (os píxeis A, B e C); notebook 3 secção 2 (imshow). Perguntar à sala antes de correr: \"o que vai aparecer?\"",
         "Não fazer os mini-exercícios aqui (ficam para casa). Se a turma já fez a preparação, encurtar para 10 min."],
        ["<span class=hora>12:25–13:10</span>", "Aula guiada (45 min)",
         "Passos 0 a 8 do notebook de 2026. O condutor projecta e corre uma célula de cada vez; os pares correm a mesma célula logo a seguir. Em cada passo: uma pergunta à sala, ouvir 1 ou 2 respostas, mostrar a interpretação (secção 6). O Passo 9 só se houver tempo.",
         "Cronometrista avisa às 13:05. Ver as horas de cada passo na secção 6."],
        ["<span class=hora>13:10–13:40</span>", "Exercícios por pares (30 min)",
         "13:10–13:13: cada par recebe o ENUNCIADO impresso do seu ano e abre <code>3_exercicios/ano_AAAA/exercicio_AAAA.ipynb</code>. 13:13–13:20: Parte A do enunciado em papel (previsão). 13:20–13:35: o notebook, até ao mapa final. 13:35–13:40: desafio e três frases para a apresentação.",
         "Padrinhos: usar a solução do ano (pasta solucoes/) no telemóvel ou impressa, só para eles. Cronometrista avisa às 13:35."],
        ["<span class=hora>13:40–13:55</span>", "Apresentações (15 min)",
         "Cada par, por ordem de ano (2014, 2016, 2021, 2023, 2025): mostra o mapa, diz o índice, o limiar, a água nova e a resposta ao desafio (2,5 min). O assistente escreve o número no <code>quadro_da_turma.ipynb</code>. No fim, o condutor projecta o gráfico e faz as 3 perguntas da secção 8.",
         "Cronometrista corta aos 2,5 min, com simpatia."],
        ["<span class=hora>13:55–14:00</span>", "Fecho da prática",
         "Condutor: as 3 ideias do dia (secção 8) e o \"desafio do analista\" (céu nublado: radar). Entrega à moderadora para o encerramento das 14:00.",
         "Lembrar: os exercícios que faltam e o teste do aluno ficam para casa."],
    ]
    a(f"""
<h2>5. Cronograma minuto a minuto (12:00–14:00)</h2>
{tabela(["Hora", "Bloco", "O que acontece", "Atenção"], blocos, ["12%", "15%", "48%", "25%"])}
{caixa('<p><b>Ritmo da aula guiada:</b> 45 minutos para 9 passos, cerca de 5 minutos por passo. A regra é\n<b>"correr, perguntar, interpretar"</b>: o condutor corre a célula, faz uma pergunta à sala, ouve uma ou duas respostas e\ndiz a interpretação. Não explicar linha a linha o código da Célula 0: basta dizer o que cada função faz.</p>')}
""")

    # ---------- 6 ----------
    a(quebra())
    passos = [
        ["0 e 1", "12:25–12:32", "Ligar as ferramentas e abrir as imagens",
         "\"Um dicionário é uma mochila com bolsos com nome.\" Pergunta: quantos píxeis tem a imagem?",
         "815 850 píxeis de 30 m × 30 m; 22 × 33 km. Seca a 23/10/2025 (5 m³/s); cheia a 24/01/2026 (1 693 m³/s), 5 dias depois do pico."],
        ["2", "12:32–12:38", "Ver a seca e a cheia; falsa cor",
         "\"De que cor é a água da cheia, e porquê?\"",
         "Castanha: sedimentos, turbidez alta. As manchas brancas são nuvens, com as sombras ao lado. Na falsa cor, a vegetação fica vermelha e a água preta."],
        ["3", "12:38–12:42", "Assinatura espectral de 3 píxeis",
         "\"Qual destes se parece com o A, o B e o C do Módulo 3?\"",
         "Rio ≈ A (0,058 / 0,061 / 0,030 / 0,008); vegetação ≈ B (NIR 0,517); solo ≈ C (sobe até ao SWIR 0,397)."],
        ["4", "12:42–12:47", "Calcular NDWI e MNDWI",
         "\"O mar aparece azul: contamos?\"",
         "Não, fica fora da zona (seriam cerca de 17 900 ha a mais nas duas datas). As nuvens dão um índice perto de 0 e metade passaria por água: por isso há a máscara de nuvens."],
        ["5", "12:47–12:53", "Escolher o limiar",
         "\"Onde fica o vale do histograma?\"",
         "Terra perto de −0,45, água perto de +0,8, vale perto de 0,1. Limiar −0,2: 22 105 ha; 0: 21 248 ha; +0,2: 20 689 ha. A área quase não muda (±4%), por isso o 0 serve."],
        ["6", "12:53–12:58", "Contar a água em hectares",
         "\"Porque dizemos 'pelo menos'?\"",
         f"Água nova {fmt(nova26)} ha = {fmt(nova26 / 100)} km² ≈ {fmt(nova26 / HA_CAMPO)} campos de futebol, cerca de metade da zona. É um mínimo: 19,5% não se vê."],
        ["7", "12:58–13:03", "O mapa final",
         "Cada par muda NOME_PAR e escreve a sua justificação.",
         "Verde-água: a planície da vila até ao limite norte. Azul escuro: o rio e as lagoas. Cinzento: nuvens, sobretudo nas dunas."],
        ["8", "13:03–13:06", "Confirmar com outras fontes",
         "\"E se estivesse nublado todos os dias?\"",
         "Radar Sentinel-1: atravessa as nuvens. O radar do ETE deu cerca de 214 km², parecido com os nossos 202 km²."],
        ["9 (extra)", "13:06–13:10", "10 m contra 30 m",
         "\"Para a cheia de janeiro de 2013, que satélite?\"",
         "Só o Landsat 7, com riscas sem dados (o Landsat 8 só ficou operacional em abril de 2013; o Sentinel-2 começou em 2015)."],
    ]
    a(f"""
<h2>6. A aula guiada passo a passo</h2>
<p>A versão completa (<code>0_facilitadores/aula_guiada_COMPLETA_facilitador.ipynb</code>) tem tudo isto por baixo de
cada resultado. Esta tabela é o resumo para ter impresso.</p>
{tabela(["Passo", "Hora", "O que se faz", "Pergunta à sala", "O que queremos ouvir / interpretação"], passos, ["8%", "11%", "19%", "22%", "40%"])}
{img(fig, "natural", 16.5, "O que os estudantes vêem no Passo 2: seca (23 out 2025) e cheia (24 jan 2026). A linha amarela é a zona em estudo.")}
""")
    a(quebra())
    a(f"""
<h3>O que vão ver nos Passos 5 a 7</h3>
{img(fig, "histograma", 14, "Passo 5: dois montes bem separados (terra à esquerda, água à direita). O limiar fica no vale.")}
{img(fig, "mapa", 9.5, "Passo 7: o mapa final. Verde-água = água nova; azul escuro = água na seca; cinzento = sem dados.")}
""")

    # ---------- 7 ----------
    a(quebra())
    linhas = []
    for ano in ANOS:
        lin, col, val = rio_para_investigar(ano)
        k = campos(r[str(ano)], ano, lin, col, val)
        ra = r[str(ano)]
        linhas.append([f"<b>{ano}</b> {ANOS[ano]['estrelas']}<br>{ANOS[ano]['titulo']}",
                       f"{ra['satelite']}<br>{data_pt(ra['data_chuvosa'])}<br>{fmt(ra['caudal_chuvosa'])} / {fmt(ra['caudal_pico'])} m³/s<br>nuvens {fmt(ra['nuvem_chuvosa_pct'])}%",
                       f"seca {fmt(ra['agua_seca_ha'])}<br>chuvosa {fmt(ra['agua_chuvosa_ha'])}<br><b>nova {fmt(ra['agua_nova_ha'])}</b>",
                       esc(ANOS[ano]['resposta'].format(**k)).replace("**", "")])
    a(f"""
<h2>7. Os exercícios por pares</h2>
<p>Cada par tem: o <b>ENUNCIADO</b> impresso (Parte A em papel: previsão e contas; Parte C: o desafio do ano) e o
notebook do ano, com 6 células ✏ para completar (área de um píxel, % de nuvens, fórmula do MNDWI, três áreas). As células
✅ confirmam cada resposta. O mapa final fica guardado como PNG e a última linha impressa é o número para o quadro da turma.</p>
<p><b>O que o par entrega:</b> o mapa PNG; três números (água na seca, água nova, % de nuvens); três frases de conclusão e
a resposta ao desafio.</p>
<h3>Respostas e interpretação de cada ano (MNDWI &gt; 0, zona sem mar, sem nuvens; em hectares)</h3>
{tabela(["Ano e tema", "Imagem chuvosa (caudal no dia / pico)", "Água (ha)", "Resposta-modelo ao desafio"], linhas, ["17%", "19%", "13%", "51%"])}
""")

    # ---------- 8 ----------
    a(quebra())
    a(f"""
<h2>8. Apresentações e quadro da turma (13:40–13:55)</h2>
<p><b>Como correr:</b> o assistente abre <code>3_exercicios/quadro_da_turma.ipynb</code>, corre a primeira célula, troca o
<code>None</code> de cada ano pelo número que o par apresentou e, no fim, corre a segunda célula para projectar o gráfico.
Para comparar, a versão preenchida está em <code>0_facilitadores/solucoes/</code>.</p>
<p><b>Cada par (2,5 min):</b> 1) mostra o mapa; 2) diz o índice e o limiar e porquê; 3) diz a água nova e a % de nuvens;
4) responde ao desafio do seu ano.</p>
{img(fig, "quadro", 16.5, "O gráfico final com as respostas de referência dos 10 anos e a cheia de 2026 (a laranja).")}
<h3>As três perguntas para a turma, com o gráfico projectado</h3>
<p>1. <b>Há relação entre o pico do caudal e a água nova?</b> Sim: a planície alaga a sério acima do limite vermelho (970 m³/s),
em 2023 e 2026; 2014 (728 m³/s) teve uma cheia média.<br>
2. <b>Que anos fogem à regra, e porquê?</b> 2021 (1 230 m³/s, mas 40% de nuvens e água barrenta que engana o NDWI); 2025 (imagem
8 dias depois do pico, a cheia já tinha passado); 2022 e 2024 (a água ficou demasiado escura e o MNDWI falhou).<br>
3. <b>Só com imagens ópticas, a plataforma conseguiria avisar a população a tempo?</b> Não: as nuvens tapam a cheia e a
imagem chega depois. Por isso o ETE junta previsão do caudal (GloFAS) e radar (Sentinel-1).</p>
{caixa('<p><b>As 3 ideias do dia (para o fecho às 13:55):</b> 1) Uma imagem de satélite é uma tabela de números,\numa por banda. 2) A água reflecte mais verde do que infravermelho: é o que os índices NDWI e MNDWI medem. 3) Um número de\nsatélite só vale com o contexto: nuvens, data da imagem e confirmação com outras fontes.</p>')}
""")

    # ---------- 9 e 10 ----------
    a(quebra())
    a(f"""
<h2>9. Como ajudar um par</h2>
{tabela(["Situação", "O que o padrinho faz"], [
        ["O par está parado e não pede ajuda", "Perguntar: \"Em que passo estão? O que diz a última linha?\" Apontar para a tabela de erros no fim do notebook"],
        ["Aparece um erro vermelho", "Ler a última linha em voz alta com eles; perguntar \"o que acham que quer dizer?\". Quase sempre é célula corrida fora de ordem ou ... por preencher"],
        ["\"Volte à célula anterior e troque os ...\"", "Normal: é o aviso de que falta uma célula ✏. Mostrar qual"],
        ["❌ no verificador", "Ler a dica com eles. Confirmar que LIMIAR = 0.0. Não dar a resposta: perguntar \"quantos hectares tem um píxel?\""],
        ["O par acabou cedo", "Pedir para refazer o mapa com o NDWI e comparar; depois dar o ano 2024 (★★★)"],
        ["O par está muito atrasado às 13:30", "Saltar o Passo 5 (investigar um píxel) e ir directo ao mapa final"],
        ["O problema é técnico (Colab, Drive, rede)", "Chamar o assistente técnico com a mão no ar; não parar a aula"],
    ], ["35%", "65%"])}
<h2>10. Se o tempo apertar, ou se sobrar</h2>
{tabela(["Às...", "Se estivermos atrasados", "O que cortar (por esta ordem)"], [
        ["12:25", "Mais de 5 min de atraso", "Python em 10 min em vez de 15 (só listas, if e o .sum() do numpy)"],
        ["12:50", "Ainda no Passo 4", "Saltar a falsa cor (Passo 2) e a barra deslizante (Passo 5)"],
        ["13:05", "Ainda no Passo 7", "Saltar o Passo 9; o Passo 8 em 1 minuto (só a pergunta do céu nublado)"],
        ["13:30", "Pares longe do mapa final", "Saltar o Passo 5 dos exercícios; o desafio fica para casa"],
        ["13:40", "Pouco tempo para apresentar", "Só 3 pares apresentam (2023, 2016, 2021: cheia grande, seca, nuvens); os outros dizem só o número"],
    ], ["10%", "30%", "60%"])}
<p><b>Se sobrar tempo:</b> o Passo 9 completo; a barra deslizante do limiar; refazer o mapa com o NDWI; um segundo ano para os
pares rápidos (2024).</p>
""")

    # ---------- 11 ----------
    a(quebra())
    a(f"""
<h2>11. Problemas frequentes</h2>
{tabela(["Problema", "Causa", "Solução"], [
        ["1. <code>FileNotFoundError: Não encontrei ...npz</code>", "O notebook foi aberto sem a pasta dados/ ao lado, ou o Drive não está montado", "No Colab: correr <code>from google.colab import drive; drive.mount('/content/drive')</code> e repetir a célula; ou carregar o ficheiro .npz quando o Colab abre a janela"],
        ["2. A janela para carregar o ficheiro não aparece", "Bloqueador de pop-ups", "Permitir pop-ups para colab.research.google.com, ou arrastar o ficheiro para o ícone de pasta à esquerda do Colab"],
        ["3. <code>NameError: name 'np' (ou 'seca') is not defined</code>", "Células corridas fora de ordem ou depois de reiniciar", "Menu Ambiente de execução → Reiniciar e executar tudo"],
        ["4. <code>AssertionError: Volte à célula anterior...</code>", "Ficaram ... por preencher", "Normal. Completar a célula ✏ anterior"],
        ["5. ❌ no verificador", "Conta errada ou LIMIAR diferente de 0", "Ler a dica; confirmar LIMIAR = 0.0"],
        ["6. O Colab pede para iniciar sessão", "O portátil não tem conta Google", "Usar a conta do colega do par; resolver isto no ensaio"],
        ["7. Colab lento ou \"memória esgotada\"", "Muitas figuras abertas", "Reiniciar o ambiente de execução (cada notebook usa menos de 500 MB)"],
        ["8. A barra deslizante não aparece", "Widgets bloqueados", "Ignorar: a célula anterior faz o mesmo com três limiares"],
        ["9. Sem Internet na sala", "Rede do local em baixo", "Plano B: o condutor corre tudo no seu portátil (Jupyter, a partir do pen drive) e projecta; os pares fazem a Parte A dos enunciados em papel e escolhem o limiar com o histograma projectado"],
    ], ["30%", "25%", "45%"])}
""")

    # ---------- 12 ----------
    a(f"""
<h2>12. Antes do dia</h2>
{tabela(["Quando", "O quê", "Quem"], [
        ["Terça 27", "Ler este manual e experimentar a aula como estudante: notebooks 1–3, a aula guiada, o ano 2024 e o teste do aluno", "Toda a equipa"],
        ["Quarta 28", "Enviar aos estudantes os 3 notebooks de introdução e o link do Colab: \"cerca de 1 hora antes de sábado\"", "Irene / Ezequias"],
        ["Quarta 28", "Criar no Google Drive a pasta partilhada (só leitura) com tudo <b>menos 0_facilitadores</b>", "Ezequias"],
        ["Quinta 29", "Ensaio geral: correr a aula guiada e 2 exercícios na rede do local, num portátil de estudante, com o cronómetro; confirmar os papéis da secção 4", "Toda a equipa"],
        ["Quinta 29", "Confirmar que cada par tem portátil, carregador e conta Google", "Glads"],
        ["Sexta 30", "Imprimir: 5 enunciados dos anos da aula (um por par), a secção 5 e o cartão de bolso (um por membro da equipa), as soluções dos 5 anos (uma por padrinho)", "Glads"],
        ["Sexta 30", "Pen drive com a pasta inteira (plano B)", "Ezequias"],
    ], ["13%", "67%", "20%"])}
<h3>Pontos a confirmar</h3>
<p>• A frase do exercício de 2021 sobre o ciclone Eloise (confirmar com as notícias de janeiro de 2021).<br>
• No plano teórico (PDF): a revisita do Sentinel-1 (o Sentinel-1B avariou em dezembro de 2021; o 1C foi lançado em
dezembro de 2024) e a pergunta da cheia de 2013 (só havia o Landsat 7, com riscas).<br>
• Os nomes dos padrinhos e do assistente técnico (secção 4).</p>
""")

    # ---------- 13 ----------
    a(quebra())
    a(f"""
<h2>13. Glossário (para responder a perguntas dos estudantes)</h2>
{tabela(["Termo", "Explicação simples"], [
        ["Píxel", "Um quadradinho da imagem. Aqui cada um tem 30 m × 30 m = 900 m² = 0,09 ha"],
        ["Banda", "A imagem tirada numa \"cor\" de luz: azul, verde, vermelho, NIR ou SWIR"],
        ["NIR", "Infravermelho próximo. A vegetação reflecte muito, a água quase nada"],
        ["SWIR", "Infravermelho de onda curta. A água absorve-o quase todo"],
        ["Reflectância", "A fracção de luz que a superfície devolve, de 0 (nada) a 1 (tudo)"],
        ["NDWI", "(Verde − NIR) ÷ (Verde + NIR). Positivo: provável água (McFeeters, 1996)"],
        ["MNDWI", "(Verde − SWIR) ÷ (Verde + SWIR). Separa melhor a água da vila e do solo escuro, e aguenta melhor a água barrenta (Xu, 2006)"],
        ["Limiar", "O valor do índice a partir do qual dizemos \"é água\". O 0 é o ponto de partida"],
        ["Histograma", "Gráfico que conta quantos píxeis têm cada valor. O limiar fica no vale entre a terra e a água"],
        ["Máscara", "Uma tabela de True/False do tamanho da imagem: <code>nuvem</code> e <code>zona</code>"],
        ["Zona em estudo", "O distrito de Marracuene sem o mar, dentro da planície recortada"],
        ["Água nova", "Água na estação chuvosa que não era água na seca, contando só píxeis vistos nas duas datas"],
        ["Caudal", "Quanta água passa no rio por segundo, em m³/s (modelo GloFAS). Alertas do ETE: laranja 376, vermelho 970"],
        ["Turbidez", "Água \"barrenta\", com sedimentos. Aparece castanha na cor natural"],
        ["Radar (Sentinel-1)", "Satélite que envia a sua própria onda e vê através das nuvens"],
        ["Contas rápidas", "ha = píxeis × 0,09 · km² = ha ÷ 100 · campos de futebol = ha ÷ 0,714"],
    ], ["22%", "78%"])}
""")

    # ---------- 14 cartão ----------
    a(quebra())
    a(f"""
<h2>14. Cartão de bolso</h2>
{tabela(["Hora", "Bloco", "Lembrete"], [
        ["11:30", "Preparação", "Projector, notebooks abertos, Célula 0 corrida, pares com conta Google"],
        ["12:00", "Arranque", "Missão: \"cada par entrega o seu mapa\". Todos com \"Ferramentas prontas.\""],
        ["12:10", "Python 15 min", "Variáveis, listas, if, funções, .sum() de True, imshow"],
        ["12:25", "Aula guiada", "Correr, perguntar, interpretar. Passos 0–8 (o 9 é extra)"],
        ["13:05", "Aviso", "Faltam 5 minutos para os exercícios"],
        ["13:10", "Exercícios", "Enunciado em papel (7 min) → notebook (15 min) → desafio (5 min)"],
        ["13:35", "Aviso", "Preparar o mapa e as 3 frases"],
        ["13:40", "Apresentações", "2,5 min por par; números no quadro da turma; gráfico e 3 perguntas"],
        ["13:55", "Fecho", "As 3 ideias do dia; desafio do analista: radar"],
        ["14:00", "Encerramento", "Passar à moderadora"],
    ], ["12%", "20%", "68%"])}
{tabela(["Ano", "Par", "Água nova (ha)", "A lição"], [
        ["2026 (guia)", "Todos", fmt(nova26), "Cheia enorme; 19,5% de nuvens: é um mínimo"],
        ["2023", "Par 1", fmt(r['2023']['agua_nova_ha']), "Cheia grande; a planície fica alagada dias depois do pico"],
        ["2014", "Par 2", fmt(r['2014']['agua_nova_ha']), "Só Landsat; o MNDWI vê mais do que o NDWI (água barrenta)"],
        ["2016", "Par 3", fmt(r['2016']['agua_nova_ha']), "Seca do El Niño: menos água do que na seca anterior"],
        ["2025", "Par 4", fmt(r['2025']['agua_nova_ha']), "A imagem chegou 8 dias depois do pico"],
        ["2021", "Par 5", fmt(r['2021']['agua_nova_ha']), "40% de nuvens (um mínimo); o NDWI falha com água barrenta"],
    ], ["17%", "13%", "17%", "53%"])}
<p class="pequeno">Um píxel = 0,09 ha · campo de futebol = 0,714 ha · LIMIAR = 0.0 para verificar · Plano B: pen drive com o assistente técnico.</p>
""")
    return "".join(partes)


def main() -> None:
    respostas = json.loads((FAC / "respostas_de_referencia.json").read_text(encoding="utf-8"))
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        fig = figuras(tmp)
        pagina = f"""<!DOCTYPE html><html lang="pt"><head><meta charset="utf-8">
<title>Manual dos facilitadores · Aula prática · Workshop 1 ETE</title><style>{CSS}</style></head>
<body>{conteudo(respostas, fig)}</body></html>"""
        fonte = tmp / "Manual_dos_Facilitadores_Aula_Pratica.html"
        fonte.write_text(pagina, encoding="utf-8")
        perfil = tmp / "perfil_lo"
        subprocess.run(["soffice", f"-env:UserInstallation={perfil.as_uri()}", "--headless",
                        "--convert-to", "pdf:writer_web_pdf_Export", "--outdir", str(tmp), str(fonte)],
                       check=True, capture_output=True, timeout=300)
        shutil.copy(tmp / "Manual_dos_Facilitadores_Aula_Pratica.pdf", SAIDA)
    print(SAIDA.relative_to(ROOT), f"{SAIDA.stat().st_size / 1024:.0f} KB")


if __name__ == "__main__":
    main()
