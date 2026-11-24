"""Notebooks de introdução ao Python (pasta 1_introducao_python): para quem nunca programou."""

from .comum import AULA, LEGENDA, code, escrever, md

CAUDAL_JAN_2026 = [178, 178, 183, 202, 203, 197, 196, 208, 223, 236, 255, 319, 464, 664, 933, 1266,
                   2239, 2932, 2987, 2718, 2375, 2086, 1859, 1693, 1558, 1446, 1348, 1257, 1176, 1101, 1031]


def python_basico():
    c = [md(f"""
# 1 · Python: primeiros passos (20 minutos)

**Para quem nunca programou.** No fim deste notebook vai saber usar as 5 peças que aparecem na aula:
**variáveis, listas, `if`, `for` e funções**. Todos os exemplos são sobre o rio Incomáti.

**Como funciona um notebook.** Tem dois tipos de células:
- **células de texto**, como esta, para ler;
- **células de código** (fundo cinzento), que o computador corre.

Para correr uma célula de código: clique nela e prima **Shift + Enter**. O resultado aparece por baixo.
Corra as células **por ordem, de cima para baixo**.

{LEGENDA}
"""),
         md("""
## 1. O Python faz contas

Corra a célula abaixo ▶️. O que vem depois de `#` é um **comentário**: o Python ignora-o, serve para nós lermos.
"""),
         code("""
# Uma conta simples
2 + 3
"""),
         code("""
# print() mostra o resultado no ecrã. Podemos ter várias linhas numa célula.
print(10 * 3)      # multiplicar
print(7 / 2)       # dividir
print(2 ** 3)      # potência: 2 elevado a 3
print(30 * 30)     # área de um píxel Landsat, em m²
"""),
         md("""
| Símbolo | Conta | Exemplo | Resultado |
| --- | --- | --- | --- |
| `+` `-` | somar, subtrair | `5 - 2` | `3` |
| `*` | multiplicar | `30 * 30` | `900` |
| `/` | dividir | `900 / 10000` | `0.09` |
| `**` | potência | `10 ** 2` | `100` |

Repare: o Python usa **ponto** nas casas decimais (`0.09`), não vírgula.
"""),
         md("""
## 2. Variáveis: dar um nome a um valor

Uma variável é uma **caixa com etiqueta**: guardamos um valor e depois usamos o nome.
O sinal `=` quer dizer "guarda na caixa", não "é igual".
"""),
         code("""
caudal = 2987          # caudal do Incomáti a 19 de janeiro de 2026, em m³/s (um número inteiro)
reflectancia = 0.06    # um número com casas decimais
rio = "Incomáti"       # um texto vai sempre entre aspas

print(rio, "levava", caudal, "m³/s")
"""),
         code("""
# Um f-texto (f antes das aspas) mistura texto e variáveis dentro de { }
caudal_seca = 0.5      # caudal em setembro de 2025
print(f"Na cheia, o {rio} levava {caudal} m³/s")
print(f"Isso é {caudal / caudal_seca:.0f} vezes o caudal da seca")
"""),
         md("""
**Regras para os nomes:** sem espaços (use `_`, como em `caudal_seca`), sem começar por número,
e de preferência sem acentos. O Python distingue maiúsculas de minúsculas: `Rio` e `rio` são diferentes.

### ✏️ Mini-exercício 1

Um campo de futebol tem 105 m × 68 m. Calcule a área em m² e em hectares (1 ha = 10 000 m²).
Troque os `...` pelas contas e corra a célula.
"""),
         code("""
comprimento = 105
largura = 68
area_m2 = ...        # ✏️ multiplique o comprimento pela largura
area_ha = ...        # ✏️ divida area_m2 por 10000
print(area_m2, "m²  =", area_ha, "hectares")
"""),
         md("""
## 3. Listas: vários valores numa só variável

Uma lista guarda vários valores por ordem, entre `[ ]`, separados por vírgulas.
"""),
         code("""
caudais = [202, 255, 664, 2239, 2987, 2718]   # caudal (m³/s) em seis dias de janeiro de 2026

print(caudais)
print("Primeiro valor:", caudais[0])     # o Python começa a contar em 0!
print("Segundo valor:", caudais[1])
print("Último valor:", caudais[-1])      # -1 é o último
print("Quantos valores:", len(caudais))
print("Maior caudal:", max(caudais))
"""),
         md("""
**Atenção:** a posição do primeiro elemento é `0`, não `1`. É a fonte de erro mais comum em Python.

## 4. Decidir com `if`

O `if` ("se") faz uma pergunta. Se a resposta for sim, corre as linhas de baixo que estão **afastadas 4 espaços**.
Os limites são os da plataforma ETE para o caudal em Marracuene.
"""),
         code("""
caudal = 2987

if caudal > 970:
    print("Alerta VERMELHO: cheia grave")
elif caudal > 376:              # elif = "senão, se"
    print("Alerta LARANJA: cheia possível")
else:                           # else = "em todos os outros casos"
    print("Sem alerta")
"""),
         md("""
Comparações: `>` maior, `<` menor, `>=` maior ou igual, `<=` menor ou igual, `==` igual (dois sinais!), `!=` diferente.

✏️ Experimente: mude o `caudal` para `500` e depois para `100`, e corra outra vez.

## 5. Repetir com `for`

O `for` repete as mesmas linhas para cada valor de uma lista.
"""),
         code("""
for q in caudais:
    print(q, "m³/s")
"""),
         code("""
# Contar os dias acima de 970 m³/s (alerta vermelho)
dias_vermelho = 0
for q in caudais:
    if q > 970:
        dias_vermelho = dias_vermelho + 1     # soma 1 à contagem
print("Dias em alerta vermelho:", dias_vermelho)
"""),
         md("""
### ✏️ Mini-exercício 2

Conte os dias com caudal **acima de 376 m³/s** (alerta laranja ou pior). Copie a ideia da célula anterior.
"""),
         code("""
dias_laranja = 0
# ✏️ escreva aqui o for e o if (lembre-se dos 4 espaços)

print("Dias em alerta laranja ou pior:", dias_laranja)
"""),
         md("""
## 6. Funções: uma receita com nome

Uma função guarda uma receita para usar muitas vezes. `def` cria a função; `return` devolve o resultado.
"""),
         code('''
def nivel_de_alerta(caudal):
    """Devolve o nível de alerta para um caudal em m³/s."""
    if caudal > 970:
        return "vermelho"
    elif caudal > 376:
        return "laranja"
    else:
        return "verde"


print(nivel_de_alerta(2987))
print(nivel_de_alerta(450))
print(nivel_de_alerta(150))
'''),
         md("""
### ✏️ Mini-exercício 3

Escreva uma função `hectares(m2)` que recebe uma área em m² e devolve a área em hectares.
Teste com o campo de futebol (7 140 m² devem dar 0.714 ha).
"""),
         code("""
# ✏️ escreva a função aqui


# print(hectares(7140))     # tire o # do início desta linha depois de escrever a função
"""),
         md("""
## 7. Bibliotecas: caixas de ferramentas

O Python sozinho sabe pouco. As **bibliotecas** juntam ferramentas prontas. Chamamo-las com `import`.
Na aula vamos usar duas: **numpy** (contas com tabelas de números) e **matplotlib** (desenhar).
São os próximos dois notebooks.
"""),
         code("""
import math                      # a biblioteca de matemática
print(math.sqrt(900))            # raiz quadrada: o lado de um píxel de 900 m² tem 30 m
"""),
         md("""
## 8. Erros: não tenha medo

Toda a gente tem erros. A mensagem vermelha diz o que correu mal: **leia a última linha**.

| Exemplo | Última linha do erro | Porquê |
| --- | --- | --- |
| `print(cauldal)` | `NameError: name 'cauldal' is not defined` | Nome escrito mal, ou a célula que cria a variável não correu |
| `print("Incomáti)` | `SyntaxError: unterminated string literal` | Falta fechar as aspas |
| `if caudal > 970` | `SyntaxError: expected ':'` | Falta os dois pontos no fim do `if` |
| `print(rio + 5)` | `TypeError: can only concatenate str...` | Não se soma texto com número |

## Respostas dos mini-exercícios

Tente primeiro sozinho. Depois compare:

```python
# Mini-exercício 1
area_m2 = comprimento * largura      # 7140
area_ha = area_m2 / 10000            # 0.714

# Mini-exercício 2
dias_laranja = 0
for q in caudais:
    if q > 376:
        dias_laranja = dias_laranja + 1
print(dias_laranja)                  # 4

# Mini-exercício 3
def hectares(m2):
    return m2 / 10000
print(hectares(7140))                # 0.714
```

**Próximo:** `2_numpy_imagens_sao_tabelas.ipynb`
""")]
    return c


