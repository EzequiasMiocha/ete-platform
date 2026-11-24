#!/usr/bin/env bash
# Instala a plataforma Eyes to Earth num servidor Ubuntu 24.04 (uma só vez, como root).
#
#   sudo bash /opt/ete/servidor/instalar.sh                  (domínio e email de servidor/dominio.conf)
#   sudo bash /opt/ete/servidor/instalar.sh DOMINIO EMAIL    (para usar outros)
#
# Antes: o domínio tem de apontar para o IP deste servidor (registo DNS "A") e os ficheiros do
# projecto têm de estar em /opt/ete (ver docs/guia_servidor_proprio.md, passos 1 a 4).
# Internet usada no servidor: cerca de 1 GB (sistema, Python e bibliotecas). Não é a rede do telemóvel.
set -euo pipefail
PASTA=/opt/ete
[ -f "$PASTA/servidor/dominio.conf" ] && . "$PASTA/servidor/dominio.conf"
DOMINIO="${1:-${DOMINIO:-}}"
EMAIL="${2:-${EMAIL_CERTIFICADO:-}}"
[ -n "$DOMINIO" ] && [ -n "$EMAIL" ] || { echo "Uso: sudo bash servidor/instalar.sh DOMINIO EMAIL (ou preencher servidor/dominio.conf)"; exit 1; }
echo "Domínio: $DOMINIO · email do certificado: $EMAIL"
[ -f "$PASTA/plataforma/app.py" ] || { echo "Não encontro $PASTA/plataforma/app.py: copie primeiro o projecto (scripts/enviar_para_servidor.sh)."; exit 1; }

echo "== 1. Sistema: fuso horário de Maputo, actualizações automáticas, firewall"
timedatectl set-timezone Africa/Maputo
apt-get update
apt-get install -y nginx certbot python3-certbot-nginx sqlite3 ufw unattended-upgrades curl rsync
ufw allow OpenSSH
ufw allow "Nginx Full"
ufw --force enable

echo "== 2. Utilizador 'ete' (a plataforma não corre como root)"
id ete >/dev/null 2>&1 || useradd --system --create-home --home-dir /home/ete --shell /bin/bash ete
mkdir -p "$PASTA/data/private" "$PASTA/data/metadata" "$PASTA/copias"
chown -R ete:ete "$PASTA"
chmod 700 "$PASTA/data/private" "$PASTA/copias"

echo "== 3. Python e bibliotecas (a mesma versão do Python com que os modelos foram treinados)"
sudo -u ete bash -c 'curl -LsSf https://astral.sh/uv/install.sh | sh'
VERSAO=$(sed -n 's/^python_version=//p' "$PASTA/servidor/versao_python.txt" 2>/dev/null || echo 3.14)
sudo -u ete bash -c "cd $PASTA && ~/.local/bin/uv venv --python $VERSAO .venv && ~/.local/bin/uv pip install --python .venv/bin/python -r requirements.txt"

echo "== 4. Ficheiro de segredos (.env), se ainda não existir"
if [ ! -f "$PASTA/.env" ]; then
    cat > "$PASTA/.env" <<EOT
# Segredos do servidor. Só o utilizador ete os pode ler. Ver docs/guia_servidor_proprio.md.
ETE_APP_URL=https://$DOMINIO
ETE_SUBSCRITORES=sqlite
WHATSAPP_TOKEN=
WHATSAPP_PHONE_ID=
EOT
fi
chown ete:ete "$PASTA/.env"
chmod 600 "$PASTA/.env"

echo "== 5. Endereço público na configuração (ligações nas mensagens de WhatsApp e na página leve)"
sed -i "s|^  app_url: \"\"|  app_url: \"https://$DOMINIO\"|; s|^  page_url: \"\"|  page_url: \"https://$DOMINIO/leve/\"|" "$PASTA/config/config.yaml"
grep -n "app_url\|page_url" "$PASTA/config/config.yaml"

echo "== 6. Serviço da plataforma (e licença para o utilizador ete o reiniciar depois de cada actualização)"
echo "ete ALL=(root) NOPASSWD: /usr/bin/systemctl restart ete-plataforma, /usr/bin/systemctl status ete-plataforma" > /etc/sudoers.d/ete-plataforma
chmod 440 /etc/sudoers.d/ete-plataforma
visudo -cf /etc/sudoers.d/ete-plataforma
install -m 644 "$PASTA/servidor/ete-plataforma.service" /etc/systemd/system/ete-plataforma.service
systemctl daemon-reload
systemctl enable --now ete-plataforma

echo "== 7. Nginx no domínio $DOMINIO"
IP_DESTE=$(curl -4 -s https://api.ipify.org || true)
IP_DNS=$(getent ahostsv4 "$DOMINIO" | awk 'NR==1{print $1}')
if [ -n "$IP_DESTE" ] && [ "$IP_DESTE" != "$IP_DNS" ]; then
    echo "ATENÇÃO: $DOMINIO aponta para '${IP_DNS:-nada}', mas este servidor é $IP_DESTE."
    echo "Corrija o registo DNS do tipo A no painel do domínio e espere que se propague; o HTTPS só funciona depois disso."
fi
sed "s/DOMINIO/$DOMINIO/g" "$PASTA/servidor/nginx_ete.conf" > /etc/nginx/sites-available/ete
ln -sf /etc/nginx/sites-available/ete /etc/nginx/sites-enabled/ete
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

echo "== 8. HTTPS (cadeado) com Let's Encrypt, renovado sozinho"
certbot --nginx --non-interactive --agree-tos -m "$EMAIL" -d "$DOMINIO" -d "www.$DOMINIO" --redirect

echo "== 9. Tarefas diárias: boletim às 05:15 e cópia de segurança às 03:30 (hora de Maputo)"
chmod +x "$PASTA/servidor/copia_de_seguranca.sh"
sudo -u ete crontab "$PASTA/servidor/crontab_ete"

echo "== 10. Primeiro boletim"
sudo -u ete bash -c "cd $PASTA && set -a && . ./.env && set +a && .venv/bin/python scripts/run_daily_pipeline.py --sem-imagens" || true
systemctl restart ete-plataforma

echo
echo "Pronto: https://$DOMINIO  (página leve: https://$DOMINIO/leve/)"
echo "Estado:  systemctl status ete-plataforma   ·   registos: journalctl -u ete-plataforma -n 50"
