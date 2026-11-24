"""Corre notebooks do princípio ao fim e guarda os resultados dentro deles.

    python scripts/run_notebooks.py notebooks/semana_2            # todos, por ordem
    python scripts/run_notebooks.py notebooks/semana_2/22_*.ipynb   # só alguns

Pára no primeiro notebook que der erro e mostra a célula que falhou.
"""

import sys
import time
from pathlib import Path

import nbformat
from nbclient import NotebookClient
from nbclient.exceptions import CellExecutionError

targets = []
for arg in sys.argv[1:] or ["notebooks/semana_2"]:
    p = Path(arg)
    targets += sorted(p.glob("*.ipynb")) if p.is_dir() else [p]

for file in targets:
    start = time.time()
    nb = nbformat.read(file, 4)
    client = NotebookClient(nb, timeout=None, kernel_name="python3", resources={"metadata": {"path": str(file.parent)}})
    try:
        client.execute()
    except CellExecutionError as err:
        nbformat.write(nb, file)
        print(f"ERRO   {file.name}\n{str(err)[-1500:]}")
        sys.exit(1)
    nbformat.write(nb, file)
    print(f"ok     {file.name}  ({(time.time() - start) / 60:.1f} min)", flush=True)
