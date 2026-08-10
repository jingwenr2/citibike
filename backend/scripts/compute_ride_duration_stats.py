"""Compute average Citi Bike NYC casual-rider trip duration from raw trip data.

The processed daily/hourly parquet files used by the dashboard don't retain
per-trip duration (started_at/ended_at are dropped during aggregation), so
this is computed directly from the raw monthly zips in data/raw/citibike/.

Produces: backend/config/ride_duration_stats.json

Usage:
    python backend/scripts/compute_ride_duration_stats.py
"""

from __future__ import annotations

import json
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
RAW_CITIBIKE = ROOT / "data" / "raw" / "citibike"
OUTPUT_PATH = ROOT / "backend" / "config" / "ride_duration_stats.json"

# Trips outside this range are almost certainly data errors (docking glitches,
# bikes reported lost/stolen, etc.) rather than real rides.
MIN_PLAUSIBLE_MINUTES = 1
MAX_PLAUSIBLE_MINUTES = 180


def compute_stats() -> dict:
    zips = sorted(RAW_CITIBIKE.glob("*.zip"))
    if not zips:
        raise RuntimeError(f"No raw trip zips found in {RAW_CITIBIKE}")

    total_minutes = 0.0
    total_count = 0
    per_rider_type: dict[str, tuple[float, int]] = {}

    for zp in zips:
        print(f"processing: {zp.name}")
        with zipfile.ZipFile(zp) as zf:
            csv_names = [n for n in zf.namelist() if n.endswith(".csv") and not n.startswith("__MACOSX")]
            for name in csv_names:
                with zf.open(name) as f:
                    for chunk in pd.read_csv(
                        f,
                        usecols=["started_at", "ended_at", "member_casual"],
                        chunksize=500_000,
                    ):
                        started = pd.to_datetime(chunk["started_at"], format="mixed", errors="coerce")
                        ended = pd.to_datetime(chunk["ended_at"], format="mixed", errors="coerce")
                        minutes = (ended - started).dt.total_seconds() / 60
                        valid = (minutes >= MIN_PLAUSIBLE_MINUTES) & (minutes <= MAX_PLAUSIBLE_MINUTES)
                        rider_type = chunk["member_casual"].str.lower()

                        for label in ("casual", "member"):
                            mask = valid & (rider_type == label)
                            s = minutes[mask].sum()
                            c = int(mask.sum())
                            prev_s, prev_c = per_rider_type.get(label, (0.0, 0))
                            per_rider_type[label] = (prev_s + s, prev_c + c)

                        total_minutes += minutes[valid].sum()
                        total_count += int(valid.sum())

    result = {
        "_description": (
            "Average Citi Bike NYC trip duration, computed directly from raw "
            "monthly trip data (started_at/ended_at), not from an external "
            "source. Trips outside [1, 180] minutes are excluded as data errors."
        ),
        "_computed_at": datetime.now(timezone.utc).isoformat(),
        "_source_files": [z.name for z in zips],
        "overall_avg_minutes": round(total_minutes / total_count, 2) if total_count else None,
        "overall_trip_count": total_count,
        "by_rider_type": {
            label: {
                "avg_minutes": round(s / c, 2) if c else None,
                "trip_count": c,
            }
            for label, (s, c) in per_rider_type.items()
        },
    }
    return result


def main() -> None:
    stats = compute_stats()
    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT_PATH.write_text(json.dumps(stats, indent=2))
    print(f"\nSaved to {OUTPUT_PATH}")
    print(json.dumps(stats, indent=2))


if __name__ == "__main__":
    main()
