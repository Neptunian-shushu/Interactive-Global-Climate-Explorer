from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


DISPLAY_CLASS_ORDER = [
    "Hot desert",
    "Semi-arid / steppe",
    "Mediterranean",
    "Humid subtropical",
    "Marine west coast",
    "Humid continental",
    "Subarctic",
    "Tundra / polar-like",
    "Other / mixed transition",
]


DISPLAY_CLASS_STYLES = {
    "Hot desert": {"slug": "hot_desert", "color": "#d97706"},
    "Semi-arid / steppe": {"slug": "semi_arid_steppe", "color": "#b8892d"},
    "Mediterranean": {"slug": "mediterranean", "color": "#74813c"},
    "Humid subtropical": {"slug": "humid_subtropical", "color": "#2f855a"},
    "Marine west coast": {"slug": "marine_west_coast", "color": "#0f766e"},
    "Humid continental": {"slug": "humid_continental", "color": "#2563eb"},
    "Subarctic": {"slug": "subarctic", "color": "#4338ca"},
    "Tundra / polar-like": {"slug": "tundra_polar_like", "color": "#64748b"},
    "Other / mixed transition": {"slug": "other_mixed_transition", "color": "#6b7280"},
}


DISPLAY_CLASS_COMPATIBILITY = {
    "Hot desert": {"Semi-arid / steppe", "Mediterranean", "Other / mixed transition"},
    "Semi-arid / steppe": {
        "Hot desert",
        "Mediterranean",
        "Humid continental",
        "Humid subtropical",
        "Marine west coast",
        "Other / mixed transition",
    },
    "Mediterranean": {
        "Semi-arid / steppe",
        "Humid subtropical",
        "Marine west coast",
        "Humid continental",
        "Other / mixed transition",
    },
    "Humid subtropical": {
        "Mediterranean",
        "Humid continental",
        "Marine west coast",
        "Semi-arid / steppe",
        "Other / mixed transition",
    },
    "Marine west coast": {
        "Mediterranean",
        "Humid continental",
        "Humid subtropical",
        "Subarctic",
        "Other / mixed transition",
    },
    "Humid continental": {
        "Humid subtropical",
        "Marine west coast",
        "Subarctic",
        "Semi-arid / steppe",
        "Mediterranean",
        "Other / mixed transition",
    },
    "Subarctic": {
        "Humid continental",
        "Marine west coast",
        "Tundra / polar-like",
        "Other / mixed transition",
    },
    "Tundra / polar-like": {"Subarctic", "Other / mixed transition"},
    "Other / mixed transition": set(DISPLAY_CLASS_ORDER),
}


@dataclass(frozen=True)
class ProjectPaths:
    root: Path
    raw_dir: Path
    output_dir: Path
    figure_dir: Path

    @property
    def grid_monthly(self) -> Path:
        return self.output_dir / "grid_monthly.parquet"

    @property
    def climatology(self) -> Path:
        return self.output_dir / "grid_climatology_1996_2025.parquet"

    @property
    def climate_features(self) -> Path:
        return self.output_dir / "grid_climate_features.parquet"

    @property
    def climate_map(self) -> Path:
        return self.output_dir / "grid_climate_map.parquet"

    @property
    def climate_regions(self) -> Path:
        return self.output_dir / "climate_regions.geojson"

    @property
    def region_summary(self) -> Path:
        return self.output_dir / "region_summary.parquet"

    @property
    def region_monthly_2025(self) -> Path:
        return self.output_dir / "region_2025_monthly.parquet"

    @property
    def region_yearly(self) -> Path:
        return self.output_dir / "region_1996_2025_yearly.parquet"

    @property
    def app_config(self) -> Path:
        return self.output_dir / "app_config.json"


DEFAULT_PATHS = ProjectPaths(
    root=Path.cwd(),
    raw_dir=Path.cwd() / "earth",
    output_dir=Path.cwd() / "outputs",
    figure_dir=Path.cwd() / "figures",
)


START_YM = 199601
END_YM = 202512
TARGET_REGION_MIN = 8
TARGET_REGION_MAX = 15
DEFAULT_PATCH_THRESHOLD = 20
PATCH_THRESHOLD_CANDIDATES = [20, 24, 30, 36, 45, 60, 80, 120, 160, 220, 300, 450, 700, 1000, 1500, 2500]
DISPLAY_REGION_ANCHOR_MIN = 250
GRID_RESOLUTION = 0.125
WARM_SEASON_MONTHS = {4, 5, 6, 7, 8, 9}
COOL_SEASON_MONTHS = {10, 11, 12, 1, 2, 3}
