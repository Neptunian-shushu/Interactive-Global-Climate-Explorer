from __future__ import annotations

import json
import math
import re
import warnings
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import pyarrow as pa
import pyarrow.parquet as pq
import xarray as xr
from matplotlib.colors import ListedColormap
from matplotlib.lines import Line2D
from matplotlib.patches import Patch
from scipy import ndimage
from shapely.geometry import box, mapping
from shapely.ops import unary_union

from .config import (
    COOL_SEASON_MONTHS,
    DEFAULT_PATHS,
    DISPLAY_REGION_ANCHOR_MIN,
    DISPLAY_CLASS_COMPATIBILITY,
    DISPLAY_CLASS_ORDER,
    DISPLAY_CLASS_STYLES,
    GRID_RESOLUTION,
    PATCH_THRESHOLD_CANDIDATES,
    START_YM,
    END_YM,
    TARGET_REGION_MAX,
    TARGET_REGION_MIN,
    WARM_SEASON_MONTHS,
    ProjectPaths,
)


FILE_PATTERN = re.compile(r"NLDAS_FORA0125_M\.A(\d{6})\.020\.nc\.SUB\.nc4$")
NEIGHBORHOOD = np.ones((3, 3), dtype=int)


@dataclass
class CubeData:
    times: pd.DatetimeIndex
    years: np.ndarray
    months: np.ndarray
    lat: np.ndarray
    lon: np.ndarray
    temp_k: np.ndarray
    rain_mm: np.ndarray

    @property
    def temp_c(self) -> np.ndarray:
        return self.temp_k - 273.15


def ym_from_name(path: Path) -> int:
    match = FILE_PATTERN.search(path.name)
    if not match:
        raise ValueError(f"Unexpected filename: {path.name}")
    return int(match.group(1))


