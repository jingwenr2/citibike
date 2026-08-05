"""Download and normalize Citi Bike + Bay Wheels trip data (past 2 years).

Produces:  data/processed/bike_share_daily.parquet

Usage:
    python backend/scripts/ingest_bike_data.py
    python backend/scripts/ingest_bike_data.py --months 12   # only last 12 months
    python backend/scripts/ingest_bike_data.py --skip-download  # reprocess already-downloaded files
"""

from __future__ import annotations

import argparse
import io
import os
import zipfile
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_CITIBIKE = ROOT / "data" / "raw" / "citibike"
RAW_BAYWHEELS = ROOT / "data" / "raw" / "baywheels"
OUTPUT_PATH = ROOT / "data" / "processed" / "bike_share_daily.parquet"

CITIBIKE_BASE = "https://s3.amazonaws.com/tripdata"
BAYWHEELS_BASE = "https://s3.amazonaws.com/baywheels-data"

# GBFS endpoint for current station capacity
CITIBIKE_STATION_INFO = (
    "https://gbfs.citibikenyc.com/gbfs/en/station_information.json"
)
BAYWHEELS_STATION_INFO = (
    "https://gbfs.baywheelsbike.com/gbfs/en/station_information.json"
)


def month_range(n_months: int) -> list[str]:
    """Return YYYYMM strings for the last n_months before current month."""
    today = pd.Timestamp.now()
    # Start from previous month (current month data likely incomplete)
    end = today.replace(day=1) - pd.Timedelta(days=1)
    months = []
    for i in range(n_months):
        dt = end - pd.DateOffset(months=i)
        months.append(dt.strftime("%Y%m"))
    return sorted(months)


def download_file(url: str, dest: Path) -> bool:
    """Download a file if it doesn't already exist. Returns True on success."""
    if dest.exists() and dest.stat().st_size > 1000:
        print(f"  cached: {dest.name}")
        return True
    print(f"  downloading: {url}")
    try:
        req = Request(url, headers={"User-Agent": "citibike-capstone/1.0"})
        with urlopen(req, timeout=180) as resp:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(resp.read())
        return True
    except Exception as exc:
        print(f"  SKIP ({exc})")
        return False


def download_citibike(months: list[str]) -> None:
    """Download Citi Bike monthly zips (NYC only, skip JC)."""
    for ym in months:
        filename = f"{ym}-citibike-tripdata.zip"
        url = f"{CITIBIKE_BASE}/{filename}"
        download_file(url, RAW_CITIBIKE / filename)


def download_baywheels(months: list[str]) -> None:
    """Download Bay Wheels monthly zips."""
    for ym in months:
        # Bay Wheels uses .csv.zip for most months
        for suffix in [".csv.zip", ".zip"]:
            filename = f"{ym}-baywheels-tripdata{suffix}"
            url = f"{BAYWHEELS_BASE}/{filename}"
            if download_file(url, RAW_BAYWHEELS / filename):
                break


def read_csvs_from_zip(zip_path: Path) -> pd.DataFrame:
    """Read all CSVs inside a zip file and concatenate them."""
    frames = []
    try:
        with zipfile.ZipFile(zip_path) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv") and not n.startswith("__MACOSX")]
            for name in csv_names:
                with zf.open(name) as f:
                    df = pd.read_csv(f, low_memory=False)
                    frames.append(df)
    except (zipfile.BadZipFile, EOFError) as exc:
        print(f"    SKIP corrupt/incomplete zip: {zip_path.name} ({exc})")
        return pd.DataFrame()
    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def normalize_trips(df: pd.DataFrame, city: str, system: str) -> pd.DataFrame:
    """Normalize raw trip data into a consistent schema."""
    if df.empty:
        return pd.DataFrame()

    # Standardize column names (handle variations)
    col_map = {}
    for col in df.columns:
        lower = col.lower().replace(" ", "_")
        if "started_at" in lower or "starttime" in lower or "start_time" in lower:
            col_map[col] = "started_at"
        elif "ended_at" in lower or "stoptime" in lower or "end_time" in lower:
            col_map[col] = "ended_at"
        elif "start_station_name" in lower or "start station name" in lower.replace("_", " "):
            col_map[col] = "start_station_name"
        elif "end_station_name" in lower or "end station name" in lower.replace("_", " "):
            col_map[col] = "end_station_name"
        elif "start_lat" in lower or "start station latitude" in lower.replace("_", " "):
            col_map[col] = "start_lat"
        elif "start_lng" in lower or "start_lon" in lower or "start station longitude" in lower.replace("_", " "):
            col_map[col] = "start_lng"
        elif "rideable_type" in lower:
            col_map[col] = "rideable_type"
        elif "member_casual" in lower or "usertype" in lower or "user_type" in lower:
            col_map[col] = "member_casual"

    df = df.rename(columns=col_map)

    # Parse start time
    if "started_at" not in df.columns:
        print(f"    WARNING: no started_at column found, skipping. Columns: {list(df.columns)}")
        return pd.DataFrame()

    df["started_at"] = pd.to_datetime(df["started_at"], errors="coerce")
    df = df.dropna(subset=["started_at"])
    df["date"] = df["started_at"].dt.date

    # Station name
    if "start_station_name" not in df.columns:
        df["start_station_name"] = "Unknown"
    df["start_station_name"] = df["start_station_name"].fillna("Unknown")

    # Coordinates
    for col in ["start_lat", "start_lng"]:
        if col not in df.columns:
            df[col] = np.nan
        df[col] = pd.to_numeric(df[col], errors="coerce")

    # Rideable type — classify electric
    if "rideable_type" not in df.columns:
        df["rideable_type"] = "classic_bike"
    df["is_electric"] = df["rideable_type"].str.contains("electric", case=False, na=False).astype(int)

    # Rider type
    if "member_casual" not in df.columns:
        df["member_casual"] = "unknown"
    # Normalize subscriber/customer to member/casual
    df["member_casual"] = (
        df["member_casual"]
        .str.lower()
        .replace({"subscriber": "member", "customer": "casual"})
    )
    df["rider_type"] = df["member_casual"].map(
        lambda x: "Member" if "member" in str(x).lower() else "Casual"
    )

    df["city"] = city
    df["system"] = system

    return df[["date", "city", "system", "start_station_name", "start_lat",
               "start_lng", "rider_type", "is_electric"]]


