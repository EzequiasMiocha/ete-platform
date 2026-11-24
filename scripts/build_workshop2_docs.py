"""Plano do dia e manual dos facilitadores do Workshop 2, em PDF (e o SLIDES.md com o link da apresentação).

    .venv/bin/python scripts/build_workshop2_docs.py

Escreve em Workshop_2/0_facilitadores/:
  Workshop2_Plano_do_dia_6h.pdf             o plano das 6 horas (cronograma, facilitadores, módulos, correspondência
                                            com o plano aprovado, preparação)
  Workshop2_Manual_dos_Facilitadores.pdf    a prática em detalhe (minuto a minuto, resultados, problemas, cartão)
  SLIDES.md                                 onde estão os slides e como os exportar
Via HTML e LibreOffice (sem instalar nada). Os números vêm de resultados_de_referencia.json (teoria) e de aulas_resolvidas/resultados_de_referencia.json (as 4 aulas).
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
from build_workshop_manual import CSS as CSS_WS1, caixa as caixa_ws1, img, tabela  # noqa: E402

# As regras de estilo do Workshop 1, nas cores dos slides do Workshop 2: preto, vermelho-escuro e cinzento (sem azul)
CORES = {"#10231f": "#1A1A1A", "#082f2c": "#1A1A1A", "#0f766e": "#A51C30", "#b9c9c5": "#CCCCCC", "#eef6f4": "#F4F4F4",
         "#4b5f5b": "#555555", "#fff4e6": "#EDEDED", "#e8893a": "#1A1A1A"}
CSS = CSS_WS1
for _velha, _nova in CORES.items():
    CSS = CSS.replace(_velha, _nova)


def caixa(conteudo, cor="#F4F4F4", borda="#A51C30"):
    return caixa_ws1(conteudo, CORES.get(cor, cor), CORES.get(borda, borda))


from workshop.comum import fmt  # noqa: E402
from workshop2.comum import ANO_POR_PAR, FAC, WS2  # noqa: E402

SLIDES_URL = "https://claude.ai/artifact/TCrXDZeA8uTCHr5R6ZmSbq"
IMAGENS = FAC / "imagens_para_slides"

# a ordem dos slides vem do próprio deck (a única fonte): os números dos slides citados mudam sozinhos
from workshop2.slides_ordem import NUM as N, ORDEM as ORDEM_SLIDES  # noqa: E402


def sl(a, b=None):
    """«slide 12» ou «slides 12 a 15», a partir dos identificadores."""
    return f"slide {N[a]}" if b is None else f"slides {N[a]} a {N[b]}"


FACILITADORES = [
    ["<b>Moderadora</b>", "Armenia Machava", "Todo o dia", "Abertura, questionário OAD, quiz relâmpago, controlo do tempo, perguntas escritas, encerramento e certificados"],
    ["<b>Facilitador 1</b>", "Comunicação de ciência", "08:25–09:05", "Revisão do Workshop 1 e Módulo 1 · na prática: padrinho do Par 1"],
    ["<b>Facilitador 2</b>", "IA e dados", "09:05–09:55", "Módulo 2, o centro do dia: tipos de aprendizagem, treino e algoritmos · padrinho do Par 2"],
    ["<b>Facilitador 3</b>", "Detecção remota e qualidade da água", "10:35–11:00", "Módulo 4 · padrinho do Par 3"],
    ["<b>Facilitador 4</b>", "Plataforma ETE", "11:00–11:20", "Módulo 5 e demonstração ao vivo · padrinho do Par 4"],
    ["<b>Facilitador 5</b>", "IA e Python (líder técnico)", "10:05–10:35 e 11:40–13:40", "Módulo 3 (avaliar um modelo), conduz a prática no projector e as apresentações dos pares"],
    ["<b>Facilitador 6</b>", "Apoio técnico (Jupyter, computadores)", "Antes do dia, 08:00 e 11:20–13:40", "Instala e verifica o Jupyter em cada computador; resolve problemas técnicos; escreve o quadro da turma"],
    ["<b>Facilitador 7</b>", "Qualquer membro da equipa", "11:40–13:25", "Padrinho do Par 5; presenças e fotografias"],
    ["<b>Logística</b>", "Como no Workshop 1", "Todo o dia", "Registo, crachás, matabicho, impressões, extensões eléctricas"],
]

_AR = json.loads((FAC / "aulas_resolvidas/resultados_de_referencia.json").read_text(encoding="utf-8"))   # números da prática

MODULOS = [
    dict(nome="Módulo 1 · O que é a Inteligência Artificial?", hora="08:35–09:05", quem="Facilitador 1", slides=f"{N['m1']} a {N['m1-gancho']}",
         abertura="Como é que o telemóvel sabe que a cara é a sua, mesmo de óculos ou com outro penteado?",
         conceitos=["Programação clássica (uma pessoa escreve as regras) contra Machine Learning (o computador descobre as regras a partir de exemplos com a resposta certa).",
                    "IA, Machine Learning e Deep Learning como caixas umas dentro das outras; o Deep Learning usa redes neuronais e precisa de milhões de exemplos.",
                    "Exemplos populares: filtro de spam, assistente de voz, desbloqueio facial, tradutor, recomendações de vídeos, mapas, ChatGPT, saúde.",
                    "Segurança e guerra: scanners de bagagem que assinalam armas e explosivos, câmaras com reconhecimento facial, drones e armas autónomas (debate na ONU desde 2014). Quem decide: a máquina ou uma pessoa?",
                    "Como aprende uma criança e uma máquina: exemplos, resposta certa, reconhecer o que é novo. A máquina só sabe o que viu."],
         actividade="Regra ou exemplos? (5 min, em pares): 6 tarefas. Respostas: troco = regra; voz da avó = exemplos; ordem alfabética = regra; spam = exemplos; metros em km = regra; água barrenta numa imagem = exemplos.",
         verificacao="Qual é a diferença entre escrever uma regra e treinar um modelo? Uma regra é escrita por uma pessoa e é sempre igual; um modelo é treinado com exemplos e muda se os exemplos mudarem."),
    dict(nome="Módulo 2 · Como uma máquina aprende", hora="09:05–09:55", quem="Facilitador 2", slides=f"{N['m2']} a {N['m2-actividade-votar']}",
         abertura="Como é que o scanner de um aeroporto aprende a reconhecer uma arma dentro de uma mala?",
         conceitos=["O que é um modelo (entrada → modelo → saída) e o que são os dados: exemplos (linhas), características (colunas, X) e rótulos (y). Treinar = modelo.fit(X, y); prever = modelo.predict(X_novo).",
                    "Os três tipos de aprendizagem: supervisionada (com rótulos), não supervisionada (sem rótulos) e por reforço (recompensas).",
                    "Supervisionada: classificação (a resposta é uma categoria: spam, arma ou sem arma, água) e regressão (a resposta é um número: preço, caudal).",
                    "Classificação com dados reais: os píxeis da cheia no gráfico NIR × SWIR e a fronteira de decisão.",
                    "Regressão: a recta horas de estudo → nota (dados inventados), o erro de cada exemplo, e como se treina: errar, medir o erro, corrigir, repetir (a curva de treino).",
                    "Regressão no nosso rio: o caudal daqui a 3 dias a partir do caudal de hoje e da chuva (GloFAS e CHIRPS); falha a subida rápida de Janeiro de 2026.",
                    "Não supervisionada: juntar o que é parecido, sem rótulos (o K-means). O projecto não a usou: tinha rótulos (os mapas oficiais das cheias), e os grupos não têm nome.",
                    "Por reforço: agente, acção, ambiente e recompensa (AlphaGo, robôs, drones); não se usa na prática.",
                    "Quatro algoritmos de classificação: árvore de decisão (perguntas, cortes direitos no espaço), Random Forest (votação), k vizinhos (a maioria dos mais parecidos), rede neuronal (camadas e pesos; a base do Deep Learning)."],
         actividade="Duas actividades em pares. «Que tipo de aprendizagem é?» (4 min): temperatura de amanhã = regressão; burla no WhatsApp = classificação; clientes em grupos = agrupamento; robô que aprende a andar = reforço; scanner de malas = classificação; caudal daqui a 3 dias = regressão; píxeis em grupos = agrupamento; nota pelas horas de estudo = regressão. «Sejam uma árvore de decisão» (6 min): 8 píxeis com NIR e SWIR; 2 perguntas; X é água, Y é solo; a turma vota como uma floresta.",
         verificacao="O quiz relâmpago, logo a seguir, verifica o Módulo 2."),
    dict(nome="Módulo 3 · Como sabemos se o modelo é bom?", hora="10:05–10:35", quem="Facilitador 5", slides=f"{N['m3']} a {N['m3-verificacao']}",
         abertura="Como é que um professor sabe se um aluno aprendeu a matéria, ou se só decorou as respostas?",
         conceitos=["O caminho completo do treino: pergunta, dados, rótulos, características, dividir, treinar, avaliar, usar.",
                    "Treino e teste (cerca de 70% e 30%); quando o tempo importa, o exame é o futuro.",
                    "No nosso rio: os rótulos (pontos marcados) e a regra de ouro (o exame independente do Copernicus EMS).",
                    "A matriz de confusão (água certa, terra certa, falso alarme, água perdida) e as notas: acerto, IoU, F1, Kappa, ROC-AUC; na regressão, o erro médio (MAE) e o R².",
                    "Subajuste, bom ajuste e sobreajuste; o erro no treino desce sempre, o erro no teste desce e depois sobe; escolhe-se a complexidade pelo teste.",
                    "Hiperparâmetros: os botões que nós escolhemos antes de treinar (número de árvores, profundidade, k, K, limiar). Escolhem-se com o exame, nunca com o treino; na prática experimentam-se três: o número de árvores, o K e a profundidade.",
                    "Decorar não é aprender: 100% no treino, 97% no exame."],
         actividade="A pergunta de verificação, com a resposta revelada no clique seguinte.",
         verificacao="Um modelo acerta 100% nos exemplos que estudou: está pronto? Não: tem de passar no exame com dados que nunca viu e rótulos independentes."),
    dict(nome="Módulo 4 · A IA e a qualidade da água", hora="10:35–11:00", quem="Facilitador 3", slides=f"{N['m4']} a {N['m4-actividade']}",
         abertura="Depois da cheia, o rio ficou castanho. O que é que essa cor nos diz sobre a água?",
         conceitos=["O que o satélite vê: turbidez e sedimentos (bem), clorofila-a (com cuidado: a lama engana o índice), plantas flutuantes (nos troços largos), temperatura (Landsat, 100 m).",
                    "A cor da água: o índice de turbidez NDTI = (vermelho − verde) ÷ (vermelho + verde); a pluma castanha da cheia na foz.",
                    "Os 9 troços do rio, de Ressano Garcia à foz; cada troço comparado com o seu próprio normal; as anomalias.",
                    f"A IA na turbidez (uma classificação): sem a maré, a floresta acerta {fmt(100 * _AR['a3_nota_sem_mare'], 1)} %, menos do que dizer sempre «turva» ({fmt(100 * _AR['a3_sempre_turva'], 1)} %); com a maré, {fmt(100 * _AR['p3_nota_com_mare'], 1)} %. O modelo final do projecto chega a ROC-AUC 0,88.",
                    "O que não mede: pH, oxigénio, nutrientes, metais, bactérias. Nunca dizer \"própria para beber\"; ferver ou tratar com cloro (Certeza)."],
         actividade="Verdade ou mito? (5 min): 6 afirmações. Respostas: V, M, M, V, M, V.",
         verificacao="Se a turbidez está normal, a água é boa para beber? Não: o satélite só vê a cor."),
    dict(nome="Módulo 5 · A plataforma EYES TO EARTH: do dado ao alerta", hora="11:00–11:20", quem="Facilitador 4", slides=f"{N['m5']} a {N['m5-actividade']}",
         abertura="Se o rio vai encher daqui a 4 dias, como avisamos quem vive na planície?",
         conceitos=["Do dado ao alerta em cinco passos: satélites, previsões (chuva e caudal), modelos e regras, nível de alerta, avisos.",
                    "Os gatilhos: caudal previsto (amarelo 164, laranja 376, vermelho 970 m³/s) e chuva anómala de 7 dias. Em Janeiro de 2026: laranja 4 a 5 dias antes.",
                    "Os quatro níveis (verde, amarelo, laranja, vermelho); o WhatsApp só envia em laranja ou vermelho.",
                    "As páginas Cheias, Mapa, Qualidade da água e Alertas; demonstração ao vivo (5 min).",
                    "Os alertas complementam os avisos oficiais (INGD, ARA-Sul, administração do distrito, rádio comunitária); não os substituem."],
         actividade="Que alerta daria? (4 min): A 120 = verde; B 250 = amarelo; C 600 = laranja; D 1 500 = vermelho; E 300 com máximo provável 450 = amarelo, mas com atenção (pode passar o laranja).",
         verificacao="A plataforma e um aviso oficial dizem coisas diferentes: qual seguir? O aviso oficial."),
]

QUIZ = [("Na aprendizagem supervisionada, o computador aprende com...", "B · exemplos com a resposta certa"),
        ("Prever o caudal do rio daqui a 3 dias é...", "B · regressão"),
        ("Os mapas oficiais da cheia, usados para treinar os nossos modelos, são…", "B · os rótulos"),
        ("Um scanner que marca as malas como «arma» ou «sem arma» faz...", "A · classificação"),
        ("Nos k vizinhos com k = 5, um píxel tem 4 vizinhos «água» e 1 «terra». O modelo diz...", "A · água")]


def converter(html_texto: str, destino: Path, pasta: Path):
    fonte = pasta / (destino.stem + ".html")
    fonte.write_text(html_texto, encoding="utf-8")
    perfil = pasta / "perfil_lo"
    subprocess.run(["soffice", f"-env:UserInstallation={perfil.as_uri()}", "--headless",
                    "--convert-to", "pdf:writer_web_pdf_Export", "--outdir", str(pasta), str(fonte)],
                   check=True, capture_output=True, timeout=300)
    shutil.copy(pasta / (destino.stem + ".pdf"), destino)
    print(destino.relative_to(ROOT), f"{destino.stem}: {destino.stat().st_size / 1024:.0f} KB")


def pagina(titulo, corpo):
    return f"""<!DOCTYPE html><html lang="pt"><head><meta charset="utf-8"><title>{titulo}</title>
