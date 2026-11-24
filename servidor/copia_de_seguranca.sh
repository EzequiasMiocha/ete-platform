#!/usr/bin/env bash
# Cópia diária da base de dados dos subscritores (e do .env), guardada 30 dias em /opt/ete/copias.
# Corre pelo cron do utilizador ete. Copiar também, de vez em quando, para fora do servidor
# (por exemplo: scp ete@SERVIDOR:/opt/ete/copias/* para um disco da equipa).
set -euo pipefail
destino=/opt/ete/copias
mkdir -p "$destino"
chmod 700 "$destino"
dia=$(date +%F)
if [ -f /opt/ete/data/private/subscritores.db ]; then
    sqlite3 /opt/ete/data/private/subscritores.db ".backup '$destino/subscritores_$dia.db'"
fi
[ -f /opt/ete/.env ] && cp /opt/ete/.env "$destino/env_$dia"
chmod 600 "$destino"/* 2>/dev/null || true
find "$destino" -type f -mtime +30 -delete
