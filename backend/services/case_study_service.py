"""Case study service for external bike-share success stories.

Loads and validates structured case study data for the dashboard's
"Evidence from Other Cities" feature. New York City (Citi Bike) is
excluded because it is the target market.

This service does NOT train models or compare cities directly.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from backend.utils.paths import CASE_STUDIES_PATH


def load_case_studies(path: Path | None = None) -> list[dict[str, Any]]:
    path = path or CASE_STUDIES_PATH
    if not path.exists():
        return []
    with open(path) as f:
        data = json.load(f)
    studies = data.get("case_studies", [])
    return [_validate_case_study(s) for s in studies]


def _validate_case_study(study: dict[str, Any]) -> dict[str, Any]:
    """Ensure required fields exist; replace missing optional fields with None."""
    required = {"city", "system_name", "main_lesson"}
    for field in required:
        if field not in study or not study[field]:
            raise ValueError(
                f"Case study missing required field: '{field}'"
            )

    optional_fields = [
        "operator", "government_involvement", "investment_action",
        "ridership_result", "fleet_growth", "station_growth",
        "financial_result", "major_milestone", "source_name",
        "source_url", "source_date", "last_verified",
    ]
    for field in optional_fields:
        if field not in study:
            study[field] = None

    return study


def get_case_study_summary() -> list[dict[str, Any]]:
    """Return a compact summary of all case studies for display."""
    studies = load_case_studies()
    return [
        {
            "city": s["city"],
            "system_name": s["system_name"],
            "government_involvement": s["government_involvement"],
            "main_lesson": s["main_lesson"],
            "financial_result": s.get("financial_result") or "Not publicly available",
            "source_url": s.get("source_url"),
        }
        for s in studies
    ]
