"""Revenue estimation service.

IMPORTANT: Citi Bike trip data does not contain audited transaction-level
revenue. All values produced by this module are ESTIMATES based on
configurable pricing assumptions. They must be clearly labeled as
estimates in any presentation or report.

Methodology:
1. Membership revenue = estimated active members x annual price
2. Casual ride revenue = annual casual trips x single ride price
3. E-bike overage revenue = annual e-bike trips x average overage per trip
4. Sponsorship revenue = fixed annual amount (public contract)
5. Total = sum of the four streams

This avoids double-counting: membership revenue is counted once at the
annual subscription level, not per-trip. Per-trip revenue is only counted
for casual riders and e-bike overage fees (which apply to all riders).
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.services.data_service import safe_divide
from backend.utils.paths import PRICE_HISTORY_PATH, PRICING_CONFIG_PATH


def load_pricing_assumptions(
    path: Path | None = None,
) -> dict[str, Any]:
    path = path or PRICING_CONFIG_PATH
    with open(path) as f:
        return json.load(f)


def load_annual_membership_price_history(
    path: Path | None = None,
) -> pd.DataFrame:
    """Load Citi Bike's annual membership price history since its 2013 launch.

    Nominal and inflation-adjusted figures are sourced from the NYC
    Independent Budget Office; see citibike_price_history.json for citations.
    """
    path = path or PRICE_HISTORY_PATH
    with open(path) as f:
        payload = json.load(f)

    df = pd.DataFrame(payload["history"])
    df["effective_date"] = pd.to_datetime(df["effective_date"])
    return df.sort_values("effective_date").reset_index(drop=True)


def estimate_annual_revenue(
    df: pd.DataFrame,
    assumptions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Estimate annual revenue from NYC trip data.

    Args:
        df: Filtered NYC daily trip data.
        assumptions: Pricing assumptions dict. Loaded from config if None.

    Returns:
        Dictionary with revenue breakdown and the assumptions used.
        All monetary values are labeled as estimates.
    """
    if assumptions is None:
        assumptions = load_pricing_assumptions()

    total_trips = int(df["trips"].sum())
    days = max(1, df["date"].nunique())
    annual_trips = total_trips / days * 365

    # Rider split from actual data
    member_trips = df[df["rider_type"] == "Member"]["trips"].sum()
    casual_trips = total_trips - member_trips
    member_pct = safe_divide(member_trips, total_trips, 0.8)
    casual_pct = 1 - member_pct

    annual_member_trips = annual_trips * member_pct
    annual_casual_trips = annual_trips * casual_pct

    # E-bike share from actual data
    electric_trips = int(df["electric_trips"].sum())
    ebike_pct = safe_divide(electric_trips, total_trips, 0.7)
    annual_ebike_trips = annual_trips * ebike_pct

    # Revenue streams
    active_members = assumptions["estimated_active_annual_members"]
    membership_revenue = active_members * assumptions["annual_membership_price"]
    casual_ride_revenue = annual_casual_trips * assumptions["single_ride_price"]
    ebike_overage_revenue = annual_ebike_trips * assumptions["average_ebike_overage_per_trip"]
    sponsorship_revenue = assumptions["sponsorship_revenue_annual"]
    total_revenue = (
        membership_revenue + casual_ride_revenue
        + ebike_overage_revenue + sponsorship_revenue
    )

    return {
        "is_estimate": True,
        "total_estimated_revenue": total_revenue,
        "membership_revenue": membership_revenue,
        "casual_ride_revenue": casual_ride_revenue,
        "ebike_overage_revenue": ebike_overage_revenue,
        "sponsorship_revenue": sponsorship_revenue,
        "annual_trips": annual_trips,
        "annual_member_trips": annual_member_trips,
        "annual_casual_trips": annual_casual_trips,
        "annual_ebike_trips": annual_ebike_trips,
        "member_pct": member_pct,
        "casual_pct": casual_pct,
        "ebike_pct": ebike_pct,
        "active_members": active_members,
        "avg_revenue_per_trip": safe_divide(total_revenue, annual_trips),
        "assumptions_used": {
            k: v for k, v in assumptions.items() if not k.startswith("_")
        },
    }