<style>{CSS}</style></head><body>{corpo}</body></html>"""


def lista(itens):
    return "<ul>" + "".join(f"<li>{i}</li>" for i in itens) + "</ul>"


# ---------------------------------------------------------------- plano do dia
def plano(ref, ar) -> str:
    e = ref["ems_modelo"]
    k4, rg = ref["kmeans"]["4"], ref["regressao"]
    p = []
    a = p.append
    a(f"""
<p class="pequeno">PROJECTO EYES TO EARTH (ETE) · WORKSHOP DE ESTUDANTES 2</p>
<h1>Plano do Workshop 2 (6 horas)<br>Inteligência Artificial para monitorizar a água e avisar das cheias</h1>
<p><b>Sábado, 21 de Novembro de 2026 · 08:00–14:00 · Maputo</b></p>
{caixa(f'<p><b>Para quem:</b> a moderadora e os facilitadores. Acompanha a apresentação ({len(ORDEM_SLIDES)} slides com notas do orador) e a pasta <code>Workshop_2</code> (prática em Python, no Jupyter Notebook). O detalhe da prática está no <i>Manual dos facilitadores</i>.</p>')}
<h2>1. Enquadramento</h2>
{tabela(["Item", "Detalhe"], [
        ["Título", "Inteligência Artificial para monitorizar a água e avisar das cheias"],
        ["Data e duração", "Sábado, 21/11/2026 · 6 horas (08:00–14:00)"],
        ["Local", "Maputo"],
        ["Público-alvo", "Estudantes pré-universitários de áreas STEM, pelo menos 10. Não precisam de saber programar nem de ter participado no Workshop 1."],
        ["Formato", "Teoria interactiva (5 módulos com actividades e um quiz) + prática em pares (5 pares) no Jupyter Notebook, em computadores preparados de véspera"],
        ["Área de estudo", "Rio Incomáti, Marracuene: a cheia de Janeiro de 2026"],
        ["Moderação", "Armenia Machava (como no Workshop 1)"],
        ["Facilitação", "Facilitadores 1 a 7 (secção 3)"],
    ], ["22%", "78%"])}
<p><b>No fim do workshop, cada participante deve ser capaz de:</b></p>
<ol>
<li>Explicar a diferença entre escrever uma regra e treinar um modelo, e dar exemplos de IA no dia-a-dia.</li>
<li>Distinguir aprendizagem supervisionada (classificação e regressão), não supervisionada (agrupamento) e por reforço, com exemplos.</li>
<li>Descrever como se treina um modelo: dados, rótulos, características, treino e teste, e o erro a descer passo a passo.</li>
<li>Avaliar um modelo: a matriz de confusão, as notas, a regra de ouro do teste, o subajuste e o sobreajuste.</li>
<li>Dizer o que o satélite vê e o que não vê na qualidade da água.</li>
<li>Treinar em pares, em Python, classificadores (árvore de decisão e floresta aleatória, para a água da cheia e para a água barrenta) e uma regressão (o caudal do rio), avaliá-los com dados que nunca viram e explicar onde cada um erra.</li>
<li>Explicar como a plataforma EYES TO EARTH passa do dado ao alerta.</li>
</ol>
<p>Estes objectivos respondem ao Resultado 2 do plano OAD (capacidade dos estudantes), medido pelos questionários pré e pós-workshop.</p>
""")
    a(f"""
