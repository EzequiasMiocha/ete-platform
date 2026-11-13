# Guia de deploy da plataforma ETE

Projecto Eyes to Earth. Para quem publica e mantém a plataforma (a equipa técnica do projecto).

## Como fica montado

```
   GitHub (repositório ete-plataforma)
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

### 1. Preparar a pasta

```bash
.venv/bin/python scripts/run_daily_pipeline.py      # boletim de hoje (poucos KB de internet)
.venv/bin/python scripts/build_deploy_repo.py       # monta deploy/ete-plataforma/
```

### 2. Criar o repositório no GitHub

1. Entrar em https://github.com com a conta da equipa.
2. **New repository**. Nome: `ete-plataforma`. Visibilidade: **Public** (é o que permite usar
   o GitHub Pages e o Streamlit grátis). Não marcar README nem .gitignore. **Create repository**.
3. No computador:

```bash
cd deploy/ete-plataforma
git add -A
git commit -m "Primeira versão da plataforma ETE"
git remote add origin https://github.com/<conta>/ete-plataforma.git
git push -u origin main
```

O GitHub pede o utilizador e um *token* (não a palavra-passe): em GitHub, **Settings >
Developer settings > Personal access tokens > Tokens (classic) > Generate new token**, com a
permissão `repo` e também `workflow` (sem esta, o envio dos ficheiros de automatização é recusado).

### 3. Ligar o boletim diário

1. No repositório: **Settings > Actions > General > Workflow permissions**: escolher
   **Read and write permissions** e guardar.
2. Separador **Actions**: se aparecer um aviso, carregar em **I understand my workflows, enable them**.
3. **Actions > Boletim diário > Run workflow**. Ao fim de 3 a 5 minutos deve ficar verde, e
   aparece um novo *commit* "Boletim de AAAA-MM-DD".

### 4. Ligar a página leve

**Settings > Pages**: em *Source* escolher **Deploy from a branch**; *Branch* `main`, pasta
`/docs`; **Save**. Ao fim de um ou dois minutos a página fica em
`https://<conta>.github.io/ete-plataforma/`.

### 5. Publicar a aplicação

1. Entrar em https://share.streamlit.io com a mesma conta GitHub.
2. **Create app > Deploy a public app from GitHub**.
3. *Repository*: `<conta>/ete-plataforma`. *Branch*: `main`. *Main file path*: `plataforma/app.py`.
4. Em **Advanced settings**, escolher Python 3.12 ou mais recente (a aplicação só precisa
   das bibliotecas de `plataforma/requirements.txt`, que não dependem dos modelos).
5. *App URL*: escolher um nome, por exemplo `ete-incomati`. **Deploy**.

### 6. Dizer à plataforma os seus endereços

No projecto principal, em `config/config.yaml`, secção `publication`:

```yaml
publication:
  app_url: "https://ete-incomati.streamlit.app"
  page_url: "https://<conta>.github.io/ete-plataforma/"
```

Depois, publicar a alteração (ver "Enviar alterações" abaixo). A página leve passa a ter a
ligação para a aplicação, e a aplicação para a página leve.

## Manter

| Tarefa | Quando | Como |
|---|---|---|
| Boletim, mensagem, página | todos os dias | automático (GitHub) |
| Ver se o boletim correu | todos os dias, de relance | separador **Actions**: verde = correu. O GitHub envia um email quando falha |
| Imagens de cor da água | uma vez por semana | no computador do projecto: `scripts/update_water_quality_scenes.py`, e enviar |
| Módulo Q e mapa de radar do mês | uma vez por mês | `scripts/update_module_q_series.py`, `scripts/export_platform_package.py`, e enviar |
| Acordar a aplicação | antes de uma demonstração | abrir o endereço; se estiver adormecida, carregar no botão e esperar |

### Enviar alterações do projecto para a plataforma

```bash
cd deploy/ete-plataforma && git pull          # primeiro, trazer os boletins que o GitHub guardou
cd ../.. && .venv/bin/python scripts/build_deploy_repo.py
cd deploy/ete-plataforma && git add -A && git commit -m "Actualização" && git push
```

O `git pull` primeiro é importante: sem ele, o envio é recusado porque o GitHub tem boletins
que o computador ainda não tem.

## Quando algo corre mal

| Sintoma | Causa provável | O que fazer |
|---|---|---|
| A aplicação e a página dizem "previsão indisponível" | o boletim não corre há mais de 36 horas | **Actions > Boletim diário**: ver o erro; correr à mão com **Run workflow** |
| O boletim falha em "Previsão" | o serviço de previsão (Open-Meteo) esteve em baixo | normalmente resolve-se no dia seguinte; pode correr-se à mão mais tarde |
| O boletim falha em "Guardar no repositório" | falta a permissão do passo 3.1 | **Settings > Actions > General > Read and write permissions** |
| A aplicação mostra "This app has gone to sleep" | ficou muito tempo sem visitas | carregar em **Yes, get this app back up** |
| A aplicação dá erro ao arrancar | versão de uma biblioteca | **Manage app > Reboot**; se continuar, ver os *logs* e o resultado de **Actions > Testes** |
| O boletim automático deixou de correr sem erro nenhum | o GitHub suspende tarefas agendadas de repositórios parados há muito tempo | **Actions > Boletim diário > Enable workflow** |
| `git push` recusado | faltou o `git pull` | ver "Enviar alterações" |

## O que este desenho não resolve

- **A turbidez prevista depende das imagens semanais.** Se ninguém as actualizar durante mais
  de 30 dias, a previsão de turbidez continua, com menos acerto, e a plataforma diz de quando
  é a última medição.
- **Sem garantia de serviço.** São serviços gratuitos: podem estar lentos ou em baixo, sobretudo
  com muitas visitas ao mesmo tempo. Por isso a mensagem para os líderes e a página leve
  existem ao lado da aplicação.
- **O envio da mensagem aos líderes não é automático.** A mensagem é gerada todos os dias
  (`plataforma/dados/boletim/mensagem_whatsapp.txt`); alguém da equipa tem de a enviar.
- **Antes de divulgar o endereço:** coordenar com o INGD, o INAM e a ARA-Sul, e confirmar as
  condições de uso do serviço de previsão (Open-Meteo) para um serviço público.