def numpy_basico():
    c = [md(f"""
# 2 · NumPy: uma imagem é uma tabela de números (20 minutos)

Uma imagem de satélite é uma **tabela enorme de números**: cada quadradinho (píxel) tem um valor por banda.
A biblioteca **numpy** faz contas com a tabela inteira de uma só vez, sem `for`.
É assim que calculamos um índice de água para 800 000 píxeis em menos de um segundo.

{LEGENDA}
"""),
         code("""
import numpy as np      # "np" é a abreviatura que toda a gente usa
print("numpy pronto, versão", np.__version__)
"""),
         md("""
## 1. Um array: uma lista que sabe fazer contas

Com uma lista normal, `lista * 2` repete a lista. Com um **array** do numpy, multiplica cada número.
"""),
         code("""
caudais = np.array([202, 255, 664, 2239, 2987, 2718])   # m³/s, janeiro de 2026

print(caudais * 2)              # cada valor vezes 2
print(caudais / 1000)           # cada valor a dividir por 1000
print("Média:", caudais.mean())
print("Máximo:", caudais.max())
"""),
         md("""
## 2. Perguntas a todos os valores: True e False

Uma comparação devolve uma tabela de `True` (verdadeiro) e `False` (falso).
E há um truque muito útil: **o numpy conta `True` como 1**, por isso `.sum()` diz quantos são verdadeiros.
"""),
         code("""
acima = caudais > 970
print(acima)
print("Dias acima de 970 m³/s:", acima.sum())
"""),
         md("""
## 3. Os píxeis misteriosos do Módulo 3

Na teoria vimos três píxeis, A, B e C. Pomos as bandas de cada um num array (uma posição por píxel)
e calculamos o **NDWI = (Verde − NIR) / (Verde + NIR)** dos três ao mesmo tempo.
"""),
         code("""
#                   A      B      C
verde = np.array([0.06,  0.10,  0.15])
nir   = np.array([0.02,  0.45,  0.28])
swir  = np.array([0.01,  0.20,  0.35])

ndwi = (verde - nir) / (verde + nir)
print("NDWI:", ndwi.round(2))       # round(2) arredonda a 2 casas decimais
print("É água (NDWI > 0)?", ndwi > 0)
"""),
         md("""
### ✏️ Mini-exercício 1

Calcule o **MNDWI = (Verde − SWIR) / (Verde + SWIR)** para os três píxeis. Deve dar `[0.71, -0.33, -0.4]`.
"""),
         code("""
mndwi = ...          # ✏️ escreva a fórmula, como no NDWI acima
print("MNDWI:", mndwi)
"""),
         md("""
## 4. Uma imagem pequena: tabela com linhas e colunas

Agora uma "imagem" de 4 linhas × 5 colunas, já com valores de NDWI.
Para ler um píxel usamos `[linha, coluna]`, sempre a contar de 0.
"""),
         code("""
imagem = np.array([[-0.4, -0.3,  0.2,  0.5, -0.2],
                   [-0.5,  0.1,  0.6,  0.4, -0.3],
                   [-0.6, -0.2,  0.3,  0.7,  0.1],
                   [-0.4, -0.5, -0.1,  0.5,  0.3]])

print("Forma (linhas, colunas):", imagem.shape)
print("Píxel da linha 1, coluna 2:", imagem[1, 2])
print("Recorte das linhas 0-1 e colunas 2-3:")
print(imagem[0:2, 2:4])        # 0:2 quer dizer "da 0 até antes da 2"
"""),
         code("""
agua = imagem > 0              # o "mapa de água": True onde o NDWI é positivo
print(agua)
n = agua.sum()
print("Píxeis de água:", n)
print("Área, se cada píxel tiver 30 m x 30 m:", n * 30 * 30 / 10000, "hectares")
"""),
         md("""
## 5. Dados que faltam: `nan`

Quando uma nuvem tapa o chão, não sabemos o valor: usamos `np.nan` ("não é um número").
Contas com `nan` dão `nan`, e `nan > 0` dá `False`.
"""),
         code("""
valores = np.array([0.3, -0.2, np.nan, 0.5])
print("Média normal:", valores.mean())          # dá nan
print("Média sem os nan:", np.nanmean(valores)) # ignora os nan
print("Onde falta:", np.isnan(valores))
print("Maior que 0:", valores > 0)
"""),
         md("""
## 6. Juntar perguntas: `&` (e), `|` (ou), `~` (não)

Na aula vamos perguntar "é água **e** não tem nuvem?". Cada pergunta vai entre parênteses.
"""),
         code("""
e_agua  = np.array([True,  True,  False, True])
nuvem   = np.array([False, True,  False, False])

print("Água E sem nuvem:", e_agua & ~nuvem)
print("Água OU nuvem:   ", e_agua | nuvem)
print("Quantos píxeis de água vistos:", (e_agua & ~nuvem).sum())
"""),
         md("""
### ✏️ Mini-exercício 2

Na `imagem` acima, quantos píxeis têm NDWI **maior que 0.4**? E qual é a área em hectares (píxeis de 30 m)?
"""),
         code("""
n_forte = ...        # ✏️ conte os píxeis com imagem > 0.4
print("Píxeis com NDWI > 0.4:", n_forte)
"""),
         md("""
## Respostas

```python
# Mini-exercício 1
mndwi = (verde - swir) / (verde + swir)      # [ 0.71 -0.33 -0.4 ]

# Mini-exercício 2
n_forte = (imagem > 0.4).sum()               # 5 píxeis
print(n_forte * 30 * 30 / 10000)             # 0.45 hectares
```

**Resumo:** um array faz contas com todos os píxeis de uma vez; `>` cria um mapa de True/False;
`.sum()` conta os True; `&` junta condições; `nan` marca o que falta.

**Próximo:** `3_matplotlib_desenhar.ipynb`
""")]
    return c


