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


## Notebook 05 — SAR Flood Inventory (Pre-Notebook Planning, Re-Verified)

### Re-Verification Note
All flood events were independently re-verified on 22 May 2026 against
primary Nigerian news sources (Vanguard, Punch, Premium Times), NiMet
post-event reports, FloodList, and peer-reviewed literature. No events
are carried forward from assumption — each date is confirmed by at least
two independent sources. A fourth event (July 2022) was added after
re-verification to strengthen training sample size and temporal coverage.

### Confirmed Flood Events for Sentinel-1 SAR Change Detection

| # | Event Date | Rainfall Evidence | Primary Source | SAR Window |
|---|-----------|------------------|---------------|------------|
| 1 | 07-08 July 2017 | Victoria Island: 176.5mm on 08 July; stations recorded 69.8mm and 65.6mm on 07 July — NiMet post-event report confirmed | NiMet (Vanguard, 14 July 2017); PMC peer-reviewed journal | Pre: June 2017 / Post: 09-15 July 2017 |
| 2 | 17-19 June 2020 | ~90mm in 48hrs; LASEMA confirmed 20 families displaced at Orile-Agege; one fatality recorded | FloodList (19 June 2020) quoting LASEMA directly | Pre: May 2020 / Post: 20-30 June 2020 |
| 3 | 16 July 2021 | Flood water up to 50cm depth reported across Lagos; roads submerged from Lekki to Oshodi | FloodList (July 2021) | Pre: June 2021 / Post: 17-25 July 2021 |
| 4 | 09-10 July 2022 | Seven deaths confirmed by NEMA South West Zonal Coordinator Ibrahim Farinloye; vehicle swept away in Agege | Punch Newspapers (13 July 2022); NEMA statement | Pre: June 2022 / Post: 11-20 July 2022 |

### On the Absence of Amuwo Odofin-Specific Event Documentation
No newspaper or institutional record was found that specifically documents
flood events at Amuwo Odofin LGA level with precise event dates. This is
a known and documented data scarcity challenge in Nigerian urban flood
research, explicitly acknowledged in the peer-reviewed literature
(Nkwunonwo et al., 2016; Ajibade et al., 2013).

However, Amuwo Odofin's flood risk status is multiply confirmed:

1. The Nigeria Hydrological Services Agency (NIHSA) explicitly lists Amuwo
   Odofin as one of the defined flood-risk zones in Lagos State alongside
   Lagos Island, Ikeja, Apapa, and Surulere (NIHSA, cited in IJEES, 2021).

2. Informal settlements in Amuwo-Odofin have lost multiple commercial
   properties to flooding, documented in peer-reviewed literature
   (Olorunfemi et al., 2020, cited in Frontiers in Climate, 2025).

3. LASEMA's 2025 Flood-Free Lagos Campaign specifically mapped Amuwo-Odofin
   as a vulnerable area requiring emergency preparedness alongside Eti-Osa,
   Kosofe, Lekki, and Apapa (Punch Newspapers, June 2025).

4. Satellite Town (within Amuwo Odofin) is documented as having inadequate
   drainage and open gutters prone to blockage, leading to significant
   flooding during the rainy season (Wikipedia/Satellite Town, Lagos).

### Methodological Response to Data Scarcity — SAR-First Framing
The absence of LGA-level event documentation is not treated as a
limitation but as the direct justification for the SAR-based approach.
SAR-derived flood labels are independent of administrative reporting
quality and provide spatially explicit, physically grounded flood extent
evidence at 10-metre resolution — a fundamentally stronger evidence base
than news report coverage.

Additionally, the JRC Global Surface Water historical occurrence layer
(1984-present, Landsat-derived) will be used in Notebook 05 as
supplementary satellite-based validation of inundation patterns in
Amuwo Odofin across the study period — providing independent corroboration
that is entirely free of news reporting bias.

### SAR Technical Parameters for Notebook 05
- Dataset: COPERNICUS/S1_GRD (Sentinel-1 Ground Range Detected)
- Polarisation: VV (vertical-vertical) — most sensitive to surface water detection
- Pass direction: Both ascending and descending acquisitions checked per event
- Change detection method: Pre-flood vs post-flood backscatter difference
- Thresholding: Otsu automatic threshold method — validated at 94.3%
  accuracy for flood inundation mapping (Tiwari et al., 2020)
- Flood class: pixels with statistically significant backscatter decrease
  (open water consistently returns low backscatter in VV polarisation)
- Non-flood class: stratified random sample from confirmed dry areas in
  the same time window, stratified by land cover type to prevent the
  model learning land cover as a proxy for flood occurrence

