# Student workshops

Two one-day workshops for pre-university and university STEM students in Maputo were part of the Eyes to Earth
project. They used the project's own satellite data and models to teach how water and floods are seen from space and
how a machine learns from examples. **The teaching materials are in Portuguese**, the language of the students; this
page explains them in English.

*Em português: cada workshop tem o seu `LEIA-ME.md` com tudo o que é preciso para o preparar e dar.*

| | Workshop 1 | Workshop 2 |
|---|---|---|
| Folder | [`Pratica_Workshop_1/`](Pratica_Workshop_1/LEIA-ME.md) | [`Workshop_2/`](Workshop_2/LEIA-ME.md) |
| Date | Saturday 31 October 2026 | Saturday 21 November 2026, 08:00-14:00 |
| Title | *Ver a água a partir do espaço com satélites e Python* (Seeing water from space with satellites and Python) | *Inteligência Artificial para monitorizar a água e avisar das cheias* (AI to monitor water and warn of floods) |
| What is in this folder | The practical session (12:00-14:00) of a 6-hour day | The whole day: plan, facilitators' manual, practice, student test |
| Students | Pairs who had never programmed | Pre-university STEM students who had never heard of machine learning |
| Where the code runs | Google Colab (only `numpy` and `matplotlib`) | Jupyter Notebook on local computers, no internet needed |
| Core activity | Map the water of the Incomati floodplain with a water index (MNDWI), compare a dry and a wet image, measure the flooded area | Train a model that predicts whether the river water will be turbid tomorrow morning, and discover that the tide is the key clue |
| Data | Landsat 8 and Sentinel-2 scenes of 11 years (2014-2026), 30 m, ready as `.npz` | The same scenes, the Copernicus EMS map of the January 2026 flood, and a table of 2,205 river mornings (colour, flow, rain, tide) |
| Student test | 12 auto-graded questions | 16 auto-graded questions |

## Workshop 1: seeing water from space

```
Pratica_Workshop_1/
├── LEIA-ME.md                         how to prepare and run the session (Portuguese)
├── Workshop_ETE_31Out_Plano_6h.pdf    the plan of the whole day
├── Aula_pratica_1_.ipynb              the team's original notebook (kept unchanged)
├── ETE_Atividade_30m_vs_10m.ipynb     the team's original 30 m vs 10 m activity (kept unchanged)
├── 0_facilitadores/                   facilitators: guide, manual (PDF), solved notebooks, reference answers, slide images
├── 1_introducao_python/               3 short notebooks for students who never programmed: Python, NumPy, Matplotlib
├── 2_aula_guiada/                     the guided lesson, solved together: the January 2026 flood
├── 3_exercicios/ano_AAAA/             10 years, the same steps, a different challenge each year (data in dados/)
└── 4_teste_do_aluno/                  12 questions with automatic correction
```

The ten exercises:

| Year | Theme | Satellite | Difficulty |
|---|---|---|---|
| 2014 | The flood of March 2014 | Landsat 8 | straightforward |
| 2016 | The drought year (El Niño 2015-2016) | Landsat 8 | needs interpretation |
| 2017 | A normal rainy season | Landsat 8 | straightforward |
| 2019 | A year without flood: the "control" | Sentinel-2 | straightforward |
| 2020 | The small flood of February 2020 | Sentinel-2 | needs interpretation |
| 2021 | The flood hidden by clouds | Sentinel-2 | has a trap to investigate |
| 2022 | An image on the day of the peak | Sentinel-2 | needs interpretation |
| 2023 | The great flood of February 2023 | Sentinel-2 | straightforward |
| 2024 | The mystery of the indices | Sentinel-2 | has a trap to investigate |
| 2025 | The flood that got away | Sentinel-2 | needs interpretation |

Two lessons are hidden in the data on purpose: MNDWI fails when the atmospheric correction over-darkens the water
(2022, 2024), and NDWI fails on very turbid flood water (2021).

**To run it:** copy the folder to Google Drive (without `0_facilitadores` for students), open a notebook with Google
Colaboratory, and run the cells in order. Nothing is downloaded during the session; each year has about 12 MB of data.

## Workshop 2: artificial intelligence for water monitoring and flood alerts

