# Final Climate Explorer Spec Bundle

This bundle freezes the final-scope implementation for the North America climate explorer project.

## Included files
- `01_final_scope_freeze.md`
- `02_final_schema.md`
- `03_final_pipeline_tasks.md`
- `04_final_ui_data_spec.md`
- `05_final_acceptance_checklist.md`
- `06_final_codex_prompt.md`

## Final frozen decisions
- Study area: NLDAS-covered North America domain only.
- Variables used: `Tair` and `Rainf` only.
- Climate typing window: **1996-01 to 2025-12** (30 complete years).
- 2025 within-year chart window: **2025-01 to 2025-12**.
- Annual variability chart window: **1996 to 2025**.
- Climate method: grid-level **Köppen–Geiger**, then merged into **medium-granularity display classes**.
- Interaction: **click-first** interface.
- Front-end stack: **Streamlit + Plotly**.
- Map regions: merged climate patches; target total number of displayed clickable regions is roughly **8 to 15**.

## Required source data
All monthly source files should be placed in one directory and follow this filename pattern:

`NLDAS_FORA0125_M.AYYYYMM.020.nc.SUB.nc4`

Example directory:
```text
project_root/
    data_raw/
        NLDAS_FORA0125_M.A199601.020.nc.SUB.nc4
        NLDAS_FORA0125_M.A199602.020.nc.SUB.nc4
        ...
        NLDAS_FORA0125_M.A202512.020.nc.SUB.nc4
```

Only files from `1996-01` through `2025-12` are required for the final implementation.
