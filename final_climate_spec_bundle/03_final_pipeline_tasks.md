# Final Pipeline Tasks

This file describes the concrete work sequence Codex should implement.

## Overview
The final build should follow this order:

1. ingest and normalize source data;
2. compute 30-year climatology;
3. build grid-level Köppen–Geiger climate labels;
4. merge grid labels into readable display regions;
5. compute region-level monthly and annual summaries for the interface;
6. build the Streamlit interface.

---

## Stage 1. Source file ingestion
### Input requirement
Read all monthly files in the source directory matching:

`NLDAS_FORA0125_M.AYYYYMM.020.nc.SUB.nc4`

### Required date filter
Keep only files from:
- `1996-01`
- through `2025-12`

### Required variables
Extract only:
- `Tair`
- `Rainf`
- `time`
- `lat`
- `lon`

### Output
Create:
- `grid_monthly.parquet`

### Notes
- Drop invalid / non-finite rows
- Preserve original units plus derived units
- Avoid loading all files into memory at once if unnecessary

---

## Stage 2. 30-year grid climatology
### Goal
Compute average monthly climatology for each valid grid cell across 1996–2025.

### Output
Create:
- `grid_climatology_1996_2025.parquet`

### Required method
For each `(lat, lon, month)`:
- average all `Tair_C`
- average all `Rainf_mm`

---

## Stage 3. Grid-level climate feature construction
### Goal
Construct interpretable features needed for Köppen–Geiger logic.

### Output
Create:
- `grid_climate_features.parquet`

### Required features
At minimum:
- annual mean temperature
- coldest month temperature
- hottest month temperature
- annual temperature range
- annual total precipitation
- driest month precipitation
- wettest month precipitation
- warm season precipitation totals/means
- cool season precipitation totals/means
- precipitation seasonality ratio

---

## Stage 4. Grid-level Köppen–Geiger classification
### Goal
Assign each grid cell a climate code using 30-year climatology.

### Implementation guidance
Use standard Köppen–Geiger logic as far as possible with available inputs:
- monthly temperature climatology
- monthly precipitation climatology

### Important constraint
Only two variables are available:
- temperature
- precipitation

So the implementation should focus on the temperature and precipitation criteria directly and should not invent unsupported inputs.

### Internal coding
It is acceptable to compute an intermediate raw class/subtype code.

### Display mapping
Then map raw subtype codes into medium-granularity display classes.

### Output
Create:
- `grid_climate_map.parquet`

---

## Stage 5. Merge grid cells into display regions
### Goal
Build readable clickable climate regions from classified grid cells.

### Required procedure
1. Start with grid-level display classes.
2. Build connected components using **8-neighbor adjacency**.
3. Compute component size in grid-cell count.
4. Merge tiny patches if they are smaller than the threshold.
5. Keep final total region count roughly in the **8–15** range.

### Default tiny-patch threshold
- `20` cells

### Merge rule preference
Merge tiny patches into:
1. the largest adjacent patch of the same display class, if available;
2. otherwise, the dominant adjacent compatible display class.

### Required outputs
Create:
- `climate_regions.geojson`
- `region_summary.parquet`

---

## Stage 6. Build region-level time-series tables
### 6A. 2025 monthly table
For each final merged region, compute:
- monthly mean temperature for 2025
- monthly mean precipitation for 2025

Output:
- `region_2025_monthly.parquet`

### 6B. 1996–2025 yearly table
For each final merged region, compute:
- annual mean temperature
- annual total precipitation

Output:
- `region_1996_2025_yearly.parquet`

---

## Stage 7. Build explanation text
### Goal
Create a concise plain-language explanation for each region.

### Suggested template logic
Explain using:
- annual mean temperature
- annual total precipitation
- coldest/hottest month contrast
- dry vs wet season balance

### Outputs
Populate:
- `explanation_short`
- optionally `explanation_long`

---

## Stage 8. Build the UI
### Stack
- Streamlit
- Plotly

### Layout
#### Left side
- climate-region map
- legend

#### Right side
- selected region title
- climate name
- explanation text
- chart A: 2025 monthly temperature and precipitation
- chart B: 1996–2025 annual temperature and precipitation

### Interaction
- click-first behavior
- hover only for brief tooltip

### Suggested files
- `app.py`
- `ui_helpers.py`
- `load_data.py`

---

## Stage 9. Save report-ready figures
Even though the interface is primary, also generate static figures for the final report.

Recommended figures:
1. final climate-region map
2. one screenshot of selected-region UI
3. one example 2025 monthly chart
4. one example 30-year annual chart
5. class legend figure if needed

---

## Stage 10. Documentation
Add a brief README that explains:
- required packages
- folder layout
- how to run preprocessing
- how to run the Streamlit app
