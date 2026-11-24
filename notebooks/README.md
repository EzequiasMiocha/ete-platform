# Notebooks

The research notebooks of the project, in the order the work was done. They are **in Portuguese** and are
**generated** by `scripts/build_notebooks*.py`: the logic lives in [`src/ete/`](../src/ete), the notebooks call it and
show the results with explanations. To change a notebook, change its builder script and rebuild it.

The saved outputs (figures, tables) are the real results. To run them again you need the raw data (about 43 GB, not in
this repository): the week 1 notebooks download it from Google Earth Engine and the Copernicus data store. See the
[developer guide](../documentation/10-developer-guide.md) and the step-by-step story in
[How we built it](../documentation/03-how-we-built-it.md).

## Week 1: data acquisition (`notebooks/`)

| Notebook | What it does |
|---|---|
| `00_setup_and_authentication` | Credentials, folder tree, check of every dataset ID |
| `01_study_area_aoi` | District, basin, imagery area, the common grid |
| `02_static_layers` | DEM, slope, HAND, flow accumulation, WorldCover, JRC water, rivers, distance to river |
| `03_precipitation_chirps`, `04_precipitation_imerg` | Daily rain |
| `05_landsat_monthly_composites` | Landsat 5/7/8/9 monthly composites, 30 m |
| `06_sentinel1_monthly_composites` | Sentinel-1 VV/VH monthly composites, 10 m |
| `07_sentinel2_monthly_composites` | Sentinel-2 L2A monthly composites, 10 m |
| `08_soil_moisture_era5land_smap` | ERA5-Land and SMAP soil moisture |
| `09_river_discharge_glofas` | GloFAS river discharge |
| `10_surface_water_jrc_and_flood_events` | JRC monthly water and candidate flood events |
| `11_dynamic_world_monthly` | Dynamic World water probability |
| `12_exposure_population_buildings_osm` | WorldPop, Open Buildings, OpenStreetMap |
| `99_data_inventory_and_qc` | Inventory, grid check, monthly coverage |

## Week 2: processing, features and labels (`semana_2/`)

| Notebook | What it does |
|---|---|
| `20_indices_espectrais_e_radar` | Spectral indices, radar dry-season reference |
| `21_stack_estatico_e_grelha_comum` | Terrain stack on the common grid |
| `22_features_de_precipitacao` | Rain sums and percentiles by time of year |
| `23_series_hidrometeorologicas` | Daily and monthly series |
| `24_quantile_mapping_humidade_do_solo` | ERA5-Land soil moisture calibrated to SMAP |
| `25_analise_de_sobreposicao` | Do the sources agree where they overlap? |
| `26_rotulos` | Water and flood labels (JRC, Copernicus EMS) |
| `27_dataset_camada1_historico`, `28_dataset_camada2_recente` | The two training tables (30 m and 10 m) |
| `29_modulo_Q_trocos_e_parametros` | The river cut into nine sections (Module Q) |

## Week 3: models, alerts, water quality (`semana_3/`)

| Notebook | What it does |
|---|---|
| `30_modelo_B_detecao_de_agua_e_cheia` | Model B: water and flood by radar, four algorithms compared |
| `31_modelo_A_suscetibilidade` | Model A: terrain susceptibility |
| `32_motor_de_alertas` | Alert rules replayed on 2006-2026, exposure |
| `33_validacao_e_resumo` | Validation report |
| `34_qualidade_da_agua` | Water colour indices per reach |
| `35_qualidade_da_agua_validacao` | Seven tests of the turbidity indicators; the tide model |
| `36_modulo_Q_normais_anomalias_tendencias` | Normals, anomalies, trends per section |
| `37_modulo_Q_turbidez_esperada_e_validacao` | Expected turbidity, GLORIA validation |
| `38_ficha_de_evidencia_do_problema` | Evidence sheet of the problem |

## Production (`producao/`)

| Notebook | What it does |
|---|---|
| `40_previsao_modelos_e_validacao` | Forecast sources, alert limits, Model C, turbidity model, warning zones |
| `41_boletim_diario` | Today's forecast with charts |

The figures and tables written by these notebooks are in [`reports/`](../reports/README.md).
