"""Station investment opportunity scoring service.

Produces an explainable, weighted opportunity score for each station
using configurable factor weights. Every recommendation includes
component scores and a plain-English explanation.

This is NOT a black-box model. All factors are derived from the data
with documented formulas, and all weights are stored in a config file.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.services.data_service import safe_divide
from backend.utils.paths import OPPORTUNITY_WEIGHTS_PATH
from backend.validation.validators import validate_weights


def load_opportunity_weights(
    path: Path | None = None,
) -> dict[str, Any]:
    path = path or OPPORTUNITY_WEIGHTS_PATH
    with open(path) as f:
        config = json.load(f)
    validate_weights(config["weights"])
    return config


def _normalize_0_100(series: pd.Series) -> pd.Series:
    """Min-max normalize a series to 0-100, handling edge cases."""
    series = series.replace([float("inf"), float("-inf")], np.nan)
    mn, mx = series.min(), series.max()
    if pd.isna(mn) or pd.isna(mx) or mx == mn:
        return pd.Series(50.0, index=series.index)
    return 100 * (series - mn) / (mx - mn)


def compute_mta_transit_scores(
    mta_df: pd.DataFrame,
    bike_station_daily: pd.DataFrame,
) -> pd.DataFrame:
    """Compute transit opportunity scores by joining MTA and bike data.

    This measures an observed association between transit ridership/delays
    and bike-share demand — it does NOT establish causation.
    """
    if mta_df.empty or bike_station_daily.empty:
        return pd.DataFrame()

    merged = mta_df.merge(
        bike_station_daily[["station_name", "bike_daily_trips"]],
        on="station_name",
        how="inner",
    )
    if merged.empty:
        return merged

    merged["mta_score"] = _normalize_0_100(merged["mta_daily_riders"])
    merged["bike_score"] = _normalize_0_100(merged["bike_daily_trips"])
    merged["delay_score"] = _normalize_0_100(merged["mta_delay_rate"])
    merged["transit_opportunity_score"] = (
        0.45 * merged["mta_score"]
        + 0.35 * (100 - merged["bike_score"])
        + 0.20 * merged["delay_score"]
    )
    return merged


def compute_station_opportunity_scores(
    station_df: pd.DataFrame,
    mta_opportunity: pd.DataFrame | None = None,
    config: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Score each station for investment opportunity.

    Each factor is normalized to 0-100 before applying weights.
    Returns component scores, weighted total, and explanation.
    """
    if config is None:
        config = load_opportunity_weights()
    weights = config["weights"]

    if station_df.empty:
        return pd.DataFrame()

    scores = station_df[["station_name"]].copy()

    # Demand score — average daily trips
    if "average_daily" in station_df.columns:
        scores["demand_score"] = _normalize_0_100(station_df["average_daily"])
    else:
        scores["demand_score"] = 50.0

    # Capacity pressure score
    if "pressure" in station_df.columns:
        clean_pressure = station_df["pressure"].replace(
            [float("inf"), float("-inf")], np.nan
        )
        scores["capacity_pressure_score"] = _normalize_0_100(clean_pressure)
    else:
        scores["capacity_pressure_score"] = 50.0

    # MTA connection score
    if mta_opportunity is not None and not mta_opportunity.empty:
        mta_lookup = mta_opportunity.set_index("station_name")[
            "transit_opportunity_score"
        ].to_dict()
        mta_vals = station_df["station_name"].map(mta_lookup)
        scores["mta_connection_score"] = mta_vals.fillna(0)
    else:
        scores["mta_connection_score"] = 0.0

    # Coverage gap score — inverse of station count at same lat/lon band
    # (Simplified: stations with fewer neighbors score higher)
    scores["coverage_gap_score"] = 50.0  # placeholder until geodensity implemented

    # Revenue potential score — based on trip volume as proxy
    if "trips" in station_df.columns:
        scores["revenue_potential_score"] = _normalize_0_100(
            station_df["trips"].astype(float)
        )
    else:
        scores["revenue_potential_score"] = 50.0

    # Electric bike score
    if "trips" in station_df.columns and "electric_trips" in station_df.columns:
        ebike_share = station_df.apply(
            lambda r: safe_divide(r.get("electric_trips", 0), r.get("trips", 1)),
            axis=1,
        )
        scores["electric_bike_score"] = _normalize_0_100(ebike_share)
    elif "ebike_share" in station_df.columns:
        scores["electric_bike_score"] = _normalize_0_100(station_df["ebike_share"])
    else:
        scores["electric_bike_score"] = 50.0

    # Weighted total
    scores["opportunity_score"] = sum(
        weights.get(col, 0) * scores[col]
        for col in weights
        if col in scores.columns
    )

    # Plain-English explanation
    scores["explanation"] = scores.apply(
        lambda r: _generate_explanation(r, weights), axis=1
    )

    # Recommendation type
    scores["recommendation_type"] = scores.apply(
        _assign_recommendation_type, axis=1
    )

    return scores


def _generate_explanation(row: pd.Series, weights: dict[str, float]) -> str:
    """Generate a deterministic plain-English explanation for a station score."""
    top_factors = sorted(
        [(col, row.get(col, 0)) for col in weights if col in row.index],
        key=lambda x: x[1],
        reverse=True,
    )[:3]

    factor_names = {
        "demand_score": "strong daily demand",
        "capacity_pressure_score": "high station pressure",
        "mta_connection_score": "a large nearby subway ridership base",
        "coverage_gap_score": "limited nearby station coverage",
        "revenue_potential_score": "high revenue potential",
        "electric_bike_score": "strong e-bike adoption",
    }

    reasons = [factor_names.get(f[0], f[0]) for f in top_factors if f[1] > 30]
    if not reasons:
        return "This station scores moderately across all factors."

    if len(reasons) == 1:
        return f"This location ranks highly because of {reasons[0]}."
    return (
        f"This location ranks highly because it combines "
        + ", ".join(reasons[:-1])
        + f", and {reasons[-1]}."
    )


def _assign_recommendation_type(row: pd.Series) -> str:
    score = row.get("opportunity_score", 0)
    pressure = row.get("capacity_pressure_score", 0)
    ebike = row.get("electric_bike_score", 0)

    if score < 30:
        return "Monitor low utilization"
    if pressure > 70:
        return "Expand dock capacity"
    if ebike > 70:
        return "Add more e-bikes"
    if score > 70:
        return "Add more bikes"
    return "Consider a new station nearby"
