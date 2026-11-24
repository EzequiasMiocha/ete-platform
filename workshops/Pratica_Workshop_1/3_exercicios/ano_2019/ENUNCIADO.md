# Exercício 2019 · Um ano sem cheia: o nosso "controlo" ★

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

Em 2019 o pico foi só 236 m³/s (20 de fevereiro de 2019). A imagem de 18 de fevereiro de 2019 (178 m³/s) está quase sem nuvens (2%). Um ano assim serve de **controlo**: mostra quanta "água nova" o método encontra quando **não** há cheia. Satélite: **Sentinel-2** (passa a 30 m nesta aula).

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | 28 de setembro de 2018 | 18 de fevereiro de 2019 |
| Caudal do rio nesse dia | 0,0 m³/s | 178 m³/s |
| Satélite | Sentinel-2 | Sentinel-2 |

Pico do caudal no ano: **236 m³/s a 20 de fevereiro de 2019**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_2019.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

Num ano sem cheia, o método ainda encontra alguma "água nova". Esse valor é o **ruído** do método. Se noutro ano encontrar 150 ha de água nova, pode dizer que houve cheia? E 3 000 ha?

## O que o par entrega

- O mapa PNG (`mapa_2019_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
