"""Evidence from Other Cities — What can we learn from global bike-share investment?"""
from __future__ import annotations

import streamlit as st

from components.cards import case_study_card
from components.headers import page_header, section_header, insight_panel


def render():
    from backend.services.case_study_service import load_case_studies

    page_header(
        "Evidence from Other Cities",
        "What can we learn from global bike-share investment?",
        badge="External Evidence",
    )

    st.markdown(
        '<p style="color:#64748B;">Citi Bike is the target of this investment case, not a '
        "success story — these systems are independent, external evidence that "
        "sustained public investment and public-private partnerships reliably grow "
        "ridership, expand infrastructure, and put bike-share on stable financial "
        "footing.</p>",
        unsafe_allow_html=True,
    )

    case_studies = load_case_studies()

    # ── Case study grid ──
    story_rows = [case_studies[i : i + 3] for i in range(0, len(case_studies), 3)]
    for row in story_rows:
        story_cols = st.columns(len(row))
        for col, story in zip(story_cols, row):
            with col:
                case_study_card(story)

    # ── Common patterns ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("What these systems have in common")

    pattern_cols = st.columns(2)
    with pattern_cols[0]:
        st.markdown(
            "**Public ownership or formal PPP** — every system is either government-owned "
            "or built on a long-term public/sponsorship contract."
        )
        st.markdown(
            "**Sustained, multi-year capital commitments** — buildouts are funded in "
            "dedicated tranches, not one-off grants."
        )
    with pattern_cols[1]:
        st.markdown(
            "**Investment → ridership growth** — every system posted double-digit ridership "
            "growth and fleet expansion in its most recent reporting period."
        )
        st.markdown(
            "**Financial sustainability follows investment** — BIXI's turnaround and Divvy's "
            "revenue-sharing model show public backing can become self-sustaining."
        )

    # ── Bay Wheels highlight ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Spotlight: Bay Wheels (San Francisco)")

    bay = next((c for c in case_studies if c["city"] == "San Francisco"), None)
    if bay:
        highlight_cols = st.columns(2)
        with highlight_cols[0]:
            st.markdown(f"*{bay['main_lesson']}*")
            st.markdown(f"**Infrastructure:** {bay['fleet_growth']}")
        with highlight_cols[1]:
            st.markdown(f"**Public role:** {bay['government_involvement']}")
            st.markdown(f"**Ridership:** {bay['ridership_result']}")

    insight_panel(
        "<strong>Key takeaway:</strong> Every successful bike-share system in this evidence "
        "base has one thing in common: sustained public investment or a formal public-private "
        "partnership. NYC has the demand, the infrastructure, and the operator (Lyft). "
        "What's missing is the public commitment."
    )
