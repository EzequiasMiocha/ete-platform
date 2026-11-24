# Protocolo de campo: qualidade da água do Incomáti

Projecto Eyes to Earth (ETE). Versão 1, 11 de Outubro de 2026.

> **Estado: não será executado nesta fase.** A 12 de Outubro de 2026 a equipa decidiu não fazer
> medições no local. O protocolo fica guardado para uma fase futura do projecto ou para um
> parceiro que as possa fazer. As datas de passagem abaixo deixam de estar actualizadas.

## Para que serve

A plataforma mede a cor da água do rio por satélite e prevê as manhãs em que a
água deve estar mais turva. Hoje esse indicador é **relativo**: diz "mais turva
do que o habitual", mas não diz quantas unidades de turbidez.

Com amostras recolhidas no rio **no mesmo dia e à mesma hora em que o satélite
passa**, conseguimos:

1. Converter o índice do satélite em unidades reais de turbidez (NTU).
2. Confirmar no local o efeito da maré que os dados de satélite mostram.
3. Começar a medir a salinidade, que o satélite não vê e que afecta a rega e a
   água para beber.

**Meta:** 20 a 30 pares "amostra + imagem do mesmo dia" por troço. Com uma saída
por semana em dia de céu limpo, chega-se lá em cerca de dois a três meses.

## Material

| Material | Para quê | Nota |
|---|---|---|
| Turbidímetro portátil (NTU) | turbidez | o mais importante; calibrar com os padrões antes de cada saída |
| Tubo de turbidez ou disco de Secchi | transparência | alternativa barata se não houver turbidímetro; usar sempre o mesmo |
| Medidor de condutividade (µS/cm) | salinidade | com compensação de temperatura |
| Termómetro | temperatura da água | muitos medidores já incluem |
| Balde limpo com corda, ou garrafa de recolha | recolher a água | lavar três vezes com água do rio antes de recolher |
| Telemóvel com GPS e relógio certo | posição, hora e fotografias | |
| Ficha de registo (no fim deste documento) | registo | uma linha por medição |

## Onde medir

Um ponto fixo por troço, sempre o mesmo. As coordenadas abaixo são o centro de
cada troço usado pela plataforma. A equipa deve escolher o ponto acessível mais
próximo (ponte, cais, margem firme) e **registar as coordenadas reais do ponto
escolhido** na primeira saída.

| Troço | Centro do troço (latitude, longitude) | Lugares próximos (a confirmar) |
|---|---|---|
| 1 montante (norte) | -25.5252, 32.7579 | Augusto Mota, Pateque |
| 2 troço médio | -25.7866, 32.7269 | Macaneta, Guamba |
| 3 jusante | -25.8396, 32.7287 | Mateu |
| 4 foz / estuário | -25.8646, 32.7218 | Rodrigues |

Regras para escolher o ponto:

- Água a correr, longe da margem: de uma ponte, de um barco, ou com o balde
  lançado para o meio do canal. A água parada junto à margem não representa o rio.
- Longe de descargas, de bebedouros de gado e de locais onde se lava roupa.
- Se só houver meios para dois pontos, escolher os troços 3 e 2, onde a medição
  por satélite é mais fiável e a maré se faz sentir.

## Quando medir

**No dia de passagem do satélite, entre as 9h00 e as 10h00 (hora de Moçambique).**
O satélite passa por volta das 9h30. A cor da água muda ao longo do dia com a
maré, por isso uma amostra recolhida à tarde não serve para comparar.

- Só contam os dias com **céu limpo sobre o rio** à hora da passagem. Se estiver
  nublado, a saída pode ser adiada para a data seguinte.
- Começar pelo ponto mais difícil de alcançar e registar sempre a hora exacta.
- Se só for possível medir fora dessa hora, medir na mesma e registar a hora:
  serve para estudar a maré, embora não para calibrar o satélite.

### Datas previstas de passagem

Datas calculadas pelo ciclo de repetição dos satélites (Sentinel-2 de 5 em 5
dias em cada órbita, Landsat de 16 em 16). **Confirmar na véspera.** A coluna da
maré é a maré calculada pelo projecto para a hora de passagem, na Baía de Maputo.

