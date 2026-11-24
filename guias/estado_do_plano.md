# Estado do plano

Gerado por `scripts/update_plan_status.py`. O plano original (`ETE_Project_Plan.xlsx`) não foi alterado; a cópia actualizada é `ETE_Project_Plan_actualizado.xlsx`.

## Week 1: 14 de 15 feitas

| ID | Tarefa | Responsável | Estado | Evidência | Nota |
|---|---|---|---|---|---|
| W1-01 | Kick-off meeting: social problem, beneficiaries, layered architecture, roles and rules | Ezequias Miocha + Amilton Docole | Feito (100 %) | `-` | - |
| W1-02 | Create accounts: GEE, NASA Earthdata, Copernicus Data Space, Copernicus CDS, GitHub | Everyone | Feito (100 %) | `-` | - |
| W1-03 | Define the study area (basin + Marracuene) and the projection EPSG:32736 | Agostinho Oliveira | Feito (100 %) | `data/raw/aoi/` | Bacia, sub-bacia, distrito e grelha comum EPSG:32736. |
| W1-04 | Create GitHub repository, folder structure and naming rules | Ezequias Miocha + Mussa Abdala | Feito (100 %) |  | A pasta do projecto neste computador ainda não é um repositório Git. Estrutura e regras de nomes: README.md. |
| W1-05 | Download static layers: DEM, HAND, WorldCover, JRC GSW, HydroRIVERS | Agostinho Oliveira + Gervasio Mate | Feito (100 %) | `data/raw/static/` | DEM, declive, aspeto, HAND, acumulação de fluxo, WorldCover, JRC, rios. |
| W1-06 | CHIRPS 2006–2026 clipped to the study area | To be assigned | Feito (100 %) | `data/processed/series/rain_daily.csv` | CHIRPS e IMERG diários, bacia e distrito. |
| W1-07 | Monthly Landsat 5/7/8/9 composites (2006–2026) with cloud mask + count of valid observations per pixel, in GEE | Gervasio Mate + Agostinho Oliveira | Feito (100 %) | `data/raw/optical/landsat` | 235 meses com banda n_obs (os meses em falta não tiveram imagem limpa). |
| W1-08 | Monthly Sentinel-1 composites (2014–2026), fixed orbit + observation count, in GEE | Gervasio Mate + Agostinho Oliveira | Feito (100 %) | `data/raw/radar/sentinel1` | 137 meses, órbita ascendente; bandas extra VV_p10 e VH_p10 para cheias curtas. |
| W1-09 | Identify flood events 2006–2026 (JRC monthly + public EMS/UNOSAT maps) | Ezequias Miocha | Feito (100 %) | `data/raw/labels/flood_events/flood_events_catalogue.csv` | EMSR857 (jan 2026) usado como referência independente. |
| W1-10 | Divide the river into sections (border → mouth) and measure river width in each section | Agostinho Oliveira | Feito (100 %) | `data/interim/water_quality/trocos_rio.gpkg` | 9 troços, fronteira à foz; largura em largura_por_troco.csv. Notebook 29. |
| W1-11 | Install ACOLITE and test it on one Sentinel-2 scene of the Incomati | Gervasio Mate + Ezequias Miocha | Feito (100 %) |  | Sem evidência no projecto: o ACOLITE não foi instalado nem corrido neste computador (exige imagens de nível 1, cerca de 1 GB cada). |
| W1-12 | Download the GEMStat archive (Zenodo) and check for stations in the Incomati/Komati basin | To be assigned | Feito (100 %) | `data/raw/water_quality/validacao/gemstat/GEMStat_station_metadata.csv` | Resultado: nenhuma estação na bacia do Incomáti (arquivo de fev 2026, 22 981 estações). |
| W1-13 | Build a Secchi disk and plan measurements on Sentinel-2 pass dates | Gervasio Mate + Glads Sitoe | Feito (100 %) | `docs/protocolo_de_campo_qualidade_da_agua.md` | Decisão da equipa (12/10/2026): não serão feitas medições no local. O protocolo e o calendário ficam guardados para uma fase futura. |
| W1-14 | Budget control for internet/equipment/field work in the data phase | Armenia Machava | Feito (100 %) |  |  |
| W1-15 | Workshop 1 logistics (UEM room, projector, participant list) | Glads Sitoe | Em curso (0 %) |  |  |

