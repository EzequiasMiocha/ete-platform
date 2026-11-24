"""Textos da aula prática: LEIA-ME, como trabalhar (estudantes) e guia dos facilitadores."""

from .comum import AULA, HA_CAMPO, fmt
from .exercicios import ANOS, campos, data_pt

# Distribuição proposta para os 5 pares durante a aula (os outros anos ficam para casa ou para pares rápidos)
PARES = [("Par 1", 2023), ("Par 2", 2014), ("Par 3", 2016), ("Par 4", 2025), ("Par 5", 2021)]


def leia_me(respostas):
    anos = [a for a in ANOS]
    linhas = "\n".join(f"| `ano_{a}` | {ANOS[a]['titulo']} | {respostas[str(a)]['satelite']} | {ANOS[a]['estrelas']} |"
                       for a in anos)
    return f"""# Aula prática · Workshop de Estudantes 1 (31 de Outubro de 2026)

**Ver a água a partir do espaço com satélites e Python** · Projecto EYES TO EARTH (ETE)

Material completo da sessão prática (12:00–14:00), preparado a partir do notebook original da equipa
(`Aula_pratica_1_.ipynb` e `ETE_Atividade_30m_vs_10m.ipynb`, que ficam nesta pasta sem alterações).

## O que há em cada pasta

| Pasta | Para quem | O que tem |
| --- | --- | --- |
| `0_facilitadores/` | Equipa ETE (não partilhar com os estudantes) | Guia do facilitador, soluções, respostas de referência, imagens para os slides |
| `1_introducao_python/` | Estudantes, **antes** do workshop (e 15 min na aula) | 3 notebooks curtos: Python, NumPy, Matplotlib. Para quem nunca programou |
| `2_aula_guiada/` | Todos, na aula | O problema resolvido em conjunto: a cheia de janeiro de 2026 |
| `3_exercicios/` | Pares, na aula e em casa | 10 anos diferentes, mesmos passos, um desafio diferente em cada ano |
| `4_teste_do_aluno/` | Estudantes (e a equipa, para experimentar) | 12 perguntas com correcção automática |

## Os 10 exercícios

| Pasta | Tema | Satélite | Dificuldade |
| --- | --- | --- | --- |
{linhas}

★ directo · ★★ precisa de interpretação · ★★★ tem uma armadilha para investigar

## Como usar no Google Colab

1. Copie a pasta `Pratica_Workshop_1` para o Google Drive (sem a pasta `0_facilitadores` na cópia dos estudantes).
2. No Drive, clique duas vezes no notebook e escolha **Abrir com → Google Colaboratory**.
3. Na primeira célula de dados, o notebook procura o ficheiro `.npz` no Drive. Se não o encontrar,
   abre uma janela para o carregar do computador.
4. Corra as células por ordem com **Shift + Enter**.

Só é preciso `numpy` e `matplotlib`, que já vêm no Colab. **Não se descarrega nada durante a aula**:
cada ano tem cerca de 12 MB de dados prontos.

## Como foi feito

Os dados vêm do Google Earth Engine (Landsat 8 Collection 2 nível 2 e Sentinel-2 nível 2A),
recortados à planície do Incomáti em Marracuene (22 × 33 km), a 30 m. As datas foram escolhidas
medindo as nuvens só dentro desta área. Para refazer tudo:

```bash
.venv/bin/python scripts/download_workshop_scenes.py    # imagens (cerca de 200 MB, uma vez)
.venv/bin/python scripts/build_workshop_data.py         # ficheiros .npz e respostas de referência
.venv/bin/python scripts/build_workshop_notebooks.py    # notebooks e textos
.venv/bin/python scripts/test_workshop.py               # corre tudo como um aluno e confirma as respostas
```
"""


def como_trabalhar(respostas):
    linhas = "\n".join(f"| {p} | `ano_{a}` | {ANOS[a]['titulo']} | {ANOS[a]['estrelas']} |" for p, a in PARES)
    return f"""# Como trabalhar nos exercícios

Cada pasta `ano_AAAA` tem:

- `ENUNCIADO.md`: o problema, para ler e pensar **antes** de abrir o computador (Parte A em papel);
- `exercicio_AAAA.ipynb`: o notebook, com os mesmos passos do notebook guiado;
- `dados/`: as duas imagens desse ano (seca e estação chuvosa).

## Na aula (13:10–13:40)

| Par | Ano | Tema | Dificuldade |
| --- | --- | --- | --- |
{linhas}

Os outros anos (2017, 2019, 2020, 2022, 2024) são para os pares que acabarem cedo e para casa.

## Passos

1. **10 min** · Parte A do enunciado, em papel: previsão e contas simples.
2. **15 min** · O notebook: troque os `...` (✏️) e corra por ordem. As células ✅ dizem se acertou.
3. **5 min** · O mapa final e a resposta ao desafio.
4. Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar, o número da água nova e porquê.
   O facilitador escreve o vosso número no `quadro_da_turma.ipynb`.

## Regras de ouro

- Corra as células **por ordem**. Se algo estranho acontecer: **Reiniciar e executar tudo**.
- Leia a **última linha** dos erros. Há uma tabela de erros comuns no fim de cada notebook.
- Pergunte! Há um membro da equipa ETE para cada par.
"""