```
Workshop_2/
├── LEIA-ME.md                 how to prepare the computers and run the day (Portuguese)
├── 0_facilitadores/           facilitators: day plan and manual (PDF), schedule (Word), slide notes and images,
│   │                          solved lessons with the trained models, reference results, certificate template
│   ├── pratica_unica/         the single practice, solved and run, with notes and timings
│   ├── aulas_resolvidas/      the earlier 8-notebook practice, solved
│   └── arquivo_pratica_antiga/  an earlier version (Parts A-H), not used on the day, kept for reference
├── 1_preparacao_python/       optional: the 3 introduction notebooks of Workshop 1
├── 2_pratica_unica/           THE PRACTICE USED WITH STUDENTS: one 85-minute notebook and its data
├── 2_pratica/                 the earlier practice: 4 guided lessons + 4 practices, tools, data, requirements
├── 3_teste_do_aluno/          16 questions about AI with automatic correction
├── criar_ambiente.sh          creates a Python environment for the workshop (jupyter_env/)
├── abrir_aulas.sh             opens the practice in Jupyter Notebook
└── testar_aulas.py            runs every notebook of the workshop and checks the answers
```

**The single practice** (`2_pratica_unica/Pratica_agua_turva.ipynb`, 85 minutes): pairs open a table of 2,205 river
mornings (2017-2026), choose the clues and the label, split train (2017-2022) and test (2023-2026), train a decision
tree, a random forest and gradient boosting, and find that none beats "always turbid" (65.6 %) until they add the
tide: then 79-83 %. They look at the errors, predict a new morning, and see the whole model in one short script. The
lesson: the right clue matters more than the algorithm. It is the same discovery the project made for the platform
(see [Water quality](../documentation/07-water-quality.md)).

**To run it on Ubuntu with Python 3.10 or newer:**

```bash
cd workshops/Workshop_2
./criar_ambiente.sh          # once: creates jupyter_env/ (about 150 MB of downloads, 700 MB on disk)
./abrir_aulas.sh             # opens the practice in the browser
jupyter_env/bin/python testar_aulas.py   # optional: runs all 23 notebooks (about 1 minute)
```

With Anaconda, open Jupyter Notebook in `2_pratica_unica/` instead. The notebook checks the computer in step 0 and must
say **PRONTO** (ready).

The theory slides were built as web slide decks (HTML slides described by a `deck.json`). Their source is in
[`../reports/apresentacao/workshop2_slides/`](../reports/apresentacao/workshop2_slides) (the full deck) and
[`../reports/apresentacao/workshop2_modulo2/`](../reports/apresentacao/workshop2_modulo2) (module 2, rebuilt in a lighter
version); the figures are in `0_facilitadores/imagens_para_slides/` and the speaker notes in `0_facilitadores/SLIDES.md`.

## How the materials were made

Every notebook and document is **generated by scripts** in [`../scripts/`](../scripts/README.md) and then run, so the
answers in the solved versions are the real outputs of the same code the students run:

| Workshop 1 | Workshop 2 |
|---|---|
| `download_workshop_scenes.py` (Earth Engine scenes, about 200 MB once) | `build_workshop2_data.py` (reuses the Workshop 1 scenes and the project series) |
| `build_workshop_data.py` (`.npz` files and reference answers) | `build_workshop2.py`, `build_workshop2_aulas.py`, `build_workshop2_pratica_unica.py` (notebooks) |
| `build_workshop_notebooks.py` (texts in `scripts/workshop/`) | texts in `scripts/workshop2/` |
| `test_workshop.py` (runs everything as a student) | `test_workshop2.py`, `testar_aulas.py` |
| `build_workshop_manual.py` (facilitators' manual, PDF) | `build_workshop2_docs.py`, `build_workshop2_cronograma_docx.py`, `build_workshop2_certificados.py`, `build_workshop2_slides.py`, `build_workshop2_modulo2.py` |

Notebooks are not edited by hand: change the texts in `scripts/workshop*/` and rebuild.

## What is not in this repository

- The list of participants and the certificates with their names (privacy). Only the blank certificate template is here.
- The Python environment `jupyter_env/` (it is created on each computer by `criar_ambiente.sh`).
- The `.zip` copies made to hand the folders to the computers on the day (they duplicate these folders).
