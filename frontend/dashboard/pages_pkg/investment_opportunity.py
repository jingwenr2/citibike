"""Investment Opportunity — If Lyft invests in expanding Citi Bike, what could happen?

An investor-facing pitch page, not a technical dashboard: storytelling backed by
data rather than tables. Distinct from Investment Strategy (the technical planner)
and Investment Impact (the revenue math) — this page is meant to be opened live
in front of Lyft executives/investors.
"""
from __future__ import annotations

import pandas as pd
import streamlit as st

from components.cards import compact_number, kpi_row, scenario_card, case_study_card, finding_card
from components.headers import hero_section, section_header, insight_panel, flow_diagram, closing_banner
from components.charts import bar_chart

INVESTMENT_TIERS = {
    "Small Expansion": {
        "amount": "$25M", "investment_amount": 25_000_000,
        "new_stations": 250, "new_classic_bikes": 3_500, "new_ebikes": 1_500,
    },
    "Medium Expansion": {
        "amount": "$50M", "investment_amount": 50_000_000,
        "new_stations": 500, "new_classic_bikes": 7_000, "new_ebikes": 3_000,
    },
    "Major Expansion": {
        "amount": "$100M", "investment_amount": 100_000_000,
        "new_stations": 1_000, "new_classic_bikes": 14_000, "new_ebikes": 6_000,
    },
}

EVIDENCE_CITIES = {"San Francisco", "Paris", "London", "Montreal", "Washington, D.C."}


