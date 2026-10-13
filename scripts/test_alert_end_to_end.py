"""Teste do alerta de ponta a ponta: previsão -> boletim -> mensagem para o líder comunitário.

    .venv/bin/python scripts/test_alert_end_to_end.py

Sem internet. Repete três situações reais e mostra a mensagem que seguiria para o canal dos
líderes (WhatsApp ou SMS): a cheia de janeiro de 2026, um dia de época seca, e um dia em que os
dados falham. Verifica o que a mensagem tem de ter e escreve o relatório em
docs/teste_alerta_ponta_a_ponta.md. A última parte do teste é humana: enviar a mensagem a um
líder e registar no relatório se a recebeu e a percebeu.
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from ete import config, forecast, forecast_models, operations  # noqa: E402

cfg = config.load_config()
history = forecast.load_history(cfg)
limits = forecast.load_limits(cfg)


def replay(day: str, spread: float = 0.15, members: int = 51) -> dict:
    """A 'forecast' made of what really happened, with scenarios scattered around it."""
    today = pd.Timestamp(day)
    q = history["q"].loc[today - pd.Timedelta(days=10):today + pd.Timedelta(days=30)]
    lead = np.clip(np.asarray((q.index - today).days), 0, None)
    scatter = np.exp(np.random.default_rng(0).normal(0, 1, (len(q), members)) * spread * np.sqrt(lead)[:, None] / 3)
    return {"date": today.date(), "discharge": pd.DataFrame(q.to_numpy()[:, None] * scatter, index=q.index, columns=[f"m{i:02d}" for i in range(members)]),
            "rain": history["rain"].loc[today - pd.Timedelta(days=60):today + pd.Timedelta(days=16)], "fetched_utc": f"{day}T05:00:00+00:00"}


def message_for(day: str) -> tuple[dict, str]:
    fc = replay(day)
    status = {"emitido_utc": fc["fetched_utc"], "desatualizado": False, "cenarios": 51, "dados_obtidos_utc": fc["fetched_utc"], "fonte": "online", "problemas": [],
              "limites_caudal": limits["discharge_m3s"], "idade_dos_dados_horas": 0.0, "estado": "ok"}
    outlook = forecast.alert_outlook(cfg, fc, limits)
    data, _ = operations.build_bulletin(cfg, fc, outlook, forecast_models.turbidity_outlook(cfg, fc), forecast_models.predict_discharge(cfg, fc), status)
    return data, operations.whatsapp_message(data)


cases, checks = [], []
for title, day, expected in (("Cheia de janeiro de 2026 (boletim de 10 de janeiro)", "2026-01-10", "vermelho"), ("Época seca (10 de agosto de 2022)", "2022-08-10", "verde")):
    data, text = message_for(day)
    cases.append((title, text))
    checks += [(f"{title}: nível {expected}", data["nivel_maximo_provavel"] == expected), (f"{title}: diz o que fazer", data["conselho"] in text),
               (f"{title}: remete para os avisos oficiais", "INGD" in text), (f"{title}: cabe num ecrã (menos de 900 caracteres)", len(text) < 900)]
    if expected == "vermelho":
        checks.append((f"{title}: indica lugares", "Alagam primeiro" in text))
text = operations.whatsapp_message({})
cases.append(("Dia em que os dados falham", text))
checks += [("dados em falta: a mensagem não diz verde", "VERDE" not in text.upper() and "INGD" in text)]

lines = ["# Teste do alerta de ponta a ponta", "", f"Corrido em {pd.Timestamp.now():%d/%m/%Y %H:%M}. Projecto Eyes to Earth.", "",
         "## 1. Verificações automáticas", "", "| Verificação | Resultado |", "|---|---|"]
lines += [f"| {name} | {'passou' if ok else '**FALHOU**'} |" for name, ok in checks]
lines += ["", "## 2. As mensagens", ""]
for title, text in cases:
    lines += [f"### {title}", "", "```", text, "```", f"{len(text)} caracteres.", ""]
lines += ["## 3. Parte humana do teste (a preencher pela equipa)", "",
          "Enviar a mensagem da cheia a pelo menos dois líderes comunitários, com a indicação clara de que é um TESTE.", "",
          "| Líder / localidade | Data e hora do envio | Recebeu? | Quanto tempo depois? | Percebeu o nível? | Percebeu o que fazer? | Reencaminhou a quem? | Observações |",
          "|---|---|---|---|---|---|---|---|", "| | | | | | | | |", "| | | | | | | | |", "",
          "Critério para dar o teste como passado: a mensagem chega em menos de 30 minutos e o líder diz, por palavras suas, qual é o nível e o que deve fazer.", ""]
if (ROOT / "docs" / "guia_de_mensagens_de_alerta.md").exists():          # only in the main project; the published repository keeps docs/ for the web page
    (ROOT / "docs" / "teste_alerta_ponta_a_ponta.md").write_text("\n".join(lines))
for name, ok in checks:
    print(f"{'ok   ' if ok else 'FALHA'} {name}")
print()
print(cases[0][1])
sys.exit(0 if all(ok for _, ok in checks) else 1)
