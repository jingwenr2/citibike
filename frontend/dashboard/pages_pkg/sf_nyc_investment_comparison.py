"""San Francisco Case Study — Investment Outcome, ported from
notebooks/SF_NYC_Investment_Comparison.ipynb.

San Francisco (Bay Wheels) growth analysis around the Feb 2023 MTC
investment and the Nov 2023 price change. NYC/Citi Bike is not used here —
this is a standalone external case study, used as supporting evidence for
the NYC investment case, not a direct cross-city comparison.

Windows tied to specific historical events (the Feb 2023 investment, the
Nov 2023 price change, and 2025 as a no-price-change control year) are
fixed, matching the original notebook analysis. The "most recent 6
months" window and all headline figures are computed live from whatever
data is loaded, rather than frozen at the values the notebook happened to
show when it was written, so this page stays correct as new data arrives.

Visual styling matches the rest of the live tabs-based app.py (st.subheader
+ ".section-note" markdown, native st.metric/st.warning/st.expander)
rather than the unused components/headers.py + components/styles.py CSS
theme, since that theme's CSS is never injected by the live app.
"""
from __future__ import annotations

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st

from components.styles import apply_layout

# SF's MTC investment was $16M nominal in Feb 2023. Since this ROI estimate
# divides by a modern (non-2023) net-revenue-per-trip assumption, the
# investment side is inflation-adjusted to 2026 dollars (~9.4%, consistent
# with the same adjustment used throughout the Government Investment tab)
# rather than mixing 2023 dollars against a current-dollars revenue rate.
INVESTMENT_AMOUNT = 17_500_000

PRICE_HISTORY = [
    {
        "effective_from": pd.Timestamp.min,
        "effective_until": pd.Timestamp("2023-11-02"),
        "membership_price": 169,
        "ebike_per_min_price": 0.20,
    },
    {
        "effective_from": pd.Timestamp("2023-11-02"),
        "effective_until": pd.Timestamp.max,
        "membership_price": 150,
        "ebike_per_min_price": 0.15,
    },
]


def _assign_price_columns(frame: pd.DataFrame, history: list[dict]) -> pd.DataFrame:
    frame = frame.copy()
    frame["membership_price"] = pd.NA
    frame["ebike_per_min_price"] = pd.NA
    for bracket in history:
        mask = (frame["date"] >= bracket["effective_from"]) & (
            frame["date"] < bracket["effective_until"]
        )
        frame.loc[mask, "membership_price"] = bracket["membership_price"]
        frame.loc[mask, "ebike_per_min_price"] = bracket["ebike_per_min_price"]
    return frame


def _seasonal_window_comparison(
    sf: pd.DataFrame,
    pre_period: pd.PeriodIndex,
    post_period: pd.PeriodIndex,
    pre_label: str,
    post_label: str,
) -> pd.DataFrame:
    rows = []
    for label, window in [(pre_label, pre_period), (post_label, post_period)]:
        sub = sf[sf["month"].isin(window)]
        daily = sub.groupby("date").agg(
            trips=("trips", "sum"), stations=("station_name", "nunique")
        )
        daily["trips_per_station"] = daily["trips"] / daily["stations"]
        rows.append(
            {
                "window": label,
                "avg_daily_total_trips": daily["trips"].mean(),
                "avg_active_stations_per_day": daily["stations"].mean(),
                "avg_daily_trips_per_station": daily["trips_per_station"].mean(),
            }
        )
    return pd.DataFrame(rows).set_index("window").round(2)


def _pct_change(before: float, after: float) -> float:
    if not before:
        return 0.0
    return (after - before) / before * 100


def _display_labels(df: pd.DataFrame) -> pd.DataFrame:
    """Snake_case index/column names -> Title Case, for display only.

    Callers keep using the original (snake_case) frame for any further
    lookups (.loc/.iloc by column name) — this returns a renamed copy.
    """
    out = df.copy()
    if out.index.name:
        out.index = out.index.rename(out.index.name.replace("_", " ").title())
    out.columns = [str(c).replace("_", " ").title() for c in out.columns]
    return out


