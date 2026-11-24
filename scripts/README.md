# Scripts

Command-line programs of the project. Run them from the root of the repository with the project's Python, for example
`.venv/bin/python scripts/run_daily_pipeline.py`. Most messages are in Portuguese. The logic they call lives in
[`src/ete/`](../src/ete).

## Daily operation (also run by GitHub Actions)

| Script | What it does |
|---|---|
| `run_daily_pipeline.py` | The single daily entry point: images (weekly), forecast and bulletin, data package, light page, WhatsApp alerts |
| `run_daily_forecast.py` | Forecast and bulletin only |
| `check_forecast_system.py` | Offline self-test: replays the January 2026 flood through the production code |
| `test_alert_end_to_end.py` | An alert message from forecast to text |
| `send_whatsapp_alerts.py` | Sends the WhatsApp alerts (step 5 of the pipeline) |
| `manter_acordada.py` | Opens the web application so the free host does not put it to sleep |

## Updating data (project computer, Earth Engine)

| Script | What it does | Internet |
|---|---|---|
| `update_water_quality_scenes.py` | Weekly: new water-colour images, map and photograph | ~1 MB |
| `update_module_q_series.py` | Monthly: Module Q tables, border to mouth | ~1 MB (10 MB the first time) |
| `run_model_b_maps.py` | Monthly radar water maps (Model B) | needs the Sentinel-1 composite (~120 MB) |
| `add_s1_p10.py` | Added the 10th-percentile bands to every Sentinel-1 month already downloaded (one-off) | ~25 MB per month |
| `run_sentinel2.py` | Sentinel-2 monthly composites outside Jupyter (same recipe as notebook 07, resumable) | large |
| `download_flood_scenes.py` | Single-day scenes before and during the 2026 flood | ~255 MB once |
| `experimento_turbidez_entradas.py` | Experiment: inputs tested for the turbidity model | small |

## Building notebooks, the package and publication

| Script | What it does |
|---|---|
| `build_notebooks.py`, `build_notebooks_semana2.py`, `build_notebooks_semana3.py`, `build_notebooks_modulo_q.py`, `build_notebooks_producao.py` | Write the research notebooks |
| `run_notebooks.py` | Runs a folder of notebooks in order |
| `export_platform_package.py` | Rebuilds the data package of the web application (`plataforma/dados/`) |
| `build_deploy_repo.py` | Builds the published repository from the project folder |
| `publicar_plataforma.py` | One command: pull the published bulletins, rebuild, test, commit, push |
| `capturar_plataforma.py` | Screenshots of the web application (computer and phone widths) |
| `build_documentation.py` | Figures of the English documentation and the link check |
| `build_platform_logos.py` | Logos in the platform colours |
| `modelos_whatsapp.py`, `ver_subscritores.py` | WhatsApp templates; the team's view of sign-ups (Excel) |
| `update_plan_status.py` | Status of every task of the project plan (`docs/estado_do_plano.md`) |
| `build_qgis_project.py` | The QGIS project in `qgis/` |
| `build_print_maps.py`, `build_presentation_figures.py`, `build_social_posts.py` | Print maps, presentation figures, social-media posts |
| `verificar_dominio.py`, `enviar_para_servidor.sh` | Own domain and server (prepared for later) |

## Workshops

| Script | Workshop |
|---|---|
| `download_workshop_scenes.py`, `build_workshop_data.py`, `build_workshop_notebooks.py`, `test_workshop.py`, `build_workshop_manual.py`; texts in `workshop/` | Workshop 1 |
| `build_workshop2_data.py`, `build_workshop2.py`, `build_workshop2_aulas.py`, `build_workshop2_pratica_unica.py`, `test_workshop2.py`, `build_workshop2_docs.py`, `build_workshop2_cronograma_docx.py`, `build_workshop2_certificados.py`, `build_workshop2_slides.py`, `build_workshop2_modulo2.py`; texts and figures in `workshop2/` | Workshop 2 |

See [`workshops/README.md`](../workshops/README.md).
