"""Download NYC Citi Bike trip data and aggregate hour-of-day x day-of-week demand.

The main daily ingestion (ingest_bike_data.py) drops timestamps down to a date,
so it can't answer "which hours are peak". This script re-downloads raw NYC
trip CSVs, keeps only the columns needed to bucket each trip by hour and
weekday, and aggregates immediately so the output stays small even across a
year of trips.

Produces:  data/processed/bike_share_hourly.parquet
           (date, hour, day_name, city, system, rider_type, trips, electric_trips)

Usage:
    python backend/scripts/ingest_hourly_demand.py
    python backend/scripts/ingest_hourly_demand.py --months 6
    python backend/scripts/ingest_hourly_demand.py --skip-download  # reprocess cached zips
"""

from __future__ import annotations

import argparse
import gc
import zipfile
from pathlib import Path

import pandas as pd

from ingest_bike_data import RAW_CITIBIKE, download_citibike, month_range

ROOT = Path(__file__).resolve().parents[2]
OUTPUT_PATH = ROOT / "data" / "processed" / "bike_share_hourly.parquet"

USECOLS = {"started_at", "member_casual", "rideable_type"}
GROUP_COLS = ["date", "hour", "day_name", "rider_type"]


def read_month_zip(zip_path: Path) -> pd.DataFrame:
    """Read only the columns needed for hour/weekday bucketing from a monthly zip."""
    frames = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            names = [n for n in zf.namelist() if n.endswith(".csv") and not n.startswith("__MACOSX")]
            for name in names:
                with zf.open(name) as f:
                    frames.append(pd.read_csv(f, usecols=lambda c: c in USECOLS, low_memory=False))
    except (zipfile.BadZipFile, EOFError) as exc:
        print(f"  SKIP corrupt/incomplete zip: {zip_path.name} ({exc})")
        return pd.DataFrame()
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def aggregate_hourly(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty or "started_at" not in df.columns:
        return pd.DataFrame()

    df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")
    df = df.dropna(subset=["started_at"])

    if "rideable_type" not in df.columns:
        df["rideable_type"] = "classic_bike"
    is_electric = df["rideable_type"].str.contains("electric", case=False, na=False).astype(int)

    if "member_casual" not in df.columns:
        df["member_casual"] = "unknown"
    member_casual = df["member_casual"].str.lower().replace({"subscriber": "member", "customer": "casual"})
    rider_type = member_casual.map(lambda x: "Member" if "member" in str(x).lower() else "Casual")

    bucketed = pd.DataFrame(
        {
            "date": df["started_at"].dt.date,
            "hour": df["started_at"].dt.hour,
            "day_name": df["started_at"].dt.day_name(),
            "rider_type": rider_type,
            "is_electric": is_electric,
        }
    )

    return bucketed.groupby(GROUP_COLS, as_index=False).agg(
        trips=("is_electric", "count"),
        electric_trips=("is_electric", "sum"),
    )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Aggregate hour-of-day NYC Citi Bike demand")
    parser.add_argument("--months", type=int, default=12, help="Number of months to download (default: 12)")
    parser.add_argument("--start", type=str, default=None, help="Start month as YYYYMM (inclusive)")
    parser.add_argument("--end", type=str, default=None, help="End month as YYYYMM (inclusive)")
    parser.add_argument("--skip-download", action="store_true", help="Reprocess already-downloaded zips")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.start and args.end:
        months = pd.period_range(args.start, args.end, freq="M").strftime("%Y%m").tolist()
    else:
        months = month_range(args.months)
    print(f"Target months: {months[0]} through {months[-1]} ({len(months)} months)")

    if not args.skip_download:
        print("\n=== Downloading Citi Bike data ===")
        download_citibike(months)

    zips = sorted(RAW_CITIBIKE.glob("*.zip"))
    print(f"\nFound {len(zips)} cached zip files")

    frames = []
    for i, zp in enumerate(zips):
        print(f"[{i + 1}/{len(zips)}] {zp.name}")
        raw = read_month_zip(zp)
        agg = aggregate_hourly(raw)
        if not agg.empty:
            frames.append(agg)
            print(f"  -> {len(agg):,} hour/day buckets")
        del raw, agg
        gc.collect()

    if not frames:
        raise SystemExit("No trip data processed")

    combined = pd.concat(frames, ignore_index=True)
    combined = combined.groupby(GROUP_COLS, as_index=False).agg(
        trips=("trips", "sum"),
        electric_trips=("electric_trips", "sum"),
    )
    combined["city"] = "New York City"
    combined["system"] = "Citi Bike"

    print(f"\nDate range: {combined['date'].min()} to {combined['date'].max()}")
    print(f"Total rows: {len(combined):,}")
    print(f"Total trips: {combined['trips'].sum():,}")

    args.output.parent.mkdir(parents=True, exist_ok=True)
    combined.to_parquet(args.output, index=False)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
