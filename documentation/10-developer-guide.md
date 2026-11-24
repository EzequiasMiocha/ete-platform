# 10. Developer guide

[Documentation home](README.md) · Previous: [9. User guide](09-user-guide.md) · Next: [11. Validation and limitations](11-validation-and-limitations.md)

This page is for whoever runs, maintains or extends the platform. Code comments and messages are partly in
Portuguese; identifiers and this guide are in English.

## Run the application on your computer

```bash
git clone https://github.com/EzequiasMiocha/ete-platform.git
cd ete-platform
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt          # exact versions used to train the models and test the app
.venv/bin/python plataforma/leitor.py --sem-prazo  # check the data package: ends with PACOTE COMPLETO
.venv/bin/streamlit run plataforma/app.py          # open http://localhost:8501 (add ?lang=en)
```

`plataforma/requirements.txt` is enough to run the application alone; the root `requirements.txt` also holds what the
daily bulletin needs (XGBoost, scikit-learn, geopandas, rasterio). The Actions use Python 3.14.

Locally, WhatsApp sign-ups and accounts are stored in SQLite under `data/private/` (ignored by git).

## Run the tests

```bash
.venv/bin/python plataforma/leitor.py --sem-prazo        # package complete and consistent
cd plataforma
../.venv/bin/python testar_app.py                         # every page, three languages: ends with APLICAÇÃO SEM ERROS
../.venv/bin/python testar_contas.py                      # accounts
../.venv/bin/python testar_alertas.py                     # WhatsApp rules
cd ..
.venv/bin/python scripts/test_alert_end_to_end.py         # an alert message from forecast to text
.venv/bin/python scripts/check_forecast_system.py         # offline replay of the January 2026 flood
```

The same tests run on GitHub at every push (workflow *Testes*).

## Issue a bulletin by hand

```bash
.venv/bin/python scripts/run_daily_pipeline.py --sem-imagens   # forecast, bulletin, package, light page, alerts
.venv/bin/python scripts/run_daily_pipeline.py --offline       # no internet: reuse the last stored forecast
```

On GitHub: *Actions* → *Boletim diário* → *Run workflow*. The workflow commits the new bulletin to `main`, and
Streamlit Cloud redeploys the application.

## Configuration

`config/config.yaml` is the single source of truth. The parts that matter for operations:

| Section | Holds |
|---|---|
| `forecast` | Open-Meteo addresses, the discharge cell (-25.775, 32.675), horizon (10 days), probability thresholds (likely 0.5, possible 0.2), rain-skill days (7), stale limit (36 h) |
| `processing.alerts` | Percentiles of the alert limits and the calibration end (2021) |
| `publication` | `app_url` and `page_url`; `stale_after_hours` |
| `whatsapp` | Levels that send messages (orange, red), reminder interval (2 days) |

The alert limits themselves are stored in `models/limites_previsao.json` (built by `ete.forecast.build_limits`).

## Secrets

| Secret | Where | Needed for |
|---|---|---|
| `EE_PROJECT` | `.env` on the project computer | Earth Engine (weekly images); not used by the daily bulletin |
| `ETE_SUBSCRITORES=supabase`, `SUPABASE_URL`, `SUPABASE_SERVICE_KEY` | Streamlit secrets and GitHub Actions secrets | Accounts and WhatsApp sign-ups in the cloud (tables: `docs/subscritores.sql`, `docs/contas.sql`) |
| `WHATSAPP_TOKEN`, `WHATSAPP_PHONE_ID` | GitHub Actions secrets | Sending WhatsApp alerts (Meta Cloud API, approved templates) |

Without them, everything else works and the forms say that sign-ups open soon.

## Recurring maintenance

| How often | Task | Command (project computer) | Internet |
|---|---|---|---|
| Daily | Bulletin | Automatic on GitHub | a few KB |
| Weekly | Water-colour images, map and photograph | `scripts/update_water_quality_scenes.py`, then publish | ~1 MB |
| Monthly | Module Q sections border to mouth | `scripts/update_module_q_series.py` | ~1 MB (10 MB the first time) |
| Monthly, if wanted | Radar water map of the new month (Model B) | download the Sentinel-1 composite, `scripts/run_model_b_maps.py`, `export_platform_package.py` | ~120 MB |
| After a new flood | Place pictures, warning zones | `src/ete/place_images.py`, `alerts.warning_zones` | depends |
| When models change | Rebuild the package | `scripts/export_platform_package.py` | none |

