# Alertas de cheia no WhatsApp

Quem visita a plataforma pode deixar o número de WhatsApp e o lugar onde vive. Quando o alerta de
cheia for **laranja ou vermelho**, a pessoa recebe uma mensagem curta com o nível, pelo menos dois
lugares que podem alagar (o dela primeiro, se estiver em risco), o que fazer e a ligação para a
plataforma. Quando o perigo passa, recebe uma mensagem de fim de alerta.

## Como funciona, passo a passo

1. **Inscrição** (na plataforma): janela de convite na primeira visita, página **Alertas** e botão
   "Receber alertas no WhatsApp" na barra do topo. Pede o número, onde vive, a língua (PT, EN, FR),
   o nome (opcional) e um "Aceito" obrigatório. Quem quer sair escreve o número na mesma página.
2. **Todas as manhãs**, depois do boletim, o pipeline diário corre `scripts/send_whatsapp_alerts.py`:
   - só com um boletim válido (nunca com dados antigos);
   - alerta laranja ou vermelho: mensagem de alerta a todos os inscritos;
   - se o nível subir, nova mensagem logo; se o alerta durar, um lembrete de 2 em 2 dias;
   - quando o nível desce abaixo de laranja: mensagem de fim de alerta;
   - quem se inscreveu desde a véspera recebe as boas-vindas (e o alerta, se houver um em curso).
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
| `nome` | nome (opcional) |
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

## Ligar o envio automático (WhatsApp Business Cloud API)

O WhatsApp só deixa uma empresa escrever primeiro a alguém com **modelos de mensagem aprovados**.

1. Criar uma conta Meta Business (business.facebook.com) e, em developers.facebook.com, uma app do tipo "Business" com o produto **WhatsApp**.
2. Juntar um número de telefone do projecto que **não** esteja já a ser usado na aplicação WhatsApp normal (pode ser um cartão novo).
3. Submeter os três modelos abaixo, na categoria **Utility**, nas línguas indicadas, com os nomes exactos.
4. Criar um token permanente (System User) com a permissão `whatsapp_business_messaging`.
5. Pôr nos segredos do GitHub e no `.env` do computador: `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID` (o "Phone number ID", não o número).
6. Preencher `publication.app_url` em `config/config.yaml` com o endereço da plataforma: é a ligação que vai nas mensagens.

**Custos.** A Meta cobra cada mensagem de modelo enviada, com um preço por país e por categoria
(Utility). Ver a tabela em vigor para Moçambique em developers.facebook.com/docs/whatsapp/pricing
antes de abrir as inscrições ao público. O envio assistido não tem custo além dos dados do telefone.
Cada envio usa poucos KB de internet.

## Modelos para submeter à Meta

Os textos abaixo são gerados a partir de `plataforma/alertas_whatsapp.py` (`TEXTOS_MENSAGEM`). Se
um texto mudar no código, o modelo tem de ser submetido de novo com o mesmo texto.

### `ete_alerta_cheia`

Variáveis: `{{1}}` = nível (LARANJA), `{{2}}` = dia (18/10), `{{3}}` = lugares (Machubo, Macaneta, Pateque), `{{4}}` = o que fazer, `{{5}}` = ligação para a plataforma, `{{6}}` = ligação para deixar de receber

**pt_PT**

```
⚠️ Eyes to Earth · ALERTA {{1}} de cheia no rio Incomáti, a partir de {{2}}.
📍 Lugares que podem alagar: {{3}}.
✅ O que fazer: {{4}}
ℹ️ Mais informação: {{5}}
Para deixar de receber: {{6}}
Siga sempre as ordens do INGD e das autoridades.
```

**en**

```
⚠️ Eyes to Earth · {{1}} flood ALERT on the Incomati River, from {{2}}.
📍 Places that may flood: {{3}}.
✅ What to do: {{4}}
ℹ️ More information: {{5}}
To stop these messages: {{6}}
Always follow the orders of INGD and the authorities.
```

**fr**

```
⚠️ Eyes to Earth · ALERTE {{1}} de crue sur le fleuve Incomati, à partir du {{2}}.
📍 Lieux qui peuvent être inondés : {{3}}.
✅ Que faire : {{4}}
ℹ️ Plus d'informations : {{5}}
Pour ne plus recevoir ces messages : {{6}}
Suivez toujours les ordres de l'INGD et des autorités.
```

### `ete_fim_alerta`

Variáveis: `{{1}}` = data (25/10), `{{2}}` = ligação para a plataforma

**pt_PT**

```
🟢 Eyes to Earth · Fim do alerta de cheia no rio Incomáti ({{1}}). O boletim de hoje já não prevê cheia.
Mais informação: {{2}}
Continue atento às autoridades.
```

**en**

```
🟢 Eyes to Earth · End of the flood alert on the Incomati River ({{1}}). Today's bulletin no longer forecasts a flood.
More information: {{2}}
Keep listening to the authorities.
```

**fr**

```
🟢 Eyes to Earth · Fin de l'alerte de crue sur le fleuve Incomati ({{1}}). Le bulletin du jour ne prévoit plus de crue.
Plus d'informations : {{2}}
Restez attentifs aux autorités.
```

### `ete_boas_vindas`

Variáveis: `{{1}}` = lugar da pessoa (Machubo), `{{2}}` = ligação para a plataforma, `{{3}}` = ligação para deixar de receber

**pt_PT**

```
👋 Olá! Está inscrito nos alertas de cheia do Eyes to Earth para {{1}}. Só lhe escrevemos quando houver perigo de cheia no rio Incomáti (alerta laranja ou vermelho) e quando o perigo passar.
Plataforma: {{2}}
Para deixar de receber: {{3}}
Obrigado!
```

**en**

```
👋 Hello! You are signed up for Eyes to Earth flood alerts for {{1}}. We only write when there is a danger of flooding on the Incomati River (orange or red alert) and when the danger is over.
Platform: {{2}}
To stop these messages: {{3}}
Thank you!
```

**fr**

```
👋 Bonjour ! Vous êtes inscrit aux alertes de crue d'Eyes to Earth pour {{1}}. Nous n'écrivons qu'en cas de danger de crue sur le fleuve Incomati (alerte orange ou rouge) et quand le danger est passé.
Plateforme : {{2}}
Pour ne plus recevoir ces messages : {{3}}
Merci !
```

## Privacidade e boas práticas

- Só se guarda o necessário: número, lugar, língua, nome (opcional) e a data do consentimento.
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
