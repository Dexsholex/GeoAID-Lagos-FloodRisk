# GeoAID

**A Geospatial Disaster Intelligence Framework for Urban Flood Risk Management**

GeoAID is an open, reproducible flood susceptibility and disaster intelligence system built for Amuwo Odofin Local Government Area, Lagos State, Nigeria. It combines fourteen satellite-derived conditioning factors, a validated machine learning model, per-location explainability, and a near-real-time rainfall activation layer, all deployed as a public interactive dashboard.

**Live dashboard:** [geoaid-lagos-flood.streamlit.app](https://geoaid-lagos-flood.streamlit.app)

Built as an MSc dissertation project (Information Technology, AI Specialisation) at Miva Open University, and currently being developed into a peer-reviewed manuscript.

---

## Why this exists

Flood risk management in Lagos has historically operated without spatially validated, explainable, LGA-scale intelligence. Existing work is fragmented across single-hazard studies, relies on expert-assigned risk weights that are never checked against observed flooding, and offers no explanation for why one location is riskier than another. GeoAID was built to close those three gaps in a single system, evaluated honestly, including under a spatial cross-validation standard most comparable work in this space does not apply.

## System architecture

GeoAID is structured as three layers, each answering a distinct question:

| Layer | Question | Approach |
|---|---|---|
| **1. Structural Susceptibility** | Where is inherently flood-prone? | 14 satellite-derived conditioning factors → Random Forest classifier → 4-tier risk map |
| **2. Dynamic Risk Activation** | Is that risk being activated right now? | Near-real-time rainfall (NASA GPM IMERG) compared against the structural risk map |
| **3. Disaster Intelligence** | Who and what is exposed? | WorldPop + OpenStreetMap overlay → population, schools, health facilities, roads at risk |

## Key results

- **Model:** Random Forest selected over Logistic Regression and XGBoost — 0.798 ROC-AUC, 0.755 recall (random 70:30 split, n = 2,652 test samples)
- **Honest evaluation:** Under 5-fold spatial cross-validation (blocks held out, not random pixels), ROC-AUC falls to 0.642 — reported and explained, not concealed
- **Explainability:** SHAP identifies vegetation cover (NDVI) as the dominant driver of flood susceptibility, independently confirmed by the model's own feature importance
- **Exposure:** 229,402 residents (51.6% of the LGA's population), 16 of 35 schools, 55 of 102 health facilities, and 148 of 208 major roads fall within High or Very High risk zones
- **Data integrity:** An early SAR-derived flood inventory misclassified 97.7% of the study area as flooded due to permanent-water contamination; diagnosed and corrected to a physically credible 5.18%, documented in full in `docs/methods_log.md`

## Repository structure

```
GeoAID-Lagos-FloodRisk/
├── notebooks/              # NB01–NB09: acquisition → features → model → SHAP → exposure
├── data/                   # Raw and resampled feature rasters, study area boundary
│   └── resampled/          # Common 100m grid used by the dashboard
├── models/                 # Trained Random Forest, Logistic Regression, XGBoost, scaler
├── outputs/                # Risk maps, probability rasters, exposure tables, figures
│   └── figures/            # Model comparison, SHAP plots, infrastructure map
├── dashboard/
│   ├── app.py               # Streamlit application
│   └── requirements.txt
└── docs/
    └── methods_log.md      # Full running log of every methodological decision and correction
```

## Getting started

**1. Clone and install**
```bash
git clone https://github.com/Dexsholex/GeoAID-Lagos-FloodRisk.git
cd GeoAID-Lagos-FloodRisk
pip install -r dashboard/requirements.txt --break-system-packages
```

**2. Authenticate Google Earth Engine** (required to re-run the acquisition notebooks)
```bash
earthengine authenticate
```

**3. Run the dashboard locally**
```bash
streamlit run dashboard/app.py
```

**Note on live rainfall:** the dashboard's Layer 2 (live rainfall activation) reads current conditions from GPM IMERG via an authenticated Earth Engine session. Locally this uses your own `earthengine authenticate` credential. On a hosted deployment (e.g. Streamlit Community Cloud), it requires a GEE service account key configured via that platform's secrets manager, since there is no persistent local credential cache in that environment.

## Methodology summary

1. **NB01–NB02** — Study area boundary (FAO GAUL) and terrain features (SRTM)
2. **NB03–NB04b** — Climate, land cover, soil, drainage proximity, and antecedent rainfall
3. **NB05** — Flood inventory from Sentinel-1 SAR change detection across 4 verified Lagos flood events (2017–2022), with three-part masking to exclude permanent water
4. **NB06** — Feature matrix assembly, resampled to a common 100m grid (8,839 labelled samples)
5. **NB07** — Model training, comparison, and evaluation under both random and spatial cross-validation
6. **NB08** — SHAP explainability, global and local
7. **NB09** — Population and infrastructure exposure assessment, clipped to the true LGA boundary

Full detail, including every correction and its cause, is in [`docs/methods_log.md`](docs/methods_log.md).

## Known limitations

- Structural susceptibility is not a flood forecast. It classifies where terrain, land cover, and drainage conditions make flooding structurally more likely, not when a specific event will occur.
- Two of the fourteen conditioning factors (CHIRPS rainfall, GPM IMERG) are coarser in resolution than the study area itself, limiting their spatial discriminative power, a contributing factor in the spatial cross-validation gap above.
- The model is trained and validated for Amuwo Odofin LGA only. Transfer to other LGAs, particularly those with different flood mechanisms (riverine/inland vs. coastal/pluvial), has not yet been tested.
- The live rainfall layer depends on an active Earth Engine session and falls back to a cached state if that session is unavailable.

## Roadmap

- [ ] Test model transferability to LGAs with different flood mechanisms
- [ ] Replace SRTM-derived terrain handling with a hydrologically conditioned DEM
- [ ] Provision a GEE service account for continuous, unattended live rainfall operation
- [ ] Explore a constrained, faithfulness-evaluated conversational explanation layer

## Citation

If referencing this work, please cite:

> Oyinloye, O. A. (2026). *Development of a Geospatial Disaster Intelligence Framework for Urban Flood Risk Management.* MSc Dissertation, Department of Information Technology, School of Computing, Miva Open University, Abuja, Nigeria.

A peer-reviewed manuscript based on this work is currently in preparation.

## License

Released under the MIT License. See [`LICENSE`](LICENSE) for details.

## Author

**Oluwasola Abdullahi Oyinloye**
Geospatial Data Scientist · GIS, Remote Sensing & Spatial Analytics
[GitHub](https://github.com/Dexsholex) · o.oyin1115@gmail.com

## Acknowledgements

Built under the supervision of [Supervisor's Name], Department of Information Technology, School of Computing, Miva Open University.
