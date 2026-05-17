# GeoAID Project — Running Methods and Statistics Log
# Updated after each notebook session
# This document feeds directly into Chapter 3 (Methodology) and Chapter 4 (Results)

---

## Notebook 01 — Study Area Definition
- Dataset: FAO GAUL 2015 Level 2
- GEE filter fix: used stringContains() due to leading space in ' Amuwo Odofin' GAUL entry
- Tier 1 (Conceptual): Lagos State — 1 feature confirmed
- Tier 2 (Empirical): Amuwo Odofin LGA — 1 feature confirmed
- Boundary exported: data/amuwo_odofin_boundary.geojson

---

## Notebook 02 — DEM and Topographic Feature Extraction
- Primary DEM: SRTM 30m (USGS/SRTMGL1_003)
- Flow accumulation: HydroSHEDS 15-arc-second (WWF/HydroSHEDS/15ACC)
- Curvature: computed via Laplacian8 convolution kernel (ee.Terrain.products() 
  does not include curvature — known GEE API limitation)
- All bands cast to Float32 before stacking to resolve Int16/Float32 type conflict
- Export scale: 30 metres | CRS: EPSG:4326
- Output file: topo_features_amuwo_odofin.tif | File size: 2.1MB

### Pixel Count per Band at 30m Resolution:
| Band | Pixel Count |
|------|-------------|
| elevation | 197,127 |
| slope | 196,081 |
| aspect | 196,081 |
| flow_accumulation | 196,065 |
| twi | 195,117 |
| curvature | 197,127 |

- Total candidate sample pool: ~197,000 observations
- Planned training sample: 10,000-15,000 stratified random points
- Train/test split: 70/30 stratified

---

## Notebook 03 — Rainfall, LULC, NDVI
<!-- Update this section after running Notebook 03 -->


## Notebook 03 — Rainfall, LULC, NDVI

### CHIRPS Rainfall
- Dataset: UCSB-CHG/CHIRPS/DAILY
- Analysis period: 2013-2023 (10-year mean)
- Extreme rainfall threshold: >50mm/day (standard West African flood literature threshold)
- Export scale: 100m (compromise resolution for multi-source stack)

| Statistic | Value (mm/year) |
|-----------|----------------|
| Minimum | 1,509.21 |
| Maximum | 1,885.31 |
| Mean | 1,662.90 |

### ESA WorldCover 2021
- Dataset: ESA/WorldCover/v200
- Resolution: 10 metres (highest resolution global LULC freely available)
- Year: 2021

| Land Cover Class | Coverage (%) |
|-----------------|-------------|
| Built-up surfaces | 40.60 |
| Permanent water | 12.74 |
| Tree cover | 16.33 |
| Mangroves | 14.61 |
| Herbaceous wetland | 0.76 |

- Interpretation: 40.60% impervious surface coverage severely constrains
  natural infiltration capacity — key flood risk amplifier in study area.
  Combined water/wetland/mangrove coverage (28.11%) confirms coastal
  low-lying character of Amuwo Odofin LGA.

### Sentinel-2 NDVI
- Dataset: COPERNICUS/S2_SR_HARMONIZED
- Composite period: Dry season (Nov-Mar), 2020-2023
- Cloud filter: <20% cloudy pixel percentage
- Cloud masking: SCL classes 3, 8, 9, 10 masked
- Composite method: Median (reduces noise and residual cloud artefacts)

| Statistic | NDVI Value |
|-----------|-----------|
| Minimum | -0.2163 |
| Maximum | 0.7787 |
| Mean | 0.2951 |

- Interpretation: Low-moderate mean NDVI (0.2951) consistent with
  heavily urbanised LGA. Negative minimum values represent water
  bodies and bare impervious surfaces.

### Export
- Output file: rainfall_lulc_ndvi_amuwo_odofin.tif
- Scale: 100 metres | CRS: EPSG:4326 | Type: Float32
- Bands: mean_annual_rainfall, mean_rainy_days_per_year,
         extreme_rain_frequency, lulc, ndvi

---
