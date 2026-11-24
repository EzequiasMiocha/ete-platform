# Modelos de mensagem do WhatsApp para submeter à Meta

Gerado por `scripts/modelos_whatsapp.py` a partir de `plataforma/alertas_whatsapp.py`. Não editar à mão.

Todos os modelos: categoria **Utility**; cabeçalho **Imagem** (o cartão de situação do dia, 1200 x 628 px, enviado pela
plataforma); rodapé fixo; dois botões **Visit website** com a parte final do endereço variável.

O botão 1 abre a página do lugar de cada pessoa (por exemplo `?p=zona&lugar=Machubo&lang=pt`); a quem não escolheu
lugar, abre a primeira página. Os exemplos abaixo são os de quem não escolheu lugar.

| Modelo | Quando sai |
|---|---|
| `ete_boas_vindas_v2` | logo depois de a pessoa se inscrever na plataforma |
| `ete_alerta_cheia_v2` | quando o alerta é laranja ou vermelho (e de 2 em 2 dias enquanto durar, ou logo se subir) |
| `ete_fim_alerta_v2` | quando o nível desce abaixo de laranja |

## `ete_boas_vindas_v2`

Sai logo depois de a pessoa se inscrever na plataforma.

### Português (pt_PT)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Olá, {{1}}! A sua inscrição nos alertas do rio Incomáti para {{2}} está feita.

Cheias nos próximos 10 dias: {{3}}
Água do rio em Marracuene: {{4}}
{{5}}

Vamos escrever-lhe sempre que houver perigo de cheia, e quando o perigo passar. Para deixar de receber, use o botão em baixo.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (lugar): Machubo
- `{{3}}` (cheia): verde até 25/11, sem sinais de cheia (caudal de 14 a 32 m³/s).
- `{{4}}` (agua): muito mais turva do que o costume. Trate sempre a água antes de beber.
- `{{5}}` (pessoal): Machubo foi dos primeiros lugares a alagar na cheia de 2026. Se houver alerta: não vá ao rio de barco enquanto durar o alerta.

**Rodapé (Footer):** Eyes to Earth · não substitui os avisos do INGD

**Botão 1 (Visit website, dinâmico):** «Ver a previsão completa» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=pt`
**Botão 2 (Visit website, dinâmico):** «Deixar de receber» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=pt`

### English (en)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Hello, {{1}}! You are now signed up for the Incomati River alerts for {{2}}.

Floods in the next 10 days: {{3}}
River water at Marracuene: {{4}}
{{5}}

We will write to you whenever there is a danger of flooding, and when the danger is over. To stop these messages, use the button below.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (lugar): Machubo
- `{{3}}` (cheia): green until 25/11, no signs of flooding (flow 14 to 32 m³/s).
- `{{4}}` (agua): much muddier than usual. Always treat the water before drinking.
- `{{5}}` (pessoal): Machubo was among the first places to flood in 2026. If there is an alert: do not go on the river by boat while the alert lasts.

**Rodapé (Footer):** Eyes to Earth · does not replace INGD warnings

**Botão 1 (Visit website, dinâmico):** «See the full forecast» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=en`
**Botão 2 (Visit website, dinâmico):** «Stop these messages» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=en`

### Français (fr)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Bonjour, {{1}} ! Votre inscription aux alertes du fleuve Incomati pour {{2}} est faite.

Crues dans les 10 prochains jours : {{3}}
Eau du fleuve à Marracuene : {{4}}
{{5}}

Nous vous écrirons à chaque danger de crue, et quand le danger sera passé. Pour ne plus recevoir ces messages, utilisez le bouton ci-dessous.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (lugar): Machubo
- `{{3}}` (cheia): vert jusqu'au 25/11, aucun signe de crue (débit de 14 à 32 m³/s).
- `{{4}}` (agua): beaucoup plus trouble que d'habitude. Traitez toujours l'eau avant de la boire.
- `{{5}}` (pessoal): Machubo a été parmi les premiers lieux inondés en 2026. En cas d'alerte : n'allez pas sur le fleuve en bateau tant que l'alerte dure.

**Rodapé (Footer):** Eyes to Earth · ne remplace pas les alertes de l'INGD

**Botão 1 (Visit website, dinâmico):** «Voir la prévision complète» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=fr`
**Botão 2 (Visit website, dinâmico):** «Ne plus recevoir» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=fr`

## `ete_alerta_cheia_v2`

Sai quando o alerta é laranja ou vermelho (e de 2 em 2 dias enquanto durar, ou logo se subir).

### Português (pt_PT)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Atenção, {{1}}: ALERTA {{2}} de cheia no rio Incomáti, a partir de {{3}}.

Lugares que podem alagar: {{4}}.
O que fazer: {{5}}
Próximos 10 dias: {{6}}.
Água do rio: {{7}}

Siga sempre as ordens do INGD e das autoridades. Detalhes e mapa na plataforma.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (nivel): LARANJA
- `{{3}}` (dia): 21/11
- `{{4}}` (lugares): Machubo (onde vive), Macanda, Machavo
- `{{5}}` (conselho): Preparação. Proteja documentos, alimentos e bens em local alto; leve o gado para terreno elevado; evite atravessar o rio e as zonas baixas. Siga as indicações do INGD e das autoridades locais. Não vá ao rio de barco enquanto durar o alerta.
- `{{6}}` (linha_cheia): verde até 25/11
- `{{7}}` (agua): muito mais turva do que o costume. Trate sempre a água antes de beber.

