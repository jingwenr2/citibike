# Citi Bike × Bay Wheels Demand Intelligence 🚲

**A two-city bike-share analytics and forecasting web app for New York City and San Francisco.**

The project compares Citi Bike and Bay Wheels trip patterns, forecasts station-level demand, and identifies capacity constraints and possible expansion opportunities.

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
- **Modeling:** XGBoost — station-level demand forecasting → [`demand_forecast_xgboost.py`](./demand_forecast_xgboost.py)
- **Dashboard:** Streamlit + Plotly (planned)

## Repo Structure

```
data/raw/citibike/ # untouched NYC downloads (gitignored)
data/raw/baywheels/# untouched Bay Wheels downloads
data/processed/    # normalized parquet/csv
notebooks/         # exploratory analysis
src/               # reusable ingestion, validation, and modeling code
sql/               # ingestion + transform scripts
dashboard/         # Streamlit app
models/            # model artifacts and metrics
report/            # final write-up, slides, sources
plan.md            # full project plan
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

## Team

See [Contributors](../../graphs/contributors).
