"""Fill the capstone slide template with Citi Bike project data — styled."""
from __future__ import annotations

from pathlib import Path

from pptx import Presentation
from pptx.util import Pt, Inches, Emu
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN

TEMPLATE = Path.home() / "Downloads" / "Data capstone slides template.pptx"
OUTPUT = Path(__file__).resolve().parents[1] / "report" / "CitiBike_Capstone_Final.pptx"

# Brand colors
DARK = RGBColor(0x0F, 0x17, 0x2A)
BLUE = RGBColor(0x2D, 0x7F, 0xF9)
PINK = RGBColor(0xFF, 0x00, 0xBF)
GRAY = RGBColor(0x64, 0x74, 0x8B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GREEN = RGBColor(0x10, 0xB9, 0x81)
ORANGE = RGBColor(0xF5, 0x9E, 0x0B)


def _clear_and_write(shape, lines, font_size=12, color=DARK, bold=False, align=PP_ALIGN.LEFT):
    """Clear shape text and write styled lines.

    Each item in *lines* is (text, opts_dict).  Recognised opts:
      size, color, bold, align, space_after, name
    """
    tf = shape.text_frame
    tf.word_wrap = True
    for p in tf.paragraphs:
        p.clear()

    for i, (text, opts) in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = opts.get("align", align)
        p.space_after = Pt(opts.get("space_after", 2))
        p.space_before = Pt(opts.get("space_before", 0))
        run = p.add_run()
        run.text = text
        run.font.size = Pt(opts.get("size", font_size))
        run.font.color.rgb = opts.get("color", color)
        run.font.bold = opts.get("bold", bold)
        if opts.get("name"):
            run.font.name = opts["name"]


def _simple(shape, text, size=12, color=DARK, bold=False, align=PP_ALIGN.LEFT):
    _clear_and_write(shape, [(text, {"size": size, "color": color, "bold": bold, "align": align})])


def _find_text_shapes(slide):
    return sorted(
        [s for s in slide.shapes if s.has_text_frame and s.text_frame.text.strip()],
        key=lambda s: (s.top, s.left),
    )


def fill_template():
    prs = Presentation(str(TEMPLATE))
    slides = list(prs.slides)

    # ── Slide 1: Title ──────────────────────────────────────────────────
    for s in _find_text_shapes(slides[0]):
        if "PROJECT TITLE" in s.text:
            _clear_and_write(s, [
                ("CityCycle NYC", {"size": 32, "bold": True, "color": DARK}),
                ("A Data-Driven Investment Case for Citi Bike Expansion", {"size": 16, "color": BLUE, "space_before": 4}),
            ])
        elif "TTPR" in s.text:
            _simple(s, "TTPR Summer 2026  ·  Nathan  ·  Jenny  ·  Nosaifa", size=13, color=GRAY)

    # ── Slide 2: Team & Roles ───────────────────────────────────────────
    s2 = _find_text_shapes(slides[1])
    team = [
        ("Nathan", "Data Engineer & Backend Lead",
         "Data pipeline · ETL · Revenue modeling · MTA integration"),
        ("Jenny", "Data Analyst & Dashboard Lead",
         "Streamlit dashboard · Plotly charts · UX design"),
        ("Nosaifa", "ML Engineer & Forecast Lead",
         "XGBoost forecast · Feature engineering · Model evaluation"),
    ]
    name_shapes = [s for s in s2 if "Student Name" in s.text]
    resp_shapes = [s for s in s2 if "Core Responsibilities" in s.text]
    for i, (name, role, resp) in enumerate(team):
        if i < len(name_shapes):
            _clear_and_write(name_shapes[i], [
                (f"{name}  —  {role}", {"size": 11, "bold": True, "color": DARK}),
            ])
        if i < len(resp_shapes):
            _simple(resp_shapes[i], resp, size=10, color=GRAY)
    for s in s2:
        if "Names and roles" in s.text:
            _simple(s, "", size=1)

    # ── Slide 3: Business Problem ───────────────────────────────────────
    for s in _find_text_shapes(slides[2]):
        t = s.text.strip()
        if "About Project" in t:
            pass  # keep slide title
        elif "This slide should" in t:
            _simple(s, "", size=1)
        elif t == "Problem":
            _simple(s, "The Problem", size=14, bold=True, color=BLUE)
        elif "What challenge exists" in t:
            _clear_and_write(s, [
                ("NYC's Citi Bike generates $196 M/yr — but 50 % of stations are at capacity.", {"size": 11, "bold": True, "color": DARK}),
                ("", {"size": 4}),
                ("MTA delays are pushing commuters toward alternatives, yet there is no data-driven expansion plan.", {"size": 10, "color": GRAY}),
            ])
        elif "Who is affected" in t:
            _clear_and_write(s, [
                ("▸ 8.3 M NYC residents on aging transit", {"size": 10, "color": DARK}),
                ("▸ Lyft (operator) leaving revenue on the table", {"size": 10, "color": DARK}),
                ("▸ City planners deciding without forecasts", {"size": 10, "color": DARK}),
                ("▸ ~$11.3 M/yr in unrealized net profit", {"size": 10, "bold": True, "color": PINK}),
            ])
        elif "Real-World" in t:
            _simple(s, "Global Context", size=14, bold=True, color=BLUE)
        elif "Write the problem" in t:
            _clear_and_write(s, [
                ("China's dockless bike-share proved global demand — but failed outside China (no docks, no gov partnership).", {"size": 10, "color": DARK}),
                ("", {"size": 4}),
                ("Citi Bike's dock-based model works. SF, DC, and Chicago confirm it.", {"size": 10, "bold": True, "color": DARK}),
            ])

    # ── Slide 4: Project Impact ─────────────────────────────────────────
    # Three 3.5 × 2.5-inch cards
    for s in _find_text_shapes(slides[3]):
        t = s.text.strip()
        if "Translate your" in t:
            _simple(s, "", size=1)
        elif t == "Industry Impact":
            _simple(s, "Industry Impact", size=12, bold=True, color=BLUE)
        elif "Connect your problem" in t:
            _clear_and_write(s, [
                ("$5 B+ global bike-share market", {"size": 11, "bold": True, "color": DARK}),
                ("growing 12 % annually.", {"size": 10, "color": GRAY}),
                ("", {"size": 4}),
                ("NYC operates the largest system in the Americas.", {"size": 10, "color": GRAY}),
            ])
        elif t == "Quantify the Scale":
            _simple(s, "By the Numbers", size=12, bold=True, color=BLUE)
        elif "Use 1–3 numbers" in t:
            _clear_and_write(s, [
                ("$196 M / yr", {"size": 18, "bold": True, "color": PINK}),
                ("Citi Bike revenue", {"size": 9, "color": GRAY, "space_after": 6}),
                ("60.9 M trips", {"size": 18, "bold": True, "color": BLUE}),
                ("in our dataset", {"size": 9, "color": GRAY, "space_after": 6}),
                ("50 %+ stations", {"size": 18, "bold": True, "color": DARK}),
                ("at or above capacity", {"size": 9, "color": GRAY}),
            ])
        elif t == "Organizational Risk":
            _simple(s, "Cost of Inaction", size=12, bold=True, color=BLUE)
        elif "Explain what happens" in t:
            _clear_and_write(s, [
                ("Without expansion:", {"size": 10, "bold": True, "color": DARK}),
                ("▸ Riders lost to competitors", {"size": 9, "color": GRAY}),
                ("▸ $11.3 M/yr unrealized profit", {"size": 9, "color": GRAY}),
                ("▸ Underserved neighborhoods", {"size": 9, "color": GRAY}),
                ("▸ Compounding loss each year", {"size": 9, "color": GRAY}),
            ])

    # ── Slide 5: Objectives ─────────────────────────────────────────────
    for s in _find_text_shapes(slides[4]):
        t = s.text.strip()
        if "Define your goals" in t:
            _simple(s, "", size=1)
        elif t == "Project Goals":
            _simple(s, "Project Goals", size=12, bold=True, color=BLUE)
        elif "What was the project" in t or "Frame goals" in t:
            _clear_and_write(s, [
                ("1.  Build XGBoost demand forecast", {"size": 11, "color": DARK}),
                ("     Predict daily station-level trips", {"size": 9, "color": GRAY, "space_after": 4}),
                ("2.  Identify expansion opportunities", {"size": 11, "color": DARK}),
                ("     MTA transit + bike demand scoring", {"size": 9, "color": GRAY, "space_after": 4}),
                ("3.  Calculate expansion ROI", {"size": 11, "color": DARK}),
                ("     NPV, IRR, payback period", {"size": 9, "color": GRAY, "space_after": 4}),
                ("4.  Build interactive dashboard", {"size": 11, "color": DARK}),
                ("     For government decision-makers", {"size": 9, "color": GRAY}),
            ])
        elif "KPIs" in t:
            _simple(s, "Success Metrics", size=12, bold=True, color=BLUE)
        elif "Define success" in t:
            _clear_and_write(s, [
                ("MAE < 12 trips/day", {"size": 11, "bold": True, "color": DARK}),
                ("  Achieved: 11.24 ✓", {"size": 10, "color": GREEN, "space_after": 4}),
                ("Beat baseline by > 30 %", {"size": 11, "bold": True, "color": DARK}),
                ("  Achieved: 42.5 % ✓", {"size": 10, "color": GREEN, "space_after": 4}),
                ("CV MAE < 10", {"size": 11, "bold": True, "color": DARK}),
                ("  Achieved: 9.35 ✓", {"size": 10, "color": GREEN}),
            ])
        elif "Break Even" in t:
            _clear_and_write(s, [
                ("Break-Even", {"size": 12, "bold": True, "color": BLUE}),
                ("250 stations × $128 K = $32 M", {"size": 11, "color": DARK, "space_after": 4}),
                ("Net profit: $11.3 M/yr", {"size": 13, "bold": True, "color": PINK}),
                ("Payback: 17 months", {"size": 13, "bold": True, "color": GREEN}),
            ])

    # ── Slide 6: Data Sources ───────────────────────────────────────────
    for s in _find_text_shapes(slides[5]):
        t = s.text.strip()
        if "Explain where" in t:
            _simple(s, "", size=1)
        elif t == "Internal Data":
            _simple(s, "Trip Data", size=11, bold=True, color=BLUE)
        elif "Operational records" in t:
            _clear_and_write(s, [
                ("Citi Bike trip records (2+ years)", {"size": 9, "bold": True, "color": DARK}),
                ("60.9 M trips · start/end station", {"size": 8, "color": GRAY}),
                ("timestamp · rider type · bike type", {"size": 8, "color": GRAY}),
            ])
        elif t == "External Data":
            _simple(s, "Transit & Weather", size=11, bold=True, color=BLUE)
        elif "Public datasets" in t:
            _clear_and_write(s, [
                ("MTA subway ridership + delays", {"size": 9, "bold": True, "color": DARK}),
                ("NOAA weather · NYC open data", {"size": 8, "color": GRAY}),
            ])
        elif t == "Surveys / Forms":
            _simple(s, "Pricing & Revenue", size=11, bold=True, color=BLUE)
        elif "Primary research" in t:
            _clear_and_write(s, [
                ("$239 annual / $4.49 single ride", {"size": 9, "color": DARK}),
                ("$3.24 avg e-bike overage", {"size": 8, "color": GRAY}),
                ("$17.5 M Citi sponsorship", {"size": 8, "color": GRAY}),
            ])
        elif "Missing Values" in t:
            _simple(s, "Data Quality", size=11, bold=True, color=BLUE)
        elif "How were nulls" in t:
            _clear_and_write(s, [
                ("Dropped null stations (< 0.1 %)", {"size": 9, "color": DARK}),
                ("Imputed missing capacity", {"size": 8, "color": GRAY}),
                ("Forward-filled weather gaps ≤ 2 d", {"size": 8, "color": GRAY}),
            ])
        elif "Transformation" in t:
            _simple(s, "Feature Engineering", size=11, bold=True, color=BLUE)
        elif "What fields were" in t:
            _clear_and_write(s, [
                ("23 features engineered:", {"size": 9, "bold": True, "color": DARK}),
                ("Temporal lags · rolling means", {"size": 8, "color": GRAY}),
                ("Weather deviations · MTA scores", {"size": 8, "color": GRAY}),
            ])

    # ── Slide 7: Analytical Methods ─────────────────────────────────────
    for s in _find_text_shapes(slides[6]):
        t = s.text.strip()
        if "List the most" in t:
            _simple(s, "", size=1)
        elif t == "Excel / SQL / Databases":
            _simple(s, "Python / Pandas", size=11, bold=True, color=BLUE)
        elif "Used for querying" in t:
            _clear_and_write(s, [
                ("ETL pipeline & feature engineering", {"size": 9, "color": DARK}),
                ("Parquet for fast I/O", {"size": 8, "color": GRAY}),
            ])
        elif t == "Tableau / Power BI":
            _simple(s, "Streamlit / Plotly", size=11, bold=True, color=BLUE)
        elif "For dashboards" in t:
            _clear_and_write(s, [
                ("9-tab interactive dashboard", {"size": 9, "color": DARK}),
                ("Deployed on Streamlit Cloud", {"size": 8, "color": GRAY}),
            ])
        elif t == "Python / APIs":
            _simple(s, "XGBoost / scikit-learn", size=11, bold=True, color=BLUE)
        elif "For scripting" in t:
            _clear_and_write(s, [
                ("Demand forecasting w/ early stopping", {"size": 9, "color": DARK}),
                ("3-fold time-series cross-validation", {"size": 8, "color": GRAY}),
            ])
        elif t == "Machine Learning / AI":
            _simple(s, "Financial Modeling", size=11, bold=True, color=BLUE)
        elif "If used, define" in t:
            _clear_and_write(s, [
                ("NPV / IRR cash flow analysis", {"size": 9, "color": DARK}),
                ("MTA opportunity scoring", {"size": 8, "color": GRAY}),
            ])

    # ── Slide 8: AI Usage ───────────────────────────────────────────────
    for s in _find_text_shapes(slides[7]):
        t = s.text.strip()
        if "If you used AI" in t:
            _clear_and_write(s, [
                ("Claude Code (Anthropic)", {"size": 14, "bold": True, "color": DARK}),
                ("AI pair-programmer", {"size": 11, "color": BLUE, "space_after": 6}),
                ("▸ Code generation — dashboard, charts, CSS", {"size": 10, "color": DARK}),
                ("▸ Model iteration — XGBoost tuning, features", {"size": 10, "color": DARK}),
                ("▸ Data pipeline — ETL, revenue, MTA integration", {"size": 10, "color": DARK}),
                ("▸ Optimization — caching & fragment decorators", {"size": 10, "color": DARK}),
                ("", {"size": 6}),
                ("All code reviewed & stress-tested. Every commit co-authored.", {"size": 9, "color": GRAY}),
            ])

    # ── Slide 9: EDA Insights ───────────────────────────────────────────
    for s in _find_text_shapes(slides[8]):
        t = s.text.strip()
        if "Exploratory Data" in t:
            _simple(s, "Key patterns from 60.9 M Citi Bike trips.", size=11, color=GRAY)
        elif "Use heatmaps" in t:
            _clear_and_write(s, [
                ("▸ Weekday demand 40 % > weekends", {"size": 11, "color": DARK}),
                ("▸ Peak hours: 8 AM + 5–6 PM", {"size": 11, "color": DARK}),
                ("▸ Subway delays → 2.3× bike usage", {"size": 11, "color": DARK}),
                ("▸ Summer = 3× winter demand", {"size": 11, "color": DARK}),
                ("▸ E-bike share growing rapidly", {"size": 11, "color": DARK}),
            ])
        elif t == "5%":
            _simple(s, "50 %+", size=28, bold=True, color=PINK)
        elif "Missing values" in t:
            _simple(s, "stations maxed out", size=9, color=GRAY)
        elif t == "45":
            _simple(s, "$196 M", size=28, bold=True, color=BLUE)
        elif "AVG" in t:
            _simple(s, "annual revenue", size=9, color=GRAY)
        elif "Don't put" in t or "Don\u2019t put" in t:
            _clear_and_write(s, [
                ("42.5 %", {"size": 22, "bold": True, "color": GREEN}),
                ("better than baseline", {"size": 9, "color": GRAY, "space_after": 8}),
                ("0.987", {"size": 22, "bold": True, "color": BLUE}),
                ("prediction correlation", {"size": 9, "color": GRAY}),
            ])

    # ── Slide 10: Dashboard ─────────────────────────────────────────────
    for s in _find_text_shapes(slides[9]):
        t = s.text.strip()
        if "Dashboard in Tableau" in t:
            _simple(s, "Interactive Streamlit Dashboard", size=18, bold=True, color=DARK)
        elif "Show the executive" in t:
            _simple(s, "9-tab dashboard deployed on Streamlit Community Cloud", size=11, color=GRAY)
        elif "Put your dashboard" in t:
            _clear_and_write(s, [
                ("citibike-citycycle.streamlit.app", {"size": 14, "bold": True, "color": PINK, "align": PP_ALIGN.CENTER}),
            ])

    # ── Slide 11: Predictive Insights ───────────────────────────────────
    # Three 3.5 × 2.8-inch cards
    for s in _find_text_shapes(slides[10]):
        t = s.text.strip()
        if "Use this section" in t or "This section can" in t or "Use graphs" in t:
            _simple(s, "", size=1)
        elif "Prediction/model" in t:
            _simple(s, "XGBoost Forecast", size=11, bold=True, color=BLUE)
        elif "What future trend" in t:
            _clear_and_write(s, [
                ("23 features: lags, rolling means,", {"size": 9, "color": DARK}),
                ("weather, MTA data, station info", {"size": 9, "color": DARK}),
                ("", {"size": 4}),
                ("MAE 11.24", {"size": 14, "bold": True, "color": PINK}),
                ("WAPE 19 % · CV MAE 9.35", {"size": 9, "color": GRAY}),
            ])
        elif t == "Recommendations":
            _simple(s, "Expansion Priorities", size=11, bold=True, color=BLUE)
        elif "What actions" in t:
            _clear_and_write(s, [
                ("Predicted demand > capacity", {"size": 9, "color": DARK}),
                ("= priority expansion zone", {"size": 9, "bold": True, "color": DARK}),
                ("", {"size": 4}),
                ("Combined with MTA scores to", {"size": 9, "color": GRAY}),
                ("rank top dock locations", {"size": 9, "color": GRAY}),
            ])
        elif t == "Risk Scoring":
            _simple(s, "Transit Opportunity Score", size=11, bold=True, color=BLUE)
        elif "If a scoring model" in t:
            _clear_and_write(s, [
                ("Score 0–100 combining:", {"size": 9, "color": DARK}),
                ("MTA ridership + delay rates", {"size": 9, "color": GRAY}),
                ("+ bike station proximity", {"size": 9, "color": GRAY}),
                ("", {"size": 4}),
                ("High score = unmet demand", {"size": 9, "bold": True, "color": DARK}),
            ])

    # ── Slide 12: Model Demo ────────────────────────────────────────────
    for s in _find_text_shapes(slides[11]):
        t = s.text.strip()
        if "demonstration" in t:
            _clear_and_write(s, [
                ("Live demo:", {"size": 14, "bold": True, "color": DARK}),
                ("citibike-citycycle.streamlit.app", {"size": 14, "bold": True, "color": PINK, "space_after": 10}),
                ("▸ Forecast Lab — weather & policy scenarios", {"size": 11, "color": DARK}),
                ("▸ Gov Investment — budget, NPV, IRR, cash flow", {"size": 11, "color": DARK}),
                ("▸ Station Explorer — click any station", {"size": 11, "color": DARK}),
                ("▸ MTA Connection — transit vs bike demand", {"size": 11, "color": DARK}),
            ])

    # ── Slide 13: Results ───────────────────────────────────────────────
    for s in _find_text_shapes(slides[12]):
        t = s.text.strip()
        if "main results" in t:
            _simple(s, "The numbers that matter:", size=12, color=GRAY)
        elif "Use graphs" in t:
            _clear_and_write(s, [
                ("$196 M / yr", {"size": 22, "bold": True, "color": PINK}),
                ("Citi Bike annual revenue", {"size": 10, "color": GRAY, "space_after": 8}),
                ("11.24 MAE", {"size": 22, "bold": True, "color": BLUE}),
                ("42.5 % better than baseline", {"size": 10, "color": GRAY, "space_after": 8}),
                ("17-month payback", {"size": 22, "bold": True, "color": GREEN}),
                ("250 new stations pay for themselves", {"size": 10, "color": GRAY, "space_after": 8}),
                ("0.987 correlation", {"size": 22, "bold": True, "color": DARK}),
                ("actual vs predicted daily demand", {"size": 10, "color": GRAY}),
            ])

    # ── Slide 14: Business Impact ───────────────────────────────────────
    for s in _find_text_shapes(slides[13]):
        t = s.text.strip()
        if "Move from analysis" in t:
            _simple(s, "From data to dollars:", size=12, color=GRAY)
        elif "AGAIN" in t:
            _clear_and_write(s, [
                ("$11.3 M / yr  net profit", {"size": 18, "bold": True, "color": PINK}),
                ("from 250 new stations", {"size": 10, "color": GRAY, "space_after": 6}),
                ("$32 M investment  ·  17-month payback", {"size": 14, "bold": True, "color": DARK}),
                ("", {"size": 4}),
                ("Public benefit: reduced congestion, lower emissions, better transit for 8.3 M residents", {"size": 10, "color": BLUE}),
            ])

    # ── Slide 15: Recommendations ───────────────────────────────────────
    for s in _find_text_shapes(slides[14]):
        t = s.text.strip()
        if "Strategic Next" in t:
            _simple(s, "Strategic Next Steps", size=12, bold=True, color=DARK)
        elif "Phase 1" in t and "Validate" not in t:
            _simple(s, "Phase 1: Validate", size=11, bold=True, color=BLUE)
        elif "Pilot the solution" in t:
            _clear_and_write(s, [
                ("Deploy 50 stations in top MTA zones.", {"size": 9, "color": DARK}),
                ("Measure actual vs predicted over 6 mo.", {"size": 9, "color": GRAY}),
            ])
        elif "Phase 2" in t and "Scale" not in t:
            _simple(s, "Phase 2: Scale", size=11, bold=True, color=BLUE)
        elif "Expand to additional" in t:
            _clear_and_write(s, [
                ("Roll out 200 remaining stations.", {"size": 9, "color": DARK}),
                ("Integrate real-time MTA delay feeds.", {"size": 9, "color": GRAY}),
            ])
        elif "Phase 3" in t:
            _clear_and_write(s, [
                ("Phase 3: Optimize", {"size": 11, "bold": True, "color": BLUE}),
            ])
        elif "Implementation Roadmap" in t:
            _simple(s, "", size=1)

    # ── Slide 16: Executive Summary ─────────────────────────────────────
    # Three 3.9 × 2.5-inch cards
    for s in _find_text_shapes(slides[15]):
        t = s.text.strip()
        if "Close with" in t:
            _simple(s, "", size=1)
        elif "The Problem" in t and len(t) < 20:
            _simple(s, "The Problem", size=12, bold=True, color=BLUE)
        elif "The Core Insight" in t:
            _simple(s, "The Core Insight", size=12, bold=True, color=BLUE)
        elif "The Value" in t:
            _simple(s, "The Value", size=12, bold=True, color=BLUE)
        elif "Restate the core" in t:
            _clear_and_write(s, [
                ("50 % of stations are maxed out while MTA service deteriorates.", {"size": 10, "color": DARK}),
                ("8.3 M residents need better options.", {"size": 10, "color": GRAY}),
            ])
        elif "Summarize the single" in t:
            _clear_and_write(s, [
                ("Demand is predictable.", {"size": 10, "bold": True, "color": DARK}),
                ("XGBoost forecasts with 11.24 MAE. MTA data shows exactly where to expand.", {"size": 10, "color": GRAY}),
            ])
        elif "State the organizational" in t:
            _clear_and_write(s, [
                ("250 stations → $11.3 M/yr", {"size": 12, "bold": True, "color": PINK}),
                ("17-month payback. SF, DC, and Chicago prove the model.", {"size": 10, "color": DARK}),
            ])

    # ── Slide 17: Thank You ─────────────────────────────────────────────
    for s in _find_text_shapes(slides[16]):
        if "Thank you" in s.text or "Thank You" in s.text:
            _clear_and_write(s, [
                ("Thank You", {"size": 32, "bold": True, "color": DARK}),
                ("", {"size": 10}),
                ("Nathan  ·  Jenny  ·  Nosaifa", {"size": 16, "color": BLUE}),
                ("", {"size": 8}),
                ("citibike-citycycle.streamlit.app", {"size": 14, "color": PINK}),
                ("", {"size": 10}),
                ("Questions?", {"size": 16, "color": GRAY}),
            ], align=PP_ALIGN.CENTER)

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    prs.save(str(OUTPUT))
    print(f"Saved to {OUTPUT}")


if __name__ == "__main__":
    fill_template()
