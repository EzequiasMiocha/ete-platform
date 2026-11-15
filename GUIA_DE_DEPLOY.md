# Guia de deploy da plataforma ETE

Projecto Eyes to Earth. Para quem publica e mantém a plataforma (a equipa técnica do projecto).

## Como fica montado

```
   GitHub (repositório ete-platform)
   ├── todos os dias às 05:15: faz a previsão, o boletim, a mensagem e a página
   │   e guarda tudo no próprio repositório              (GitHub Actions, grátis)
   ├── plataforma/  ──────────►  aplicação Streamlit     (Streamlit Community Cloud, grátis)
   └── docs/index.html  ──────►  página leve do boletim  (GitHub Pages, grátis)
```

- **Nenhum computador da equipa precisa de estar ligado.** O boletim corre nos servidores do GitHub.
- **A aplicação** actualiza-se sozinha sempre que o repositório muda.
- **A página leve** é a reserva: abre com pouca rede e não adormece. Se o boletim tiver mais
  de 36 horas, tanto a página como a aplicação dizem "previsão indisponível", nunca verde.
- **O computador do projecto** só é preciso para o que usa o Earth Engine: as imagens de cor
  da água (uma vez por semana) e o Módulo Q (uma vez por mês).

## Publicar pela primeira vez (cerca de 20 minutos)

### 1. Criar o repositório no GitHub e dar acesso a este computador

1. Entrar em https://github.com com a conta da equipa.
2. **New repository**. Nome: `ete-platform`. Visibilidade: **Public** (é o que permite usar
   o GitHub Pages e o Streamlit grátis). Não marcar README, .gitignore nem licença. **Create repository**.
3. No repositório: **Settings > Deploy keys > Add deploy key**. *Title*: `computador do projecto`.
   *Key*: o conteúdo de `~/.ssh/ete_github_deploy.pub` (uma linha que começa por `ssh-ed25519`).
   Marcar **Allow write access**. **Add key**.

Esta **chave de publicação** só abre este repositório (não dá acesso ao resto da conta) e evita
palavras-passe e *tokens*. No computador do projecto já existe, com o nome curto `github-ete` em
`~/.ssh/config`. Noutro computador, criá-la assim e acrescentar a chave nova no GitHub:

```bash
ssh-keygen -t ed25519 -N "" -C "chave de publicação ete-platform" -f ~/.ssh/ete_github_deploy
printf '\nHost github-ete\n    HostName github.com\n    User git\n    IdentityFile ~/.ssh/ete_github_deploy\n    IdentitiesOnly yes\n' >> ~/.ssh/config
```

### 2. Publicar (um só comando, também para todas as actualizações)

```bash
.venv/bin/python scripts/publicar_plataforma.py
```

Na primeira vez, o comando descobre sozinho o repositório (a chave só abre um) e guarda-o. Depois,
sempre: traz o que está publicado (com os boletins que o GitHub guardou), remonta o pacote a partir
do projecto, verifica o pacote de dados e todas as páginas nas três línguas, e só então regista e
envia. Se uma verificação falhar, não envia nada. Na primeira vez são cerca de 8 MB; depois, só o
que mudou. Para ver se está tudo bem sem enviar: `--verificar`. Para uma mensagem própria: `-m "..."`.

### 3. Ligar o boletim diário

1. **Actions > Boletim diário > Run workflow** (o botão à direita) e, na janela pequena, o botão
   verde **Run workflow**. Ao fim de 3 a 5 minutos deve ficar verde, e aparece um novo *commit*
   "Boletim de AAAA-MM-DD". Se o separador **Actions** mostrar um aviso, carregar primeiro em
   **I understand my workflows, enable them**.
2. Não é preciso mudar permissões: o fluxo pede ele próprio licença para guardar o boletim
   (`permissions: contents: write`). Só se o passo "Guardar no repositório" falhar com o erro 403:
   **Settings > Actions > General > Workflow permissions > Read and write permissions > Save**.
3. Os alertas no WhatsApp só saem quando o repositório tiver os segredos `WHATSAPP_TOKEN`,
   `WHATSAPP_PHONE_ID`, `SUPABASE_URL` e `SUPABASE_SERVICE_KEY` (**Settings > Secrets and variables >
   Actions**). Sem eles, o boletim, a página e a aplicação funcionam na mesma.

### 4. Ligar a página leve

**Settings > Pages**: em *Source* escolher **Deploy from a branch**; *Branch* `main`, pasta
`/docs`; **Save**. Ao fim de um ou dois minutos a página fica em
`https://<conta>.github.io/ete-platform/`.

### 5. Publicar a aplicação

