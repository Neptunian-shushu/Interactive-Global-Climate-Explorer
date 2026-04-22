# Final UI Data Spec

## UI goal
Provide a clean click-first interface for a North America climate explorer.

## Recommended stack
- Streamlit
- Plotly
- GeoJSON-backed region rendering

## UI layout
### Left panel
Map view:
- merged climate regions
- colored by `display_climate_name`
- legend visible
- click selects one region

### Right panel
Selected region details:
1. region name
2. climate label
3. short explanation
4. 2025 monthly chart
5. 1996–2025 annual chart

## Region naming rule
Keep names simple.
Suggested naming pattern:
- `Region 01 - Humid Subtropical East`
- `Region 02 - Marine West Coast`
- `Region 03 - Semi-arid Interior`

Names do not need to correspond to political geography.

## Display climate naming
### Recommended main display label
Use friendly text:
- `Hot desert`
- `Semi-arid / steppe`
- `Mediterranean`
- `Humid subtropical`
- `Marine west coast`
- `Humid continental`
- `Subarctic`
- `Tundra / polar-like`
- `Highland` (only if needed)

### Optional secondary label
Show Köppen-like code in smaller text if available:
- e.g. `Humid subtropical (Cfa)`

## Color rule
Colors should be stable and distinct.
Suggested semantic mapping:
- deserts: warm orange
- semi-arid: sandy yellow-brown
- Mediterranean: muted olive
- humid subtropical: green
- marine west coast: teal
- humid continental: blue
- subarctic: indigo
- tundra / polar-like: gray-blue
- highland: purple-gray

Do not overuse many similar shades.

## Chart A: 2025 monthly climate
### Purpose
Show within-year seasonal pattern for the selected region.

### X-axis
- months Jan–Dec

### Y-values
- line: monthly mean temperature (°C)
- bars or second line: monthly mean precipitation (mm)

### Data source
- `region_2025_monthly.parquet`

## Chart B: 30-year annual variability
### Purpose
Show how the selected region varies year to year across 1996–2025.

### X-axis
- years 1996–2025

### Y-values
- line 1: annual mean temperature (°C)
- line 2 or bar/line combo: annual total precipitation (mm)

### Data source
- `region_1996_2025_yearly.parquet`

## Tooltip minimum
On map hover, show only:
- region name
- climate label

No heavy tooltip text.

## Explanation text style
Keep it short and readable.
Example style:
- `Warm and humid with high annual rainfall and a relatively mild winter.`
- `Dry interior climate with low annual precipitation and a large summer-winter contrast.`

## UI performance requirement
The app should load quickly and avoid reconstructing expensive data objects on every click.
Use cached loading where appropriate.

## Deliverable expectation
A simple but polished app is preferred over a complex, fragile one.
