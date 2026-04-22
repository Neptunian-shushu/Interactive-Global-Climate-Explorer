from __future__ import annotations

import argparse
from pathlib import Path

from climate_explorer.config import ProjectPaths
from climate_explorer.pipeline import run_pipeline


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Run the NLDAS climate classification pipeline.",
    )
    parser.add_argument(
        "--raw-dir",
        type=Path,
        default=Path.cwd() / "earth",
        help="Directory containing raw NLDAS nc4 files (default: ./earth)",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=Path.cwd() / "outputs",
        help="Output directory for parquet/geojson files (default: ./outputs)",
    )
    parser.add_argument(
        "--figure-dir",
        type=Path,
        default=Path.cwd() / "figures",
        help="Output directory for report figures (default: ./figures)",
    )
    parser.add_argument(
        "--start",
        type=int,
        default=199601,
        metavar="YYYYMM",
        help="Start year-month as YYYYMM (default: 199601)",
    )
    parser.add_argument(
        "--end",
        type=int,
        default=202512,
        metavar="YYYYMM",
        help="End year-month as YYYYMM (default: 202512)",
    )
    args = parser.parse_args()

    paths = ProjectPaths(
        root=Path.cwd(),
        raw_dir=args.raw_dir,
        output_dir=args.output_dir,
        figure_dir=args.figure_dir,
    )
    run_pipeline(paths, start_ym=args.start, end_ym=args.end)


if __name__ == "__main__":
    main()
