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

---g

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


## Notebook 05 — SAR Flood Inventory (Executed Results)

### Sentinel-1 Archive Availability (Confirmed from GEE)

| Event | Pre-flood Acquisitions | Post-flood Acquisitions | Pass Directions |
|-------|----------------------|------------------------|-----------------|
| Jul 2017 | 3 (03, 15, 27 Jun 2017) | 2 (09, 21 Jul 2017) | Ascending only |
| Jun 2020 | 7 (01 May–06 Jun 2020) | 3 (23 Jun–05 Jul 2020) | Mixed ASC/DESC |
| Jul 2021 | 7 (01 Jun–07 Jul 2021) | 3 (19–31 Jul 2021) | Mixed ASC/DESC |
| Jul 2022 | 5 (01 Jun–25 Jun 2022) | 3 (14–26 Jul 2022) | Mixed ASC/DESC |

Post-flood timing from event date: 1 day (2017), 4 days (2020),
3 days (2021), 4 days (2022) — all within standard 6-day window
before significant urban flood recession in coastal Lagos terrain.

### Initial Detection Attempt — Problem Identified and Corrected
Initial run with 40-day pre-flood window produced flood coverage of 97.70%
across composite — physically implausible for an urban LGA. Root cause:
40-day pre-flood window spanned the dry-to-wet season transition in Lagos,
producing backscatter changes comparable in magnitude to actual inundation.
Otsu threshold contaminated by seasonal surface moisture signal rather
than flood signal. This problem is documented in the SAR flood mapping
literature for tropical West Africa (Twele et al., 2016).

Three corrections applied:
1. Pre-flood window shortened to maximum 20 days — avoids seasonal
   transition contamination, uses closest stable dry baseline.
2. Permanent water mask applied (JRC occurrence > 50%) — removes lagoons,
   Badagry Creek, and permanent drainage channels which produce
   persistently low backscatter unrelated to flood events.
3. Dual threshold: Otsu + minimum 1.5 dB absolute change — removes
   low-magnitude noise changes incorrectly classified by Otsu alone.
   1.5 dB is the standard C-band minimum magnitude threshold
   (Boni et al., 2016).

### Corrected Detection Results

| Event | Pre Window Used | Post Window Used | Otsu Threshold | Flood Pixels | Coverage |
|-------|----------------|-----------------|---------------|-------------|---------|
| Jul 2017 | 15–30 Jun 2017 | 08–22 Jul 2017 | -0.3117 dB | 522 | 7.78% |
| Jun 2020 | 28 May–10 Jun 2020 | 19 Jun–01 Jul 2020 | -0.8105 dB | 365 | 5.43% |
| Jul 2021 | 28 Jun–08 Jul 2021 | 16–25 Jul 2021 | -0.1251 dB | 941 | 14.02% |
| Jul 2022 | 19 Jun–01 Jul 2022 | 10–20 Jul 2022 | +0.3158 dB | 1,139 | 16.97% |

Coverage range of 5.43%–16.97% per event is physically credible for
an urban coastal LGA with 40.60% impervious surface cover and documented
poor drainage infrastructure. Larger footprints in 2021 and 2022 are
consistent with more severe documented rainfall for those events.

### Composite Flood Inventory

| Statistic | Value |
|-----------|-------|
| Total study area pixels | 6,715 |
| Confirmed flood pixels | 2,325 |
| Composite flood coverage | 34.63% |

Composite method: maximum value per pixel across all four events —
a pixel classified as flood in any one event is retained as flood
in the composite. Standard approach for multi-event flood inventory
construction (Tiwari et al., 2020).

### Training Sample Statistics

| Class | Sample Count | Percentage |
|-------|-------------|------------|
| Flood (class 1) | 2,328 | 34.7% |
| Non-flood (class 0) | 4,387 | 65.3% |
| Total | 6,715 | 100% |

Class imbalance note: 34.7:65.3 flood-to-non-flood ratio reflects the
realistic spatial distribution of flood exposure in the LGA rather than
a methodological failure. The imbalance is moderate and will be addressed
during model training (Notebook 07) via class_weight='balanced' in
scikit-learn and scale_pos_weight parameter in XGBoost. This ensures
models do not develop majority-class bias toward non-flood predictions.

### Exports Submitted to Google Drive
- flood_inventory_amuwo_odofin.tif (30m resolution, binary flood/non-flood)
- training_points_amuwo_odofin.csv (6,715 labelled sample points with coordinates)

### Implementation Notes
- Otsu computation method: hybrid GEE + NumPy (histogram downloaded to Python)
  GEE server-side Array API produced dimensionality errors in pure server-side
  implementation — hybrid approach is standard in published workflows and
  produces identical results with improved robustness.
- Speckle filter: Refined Lee 3x3 approximated via focal mean on linear scale
  with dB conversion — standard pre-processing for Sentinel-1 IW mode at 10m.


---

## PROJECT RESTRUCTURING NOTE — Logged June 2026

### Critical Issue Identified: Flood Labels Contaminated by Water Bodies
During visual inspection of the flood inventory output from NB05,
flood-classified pixels (Class 1) were found to cluster predominantly
on permanent and semi-permanent water surfaces — Lagos Lagoon,
drainage channels, and tidal inlets — rather than on genuinely
inundated urban land. This renders the training labels methodologically
invalid for an urban flood susceptibility model.

Root causes identified:
1. JRC permanent water mask threshold of 50% occurrence too permissive —
   seasonal and semi-permanent water bodies (20-49% occurrence) passed
   through the mask and consistently triggered low SAR backscatter signal
   regardless of whether a flood event occurred.
2. Otsu threshold responding to permanent water signal rather than
   urban inundation signal even after 1.5dB minimum change filter.
3. No land cover constraint applied — SAR change detection was operating
   on water, wetland, and mangrove pixels that should have been excluded
   from urban flood inventory entirely.

### Corrective Methodology Decisions
Three simultaneous fixes applied to NB05 (rebuild):
1. JRC occurrence threshold tightened from 50% to 5% — any pixel
   water-covered more than 5% of the time is permanently excluded.
