# NYC Zero-Friction Mobility — Capstone Project Plan

**Core question:** What if NYC treated getting around as essential infrastructure that pays for itself through economic growth — not fares? CitiBike is the analytics nucleus; MTA free-fare is the policy case; the unified mobility stack is the vision.

**Status:** in execution. EDA complete, reform-analysis notebook complete (8 visuals), demand-forecast scaffold in place, and an interactive decision-engine prototype built. Current focus: joining MTA ridership to CitiBike at the neighborhood level and shipping the Streamlit web app.

---

## 0. Progress Snapshot (updated July 2026)

**Done**
- [x] Project plan
- [x] Layer 1 EDA — `NYC_CitiBike_Analysis.ipynb`
- [x] Reform-analysis notebook — `CitiBike_Reform_Analysis.ipynb` (8 visuals: price inflation, ridership divergence, revenue/trip, suppression chart, IBX station-desert map, IBX demographics, price optimization, ROI break-even)
- [x] Demand-forecast model scaffold — `demand_forecast_xgboost.py`
- [x] Interactive decision-engine prototype — expansion profit calculator + subway×bike signal (HTML; ports to Streamlit)

**In progress / next**
- [ ] MTA × CitiBike ridership join at neighborhood level (the new relationship analysis)
- [ ] Reproducible data pipeline — decouple `master` build from Google Drive/Colab paths
- [ ] Source/verify the 3-city (NYC/DC/Chicago) comparison figures currently hand-entered in the reform notebook
- [ ] Streamlit deployment of the decision engine
- [ ] Final report + slides

---

## 1. Three-Layer Architecture

| Layer                      | Focus                                                                                | Primary tools                   | Status |
| -------------------------- | ------------------------------------------------------------------------------------ | ------------------------------- | ------ |
| 1. CitiBike Data Core      | Trip-level analytics: volume, e-bike vs. classic, member vs. casual, station deserts | Python, SQL, Excel              | EDA + reform analysis done; pipeline to make reproducible |
| 2. MTA Analysis            | Subway↔bike ridership relationship (active); free-fare cost/savings case (parked)    | Python, data.ny.gov, case studies | ridership join = current work |
| 3. Unified Mobility Vision | Zero-friction narrative + interactive decision-engine dashboard                      | Streamlit, slides               | prototype built; Streamlit port next |

**Direction note:** the working spine has narrowed to two engines — (a) the price → ridership *suppression* story (NYC raised prices faster than DC/Chicago; ridership growth lagged), and (b) an interactive **expansion decision engine** that answers "which unserved neighborhood, and how much profit if we add stations." The MTA free-fare cost-savings case (Layer 2 original scope) stays as supporting narrative, not the centerpiece.

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

### 2.2 MTA (Layer 2)

| Dataset                                       | Source                                                                                    | Notes                                                                                                                                                    |
| --------------------------------------------- | ----------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------- |
| MTA Daily Ridership Data 2020–2025            | https://data.ny.gov/Transportation/MTA-Daily-Ridership-Data-2020-2025/vxuj-8kew           | Subway/bus/LIRR/MNR/bridge-tunnel daily totals, good for trend + COVID recovery baseline.                                                                |
| MTA Subway Hourly Ridership (2025–)           | https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2025/5wq4-mkjj   | Station-complex, hourly, by fare payment class. **This is the join source for the subway↔bike relationship analysis** — aggregate to neighborhood and merge with `master`. |
| Subway Origin–Destination Ridership Estimates | via mta.info Open Data blog                                                                | Estimated rider flow between station pairs (OMNY/MetroCard-based) — closest thing to a "who goes where" dataset, useful for the labor-mobility argument. |
| Fare Card History                             | data.ny.gov                                                                               | Historical fare structure changes for context.                                                                                                          |

**Gap:** NYC has never run a fare-free pilot, so there's no natural experiment to regress ridership-vs-fare elasticity from local data. Treat Kansas City / Tallinn / Luxembourg as **literature-review inputs**, not datasets to merge in — cite them, don't try to join them.

### 2.3 Economic activity / foot traffic proxies (for the correlation story)

| Dataset                               | Source                                                                                             | Notes                                                                                                                                                                                                    |
| ------------------------------------- | -------------------------------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| DOF Summary of Neighborhood Sales     | data.cityofnewyork.us/City-Government/DOF-Summary-of-Neighborhood-Sales-by-Neighborhood-/5ebm-myj7 | Property-sale based, a rough proxy — not retail revenue. Flag limitation clearly in the report.                                                                                                          |
| DCA Licensed Businesses               | data.cityofnewyork.us/Business/businesses/d8ic-tk4f                                                | Business density by address — can aggregate to station-buffer counts.                                                                                                                                    |
| NYC DOT Bi-Annual Pedestrian Counts   | data.cityofnewyork.us/Transportation/Bi-Annual-Pedestrian-Counts/2de2-6x2h                         | 114 fixed count locations, collected since ~2007, restarted 2020. **Best available real foot-traffic proxy** — but only 114 points citywide, so it constrains which neighborhoods can be in the correlation analysis. |
| DCP Storefront Vacancy dataset/report | nyc.gov/planning (Storefronts Report, Nov 2024)                                                    | Retail corridor health trend, citywide first-of-its-kind storefront-level dataset.                                                                                                                       |