The Earth Engine steps need the project's Earth Engine account, which is why they are not on GitHub Actions.

## Publish a change

The repository is **generated** from the project folder by `scripts/build_deploy_repo.py`: changes are made in the
project folder (`plataforma/`, `src/ete/`, `config/`, `documentation/`), never directly in the generated copy. Then:

```bash
.venv/bin/python scripts/publicar_plataforma.py --verificar   # rebuild and check only, nothing is sent
.venv/bin/python scripts/publicar_plataforma.py -m "message"  # pull the bulletins, rebuild, test, commit, push
```

`publicar_plataforma.py` first pulls what GitHub committed (the daily bulletins), so it never overwrites newer data;
rebuilds the package; runs the same checks as GitHub; and sends nothing if a check fails. It pushes with a
repository deploy key. Streamlit Cloud updates the application in one to two minutes.

If you work directly on this repository instead (for example from a fork), keep in mind that the daily workflow
commits to `main` every day: pull before you push.

## Rebuild the science

The code and the notebooks are in this repository; the data they need (about 43 GB) is not, and the week 1 notebooks
download it again (Earth Engine account and Copernicus key needed). In order:

```bash
.venv/bin/earthengine authenticate
.venv/bin/python scripts/build_notebooks.py           # week 1 notebooks: downloads (tens of GB)
.venv/bin/python scripts/build_notebooks_semana2.py   # week 2: indices, features, labels, training tables
.venv/bin/python scripts/build_notebooks_semana3.py   # week 3: models A and B, alerts, validation
.venv/bin/python scripts/build_notebooks_modulo_q.py  # Module Q notebooks
.venv/bin/python scripts/build_notebooks_producao.py  # production notebooks 40-41 (forecast models)
.venv/bin/python scripts/run_notebooks.py notebooks/semana_2   # run a folder of notebooks in order
.venv/bin/python scripts/export_platform_package.py   # the package
.venv/bin/python scripts/build_documentation.py       # the figures of this documentation
```

The laptop used has 14 GB of RAM: close other notebooks before training (one experiment was stopped by the system for
lack of memory).

## Extend the platform

- **A new text**: write it in Portuguese with `t("...")` in the code and add its English and French translations to
  `plataforma/textos.py` (`{"pt": ("en", "fr")}`). A text without translation is shown in Portuguese;
  `ETE_REGISTAR_EM_FALTA=1 python testar_app.py` writes every missing one to `textos_em_falta.txt`.
- **A new layer or chart**: write the data into the package from `src/ete/platform.py`, describe it in the catalogue,
  read it with `leitor.py`, and draw it with `graficos.py` (colours: `graficos.SERIES`, validated for colour-blind
  readers).
- **A new page section**: use `T.section(title, subtitle, eyebrow, anchor)` from `tema.py`; keep the first thing a
  plain sentence and a picture, and put technical detail in a closed `st.expander`. Check the result at 390 px wide.
- **A new search topic**: add it to `TEMAS` in `plataforma/pesquisa.py` with keywords in the three languages.
- **A new place**: places come from `src/ete/places.py`; rebuild the place pictures with `src/ete/place_images.py`.

## Troubleshooting

| Symptom | Likely cause | What to do |
|---|---|---|
| The app shows "forecast unavailable" | The daily workflow failed, or the bulletin is older than 36 h | Open *Actions* → *Boletim diário*, read the log, run it again |
| `estado.json` shows `fonte: cache` and an HTTP error | Open-Meteo did not answer; the last stored forecast was reused | Usually solved the next day; run the workflow again later |
| "Your app is in the oven" for a long time | Streamlit Cloud is installing or stuck | share.streamlit.io → *Manage app* → read the logs → *Reboot app* |
| Logos or images missing on the cloud | Static files answered with an error | Images are embedded as data URIs (`tema.imagem()`); keep it that way |
| A push is refused | GitHub committed a bulletin meanwhile | Pull first (`publicar_plataforma.py` does it) |
| The workflow *Manter a plataforma acordada* fails | The app did not open in 10 minutes | Reboot the app; GitHub sends an email when this happens |