<h2>2. Cronograma (08:00–14:00)</h2>
{tabela(["Hora", "Bloco", "Conteúdo", "Responsável", "Slides"], [
        ["<span class=hora>08:00–08:15</span>", "Registo (15 min)", "Presenças e crachás; formar os 5 pares; os computadores já têm o Jupyter aberto na pasta da prática", "Logística + Facilitador 6", "1"],
        ["<span class=hora>08:15–08:35</span>", "Abertura (20 min)", "Boas-vindas, objectivo e programa (5) · questionário OAD pré-workshop (5) · revisão do Workshop 1 (10)", "Moderadora + Facilitador 1", f"1–{N['revisao-2024']}"],
        ["<span class=hora>08:35–09:05</span>", "Módulo 1 (25 + 5)", "O que é a Inteligência Artificial?", "Facilitador 1", f"{N['m1']}–{N['m1-gancho']}"],
        ["<span class=hora>09:05–09:55</span>", "Módulo 2 (43 + 7)", "Como uma máquina aprende: supervisionada (classificação, regressão), não supervisionada (só uma menção: o projecto não a usou), por reforço; quatro algoritmos", "Facilitador 2", f"{N['m2']}–{N['m2-actividade-votar']}"],
        ["<span class=hora>09:55–10:05</span>", "Quiz relâmpago (10)", "5 perguntas, uma por slide, em pares, cartões A/B/C; a resposta aparece no clique seguinte", "Moderadora", f"{N['quiz']}–{N['quiz-5']}"],
        ["<span class=hora>10:05–10:35</span>", "Módulo 3 (27 + 3)", "Como sabemos se o modelo é bom? Treino e teste, matriz de confusão, notas, subajuste e sobreajuste, hiperparâmetros", "Facilitador 5", f"{N['m3']}–{N['m3-verificacao']}"],
        ["<span class=hora>10:35–11:00</span>", "Módulo 4 (22 + 3)", "A IA e a qualidade da água", "Facilitador 3", f"{N['m4']}–{N['m4-actividade']}"],
        ["<span class=hora>11:00–11:20</span>", "Módulo 5 (18 + 2)", "A plataforma EYES TO EARTH, com demonstração ao vivo", "Facilitador 4", f"{N['m5']}–{N['m5-actividade']}"],
        ["<span class=hora>11:20–11:40</span>", "Intervalo (20)", "Matabicho; o Facilitador 6 confirma cada computador", "Logística + Facilitador 6", f"{N['intervalo']}"],
        ["<span class=hora>11:40–13:25</span>", "Prática em pares (105)", "Quatro temas, cada um com uma aula guiada e uma prática em que os pares escrevem o código: ensinar com exemplos e treinar e testar (classificação), a cor do rio e a maré (classificação), prever o caudal (regressão)", "Facilitador 5 + padrinhos", f"{N['pratica']}–{N['pratica-aula4']}"],
        ["<span class=hora>13:25–13:40</span>", "Apresentações (15)", "Cada par, 2 minutos: a regra do seu ano, o acerto no teste, o acerto com e sem a maré e o erro a 7 dias, uma lição", "Facilitador 5 + Moderadora", f"{N['apresentacoes']}–{N['resultados-modelos']}"],
        ["<span class=hora>13:40–14:00</span>", "Encerramento (20)", "Conclusões, perguntas, questionário OAD pós-workshop, avaliação, certificados, foto", "Moderadora", f"{N['licoes']}–{N['obrigado']}"],
    ], ["12%", "16%", "44%", "18%", "10%"])}
<p>Distribuição: 15 registo + 20 abertura + 155 de teoria (5 módulos e o quiz) + 20 intervalo + 105 prática + 15 apresentações + 20 encerramento = 360 minutos.</p>
<h3>Adaptação do plano OAD (4 horas) às 6 horas</h3>
<p>O plano OAD previa 15 min de abertura, 1 hora de teoria, 15 min de intervalo, 2 horas de prática e 30 min de encerramento. Com 6 horas e estudantes que nunca ouviram falar de Machine Learning, a teoria passa a 5 módulos (os quatro temas pedidos no plano, mais o Módulo 3 sobre como avaliar um modelo) e um quiz, com a teoria completa da aprendizagem supervisionada e não supervisionada e os gráficos clássicos de cada conceito; a ordem do plano mantém-se (abertura, teoria, intervalo, prática, encerramento); a prática mantém cerca de 2 horas (105 minutos + 15 de apresentações), em quatro temas, cada um com uma aula guiada e uma prática em que os pares escrevem o código, e treina a classificação e a regressão vistas na teoria, com os dados do projecto.</p>
<h3>Como manter os estudantes envolvidos</h3>
{lista(["<b>Uma missão do início ao fim:</b> no fim, cada par treinou os seus modelos e sabe dizer onde eles erram.",
        "<b>Nunca mais de 25 minutos de exposição seguida:</b> o Módulo 2, o mais longo, tem duas actividades em pares e é seguido do quiz.",
        "<b>Gráficos clássicos com dados reais:</b> a fronteira de classificação, a recta de regressão, os grupos do K-means e a curva do sobreajuste, quase sempre com píxeis e caudais reais do Incomáti.",
        "<b>Exemplos populares:</b> o telemóvel, o spam, o scanner de armas no aeroporto, o AlphaGo, e sempre imagens reais de Marracuene.",
        "<b>A teoria volta na prática:</b> os pares desenham com os seus dados os mesmos gráficos que viram de manhã (por exemplo, o sobreajuste na Aula 4).",
        "<b>A moderadora gere o ritmo:</b> anuncia cada bloco, avisa aos 5 minutos do fim e recolhe perguntas escritas."])}
""")
    a(f"""
<h2>3. Facilitadores e papéis</h2>
<p>Proposta para a equipa actual (9 pessoas): a moderadora, 7 facilitadores e a logística. Os perfis ajudam a escolher quem faz cada papel.</p>
{tabela(["Papel", "Perfil recomendado", "Quando", "O que faz"], FACILITADORES, ["15%", "22%", "17%", "46%"])}
{caixa('<p><b>Configuração mínima (se faltar gente):</b> moderadora + 5 facilitadores. O Facilitador 2 dá os Módulos 2 e 3; os Facilitadores 1, 3 e 4 dão os Módulos 1, 4 e 5 e são padrinhos dos Pares 1, 3 e 4; o Facilitador 2 é padrinho dos Pares 2 e 5; o Facilitador 5 conduz a prática e resolve os problemas técnicos; a logística faz o registo.</p>')}
{caixa('<p><b>Regra de ouro dos padrinhos:</b> o estudante é que escreve. O padrinho aponta, pergunta e explica, mas não toca no teclado.</p>', "#fff4e6", "#e8893a")}
<h2>4. Registo e abertura (08:00–08:35)</h2>
{tabela(["Hora", "Momento", "Como"], [
        ["08:00–08:15", "Registo", "Lista de presenças e crachás; formar os 5 pares (juntar quem já programou com quem nunca programou); cada par senta-se num computador com o Jupyter já aberto"],
        ["08:15–08:20", "Boas-vindas, objectivo e programa", f"A moderadora abre o dia: {sl('capa', 'dia-tarde')} (o objectivo e o programa da manhã e da tarde)"],
        ["08:20–08:25", "Questionário OAD pré-workshop", f"QR ou link no ecrã ({sl('inquerito')}); cópias em papel; ninguém avança sem submeter"],
        ["08:25–08:35", "Revisão do Workshop 1", f"{sl('revisao-luz', 'revisao-2024')}, para quem não esteve: o satélite, a regra MNDWI, a cheia de 2026 (20 244 ha) e as regras que falharam (2021, 2024); 8 minutos e 2 de perguntas"],
    ], ["13%", "22%", "65%"])}
""")
    a("<h2>5. Sessão teórica (08:35–11:20)</h2><p>Cada módulo: pergunta de abertura, conceitos com os gráficos clássicos, actividade em pares e dúvidas. As notas do orador de cada slide têm o texto a dizer, os tempos e as respostas.</p>")
    for i, m in enumerate(MODULOS):
        a(f"""<h3>{m['nome']} · {m['hora']} · {m['quem']} · slides {m['slides']}</h3>
