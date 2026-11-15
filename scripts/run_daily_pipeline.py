"""Pipeline diário do ETE: um só comando para manter a plataforma atualizada.

    .venv/bin/python scripts/run_daily_pipeline.py                # normal
    .venv/bin/python scripts/run_daily_pipeline.py --offline      # sem internet: reutiliza o que está guardado
    .venv/bin/python scripts/run_daily_pipeline.py --imagens      # força a atualização das imagens de cor da água
    .venv/bin/python scripts/run_daily_pipeline.py --sem-imagens  # salta esse passo

Passos:
  1. Imagens de cor da água (Earth Engine, centenas de KB): só quando a última atualização tem
     6 dias ou mais. Se falhar, o resto continua e o boletim diz de quando é a última medição.
     Uma vez por mês, também os troços do Módulo Q, da fronteira à foz (cerca de 1 MB).
  2. Previsão de cheia e de turbidez e boletim (Open-Meteo, poucos KB).
  3. Pacote de dados da plataforma (plataforma/dados/), sem internet.
  4. Página leve do boletim (plataforma/pagina/index.html): a reserva para quando a aplicação não abre.
  5. Alertas no WhatsApp para quem se inscreveu na plataforma (laranja ou vermelho; ver docs/alertas_whatsapp.md).
O resumo de cada execução fica em plataforma/dados/pipeline.json.

Código de saída: 0 = boletim emitido, 1 = previsão indisponível, 2 = erro.

Os mapas mensais de água por radar (Modelo B) NÃO fazem parte deste pipeline: precisam de
descarregar o Sentinel-1 do mês (cerca de 120 MB). Fazem-se uma vez por mês, ver README.

Para correr todos os dias às 06:00 (crontab -e):
    0 6 * * * cd /caminho/para/Projecto-ETE && .venv/bin/python scripts/run_daily_pipeline.py >> data/metadata/pipeline_diario.log 2>&1
"""

import json
import subprocess
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ete import config, operations, platform  # noqa: E402

IMAGES_EVERY_DAYS = 6
cfg = config.load_config()
offline = "--offline" in sys.argv
steps, code = [], 0


def record(name: str, state: str, detail: str = "", started: float | None = None) -> None:
    steps.append({"passo": name, "estado": state, "detalhe": detail, "segundos": round(time.time() - started, 1) if started else 0})
    print(f"[{name}] {state}" + (f": {detail}" if detail else ""), flush=True)


# 1. water colour images
files = sorted(config.path(cfg, "water_quality").glob("sentinel2_*.csv"))
age_days = (time.time() - files[-1].stat().st_mtime) / 86400 if files else float("inf")
if "--sem-imagens" in sys.argv or (offline and "--imagens" not in sys.argv):
    record("imagens", "saltado", f"última actualização há {age_days:.0f} dias")
elif age_days < IMAGES_EVERY_DAYS and "--imagens" not in sys.argv:
    record("imagens", "em dia", f"última actualização há {age_days:.0f} dias")
else:
    started = time.time()
    try:
        done = subprocess.run([sys.executable, str(ROOT / "scripts" / "update_water_quality_scenes.py")], capture_output=True, text=True, timeout=1800)
        if done.returncode == 0:
            record("imagens", "actualizado", "", started)
        else:
            record("imagens", "falhou", (done.stderr.strip().splitlines() or ["erro"])[-1][:200], started)
    except subprocess.TimeoutExpired:
        record("imagens", "falhou", "demorou mais de 30 minutos", started)

# 1b. Module Q (sections from the border to the mouth): once a month
MODULE_Q_EVERY_DAYS = 30
q_files = sorted(config.path(cfg, "module_q_raw").glob("sentinel2_*.csv"))
q_age = (time.time() - q_files[-1].stat().st_mtime) / 86400 if q_files else float("inf")
if "--sem-imagens" in sys.argv or offline or not q_files:
    record("modulo_q", "saltado", f"última actualização há {q_age:.0f} dias" if q_files else "feito no computador do projecto, uma vez por mês")
elif q_age < MODULE_Q_EVERY_DAYS and "--imagens" not in sys.argv:
    record("modulo_q", "em dia", f"última actualização há {q_age:.0f} dias")
else:
    started = time.time()
    try:
        done = subprocess.run([sys.executable, str(ROOT / "scripts" / "update_module_q_series.py")], capture_output=True, text=True, timeout=5400)
        record("modulo_q", "actualizado" if done.returncode == 0 else "falhou", "" if done.returncode == 0 else (done.stderr.strip().splitlines() or ["erro"])[-1][:200], started)
    except subprocess.TimeoutExpired:
        record("modulo_q", "falhou", "demorou mais de 90 minutos", started)

# 2. forecast and bulletin
started = time.time()
try:
    result = operations.run_daily(cfg, offline=offline)
    status = result["status"]
    record("previsao", status["estado"], "; ".join(status["problemas"]), started)
    code = 0 if status["estado"] != "previsao_indisponivel" else 1
except Exception as err:                       # nothing usable at all
    record("previsao", "erro", f"{type(err).__name__}: {err}", started)
    code = 2

# 3. platform package
started = time.time()
try:
    catalogue = platform.refresh_daily(cfg)
    record("pacote", "actualizado", f"{len(catalogue['camadas'])} camadas", started)
except Exception as err:
    record("pacote", "erro", f"{type(err).__name__}: {err}", started)
    code = 2

# 4. light static page (fallback)
started = time.time()
try:
    page = platform.write_static_page(cfg)
    record("pagina", "actualizada", str(page.relative_to(ROOT)), started)
except Exception as err:
    record("pagina", "erro", f"{type(err).__name__}: {err}", started)

# 5. WhatsApp alerts to the people who signed up (only with a valid bulletin; no phone numbers are logged)
started = time.time()
if code == 2:
    record("whatsapp", "saltado", "sem boletim novo")
else:
    try:
        sys.path.insert(0, str(ROOT / "scripts"))
        import send_whatsapp_alerts

        sent = send_whatsapp_alerts.correr()
        detail = f"{sent['motivo']}; enviadas {sent['enviadas']}, boas-vindas {sent['boas_vindas']}" + (f", falharam {sent['falharam']}" if sent["falharam"] else "")
        record("whatsapp", sent["decisao"] if sent["modo"] != "não configurado" else "não configurado", detail, started)
    except Exception as err:
        record("whatsapp", "erro", f"{type(err).__name__}: {err}", started)

summary = {"executado_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"), "codigo_de_saida": code, "passos": steps}
(config.path(cfg, "platform") / "pipeline.json").write_text(json.dumps(summary, indent=1, ensure_ascii=False))
sys.exit(code)
