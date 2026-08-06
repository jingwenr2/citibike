"""Network Performance — How is the current Citi Bike network performing?"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import compact_number, kpi_row
from components.headers import page_header, section_header, insight_panel
from components.charts import line_chart, dual_donut, bar_chart, heatmap
from components.styles import RIDER_COLORS, BIKE_COLORS, PRESSURE_COLORS

DAY_ORDER = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]


def render(nyc_filtered, filtered, hourly, smoothing, is_demo, demand_service):
    page_header(
        "Network Performance",
        "How is the current Citi Bike network performing?",
        badge="Historical",
    )

    # ── KPIs ──
    total = demand_service.total_trips(nyc_filtered)
    avg_daily = demand_service.average_daily_trips(nyc_filtered)
    active_stations = nyc_filtered["station_name"].nunique()
    electric_share = demand_service.electric_bike_share(nyc_filtered)
    peak_share = demand_service.peak_hour_share(hourly)

    kpi_row([
        {"label": "Total Trips", "value": compact_number(total)},
        {"label": "Avg Daily Demand", "value": compact_number(avg_daily)},
        {"label": "Active Stations", "value": f"{active_stations:,}"},
        {"label": "E-bike Share", "value": f"{electric_share:.0%}"},
        {"label": "Peak Hour Share", "value": f"{peak_share:.0%}"},
    ])

    # ── Ridership trend ──
    section_header("NYC demand over time", "Member vs. casual ridership, smoothed.")
    trend = demand_service.daily_demand_trend(nyc_filtered, smoothing=smoothing)
    fig_trend = line_chart(
        trend, x="date", y="smoothed_trips", color="rider_type",
        color_map=RIDER_COLORS,
        labels={"smoothed_trips": "Trips", "date": "", "rider_type": "Rider"},
        title="Member ridership dominates but casual is growing",
        height=380,
    )
    st.plotly_chart(fig_trend, use_container_width=True)

    # ── Rider + bike mix ──
    mix_col1, mix_col2 = st.columns(2)
    rider_mix = demand_service.member_casual_split(nyc_filtered)
    bike_mix = demand_service.bike_type_split(nyc_filtered)

    with mix_col1:
        section_header("Rider mix")
        fig_mix = dual_donut(
            rider_mix["rider_type"].tolist(), rider_mix["trips"].tolist(),
            [RIDER_COLORS.get(r, "#94A3B8") for r in rider_mix["rider_type"]],
            "Member vs. Casual",
            bike_mix["bike_type"].tolist(), bike_mix["trips"].tolist(),
            [BIKE_COLORS.get(b, "#94A3B8") for b in bike_mix["bike_type"]],
            "Electric vs. Classic",
            height=340,
        )
        st.plotly_chart(fig_mix, use_container_width=True)

    with mix_col2:
        section_header("Weekly rhythm by bike type")
        weekday = demand_service.weekday_bike_type_demand(nyc_filtered)
        if not weekday.empty:
            fig_wd = bar_chart(
                weekday, x="weekday", y="trips", color="bike_type",
                color_map=BIKE_COLORS, barmode="group",
                labels={"trips": "Avg trips", "weekday": "", "bike_type": ""},
                title="Weekday commuters prefer e-bikes",
                height=340,
            )
            st.plotly_chart(fig_wd, use_container_width=True)

    # ── Heatmap ──
    section_header(
        "Peak demand by hour and day",
        f"{peak_share:.0%} of trips happen during the six peak rush hours.",
    )
    day_counts = hourly.drop_duplicates(["date", "day_name"]).groupby("day_name")["date"].nunique()
    hourly_pivot = hourly.groupby(["hour", "day_name"], as_index=False)["trips"].sum()
    hourly_pivot["day_count"] = hourly_pivot["day_name"].map(day_counts).clip(lower=1)
    hourly_pivot["avg_trips"] = hourly_pivot["trips"] / hourly_pivot["day_count"]
    hourly_days = [d for d in DAY_ORDER if d in hourly_pivot["day_name"].unique()]
    hourly_wide = (
        hourly_pivot.pivot(index="hour", columns="day_name", values="avg_trips")
        .reindex(columns=hourly_days).reindex(index=range(24)).fillna(0)
    )
    fig_hm = heatmap(
        hourly_wide.values,
        hourly_wide.columns.tolist(),
        hourly_wide.index.tolist(),
        height=480,
    )
    st.plotly_chart(fig_hm, use_container_width=True)

    sample_dates = pd.to_datetime(hourly["date"])
    st.caption(
        "Pink dashed lines mark peak hours: 7-10am and 5-8pm on weekdays, "
        "12-4pm on weekends. Weekday and weekend columns are gapped apart. "
        f"Based on {sample_dates.min():%b %Y}\u2013{sample_dates.max():%b %Y} hourly data. "
        "Independent of sidebar date filters."
    )

    # ── Station pressure ──
    section_header("Station capacity pressure", "Average daily trips / dock capacity.")
    pressure = demand_service.station_pressure_categories(nyc_filtered)
    if not pressure.empty:
        strained = pressure[pressure["pressure"] >= 1.0]
        critical = pressure[pressure["pressure"] >= 1.5]

        p_cols = st.columns(3)
        p_cols[0].metric("Total stations scored", f"{len(pressure):,}")
        p_cols[1].metric("At or above capacity", f"{len(strained):,}", f"{len(strained)/len(pressure)*100:.0f}% of network")
        p_cols[2].metric("Critical (>1.5x)", f"{len(critical):,}")

        insight_panel(
            f"<strong>{len(strained):,} stations</strong> are running at or above capacity. "
            "Every empty dock is a lost ride. Expansion here directly converts latent demand into revenue."
        )
