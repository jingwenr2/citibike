"""Build the MTA × Citi Bike opportunity table used by the dashboard.

Official inputs:
  - MTA Subway Hourly Ridership: Beginning 2025 (5wq4-mkjj)
  - MTA Subway Wait Assessment: Beginning 2015 (s666-h6b7)

The script aggregates recent subway entries by complex, converts wait
assessment to a reliability-gap rate, and assigns subway complexes to their
nearest Citi Bike station. It writes:

    data/processed/mta_bike_opportunity.parquet

Run with real processed bike stations:
    python scripts/build_mta_opportunity.py

Run before the Citi Bike pipeline is ready:
    python scripts/build_mta_opportunity.py --allow-demo-stations
"""

from __future__ import annotations

import argparse
import json
import math
import re
from datetime import datetime, timedelta
from pathlib import Path
from urllib.parse import urlencode
from urllib.request import Request, urlopen

import numpy as np
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
BIKE_PATH = ROOT / "data" / "processed" / "bike_share_daily.parquet"
OUTPUT_PATH = ROOT / "data" / "processed" / "mta_bike_opportunity.parquet"

RIDERSHIP_ENDPOINT = "https://data.ny.gov/resource/5wq4-mkjj.json"
WAIT_ENDPOINT = "https://data.ny.gov/resource/s666-h6b7.json"

DEMO_NYC_STATIONS = [
    ("Broadway & W 25 St", 40.7429, -73.9892),
    ("West St & Chambers St", 40.7175, -74.0132),
    ("E 17 St & Broadway", 40.7370, -73.9901),
    ("1 Ave & E 68 St", 40.7650, -73.9570),
    ("Bedford Ave & Nassau Ave", 40.7231, -73.9521),
    ("Crescent St & 30 Ave", 40.7687, -73.9240),
]


def fetch_json(endpoint: str, params: dict[str, str]) -> list[dict]:
    url = f"{endpoint}?{urlencode(params)}"
    request = Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "citibike-capstone/1.0",
        },
    )
    with urlopen(request, timeout=120) as response:
        payload = json.load(response)
    if isinstance(payload, dict) and payload.get("error"):
        raise RuntimeError(payload.get("message", "MTA API request failed"))
    return payload


def latest_timestamp(endpoint: str, field: str) -> pd.Timestamp:
    rows = fetch_json(endpoint, {"$select": f"max({field}) as latest"})
    if not rows or "latest" not in rows[0]:
        raise RuntimeError(f"Could not determine latest {field}")
    return pd.Timestamp(rows[0]["latest"])


def load_ridership(lookback_days: int) -> tuple[pd.DataFrame, pd.Timestamp, pd.Timestamp]:
    latest = latest_timestamp(RIDERSHIP_ENDPOINT, "transit_timestamp")
    end = latest.floor("D") + pd.Timedelta(days=1)
    start = end - pd.Timedelta(days=lookback_days)
    params = {
        "$select": (
            "station_complex_id,station_complex,borough,latitude,longitude,"
            "sum(ridership) as ridership"
        ),
        "$where": (
            f"transit_timestamp >= '{start:%Y-%m-%dT%H:%M:%S}' "
            f"AND transit_timestamp < '{end:%Y-%m-%dT%H:%M:%S}' "
            "AND transit_mode = 'subway'"
        ),
        "$group": (
            "station_complex_id,station_complex,borough,latitude,longitude"
        ),
        "$limit": "5000",
    }
    rows = fetch_json(RIDERSHIP_ENDPOINT, params)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("The MTA ridership query returned no rows")
    numeric = ["latitude", "longitude", "ridership"]
    frame[numeric] = frame[numeric].apply(pd.to_numeric, errors="coerce")
    frame = frame.dropna(subset=numeric)
    frame["mta_daily_riders"] = frame["ridership"] / lookback_days
    return frame, start, end


def load_wait_assessment(months: int = 6) -> tuple[pd.DataFrame, pd.Timestamp]:
    latest = latest_timestamp(WAIT_ENDPOINT, "month").floor("D")
    start = (latest - pd.DateOffset(months=months - 1)).replace(day=1)
    params = {
        "$select": (
            "line,avg(wait_assessment) as wait_assessment,"
            "sum(num_sched_timepoints) as scheduled_timepoints"
        ),
        "$where": f"month >= '{start:%Y-%m-%dT%H:%M:%S}'",
        "$group": "line",
        "$limit": "100",
    }
    rows = fetch_json(WAIT_ENDPOINT, params)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("The MTA wait-assessment query returned no rows")
    frame["wait_assessment"] = pd.to_numeric(
        frame["wait_assessment"], errors="coerce"
    )
    frame["mta_delay_rate"] = 1 - frame["wait_assessment"]
    frame["line_key"] = frame["line"].map(normalize_line)
    return frame.dropna(subset=["mta_delay_rate"]), start


def normalize_line(line: str) -> str:
    clean = re.sub(r"[^A-Za-z0-9]", "", str(line)).upper()
    if clean in {"J", "Z", "JZ"}:
        return "JZ"
    if clean.startswith("S"):
        return "S"
    return clean


def station_lines(station_complex: str) -> list[str]:
    match = re.search(r"\(([^()]*)\)\s*$", str(station_complex))
    if not match:
        return []
    lines = re.split(r"[,/ ]+", match.group(1))
    return sorted({normalize_line(line) for line in lines if line.strip()})


