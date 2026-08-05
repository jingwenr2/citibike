"""XGBoost model loader for NYC demand forecasting.

Loads the pre-trained NYC model once and provides forecast functions.
Does NOT train a San Francisco model — SF is a case study only.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.utils.paths import NYC_MODEL_PATH, FORECAST_METRICS_PATH

FEATURES = [
    "lat", "lon", "capacity",
    "day_of_week", "month", "is_weekend", "is_holiday",
    "lag_1d", "lag_7d", "roll_mean_7d", "roll_mean_28d", "roll_std_7d",
    "electric_share", "member_share",
    "mta_daily_riders", "mta_delay_rate", "nearest_mta_distance_km",
    "peak_hour_share",
]

US_HOLIDAYS = {
    "2024-01-01", "2024-01-15", "2024-02-19", "2024-05-27",
    "2024-07-04", "2024-09-02", "2024-10-14", "2024-11-28", "2024-12-25",
    "2025-01-01", "2025-01-20", "2025-02-17", "2025-05-26",
    "2025-07-04", "2025-09-01", "2025-10-13", "2025-11-27", "2025-12-25",
    "2026-01-01", "2026-01-19", "2026-02-16", "2026-05-25",
    "2026-07-04", "2026-09-07", "2026-10-12", "2026-11-26", "2026-12-25",
}

_model_cache: dict[str, Any] = {}


def load_nyc_model():
    """Load the XGBoost NYC model, caching after first load."""
    if "model" in _model_cache:
        return _model_cache["model"]

    if not NYC_MODEL_PATH.exists():
        raise FileNotFoundError(
            f"NYC XGBoost model not found at {NYC_MODEL_PATH}. "
            "Run backend/demand_forecast_xgboost.py to train it."
        )

    try:
        from xgboost import XGBRegressor
    except ImportError:
        raise ImportError(
            "xgboost is required for forecasting. Install it with: pip install xgboost"
        )

    model = XGBRegressor()
    model.load_model(str(NYC_MODEL_PATH))
    _model_cache["model"] = model
    return model


def load_forecast_metrics() -> list[dict[str, Any]]:
    if not FORECAST_METRICS_PATH.exists():
        return []
    with open(FORECAST_METRICS_PATH) as f:
        return json.load(f)


def get_nyc_metrics() -> dict[str, Any] | None:
    metrics = load_forecast_metrics()
    for m in metrics:
        if m.get("city") == "New York City":
            return m
    return None


def prepare_forecast_features(
    historical_df: pd.DataFrame,
    forecast_dates: pd.DatetimeIndex,
    station_name: str,
) -> pd.DataFrame | None:
    """Build feature DataFrame for forecasting a single station.

    Returns None if insufficient historical data for lag features.
    """
    station_data = historical_df[
        historical_df["station_name"] == station_name
    ].sort_values("date")

    if len(station_data) < 28:
        return None

    latest = station_data.iloc[-1]
    recent_trips = station_data["trips"].tail(28).values

    rows = []
    for date in forecast_dates:
        row = {
            "date": date,
            "lat": latest["lat"],
            "lon": latest["lon"],
            "day_of_week": date.dayofweek,
            "month": date.month,
            "is_weekend": int(date.dayofweek >= 5),
            "is_holiday": int(date.strftime("%Y-%m-%d") in US_HOLIDAYS),
            "electric_share": latest.get("electric_share", 0.7),
            "member_share": latest.get("member_share", 0.8),
        }
        # Lag features from recent history
        idx = len(recent_trips) - 1
        row["lag_1d"] = recent_trips[idx] if idx >= 0 else 0
        row["lag_7d"] = recent_trips[idx - 6] if idx >= 6 else recent_trips[0]
        row["roll_mean_7d"] = float(np.mean(recent_trips[-7:])) if len(recent_trips) >= 7 else float(np.mean(recent_trips))
        row["roll_mean_28d"] = float(np.mean(recent_trips[-28:])) if len(recent_trips) >= 28 else float(np.mean(recent_trips))
        rows.append(row)

    return pd.DataFrame(rows)


def forecast_station(
    historical_df: pd.DataFrame,
    station_name: str,
    horizon_days: int = 30,
) -> dict[str, Any] | None:
    """Forecast daily trips for a single NYC station.

    Returns forecast values plus a warning if the forecast date
    is far from the training period.
    """
    model = load_nyc_model()
    max_date = historical_df["date"].max()
    forecast_dates = pd.date_range(
        max_date + pd.Timedelta(days=1), periods=horizon_days
    )

    features_df = prepare_forecast_features(
        historical_df, forecast_dates, station_name
    )
    if features_df is None:
        return None

    predictions = model.predict(features_df[FEATURES])
    predictions = np.clip(predictions, 0, None)

    # Warning if forecasting far from training data
    warning = None
    if horizon_days > 90:
        warning = (
            "Forecast horizon exceeds 90 days. Accuracy may decline "
            "significantly outside the training period."
        )

    return {
        "station_name": station_name,
        "forecast_dates": forecast_dates.tolist(),
        "forecast_values": predictions.tolist(),
        "horizon_days": horizon_days,
        "warning": warning,
        "model_type": "XGBoost",
        "features_used": FEATURES,
    }
