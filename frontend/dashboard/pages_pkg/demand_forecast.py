"""Demand Forecast — Where and when is future demand expected to grow?"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from components.cards import compact_number, kpi_row
from components.headers import page_header, section_header, insight_panel
from components.charts import forecast_chart
from components.styles import (
    FORECAST_PURPLE,
    HISTORICAL_BLUE,
    POSITIVE_GREEN,
    LIGHT_GRAY,
    TEXT_PRIMARY,
    apply_layout,
)


def _load_json(path):
    if path and path.exists():
        with open(path) as f:
            return json.load(f)
    return None


def _load_parquet(path):
    if path and path.exists():
        return pd.read_parquet(path)
    return None


def render(nyc_filtered, is_demo):
    page_header(
        "Demand Forecast",
        "Where and when is future demand expected to grow?",
        badge="Forecast",
    )

    # ── Resolve paths ──
    metrics_path = predictions_path = importance_path = None
    try:
        from backend.utils.paths import (
            FORECAST_METRICS_PATH,
            FORECAST_PREDICTIONS_PATH,
            FEATURE_IMPORTANCE_PATH,
        )
        metrics_path = FORECAST_METRICS_PATH
        predictions_path = FORECAST_PREDICTIONS_PATH
        importance_path = FEATURE_IMPORTANCE_PATH
    except ImportError:
        pass

    # ── Load artifacts ──
    model_metrics = None
    all_metrics = _load_json(metrics_path)
    if all_metrics:
        for m in all_metrics:
            if m.get("city") == "New York City":
                model_metrics = m
                break

    predictions_df = _load_parquet(predictions_path)
    importance_data = _load_json(importance_path)

    # ── Model KPIs ──
    if model_metrics:
        xgb = model_metrics.get("xgboost", {})
        n_features = model_metrics.get("n_features", 23)
        test_days = model_metrics.get("test_station_days", 0)
        naive = model_metrics.get("seasonal_naive", {})
        cv_avg = model_metrics.get("cv_avg", {})
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

        cv_note = ""
        if cv_avg:
            cv_note = (
                f" Cross-validated MAE: {cv_avg.get('MAE', '?')} trips "
                f"(3-fold time-series CV)."
            )

        insight_panel(
            f"<strong>XGBoost model</strong> predicts daily station-level demand with "
            f"MAE of {xgb.get('MAE', '?')} trips, {improvement_mae:.0f}% better than "
            "the seasonal naive baseline. Uses weather deviations, MTA transit data, "
            f"and temporal lag features.{cv_note}"
        )
    else:
        st.info("Model metrics not available. Run `python backend/demand_forecast_xgboost.py` to train.")

    # ── Feature importance chart ──
    if importance_data:
        section_header(
            "Feature importance",
            "Which features drive the model's predictions most?",
        )
        imp_df = (
            pd.DataFrame(list(importance_data.items()), columns=["feature", "importance"])
            .sort_values("importance", ascending=True)
        )
        top_n = imp_df.tail(15)

        colors = [
            FORECAST_PURPLE if v >= top_n["importance"].quantile(0.75)
            else HISTORICAL_BLUE
            for v in top_n["importance"]
        ]
        fig_imp = go.Figure(go.Bar(
            x=top_n["importance"],
            y=top_n["feature"].str.replace("_", " ").str.title(),
            orientation="h",
            marker_color=colors,
        ))
        fig_imp = apply_layout(
            fig_imp, height=420,
            title="Top features driving demand predictions",
            xaxis_title="Importance",
            yaxis_title="",
        )
        st.plotly_chart(fig_imp, use_container_width=True)

    # ── Actual vs Predicted chart ──
    if predictions_df is not None and not predictions_df.empty:
        section_header(
            "Model accuracy",
            "How well do predictions match actual demand?",
        )

        act_vs_pred_tab, residual_tab = st.tabs(["Actual vs Predicted", "Residual distribution"])

        with act_vs_pred_tab:
            daily_agg = (
                predictions_df.groupby("date", as_index=False)
                .agg(actual=("trips", "sum"), predicted=("predicted", "sum"))
                .sort_values("date")
            )
            fig_avp = go.Figure()
            fig_avp.add_trace(go.Scatter(
                x=daily_agg["date"], y=daily_agg["actual"],
                name="Actual", line=dict(color=HISTORICAL_BLUE, width=2),
            ))
            fig_avp.add_trace(go.Scatter(
                x=daily_agg["date"], y=daily_agg["predicted"],
                name="Predicted", line=dict(color=FORECAST_PURPLE, width=2, dash="dot"),
            ))
            fig_avp = apply_layout(
                fig_avp, height=400,
                title="Daily total: actual vs predicted trips (test set)",
                xaxis_title="", yaxis_title="Trips",
            )
            st.plotly_chart(fig_avp, use_container_width=True)

            corr = daily_agg["actual"].corr(daily_agg["predicted"])
            st.caption(f"Daily correlation: **{corr:.3f}**")

        with residual_tab:
            fig_res = px.histogram(
                predictions_df, x="residual", nbins=80,
                title="Residual distribution (actual - predicted)",
                labels={"residual": "Residual (trips)", "count": "Station-days"},
                color_discrete_sequence=[FORECAST_PURPLE],
            )
            fig_res = apply_layout(fig_res, height=380, title="Residual distribution (actual - predicted)")
            st.plotly_chart(fig_res, use_container_width=True)

            mean_res = predictions_df["residual"].mean()
            std_res = predictions_df["residual"].std()
            st.caption(f"Mean residual: **{mean_res:.2f}** | Std: **{std_res:.2f}**")

    # ── Station-level forecast rankings ──
    if predictions_df is not None and not predictions_df.empty:
        section_header(
            "Station-level demand forecast",
            "Which stations have the highest predicted demand?",
        )

        station_agg = (
            predictions_df.groupby("station_name", as_index=False)
            .agg(
                avg_actual=("trips", "mean"),
                avg_predicted=("predicted", "mean"),
                total_predicted=("predicted", "sum"),
                lat=("lat", "first"),
                lon=("lon", "first"),
            )
        )
        station_agg["gap"] = station_agg["avg_predicted"] - station_agg["avg_actual"]
        station_agg["gap_pct"] = (
            (station_agg["gap"] / station_agg["avg_actual"].replace(0, np.nan)) * 100
        ).fillna(0)

        top_col, bottom_col = st.columns(2)

        with top_col:
            st.markdown("**Highest predicted demand**")
            top_stations = station_agg.nlargest(10, "avg_predicted")
            for _, row in top_stations.iterrows():
                delta_str = f"{row['gap']:+.1f} trips/day vs actual"
                st.metric(
                    row["station_name"][:40],
                    f"{row['avg_predicted']:.0f} trips/day",
                    delta_str,
                )

        with bottom_col:
            st.markdown("**Largest growth signals** (predicted > actual)")
            growth_stations = (
                station_agg[station_agg["avg_actual"] >= 5]
                .nlargest(10, "gap_pct")
            )
            for _, row in growth_stations.iterrows():
                st.metric(
                    row["station_name"][:40],
                    f"{row['avg_predicted']:.0f} trips/day",
                    f"+{row['gap_pct']:.0f}% above current",
                )

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

    # Use model-learned weekday patterns from predictions if available
    if predictions_df is not None and not predictions_df.empty:
        pred_daily = (
            predictions_df.assign(weekday=predictions_df["date"].dt.dayofweek)
            .groupby("weekday")["predicted"].mean()
        )
        pred_mean = pred_daily.mean()
        weekday_factors = pred_daily / pred_mean if pred_mean > 0 else pred_daily * 0 + 1
    else:
        weekday_factors = (
            city_history.assign(weekday=city_history["date"].dt.dayofweek)
            .groupby("weekday")["trips"].mean()
            / city_history["trips"].mean()
        )

    forecast_dates = pd.date_range(
        city_history["date"].max() + pd.Timedelta(days=1), periods=horizon
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
**XGBoost v4 — 23 features (with early stopping & time-series CV)**

| Category | Features |
|----------|----------|
| Station | lat, lon, capacity |
| Calendar | day_of_week, month, quarter, year, is_weekend, is_holiday |
| Lag/rolling | lag_1d, lag_7d, roll_mean_7d, roll_mean_28d, roll_std_7d |
| Ridership | electric_share, member_share |
| MTA transit | mta_daily_riders, mta_delay_rate, nearest_mta_distance_km |
| Hourly | peak_hour_share |
| Weather | temp_deviation, precip_deviation, is_bad_weather |

**Training**: Chronological split — last 60 days held out. Early stopping with 30-round patience on 20% eval holdout. 3-fold time-series cross-validation for robust metrics.

**Weather approach**: Uses deviation from monthly climate normals (not raw values) so the model
learns that the same temperature has different impact depending on the time of year.
        """)