<p><b>Pergunta de abertura:</b> <i>{m['abertura']}</i></p>
<p><b>Conceitos:</b></p>{lista(m['conceitos'])}
<p><b>Actividade:</b> {m['actividade']}</p>
<p><b>Pergunta de verificação:</b> {m['verificacao']}</p>""")
        if i == 1:
            a(f"""<h3>Quiz relâmpago · 09:55–10:05 · Moderadora · {sl('quiz', 'quiz-5')}</h3>
<p>Cada par com cartões A, B, C. Uma pergunta por slide: ler, contar até 5, todos levantam o cartão; a resposta e a explicação aparecem no clique seguinte. 1 ponto por resposta certa; o par vencedor é anunciado no encerramento.</p>
{tabela(["N.º", "Pergunta", "Resposta"], [[str(k + 1), q, r] for k, (q, r) in enumerate(QUIZ)], ["6%", "60%", "34%"])}""")
    a(f"""
<h2>6. Sessão prática (11:40–13:25) e apresentações (13:25–13:40)</h2>
<p>Em pares, no <b>Jupyter Notebook</b>, com a pasta <code>Workshop_2/2_pratica</code> copiada para cada computador (cerca de 40 MB de dados já preparados: a prática não precisa de Internet). O Facilitador 5 conduz no projector; cada par tem um padrinho.</p>
{tabela(["Hora", "Tema", "O que os pares fazem", "Tipo de modelo"], [
        ["11:40–11:50 · 11:50–12:05", "1 · Aula guiada + Prática", "Na aula, a árvore aprende a regra da água na cheia; na prática, cada par treina a árvore com os pontos do seu ano e escreve a tabela, X e y, fit e predict", "Classificação"],
        ["12:05–12:17 · 12:17–12:35", "2 · Aula guiada + Prática", "Na aula, treino e teste, o exame com o mapa oficial e a matriz de confusão; na prática, outra separação, as duas notas, o exame e uma só árvore", "Classificação"],
        ["12:35–12:43 · 12:43–12:55", "3 · Aula guiada + Prática", "Na aula, prever a água turva sem a maré; na prática, juntar a maré", "Classificação"],
        ["12:55–13:05 · 13:05–13:20", "4 · Aula guiada + Prática", "Na aula, o caudal a 3 dias e o sobreajuste; na prática, o caudal a 7 dias e sem o caudal de hoje", "Regressão"],
        ["13:20–13:25", "—", "Guardar e preparar a apresentação", "—"],
        ["13:25–13:40", "Apresentações", f"Cada par, 2 min ({sl('apresentacoes', 'resultados-modelos')}); depois os resultados de referência", "—"],
    ], ["17%", "17%", "50%", "16%"])}
<p><b>Aula guiada e prática:</b> na aula guiada, o condutor mostra no projector e os pares correm as mesmas células. Na prática, os pares escrevem o código sozinhos: cada passo tem uma pista e uma célula de verificação («Certo!», ou «Ainda não» com uma pista). As versões resolvidas, com notas para os facilitadores, os modelos treinados e as separações de treino e teste, estão em <code>0_facilitadores/aulas_resolvidas</code>.</p>
<p><b>Ano de cada par na Prática 1:</b> {", ".join(f"{p_} {a_}" for p_, a_ in ANO_POR_PAR.items())}.</p>
<p><b>O que a turma deve descobrir:</b> cada ano tem a sua regra da água (em 2021, com água barrenta, o limite do SWIR é {fmt(ar['p1_anos']['2021']['limite'], 2)}; em 2022 e 2024 a árvore prefere a banda vermelha); a nota do treino engana e a do teste diz a verdade; sem a maré, o modelo da água barrenta não aprende nada útil, e com ela acerta muito mais ({fmt(100 * ar['a3_nota_sem_mare'], 1)} % contra {fmt(100 * ar['p3_nota_com_mare'], 1)} %); quanto mais longe a previsão, maior o erro ({fmt(ar['a4_erro_teste'], 1)} m³/s a 3 dias, {fmt(ar['p4_erro_7'], 1)} a 7).</p>
<p><b>Plano B se um computador falhar:</b> o par junta-se a outro par e trabalham os quatro; o Facilitador 5 tem a prática completa no seu portátil e pode projectar os resultados.</p>
<h2>7. Encerramento (13:40–14:00)</h2>
{tabela(["Hora", "Momento"], [
        ["13:40–13:45", f"As 4 conclusões do dia ({sl('licoes')}); o par vencedor do quiz; perguntas abertas e perguntas escritas"],
        ["13:45–13:52", f"Questionário OAD pós-workshop ({sl('inquerito-final')}): o mesmo da manhã"],
        ["13:52–13:56", "Formulário curto de avaliação do workshop"],
        ["13:56–14:00", "Certificados de participação (chamar cada estudante pelo nome) e foto de grupo"],
    ], ["15%", "85%"])}
""")
    a(f"""
<h2>8. Correspondência com o plano aprovado</h2>
<p>Cada ponto do plano OAD e do quadro de conteúdos, e onde está no material.</p>
{tabela(["Componente", "Pedido no plano", "Onde está"], [
        ["Abertura", "Boas-vindas, breve revisão do Workshop 1, questionário inicial OAD", f"Slides 1 a {N['revisao-2024']} (08:15–08:35)"],
        ["Aula teórica", "Conceitos de IA e ML; regra contra exemplos; exemplos do dia-a-dia (spam, voz)", f"Módulo 1, {sl('m1-regras', 'm1-aprende')}; actividade no {sl('m1-actividade')}"],
        ["", "Gancho: as regras falharam com água barrenta (2021) e muito escura (2022, 2024)", f"{sl('revisao-2021', 'revisao-2024')} e {sl('m1-gancho')} (corrigido: em 2022 e 2024 falhou o MNDWI)"],
        ["", "Como um computador aprende a reconhecer água: rótulos e características; treino e teste", f"Módulo 2, {sl('m2-modelo', 'm2-tipos')}; Módulo 3, {sl('m3-fluxo', 'm3-rotulos')}"],
        ["", "(pedido da equipa) Aprendizagem supervisionada e não supervisionada, classificação, regressão, agrupamento, com os gráficos da teoria", f"Módulo 2, {sl('m2-supervisionada', 'm2-actividade-tipos')}; Módulo 3, {sl('m3-ajuste')} e {N['m3-complexidade']}"],
        ["", "Random Forest como muitas árvores a votar", f"{sl('m2-algoritmos', 'm2-floresta-porque')}; actividade nos {sl('m2-actividade', 'm2-actividade-votar')}"],
        ["", "Testar com dados que o modelo nunca viu; métricas simples (IoU, F1, Kappa, ROC-AUC)", f"Módulo 3, {sl('m3-divisao', 'm3-futuro')} e {sl('m3-matriz', 'm3-notas-regressao')}"],
        ["", "(pedido da equipa) Configurar os modelos: hiperparâmetros", f"{sl('m3-hiperparametros')}; na prática: o número de árvores (Aula 2), o K (Aula 3) e a profundidade (Aula 4)"],
        ["", "Regra de ouro: nunca validar com rótulos gerados pelo próprio modelo", f"{sl('m3-regra-de-ouro')}; Tema 2 da prática (aula e Prática 2)"],
        ["", "Turbidez, sedimentos, clorofila-a, plantas flutuantes, temperatura", f"Módulo 4, {sl('m4-o-que-ve')} e {N['m4-cor']}"],
        ["", "Os 9 troços; anomalias e tendências de 20 anos", f"{sl('m4-trocos')} e {N['m4-anomalias']} (tendências: ainda sem confirmação)"],
        ["", "O que não mede: pH, oxigénio, nutrientes, metais, bactérias; nunca \"água própria para beber\"", f"{sl('m4-nao-mede')}"],
        ["", "Do dado ao alerta; gatilhos (chuva anómala e caudal)", f"Módulo 5, {sl('m5-dado-alerta')} e {N['m5-gatilhos']}"],
        ["", "Páginas Quantidade, Qualidade e Alertas; os quatro níveis", f"{sl('m5-niveis', 'm5-demo')}; demonstração ao vivo"],
        ["", "Os alertas complementam os avisos oficiais", f"{sl('m5-oficiais')}"],
        ["Pausa", "Intervalo", f"11:20–11:40, {sl('intervalo')}"],
        ["Aula prática", "Identificação e classificação de exemplos de água e não água", "Tema 1: a aula guiada (exemplos, rótulos e características) e a Prática 1 (o ano de cada par)"],
        ["", "Treino de um Random Forest em Python", "Tema 2: a floresta aleatória, com a separação em treino e teste (aula e Prática 2)"],
        ["", "Análise dos resultados: acertos e erros", "Tema 2: o exame com o mapa oficial e a matriz de confusão; Prática 1: a regra de cada ano"],
        ["", "(pedido da equipa) Treinar os outros modelos da teoria", "Temas 3 (a qualidade da água e a maré) e 4 (regressão do caudal), cada um com aula e prática"],
        ["", "(pedido da equipa) Prática em que os alunos escrevem o código, e versões resolvidas", "Uma prática por tema, com verificação em cada passo; aulas e práticas resolvidas, modelos treinados e separações em 0_facilitadores/aulas_resolvidas"],
        ["", "Exploração da plataforma: risco de cheia, qualidade da água, alertas", f"Demonstração ao vivo no Módulo 5 ({sl('m5-demo')})"],
        ["Encerramento", "Perguntas e respostas, questionário final OAD, avaliação, certificados", f"{sl('licoes', 'obrigado')}; certificados em 0_facilitadores/certificados"],
    ], ["15%", "50%", "35%"])}
""")
    a(f"""
<h2>9. Preparação e materiais</h2>
<p><b>Materiais:</b> projector e portátil do apresentador (com os slides também em PDF e PPTX); 5 computadores (um por par) com carregador e o Jupyter Notebook instalado; 1 ou 2 computadores de reserva; extensões eléctricas; pen drive com a pasta Workshop_2 e o instalador do Anaconda; Internet só para a demonstração da plataforma; cartões A/B/C para o quiz (5 conjuntos); QR dos questionários OAD e da avaliação; lista de presenças e crachás; certificados impressos; matabicho.</p>
{tabela(["Quando", "O quê", "Quem"], [
        ["Qui 12/11", "Decidir quem é o Facilitador 1 a 7 e enviar este plano", "Moderadora + líder técnico"],
        ["Sex 13/11", "Partilhar os slides com a equipa (menu Partilhar do artefacto); cada facilitador lê os seus slides e as notas", "Líder técnico"],
        ["Seg 16/11", "Descarregar o Anaconda uma só vez (cerca de 1 GB) e copiá-lo para o pen drive; instalar em cada computador; copiar a pasta Workshop_2 SEM 0_facilitadores; correr 0_verificar_computador.ipynb em cada um", "Facilitador 6"],
        ["Qua 18/11", f"Pôr nos slides os QR dos questionários ({sl('inquerito')} e {N['inquerito-final']}) e o contacto ({sl('obrigado')}); o endereço da plataforma já está nos slides", "Moderadora + Facilitador 4"],
        ["Qui 19/11", "Ensaio geral cronometrado nos computadores do local: a teoria em ritmo rápido e as 4 aulas e 4 práticas, comparando com as versões resolvidas", "Toda a equipa"],
        ["Sex 20/11", "Imprimir cartões, presenças e certificados (nomes confirmados); exportar os slides em PDF e PPTX; confirmar a rede para a demonstração da plataforma", "Logística"],
        ["Sáb 21/11, 07:30", "Ligar os computadores e abrir o Jupyter na pasta 2_pratica; abrir ete-platform.streamlit.app no portátil do projector (o boletim do dia já correu sozinho)", "Facilitadores 4, 5 e 6"],
    ], ["15%", "62%", "23%"])}
<h2>10. Notas e correcções ao plano</h2>
{lista(["<b>NDWI e MNDWI:</b> o quadro de conteúdos diz que o NDWI falhou com água muito escura em 2022 e 2024. Nos nossos dados, nesses anos falhou o MNDWI (2024: 0% do rio; 2022: 66%) e o NDWI funcionou (91% e 93%); em 2021, com água barrenta, falhou o NDWI (51%). Os slides já dizem isto.",
        "<b>Tendências de 20 anos:</b> os satélites mudaram (Landsat 5 e 7, Landsat 8 e 9, Sentinel-2) e ainda não há uma tendência de 20 anos confirmada. O slide das anomalias diz isto.",
        "<b>Clorofila-a:</b> no Incomáti, o índice de clorofila (NDCI) sobe com a lama; a plataforma não afirma que há algas sem confirmação no terreno.",
        "<b>O exame tinha um erro:</b> as amostras \"não água\" do Copernicus EMS caíam em cima do leito normal do rio (o EMS só mapeia a água da cheia). Corrigiu-se com o arquivo JRC (4 419 píxeis). Sem a correcção, 2 883 dos 2 901 falsos alarmes do modelo estavam no rio. Vale a pena verificar se o mesmo afecta a validação do Modelo B do projecto (IoU 0,90).",
        "<b>Dados inventados:</b> três gráficos da teoria usam dados inventados, porque o conceito o pede (horas de estudo e nota; subajuste e sobreajuste; a curva de complexidade). Os slides dizem-no na legenda; todos os outros usam dados reais do Incomáti.",
        "<b>A plataforma:</b> está publicada em ete-platform.streamlit.app; o boletim corre sozinho todas as manhãs nos servidores do GitHub. Se o boletim tiver mais de 36 horas, o Início mostra \"previsão indisponível\".",
        "<b>A cheia de 2021:</b> as notas dos slides ligam a cheia de Janeiro de 2021 às chuvas do ciclone Eloise; confirmar antes de o dizer."])}
""")
    return pagina("Plano do Workshop 2", "".join(p))


# ---------------------------------------------------------------- manual dos facilitadores (prática)
def manual(ar) -> str:
    """A prática: 4 temas, cada um com uma aula guiada e uma prática em que os pares escrevem o código.
    Os números vêm de 0_facilitadores/aulas_resolvidas/resultados_de_referencia.json."""
    prof = ar["a4_profundidades"]
    melhor = str(ar["a4_melhor_profundidade"])
    p1 = ar["p1_anos"]
    p = []
    a = p.append
    a(f"""
<p class="pequeno">PROJECTO EYES TO EARTH (ETE) · WORKSHOP DE ESTUDANTES 2</p>
<h1>Manual dos facilitadores<br>A prática: aulas guiadas e práticas em que os pares escrevem o código</h1>
<p><b>Sábado, 21 de Novembro de 2026 · 11:40–13:40 · 5 pares · Jupyter Notebook</b></p>
{caixa('<p><b>Para quem:</b> o Facilitador 5 (condutor), os padrinhos dos pares e o Facilitador 6 (apoio técnico). O plano do dia inteiro está no <i>Plano do Workshop 2</i>. As aulas e as práticas resolvidas, já corridas e com notas para os facilitadores (o que dizer, os resultados esperados, as respostas), estão em <code>0_facilitadores/aulas_resolvidas/</code>.</p>')}
<h2>1. A prática numa página</h2>
<p><b>A missão:</b> treinar, com dados reais do Incomáti, os modelos vistos de manhã (classificação e regressão), na água da cheia, na água barrenta e no caudal, avaliá-los com dados que nunca viram e dizer onde erram. Há 4 temas. Em cada um, primeiro uma <b>aula guiada</b> (o condutor mostra no projector e os pares acompanham) e depois uma <b>prática</b>, em que os pares <b>escrevem o código sozinhos</b> num caso novo.</p>
{tabela(["Tema", "Aula guiada (projector)", "Prática (sozinhos)", "Resultado de referência da prática"], [
        ["1 · Ensinar a máquina com exemplos", "11:40–11:50 · exemplos, rótulos e a árvore que aprende a regra", "11:50–12:05 · a água no ano de cada par: a tabela, X e y, fit, predict", "A regra muda de ano para ano (tabela da secção 5)"],
        ["2 · Treinar e testar", "12:05–12:17 · treino e teste, o exame, a matriz de confusão", "12:17–12:35 · outra separação; as duas notas; o exame; uma só árvore", f"Teste {fmt(100 * ar['p2_teste'], 1)} %; mapa oficial {fmt(100 * ar['p2_ems'], 1)} %; {fmt(ar['p2_falsos'])} falsos alarmes"],
        ["3 · A cor do rio e a maré", "12:35–12:43 · prever a água turva sem a maré", "12:43–12:55 · juntar a maré ao modelo", f"de {fmt(100 * ar['a3_nota_sem_mare'], 1)} % para {fmt(100 * ar['p3_nota_com_mare'], 1)} % com a maré"],
        ["4 · Prever o caudal", "12:55–13:05 · a 3 dias; o sobreajuste", "13:05–13:20 · a 7 dias, e sem o caudal de hoje", f"Erro a 7 dias {fmt(ar['p4_erro_7'], 1)} m³/s; só com a chuva {fmt(ar['p4_so_chuva_7'], 1)}"],
        ["Preparar a apresentação", "—", "13:20–13:25 · guardar e escolher os números (o último quadro da Prática 4)", "—"],
    ], ["20%", "27%", "29%", "24%"])}