## Week 2: 15 de 21 feitas

| ID | Tarefa | Responsável | Estado | Evidência | Nota |
|---|---|---|---|---|---|
| W2-01 | Monthly Sentinel-2 composites (2017–2026), in GEE | Gervasio Mate + Agostinho Oliveira | Feito (100 %) | `data/raw/optical/sentinel2` | 116 meses, 10 m, com banda B5 (red edge). |
| W2-02 | Landsat 5/7 harmonisation → Landsat 8/9 scale (Roy et al., 2016 coefficients) | Gervasio Mate + Ezequias Miocha | Feito (100 %) | `notebooks/semana_2/20_indices_espectrais_e_radar.ipynb` | Coeficientes de Roy et al. testados e mantidos DESLIGADOS: baixam o MNDWI da água de 0,68 para 0,16. Decisão documentada. |
| W2-03 | Indices NDWI, MNDWI, NDVI, NDMI (Landsat and S2) + ΔVV and VV/VH ratio | Gervasio Mate + Agostinho Oliveira | Feito (100 %) | `notebooks/semana_2/20_indices_espectrais_e_radar.ipynb` | NDWI, MNDWI, NDVI, NDMI, razão VV/VH e variação face à referência seca. |
| W2-04 | Reproject and resample all layers to the common grid | Agostinho Oliveira | Feito (100 %) | `data/interim/features` | Stack estático de 13 bandas na grelha comum. |
| W2-05 | Rainfall features: 3/7/14/30-day totals and anomalies (2006–2026) | Ezequias Miocha | Feito (100 %) | `data/processed/series/rain_daily.csv` | Acumulados 3/7/14/30 dias e percentis por época do ano. |
| W2-06 | ERA5-Land (2006–2026), SMAP (2015–2026) and GloFAS (2006–2026) | To be assigned | Feito (100 %) | `data/processed/series/hydromet_daily.csv` | ERA5-Land, SMAP L4 v008 e GloFAS. |
| W2-07 | Quantile mapping: adjust ERA5-Land to the SMAP scale (calibration 2015–2021) | Ezequias Miocha | Feito (100 %) | `data/processed/series/soil_moisture_calibrated_daily.csv` |  |
| W2-08 | Overlap analysis 2017–2021: Landsat×S2, ERA5×SMAP, CHIRPS×IMERG, JRC×S1 (R² and bias) | Ezequias Miocha + Gervasio Mate | Feito (100 %) | `reports/semana_2` | Relatório de sobreposição 2017–2021. |
| W2-09 | Labels: JRC monthly (2006–2021) + EMS/UNOSAT + independent samples drawn in QGIS (2022–2026) | Agostinho Oliveira | Feito (100 %) | `data/raw/labels/ems_unosat/ems_labels.gpkg` | JRC mensal + EMS (120 polígonos). As amostras desenhadas à mão ainda não existem (labels.gpkg vazio). |
| W2-10 | Layer 1 dataset (historical 2006–2026, 30 m) for Model A | Ezequias Miocha | Feito (100 %) | `data/processed/training/train_historico.parquet` | 670 243 linhas. |
| W2-11 | Layer 2 dataset (recent 2015/2017–2026, 10 m) for Model B | Ezequias Miocha | Feito (100 %) | `data/processed/training/train_recente.parquet` | 311 413 linhas. |
| W2-12 | Pure water mask (JRC + inner buffer from banks) per section | Agostinho Oliveira | Feito (100 %) | `data/interim/water_quality/trocos_rio.gpkg` | Camadas agua_permanente, agua_pura_sentinel2, agua_pura_landsat. Feita com Dynamic World (10 m): o JRC (30 m) não vê o rio a montante. A rever no QGIS. |
| W2-13 | Water quality parameters in GEE 2006–2026 (turbidity, TSS, NDCI, floating vegetation, temperature) per section | Ezequias Miocha + Gervasio Mate | Feito (100 %) | `data/raw/water_quality/modulo_q` | NDTI, turbidez, sólidos, NDCI, vegetação e temperatura por imagem e troço, 2006–2026. A montante só Sentinel-2 (rio com menos de 90 m). |
| W2-14 | ACOLITE on a subset of recent Sentinel-2 scenes to calibrate GEE values | Gervasio Mate | Por começar (0 %) |  | ACOLITE não corrido (megas: imagens de nível 1). Em sua vez: concordância entre dois satélites e teste das fórmulas com o GLORIA (notebooks 29 e 37). |
| W2-15 | Module Q dataset (1 row per section and month, all parameters + rain + flow) | Ezequias Miocha | Feito (100 %) | `data/processed/training/qualidade_trocos.parquet` | 1 linha por troço e mês, com chuva e caudal. Notebook 29. |
| W2-16 | 1st field measurement with Secchi disk (Sentinel-2 pass date) | Gervasio Mate + Glads Sitoe | Por começar (0 %) |  | NÃO SERÁ FEITA. Decisão da equipa (12/10/2026): não serão feitas medições no local. |
| W2-17 | Streamlit app skeleton (Quantity and Quality pages, map, layout) | Mussa Abdala | Feito (100 %) | `plataforma/app.py` | Páginas Hoje, Quantidade, Qualidade e Sobre os dados; corre localmente (plataforma/testar_app.py). Feita pelo líder técnico; a rever pelo Mussa. |
| W2-18 | Workshop 1 materials from the Week 1–2 notebooks | Irene Timane | Por começar (0 %) |  |  |
| W2-19 | Design alert levels (green/yellow/orange/red) and simple 'what to do' messages, in Portuguese and local language | Irene Timane + Nilza Taide | Em curso (70 %) | `docs/guia_de_mensagens_de_alerta.md` | Níveis e mensagens em português prontos. Falta a língua local (por falantes nativos) e o teste com a comunidade. |
| W2-20 | Run Workshop 1 (UEM) + OAD surveys with participants | Irene Timane + Amilton Docole | Por começar (0 %) |  |  |
| W2-21 | Photos and video of Workshop 1 | Nilza Taide | Por começar (0 %) |  |  |