**Rodapé (Footer):** Eyes to Earth · não substitui os avisos do INGD

**Botão 1 (Visit website, dinâmico):** «Ver a previsão completa» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=pt`
**Botão 2 (Visit website, dinâmico):** «Deixar de receber» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=pt`

### English (en)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Attention, {{1}}: FLOOD ALERT {{2}} on the Incomati River, from {{3}}.

Places that may flood: {{4}}.
What to do: {{5}}
Next 10 days: {{6}}.
River water: {{7}}

Always follow the orders of INGD and the authorities. Details and map on the platform.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (nivel): ORANGE
- `{{3}}` (dia): 21/11
- `{{4}}` (lugares): Machubo (where you live), Macanda, Machavo
- `{{5}}` (conselho): Get ready. Protect documents, food and belongings in a high place; take livestock to higher ground; avoid crossing the river and the low areas. Follow the instructions of INGD and the local authorities. Do not go on the river by boat while the alert lasts.
- `{{6}}` (linha_cheia): green until 25/11
- `{{7}}` (agua): much muddier than usual. Always treat the water before drinking.

**Rodapé (Footer):** Eyes to Earth · does not replace INGD warnings

**Botão 1 (Visit website, dinâmico):** «See the full forecast» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=en`
**Botão 2 (Visit website, dinâmico):** «Stop these messages» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=en`

### Français (fr)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Attention, {{1}} : ALERTE {{2}} de crue sur le fleuve Incomati, à partir du {{3}}.

Lieux qui peuvent être inondés : {{4}}.
Que faire : {{5}}
10 prochains jours : {{6}}.
Eau du fleuve : {{7}}

Suivez toujours les ordres de l'INGD et des autorités. Détails et carte sur la plateforme.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (nivel): ORANGE
- `{{3}}` (dia): 21/11
- `{{4}}` (lugares): Machubo (chez vous), Macanda, Machavo
- `{{5}}` (conselho): Préparation. Mettez documents, nourriture et biens en hauteur ; emmenez le bétail sur un terrain élevé ; évitez de traverser le fleuve et les zones basses. Suivez les consignes de l'INGD et des autorités locales. N'allez pas sur le fleuve en bateau tant que l'alerte dure.
- `{{6}}` (linha_cheia): vert jusqu'au 25/11
- `{{7}}` (agua): beaucoup plus trouble que d'habitude. Traitez toujours l'eau avant de la boire.

**Rodapé (Footer):** Eyes to Earth · ne remplace pas les alertes de l'INGD

**Botão 1 (Visit website, dinâmico):** «Voir la prévision complète» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=fr`
**Botão 2 (Visit website, dinâmico):** «Ne plus recevoir» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=fr`

## `ete_fim_alerta_v2`

Sai quando o nível desce abaixo de laranja.

### Português (pt_PT)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Boas notícias, {{1}}: terminou o alerta de cheia no rio Incomáti ({{2}}). O boletim de hoje já não prevê cheia.

Água do rio: {{3}}
Depois de uma cheia a água fica mais suja durante semanas: trate-a sempre antes de beber.

Continue atento às autoridades.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (data): 15/11
- `{{3}}` (agua): muito mais turva do que o costume. Trate sempre a água antes de beber.

**Rodapé (Footer):** Eyes to Earth · não substitui os avisos do INGD

**Botão 1 (Visit website, dinâmico):** «Ver a previsão completa» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=pt`
**Botão 2 (Visit website, dinâmico):** «Deixar de receber» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=pt`

### English (en)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Good news, {{1}}: the flood alert on the Incomati River has ended ({{2}}). Today's bulletin no longer forecasts a flood.

River water: {{3}}
After a flood the water stays dirtier for weeks: always treat it before drinking.

Keep listening to the authorities.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (data): 15/11
- `{{3}}` (agua): much muddier than usual. Always treat the water before drinking.

**Rodapé (Footer):** Eyes to Earth · does not replace INGD warnings

**Botão 1 (Visit website, dinâmico):** «See the full forecast» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=en`
**Botão 2 (Visit website, dinâmico):** «Stop these messages» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=en`

### Français (fr)

**Cabeçalho:** Imagem (exemplo: `plataforma/dados/modelos/exemplo_cartao_whatsapp.png`).

**Texto (Body):**

```
Bonne nouvelle, {{1}} : l'alerte de crue sur le fleuve Incomati est terminée ({{2}}). Le bulletin du jour ne prévoit plus de crue.

Eau du fleuve : {{3}}
Après une crue, l'eau reste plus sale pendant des semaines : traitez-la toujours avant de la boire.

Restez attentifs aux autorités.
```

**Exemplos das variáveis** (com os números de hoje):

- `{{1}}` (nome): Ana Cossa
- `{{2}}` (data): 15/11
- `{{3}}` (agua): beaucoup plus trouble que d'habitude. Traitez toujours l'eau avant de la boire.

**Rodapé (Footer):** Eyes to Earth · ne remplace pas les alertes de l'INGD

**Botão 1 (Visit website, dinâmico):** «Voir la prévision complète» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=inicio&lang=fr`
**Botão 2 (Visit website, dinâmico):** «Ne plus recevoir» → `https://ete-platform.streamlit.app/{{1}}` · exemplo: `?p=alertas&lang=fr`

