# EYES TO EARTH (ETE): technical runbook

Every command of the project folder, week by week, with the decisions taken at each step. For an overview read the
[documentation](../documentation/README.md); for the folder map read the [main README](../README.md). The data
described here (2006-2026) follows the variables of the project plan (kept in `plano/`, not published).

## Setup

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
cp .env.example .env            # then fill in EE_PROJECT and CDS_API_KEY
.venv/bin/earthengine authenticate
```

Open the notebooks with the `.venv` interpreter as kernel and run them in order.

## Notebooks

| Notebook | Plan task | Data | Output folder |
|---|---|---|---|
| `00_setup_and_authentication` | S1-02 | credentials, folder tree, check of all dataset IDs | `data/metadata/` |
| `01_study_area_aoi` | S1-03 | district, basin, AOI, common grid | `data/raw/aoi/` |
| `02_static_layers` | S1-05 | DEM, slope, aspect, HAND, flow accumulation, WorldCover, JRC GSW, rivers, distance to river | `data/raw/static/` |
| `03_precipitation_chirps` | S1-06 | CHIRPS daily | `data/raw/precipitation/chirps/` |
| `04_precipitation_imerg` | - | GPM IMERG daily | `data/raw/precipitation/imerg/` |
| `05_landsat_monthly_composites` | S1-07 | Landsat 5/7/8/9, 30 m | `data/raw/optical/landsat/` |
| `06_sentinel1_monthly_composites` | S1-08 | Sentinel-1 VV/VH, 10 m | `data/raw/radar/sentinel1/` |
| `07_sentinel2_monthly_composites` | - | Sentinel-2 L2A, 10 m | `data/raw/optical/sentinel2/` |
| `08_soil_moisture_era5land_smap` | - | ERA5-Land, SMAP L4 | `data/raw/hydromet/` |
| `09_river_discharge_glofas` | S1-09 | GloFAS discharge | `data/raw/discharge/glofas/` |
| `10_surface_water_jrc_and_flood_events` | S1-09 | JRC monthly water, flood-event candidates | `data/raw/labels/` |
| `11_dynamic_world_monthly` | - | Dynamic World water probability | `data/raw/land_cover/dynamic_world/` |
| `12_exposure_population_buildings_osm` | - | WorldPop, Open Buildings, OSM | `data/raw/exposure/` |
| `99_data_inventory_and_qc` | - | inventory, grid check, monthly coverage | `data/metadata/` |

The notebooks are generated from `scripts/build_notebooks.py`; the download logic
is in `src/ete/`. To change a recipe permanently, edit those and rebuild.

## Week 2 - processing, features and labels

No internet needed. Notebooks are in `notebooks/semana_2/` and are generated from
`scripts/build_notebooks_semana2.py`. Run them in order (or all at once with
`python scripts/run_notebooks.py notebooks/semana_2`).

| Notebook | Plan task | Output |
|---|---|---|
| `20_indices_espectrais_e_radar` | S2-02, S2-03 | Sentinel-1 dry reference, index rasters for chosen months |
| `21_stack_estatico_e_grelha_comum` | S2-04 | `data/interim/features/static_stack_*_30m.tif`, alignment check |
| `22_features_de_precipitacao` | S2-05 | `data/processed/series/rain_daily.csv`, `rain_monthly.csv` |
| `23_series_hidrometeorologicas` | S2-06 | `hydromet_daily.csv`, `hydromet_monthly.csv` |
| `24_quantile_mapping_humidade_do_solo` | S2-07 | `soil_moisture_calibrated_*.csv` |
| `25_analise_de_sobreposicao` | S2-08 | `reports/semana_2/25_sobreposicao_resumo.csv` + figures |
| `26_rotulos` | S2-09 | `data/raw/labels/manual/labels.gpkg` (template), candidate months |
| `27_dataset_camada1_historico` | S2-10 | `data/processed/training/train_historico.parquet` |
| `28_dataset_camada2_recente` | S2-11 | `data/processed/training/train_recente.parquet` |

Each training table comes with a data dictionary (`*_dicionario.csv`) and a
metadata file (`*.meta.json`). Figures and tables for the OAD report are written
to `reports/semana_2/`.

Decisions recorded during weeks 1-2 (see the notebooks for the evidence):

- Landsat 5/7 harmonisation (Roy et al., 2016) is **not** applied: it lowered the
  water MNDWI of Landsat 7 from 0.68 to 0.16 over the study area.
- SMAP uses collection version 008 (version 007 stopped in June 2025).
- The Sentinel-1 composites mix relative orbits 145 and 72 of the ascending pass;
  2015 has orbit 145 only. `s1_angle`, `dvv_rel` and `dvh_rel` are provided so
  models can account for it.
- `jrc_occurrence` and same-month Landsat columns must not be used as Model A
  features (they leak the label).

## Week 3 - models, alerts and validation

No internet needed. Notebooks are in `notebooks/semana_3/`, generated from
`scripts/build_notebooks_semana3.py`.

| Notebook | Plan task | Output |
|---|---|---|
| `30_modelo_B_detecao_de_agua_e_cheia` | S3-01, S3-05 | `models/modelo_b_radar.joblib`, maps in `data/processed/maps/modelo_b/` |
| `31_modelo_A_suscetibilidade` | S3-02 | `models/modelo_a_terreno.joblib`, `data/processed/maps/modelo_a/` |
| `32_motor_de_alertas` | S3-03 | alert rules, backtest and exposure tables in `reports/semana_3/` |
| `33_validacao_e_resumo` | S3-04 | `reports/semana_3/33_relatorio_de_validacao.csv` |
| `34_qualidade_da_agua` | variables #51, #52 | `data/processed/series/qualidade_agua_mensal.csv`, maps in `data/processed/maps/qualidade_agua/` |
| `35_qualidade_da_agua_validacao` | variables #51, #52 | seven tests of the turbidity indicators; `models/modelo_turbidez.joblib`, `models/turbidez_por_caudal.json` |

`scripts/run_model_b_maps.py` writes the monthly water/flood maps for every
Sentinel-1 month. Four algorithms (logistic regression, Random Forest, HistGradientBoosting,
XGBoost) are compared in notebooks 30 and 31 with a selection rule stated beforehand. Model B is validated by 3 km spatial blocks on the January
2026 flood mapped by Copernicus EMS (EMSR857); Model A is tested on the same
event, which it never saw. Both are single-event tests: see notebook 33 for what
is and is not proven.

## Production - daily forecast and bulletin

```bash
.venv/bin/python scripts/run_daily_forecast.py             # needs internet (a few KB)
.venv/bin/python scripts/run_daily_forecast.py --offline   # reuse the last stored forecast
.venv/bin/python scripts/check_forecast_system.py          # offline self-test (replays the January 2026 flood)
```

To run every day at 06:00, add to `crontab -e`:

```
0 6 * * * cd /path/to/Projecto-ETE && .venv/bin/python scripts/run_daily_forecast.py >> data/metadata/previsao_diaria.log 2>&1
```

What it does: fetches 51 discharge scenarios for the Incomati at Marracuene (GloFAS v4) and
the basin rain forecast (ECMWF IFS), both through Open-Meteo (free, no key, CC BY 4.0; check
its terms before any commercial use), checks them, applies the alert limits in
`models/limites_previsao.json`, adds our own discharge model (Model C) as a second opinion and
the turbidity outlook per river reach, and writes the bulletin.

| File in `data/processed/forecast/latest/` | Content |
|---|---|
| `estado.json` | when the data was fetched, whether it is fresh, problems found - **read this first** |
| `boletim.json`, `boletim.md` | the bulletin for the platform and for people |
| `previsao_alertas.csv` | alert level, discharge scenarios summary and rain, per day |
| `cenarios_caudal.csv`, `chuva_bacia.csv`, `turbidez.csv`, `turbidez_diaria.csv` | the underlying series |

Rules built into the code:

- If today's data cannot be fetched or fails the checks, the bulletin says "previsão
  indisponível". It never shows green for lack of data.
- Without a connection the last stored forecast is reused and flagged as a copy; it is flagged
  as out of date after 36 hours.
- Every run is archived under `data/processed/forecast/archive/<date>/` and the raw answers
  under `data/raw/forecast/runs/<date>/`, so forecasts can later be verified
  (`ete.operations.verification`).
- Warning zones come from where the water went in the January 2026 flood
  (`data/processed/maps/zonas_de_aviso/`), not from the susceptibility classes.

Water quality in production (evidence in notebook 35):

- The product is the **measurement** of water colour (NDTI) per river reach from every clear
  Sentinel-2 image. Sentinel-2 and Landsat 8/9, two independent satellites, agree on the same
  day (r = 0.92, 261 pairs). Update the series weekly with
  `.venv/bin/python scripts/update_water_quality_scenes.py` (Earth Engine, a few hundred KB).
- Turbidity in physical units with the near-infrared band (Dogliotti et al. 2011) was tested and
  **rejected**: the two satellites disagree (r = 0.21). The red-band version (Dogliotti et al.
  2015) agrees better (r = 0.85, typical factor 1.5) and is kept in Module Q as an estimate
  only; the public pages show classes, not FNU.
- A model with discharge, rain and time of year alone did not beat the time of year (R2 0.19).
  Adding the tide did (R2 0.60 with the phase of the main lunar tide alone). The final model
  (`forecast_models.fit_turbidity_model`, saved as `models/modelo_turbidez.joblib`) uses the
  computed tide at the satellite hour (height, rising or falling, range) and the latest
  satellite measurement of the reach from either satellite. Each year predicted by a model
  that never saw it: R2 0.65-0.68 and AUC 0.87-0.89 depending on the age of the latest
  measurement (0.61 / 0.85 with no measurement in 30 days). Trained on Sentinel-2 and tested on
  Landsat 8/9 before 2017 (another satellite, other years): R2 0.59, AUC 0.88.
- The tide is computed from 22 harmonic constants fitted to the hourly sea level of Maputo Bay
  (Open-Meteo marine service, 2023-2026, 0.8 MB in `data/raw/tide`; `models/mare_maputo.json`).
  It reproduces 98.7 % of the variance of the 12 months left out of the fit. No tide gauge.
- Tested and not used (no gain in the probability of elevated turbidity): wind, local rain,
  rain per part of the basin, training on both satellites
  (`scripts/experimento_turbidez_entradas.py`). The upstream reach still has no forecast.
- The forecast is the probability of "more turbid than usual" for each of the next 10 mornings
  in the three reliable reaches. It holds for the satellite overpass time only (about 09:30
  local) and is a relative colour index. Keep the image series up to date (weekly).
- Vegetation on the water (share of the channel that is green, per month and reach) is in
  `data/processed/series/vegetacao_no_rio_mensal.csv` (notebook 34). It matters only in the
  upstream reach; the species and the 2018 peak need checking on site.
- Field protocol to turn the index into turbidity units: `docs/protocolo_de_campo_qualidade_da_agua.md`.
- The table per discharge class (14 % of days elevated below 20 m3/s, 79 % above the orange
  limit) is kept as the plain explanation of the flood effect.
- The bulletin reports the median state of the last 20 days, not a single image (single images
  swing with the tide in the lower reaches).

Place names: `ete.places` joins OpenStreetMap and GeoNames names to the warning zones and
orders them by when the water arrived in January 2026
(`data/processed/maps/zonas_de_aviso/lugares_por_ordem_de_alagamento_marracuene.csv`). The
names must be validated locally before publication (column `validado`).

Notebooks: `notebooks/producao/40_previsao_modelos_e_validacao` (sources, limits, model skill,
warning zones) and `41_boletim_diario` (today's forecast with charts). Retrain the forecast
models by re-running notebook 40. The bulletin is experimental and does not replace the
official warnings of INGD, INAM and ARA-Sul.

## Module Q - water quality per river section, border to mouth

The plan (`ETE_Project_Plan.xlsx`) asks for the whole river in Mozambique, 2006-2026.
`docs/estado_do_plano.md` lists every task of the plan with its state and evidence
(`scripts/update_plan_status.py` rebuilds it and writes `ETE_Project_Plan_actualizado.xlsx`;
the original plan file is never changed).

```bash
.venv/bin/python scripts/update_module_q_series.py     # Earth Engine tables, about 10 MB the first time
.venv/bin/python scripts/build_notebooks_modulo_q.py   # notebooks 29, 36, 37, 38
```

| Notebook | Plan task | Output |
|---|---|---|
| `semana_2/29_modulo_Q_trocos_e_parametros` | W1-10, W2-12, W2-13, W2-15 | `data/interim/water_quality/trocos_rio.gpkg`, `largura_por_troco.csv`, `data/processed/training/qualidade_trocos.parquet` |
| `semana_3/36_modulo_Q_normais_anomalias_tendencias` | W3-05 | normal values, anomalies, Isolation Forest, seasonal Mann-Kendall |
| `semana_3/37_modulo_Q_turbidez_esperada_e_validacao` | W3-06, W3-07 | expected turbidity, upstream vs downstream, GLORIA validation, GEMStat check |
| `semana_3/38_ficha_de_evidencia_do_problema` | W3-09 | `docs/ficha_de_evidencia_do_problema.md` |

What was found (code in `src/ete/module_q.py`, `module_q_analysis.py`):

- Nine sections, Q1 (border, Ressano Garcia) to Q9 (estuary). From the border to near Manhiça
  the river is 50-80 m wide: under three Landsat pixels, so only Sentinel-2 (2017 onwards) is
  used there. The 20-year record exists for Q7-Q9.
- The JRC permanent-water map (30 m) misses the upstream river; the water mask comes from the
  Dynamic World water frequency (10 m). It is automatic and should be checked in QGIS.
- NDTI is repeatable between Sentinel-2 and Landsat 8/9 (r 0.85 over 438 same-day pairs).
  Sections Q3 and Q6 are flagged `fiabilidade reduzida` (r 0.15 and 0.53): no alerts there.
- Turbidity (Dogliotti 2015, red band) and suspended solids (Nechad 2010) are estimates: the two
  satellites differ by a typical factor of 1.5, and on GLORIA's in-water measurements the
  formulas are unbiased but off by a typical factor of 2.5. Coefficients checked against the
  files distributed with ACOLITE. ACOLITE itself was not run (level-1 scenes, about 1 GB each).
- NDCI is computed but not reported as chlorophyll (it follows sediment in this river).
- Trends: none of the 20-year trends is confirmed once the 2013 change of satellite is tested.
  Upstream, 2017-2026 goes from clear water (drought years) to turbid water (wet years).
- "Turbidity expected from rain and flow": the monthly model of the plan did not work; the
  image-by-image model only has skill at the estuary (R2 0.52). Elsewhere no "unexplained
  turbidity" flag is given.
- The border section does not predict the colour at Marracuene (monthly correlation -0.06).
- GEMStat has no station in the Incomati basin, and the team decided (12 Oct 2026) not to take
  field measurements in this phase. There is therefore no local validation: Module Q is a
  relative indicator (colour against its own normal), and FNU, mg/L and Secchi values stay
  estimates that must not be shown to the public as measurements.

Other deliverables of the plan: `docs/guia_de_mensagens_de_alerta.md` (W2-19),
`scripts/test_alert_end_to_end.py` and `docs/teste_alerta_ponta_a_ponta.md` (W4-08),
`scripts/build_print_maps.py` and `reports/mapas_para_impressao/` (W4-09, B-03).

Presentation and social-media figures (PT and EN, nothing is downloaded unless stated):

```bash
.venv/bin/python scripts/download_flood_scenes.py        # single-day Landsat/Sentinel-2 scenes, before and during the Jan 2026 flood (~255 MB once)
.venv/bin/python scripts/build_presentation_figures.py   # reports/apresentacao/{pt,en}/ (7 figures, 16:9) + the PDFs
.venv/bin/python scripts/build_social_posts.py           # reports/redes_sociais/ (LinkedIn/Facebook carousel, 4:5)
```

Student workshop 1 (31 Oct 2026), practical session in `workshops/Pratica_Workshop_1/` (see its `LEIA-ME.md`):

```bash
.venv/bin/python scripts/download_workshop_scenes.py    # 22 single-day scenes, 11 years, floodplain at 30 m (~200 MB once)
.venv/bin/python scripts/build_workshop_data.py         # light .npz files for students + reference answers
.venv/bin/python scripts/build_workshop_notebooks.py    # all notebooks and texts (generated: do not edit by hand)
.venv/bin/python scripts/test_workshop.py               # runs everything as a student (about 12 minutes)
.venv/bin/python scripts/build_workshop_manual.py      # facilitators' manual in PDF (via LibreOffice; run after the test)
```

Student workshop 2 (21 Nov 2026, AI for water monitoring and flood alerts, 08:00-14:00) in `workshops/Workshop_2/` (see its
`LEIA-ME.md`). Theory slides (104, one idea per slide, white academic style, no blue): Claude artifact linked in
`workshops/Workshop_2/0_facilitadores/SLIDES.md`, generated from `scripts/workshop2/slides*.py` (the slide order in
`slides_ordem.py` is the single source of the slide numbers in the plan, the manual and the Word schedule).
The practice runs locally in Jupyter Notebook (no Colab, no Internet) and trains the three model types of the theory:
classification (Random Forest and three other algorithms), clustering (K-means) and regression (discharge 3 days
ahead, GloFAS + CHIRPS). Notebooks 2, 3 and 5 start with a configuration panel (`CONFIG`); the pure-Python scripts read
`2_pratica/configuracao.json` (validated, with `_ajuda` notes), accept command-line overrides and save each run
(figure, scores, model, config used) in `2_pratica/resultados/`. Part H (`5_nivel_avancado.ipynb`, optional) covers
cross-validation by year, grid search, threshold/ROC, permutation importance, learning curve, saving models, the
K-means silhouette and three regression models with POD/FAR. No download needed (reuses the workshop 1 scenes and the
project series):

```bash
.venv/bin/python scripts/build_workshop2_data.py                     # practice data (.npz, discharge/rain csv), EMS exam, team points
cd scripts && ../.venv/bin/python -m workshop2.referencia && cd ..   # reference results (same code as the notebooks)
.venv/bin/python scripts/build_workshop2.py                          # notebooks A-F and H, computer check, 3 scripts + configuracao.json, student test
.venv/bin/python scripts/test_workshop2.py                           # runs everything as a student, changes the CONFIG panels, scripts with errors (about 15 minutes)
cd scripts && ../.venv/bin/python -m workshop2.figuras && cd ..      # slide images (maps, project charts)
cd scripts && ../.venv/bin/python -m workshop2.figuras_teoria && cd ..   # theory charts (classification, regression, K-means, overfitting)
.venv/bin/python scripts/build_workshop2_slides.py                   # the 104 slides -> reports/apresentacao/workshop2_slides/project (publish to the artifact)
.venv/bin/python scripts/build_workshop2_docs.py                     # day plan + facilitators' manual (PDF) + SLIDES.md
.venv/bin/python scripts/build_workshop2_certificados.py             # certificates from certificados/participantes.csv
.venv/bin/python scripts/build_workshop2_cronograma_docx.py          # the day schedule only, in Word (.docx, one A4 landscape page)
```

Monthly composites (median of the month) erase a flood that lasts a few days, so figures of the
flood use the single-day scenes in `data/raw/optical/cenas_cheia_2026/`. Catalogue cloud cover is
per tile: choose dates by the cloud measured inside the district. Revisit times are checked
against the real pass dates over Marracuene (`reports/apresentacao/passagens_2025_2026.csv`).

## Week 4 - platform package and daily pipeline

```bash
.venv/bin/python scripts/run_daily_pipeline.py            # every day: images (weekly), forecast, bulletin, package
.venv/bin/python scripts/run_daily_pipeline.py --offline  # no internet: reuse what is stored
.venv/bin/python scripts/export_platform_package.py       # rebuild the whole package (after new models or monthly maps)
python plataforma/leitor.py                               # check the package: must end with PACOTE COMPLETO
```

`plataforma/dados/` (about 4 MB, EPSG:4326) is all the web application needs: PNG overlays with
their corner coordinates, GeoJSON layers, the latest bulletin, the series behind the charts and
`catalogo.json` (titles, legends, colours and limits of every layer). `plataforma/leitor.py`
reads it; `plataforma/app.py` is the Streamlit application (pages Hoje, Quantidade, Qualidade,
Sobre os dados; `cd plataforma && streamlit run app.py`; `python testar_app.py` runs every page
without a browser). `app_exemplo.py` is the earlier minimal example. Rules for the application are in
`plataforma/LEIA-ME.md`; the state of each week-4 task and the open decisions are in
`docs/semana_4_preparacao.md`.

The daily cron line should now call the pipeline instead of `run_daily_forecast.py`:

```
0 6 * * * cd /path/to/Projecto-ETE && .venv/bin/python scripts/run_daily_pipeline.py >> data/metadata/pipeline_diario.log 2>&1
```

The monthly radar water maps (Model B) are not part of the daily pipeline: a new month needs
its Sentinel-1 composite (about 120 MB) and `scripts/run_model_b_maps.py`.

## Deployment

```bash
.venv/bin/python scripts/publicar_plataforma.py               # one command: pull, rebuild, check, commit, push
.venv/bin/python scripts/publicar_plataforma.py --verificar   # rebuild and check only, nothing is sent
.venv/bin/python scripts/build_deploy_repo.py                 # (called by the above) builds deploy/ete-plataforma/ (about 12 MB)
```

`deploy/ete-plataforma/` is a standalone Git repository, ready for GitHub: the Streamlit
application, the data package, the light static bulletin page (`docs/index.html`, for GitHub
Pages), only the code, models and small data the daily bulletin needs, pinned requirements, and
two workflows: `boletim_diario.yml` (runs the bulletin every day at 03:15 UTC on GitHub's
servers and commits the result, so no team computer has to stay on) and `testes.yml` (package,
every page of the application, the alert message). It was rehearsed from a clean clone.
`publicar_plataforma.py` pushes with a repository deploy key (`~/.ssh/ete_github_deploy`, SSH host alias
`github-ete`), first pulls the bulletins committed by GitHub, and sends nothing if a check fails.
The steps on GitHub and Streamlit Community Cloud, upkeep
and troubleshooting are in `docs/guia_de_deploy.md`; the public addresses go in the
`publication` section of `config/config.yaml`. End-user help: `docs/manual_do_utilizador.md`.

## Repository layout

```
config/config.yaml      study area, grid, periods, dataset IDs, folders (single source of truth)
src/ete/                week 1: config, grid, gee, datasets, series
                        week 2: features, rasters, drivers, overlap, training, labels
                        week 3: models, alerts, plots, water_quality
                        production: forecast, forecast_models, operations, places
                        week 4: platform (export of the web-ready package)
                        module Q: module_q (sections, Earth Engine extraction), module_q_analysis