def list_source_files(raw_dir: Path, start_ym: int = START_YM, end_ym: int = END_YM) -> list[Path]:
    files = sorted(raw_dir.glob("NLDAS_FORA0125_M.A*.020.nc.SUB.nc4"), key=ym_from_name)
    selected = [path for path in files if start_ym <= ym_from_name(path) <= end_ym]
    if not selected:
        raise FileNotFoundError(f"No matching nc4 files found in {raw_dir}")
    expected = (end_ym // 100 - start_ym // 100) * 12 + (end_ym % 100 - start_ym % 100) + 1
    if len(selected) != expected:
        raise ValueError(f"Expected {expected} monthly files between {start_ym} and {end_ym}, found {len(selected)}")
    return selected


def load_cube(files: list[Path]) -> CubeData:
    times: list[pd.Timestamp] = []
    temp_blocks: list[np.ndarray] = []
    rain_blocks: list[np.ndarray] = []
    lat: np.ndarray | None = None
    lon: np.ndarray | None = None
    for idx, path in enumerate(files, start=1):
        with xr.open_dataset(path, engine="netcdf4") as ds:
            if lat is None:
                lat = ds["lat"].values.astype(np.float32)
                lon = ds["lon"].values.astype(np.float32)
            times.append(pd.Timestamp(ds["time"].values[0]))
            temp_blocks.append(ds["Tair"].values[0].astype(np.float32))
            rain_blocks.append(ds["Rainf"].values[0].astype(np.float32))
        if idx % 24 == 0 or idx == len(files):
            print(f"Loaded {idx}/{len(files)} monthly files")
    assert lat is not None and lon is not None
    dt_index = pd.DatetimeIndex(times)
    return CubeData(
        times=dt_index,
        years=dt_index.year.to_numpy(),
        months=dt_index.month.to_numpy(),
        lat=lat,
        lon=lon,
        temp_k=np.stack(temp_blocks, axis=0),
        rain_mm=np.stack(rain_blocks, axis=0),
    )


def write_grid_monthly_parquet(cube: CubeData, out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    lat_grid, lon_grid = np.meshgrid(cube.lat, cube.lon, indexing="ij")
    lat_flat = lat_grid.ravel()
    lon_flat = lon_grid.ravel()
    writer: pq.ParquetWriter | None = None
    try:
        for idx, timestamp in enumerate(cube.times):
            temp_k = cube.temp_k[idx].ravel()
            temp_c = temp_k - 273.15
            rain_mm = cube.rain_mm[idx].ravel()
            valid = np.isfinite(temp_k) & np.isfinite(rain_mm)
            frame = pd.DataFrame(
                {
                    "time": pd.to_datetime(np.repeat(timestamp, valid.sum())),
                    "year": np.repeat(timestamp.year, valid.sum()),
                    "month": np.repeat(timestamp.month, valid.sum()),
                    "lat": lat_flat[valid],
                    "lon": lon_flat[valid],
                    "Tair_K": temp_k[valid].astype(np.float32),
                    "Tair_C": temp_c[valid].astype(np.float32),
                    "Rainf_kg_m2": rain_mm[valid].astype(np.float32),
                    "Rainf_mm": rain_mm[valid].astype(np.float32),
                }
            )
            table = pa.Table.from_pandas(frame, preserve_index=False)
            if writer is None:
                writer = pq.ParquetWriter(out_path, table.schema, compression="snappy")
            writer.write_table(table)
        print(f"Wrote {out_path}")
    finally:
        if writer is not None:
            writer.close()


def build_climatology(cube: CubeData) -> tuple[pd.DataFrame, np.ndarray, np.ndarray, np.ndarray]:
    temp_c = cube.temp_c
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        monthly_temp = np.stack([np.nanmean(temp_c[cube.months == month], axis=0) for month in range(1, 13)], axis=0)
        monthly_rain = np.stack([np.nanmean(cube.rain_mm[cube.months == month], axis=0) for month in range(1, 13)], axis=0)
    valid_mask = np.all(np.isfinite(monthly_temp), axis=0) & np.all(np.isfinite(monthly_rain), axis=0)
    lat_grid, lon_grid = np.meshgrid(cube.lat, cube.lon, indexing="ij")
    records = []
    for month in range(1, 13):
        records.append(
            pd.DataFrame(
                {
                    "lat": lat_grid[valid_mask].astype(np.float32),
                    "lon": lon_grid[valid_mask].astype(np.float32),
                    "month": month,
                    "clim_Tair_C": monthly_temp[month - 1][valid_mask].astype(np.float32),
                    "clim_Rainf_mm": monthly_rain[month - 1][valid_mask].astype(np.float32),
                }
            )
        )
    climatology_df = pd.concat(records, ignore_index=True)
    return climatology_df, monthly_temp, monthly_rain, valid_mask


def _resolve_c_dryness(monthly_precip: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    summer_idx = np.array([month - 1 for month in sorted(WARM_SEASON_MONTHS)], dtype=int)
    winter_idx = np.array([month - 1 for month in sorted(COOL_SEASON_MONTHS)], dtype=int)
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        driest_summer = np.nanmin(monthly_precip[summer_idx], axis=0)
        wettest_summer = np.nanmax(monthly_precip[summer_idx], axis=0)
        driest_winter = np.nanmin(monthly_precip[winter_idx], axis=0)
        wettest_winter = np.nanmax(monthly_precip[winter_idx], axis=0)
    summer_dry = (driest_summer < 40.0) & (driest_summer < wettest_winter / 3.0)
    winter_dry = driest_winter < wettest_summer / 10.0
    return summer_dry, winter_dry


def _heat_suffix(months_ge_10: np.ndarray, hottest: np.ndarray) -> np.ndarray:
    suffix = np.full(hottest.shape, "c", dtype="<U1")
    suffix[(months_ge_10 >= 4) & (hottest < 22.0)] = "b"
    suffix[hottest >= 22.0] = "a"
    return suffix


def classify_climate(monthly_temp: np.ndarray, monthly_precip: np.ndarray, valid_mask: np.ndarray) -> pd.DataFrame:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore", category=RuntimeWarning)
        annual_mean_temp = np.nanmean(monthly_temp, axis=0)
        coldest = np.nanmin(monthly_temp, axis=0)
        hottest = np.nanmax(monthly_temp, axis=0)
        annual_precip = np.nansum(monthly_precip, axis=0)
        driest = np.nanmin(monthly_precip, axis=0)
        wettest = np.nanmax(monthly_precip, axis=0)
        summer_mean = np.nanmean(monthly_precip[np.array([month - 1 for month in sorted(WARM_SEASON_MONTHS)], dtype=int)], axis=0)
        winter_mean = np.nanmean(monthly_precip[np.array([month - 1 for month in sorted(COOL_SEASON_MONTHS)], dtype=int)], axis=0)
    temp_range = hottest - coldest

    summer_idx = np.array([month - 1 for month in sorted(WARM_SEASON_MONTHS)], dtype=int)
    winter_idx = np.array([month - 1 for month in sorted(COOL_SEASON_MONTHS)], dtype=int)
    summer_total = np.nansum(monthly_precip[summer_idx], axis=0)
    winter_total = np.nansum(monthly_precip[winter_idx], axis=0)
    seasonality_ratio = wettest / np.maximum(driest, 1e-6)
    months_ge_10 = np.sum(monthly_temp >= 10.0, axis=0)

    summer_dry, winter_dry = _resolve_c_dryness(monthly_precip)
    summer_fraction = summer_total / np.maximum(annual_precip, 1e-6)
    precip_threshold = 20.0 * annual_mean_temp + np.select(
        [summer_fraction >= 0.7, summer_fraction <= 0.3],
        [280.0, 0.0],
        default=140.0,
    )
    precip_threshold = np.maximum(precip_threshold, 0.0)

    raw_code = np.full(annual_mean_temp.shape, "Unclassified", dtype="<U14")
    display_name = np.full(annual_mean_temp.shape, "Other / mixed transition", dtype="<U28")

    arid = annual_precip < precip_threshold
    desert = annual_precip < (0.5 * precip_threshold)
    hot = annual_mean_temp >= 18.0

    raw_code[arid & desert & hot] = "BWh"
    raw_code[arid & desert & ~hot] = "BWk"
    raw_code[arid & ~desert & hot] = "BSh"
    raw_code[arid & ~desert & ~hot] = "BSk"

    display_name[np.char.startswith(raw_code.astype(str), "BW")] = "Hot desert"
    display_name[np.char.startswith(raw_code.astype(str), "BS")] = "Semi-arid / steppe"

    polar = ~arid & (hottest < 10.0)
    raw_code[polar & (hottest >= 0.0)] = "ET"
    raw_code[polar & (hottest < 0.0)] = "EF"
    display_name[polar] = "Tundra / polar-like"

    tropical = ~arid & ~polar & (coldest >= 18.0)
    raw_code[tropical] = "Aw"
    display_name[tropical] = "Other / mixed transition"

    temperate = ~arid & ~polar & ~tropical & (coldest >= 0.0)
    continental = ~arid & ~polar & ~tropical & (coldest < 0.0) & (hottest >= 10.0)

    c_suffix = _heat_suffix(months_ge_10, hottest)

    raw_code[temperate & summer_dry] = np.char.add("Cs", c_suffix[temperate & summer_dry])
    raw_code[temperate & ~summer_dry & winter_dry] = np.char.add("Cw", c_suffix[temperate & ~summer_dry & winter_dry])
    raw_code[temperate & ~summer_dry & ~winter_dry] = np.char.add("Cf", c_suffix[temperate & ~summer_dry & ~winter_dry])

    d_suffix = np.full(hottest.shape, "c", dtype="<U1")
    d_suffix[(continental) & (months_ge_10 >= 4) & (hottest < 22.0)] = "b"
    d_suffix[(continental) & (hottest >= 22.0)] = "a"
    raw_code[continental & summer_dry] = np.char.add("Ds", d_suffix[continental & summer_dry])
    raw_code[continental & ~summer_dry & winter_dry] = np.char.add("Dw", d_suffix[continental & ~summer_dry & winter_dry])
    raw_code[continental & ~summer_dry & ~winter_dry] = np.char.add("Df", d_suffix[continental & ~summer_dry & ~winter_dry])

    for code in ["Csa", "Csb", "Csc"]:
        display_name[raw_code == code] = "Mediterranean"
    for code in ["Cfa", "Cwa", "Cwb"]:
        display_name[raw_code == code] = "Humid subtropical"
    for code in ["Cfb", "Cfc", "Cwc"]:
        display_name[raw_code == code] = "Marine west coast"
    for code in ["Dfa", "Dfb", "Dwa", "Dwb", "Dsa", "Dsb"]:
        display_name[raw_code == code] = "Humid continental"
    for code in ["Dfc", "Dwc", "Dsc"]:
        display_name[raw_code == code] = "Subarctic"

    lat_grid, lon_grid = np.meshgrid(np.arange(valid_mask.shape[0]), np.arange(valid_mask.shape[1]), indexing="ij")
    valid_idx = valid_mask
    feature_df = pd.DataFrame(
        {
            "lat_idx": lat_grid[valid_idx].astype(np.int16),
            "lon_idx": lon_grid[valid_idx].astype(np.int16),
            "annual_mean_temp_c": annual_mean_temp[valid_idx].astype(np.float32),
            "coldest_month_temp_c": coldest[valid_idx].astype(np.float32),
            "hottest_month_temp_c": hottest[valid_idx].astype(np.float32),
            "temp_annual_range_c": temp_range[valid_idx].astype(np.float32),
            "annual_total_precip_mm": annual_precip[valid_idx].astype(np.float32),
            "driest_month_precip_mm": driest[valid_idx].astype(np.float32),
            "wettest_month_precip_mm": wettest[valid_idx].astype(np.float32),
            "summer_mean_precip_mm": summer_mean[valid_idx].astype(np.float32),
            "winter_mean_precip_mm": winter_mean[valid_idx].astype(np.float32),
            "summer_total_precip_mm": summer_total[valid_idx].astype(np.float32),
            "winter_total_precip_mm": winter_total[valid_idx].astype(np.float32),
            "precip_seasonality_ratio": seasonality_ratio[valid_idx].astype(np.float32),
            "kg_raw_code": raw_code[valid_idx].astype(str),
            "display_climate_name": display_name[valid_idx].astype(str),
        }
    )
    feature_df["display_climate_class"] = feature_df["display_climate_name"].map(
        lambda name: DISPLAY_CLASS_STYLES[name]["slug"]
    )
    return feature_df


def _component_table(class_grid: np.ndarray) -> tuple[np.ndarray, pd.DataFrame]:
    component_map = np.zeros(class_grid.shape, dtype=np.int32)
    records: list[dict[str, Any]] = []
    next_id = 1
    for class_name in DISPLAY_CLASS_ORDER:
        mask = class_grid == class_name
        if not np.any(mask):
            continue
        labeled, n_components = ndimage.label(mask, structure=NEIGHBORHOOD)
        for local_id in range(1, n_components + 1):
            region_mask = labeled == local_id
            component_map[region_mask] = next_id
            records.append(
                {
                    "component_id": next_id,
                    "display_climate_name": class_name,
                    "n_grid": int(region_mask.sum()),
                }
            )
            next_id += 1
    return component_map, pd.DataFrame(records)


def _pick_neighbor_class(
    source_class: str,
    neighbor_components: np.ndarray,
    neighbor_classes: np.ndarray,
    component_sizes: dict[int, int],
) -> str | None:
    if neighbor_components.size == 0:
        return None
    compatibility = DISPLAY_CLASS_COMPATIBILITY[source_class]
    scores: dict[tuple[int, str], int] = {}
    for comp_id, class_name in zip(neighbor_components.tolist(), neighbor_classes.tolist()):
        if class_name == source_class:
            continue
        if class_name not in compatibility and source_class != "Other / mixed transition":
            continue
        scores[(int(comp_id), str(class_name))] = scores.get((int(comp_id), str(class_name)), 0) + 1
    if not scores:
        for comp_id, class_name in zip(neighbor_components.tolist(), neighbor_classes.tolist()):
            if class_name == source_class:
                continue
            scores[(int(comp_id), str(class_name))] = scores.get((int(comp_id), str(class_name)), 0) + 1
    if not scores:
        return None
    best = sorted(
        scores.items(),
        key=lambda item: (item[1], component_sizes.get(item[0][0], 0)),
        reverse=True,
    )[0][0]
    return best[1]


def merge_small_patches(class_grid: np.ndarray, threshold: int) -> tuple[np.ndarray, np.ndarray, pd.DataFrame]:
    merged = class_grid.copy()
    for _ in range(12):
        component_map, components = _component_table(merged)
        small = components[components["n_grid"] < threshold].sort_values("n_grid")
        if small.empty:
            return merged, component_map, components
        component_sizes = dict(zip(components["component_id"], components["n_grid"]))
        changed = False
        for _, row in small.iterrows():
            comp_id = int(row["component_id"])
            component_mask = component_map == comp_id
            if not np.any(component_mask):
                continue
            source_class = str(row["display_climate_name"])
            border = ndimage.binary_dilation(component_mask, structure=NEIGHBORHOOD) & ~component_mask & (merged != "")
            neighbor_components = component_map[border]
            neighbor_classes = merged[border]
            target_class = _pick_neighbor_class(source_class, neighbor_components, neighbor_classes, component_sizes)
            if target_class is None:
                continue
            merged[component_mask] = target_class
            changed = True
        if not changed:
            return merged, component_map, components
    component_map, components = _component_table(merged)
    return merged, component_map, components


def pick_best_patch_threshold(class_grid: np.ndarray) -> tuple[int, np.ndarray, np.ndarray, pd.DataFrame]:
    best_result: tuple[int, np.ndarray, np.ndarray, pd.DataFrame] | None = None
    best_score = math.inf
    for threshold in PATCH_THRESHOLD_CANDIDATES:
        merged_grid, component_map, components = merge_small_patches(class_grid, threshold)
        region_count = len(components)
        midpoint_penalty = abs(region_count - (TARGET_REGION_MIN + TARGET_REGION_MAX) / 2)
        range_penalty = 0 if TARGET_REGION_MIN <= region_count <= TARGET_REGION_MAX else min(
            abs(region_count - TARGET_REGION_MIN),
            abs(region_count - TARGET_REGION_MAX),
        ) * 10
        score = range_penalty + midpoint_penalty
        if score < best_score:
            best_score = score
            best_result = (threshold, merged_grid, component_map, components)
        if TARGET_REGION_MIN <= region_count <= TARGET_REGION_MAX:
            return threshold, merged_grid, component_map, components
    assert best_result is not None
    return best_result


def summarize_components(component_map: np.ndarray, merged_grid: np.ndarray, cube: CubeData) -> pd.DataFrame:
    records: list[dict[str, Any]] = []
    for component_id in np.unique(component_map):
        if component_id == 0:
            continue
        mask = component_map == component_id
        class_name = str(merged_grid[mask][0])
        records.append(
            {
                "component_id": int(component_id),
                "display_climate_name": class_name,
                "n_grid": int(mask.sum()),
                "centroid_lat": float(np.mean(cube.lat[np.where(mask)[0]])),
                "centroid_lon": float(np.mean(cube.lon[np.where(mask)[1]])),
            }
        )
    return pd.DataFrame(records)


def select_anchor_components(components: pd.DataFrame, anchor_min: int = DISPLAY_REGION_ANCHOR_MIN) -> pd.DataFrame:
    anchors = components[components["n_grid"] >= anchor_min].copy()
    if anchors.empty:
        anchors = components.nlargest(1, "n_grid").copy()
    for climate_name, group in components.groupby("display_climate_name"):
        if climate_name not in set(anchors["display_climate_name"]):
            anchors = pd.concat([anchors, group.nlargest(1, "n_grid")], ignore_index=True)
    anchors = anchors.drop_duplicates(subset=["component_id"]).sort_values(
        ["display_climate_name", "centroid_lon", "centroid_lat"]
    )
    return anchors.reset_index(drop=True)


def assign_components_to_anchors(components: pd.DataFrame, anchors: pd.DataFrame) -> dict[int, int]:
    assignments = {int(row["component_id"]): int(row["component_id"]) for _, row in anchors.iterrows()}
    anchor_rows = anchors.to_dict("records")
    for _, component in components.iterrows():
        comp_id = int(component["component_id"])
        if comp_id in assignments:
            continue
        same_class = [row for row in anchor_rows if row["display_climate_name"] == component["display_climate_name"]]
        if same_class:
            candidates = same_class
        else:
            compatible = DISPLAY_CLASS_COMPATIBILITY[str(component["display_climate_name"])]
            candidates = [row for row in anchor_rows if row["display_climate_name"] in compatible]
            if not candidates:
                candidates = anchor_rows
        target = min(
            candidates,
            key=lambda row: (
                (row["centroid_lon"] - component["centroid_lon"]) ** 2 + (row["centroid_lat"] - component["centroid_lat"]) ** 2,
                -row["n_grid"],
            ),
        )
        assignments[comp_id] = int(target["component_id"])
    return assignments


def pick_best_display_regions(
    class_grid: np.ndarray,
    cube: CubeData,
    anchor_min: int = DISPLAY_REGION_ANCHOR_MIN,
) -> tuple[int, np.ndarray, np.ndarray, pd.DataFrame, pd.DataFrame, dict[int, int]]:
    best_result: tuple[int, np.ndarray, np.ndarray, pd.DataFrame, pd.DataFrame, dict[int, int]] | None = None
    best_score = math.inf
    for threshold in PATCH_THRESHOLD_CANDIDATES:
        merged_grid, component_map, _ = merge_small_patches(class_grid, threshold)
        components = summarize_components(component_map, merged_grid, cube)
        anchors = select_anchor_components(components, anchor_min=anchor_min)
        assignments = assign_components_to_anchors(components, anchors)
        region_count = len(anchors)
        midpoint_penalty = abs(region_count - (TARGET_REGION_MIN + TARGET_REGION_MAX) / 2)
        range_penalty = 0 if TARGET_REGION_MIN <= region_count <= TARGET_REGION_MAX else min(
            abs(region_count - TARGET_REGION_MIN),
            abs(region_count - TARGET_REGION_MAX),
        ) * 10
        score = range_penalty + midpoint_penalty
        if score < best_score:
            best_score = score
            best_result = (threshold, merged_grid, component_map, components, anchors, assignments)
        if TARGET_REGION_MIN <= region_count <= TARGET_REGION_MAX:
            return threshold, merged_grid, component_map, components, anchors, assignments
    assert best_result is not None
    return best_result


def classify_orientation(lon: float, lat: float, lon_bounds: tuple[float, float], lat_bounds: tuple[float, float]) -> str:
    lon_min, lon_max = lon_bounds
    lat_min, lat_max = lat_bounds
    lon_thirds = np.linspace(lon_min, lon_max, 4)
    lat_thirds = np.linspace(lat_min, lat_max, 4)
    if lon <= lon_thirds[1]:
        x_label = "West"
    elif lon >= lon_thirds[2]:
        x_label = "East"
    else:
        x_label = "Central"
    if lat <= lat_thirds[1]:
        y_label = "South"
    elif lat >= lat_thirds[2]:
        y_label = "North"
    else:
        y_label = "Mid"
    if x_label == "Central" and y_label == "Mid":
        return "Interior"
    if y_label == "Mid":
        return x_label
    if x_label == "Central":
        return f"{y_label}-Central"
    return f"{y_label}-{x_label}"


def build_explanation(summary: pd.Series) -> tuple[str, str]:
    annual_temp = summary["annual_mean_temp_c"]
    annual_precip = summary["annual_total_precip_mm"]
    coldest = summary["coldest_month_temp_c"]
    hottest = summary["hottest_month_temp_c"]
    summer_total = summary["summer_total_precip_mm"]
    winter_total = summary["winter_total_precip_mm"]
    display_name = summary["display_climate_name"]

    thermal_text = f"Annual mean temperature is {annual_temp:.1f}°C, from {coldest:.1f}°C in the coldest month to {hottest:.1f}°C in the hottest month."
    if summer_total > winter_total * 1.2:
        precip_text = f"Precipitation is summer-leaning, with about {annual_precip:.0f} mm per year and a wetter warm season."
    elif winter_total > summer_total * 1.2:
        precip_text = f"Precipitation leans toward the cool season, totaling about {annual_precip:.0f} mm per year."
    else:
        precip_text = f"Precipitation is fairly balanced across the year at about {annual_precip:.0f} mm annually."

    lead = {
        "Hot desert": "Very dry conditions dominate this region.",
        "Semi-arid / steppe": "This region is dry overall but not as extreme as the desert core.",
        "Mediterranean": "Warm dry summers and wetter cool months define this region.",
        "Humid subtropical": "Warm conditions combine with abundant moisture through much of the year.",
        "Marine west coast": "This region stays mild with persistent maritime moisture.",
        "Humid continental": "Large seasonal temperature swings are paired with moderate to high precipitation.",
        "Subarctic": "Long cold seasons dominate, with only a short mild summer window.",
        "Tundra / polar-like": "Cold temperatures limit this region for most of the year.",
        "Other / mixed transition": "This region sits in a transition zone between the main display classes.",
    }[display_name]
    short = f"{lead} {precip_text}"
    long = f"{lead} {thermal_text} {precip_text}"
    return short, long


def region_geojson(
    region_cells: pd.DataFrame,
    region_summary: pd.DataFrame,
) -> dict[str, Any]:
    lon_step = GRID_RESOLUTION / 2
    lat_step = GRID_RESOLUTION / 2
    features = []
    for _, summary in region_summary.iterrows():
        region_id = summary["region_id"]
        cells = region_cells[region_cells["region_id"] == region_id]
        lons = cells["lon"].to_numpy()
        lats = cells["lat"].to_numpy()
        polygons = [
            box(lo - lon_step, la - lat_step, lo + lon_step, la + lat_step)
            for lo, la in zip(lons, lats)
        ]
        geometry = unary_union(polygons).simplify(0.0, preserve_topology=True)
        properties = {
            "region_id": region_id,
            "region_name": summary["region_name"],
            "display_climate_class": summary["display_climate_class"],
            "display_climate_name": summary["display_climate_name"],
            "n_grid": int(summary["n_grid"]),
            "area_proxy_ncells": int(summary["n_grid"]),
            "dominant_raw_code": summary["dominant_raw_code"],
            "explanation_short": summary["explanation_short"],
            "centroid_lon": float(summary["centroid_lon"]),
            "centroid_lat": float(summary["centroid_lat"]),
            "color": DISPLAY_CLASS_STYLES[summary["display_climate_name"]]["color"],
        }
        features.append({"type": "Feature", "geometry": mapping(geometry), "properties": properties})
    return {"type": "FeatureCollection", "features": features}


def build_regions(
    cube: CubeData,
    feature_df: pd.DataFrame,
    valid_mask: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame, dict[str, Any], np.ndarray, int, np.ndarray]:
    class_grid = np.full(valid_mask.shape, "", dtype=object)
    class_grid[feature_df["lat_idx"].to_numpy(), feature_df["lon_idx"].to_numpy()] = feature_df["display_climate_name"].to_numpy()

    premerge_component_map, _ = _component_table(class_grid)
    threshold, merged_grid, component_map, components, anchors, assignments = pick_best_display_regions(class_grid, cube)
    print(f"Using patch threshold {threshold}; final region count = {len(anchors)}")

    lat_grid, lon_grid = np.meshgrid(cube.lat, cube.lon, indexing="ij")
    anchor_lookup = anchors.set_index("component_id")
    component_records: list[pd.DataFrame] = []
    for _, row in components.iterrows():
        comp_id = int(row["component_id"])
        assigned_anchor = assignments[comp_id]
        anchor_row = anchor_lookup.loc[assigned_anchor]
        mask = component_map == comp_id
        cells = pd.DataFrame(
            {
                "region_anchor_id": assigned_anchor,
                "lat_idx": np.where(mask)[0].astype(np.int16),
                "lon_idx": np.where(mask)[1].astype(np.int16),
                "lat": lat_grid[mask].astype(np.float32),
                "lon": lon_grid[mask].astype(np.float32),
                "display_climate_name": np.repeat(anchor_row["display_climate_name"], mask.sum()),
            }
        )
        component_records.append(cells)
    region_cells = pd.concat(component_records, ignore_index=True)
    region_cells["region_id"] = region_cells["region_anchor_id"].map(lambda value: f"A{int(value):02d}")

    region_features = feature_df.merge(region_cells[["region_id", "lat_idx", "lon_idx"]], on=["lat_idx", "lon_idx"], how="left")
    numeric_cols = [
        "annual_mean_temp_c",
        "annual_total_precip_mm",
        "coldest_month_temp_c",
        "hottest_month_temp_c",
        "temp_annual_range_c",
        "driest_month_precip_mm",
        "wettest_month_precip_mm",
        "summer_total_precip_mm",
        "winter_total_precip_mm",
        "precip_seasonality_ratio",
    ]
    region_summary = region_features.groupby("region_id")[numeric_cols].mean().reset_index()
    meta = (
        region_cells.groupby("region_id")
        .agg(
            display_climate_name=("display_climate_name", "first"),
            n_grid=("region_id", "size"),
            centroid_lat=("lat", "mean"),
            centroid_lon=("lon", "mean"),
        )
        .reset_index()
    )
    raw_mode = (
        region_features.groupby("region_id")["kg_raw_code"]
        .agg(lambda values: values.mode().iat[0] if not values.mode().empty else values.iloc[0])
        .reset_index(name="dominant_raw_code")
    )
    region_summary = region_summary.merge(meta, on="region_id").merge(raw_mode, on="region_id")
    region_summary["display_climate_class"] = region_summary["display_climate_name"].map(
        lambda name: DISPLAY_CLASS_STYLES[name]["slug"]
    )

    lon_bounds = (float(cube.lon.min()), float(cube.lon.max()))
    lat_bounds = (float(cube.lat.min()), float(cube.lat.max()))
    region_summary = region_summary.sort_values(["display_climate_name", "centroid_lon", "centroid_lat"]).reset_index(drop=True)
    region_summary["old_region_id"] = region_summary["region_id"]
    region_summary["region_id"] = [f"R{i:02d}" for i in range(1, len(region_summary) + 1)]
    region_summary["region_name"] = [
        f"Region {i:02d} - {name} {classify_orientation(lon, lat, lon_bounds, lat_bounds)}"
        for i, (name, lon, lat) in enumerate(
            zip(
                region_summary["display_climate_name"],
                region_summary["centroid_lon"],
                region_summary["centroid_lat"],
            ),
            start=1,
        )
    ]
    old_to_new = dict(zip(region_summary["old_region_id"], region_summary["region_id"]))
    region_cells["region_id"] = region_cells["region_id"].map(old_to_new)
    explanations = region_summary.apply(build_explanation, axis=1, result_type="expand")
    region_summary["explanation_short"] = explanations[0]
    region_summary["explanation_long"] = explanations[1]
    region_summary = region_summary.drop(columns=["old_region_id"])

    geojson = region_geojson(region_cells, region_summary)

    final_region_map = np.zeros(valid_mask.shape, dtype=np.int32)
    numeric_ids = region_cells["region_id"].str[1:].astype(np.int32).to_numpy()
    final_region_map[region_cells["lat_idx"].to_numpy(), region_cells["lon_idx"].to_numpy()] = numeric_ids

    region_cells = region_cells.drop(columns=["region_anchor_id"])
    return region_cells, region_summary, geojson, final_region_map, threshold, premerge_component_map


def build_region_timeseries(
    cube: CubeData,
    region_summary: pd.DataFrame,
    final_region_map: np.ndarray,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    classified_mask = final_region_map > 0
    region_flat = final_region_map[classified_mask]

    temp_c = cube.temp_c[:, classified_mask]
    rain_mm = cube.rain_mm[:, classified_mask]

    monthly_rows: list[dict[str, Any]] = []
    yearly_rows: list[dict[str, Any]] = []
    years = np.unique(cube.years)
    for _, meta in region_summary.iterrows():
        region_id = meta["region_id"]
        numeric_id = int(region_id[1:])
        cell_mask = region_flat == numeric_id
        region_temp_monthly = np.nanmean(temp_c[:, cell_mask], axis=1)
        region_rain_monthly = np.nanmean(rain_mm[:, cell_mask], axis=1)
        for timestamp, month, year, temp_value, rain_value in zip(
            cube.times,
            cube.months,
            cube.years,
            region_temp_monthly,
            region_rain_monthly,
        ):
            if year == 2025:
                monthly_rows.append(
                    {
                        "region_id": region_id,
                        "region_name": str(meta["region_name"]),
                        "display_climate_name": str(meta["display_climate_name"]),
                        "year": 2025,
                        "month": int(month),
                        "mean_Tair_C": float(temp_value),
                        "mean_Rainf_mm": float(rain_value),
                    }
                )
        for year in years:
            mask = cube.years == year
            yearly_rows.append(
                {
                    "region_id": region_id,
                    "region_name": str(meta["region_name"]),
                    "display_climate_name": str(meta["display_climate_name"]),
                    "year": int(year),
                    "annual_mean_temp_c": float(np.nanmean(region_temp_monthly[mask])),
                    "annual_total_precip_mm": float(np.nansum(region_rain_monthly[mask])),
                }
            )
    region_monthly_2025 = pd.DataFrame(monthly_rows)
    region_yearly = pd.DataFrame(yearly_rows)
    return region_monthly_2025, region_yearly


def write_app_config(paths: ProjectPaths, region_summary: pd.DataFrame, patch_threshold: int) -> None:
    default_region = region_summary.sort_values("n_grid", ascending=False).iloc[0]["region_id"]
    payload = {
        "default_selected_region": default_region,
        "patch_threshold": patch_threshold,
        "legend_labels": DISPLAY_CLASS_ORDER,
        "color_mapping": {name: style["color"] for name, style in DISPLAY_CLASS_STYLES.items()},
        "chart_titles": {
            "monthly_2025": "2025 Monthly Temperature and Precipitation",
            "annual_1996_2025": "1996-2025 Annual Temperature and Precipitation",
        },
    }
    paths.app_config.write_text(json.dumps(payload, indent=2))


def save_report_figures(
    paths: ProjectPaths,
    cube: CubeData,
    feature_df: pd.DataFrame,
    region_summary: pd.DataFrame,
    region_monthly_2025: pd.DataFrame,
    region_yearly: pd.DataFrame,
    final_region_map: np.ndarray,
) -> None:
    paths.figure_dir.mkdir(parents=True, exist_ok=True)
    default_region = region_summary.sort_values("n_grid", ascending=False).iloc[0]["region_id"]
    region_info = region_summary.set_index("region_id").loc[default_region]
    monthly = region_monthly_2025[region_monthly_2025["region_id"] == default_region].sort_values("month")
    yearly = region_yearly[region_yearly["region_id"] == default_region].sort_values("year")

    class_to_index = {name: idx for idx, name in enumerate(DISPLAY_CLASS_ORDER)}
    numeric_grid = np.full(final_region_map.shape, np.nan)
    class_indices = feature_df["display_climate_name"].map(class_to_index).to_numpy(dtype=np.float64)
    numeric_grid[feature_df["lat_idx"].to_numpy(), feature_df["lon_idx"].to_numpy()] = class_indices

    cmap = ListedColormap([DISPLAY_CLASS_STYLES[name]["color"] for name in DISPLAY_CLASS_ORDER])
    legend_handles = [Patch(facecolor=DISPLAY_CLASS_STYLES[name]["color"], label=name) for name in DISPLAY_CLASS_ORDER]

    fig_map, ax_map = plt.subplots(figsize=(12, 6.2))
    ax_map.imshow(
        numeric_grid,
        origin="lower",
        cmap=cmap,
        interpolation="nearest",
        extent=[cube.lon.min(), cube.lon.max(), cube.lat.min(), cube.lat.max()],
        aspect="auto",
    )
    ax_map.set_title("North America Climate Regions (1996-2025)")
    ax_map.set_xlabel("Longitude")
    ax_map.set_ylabel("Latitude")
    ax_map.legend(handles=legend_handles, loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
    fig_map.tight_layout()
    fig_map.savefig(paths.figure_dir / "final_climate_region_map.png", dpi=180, bbox_inches="tight")
    plt.close(fig_map)

    fig_month, ax_temp = plt.subplots(figsize=(10, 4.8))
    ax_precip = ax_temp.twinx()
    month_labels = ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    ax_precip.bar(month_labels, monthly["mean_Rainf_mm"], color="#60a5fa", alpha=0.55, label="Precipitation (mm)")
    ax_temp.plot(month_labels, monthly["mean_Tair_C"], color="#dc2626", marker="o", linewidth=2.2, label="Temperature (°C)")
    ax_temp.set_ylabel("Temperature (°C)")
    ax_precip.set_ylabel("Precipitation (mm)")
    ax_temp.set_title(f"{region_info['region_name']}: 2025 Monthly Climate")
    temp_handle = Line2D([0], [0], color="#dc2626", marker="o", linewidth=2.2, label="Temperature (°C)")
    precip_handle = Patch(facecolor="#60a5fa", alpha=0.55, label="Precipitation (mm)")
    ax_temp.legend(handles=[temp_handle, precip_handle], loc="upper left", frameon=False)
    fig_month.tight_layout()
    fig_month.savefig(paths.figure_dir / "example_2025_monthly_chart.png", dpi=180, bbox_inches="tight")
    plt.close(fig_month)

    fig_year, ax_temp_year = plt.subplots(figsize=(10, 4.8))
    ax_precip_year = ax_temp_year.twinx()
    ax_precip_year.bar(yearly["year"], yearly["annual_total_precip_mm"], color="#93c5fd", alpha=0.45, label="Annual precipitation (mm)")
    ax_temp_year.plot(yearly["year"], yearly["annual_mean_temp_c"], color="#1d4ed8", linewidth=2.1, label="Annual mean temperature (°C)")
    ax_temp_year.set_ylabel("Temperature (°C)")
    ax_precip_year.set_ylabel("Precipitation (mm)")
    ax_temp_year.set_title(f"{region_info['region_name']}: 1996-2025 Annual Variability")
    temp_year_handle = Line2D([0], [0], color="#1d4ed8", linewidth=2.1, label="Annual mean temperature (°C)")
    precip_year_handle = Patch(facecolor="#93c5fd", alpha=0.45, label="Annual precipitation (mm)")
    ax_temp_year.legend(handles=[temp_year_handle, precip_year_handle], loc="upper left", frameon=False)
    fig_year.tight_layout()
    fig_year.savefig(paths.figure_dir / "example_30yr_annual_chart.png", dpi=180, bbox_inches="tight")
    plt.close(fig_year)

    fig_ui = plt.figure(figsize=(15, 8))
    gs = fig_ui.add_gridspec(2, 2, width_ratios=[1.2, 1.0], height_ratios=[1.0, 1.0], wspace=0.25, hspace=0.3)
    ax_ui_map = fig_ui.add_subplot(gs[:, 0])
    ax_ui_map.imshow(
        numeric_grid,
        origin="lower",
        cmap=cmap,
        interpolation="nearest",
        extent=[cube.lon.min(), cube.lon.max(), cube.lat.min(), cube.lat.max()],
        aspect="auto",
    )
    ax_ui_map.scatter(region_info["centroid_lon"], region_info["centroid_lat"], color="black", s=32, zorder=3)
    ax_ui_map.set_title("Interactive Climate Region Map")
    ax_ui_map.set_xlabel("Longitude")
    ax_ui_map.set_ylabel("Latitude")

    ax_ui_text = fig_ui.add_subplot(gs[0, 1])
    ax_ui_text.axis("off")
    ax_ui_text.text(0.0, 1.0, region_info["region_name"], fontsize=16, fontweight="bold", va="top")
    ax_ui_text.text(0.0, 0.82, region_info["display_climate_name"], fontsize=13, color=DISPLAY_CLASS_STYLES[region_info["display_climate_name"]]["color"])
    ax_ui_text.text(0.0, 0.7, region_info["explanation_short"], fontsize=11, wrap=True)
    ax_ui_text.text(
        0.0,
        0.36,
        "\n".join(
            [
                f"Annual mean temp: {region_info['annual_mean_temp_c']:.1f}°C",
                f"Annual total precip: {region_info['annual_total_precip_mm']:.0f} mm",
                f"Thermal range: {region_info['coldest_month_temp_c']:.1f}°C to {region_info['hottest_month_temp_c']:.1f}°C",
                f"Patch size: {int(region_info['n_grid'])} grid cells",
            ]
        ),
        fontsize=10.5,
        va="top",
    )

    ax_ui_chart = fig_ui.add_subplot(gs[1, 1])
    ax_ui_precip = ax_ui_chart.twinx()
    ax_ui_precip.bar(month_labels, monthly["mean_Rainf_mm"], color="#60a5fa", alpha=0.55)
    ax_ui_chart.plot(month_labels, monthly["mean_Tair_C"], color="#dc2626", marker="o", linewidth=2.0)
    ax_ui_chart.set_title("Selected Region: 2025 Monthly Climate")
    ax_ui_chart.set_ylabel("Temperature (°C)")
    ax_ui_precip.set_ylabel("Precipitation (mm)")

    fig_ui.savefig(paths.figure_dir / "final_ui_screenshot.png", dpi=180, bbox_inches="tight")
    plt.close(fig_ui)


def build_grid_climate_map(
    feature_df: pd.DataFrame,
    region_cells: pd.DataFrame,
    premerge_component_map: np.ndarray,
    cube: CubeData,
) -> pd.DataFrame:
    frame = feature_df[["kg_raw_code", "lat_idx", "lon_idx"]].merge(
        region_cells[["lat_idx", "lon_idx", "display_climate_name"]],
        on=["lat_idx", "lon_idx"],
        how="left",
    )
    frame["display_climate_class"] = frame["display_climate_name"].map(lambda name: DISPLAY_CLASS_STYLES[name]["slug"])
    frame["lat"] = cube.lat[frame["lat_idx"].to_numpy()].astype(np.float32)
    frame["lon"] = cube.lon[frame["lon_idx"].to_numpy()].astype(np.float32)
    frame["component_id_premerge"] = premerge_component_map[frame["lat_idx"].to_numpy(), frame["lon_idx"].to_numpy()]
    return frame[["lat", "lon", "display_climate_class", "display_climate_name", "kg_raw_code", "component_id_premerge"]]


def run_pipeline(paths: ProjectPaths = DEFAULT_PATHS, start_ym: int = START_YM, end_ym: int = END_YM) -> dict[str, Any]:
    paths.output_dir.mkdir(parents=True, exist_ok=True)
    paths.figure_dir.mkdir(parents=True, exist_ok=True)
    files = list_source_files(paths.raw_dir, start_ym=start_ym, end_ym=end_ym)
    cube = load_cube(files)
    write_grid_monthly_parquet(cube, paths.grid_monthly)

    climatology_df, monthly_temp, monthly_rain, valid_mask = build_climatology(cube)
    climatology_df.to_parquet(paths.climatology, index=False)
    print(f"Wrote {paths.climatology}")

    feature_df = classify_climate(monthly_temp, monthly_rain, valid_mask)
    feature_df["lat"] = cube.lat[feature_df["lat_idx"].to_numpy()].astype(np.float32)
    feature_df["lon"] = cube.lon[feature_df["lon_idx"].to_numpy()].astype(np.float32)
    feature_output = feature_df[
        [
            "lat",
            "lon",
            "annual_mean_temp_c",
            "coldest_month_temp_c",
            "hottest_month_temp_c",
            "temp_annual_range_c",
            "annual_total_precip_mm",
            "driest_month_precip_mm",
            "wettest_month_precip_mm",
            "summer_mean_precip_mm",
            "winter_mean_precip_mm",
            "summer_total_precip_mm",
            "winter_total_precip_mm",
            "precip_seasonality_ratio",
            "kg_raw_code",
            "display_climate_class",
            "display_climate_name",
        ]
    ]
    feature_output.to_parquet(paths.climate_features, index=False)
    print(f"Wrote {paths.climate_features}")

    region_cells, region_summary, geojson, final_region_map, patch_threshold, premerge_component_map = build_regions(
        cube,
        feature_df,
        valid_mask,
    )
    with paths.climate_regions.open("w", encoding="utf-8") as fh:
        json.dump(geojson, fh)
    print(f"Wrote {paths.climate_regions}")

    region_summary.to_parquet(paths.region_summary, index=False)
    print(f"Wrote {paths.region_summary}")

    region_monthly_2025, region_yearly = build_region_timeseries(cube, region_summary, final_region_map)
    region_monthly_2025.to_parquet(paths.region_monthly_2025, index=False)
    region_yearly.to_parquet(paths.region_yearly, index=False)
    print(f"Wrote {paths.region_monthly_2025}")
    print(f"Wrote {paths.region_yearly}")

    climate_map_df = build_grid_climate_map(feature_df, region_cells, premerge_component_map, cube)
    climate_map_df.to_parquet(paths.climate_map, index=False)
    print(f"Wrote {paths.climate_map}")

    write_app_config(paths, region_summary, patch_threshold)
    save_report_figures(paths, cube, feature_df, region_summary, region_monthly_2025, region_yearly, final_region_map)

    summary = {
        "source_file_count": len(files),
        "grid_monthly_rows": pq.ParquetFile(paths.grid_monthly).metadata.num_rows,
        "classified_grid_cells": int(len(feature_df)),
        "region_count": int(len(region_summary)),
        "patch_threshold": patch_threshold,
        "display_classes": region_summary["display_climate_name"].value_counts().sort_index().to_dict(),
    }
    print(json.dumps(summary, indent=2))
    return summary