| Data | Satélites | Maré às 9h30 (m) | Tendência | Amplitude do dia (m) |
|---|---|---|---|---|
| 14/10/2026 | Sentinel-2 | -0,61 | a vazar | 2,2 |
| 16/10/2026 | Sentinel-2 | -0,06 | a vazar | 1,6 |
| **19/10/2026** | **Sentinel-2 + Landsat 9** | 0,35 | parada | 0,4 |
| 21/10/2026 | Sentinel-2 | 0,16 | a encher | 0,7 |
| 24/10/2026 | Sentinel-2 | -0,64 | a encher | 2,1 |
| 26/10/2026 | Sentinel-2 | -1,17 | parada | 2,6 |
| 27/10/2026 | Landsat 8 | -1,17 | a vazar | 2,7 |
| 29/10/2026 | Sentinel-2 | -0,67 | a vazar | 2,4 |
| 31/10/2026 | Sentinel-2 | 0,19 | a vazar | 1,6 |
| 03/11/2026 | Sentinel-2 | 0,54 | a encher | 0,7 |
| 04/11/2026 | Landsat 9 | 0,36 | a encher | 0,9 |
| 05/11/2026 | Sentinel-2 | 0,01 | a encher | 1,3 |
| 08/11/2026 | Sentinel-2 | -0,85 | a encher | 2,2 |
| 10/11/2026 | Sentinel-2 | -0,95 | a vazar | 2,3 |
| 12/11/2026 | Landsat 8 | -0,60 | a vazar | 2,1 |
| 13/11/2026 | Sentinel-2 | -0,36 | a vazar | 1,8 |
| 15/11/2026 | Sentinel-2 | 0,17 | a vazar | 1,2 |
| 18/11/2026 | Sentinel-2 | 0,55 | a encher | 0,6 |
| **20/11/2026** | **Sentinel-2 + Landsat 9** | 0,36 | a encher | 1,0 |
| 23/11/2026 | Sentinel-2 | -0,68 | a encher | 2,1 |
| 25/11/2026 | Sentinel-2 | -1,06 | a vazar | 2,5 |
| **28/11/2026** | **Sentinel-2 + Landsat 8** | -0,21 | a vazar | 2,1 |
| 30/11/2026 | Sentinel-2 | 0,61 | a vazar | 1,5 |
| 03/12/2026 | Sentinel-2 | 0,58 | a encher | 0,9 |
| 05/12/2026 | Sentinel-2 | 0,00 | a encher | 1,3 |

Como escolher as datas:

- **Os dias a negrito valem a dobrar:** passam dois satélites na mesma manhã.
- **Variar a maré.** Para a calibração ser boa, as amostras devem cobrir água
  limpa e água turva. Escolher dias de maré baixa de manhã (valores negativos,
  amplitude grande) **e** dias de maré alta ou amplitude pequena.
- **Depois de chuva forte ou de subida do rio**, fazer uma saída extra na data
  de passagem seguinte: são as amostras de água muito turva, as mais raras.

## Como medir (em cada ponto)

1. Registar data, hora, coordenadas e o estado do céu (limpo, algumas nuvens,
   nublado).
2. Lavar o balde três vezes com água do rio. Recolher água a cerca de 20 a 30 cm
   de profundidade, sem tocar no fundo nem levantar lama.
3. **Turbidez:** agitar suavemente a amostra, encher o frasco do turbidímetro,
   limpar o vidro por fora e fazer **três leituras**. Registar as três.
4. **Condutividade e temperatura:** mergulhar a sonda na amostra (ou
   directamente no rio), esperar que o valor estabilize e registar.
5. **Transparência** (se houver disco de Secchi): descer o disco do lado da
   sombra até deixar de se ver, subir até voltar a ver-se, e registar a média
   das duas profundidades.
6. Tirar **duas fotografias**: uma da superfície da água de cima para baixo, e
   uma do rio com as margens.
7. Anotar o que se vê: plantas flutuantes, espuma, cor estranha, cheiro, se a
   água corre para o mar ou para montante (maré a encher), vento forte.

## Cuidados

- Nunca entrar no rio (pode haver crocodilos e hipopótamos). Medir a partir
  de pontes, cais ou margem firme, e nunca sozinho.
- Não sair com o rio em alerta laranja ou vermelho.
- Calibrar o turbidímetro e o medidor de condutividade antes de cada saída e
  registar que foi feito.

## Ficha de registo

Uma linha por ponto e por saída. Guardar também em folha de cálculo, com estas
colunas exactas, e enviar ao responsável técnico depois de cada saída.

| Campo | Exemplo |
|---|---|
| data | 2026-10-19 |
| hora_local | 09:25 |
| troco | 3 jusante |
| latitude, longitude | -25.8391, 32.7290 |
| ceu | limpo |
| turbidez_ntu_1, _2, _3 | 48, 51, 50 |
| condutividade_us_cm | 820 |
| temperatura_c | 24,5 |
| secchi_cm | 35 |
| sentido_da_corrente | para o mar |
| plantas_flutuantes | não |
| observacoes | vento fraco; água castanha |
| equipamento_calibrado | sim |
| quem_mediu | nome |
| fotografias | nomes dos ficheiros |

## O que acontece aos dados

1. Cada medição é comparada com a imagem de satélite do mesmo dia e troço.
2. Com 20 a 30 pares, ajusta-se a relação entre o índice do satélite e a
   turbidez em NTU, e testa-se em pares que não entraram no ajuste.
3. Se a relação for boa, a plataforma passa a mostrar turbidez em NTU. Se não
   for, o resultado é publicado na mesma, como foi feito com os outros testes.
4. As medições de condutividade começam uma série de salinidade, para estudar
   até onde a água salgada sobe com o rio baixo.

## Limites

- As amostras calibram a turbidez. Não dizem se a água é segura: para isso são
  precisas análises de laboratório (bactérias, químicos).
- Os nomes dos lugares na tabela vêm de mapas públicos e ainda não foram
  validados no terreno.
