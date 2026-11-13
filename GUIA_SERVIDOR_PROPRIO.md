# Publicar a plataforma num domínio próprio (sem GitHub nem Streamlit Cloud)

Domínio escolhido: **eyestoearth.co.mz** (registo e DNS: `docs/guia_dominio_co_mz.md`; domínio e email em `servidor/dominio.conf`).

Um servidor alugado (VPS) faz tudo o que antes estava espalhado pelo GitHub, pelo Streamlit
Community Cloud e pelo Supabase:

| Antes (plano GitHub) | Com servidor próprio |
|---|---|
| Streamlit Community Cloud serve a plataforma | O servidor serve a plataforma em `https://o-vosso-dominio` |
| GitHub Actions faz o boletim às 05:15 | O próprio servidor faz o boletim às 05:15 (cron) |
| GitHub Pages serve a página leve | O servidor serve a página leve em `https://o-vosso-dominio/leve/` (e mostra-a sozinho se a plataforma cair) |
| Supabase guarda os subscritores | A base `subscritores` fica no disco do servidor (SQLite), com cópia diária |
| Alertas no WhatsApp a partir do GitHub | Alertas no WhatsApp a partir do servidor |

## O que é preciso comprar

| O quê | Exemplos | Custo aproximado (confirmar no dia) |
|---|---|---|
| **Domínio** | `eyestoearth.org`, `ete-incomati.org`; ou um domínio moçambicano `.co.mz` / `.org.mz` | `.org` ou `.com`: cerca de 10 a 20 USD por ano. `.mz`: ver o registo nacional de domínios de Moçambique (gerido pela Universidade Eduardo Mondlane) |
| **Servidor (VPS)** com Ubuntu 24.04, pelo menos 2 GB de memória (4 GB é mais confortável) e 40 GB de disco | Hetzner, DigitalOcean, Contabo, OVH; ou um fornecedor com centro de dados na África do Sul ou em Moçambique (menos atraso para quem está em Marracuene) | cerca de 5 a 15 USD por mês |

O domínio compra-se num registador (por exemplo Namecheap, Porkbun, Cloudflare, ou um registador
moçambicano para `.mz`). Convém que fique em nome do projecto ou da instituição, não de uma pessoa,
e que a renovação seja automática: um domínio que caduca deixa a plataforma e as ligações das
mensagens de WhatsApp sem funcionar.

## Passo a passo (cerca de 1 hora, uma só vez)

1. **Comprar o servidor** com Ubuntu 24.04 e guardar o endereço IP e a palavra-passe (ou chave SSH) do utilizador `root`.
2. **Comprar o domínio** e, no painel do registador, criar dois registos DNS do tipo **A**:
   `@` → IP do servidor e `www` → IP do servidor. Pode demorar de minutos a algumas horas a funcionar.
3. **Enviar a plataforma** a partir do computador do projecto (cerca de 12 MB de internet):
   ```bash
   bash scripts/enviar_para_servidor.sh root@IP_DO_SERVIDOR
   ```
4. **Instalar** (no servidor, cerca de 1 GB de internet do servidor, não do telemóvel):
   ```bash
   ssh root@IP_DO_SERVIDOR
   sudo bash /opt/ete/servidor/instalar.sh o-vosso-dominio.org email-da-equipa@exemplo.org
   ```
   O script prepara tudo sozinho:
   - fuso horário de Maputo, firewall e actualizações de segurança automáticas;
   - o utilizador `ete`, para a plataforma não correr como administrador;
   - o Python e as bibliotecas;
   - o serviço que mantém a plataforma ligada;
   - o Nginx com o cadeado HTTPS (Let's Encrypt, renovado sozinho);
   - o boletim diário às 05:15 e a cópia de segurança às 03:30;
   - o primeiro boletim.
5. **Abrir** `https://o-vosso-dominio.org`. A página leve fica em `https://o-vosso-dominio.org/leve/`.
6. **Alertas no WhatsApp** (quando a conta da Meta estiver aprovada, ver `docs/alertas_whatsapp.md`):
   no servidor, `sudo -u ete nano /opt/ete/.env`, preencher `WHATSAPP_TOKEN` e `WHATSAPP_PHONE_ID`,
   e reiniciar com `sudo systemctl restart ete-plataforma`.

## Actualizar a plataforma

Depois de mudar alguma coisa no computador do projecto (modelos, textos, mapas):

```bash
bash scripts/enviar_para_servidor.sh ete@o-vosso-dominio.org
```

Envia só o que mudou e reinicia a plataforma. Não apaga o que o servidor faz sozinho: boletim,
histórico das previsões, página leve, segredos (`.env`) e a base dos subscritores.

As imagens de cor da água (Earth Engine, uma vez por semana) e o Módulo Q (uma vez por mês)
continuam a ser feitos no computador do projecto e enviados com este mesmo comando.

## No dia-a-dia

| Para quê | Comando (no servidor) |
|---|---|
| A plataforma está ligada? | `systemctl status ete-plataforma` |
| Ver os últimos erros | `journalctl -u ete-plataforma -n 50` |
| Ver o boletim de hoje | `tail -30 /opt/ete/data/metadata/pipeline_diario.log` |
| Correr o boletim agora | `sudo -u ete bash -c 'cd /opt/ete && set -a && . ./.env && set +a && .venv/bin/python scripts/run_daily_pipeline.py --sem-imagens'` |
| Ver os subscritores | `sudo -u ete bash -c 'cd /opt/ete && .venv/bin/python scripts/ver_subscritores.py'` |
| Excel dos subscritores | o mesmo comando com `--excel`; depois trazer o ficheiro com `scp ete@o-vosso-dominio.org:/opt/ete/data/private/subscritores_*.xlsx .` |

## Cópias de segurança

Todos os dias às 03:30 a base `subscritores` (e o `.env`) é copiada para `/opt/ete/copias/`, onde
fica 30 dias. Uma cópia no mesmo servidor não protege se o servidor se perder: de vez em quando
(por exemplo, uma vez por semana), trazer as cópias para um disco da equipa:

```bash
scp 'ete@o-vosso-dominio.org:/opt/ete/copias/*' copias_servidor/
```

Muitos fornecedores de VPS vendem também "snapshots" ou "backups" automáticos do servidor inteiro
por um pequeno valor mensal: vale a pena activar.

## Segurança

- Entrar no servidor com chave SSH, não com palavra-passe; depois de configurada, desligar a entrada por palavra-passe.
- O `.env` (chaves do WhatsApp) e a pasta `data/private` só são legíveis pelo utilizador `ete`.
- A plataforma só ouve dentro do servidor (127.0.0.1:8501); quem está na internet entra pelo Nginx, com HTTPS.
- O firewall só deixa passar SSH, HTTP e HTTPS. As actualizações de segurança do sistema instalam-se sozinhas.

## Ficheiros

| O quê | Onde |
|---|---|
| Instalação no servidor | `servidor/instalar.sh` |
| Serviço da plataforma | `servidor/ete-plataforma.service` |
| Nginx (domínio, página leve, página de reserva) | `servidor/nginx_ete.conf` |
| Tarefas diárias | `servidor/crontab_ete` |
| Cópia de segurança | `servidor/copia_de_seguranca.sh` |
| Enviar do computador para o servidor | `scripts/enviar_para_servidor.sh` |
