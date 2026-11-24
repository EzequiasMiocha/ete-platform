# Exercício 2024 · O mistério dos índices ★★★

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

Em janeiro de 2024 o pico foi de 253 m³/s (21 de janeiro de 2024), sem cheia. A imagem Sentinel-2 de 20 de janeiro de 2024 (240 m³/s) tem 20% de nuvens. Este ano esconde uma surpresa.

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | 30 de setembro de 2023 | 20 de janeiro de 2024 |
| Caudal do rio nesse dia | 28,4 m³/s | 240 m³/s |
| Satélite | Sentinel-2 | Sentinel-2 |

Pico do caudal no ano: **253 m³/s a 21 de janeiro de 2024**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_2024.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

O MNDWI diz que o rio quase desapareceu (de cerca de 1 304 ha para 42 ha). 1) Olhe para a imagem em cor natural: o rio desapareceu mesmo? 2) Faça o mapa também com o NDWI. 3) Na célula "investigar um píxel", veja o verde, o NIR e o SWIR do píxel do rio nas duas datas. O que está estranho?

## O que o par entrega

- O mapa PNG (`mapa_2024_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
