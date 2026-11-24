# Alertas de cheia no WhatsApp

Quem visita a plataforma pode deixar o número de WhatsApp e o lugar onde vive. Quando o alerta de
cheia for **laranja ou vermelho**, a pessoa recebe uma mensagem curta com o nível, pelo menos dois
lugares que podem alagar (o dela primeiro, se estiver em risco), o que fazer e a ligação para a
plataforma. Quando o perigo passa, recebe uma mensagem de fim de alerta.

## Como funciona, passo a passo

1. **Inscrição** (na plataforma): janela de convite na primeira visita, página **Alertas** e botão
   "Receber alertas no WhatsApp" na barra do topo. Pede o número, onde vive, a língua (PT, EN, FR),
   o nome completo (obrigatório: as mensagens tratam a pessoa pelo nome) e um "Aceito" obrigatório.
   Quem tem conta na plataforma (plataforma/contas.py) encontra o formulário já preenchido. Quem quer sair escreve o número na mesma página.
2. **Todas as manhãs**, depois do boletim, o pipeline diário corre `scripts/send_whatsapp_alerts.py`:
   - só com um boletim válido (nunca com dados antigos);
   - alerta laranja ou vermelho: mensagem de alerta a todos os inscritos;
   - se o nível subir, nova mensagem logo; se o alerta durar, um lembrete de 2 em 2 dias;
   - quando o nível desce abaixo de laranja: mensagem de fim de alerta;
   - quem se inscreveu desde a véspera e ainda não recebeu as boas-vindas recebe-as (e o alerta, se houver um em curso).
     Com a API ligada também no Streamlit Cloud, as boas-vindas saem logo no momento da inscrição.
3. O registo do que foi enviado fica em `plataforma/dados/boletim/avisos_whatsapp.json`: datas,
   níveis e quantidades, **nunca números de telefone**.

As regras (que níveis avisam, de quantos em quantos dias o lembrete) estão em `config/config.yaml`,
na secção `whatsapp`.

## Conselho próprio para cada tipo de pessoa

Sexo, idade e profissão são opcionais no formulário. Quando a pessoa os indica, o alerta junta ao
conselho do nível uma frase a mais (a idade conta primeiro, depois a profissão):

| Quem | Frase a mais |
|---|---|
| 60 anos ou mais | Se precisar de ajuda para sair de casa, combine já com um vizinho ou familiar. |
| Menos de 18 anos | Fique junto da sua família e siga as instruções dos adultos e das autoridades. |
| Agricultor(a) | Leve o gado e guarde as sementes e a colheita em lugar alto. |
| Pescador(a) | Não vá ao rio de barco enquanto durar o alerta. |
| Comerciante | Guarde a mercadoria em lugar alto. |
| Professor(a) | Combine com a escola como avisar as famílias dos alunos. |
| Motorista / transportador(a) | Não atravesse estradas nem pontes cobertas de água. |
| Líder comunitário / protecção civil | Partilhe este aviso com a sua comunidade (e a sua equipa). |

As frases estão em `plataforma/alertas_whatsapp.py` (`DICAS`), nas três línguas. Convém que a equipa
e o INGD as revejam antes de abrir as inscrições ao público.

## Ficheiro Excel para acompanhar os subscritores

```bash
.venv/bin/python scripts/ver_subscritores.py --excel
```

Cria `data/private/subscritores_AAAA-MM-DD.xlsx` com quatro folhas:
- **Subscritores**: uma linha por pessoa, todas as variáveis, respostas por extenso, com filtros;
- **Resumo**: inscrições activas, saídas, alertas enviados, e contagens e percentagens por sexo,
  idade, profissão, lugar e língua (com gráficos por idade e por profissão);
- **Envios**: cada alerta enviado (data, tipo, nível, quantas pessoas, modo);
- **Dicionário**: o que quer dizer cada coluna e os valores possíveis.

O ficheiro tem números de telefone: é só para a equipa e não deve ser partilhado.

## Dois modos de envio

| Modo | Quando | O que acontece |
|---|---|---|
| **Envio assistido** | Enquanto a API do WhatsApp não está pronta. Só no computador do projecto. | É criada uma página em `data/private/caixa_de_saida/` com um botão por pessoa. Alguém da equipa abre a página num telefone ou computador com WhatsApp e carrega em cada botão: o WhatsApp abre com a mensagem já escrita, basta enviar. Serve para um piloto com dezenas de pessoas. Apagar a página depois de enviar. |
| **Automático (API oficial)** | Quando `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID` estão definidos. | As mensagens saem sozinhas, pelos servidores da Meta, com os modelos aprovados abaixo. Funciona também no GitHub Actions. |

