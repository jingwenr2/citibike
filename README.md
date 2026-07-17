[README.md](https://github.com/user-attachments/files/30131630/README.md)
# NYC Zero-Friction Mobility 🚲🚇

**A data-driven case for unified, affordable urban transportation as economic infrastructure — with CitiBike as the analytics core.**

> What if NYC treated getting around the same way it treats turning on a light — as essential infrastructure that pays for itself through economic growth, not fares?

## The Idea

We're using CitiBike's public trip data as a proof-of-concept to build the case for a broader "zero-friction mobility" vision for NYC — free/expanded transit paying for itself through induced economic demand, not fares.

## Three-Layer Architecture

| Layer | Focus |
|---|---|
| **1. CitiBike Data Core** | Trip volume, e-bike vs. classic adoption, member vs. casual behavior, station deserts, demand forecasting |
| **2. MTA Free Fare Analysis** | Cost/savings case for fare elimination — collection costs, enforcement, comparative case studies (Kansas City, Tallinn, Luxembourg) |
| **3. Unified Mobility Vision** | Zero-friction mobility stack narrative + interactive decision-engine dashboard |

Full plan: [`plan.md`](./plan.md)

## Tech Stack

- **Data:** Citi Bike System Data, MTA Open Data (data.ny.gov), NYC Open Data
- **Analysis:** Python (pandas), SQL
- **Modeling:** XGBoost — station-level demand forecasting → [`demand_forecast_xgboost.py`](./demand_forecast_xgboost.py)
- **Dashboard:** Streamlit (planned)

## Repo Structure

```
data/raw/          # untouched downloads (gitignored)
data/processed/    # cleaned parquet/csv
notebooks/         # exploratory analysis
sql/               # ingestion + transform scripts
dashboard/         # Streamlit app
report/            # final write-up, slides, sources
plan.md            # full project plan
```

## Status

🚧 In progress — capstone project.

- [x] Project plan
- [x] Demand forecasting model scaffold
- [ ] Data ingestion pipeline
- [ ] Cost-savings model (Layer 2)
- [ ] Interactive dashboard
- [ ] Final report + slides

## Team

See [Contributors](../../graphs/contributors).