def render(nyc_filtered, active_stations, is_demo):
    from backend.services import revenue_service, scenario_service
    from backend.services.case_study_service import load_case_studies
    from backend.validation.validators import ValidationError

    # ══════════════════════════════════════════════════════════════
    # Hero
    # ══════════════════════════════════════════════════════════════
    hero_section(
        eyebrow="INVESTMENT OPPORTUNITY",
        title="Invest in the Future of Urban Mobility",
        body=(
            "Strategic investment in Citi Bike can expand service coverage, "
            "accelerate ridership growth, and strengthen long-term recurring "
            "revenue — for Lyft and for the cities it serves."
        ),
    )

    current_rev = revenue_service.estimate_annual_revenue(nyc_filtered)
    st.caption(
        f"📊 Today, from live NYC trip data: {active_stations:,} active stations, "
        f"an estimated ${current_rev['total_estimated_revenue']:,.0f}/yr in revenue. "
        "Everything below this line is a scenario-based projection, not historical data."
    )

    # ══════════════════════════════════════════════════════════════
    # Investment Scenario Cards
    # ══════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header(
        "Choose an investment scenario",
        "Three expansion tiers, sized against today's network. Figures use the "
        "same scenario model as the ROI simulator below.",
    )

    if "opportunity_tier" not in st.session_state:
        st.session_state.opportunity_tier = "Medium Expansion"

    tier_cols = st.columns(3)
    for i, (name, cfg) in enumerate(INVESTMENT_TIERS.items()):
        with tier_cols[i]:
            scenario_card(
                name, cfg["amount"],
                is_active=(name == st.session_state.opportunity_tier),
                label=f"{cfg['new_stations']:,} stations",
            )
            if st.button(f"Select {name}", key=f"opp_tier_{i}", use_container_width=True):
                st.session_state.opportunity_tier = name
                st.rerun()

    tier = INVESTMENT_TIERS[st.session_state.opportunity_tier]
    tier_sim = scenario_service.simulate_investment(
        investment_amount=tier["investment_amount"],
        new_stations=tier["new_stations"],
        new_classic_bikes=tier["new_classic_bikes"],
        new_ebikes=tier["new_ebikes"],
        analysis_years=5,
        mode="base",
    )

    kpi_row([
        {"label": "New Stations", "value": f"{tier['new_stations']:,}"},
        {"label": "Additional Bikes", "value": f"{tier['new_classic_bikes'] + tier['new_ebikes']:,}"},
        {"label": "Additional E-bikes", "value": f"{tier['new_ebikes']:,}"},
        {"label": "Additional Annual Rides", "value": compact_number(tier_sim["projected_rides"]["steady_state_annual"])},
    ])
    tier_payback = tier_sim["payback_period_years"]
    kpi_row([
        {"label": "Est. Annual Revenue Increase", "value": f"${compact_number(tier_sim['projected_revenue']['steady_state_annual'])}"},
        {"label": "Est. 5-yr ROI", "value": f"{tier_sim['simple_roi']:.0%}"},
        {"label": "Est. Payback Period", "value": f"{tier_payback:.1f} yrs" if tier_payback is not None else "5+ yrs"},
    ])
    st.caption(
        "Estimates based on this app's base-case financial assumptions "
        "(see Investment Strategy for the full assumption set). Not a guaranteed outcome."
    )

    # ══════════════════════════════════════════════════════════════
    # Expected Impact
    # ══════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Expected impact", "Directional benefits of the selected scenario — not guaranteed figures.")

    impact_items = [
        ("More Neighborhood Coverage", "Denser station spacing reaches areas today's network skips."),
        ("Higher Ridership", f"Up to {compact_number(tier_sim['projected_rides']['steady_state_annual'])} additional annual rides at this tier."),
        ("Better First/Last Mile Transit", "New stations near high-delay subway stops close the gap trains leave behind."),
        ("Reduced Car Dependency", "Every added trip is a potential car, taxi, or rideshare trip that didn't happen."),
        ("Increased Membership Growth", "More docks near where people live and work convert casual riders into annual members."),
        ("Higher Revenue Potential", f"Est. +${compact_number(tier_sim['projected_revenue']['steady_state_annual'])}/yr in recurring revenue at this tier."),
        ("Lower Carbon Emissions", "Each bike trip that replaces a car trip cuts tailpipe emissions directly."),
    ]
    impact_cols = st.columns(2)
    for i, (title, body) in enumerate(impact_items):
        with impact_cols[i % 2]:
            finding_card(i + 1, title, body)

    # ══════════════════════════════════════════════════════════════
    # Growth Timeline
    # ══════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("How investment compounds over time")
    flow_diagram([
        ("💵", "Investment"),
        ("🏗️", "Expand Stations"),
        ("🚲", "Increase Bike<br>Availability"),
        ("📈", "More Daily<br>Riders"),
        ("💳", "Higher<br>Membership"),
        ("💰", "Higher<br>Revenue"),
        ("🌱", "Long-term<br>Sustainable Growth"),
    ])

    # ══════════════════════════════════════════════════════════════
    # Supporting Evidence
    # ══════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header(
        "Evidence from other cities",
        "Not a comparison with New York — independent proof that public and "
        "public-private investment reliably grows bike-share ridership and "
        "infrastructure elsewhere.",
    )

    evidence_studies = [c for c in load_case_studies() if c["city"] in EVIDENCE_CITIES]
    if evidence_studies:
        evidence_cols = st.columns(len(evidence_studies))
        for col, study in zip(evidence_cols, evidence_studies):
            with col:
                case_study_card(study)

    # ══════════════════════════════════════════════════════════════
    # Why Lyft?
    # ══════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Why Lyft?", "Business opportunities this investment could unlock — not guarantees.")

    why_lyft_items = [
        ("Strengthening Multimodal Transportation", "Bikes complement rideshare rather than compete with it, capturing trips too short for a car."),
        ("Expanding Sustainable Mobility", "A larger e-bike fleet extends zero-emission trip share without new vehicle capital."),
        ("Increasing Recurring Membership Revenue", "Annual memberships are predictable, subscription-style revenue — not one-off rides."),
        ("Stronger Government Partnerships", "The Evidence from Other Cities page shows public investment following, not replacing, a private operator."),
        ("Improving Customer Retention", "Riders who use both rideshare and bike-share for different trip types become stickier customers."),
        ("Supporting Climate & ESG Goals", "Expanded bike-share is a direct, measurable lever for sustainability commitments."),
        ("Expanding First/Last-Mile Reach", "Denser station coverage extends reach into trips transit and rideshare alone don't cover well."),
    ]
    why_cols = st.columns(2)
    for i, (title, body) in enumerate(why_lyft_items):
        with why_cols[i % 2]:
            finding_card(i + 1, title, body)

    # ══════════════════════════════════════════════════════════════
    # Interactive ROI Simulator
    # ══════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header(
        "Interactive ROI simulator",
        "Adjust the assumptions yourself. Same transparent financial formulas as "
        "the scenario cards above — no machine learning, no black box.",
    )

    sim_cols = st.columns(4)
    with sim_cols[0]:
        sim_investment_m = st.slider("Investment amount ($M)", 10, 150, 50, step=5, key="opp_sim_amount")
    with sim_cols[1]:
        sim_stations = st.slider("New stations", 50, 1_500, 500, step=25, key="opp_sim_stations")
    with sim_cols[2]:
        sim_ebikes = st.slider("New e-bikes", 0, 12_000, 3_000, step=250, key="opp_sim_ebikes")
    with sim_cols[3]:
        sim_growth_pct = st.slider("Expected annual ridership growth", 0, 15, 3, format="%d%%", key="opp_sim_growth")

    sim_total_bikes = sim_stations * 20
    sim_classic = max(0, sim_total_bikes - sim_ebikes)
    st.caption(
        f"Assumes ~20 bikes per new station: {sim_total_bikes:,} total bikes "
        f"({sim_classic:,} classic + {sim_ebikes:,} e-bikes)."
    )

    sim_result = None
    try:
        sim_result = scenario_service.simulate_investment(
            investment_amount=sim_investment_m * 1_000_000,
            new_stations=sim_stations,
            new_classic_bikes=sim_classic,
            new_ebikes=sim_ebikes,
            analysis_years=5,
            mode="base",
            overrides={"organic_growth_rate": sim_growth_pct / 100},
        )
    except ValidationError as exc:
        st.warning(str(exc))

    if sim_result:
        if sim_result["capital_warning"]:
            st.warning(sim_result["capital_warning"])

        sim_payback = sim_result["payback_period_years"]
        kpi_row([
            {"label": "Total Capital Cost", "value": f"${compact_number(sim_result['capital_cost']['total_capital'])}"},
            {"label": "Additional Annual Rides", "value": compact_number(sim_result["projected_rides"]["steady_state_annual"])},
            {"label": "Est. Annual Revenue", "value": f"${compact_number(sim_result['projected_revenue']['steady_state_annual'])}"},
            {"label": "Est. 5-yr ROI", "value": f"{sim_result['simple_roi']:.0%}"},
            {"label": "Est. Payback Period", "value": f"{sim_payback:.1f} yrs" if sim_payback is not None else "5+ yrs"},
        ])

        sim_proj_df = pd.DataFrame(sim_result["annual_projections"])
        fig_sim = bar_chart(
            sim_proj_df, x="year", y="projected_revenue",
            labels={"year": "Year", "projected_revenue": "Projected annual revenue ($)"},
            title="Projected revenue ramp-up",
            height=320,
        )
        fig_sim.update_layout(yaxis_tickprefix="$", yaxis_tickformat=",.0f")
        st.plotly_chart(fig_sim, use_container_width=True)

    st.caption(
        "This simulator uses transparent, editable financial assumptions — not a "
        "machine-learning model. See Investment Strategy for the full assumption "
        "set and sensitivity analysis."
    )

    # ══════════════════════════════════════════════════════════════
    # Closing
    # ══════════════════════════════════════════════════════════════
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    closing_banner(
        "Strategic investment today can create a larger, more connected, and "
        "more sustainable Citi Bike network for tomorrow.",
        "Every figure on this page is a labeled estimate, not a guarantee — but "
        "the pattern holds across every government-backed system in the Evidence "
        "from Other Cities page. The question isn't whether investment works. "
        "It's how much, how fast, and with whom.",
    )
