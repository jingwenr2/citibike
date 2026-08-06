"""Investment Strategy — How should Lyft allocate its investment?"""
from __future__ import annotations

import numpy as np
import streamlit as st

from components.cards import compact_number, kpi_row
from components.headers import page_header, section_header, insight_panel
from components.charts import bar_chart
from components.styles import CHART_COLORS, apply_layout


def render(nyc_filtered, mta_opportunity, is_demo):
    page_header(
        "Investment Strategy",
        "How should Lyft allocate its investment?",
        badge="Scenario",
    )

    # ── Inputs ──
    input_col, results_col = st.columns([0.9, 2.1])
    with input_col:
        st.markdown("**Investment geography:** New York City")
        public_budget = st.number_input(
            "Capital budget ($)", min_value=50_000, max_value=20_000_000,
            value=1_000_000, step=50_000, format="%d", key="inv_budget",
        )
        docks_added = st.slider("Docks per station", 4, 40, 16, key="inv_docks")
        cost_per_dock = st.number_input(
            "Cost per dock ($)", min_value=1_000, max_value=50_000,
            value=8_000, step=500, format="%d", key="inv_cost_dock",
        )
        demand_uplift = st.slider("Demand uplift (%)", 5, 60, 20, format="%d%%", key="inv_uplift")
        net_revenue_trip = st.number_input(
            "Net revenue / new trip ($)", min_value=0.0, max_value=20.0,
            value=2.25, step=0.25, key="inv_rev_trip",
        )
        public_value_trip = st.number_input(
            "Public value / trip ($)", min_value=0.0, max_value=30.0,
            value=4.00, step=0.25, key="inv_pub_val",
            help="Congestion, health, and emissions benefit estimate.",
        )
        annual_station_cost = st.number_input(
            "Annual station ops ($)", min_value=0, max_value=250_000,
            value=28_000, step=2_000, format="%d", key="inv_ops",
        )
        analysis_years = st.slider("Analysis period (years)", 3, 15, 5, key="inv_years")
        discount_rate = st.slider("Discount rate (%)", 0, 15, 5, format="%d%%", key="inv_disc")

    # ── Calculations ──
    observed_days = max(1, nyc_filtered["date"].nunique())
    inv_rank = (
        nyc_filtered.groupby(["station_name", "capacity"], as_index=False)["trips"]
        .sum().rename(columns={"trips": "period_trips"})
    )
    if not mta_opportunity.empty:
        inv_rank = inv_rank.merge(
            mta_opportunity[["station_name", "transit_opportunity_score"]],
            on="station_name", how="left",
        )
    else:
        inv_rank["transit_opportunity_score"] = np.nan

    inv_rank["daily_trips"] = inv_rank["period_trips"] / observed_days
    inv_rank["new_annual_trips"] = inv_rank["daily_trips"] * 365 * demand_uplift / 100
    inv_rank["capital_cost"] = docks_added * cost_per_dock
    inv_rank["annual_operating_return"] = (
        inv_rank["new_annual_trips"] * net_revenue_trip - annual_station_cost
    )
    inv_rank["annual_public_benefit"] = inv_rank["new_annual_trips"] * public_value_trip
    discount = discount_rate / 100
    annuity = sum(1 / ((1 + discount) ** y) for y in range(1, analysis_years + 1))
    inv_rank["five_year_fiscal_npv"] = inv_rank["annual_operating_return"] * annuity - inv_rank["capital_cost"]
    inv_rank["public_npv"] = (
        (inv_rank["annual_operating_return"] + inv_rank["annual_public_benefit"]) * annuity
        - inv_rank["capital_cost"]
    )
    inv_rank["public_benefit_cost_ratio"] = (
        (inv_rank["annual_operating_return"] + inv_rank["annual_public_benefit"]) * annuity
        / inv_rank["capital_cost"]
    )
    inv_rank["fiscal_payback_years"] = np.where(
        inv_rank["annual_operating_return"] > 0,
        inv_rank["capital_cost"] / inv_rank["annual_operating_return"], np.nan,
    )
    inv_rank = inv_rank.sort_values(["public_npv", "transit_opportunity_score"], ascending=[False, False])

    max_projects = int(public_budget // (docks_added * cost_per_dock))
    inv_rank["recommended"] = False
    rec_idx = inv_rank[inv_rank["public_npv"] > 0].head(max_projects).index
    inv_rank.loc[rec_idx, "recommended"] = True

    recommended = inv_rank[inv_rank["recommended"]]
    total_capital = recommended["capital_cost"].sum()
    public_npv = recommended["public_npv"].sum()
    new_trips = recommended["new_annual_trips"].sum()
    bcr = (public_npv + total_capital) / total_capital if total_capital else 0

    with results_col:
        kpi_row([
            {"label": "Recommended Projects", "value": f"{len(recommended)}"},
            {"label": "Capital Deployed", "value": f"${compact_number(total_capital)}"},
            {"label": "New Annual Trips", "value": compact_number(new_trips)},
            {"label": "Benefit-Cost Ratio", "value": f"{bcr:.2f}x"},
        ])

        section_header("Top stations by public NPV")
        top10 = inv_rank.head(10).copy()
        fig = bar_chart(
            top10, x="public_npv", y="station_name", color="recommended",
            orientation="h",
            color_map={True: "#FF00BF", False: "#CBD5E1"},
            labels={"public_npv": f"{analysis_years}-yr public NPV ($)", "station_name": "", "recommended": "Funded"},
            height=400,
        )
        fig.update_layout(yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig, use_container_width=True)

    # ── 3-phase roadmap ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Implementation roadmap")
    phase_cols = st.columns(3)
    with phase_cols[0]:
        st.markdown("**Phase 1 — 0-6 months**")
        st.markdown("High-demand transit corridors")
        st.caption("Target the top-pressure stations near major subway hubs. Focus on dock capacity and e-bike fleet.")
    with phase_cols[1]:
        st.markdown("**Phase 2 — 6-18 months**")
        st.markdown("Underserved neighborhood expansion")
        st.caption("Extend coverage to outer-borough areas where MTA transit gaps create demand but Citi Bike is absent.")
    with phase_cols[2]:
        st.markdown("**Phase 3 — 18-36 months**")
        st.markdown("Network optimization")
        st.caption("Rebalance fleet distribution, upgrade charging infrastructure, and optimize station density.")

    # ── Full table ──
    with st.expander("Full project-level table"):
        st.dataframe(
            inv_rank[[
                "recommended", "station_name", "daily_trips", "new_annual_trips",
                "capital_cost", "annual_operating_return", "fiscal_payback_years",
                "five_year_fiscal_npv", "public_npv", "public_benefit_cost_ratio",
                "transit_opportunity_score",
            ]],
            hide_index=True, use_container_width=True,
            column_config={
                "recommended": st.column_config.CheckboxColumn("Fund"),
                "station_name": "Station",
                "daily_trips": st.column_config.NumberColumn("Daily demand", format="%.0f"),
                "new_annual_trips": st.column_config.NumberColumn("New trips/yr", format="%.0f"),
                "capital_cost": st.column_config.NumberColumn("Capital", format="$%.0f"),
                "annual_operating_return": st.column_config.NumberColumn("Annual return", format="$%.0f"),
                "fiscal_payback_years": st.column_config.NumberColumn("Payback", format="%.1f yr"),
                "five_year_fiscal_npv": st.column_config.NumberColumn("Fiscal NPV", format="$%.0f"),
                "public_npv": st.column_config.NumberColumn("Public NPV", format="$%.0f"),
                "public_benefit_cost_ratio": st.column_config.NumberColumn("BCR", format="%.2fx"),
                "transit_opportunity_score": st.column_config.ProgressColumn("MTA opp.", min_value=0, max_value=100, format="%.0f"),
            },
        )

    insight_panel(
        "<strong>Decision rule:</strong> Prioritize positive public NPV and benefit-cost ratio "
        "above 1.0x, then confirm annual operating support fits the budget. "
        "Fiscal return is a sustainability constraint, not the sole goal."
    )