**Honest gap:** there is no NYC dataset that directly measures "retail spending near a CitiBike station." The correlation claim has to be built from these proxies (business density + pedestrian counts + property sales), with the limitation stated explicitly, not implied as direct causation.

### 2.4 Secondary / comparative (Layer 3 narrative, not for merging)

- Kansas City (KCATA) free-bus ridership case
- Tallinn, Estonia fare-free transit (since 2013)
- Luxembourg nationwide free transit (2020)
- Interstate Highway System economic-return literature (for the "induced demand" framing)

These stay as cited sources in the report/slides, not tables in the data pipeline.

---

## 3. Methodology Sketch

1. **Ingest:** CitiBike monthly CSVs (chosen date range) + MTA ridership + NYC Open Data proxies into a local Postgres/SQLite or a set of cleaned Parquet files. Rebuild `master` this way so it no longer depends on Google Drive.
2. **Geo join:** map CitiBike stations and MTA station complexes to NYC Neighborhood Tabulation Areas (NTAs) or ZIP codes so all datasets share a common geography.
3. **Layer 1 analysis (done, to be data-backed):** trip volume by station/time/neighborhood/bike type; e-bike vs. classic; member vs. casual; station-desert mapping (IBX-corridor NTAs with zero station access vs. population/transit dependency).
4. **Price → ridership story (reform notebook):** 3-city price inflation + ridership divergence, revenue-per-trip, price-optimization "sweet spot," and IBX expansion ROI/break-even. To harden: add DC/Chicago price index to the divergence chart, update to $239, source the Cell-3 figures, and — per the notebook's own margin note — forecast expected 2026 ridership under the hike and compare to actual 2026 trips as a validation.
5. **Subway ↔ bike relationship (NEW, active):** aggregate MTA Subway Hourly Ridership to neighborhood, join to CitiBike trips, and test the relationship. Neighborhoods with **high subway demand but low/zero bike access** (large negative residual vs. the fit line) become ranked expansion candidates that feed the decision engine.
6. **Economic correlation layer:** station density vs. DCA business density and pedestrian-count trend, controlling for population — present as correlation, explicitly not causation.
7. **Layer 2 (parked):** compile the fare-collection cost-savings table from public MTA budget documents — cite each figure individually; verify the headline fare-collection-cost number against current MTA financials before presenting it.
8. **Layer 3 synthesis:** the **decision engine** — expansion profit calculator (revenue, build cost, break-even, 5-yr net per neighborhood, with adjustable assumptions) + subway×bike signal view. Prototype exists; port to Streamlit as the capstone deliverable.

### 3b. Demand Forecasting (XGBoost) — supporting

- Target: daily trip count per station
- Features: calendar (day/month/weekend/holiday) + 1-day and 7-day lag + rolling mean
- Split: chronological (train on earlier months, test on most recent 60 days)
- Output: predicted demand vs. dock capacity → ranked expansion candidate list (feeds the decision engine)
- Metrics reported: MAE, RMSE, feature importance plot
- Role: this is a Layer-1 feature, not the load-bearing model. The price↔ridership validation (step 4) and subway↔bike relationship (step 5) carry the argument.

---

## 4. Repo Structure

```
/data/raw/          # untouched downloads (gitignored if large)
/data/processed/    # cleaned parquet/csv
/notebooks/         # EDA + reform analysis
/sql/               # ingestion + transform scripts
/dashboard/         # Streamlit app (from the decision-engine prototype)
/report/            # final write-up, slides, sources.md
demand_forecast_xgboost.py
plan.md             # this file
```

Current files in repo: `NYC_CitiBike_Analysis.ipynb`, `CitiBike_Reform_Analysis.ipynb`, `demand_forecast_xgboost.py`, `requirements.txt`, `README.md`, `plan.md`.

---

## 5. Open Decisions

- Date range for CitiBike data (recommend last 2–3 years for relevance + file size)
- Include Jersey City stations or NYC-only? (recommend NYC-only for a cleaner story)
- ~~Dashboard tool: Tableau vs. Power BI vs. web app~~ → **resolved: Streamlit web app**, built off the interactive decision-engine prototype
- Geography key for the join: NTA vs. ZIP vs. community district (the MTA quarterly report uses community district — may be the path of least resistance)
- How rigorously to fact-check the fare-collection-cost figure against current MTA budget documents before presenting it as a headline number
- Whether to source-verify or rebuild the 3-city comparison figures (see data-integrity note in 2.1)

---

## 6. Next Steps

1. Build the neighborhood crosswalk and produce one joined table: **MTA subway ridership × CitiBike trips** by neighborhood → unlocks the subway↔bike analysis and the candidate flags in the decision engine.
2. Make `master` reproducible from raw CSVs (drop the Google Drive dependency) so the app and notebooks run anywhere.
3. Harden the reform notebook: update to $239, add DC/Chicago price index to the divergence chart, source Cell-3 figures, run the 2026 ridership validation.
4. Port the decision-engine prototype to Streamlit and wire it to the real joined data.
5. Draft the report + slides, addressing the 250-station 2026 expansion head-on.