scripts/                build_notebooks*.py, run_notebooks.py (notebooks are generated, do not edit by hand)
                        run_daily_pipeline.py, run_daily_forecast.py, check_forecast_system.py
                        export_platform_package.py, update_water_quality_scenes.py, run_model_b_maps.py
                        build_qgis_project.py, experimento_turbidez_entradas.py
                        download_flood_scenes.py, build_presentation_figures.py, build_social_posts.py
notebooks/              week 1 (one per data type), semana_2/, semana_3/, producao/
plataforma/             dados/ (package), leitor.py (reader), app.py, testar_app.py, LEIA-ME.md
models/                 trained models (.joblib) and their metadata (.json)
docs/                   estado_do_plano.md, semana_4_preparacao.md, ficha_de_evidencia_do_problema.md,
                        guia_de_mensagens_de_alerta.md, teste_alerta_ponta_a_ponta.md, protocolo_de_campo_qualidade_da_agua.md
qgis/                   QGIS project and guide
reports/                figures and tables for the OAD report; apresentacao/ (slides), redes_sociais/ (posts)
data/raw/               downloads, exactly as obtained (never edited by hand)
data/interim/           derived helper products (area-mean series, distance to river)
data/processed/         features, training tables, maps, series, forecast (latest, archive)
data/metadata/          download_manifest.csv, inventory.csv, gee_catalogue_check.csv, logs
```

## Conventions

- **Grid.** Every raster is downloaded on one fixed grid in EPSG:32736
  (`data/raw/aoi/grid.json`): 30 m for the historical layer, 10 m nested in it for
  the Sentinel layer. Coarse products (rain, soil moisture, discharge) stay on
  their native lat/lon grid and cover the whole basin.
- **File names.** `<dataset>_<aoi>_<YYYY-MM>_<res>m.tif` in a folder per year;
  daily series are `<dataset>_<variable>_<aoi>_<YYYY>.nc`.
- **Integer storage.** Monthly imagery is stored as int16: reflectance and
  Dynamic World probabilities x10000, Sentinel-1 dB and angle x100; `n_obs` and
  class bands are unscaled. The factor is saved in the GeoTIFF band scale. Read
  rasters with `ete.series.read_scaled()`, which returns physical values.
- **Mask.** Monthly imagery outside the district + buffer polygon is nodata.
- **Nodata.** -9999 for float and int16 rasters, 255 for uint8. A pixel or a month with no
  observation stays missing; nothing is interpolated or filled.
- **`n_obs` band.** Each monthly composite stores the number of clean observations
  per pixel.
- **Manifest.** Each download adds a row to `data/metadata/download_manifest.csv`
  with the source ID, period and status (`downloaded`, `absent`, `failed`).
- **Resumable.** Existing files are skipped; partial files are named `*.part.*`.
- **Data is not committed** to git (see `.gitignore`), only the AOI, the manifest
  and the event catalogue.

## Data sources to cite

Copernicus (Sentinel-1/2, DEM, GloFAS, ERA5-Land/ECMWF), USGS/NASA (Landsat, GPM
IMERG, SMAP), CHC/UCSB (CHIRPS), JRC (Global Surface Water), ESA (WorldCover),
MERIT Hydro, HydroSHEDS/WWF, FAO GAUL, WorldPop, Google (Open Buildings, Dynamic
World), OpenStreetMap contributors.
