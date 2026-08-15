---
title: CityCycle Intelligence
emoji: 🚲
colorFrom: pink
colorTo: blue
sdk: docker
app_port: 7860
---

# NYC Citi Bike Public Investment Intelligence 🚲

**A New York City bike-share forecasting and public-investment web app, with San Francisco as a comparison benchmark.**

The project makes the data-backed case that NYC should invest more in Citi
Bike. It forecasts station demand, compares Citi Bike with MTA ridership and
reliability to identify first/last-mile and disruption-resilience gaps, and
ranks expansion opportunities for public investment. Bay Wheels is used for
high-level comparison only; it is not included in the app's forecasts or
funding recommendations.

## The Idea

We're building a shared data pipeline and Streamlit app for exploring how bike-share usage differs between NYC and San Francisco. NYC's transit-access and pricing work remains a focused case study within the broader comparison.

## Three-Layer Architecture

| Layer | Focus |
|---|---|
| **1. Shared Data Core** | Normalize Citi Bike and Bay Wheels trips into one validated schema |
| **2. City Comparison** | Demand, seasonality, rider/bike mix, station usage, and city-specific context |
| **3. Forecast Web App** | Station explorer, demand forecasts, model metrics, and expansion rankings |

Full plan: [`plan.md`](./plan.md)

## Tech Stack

- **Data:** Citi Bike System Data, Bay Wheels System Data, MTA/NYC Open Data, and selected Bay Area public data
- **Analysis:** Python (pandas), SQL
- **Modeling:** XGBoost — station-level demand forecasting → [`backend/demand_forecast_xgboost.py`](./backend/demand_forecast_xgboost.py)
- **Dashboard:** Streamlit + Plotly (planned)

## Repo Structure

```
frontend/
  dashboard/         # Streamlit app
docs/                # static GitHub Pages demo
backend/
  src/               # reusable ingestion, validation, and modeling code
  scripts/           # data-build scripts (e.g. MTA opportunity table)
  download_tripdata.py
  demand_forecast_xgboost.py
  requirements.txt
notebooks/           # exploratory analysis
tests/               # unit tests
data/raw/citibike/   # untouched NYC downloads (gitignored)
data/raw/baywheels/  # untouched Bay Wheels downloads
data/processed/      # normalized parquet/csv
sql/                 # ingestion + transform scripts
models/              # model artifacts and metrics
report/              # final write-up, slides, sources
plan.md              # full project plan
```

## Status
🚧 In progress — capstone project.

- [x] Project plan
- [x] Layer 1 EDA
- [x] Reform analysis notebook (8 visuals)
- [x] Demand forecast scaffold
- [x] Interactive decision-engine prototype
- [ ] Bay Wheels ingestion and profiling
- [ ] Shared two-city schema and validation pipeline
- [ ] City-aware forecasting and baseline evaluation
- [ ] MTA × CitiBike neighborhood join
- [ ] Reproducible data pipeline (off Google Drive)
- [ ] Streamlit comparison web app
- [ ] Final report + slides

## Download trip data from the public S3 indexes

You can pull the latest Citi Bike or Bay Wheels archives directly from the public S3 listings:

```bash
python backend/download_tripdata.py --provider citibike --months 6
python backend/download_tripdata.py --provider baywheels --months 6
```

The downloader saves files under `data/raw/` and exposes the same logic through the reusable module in [backend/src/ingest_tripdata.py](backend/src/ingest_tripdata.py).

## Run the Web App

```bash
python -m pip install -r backend/requirements.txt
streamlit run frontend/dashboard/app.py
```

The dashboard runs with labeled demonstration data until
`data/processed/bike_share_daily.parquet` is available. The expected columns
are documented on the app's **Data & methods** tab.

Build the official MTA opportunity table with:

```bash
python backend/scripts/build_mta_opportunity.py
```

Until the processed Citi Bike station table exists, the importer can join the
official MTA data to the app's demonstration station locations:

```bash
python backend/scripts/build_mta_opportunity.py --allow-demo-stations
```

The importer uses MTA Subway Hourly Ridership (`5wq4-mkjj`) and MTA Subway
Wait Assessment (`s666-h6b7`) from New York State Open Data. It aggregates
recent station entries, estimates a line-based reliability gap, spatially
matches subway complexes to Citi Bike stations, and writes
`data/processed/mta_bike_opportunity.parquet`.

The **Government & Transportation Investment Planner** converts projected
demand into new trips, capital cost, operating support, fiscal sustainability,
public-benefit NPV, benefit-cost ratio, and cost per new trip. These are
scenario assumptions for planning—not official cost or benefit estimates.

## Shareable GitHub Pages Demo

The static teammate-ready prototype is published from `docs/` through GitHub
Pages:

**https://jingwenr2.github.io/citibike/**

This version demonstrates the interface with modeled data. The Streamlit app
remains the full Python implementation for connecting processed datasets and
trained model outputs.

## Team

See [Contributors](../../graphs/contributors).

