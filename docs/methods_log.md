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

## Notebook 04 — Soil Permeability and Distance Features

### Soil Permeability
- Primary source attempted: projects/soilgrids-isric/properties/sand/mean
- Status: ACCESS DENIED — asset not publicly available in GEE
- Fallback source used: OpenLandMap/SOL/SOL_SAND-WFRACTION_USDA-3A1A1A_M/v02
- Justification: OpenLandMap uses USDA soil taxonomy validated for West Africa
- Property: Sand fraction (% weight) as hydraulic conductivity proxy
- Resolution: 250 metres
- Scientific basis: Sandy soils = high permeability = lower runoff generation
  Clay-rich soils = low permeability = higher runoff (Saxton & Rawls, 2006)

| Statistic | Value (%) |
|-----------|----------|
| Minimum | 14.50 |
| Maximum | 34.50 |
| Mean | 25.68 |

- Interpretation: Moderate-low sand content consistent with coastal clay-rich
  soils typical of Lagos State — confirms low infiltration capacity and
  supports flood risk amplification in the study area

### Distance to Rivers
- Primary source attempted: WWF/HydroSHEDS/v1/FreeFlowingRivers (vector)
- Status: ZERO FEATURES — dataset excludes heavily modified urban waterways
  Amuwo Odofin's drainage network does not meet FreeFlowingRivers criteria
- Method adopted: Flow accumulation thresholding (WWF/HydroSHEDS/15ACC)
- Threshold: flow accumulation > 200 cells (95th percentile for LGA)
  Selected after diagnostic confirmed LGA maximum = 708 cells
  (threshold of 1000 was above all pixel values — flat coastal terrain)
- Distance method: fastDistanceTransform() — more reliable than
  kernel-based distance on masked binary images in GEE
- Resolution: 500 metres (HydroSHEDS native resolution)
- River pixels identified: ~32 pixels at 500m scale

| Statistic | Value (metres) |
|-----------|---------------|
| Minimum | 0.00 |
| Maximum | 6,726.81 |
| Mean | 2,337.43 |

### Distance to Drainage
- Source: JRC/GSW1_4/GlobalSurfaceWater (Pekel et al., 2016)
- Resolution: 30 metres
- Occurrence threshold: >10% water occurrence
  Captures seasonal and intermittent urban drainage features
- Distance method: fastDistanceTransform() × 30m resolution
- Justification: JRC captures urban drainage infrastructure
  (canals, seasonal streams) not mapped in HydroSHEDS

| Statistic | Value (metres) |
|-----------|---------------|
| Minimum | 0.00 |
| Maximum | 7,018.33 |
| Mean | 1,207.16 |

### Export
- Output file: soil_distance_amuwo_odofin.tif
- Scale: 100 metres | CRS: EPSG:4326 | Type: Float32
- Bands: soil_permeability, distance_to_river, distance_to_drainage

---

## COMPLETE FEATURE MATRIX — 14 Features (Updated from initial 12)
Feature count revised upward after NB03 produced 5 features (not 4)
and NB04 produced 3 features (soil + 2 distance measures).
14 features is methodologically defensible — tree-based models (RF, XGBoost)
handle feature redundancy gracefully. Multicollinearity check (VIF) to be
performed in NB06 before modelling.

| # | Feature | Source | Notebook | Resolution |
|---|---------|--------|----------|------------|
| 1 | Elevation | SRTM (NASA/USGS) | NB02 | 30m |
| 2 | Slope | SRTM derived | NB02 | 30m |
| 3 | Aspect | SRTM derived | NB02 | 30m |
| 4 | Flow Accumulation | HydroSHEDS (WWF) | NB02 | 500m |
| 5 | Topographic Wetness Index | SRTM + HydroSHEDS | NB02 | 30m |
| 6 | Curvature | SRTM (Laplacian kernel) | NB02 | 30m |
| 7 | Mean Annual Rainfall | CHIRPS 2013-2023 | NB03 | 5km |
| 8 | Mean Rainy Days/Year | CHIRPS 2013-2023 | NB03 | 5km |
| 9 | Extreme Rainfall Frequency | CHIRPS >50mm/day | NB03 | 5km |
| 10 | Land Use / Land Cover | ESA WorldCover 2021 | NB03 | 10m |
| 11 | NDVI | Sentinel-2 2020-2023 | NB03 | 10m |
| 12 | Soil Permeability | OpenLandMap (USDA) | NB04 | 250m |
| 13 | Distance to Rivers | HydroSHEDS flow acc. | NB04 | 500m |
| 14 | Distance to Drainage | JRC Surface Water | NB04 | 30m |

Resolution harmonisation: all 14 features resampled to 100m
common resolution in NB06 before feature matrix assembly.

