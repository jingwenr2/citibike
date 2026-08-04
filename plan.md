# NYC × San Francisco Bike-Share Intelligence — Capstone Project Plan

**Core question:** Where should NYC government and transportation teams invest more in Citi Bike capacity, based on predicted bike demand, MTA ridership, and transit reliability gaps? Bay Wheels provides a San Francisco benchmark, not a second investment geography.

**Status:** in execution. NYC EDA and reform analysis are complete, the XGBoost demand-forecast scaffold is in place, and an interactive public-investment dashboard exists. Current focus: building the reproducible NYC pipeline, validating the forecast, and adding a high-level San Francisco benchmark.

---

## 0. Progress Snapshot (updated August 2026)

**Done**
- [x] Project plan
- [x] Layer 1 EDA — `NYC_CitiBike_Analysis.ipynb`
- [x] Reform-analysis notebook — `CitiBike_Reform_Analysis.ipynb` (8 visuals: price inflation, ridership divergence, revenue/trip, suppression chart, IBX station-desert map, IBX demographics, price optimization, ROI break-even)
- [x] Demand-forecast model scaffold — `demand_forecast_xgboost.py`
- [x] Interactive decision-engine prototype — expansion profit calculator + subway×bike signal (HTML; ports to Streamlit)

**In progress / next**
- [ ] Download and profile Bay Wheels trip-history and station data
- [ ] Create one normalized Citi Bike/Bay Wheels trip schema
- [ ] Validate the XGBoost pipeline for NYC station demand
- [ ] MTA × CitiBike ridership join at neighborhood level (the new relationship analysis)
- [ ] Reproducible data pipeline — decouple `master` build from Google Drive/Colab paths
- [ ] Source/verify the 3-city (NYC/DC/Chicago) comparison figures currently hand-entered in the reform notebook
- [ ] Streamlit deployment of the NYC decision engine with SF benchmark
- [ ] Final report + slides

---

## 1. Three-Layer Architecture

| Layer                      | Focus                                                                                | Primary tools                   | Status |
| -------------------------- | ------------------------------------------------------------------------------------ | ------------------------------- | ------ |
| 1. Citi Bike Data Core     | Build the NYC trip, station, capacity, and forecast pipeline; normalize limited Bay Wheels aggregates for benchmarking | Python, pandas, SQL/Parquet | NYC analysis exists; reproducible pipeline next |
| 2. City Context            | NYC subway↔bike relationship and Bay Area transit/geographic context                  | MTA, BART/SFMTA, Census/geospatial data | NYC join planned; Bay Area sources to validate |
| 3. NYC Investment Web App  | NYC station explorer, demand forecast, public investment ranking, and SF benchmark | Streamlit, Plotly, XGBoost      | interactive prototype built |

**Direction note:** the main deliverable is an NYC government and transportation investment tool. Bay Wheels supports the narrative as a benchmark only; it does not enter NYC station forecasts, maps, rankings, or funding recommendations.

---

## 1b. Real-World Context (verified July 2026 — address these in the writeup)

- **Current pricing:** annual membership is **$239/yr** (effective Jan 28, 2026; was $220); e-bike / classic overage **$0.27/min** in NYC. The reform notebook still uses $219 — update `current_price` and extend the price-optimization curve up through $239.
- **Active expansion:** Citi Bike is adding **250 new stations across the Bronx, Queens, and Brooklyn in 2026** — the same boroughs as the IBX corridor. This does not sink the station-desert argument, but it reframes it: our 12-station proposal is a *targeted critique/prioritization* of a rollout that's already underway, not a plan in a vacuum. Use the expansion leaderboard to argue which neighborhoods that rollout should hit first.
- **Subsidy caveat:** DC and Chicago systems are publicly subsidized, which affects their revenue-per-trip comparison — flag this rather than treating the three cities as like-for-like.

---

## 2. Validated Datasets (checked July 2026)

### 2.1 CitiBike (Layer 1 — primary)

| Dataset                  | Source                                                     | Notes                                                                                                                                                                                                    |
| ------------------------ | ---------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Citi Bike Trip Histories | https://citibikenyc.com/system-data                        | Monthly CSVs since 2013, ~1–2M rows/month. Post-2021 schema: `ride_id, rideable_type (classic_bike/electric_bike/docked_bike), started_at, ended_at, start/end station name+id+lat/lng, member_casual`. **This is the field that unlocks the e-bike analysis.** Pre-2021 files have older schema (gender, birth year) — decide whether to normalize or scope to 2021+ only. Monthly files now run into 2026, so a Q1/Q2-2026 validation of the price/ridership relationship is feasible. |
| GBFS real-time feed      | https://gbfs.citibikenyc.com/gbfs/en/station_status.json   | Live station status/capacity — useful for "station desert" mapping, not historical trend.                                                                                                                |
| NYC Open Data mirror     | https://catalog.data.gov/dataset/citi-bike-system-data     | Same data, city catalog listing.                                                                                                                                                                         |
| NYC DOT Bike Share Usage Reports | nyc.gov (Local Law 099 quarterly reports)          | Trips by month/quarter, disaggregated by council + community district. Q2 2025 = 12.8M NYC trips. Useful independent cross-check on the trip CSV totals.                                                  |
| Starter ETL kit          | https://github.com/toddwschneider/nyc-citibike-data        | Scripts to download/clean/load trip data into Postgres. Good baseline to fork instead of writing ingestion from scratch.                                                                                 |

