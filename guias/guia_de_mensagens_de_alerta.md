# Guia de mensagens de alerta

Projecto Eyes to Earth (tarefa W2-19). Versão 1, 11 de Outubro de 2026.
Para: Irene Timane e Nilza Taide (texto e desenho), líderes comunitários (leitura).

Este guia fixa os quatro níveis de alerta de cheia, o que cada um quer dizer e o que se pede
às pessoas. Os textos em português são os que o sistema já envia. **A coluna da língua local
está vazia de propósito:** deve ser preenchida por falantes nativos (changana ou ronga) e
testada com pessoas da comunidade, não traduzida por máquina.

## Os quatro níveis

| Nível | Quando é dado | O que quer dizer |
|---|---|---|
| Verde | Nenhum cenário da previsão passa os limites nos próximos 10 dias | Sem sinais de cheia |
| Amarelo | Caudal previsto acima de 164 m³/s, ou chuva de 7 dias muito acima do normal para a época | Atenção: o rio está a subir ou choveu muito na bacia |
| Laranja | Caudal previsto acima de 376 m³/s em pelo menos metade dos cenários, ou chuva de 7 dias excecional para a época | Preparação: a água pode chegar às zonas mais baixas (zona 1) |
| Vermelho | Caudal previsto acima de 970 m³/s em pelo menos metade dos cenários | Cheia provável ou em curso nas zonas baixas (zonas 1 e 2) |

Os limites vêm de 25 anos de caudal (1997 a 2021). Na cheia de Janeiro de 2026, as regras
teriam dado laranja 4 a 5 dias antes do primeiro mapa de cheia.

## O que fazer (texto que segue na mensagem)

| Nível | Português | Língua local (a preencher) |
|---|---|---|
| Verde | Sem sinais de cheia nos próximos dias. Não é preciso fazer nada de especial. | |
| Amarelo | Atenção. Acompanhe os próximos boletins. Quem vive ou trabalha nas zonas baixas junto ao rio deve rever para onde ir e o que levar se a água subir. | |
| Laranja | Preparação. Proteja documentos, alimentos e bens em local alto; leve o gado para terreno elevado; evite atravessar o rio e as zonas baixas. Siga as indicações do INGD e das autoridades locais. | |
| Vermelho | Cheia provável ou em curso nas zonas baixas junto ao Incomáti. Siga de imediato as ordens das autoridades, incluindo a de sair de casa. Não atravesse zonas alagadas a pé nem de carro. | |

## Qualidade da água

| Situação | Português | Língua local (a preencher) |
|---|---|---|
| Água mais turva do que o habitual | Água do rio mais turva do que o habitual. Deixe assentar, filtre por um pano limpo e ferva ou use cloro antes de beber. | |
| Sempre | A água do rio deve ser sempre tratada antes de beber. | |

O satélite vê a cor da água. Não vê bactérias nem químicos. Por isso as mensagens **nunca**
dizem que a água é segura ou insegura.

## Forma da mensagem

1. Primeiro o nível, com a cor e a palavra (há pessoas que não distinguem cores).
2. Até quando vale e qual é o dia mais crítico.
3. O que fazer, numa ou duas frases.
4. Onde: os nomes dos lugares que alagam primeiro.
5. No fim, sempre: "Aviso experimental. Não substitui o INGD, o INAM e a ARA-Sul."

A mensagem é gerada todos os dias em `plataforma/dados/boletim/mensagem_whatsapp.txt` e tem
menos de 900 caracteres. Exemplos reais em `docs/teste_alerta_ponta_a_ponta.md`.

## Regras

- **Nunca "verde" sem dados.** Se a previsão falhar, a mensagem diz que não foi possível
  fazer a previsão e remete para os avisos oficiais.
- **Não alterar os textos de "o que fazer" sem rever com a protecção civil local.**
- **Só enviar a quem deu consentimento** para estar no canal (tarefa W3-10).
- **Os nomes dos lugares** vêm de mapas públicos e ainda não foram validados no terreno.
- **Cores e ícones** (tarefa W3-13): verde #27ae60, amarelo #f1c40f, laranja #e67e22,
  vermelho #c0392b, as mesmas da plataforma.

## Por decidir pela equipa

- Quem envia a mensagem, a que horas, e quem a substitui quando está ausente.
- Se a mensagem verde é enviada todos os dias ou só uma vez por semana.
- Quem valida a tradução e com quantas pessoas é testada.
