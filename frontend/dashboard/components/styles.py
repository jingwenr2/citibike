"""Design system: colors, typography, spacing, CSS, and chart defaults."""
from __future__ import annotations

import streamlit as st

# ── Color palette ──────────────────────────────────────────────────
LYFT_PINK = "#FF00BF"
HISTORICAL_BLUE = "#1E3A5F"
FORECAST_PURPLE = "#7C3AED"
POSITIVE_GREEN = "#059669"
PRESSURE_AMBER = "#D97706"
CRITICAL_RED = "#DC2626"
NEUTRAL_GRAY = "#64748B"
LIGHT_GRAY = "#94A3B8"
SURFACE_WHITE = "#FFFFFF"
BG_LIGHT = "#F8F9FB"
BORDER_LIGHT = "#E5E7EB"
TEXT_PRIMARY = "#0F172A"
TEXT_SECONDARY = "#64748B"
ACCENT_CYAN = "#7DD3FC"

CHART_COLORS = {
    "member": HISTORICAL_BLUE,
    "casual": ACCENT_CYAN,
    "electric": "#2D7FF9",
    "classic": LIGHT_GRAY,
    "nyc": "#2D7FF9",
    "sf": "#F26B4A",
    "recommended": LYFT_PINK,
    "not_recommended": "#CBD5E1",
    "scenario_none": LIGHT_GRAY,
    "scenario_base": "#2D7FF9",
    "scenario_growth": POSITIVE_GREEN,
}

RIDER_COLORS = {"Member": "#358DC3", "Casual": "#48C4E4"}
BIKE_COLORS = {"Electric": "#358DC3", "Classic": "#48C4E4"}
CITY_COLORS = {"New York City": "#2D7FF9", "San Francisco": "#F26B4A"}
SCENARIO_COLORS = ["#94A3B8", "#2D7FF9", "#10B981"]
PRESSURE_COLORS = [LIGHT_GRAY, ACCENT_CYAN, PRESSURE_AMBER, CRITICAL_RED]

# Cyan-to-magenta scale for the hourly demand heatmap, fading to a light
# blue (not pure white) at the low end for contrast among quiet hours.
_HEATMAP_HEX = [
    "#eaf6ff", "#d3f0ff", "#a9e6ff",
    "#59e9ff", "#4ed2ee", "#43b8dc", "#399bca", "#317cba",
    "#2b5cac", "#263aa1", "#2f2398", "#502091", "#731f8d", "#891d7d",
]
HEATMAP_SCALE = [[i / (len(_HEATMAP_HEX) - 1), hex_] for i, hex_ in enumerate(_HEATMAP_HEX)]

# ── Badge colors by data type ─────────────────────────────────────
BADGE_COLORS = {
    "Historical": ("#DBEAFE", "#1E40AF"),
    "Estimated": ("#FEF3C7", "#92400E"),
    "Forecast": ("#EDE9FE", "#5B21B6"),
    "Scenario": ("#F1F5F9", "#475569"),
    "External Evidence": ("#D1FAE5", "#065F46"),
}

# ── Chart defaults ────────────────────────────────────────────────
CHART_MARGIN = dict(l=10, r=10, t=30, b=10)
CHART_MARGIN_TIGHT = dict(l=10, r=10, t=15, b=10)
CHART_MARGIN_MAP = dict(l=0, r=0, t=0, b=0)

CHART_LAYOUT = dict(
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="white",
    margin=CHART_MARGIN,
    hovermode="x unified",
    legend_title_text="",
    font=dict(family="Inter, system-ui, -apple-system, sans-serif"),
)


def apply_layout(fig, height: int = 400, title: str = "", **overrides):
    """Apply the standard layout to any Plotly figure."""
    layout = {**CHART_LAYOUT, "height": height}
    if title:
        layout["title"] = dict(text=title, font=dict(size=15, color=TEXT_PRIMARY))
    layout.update(overrides)
    fig.update_layout(**layout)
    return fig


