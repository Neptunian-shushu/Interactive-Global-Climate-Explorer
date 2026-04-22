# Interactive Global Climate Explorer

This repository rebuilds the final North America climate explorer from raw monthly NLDAS `nc4` files only. The pipeline reads monthly `Tair` and `Rainf` fields for `1996-01` through `2025-12`, computes a 30-year climatology, assigns grid-level Koppen-Geiger-compatible climate labels, merges those labels into readable clickable display regions, and serves the results in a Streamlit app.

The GitHub-ready repo excludes the local `earth/` raw archive and the heavyweight intermediate file `outputs/grid_monthly.parquet` because they are regenerated locally from source data. The published repo keeps the code, documentation, figures, and app-ready outputs needed to inspect or run the UI immediately.

## Project Layout

```text
Interactive-Global-Climate-Explorer/
├── earth/                            # raw monthly nc4 files
├── figures/                          # regenerated report-ready figures
├── outputs/                          # regenerated parquet, geojson, app config
├── src/climate_explorer/             # pipeline + UI package
├── app.py                            # Streamlit entrypoint
├── run_pipeline.py                   # full preprocessing entrypoint (with CLI args)
├── pyproject.toml                    # package metadata and install config
├── FINAL_REPORT.md                   # final report-style summary
├── FINAL_ACCEPTANCE_CHECKLIST.md     # completed acceptance checklist
└── requirements.txt
```

## Environment

Install the required packages:

```bash
python -m pip install -r requirements.txt
```

Or install as an editable package (recommended):

```bash
pip install -e .
```

The implementation uses:

- `netCDF4`, `xarray`
- `numpy`, `pandas`, `pyarrow`, `scipy`
- `matplotlib`, `plotly`, `streamlit`
- `shapely`, `scikit-learn`

## Run The Full Pipeline

The raw data directory is expected at `earth/` and must contain monthly files named like:

```text
NLDAS_FORA0125_M.AYYYYMM.020.nc.SUB.nc4
```

Run the full rebuild with default settings:

```bash
python run_pipeline.py
```

Or customize via CLI arguments:

```bash
python run_pipeline.py --start 200001 --end 202512 --raw-dir ./earth --output-dir ./outputs
```

Available options:

| Flag | Default | Description |
|------|---------|-------------|
| `--raw-dir` | `./earth` | Directory containing raw NLDAS nc4 files |
| `--output-dir` | `./outputs` | Output directory for parquet/geojson files |
| `--figure-dir` | `./figures` | Output directory for report figures |
| `--start` | `199601` | Start year-month as YYYYMM |
| `--end` | `202512` | End year-month as YYYYMM |

This regenerates:

- `outputs/grid_monthly.parquet`
- `outputs/grid_climatology_1996_2025.parquet`
- `outputs/grid_climate_features.parquet`
- `outputs/grid_climate_map.parquet`
- `outputs/climate_regions.geojson`
- `outputs/region_summary.parquet`
- `outputs/region_2025_monthly.parquet`
- `outputs/region_1996_2025_yearly.parquet`
- `outputs/app_config.json`
- `figures/final_climate_region_map.png`
- `figures/final_ui_screenshot.png`
- `figures/example_2025_monthly_chart.png`
- `figures/example_30yr_annual_chart.png`

## Run The Streamlit App

After the outputs exist, launch the interface with:

```bash
streamlit run app.py
```

### Features

- **Interactive climate region map** with click-to-select and hover tooltips showing temperature and precipitation
- **Climate type filter** to highlight specific climate zones on the map
- **Region detail panel** with climate label, explanation, 4 key metrics
- **2025 monthly chart** showing temperature curve and precipitation bars
- **30-year annual chart** with optional linear regression trend lines showing the climate change signal
- **Region comparison mode** to view two regions side-by-side with temperature and precipitation comparison charts
- **CSV export** for downloading any region's monthly and annual data
- **Polished UI** with custom styling, chip-style legend, and responsive layout

## Regenerated Output Meaning

- `grid_monthly.parquet`: one valid `(time, lat, lon)` row per month-grid observation
- `grid_climatology_1996_2025.parquet`: 30-year monthly climatology for each valid grid cell
- `grid_climate_features.parquet`: grid-level climate features and raw/display climate labels
- `grid_climate_map.parquet`: final map-ready climate class per classified cell
- `climate_regions.geojson`: merged clickable climate-region polygons or multipolygons
- `region_summary.parquet`: region-level descriptive summary and explanation text
- `region_2025_monthly.parquet`: selected-region monthly chart source for 2025
- `region_1996_2025_yearly.parquet`: selected-region annual chart source for 1996-2025

## Final Run Summary

The full raw-data rebuild completed with:

- `360` monthly source files
- `28,958,040` valid monthly grid observations
- `80,439` classified grid cells
- `15` clickable climate regions
- patch smoothing threshold `60`

The detailed methodology, regenerated region inventory, and acceptance summary are in [FINAL_REPORT.md](FINAL_REPORT.md) and [FINAL_ACCEPTANCE_CHECKLIST.md](FINAL_ACCEPTANCE_CHECKLIST.md).
