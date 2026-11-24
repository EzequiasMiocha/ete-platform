# Exercício 2014 · A cheia de março de 2014 ★

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

Em março de 2014 o Incomáti subiu até 728 m³/s (13 de março de 2014). Nessa altura o Sentinel-2 ainda não existia: só havia o **Landsat 8**, lançado em 2013. A imagem da estação chuvosa é de 16 de março de 2014, 3 dias depois do pico.

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | 4 de agosto de 2013 | 16 de março de 2014 |
| Caudal do rio nesse dia | 1,3 m³/s | 504 m³/s |
| Satélite | Landsat 8 | Landsat 8 |

Pico do caudal no ano: **728 m³/s a 13 de março de 2014**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_2014.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

Calcule a água nova também com o **NDWI** (troque `INDICE_FINAL` no mapa final). Qual dos dois índices encontra mais água nova? Olhe para a imagem em cor natural: a água da cheia é limpa ou barrenta? Porque é que isso pode enganar o NDWI?

## O que o par entrega

- O mapa PNG (`mapa_2014_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
