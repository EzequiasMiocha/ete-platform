"""Teste do aluno (com correcção automática) e quadro da turma (síntese final dos pares)."""

import base64
import json

from .comum import AULA, LEGENDA, code, escrever, md

PERGUNTAS = [
    # (enunciado, resposta, tipo, explicação)
    ("Depois destas linhas, quanto vale `x`?\n\n```python\nx = 5\nx = x + 2\nx = x * 3\n```",
     21, "numero", "x começa em 5, passa a 7 e depois a 7 × 3 = 21. O `=` guarda o resultado na caixa x."),
    ("`caudais = [120, 450, 1300, 80]`. Quanto vale `caudais[2]`?",
     1300, "numero", "O Python conta a partir de 0: caudais[0] = 120, caudais[1] = 450, caudais[2] = 1300."),
    ("Na mesma lista, quantos caudais passam o limite de alerta laranja (376 m³/s)? "
     "Pode usar código: `(np.array(caudais) > 376).sum()`",
     2, "numero", "450 e 1300 passam 376. O numpy conta True como 1, por isso .sum() dá 2."),
    ("Um píxel tem verde = 0.08 e NIR = 0.02. Quanto vale o NDWI? (escreva o número, com ponto)",
     0.6, "numero", "NDWI = (0.08 − 0.02) / (0.08 + 0.02) = 0.06 / 0.10 = 0.6. Positivo: provavelmente água."),
    ("Um píxel tem verde = 0.10 e SWIR = 0.30. Quanto vale o MNDWI?",
     -0.5, "numero", "MNDWI = (0.10 − 0.30) / (0.10 + 0.30) = −0.20 / 0.40 = −0.5. Negativo: não é água."),
    ("Um mapa do **Sentinel-2 a 10 m** tem 5 000 píxeis de água. Quantos hectares são?",
     50, "numero", "Um píxel de 10 m × 10 m = 100 m². 5 000 × 100 = 500 000 m² = 50 ha."),
    ("O mesmo número de píxeis (5 000) num mapa do **Landsat a 30 m**. Quantos hectares?",
     450, "numero", "Um píxel de 30 m × 30 m = 900 m² = 0.09 ha. 5 000 × 0.09 = 450 ha. Atenção ao tamanho do píxel!"),
    ("Quantos `True` dá `np.array([0.3, -0.2, 0.5, np.nan, 0.1]) > 0`?",
     3, "numero", "0.3, 0.5 e 0.1 são maiores que 0. O nan (nuvem) dá False: não sabemos o valor."),
    ("Queremos mapear a cheia de **janeiro de 2013** com imagens ópticas. Que satélite temos?\n\n"
     "a) Sentinel-2, a 10 m  \nb) Landsat 7, com riscas sem dados  \nc) Landsat 9",
     "b", "letra", "O Sentinel-2 só começou em 2015, o Landsat 8 só ficou operacional em abril de 2013 e o "
                   "Landsat 9 é de 2021. Restava o Landsat 7, com riscas sem dados desde 2003."),
    ("A água de uma cheia está muito barrenta e reflecte bastante NIR. Que índice tem mais probabilidade de falhar?\n\n"
     "a) NDWI  \nb) MNDWI",
     "a", "letra", "O NDWI compara o verde com o NIR: se a água barrenta reflecte NIR, o NDWI fica negativo. "
                   "O SWIR continua baixo na água, por isso o MNDWI aguenta melhor (foi o que vimos em 2021)."),
    ("40% da zona tem nuvens e encontrámos 250 ha de água nova. A água nova verdadeira é:\n\n"
     "a) exactamente 250 ha  \nb) pelo menos 250 ha  \nc) no máximo 250 ha",
     "b", "letra", "Só contamos o que vemos. Debaixo das nuvens pode haver mais água: 250 ha é um mínimo."),
    ("Durante uma cheia, o céu ficou nublado todos os dias. Que satélite consegue mesmo assim ver a água?\n\n"
     "a) Landsat 8  \nb) Sentinel-2  \nc) Sentinel-1 (radar)",
     "c", "letra", "O radar envia a sua própria onda e atravessa as nuvens. Os ópticos dependem da luz do Sol."),
]


