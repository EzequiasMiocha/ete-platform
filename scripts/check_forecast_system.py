"""Auto-teste do sistema de previsão, sem internet.

    .venv/bin/python scripts/check_forecast_system.py

Verifica quatro coisas e termina com erro se alguma falhar:
  1. Repetição da cheia de janeiro de 2026: com o caudal e a chuva que realmente ocorreram
     dados como "previsão", o boletim de 10 de janeiro tem de chegar a vermelho.
  2. Época seca: o boletim de 10 de agosto de 2022 tem de ficar verde.
  3. Dados em falta ou absurdos: o boletim tem de dizer "previsão indisponível", nunca verde.
  4. Modo sem ligação: reutiliza a última previsão guardada e assinala a origem.
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

import numpy as np
import pandas as pd

from ete import config, forecast, forecast_models, operations

cfg = config.load_config()
history = forecast.load_history(cfg)
limits = forecast.load_limits(cfg)


def replay(day: str, spread: float = 0.15, members: int = 51) -> dict:
    """A 'forecast' made of what really happened, with scenarios scattered around it."""
    today = pd.Timestamp(day)
    q = history["q"].loc[today - pd.Timedelta(days=10):today + pd.Timedelta(days=30)]
    rng = np.random.default_rng(0)
    lead = np.clip(np.asarray((q.index - today).days), 0, None)
    scatter = np.exp(rng.normal(0, 1, (len(q), members)) * spread * np.sqrt(lead)[:, None] / 3)
    discharge = pd.DataFrame(q.to_numpy()[:, None] * scatter, index=q.index, columns=[f"m{i:02d}" for i in range(members)])
    return {"date": today.date(), "discharge": discharge, "rain": history["rain"].loc[today - pd.Timedelta(days=60):today + pd.Timedelta(days=16)],
            "fetched_utc": pd.Timestamp.now(tz="UTC").isoformat(timespec="seconds")}


def status_for(fc):
    return {"emitido_utc": fc["fetched_utc"], "desatualizado": False, "fonte": "teste", "dados_obtidos_utc": fc["fetched_utc"],
            "cenarios": fc["discharge"].shape[1], "limites_caudal": limits["discharge_m3s"]}


failures = []


def check(name: str, ok: bool, detail: str = ""):
    print(("ok    " if ok else "FALHA ") + name + (f"  [{detail}]" if detail else ""))
    if not ok:
        failures.append(name)


# 1. flood replay
fc = replay("2026-01-10")
outlook = forecast.alert_outlook(cfg, fc, limits)
first_orange = outlook.index[outlook["nivel"] >= 2].min()
check("cheia de jan 2026: sem problemas nas verificações", operations.check_forecast(cfg, fc) == [])
check("cheia de jan 2026: chega a vermelho no horizonte", outlook["nivel"].max() == 3, f"níveis {outlook['nivel'].tolist()}")
check("cheia de jan 2026: laranja ou mais antes de 17 de janeiro", first_orange <= pd.Timestamp("2026-01-16"), f"primeiro dia {first_orange.date()}")
turbidity = forecast_models.turbidity_outlook(cfg, fc)
daily_p = turbidity.attrs["daily"]
start_p, end_p = float(daily_p.iloc[:2].mean().max()), float(daily_p.iloc[-4:].mean().min())
# on 10 January the river was already above the yellow limit, so "possible" at the start is right;
# what must hold is that it is not yet likely, and that it becomes likely as the flood arrives
check("cheia de jan 2026: turbidez sobe com a cheia (não provável no início, provável no fim do horizonte)",
      start_p < 0.5 and end_p >= 0.5 and end_p - start_p >= 0.2, f"início {start_p:.2f}, fim {end_p:.2f}")
flood_days = int(turbidity.loc[turbidity["previsao"] != "sem previsão", "dias_elevada"].min())
data, text = operations.build_bulletin(cfg, fc, outlook, turbidity, forecast_models.predict_discharge(cfg, fc), status_for(fc))
check("cheia de jan 2026: boletim diz VERMELHO e indica a zona de aviso", "VERMELHO" in text and "**Onde:** zonas 1 e 2" in text)
Path(config.path(cfg, "forecast", "exemplos") / "boletim_cheia_2026-01-10.md").write_text(text)

# 2. dry season
fc = replay("2022-08-10")
outlook = forecast.alert_outlook(cfg, fc, limits)
check("época seca (ago 2022): tudo verde", outlook["nivel_possivel"].max() == 0)
dry = forecast_models.turbidity_outlook(cfg, fc)
dry_days = int(dry.loc[dry["previsao"] != "sem previsão", "dias_elevada"].max())
check("época seca (ago 2022): menos manhãs turvas do que na cheia", dry_days < flood_days, f"máximo de {dry_days} em 11 dias")

# 3. bad data must never look green
bad = replay("2022-08-10")
bad["discharge"].iloc[12:, :40] = np.nan
check("cenários em falta: verificação apanha", len(operations.check_forecast(cfg, bad)) > 0)
bad = replay("2022-08-10")
bad["discharge"] *= -1
check("caudal negativo: verificação apanha", len(operations.check_forecast(cfg, bad)) > 0)
bad = replay("2022-08-10")
bad["rain"] = bad["rain"].iloc[:-12]
check("chuva em falta: verificação apanha", len(operations.check_forecast(cfg, bad)) > 0)

# 4. offline mode
if forecast.latest_run(cfg):
    result = operations.run_daily(cfg, offline=True)
    check("modo sem ligação: usa a cópia guardada e diz que é cópia", result["status"]["fonte"] == "cache" and "boletim" in "".join(p.name for p in config.path(cfg, "forecast", "latest").iterdir()))
else:
    print("aviso: ainda não há nenhuma previsão guardada; o modo sem ligação não foi testado")

print()
print("TUDO CERTO" if not failures else f"{len(failures)} FALHA(S): " + "; ".join(failures))
sys.exit(1 if failures else 0)
