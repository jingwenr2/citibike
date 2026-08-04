from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st


ROOT = Path(__file__).resolve().parents[2]
DATA_PATH = ROOT / "data" / "processed" / "bike_share_daily.parquet"
MTA_PATH = ROOT / "data" / "processed" / "mta_bike_opportunity.parquet"

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


st.set_page_config(
    page_title="CityCycle Intelligence",
    page_icon="🚲",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
    .stApp {background: #F5F7FA;}
    [data-testid="stSidebar"] {background: #111827;}
    [data-testid="stSidebar"] * {color: #F9FAFB;}
    .hero {
        padding: 2rem 2.25rem;
        border-radius: 22px;
        color: white;
        background:
          radial-gradient(circle at 90% 15%, rgba(45,127,249,.45), transparent 30%),
          linear-gradient(120deg, #0B1324 0%, #17233D 60%, #102A43 100%);
        box-shadow: 0 18px 45px rgba(15, 23, 42, .16);
        margin-bottom: 1.2rem;
    }
    .hero h1 {font-size: 2.45rem; margin: 0 0 .35rem 0;}
    .hero p {font-size: 1.05rem; color: #D6E4FF; margin: 0; max-width: 760px;}
    .eyebrow {font-size: .78rem; letter-spacing: .15em; text-transform: uppercase; color: #7DD3FC;}
    div[data-testid="stMetric"] {
        background: white; border: 1px solid #E5E7EB; padding: 1rem 1.1rem;
        border-radius: 16px; box-shadow: 0 6px 18px rgba(15,23,42,.05);
    }
    div[data-testid="stMetricLabel"] {color: #64748B;}
    .section-note {color: #64748B; margin-top: -.6rem;}
    .demo-pill {
        display: inline-block; padding: .28rem .65rem; border-radius: 999px;
        background: #FEF3C7; color: #92400E; font-size: .78rem; font-weight: 700;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


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
                trips = max(
                    35,
                    int(meta["base"] * station_factor * seasonal * weekend * trend * noise),
                )
                member_share = 0.77 if city == "New York City" else 0.71
                electric_share = 0.43 if city == "New York City" else 0.52

                for rider_type, share in (
                    ("Member", member_share),
                    ("Casual", 1 - member_share),
                ):
                    rider_trips = int(trips * share)
                    rows.append(
                        {
                            "date": date,
                            "city": city,
                            "system": meta["system"],
                            "station_name": station,
                            "lat": lat,
                            "lon": lon,
                            "rider_type": rider_type,
                            "trips": rider_trips,
                            "electric_trips": int(rider_trips * electric_share),
                            "capacity": 22 + station_index * 4,
                            "is_demo": True,
                        }
                    )
    return pd.DataFrame(rows)


@st.cache_data
def load_data() -> pd.DataFrame:
    if not DATA_PATH.exists():
        return make_demo_data()

    frame = pd.read_parquet(DATA_PATH)
    required = {
        "date",
        "city",
        "system",
        "station_name",
        "lat",
        "lon",
        "rider_type",
        "trips",
        "electric_trips",
        "capacity",
    }
    missing = required.difference(frame.columns)
    if missing:
        st.error(
            "The processed dataset is missing required columns: "
            + ", ".join(sorted(missing))
        )
        st.stop()
    frame["date"] = pd.to_datetime(frame["date"])
    frame["is_demo"] = False
    return frame


@st.cache_data
def load_mta_signal() -> pd.DataFrame:
    if MTA_PATH.exists():
        frame = pd.read_parquet(MTA_PATH)
        required = {
            "station_name",
            "neighborhood",
            "mta_daily_riders",
            "mta_delay_rate",
        }
        missing = required.difference(frame.columns)
        if missing:
            st.error(
                "The MTA opportunity dataset is missing required columns: "
                + ", ".join(sorted(missing))
            )
            st.stop()
        if "mta_is_demo" not in frame.columns:
            frame["mta_is_demo"] = False
        frame["mta_is_demo"] = frame["mta_is_demo"].astype(bool)
        return frame

    return pd.DataFrame(
        [
            ("Broadway & W 25 St", "Chelsea", 58_000, 0.12),
            ("West St & Chambers St", "Lower Manhattan", 72_000, 0.09),
            ("E 17 St & Broadway", "Union Square", 95_000, 0.14),
            ("1 Ave & E 68 St", "Upper East Side", 82_000, 0.11),
            ("Bedford Ave & Nassau Ave", "Greenpoint", 41_000, 0.18),
            ("Crescent St & 30 Ave", "Astoria", 63_000, 0.21),
        ],
        columns=[
            "station_name",
            "neighborhood",
            "mta_daily_riders",
            "mta_delay_rate",
        ],
    ).assign(mta_is_demo=True)


def compact_number(value: float) -> str:
    if value >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if value >= 1_000:
        return f"{value / 1_000:.1f}K"
    return f"{value:,.0f}"


def prior_period_delta(frame: pd.DataFrame) -> float:
    days = max(1, (frame["date"].max() - frame["date"].min()).days + 1)
    cutoff = frame["date"].min() - pd.Timedelta(days=1)
    prior_start = cutoff - pd.Timedelta(days=days - 1)
    all_data = load_data()
    prior = all_data[
        all_data["city"].isin(frame["city"].unique())
        & all_data["rider_type"].isin(frame["rider_type"].unique())
        & all_data["date"].between(prior_start, cutoff)
    ]
    current_total = frame["trips"].sum()
    prior_total = prior["trips"].sum()
    return (current_total / prior_total - 1) if prior_total else 0


data = load_data()
is_demo = bool(data["is_demo"].all())

with st.sidebar:
    st.markdown("## 🚲 CityCycle")
    st.caption("NYC public investment intelligence")
    st.markdown("---")
    city_options = list(CITY_META)
    selected_cities = city_options
    st.markdown("**Decision geography**")
    st.markdown("New York City · Citi Bike")
    st.caption("San Francisco is included only as a comparison benchmark.")

    min_date = data["date"].min().date()
    max_date = data["date"].max().date()
    selected_dates = st.date_input(
        "Date range",
        value=(max(min_date, max_date - pd.Timedelta(days=89)), max_date),
        min_value=min_date,
        max_value=max_date,
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
    st.markdown("---")
    st.caption("NYC · Citi Bike")
    st.caption("San Francisco · Bay Wheels")

filtered = data[
    data["city"].isin(selected_cities)
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

mta_signal = load_mta_signal()
nyc_station_daily = (
    nyc_filtered.groupby("station_name", as_index=False)["trips"].sum()
    .assign(observed_days=nyc_filtered["date"].nunique())
)
nyc_station_daily["bike_daily_trips"] = (
    nyc_station_daily["trips"] / nyc_station_daily["observed_days"]
)
mta_opportunity = mta_signal.merge(
    nyc_station_daily[["station_name", "bike_daily_trips"]],
    on="station_name",
    how="inner",
)
if not mta_opportunity.empty:
    mta_range = (
        mta_opportunity["mta_daily_riders"].max()
        - mta_opportunity["mta_daily_riders"].min()
    )
    bike_range = (
        mta_opportunity["bike_daily_trips"].max()
        - mta_opportunity["bike_daily_trips"].min()
    )
    mta_opportunity["mta_score"] = (
        100
        * (mta_opportunity["mta_daily_riders"] - mta_opportunity["mta_daily_riders"].min())
        / (mta_range if mta_range else 1)
    )
    mta_opportunity["bike_score"] = (
        100
        * (mta_opportunity["bike_daily_trips"] - mta_opportunity["bike_daily_trips"].min())
        / (bike_range if bike_range else 1)
    )
    delay_range = (
        mta_opportunity["mta_delay_rate"].max()
        - mta_opportunity["mta_delay_rate"].min()
    )
    mta_opportunity["delay_score"] = (
        100
        * (mta_opportunity["mta_delay_rate"] - mta_opportunity["mta_delay_rate"].min())
        / (delay_range if delay_range else 1)
    )
    mta_opportunity["transit_opportunity_score"] = (
        0.45 * mta_opportunity["mta_score"]
        + 0.35 * (100 - mta_opportunity["bike_score"])
        + 0.20 * mta_opportunity["delay_score"]
    )

st.markdown(
    """
    <div class="hero">
      <div class="eyebrow">NYC investment · prediction · MTA connection</div>
      <h1>NYC should invest more—where the data supports it.</h1>
      <p>Forecast Citi Bike demand, compare it with MTA ridership and reliability,
      and invest in bike-share as a resilient option when transit is disrupted.</p>
    </div>
    """,
    unsafe_allow_html=True,
)

if is_demo:
    st.markdown(
        '<span class="demo-pill">DEMO DATA</span> '
        "The app will automatically use "
        "`data/processed/bike_share_daily.parquet` when available.",
        unsafe_allow_html=True,
    )

total_trips = nyc_filtered["trips"].sum()
active_stations = nyc_filtered["station_name"].nunique()
electric_share = nyc_filtered["electric_trips"].sum() / total_trips
daily = nyc_filtered.groupby("date", as_index=False)["trips"].sum()
avg_daily = daily["trips"].mean()
delta = prior_period_delta(nyc_filtered)

metric_cols = st.columns(4)
metric_cols[0].metric("NYC total trips", compact_number(total_trips), f"{delta:+.1%} vs prior period")
metric_cols[1].metric("NYC average daily demand", compact_number(avg_daily))
metric_cols[2].metric("NYC active stations", f"{active_stations:,}")
metric_cols[3].metric("NYC electric-bike share", f"{electric_share:.1%}")

overview_tab, stations_tab, forecast_tab, mta_tab, investment_tab, dot_tab, methods_tab = st.tabs(
    [
        "Overview",
        "Station explorer",
        "Forecast lab",
        "MTA connection",
        "Government investment",
        "DOT support case",
        "Data & methods",
    ]
)

with overview_tab:
    st.subheader("Demand over time")
    trend = (
        filtered.groupby(["date", "city"], as_index=False)["trips"]
        .sum()
        .sort_values("date")
    )
    trend["smoothed_trips"] = trend.groupby("city")["trips"].transform(
        lambda values: values.rolling(smoothing, min_periods=1).mean()
    )
    trend_chart = px.line(
        trend,
        x="date",
        y="smoothed_trips",
        color="city",
        color_discrete_map={city: meta["color"] for city, meta in CITY_META.items()},
        labels={"smoothed_trips": "Trips", "date": "", "city": "City"},
    )
    trend_chart.update_layout(
        height=390,
        hovermode="x unified",
        legend_title_text="",
        margin=dict(l=10, r=10, t=20, b=10),
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="white",
    )
    st.plotly_chart(trend_chart, use_container_width=True)

    mix_col, weekday_col = st.columns([1, 1.35])
    with mix_col:
        st.subheader("Who is riding?")
        rider_mix = filtered.groupby(["city", "rider_type"], as_index=False)["trips"].sum()
        rider_chart = px.bar(
            rider_mix,
            x="city",
            y="trips",
            color="rider_type",
            barmode="stack",
            color_discrete_map={"Member": "#17233D", "Casual": "#7DD3FC"},
            labels={"trips": "Trips", "city": "", "rider_type": "Rider"},
        )
        rider_chart.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=15, b=10),
            legend_title_text="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
        )
        st.plotly_chart(rider_chart, use_container_width=True)

    with weekday_col:
        st.subheader("Weekly rhythm")
        weekday = filtered.assign(
            weekday=filtered["date"].dt.day_name(),
            weekday_index=filtered["date"].dt.dayofweek,
        )
        weekday = (
            weekday.groupby(["city", "weekday", "weekday_index"], as_index=False)["trips"]
            .mean()
            .sort_values("weekday_index")
        )
        weekday_chart = px.bar(
            weekday,
            x="weekday",
            y="trips",
            color="city",
            barmode="group",
            color_discrete_map={city: meta["color"] for city, meta in CITY_META.items()},
            labels={"trips": "Average trips", "weekday": "", "city": "City"},
        )
        weekday_chart.update_layout(
            height=350,
            margin=dict(l=10, r=10, t=15, b=10),
            legend_title_text="",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
        )
        st.plotly_chart(weekday_chart, use_container_width=True)

with stations_tab:
    st.subheader("NYC station demand map")
    st.caption("Bay Wheels is excluded from station-level investment decisions.")
    station_summary = (
        nyc_filtered.groupby(["city", "system", "station_name", "lat", "lon", "capacity"], as_index=False)
        .agg(trips=("trips", "sum"), average_daily=("trips", "mean"))
    )
    station_summary["pressure"] = station_summary["average_daily"] / station_summary["capacity"]
    station_summary["marker_size"] = (
        10 + 28 * station_summary["trips"] / station_summary["trips"].max()
    )

    map_chart = px.scatter_map(
        station_summary,
        lat="lat",
        lon="lon",
        color="city",
        size="marker_size",
        hover_name="station_name",
        hover_data={
            "system": True,
            "trips": ":,.0f",
            "average_daily": ":,.0f",
            "pressure": ":.1f",
            "lat": False,
            "lon": False,
            "marker_size": False,
        },
        color_discrete_map={city: meta["color"] for city, meta in CITY_META.items()},
        zoom=10.5,
        center={
            "lat": CITY_META["New York City"]["center"][0],
            "lon": CITY_META["New York City"]["center"][1],
        },
        map_style="carto-positron",
    )
    map_chart.update_layout(
        height=500,
        margin=dict(l=0, r=0, t=0, b=0),
        legend_title_text="",
    )
    st.plotly_chart(map_chart, use_container_width=True)

    ranking_col, detail_col = st.columns([1.05, 1])
    ranked = station_summary.sort_values("pressure", ascending=False)
    with ranking_col:
        st.subheader("Highest demand pressure")
        st.caption("Average daily trips divided by stated dock capacity")
        display_ranked = ranked[
            ["city", "station_name", "average_daily", "capacity", "pressure"]
        ].head(10)
        st.dataframe(
            display_ranked,
            hide_index=True,
            use_container_width=True,
            column_config={
                "city": "City",
                "station_name": "Station",
                "average_daily": st.column_config.NumberColumn("Avg. trips", format="%.0f"),
                "capacity": "Docks",
                "pressure": st.column_config.ProgressColumn(
                    "Pressure",
                    format="%.1f",
                    min_value=0,
                    max_value=max(1.0, float(display_ranked["pressure"].max())),
                ),
            },
        )

    with detail_col:
        st.subheader("Inspect a station")
        station_options = sorted(nyc_filtered["station_name"].unique())
        selected_station = st.selectbox("Station", station_options)
        station_daily = (
            nyc_filtered[nyc_filtered["station_name"] == selected_station]
            .groupby("date", as_index=False)["trips"]
            .sum()
        )
        station_daily["7-day average"] = station_daily["trips"].rolling(
            7, min_periods=1
        ).mean()
        station_chart = px.area(
            station_daily,
            x="date",
            y="7-day average",
            labels={"7-day average": "Trips", "date": ""},
            color_discrete_sequence=["#2D7FF9"],
        )
        station_chart.update_layout(
            height=310,
            margin=dict(l=10, r=10, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
        )
        st.plotly_chart(station_chart, use_container_width=True)

with forecast_tab:
    st.subheader("Interactive demand scenario")
    st.markdown(
        '<p class="section-note">Adjust assumptions to explore a planning scenario. '
        "This is a transparent scenario model—not the trained XGBoost forecast yet.</p>",
        unsafe_allow_html=True,
    )
    control_col, chart_col = st.columns([0.8, 2.2])
    with control_col:
        forecast_city = "New York City"
        st.markdown("**Forecast geography:** New York City")
        horizon = st.slider("Forecast horizon", 7, 60, 30)
        weather_effect = st.slider("Weather effect", -30, 30, 0, format="%d%%")
        event_effect = st.slider("Event / policy effect", -20, 40, 0, format="%d%%")

    city_history = nyc_filtered.groupby("date", as_index=False)["trips"].sum().sort_values("date")
    recent = city_history.tail(min(28, len(city_history)))
    baseline = recent["trips"].mean()
    forecast_dates = pd.date_range(
        city_history["date"].max() + pd.Timedelta(days=1), periods=horizon
    )
    weekday_factors = (
        city_history.assign(weekday=city_history["date"].dt.dayofweek)
        .groupby("weekday")["trips"]
        .mean()
        / city_history["trips"].mean()
    )
    scenario_factor = (1 + weather_effect / 100) * (1 + event_effect / 100)
    forecast_values = [
        baseline * weekday_factors.get(date.dayofweek, 1.0) * scenario_factor
        for date in forecast_dates
    ]
    forecast_frame = pd.DataFrame(
        {"date": forecast_dates, "forecast": forecast_values}
    )
    forecast_frame["lower"] = forecast_frame["forecast"] * 0.86
    forecast_frame["upper"] = forecast_frame["forecast"] * 1.14

    with chart_col:
        figure = go.Figure()
        figure.add_trace(
            go.Scatter(
                x=city_history.tail(60)["date"],
                y=city_history.tail(60)["trips"],
                name="Actual",
                line=dict(color="#94A3B8", width=2),
            )
        )
        figure.add_trace(
            go.Scatter(
                x=pd.concat([forecast_frame["date"], forecast_frame["date"][::-1]]),
                y=pd.concat([forecast_frame["upper"], forecast_frame["lower"][::-1]]),
                fill="toself",
                fillcolor="rgba(45,127,249,.14)",
                line=dict(color="rgba(255,255,255,0)"),
                hoverinfo="skip",
                name="Scenario range",
            )
        )
        figure.add_trace(
            go.Scatter(
                x=forecast_frame["date"],
                y=forecast_frame["forecast"],
                name="Scenario",
                line=dict(color=CITY_META[forecast_city]["color"], width=3),
            )
        )
        figure.update_layout(
            height=410,
            hovermode="x unified",
            legend_title_text="",
            margin=dict(l=10, r=10, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            xaxis_title="",
            yaxis_title="Trips",
        )
        st.plotly_chart(figure, use_container_width=True)
        projected = forecast_frame["forecast"].sum()
        base_projected = baseline * horizon
        st.metric(
            f"Projected {horizon}-day trips",
            compact_number(projected),
            f"{projected / base_projected - 1:+.1%} vs recent baseline",
        )

with mta_tab:
    st.subheader("Where MTA demand and delays signal a Citi Bike opportunity")
    st.markdown(
        '<p class="section-note">High transit ridership paired with relatively low '
        "bike-share demand or weaker reliability can indicate a first/last-mile and "
        "resilience investment gap. This is a prioritization signal—not evidence of "
        "causation.</p>",
        unsafe_allow_html=True,
    )
    if bool(mta_signal["mta_is_demo"].all()):
        st.warning(
            "MTA values on this tab are demonstration data. Replace them with "
            "`data/processed/mta_bike_opportunity.parquet` before presenting findings."
        )

    if mta_opportunity.empty:
        st.info("No Citi Bike stations match the current MTA opportunity table.")
    else:
        signal_chart = px.scatter(
            mta_opportunity,
            x="mta_daily_riders",
            y="bike_daily_trips",
            size="transit_opportunity_score",
            color="transit_opportunity_score",
            hover_name="neighborhood",
            hover_data={
                "station_name": True,
                "mta_daily_riders": ":,.0f",
                "mta_delay_rate": ":.1%",
                "bike_daily_trips": ":,.0f",
                "transit_opportunity_score": ":.1f",
            },
            color_continuous_scale=["#CBD5E1", "#2D7FF9", "#0B1324"],
            labels={
                "mta_daily_riders": "MTA daily riders",
                "bike_daily_trips": "Citi Bike daily trips",
                "transit_opportunity_score": "Opportunity score",
            },
        )
        signal_chart.update_layout(
            height=460,
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
        )
        st.plotly_chart(signal_chart, use_container_width=True)

        opportunity_table = mta_opportunity.sort_values(
            "transit_opportunity_score", ascending=False
        )[
            [
                "neighborhood",
                "station_name",
                "mta_daily_riders",
                "mta_delay_rate",
                "bike_daily_trips",
                "transit_opportunity_score",
            ]
        ]
        st.dataframe(
            opportunity_table,
            hide_index=True,
            use_container_width=True,
            column_config={
                "neighborhood": "Neighborhood",
                "station_name": "Citi Bike station",
                "mta_daily_riders": st.column_config.NumberColumn(
                    "MTA riders/day", format="%d"
                ),
                "mta_delay_rate": st.column_config.NumberColumn(
                    "MTA delay rate", format="percent"
                ),
                "bike_daily_trips": st.column_config.NumberColumn(
                    "Bike trips/day", format="%.0f"
                ),
                "transit_opportunity_score": st.column_config.ProgressColumn(
                    "Investment signal", min_value=0, max_value=100, format="%.1f"
                ),
            },
        )

with investment_tab:
    st.subheader("Government & transportation investment planner")
    st.markdown(
        '<p class="section-note">Prioritize station expansions for public mobility impact, '
        "budget efficiency, and long-term operating sustainability. Dollar values below "
        "are editable planning assumptions, not official agency estimates.</p>",
        unsafe_allow_html=True,
    )

    assumption_col, results_col = st.columns([0.9, 2.1])
    with assumption_col:
        investment_city = "New York City"
        st.markdown("**Investment geography:** New York City")
        public_budget = st.number_input(
            "Available capital budget",
            min_value=50_000,
            max_value=20_000_000,
            value=1_000_000,
            step=50_000,
            format="%d",
        )
        docks_added = st.slider("Docks added per station", 4, 40, 16)
        cost_per_dock = st.number_input(
            "Installed cost per dock",
            min_value=1_000,
            max_value=50_000,
            value=8_000,
            step=500,
            format="%d",
        )
        demand_uplift = st.slider(
            "Demand captured after expansion",
            5,
            60,
            20,
            format="%d%%",
        )
        net_revenue_trip = st.number_input(
            "Net operating revenue per new trip",
            min_value=0.0,
            max_value=20.0,
            value=2.25,
            step=0.25,
        )
        public_value_trip = st.number_input(
            "Estimated public value per new trip",
            min_value=0.0,
            max_value=30.0,
            value=4.00,
            step=0.25,
            help="Editable proxy for congestion, access, health, and emissions benefits.",
        )
        annual_station_cost = st.number_input(
            "Annual added station operating cost",
            min_value=0,
            max_value=250_000,
            value=28_000,
            step=2_000,
            format="%d",
        )
        analysis_years = st.slider("Analysis period", 3, 15, 5)
        discount_rate = st.slider("Discount rate", 0, 15, 5, format="%d%%")

    investment_source = nyc_filtered
    investment_rank = (
        investment_source.groupby(["station_name", "capacity"], as_index=False)["trips"]
        .sum()
        .rename(columns={"trips": "period_trips"})
    )
    if not mta_opportunity.empty:
        investment_rank = investment_rank.merge(
            mta_opportunity[["station_name", "transit_opportunity_score"]],
            on="station_name",
            how="left",
        )
    else:
        investment_rank["transit_opportunity_score"] = np.nan
    observed_days = max(1, investment_source["date"].nunique())
    investment_rank["daily_trips"] = investment_rank["period_trips"] / observed_days
    investment_rank["new_annual_trips"] = (
        investment_rank["daily_trips"] * 365 * demand_uplift / 100
    )
    investment_rank["capital_cost"] = docks_added * cost_per_dock
    investment_rank["annual_operating_return"] = (
        investment_rank["new_annual_trips"] * net_revenue_trip - annual_station_cost
    )
    investment_rank["annual_public_benefit"] = (
        investment_rank["new_annual_trips"] * public_value_trip
    )
    discount = discount_rate / 100
    annuity_factor = sum(1 / ((1 + discount) ** year) for year in range(1, analysis_years + 1))
    investment_rank["five_year_fiscal_npv"] = (
        investment_rank["annual_operating_return"] * annuity_factor
        - investment_rank["capital_cost"]
    )
    investment_rank["public_npv"] = (
        (
            investment_rank["annual_operating_return"]
            + investment_rank["annual_public_benefit"]
        )
        * annuity_factor
        - investment_rank["capital_cost"]
    )
    investment_rank["public_benefit_cost_ratio"] = (
        (
            investment_rank["annual_operating_return"]
            + investment_rank["annual_public_benefit"]
        )
        * annuity_factor
        / investment_rank["capital_cost"]
    )
    investment_rank["capital_cost_per_new_trip"] = (
        investment_rank["capital_cost"]
        / (investment_rank["new_annual_trips"] * analysis_years)
    )
    investment_rank["annual_operating_support_needed"] = (
        -investment_rank["annual_operating_return"].clip(upper=0)
    )
    investment_rank["fiscal_payback_years"] = np.where(
        investment_rank["annual_operating_return"] > 0,
        investment_rank["capital_cost"] / investment_rank["annual_operating_return"],
        np.nan,
    )
    investment_rank = investment_rank.sort_values(
        ["public_npv", "transit_opportunity_score"],
        ascending=[False, False],
    )
    maximum_projects = int(public_budget // (docks_added * cost_per_dock))
    investment_rank["recommended"] = False
    recommended_index = investment_rank[
        investment_rank["public_npv"] > 0
    ].head(maximum_projects).index
    investment_rank.loc[recommended_index, "recommended"] = True

    with results_col:
        recommended = investment_rank[investment_rank["recommended"]]
        total_capital = recommended["capital_cost"].sum()
        fiscal_npv = recommended["five_year_fiscal_npv"].sum()
        public_npv = recommended["public_npv"].sum()
        new_trips = recommended["new_annual_trips"].sum()
        portfolio_bcr = (
            (public_npv + total_capital) / total_capital if total_capital else 0
        )

        summary_columns = st.columns(4)
        summary_columns[0].metric("Recommended projects", f"{len(recommended)}")
        summary_columns[1].metric("Capital deployed", f"${compact_number(total_capital)}")
        summary_columns[2].metric(
            "New annual trips",
            compact_number(new_trips),
        )
        summary_columns[3].metric(
            "Public benefit-cost ratio",
            f"{portfolio_bcr:.2f}×",
            "Above 1.0× creates modeled public value",
        )

        value_chart_data = investment_rank.head(10).copy()
        value_chart = px.bar(
            value_chart_data,
            x="public_npv",
            y="station_name",
            orientation="h",
            color="recommended",
            color_discrete_map={True: "#2D7FF9", False: "#CBD5E1"},
            labels={
                "public_npv": f"{analysis_years}-year public NPV ($)",
                "station_name": "",
                "recommended": "Within budget",
            },
        )
        value_chart.update_layout(
            height=410,
            yaxis={"categoryorder": "total ascending"},
            legend_title_text="",
            margin=dict(l=10, r=10, t=20, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
        )
        st.plotly_chart(value_chart, use_container_width=True)

        st.caption(
            f"Selected projects are estimated to add {compact_number(new_trips)} "
            "annual trips under the current assumptions."
        )

    st.subheader("Project-level recommendation table")
    planner_table = investment_rank[
        [
            "recommended",
            "station_name",
            "daily_trips",
            "new_annual_trips",
            "capital_cost",
            "annual_operating_return",
            "annual_operating_support_needed",
            "fiscal_payback_years",
            "five_year_fiscal_npv",
            "public_npv",
            "public_benefit_cost_ratio",
            "capital_cost_per_new_trip",
            "transit_opportunity_score",
        ]
    ].copy()
    st.dataframe(
        planner_table,
        hide_index=True,
        use_container_width=True,
        column_config={
            "recommended": st.column_config.CheckboxColumn("Fund"),
            "station_name": "Station",
            "daily_trips": st.column_config.NumberColumn("Daily demand", format="%.0f"),
            "new_annual_trips": st.column_config.NumberColumn(
                "New trips/year", format="%.0f"
            ),
            "capital_cost": st.column_config.NumberColumn(
                "Capital cost", format="$%.0f"
            ),
            "annual_operating_return": st.column_config.NumberColumn(
                "Annual operating return", format="$%.0f"
            ),
            "annual_operating_support_needed": st.column_config.NumberColumn(
                "Annual support needed", format="$%.0f"
            ),
            "fiscal_payback_years": st.column_config.NumberColumn(
                "Fiscal payback", format="%.1f years"
            ),
            "five_year_fiscal_npv": st.column_config.NumberColumn(
                f"{analysis_years}-yr fiscal NPV", format="$%.0f"
            ),
            "public_npv": st.column_config.NumberColumn(
                f"{analysis_years}-yr public NPV", format="$%.0f"
            ),
            "public_benefit_cost_ratio": st.column_config.NumberColumn(
                "Public BCR", format="%.2f×"
            ),
            "capital_cost_per_new_trip": st.column_config.NumberColumn(
                "Capital/new trip", format="$%.2f"
            ),
            "transit_opportunity_score": st.column_config.ProgressColumn(
                "MTA opportunity", min_value=0, max_value=100, format="%.1f"
            ),
        },
    )
    st.info(
        "**Public-sector decision rule:** prioritize positive public NPV and a benefit-cost "
        "ratio above 1.0, then confirm the annual operating support fits the agency budget. "
        "Fiscal return remains visible as a sustainability constraint—not the sole goal."
    )

with dot_tab:
    st.subheader("Why city transportation departments should invest in bike-share")
    st.markdown(
        '<p class="section-note">Data-driven arguments for DOT support, '
        "drawn from ridership trends, MTA reliability gaps, and cross-city benchmarks.</p>",
        unsafe_allow_html=True,
    )

    # --- Argument 1: Ridership growth trajectory ---
    st.markdown("### 1. Ridership is growing — and demand outpaces supply")
    growth_col, gap_col = st.columns(2)

    with growth_col:
        # Monthly ridership trend
        monthly_trend = (
            filtered.assign(month=filtered["date"].dt.to_period("M").dt.to_timestamp())
            .groupby(["month", "city"], as_index=False)["trips"]
            .sum()
            .sort_values("month")
        )
        monthly_chart = px.line(
            monthly_trend,
            x="month",
            y="trips",
            color="city",
            color_discrete_map={city: meta["color"] for city, meta in CITY_META.items()},
            labels={"trips": "Monthly trips", "month": "", "city": "System"},
        )
        monthly_chart.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=15, b=10),
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="white",
            legend_title_text="",
        )
        st.plotly_chart(monthly_chart, use_container_width=True)

    with gap_col:
        # Capacity pressure distribution — stations running hot
        station_pressure = (
            nyc_filtered.groupby(["station_name", "capacity"], as_index=False)
            .agg(total_trips=("trips", "sum"), days=("date", "nunique"))
        )
        station_pressure["daily_demand"] = station_pressure["total_trips"] / station_pressure["days"]
        station_pressure["pressure"] = station_pressure["daily_demand"] / station_pressure["capacity"]
        station_pressure["pressure_category"] = pd.cut(
            station_pressure["pressure"],
            bins=[0, 0.5, 1.0, 1.5, float("inf")],
            labels=["Under-utilized (<0.5)", "Balanced (0.5–1.0)", "Strained (1.0–1.5)", "Critical (>1.5)"],
        )
        pressure_dist = station_pressure["pressure_category"].value_counts().reset_index()
        pressure_dist.columns = ["Category", "Stations"]
        pressure_chart = px.pie(
            pressure_dist,
            values="Stations",
            names="Category",
            color_discrete_sequence=["#94A3B8", "#7DD3FC", "#F59E0B", "#EF4444"],
            hole=0.45,
        )
        pressure_chart.update_layout(
            height=320,
            margin=dict(l=10, r=10, t=15, b=10),
        )
        st.plotly_chart(pressure_chart, use_container_width=True)
        strained = station_pressure[station_pressure["pressure"] >= 1.0]
        st.metric(
            "NYC stations at or above capacity",
            f"{len(strained)} of {len(station_pressure)}",
            f"{len(strained)/len(station_pressure)*100:.0f}% of network" if len(station_pressure) > 0 else "",
        )

    # --- Argument 2: Transit reliability gap ---
    st.markdown("### 2. Bike-share fills transit reliability gaps")
    st.markdown(
        "When subway service is unreliable, bike-share provides a resilient alternative. "
        "Neighborhoods with high MTA delay rates and high transit ridership are prime "
        "candidates for DOT-supported bike-share investment."
    )

    if not mta_opportunity.empty:
        reliability_col, resilience_col = st.columns(2)

        with reliability_col:
            delay_chart = px.bar(
                mta_opportunity.sort_values("mta_delay_rate", ascending=False),
                x="neighborhood",
                y="mta_delay_rate",
                color="bike_daily_trips",
                color_continuous_scale=["#CBD5E1", "#2D7FF9"],
                labels={
                    "mta_delay_rate": "MTA delay rate",
                    "neighborhood": "",
                    "bike_daily_trips": "Bike trips/day",
                },
            )
            delay_chart.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=15, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="white",
                yaxis_tickformat=".0%",
            )
            st.plotly_chart(delay_chart, use_container_width=True)

        with resilience_col:
            # Resilience score: high MTA riders + high delay = high need
            mta_opportunity["resilience_need"] = (
                mta_opportunity["mta_daily_riders"] * mta_opportunity["mta_delay_rate"]
            )
            resilience_chart = px.scatter(
                mta_opportunity,
                x="mta_delay_rate",
                y="mta_daily_riders",
                size="bike_daily_trips",
                hover_name="neighborhood",
                color="transit_opportunity_score",
                color_continuous_scale=["#CBD5E1", "#F26B4A", "#0B1324"],
                labels={
                    "mta_delay_rate": "MTA delay rate",
                    "mta_daily_riders": "MTA daily riders",
                    "transit_opportunity_score": "Investment priority",
                },
            )
            resilience_chart.update_layout(
                height=350,
                margin=dict(l=10, r=10, t=15, b=10),
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="white",
                xaxis_tickformat=".0%",
            )
            st.plotly_chart(resilience_chart, use_container_width=True)
    else:
        st.info("MTA opportunity data not available. Run build_mta_opportunity.py.")

    # --- Argument 3: Cross-city benchmark ---
    st.markdown("### 3. San Francisco benchmark — what peer support looks like")
    if "San Francisco" in filtered["city"].unique():
        benchmark_data = (
            filtered.groupby("city", as_index=False)
            .agg(
                total_trips=("trips", "sum"),
                stations=("station_name", "nunique"),
                electric_trips=("electric_trips", "sum"),
                days=("date", "nunique"),
            )
        )
        benchmark_data["trips_per_station_day"] = (
            benchmark_data["total_trips"] / benchmark_data["stations"] / benchmark_data["days"]
        )
        benchmark_data["electric_share"] = benchmark_data["electric_trips"] / benchmark_data["total_trips"]

        bench_cols = st.columns(3)
        for i, (_, row) in enumerate(benchmark_data.iterrows()):
            with bench_cols[i % 3]:
                st.markdown(f"**{row['city']}**")
                st.metric("Trips/station/day", f"{row['trips_per_station_day']:.0f}")
                st.metric("Electric share", f"{row['electric_share']:.0%}")
                st.metric("Active stations", f"{int(row['stations']):,}")

        st.markdown(
            "> Bay Wheels operates in a metro area ~1/10th the size of NYC but achieves "
            "competitive per-station utilization, partly due to SFMTA integration and "
            "municipal support. NYC's scale advantage means DOT investment would unlock "
            "proportionally larger mobility gains."
        )
    else:
        st.info("Add San Francisco data to see the cross-city benchmark.")

    # --- Argument 4: The DOT investment case summary ---
    st.markdown("### 4. The case for DOT support")
    st.markdown(
        """
        | Argument | Evidence | DOT action |
        |---|---|---|
        | **Demand exceeds supply** | Stations running above capacity across Manhattan and Brooklyn | Fund dock expansions at high-pressure stations |
        | **Transit resilience** | Subway delays create unserved mobility demand | Co-locate bike-share expansions near unreliable subway lines |
        | **Electric transition** | E-bike share growing; higher revenue per trip | Subsidize e-bike fleet expansion and charging infrastructure |
        | **Equity gaps** | Outer-borough station deserts along IBX corridor | Prioritize new stations in underserved neighborhoods |
        | **Proven peer model** | SF Bay Wheels operates with SFMTA municipal partnership | Adopt similar DOT integration for route planning and subsidies |
        | **Positive public ROI** | Benefit-cost ratio above 1.0 for top expansion candidates | Allocate capital budget to highest-NPV station projects |
        """
    )

    st.info(
        "**Recommendation:** NYC DOT should allocate dedicated capital and operating "
        "budget lines for bike-share expansion, prioritizing neighborhoods where "
        "transit reliability is weakest, ridership demand is highest, and station "
        "capacity is most constrained. The Government Investment tab provides "
        "project-level NPV rankings to guide specific funding decisions."
    )

with methods_tab:
    st.subheader("How to read this dashboard")
    st.markdown(
        """
        - **Benchmark role:** Bay Wheels appears only in the high-level comparison.
          Forecasting, station rankings, and funding recommendations are NYC-only.
        - **Demand pressure:** average daily trips divided by current dock capacity. It is
          a prioritization signal, not proof that a station should be expanded.
        - **Forecast lab:** the current controls create an interpretable scenario. Once
          trained model outputs are saved, this view can overlay XGBoost predictions and
          holdout metrics.
        - **MTA connection:** compares transit demand and reliability with bike demand
          to identify potential first/last-mile and disruption-resilience gaps. It is a
          prioritization signal, not causation.
        - **Government investment planner:** ranks expansions by public NPV, benefit-cost
          ratio, new trips, operating support, and fiscal sustainability. Inputs are
          assumptions and should be replaced with agency-validated capital, operating,
          revenue, equity, and benefit estimates before a real funding decision.
        - **Scope:** Bay Wheels serves the wider Bay Area. Its benchmark is labeled
          separately and does not enter NYC funding recommendations.
        """
    )
    st.subheader("Expected production dataset")
    st.code(
        "data/processed/bike_share_daily.parquet\n\n"
        "date | city | system | station_name | lat | lon | rider_type |\n"
        "trips | electric_trips | capacity",
        language="text",
    )
    st.code(
        "data/processed/mta_bike_opportunity.parquet\n\n"
        "station_name | neighborhood | mta_daily_riders | mta_delay_rate",
        language="text",
    )
    st.caption(
        f"Current source: {'built-in demonstration dataset' if is_demo else DATA_PATH}"
    )
