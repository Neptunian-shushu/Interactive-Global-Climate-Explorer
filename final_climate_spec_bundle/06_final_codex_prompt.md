# Final Codex Prompt

You are implementing the **final version** of a North America climate explorer project.

## Objective
Build a lightweight interactive climate explorer for the **NLDAS-covered North America region** using only monthly temperature and precipitation.

The final system must:
1. classify climate from **1996–2025** using **Köppen–Geiger-compatible temperature/precipitation rules**;
2. merge grid-level classifications into a readable set of clickable climate regions;
3. display a North America map colored by climate region;
4. on click, show:
   - climate name,
   - short explanation,
   - 2025 monthly temperature and precipitation,
   - 1996–2025 annual temperature and precipitation.

## Data source
Use the monthly `nc4` files in a single directory.

### Filename pattern
`NLDAS_FORA0125_M.AYYYYMM.020.nc.SUB.nc4`

### Required source window
Keep only files from:
- `1996-01`
- through `2025-12`

### Required variables only
- `Tair`
- `Rainf`

Do not use other variables.

## Folder setup
Assume the project root is organized like this:

```text
project_root/
    data_raw/
        NLDAS_FORA0125_M.A199601.020.nc.SUB.nc4
        ...
        NLDAS_FORA0125_M.A202512.020.nc.SUB.nc4
    outputs/
    figures/
    app/
```

If needed, allow the raw data directory to be configurable through a constant or CLI argument.

## Required implementation stages

### Stage 1. Build normalized grid-month table
Read all source files, filter to 1996-01..2025-12, keep only valid rows, and save:
- `outputs/grid_monthly.parquet`

Required columns:
- `time`, `year`, `month`, `lat`, `lon`,
- `Tair_K`, `Tair_C`,
- `Rainf_kg_m2`, `Rainf_mm`

### Stage 2. Build 30-year grid climatology
Compute `(lat, lon, month)` climatology across 1996–2025 and save:
- `outputs/grid_climatology_1996_2025.parquet`

### Stage 3. Build grid climate features
Compute features needed for climate classification and save:
- `outputs/grid_climate_features.parquet`

### Stage 4. Grid-level climate classification
Use standard Köppen–Geiger-compatible logic based only on monthly temperature and precipitation climatology.
It is acceptable to compute internal raw subtype codes, but the final display must use **medium-granularity classes**.

Recommended display classes:
- Hot desert
- Semi-arid / steppe
- Mediterranean
- Humid subtropical
- Marine west coast
- Humid continental
- Subarctic
- Tundra / polar-like
- Highland (only if needed)
- Other / mixed transition (only if unavoidable)

Save:
- `outputs/grid_climate_map.parquet`

### Stage 5. Merge into clickable climate regions
1. Build connected components using **8-neighbor adjacency**.
2. Merge tiny patches under a default threshold of **20 grid cells**.
3. Keep the final number of clickable regions roughly in the **8–15** range.
4. Favor readability over excessive detail.

Save:
- `outputs/climate_regions.geojson`
- `outputs/region_summary.parquet`

### Stage 6. Build UI tables
Create:
- `outputs/region_2025_monthly.parquet`
- `outputs/region_1996_2025_yearly.parquet`

These power the click-view charts.

### Stage 7. Build Streamlit app
Use:
- Streamlit
- Plotly

App requirements:
- left: climate-region map with legend
- right: selected region title, climate label, short explanation
- chart A: 2025 monthly temperature and precipitation
- chart B: 1996–2025 annual temperature and precipitation

Interaction:
- click-first
- hover only for minimal tooltip

### Stage 8. Save report-ready figures
Save at least:
- `figures/final_climate_region_map.png`
- `figures/final_ui_screenshot.png` (or clear saved screenshot instruction if full automated screenshot is not feasible)
- `figures/example_2025_monthly_chart.png`
- `figures/example_30yr_annual_chart.png`

## Quality priorities
1. Code must be concise, readable, and efficient.
2. The system should be robust and easy to run.
3. Do not over-engineer the UI.
4. Do not create unnecessary files.
5. Keep explanations and labels simple and clear.

## Deliverables
Please produce:
1. Python scripts/modules
2. output parquet/geojson files
3. Streamlit app
4. static figures
5. brief README with run instructions

## Important constraints
- No global analysis
- No country-boundary aggregation
- No daily/hourly expansion
- No overly fine-grained fragmentation
- No unsupported climate logic requiring unavailable variables
