# Aula prática · Workshop de Estudantes 1 (31 de Outubro de 2026)

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
| `ano_2014` | A cheia de março de 2014 | Landsat 8 | ★ |
| `ano_2016` | O ano da seca (El Niño 2015-2016) | Landsat 8 | ★★ |
| `ano_2017` | Uma estação chuvosa normal | Landsat 8 | ★ |
| `ano_2019` | Um ano sem cheia: o nosso "controlo" | Sentinel-2 | ★ |
| `ano_2020` | A cheia pequena de fevereiro de 2020 | Sentinel-2 | ★★ |
| `ano_2021` | A cheia escondida pelas nuvens | Sentinel-2 | ★★★ |
| `ano_2022` | Uma imagem no dia do pico | Sentinel-2 | ★★ |
| `ano_2023` | A grande cheia de fevereiro de 2023 | Sentinel-2 | ★ |
| `ano_2024` | O mistério dos índices | Sentinel-2 | ★★★ |
| `ano_2025` | A cheia que fugiu | Sentinel-2 | ★★ |

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
