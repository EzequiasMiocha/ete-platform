"""Experiência: que outras entradas melhoram o modelo de turbidez?

Testa, por cima do modelo final (caudal, chuva, época do ano, maré, última medição):
  * vento na foz (velocidade máxima da véspera e dos três dias anteriores)
  * chuva local na foz (1, 3 e 7 dias)
  * chuva separada entre a parte alta e a parte baixa da bacia
  * treinar com os dois satélites juntos em vez de só com o Sentinel-2
Cada ano é previsto por um modelo que nunca o viu. O resultado fica em
reports/semana_3/35_entradas_testadas.csv e é lido pelo notebook 35.

Os dados de vento e chuva (ERA5, serviço Open-Meteo, cerca de 0,6 MB) estão em
data/raw/forecast/experimento/. Demora cerca de 15 minutos.

    .venv/bin/python scripts/experimento_turbidez_entradas.py
"""

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import brier_score_loss, r2_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
warnings.filterwarnings("ignore")

from ete import config, forecast  # noqa: E402
from ete import forecast_models as fm  # noqa: E402

cfg = config.load_config()
folder = config.path(cfg, "forecast_raw", "experimento", mkdir=False)
met = pd.read_csv(folder / "tempo_local_foz.csv", index_col=0, parse_dates=True)
points = pd.read_csv(folder / "chuva_por_ponto_da_bacia.csv", index_col=0, parse_dates=True)
lon = np.array([p[1] for p in forecast.basin_points(cfg)])
low, up = points.loc[:, lon >= 32.0].mean(axis=1), points.loc[:, lon < 31.5].mean(axis=1)
rain = met["precipitation_sum"].shift(1)
extra = pd.DataFrame({"w_prev": met["wind_speed_10m_max"].shift(1), "w_max3": met["wind_speed_10m_max"].shift(1).rolling(3).max(),
                      "l1": rain, "l3": rain.rolling(3).sum(), "l7": rain.rolling(7).sum(),
                      "low3": low.rolling(3).sum(), "low7": low.rolling(7).sum(), "up3": up.rolling(3).sum(), "up7": up.rolling(7).sum(), "up30": up.rolling(30).sum()})

days = fm.tide_model_table(cfg)
limits, reaches = days.attrs["limits"], days.attrs["reaches"]
landsat = fm.tide_model_table(cfg, "landsat89", limits=limits, reaches=reaches)
source = fm.measurement_source(cfg)
medians = days.groupby("troco")["ndti"].median().to_dict()
landsat["ndti"] = landsat["ndti"] + source.attrs["bias"]
s2 = fm._stack_lags(days, source, medians).join(extra, on="date").assign(landsat=0.0)
both = pd.concat([s2, fm._stack_lags(landsat, source, medians).join(extra, on="date").assign(landsat=1.0)], ignore_index=True)
final = fm.TIDE_MODEL_FEATURES + [c for c in days if c.startswith("troco=")]
variants = {"modelo final": (s2, final), "+ vento na foz": (s2, final + ["w_prev", "w_max3"]), "+ chuva local na foz": (s2, final + ["l1", "l3", "l7"]),
            "+ chuva por parte da bacia": (s2, final + ["low3", "low7", "up3", "up7", "up30"]),
            "treinado com os dois satélites": (both, final + ["landsat"])}
rows = []
for name, (table, features) in variants.items():
    table = table.dropna(subset=features).reset_index(drop=True)
    test = table[table["landsat"] == 0]
    pred, prob = pd.Series(np.nan, test.index), pd.Series(np.nan, test.index)
    for year in sorted(test["ano"].unique()):
        train, inside = table[table["ano"] != year], test[test["ano"] == year]
        regressor, classifier = fm._tide_models(cfg["processing"]["seed"])
        pred[inside.index] = regressor.fit(train[features], train["ndti"]).predict(inside[features])
        prob[inside.index] = classifier.fit(train[features], train["elevada"]).predict_proba(inside[features])[:, 1]
    rows.append({"entradas": name, "r2": r2_score(test["ndti"], pred), "auc": roc_auc_score(test["elevada"], prob), "brier": brier_score_loss(test["elevada"], prob)})
    print(rows[-1], flush=True)
out = pd.DataFrame(rows).set_index("entradas").round(3)
out.to_csv(config.path(cfg, "reports", "semana_3") / "35_entradas_testadas.csv")
print(out)
