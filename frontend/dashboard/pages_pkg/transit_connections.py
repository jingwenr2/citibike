"""Transit Connections — Where could Citi Bike improve first/last-mile transportation?"""
from __future__ import annotations

import streamlit as st

from components.cards import compact_number, kpi_row
from components.headers import page_header, section_header, insight_panel
from components.charts import opportunity_scatter


def render(mta_opportunity, mta_signal, nyc_filtered, is_demo):
    page_header(
        "Transit Connections",
        "Where could Citi Bike improve first-mile and last-mile transportation?",
        badge="Historical",
    )

    if bool(mta_signal["mta_is_demo"].all()):
        st.markdown(
            '<span class="demo-pill">DEMO DATA</span> '
            "MTA values are demonstration data.",
            unsafe_allow_html=True,
        )

    if mta_opportunity.empty:
        st.info("No Citi Bike stations match the current MTA opportunity table.")
        return

    # ── KPIs ──
    top5 = mta_opportunity.nlargest(5, "transit_opportunity_score")
    avg_score = mta_opportunity["transit_opportunity_score"].mean()
    high_delay = mta_opportunity[mta_opportunity["mta_delay_rate"] > 0.05]

    kpi_row([
        {"label": "Stations Scored", "value": f"{len(mta_opportunity):,}"},
        {"label": "Avg Opportunity Score", "value": f"{avg_score:.0f}/100"},
        {"label": "High-Delay Neighborhoods", "value": f"{len(high_delay):,}"},
        {"label": "Top Opportunity", "value": top5.iloc[0].get("neighborhood", "—") if len(top5) > 0 else "—"},
    ])

    # ── Scatter chart ──
    section_header(
        "MTA ridership vs. Citi Bike demand",
        "High subway ridership with low bike-share demand signals an investment opportunity.",
    )
    fig = opportunity_scatter(
        mta_opportunity,
        title="Stations in the upper-left quadrant are underserved by Citi Bike",
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Top opportunities ──
    section_header("Highest-opportunity stations")
    st.dataframe(
        mta_opportunity.sort_values("transit_opportunity_score", ascending=False)[
            ["neighborhood", "station_name", "mta_daily_riders",
             "mta_delay_rate", "bike_daily_trips", "transit_opportunity_score"]
        ].head(15),
        hide_index=True,
        use_container_width=True,
        column_config={
            "neighborhood": "Neighborhood",
            "station_name": "Station",
            "mta_daily_riders": st.column_config.NumberColumn("MTA riders/day", format="%d"),
            "mta_delay_rate": st.column_config.NumberColumn("Delay rate", format="percent"),
            "bike_daily_trips": st.column_config.NumberColumn("Bike trips/day", format="%.0f"),
            "transit_opportunity_score": st.column_config.ProgressColumn(
                "Opportunity", min_value=0, max_value=100, format="%.0f"
            ),
        },
    )

    if not high_delay.empty:
        avg_delay = high_delay["mta_delay_rate"].mean()
        total_riders = high_delay["mta_daily_riders"].sum()
        insight_panel(
            f"<strong>{len(high_delay)} neighborhoods</strong> have subway delay rates "
            f"above 5%, affecting <strong>{total_riders:,.0f} daily MTA riders</strong>. "
            "These riders are the primary adoption target for Citi Bike expansion."
        )
