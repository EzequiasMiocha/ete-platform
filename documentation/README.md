# Eyes to Earth (ETE): documentation

**Machine learning and satellite data for water-quality monitoring and flood alerts on the Incomati River, Marracuene, Mozambique.**

Eyes to Earth is a public web platform that watches the lower Incomati River from space. Every day it tells the
people of Marracuene district two things in plain language: **how the river water looks** (its colour, a proxy for
how much mud it carries) and **whether the river is likely to flood in the next ten days**. It is built only on open
satellite and climate data, runs by itself, and costs nothing to host.

| | |
|---|---|
| Live platform | <https://ete-platform.streamlit.app> |
| Light page of the daily bulletin (for weak connections) | <https://ezequiasmiocha.github.io/ete-platform/> |
| Languages | Portuguese, English, French |
| Status | Experimental. It does **not** replace the official warnings of INGD, INAM and ARA-Sul. |
| Funding | IAU Office of Astronomy for Development (OAD), with the support of DARA (Development in Africa with Radio Astronomy) |

![The home page of the platform](figures/platform/home_top.jpg)

## How to read this documentation

The pages are numbered in reading order, but each one stands on its own. Pick the path that fits you.

| If you want to... | Read |
|---|---|
| Understand the project in ten minutes | [1. Project overview](01-project-overview.md), then the figures of [5](05-flood-models.md) and [7](07-water-quality.md) |
| **Use the platform** | [9. User guide](09-user-guide.md) |
| Know **how we built it, step by step** | [3. How we built it](03-how-we-built-it.md) |
| Check the science: data, models, tests | [2](02-data-sources.md), [4](04-satellite-imagery.md), [5](05-flood-models.md), [6](06-forecast-and-alerts.md), [7](07-water-quality.md), [11](11-validation-and-limitations.md) |
| Run, maintain or extend the software | [8. Platform architecture](08-platform-architecture.md), [10. Developer guide](10-developer-guide.md) |
| Look up a term or a source | [12. Glossary and references](12-glossary-and-references.md) |
| See the student workshops | [workshops/](../workshops/README.md) |

## Contents

1. [Project overview](01-project-overview.md): the problem, the two objectives, the study area, who it is for.
2. [Data sources](02-data-sources.md): every dataset, its period and resolution, and the conventions we follow.
3. [How we built it, step by step](03-how-we-built-it.md): from the first download to the daily automatic bulletin.
4. [Satellite imagery](04-satellite-imagery.md): what optical and radar satellites see, and the January 2026 flood seen from space.
5. [Flood models](05-flood-models.md): Model B (radar water), Model A (terrain susceptibility), warning zones and exposure.
6. [Flood forecast and alerts](06-forecast-and-alerts.md): the alert rules, the 10-day forecast, Model C and the daily bulletin.
7. [Water quality](07-water-quality.md): Module Q, the colour index, the tide discovery and the water-colour forecasts.
8. [Platform architecture](08-platform-architecture.md): code, data package, automation and hosting.
9. [User guide](09-user-guide.md): how to use every page of the platform, on a computer or a phone.
10. [Developer guide](10-developer-guide.md): install, run, test, update and publish.
11. [Validation and limitations](11-validation-and-limitations.md): what is proven, what is not, and what was tested and rejected.
12. [Glossary and references](12-glossary-and-references.md).

Outside this folder: the [student workshops](../workshops/README.md), with their lessons, data, solutions and manuals.

## The project in five numbers

| | |
|---|---|
| **20 years** of open satellite and climate data (2006-2026), about 43 GB | [Data sources](02-data-sources.md) |
| **5 days** of warning: the alert rules turned orange on 12 January 2026; flood water was first mapped at Marracuene on 17 January | [Forecast and alerts](06-forecast-and-alerts.md) |
| **IoU 0.91**: radar flood map against the Copernicus EMS map of the January 2026 flood | [Flood models](05-flood-models.md) |
| **9 river sections**, border to mouth, measured on 5,276 satellite images | [Water quality](07-water-quality.md) |
| **R² 0.19 to 0.68**: what adding the tide did to the water-colour forecast | [Water quality](07-water-quality.md) |

## A rule we never break

> **Never invent data.** A month without a clear image stays empty. A satellite that did not exist in a given year
> is marked as absent. The tests that failed are published next to those that passed. What the satellite does not
> see (germs, chemicals, pH) is said plainly.

## About this repository

This repository holds the whole project except its 43 GB of satellite data: the web application and the small data
package it reads, the library that built everything ([`src/ete/`](../src/ete)), the trained models, every script, the
research notebooks with their results, every figure and table ([`reports/`](../reports/README.md)), the two student
workshops ([`workshops/`](../workshops/README.md)) and the automation that issues the bulletin every day. The map of the
folders is in the [main README](../README.md). The figures of this documentation are drawn from the project's own data
by `scripts/build_documentation.py`.

Practical guides in Portuguese are in [`guias/`](../guias/README.md): user manual, publishing, WhatsApp alerts, own
server and domain, plan status and the technical runbook.
