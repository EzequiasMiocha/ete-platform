#!/usr/bin/env bash
# Abre o Jupyter Notebook do Workshop 2 com o ambiente jupyter_env.
#
#   ./abrir_aulas.sh                                    abre a prática única dos alunos (pasta 2_pratica_unica)
#   ./abrir_aulas.sh 0_facilitadores/pratica_unica      abre a versão resolvida, para os facilitadores
#
# Para fechar: guardar os notebooks e carregar Ctrl + C duas vezes neste terminal.

AQUI="$(cd "$(dirname "$0")" && pwd)"
PASTA="${1:-2_pratica_unica}"

if [ ! -x "$AQUI/jupyter_env/bin/jupyter" ]; then
    echo "O ambiente jupyter_env ainda não existe. Corram primeiro:  ./criar_ambiente.sh"
    exit 1
fi
if [ ! -d "$AQUI/$PASTA" ]; then
    echo "A pasta $PASTA não existe dentro de Workshop_2."
    exit 1
fi

cd "$AQUI/$PASTA" || exit 1
exec "$AQUI/jupyter_env/bin/jupyter" notebook