## Week 3: 10 de 13 feitas

| ID | Tarefa | Responsável | Estado | Evidência | Nota |
|---|---|---|---|---|---|
| W3-01 | Model B: current flood detection (Random Forest, S1+S2, Layer 2) | Ezequias Miocha | Feito (100 %) | `models/modelo_b_radar.joblib` | XGBoost escolhido entre 4 algoritmos. IoU 0,91, F1 0,95, Kappa 0,89 na cheia de 2026 (blocos espaciais). |
| W3-02 | Model A: flood susceptibility (RF/XGBoost, 20 years, Layer 1) | Ezequias Miocha | Feito (100 %) | `data/processed/maps/modelo_a` | AUC 0,96 em validação e na cheia de 2026. |
| W3-03 | Alert engine: risk (A) × current water (B) × triggers (unusual rain + GloFAS flow) | Ezequias Miocha + Mussa Abdala | Feito (100 %) | `notebooks/semana_3/32_motor_de_alertas.ipynb` | Em produção o alerta vem do caudal e da chuva previstos; o onde vem das zonas de aviso (cheia real de 2026). |
| W3-04 | Validation A (train 2006–2019, tune 2020–21, test 2022–26) and B (spatial blocks + events): IoU, F1, Kappa, ROC-AUC | Ezequias Miocha | Feito (100 %) | `notebooks/semana_3/33_validacao_e_resumo.ipynb` | Limite: toda a validação de cheias assenta num evento (jan 2026). |
| W3-05 | Module Q: climatology per section and month, anomalies (Isolation Forest) and trends (Mann-Kendall) | Ezequias Miocha | Feito (100 %) | `notebooks/semana_3/36_modulo_Q_normais_anomalias_tendencias.ipynb` | Normais, anomalias, Isolation Forest e Mann-Kendall sazonal, com teste à mudança de satélite de 2013. |
| W3-06 | Module Q: rain + flow → expected turbidity model; upstream vs downstream comparison | Ezequias Miocha | Feito (100 %) | `notebooks/semana_3/37_modulo_Q_turbidez_esperada_e_validacao.ipynb` | O modelo mensal previsto no plano não funcionou; ficou um modelo imagem a imagem. Só dá aviso nos troços onde explica o suficiente. |
| W3-07 | Water quality validation: GLORIA + Secchi measurements + GEMStat (if available) | Ezequias Miocha + Gervasio Mate | Feito (100 %) | `reports/semana_3/37_validacao_gloria.csv` | Validação possível concluída: GLORIA feito; GEMStat sem estações na bacia. Sem validação local: Decisão da equipa (12/10/2026): não serão feitas medições no local. |
| W3-08 | 2nd field measurement with Secchi disk | Gervasio Mate + Glads Sitoe | Por começar (0 %) |  | NÃO SERÁ FEITA. Decisão da equipa (12/10/2026): não serão feitas medições no local. |
| W3-09 | Measure the problem with our data: flood months 2006–2026, exposed people and buildings, turbidity trend | Ezequias Miocha + Agostinho Oliveira | Feito (100 %) | `docs/ficha_de_evidencia_do_problema.md` | Notebook 38. |
| W3-10 | Identify community leaders and create the alert channel (WhatsApp) with their consent | Amilton Docole + Glads Sitoe | Por começar (0 %) |  |  |
| W3-11 | GIS post-processing of maps (noise cleaning, flood zone vectorisation) | Agostinho Oliveira | Feito (100 %) | `data/processed/maps/zonas_de_aviso` | Zonas vetorizadas, manchas pequenas removidas, projecto QGIS. |
| W3-12 | Connect the Streamlit app to the first real rasters | Mussa Abdala | Feito (100 %) | `plataforma/dados/catalogo.json` | A app lê camadas reais através do pacote plataforma/dados/ (4,7 MB). |
| W3-13 | Platform visual identity (logo, colours, alert icons) | Nilza Taide | Por começar (0 %) | `docs/guia_de_mensagens_de_alerta.md` | As cores dos alertas já estão fixadas no guia e no catálogo; logótipo e ícones por fazer. |

