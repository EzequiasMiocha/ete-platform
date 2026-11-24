"""Previsão diária do ETE: alertas de cheia e turbidez da água do Incomáti.

    .venv/bin/python scripts/run_daily_forecast.py            # normal (precisa de internet, poucos KB)
    .venv/bin/python scripts/run_daily_forecast.py --offline  # reutiliza a última previsão guardada

Escreve o boletim e as tabelas em data/processed/forecast/latest/ e guarda uma cópia em
data/processed/forecast/archive/<data>/. Código de saída: 0 = boletim emitido, 1 = previsão
indisponível (os dados não passaram nas verificações), 2 = erro.

Para correr todos os dias às 06:00, acrescentar ao crontab (crontab -e):
    0 6 * * * cd /caminho/para/Projecto-ETE && .venv/bin/python scripts/run_daily_forecast.py >> data/metadata/previsao_diaria.log 2>&1
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from ete import config, operations

try:
    result = operations.run_daily(config.load_config(), offline="--offline" in sys.argv)
except Exception as err:                       # nothing usable at all: say so and fail loudly
    print(f"ERRO: {type(err).__name__}: {err}")
    sys.exit(2)

status = result["status"]
print(f"{status['emitido_utc']}  estado={status['estado']}  fonte={status['fonte']}  dados com {status['idade_dos_dados_horas']} h")
for problem in status["problemas"]:
    print("  aviso:", problem)
print()
print(result["bulletin"])
sys.exit(0 if status["estado"] != "previsao_indisponivel" else 1)
