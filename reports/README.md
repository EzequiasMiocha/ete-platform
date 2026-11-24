# Reports: figures and tables

Every figure and table produced during the project, grouped by stage. Labels are mostly in Portuguese; the main
figures were redrawn in English for the [documentation](../documentation/README.md).

| Folder | Content | Made by |
|---|---|---|
| `semana_2/` | Week 2: indices, flood vs dry, radar threshold, terrain stack, rain indicators, source overlap, labels, Module Q sections | notebooks 20-29 |
| `semana_3/` | Week 3: Models A and B (algorithms, features, maps, tests), alert rules and lead times, exposure, water quality tests, Module Q normals and trends | notebooks 30-38 |
| `producao/` | Production: forecast sources, alert limits, Model C, turbidity model, warning zones, January 2026 replay | notebook 40 |
| `apresentacao/pt`, `apresentacao/en` | Presentation figures in Portuguese and English (study area, natural colour, Landsat vs Sentinel-2, river widths, orbits, the 2026 flood), with PDFs | `scripts/build_presentation_figures.py` |
| `apresentacao/workshop2_slides/`, `apresentacao/workshop2_modulo2/` | Source of the Workshop 2 slide decks (HTML slides and `deck.json`) | `scripts/build_workshop2_slides.py`, `build_workshop2_modulo2.py` |
| `apresentacao/passagens_2025_2026.csv` | Measured satellite passes over Marracuene | `build_presentation_figures.py` |
| `mapas_para_impressao/` | A3 maps to print: susceptibility and warning zones (PDF and PNG) | `scripts/build_print_maps.py` |
| `redes_sociais/` | Social-media carousel (English; Portuguese in `pt/`) and the post text | `scripts/build_social_posts.py` |
| `plataforma/` | Screenshots of earlier designs of the web application (`v4` to `v9` and the first pages) | `scripts/capturar_plataforma.py` |

Not included: the raw screenshot sessions (`plataforma/capturas/`) and the browser profile used to take them.
