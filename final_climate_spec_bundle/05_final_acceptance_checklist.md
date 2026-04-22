# Final Acceptance Checklist

A build is considered complete only if all items below are satisfied.

## A. Data scope
- [ ] Source files are read only from `1996-01` to `2025-12`
- [ ] Only `Tair` and `Rainf` are used
- [ ] Invalid rows are removed
- [ ] Derived units `Tair_C` and `Rainf_mm` are created

## B. Climate typing
- [ ] 30-year grid climatology is computed
- [ ] Grid-level climate features are computed
- [ ] Grid-level Köppen–Geiger logic is implemented
- [ ] Raw climate codes are mapped into medium-granularity display classes

## C. Region generation
- [ ] Grid climate classes are merged into contiguous display regions
- [ ] 8-neighbor connectivity is used
- [ ] Tiny-patch merging is implemented
- [ ] Final total number of clickable regions is approximately 8–15

## D. Region outputs
- [ ] `climate_regions.geojson` is created
- [ ] `region_summary.parquet` is created
- [ ] `region_2025_monthly.parquet` is created
- [ ] `region_1996_2025_yearly.parquet` is created

## E. Interface
- [ ] Streamlit app runs
- [ ] Map is colored by display climate class
- [ ] Clicking a region updates the side panel
- [ ] Side panel shows climate label
- [ ] Side panel shows explanation text
- [ ] Side panel shows 2025 monthly chart
- [ ] Side panel shows 1996–2025 annual chart

## F. Static deliverables
- [ ] Final climate-region map figure is saved
- [ ] At least one UI screenshot is saved
- [ ] At least one sample chart figure is saved

## G. Documentation
- [ ] Folder structure is documented
- [ ] Required packages are documented
- [ ] Run instructions are documented
- [ ] Output file meanings are documented

## H. Out-of-scope compliance
- [ ] No global analysis was introduced
- [ ] No country-boundary aggregation was introduced
- [ ] No unnecessary front-end complexity was introduced
- [ ] No unsupported climate logic requiring unavailable variables was introduced
