"""Input validation for backend services."""

from __future__ import annotations

from datetime import date
from typing import Any

import pandas as pd

VALID_CITIES = {"New York City", "San Francisco"}
VALID_RIDER_TYPES = {"Member", "Casual"}
VALID_BIKE_TYPES = {"Electric", "Classic"}
VALID_SCENARIO_MODES = {"conservative", "base", "optimistic"}


class ValidationError(ValueError):
    """Raised when user-facing input validation fails."""


def validate_date_range(
    start: date | str | None,
    end: date | str | None,
    available_min: date | None = None,
    available_max: date | None = None,
) -> tuple[date, date]:
    if start is None or end is None:
        raise ValidationError("Both start and end dates are required.")
    if isinstance(start, str):
        start = pd.Timestamp(start).date()
    if isinstance(end, str):
        end = pd.Timestamp(end).date()
    if start > end:
        raise ValidationError(
            f"Start date ({start}) cannot be after end date ({end})."
        )
    if available_min and start < available_min:
        raise ValidationError(
            f"Start date ({start}) is before the earliest available data ({available_min})."
        )
    if available_max and end > available_max:
        raise ValidationError(
            f"End date ({end}) is after the latest available data ({available_max})."
        )
    return start, end


def validate_city(city: str) -> str:
    if city not in VALID_CITIES:
        raise ValidationError(
            f"Unknown city: '{city}'. Valid cities: {', '.join(sorted(VALID_CITIES))}"
        )
    return city


def validate_positive_number(value: float | int, name: str) -> float:
    if value is None or value <= 0:
        raise ValidationError(f"{name} must be a positive number, got {value}.")
    return float(value)


def validate_non_negative(value: float | int, name: str) -> float:
    if value is None or value < 0:
        raise ValidationError(f"{name} cannot be negative, got {value}.")
    return float(value)


def validate_percentage(value: float, name: str) -> float:
    if value < 0 or value > 1:
        raise ValidationError(
            f"{name} must be between 0 and 1 (0% to 100%), got {value}."
        )
    return value


def validate_scenario_mode(mode: str) -> str:
    if mode not in VALID_SCENARIO_MODES:
        raise ValidationError(
            f"Unknown scenario mode: '{mode}'. "
            f"Valid modes: {', '.join(sorted(VALID_SCENARIO_MODES))}"
        )
    return mode


def validate_required_columns(
    df: pd.DataFrame, required: set[str], dataset_name: str
) -> None:
    missing = required - set(df.columns)
    if missing:
        raise ValidationError(
            f"The {dataset_name} dataset is missing required columns: "
            + ", ".join(sorted(missing))
        )


def validate_investment_inputs(
    investment_amount: float,
    new_stations: int,
    new_classic_bikes: int,
    new_ebikes: int,
    analysis_years: int,
) -> None:
    if investment_amount <= 0:
        raise ValidationError("Investment amount must be positive.")
    if new_stations < 0:
        raise ValidationError("Number of new stations cannot be negative.")
    if new_classic_bikes < 0:
        raise ValidationError("Number of new classic bikes cannot be negative.")
    if new_ebikes < 0:
        raise ValidationError("Number of new e-bikes cannot be negative.")
    if new_stations == 0 and new_classic_bikes == 0 and new_ebikes == 0:
        raise ValidationError(
            "At least one of new stations, classic bikes, or e-bikes must be greater than zero."
        )
    if analysis_years <= 0:
        raise ValidationError("Analysis period must be at least 1 year.")


def validate_weights(weights: dict[str, float]) -> None:
    total = sum(weights.values())
    if abs(total - 1.0) > 0.01:
        raise ValidationError(
            f"Opportunity weights must sum to 1.0, got {total:.3f}."
        )
    for name, value in weights.items():
        if value < 0:
            raise ValidationError(f"Weight '{name}' cannot be negative.")