Nos servidores do GitHub o envio assistido não corre: os números ficariam num servidor partilhado.

Para ver o que seria enviado hoje, sem enviar nem gravar nada:

```bash
.venv/bin/python scripts/send_whatsapp_alerts.py --ensaio
```

## Onde ficam os dados: a base de dados `subscritores`

Tudo o que as pessoas escrevem no formulário vai para uma única tabela, **`subscritores`**:

| Coluna | O que guarda |
|---|---|
| `id` | identificador da inscrição |
| `criado_utc` | quando a pessoa se inscreveu |
| `nome` | nome completo (usado no início de cada mensagem) |
| `telefone` | número de WhatsApp, formato internacional sem "+" (258841234567) |
| `lugar` | bairro ou lugar escolhido (vazio = "outro lugar / não sei") |
| `lingua` | pt, en ou fr |
| `sexo` | mulher, homem ou vazio (prefere não dizer) — opcional |
| `faixa_etaria` | menos_18, 18_29, 30_44, 45_59, 60_mais ou vazio — opcional |
| `profissao` | agricultor, pescador, comerciante, estudante, professor, saude, funcionario, lider, protecao_civil, transporte, domestico, desempregado, reformado, outra, ou vazio — opcional |
| `consentimento` | quando marcou "Aceito" |
| `estado` | `activa` ou `removido` |
| `boas_vindas_utc` | quando recebeu a mensagem de boas-vindas |
| `removido_utc` | quando pediu para sair |
| `ultimo_envio_utc` | quando recebeu o último alerta ou fim de alerta |
| `envios` | quantos alertas e fins de alerta já recebeu |

A tabela existe em dois sítios, conforme a definição `ETE_SUBSCRITORES`:

| Onde | Quando | Como se vê |
|---|---|---|
| **SQLite**, no computador do projecto: `data/private/subscritores.db` (por defeito) | Testes e envio a partir do computador | `.venv/bin/python scripts/ver_subscritores.py` |
| **Supabase**, uma base de dados Postgres na internet (plano gratuito) | Plataforma publicada e envio diário no GitHub | No painel do Supabase: Table Editor > `subscritores`; ou o mesmo comando com `ETE_SUBSCRITORES=supabase` no `.env` |

A pasta `data/private/` nunca vai para o Git. No Streamlit Community Cloud o disco do servidor
apaga-se quando a aplicação reinicia, por isso a plataforma publicada tem de usar o Supabase.
Enquanto não estiver configurado, o formulário diz "As inscrições abrem em breve" em vez de aceitar
números que se perderiam.

Criar a base no Supabase (uma vez, cerca de 10 minutos):
1. Criar uma conta em supabase.com e um projecto novo (região mais próxima: a de África do Sul, se existir na lista).
2. No painel, "SQL Editor": colar o conteúdo de `docs/subscritores.sql` e carregar em "Run". Cria a tabela `subscritores` fechada ao público.
3. Em "Project Settings > API", copiar o **Project URL** e a chave **service_role** (secreta).
4. Pôr nos segredos do Streamlit (Settings > Secrets) e nos segredos do GitHub (Settings > Secrets and variables > Actions):
   `ETE_SUBSCRITORES = "supabase"`, `SUPABASE_URL = "<Project URL>"`, `SUPABASE_SERVICE_KEY = "<chave service_role>"`.
   No computador, as mesmas três linhas no ficheiro `.env`.

A chave service_role dá acesso total à base: nunca a pôr no código, no repositório nem em mensagens.
No plano gratuito, o Supabase pausa projectos sem actividade durante uma semana; o envio diário lê
a tabela todas as manhãs e mantém-no activo.

Para retirar alguém à mão: no Table Editor, mudar `estado` para `removido`.

## As mensagens (versão 2)

Cada mensagem traz no topo o **cartão de situação** do dia (`plataforma/cartao_whatsapp.py`):
uma imagem com o nível de cheia em grande, a **quantidade** de água (o caudal previsto para 10 dias,
com o limite amarelo) e a **qualidade** (a cor da água prevista em Marracuene, um quadrado por dia).
Por baixo, o texto, só com palavras (sem emojis), que começa pelo nome completo da pessoa («Olá, Ana Cossa!»,
«Atenção, Ana Cossa: ALERTA LARANJA…», «Boas notícias, Ana Cossa: terminou o alerta…»; a quem se inscreveu
antes de o nome ser pedido, «amigo(a)»), e dois botões: **Ver a previsão completa**, que abre a página
do lugar da pessoa na plataforma (`?p=zona&lugar=...`), e **Deixar de receber**.

