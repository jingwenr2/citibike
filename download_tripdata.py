from __future__ import annotations

import argparse
from pathlib import Path

from src.ingest_tripdata import (
    DEFAULT_BAYWHEELS_INDEX,
    DEFAULT_CITIBIKE_INDEX,
    download_tripdata,
)


def parse_year_month(value: str) -> tuple[int, int]:
    year_str, month_str = value.split("-")
    return int(year_str), int(month_str)


def main() -> None:
    parser = argparse.ArgumentParser(description="Download Citi Bike or Bay Wheels tripdata archives")
    parser.add_argument("--provider", choices=["citibike", "baywheels"], default="citibike")
    parser.add_argument(
        "--months", type=int, default=6,
        help="Download the N most recent months (ignored if --start/--end are given)",
    )
    parser.add_argument("--start", type=str, help="Start month, format YYYY-MM (inclusive)")
    parser.add_argument("--end", type=str, help="End month, format YYYY-MM (inclusive)")
    parser.add_argument("--output-dir", type=Path, default=None)
    args = parser.parse_args()

    index_url = DEFAULT_CITIBIKE_INDEX if args.provider == "citibike" else DEFAULT_BAYWHEELS_INDEX
    output_dir = args.output_dir or Path("data/raw") / args.provider
    start = parse_year_month(args.start) if args.start else None
    end = parse_year_month(args.end) if args.end else None

    files = download_tripdata(
        index_url=index_url,
        output_dir=output_dir,
        months=args.months,
        start=start,
        end=end,
    )

    print(f"Downloaded {len(files)} file(s) to {output_dir}")
    for path in files:
        print(path)


if __name__ == "__main__":
    main()