def guia(respostas, sondas):
    def linha(a):
        r = respostas[str(a)]
        return (f"| {a} | {r['satelite']} | {data_pt(r['data_seca'])} | {data_pt(r['data_chuvosa'])} | "
                f"{fmt(r['caudal_chuvosa'])} / {fmt(r['caudal_pico'])} | {fmt(r['nuvem_chuvosa_pct'], 1)} | "
                f"{fmt(r['agua_seca_ha'])} | {fmt(r['agua_chuvosa_ha'])} | **{fmt(r['agua_nova_ha'])}** | "
                f"{fmt(r['ndwi_agua_nova_ha'])} |")
    anos = [a for a in ANOS] + [2026]
    tabela = "\n".join(linha(a) for a in anos)
    desafios = []
    for a in ANOS:
        lin, col, valores = sondas[a]
        k = campos(respostas[str(a)], a, lin, col, valores)
        desafios.append(f"**{a} · {ANOS[a]['titulo']} {ANOS[a]['estrelas']}**  \n"
                        f"*Desafio:* {ANOS[a]['desafio'].format(**k)}  \n"
                        f"*Resposta-modelo:* {ANOS[a]['resposta'].format(**k)}")
    desafios = "\n\n".join(desafios)
    r26 = respostas["2026"]
    pares = "\n".join(f"| {p} | {a} | {ANOS[a]['titulo']} | {ANOS[a]['estrelas']} | {fmt(respostas[str(a)]['agua_nova_ha'])} ha |"
                      for p, a in PARES)
    return f"""# Guia dos facilitadores · Aula prática do Workshop 1

**Sábado, 31 de Outubro de 2026 · 12:00–14:00 · 5 pares (10 estudantes) · Google Colab**

> Documento só para a equipa ETE. As soluções estão em `solucoes/`.

## 1. A aula num minuto

Os estudantes **não sabem Python**. A aula tem três camadas:

1. **Antes do sábado:** os 3 notebooks de `1_introducao_python` (cerca de 1 hora em casa). Na aula,
   15 minutos de revisão rápida.
2. **Aula guiada (2026):** a equipa resolve no projector um problema real, passo a passo:
   *quantos hectares da planície de Marracuene ficaram debaixo de água na cheia de janeiro de 2026?*
   Resposta: cerca de **{fmt(r26['agua_nova_ha'])} ha de água nova ({fmt(r26['agua_nova_ha'] / 100)} km²)**, com {fmt(r26['nuvem_chuvosa_pct'])}% de nuvens.
3. **Exercícios por pares:** cada par repete os mesmos passos para **um ano diferente** e descobre
   uma lição diferente: cheia grande, seca, nuvens, imagem tardia, índice que falha.
   No fim, os resultados juntam-se num gráfico: **10 anos de cheias no Incomáti**.

## 2. O que mudou em relação ao material original

O notebook original (`Aula_pratica_1_.ipynb`) tinha uma boa base pedagógica (comparações do dia-a-dia,
partes editáveis, plano B sem Internet, mapa final com justificação), que se manteve. Mas, ao correr,
**o resultado dizia que não houve cheia**: 14 487 ha de água na seca contra 14 461 ha na "cheia" (−26 ha).

| Problema no original | Consequência | O que se fez |
| --- | --- | --- |
| A área (AOI) começa a 25,67° S, a norte da vila, e desce até ao mar | Fica de fora quase toda a planície que inundou (até 25,47° S) | Nova área: 32,64–32,86° E, 25,47–25,77° S (a planície) |
| O mar entra nas contas como água | Cerca de 14 000 ha de "água" nas duas datas esconde a cheia | Máscara `zona` = distrito de Marracuene sem o mar |
| A "cheia" é de 8 de fevereiro (630 m³/s), já em recuo | A janela 1 fev–15 mar falha o pico de 19 de janeiro (2 987 m³/s) | Imagem de 24 de janeiro (1 693 m³/s), a mais limpa perto do pico |
| `MAX_NUVENS` usa as nuvens da cena inteira | Uma cena "com 7% de nuvens" pode ter 31% sobre Marracuene | Datas escolhidas medindo as nuvens só na planície; máscara `nuvem` por píxel |
| Descarrega as imagens durante a aula (5 pacotes + ~50 MB por imagem, por par) | Risco alto com a rede do local | Dados prontos (.npz, ~12 MB por ano); só numpy e matplotlib |
| Simula o Landsat guardando 1 píxel em cada 3 | Não é como o Landsat funciona | Comparação com imagens reais: Sentinel-2A (10 m) e Landsat 9 (30 m) |
| Sem introdução ao Python | Estudantes sem bases perdem-se no primeiro erro | 3 notebooks de introdução, tabela de erros comuns em todos os notebooks |
| Histograma e áreas incluem o mar | O "vale" do histograma fica distorcido | Histograma e áreas só na zona, sem nuvens |

**Correcções sugeridas ao plano teórico (PDF):**

- *Módulo 2, pergunta "cheia de 2013 a 10 m?":* a resposta "usa-se o Landsat a 30 m" está incompleta. Em
  janeiro de 2013 o Landsat 8 ainda não estava operacional (lançado em fevereiro, dados a partir de abril
  de 2013) e o Landsat 5 já não adquiria imagens. Só havia o **Landsat 7, com riscas sem dados** (avaria do
  SLC desde 2003). Boa pergunta para discutir.
- *Módulo 2, revisita do Sentinel-2:* "cerca de 5 dias" é o valor oficial do par. Em Marracuene medimos
  uma passagem a cada **cerca de 2 dias**, porque a zona fica em duas órbitas (49 e 92) e o Sentinel-2A
  continua em campanha prolongada (figura `reports/apresentacao/pt/5_orbitas_e_revisitas.png`).
- *Módulo 2, Sentinel-1 "6–12 dias":* confirmar com o Agostinho o estado actual da constelação
  (o Sentinel-1B avariou em dezembro de 2021; o Sentinel-1C foi lançado em dezembro de 2024).
- *Módulo 2, "dados desde 2015":* certo para o Sentinel-2, mas o produto corrigido da atmosfera (nível 2A)
  quase não existe em Marracuene antes de 2019. Por isso os exercícios de 2014–2017 usam Landsat 8.
- *Módulos 2, 3 e 4, visuais:* já existem as figuras em `reports/apresentacao/pt/` (mapa, cor natural com
  legendas, Landsat vs Sentinel-2, antes e durante a cheia) e as de `imagens_para_slides/` nesta pasta
  (falsa cor, NDWI e MNDWI na seca e na cheia).

## 3. Cronograma da prática

| Hora | Bloco | O que acontece | Quem |
| --- | --- | --- | --- |
| 12:00–12:10 | Arranque | Pares sentados, Colab aberto, `aula_guiada_cheia_2026.ipynb` aberto e Célula 0 corrida | Toda a equipa circula |
| 12:10–12:25 | Python em 15 min | Revisão no projector: variável, lista, `if`, numpy (`>` e `.sum()`), `imshow`. Usar as células dos notebooks 1–3 | Ezequias |
| 12:25–13:10 | Aula guiada | Passos 1–8 do notebook de 2026 (o Passo 9 só se houver tempo). A equipa projecta; os pares correm as mesmas células | Ezequias projecta; 1 membro da equipa por par |
| 13:10–13:40 | Exercício do par | Cada par faz o seu ano (tabela abaixo): Parte A em papel, depois o notebook | Equipa circula |
| 13:40–13:55 | Apresentação | Cada par: mapa + número + desafio (2–3 min). O facilitador escreve os números no `quadro_da_turma.ipynb` e projecta o gráfico | Ezequias + moderadora |
| 13:55–14:00 | Fecho da prática | Três ideias do dia; ligação ao encerramento | Ezequias |

**Distribuição dos anos (proposta):**

| Par | Ano | Tema | Dificuldade | Resposta (água nova) |
| --- | --- | --- | --- | --- |
{pares}

Os pares mais rápidos recebem um segundo ano (2024 ★★★ é o melhor para os curiosos). Os restantes ficam para casa.

### Pontos a dizer em cada passo da aula guiada

| Passo | Pergunta para a turma | O que queremos ouvir |
| --- | --- | --- |
| 1 · Abrir | "Quantos píxeis tem a imagem?" | 815 850 píxeis, cada um com 900 m² |
| 2 · Ver | "De que cor é a água da cheia, e porquê?" | Castanha: sedimentos, turbidez alta (Módulo 3) |
| 3 · Assinatura | "Qual dos píxeis é parecido com o A, o B e o C do Módulo 3?" | Rio ≈ A, vegetação ≈ B, solo ≈ C |
| 4 · Índices | "O mar aparece azul: contamos?" | Não: está fora da zona |
| 5 · Limiar | "Onde fica o vale do histograma?" | Perto de 0; com limiar alto perde-se a água das margens |
| 6 · Contar | "Porquê 'pelo menos'?" | As nuvens ({fmt(r26['nuvem_chuvosa_pct'])}%) escondem parte da planície |
| 7 · Mapa | "O vosso mapa está certo?" | Comparar com o Passo 8 |
| 8 · Confirmar | "E se estivesse nublado todos os dias?" | Radar Sentinel-1 |

## 4. Respostas de referência (MNDWI > 0, zona sem mar, sem nuvens)

| Ano | Satélite | Seca | Estação chuvosa | Caudal no dia / pico (m³/s) | Nuvens (%) | Água seca (ha) | Água chuvosa (ha) | Água nova (ha) | Água nova com NDWI (ha) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
{tabela}

Um píxel = 0,09 ha. Um campo de futebol = {fmt(HA_CAMPO, 3)} ha. O verificador aceita 1% de diferença.

**O padrão que a turma deve descobrir:** a planície alaga a sério quando o caudal passa o limite vermelho
(970 m³/s): 2023 e 2026. Os anos que fogem à regra têm explicação: **nuvens** (2021), **imagem longe do pico**
(2025), **índice que falha** (2022 e 2024). É a lição principal: um número de satélite só vale com o contexto.

## 5. Desafios e respostas-modelo

{desafios}

## 6. Antes do sábado

| Quando | O quê | Quem |
| --- | --- | --- |
| Quarta 28 | Enviar aos estudantes os notebooks de `1_introducao_python` e o link do Colab, com a mensagem "1 hora antes de sábado" | Irene / Ezequias |
| Quarta 28 | Criar a pasta partilhada no Google Drive (só leitura) **sem** `0_facilitadores` | Ezequias |
| Quinta 29 | Ensaio geral: correr a aula guiada e 2 exercícios **na rede do local**, com um portátil "de estudante" | Toda a equipa |
| Quinta 29 | Confirmar: cada par com portátil, carregador e conta Google | Glads |
| Sexta 30 | Imprimir os 5 `ENUNCIADO.md` da aula (um por par) e este guia (um por membro da equipa) | Glads |
| Sexta 30 | Pen drive com a pasta inteira (plano B) | Ezequias |

## 7. Problemas frequentes

| Sintoma | Causa | Solução |
| --- | --- | --- |
| `FileNotFoundError: Não encontrei ...npz` | O notebook foi aberto sem a pasta `dados` | Montar o Drive (`from google.colab import drive; drive.mount("/content/drive")`) ou carregar o ficheiro quando o Colab pedir |
| A janela de carregar ficheiro não aparece | Bloqueador de pop-ups do navegador | Permitir pop-ups para colab.research.google.com, ou usar o ícone de pasta à esquerda do Colab |
| `NameError` | Células corridas fora de ordem | **Ambiente de execução → Reiniciar e executar tudo** |
| `AssertionError: ✏️ Volte à célula anterior` | Ficaram `...` por preencher | Normal: é o aviso pedagógico. Ajudar a completar a célula ✏️ |
| ❌ no verificador | Conta errada ou LIMIAR diferente de 0 | Ver a dica; confirmar `LIMIAR = 0.0` |
| Colab lento ou "sem memória" | Muitas figuras abertas | Reiniciar o ambiente; cada notebook usa menos de 500 MB |
| Sem Internet | Rede do local em baixo | Plano B: notebooks em Jupyter num portátil da equipa (Anaconda) a partir do pen drive, projectados; os pares trabalham no papel (Parte A dos enunciados) |

## 8. Avaliação

- O **inquérito OAD** (pré e pós) é o instrumento oficial.
- O `4_teste_do_aluno/teste_do_aluno.ipynb` (12 perguntas, nota em 20) pode ser feito em casa, no fim do dia
  ou numa sessão seguinte. Também serve para a equipa experimentar a aula como estudante.
"""


def construir(respostas, sondas):
    (AULA / "LEIA-ME.md").write_text(leia_me(respostas), encoding="utf-8")
    (AULA / "3_exercicios/COMO_TRABALHAR.md").write_text(como_trabalhar(respostas), encoding="utf-8")
    (AULA / "0_facilitadores/GUIA_DO_FACILITADOR.md").write_text(guia(respostas, sondas), encoding="utf-8")
    return [AULA / "LEIA-ME.md", AULA / "3_exercicios/COMO_TRABALHAR.md", AULA / "0_facilitadores/GUIA_DO_FACILITADOR.md"]
