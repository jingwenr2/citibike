"""Citi Bike Growth Intelligence — Streamlit Dashboard Orchestrator."""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd
import streamlit as st

# ── Path setup ──
ROOT = Path(__file__).resolve().parents[2]
DASHBOARD = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(DASHBOARD))

from backend.services import data_service, demand_service, revenue_service
from backend.services.opportunity_service import compute_mta_transit_scores
from backend.utils.paths import DAILY_DATA_PATH, HOURLY_DATA_PATH, MTA_DATA_PATH

from components.styles import inject_css
from components.navigation import render_sidebar

# ── Page config ──
st.set_page_config(
    page_title="Citi Bike Growth Intelligence",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_css()

DAY_ORDER = demand_service.DAY_ORDER
PEAK_HOURS = demand_service.PEAK_HOURS

CITY_META = {
    "New York City": {
        "system": "Citi Bike",
        "color": "#2D7FF9",
        "center": (40.7306, -73.9866),
        "base": 1180,
        "stations": [
            ("Broadway & W 25 St", 40.7429, -73.9892),
            ("West St & Chambers St", 40.7175, -74.0132),
            ("E 17 St & Broadway", 40.7370, -73.9901),
            ("1 Ave & E 68 St", 40.7650, -73.9570),
            ("Bedford Ave & Nassau Ave", 40.7231, -73.9521),
            ("Crescent St & 30 Ave", 40.7687, -73.9240),
        ],
    },
    "San Francisco": {
        "system": "Bay Wheels",
        "color": "#F26B4A",
        "center": (37.7749, -122.4194),
        "base": 560,
        "stations": [
            ("Market St at 10th St", 37.7766, -122.4174),
            ("San Francisco Caltrain", 37.7764, -122.3943),
            ("The Embarcadero at Sansome St", 37.8048, -122.4032),
            ("Powell St BART", 37.7844, -122.4078),
            ("Valencia St at 24th St", 37.7524, -122.4206),
            ("Berry St at 4th St", 37.7759, -122.3932),
        ],
    },
}


# ══════════════════════════════════════════════════════════════════════
# DATA LOADING (cached)
# ══════════════════════════════════════════════════════════════════════

@st.cache_data
def make_demo_data() -> pd.DataFrame:
    rng = np.random.default_rng(42)
    dates = pd.date_range("2025-01-01", periods=365, freq="D")
    rows: list[dict] = []
    for city, meta in CITY_META.items():
        for station_index, (station, lat, lon) in enumerate(meta["stations"]):
            station_factor = 0.68 + station_index * 0.105
            for date in dates:
                day_angle = 2 * np.pi * date.dayofyear / 365
                seasonal = 1 + 0.31 * np.sin(day_angle - 1.15)
                weekend = 0.82 if date.dayofweek >= 5 else 1.0
                trend = 1 + 0.00045 * date.dayofyear
                noise = rng.normal(1, 0.09)
                trips = max(35, int(meta["base"] * station_factor * seasonal * weekend * trend * noise))
                member_share = 0.77 if city == "New York City" else 0.71
                electric_share = 0.43 if city == "New York City" else 0.52
                for rider_type, share in (("Member", member_share), ("Casual", 1 - member_share)):
                    rider_trips = int(trips * share)
                    rows.append({
                        "date": date, "city": city, "system": meta["system"],
                        "station_name": station, "lat": lat, "lon": lon,
                        "rider_type": rider_type, "trips": rider_trips,
                        "electric_trips": int(rider_trips * electric_share),
                        "capacity": 22 + station_index * 4, "is_demo": True,
                    })
    return pd.DataFrame(rows)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DAILY_DATA_PATH.exists():
        return make_demo_data()
    try:
        frame = data_service.load_daily_data()
    except Exception as exc:
        st.error(str(exc))
        st.stop()
    frame["is_demo"] = False
    return frame


@st.cache_data
def load_mta_signal() -> pd.DataFrame:
    try:
        frame = data_service.load_mta_opportunity_data()
    except Exception as exc:
        st.error(str(exc))
        st.stop()
    if frame.empty:
        return pd.DataFrame(
            [
                ("Broadway & W 25 St", "Chelsea", 58_000, 0.12),
                ("West St & Chambers St", "Lower Manhattan", 72_000, 0.09),
                ("E 17 St & Broadway", "Union Square", 95_000, 0.14),
                ("1 Ave & E 68 St", "Upper East Side", 82_000, 0.11),
                ("Bedford Ave & Nassau Ave", "Greenpoint", 41_000, 0.18),
                ("Crescent St & 30 Ave", "Astoria", 63_000, 0.21),
            ],
            columns=["station_name", "neighborhood", "mta_daily_riders", "mta_delay_rate"],
        ).assign(mta_is_demo=True)
    return frame


@st.cache_data
def make_demo_hourly() -> pd.DataFrame:
    rng = np.random.default_rng(7)
    rows: list[dict] = []
    reference_monday = pd.Timestamp("2026-01-05")
    for day_index, day in enumerate(DAY_ORDER):
        weekend = day_index >= 5
        demo_date = reference_monday + pd.Timedelta(days=day_index)
        for hour in range(24):
            morning_peak = np.exp(-((hour - 8) ** 2) / 6)
            evening_peak = np.exp(-((hour - 18) ** 2) / 6)
            midday_lull = 0.28 * np.exp(-((hour - 13) ** 2) / 30)
            base = 650 if weekend else 950
            shape = (0.45 if weekend else 1.0) * (morning_peak + evening_peak) + midday_lull + 0.06
            trips = max(20, base * shape * float(rng.normal(1, 0.05)))
            rows.append({"date": demo_date, "day_name": day, "hour": hour, "rider_type": "Member", "trips": trips * 0.78})
            rows.append({"date": demo_date, "day_name": day, "hour": hour, "rider_type": "Casual", "trips": trips * 0.22})
    frame = pd.DataFrame(rows)
    frame["hourly_is_demo"] = True
    return frame


@st.cache_data
def load_hourly_demand() -> pd.DataFrame:
    if not HOURLY_DATA_PATH.exists():
        return make_demo_hourly()
    try:
        frame = data_service.load_hourly_data()
    except Exception as exc:
        st.error(str(exc))
        st.stop()
    frame["hourly_is_demo"] = False
    return frame


# ══════════════════════════════════════════════════════════════════════
# DATA PREPARATION
# ══════════════════════════════════════════════════════════════════════

data = load_data()
is_demo = bool(data["is_demo"].all())
hourly = load_hourly_demand()

# ── Sidebar filters ──
active_page = render_sidebar(
    data_period=f"{data['date'].min():%b %Y} – {data['date'].max():%b %Y}"
)

with st.sidebar:
    st.markdown("<hr style='border-color:#1E293B;margin:.5rem 0;'>", unsafe_allow_html=True)
    min_date = data["date"].min().date()
    max_date = data["date"].max().date()
    selected_dates = st.date_input(
        "Date range", value=(min_date, max_date),
        min_value=min_date, max_value=max_date,
    )
    if isinstance(selected_dates, tuple) and len(selected_dates) == 2:
        start_date, end_date = selected_dates
    else:
        start_date, end_date = min_date, max_date

    rider_types = st.multiselect(
        "Rider type",
        options=sorted(data["rider_type"].unique()),
        default=sorted(data["rider_type"].unique()),
    )
    smoothing = st.slider("Trend smoothing", 1, 28, 7, help="Rolling average in days")

# ── Apply filters ──
city_options = list(CITY_META)
filtered = data[
    data["city"].isin(city_options)
    & data["rider_type"].isin(rider_types)
    & data["date"].between(pd.Timestamp(start_date), pd.Timestamp(end_date))
].copy()

if filtered.empty:
    st.warning("No data matches the current filters. Try a wider date range.")
    st.stop()

nyc_filtered = filtered[filtered["city"] == "New York City"].copy()
if nyc_filtered.empty:
    st.warning("No New York City data matches the current filters.")
    st.stop()

# ── MTA opportunity scores ──
mta_signal = load_mta_signal()
nyc_station_daily = (
    nyc_filtered.groupby("station_name", as_index=False)["trips"]
    .sum()
    .assign(observed_days=nyc_filtered["date"].nunique())
)
nyc_station_daily["bike_daily_trips"] = (
    nyc_station_daily["trips"] / nyc_station_daily["observed_days"]
)
mta_opportunity = compute_mta_transit_scores(mta_signal, nyc_station_daily)

# ── Shared computations ──
active_stations = nyc_filtered["station_name"].nunique()
station_summary_df = demand_service.station_summary(nyc_filtered)
rev = revenue_service.estimate_annual_revenue(nyc_filtered)
delta = demand_service.prior_period_delta(nyc_filtered, data)


# ══════════════════════════════════════════════════════════════════════
# PAGE ROUTING
# ══════════════════════════════════════════════════════════════════════

if active_page == "executive_overview":
    from pages_pkg.executive_overview import render
    render(nyc_filtered, mta_opportunity, station_summary_df, rev, delta, is_demo, demand_service)

elif active_page == "network_performance":
    from pages_pkg.network_performance import render
    render(nyc_filtered, filtered, hourly, smoothing, is_demo, demand_service)

elif active_page == "demand_forecast":
    from pages_pkg.demand_forecast import render
    render(nyc_filtered, is_demo)

elif active_page == "transit_connections":
    from pages_pkg.transit_connections import render
    render(mta_opportunity, mta_signal, nyc_filtered, is_demo)

elif active_page == "station_opportunities":
    from pages_pkg.station_opportunities import render
    render(nyc_filtered, mta_opportunity, station_summary_df, demand_service)

elif active_page == "investment_strategy":
    from pages_pkg.investment_strategy import render
    render(nyc_filtered, mta_opportunity, is_demo)

elif active_page == "investment_impact":
    from pages_pkg.investment_impact import render
    render(nyc_filtered, rev, active_stations, is_demo)

elif active_page == "investment_opportunity":
    from pages_pkg.investment_opportunity import render
    render(nyc_filtered, active_stations, is_demo)

elif active_page == "evidence_cities":
    from pages_pkg.evidence_cities import render
    render()

elif active_page == "data_methodology":
    from pages_pkg.data_methodology import render
    render(is_demo, DAILY_DATA_PATH, HOURLY_DATA_PATH, MTA_DATA_PATH)
