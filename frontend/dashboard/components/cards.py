"""Reusable card components: KPI, recommendation, scenario, case study."""
from __future__ import annotations

import streamlit as st


def compact_number(value: float) -> str:
    """Format a number compactly (14.1M, 156.3K, 42)."""
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def kpi_row(metrics: list[dict]):
    """Render a row of KPI cards. Each dict: label, value, delta (optional)."""
    cols = st.columns(len(metrics))
    for col, m in zip(cols, metrics):
        col.metric(m["label"], m["value"], m.get("delta", None))


def recommendation_card(
    station: str,
    score: float,
    action: str,
    reason: str,
    is_recommended: bool = False,
):
    """Render a station recommendation card."""
    cls = "rec-card recommended" if is_recommended else "rec-card"
    st.markdown(
        f'<div class="{cls}">'
        f'<span class="rec-score">{score:.0f}</span>'
        f"<h4>{station}</h4>"
        f'<div class="rec-action">{action}</div>'
        f'<div class="rec-reason">{reason}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def scenario_card(title: str, amount: str, is_active: bool = False, label: str = ""):
    """Render an investment scenario card."""
    cls = "scenario-card active" if is_active else "scenario-card"
    label_html = f'<div><span class="scenario-label">{label}</span></div>' if label else ""
    st.markdown(
        f'<div class="{cls}">'
        f"<h3>{title}</h3>"
        f'<div class="amount">{amount}</div>'
        f"{label_html}"
        f"</div>",
        unsafe_allow_html=True,
    )


def case_study_card(study: dict):
    """Render a compact case study card."""
    city = study.get("city", "")
    system = study.get("system_name", study.get("system", ""))
    gov = study.get("government_involvement", "")
    lesson = study.get("main_lesson", "")
    result = study.get("ridership_result", study.get("financial_result", ""))

    st.markdown(
        f'<div class="case-card">'
        f"<h4>{city}</h4>"
        f'<div class="case-system">{system}</div>'
        + (f"<p style='font-size:.85rem;color:#334155;margin:.3rem 0;'><strong>Public role:</strong> {gov}</p>" if gov else "")
        + (f"<p style='font-size:.85rem;color:#334155;margin:.3rem 0;'><strong>Result:</strong> {result}</p>" if result else "")
        + (f'<div class="case-lesson"><strong>Key lesson:</strong> {lesson}</div>' if lesson else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def finding_card(number: int, title: str, body: str):
    """Render a numbered executive finding."""
    st.markdown(
        f"<div style='margin-bottom:.8rem;'>"
        f"<span style='color:#FF00BF;font-weight:700;font-size:.85rem;'>{number:02d}</span>"
        f"<span style='font-weight:600;font-size:.95rem;color:#0F172A;margin-left:.5rem;'>{title}</span>"
        f"<p style='color:#64748B;font-size:.88rem;margin:.2rem 0 0 1.6rem;line-height:1.45;'>{body}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )
