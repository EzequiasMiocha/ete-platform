# Os dados das aulas

Esta pasta tem os dados das 4 aulas e das 4 práticas (cerca de 38 MB). **Não é preciso abrir estes ficheiros:** os
notebooks abrem-nos sozinhos. Todos são usados: não apaguem nenhum.

| Ficheiro | O que tem | Onde se usa |
| --- | --- | --- |
| `incomati_2026_cheia.npz` | A imagem do satélite da cheia de 24/01/2026, em Marracuene | Aulas 1 e 2, Prática 2 |
| `incomati_2014_chuvosa.npz` a `incomati_2025_chuvosa.npz` | A imagem de um dia de chuvas de cada ano (uma por par) | Prática 1 |
| `exemplos_da_equipa.json` | Os pontos de exemplo de cada imagem, com a resposta certa: água ou não água | Aulas 1 e 2, Práticas 1 e 2 |
| `mapa_oficial_cheia_2026.npz` | O mapa oficial da cheia de 24/01/2026: o exame | Aula 2, Prática 2 |
| `cor_do_rio_e_mare.csv` | 2 205 linhas (uma manhã num troço do rio): a cor do rio, o caudal, a chuva e a maré | Aula 3, Prática 3 |
| `caudal_e_chuva_diarios.csv` | 7 517 dias: o caudal do rio e a chuva | Aula 4, Prática 4 |

## Treino e teste em cada aula

Para aprender, o modelo precisa de exemplos com a resposta certa: é o **treino**. Para saber se aprendeu bem, faz-se um
exame com exemplos que ele nunca viu: é o **teste**.

| Aula | O algoritmo | Treino (o modelo aprende) | Teste (o modelo é avaliado) |
| --- | --- | --- | --- |
| Aula 1 | árvore de decisão | todos os pontos de 2026 | os mesmos pontos (por isso esta nota engana) |
| Prática 1 | árvore de decisão | todos os pontos do ano do par | os mesmos pontos |
| Aula 2 | floresta aleatória | os primeiros 10 + 10 pontos de 2026 (498 píxeis) | os outros 5 + 5 pontos (240 píxeis) e o mapa oficial |
| Prática 2 | floresta aleatória | os últimos 10 + 10 pontos (488 píxeis) | os primeiros 5 + 5 pontos (250 píxeis) e o mapa oficial |
| Aula 3 e Prática 3 | floresta aleatória | as manhãs de 2017 a 2022 (1 214) | as manhãs de 2023 a 2026 (991) |
| Aula 4 e Prática 4 | regressão linear (e, na Aula 4, a árvore de regressão) | os dias de 2006 a 2018 | os dias de 2019 a 2026 |

## As imagens do satélite (`incomati_*.npz`)

- Cada imagem é uma tabela de 1110 linhas por 735 colunas: 33 km por 22 km do vale do Incomáti, em Marracuene.
- Cada casa da tabela é um **píxel**: um quadrado de 30 m por 30 m no chão.
- Em cada píxel, o satélite mede 5 **bandas**: azul, verde, vermelho, nir e swir (as duas últimas são infravermelhos que
  os olhos não vêem). Cada número diz quanta luz o chão devolve, de 0 (nada) a 1 (tudo). A água devolve muito pouco swir.
- `nuvem` marca os píxeis com nuvem ou sombra (aí o satélite não vê o chão) e `zona` marca o distrito de Marracuene,
  sem o mar.

| Imagem | Satélite | Dia | Caudal do rio nesse dia | Quem a usa |
| --- | --- | --- | --- | --- |
| `incomati_2026_cheia.npz` | Sentinel-2 | 24/01/2026 | 1 693 m³/s | todos (Aulas 1 e 2, Prática 2) |
| `incomati_2024_chuvosa.npz` | Sentinel-2 | 20/01/2024 | 240 m³/s | Par 1 (Prática 1) |
| `incomati_2021_chuvosa.npz` | Sentinel-2 | 30/01/2021 | 553 m³/s | Par 2 (Prática 1) |
| `incomati_2022_chuvosa.npz` | Sentinel-2 | 10/01/2022 | 440 m³/s | Par 3 (Prática 1) |
| `incomati_2014_chuvosa.npz` | Landsat 8 | 16/03/2014 | 504 m³/s | Par 4 (Prática 1) |
| `incomati_2025_chuvosa.npz` | Sentinel-2 | 24/01/2025 | 276 m³/s | Par 5 (Prática 1) |

## Os pontos de exemplo (`exemplos_da_equipa.json`)

Para cada imagem, a equipa ETE preparou pontos onde se sabe a resposta: **água** ou **não água**. Cada ponto é uma linha
e uma coluna da imagem, e conta como o quadrado de 5 por 5 píxeis à volta dele (até 25 exemplos por ponto; os píxeis com
nuvem ficam de fora).

- 2026: 15 pontos de água (cheia barrenta, rio e lagoas) e 15 de não água (plantas, campos, areia e casas).
- 2014, 2021, 2022, 2024 e 2025: 5 pontos de água (no rio) e 5 de não água (terra baixa com plantas), em cada ano.

## O mapa oficial da cheia (`mapa_oficial_cheia_2026.npz`)

Especialistas do serviço europeu **Copernicus EMS** desenharam onde estava a água a 24/01/2026. Para cada píxel, `rotulo`
diz 1 (água), 0 (não água) ou -1 (sem resposta). São 407 875 píxeis com resposta: um exame muito maior
do que os nossos pontos, e feito por outros. No exame só contam os que não estão debaixo de nuvens.

## A cor do rio e a maré (`cor_do_rio_e_mare.csv`)

Uma linha por manhã em que o satélite viu o rio sem nuvens, em cada um de 3 troços, de 06/01/2017 a
26/09/2026.

| Coluna | O que é |
| --- | --- |
| `data`, `ano`, `mes` | o dia |
| `troco` | o pedaço do rio: troço médio, jusante ou foz (onde o rio chega ao mar) |
| `ndti` | a turbidez medida pelo satélite: mais alto = água mais barrenta |
| `caudal_m3s` | quanta água passa no rio, em metros cúbicos por segundo |
| `chuva_7d_mm` | a chuva na bacia do rio nos últimos 7 dias, em milímetros |
| `altura_da_mare_m` | a maré à hora do satélite (cerca das 9:30), em metros acima (+) ou abaixo (-) do nível médio do mar |
| `turva` | **o rótulo** (a resposta certa): 1 = mais barrenta do que o normal nesse troço, 0 = mais limpa |

## O caudal e a chuva (`caudal_e_chuva_diarios.csv`)

Uma linha por dia, de 30/01/2006 a 31/08/2026.

| Coluna | O que é |
| --- | --- |
| `data` | o dia |
| `caudal_m3s` | o caudal do Incomáti em Marracuene, em m³/s (calculado pelo modelo europeu GloFAS) |
| `chuva_dia_mm` | a chuva desse dia na bacia do rio, em milímetros |
| `chuva_7d_mm`, `chuva_14d_mm`, `chuva_30d_mm` | a chuva somada nos últimos 7, 14 e 30 dias, contando com esse dia |

Na Aula 4 e na Prática 4, o **alvo** (o número a prever) é criado no próprio notebook: o caudal 3 ou 7 dias depois.
