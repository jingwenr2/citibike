"""Data loading and filtering service for processed parquet files.

Provides cached loading, column validation, and safe filtering for the
three main datasets: daily trips, hourly demand, and MTA opportunity.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.utils.paths import DAILY_DATA_PATH, HOURLY_DATA_PATH, MTA_DATA_PATH
from backend.validation.validators import validate_required_columns

DAILY_REQUIRED = {
    "date", "city", "system", "station_name", "lat", "lon",
    "rider_type", "trips", "electric_trips", "capacity",
}
HOURLY_REQUIRED = {"date", "hour", "day_name", "rider_type", "trips"}
MTA_REQUIRED = {
    "station_name", "neighborhood", "mta_daily_riders", "mta_delay_rate",
}


def _clean_daily(df: pd.DataFrame) -> pd.DataFrame:
    df["date"] = pd.to_datetime(df["date"])
    df["capacity"] = pd.to_numeric(df["capacity"], errors="coerce").fillna(0)
    df["capacity"] = df["capacity"].replace([float("inf"), float("-inf")], 0).astype("int16")
    df["trips"] = pd.to_numeric(df["trips"], errors="coerce").fillna(0).astype("int32")
    df["electric_trips"] = (
        pd.to_numeric(df["electric_trips"], errors="coerce").fillna(0).astype("int32")
    )
    df["lat"] = pd.to_numeric(df["lat"], errors="coerce").astype("float32")
    df["lon"] = pd.to_numeric(df["lon"], errors="coerce").astype("float32")
    for col in ("city", "system", "station_name", "rider_type"):
        if col in df.columns:
            df[col] = df[col].astype("category")
    return df


def load_daily_data(path: Path | None = None) -> pd.DataFrame:
    """Load the daily bike-share dataset from parquet.

    Returns the full dataset with validated columns and cleaned types.
    Returns None-equivalent empty DataFrame if file is missing.
    """
    path = path or DAILY_DATA_PATH
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    validate_required_columns(df, DAILY_REQUIRED, "bike_share_daily")
    return _clean_daily(df)


def load_hourly_data(path: Path | None = None) -> pd.DataFrame:
    path = path or HOURLY_DATA_PATH
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    validate_required_columns(df, HOURLY_REQUIRED, "bike_share_hourly")
    df["date"] = pd.to_datetime(df["date"])
    df["trips"] = pd.to_numeric(df["trips"], errors="coerce").fillna(0)
    return df


def load_mta_opportunity_data(path: Path | None = None) -> pd.DataFrame:
    path = path or MTA_DATA_PATH
    if not path.exists():
        return pd.DataFrame()
    df = pd.read_parquet(path)
    validate_required_columns(df, MTA_REQUIRED, "mta_bike_opportunity")
    if "mta_is_demo" not in df.columns:
        df["mta_is_demo"] = False
    df["mta_is_demo"] = df["mta_is_demo"].astype(bool)
    return df


def get_available_date_range(df: pd.DataFrame) -> tuple[date, date]:
    if df.empty or "date" not in df.columns:
        today = pd.Timestamp.now().date()
        return today, today
    return df["date"].min().date(), df["date"].max().date()


def get_available_cities(df: pd.DataFrame) -> list[str]:
    if df.empty or "city" not in df.columns:
        return []
    return sorted(df["city"].unique().tolist())


def filter_data(
    df: pd.DataFrame,
    *,
    cities: list[str] | None = None,
    rider_types: list[str] | None = None,
    start_date: date | pd.Timestamp | None = None,
    end_date: date | pd.Timestamp | None = None,
) -> pd.DataFrame:
    """Filter the daily dataset by city, rider type, and date range."""
    if df.empty:
        return df
    mask = pd.Series(True, index=df.index)
    if cities:
        mask &= df["city"].isin(cities)
    if rider_types:
        mask &= df["rider_type"].isin(rider_types)
    if start_date is not None:
        mask &= df["date"] >= pd.Timestamp(start_date)
    if end_date is not None:
        mask &= df["date"] <= pd.Timestamp(end_date)
    return df.loc[mask].copy()


def filter_nyc(df: pd.DataFrame) -> pd.DataFrame:
    """Convenience filter for NYC-only data."""
    return filter_data(df, cities=["New York City"])


def safe_divide(numerator: float, denominator: float, default: float = 0.0) -> float:
    """Division that handles zero, inf, and NaN safely."""
    if denominator == 0 or not np.isfinite(denominator):
        return default
    result = numerator / denominator
    return result if np.isfinite(result) else default
