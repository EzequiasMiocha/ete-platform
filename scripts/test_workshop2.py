"""Corre a prática do Workshop 2 como no dia e confirma que tudo funciona.

    .venv/bin/python scripts/test_workshop2.py

As 4 aulas dos alunos correm sem preencher nada (não pode haver erros) e as 4 resolvidas têm de dar «Certo!» em todas
as respostas. É o mesmo teste que build_workshop2_aulas.py faz depois de gerar as aulas.
A versão antiga deste teste (Partes A a H) está guardada no histórico do projecto.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import build_workshop2_aulas  # noqa: E402

if __name__ == "__main__":
    sys.exit(build_workshop2_aulas.main())
