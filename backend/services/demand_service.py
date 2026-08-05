"""Demand analytics service — extracts demand calculations from the UI layer.

All functions accept pre-filtered DataFrames and return clean DataFrames
or dictionaries ready for Plotly / Streamlit rendering.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from backend.services.data_service import safe_divide

DAY_ORDER = [
    "Monday", "Tuesday", "Wednesday", "Thursday",
    "Friday", "Saturday", "Sunday",
]
PEAK_HOURS = {7, 8, 9, 17, 18, 19}


def total_trips(df: pd.DataFrame) -> int:
    return int(df["trips"].sum()) if not df.empty else 0


def average_daily_trips(df: pd.DataFrame) -> float:
    if df.empty:
        return 0.0
    daily = df.groupby("date", as_index=False)["trips"].sum()
    return float(daily["trips"].mean())


def electric_bike_share(df: pd.DataFrame) -> float:
    t = df["trips"].sum()
    return safe_divide(df["electric_trips"].sum(), t)


def member_casual_split(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["rider_type", "trips"])
    return df.groupby("rider_type", as_index=False)["trips"].sum()


def bike_type_split(df: pd.DataFrame) -> pd.DataFrame:
    electric = int(df["electric_trips"].sum())
    classic = int(df["trips"].sum()) - electric
    return pd.DataFrame({
        "bike_type": ["Electric", "Classic"],
        "trips": [electric, classic],
    })


def monthly_demand(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["month", "city", "trips"])
    out = df.assign(month=df["date"].dt.to_period("M").dt.to_timestamp())
    return (
        out.groupby(["month", "city"], as_index=False)["trips"]
        .sum()
        .sort_values("month")
    )


def daily_demand_trend(
    df: pd.DataFrame, smoothing: int = 7
) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame(columns=["date", "rider_type", "trips", "smoothed_trips"])
    trend = (
        df.groupby(["date", "rider_type"], as_index=False)["trips"]
        .sum()
        .sort_values("date")
    )
    trend["smoothed_trips"] = trend.groupby("rider_type")["trips"].transform(
        lambda v: v.rolling(smoothing, min_periods=1).mean()
    )
    return trend


def weekday_bike_type_demand(df: pd.DataFrame) -> pd.DataFrame:
    if df.empty:
        return pd.DataFrame()
    wd = df.assign(
        weekday=df["date"].dt.day_name(),
        weekday_index=df["date"].dt.dayofweek,
        classic_trips=df["trips"] - df["electric_trips"],
    )[["weekday", "weekday_index", "date", "electric_trips", "classic_trips"]]
    long = wd.melt(
        id_vars=["weekday", "weekday_index", "date"],
        value_vars=["electric_trips", "classic_trips"],
        var_name="bike_type",
        value_name="trips",
    )
    long["bike_type"] = long["bike_type"].map(
        {"electric_trips": "Electric", "classic_trips": "Classic"}
    )
    return (
        long.groupby(
            ["weekday", "weekday_index", "bike_type"], as_index=False
        )["trips"]
        .mean()
        .sort_values("weekday_index")
    )


def hourly_heatmap_data(hourly_df: pd.DataFrame) -> pd.DataFrame:
    """Compute average trips per hour-weekday cell for the heatmap."""
    if hourly_df.empty:
        return pd.DataFrame()
    day_counts = (
        hourly_df.drop_duplicates(["date", "day_name"])
        .groupby("day_name")["date"]
        .nunique()
    )
    pivot = hourly_df.groupby(["hour", "day_name"], as_index=False)["trips"].sum()
    pivot["day_count"] = pivot["day_name"].map(day_counts).clip(lower=1)
    pivot["avg_trips"] = pivot["trips"] / pivot["day_count"]
    return pivot


def peak_hour_share(hourly_df: pd.DataFrame) -> float:
    if hourly_df.empty:
        return 0.0
    peak_total = hourly_df[hourly_df["hour"].isin(PEAK_HOURS)]["trips"].sum()
    total = hourly_df["trips"].sum()
    return safe_divide(peak_total, total)


def station_summary(df: pd.DataFrame) -> pd.DataFrame:
    """Station-level aggregation with demand pressure.

    Safely handles zero/missing capacity and infinite pressure values.
    """
    if df.empty:
        return pd.DataFrame()
    summary = (
        df.groupby(
            ["city", "system", "station_name", "lat", "lon", "capacity"],
            as_index=False,
        )
        .agg(trips=("trips", "sum"), average_daily=("trips", "mean"))
    )
    summary["capacity"] = summary["capacity"].replace(0, np.nan)
    summary["pressure"] = summary["average_daily"] / summary["capacity"]
    summary["pressure"] = summary["pressure"].replace(
        [float("inf"), float("-inf")], np.nan
    )
    max_trips = summary["trips"].max()
    if max_trips > 0:
        summary["marker_size"] = 10 + 28 * summary["trips"] / max_trips
    else:
        summary["marker_size"] = 10.0
    return summary


def station_pressure_categories(df: pd.DataFrame) -> pd.DataFrame:
    """Compute station capacity pressure and categorize stations."""
    if df.empty:
        return pd.DataFrame()
    pressure = (
        df.groupby(["station_name", "capacity"], as_index=False)
        .agg(total_trips=("trips", "sum"), days=("date", "nunique"))
    )
    pressure["daily_demand"] = pressure["total_trips"] / pressure["days"]
    pressure["capacity"] = pressure["capacity"].replace(0, np.nan)
    pressure["pressure"] = pressure["daily_demand"] / pressure["capacity"]
    pressure["pressure"] = pressure["pressure"].replace(
        [float("inf"), float("-inf")], np.nan
    )
    pressure["pressure_category"] = pd.cut(
        pressure["pressure"].fillna(0),
        bins=[0, 0.5, 1.0, 1.5, float("inf")],
        labels=[
            "Under-utilized (<0.5)",
            "Balanced (0.5-1.0)",
            "Strained (1.0-1.5)",
            "Critical (>1.5)",
        ],
    )
    return pressure


def prior_period_delta(
    current: pd.DataFrame, full_data: pd.DataFrame
) -> float:
    """Calculate growth rate versus the equivalent prior period."""
    if current.empty or full_data.empty:
        return 0.0
    days = max(1, (current["date"].max() - current["date"].min()).days + 1)
    cutoff = current["date"].min() - pd.Timedelta(days=1)
    prior_start = cutoff - pd.Timedelta(days=days - 1)
    prior = full_data[
        full_data["city"].isin(current["city"].unique())
        & full_data["rider_type"].isin(current["rider_type"].unique())
        & full_data["date"].between(prior_start, cutoff)
    ]
    return safe_divide(
        current["trips"].sum() - prior["trips"].sum(),
        prior["trips"].sum(),
    )
