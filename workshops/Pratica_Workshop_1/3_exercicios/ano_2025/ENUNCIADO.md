# Exercício 2025 · A cheia que fugiu ★★

**Workshop de Estudantes 1 · Projecto EYES TO EARTH (ETE)**

## A história

Em janeiro de 2025 o Incomáti chegou a 809 m³/s (16 de janeiro de 2025), acima do limite laranja. A imagem Sentinel-2 mais limpa é de 24 de janeiro de 2025 (276 m³/s), com 25% de nuvens.

| | Época seca | Estação chuvosa |
| --- | --- | --- |
| Data da imagem | 4 de setembro de 2024 | 24 de janeiro de 2025 |
| Caudal do rio nesse dia | 0,9 m³/s | 276 m³/s |
| Satélite | Sentinel-2 | Sentinel-2 |

Pico do caudal no ano: **809 m³/s a 16 de janeiro de 2025**. Limites de alerta: laranja 376 m³/s, vermelho 970 m³/s.

## Parte A · Pense antes de abrir o computador (10 minutos, em papel)

1. A imagem da estação chuvosa foi tirada antes ou depois do pico? Quantos dias de diferença?
2. O caudal no dia da imagem passa algum limite de alerta? E o pico do ano?
3. **Previsão:** espera muita ou pouca água nova na planície? Porquê?
4. Cada píxel tem 30 m × 30 m. Se 5 000 píxeis forem água nova, quantos hectares são? Quantos km²?
5. Se uma parte da planície estiver debaixo de nuvens, a área de água que vai medir será exacta,
   um mínimo ou um máximo?

## Parte B · No computador (notebook `exercicio_2025.ipynb`)

Os mesmos passos do notebook guiado de 2026:

1. Abrir as imagens e vê-las em cor natural.
2. Medir a percentagem de nuvens na zona.
3. Escrever a fórmula do MNDWI.
4. Contar a água na seca, na estação chuvosa e a água nova, em hectares.
5. Investigar um píxel do rio.
6. Fazer e guardar o mapa final.

## Parte C · O desafio deste ano

O pico passou o limite laranja, mas quase não há água nova. 1) Quantos dias passaram entre o pico e a imagem? 2) Que caudal tinha o rio no dia da imagem? 3) O Sentinel-2 passa sobre Marracuene a cada 2 dias, mais ou menos. Porque não usámos uma imagem mais perto do pico?

## O que o par entrega

- O mapa PNG (`mapa_2025_...png`).
- Três números: água na seca, água nova (em ha) e % de nuvens.
- Três frases de conclusão e a resposta ao desafio.
- Na apresentação (2 a 3 minutos): o mapa, o índice e o limiar escolhidos, e porquê.
