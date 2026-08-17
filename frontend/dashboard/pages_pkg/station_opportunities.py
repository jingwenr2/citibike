"""Station Opportunities — Which stations should receive additional investment?"""
from __future__ import annotations

import streamlit as st

from components.cards import compact_number, kpi_row, recommendation_card
from components.headers import page_header, section_header, insight_panel
from components.charts import scatter_map_chart
from components.styles import CITY_COLORS


def render(nyc_filtered, mta_opportunity, station_summary_df, demand_service):
    page_header(
        "Station Opportunities",
        "Which stations or neighborhoods should receive additional investment?",
        badge="Historical",
    )

    if station_summary_df.empty:
        st.info("No station data available for the current filters.")
        return

    # ── KPIs ──
    pressure_df = demand_service.station_pressure_categories(nyc_filtered)
    strained = pressure_df[pressure_df["pressure"] >= 1.0] if not pressure_df.empty else pressure_df
    critical = pressure_df[pressure_df["pressure"] >= 1.5] if not pressure_df.empty else pressure_df

    kpi_row([
        {"label": "Stations Analyzed", "value": f"{len(station_summary_df):,}"},
        {"label": "At or Above Capacity", "value": f"{len(strained):,}"},
        {"label": "Critical Pressure", "value": f"{len(critical):,}"},
    ])

    # ── Map + recommendations ──
    map_col, rec_col = st.columns([1.6, 1])

    with map_col:
        section_header("Station demand map")
        fig = scatter_map_chart(
            station_summary_df,
            color="city",
            color_map=CITY_COLORS,
            hover_data={
                "trips": ":,.0f",
                "average_daily": ":,.0f",
                "pressure": ":.1f",
                "lat": False, "lon": False, "marker_size": False,
            },
            height=500,
        )
        st.plotly_chart(fig, width="stretch")

    with rec_col:
        section_header("Top recommendations")

        ranked = station_summary_df.dropna(subset=["pressure"]).sort_values("pressure", ascending=False)
        top_stations = ranked.head(8)

        for i, (_, row) in enumerate(top_stations.iterrows()):
            pressure = row.get("pressure", 0)
            if pressure >= 1.5:
                action = "Expand dock capacity urgently"
                reason = f"Running at {pressure:.1f}x capacity with {row['average_daily']:.0f} avg daily trips."
            elif pressure >= 1.0:
                action = "Add more bikes and docks"
                reason = f"At {pressure:.1f}x capacity. Demand consistently exceeds supply."
            else:
                action = "Monitor and consider e-bike fleet"
                reason = f"Pressure at {pressure:.1f}x. Opportunity to increase e-bike share."

            recommendation_card(
                station=row["station_name"],
                score=min(99, pressure * 40),
                action=action,
                reason=reason,
                is_recommended=(i < 3),
            )

    # ── Station inspector ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Inspect a station")
    station_options = sorted(nyc_filtered["station_name"].unique())
    selected = st.selectbox("Station", station_options, key="opp_station")
    station_daily = (
        nyc_filtered[nyc_filtered["station_name"] == selected]
        .groupby("date", as_index=False)["trips"].sum()
    )
    station_daily["7-day average"] = station_daily["trips"].rolling(7, min_periods=1).mean()
    import plotly.express as px
    from components.styles import apply_layout
    fig_s = px.area(
        station_daily, x="date", y="7-day average",
        labels={"7-day average": "Trips", "date": ""},
        color_discrete_sequence=["#2D7FF9"],
    )
    apply_layout(fig_s, height=300)
    st.plotly_chart(fig_s, width="stretch")

    insight_panel(
        "<strong>Investment priority:</strong> Focus on stations where pressure exceeds 1.0x "
        "capacity. These are locations where demand is proven but supply is constrained — "
        "expansion here converts latent demand directly into revenue."
    )
