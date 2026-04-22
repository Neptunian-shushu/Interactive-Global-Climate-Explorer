# Final Acceptance Checklist

## A. Data scope

- [x] Source files are read only from `1996-01` to `2025-12`
- [x] Only `Tair` and `Rainf` are used
- [x] Invalid rows are removed
- [x] Derived units `Tair_C` and `Rainf_mm` are created

## B. Climate typing

- [x] 30-year grid climatology is computed
- [x] Grid-level climate features are computed
- [x] Grid-level Koppen-Geiger-compatible logic is implemented
- [x] Raw climate codes are mapped into medium-granularity display classes

## C. Region generation

- [x] Grid climate classes are merged into contiguous display regions
- [x] 8-neighbor connectivity is used
- [x] Tiny-patch merging is implemented
- [x] Final total number of clickable regions is approximately 8-15

## D. Region outputs

- [x] `climate_regions.geojson` is created
- [x] `region_summary.parquet` is created
- [x] `region_2025_monthly.parquet` is created
- [x] `region_1996_2025_yearly.parquet` is created

## E. Interface

- [x] Streamlit app runs
- [x] Map is colored by display climate class
- [x] Clicking a region updates the side panel
- [x] Side panel shows climate label
- [x] Side panel shows explanation text
- [x] Side panel shows 2025 monthly chart
- [x] Side panel shows 1996-2025 annual chart

## F. Static deliverables

- [x] Final climate-region map figure is saved
- [x] At least one UI screenshot is saved
- [x] At least one sample chart figure is saved

## G. Documentation

- [x] Folder structure is documented
- [x] Required packages are documented
- [x] Run instructions are documented
- [x] Output file meanings are documented

## H. Out-of-scope compliance

- [x] No global analysis was introduced
- [x] No country-boundary aggregation was introduced
- [x] No unnecessary front-end complexity was introduced
- [x] No unsupported climate logic requiring unavailable variables was introduced
