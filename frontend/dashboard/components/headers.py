"""Page headers, section headers, and data-type badges."""
from __future__ import annotations

import streamlit as st

from .styles import BADGE_COLORS


def page_header(title: str, subtitle: str = "", badge: str | None = None):
    """Render page title with optional one-line subtitle and data-type badge."""
    badge_html = ""
    if badge and badge in BADGE_COLORS:
        bg, fg = BADGE_COLORS[badge]
        badge_html = f'<span class="page-badge" style="background:{bg};color:{fg};">{badge}</span>'
    st.markdown(
        f'<div class="page-header">'
        f"<h1>{title}{badge_html}</h1>"
        + (f"<p>{subtitle}</p>" if subtitle else "")
        + "</div>",
        unsafe_allow_html=True,
    )


def section_header(title: str, note: str = ""):
    """Render a section heading with optional explanatory note."""
    st.markdown(f"### {title}")
    if note:
        st.caption(note)


def hero_section(
    eyebrow: str, title: str, body: str,
):
    """Render the Executive Overview hero banner."""
    st.markdown(
        f'<div class="hero-section">'
        f'<div class="eyebrow">{eyebrow}</div>'
        f"<h1>{title}</h1>"
        f"<p>{body}</p>"
        f"</div>",
        unsafe_allow_html=True,
    )


def insight_panel(body: str):
    """Render a highlighted insight/takeaway panel."""
    st.markdown(
        f'<div class="insight-panel"><p>{body}</p></div>',
        unsafe_allow_html=True,
    )