def teste():
    gabarito = [[r, t, e] for _, r, t, e in PERGUNTAS]
    pacote = base64.b64encode(json.dumps(gabarito, ensure_ascii=False).encode()).decode()
    c = [md(f"""
# Teste do aluno · 12 perguntas com correcção automática

Use este teste **depois** dos notebooks de introdução, ou no fim da aula, para saber o que já domina.
Responda trocando os `...` e corra a célula: aparece logo ✅ ou ❌ com a explicação.
No fim, a última célula dá a sua nota.

{LEGENDA}
"""),
         code(f"""
# Célula 0 · corrector: corra sem mudar nada ▶️
import base64, json
import numpy as np
_GABARITO = json.loads(base64.b64decode("{pacote}").decode())
_NOTAS = {{}}


def corrigir(numero, resposta):
    certa, tipo, explicacao = _GABARITO[numero - 1]
    if resposta is ...:
        print("✏️ Ainda não respondeu.")
        return
    if tipo == "numero":
        acertou = abs(float(resposta) - certa) <= 0.01
    else:
        acertou = str(resposta).strip().lower().startswith(certa)
    _NOTAS[numero] = acertou
    print(("✅ Certo! " if acertou else f"❌ Não. A resposta é {{certa}}. ") + explicacao)


def resultado():
    certas = sum(_NOTAS.values())
    print(f"Respondeu a {{len(_NOTAS)}} de {{len(_GABARITO)}} perguntas e acertou {{certas}}.")
    if len(_NOTAS) == len(_GABARITO):
        nota = 20 * certas / len(_GABARITO)
        print(f"Nota: {{nota:.0f}} valores em 20.")
        if nota >= 16:
            print("Excelente: está pronto para os exercícios ★★★.")
        elif nota >= 10:
            print("Bom. Reveja as perguntas erradas no notebook indicado na explicação.")
        else:
            print("Volte aos notebooks de introdução 1 e 2 e repita o teste.")


print("Corrector pronto.")
""")]
    for i, (pergunta, _, tipo, _) in enumerate(PERGUNTAS, start=1):
        c.append(md(f"### Pergunta {i}\n\n{pergunta}"))
        dica = "# um número, por exemplo 12 ou 0.5" if tipo == "numero" else '# a letra entre aspas, por exemplo "a"'
        c.append(code(f"resposta_{i} = ...      {dica}\ncorrigir({i}, resposta_{i})"))
    c.append(md("## A sua nota ▶️"))
    c.append(code("resultado()"))
    return c


def turma(respostas: dict, facilitador: bool):
    anos = [int(a) for a in respostas if int(a) != 2026]
    picos = {a: respostas[str(a)]["caudal_pico"] for a in anos}
    if facilitador:
        valores = {a: respostas[str(a)]["agua_nova_ha"] for a in anos}
        linhas = "\n".join(f"    {a}: {valores[a]},      # {respostas[str(a)]['satelite']}, nuvens {respostas[str(a)]['nuvem_chuvosa_pct']:.0f}%"
                           for a in anos)
    else:
        linhas = "\n".join(f"    {a}: None," for a in anos)
    c = [md(f"""
# Quadro da turma · 10 anos de cheias no Incomáti
{"**VERSÃO DOS FACILITADORES: preenchida com as respostas de referência (MNDWI > 0).**" if facilitador else ""}

Durante as apresentações, o facilitador escreve aqui a **água nova (ha)** que cada par encontrou.
Juntos, os resultados mostram como a cheia na planície depende do caudal do rio,
e quando é que o método falha (nuvens, data da imagem, índice).
"""),
         code(f"""
import matplotlib.pyplot as plt

# Pico do caudal em cada ano (m³/s, GloFAS): já preenchido
PICO = {picos}

# ✏️ Água nova (ha) de cada par: troque None pelo número que o par apresentou
AGUA_NOVA = {{
{linhas}
}}

# A cheia de 2026 do notebook guiado, para comparação
AGUA_NOVA_2026, PICO_2026 = {respostas['2026']['agua_nova_ha']}, {respostas['2026']['caudal_pico']}
print("Anos já preenchidos:", [a for a, v in AGUA_NOVA.items() if v is not None])
"""),
         code("""
anos = [a for a, v in AGUA_NOVA.items() if v is not None]
fig, eixos = plt.subplots(1, 2, figsize=(14, 5))

eixos[0].bar([str(a) for a in anos] + ["2026"], [AGUA_NOVA[a] for a in anos] + [AGUA_NOVA_2026], color="teal")
eixos[0].set_ylabel("Água nova na planície (ha)")
eixos[0].set_title("Água nova em cada ano")

eixos[1].scatter([PICO[a] for a in anos], [AGUA_NOVA[a] for a in anos], s=80, color="teal")
eixos[1].scatter([PICO_2026], [AGUA_NOVA_2026], s=120, color="darkorange")
for a in anos:
    eixos[1].annotate(str(a), (PICO[a], AGUA_NOVA[a]), textcoords="offset points", xytext=(6, 4))
eixos[1].annotate("2026", (PICO_2026, AGUA_NOVA_2026), textcoords="offset points", xytext=(-30, -14))
for limite, cor in [(376, "orange"), (970, "red")]:
    eixos[1].axvline(limite, color=cor, linestyle="--")
eixos[1].set_xlabel("Pico do caudal no ano (m³/s)")
eixos[1].set_ylabel("Água nova (ha)")
eixos[1].set_title("Mais caudal, mais cheia? (linhas: alerta laranja e vermelho)")
plt.tight_layout()
plt.show()
"""),
         md("""
## Para discutir em turma

1. Há uma relação entre o pico do caudal e a água nova? A partir de que caudal a planície alaga a sério?
2. Que anos **fogem** à regra? Para cada um, qual é a explicação: nuvens, data da imagem longe do pico,
   ou um índice que falhou?
3. Se a plataforma ETE só tivesse imagens ópticas, conseguiria avisar a população a tempo? O que falta?
   (Pista: previsão do caudal e radar.)
""")]
    return c


def construir(respostas: dict):
    return [
        escrever(teste(), AULA / "4_teste_do_aluno/teste_do_aluno.ipynb", "ETE · Teste do aluno"),
        escrever(turma(respostas, False), AULA / "3_exercicios/quadro_da_turma.ipynb", "ETE · Quadro da turma"),
        escrever(turma(respostas, True), AULA / "0_facilitadores/solucoes/quadro_da_turma_preenchido.ipynb",
                 "ETE · Quadro da turma (facilitadores)"),
    ]
