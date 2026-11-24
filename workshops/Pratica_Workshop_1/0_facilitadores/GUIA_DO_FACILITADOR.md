# Guia dos facilitadores · Aula prática do Workshop 1

**Sábado, 31 de Outubro de 2026 · 12:00–14:00 · 5 pares (10 estudantes) · Google Colab**

> Documento só para a equipa ETE. As soluções estão em `solucoes/`.

## 1. A aula num minuto

Os estudantes **não sabem Python**. A aula tem três camadas:

1. **Antes do sábado:** os 3 notebooks de `1_introducao_python` (cerca de 1 hora em casa). Na aula,
   15 minutos de revisão rápida.
2. **Aula guiada (2026):** a equipa resolve no projector um problema real, passo a passo:
   *quantos hectares da planície de Marracuene ficaram debaixo de água na cheia de janeiro de 2026?*
   Resposta: cerca de **20 244 ha de água nova (202 km²)**, com 20% de nuvens.
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
| Par 1 | 2023 | A grande cheia de fevereiro de 2023 | ★ | 11 244 ha |
| Par 2 | 2014 | A cheia de março de 2014 | ★ | 3 081 ha |
| Par 3 | 2016 | O ano da seca (El Niño 2015-2016) | ★★ | 37 ha |
| Par 4 | 2025 | A cheia que fugiu | ★★ | 32 ha |
| Par 5 | 2021 | A cheia escondida pelas nuvens | ★★★ | 246 ha |

Os pares mais rápidos recebem um segundo ano (2024 ★★★ é o melhor para os curiosos). Os restantes ficam para casa.

### Pontos a dizer em cada passo da aula guiada

| Passo | Pergunta para a turma | O que queremos ouvir |
| --- | --- | --- |
| 1 · Abrir | "Quantos píxeis tem a imagem?" | 815 850 píxeis, cada um com 900 m² |
| 2 · Ver | "De que cor é a água da cheia, e porquê?" | Castanha: sedimentos, turbidez alta (Módulo 3) |
| 3 · Assinatura | "Qual dos píxeis é parecido com o A, o B e o C do Módulo 3?" | Rio ≈ A, vegetação ≈ B, solo ≈ C |
| 4 · Índices | "O mar aparece azul: contamos?" | Não: está fora da zona |
| 5 · Limiar | "Onde fica o vale do histograma?" | Perto de 0; com limiar alto perde-se a água das margens |
| 6 · Contar | "Porquê 'pelo menos'?" | As nuvens (20%) escondem parte da planície |
| 7 · Mapa | "O vosso mapa está certo?" | Comparar com o Passo 8 |
| 8 · Confirmar | "E se estivesse nublado todos os dias?" | Radar Sentinel-1 |

## 4. Respostas de referência (MNDWI > 0, zona sem mar, sem nuvens)

| Ano | Satélite | Seca | Estação chuvosa | Caudal no dia / pico (m³/s) | Nuvens (%) | Água seca (ha) | Água chuvosa (ha) | Água nova (ha) | Água nova com NDWI (ha) |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| 2014 | Landsat 8 | 4 de agosto de 2013 | 16 de março de 2014 | 504 / 728 | 0,1 | 1 127 | 4 583 | **3 081** | 1 896 |
| 2016 | Landsat 8 | 13 de outubro de 2015 | 22 de abril de 2016 | 3 / 79 | 20,9 | 1 258 | 983 | **37** | 95 |
| 2017 | Landsat 8 | 15 de outubro de 2016 | 8 de março de 2017 | 215 / 310 | 16,6 | 1 219 | 887 | **43** | 36 |
| 2019 | Sentinel-2 | 28 de setembro de 2018 | 18 de fevereiro de 2019 | 178 / 236 | 1,5 | 1 090 | 1 186 | **134** | 115 |
| 2020 | Sentinel-2 | 21 de setembro de 2019 | 15 de fevereiro de 2020 | 400 / 646 | 10,5 | 1 168 | 1 039 | **202** | 64 |
| 2021 | Sentinel-2 | 25 de setembro de 2020 | 30 de janeiro de 2021 | 553 / 1 230 | 39,7 | 1 203 | 609 | **246** | 99 |
| 2022 | Sentinel-2 | 25 de setembro de 2021 | 10 de janeiro de 2022 | 440 / 440 | 15,0 | 1 230 | 540 | **22** | 32 |
| 2023 | Sentinel-2 | 25 de setembro de 2022 | 22 de fevereiro de 2023 | 499 / 2 371 | 0,6 | 1 231 | 12 451 | **11 244** | 9 573 |
| 2024 | Sentinel-2 | 30 de setembro de 2023 | 20 de janeiro de 2024 | 240 / 253 | 20,0 | 1 304 | 42 | **38** | 29 |
| 2025 | Sentinel-2 | 4 de setembro de 2024 | 24 de janeiro de 2025 | 276 / 809 | 24,8 | 1 291 | 900 | **32** | 23 |
| 2026 | Sentinel-2 | 23 de outubro de 2025 | 24 de janeiro de 2026 | 1 693 / 2 987 | 19,5 | 1 238 | 21 248 | **20 244** | 19 324 |

