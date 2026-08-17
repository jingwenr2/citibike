"""Investment Impact — What is the financial case for expansion?"""
from __future__ import annotations

import streamlit as st

from components.cards import compact_number, kpi_row, scenario_card
from components.headers import page_header, section_header, insight_panel
from components.charts import line_chart, bar_chart
from components.styles import CHART_COLORS, apply_layout


def render(nyc_filtered, rev, active_stations, is_demo):
    from backend.services import revenue_service

    page_header(
        "Investment Impact",
        "What is the financial case for Citi Bike expansion?",
        badge="Scenario",
    )

    # ── Current revenue ──
    section_header(
        "Current Citi Bike revenue (estimated)",
        "All values are estimates based on public pricing and trip data.",
    )
    kpi_row([
        {"label": "Membership Revenue", "value": f"${compact_number(rev['membership_revenue'])}"},
        {"label": "Casual Ride Fees", "value": f"${compact_number(rev['casual_ride_revenue'])}"},
        {"label": "E-bike Overage", "value": f"${compact_number(rev['ebike_overage_revenue'])}"},
        {"label": "Sponsorship", "value": f"${compact_number(rev['sponsorship_revenue'])}"},
        {"label": "Total Annual", "value": f"${compact_number(rev['total_estimated_revenue'])}"},
    ])

    total_current_revenue = rev["total_estimated_revenue"]

    # ── Scenario selector ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Expansion scenarios")

    scenarios = {
        "$25M — Targeted": {"stations": 100, "label": "100 stations in high-pressure zones"},
        "$50M — Moderate": {"stations": 250, "label": "250 stations citywide"},
        "$100M — DOT Partnership": {"stations": 500, "label": "500 stations + protected lanes"},
    }

    sc_cols = st.columns(3)
    selected_scenario = None
    for i, (name, cfg) in enumerate(scenarios.items()):
        with sc_cols[i]:
            amount = name.split("—")[0].strip()
            subtitle = name.split("—")[1].strip()
            is_active = (i == 1)  # default to moderate
            scenario_card(subtitle, amount, is_active=is_active, label=cfg["label"])
            if st.button(f"Select {subtitle}", key=f"sc_{i}", width="stretch"):
                selected_scenario = name

    if selected_scenario is None:
        selected_scenario = "$50M — Moderate"

    chosen = scenarios[selected_scenario]
    new_stations = chosen["stations"]

    # ── Expansion math ──
    rev_copy = dict(rev)
    rev_copy["active_stations"] = active_stations
    exp = revenue_service.estimate_expansion_revenue(rev_copy, new_stations=new_stations)

    new_total_revenue = exp["new_total_revenue"]
    new_annual_trips = exp["new_annual_trips"]
    total_install = exp["install_cost"]
    net_annual_profit = exp["net_annual_profit"]
    payback_months = exp["payback_months"]

    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header(f"Impact: {new_stations} new stations")

    kpi_row([
        {"label": "New Annual Revenue", "value": f"${compact_number(new_total_revenue)}"},
        {"label": "New Annual Trips", "value": compact_number(new_annual_trips)},
        {"label": "Installation Cost", "value": f"${compact_number(total_install)}"},
        {"label": "Net Annual Profit", "value": f"${compact_number(net_annual_profit)}"},
        {"label": "Payback Period", "value": f"{payback_months:.0f} months"},
    ])

    # ── Revenue breakdown ──
    rev_col, cost_col = st.columns(2)
    with rev_col:
        section_header("New revenue breakdown")
        import pandas as pd
        rev_data = pd.DataFrame([
            {"Stream": "Member subscriptions", "Revenue": exp["new_member_revenue"]},
            {"Stream": "Casual ride fees", "Revenue": exp["new_casual_revenue"]},
            {"Stream": "E-bike overage fees", "Revenue": exp["new_ebike_revenue"]},
        ])
        import plotly.express as px
        fig_rev = px.bar(
            rev_data, x="Revenue", y="Stream", orientation="h",
            color_discrete_sequence=["#2D7FF9"],
            labels={"Revenue": "Annual revenue ($)", "Stream": ""},
        )
        apply_layout(fig_rev, height=250)
        st.plotly_chart(fig_rev, width="stretch")

    with cost_col:
        section_header("Costs & payback")
        st.metric("One-time installation", f"${total_install:,.0f}")
        st.metric("Annual operations", f"${exp['annual_operating_cost']:,.0f}")
        st.metric("Net profit/year", f"${net_annual_profit:,.0f}")
        growth_pct = new_total_revenue / total_current_revenue * 100 if total_current_revenue else 0
        st.metric("Revenue growth", f"+{growth_pct:.0f}%")

    # ── 5-year projection ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("5-year revenue projection", "Invest vs. do nothing.")

    proj_df, proj_scenarios = revenue_service.revenue_projection(
        total_current_revenue, new_total_revenue
    )
    fig_proj = line_chart(
        proj_df, x="Year", y="Annual Revenue", color="Scenario",
        color_map={
            "Do nothing (3% organic growth)": "#94A3B8",
            "250 stations — Lyft self-funded": "#2D7FF9",
            "500 stations + DOT partnership": "#10B981",
        },
        labels={"Annual Revenue": "Projected annual revenue ($)"},
        title="The cost of doing nothing vs. the return on investing",
        height=420,
    )
    fig_proj.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f")
    st.plotly_chart(fig_proj, width="stretch")

    gap_2031 = proj_scenarios["500 stations + DOT partnership"][-1] - proj_scenarios["Do nothing (3% organic growth)"][-1]
    cumulative_gap = sum(
        b - a for a, b in zip(
            proj_scenarios["Do nothing (3% organic growth)"],
            proj_scenarios["500 stations + DOT partnership"]
        )
    )

    insight_panel(
        f"<strong>By 2031</strong>, the gap between investing and doing nothing is "
        f"<strong>${compact_number(gap_2031)}/year</strong>. Over 5 years, the DOT partnership "
        f"scenario generates <strong>${compact_number(cumulative_gap)} more</strong> than the status quo."
    )

    # ── Government co-investment ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Why government should co-invest")

    pub = revenue_service.estimate_public_benefits(
        new_annual_trips, new_total_revenue, total_install
    )
    gov_cols = st.columns(3)
    with gov_cols[0]:
        st.markdown("**Public health**")
        st.metric("Annual health benefit", f"${pub['health_benefit']:,.0f}")
        st.caption("Each bike trip reduces obesity, heart disease, and diabetes risk.")

    with gov_cols[1]:
        st.markdown("**Congestion & emissions**")
        st.metric("Congestion reduction", f"${pub['congestion_benefit']:,.0f}/yr")
        st.metric("Emissions reduction", f"${pub['emissions_benefit']:,.0f}/yr")

    with gov_cols[2]:
        st.markdown("**Tax revenue & total**")
        st.metric("Additional tax revenue", f"${pub['tax_benefit']:,.0f}/yr")
        st.metric("Total annual public benefit", f"${pub['total_public_benefit']:,.0f}")
        st.caption(f"Government payback: {pub['govt_payback_years']:.1f} years.")

    insight_panel(
        "<strong>Decision rule:</strong> Expansion pays for itself in "
        f"<strong>{payback_months:.0f} months</strong>. After that, it's pure margin. "
        "Government co-investment accelerates payback and unlocks public health, "
        "congestion, and emissions benefits."
    )