| Mensagem | Quando | O que diz |
|---|---|---|
| Boas-vindas | **logo** depois da inscrição (com a API ligada; senão, na corrida da manhã seguinte) | cheias nos próximos 10 dias (em palavras, com as datas: «verde até 18/11, laranja de 19/11 a 24/11»), a cor da água, o que a cheia de 2026 fez ao lugar da pessoa e um conselho para o seu perfil |
| Alerta | laranja ou vermelho; de 2 em 2 dias enquanto durar; logo se subir | nível e dia, pelo menos dois lugares que podem alagar (o da pessoa primeiro), o que fazer (com o conselho do perfil), os 10 dias em palavras, com as datas, a cor da água |
| Fim do alerta | quando o nível desce abaixo de laranja | fim do alerta, a cor da água e o cuidado com a água depois de uma cheia |

A página **Alertas** da plataforma mostra a mensagem de boas-vindas exactamente como chega, com os
números de hoje. No envio assistido (sem API) o texto leva as ligações escritas no fim e a página
da equipa mostra o cartão ao lado de cada mensagem, para o anexar à mão.

## Ligar o envio automático (WhatsApp Business Cloud API)

O WhatsApp só deixa uma empresa escrever primeiro a alguém com **modelos de mensagem aprovados**.

1. Criar uma conta Meta Business (business.facebook.com) e, em developers.facebook.com, uma app do tipo "Business" com o produto **WhatsApp**.
2. Juntar um número de telefone do projecto que **não** esteja já a ser usado na aplicação WhatsApp normal (pode ser um cartão novo).
3. Submeter os três modelos de `docs/modelos_whatsapp.md` (gerado por `scripts/modelos_whatsapp.py`), categoria **Utility**,
   nas três línguas, com os nomes exactos, o cabeçalho de imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`) e os dois botões.
4. Criar um token permanente (System User) com a permissão `whatsapp_business_messaging`.
5. Pôr `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID` (o "Phone number ID", não o número):
   - nos **segredos do Streamlit Cloud** (share.streamlit.io > a app > Settings > Secrets), para a boas-vindas sair no momento da inscrição;
   - nos **segredos do GitHub** (Settings > Secrets and variables > Actions), para os alertas da manhã;
   - no `.env` do computador do projecto.
6. O endereço da plataforma nas mensagens vem de `publication.app_url` em `config/config.yaml`.

**Custos.** A Meta cobra cada mensagem de modelo entregue, com um preço por região e por categoria.
Moçambique está na região "Resto de África"; tabelas de terceiros indicam cerca de **0,004 USD por
mensagem Utility** (e 5 a 6 vezes mais para Marketing). Com 1000 inscritos: cerca de 4 USD por cada
alerta enviado a todos, mais 0,004 USD por cada boas-vindas. Confirmar na tabela oficial
(developers.facebook.com/docs/whatsapp/pricing) antes de abrir as inscrições ao público. O envio
assistido não tem custo além dos dados do telefone.

## Privacidade e boas práticas

- Só se guarda o necessário: número, lugar, língua, nome completo e a data do consentimento.
- Os números nunca aparecem na plataforma, nunca vão para o GitHub e nunca ficam nos registos de envio.
- Quem sai deixa de receber no envio seguinte. O pedido para sair é feito na página Alertas, com o número.
- Não usar a lista para outro fim (por exemplo, publicidade). Só alertas de cheia.
- Não usar programas não oficiais que automatizam o WhatsApp do telefone: violam as regras do
  WhatsApp e o número do projecto pode ser bloqueado.

## Ficheiros

| O quê | Onde |
|---|---|
| Base de dados `subscritores` (SQLite ou Supabase) e regras dos números | `plataforma/inscricoes.py` |
| Criar a tabela no Supabase | `docs/subscritores.sql` |
| Ver os subscritores e criar o Excel | `scripts/ver_subscritores.py` (`--excel`) e `plataforma/relatorio_subscritores.py` |
| Decidir, escrever e enviar | `plataforma/alertas_whatsapp.py` |
| Comando diário | `scripts/send_whatsapp_alerts.py` (chamado pelo `scripts/run_daily_pipeline.py`, passo 5) |
| Página e convite na plataforma | `plataforma/app.py` (`pagina_alertas`, `convite_alertas`) |
| Teste (simula uma cheia inteira, sem enviar nada) | `cd plataforma && python testar_alertas.py` |