**Action item:** decide date range (recommend last 24–36 months for recency + manageable size) and whether to include Jersey City files (prefixed `JC`, exclude for an NYC-only story).

**Data-integrity note (reform notebook):** the 3-city pricing and ridership tables in `CitiBike_Reform_Analysis.ipynb` (Cell 3) are hand-entered published figures, not derived from trip data — the only cell reading real data is the `master` summary. Before the defense, either cite every figure in Cell 3 to a source or rebuild NYC's numbers from the trip CSVs. This is the first question a reviewer will ask.

### 2.2 Bay Wheels (comparison benchmark only)

| Dataset | Source | Notes |
| --- | --- | --- |
| Bay Wheels trip history | Lyft Bay Wheels system-data page | Monthly trip files; inspect each period because column names and bike-type labels may change over time. Normalize them into the shared trip schema before analysis. |
| Bay Wheels GBFS feeds | Bay Wheels GBFS endpoint | Current station information/status and dock capacity. Use for station metadata and current-capacity features, not as historical availability unless snapshots are collected. |
| Bay Area geography | Census/official Bay Area geographic boundaries | Assign stations to San Francisco neighborhoods or consistent Census geographies for maps and expansion analysis. |

**Scope rule:** label the system as **Bay Wheels / San Francisco Bay Area**, because Bay Wheels extends beyond the City of San Francisco. Use comparable aggregate indicators in the Overview only. Do not include Bay Wheels in forecasts, station recommendations, or the government investment planner.

### 2.3 MTA (NYC city context)

| Dataset                                       | Source                                                                                    | Notes                                                                                                                                                    |
| --------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MTA Daily Ridership Data 2020–2025            | https://data.ny.gov/Transportation/MTA-Daily-Ridership-Data-2020-2025/vxuj-8kew           | Subway/bus/LIRR/MNR/bridge-tunnel daily totals, good for trend + COVID recovery baseline.                                                                |
| MTA Subway Hourly Ridership (2025–)           | https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2025/5wq4-mkjj   | Station-complex, hourly, by fare payment class. **This is the join source for the subway↔bike relationship analysis** — aggregate to neighborhood and merge with `master`. |
| Subway Origin–Destination Ridership Estimates | via mta.info Open Data blog                                                                | Estimated rider flow between station pairs (OMNY/MetroCard-based) — closest thing to a "who goes where" dataset, useful for the labor-mobility argument. |
| Fare Card History                             | data.ny.gov                                                                               | Historical fare structure changes for context.                                                                                                          |

**Gap:** NYC has never run a fare-free pilot, so there's no natural experiment to regress ridership-vs-fare elasticity from local data. Treat Kansas City / Tallinn / Luxembourg as **literature-review inputs**, not datasets to merge in — cite them, don't try to join them.

### 2.4 Economic activity / foot traffic proxies (for the correlation story)

| Dataset                               | Source                                                                                             | Notes                                                                                                                                                                                                    |
| ------------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DOF Summary of Neighborhood Sales     | data.cityofnewyork.us/City-Government/DOF-Summary-of-Neighborhood-Sales-by-Neighborhood-/5ebm-myj7 | Property-sale based, a rough proxy — not retail revenue. Flag limitation clearly in the report.                                                                                                          |
| DCA Licensed Businesses               | data.cityofnewyork.us/Business/businesses/d8ic-tk4f                                                | Business density by address — can aggregate to station-buffer counts.                                                                                                                                    |
| NYC DOT Bi-Annual Pedestrian Counts   | data.cityofnewyork.us/Transportation/Bi-Annual-Pedestrian-Counts/2de2-6x2h                         | 114 fixed count locations, collected since ~2007, restarted 2020. **Best available real foot-traffic proxy** — but only 114 points citywide, so it constrains which neighborhoods can be in the correlation analysis. |
| DCP Storefront Vacancy dataset/report | nyc.gov/planning (Storefronts Report, Nov 2024)                                                    | Retail corridor health trend, citywide first-of-its-kind storefront-level dataset.                                                                                                                       |

**Honest gap:** there is no NYC dataset that directly measures "retail spending near a CitiBike station." The correlation claim has to be built from these proxies (business density + pedestrian counts + property sales), with the limitation stated explicitly, not implied as direct causation.

### 2.5 Secondary / comparative (narrative, not for merging)

- Kansas City (KCATA) free-bus ridership case
- Tallinn, Estonia fare-free transit (since 2013)
- Luxembourg nationwide free transit (2020)
- Interstate Highway System economic-return literature (for the "induced demand" framing)

These stay as cited sources in the report/slides, not tables in the data pipeline.

---

## 3. Methodology Sketch

