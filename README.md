# Eyes to Earth (ETE): water quality and flood alerts for the Incomati River, Marracuene

**Machine learning and satellite data for water-quality monitoring and flood alerts on the lower Incomati River,
Marracuene district, Mozambique.** Every day the platform says, in plain language and in Portuguese, English and
French, how the river water looks and whether the river is likely to flood in the next ten days. It runs on open data
only, by itself, at no hosting cost.

| | |
|---|---|
| **Platform** | <https://ete-platform.streamlit.app> |
| **Light page of the daily bulletin** (weak connections) | <https://ezequiasmiocha.github.io/ete-platform/> |
| **Documentation** (how we built it, how to use it, data, models, tests) | [documentation/](documentation/README.md) |

![The home page of the platform](documentation/figures/platform/home_top.jpg)

## Documentation

| | |
|---|---|
| [Project overview](documentation/01-project-overview.md) | The problem, the two objectives, the study area |
| [Data sources](documentation/02-data-sources.md) | Twenty years of open satellite, climate and river data |
| [How we built it, step by step](documentation/03-how-we-built-it.md) | From the first download to the daily automatic bulletin |
| [Satellite imagery](documentation/04-satellite-imagery.md) | Optical and radar, and the January 2026 flood seen from space |
| [Flood models](documentation/05-flood-models.md) | Radar water (Model B), terrain susceptibility (Model A), warning zones |
| [Flood forecast and alerts](documentation/06-forecast-and-alerts.md) | Alert rules, the 10-day forecast, Model C, the daily bulletin |
| [Water quality](documentation/07-water-quality.md) | Nine river sections, the colour index, the tide, colour forecasts |
| [Platform architecture](documentation/08-platform-architecture.md) | Code, data package, automation, hosting |
| [User guide](documentation/09-user-guide.md) | How to use every page, on a computer or a phone |
| [Developer guide](documentation/10-developer-guide.md) | Install, run, test, update, publish |
| [Validation and limitations](documentation/11-validation-and-limitations.md) | What is proven, what is not, what was rejected |
| [Glossary and references](documentation/12-glossary-and-references.md) | Terms, institutions, sources |

## What is in this repository

This is the published part of the project. The research workspace (about 43 GB of data and the analysis notebooks)
stays on the project computer; the code that built everything is in `src/ete/`.

| What | Where |
|---|---|
| Web application (Streamlit) | `plataforma/app.py` and its modules |
| Data the application shows (about 11 MB) | `plataforma/dados/` (see `plataforma/LEIA-ME.md`) |
| Project library: processing, models, forecast, data package | `src/ete/` |
| Trained models and their metadata | `models/` |
| Daily pipeline and checks | `scripts/` |
| Light bulletin page (GitHub Pages) | `docs/index.html` |
| Daily bulletin, once a day (scheduled 03:15 UTC) | `.github/workflows/boletim_diario.yml` |
| Tests on every change | `.github/workflows/testes.yml` |
| Visit that keeps the application awake | `.github/workflows/manter_acordada.yml` |

Guides in Portuguese: `MANUAL_DO_UTILIZADOR.md` (user manual), `GUIA_DE_DEPLOY.md` (publishing and upkeep),
`ALERTAS_WHATSAPP.md` (WhatsApp alerts), `GUIA_SERVIDOR_PROPRIO.md` and `GUIA_DOMINIO_CO_MZ.md` (own server and domain,
prepared for later).

## Quick start

```bash
python3 -m venv .venv && .venv/bin/pip install -r requirements.txt
.venv/bin/python plataforma/leitor.py --sem-prazo      # the data package is complete
.venv/bin/streamlit run plataforma/app.py              # http://localhost:8501/?lang=en
```

## Important

Experimental service. It does not replace the official warnings of INGD, INAM and ARA-Sul: if the authorities give an
order, follow the order. The colour of the water says how much mud it carries, not whether it is safe: river water must
always be treated before drinking.

Project funded by the IAU Office of Astronomy for Development (OAD), with the support of DARA (Development in Africa
with Radio Astronomy).

Data: Copernicus (Sentinel-1, Sentinel-2, DEM, GloFAS, EMS, ERA5), NASA and USGS (Landsat, IMERG, SMAP), ESA, JRC,
ECMWF, UCSB-CHC (CHIRPS), Google (Dynamic World, Open Buildings), WorldPop, Open-Meteo, OpenStreetMap, GeoNames.

*Em português: a plataforma está em <https://ete-platform.streamlit.app> e o manual do utilizador em
`MANUAL_DO_UTILIZADOR.md`.*
