# Ficha de evidência do problema

Projecto Eyes to Earth (tarefa W3-09). Gerada pelo notebook 38 em 11/10/2026.
Todos os números vêm dos dados do projecto; a origem de cada um está indicada.

## Cheias sem aviso

| Facto | Número | Origem |
|---|---|---|
| Anos (de Outubro a Setembro) em que o rio passou o limite laranja | **16 em 21** | regras de alerta sobre o caudal GloFAS e a chuva, 2006–2026 |
| Anos em que passou o limite vermelho | **9 em 21** | idem |
| Meses com alerta laranja ou vermelho | **43 em 249** | idem |
| Maior caudal do período | **2 987 m³/s em 2026** | GloFAS (modelo, não estação) |
| Antecedência que o sistema teria dado em Janeiro de 2026 | **4 a 5 dias** antes do primeiro mapa de cheia | notebook 32 |

## O que está no caminho da água (cheia de Janeiro de 2026, dentro do distrito)

| Facto | Número | Origem |
|---|---|---|
| Área alagada | **239 km²** | Copernicus EMS (EMSR857) |
| Terras agrícolas alagadas | **46 km²** | ESA WorldCover |
| Edifícios na zona alagada | **1 935** | Google Open Buildings |
| Estradas e caminhos na zona alagada | **232 km** | OpenStreetMap |
| Pessoas na zona alagada | **até cerca de 24 700** (limite superior) | WorldPop 2020; ver nota |
| Lugares com nome que alagam primeiro / em cheia grande | **4 / 18** | OpenStreetMap e GeoNames, por validar |

## Água cuja qualidade ninguém acompanha

| Facto | Número | Origem |
|---|---|---|
| Estações públicas de qualidade da água na bacia do Incomáti | **0** | arquivo mundial GEMStat (UNEP), Fevereiro de 2026 |
| Troços do rio agora acompanhados por satélite | **9**, da fronteira à foz | Módulo Q |
| Troços com 20 anos de registo | **3** (os de jusante; a montante o rio é estreito e só há dados desde 2017) | notebook 29 |
| Ano com mais meses de água turva a jusante, desde 2014 | **2015** (46 % dos meses acima do normal) | notebook 36 |
| Troços com tendência de 20 anos confirmada de água mais turva | **0** (os dados não mostram que o rio esteja a ficar mais turvo) | Mann-Kendall sazonal, notebook 36 |

## Notas para usar estes números

- "Anos em que o rio passou o limite" são anos em que o sistema teria avisado. Não são
  cheias confirmadas uma a uma no terreno.
- As pessoas vêm de um mapa que espalha a população por todo o terreno. Numa planície com
  poucas casas dá gente a mais; dizer sempre "até cerca de".
- A área alagada é a da zona que o Copernicus analisou (58 % do distrito), mais a zona
  estimada pelo Modelo A fora dela.
- O satélite vê a cor da água. Não diz se a água é segura.