<p>Todos os pares usam os pontos marcados pela equipa, por isso os números de cada par devem ser iguais aos de referência. Só a Prática 1 muda de par para par: cada par treina a árvore com os pontos de um ano diferente ({", ".join(f"{p_} {a_}" for p_, a_ in ANO_POR_PAR.items())}).</p>
<h2>2. A pasta Workshop_2</h2>
{tabela(["Pasta ou ficheiro", "Para quem", "O que é"], [
        ["<b>0_facilitadores/</b>", "Só a equipa: não copiar para os computadores dos alunos", "Plano, este manual, as aulas e práticas resolvidas, os modelos treinados, as imagens dos slides e os certificados"],
        ["<b>0_facilitadores/aulas_resolvidas/</b>", "Facilitadores", "As 4 aulas e as 4 práticas resolvidas e já corridas, com notas; <code>modelos_treinados/</code>; <code>separacoes/</code>; <code>resultados_de_referencia.json</code>"],
        ["<b>0_facilitadores/arquivo_pratica_antiga/</b>", "Só a equipa", "A prática antiga (Partes A a H, scripts, nível avançado), guardada mas fora das aulas"],
        ["<b>1_preparacao_python/</b>", "Alunos (opcional)", "Os 3 notebooks de introdução ao Python do Workshop 1"],
        ["<b>2_pratica/0_verificar_computador.ipynb</b>", "Facilitador 6", "Verifica o Python, as bibliotecas, os dados, o ferramentas.py e um treino de teste: tem de dizer «PRONTO»"],
        ["<b>2_pratica/1_Aula_… a 4_Aula_…</b>", "Pares, com o condutor", "As 4 aulas guiadas"],
        ["<b>2_pratica/1_Pratica_… a 4_Pratica_…</b>", "Pares, sozinhos", "As 4 práticas, com o código por escrever"],
        ["<b>2_pratica/ferramentas.py</b>", "Os notebooks", "As funções das aulas e as verificações das práticas. Os alunos não precisam de o abrir"],
        ["<b>2_pratica/dados/</b>", "Os notebooks", "A imagem da cheia de 2026 e as dos 5 anos, o mapa oficial da cheia, os pontos da equipa, 10 anos da cor do rio e da maré, e 20 anos de caudal e chuva (cerca de 38 MB). O dados/LEIA-ME.md explica cada ficheiro e como cada aula separa o treino do teste"],
        ["<b>2_pratica/requirements.txt</b>", "Facilitador 6", "As bibliotecas, para instalar sem o Anaconda: pip install -r requirements.txt"],
        ["<b>3_teste_do_aluno/teste_ia.ipynb</b>", "Alunos", "16 perguntas com correcção automática"],
    ], ["34%", "22%", "44%"])}
<h3>Os modelos treinados e as separações</h3>
<p>As aulas e as práticas resolvidas guardam, ao lado delas, os modelos treinados e os dados exactos com que foram treinados e testados. Para abrir um modelo noutro notebook: <code>import joblib; modelo = joblib.load("modelos_treinados/aula2_floresta_100_arvores.joblib")</code>.</p>
{tabela(["Ficheiro", "O que é"], [
        ["aula1_arvore_de_decisao.joblib", f"A árvore da Aula 1 (5 bandas, profundidade 2), treinada com os {ar['a1_n']} exemplos da cheia"],
        ["aula2_floresta_100_arvores.joblib", f"A floresta da Aula 2, treinada só com os {ar['a2_n_treino']} exemplos de treino"],
        ["aula3_floresta_sem_mare.joblib", f"A floresta da Aula 3 (turva ou não), com o caudal, a chuva e o mês, treinada com {fmt(ar['p3_n_treino'])} manhãs de 2017 a 2022"],
        ["aula4_regressao_linear.joblib e aula4_arvore_profundidade_" + melhor + ".joblib", "A regressão do caudal a 3 dias e a melhor árvore de regressão"],
        ["pratica1_arvore_2021.joblib", "A árvore da Prática 1, com os pontos de 2021 (o ano da versão resolvida)"],
        ["pratica2_floresta_100_arvores.joblib", f"A floresta da Prática 2 (o teste são os primeiros 5 + 5 pontos), com {ar['p2_n_treino']} exemplos de treino"],
        ["pratica3_floresta_com_mare.joblib, pratica3_floresta_troco_medio.joblib", "As florestas da Prática 3, com a maré: nos três troços e só no troço médio"],
        ["pratica4_regressao_7_dias.joblib", "A regressão do caudal a 7 dias"],
        ["separacoes/", "Os exemplos, os pontos e os píxeis de treino e de teste, e as separações no tempo, em CSV"],
    ], ["42%", "58%"])}
""")
    a(f"""
<h2>3. Como funcionam as aulas e as práticas</h2>
{lista(["<b>Abrir sempre a partir da pasta</b> <code>2_pratica</code> (Anaconda Navigator → Jupyter Notebook, ou <code>jupyter notebook</code> num terminal nessa pasta). Os notebooks encontram os dados e o ferramentas.py sozinhos.",
        "<b>Aula guiada:</b> o condutor mostra no projector, passo a passo; os pares correm as mesmas células ao mesmo tempo (Shift + Enter, por ordem). Não há nada para escrever. Começa com uma tabela de palavras novas: ler em voz alta.",
        "<b>Prática:</b> um caso novo, com os mesmos passos da aula. Em cada passo há uma célula com uma <b>pista</b> (linhas que começam por #). Os pares escrevem o código por baixo (podem copiar a pista, tirar o # e trocar os ...), correm a célula, e depois correm a célula de verificação: «Certo!», ou «Ainda não» com uma pista que diz o que escrever.",
        "<b>Para pensar:</b> no fim de cada prática, 2 a 4 perguntas de escolha, também corrigidas (a letra entre aspas: \"a\").",
        "<b>Os números saem à portuguesa</b> (98,2 %, 20 300 hectares), mas em Python escrevem-se com ponto (0.05).",
        "<b>As versões resolvidas</b> têm uma «Nota para o facilitador» a seguir aos passos, com o que dizer e os resultados esperados; nas práticas, o código está escrito e as perguntas respondidas.",
        "<b>Tabela de erros comuns</b> no fim de cada notebook."])}
<h2>4. Minuto a minuto</h2>
{tabela(["Hora", "Condutor (Facilitador 5)", "Padrinhos e apoio técnico"], [
        ["11:40–11:50", f"{sl('pratica', 'pratica-aula1')}: como trabalhar; Aula 1 no projector", "Cada padrinho junto do seu par; o Facilitador 6 confirma que todos abriram a Aula 1"],
        ["11:50–12:05", f"{sl('pratica-anos')}: o ano de cada par; Prática 1", "O par escreve; o padrinho aponta para o passo igual da Aula 1"],
        ["12:05–12:17", f"{sl('pratica-aula2')}: Aula 2 no projector", "Perguntar: que nota poríamos num relatório?"],
        ["12:17–12:35", "Prática 2", "Ver se a separação está certa (o teste são os primeiros 5 + 5)"],
        ["12:35–12:43", f"{sl('pratica-aula3')}: Aula 3 no projector", "Perguntar: quem dá o nome aos grupos?"],
        ["12:43–12:55", "Prática 3", "Perguntar: porque é que a maré conta mais perto do mar?"],
        ["12:55–13:05", f"{sl('pratica-aula4')}: Aula 4 no projector; a curva do sobreajuste", "Perguntar: a partir de que profundidade a árvore decora?"],
        ["13:05–13:20", "Prática 4", "Ajudar a escrever o shift(-7) e a separação no tempo"],
        ["13:20–13:25", "Guardar (Ctrl + S) e preparar a apresentação", "Ajudar cada par a escolher os seus números"],
        ["13:25–13:40", f"Apresentações ({sl('apresentacoes')}), depois {sl('resultados', 'resultados-modelos')}", "O Facilitador 6 escreve no quadro a regra de cada ano"],
    ], ["13%", "50%", "37%"])}
""")
    linhas_p1 = [[p_, str(a_), p1[str(a_)]["dia"], p1[str(a_)]["satelite"], str(p1[str(a_)]["exemplos"]),
                  f"{p1[str(a_)]['banda'].upper()} ≤ {fmt(p1[str(a_)]['limite'], 3)}", fmt(p1[str(a_)]["hectares"]) + " ha"]
                 for p_, a_ in ANO_POR_PAR.items()]
    a(f"""
<h2>5. Resultados de referência e respostas</h2>
<h3>Tema 1 · Ensinar a máquina com exemplos</h3>
{tabela(["Aula guiada", "Resultado esperado"], [
        ["Passo 3 · um píxel de água e um de terra", f"SWIR da água {fmt(ar['a1_swir_agua'], 3)}; da terra {fmt(ar['a1_swir_terra'], 3)}"],
        ["Passo 4 · os exemplos", f"{ar['a1_n']} exemplos: {ar['a1_n_agua']} de água e {ar['a1_n'] - ar['a1_n_agua']} de não água"],
        ["Passo 5 · a nossa regra (SWIR menor do que 0,10)", f"acerta {fmt(100 * ar['a1_regra_010'], 1)} %"],
        ["Passo 6 · a árvore de decisão", f"«SWIR ≤ {fmt(ar['a1_limiar_arvore'], 2)} é água»; acerta {fmt(100 * ar['a1_acerto_arvore'], 1)} % (nos mesmos exemplos do treino)"],
        ["Passo 7 · o mapa", f"cerca de {fmt(ar['a1_ha_cheia'])} hectares de água (o distrito tem cerca de 70 600)"],
    ], ["40%", "60%"])}
