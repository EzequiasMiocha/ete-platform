# As 4 aulas resolvidas (só para os facilitadores)

Não copiar esta pasta para os computadores dos alunos.

| Ficheiro | O que é |
| --- | --- |
| `1_Aula_..._RESOLVIDA.ipynb` a `4_Aula_..._RESOLVIDA.ipynb` | As 4 aulas guiadas, já corridas, com uma «Nota para o facilitador» a seguir a cada passo |
| `1_Pratica_..._RESOLVIDA.ipynb` a `4_Pratica_..._RESOLVIDA.ipynb` | As 4 práticas com o código escrito e as perguntas respondidas, já corridas, com notas e os resultados esperados (a Prática 1 está feita com o ano 2021; os outros anos estão na nota) |
| `modelos_treinados/aula1_arvore_de_decisao.joblib` | A árvore da Aula 1 (5 bandas, profundidade 2), treinada com os 738 exemplos da cheia de 24/01/2026 |
| `modelos_treinados/aula2_floresta_100_arvores.joblib` | A floresta da Aula 2, treinada só com os 498 exemplos de treino (10 + 10 pontos) |
| `modelos_treinados/aula3_floresta_sem_mare.joblib` | A floresta da Aula 3 (turva ou não) com o caudal, a chuva e o mês, sem a maré, treinada com 2017 a 2022 |
| `modelos_treinados/aula4_regressao_linear.joblib` | A regressão linear do caudal daqui a 3 dias, treinada com 2006 a 2018 |
| `modelos_treinados/aula4_arvore_profundidade_5.joblib` | A árvore de regressão com o menor erro no teste |
| `separacoes/aula1_exemplos_2026.csv` | Os exemplos da Aula 1: as 5 bandas e o rótulo de cada píxel |
| `separacoes/aula2_pontos_treino.csv`, `aula2_pontos_teste.csv` | Os pontos de treino (10 + 10) e de teste (5 + 5): linha, coluna e rótulo |
| `separacoes/aula2_pixeis_treino.csv`, `aula2_pixeis_teste.csv` | Os píxeis de treino (498) e de teste (240) |
| `separacoes/aula3_treino_2017_a_2022.csv`, `aula3_teste_2023_a_2026.csv` | A separação no tempo da Aula 3: 1214 manhãs de treino e 991 de teste |
| `separacoes/aula4_treino_2006_a_2018.csv`, `aula4_teste_2019_a_2026.csv` | A separação no tempo: 4719 dias de treino e 2795 de teste |
| `modelos_treinados/pratica1_arvore_2021.joblib` | A árvore da Prática 1, treinada com os pontos de 2021 |
| `modelos_treinados/pratica2_floresta_100_arvores.joblib` | A floresta da Prática 2 (teste = os primeiros 5 + 5 pontos) |
| `modelos_treinados/pratica3_floresta_com_mare.joblib`, `pratica3_floresta_troco_medio.joblib` | As florestas da Prática 3, com a maré: nos três troços e só no troço médio |
| `modelos_treinados/pratica4_regressao_7_dias.joblib` | A regressão do caudal daqui a 7 dias |
| `separacoes/pratica1_...`, `pratica2_...`, `pratica3_...`, `pratica4_...` | Os exemplos, os pontos de treino e de teste e as separações no tempo de cada prática |
| `resultados_de_referencia.json` | Os números de referência (usados no manual e nos slides) |

Para usar um modelo noutro notebook, nesta pasta:

```python
import joblib
modelo = joblib.load("modelos_treinados/aula2_floresta_100_arvores.joblib")
```

Para refazer tudo: `.venv/bin/python scripts/build_workshop2_aulas.py` (na pasta do projecto).
