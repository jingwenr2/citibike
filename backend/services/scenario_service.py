"""Investment scenario simulation service.

This is a financial scenario calculator, not a machine-learning prediction.
All outputs are projections based on user-selected assumptions and must
be clearly labeled as such. They are not guaranteed outcomes.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from backend.services.data_service import safe_divide
from backend.utils.paths import SCENARIO_CONFIG_PATH
from backend.validation.validators import (
    ValidationError,
    validate_investment_inputs,
    validate_positive_number,
    validate_scenario_mode,
)


def load_scenario_assumptions(
    path: Path | None = None,
) -> dict[str, Any]:
    path = path or SCENARIO_CONFIG_PATH
    with open(path) as f:
        return json.load(f)


def get_scenario_defaults(mode: str = "base") -> dict[str, Any]:
    validate_scenario_mode(mode)
    config = load_scenario_assumptions()
    return config[mode]


def simulate_investment(
    investment_amount: float,
    new_stations: int,
    new_classic_bikes: int,
    new_ebikes: int,
    analysis_years: int = 5,
    mode: str = "base",
    overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Run an investment scenario simulation.

    All outputs are labeled as projections. Sensitivity analysis is
    included by running all three scenarios internally.

    Args:
        investment_amount: Total capital budget.
        new_stations: Number of new stations to build.
        new_classic_bikes: Number of new classic bikes to deploy.
        new_ebikes: Number of new e-bikes to deploy.
        analysis_years: Period over which to project returns.
        mode: One of 'conservative', 'base', 'optimistic'.
        overrides: Optional dict to override specific assumption values.

    Returns:
        Dict with projected costs, revenue, ROI, and sensitivity analysis.
    """
    validate_investment_inputs(
        investment_amount, new_stations, new_classic_bikes, new_ebikes, analysis_years
    )
    validate_scenario_mode(mode)

    config = load_scenario_assumptions()
    params = dict(config[mode])  # copy
    if overrides:
        params.update(overrides)

    total_new_bikes = new_classic_bikes + new_ebikes

    # Capital costs
    station_capital = new_stations * params["station_install_cost"]
    classic_capital = new_classic_bikes * params["classic_bike_cost"]
    ebike_capital = new_ebikes * params["ebike_cost"]
    total_capital = station_capital + classic_capital + ebike_capital

    if total_capital > investment_amount:
        capital_warning = (
            f"Total capital cost (${total_capital:,.0f}) exceeds the "
            f"investment budget (${investment_amount:,.0f})."
        )
    else:
        capital_warning = None

    # Operating costs
    annual_bike_ops = total_new_bikes * params["annual_operating_cost_per_bike"]
    annual_station_ops = new_stations * params["annual_station_operating_cost"]
    annual_operating_cost = annual_bike_ops + annual_station_ops

    # Projected rides
    rides_per_bike_day = params["rides_per_new_bike_per_day"]
    ramp_months = params["utilization_ramp_months"]
    # First-year rides account for utilization ramp-up
    ramp_factor = max(0.5, 1 - ramp_months / 24)
    first_year_rides = total_new_bikes * rides_per_bike_day * 365 * ramp_factor
    steady_state_rides = total_new_bikes * rides_per_bike_day * 365

    # Revenue
    revenue_per_ride = params["revenue_per_ride"]
    first_year_revenue = first_year_rides * revenue_per_ride
    steady_state_revenue = steady_state_rides * revenue_per_ride

    # Membership growth
    membership_growth = params["membership_growth_rate"]

    # Multi-year projection
    annual_projections = []
    cumulative_revenue = 0
    cumulative_cost = total_capital
    for year in range(1, analysis_years + 1):
        if year == 1:
            rides = first_year_rides
            revenue = first_year_revenue
        else:
            growth = (1 + params["organic_growth_rate"]) ** (year - 1)
            rides = steady_state_rides * growth
            revenue = rides * revenue_per_ride

        net = revenue - annual_operating_cost
        cumulative_revenue += revenue
        cumulative_cost += annual_operating_cost

        annual_projections.append({
            "year": year,
            "projected_rides": rides,
            "projected_revenue": revenue,
            "operating_cost": annual_operating_cost,
            "net_contribution": net,
            "cumulative_revenue": cumulative_revenue,
            "cumulative_cost": cumulative_cost,
        })

    # Summary metrics
    total_projected_revenue = cumulative_revenue
    total_operating_costs = annual_operating_cost * analysis_years
    total_cost = total_capital + total_operating_costs
    total_profit = total_projected_revenue - total_cost

    payback_period = None
    cumulative_net = -total_capital
    for proj in annual_projections:
        cumulative_net += proj["net_contribution"]
        if cumulative_net >= 0 and payback_period is None:
            # Interpolate within the year
            prev_net = cumulative_net - proj["net_contribution"]
            fraction = safe_divide(-prev_net, proj["net_contribution"], 1)
            payback_period = proj["year"] - 1 + fraction

    simple_roi = safe_divide(total_profit, total_capital) if total_capital > 0 else 0
    revenue_per_station = safe_divide(total_projected_revenue, new_stations) if new_stations > 0 else 0
    rides_per_bike = safe_divide(steady_state_rides, total_new_bikes) if total_new_bikes > 0 else 0

    # Break-even utilization: min rides/bike/day needed to cover costs
    annual_cost_per_bike = safe_divide(
        annual_operating_cost + safe_divide(total_capital, analysis_years),
        total_new_bikes,
    )
    breakeven_rides_per_day = safe_divide(
        annual_cost_per_bike, revenue_per_ride * 365
    )

    # Sensitivity: run all three scenarios
    sensitivity = {}
    for scenario_mode in ["conservative", "base", "optimistic"]:
        s_params = config[scenario_mode]
        s_rides = total_new_bikes * s_params["rides_per_new_bike_per_day"] * 365
        s_revenue = s_rides * s_params["revenue_per_ride"] * analysis_years
        s_ops = (
            total_new_bikes * s_params["annual_operating_cost_per_bike"]
            + new_stations * s_params["annual_station_operating_cost"]
        ) * analysis_years
        s_profit = s_revenue - total_capital - s_ops
        sensitivity[scenario_mode] = {
            "label": s_params["label"],
            "total_revenue": s_revenue,
            "total_profit": s_profit,
            "simple_roi": safe_divide(s_profit, total_capital),
        }

    return {
        "is_projection": True,
        "mode": mode,
        "inputs": {
            "investment_amount": investment_amount,
            "new_stations": new_stations,
            "new_classic_bikes": new_classic_bikes,
            "new_ebikes": new_ebikes,
            "analysis_years": analysis_years,
        },
        "capital_cost": {
            "station_capital": station_capital,
            "classic_bike_capital": classic_capital,
            "ebike_capital": ebike_capital,
            "total_capital": total_capital,
        },
        "annual_operating_cost": annual_operating_cost,
        "projected_rides": {
            "first_year": first_year_rides,
            "steady_state_annual": steady_state_rides,
        },
        "projected_revenue": {
            "first_year": first_year_revenue,
            "steady_state_annual": steady_state_revenue,
            "total_over_period": total_projected_revenue,
        },
        "total_cost": total_cost,
        "total_profit": total_profit,
        "payback_period_years": payback_period,
        "simple_roi": simple_roi,
        "revenue_per_station": revenue_per_station,
        "rides_per_bike_annual": rides_per_bike,
        "breakeven_rides_per_bike_per_day": breakeven_rides_per_day,
        "annual_projections": annual_projections,
        "sensitivity": sensitivity,
        "capital_warning": capital_warning,
        "assumptions_used": {
            k: v for k, v in params.items() if not k.startswith("_")
        },
    }