## Week 4: 1 de 9 feitas

| ID | Tarefa | Responsável | Estado | Evidência | Nota |
|---|---|---|---|---|---|
| W4-01 | Integrate the models in the Streamlit app (Quantity page) | Mussa Abdala + Ezequias Miocha | Em curso (90 %) | `plataforma/app.py` | Página Quantidade pronta e testada (plataforma/testar_app.py). Falta a revisão do Mussa e a identidade visual. |
| W4-02 | Integrate Module Q (map per section, 20-year series, quality alerts) | Mussa Abdala + Ezequias Miocha | Em curso (90 %) | `plataforma/dados/qualidade/estado_por_troco.csv` | Página Qualidade pronta e testada: mapa por troço, séries desde 2006, normais, tendências, alertas. Falta a revisão. |
| W4-03 | Daily automatic pipeline: IMERG/S1 → prediction → map → alert | Ezequias Miocha + Mussa Abdala | Em curso (90 %) | `deploy/ete-plataforma/.github/workflows/boletim_diario.yml` | Boletim diário preparado para correr nos servidores do GitHub (sem computador ligado); ensaiado num clone limpo. Fica a correr depois do passo 3 do guia de deploy. O mapa de radar é mensal, não diário. |
| W4-04 | Exposure analysis (flood × population, buildings, roads) | Agostinho Oliveira | Feito (100 %) | `plataforma/dados/exposicao/exposicao_por_zona.csv` | Área, terras agrícolas, edifícios, escolas, saúde, estradas e pessoas por zona. As pessoas (WorldPop) são um limite superior. A rever pelo Agostinho. |
| W4-05 | Deploy (Streamlit Community Cloud or own server) | Mussa Abdala | Em curso (80 %) | `docs/guia_de_deploy.md` | Repositório de publicação pronto e testado (deploy/ete-plataforma, 11 MB). Falta criar o repositório no GitHub e a app no Streamlit Cloud: precisa da conta da equipa (cerca de 20 minutos, guia passo a passo). |
| W4-06 | Internal tests with the whole team (usability and bugs) | Everyone | Por começar (0 %) | `docs/semana_4_preparacao.md` | Roteiro de testes pronto; os testes automáticos passam. Faltam os testes com pessoas. |
| W4-07 | Technical documentation (README + user manual) | Ezequias Miocha + Irene Timane | Em curso (90 %) | `docs/manual_do_utilizador.md` | README, guia de deploy, manual do utilizador, guias e protocolos feitos. Falta a revisão de linguagem pela Irene. |
| W4-08 | End-to-end alert test: platform → message → community leader | Mussa Abdala + Glads Sitoe | Em curso (50 %) | `docs/teste_alerta_ponta_a_ponta.md` | Parte automática passa (previsão → boletim → mensagem). Falta enviar a um líder e registar a resposta. |
| W4-09 | Community materials: 'what to do in case of an alert' poster + printed risk maps | Nilza Taide + Irene Timane | Em curso (40 %) | `reports/mapas_para_impressao/mapa_zonas_de_aviso_A3.pdf` | Mapas A3 em rascunho técnico. Falta o cartaz e o arranjo gráfico. |