1. Entrar em https://share.streamlit.io com a mesma conta GitHub.
2. **Create app > Deploy a public app from GitHub**.
3. *Repository*: `<conta>/ete-platform`. *Branch*: `main`. *Main file path*: `plataforma/app.py`.
4. Em **Advanced settings**, escolher Python 3.12 ou mais recente (a aplicação só precisa
   das bibliotecas de `plataforma/requirements.txt`, que não dependem dos modelos).
5. *App URL*: escolher um nome, por exemplo `ete-platform` (o que está publicado). **Deploy**.

### 6. Dizer à plataforma os seus endereços

No projecto principal, em `config/config.yaml`, secção `publication`:

```yaml
publication:
  app_url: "https://ete-platform.streamlit.app"
  page_url: "https://<conta>.github.io/ete-platform/"
```

Depois, publicar a alteração (ver "Enviar alterações" abaixo). A página leve passa a ter a
ligação para a aplicação, e a aplicação para a página leve.

## Manter

| Tarefa | Quando | Como |
|---|---|---|
| Boletim, mensagem, página | todos os dias | automático (GitHub) |
| Ver se o boletim correu | todos os dias, de relance | separador **Actions**: verde = correu. O GitHub envia um email quando falha |
| Imagens de cor da água, o mapa da cor da água e a fotografia do satélite | uma vez por semana | no computador do projecto: `scripts/update_water_quality_scenes.py` (1 a 2 MB; também põe o mapa e a fotografia no pacote e actualiza a cor de Marracuene, o ponto de partida da previsão a 30 dias), e enviar |
| Previsão da cor da água a 30 dias | todos os dias | automático (GitHub): `boletim/cor_prevista.csv`; a aplicação desenha os mapas das 4 semanas |
| Módulo Q e mapa de radar do mês | uma vez por mês | `scripts/update_module_q_series.py`, `scripts/export_platform_package.py`, e enviar |
| Acordar a aplicação | antes de uma demonstração | abrir o endereço; se estiver adormecida, carregar no botão e esperar |

### Enviar alterações do projecto para a plataforma

Fazer as alterações no projecto (`plataforma/`, `src/`, `config/`), nunca em `deploy/` (é gerado), e depois:

```bash
.venv/bin/python scripts/publicar_plataforma.py -m "O que mudou"
```

O comando traz primeiro os boletins que o GitHub guardou, por isso o envio não é recusado por isso.

## Quando algo corre mal

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| A aplicação e a página dizem "previsão indisponível" | o boletim não corre há mais de 36 horas | **Actions > Boletim diário**: ver o erro; correr à mão com **Run workflow** |
| O boletim falha em "Previsão" | o serviço de previsão (Open-Meteo) esteve em baixo | normalmente resolve-se no dia seguinte; pode correr-se à mão mais tarde |
| O boletim falha em "Guardar no repositório" | falta a permissão do passo 3.1 | **Settings > Actions > General > Read and write permissions** |
| A aplicação mostra "This app has gone to sleep" | ficou muito tempo sem visitas | carregar em **Yes, get this app back up** |
| A aplicação dá erro ao arrancar | versão de uma biblioteca | **Manage app > Reboot**; se continuar, ver os *logs* e o resultado de **Actions > Testes** |
| O boletim automático deixou de correr sem erro nenhum | o GitHub suspende tarefas agendadas de repositórios parados há muito tempo | **Actions > Boletim diário > Enable workflow** |
| O comando de publicar diz que o envio foi recusado | o GitHub guardou um boletim no mesmo minuto | voltar a correr o comando |
| O comando de publicar diz que o GitHub não aceita a chave | a chave de publicação não está no repositório, ou sem escrita | **Settings > Deploy keys**: acrescentar `~/.ssh/ete_github_deploy.pub` com **Allow write access** |

## O que este desenho não resolve

- **A turbidez prevista e o mapa da cor da água dependem das imagens semanais.** Se ninguém as
  actualizar durante mais de 30 dias, a previsão de turbidez continua, com menos acerto, e a
  plataforma diz de quando é a última medição e a data da imagem do mapa.
- **Os logótipos vão dentro da própria página.** O Streamlit Cloud respondeu "erro interno" aos
  ficheiros de `app/static` (14/11/2026); por isso a plataforma não depende desse serviço.
- **Sem garantia de serviço.** São serviços gratuitos: podem estar lentos ou em baixo, sobretudo
  com muitas visitas ao mesmo tempo. Por isso a mensagem para os líderes e a página leve
  existem ao lado da aplicação.
- **O envio da mensagem aos líderes não é automático.** A mensagem é gerada todos os dias
  (`plataforma/dados/boletim/mensagem_whatsapp.txt`); alguém da equipa tem de a enviar.
- **Antes de divulgar o endereço:** coordenar com o INGD, o INAM e a ARA-Sul, e confirmar as
  condições de uso do serviço de previsão (Open-Meteo) para um serviço público.
