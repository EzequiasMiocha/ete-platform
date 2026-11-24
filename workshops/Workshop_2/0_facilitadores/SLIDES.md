# Slides do Workshop 2

**Apresentação (99 slides, com notas do orador):** https://claude.ai/artifact/TCrXDZeA8uTCHr5R6ZmSbq

**Módulo 2 refeito, num deck à parte (19 slides, 09:05–09:55, Facilitador 2):** https://claude.ai/artifact/5yoVWyumH2qVSGTKEqnBuu
Uma versão leve, para quem nunca ouviu falar de modelos de IA: aprender com exemplos (cães e gatos, burlas no WhatsApp),
treinar e prever, as três formas de aprender, a árvore e a floresta com dois jogos, a regressão, e quatro ligações ao
projecto (a imagem de satélite, o mapa da água da Aula 1, o caudal do rio e as três perguntas da plataforma). Gerado por
`scripts/build_workshop2_modulo2.py`. Ainda não substitui os slides do Módulo 2 do deck principal.

O artefacto é privado: só abre para quem o criou. Para a equipa o ver, abrir o link e usar o menu **Partilhar**.

## Como usar

- **Apresentar:** abrir o link e escolher o modo de apresentação. As notas do orador (o texto a dizer, as respostas das
  actividades e os tempos) aparecem na vista do apresentador.
- **Sem Internet no dia:** exportar antes em PDF e em PowerPoint (menu Partilhar, Exportar) e levar no pen drive.
- **Uma ideia por slide:** cada slide tem pouco texto (cerca de 60 palavras em média) e letra grande; o que o
  facilitador diz está nas notas. No quiz, cada pergunta tem o seu slide e a resposta aparece no clique seguinte (o mesmo
  na pergunta de verificação do Módulo 3).
- **Antes do workshop, trocar:** os QR dos questionários OAD (slides 5 e 98) e o contacto
  do projecto (slide 99). O endereço da plataforma (ete-platform.streamlit.app) já está nos slides.
- **Estilo:** fundo branco e visual académico, sem azul: títulos a preto, linha vermelho-escuro (#A51C30) por baixo do
  título, destaques a vermelho-escuro, cabeçalhos das tabelas a preto, rodapé com a secção e o número do slide, figuras e
  tabelas numeradas com a fonte dos dados. O azul só aparece onde representa a água (mapas e gráficos de píxeis).
- **Letra:** os títulos usam a Archivo Black, a versão web da Arial Black (o leitor de slides só aceita fontes web ou
  básicas e trocava a Arial Black por Arial normal); o texto usa Arial. No PowerPoint exportado, para pôr a Arial Black:
  separador Base, Substituir, Substituir Tipos de Letra, de Archivo Black para Arial Black.

## Secções

| Slides | Secção | Quem |
| --- | --- | --- |
| 1–9 | Abertura, programa, questionário OAD e revisão do Workshop 1 | Moderadora + Facilitador 1 |
| 10–19 | Módulo 1 · O que é a Inteligência Artificial? | Facilitador 1 |
| 20–44 | Módulo 2 · Como uma máquina aprende (supervisionada, não supervisionada, por reforço; 4 algoritmos) | Facilitador 2 |
| 45–50 | Quiz relâmpago (uma pergunta por slide) | Moderadora |
| 51–66 | Módulo 3 · Como sabemos se o modelo é bom? (com os hiperparâmetros) | Facilitador 5 |
| 67–74 | Módulo 4 · A IA e a qualidade da água | Facilitador 3 |
| 75–82 | Módulo 5 · A plataforma EYES TO EARTH | Facilitador 4 |
| 83–91 | Intervalo e prática (quatro temas, cada um com aula guiada e prática) | Facilitador 5 |
| 92–95 | Apresentações e resultados | Facilitador 5 |
| 96–99 | Encerramento | Moderadora |

As imagens dos slides estão em `imagens_para_slides/` (geradas por `scripts/workshop2/figuras.py` e, as da teoria,
por `scripts/workshop2/figuras_teoria.py`).

## Como o deck é feito

O deck é gerado pelo código do projecto, como o resto do material: `scripts/build_workshop2_slides.py` escreve-o em
`reports/apresentacao/workshop2_slides/project/`. O conteúdo está em `scripts/workshop2/slides.py`, as notas fixas em
`slides_notas.py` (as notas com números vêm das respostas de referência) e a ordem em `slides_ordem.py`, que é também a
fonte dos números dos slides citados no plano, no manual e no cronograma em Word. O script verifica as regras do deck:
letra de 24 px ou mais, sem azul fora da água, sem emoji, notas com 4 000 caracteres no máximo, figuras numeradas.
