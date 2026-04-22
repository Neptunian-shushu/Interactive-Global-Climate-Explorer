# Final Scope Freeze

## Project objective
Build a lightweight interactive climate explorer for the NLDAS-covered North America region.

The final system should:
1. classify climate using **Köppen–Geiger** logic from monthly temperature and precipitation;
2. color a North America map by climate region;
3. allow users to **click** a displayed region;
4. show:
   - the region climate name,
   - a concise explanation of why the region is assigned that climate,
   - monthly temperature and precipitation for **2025**,
   - yearly temperature and precipitation trends for **1996–2025**.

## Data source
- Dataset: `NLDAS_FORA0125_M.2.0`
- Variables used:
  - `Tair`: 2-meter above ground temperature (K)
  - `Rainf`: total precipitation (kg m^-2)
- File type: monthly `nc4`
- Spatial scope: NLDAS North America domain only

## Frozen time windows
### Climate classification window
- Use **1996-01 through 2025-12**
- This is the fixed 30-year climate window

### 2025 intra-year display
- Use **2025-01 through 2025-12**
- This powers the click-view monthly chart

### 30-year annual variability display
- Use yearly summaries from **1996 through 2025**
- This powers the click-view annual chart

## Frozen implementation principles
1. Use Python only.
2. Prefer `xarray`, `pandas`, `numpy`, `scipy`, `matplotlib`, `plotly`, `streamlit`.
3. Keep the pipeline modular and reproducible.
4. Preserve clear separation between:
   - grid-level data,
   - climate classification,
   - merged display regions,
   - UI-ready outputs.
5. Use click-first interaction. Hover may show a minimal tooltip only.

## Climate classification granularity
### Internal computation
- Compute **standard Köppen–Geiger subtype-compatible logic** at grid level.

### Final displayed climate categories
Do **not** display the full raw subtype map if it becomes too fragmented.
Instead, merge into a **medium-granularity display layer**.

Recommended display categories:
1. Hot desert
2. Semi-arid / steppe
3. Mediterranean
4. Humid subtropical
5. Marine west coast
6. Humid continental
7. Subarctic
8. Tundra / polar-like
9. Highland (only if clearly needed after patch merging)
10. Other / mixed transition (use only if unavoidable)

Target displayed categories: roughly **8–10 classes**.

## Display-region strategy
Displayed clickable regions are **not** fixed macro-regions and are **not** country polygons.

They should be built as:
1. grid-level climate classification;
2. connected patches of adjacent cells with the same display class;
3. optional merging/smoothing of tiny patches.

### Patch merging target
- Keep the final map readable.
- Aim for approximately **8 to 15 clickable regions total**.
- Fewer than 8 likely over-merges.
- More than 15 likely becomes too fragmented for this project.

### Recommended patch-merging rule
1. Use **8-neighbor connected components**.
2. Compute component size in number of valid grid cells.
3. Any patch smaller than a threshold should be merged into the strongest adjacent compatible patch.

Recommended default threshold:
- **20 grid cells**

Codex may slightly adjust this threshold if needed to keep the final region count in the 8–15 range, but should not introduce complicated optimization.

## What the final map must show
- North America base map
- climate-region polygons or grid-derived merged patches
- one color per display climate class
- click interaction
- a legend

## What the click panel must show
For the clicked region:
1. region identifier / region name
2. display climate name
3. optional underlying KG code summary
4. concise explanation text
5. chart A: 2025 monthly temperature and precipitation
6. chart B: 1996–2025 annual temperature and precipitation

## What is explicitly out of scope
1. Global analysis
2. Country-level aggregation
3. Full-resolution raw cell-by-cell interface
4. Daily or hourly data
5. Statistical clustering as the main climate definition
6. Sophisticated web engineering beyond a clean Streamlit app
7. Large-scale external validation study
8. Overly detailed micrometeorological regionalization