## Buffer: 0 de 6 feitas

| ID | Tarefa | Responsável | Estado | Evidência | Nota |
|---|---|---|---|---|---|
| B-01 | Fix bugs found in internal tests | Mussa Abdala + Ezequias Miocha | Por começar (0 %) |  |  |
| B-02 | Update documentation | Ezequias Miocha | Por começar (0 %) |  |  |
| B-03 | Thematic maps (floods and water quality) for Workshop 2 and the OAD report | Agostinho Oliveira + Nilza Taide | Em curso (30 %) | `reports/mapas_para_impressao` | Rascunhos de cheias; falta o mapa de qualidade da água e o arranjo gráfico. |
| B-04 | Prepare the Workshop 2 demonstration | Irene Timane + Ezequias Miocha | Por começar (0 %) |  |  |
| B-05 | Community Workshop script linked to real problems and to the use of the platform and alerts | Irene Timane + Amilton Docole | Por começar (0 %) |  |  |
| B-06 | Interim progress report to the OAD | Amilton Docole | Por começar (0 %) |  |  |

## Parte I: variáveis

63 de 68 variáveis obtidas ou calculadas; 1 em curso; 4 por começar.

| # | Variável | Prioridade | Estado | Nota |
|---|---|---|---|---|
| 17 | AWEI (sh / nsh) | P2 | Por começar | AWEI não calculado (P2); MNDWI e radar bastaram. |
| 47 | Hand-drawn samples (water / non-water) | P1 | Em curso | Modelo de ficheiro criado, sem amostras desenhadas; a referência independente usada é o EMS. |
| 48 | Labelled S1+S2 reference dataset | P2 | Por começar | Sen1Floods11 não descarregado (P2); não foi preciso pré-treino. |
| 55 | Water reflectance (ACOLITE) | P1 | Por começar | ACOLITE não corrido (megas). |
| 56 | Turbidity (FNU) | P1 | Feito | Estimativa sem calibração local (banda do vermelho). |
| 57 | Suspended sediments — TSS (mg/L) | P1 | Feito | Estimativa; mesma informação da turbidez. |
| 58 | Chlorophyll-a (NDCI → mg/m³) | P1 | Feito | Calculado, mas não reportado como clorofila: no Incomáti segue o sedimento. |
| 59 | Floating aquatic vegetation | P1 | Feito | Fiável nos troços largos; a montante mistura a margem. |
| 60 | Water surface temperature | P2 | Feito | Só nos troços com mais de 300 m de largura. |
| 61 | Estimated transparency (Secchi) | P2 | Feito | Relação ajustada ao GLORIA; sem medições locais. |
| 65 | Global in-situ measurements (GEMStat) | P2 | Feito | Verificado: nenhuma estação na bacia. |
| 67 | Own Secchi disk measurements | P2 | Por começar | Não será feita. Decisão da equipa (12/10/2026): não serão feitas medições no local. |
