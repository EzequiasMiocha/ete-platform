# Guia do projeto QGIS do ETE

Abrir o ficheiro `qgis/ete_marracuene.qgz` com o QGIS. As camadas, as cores e as
escalas já estão configuradas. Se algo se estragar, ou quando houver dados novos,
o projeto pode ser criado de novo com:

```bash
QT_QPA_PLATFORM=offscreen /usr/bin/python3 scripts/build_qgis_project.py
```

Isto não toca nos polígonos desenhados em `labels.gpkg`.

## Como usar o painel de camadas

- A caixa ao lado de cada camada liga e desliga a camada.
- A camada de cima tapa as de baixo. Para ver uma camada, desligar as que estão por cima.
- Para saber o valor de um píxel: ferramenta **Identificar** (ícone "i" com seta) e clicar no mapa.
- Para comparar duas camadas: ligar as duas e usar a caixa da de cima para a mostrar e esconder.

## O que está em cada grupo e como ler

| Grupo | Camada | Como ler | Para que serve |
|---|---|---|---|
| 1. Área de estudo | Distrito, canal real do Incomáti | Contorno preto e rio a azul | Orientação. As linhas do HydroSHEDS (desligadas) são aproximadas |
| 2. Rótulos | Amostras água / não-água | Azul = água, laranja = não é água | Camada para desenhar polígonos de validação |
| | Referência Copernicus EMS, jan. 2026 | Azul = alagado, laranja claro = não alagado | Os rótulos de teste usados nos modelos |
| 3. Cheia de jan. 2026 dia a dia | Alagado a 17, 18, 23 e 24 jan. | Quatro tons de azul, um por data | Ver a cheia a crescer; mapas oficiais do Copernicus |
| | Área analisada pelo Copernicus | Tracejado laranja | Fora dela não há mapa oficial |
| 4. Exposição | Saúde, escolas, estradas, edifícios | Pontos, linhas e polígonos | Ver o que fica dentro das zonas alagadas |
| 5. Cheia de janeiro de 2026 | Radar: queda do VH no momento mais escuro | Azul forte = água nova | A camada que melhor mostra a cheia |
| | Radar VH no momento mais escuro | Preto = água | Confirmar a água |
| | Radar ΔVV e VV da mediana | Como acima, mas com a mediana do mês | Comparar: a mediana quase não vê a cheia |
| | MNDWI, NDVI, cor verdadeira (Sentinel-2) | Azul = água; verde = vegetação; fotografia | Ver em imagem ótica, se não houver nuvens |
| 6. Cheia de fevereiro de 2023 | As mesmas camadas | Igual | Segundo evento, sem mapa oficial para Marracuene |
| 7. Mês seco (2022-08) | As mesmas camadas | Igual | O "normal": o que é água aqui é água sempre |
| 8. Terreno | HAND | Amarelo = quase ao nível do rio; roxo = alto | As zonas amarelas são as que podem inundar |
| | Ocorrência JRC, elevação, declive, distâncias | Escalas contínuas | Contexto do terreno |
| 9. Mapa de base | OpenStreetMap | Mapa de ruas | Nomes de lugares (precisa de internet) |

## Quatro exercícios para aprender a ler os dados

1. **Ver a cheia de janeiro de 2026 crescer.** No grupo 3, ligar primeiro só
   "Alagado a 17 jan" e depois "Alagado a 24 jan": a mancha passa de cerca de 45
   para cerca de 300 km² na zona de estudo em uma semana.
2. **Comparar o nosso radar com o mapa oficial.** No grupo 5, ligar "Radar: queda
   do VH no momento mais escuro" e, por cima, "Alagado a 24 jan" do grupo 3. As
   duas manchas coincidem ao longo do Incomáti.
3. **Ver porque a mediana não chega.** No grupo 5, desligar a camada do momento
   mais escuro e ligar "Radar ΔVV da mediana": a cheia quase desaparece. Foi por
   isto que se acrescentaram as bandas do momento mais escuro.
4. **Perceber porque inunda ali.** Ligar "HAND" (grupo 8): a cheia cai sobre a
   zona amarela, o terreno baixo junto ao rio.

## Desenhar rótulos para outros meses

Os meses prioritários estão em `reports/semana_2/26_meses_candidatos.csv`.
Para um mês que não esteja no projeto, exportar primeiro os índices no notebook
20 (lista `EXPORT_MONTHS`) e arrastar os ficheiros de
`data/interim/features/indices/<mês>/` para o QGIS.

1. Selecionar a camada "Amostras água / não-água" e clicar no lápis (**Alternar edição**).
2. Clicar em **Adicionar polígono**, desenhar com cliques e terminar com o botão direito.
3. Preencher os campos: `class` (`water` ou `non_water`), `month` (`AAAA-MM`),
   `source` (por exemplo `S1 VH p10 2023-02`), `author`, `confidence` (`alta` ou `media`).
4. Guardar com o ícone da disquete da barra de edição e desligar o lápis.

Regras para bons rótulos:

- Polígonos pequenos, só onde a classe é evidente em pelo menos duas camadas.
- Deixar de fora as margens e as zonas duvidosas.
- Desenhar as duas classes em cada mês, incluindo "não é água" em terreno baixo
  perto do rio: é o caso que mais ensina o modelo.
- Não desenhar sobre o mar.

Depois de desenhar, correr de novo os notebooks 27 e 28: os polígonos entram nas
tabelas de treino com `label_source = manual`.

## Cuidados

- Os valores já aparecem em unidades reais (refletância de 0 a 1, radar em dB).
- O branco fora do distrito + 5 km é "sem dados", não é água nem terra.
- No radar, o mar aparece quase sempre como "água nova": a superfície do mar muda
  com o vento. Ignorar o mar ao ler as camadas de radar.
- Solo nu muito seco e liso também fica escuro no radar. Escuro não quer dizer
  sempre água: confirmar com o HAND e a imagem ótica.
- O QGIS cria ficheiros `.aux.xml` ao lado dos rasters que abre. São só uma
  memória de estatísticas e podem ser apagados.
- O mapa de base do OpenStreetMap gasta internet quando está ligado.

## Módulo Q: troços do rio da fronteira à foz

O grupo "Módulo Q" tem as camadas do ficheiro `data/interim/water_quality/trocos_rio.gpkg`:

- **Troços Q1 a Q9 (linha do rio):** o rio cortado em nove troços, com o nome de cada um.
- **Água permanente:** onde a cor da água é medida. Foi feita de forma automática.
- **Água pura para o Sentinel-2 / para o Landsat:** a mesma água, afastada 10 m ou 30 m da margem.
- **Corredor de procura:** a faixa de 2,5 km em que a água foi procurada.

**Trabalho pedido (tarefas W1-10 e W2-12):** percorrer o rio da fronteira à foz com a camada
"Água permanente" ligada sobre o mapa de base e anotar onde ela apanha lagoas, charcas ou
canais de rega que não são o rio, e onde falha troços do rio. Para corrigir, edita-se a camada
`agua_permanente` e avisa-se o responsável técnico, que volta a correr a extração.