<p><b>Prática 1</b> (cada par com o seu ano). Respostas das perguntas: a (supervisionada) e b (a regra muda com a água).</p>
{tabela(["Par", "Ano", "Data", "Satélite", "Exemplos", "A regra aprendida", "Água no mapa"], linhas_p1,
        ["9%", "8%", "15%", "14%", "11%", "24%", "19%"])}
<h3>Tema 2 · Treinar e testar</h3>
{tabela(["Passo", "Aula guiada (teste = últimos 5 + 5)", "Prática 2 (teste = primeiros 5 + 5)"], [
        ["Exemplos de treino e de teste", f"{ar['a2_n_treino']} e {ar['a2_n_teste']}", f"{ar['p2_n_treino']} e {ar['p2_n_teste']}"],
        ["Acerto no treino e no teste", f"{fmt(100 * ar['a2_treino'], 1)} % e {fmt(100 * ar['a2_teste'], 1)} %", f"{fmt(100 * ar['p2_treino'], 1)} % e {fmt(100 * ar['p2_teste'], 1)} %"],
        ["Exame com o mapa oficial", f"{fmt(100 * ar['a2_ems'], 1)} %", f"{fmt(100 * ar['p2_ems'], 1)} %"],
        ["Falsos alarmes / água perdida", f"{fmt(ar['a2_falsos'])} / {fmt(ar['a2_perdida'])}", f"{fmt(ar['p2_falsos'])} / {fmt(ar['p2_perdida'])}"],
        ["Uma só árvore, no teste", f"{fmt(100 * ar['a2_1arvore_teste'], 1)} %", f"{fmt(100 * ar['p2_1arvore_teste'], 1)} %"],
    ], ["34%", "33%", "33%"])}
<p>Respostas das perguntas da Prática 2: b (o modelo já viu o treino), b (com uma só árvore o teste desce), b (a água perdida é o erro mais perigoso).</p>
<h3>Tema 3 · A cor do rio e a maré</h3>
{tabela(["Passo", "Resultado esperado"], [
        ["A tabela", f"{fmt(ar['a3_n'])} manhãs × troço (2017 a 2026, Sentinel-2); {fmt(100 * ar['a3_turva'], 1)} % turvas"],
        ["Separação no tempo", f"{fmt(ar['p3_n_treino'])} manhãs de treino (2017 a 2022) e {fmt(ar['p3_n_teste'])} de teste (2023 a 2026)"],
        ["Aula · floresta sem a maré", f"{fmt(100 * ar['a3_nota_sem_mare'], 1)} % no teste; dizer sempre «turva»: {fmt(100 * ar['a3_sempre_turva'], 1)} %"],
        ["Aula · água turva por maré", f"maré baixa {fmt(100 * ar['a3_turva_mare']['maré baixa'], 0)} %, média {fmt(100 * ar['a3_turva_mare']['maré média'], 0)} %, alta {fmt(100 * ar['a3_turva_mare']['maré alta'], 0)} %"],
        ["Prática · floresta com a maré", f"{fmt(100 * ar['p3_nota_com_mare'], 1)} % no teste"],
        ["Prática · longe do mar", f"troço médio {fmt(100 * ar['p3_nota_medio'], 1)} % (sempre «turva»: {fmt(100 * ar['p3_sempre_medio'], 1)} %); foz {fmt(100 * ar['p3_nota_foz'], 1)} %"],
    ], ["34%", "66%"])}
<p>É a descoberta do projecto: o modelo da água barrenta só funcionou quando lhe demos a maré. Na maré alta entra água do mar, mais limpa; na maré baixa sai a água barrenta do rio. Respostas da Prática 3: a, a, a.</p>
<h3>Tema 4 · Prever o caudal</h3>
{tabela(["Passo", "Resultado esperado"], [
        ["Aula · separação no tempo", f"{fmt(ar['a4_n_treino'])} dias de treino (2006 a 2018) e {fmt(ar['a4_n_teste'])} de teste (2019 a 2026)"],
        ["Aula · regressão linear a 3 dias", f"erro médio no treino {fmt(ar['a4_erro_treino'], 1)} e no teste {fmt(ar['a4_erro_teste'], 1)} m³/s; «fica igual a hoje» {fmt(ar['a4_igual_a_hoje'], 1)}"],
        ["Aula · árvore de regressão (treino / teste)", "; ".join(f"profundidade {k}: {fmt(v['treino'], 1)} / {fmt(v['teste'], 1)}" for k, v in prof.items()) + f". A melhor é {melhor}"],
        ["Prática 4 · regressão a 7 dias", f"erro médio no teste {fmt(ar['p4_erro_7'], 1)} m³/s («fica igual a hoje»: {fmt(ar['p4_igual_7'], 1)})"],
        ["Prática 4 · só com a chuva", f"{fmt(ar['p4_so_chuva_7'], 1)} m³/s: o caudal de hoje é a pista mais importante"],
    ], ["34%", "66%"])}
<p>Respostas das perguntas da Prática 4: a, a, a, a.</p>
""")
    a(f"""
<h2>6. Como ajudar um par na prática</h2>
{tabela(["Situação", "O que o padrinho faz"], [
        ["«Ainda não: falta criar ...»", "O par ainda não escreveu (ou não correu) a célula de cima: escrever o código e correr com Shift + Enter"],
        ["«Ainda não» com uma pista", "Ler a pista com o par e comparar com o passo igual da aula guiada; não escrever por eles"],
        ["Erro vermelho", "Ler a última linha em voz alta; quase sempre é um parêntese, uma aspa ou um # que ficou no início da linha"],
        ["Ficaram três pontos (...)", "Trocar os ... pelo nome certo (por exemplo img, X, y, treino)"],
        ["Escreveram 0,05 em vez de 0.05", "Em Python, as décimas escrevem-se com ponto"],
        ["O par acabou cedo", "Voltar a uma prática por acabar; experimentar outro K na Prática 3; o teste do aluno"],
        ["Problema no computador ou no Jupyter", "Chamar o Facilitador 6 com a mão no ar; não parar a aula"],
    ], ["35%", "65%"])}
<h3>Se o tempo apertar</h3>
{tabela(["Às...", "Se", "Fazer"], [
        ["12:05", "Prática 1 por acabar", "Começar a Aula 2 na mesma; a Prática 1 acaba-se depois (é a que dá a regra para a apresentação)"],
        ["12:35", "Prática 2 por acabar", "Passar à Aula 3; os números da Prática 2 mostram-se no projector com a versão resolvida"],
        ["12:55", "Prática 3 por acabar", "Passar à Aula 4"],
        ["13:20", "Prática 4 por acabar", "Guardar; os resultados mostram-se no projector com a versão resolvida"],
    ], ["10%", "30%", "60%"])}
<h2>7. Problemas frequentes</h2>
{tabela(["Problema", "Solução"], [
        ["FileNotFoundError: Não encontrei ...", "O Jupyter foi aberto noutra pasta: abrir o notebook a partir de Workshop_2/2_pratica"],
        ["ModuleNotFoundError: No module named 'ferramentas'", "O notebook não está na pasta 2_pratica, ao lado do ferramentas.py: abri-lo a partir dessa pasta"],
        ["ModuleNotFoundError: No module named 'sklearn'", "Falta uma biblioteca: o Jupyter não foi aberto pelo Anaconda. Abri-lo pelo Anaconda Navigator; ou, com Internet, correr numa célula %pip install -r requirements.txt e reiniciar o kernel"],
        ["NameError", "Uma célula ficou por correr: correr por ordem, a partir do Passo 1"],
        ["Kernel died / Dead kernel", "O Python parou: Kernel → Restart Kernel e correr outra vez por ordem; fechar outros programas"],
        ["O notebook não guarda", "Ctrl + S; confirmar que a pasta não é só de leitura (copiar a pasta para o computador)"],
        ["Computador lento", "Fechar outros programas; os mapas e as florestas levam alguns segundos cada"],
    ], ["40%", "60%"])}
""")
    a(f"""
