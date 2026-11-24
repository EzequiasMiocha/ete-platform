# Data

The project uses about **43 GB** of data (satellite images, climate, labels), downloaded by the week 1 notebooks from
Google Earth Engine, the Copernicus data store and other open sources. That is too large for GitHub, so this folder holds
only the **small files** that the daily bulletin needs or that describe the rest. Everything else can be rebuilt by
running the notebooks (see [notebooks/README.md](../notebooks/README.md) and the
[data sources](../documentation/02-data-sources.md)).

| Folder | In this repository | Content |
|---|---|---|
| `raw/aoi/` | Yes | District, basin, imagery area (GeoJSON), the common grid (`grid.json`) |
| `raw/forecast/` | Yes | Discharge and rain history used by the forecast, the latest raw forecast runs (updated every day by GitHub Actions) |
| `raw/tide/` | Yes | Hourly sea level of Maputo Bay (fits the tide constants) |
| `raw/places/` | Partly | OpenStreetMap places and administrative posts (the GeoNames dump is not included) |
| `raw/water_quality/` | Yes (tables) | Water colour per satellite image and river section |
| `raw/labels/flood_events/` | Yes | Catalogue of candidate flood events, JRC monthly water area |
| `metadata/` | Yes | Download manifest, data inventory, catalogue check |
| `processed/series/` | Yes | Daily and monthly series: rain, discharge, soil moisture, alerts, radar flood area, water colour, vegetation |
| `processed/forecast/` | Yes | Latest bulletin and archive of the daily forecasts |
| `processed/training/` | Dictionaries only | The training tables (670,243 and 311,413 rows) are not included; their data dictionaries and metadata are |
| `processed/water_colour/` | One file | The daily colour at Marracuene used by the 30-day forecast |
| `raw/optical`, `raw/radar`, `raw/land_cover`, `raw/labels`, `raw/exposure`, `interim/`, `processed/maps/` | No | Satellite images, labels, exposure layers and maps (tens of GB) |
| `private/` | **Never** | WhatsApp sign-ups and accounts (phone numbers): never published |

Conventions: one UTM 36S grid (30 m nesting 10 m), rasters stored as int16 with the scale in the file, nothing is gap
filled. See [data sources](../documentation/02-data-sources.md#conventions).
