# 12. Glossary and references

[Documentation home](README.md) · Previous: [11. Validation and limitations](11-validation-and-limitations.md)

## Glossary

| Term | Meaning |
|---|---|
| **AUC (ROC-AUC)** | Probability that the model ranks a random positive case above a random negative one. 0.5 = chance, 1 = perfect. |
| **Composite (monthly)** | One image per month built from all clear images of the month, pixel by pixel (median or a percentile). |
| **CSI** (critical success index) | Hits / (hits + misses + false alarms), for days above a limit. |
| **Discharge (flow)** | Volume of water passing a point of the river per second, in m³/s. |
| **Ensemble (51 scenarios)** | The forecast is run 51 times with slightly different starting conditions; the spread shows the uncertainty. |
| **F1** | Harmonic mean of precision and recall. |
| **FNU** | Formazin Nephelometric Units, the laboratory unit of turbidity. Not used on the public pages. |
| **GloFAS** | Global Flood Awareness System of the Copernicus Emergency Management Service: a global river model (LISFLOOD) with reanalysis and forecasts. |
| **HAND** | Height Above the Nearest Drainage: how many metres a point sits above the nearest stream. |
| **Hydrological year** | October to September, so a whole rainy season falls in one year. |
| **IoU** (intersection over union) | Area mapped as water by both the model and the reference, divided by the area mapped by either. 1 = perfect overlap. |
| **Kappa (Cohen's)** | Agreement between two maps beyond what chance would give. |
| **M2, S2** | The main lunar and solar semi-diurnal tidal constituents (periods of 12.42 and 12 hours). |
| **MNDWI, NDWI** | Water indices from green and short-wave or near infrared; water when above 0. |
| **NDTI** | Normalised Difference Turbidity Index, (red - green) / (red + green): the colour of the water, higher = more sediment. |
| **NDCI** | Normalised Difference Chlorophyll Index, from red edge and red. Follows sediment in this river. |
| **NSE** (Nash-Sutcliffe efficiency) | 1 = perfect, 0 = no better than always predicting the mean. |
| **Percentile** | The value below which a given share of the record falls (the 90th percentile is exceeded on 10 % of days). |
| **Persistence** | The forecast "tomorrow equals today", a baseline every flow model must beat. |
| **POD / FAR** | Probability of detection (share of events forecast) / false alarm ratio (share of forecasts that were wrong). |
| **Precision / recall** | Of the pixels called water, the share that is water / of the water pixels, the share found. |
| **Quantile mapping** | Adjusting one series so its distribution matches a reference (ERA5-Land soil moisture to SMAP). |
| **R²** | Share of the variation explained by a model. |
| **SAR** | Synthetic aperture radar: an active sensor that works day and night and through clouds. |
| **Spatial blocks** | Cutting the map into squares (here 3 km) so training and test pixels are never neighbours. |
| **VV, VH** | Radar polarisations: sent and received vertically (VV), sent vertically and received horizontally (VH). |
| **VV_p10, VH_p10** | The 10th percentile of a month's radar values: its darkest moment, which keeps short floods. |
| **Warning zone** | Where the water arrived in the January 2026 flood: zone 1 first, zone 2 at the largest extent. |
| **XGBoost, HistGradientBoosting, Random Forest** | Ensembles of decision trees: in sequence, each correcting the last (boosting), or in parallel, voting (forest). |

## Institutions

| Acronym | Name |
|---|---|
| ARA-Sul | Administração Regional de Águas do Sul (southern regional water administration, Mozambique) |
| CEMS / EMS | Copernicus Emergency Management Service / its rapid mapping |
| DARA | Development in Africa with Radio Astronomy |
| ECMWF | European Centre for Medium-Range Weather Forecasts |
| ESA | European Space Agency |
| IAU OAD | International Astronomical Union Office of Astronomy for Development |
| INAM | Instituto Nacional de Meteorologia (Mozambique) |
| INGD | Instituto Nacional de Gestão e Redução do Risco de Desastres (Mozambique) |
| JRC | Joint Research Centre of the European Commission |
| MISAU | Ministério da Saúde (Mozambique) |
| WHO / UNICEF | World Health Organization / United Nations Children's Fund |

## References: methods

- Dogliotti, A. I., et al. (2011). *EARSeL eProceedings*, 10(2): near-infrared turbidity algorithm (Table 2, 858 nm:
  A = 3078.9 FNU, C = 0.211). Tested and rejected here.
- Dogliotti, A. I., Ruddick, K. G., Nechad, B., Doxaran, D., Knaeps, E. (2015). A single algorithm to retrieve turbidity
  from remotely-sensed data in all coastal and estuarine waters. *Remote Sensing of Environment*, 156, 157-168.
- Nechad, B., Ruddick, K. G., Park, Y. (2010). Calibration and validation of a generic multisensor algorithm for
  mapping of total suspended matter in turbid waters. *Remote Sensing of Environment*, 114(4), 854-866.
- Lehmann, M. K., et al. (2023). GLORIA, a globally representative hyperspectral in situ dataset for optical sensing of
  water quality (2022 release used). *Scientific Data*, 10, 100.
- Mishra, S., Mishra, D. R. (2012). Normalized difference chlorophyll index. *Remote Sensing of Environment*, 117,
  394-406.
- Lacaux, J. P., Tourre, Y. M., Vignolles, C., Ndione, J. A., Lafaye, M. (2007). Classification of ponds from
  high-spatial resolution remote sensing (NDTI). *Remote Sensing of Environment*, 106(1), 66-74.
- Xu, H. (2006). Modification of normalised difference water index (NDWI) to enhance open water features (MNDWI).
  *International Journal of Remote Sensing*, 27(14), 3025-3033.
- McFeeters, S. K. (1996). The use of the Normalized Difference Water Index (NDWI). *International Journal of Remote
  Sensing*, 17(7), 1425-1432.
- Roy, D. P., et al. (2016). Characterization of Landsat-7 to Landsat-8 reflective wavelength and normalized difference
  vegetation index continuity. *Remote Sensing of Environment*, 185, 57-70.
- Nobre, A. D., et al. (2011). Height Above the Nearest Drainage: a hydrologically relevant new terrain model.
  *Journal of Hydrology*, 404, 13-29.
- Chen, T., Guestrin, C. (2016). XGBoost: a scalable tree boosting system. *Proceedings of KDD*, 785-794.
- Liu, F. T., Ting, K. M., Zhou, Z.-H. (2008). Isolation Forest. *Proceedings of ICDM*, 413-422.
- Hirsch, R. M., Slack, J. R., Smith, R. A. (1982). Techniques of trend analysis for monthly water quality data
  (seasonal Mann-Kendall). *Water Resources Research*, 18(1), 107-121.
- Nash, J. E., Sutcliffe, J. V. (1970). River flow forecasting through conceptual models. *Journal of Hydrology*, 10(3),
  282-290.
- Roberts, D. R., et al. (2017). Cross-validation strategies for data with temporal, spatial, hierarchical, or
  phylogenetic structure. *Ecography*, 40, 913-929.
- World Health Organization (2022). *Guidelines for drinking-water quality*, 4th edition incorporating the first and
  second addenda.

## References: data

- Copernicus Sentinel-1 and Sentinel-2 data, ESA, processed in Google Earth Engine.
- Landsat Collection 2 Level 2, courtesy of the U.S. Geological Survey.
- Copernicus DEM GLO-30, © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018, provided under COPERNICUS by
  the European Union and ESA.
- Yamazaki, D., et al. (2019). MERIT Hydro: a high-resolution global hydrography map. *Water Resources Research*, 55,
  5053-5073.
- Lehner, B., Grill, G. (2013). Global river hydrography and network routing: HydroSHEDS and HydroBASINS.
  *Hydrological Processes*, 27(15), 2171-2186.
- Pekel, J.-F., Cottam, A., Gorelick, N., Belward, A. S. (2016). High-resolution mapping of global surface water and its
  long-term changes. *Nature*, 540, 418-422.
- Brown, C. F., et al. (2022). Dynamic World, near real-time global 10 m land use land cover mapping. *Scientific Data*,
  9, 251.
- Zanaga, D., et al. (2022). ESA WorldCover 10 m 2021 v200.
- Funk, C., et al. (2015). The climate hazards infrared precipitation with stations (CHIRPS). *Scientific Data*, 2,
  150066.
- Huffman, G. J., et al. (2023). GPM IMERG Final Precipitation L3, V07. NASA GES DISC.
- Muñoz-Sabater, J., et al. (2021). ERA5-Land: a state-of-the-art global reanalysis dataset for land applications.
  *Earth System Science Data*, 13, 4349-4383.
- Reichle, R., et al. (2022). SMAP L4 Global 3-hourly 9 km EASE-Grid Surface and Root Zone Soil Moisture, Version 7/8.
  NASA NSIDC DAAC.
- Harrigan, S., et al. (2020). GloFAS-ERA5 operational global river discharge reanalysis 1979-present. *Earth System
  Science Data*, 12, 2043-2060. (GloFAS v4 used here.)
- Copernicus Emergency Management Service (2026). EMSR857, Mozambique, AOI06 Palmeira, delineation products.
- Zippenfenig, P. (2023). Open-Meteo.com Weather API (flood, weather, archive and marine APIs). CC BY 4.0.
- WorldPop (2020). Global High Resolution Population Denominators, University of Southampton.
- Sirko, W., et al. (2021). Continental-scale building detection from high resolution satellite imagery (Google Open
  Buildings).
- FAO (2015). Global Administrative Unit Layers (GAUL).
- OpenStreetMap contributors, © OpenStreetMap, ODbL; GeoNames, CC BY 4.0.
- UN Environment Programme GEMS/Water, GEMStat database (checked: no station in the Incomati basin).
