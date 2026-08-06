"""Demand Forecast — Where and when is future demand expected to grow?"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import streamlit as st

from components.cards import compact_number, kpi_row
from components.headers import page_header, section_header, insight_panel
from components.charts import forecast_chart
from components.styles import FORECAST_PURPLE


def render(nyc_filtered, is_demo):
    page_header(
        "Demand Forecast",
        "Where and when is future demand expected to grow?",
        badge="Forecast",
    )

    # ── Model metrics ──
    metrics_path = None
    try:
        from backend.utils.paths import FORECAST_METRICS_PATH
        metrics_path = FORECAST_METRICS_PATH
    except ImportError:
        pass

    model_metrics = None
    if metrics_path and metrics_path.exists():
        with open(metrics_path) as f:
            all_metrics = json.load(f)
        for m in all_metrics:
            if m.get("city") == "New York City":
                model_metrics = m
                break

    if model_metrics:
        xgb = model_metrics.get("xgboost", {})
        n_features = model_metrics.get("n_features", 21)
        test_days = model_metrics.get("test_station_days", 0)
        naive = model_metrics.get("seasonal_naive", {})
        improvement_mae = 0
        if naive.get("MAE") and xgb.get("MAE"):
            improvement_mae = (naive["MAE"] - xgb["MAE"]) / naive["MAE"] * 100

        kpi_row([
            {"label": "Model MAE", "value": f"{xgb.get('MAE', '—')} trips"},
            {"label": "Model WAPE", "value": f"{xgb.get('WAPE', '—'):.0%}" if isinstance(xgb.get('WAPE'), (int, float)) else "—"},
            {"label": "vs Naive Baseline", "value": f"+{improvement_mae:.0f}% better"},
            {"label": "Features", "value": str(n_features)},
            {"label": "Test Rows", "value": compact_number(test_days)},
        ])

        st.markdown("")
        insight_panel(
            f"<strong>XGBoost model</strong> predicts daily station-level demand with "
            f"MAE of {xgb.get('MAE', '?')} trips, {improvement_mae:.0f}% better than "
            "the seasonal naive baseline. Uses weather deviations, MTA transit data, "
            "and temporal lag features."
        )
    else:
        st.info("Model metrics not available. Run `python backend/demand_forecast_xgboost.py` to train.")

    # ── Interactive scenario ──
    section_header(
        "Interactive demand scenario",
        "Adjust assumptions to explore a planning scenario.",
    )

    control_col, chart_col = st.columns([0.8, 2.2])
    with control_col:
        st.markdown("**Forecast geography:** New York City")
        horizon = st.slider("Forecast horizon (days)", 7, 60, 30, key="fc_horizon")
        weather_effect = st.slider("Weather effect", -30, 30, 0, format="%d%%", key="fc_weather")
        event_effect = st.slider("Event / policy effect", -20, 40, 0, format="%d%%", key="fc_event")

    city_history = (
        nyc_filtered.groupby("date", as_index=False)["trips"].sum().sort_values("date")
    )
    recent = city_history.tail(min(28, len(city_history)))
    baseline = recent["trips"].mean()
    forecast_dates = pd.date_range(
        city_history["date"].max() + pd.Timedelta(days=1), periods=horizon
    )
    weekday_factors = (
        city_history.assign(weekday=city_history["date"].dt.dayofweek)
        .groupby("weekday")["trips"].mean()
        / city_history["trips"].mean()
    )
    scenario_factor = (1 + weather_effect / 100) * (1 + event_effect / 100)
    forecast_values = [
        baseline * weekday_factors.get(date.dayofweek, 1.0) * scenario_factor
        for date in forecast_dates
    ]
    forecast_frame = pd.DataFrame({"date": forecast_dates, "forecast": forecast_values})
    forecast_frame["lower"] = forecast_frame["forecast"] * 0.86
    forecast_frame["upper"] = forecast_frame["forecast"] * 1.14

    with chart_col:
        fig = forecast_chart(
            city_history.tail(60), forecast_frame,
            title="Historical demand with scenario projection",
        )
        st.plotly_chart(fig, use_container_width=True)

        projected = forecast_frame["forecast"].sum()
        base_projected = baseline * horizon
        st.metric(
            f"Projected {horizon}-day trips",
            compact_number(projected),
            f"{projected / base_projected - 1:+.1%} vs recent baseline",
        )

    # ── Model details (collapsed) ──
    with st.expander("Model methodology"):
        st.markdown("""
**XGBoost v3 — 21 features**

| Category | Features |
|----------|----------|
| Station | lat, lon, capacity |
| Calendar | day_of_week, month, is_weekend, is_holiday |
| Lag/rolling | lag_1d, lag_7d, roll_mean_7d, roll_mean_28d, roll_std_7d |
| Ridership | electric_share, member_share |
| MTA transit | mta_daily_riders, mta_delay_rate, nearest_mta_distance_km |
| Hourly | peak_hour_share |
| Weather | temp_deviation, precip_deviation, is_bad_weather |

**Training**: Chronological split — last 60 days held out. 1.44M training rows across 2,464 stations.

**Weather approach**: Uses deviation from monthly climate normals (not raw values) so the model
learns that the same temperature has different impact depending on the time of year.
        """)
