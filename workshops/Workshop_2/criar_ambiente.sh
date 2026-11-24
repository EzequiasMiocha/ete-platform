#!/usr/bin/env bash
# Cria o ambiente jupyter_env dentro da pasta Workshop_2 e instala as bibliotecas das aulas
# (Jupyter Notebook, numpy, pandas, matplotlib, scikit-learn e joblib).
#
#   ./criar_ambiente.sh
#
# Internet: cerca de 150 MB na primeira vez (menos se o pip já tiver as bibliotecas guardadas).
# Espaço em disco: cerca de 700 MB. Correr outra vez não faz mal: só instala o que faltar.

AQUI="$(cd "$(dirname "$0")" && pwd)"
cd "$AQUI" || exit 1
PY="${PYTHON:-python3}"

if ! "$PY" -c 'import sys; sys.exit(0 if sys.version_info >= (3, 10) else 1)' 2>/dev/null; then
    echo "É preciso o Python 3.10 ou mais recente (comando: $PY)."
    exit 1
fi

if [ ! -x jupyter_env/bin/python ]; then
    echo "A criar o ambiente jupyter_env..."
    if ! "$PY" -m venv jupyter_env; then
        echo "Não foi possível criar o ambiente. No Ubuntu, instalem primeiro:  sudo apt install python3-venv"
        exit 1
    fi
fi

echo "A instalar as bibliotecas das aulas..."
if ! jupyter_env/bin/python -m pip install --disable-pip-version-check -r 2_pratica/requirements.txt; then
    echo "A instalação falhou. Confirmem a ligação à Internet e corram outra vez:  ./criar_ambiente.sh"
    exit 1
fi

echo "A registar o kernel \"Python (Workshop 2 - jupyter_env)\" (para o VS Code e para outros Jupyter)..."
jupyter_env/bin/python -m ipykernel install --user --name workshop2 --display-name "Python (Workshop 2 - jupyter_env)"

echo
echo "PRONTO."
echo "  Abrir as aulas:              ./abrir_aulas.sh"
echo "  Testar todas as aulas:       jupyter_env/bin/python testar_aulas.py"