Um píxel = 0,09 ha. Um campo de futebol = 0,714 ha. O verificador aceita 1% de diferença.

**O padrão que a turma deve descobrir:** a planície alaga a sério quando o caudal passa o limite vermelho
(970 m³/s): 2023 e 2026. Os anos que fogem à regra têm explicação: **nuvens** (2021), **imagem longe do pico**
(2025), **índice que falha** (2022 e 2024). É a lição principal: um número de satélite só vale com o contexto.

## 5. Desafios e respostas-modelo

**2014 · A cheia de março de 2014 ★**  
*Desafio:* Calcule a água nova também com o **NDWI** (troque `INDICE_FINAL` no mapa final). Qual dos dois índices encontra mais água nova? Olhe para a imagem em cor natural: a água da cheia é limpa ou barrenta? Porque é que isso pode enganar o NDWI?  
*Resposta-modelo:* O MNDWI encontra cerca de 3 081 ha e o NDWI cerca de 1 896 ha. A água da cheia é barrenta (sedimentos) e há água pouco funda entre a vegetação: os dois reflectem bastante NIR, por isso o NDWI fica negativo nesses píxeis. O SWIR continua baixo em quase toda a água, e o MNDWI apanha-os. Para cheias barrentas, o MNDWI é mais fiável (Xu, 2006).

**2016 · O ano da seca (El Niño 2015-2016) ★★**  
*Desafio:* Encontrou **menos** água na estação chuvosa do que na seca anterior. Como é possível? Dê duas razões: pense na chuva desse ano e olhe para as nuvens.  
*Resposta-modelo:* 1) A estação chuvosa falhou: o rio e as lagoas encolheram em vez de crescer (de 1 258 ha para 983 ha). 2) Cerca de 21% da zona tem nuvens, que tapam parte do rio e das lagoas. A "água nova" (cerca de 37 ha) é só ruído do método.

**2017 · Uma estação chuvosa normal ★**  
*Desafio:* O caudal nunca passou o limite laranja. Esperava encontrar uma cheia? O que diz o seu mapa? Que parte da "água nova" pode ser erro? Procure-a no mapa e compare com as nuvens.  
*Resposta-modelo:* Não houve cheia: só cerca de 43 ha de água nova, espalhados em manchas pequenas. Parte é ruído: sombras de nuvens (17% de nuvens) parecem água escura, e pequenas lagoas enchem com a chuva local.

**2019 · Um ano sem cheia: o nosso "controlo" ★**  
*Desafio:* Num ano sem cheia, o método ainda encontra alguma "água nova". Esse valor é o **ruído** do método. Se noutro ano encontrar 150 ha de água nova, pode dizer que houve cheia? E 3 000 ha?  
*Resposta-modelo:* Cerca de 134 ha é o nível de ruído: lagoas e campos que enchem com a chuva local, e pequenas diferenças entre as duas datas. Com 150 ha não se pode afirmar que houve cheia; com 3 000 ha sim (é cerca de 20 vezes o ruído, como em 2014).

**2020 · A cheia pequena de fevereiro de 2020 ★★**  
*Desafio:* O caudal passou o limite laranja, mas o mapa mostra pouca água nova. O rio transbordou para a planície? Compare com o "controlo" de 2019 (cerca de 130 ha de ruído).  
*Resposta-modelo:* Encontra cerca de 202 ha, pouco acima do ruído de 2019. A água ficou quase toda no leito, com pequenas extravasões. A planície de Marracuene alaga a sério quando o caudal passa o limite vermelho (970 m³/s), como em 2023 e 2026.