def matplotlib_basico():
    c = [md(f"""
# 3 · Matplotlib: desenhar gráficos e imagens (20 minutos)

**matplotlib** é a biblioteca de desenho. Vamos usar quatro coisas:
um **gráfico de linha**, uma **imagem** (`imshow`), **várias imagens lado a lado** e um **histograma**.

{LEGENDA}
"""),
         code("""
import numpy as np
import matplotlib.pyplot as plt     # "plt" é a abreviatura de costume
print("Prontos para desenhar.")
"""),
         md("""
## 1. Gráfico de linha: o caudal do Incomáti em janeiro de 2026

Dados do modelo GloFAS para Marracuene, um valor por dia.
"""),
         code(f"""
caudal = np.array({CAUDAL_JAN_2026})
dias = np.arange(1, 32)            # os números de 1 a 31

plt.figure(figsize=(9, 4))         # tamanho do desenho (largura, altura)
plt.plot(dias, caudal, color="teal", linewidth=2)
plt.axhline(376, color="orange", linestyle="--", label="alerta laranja (376 m³/s)")
plt.axhline(970, color="red", linestyle="--", label="alerta vermelho (970 m³/s)")
plt.xlabel("Dia de janeiro de 2026")
plt.ylabel("Caudal (m³/s)")
plt.title("Rio Incomáti em Marracuene")
plt.legend()
plt.show()
"""),
         md("""
✍️ **Pergunta:** em que dia foi o pico? Quantos dias esteve o rio acima do alerta vermelho?

## 2. Uma imagem: `imshow` desenha uma tabela de números

Cada número vira uma cor. O `cmap` escolhe as cores e a `colorbar` mostra a legenda.
"""),
         code("""
imagem = np.array([[-0.4, -0.3,  0.2,  0.5, -0.2],
                   [-0.5,  0.1,  0.6,  0.4, -0.3],
                   [-0.6, -0.2,  0.3,  0.7,  0.1],
                   [-0.4, -0.5, -0.1,  0.5,  0.3]])

plt.figure(figsize=(5, 4))
plt.imshow(imagem, cmap="RdYlBu", vmin=-1, vmax=1)   # vermelho = baixo, azul = alto
plt.colorbar(label="NDWI")
plt.title("Uma imagem é uma tabela de números")
plt.show()
"""),
         md("""
`vmin` e `vmax` fixam os limites da escala de cores. Assim, o mesmo valor tem sempre a mesma cor
em imagens diferentes. Isso é muito importante quando comparamos a seca com a cheia.

## 3. Várias imagens lado a lado: `subplots`
"""),
         code("""
agua = imagem > 0

fig, eixos = plt.subplots(1, 2, figsize=(9, 4))    # 1 linha, 2 colunas de desenhos
eixos[0].imshow(imagem, cmap="RdYlBu", vmin=-1, vmax=1)
eixos[0].set_title("NDWI")
eixos[1].imshow(agua, cmap="Blues")
eixos[1].set_title("Água (NDWI > 0)")
for e in eixos:
    e.axis("off")                  # tira os números das margens
plt.show()
"""),
         md("""
## 4. Histograma: quantos píxeis têm cada valor

O histograma conta quantos valores caem em cada intervalo. Na aula usamos o histograma
para escolher o **limiar** entre água e terra.
"""),
         code("""
# 1000 valores inventados: muita terra (perto de -0.4) e alguma água (perto de +0.5)
rng = np.random.default_rng(1)
valores = np.concatenate([rng.normal(-0.4, 0.1, 800), rng.normal(0.5, 0.1, 200)])

plt.figure(figsize=(8, 3.5))
plt.hist(valores, bins=40, color="steelblue")
plt.axvline(0, color="red", linestyle="--", label="limiar = 0")
plt.xlabel("Valor do índice")
plt.ylabel("Número de píxeis")
plt.legend()
plt.show()
"""),
         md("""
Vê dois "montes": o grande é a terra e o pequeno é a água. Um bom limiar fica **no vale entre os dois**.

## 5. Guardar uma figura

`plt.savefig("nome.png")` guarda o desenho num ficheiro. Tem de vir **antes** de `plt.show()`.
"""),
         code("""
plt.figure(figsize=(4, 3))
plt.imshow(agua, cmap="Blues")
plt.title("O meu primeiro mapa de água")
plt.axis("off")
plt.savefig("primeiro_mapa.png", dpi=100)
plt.show()
print("Guardado: primeiro_mapa.png")
"""),
         md("""
### ✏️ Mini-exercício

Desenhe só os **últimos 10 dias** de janeiro (do dia 22 ao 31). Dica: `caudal[21:]` e `dias[21:]`.
"""),
         code("""
# ✏️ escreva aqui o seu gráfico

"""),
         md("""
## Resposta

```python
plt.plot(dias[21:], caudal[21:], color="teal")
plt.title("Últimos 10 dias de janeiro de 2026")
plt.show()
```

**Já sabe o suficiente para a aula.** Ponto de partida seguinte: `2_aula_guiada/aula_guiada_cheia_2026.ipynb`.
""")]
    return c


def construir():
    pasta = AULA / "1_introducao_python"
    feitos = [
        escrever(python_basico(), pasta / "1_python_primeiros_passos.ipynb", "ETE · 1 · Python: primeiros passos"),
        escrever(numpy_basico(), pasta / "2_numpy_imagens_sao_tabelas.ipynb", "ETE · 2 · NumPy"),
        escrever(matplotlib_basico(), pasta / "3_matplotlib_desenhar.ipynb", "ETE · 3 · Matplotlib"),
    ]
    return feitos
