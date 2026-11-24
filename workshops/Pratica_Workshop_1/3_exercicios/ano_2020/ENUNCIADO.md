# Exercício 2020 · A cheia pequena de fevereiro de 2020 ★★

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

Em fevereiro de 2020 o Incomáti chegou a 646 m³/s (13 de fevereiro de 2020), acima do limite laranja (376 m³/s) mas abaixo do vermelho (970 m³/s). A imagem é de 15 de fevereiro de 2020, com o rio a 400 m³/s e 10% de nuvens. Satélite: **Sentinel-2**.

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | 21 de setembro de 2019 | 15 de fevereiro de 2020 |
| Caudal do rio nesse dia | 2,5 m³/s | 400 m³/s |
| Satélite | Sentinel-2 | Sentinel-2 |

Pico do caudal no ano: **646 m³/s a 13 de fevereiro de 2020**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_2020.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

O caudal passou o limite laranja, mas o mapa mostra pouca água nova. O rio transbordou para a planície? Compare com o "controlo" de 2019 (cerca de 130 ha de ruído).

## O que o par entrega

- O mapa PNG (`mapa_2020_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
