# Exercício 2017 · Uma estação chuvosa normal ★

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

Em 2017 o pico do Incomáti foi de 310 m³/s (1 de março de 2017), **abaixo** do limite de alerta laranja (376 m³/s). A imagem da estação chuvosa é de 8 de março de 2017 (215 m³/s). Satélite: **Landsat 8**.

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | 15 de outubro de 2016 | 8 de março de 2017 |
| Caudal do rio nesse dia | 0,0 m³/s | 215 m³/s |
| Satélite | Landsat 8 | Landsat 8 |

Pico do caudal no ano: **310 m³/s a 1 de março de 2017**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_2017.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

O caudal nunca passou o limite laranja. Esperava encontrar uma cheia? O que diz o seu mapa? Que parte da "água nova" pode ser erro? Procure-a no mapa e compare com as nuvens.

## O que o par entrega

- O mapa PNG (`mapa_2017_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