# ── Global CSS ────────────────────────────────────────────────────
_CSS = """
<style>
/* ── Base ── */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
.stApp {background: #F8F9FB; font-family: 'Inter', system-ui, -apple-system, sans-serif;}
.stApp [data-testid="stAppViewBlockContainer"] {max-width: 1180px; padding: 1.5rem 2rem;}

/* ── Sidebar ── */
[data-testid="stSidebar"] {background: #0F172A; border-right: 1px solid #1E293B;}
[data-testid="stSidebar"] * {color: #E2E8F0 !important;}
[data-testid="stSidebar"] input, [data-testid="stSidebar"] select {color: #0F172A !important;}
[data-testid="stSidebar"] .nav-section {
    font-size: .65rem; font-weight: 700; letter-spacing: .14em;
    text-transform: uppercase; color: #64748B !important;
    padding: .6rem 0 .25rem 0; margin-top: .5rem;
}
[data-testid="stSidebar"] [data-testid="stMarkdownContainer"] p {font-size: .9rem;}

/* ── Metric cards ── */
div[data-testid="stMetric"] {
    background: white; border: 1px solid #E5E7EB;
    padding: 1rem 1.1rem; border-radius: 14px;
    box-shadow: 0 1px 3px rgba(15,23,42,.04);
}
div[data-testid="stMetricLabel"] {color: #64748B; font-size: .82rem; text-transform: uppercase; letter-spacing: .04em;}
div[data-testid="stMetricValue"] {font-weight: 700;}

/* ── Page header ── */
.page-header {margin-bottom: 1.5rem;}
.page-header h1 {font-size: 2rem; font-weight: 700; color: #0F172A; margin: 0 0 .25rem 0; line-height: 1.2;}
.page-header p {font-size: .95rem; color: #64748B; margin: 0; max-width: 680px;}
.page-badge {
    display: inline-block; padding: .2rem .6rem; border-radius: 999px;
    font-size: .7rem; font-weight: 600; letter-spacing: .03em;
    vertical-align: middle; margin-left: .5rem;
}

/* ── Hero ── */
.hero-section {
    padding: 2.5rem 2.5rem 2rem; border-radius: 18px; color: white;
    background: linear-gradient(135deg, #0F172A 0%, #1E293B 100%);
    margin-bottom: 1.5rem; position: relative; overflow: hidden;
}
.hero-section::before {
    content: ''; position: absolute; top: -40%; right: -10%;
    width: 400px; height: 400px; border-radius: 50%;
    background: radial-gradient(circle, rgba(255,0,191,.15), transparent 70%);
}
.hero-section h1 {font-size: 2.2rem; font-weight: 700; margin: 0 0 .5rem 0; position: relative;}
.hero-section p {font-size: 1rem; color: #CBD5E1; margin: 0; max-width: 640px; position: relative;}
.hero-section .eyebrow {
    font-size: .72rem; letter-spacing: .12em; text-transform: uppercase;
    color: #FF00BF; margin-bottom: .4rem; font-weight: 600; position: relative;
}

/* ── Insight panel ── */
.insight-panel {
    background: #F0F9FF; border-left: 3px solid #2D7FF9;
    padding: 1rem 1.25rem; border-radius: 0 10px 10px 0; margin: 1rem 0;
}
.insight-panel strong {color: #0F172A;}
.insight-panel p {color: #334155; margin: 0; font-size: .92rem; line-height: 1.55;}

/* ── Recommendation card ── */
.rec-card {
    background: white; border: 1px solid #E5E7EB; border-radius: 14px;
    padding: 1.2rem 1.4rem; margin-bottom: .75rem;
    box-shadow: 0 1px 3px rgba(15,23,42,.04);
}
.rec-card.recommended {border-left: 3px solid #FF00BF;}
.rec-score {
    display: inline-block; background: #0F172A; color: white;
    padding: .2rem .55rem; border-radius: 8px; font-weight: 700;
    font-size: .9rem; float: right;
}
.rec-card h4 {margin: 0 0 .35rem 0; font-size: 1rem; color: #0F172A;}
.rec-card .rec-action {color: #FF00BF; font-weight: 600; font-size: .88rem; margin-bottom: .3rem;}
.rec-card .rec-reason {color: #64748B; font-size: .85rem; line-height: 1.4;}

/* ── Scenario card ── */
.scenario-card {
    background: white; border: 1px solid #E5E7EB; border-radius: 14px;
    padding: 1.3rem; text-align: center; cursor: pointer; transition: border-color .15s;
}
.scenario-card:hover {border-color: #94A3B8;}
.scenario-card.active {border: 2px solid #FF00BF; box-shadow: 0 0 0 3px rgba(255,0,191,.1);}
.scenario-card h3 {margin: 0 0 .3rem 0; font-size: 1.1rem; color: #0F172A;}
.scenario-card .amount {font-size: 1.75rem; font-weight: 700; color: #0F172A;}
.scenario-label {
    display: inline-block; background: #FF00BF; color: white;
    padding: .15rem .5rem; border-radius: 999px; font-size: .68rem;
    font-weight: 700; letter-spacing: .03em; margin-top: .3rem;
}

/* ── Case study card ── */
.case-card {
    background: white; border: 1px solid #E5E7EB; border-radius: 14px;
    padding: 1.2rem 1.3rem; height: 100%;
    box-shadow: 0 1px 3px rgba(15,23,42,.04);
}
.case-card h4 {margin: 0 0 .2rem 0; font-size: 1.05rem; color: #0F172A;}
.case-card .case-system {color: #64748B; font-size: .82rem; margin-bottom: .5rem;}
.case-card .case-lesson {
    background: #F0FDF4; border-radius: 8px; padding: .6rem .8rem;
    font-size: .85rem; color: #065F46; margin-top: .5rem;
}

/* ── Tags ── */
.tag {
    display: inline-block; padding: .15rem .45rem; border-radius: 6px;
    font-size: .7rem; font-weight: 600; margin-right: .3rem;
}
.tag-demand {background: #DBEAFE; color: #1E40AF;}
.tag-gap {background: #FEF3C7; color: #92400E;}
.tag-transit {background: #EDE9FE; color: #5B21B6;}
.tag-pressure {background: #FEE2E2; color: #991B1B;}
.tag-revenue {background: #D1FAE5; color: #065F46;}

/* ── Demo pill ── */
.demo-pill {
    display: inline-block; padding: .22rem .55rem; border-radius: 999px;
    background: #FEF3C7; color: #92400E; font-size: .72rem; font-weight: 700;
}

/* ── Misc ── */
.section-divider {border: none; border-top: 1px solid #E5E7EB; margin: 1.5rem 0;}
</style>
"""


def inject_css():
    """Inject the global design system CSS."""
    st.markdown(_CSS, unsafe_allow_html=True)
