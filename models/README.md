# Trained models

Each model is saved with joblib (`.joblib`) next to a `.json` card with its inputs, settings, training period and test
scores. They were trained with the exact library versions of the root `requirements.txt`. Details in the
documentation: [flood models](../documentation/05-flood-models.md), [forecast](../documentation/06-forecast-and-alerts.md),
[water quality](../documentation/07-water-quality.md).

| File | Model | Used by |
|---|---|---|
| `modelo_b_radar.joblib` | Model B: water and flood from Sentinel-1 radar (XGBoost) | Monthly radar maps, place pictures |
| `modelo_a_terreno.joblib` | Model A: terrain susceptibility (XGBoost) | Susceptibility map |
| `modelo_c_caudal.joblib` | Model C: river flow 1-7 days ahead (XGBoost, one per lead) | Daily bulletin (second opinion) |
| `modelo_turbidez.joblib` | Water colour of the next mornings (gradient boosting, with the tide) | Daily bulletin |
| `modelo_cor_marracuene.joblib` | Water colour at Marracuene up to 30 days (gradient boosting) | Daily bulletin, forecast maps |
| `limites_previsao.json` | Alert limits: flow percentiles 1997-2021, rain percentiles by day of year | Daily bulletin |
| `mare_maputo.json` | 22 tide constituents fitted to the sea level of Maputo Bay | Turbidity and colour models |
| `turbidez_por_caudal.json` | Share of turbid days by river flow | Bulletin text |
| `secchi_gloria.json` | Secchi depth from red reflectance, fitted on GLORIA (estimate only) | Module Q technical tables |