def load_all_trips(raw_dir: Path, city: str, system: str) -> pd.DataFrame:
    """Load and normalize all zips in a raw directory."""
    zips = sorted(raw_dir.glob("*.zip"))
    if not zips:
        print(f"  No zip files found in {raw_dir}")
        return pd.DataFrame()

    frames = []
    for zp in zips:
        print(f"  processing: {zp.name}")
        raw = read_csvs_from_zip(zp)
        if raw.empty:
            continue
        norm = normalize_trips(raw, city, system)
        if not norm.empty:
            frames.append(norm)
            print(f"    {len(norm):,} trips")

    if not frames:
        return pd.DataFrame()
    return pd.concat(frames, ignore_index=True)


def fetch_station_capacity(url: str) -> dict[str, int]:
    """Fetch current station capacities from GBFS feed."""
    try:
        req = Request(url, headers={"User-Agent": "citibike-capstone/1.0"})
        import json
        with urlopen(req, timeout=60) as resp:
            data = json.load(resp)
        stations = data.get("data", {}).get("stations", [])
        return {s["name"]: s.get("capacity", 0) for s in stations if "name" in s}
    except Exception as exc:
        print(f"  Could not fetch station capacity: {exc}")
        return {}


def aggregate_daily(trips: pd.DataFrame) -> pd.DataFrame:
    """Aggregate individual trips into station-day-rider_type summaries."""
    if trips.empty:
        return pd.DataFrame()

    trips["date"] = pd.to_datetime(trips["date"])

    daily = (
        trips.groupby(
            ["date", "city", "system", "start_station_name", "rider_type"],
            as_index=False,
        )
        .agg(
            trips=("is_electric", "count"),
            electric_trips=("is_electric", "sum"),
            lat=("start_lat", "median"),
            lon=("start_lng", "median"),
        )
    )
    daily = daily.rename(columns={"start_station_name": "station_name"})

    # Drop rows with unknown stations or missing coordinates
    daily = daily[daily["station_name"] != "Unknown"].copy()
    daily = daily.dropna(subset=["lat", "lon"])

    return daily


def attach_capacity(daily: pd.DataFrame) -> pd.DataFrame:
    """Attach current dock capacity from GBFS feeds."""
    print("Fetching station capacities from GBFS...")
    nyc_cap = fetch_station_capacity(CITIBIKE_STATION_INFO)
    bw_cap = fetch_station_capacity(BAYWHEELS_STATION_INFO)

    all_cap = {}
    all_cap.update(bw_cap)
    all_cap.update(nyc_cap)

    daily["capacity"] = daily["station_name"].map(all_cap).fillna(0).astype(int)
    # For stations not found in GBFS, estimate from median
    median_cap = daily.loc[daily["capacity"] > 0, "capacity"].median()
    if pd.notna(median_cap) and median_cap > 0:
        daily.loc[daily["capacity"] == 0, "capacity"] = int(median_cap)

    return daily


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Ingest Citi Bike + Bay Wheels data")
    parser.add_argument(
        "--months", type=int, default=24,
        help="Number of months to download (default: 24)",
    )
    parser.add_argument(
        "--skip-download", action="store_true",
        help="Skip download, reprocess already-downloaded files",
    )
    parser.add_argument(
        "--output", type=Path, default=OUTPUT_PATH,
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    months = month_range(args.months)
    print(f"Target months: {months[0]} through {months[-1]} ({len(months)} months)")

    if not args.skip_download:
        print("\n=== Downloading Citi Bike data ===")
        download_citibike(months)
        print("\n=== Downloading Bay Wheels data ===")
        download_baywheels(months)

    print("\n=== Loading Citi Bike trips ===")
    citibike_trips = load_all_trips(RAW_CITIBIKE, "New York City", "Citi Bike")

    print("\n=== Loading Bay Wheels trips ===")
    baywheels_trips = load_all_trips(RAW_BAYWHEELS, "San Francisco", "Bay Wheels")

    all_trips = pd.concat([citibike_trips, baywheels_trips], ignore_index=True)
    print(f"\nTotal raw trips: {len(all_trips):,}")

    print("\n=== Aggregating to station-day level ===")
    daily = aggregate_daily(all_trips)
    daily = attach_capacity(daily)

    # Final validation
    print(f"\nDaily rows: {len(daily):,}")
    print(f"Date range: {daily['date'].min().date()} to {daily['date'].max().date()}")
    for city in daily["city"].unique():
        city_data = daily[daily["city"] == city]
        print(
            f"  {city}: {city_data['trips'].sum():,.0f} trips, "
            f"{city_data['station_name'].nunique():,} stations, "
            f"{city_data['date'].nunique()} days"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(args.output, index=False)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