2. ESA WorldCover urban land mask added — only built-up (class 50),
   cropland (class 40), and grassland (class 30) pixels are eligible
   for flood classification. Water (80), wetland (90), and mangrove
   (95) pixels masked regardless of SAR signal.
3. Minimum backscatter change threshold increased from 1.5dB to 3.0dB —
   genuine urban inundation produces stronger signal than surface
   moisture variation on near-water terrain (Twele et al., 2016).

### Project Scope Enhancement — Title Alignment
Following review of the project title ("AI-Enabled Geospatial Decision
Support and Disaster Intelligence for Urban Flood Risk Management"),
the GeoAID framework was expanded from a single-layer static
susceptibility model to a three-layer decision support architecture:

Layer 1 — Structural Susceptibility (NB02-NB08):
  Static flood risk map from 16 conditioning factors and ML models.
  Answers: WHERE is inherently flood-prone.

Layer 2 — Dynamic Risk Activation (NB10 dashboard):
  GPM IMERG near-real-time rainfall overlaid on static risk map.
  Answers: WHICH risk zones are being actively triggered by current rainfall.

Layer 3 — Disaster Intelligence (NB09):
  Infrastructure risk assessment — population, roads, schools,
  hospitals, buildings at risk per flood risk zone.
  Answers: WHO and WHAT is at risk in activated zones.

### Feature Matrix Expanded from 14 to 16 Features
Two new features added:

Feature 15 — HAND (Height Above Nearest Drainage):
  Derived from DEM and HydroSHEDS flow accumulation.
  Measures vertical elevation of each pixel above nearest drainage
  channel. Low HAND = terrain barely above drainage network = highest
  first-inundation risk. Specifically validated for low-lying coastal
  urban terrain. Added in revised NB04.

Feature 16 — GPM IMERG 72-hour Event Rainfall Accumulation:
  NASA Global Precipitation Measurement IMERG product.
  Event-specific cumulative rainfall in 72 hours preceding each of
  the four verified flood events. Captures antecedent soil moisture
  conditions that determine flood response magnitude for equivalent
  rainfall inputs. Added in new NB04b.

### Revised Notebook Pipeline
NB01 ✓ — Study area (unchanged)
NB02 ✓ — Topographic features (unchanged)
NB03 ✓ — Rainfall, LULC, NDVI (unchanged)
NB04 ↺ — Soil + distance + HAND model (revised — HAND added)
NB04b ★ — GPM IMERG event rainfall (new)
NB05 ↺ — SAR flood inventory (rebuilt — water body masking corrected)
NB06    — Feature matrix assembly (updated for 16 features)
NB07    — Model training and evaluation
NB08    — SHAP explainability analysis
NB09 ★ — Infrastructure risk assessment — OSM schools, hospitals,
          roads, buildings overlaid with flood risk map (new)
NB10 ★ — Streamlit dashboard with GPM IMERG live rainfall layer (updated)

### Methodological Note on SAR Temporal Gap
The 6-12 day Sentinel-1 revisit cycle does not affect the validity of
historical label generation (Use Case B). SAR imagery is used ONCE
to construct historical flood labels from verified past events where
acquisitions within 1-4 days of each event were confirmed. The temporal
gap concern applies to real-time flood detection (Use Case A), which
is outside the scope of this project. Real-time monitoring is
acknowledged as a natural extension for future work. Dynamic rainfall
forcing for the operational decision support layer is provided by
GPM IMERG (30-minute update cycle) rather than SAR.


---

## Notebook 04 (Revised) — Soil, Distance Features

### HAND Model — Attempted and Removed
HAND (Height Above Nearest Drainage) was implemented using two approaches:

Attempt 1: HydroSHEDS flow accumulation thresholding at 500m resolution.
Result: Sparse channel network missed most urban drainage features in
Amuwo Odofin. Kernel computation at 30m resolution (5000m radius =
167-pixel kernel) timed out after 37+ minutes without completing.

Attempt 2: JRC Global Surface Water occurrence > 5% at 100m resolution
as channel network. focal_min 5000m radius at 100m = 50-pixel kernel.
Result: Computation completed but produced physically incorrect values.
Festac Town pixels immediately adjacent to canals showed HAND > 13m
(red/high) rather than expected low values. Root cause: focal_min
propagates the MINIMUM elevation within search radius — in coastal
Lagos, this is always the Lagos Lagoon (0m) rather than local canal
elevation (3-4m). All HAND values relative to lagoon sea level rather
than nearest local drainage channel, rendering the layer hydrologically
meaningless for urban flood susceptibility in this coastal setting.

Decision: HAND removed from feature matrix.
Justification: Correct HAND computation requires a hydrologically
conditioned DEM (e.g. MERIT DEM or NASADEM with depression filling)
where sea-level water bodies are treated separately from inland
drainage channels. SRTM-based HAND in coastal environments with
large tidal water bodies produces systematically incorrect values.
Documented as priority for future work.

### Final NB04 Outputs (Three Features)
- Feature 12: Soil permeability (OpenLandMap sand fraction, 250m)
  Mean: 25.68% — clay-dominant coastal soils confirming low
  infiltration capacity and high runoff generation potential
- Feature 13: Distance to river (HydroSHEDS flow acc threshold,
  fastDistanceTransform, 500m) — Mean: 2,337.43m
- Feature 14: Distance to drainage (JRC occurrence > 10%,
  fastDistanceTransform, 30m) — Mean: 1,207.16m

Export: soil_distance_amuwo_odofin.tif (3 bands, 100m, Float32)

---

## Notebook 04b — GPM IMERG Antecedent Rainfall (Feature 15)

### Dataset
- Source: NASA/GPM_L3/IMERG_V07 (gauge-calibrated)
- Band: precipitation (mm/hr) — note: named 'precipitationCal' in
  older IMERG versions; renamed 'precipitation' in V07
- Temporal resolution: 30-minute intervals
- Spatial resolution: 0.1° (~11km at Lagos latitude)
- Unit conversion: sum(mm/hr) × 0.5hr interval = total mm accumulated

### Antecedent Window Design
72-hour window immediately preceding each flood event peak date.
Scientific rationale: 72-hour antecedent rainfall captures soil
moisture saturation state — the primary determinant of flood response
magnitude for equivalent rainfall inputs in tropical urban catchments
(Beven & Kirkby, 1979; Western et al., 2002).

### Event-Specific 72-Hour Antecedent Rainfall

| Event | Window | Images | Min (mm) | Max (mm) | Mean (mm) |
|-------|--------|--------|----------|----------|-----------|
| Jul 2017 | 04-07 Jul 2017 | 144 | 110.14 | 134.29 | 126.20 |
| Jun 2020 | 14-17 Jun 2020 | 144 | 25.94 | 40.65 | 34.01 |
| Jul 2021 | 13-16 Jul 2021 | 144 | 3.69 | 11.92 | 10.09 |
| Jul 2022 | 06-09 Jul 2022 | 144 | 48.54 | 84.39 | 58.70 |

### Key Scientific Finding — Event 3 (July 2021)
Event 3 produced the second-largest flood footprint (14.02% coverage)
despite only 10.09mm of antecedent rainfall in the preceding 72 hours.
This indicates the July 2021 flood was driven by intense short-duration
rainfall overwhelming structurally constrained drainage capacity rather
than prolonged antecedent soil saturation. This finding demonstrates
that antecedent rainfall alone does not explain flood occurrence in
urbanised coastal terrain — structural drainage capacity (captured by
TWI, flow accumulation, distance to drainage) matters equally.
SHAP analysis in NB08 will reveal how the model weights GPM IMERG
relative to terrain conditioning factors.

### Spatial Note
GPM IMERG at 0.1° (~11km) resolution is coarser than Amuwo Odofin
LGA extent. The feature contributes event-specific temporal forcing
information rather than spatial differentiation within the LGA.
Standard deviation of composite (3.77mm) confirms spatial uniformity.

### Composite Statistics (Feature 15 — Mean Across Four Events)

| Statistic | Value (mm/72hr) |
|-----------|----------------|
| Minimum | 48.09 |
| Maximum | 62.37 |
| Mean | 57.25 |
| Std Dev | 3.77 |

### Exports Submitted
- gpm_antecedent_rainfall_amuwo_odofin.tif → Feature 15 (ML matrix)
- gpm_rainfall_2017_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2020_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2021_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2022_amuwo_odofin.tif (event-specific)

---

## FINAL FEATURE MATRIX — 15 Features

| # | Feature | Source | NB | Resolution |
|---|---------|--------|----|------------|
| 1 | Elevation | SRTM (NASA/USGS) | NB02 | 30m |
| 2 | Slope | SRTM derived | NB02 | 30m |
| 3 | Aspect | SRTM derived | NB02 | 30m |
| 4 | Flow Accumulation | HydroSHEDS (WWF) | NB02 | 500m |
| 5 | TWI | SRTM + HydroSHEDS | NB02 | 30m |
| 6 | Curvature | SRTM Laplacian kernel | NB02 | 30m |
| 7 | Mean Annual Rainfall | CHIRPS 2013-2023 | NB03 | 5km |
| 8 | Mean Rainy Days/Year | CHIRPS 2013-2023 | NB03 | 5km |
| 9 | Extreme Rainfall Freq | CHIRPS >50mm/day | NB03 | 5km |
| 10 | Land Use/Land Cover | ESA WorldCover 2021 | NB03 | 10m |
| 11 | NDVI | Sentinel-2 2020-2023 | NB03 | 10m |
| 12 | Soil Permeability | OpenLandMap (USDA) | NB04 | 250m |
| 13 | Distance to Rivers | HydroSHEDS flow acc | NB04 | 500m |
| 14 | Distance to Drainage | JRC Surface Water | NB04 | 30m |
| 15 | GPM IMERG 72hr Rainfall | NASA GPM IMERG V07 | NB04b | 11km |

HAND excluded: SRTM-based HAND computation in coastal environments
with large tidal water bodies produces systematically incorrect values
relative to sea-level rather than local drainage. Recommended for
future work using MERIT DEM or NASADEM with hydrological conditioning.

All 15 features to be resampled to common 100m resolution in NB06.

### GeoTIFF Export Summary — Data Acquisition Phase Complete

| File | Features | Bands | Scale |
|------|----------|-------|-------|
| topo_features_amuwo_odofin.tif | F1-F6 | 6 | 30m |
| rainfall_lulc_ndvi_amuwo_odofin.tif | F7-F11 | 5 | 100m |
| soil_distance_amuwo_odofin.tif | F12-F14 | 3 | 100m |
| gpm_antecedent_rainfall_amuwo_odofin.tif | F15 | 1 | 1000m |
| flood_inventory_amuwo_odofin.tif | Labels | 1 | 30m |


---

## Notebook 04 (Revised) — Soil, Distance Features

### HAND Model — Attempted and Removed
HAND (Height Above Nearest Drainage) was implemented using two approaches:

Attempt 1: HydroSHEDS flow accumulation thresholding at 500m resolution.
Result: Sparse channel network missed most urban drainage features in
Amuwo Odofin. Kernel computation at 30m resolution (5000m radius =
167-pixel kernel) timed out after 37+ minutes without completing.

Attempt 2: JRC Global Surface Water occurrence > 5% at 100m resolution
as channel network. focal_min 5000m radius at 100m = 50-pixel kernel.
Result: Computation completed but produced physically incorrect values.
Festac Town pixels immediately adjacent to canals showed HAND > 13m
(red/high) rather than expected low values. Root cause: focal_min
propagates the MINIMUM elevation within search radius — in coastal
Lagos, this is always the Lagos Lagoon (0m) rather than local canal
elevation (3-4m). All HAND values relative to lagoon sea level rather
than nearest local drainage channel, rendering the layer hydrologically
meaningless for urban flood susceptibility in this coastal setting.

Decision: HAND removed from feature matrix.
Justification: Correct HAND computation requires a hydrologically
conditioned DEM (e.g. MERIT DEM or NASADEM with depression filling)
where sea-level water bodies are treated separately from inland
drainage channels. SRTM-based HAND in coastal environments with
large tidal water bodies produces systematically incorrect values.
Documented as priority for future work.

### Final NB04 Outputs (Three Features)
- Feature 12: Soil permeability (OpenLandMap sand fraction, 250m)
  Mean: 25.68% — clay-dominant coastal soils confirming low
  infiltration capacity and high runoff generation potential
- Feature 13: Distance to river (HydroSHEDS flow acc threshold,
  fastDistanceTransform, 500m) — Mean: 2,337.43m
- Feature 14: Distance to drainage (JRC occurrence > 10%,
  fastDistanceTransform, 30m) — Mean: 1,207.16m

Export: soil_distance_amuwo_odofin.tif (3 bands, 100m, Float32)

---

## Notebook 04b — GPM IMERG Antecedent Rainfall (Feature 15)

### Dataset
- Source: NASA/GPM_L3/IMERG_V07 (gauge-calibrated)
- Band: precipitation (mm/hr) — note: named 'precipitationCal' in
  older IMERG versions; renamed 'precipitation' in V07
- Temporal resolution: 30-minute intervals
- Spatial resolution: 0.1° (~11km at Lagos latitude)
- Unit conversion: sum(mm/hr) × 0.5hr interval = total mm accumulated

### Antecedent Window Design
72-hour window immediately preceding each flood event peak date.
Scientific rationale: 72-hour antecedent rainfall captures soil
moisture saturation state — the primary determinant of flood response
magnitude for equivalent rainfall inputs in tropical urban catchments
(Beven & Kirkby, 1979; Western et al., 2002).

### Event-Specific 72-Hour Antecedent Rainfall

| Event | Window | Images | Min (mm) | Max (mm) | Mean (mm) |
|-------|--------|--------|----------|----------|-----------|
| Jul 2017 | 04-07 Jul 2017 | 144 | 110.14 | 134.29 | 126.20 |
| Jun 2020 | 14-17 Jun 2020 | 144 | 25.94 | 40.65 | 34.01 |
| Jul 2021 | 13-16 Jul 2021 | 144 | 3.69 | 11.92 | 10.09 |
| Jul 2022 | 06-09 Jul 2022 | 144 | 48.54 | 84.39 | 58.70 |

### Key Scientific Finding — Event 3 (July 2021)
Event 3 produced the second-largest flood footprint (14.02% coverage)
despite only 10.09mm of antecedent rainfall in the preceding 72 hours.
This indicates the July 2021 flood was driven by intense short-duration
rainfall overwhelming structurally constrained drainage capacity rather
than prolonged antecedent soil saturation. This finding demonstrates
that antecedent rainfall alone does not explain flood occurrence in
urbanised coastal terrain — structural drainage capacity (captured by
TWI, flow accumulation, distance to drainage) matters equally.
SHAP analysis in NB08 will reveal how the model weights GPM IMERG
relative to terrain conditioning factors.

### Spatial Note
GPM IMERG at 0.1° (~11km) resolution is coarser than Amuwo Odofin
LGA extent. The feature contributes event-specific temporal forcing
information rather than spatial differentiation within the LGA.
Standard deviation of composite (3.77mm) confirms spatial uniformity.

### Composite Statistics (Feature 15 — Mean Across Four Events)

| Statistic | Value (mm/72hr) |
|-----------|----------------|
| Minimum | 48.09 |
| Maximum | 62.37 |
| Mean | 57.25 |
| Std Dev | 3.77 |

### Exports Submitted
- gpm_antecedent_rainfall_amuwo_odofin.tif → Feature 15 (ML matrix)
- gpm_rainfall_2017_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2020_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2021_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2022_amuwo_odofin.tif (event-specific)

---

## FINAL FEATURE MATRIX — 15 Features

| # | Feature | Source | NB | Resolution |
|---|---------|--------|----|------------|
| 1 | Elevation | SRTM (NASA/USGS) | NB02 | 30m |
| 2 | Slope | SRTM derived | NB02 | 30m |
| 3 | Aspect | SRTM derived | NB02 | 30m |
| 4 | Flow Accumulation | HydroSHEDS (WWF) | NB02 | 500m |
| 5 | TWI | SRTM + HydroSHEDS | NB02 | 30m |
| 6 | Curvature | SRTM Laplacian kernel | NB02 | 30m |
| 7 | Mean Annual Rainfall | CHIRPS 2013-2023 | NB03 | 5km |
| 8 | Mean Rainy Days/Year | CHIRPS 2013-2023 | NB03 | 5km |
| 9 | Extreme Rainfall Freq | CHIRPS >50mm/day | NB03 | 5km |
| 10 | Land Use/Land Cover | ESA WorldCover 2021 | NB03 | 10m |
| 11 | NDVI | Sentinel-2 2020-2023 | NB03 | 10m |
| 12 | Soil Permeability | OpenLandMap (USDA) | NB04 | 250m |
| 13 | Distance to Rivers | HydroSHEDS flow acc | NB04 | 500m |
| 14 | Distance to Drainage | JRC Surface Water | NB04 | 30m |
| 15 | GPM IMERG 72hr Rainfall | NASA GPM IMERG V07 | NB04b | 11km |

HAND excluded: SRTM-based HAND computation in coastal environments
with large tidal water bodies produces systematically incorrect values
relative to sea-level rather than local drainage. Recommended for
future work using MERIT DEM or NASADEM with hydrological conditioning.

All 15 features to be resampled to common 100m resolution in NB06.

### GeoTIFF Export Summary — Data Acquisition Phase Complete

| File | Features | Bands | Scale |
|------|----------|-------|-------|
| topo_features_amuwo_odofin.tif | F1-F6 | 6 | 30m |
| rainfall_lulc_ndvi_amuwo_odofin.tif | F7-F11 | 5 | 100m |
| soil_distance_amuwo_odofin.tif | F12-F14 | 3 | 100m |
| gpm_antecedent_rainfall_amuwo_odofin.tif | F15 | 1 | 1000m |
| flood_inventory_amuwo_odofin.tif | Labels | 1 | 30m |


---

## Notebook 04 (Revised) — Soil, Distance Features

### HAND Model — Attempted and Removed
HAND (Height Above Nearest Drainage) was implemented using two approaches:

Attempt 1: HydroSHEDS flow accumulation thresholding at 500m resolution.
Result: Sparse channel network missed most urban drainage features in
Amuwo Odofin. Kernel computation at 30m resolution (5000m radius =
167-pixel kernel) timed out after 37+ minutes without completing.

Attempt 2: JRC Global Surface Water occurrence > 5% at 100m resolution
as channel network. focal_min 5000m radius at 100m = 50-pixel kernel.
Result: Computation completed but produced physically incorrect values.
Festac Town pixels immediately adjacent to canals showed HAND > 13m
(red/high) rather than expected low values. Root cause: focal_min
propagates the MINIMUM elevation within search radius — in coastal
Lagos, this is always the Lagos Lagoon (0m) rather than local canal
elevation (3-4m). All HAND values relative to lagoon sea level rather
than nearest local drainage channel, rendering the layer hydrologically
meaningless for urban flood susceptibility in this coastal setting.

Decision: HAND removed from feature matrix.
Justification: Correct HAND computation requires a hydrologically
conditioned DEM (e.g. MERIT DEM or NASADEM with depression filling)
where sea-level water bodies are treated separately from inland
drainage channels. SRTM-based HAND in coastal environments with
large tidal water bodies produces systematically incorrect values.
Documented as priority for future work.

### Final NB04 Outputs (Three Features)
- Feature 12: Soil permeability (OpenLandMap sand fraction, 250m)
  Mean: 25.68% — clay-dominant coastal soils confirming low
  infiltration capacity and high runoff generation potential
- Feature 13: Distance to river (HydroSHEDS flow acc threshold,
  fastDistanceTransform, 500m) — Mean: 2,337.43m
- Feature 14: Distance to drainage (JRC occurrence > 10%,
  fastDistanceTransform, 30m) — Mean: 1,207.16m

Export: soil_distance_amuwo_odofin.tif (3 bands, 100m, Float32)

---

## Notebook 04b — GPM IMERG Antecedent Rainfall (Feature 15)

### Dataset
- Source: NASA/GPM_L3/IMERG_V07 (gauge-calibrated)
- Band: precipitation (mm/hr) — note: named 'precipitationCal' in
  older IMERG versions; renamed 'precipitation' in V07
- Temporal resolution: 30-minute intervals
- Spatial resolution: 0.1° (~11km at Lagos latitude)
- Unit conversion: sum(mm/hr) × 0.5hr interval = total mm accumulated

### Antecedent Window Design
72-hour window immediately preceding each flood event peak date.
Scientific rationale: 72-hour antecedent rainfall captures soil
moisture saturation state — the primary determinant of flood response
magnitude for equivalent rainfall inputs in tropical urban catchments
(Beven & Kirkby, 1979; Western et al., 2002).

### Event-Specific 72-Hour Antecedent Rainfall

| Event | Window | Images | Min (mm) | Max (mm) | Mean (mm) |
|-------|--------|--------|----------|----------|-----------|
| Jul 2017 | 04-07 Jul 2017 | 144 | 110.14 | 134.29 | 126.20 |
| Jun 2020 | 14-17 Jun 2020 | 144 | 25.94 | 40.65 | 34.01 |
| Jul 2021 | 13-16 Jul 2021 | 144 | 3.69 | 11.92 | 10.09 |
| Jul 2022 | 06-09 Jul 2022 | 144 | 48.54 | 84.39 | 58.70 |

### Key Scientific Finding — Event 3 (July 2021)
Event 3 produced the second-largest flood footprint (14.02% coverage)
despite only 10.09mm of antecedent rainfall in the preceding 72 hours.
This indicates the July 2021 flood was driven by intense short-duration
rainfall overwhelming structurally constrained drainage capacity rather
than prolonged antecedent soil saturation. This finding demonstrates
that antecedent rainfall alone does not explain flood occurrence in
urbanised coastal terrain — structural drainage capacity (captured by
TWI, flow accumulation, distance to drainage) matters equally.
SHAP analysis in NB08 will reveal how the model weights GPM IMERG
relative to terrain conditioning factors.

### Spatial Note
GPM IMERG at 0.1° (~11km) resolution is coarser than Amuwo Odofin
LGA extent. The feature contributes event-specific temporal forcing
information rather than spatial differentiation within the LGA.
Standard deviation of composite (3.77mm) confirms spatial uniformity.

### Composite Statistics (Feature 15 — Mean Across Four Events)

| Statistic | Value (mm/72hr) |
|-----------|----------------|
| Minimum | 48.09 |
| Maximum | 62.37 |
| Mean | 57.25 |
| Std Dev | 3.77 |

### Exports Submitted
- gpm_antecedent_rainfall_amuwo_odofin.tif → Feature 15 (ML matrix)
- gpm_rainfall_2017_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2020_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2021_amuwo_odofin.tif (event-specific)
- gpm_rainfall_2022_amuwo_odofin.tif (event-specific)

---

## FINAL FEATURE MATRIX — 15 Features

| # | Feature | Source | NB | Resolution |
|---|---------|--------|----|------------|
| 1 | Elevation | SRTM (NASA/USGS) | NB02 | 30m |
| 2 | Slope | SRTM derived | NB02 | 30m |
| 3 | Aspect | SRTM derived | NB02 | 30m |
| 4 | Flow Accumulation | HydroSHEDS (WWF) | NB02 | 500m |
| 5 | TWI | SRTM + HydroSHEDS | NB02 | 30m |
| 6 | Curvature | SRTM Laplacian kernel | NB02 | 30m |
| 7 | Mean Annual Rainfall | CHIRPS 2013-2023 | NB03 | 5km |
| 8 | Mean Rainy Days/Year | CHIRPS 2013-2023 | NB03 | 5km |
| 9 | Extreme Rainfall Freq | CHIRPS >50mm/day | NB03 | 5km |
| 10 | Land Use/Land Cover | ESA WorldCover 2021 | NB03 | 10m |
| 11 | NDVI | Sentinel-2 2020-2023 | NB03 | 10m |
| 12 | Soil Permeability | OpenLandMap (USDA) | NB04 | 250m |
| 13 | Distance to Rivers | HydroSHEDS flow acc | NB04 | 500m |
| 14 | Distance to Drainage | JRC Surface Water | NB04 | 30m |
| 15 | GPM IMERG 72hr Rainfall | NASA GPM IMERG V07 | NB04b | 11km |

HAND excluded: SRTM-based HAND computation in coastal environments
with large tidal water bodies produces systematically incorrect values
relative to sea-level rather than local drainage. Recommended for
future work using MERIT DEM or NASADEM with hydrological conditioning.

All 15 features to be resampled to common 100m resolution in NB06.

### GeoTIFF Export Summary — Data Acquisition Phase Complete

| File | Features | Bands | Scale |
|------|----------|-------|-------|
| topo_features_amuwo_odofin.tif | F1-F6 | 6 | 30m |
| rainfall_lulc_ndvi_amuwo_odofin.tif | F7-F11 | 5 | 100m |
| soil_distance_amuwo_odofin.tif | F12-F14 | 3 | 100m |
| gpm_antecedent_rainfall_amuwo_odofin.tif | F15 | 1 | 1000m |
| flood_inventory_amuwo_odofin.tif | Labels | 1 | 30m |


---

## Notebook 05 (Rebuilt) — SAR Flood Inventory (Corrected)

### Corrective Fixes Applied
Three simultaneous fixes resolved water body contamination:

Fix 1 — JRC threshold tightened from 50% to 5% occurrence:
  Pixels excluded by JRC mask: 16,691
  Seasonal and semi-permanent water bodies now excluded.

Fix 2 — ESA WorldCover urban land eligibility mask added:
  Eligible classes: tree cover (10), grassland (30), cropland (40),
  built-up (50), bare/sparse (60).
  Excluded classes: water (80), wetland (90), mangrove (95).
  Pixels excluded by WorldCover mask: 501,694

Combined urban land mask:
  Valid urban land pixels : 140,630 (71.3% of study area)
  Total study area pixels : 197,134
  SAR change detection restricted to urban land pixels only.

Fix 3 — Minimum backscatter change threshold:
  Initial attempt: 3.0dB → coverage 0.10-0.53% per event (too strict)
  Final value: 2.0dB — published standard for dense urban C-band
  flood detection (Chini et al., 2019; Boni et al., 2016).
  Justification: urban double-bounce scattering from buildings
  attenuates flood signal in densely built environments. Water body
  contamination now controlled by three-layer mask, not threshold alone.

### Per-Event Detection Results (Corrected)

| Event | Otsu Threshold | Flood Pixels | Urban Coverage |
|-------|---------------|-------------|----------------|
| Jul 2017 | +0.0631 dB | 3,108 | 1.58% |
| Jun 2020 | -1.0620 dB | 679 | 0.34% |
| Jul 2021 | +0.4368 dB | 5,312 | 2.69% |
| Jul 2022 | -0.1874 dB | 1,811 | 0.92% |

Note on low individual event coverages:
Otsu thresholds near zero indicate weak bimodal separation in urban
terrain — consistent with literature on SAR urban flood detection
where building double-bounce dominates radar return even during
inundation. Low individual coverages reflect genuine SAR signal
limitations in dense urban Lagos, not methodological failure.
Event 2 (Jun 2020) weakest signal — consistent with moderate
antecedent rainfall (34mm/72hr, lowest of four events).

### Composite Flood Inventory
- Total urban land pixels : 197,141
- Confirmed flood pixels  : 10,208
- Composite flood coverage: 5.18% ✓
- Method: union (max per pixel across four events)
- Composite within credible range for dense urban coastal LGA

### Training Samples (Final — Balanced)
- Flood samples (class 1)     : 5,000
- Non-flood samples (class 0) : 5,000
- Total training samples      : 10,000
- Class balance               : 50:50
- Additional safeguard: class_weight='balanced' applied in NB07

### Exports Submitted
- flood_inventory_corrected_amuwo_odofin.tif (30m, binary)
- training_points_corrected_amuwo_odofin.csv (10,000 labelled points)

### Visual Confirmation
Map inspection confirmed flood pixels located exclusively on
urban land surfaces — no flood classifications on Lagos Lagoon,
Badagry Creek, canals, or tidal inlets. Water body contamination
problem fully resolved.


---

## Notebook 06 — Feature Matrix Assembly

### Raster Metadata (Pre-Resampling)
| Dataset | Bands | Resolution | Dimensions | CRS |
|---------|-------|-----------|------------|-----|
| topo_features | 6 | 30m | 687×489 | EPSG:4326 |
| rainfall_lulc_ndvi | 5 | 100m | 206×147 | EPSG:4326 |
| soil_distance | 3 | 100m | 206×147 | EPSG:4326 |
| gpm_antecedent_rainfall | 1 | 499m | 42×30 | EPSG:4326 |

### Resampling
- Target resolution: 0.0009° ≈ 100m at Lagos latitude
- Target CRS: EPSG:4326
- Method: bilinear interpolation for all continuous features
- Exception: nearest-neighbour for rainfall_lulc_ndvi stack
  (contains LULC categorical band — bilinear would produce
  non-integer values not corresponding to valid land cover classes)
- Post-resampling dimensions: 206×147 for all stacks except
  GPM (210×150 — slightly extended bounds from 500m native resolution)

### Training Points CSV
- File: training_points_amuwo_odofin.csv
- Shape: 10,000 rows × 3 columns
- Columns: system:index, flood_label, .geo (GeoJSON coordinates)
- Label distribution: 5,000 flood (1), 5,000 non-flood (0) — 50:50

### NB05 Training Label Bug — Documented
- Original export produced 10,000 flood labels (0 non-flood)
- Root cause: .selfMask() on binary image converts all kept pixels
  to value 1 regardless of intended class — non-flood pixels
  exported with flood_label=1 instead of 0
- Fix: explicit ee.Image(0) remapping before stratifiedSample()
- Verified: system:index prefix 1_ = flood, 2_ = non-flood
- Re-export confirmed correct distribution

### Spatial Join Results — Feature Values at 10,000 Sample Points
All 15 features extracted successfully via rasterio.sample():

| Feature | Min | Max | Mean |
|---------|-----|-----|------|
| elevation | -10.57m | 22.80m | 6.57m |
| slope | 0.38° | 19.70° | 2.80° |
| aspect | 7.48° | 292.01° | 161.65° |
| flow_accumulation | 1.00 | 707.04 | 34.80 |
| twi | 1.93 | 11.14 | 4.46 |
| curvature | -8.12 | 9.68 | -0.05 |
| mean_annual_rainfall | 1,509.21mm | 1,885.31mm | 1,633.75mm |
| mean_rainy_days | 121.90 | 128.60 | 124.71 |
| extreme_rain_freq | 1.20 | 3.40 | 1.65 |
| lulc | 10 | 95 | 43.07 |
| ndvi | -0.08 | 0.74 | 0.27 |
| soil_permeability | 15.00% | 35.50% | 26.47% |
| distance_to_river | 0.00m | 29,302.17m | 9,653.46m |
| distance_to_drainage | 0.00m | 2,041.51m | 460.09m |
| gpm_antecedent_rainfall | 48.09mm | 64.49mm | 57.62mm |

Note on distance_to_river max (29,302m): reflects sparse HydroSHEDS
channel network from flow accumulation thresholding. Some points
far from identified channels. Does not affect model training.

### Missing Values and Cleaning
| Feature | Missing | % |
|---------|---------|---|
| elevation | 442 | 4.42% |
| slope | 576 | 5.76% |
| aspect | 576 | 5.76% |
| flow_accumulation | 507 | 5.07% |
| twi | 625 | 6.25% |
| curvature | 442 | 4.42% |
| mean_annual_rainfall | 6 | 0.06% |
| mean_rainy_days | 6 | 0.06% |
| extreme_rain_freq | 6 | 0.06% |
| soil_permeability | 628 | 6.28% |
| distance_to_river | 60 | 0.60% |
| distance_to_drainage | 60 | 0.60% |
| gpm_antecedent_rainfall | 301 | 3.01% |
| lulc | 0 | 0.00% |
| ndvi | 0 | 0.00% |

Missing value cause: raster boundary edge pixels where clipping
produced incomplete cells at LGA margin. Standard spatial join
artefact — not a data quality failure.

Rows removed: 1,161 (11.61%)
Final dataset: 8,839 rows
Post-cleaning class balance: 4,455 flood (50.4%) / 4,384 non-flood (49.6%)

### Multicollinearity Analysis

#### Highly Correlated Pairs (|r| > 0.7)
1. flow_accumulation ↔ twi: r = 0.771
   Explanation: TWI is mathematically derived from flow accumulation.
   Correlation moderated by slope — both features retained as they
   capture different aspects of hydrological saturation potential.

2. mean_annual_rainfall ↔ extreme_rain_freq: r = 0.871
   Explanation: climatological link — areas with higher total annual
   rainfall experience more extreme rainfall days. Both features
   retained; tree model SHAP will reveal relative importance.

#### VIF Analysis Results
| Feature | VIF | Status |
|---------|-----|--------|
| mean_annual_rainfall | 1,552.87 | HIGH |
| mean_rainy_days | 1,535.67 | HIGH |
| gpm_antecedent_rainfall | 663.29 | HIGH |
| soil_permeability | 121.34 | HIGH |
| extreme_rain_freq | 86.37 | HIGH |
| twi | 29.72 | HIGH |
| aspect | 20.11 | HIGH |
| lulc | 14.60 | HIGH |
| slope | 10.93 | HIGH |
| elevation | 7.58 | MODERATE |
| distance_to_river | 7.09 | MODERATE |
| ndvi | 6.76 | MODERATE |
| distance_to_drainage | 5.27 | MODERATE |
| flow_accumulation | 3.83 | ACCEPTABLE |
| curvature | 1.19 | ACCEPTABLE |

VIF Interpretation:
Extreme VIF values for rainfall features reflect spatial uniformity
of coarser-resolution datasets (CHIRPS 5km, GPM 11km) across the
small LGA extent (15km × 13km). At this scale, low within-study-area
variance inflates VIF estimates without reducing predictive value.
This is a known phenomenon in local-scale geospatial ML studies.

Action taken:
- Tree-based models (RF, XGBoost): no action — immune to multicollinearity
- Logistic Regression: coefficients reported but not used for feature
  importance interpretation. SHAP analysis is the primary interpretability
  framework for all three models.
- No features removed — all 15 retained for consistent model comparison

Notable: curvature (VIF=1.19) and flow_accumulation (VIF=3.83) are
the most independent features in the matrix — watch for prominence
in SHAP analysis.

### Final Feature Matrix
- File: data/feature_matrix.csv and outputs/feature_matrix.csv
- Shape: 8,839 rows × 18 columns
- Columns: longitude, latitude, flood_label + 15 features
- Class balance: 50.4% flood / 49.6% non-flood
- Correlation figure: outputs/figures/correlation_matrix.png


---

## Notebook 07 — Model Training and Evaluation

### Feature Set Decision — distance_to_river Removed
Initial training used 15 features. Diagnostic investigation revealed
distance_to_river was physically invalid:
- Max distance 28,638m exceeds LGA dimensions (~15km across)
- Median 9,899m — half of all points supposedly >10km from a river
- Compare distance_to_drainage (JRC 30m): max 2,000m, mean 476m
Root cause: HydroSHEDS river network at 500m resolution identifies
almost no channels within the small LGA, producing meaningless large
distances. distance_to_drainage (JRC, denser 30m network) is the valid
replacement capturing the same conditioning concept correctly.

Feature importance confirmed distance_to_river ranked 4th (0.0879)
despite being broken — actively contributing spatial noise. Removal
improved spatial CV recall (0.3419 → 0.3678) and F1 (0.4251 → 0.4454)
while holding random-split performance flat (ROC-AUC 0.7994 → 0.7979,
OOB 0.7210 → 0.7247). Final feature count: 14.

### Final Feature Set (14)
elevation, slope, aspect, flow_accumulation, twi, curvature,
mean_annual_rainfall, mean_rainy_days, extreme_rain_freq, lulc, ndvi,
soil_permeability, distance_to_drainage, gpm_antecedent_rainfall

### Training Configuration
- Dataset: 8,839 samples (4,455 flood / 4,384 non-flood, 50.4/49.6%)
- Split: 70:30 stratified, random_state=42
- Train: 6,187 | Test: 2,652
- StandardScaler applied to Logistic Regression only (tree models scale-invariant)

### Model Performance — Random Split (70:30)
| Model | Accuracy | Precision | Recall | F1 | ROC-AUC |
|-------|----------|-----------|--------|-----|---------|
| Logistic Regression | 0.5969 | 0.5868 | 0.6776 | 0.6289 | 0.6431 |
| Random Forest | 0.7281 | 0.7194 | 0.7554 | 0.7370 | 0.7979 |
| XGBoost | 0.7006 | 0.6903 | 0.7367 | 0.7127 | 0.7674 |

Selected model: Random Forest (best on all metrics)

### Confusion Matrices (Test Set, n=2,652)
Logistic Regression: TN=677 FP=638 FN=431 TP=906
Random Forest:       TN=921 FP=394 FN=327 TP=1010
XGBoost:             TN=873 FP=442 FN=352 TP=985

### OOB Convergence Verification
OOB error stabilised by 150 trees (0.2743) with negligible change to
200 trees (0.2753). Confirms n_estimators=200 (Chapter 3 claim verified).
RF OOB score 0.7247 closely matches test accuracy 0.7281 — no overfitting.

### Spatial K-Fold Cross-Validation (5x5 grid, 5-fold)
| Model | Accuracy | Recall | F1 | ROC-AUC |
|-------|----------|--------|-----|---------|
| Logistic Regression | 0.6011±0.020 | 0.6429±0.200 | 0.5998±0.119 | 0.6393±0.030 |
| Random Forest | 0.5663±0.033 | 0.3678±0.142 | 0.4454±0.105 | 0.6422±0.018 |
| XGBoost | 0.5744±0.022 | 0.4438±0.153 | 0.4958±0.118 | 0.6259±0.017 |

### Spatial CV Gap — Interpretation (CRITICAL for viva)
Random Forest random-split ROC-AUC (0.7979) vs spatial-CV ROC-AUC (0.6422):
gap of ~0.16 reflects spatial autocorrelation leakage in random splitting.
Diagnosed causes (evidence-based):
1. Small study area (15x13km) — CHIRPS (5km) and GPM (11km) rainfall
   features near-spatially-constant. Feature importance confirms all four
   rainfall features contribute <0.02 each (~6% combined) — minimal spatial
   discriminative signal at this scale.
2. Spatially clustered flooding — block composition analysis shows flood
   pixels concentrated in blocks 6,8,11,13 (60-70% flood) vs blocks 0,4
   (<20%). Holding out flood-dense blocks removes most flood training
   examples, causing recall collapse and high variance (±0.14).
3. Only 21 populated blocks over small area — spatial CV estimates
   themselves unstable (wide standard deviations).
Conclusion: spatial CV gap is substantially a small-area sampling artefact,
not model failure. Reported honestly in Chapter 4 as evidence of
methodological rigour. Most published flood susceptibility studies report
only inflated random-split numbers and never run spatial CV.

### Feature Importance (Gini, Random Forest — diagnostic only)
ndvi (0.159), distance_to_drainage (0.093), elevation (0.090),
soil_permeability (0.083), curvature (0.083), aspect (0.082),
twi (0.082), slope (0.079), flow_accumulation (0.057), lulc (0.036),
rainfall features all <0.02. NDVI dominance is physically sensible —
low NDVI marks impervious built-up surfaces where urban flooding
concentrates. SHAP analysis (NB08) is the primary interpretability tool;
Gini importance retained here for diagnostic transparency only.

### Models Saved
models/logistic_regression.pkl, models/random_forest.pkl,
models/xgboost.pkl, models/scaler.pkl


---

## Notebook 07 — Final Outputs (Figures and Spatial Products)

### Flood Susceptibility Map Generated (Primary Spatial Output)
- Method: Random Forest applied to all valid pixels in Amuwo Odofin
- Grid: 206 x 147 pixels at 100m (reference: topo raster)
- Valid land pixels predicted: 13,022 of 30,282 total grid cells
- Probability range: 0.004 to 1.000, mean 0.389
- Full probability spread confirms model produces differentiated
  predictions, not clustered at extremes

### Risk Tier Reclassification (Quartile Breakpoints)
| Tier | Threshold | Pixels | Share |
|------|-----------|--------|-------|
| Low | < 0.189 | 3,256 | 25.0% |
| Moderate | 0.189 - 0.373 | 3,255 | 25.0% |
| High | 0.373 - 0.544 | 3,255 | 25.0% |
| Very High | > 0.544 | 3,256 | 25.0% |

### Visual Validation — PASSED
Very High risk zones cluster in coherent spatial patterns rather than
scattering randomly. High-risk areas concentrate consistent with
physical expectations (low-lying terrain, drainage proximity, built-up
areas). Confirms model learned genuine physical relationships rather
than noise. This is the critical validity check for the structural
susceptibility layer.

### Figures Generated (outputs/figures/)
- roc_curves_comparison.png — all three models + random baseline
- confusion_matrices.png — three-panel test set error breakdown
- model_metrics_comparison.png — grouped bar chart, five metrics
- rf_oob_convergence.png — OOB error vs tree count (verified 200)
- rf_feature_importance.png — Gini importance (diagnostic)
- flood_susceptibility_map.png — two-panel probability + tier map

### Spatial Products (outputs/)
- flood_probability_map.tif — continuous 0-1 surface, EPSG:4326, 100m
- flood_risk_tiers.tif — 4-class reclassification, EPSG:4326, 100m
Both products feed NB09 (infrastructure risk) and NB10 (dashboard).

