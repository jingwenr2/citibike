"""Sidebar navigation with grouped sections."""
from __future__ import annotations

import streamlit as st

PAGES = [
    ("UNDERSTAND", [
        ("Executive Overview", "executive_overview"),
        ("Network Performance", "network_performance"),
        ("Demand Forecast", "demand_forecast"),
        ("Transit Connections", "transit_connections"),
    ]),
    ("DECIDE", [
        ("Station Opportunities", "station_opportunities"),
        ("Investment Strategy", "investment_strategy"),
        ("Investment Impact", "investment_impact"),
        ("Investment Opportunity", "investment_opportunity"),
    ]),
    ("VALIDATE", [
        ("Evidence from Other Cities", "evidence_cities"),
        ("Data & Methodology", "data_methodology"),
    ]),
]

# Flat list for radio indexing
_ALL_PAGES = []
for _, pages in PAGES:
    for display, key in pages:
        _ALL_PAGES.append((display, key))


def render_sidebar(data_period: str = "") -> str:
    """Render sidebar navigation. Returns selected page key."""
    with st.sidebar:
        st.markdown(
            "<div style='padding:.5rem 0 .3rem;'>"
            "<span style='font-size:1.15rem;font-weight:700;color:#F8FAFC;'>Citi Bike Growth Intelligence</span>"
            "</div>",
            unsafe_allow_html=True,
        )
        st.caption("A data-driven strategy for Citi Bike expansion in New York City.")
        st.markdown("<hr style='border-color:#1E293B;margin:.5rem 0;'>", unsafe_allow_html=True)

        if "active_page" not in st.session_state:
            st.session_state.active_page = "executive_overview"

        for section_name, pages in PAGES:
            st.markdown(
                f'<div class="nav-section">{section_name}</div>',
                unsafe_allow_html=True,
            )
            for display_name, key in pages:
                is_active = st.session_state.active_page == key
                if is_active:
                    style = "background:#1E293B;border-radius:8px;padding:.35rem .6rem;margin:.1rem 0;"
                else:
                    style = "padding:.35rem .6rem;margin:.1rem 0;"
                if st.sidebar.button(
                    display_name,
                    key=f"nav_{key}",
                    use_container_width=True,
                    type="tertiary" if not is_active else "primary",
                ):
                    st.session_state.active_page = key
                    st.rerun()

        st.markdown("<hr style='border-color:#1E293B;margin:.75rem 0 .5rem;'>", unsafe_allow_html=True)
        if data_period:
            st.caption(f"Data: {data_period}")
        st.caption("New York City · Citi Bike")

    return st.session_state.active_page