def render(data: pd.DataFrame, net_revenue_per_trip: float) -> None:
    st.subheader("San Francisco Case Study: Investment Outcome")
    st.markdown(
        '<p class="section-note">How San Francisco\'s Bay Wheels network grew '
        "after a $16M public investment from MTC in Feb 2023, used here as "
        "supporting evidence, not a direct NYC comparison.</p>",
        unsafe_allow_html=True,
    )

    sf = data[data["city"] == "San Francisco"].copy()
    if sf.empty:
        st.info("No San Francisco data available in the loaded dataset.")
        return

    sf["month"] = sf["date"].dt.to_period("M")

    st.markdown(
        '<p style="color:#64748B;">Data caveat: <code>2024-06</code> is a '
        "partial/boundary month (a ~1-day artifact from where two separate "
        "download windows meet) and is excluded from the trend below so it "
        "doesn't read as a ridership collapse. The prior Jan–May 2024 gap "
        "has been backfilled.</p>",
        unsafe_allow_html=True,
    )

    # ── Fixed historical windows ──
    post_window = pd.period_range("2023-03", "2023-08", freq="M")
    latest_month = sf["month"].max()
    recent_window = pd.period_range(latest_month - 5, latest_month, freq="M")

    headline = _seasonal_window_comparison(
        sf, post_window, recent_window,
        "Post-Feb-2023 (Mar-Aug 2023)", f"Most recent ({recent_window[0]} to {recent_window[-1]})",
    )
    trips_per_station_growth = _pct_change(
        headline.loc[headline.index[0], "avg_daily_trips_per_station"],
        headline.loc[headline.index[1], "avg_daily_trips_per_station"],
    )
    total_trips_growth = _pct_change(
        headline.loc[headline.index[0], "avg_daily_total_trips"],
        headline.loc[headline.index[1], "avg_daily_total_trips"],
    )

    feb2023_stations = set(
        sf.loc[sf["month"] == pd.Period("2023-02"), "station_name"].unique()
    )
    latest_stations = set(
        sf.loc[sf["month"] == latest_month, "station_name"].unique()
    )
    net_new = latest_stations - feb2023_stations
    lost = feb2023_stations - latest_stations
    station_growth_pct = _pct_change(len(feb2023_stations), len(latest_stations))

    # ── KPI summary ──
    # Keying these "kpi-..." routes them through app.py's shared KPI-row CSS
    # (Ledger tile style, Lyft-pink accent) instead of needing a page-local override.
    with st.container(key="kpi-sf-growth"):
        kpi_cols = st.columns(4)
        kpi_cols[0].metric("Trips/Station Growth", f"{trips_per_station_growth:+.0f}%")
        kpi_cols[1].metric("Total Daily Trips Growth", f"{total_trips_growth:+.0f}%")
        kpi_cols[2].metric("Station Network Growth", f"{station_growth_pct:+.0f}%")
        kpi_cols[3].metric("Stations Today", f"{len(latest_stations):,}")

    # ── ROI estimate ──
    st.markdown("---")
    st.subheader("Estimated ROI on the $17.5M investment")
    st.markdown(
        '<p class="section-note">Applies the same net-operating-revenue-per-trip '
        "assumption used in the Government investment tab to the incremental "
        "ridership observed since Feb 2023. MTC's investment was $16M nominal "
        "at the time; shown here inflation-adjusted to 2026 dollars so it isn't "
        "mixed against a current-dollars revenue-per-trip rate.</p>",
        unsafe_allow_html=True,
    )

    incremental_daily_trips = (
        headline.loc[headline.index[1], "avg_daily_total_trips"]
        - headline.loc[headline.index[0], "avg_daily_total_trips"]
    )
    annualized_incremental_revenue = incremental_daily_trips * 365 * net_revenue_per_trip
    payback_years = (
        INVESTMENT_AMOUNT / annualized_incremental_revenue
        if annualized_incremental_revenue > 0
        else float("inf")
    )

    with st.container(key="kpi-sf-roi"):
        roi_cols = st.columns(3)
        roi_cols[0].metric(
            "Estimated annual incremental revenue",
            f"${annualized_incremental_revenue:,.0f}",
        )
        roi_cols[1].metric("Investment amount", f"${INVESTMENT_AMOUNT:,.0f}")
        roi_cols[2].metric(
            "Estimated payback period",
            f"{payback_years:.1f} years" if payback_years != float("inf") else "N/A",
        )

    st.markdown(
        '<div class="tab-takeaway"><p>'
        "Illustrative estimate only, uses the same revenue-per-trip assumption "
        "as the NYC model. Ridership growth likely reflects multiple factors "
        "beyond the investment alone (Electric rollout, network expansion, "
        "post-pandemic recovery)."
        "</p></div>",
        unsafe_allow_html=True,
    )

    # ── Monthly trend chart ──
    st.markdown("---")
    st.subheader("Monthly ridership trend")
    st.markdown(
        '<p class="section-note">Feb 2023 (MTC investment) and Nov 2023 (price '
        "drop) marked. 2024-06 (a 1-day boundary artifact, not a real drop) is "
        "excluded.</p>",
        unsafe_allow_html=True,
    )

    monthly_trips = (
        sf[sf["month"] != pd.Period("2024-06")]
        .groupby("month")["trips"]
        .sum()
    )
    # Real datetimes on the x-axis, not formatted strings — Plotly's
    # add_vline/add_vrect annotation positioning breaks on a categorical
    # (string) axis (tries to average x-values numerically).
    months_dt = monthly_trips.index.to_timestamp()

    # Linear trend (OLS fit on month index vs. trips) — same amber-dashed
    # "Trend" convention used for the MTA opportunity scatter in app.py.
    month_ordinals = np.arange(len(months_dt))
    slope, intercept = np.polyfit(month_ordinals, monthly_trips.to_numpy(), 1)
    trend_y = slope * month_ordinals + intercept

    # Quarter tick labels ("Q1" over "2023") — Plotly has no built-in
    # quarter tickformat, so build explicit tick positions/labels instead.
    quarter_starts = pd.period_range(
        months_dt.min(), months_dt.max(), freq="Q"
    ).to_timestamp()
    quarter_ticktext = [f"Q{ts.quarter}<br>{ts.year}" for ts in quarter_starts]

    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=months_dt, y=monthly_trips.to_numpy(),
        mode="lines+markers",
        line=dict(color="#FF00BF", width=2),
        name="Total trips",
    ))
    fig.add_trace(go.Scatter(
        x=months_dt, y=trend_y,
        mode="lines",
        line=dict(color="#F59E0B", width=2, dash="dash"),
        name="Trend",
    ))
    fig.add_shape(type="line", x0="2023-02-01", x1="2023-02-01", y0=0, y1=1,
                  yref="paper", line=dict(dash="dash", color="#1B3A6B", width=1))
    fig.add_annotation(x="2023-02-01", y=1, yref="paper", text="Feb 2023: MTC investment",
                       showarrow=False, font=dict(color="#1B3A6B", size=11), yshift=10)
    fig.add_shape(type="line", x0="2023-11-01", x1="2023-11-01", y0=0, y1=1,
                  yref="paper", line=dict(dash="dashdot", color="#7DD3FC", width=1))
    fig.add_annotation(x="2023-11-01", y=1, yref="paper", text="Nov 2023: price drop",
                       showarrow=False, font=dict(color="#7DD3FC", size=11), yshift=10)
    fig.update_xaxes(
        tickangle=0, tickmode="array",
        tickvals=quarter_starts, ticktext=quarter_ticktext,
    )
    fig.update_yaxes(tickangle=0)
    apply_layout(
        fig, height=440,
        title="San Francisco (Bay Wheels): total trips per month",
        margin=dict(l=10, r=10, t=70, b=10),
        plot_bgcolor="white",
    )
    fig.update_layout(title_font_color="#0F172A")
    st.plotly_chart(fig, use_container_width=True)

    # ── Per-station before/after ──
    st.markdown("---")
    st.subheader("Average daily trips per station: right after Feb 2023 vs most recent")
    st.markdown(
        '<p class="section-note">Two equal-length 6-month windows so the '
        "comparison isn't skewed by window size. Per-station, not just total "
        "trips, so network expansion doesn't automatically inflate the growth "
        "story.</p>",
        unsafe_allow_html=True,
    )
    st.dataframe(_display_labels(headline), use_container_width=True)

    # ── Station network size + Findings (side by side) ──
    st.markdown("---")
    network_row = pd.DataFrame(
        {
            "metric": [
                "Stations active in Feb 2023",
                f"Stations active in {latest_month}",
                "Net new stations",
                "Stations no longer active",
                "Net network growth (%)",
            ],
            "value": [
                len(feb2023_stations),
                len(latest_stations),
                len(net_new),
                len(lost),
                round(station_growth_pct, 1),
            ],
        }
    )
    network_cols = st.columns([1, 2])
    with network_cols[0]:
        st.subheader("Station network size: Feb 2023 vs now")
        network_rows_html = "".join(
            f"""
            <tr>
                <td>{row.metric}</td>
                <td style="text-align:right;">{row.value:,.1f}</td>
            </tr>
            """
            for row in network_row.itertuples()
        )
        st.markdown(
            f"""
            <style>
            .sf-network-table {{ width: 100%; border-collapse: collapse; font-size: .85rem; }}
            .sf-network-table th {{
                text-align: left; padding: .35rem .5rem; border-bottom: 1px solid #E5E7EB;
                color: #64748B; font-weight: 600; font-size: .72rem;
                text-transform: uppercase; letter-spacing: .03em;
            }}
            .sf-network-table td {{
                padding: .35rem .5rem; border-bottom: 1px solid #F1F5F9; color: #0F172A;
            }}
            </style>
            <table class="sf-network-table">
                <thead><tr><th>Metric</th><th style="text-align:right;">Value</th></tr></thead>
                <tbody>{network_rows_html}</tbody>
            </table>
            """,
            unsafe_allow_html=True,
        )

    with network_cols[1]:
        st.subheader("Findings")
        st.markdown(
            f"""
- **Ridership per station grew {trips_per_station_growth:+.0f}%** from the
  post-Feb-2023 window to the most recent window, per-station, so it isn't
  just "more stations means more trips."
- **Total daily ridership grew {total_trips_growth:+.0f}%** over the same
  period, reflecting both more trips per station and a larger network.
- **The network grew {station_growth_pct:+.0f}%**: {len(feb2023_stations)}
  active stations in Feb 2023 vs {len(latest_stations)} in {latest_month}
  ({len(net_new)} net-new, {len(lost)} no longer active).
- **The Nov 2023 price drop does not show a clean ridership response.**
  Seasonality dominates the Sep-Oct → Nov-Dec window in both the event year
  and the no-change control year, the data doesn't support a "the price
  drop grew ridership" claim, though it's weakly consistent with the drop
  softening the usual seasonal decline.
            """
        )

    st.caption(
        "Note: the Jan–May 2024 gap that previously affected this dataset has "
        "been backfilled. The Nov 2023 \"after\" window is still kept at 2 "
        "months (Nov-Dec 2023) to match the 2-month \"before\" window "
        "(Sep-Oct 2023) for a symmetric comparison, that's a methodology "
        "choice now, not a data limitation."
    )

    # ── Nov 2023 price-drop methodology (de-emphasized, collapsed) ──
    with st.expander(
        "Methodology: ruling out the Nov 2023 price change as the growth driver"
    ):
        st.markdown("**Price history: the Nov 2023 fare change**")
        st.markdown(
            '<p class="section-note">Bay Wheels changed pricing on 2023-11-02: '
            "annual membership $169 -> $150, Electric per-minute rate $0.20 -> "
            "$0.15. Published pricing, mapped onto each row by date via an "
            "explicit lookup table.</p>",
            unsafe_allow_html=True,
        )
        sf = _assign_price_columns(sf, PRICE_HISTORY)
        price_check = (
            sf.groupby(["membership_price", "ebike_per_min_price"])["date"]
            .agg(["min", "max", "count"])
            .rename_axis(index={"ebike_per_min_price": "Electric per-min price"})
        )
        st.dataframe(price_check, use_container_width=True)

        st.markdown("**Ridership before vs after the Nov 2023 price drop**")
        st.markdown(
            '<p class="section-note">Two symmetric 2-month windows immediately '
            "adjacent to the change. This window also spans a known seasonal "
            "transition, so the same Sep-Oct -> Nov-Dec comparison is also run "
            "for 2025 (no price change that year) as a control for how much of "
            "any 2023 change is just seasonality rather than price.</p>",
            unsafe_allow_html=True,
        )

        price_change_comparison = _seasonal_window_comparison(
            sf,
            pd.period_range("2023-09", "2023-10", freq="M"),
            pd.period_range("2023-11", "2023-12", freq="M"),
            "2023: Before price drop (Sep-Oct, $169/$0.20)",
            "2023: After price drop (Nov-Dec, $150/$0.15)",
        )
        seasonal_control_comparison = _seasonal_window_comparison(
            sf,
            pd.period_range("2025-09", "2025-10", freq="M"),
            pd.period_range("2025-11", "2025-12", freq="M"),
            "2025 control: Sep-Oct (no price change)",
            "2025 control: Nov-Dec (no price change)",
        )

        price_col, control_col = st.columns(2)
        with price_col:
            st.markdown("**2023 price-drop window**")
            st.dataframe(_display_labels(price_change_comparison), use_container_width=True)
        with control_col:
            st.markdown("**2025 seasonality control**")
            st.dataframe(_display_labels(seasonal_control_comparison), use_container_width=True)

        price_2023_before = price_change_comparison.iloc[0]["avg_daily_trips_per_station"]
        price_2023_after = price_change_comparison.iloc[1]["avg_daily_trips_per_station"]
        control_before = seasonal_control_comparison.iloc[0]["avg_daily_trips_per_station"]
        control_after = seasonal_control_comparison.iloc[1]["avg_daily_trips_per_station"]
        price_2023_pct = _pct_change(price_2023_before, price_2023_after)
        control_pct = _pct_change(control_before, control_after)

        st.markdown(
            '<div style="background:#FDF1F8; border-left:4px solid #FF00BF; '
            'padding:1rem 1.25rem; border-radius:0 12px 12px 0; margin:0 0 1.2rem 0;">'
            '<p style="margin:0; font-size:.95rem; color:#334155; line-height:1.5;">'
            '<strong style="color:#7A1263;">Reading the two tables together:</strong> '
            "avg daily trips per station "
            f"fell from Sep-Oct to Nov-Dec in <em>both</em> 2023 ({price_2023_before:.1f} "
            f"→ {price_2023_after:.1f}, about {price_2023_pct:+.0f}%) and 2025 "
            f"({control_before:.1f} → {control_after:.1f}, about "
            f"{control_pct:+.0f}%), even though 2025 had no price change at all "
            "in that window. That means the raw 2023 before/after "
            '<strong style="color:#7A1263;">cannot be '
            'read as "the price drop hurt ridership"</strong>, seasonality alone '
            "predicts a comparable or larger drop than what was actually "
            "observed."
            "</p></div>",
            unsafe_allow_html=True,
        )