def attach_delay_rate(
    ridership: pd.DataFrame, wait: pd.DataFrame
) -> pd.DataFrame:
    delay_by_line = wait.set_index("line_key")["mta_delay_rate"].to_dict()
    system_delay = float(wait["mta_delay_rate"].mean())

    def station_delay(name: str) -> float:
        values = [
            delay_by_line[line]
            for line in station_lines(name)
            if line in delay_by_line
        ]
        return float(np.mean(values)) if values else system_delay

    out = ridership.copy()
    out["mta_delay_rate"] = out["station_complex"].map(station_delay)
    return out


def load_bike_stations(allow_demo: bool) -> tuple[pd.DataFrame, bool]:
    if BIKE_PATH.exists():
        bike = pd.read_parquet(BIKE_PATH)
        bike = bike[bike["city"].eq("New York City")].copy()
        required = {"station_name", "lat", "lon"}
        missing = required.difference(bike.columns)
        if missing:
            raise ValueError(
                "Bike dataset is missing columns: " + ", ".join(sorted(missing))
            )
        bike = (
            bike.groupby("station_name", as_index=False)[["lat", "lon"]]
            .median()
            .dropna()
        )
        if bike.empty:
            raise ValueError("No NYC stations found in the bike dataset")
        return bike, False
    if not allow_demo:
        raise FileNotFoundError(
            f"{BIKE_PATH} does not exist. Build the Citi Bike processed data "
            "or rerun with --allow-demo-stations."
        )
    return pd.DataFrame(
        DEMO_NYC_STATIONS, columns=["station_name", "lat", "lon"]
    ), True


def haversine_km(
    lat1: np.ndarray,
    lon1: np.ndarray,
    lat2: float,
    lon2: float,
) -> np.ndarray:
    radius = 6371.0088
    lat1r, lon1r = np.radians(lat1), np.radians(lon1)
    lat2r, lon2r = math.radians(lat2), math.radians(lon2)
    dlat, dlon = lat1r - lat2r, lon1r - lon2r
    value = (
        np.sin(dlat / 2) ** 2
        + np.cos(lat1r) * math.cos(lat2r) * np.sin(dlon / 2) ** 2
    )
    return 2 * radius * np.arcsin(np.sqrt(value))


def join_nearest(
    subway: pd.DataFrame,
    bike: pd.DataFrame,
    max_distance_km: float,
) -> pd.DataFrame:
    bike_lat = bike["lat"].to_numpy()
    bike_lon = bike["lon"].to_numpy()
    assignments: list[dict] = []

    for row in subway.itertuples(index=False):
        distances = haversine_km(bike_lat, bike_lon, row.latitude, row.longitude)
        nearest_idx = int(np.argmin(distances))
        if distances[nearest_idx] > max_distance_km:
            continue
        assignments.append(
            {
                "station_name": bike.iloc[nearest_idx]["station_name"],
                "mta_complex": row.station_complex,
                "mta_daily_riders": row.mta_daily_riders,
                "mta_delay_rate": row.mta_delay_rate,
                "distance_km": float(distances[nearest_idx]),
            }
        )
    assigned = pd.DataFrame(assignments)
    if assigned.empty:
        raise RuntimeError(
            "No MTA complexes were within the configured bike-station radius"
        )

    output_rows: list[dict] = []
    for station_name, group in assigned.groupby("station_name"):
        weights = group["mta_daily_riders"].clip(lower=0)
        closest = group.loc[group["distance_km"].idxmin()]
        output_rows.append(
            {
                "station_name": station_name,
                "neighborhood": closest["mta_complex"],
                "mta_daily_riders": float(group["mta_daily_riders"].sum()),
                "mta_delay_rate": (
                    float(np.average(group["mta_delay_rate"], weights=weights))
                    if weights.sum()
                    else float(group["mta_delay_rate"].mean())
                ),
                "mta_station_count": int(len(group)),
                "nearest_mta_distance_km": float(group["distance_km"].min()),
            }
        )
    return pd.DataFrame(output_rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookback-days", type=int, default=90)
    parser.add_argument("--wait-months", type=int, default=6)
    parser.add_argument("--max-distance-km", type=float, default=0.8)
    parser.add_argument("--allow-demo-stations", action="store_true")
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    ridership, ride_start, ride_end = load_ridership(args.lookback_days)
    wait, wait_start = load_wait_assessment(args.wait_months)
    subway = attach_delay_rate(ridership, wait)
    bike, bike_is_demo = load_bike_stations(args.allow_demo_stations)
    output = join_nearest(subway, bike, args.max_distance_km)
    output["mta_is_demo"] = bike_is_demo
    output["ridership_start"] = ride_start
    output["ridership_end"] = ride_end
    output["wait_assessment_start"] = wait_start
    output["source_ridership_dataset"] = "5wq4-mkjj"
    output["source_reliability_dataset"] = "s666-h6b7"

    args.output.parent.mkdir(parents=True, exist_ok=True)
    output.to_parquet(args.output, index=False)
    print(f"Saved {len(output):,} station rows to {args.output}")
    print(
        f"Ridership: {ride_start.date()} through "
        f"{(ride_end - pd.Timedelta(days=1)).date()}"
    )
    print(f"Wait assessment beginning: {wait_start.date()}")
    if bike_is_demo:
        print(
            "WARNING: Official MTA data was joined to demonstration bike "
            "stations. Rebuild after bike_share_daily.parquet is available."
        )


if __name__ == "__main__":
    main()