<h2>8. Glossário</h2>
{tabela(["Palavra", "Explicação simples"], [
        ["Exemplo", "Um caso que mostramos ao computador (aqui, um píxel da imagem, ou um dia do rio)"],
        ["Característica", "O que se mede em cada exemplo (as 5 bandas do satélite; o caudal e a chuva)"],
        ["Rótulo", "A resposta certa de cada exemplo (1 = água, 0 = não água)"],
        ["Modelo", "A regra que o computador aprende com os exemplos"],
        ["Treinar (fit) / prever (predict)", "Dar os exemplos ao modelo para ele aprender / usar o modelo num caso novo"],
        ["Treino / teste", "Os exemplos com que o modelo aprende / os exemplos guardados à parte para o avaliar"],
        ["Árvore de decisão", "Perguntas de sim ou não, escolhidas pelo computador"],
        ["Floresta aleatória (Random Forest)", "Muitas árvores, cada uma com parte dos exemplos, que votam"],
        ["Matriz de confusão", "Água certa, água perdida, falso alarme e terra certa, num quadro 2 × 2"],
        ["Turbidez (NDTI)", "A água barrenta; o satélite mede-a pela cor (mais vermelho, mais barrenta)"],
        ["Maré", "O mar sobe e desce duas vezes por dia; na maré alta entra água do mar, mais limpa"],
        ["Regressão", "Prever um número (o caudal), em vez de uma categoria"],
        ["Erro médio", "Quanto a previsão falha, em média, nas unidades do alvo (m³/s)"],
        ["Sobreajuste", "O modelo decora o treino e falha nos dados novos"],
        ["Mapa oficial da cheia (Copernicus EMS)", "O mapa da água a 24/01/2026, feito por um serviço europeu: o grande exame do Tema 2"],
    ], ["32%", "68%"])}
<h2>9. Cartão de bolso</h2>
{tabela(["Hora", "O quê", "Lembrete"], [
        ["11:40", "Aula 1", "Ler as palavras novas; a regra feita à mão contra a árvore"],
        ["11:50", "Prática 1", f"Anos: {', '.join(f'{p_} {a_}' for p_, a_ in ANO_POR_PAR.items())}; anotar a regra"],
        ["12:05", "Aula 2", "Nunca avaliar com o treino; o exame oficial; a matriz de confusão"],
        ["12:17", "Prática 2", "O teste são os primeiros 5 + 5; uma só árvore"],
        ["12:35", "Aula 3", "A água turva: sem a maré, o modelo não aprende"],
        ["12:43", "Prática 3", "Com a maré, o acerto sobe; longe do mar, menos"],
        ["12:55", "Aula 4", "O exame é o futuro; o erro médio; o sobreajuste"],
        ["13:05", "Prática 4", "shift(-7); sem o caudal de hoje o erro sobe"],
        ["13:20", "Guardar", "Ctrl + S; escolher os números para a apresentação"],
        ["13:25", "Apresentações", "2 minutos por par; a regra de cada ano no quadro"],
    ], ["12%", "20%", "68%"])}
""")
    return pagina("Manual dos facilitadores · Workshop 2", "".join(p))


SLIDES_MD = f"""# Slides do Workshop 2

**Apresentação ({len(ORDEM_SLIDES)} slides, com notas do orador):** {SLIDES_URL}

**Módulo 2 refeito, num deck à parte (19 slides, 09:05–09:55, Facilitador 2):** https://claude.ai/artifact/5yoVWyumH2qVSGTKEqnBuu
Uma versão leve, para quem nunca ouviu falar de modelos de IA: aprender com exemplos (cães e gatos, burlas no WhatsApp),
treinar e prever, as três formas de aprender, a árvore e a floresta com dois jogos, a regressão, e quatro ligações ao
projecto (a imagem de satélite, o mapa da água da Aula 1, o caudal do rio e as três perguntas da plataforma). Gerado por
`scripts/build_workshop2_modulo2.py`. Ainda não substitui os slides do Módulo 2 do deck principal.

O artefacto é privado: só abre para quem o criou. Para a equipa o ver, abrir o link e usar o menu **Partilhar**.

## Como usar

- **Apresentar:** abrir o link e escolher o modo de apresentação. As notas do orador (o texto a dizer, as respostas das
  actividades e os tempos) aparecem na vista do apresentador.
- **Sem Internet no dia:** exportar antes em PDF e em PowerPoint (menu Partilhar, Exportar) e levar no pen drive.
- **Uma ideia por slide:** cada slide tem pouco texto (cerca de 60 palavras em média) e letra grande; o que o
  facilitador diz está nas notas. No quiz, cada pergunta tem o seu slide e a resposta aparece no clique seguinte (o mesmo
  na pergunta de verificação do Módulo 3).
- **Antes do workshop, trocar:** os QR dos questionários OAD (slides {N['inquerito']} e {N['inquerito-final']}) e o contacto
  do projecto (slide {N['obrigado']}). O endereço da plataforma (ete-platform.streamlit.app) já está nos slides.
- **Estilo:** fundo branco e visual académico, sem azul: títulos a preto, linha vermelho-escuro (#A51C30) por baixo do
  título, destaques a vermelho-escuro, cabeçalhos das tabelas a preto, rodapé com a secção e o número do slide, figuras e
  tabelas numeradas com a fonte dos dados. O azul só aparece onde representa a água (mapas e gráficos de píxeis).
- **Letra:** os títulos usam a Archivo Black, a versão web da Arial Black (o leitor de slides só aceita fontes web ou
  básicas e trocava a Arial Black por Arial normal); o texto usa Arial. No PowerPoint exportado, para pôr a Arial Black:
  separador Base, Substituir, Substituir Tipos de Letra, de Archivo Black para Arial Black.

## Secções

| Slides | Secção | Quem |
| --- | --- | --- |
| 1–{N['revisao-2024']} | Abertura, programa, questionário OAD e revisão do Workshop 1 | Moderadora + Facilitador 1 |
| {N['m1']}–{N['m1-gancho']} | Módulo 1 · O que é a Inteligência Artificial? | Facilitador 1 |
| {N['m2']}–{N['m2-actividade-votar']} | Módulo 2 · Como uma máquina aprende (supervisionada, não supervisionada, por reforço; 4 algoritmos) | Facilitador 2 |
| {N['quiz']}–{N['quiz-5']} | Quiz relâmpago (uma pergunta por slide) | Moderadora |
| {N['m3']}–{N['m3-verificacao']} | Módulo 3 · Como sabemos se o modelo é bom? (com os hiperparâmetros) | Facilitador 5 |
| {N['m4']}–{N['m4-actividade']} | Módulo 4 · A IA e a qualidade da água | Facilitador 3 |
| {N['m5']}–{N['m5-actividade']} | Módulo 5 · A plataforma EYES TO EARTH | Facilitador 4 |
| {N['intervalo']}–{N['pratica-aula4']} | Intervalo e prática (quatro temas, cada um com aula guiada e prática) | Facilitador 5 |
| {N['apresentacoes']}–{N['resultados-modelos']} | Apresentações e resultados | Facilitador 5 |
| {N['licoes']}–{N['obrigado']} | Encerramento | Moderadora |

As imagens dos slides estão em `imagens_para_slides/` (geradas por `scripts/workshop2/figuras.py` e, as da teoria,
por `scripts/workshop2/figuras_teoria.py`).

## Como o deck é feito

O deck é gerado pelo código do projecto, como o resto do material: `scripts/build_workshop2_slides.py` escreve-o em
`reports/apresentacao/workshop2_slides/project/`. O conteúdo está em `scripts/workshop2/slides.py`, as notas fixas em
`slides_notas.py` (as notas com números vêm das respostas de referência) e a ordem em `slides_ordem.py`, que é também a
fonte dos números dos slides citados no plano, no manual e no cronograma em Word. O script verifica as regras do deck:
letra de 24 px ou mais, sem azul fora da água, sem emoji, notas com 4 000 caracteres no máximo, figuras numeradas.
"""


def main():
    ref = json.loads((FAC / "resultados_de_referencia.json").read_text(encoding="utf-8"))
    ar = json.loads((FAC / "aulas_resolvidas/resultados_de_referencia.json").read_text(encoding="utf-8"))
    (FAC / "SLIDES.md").write_text(SLIDES_MD, encoding="utf-8")
    with tempfile.TemporaryDirectory() as tmp:
        tmp = Path(tmp)
        fig = {}
        for nome, ficheiro in [("anos", "ia_contra_regras_por_ano.png")]:
            shutil.copy(IMAGENS / ficheiro, tmp / ficheiro)
            fig[nome] = tmp / ficheiro
        converter(plano(ref, ar), FAC / "Workshop2_Plano_do_dia_6h.pdf", tmp)
        converter(manual(ar), FAC / "Workshop2_Manual_dos_Facilitadores.pdf", tmp)
    print((FAC / "SLIDES.md").relative_to(ROOT))


if __name__ == "__main__":
    main()
