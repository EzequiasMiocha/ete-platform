#!/usr/bin/env bash
# Envia a plataforma do computador do projecto para o servidor próprio (sem GitHub).
#
#   bash scripts/enviar_para_servidor.sh root@IP_DO_SERVIDOR      (a primeira vez, antes de instalar)
#   bash scripts/enviar_para_servidor.sh                          (todas as actualizações seguintes: ete@eyestoearth.co.mz)
#
# 1. Monta a versão de publicação (deploy/ete-plataforma) com o código, os modelos e os dados da plataforma.
# 2. Copia-a para /opt/ete no servidor, sem apagar o que o servidor produz sozinho todos os dias
#    (boletim, histórico das previsões, página leve) nem os segredos e a base dos subscritores.
# 3. Reinicia a plataforma.
# Internet: a primeira vez cerca de 12 MB (código, modelos e dados da plataforma); depois só o que mudou (poucos KB a 1 MB).
set -euo pipefail
cd "$(dirname "$0")/.."
. servidor/dominio.conf
SERVIDOR="${1:-ete@$DOMINIO}"          # by default the project's domain (servidor/dominio.conf)
echo "A enviar para $SERVIDOR"
.venv/bin/python scripts/build_deploy_repo.py
rsync -az --info=stats1 \
    --exclude '.git/' --exclude '.github/' --exclude '.venv/' --exclude '__pycache__/' --exclude '.env' \
    --exclude 'data/private/' --exclude 'copias/' --exclude 'data/metadata/*.log' \
    --exclude 'data/raw/forecast/history/' --exclude 'data/processed/forecast/latest/' \
    --exclude 'plataforma/dados/boletim/' --exclude 'plataforma/dados/pipeline.json' --exclude 'docs/index.html' --exclude 'docs/boletim.json' \
    deploy/ete-plataforma/ "$SERVIDOR:/opt/ete/"
rsync -az servidor "$SERVIDOR:/opt/ete/"
# first time (before servidor/instalar.sh) there is nothing to restart yet
ssh "$SERVIDOR" 'cd /opt/ete && if [ -x .venv/bin/python ]; then
    /home/ete/.local/bin/uv pip install --quiet --python .venv/bin/python -r requirements.txt
    [ "$(id -u)" = 0 ] && chown -R ete:ete /opt/ete
    sudo systemctl restart ete-plataforma && systemctl is-active ete-plataforma && echo "Enviado. A plataforma foi reiniciada."
else
    echo "Ficheiros enviados. Falta instalar: sudo bash /opt/ete/servidor/instalar.sh DOMINIO EMAIL"
fi'

