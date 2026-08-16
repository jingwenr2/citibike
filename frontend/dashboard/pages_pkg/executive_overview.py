"""Executive Overview — Where Should Lyft Invest Next?"""
from __future__ import annotations

import streamlit as st

from components.cards import compact_number, kpi_row, finding_card
from components.headers import hero_section, insight_panel
from components.charts import scatter_map_chart
from components.styles import CITY_COLORS


def render(nyc_filtered, mta_opportunity, station_summary_df, rev, delta, is_demo, demand_service):
    if is_demo:
        st.markdown(
            '<span class="demo-pill">DEMO DATA</span> '
            "Using built-in demonstration data. Place parquet files in "
            "<code>data/processed/</code> for real results.",
            unsafe_allow_html=True,
        )

    hero_section(
        eyebrow="Citi Bike Growth Intelligence",
        title="Where Should Lyft Invest Next?",
        body=(
            "Citi Bike demand is growing, but network coverage and station capacity "
            "remain uneven across New York City. This platform identifies where "
            "expansion could create the greatest mobility and business impact."
        ),
    )

    # ── KPI row ──
    active_stations = nyc_filtered["station_name"].nunique()
    electric_share = demand_service.electric_bike_share(nyc_filtered)
    avg_daily = demand_service.average_daily_trips(nyc_filtered)
    total = demand_service.total_trips(nyc_filtered)

    top_area = ""
    if not mta_opportunity.empty:
        top_row = mta_opportunity.sort_values("transit_opportunity_score", ascending=False).iloc[0]
        top_area = top_row.get("neighborhood", top_row.get("station_name", ""))

    kpi_row([
        {"label": "Total Trips", "value": compact_number(total)},
        {"label": "Avg Daily Demand", "value": compact_number(avg_daily), "delta": f"{delta:+.1%} vs prior period"},
        {"label": "Active Stations", "value": f"{active_stations:,}"},
        {"label": "E-bike Share", "value": f"{electric_share:.0%}"},
        {"label": "Top Opportunity Area", "value": top_area or "—"},
    ])

    st.markdown("")

    # ── Two-column: map + findings ──
    map_col, findings_col = st.columns([1.8, 1])

    with map_col:
        if not station_summary_df.empty:
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
                height=460,
            )
            st.plotly_chart(fig, width="stretch")
            st.caption("Station size = trip volume. Color = system.")

    with findings_col:
        st.markdown("#### Key Findings")
        finding_card(
            1, "Demand exceeds supply",
            "Many high-traffic stations regularly run out of bikes or docks, "
            "turning away potential riders.",
        )
        finding_card(
            2, "Transit gaps create opportunity",
            "Neighborhoods with high subway ridership and frequent delays "
            "are underserved by Citi Bike.",
        )
        finding_card(
            3, "E-bikes drive growth",
            f"Electric bikes now account for {electric_share:.0%} of trips and "
            "generate the highest per-trip revenue.",
        )

        if rev:
            total_rev = rev.get("total_estimated_revenue", 0)
            if total_rev:
                finding_card(
                    4, "Revenue engine",
                    f"Estimated annual revenue: ${compact_number(total_rev)}. "
                    "Expansion pays for itself within months.",
                )

    insight_panel(
        "<strong>Recommendation:</strong> Prioritize expansion in outer-borough "
        "transit corridors where demand is growing fastest and current Citi Bike "
        "coverage remains limited."
    )
