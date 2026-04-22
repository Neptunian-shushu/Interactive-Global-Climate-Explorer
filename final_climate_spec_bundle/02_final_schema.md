# Final Data Schema

## 1. grid_monthly.parquet
Long-format valid grid-month observations.

### Grain
One row per valid `(time, lat, lon)` record.

### Required columns
- `time` : datetime64[ns]
- `year` : int
- `month` : int
- `lat` : float
- `lon` : float
- `Tair_K` : float
- `Tair_C` : float
- `Rainf_kg_m2` : float
- `Rainf_mm` : float

### Notes
- `Tair_C = Tair_K - 273.15`
- `Rainf_mm = Rainf_kg_m2`
- Keep only rows with finite temperature and precipitation

---

## 2. grid_climatology_1996_2025.parquet
30-year monthly climatology per valid grid cell.

### Grain
One row per `(lat, lon, month)`.

### Required columns
- `lat`
- `lon`
- `month`
- `clim_Tair_C`
- `clim_Rainf_mm`

### Derived from
Average monthly values across 1996–2025.

---

## 3. grid_climate_features.parquet
Feature table used for grid-level Köppen–Geiger classification.

### Grain
One row per valid `(lat, lon)` cell.

### Required columns
- `lat`
- `lon`
- `annual_mean_temp_c`
- `coldest_month_temp_c`
- `hottest_month_temp_c`
- `temp_annual_range_c`
- `annual_total_precip_mm`
- `driest_month_precip_mm`
- `wettest_month_precip_mm`
- `summer_mean_precip_mm`
- `winter_mean_precip_mm`
- `summer_total_precip_mm`
- `winter_total_precip_mm`
- `precip_seasonality_ratio`
- `kg_raw_code` (optional intermediate subtype code)
- `display_climate_class`
- `display_climate_name`

### Definitions
- `temp_annual_range_c = hottest_month_temp_c - coldest_month_temp_c`
- `precip_seasonality_ratio = wettest_month_precip_mm / max(driest_month_precip_mm, 1e-6)`

### Season definition
For this project, define:
- warm season months: `Apr-Sep` = 4,5,6,7,8,9
- cool season months: `Oct-Mar` = 10,11,12,1,2,3

Keep this fixed across the project.

---

## 4. grid_climate_map.parquet
Grid cells with final display class information for map generation.

### Grain
One row per valid `(lat, lon)` cell.

### Required columns
- `lat`
- `lon`
- `display_climate_class`
- `display_climate_name`
- `kg_raw_code` (optional)
- `component_id_premerge` (optional)

---

## 5. climate_regions.geojson
Merged clickable climate-region geometries for UI.

### Feature-level required properties
- `region_id`
- `region_name`
- `display_climate_class`
- `display_climate_name`
- `n_grid`
- `area_proxy_ncells`
- `dominant_raw_code` (optional)
- `explanation_short`

### Geometry
- Polygon or MultiPolygon
- Must be simple enough for Streamlit/Plotly use

---

## 6. region_2025_monthly.parquet
For click-view monthly chart.

### Grain
One row per `(region_id, month)` for year 2025 only.

### Required columns
- `region_id`
- `region_name`
- `display_climate_name`
- `year` = 2025
- `month`
- `mean_Tair_C`
- `mean_Rainf_mm`

---

## 7. region_1996_2025_yearly.parquet
For click-view long-run annual chart.

### Grain
One row per `(region_id, year)`.

### Required columns
- `region_id`
- `region_name`
- `display_climate_name`
- `year`
- `annual_mean_temp_c`
- `annual_total_precip_mm`

---

## 8. region_summary.parquet
Region-level explanatory summary for side panel text.

### Grain
One row per `region_id`.

### Required columns
- `region_id`
- `region_name`
- `display_climate_class`
- `display_climate_name`
- `n_grid`
- `annual_mean_temp_c`
- `annual_total_precip_mm`
- `coldest_month_temp_c`
- `hottest_month_temp_c`
- `temp_annual_range_c`
- `driest_month_precip_mm`
- `wettest_month_precip_mm`
- `summer_total_precip_mm`
- `winter_total_precip_mm`
- `precip_seasonality_ratio`
- `explanation_short`
- `explanation_long` (optional)

---

## 9. UI assets
### app_config.json
Optional metadata/config for the app.

### Required items if created
- color mapping for display classes
- chart titles
- legend labels
- default selected region