1. **Ingest:** download Citi Bike and Bay Wheels monthly trip files for the same date window. Store untouched files under city-specific raw folders and cleaned outputs as Parquet.
2. **Normalize:** map both providers to a shared schema: `city, system, ride_id, started_at, ended_at, start/end_station_id, start/end_station_name, start/end_lat, start/end_lng, rideable_type, rider_type`.
3. **Validate:** report row counts, date coverage, missing station IDs/coordinates, duplicates, invalid durations, and provider-specific category mappings before modeling.
4. **Geo join:** assign stations to comparable neighborhood or Census geographies. Keep NYC-specific MTA joins and Bay Area-specific transit joins in separate context tables.
5. **Benchmark analysis:** compare NYC with San Francisco/Bay Wheels using a small set of comparable aggregate indicators. Use rates or normalized indexes when system sizes differ.
6. **NYC case study:** preserve the price→ridership, station-desert, and subway↔bike analyses as NYC-specific views.
7. **Forecast:** train a reproducible NYC station-day model, compare it against a seasonal-naive baseline, and expose test-period metrics in the app.
8. **Decision engine:** rank high-demand/capacity-constrained stations and underserved areas. Avoid comparing raw scores across cities until features are normalized.
9. **Web app:** deliver Streamlit pages for Overview with SF benchmark, NYC Station Explorer, NYC Demand Forecast, Government Investment, and Data/Methods.

### 3b. Demand Forecasting (XGBoost)

- Target: daily trip count per station and city
- Features: city/system, station location, calendar, city-specific holidays, 1-day and 7-day lags, rolling mean, and optional weather/capacity
- Split: chronological and identical in principle for each city; never random-split time-series rows
- Baseline: previous-week demand (`lag_7d`) so XGBoost must demonstrate measurable improvement
- Output: predicted demand, confidence/uncertainty note, test metrics, and capacity-normalized candidate rankings
- Metrics: MAE, RMSE, WAPE, and metrics broken out by city
- Guardrail: train separate city models first; test a pooled city-aware model only after the separate baselines are trustworthy

---

## 4. Repo Structure

```
/data/raw/citibike/ # untouched NYC downloads (gitignored if large)
/data/raw/baywheels/# untouched Bay Wheels downloads
/data/processed/    # normalized trip/station parquet files
/notebooks/         # EDA + reform analysis
/sql/               # ingestion + transform scripts
/dashboard/         # Streamlit NYC investment app with SF benchmark
/src/               # shared ingestion, validation, features, and modeling modules
/models/            # serialized model artifacts and metric summaries
/report/            # final write-up, slides, sources.md
demand_forecast_xgboost.py
plan.md             # this file
```

Current files in repo: `NYC_CitiBike_Analysis.ipynb`, `CitiBike_Reform_Analysis.ipynb`, `demand_forecast_xgboost.py`, `requirements.txt`, `README.md`, `plan.md`.

---

## 5. Open Decisions

- Date range for CitiBike data (recommend last 2–3 years for relevance + file size)
- Choose the small set of Bay Wheels measures that are genuinely comparable to NYC and useful as benchmarks
- Include Jersey City Citi Bike stations or NYC-only? (recommend NYC-only for a cleaner NYC–SF comparison)
- ~~Dashboard tool: Tableau vs. Power BI vs. web app~~ → **resolved: Streamlit web app**, built off the interactive decision-engine prototype
- Comparable geography key across cities; retain local geography keys for city-specific transit analysis
- Whether weather joins belong in v1 or v2 (recommend v2 unless the core pipeline is complete early)
- How rigorously to fact-check the fare-collection-cost figure against current MTA budget documents before presenting it as a headline number
- Whether to source-verify or rebuild the 3-city comparison figures (see data-integrity note in 2.1)

---

## 6. Next Steps

1. Acquire a matched date range of Citi Bike and Bay Wheels trip files and document their schemas.
2. Build the normalized NYC Parquet dataset plus automated validation checks; create a separate SF benchmark table.
3. Refactor `demand_forecast_xgboost.py` into reusable NYC training code with a seasonal-naive baseline, saved metrics, and saved predictions.
4. Wire the Streamlit Overview, NYC Station Explorer, and SF benchmark to real processed data.
5. Add the Demand Forecast and Expansion Candidates pages, then verify all charts, filters, empty states, and app startup.
6. Complete the NYC transit-access case study and add Bay Area context only when authoritative, comparable inputs are available.
7. Update the README with local setup, data preparation, model training, app launch, and deployment instructions.
8. Draft the report and slides around the cross-city findings, limitations, and planner/rider use cases.

## 7. Web App Definition of Done

- App starts locally with one documented command and no notebook dependency.
- Users see San Francisco only in clearly labeled benchmark comparisons.
- Station exploration, forecasting, and investment recommendations are restricted to NYC.
- Filters include date range, bike type, rider type, and station/neighborhood where supported.
- Every chart states its unit, date coverage, and active city/system scope.
- Forecast pages show holdout metrics and a baseline comparison, not predictions alone.
- Missing or unavailable city-specific fields are labeled rather than silently treated as zero.
- Large raw files and trained artifacts are excluded from Git; reproducible download/build steps are documented.
- A deployment smoke test confirms the hosted app loads and core filters work.
