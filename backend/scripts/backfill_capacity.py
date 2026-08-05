"""Backfill real per-station dock capacity into bike_share_daily.parquet.

The ingestion pipeline's Bay Wheels GBFS URL was broken (wrong domain), so
every San Francisco station silently fell back to a flat placeholder
capacity. This patches the `capacity` column in place using live GBFS
station_information feeds, without re-downloading or re-aggregating trip
data.

Matching order per station:
  1. exact station name match against the live GBFS feed
  2. nearest GBFS station within 200m (for renamed/decommissioned stations)
  3. left as NaN if neither matches (reported, not silently guessed)

Also drops a small number of non-customer rows (internal depots, firmware
test stations, e-bike valet corrals) that show up in the raw trip data but
are not real dock stations, so they don't pollute the ridership dataset.

Usage:
    python backend/scripts/backfill_capacity.py
    python backend/scripts/backfill_capacity.py --output data/processed/bike_share_daily_patched.parquet
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "bike_share_daily.parquet"

CITIBIKE_STATION_INFO = "https://gbfs.citibikenyc.com/gbfs/en/station_information.json"
BAYWHEELS_STATION_INFO = "https://gbfs.baywheels.com/gbfs/en/station_information.json"

# Found by manual inspection of station_name values in the trip data that
# are internal operations infrastructure, not real customer-facing docks.
NON_CUSTOMER_STATIONS = {
    "San Francisco": {
        "Firmware Test Internal Howard ",
        "Firmware Test Charging Internal Howard ",
        "San Jose Depot",
        "Minnesota St Depot (Outgoing)",
        "SF Depot-2 (Minnesota St Incoming)",
        "Berry HQ",
        "Emeryville Depot",
        "Test",
    },
    "New York City": {
        "Shop Morgan",
        "Morgan HCT Charging",
    },
}

# Valet/corral capacity is reported as a placeholder (e.g. 999), not a real
# dock count — exclude those GBFS entries from the matching reference set.
MAX_PLAUSIBLE_GBFS_CAPACITY = 200
NEAREST_MATCH_MAX_KM = 0.2

CITY_GBFS = {
    "New York City": CITIBIKE_STATION_INFO,
    "San Francisco": BAYWHEELS_STATION_INFO,
}


def fetch_station_info(url: str) -> pd.DataFrame:
    req = Request(url, headers={"User-Agent": "citibike-capstone/1.0"})
    with urlopen(req, timeout=60) as resp:
        data = json.load(resp)
    stations = pd.DataFrame(data["data"]["stations"])[["name", "lat", "lon", "capacity"]]
    return stations[stations["capacity"] <= MAX_PLAUSIBLE_GBFS_CAPACITY]


def nearest_capacity(missing: pd.DataFrame, gbfs: pd.DataFrame) -> dict[str, float]:
    """Match each unmatched station to the nearest GBFS station within NEAREST_MATCH_MAX_KM."""
    if missing.empty or gbfs.empty:
        return {}

    gbfs_lat = np.radians(gbfs["lat"].to_numpy())
    gbfs_lon = np.radians(gbfs["lon"].to_numpy())

    result: dict[str, float] = {}
    for station_name, lat, lon in missing.itertuples(index=False):
        if pd.isna(lat) or pd.isna(lon):
            continue
        lat1, lon1 = np.radians(lat), np.radians(lon)
        dlat = gbfs_lat - lat1
        dlon = gbfs_lon - lon1
        a = np.sin(dlat / 2) ** 2 + np.cos(lat1) * np.cos(gbfs_lat) * np.sin(dlon / 2) ** 2
        dist_km = 2 * 6371 * np.arcsin(np.sqrt(a))
        idx = int(np.argmin(dist_km))
        if dist_km[idx] <= NEAREST_MATCH_MAX_KM:
            result[station_name] = float(gbfs.iloc[idx]["capacity"])
    return result


def backfill_city_capacity(daily: pd.DataFrame, city: str) -> None:
    city_mask = daily["city"] == city
    gbfs = fetch_station_info(CITY_GBFS[city])
    print(f"  {city}: {len(gbfs)} live GBFS stations (after excluding valet/corral entries)")

    name_cap = gbfs.groupby("name")["capacity"].median()
    station_names = daily.loc[city_mask, "station_name"]
    exact = station_names.map(name_cap)
    n_exact = exact.notna().sum()
    daily.loc[city_mask, "capacity"] = exact.to_numpy()
    print(f"  {city}: {n_exact:,}/{city_mask.sum():,} rows matched by exact station name")

    still_missing_mask = city_mask & daily["capacity"].isna()
    unmatched_coords = (
        daily.loc[still_missing_mask, ["station_name", "lat", "lon"]]
        .drop_duplicates("station_name")
    )
    fallback = nearest_capacity(unmatched_coords, gbfs)
    if fallback:
        daily.loc[still_missing_mask, "capacity"] = (
            daily.loc[still_missing_mask, "station_name"].map(fallback)
        )
    n_fallback_stations = len(fallback)
    n_still_missing = daily.loc[city_mask, "capacity"].isna().sum()
    print(
        f"  {city}: {n_fallback_stations} additional stations matched via nearest-station "
        f"fallback (<= {NEAREST_MATCH_MAX_KM * 1000:.0f}m); "
        f"{n_still_missing:,} rows still unmatched"
    )


def drop_non_customer_rows(daily: pd.DataFrame) -> pd.DataFrame:
    drop_mask = pd.Series(False, index=daily.index)
    for city, names in NON_CUSTOMER_STATIONS.items():
        drop_mask |= (daily["city"] == city) & daily["station_name"].isin(names)

    if drop_mask.any():
        dropped_trips = daily.loc[drop_mask, "trips"].sum()
        print(
            f"Dropping {drop_mask.sum():,} rows ({dropped_trips:,} trips) for "
            f"{daily.loc[drop_mask, 'station_name'].nunique()} non-customer stations: "
            f"{sorted(daily.loc[drop_mask, 'station_name'].unique())}"
        )
    return daily.loc[~drop_mask].copy()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Backfill real GBFS dock capacity")
    parser.add_argument("--input", type=Path, default=DATA_PATH)
    parser.add_argument("--output", type=Path, default=DATA_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    daily = pd.read_parquet(args.input)
    daily["capacity"] = daily["capacity"].astype("float64")

    print("Before:")
    for city in CITY_GBFS:
        cap = daily.loc[daily["city"] == city, "capacity"]
        print(f"  {city}: {cap.nunique()} unique capacity values, median {cap.median():.0f}")

    daily = drop_non_customer_rows(daily)

    print("\nBackfilling capacity from live GBFS feeds...")
    for city in CITY_GBFS:
        backfill_city_capacity(daily, city)

    print("\nAfter:")
    for city in CITY_GBFS:
        cap = daily.loc[daily["city"] == city, "capacity"]
        print(
            f"  {city}: {cap.nunique()} unique capacity values, "
            f"median {cap.median():.0f}, missing {cap.isna().sum():,} rows"
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    daily.to_parquet(args.output, index=False)
    print(f"\nSaved to {args.output}")


if __name__ == "__main__":
    main()
