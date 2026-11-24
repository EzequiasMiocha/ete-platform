# Exercício 2021 · A cheia escondida pelas nuvens ★★★

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

No fim de janeiro de 2021, depois das chuvas do ciclone tropical Eloise na região, o Incomáti chegou a 1 230 m³/s (28 de janeiro de 2021). A imagem mais próxima é de 30 de janeiro de 2021 (553 m³/s), mas tem **40%** da zona coberta de nuvens. Satélite: **Sentinel-2**.

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | 25 de setembro de 2020 | 30 de janeiro de 2021 |
| Caudal do rio nesse dia | 0,1 m³/s | 553 m³/s |
| Satélite | Sentinel-2 | Sentinel-2 |

Pico do caudal no ano: **1 230 m³/s a 28 de janeiro de 2021**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_2021.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

1) A água nova que encontrou é a resposta certa, um mínimo ou um máximo? Porquê? 2) Calcule também com o NDWI: dá muito menos. Use a célula "investigar um píxel": compare o verde e o NIR do píxel do rio na estação chuvosa. Porque é que o NDWI falha aqui? 3) Que satélite usaria para mapear esta cheia?

## O que o par entrega

- O mapa PNG (`mapa_2021_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