**2021 · A cheia escondida pelas nuvens ★★★**  
*Desafio:* 1) A água nova que encontrou é a resposta certa, um mínimo ou um máximo? Porquê? 2) Calcule também com o NDWI: dá muito menos. Use a célula "investigar um píxel": compare o verde e o NIR do píxel do rio na estação chuvosa. Porque é que o NDWI falha aqui? 3) Que satélite usaria para mapear esta cheia?  
*Resposta-modelo:* 1) É um **mínimo**: 40% da zona não se vê, e a cheia pode estar debaixo das nuvens. 2) A água da cheia é tão barrenta que reflecte mais NIR do que verde (no píxel do rio: verde 0,070, NIR 0,091): o NDWI fica negativo e diz "não é água". O MNDWI usa o SWIR, que continua baixo (0,043), e funciona. 3) O radar Sentinel-1, que vê através das nuvens.

**2022 · Uma imagem no dia do pico ★★**  
*Desafio:* A imagem é do próprio dia do pico, mas o MNDWI encontra **menos** água do que na seca! Investigue: 1) há nuvens sobre o rio? 2) Na célula "investigar um píxel", compare o verde e o SWIR do píxel do rio nas duas datas. 3) Repita o mapa com o NDWI. O que conclui?  
*Resposta-modelo:* 1) Sim: nuvens e sombras tapam parte do rio. 2) Na estação chuvosa a água ficou muito escura (verde 0,010, SWIR 0,012): é um efeito da correcção atmosférica. Com o verde tão baixo, o MNDWI fica perto de 0 e falha em parte do rio, enquanto o NDWI (verde contra NIR 0,000) ainda funciona. 3) Com 440 m³/s (pouco acima do laranja) não houve cheia na planície: a água nova é cerca de 22 ha.

**2023 · A grande cheia de fevereiro de 2023 ★**  
*Desafio:* Dez dias depois do pico, o caudal já tinha descido para 499 m³/s, mas a planície continuava alagada. Porquê? Quantos km² de água nova? Quantos campos de futebol?  
*Resposta-modelo:* A planície é baixa e plana: a água que sai do rio fica retida e só sai devagar (volta ao rio, infiltra-se e evapora), por isso o mapa mostra a cheia muitos dias depois do pico. Água nova: cerca de 11 244 ha = 112,4 km² = cerca de 15 748 campos de futebol.

**2024 · O mistério dos índices ★★★**  
*Desafio:* O MNDWI diz que o rio quase desapareceu (de cerca de 1 304 ha para 42 ha). 1) Olhe para a imagem em cor natural: o rio desapareceu mesmo? 2) Faça o mapa também com o NDWI. 3) Na célula "investigar um píxel", veja o verde, o NIR e o SWIR do píxel do rio nas duas datas. O que está estranho?  
*Resposta-modelo:* 1) Não: o rio está lá, muito escuro. 2) O NDWI encontra o rio. 3) A correcção atmosférica deixou a água quase sem luz: verde 0,007, NIR 0,000, SWIR 0,018. Como o SWIR ficou maior do que o verde, o MNDWI fica negativo; o NDWI (verde maior do que NIR) ainda diz "água". Mas o NDWI dá 1,00, o máximo possível, só porque o NIR ficou a zero: também é um sinal de que a imagem tem um problema. Lição: nunca confiar num número sem olhar para a imagem, e comparar dois índices.

**2025 · A cheia que fugiu ★★**  
*Desafio:* O pico passou o limite laranja, mas quase não há água nova. 1) Quantos dias passaram entre o pico e a imagem? 2) Que caudal tinha o rio no dia da imagem? 3) O Sentinel-2 passa sobre Marracuene a cada 2 dias, mais ou menos. Porque não usámos uma imagem mais perto do pico?  
*Resposta-modelo:* 1) 8 dias. 2) 276 m³/s, já abaixo do limite laranja: a cheia tinha passado. 3) As passagens mais perto do pico (14, 17 e 19 de janeiro) tinham entre 37% e 93% da planície com nuvens. Uma imagem óptica só vê a cheia se o céu estiver limpo no dia certo.

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