def estimate_expansion_revenue(
    current_revenue: dict[str, Any],
    new_stations: int = 250,
    assumptions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Estimate revenue from station expansion.

    Returns projections labeled as estimates, not guaranteed outcomes.
    """
    if assumptions is None:
        assumptions = load_pricing_assumptions()

    active_stations = max(1, current_revenue.get("active_stations", 2400))
    trips_per_station_day = safe_divide(
        current_revenue["annual_trips"], active_stations * 365, 48
    )

    new_annual_trips = new_stations * trips_per_station_day * 365
    casual_pct = current_revenue["casual_pct"]
    ebike_pct = current_revenue["ebike_pct"]

    new_casual_trips = new_annual_trips * casual_pct
    new_ebike_trips = new_annual_trips * ebike_pct

    new_members_per_station = assumptions["new_members_per_new_station"]
    new_member_revenue = new_stations * new_members_per_station * assumptions["annual_membership_price"]
    new_casual_revenue = new_casual_trips * assumptions["single_ride_price"]
    new_ebike_revenue = new_ebike_trips * assumptions["average_ebike_overage_per_trip"]
    new_total_revenue = new_member_revenue + new_casual_revenue + new_ebike_revenue

    install_cost = new_stations * assumptions["station_install_cost"]
    annual_ops = new_stations * assumptions["station_annual_operating_cost"]
    net_annual_profit = new_total_revenue - annual_ops
    payback_months = (
        safe_divide(install_cost, net_annual_profit / 12, float("inf"))
        if net_annual_profit > 0
        else float("inf")
    )

    return {
        "is_estimate": True,
        "new_stations": new_stations,
        "new_annual_trips": new_annual_trips,
        "new_member_revenue": new_member_revenue,
        "new_casual_revenue": new_casual_revenue,
        "new_ebike_revenue": new_ebike_revenue,
        "new_total_revenue": new_total_revenue,
        "install_cost": install_cost,
        "annual_operating_cost": annual_ops,
        "net_annual_profit": net_annual_profit,
        "payback_months": payback_months,
        "trips_per_station_day": trips_per_station_day,
        "assumptions_used": {
            k: v for k, v in assumptions.items() if not k.startswith("_")
        },
    }


def estimate_public_benefits(
    new_annual_trips: float,
    new_total_revenue: float,
    install_cost: float,
    assumptions: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Estimate public benefits from expansion — health, congestion, emissions, tax."""
    if assumptions is None:
        assumptions = load_pricing_assumptions()

    health = new_annual_trips * assumptions["health_benefit_per_trip"]
    congestion = new_annual_trips * assumptions["congestion_benefit_per_trip"]
    emissions = new_annual_trips * assumptions["emissions_benefit_per_trip"]
    tax = new_total_revenue * assumptions["estimated_tax_rate"]
    total = health + congestion + emissions + tax
    govt_payback = safe_divide(install_cost, total, 0)

    return {
        "is_estimate": True,
        "health_benefit": health,
        "congestion_benefit": congestion,
        "emissions_benefit": emissions,
        "tax_benefit": tax,
        "total_public_benefit": total,
        "govt_payback_years": govt_payback,
    }


def revenue_projection(
    current_revenue: float,
    new_station_revenue: float,
    years: list[int] | None = None,
) -> pd.DataFrame:
    """Generate 5-year revenue projections under three scenarios."""
    if years is None:
        years = list(range(2026, 2032))

    scenarios = {
        "Do nothing (3% organic growth)": [
            current_revenue * (1.03 ** i) for i in range(len(years))
        ],
        "250 stations — Lyft self-funded": [
            (current_revenue + new_station_revenue * min(i / 2, 1)) * (1.05 ** i)
            for i in range(len(years))
        ],
        "500 stations + DOT partnership": [
            (current_revenue + new_station_revenue * 2 * min(i / 2, 1)) * (1.08 ** i)
            for i in range(len(years))
        ],
    }

    rows = []
    for scenario, values in scenarios.items():
        for yr, val in zip(years, values):
            rows.append({"Year": yr, "Scenario": scenario, "Annual Revenue": val})
    return pd.DataFrame(rows), scenarios


def monthly_revenue(
    df: pd.DataFrame,
    assumptions: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Estimate revenue by month."""
    if assumptions is None:
        assumptions = load_pricing_assumptions()
    if df.empty:
        return pd.DataFrame()

    monthly = df.assign(
        month=df["date"].dt.to_period("M").dt.to_timestamp()
    ).groupby("month", as_index=False).agg(
        trips=("trips", "sum"),
        electric_trips=("electric_trips", "sum"),
    )
    casual_df = df[df["rider_type"] == "Casual"]
    casual_monthly = casual_df.assign(
        month=casual_df["date"].dt.to_period("M").dt.to_timestamp()
    ).groupby("month", as_index=False)["trips"].sum().rename(columns={"trips": "casual_trips"})

    monthly = monthly.merge(casual_monthly, on="month", how="left")
    monthly["casual_trips"] = monthly["casual_trips"].fillna(0)

    monthly["casual_revenue"] = monthly["casual_trips"] * assumptions["single_ride_price"]
    monthly["ebike_revenue"] = monthly["electric_trips"] * assumptions["average_ebike_overage_per_trip"]
    monthly["estimated_revenue"] = monthly["casual_revenue"] + monthly["ebike_revenue"]

    return monthly


def revenue_by_station(
    df: pd.DataFrame,
    assumptions: dict[str, Any] | None = None,
) -> pd.DataFrame:
    """Estimate revenue contribution by station."""
    if assumptions is None:
        assumptions = load_pricing_assumptions()
    if df.empty:
        return pd.DataFrame()

    station = df.groupby("station_name", as_index=False).agg(
        trips=("trips", "sum"),
        electric_trips=("electric_trips", "sum"),
    )
    casual_station = (
        df[df["rider_type"] == "Casual"]
        .groupby("station_name", as_index=False)["trips"]
        .sum()
        .rename(columns={"trips": "casual_trips"})
    )
    station = station.merge(casual_station, on="station_name", how="left")
    station["casual_trips"] = station["casual_trips"].fillna(0)

    station["casual_revenue"] = station["casual_trips"] * assumptions["single_ride_price"]
    station["ebike_revenue"] = station["electric_trips"] * assumptions["average_ebike_overage_per_trip"]
    station["estimated_revenue"] = station["casual_revenue"] + station["ebike_revenue"]
    station["avg_revenue_per_trip"] = station.apply(
        lambda r: safe_divide(r["estimated_revenue"], r["trips"]), axis=1
    )

    return station.sort_values("estimated_revenue", ascending=False)
