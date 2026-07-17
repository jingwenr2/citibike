# NYC Zero-Friction Mobility — Capstone Project Plan

**Core question:** What if NYC treated getting around as essential infrastructure that pays for itself through economic growth — not fares? CitiBike is the analytics nucleus; MTA free-fare is the policy case; the unified mobility stack is the vision.

**Status:** repo created, brainstorming locked (source: `CAPSTONE_BRAINSTORMING_IDEAS.pdf`, tab 2/5). This doc turns that pitch into an executable plan.

---

## 1. Three-Layer Architecture

| Layer | Focus | Primary tools |
|---|---|---|
| 1. CitiBike Data Core | Trip-level analytics: volume, e-bike vs. classic, member vs. casual, station deserts | Python, SQL, Excel |
| 2. MTA Free Fare Analysis | Cost/savings case for fare elimination | Excel, comparative case studies |
| 3. Unified Mobility Vision | Zero-friction mobility stack narrative + decision engine dashboard | Tableau/PowerBI, slides |

---

## 2. Validated Datasets (checked July 2026)

### 2.1 CitiBike (Layer 1 — primary)

| Dataset | Source | Notes |
|---|---|---|
| Citi Bike Trip Histories | https://citibikenyc.com/system-data | Monthly CSVs since 2013, ~1–2M rows/month. Post-2021 schema: `ride_id, rideable_type (classic_bike/electric_bike/docked_bike), started_at, ended_at, start/end station name+id+lat/lng, member_casual`. **This is the field that unlocks the e-bike analysis.** Pre-2021 files have older schema (gender, birth year) — decide whether to normalize or scope to 2021+ only. |
| GBFS real-time feed | https://gbfs.citibikenyc.com/gbfs/en/station_status.json | Live station status/capacity — useful for "station desert" mapping, not historical trend. |
| NYC Open Data mirror | https://catalog.data.gov/dataset/citi-bike-system-data | Same data, city catalog listing. |
| Starter ETL kit | https://github.com/toddwschneider/nyc-citibike-data | Scripts to download/clean/load trip data into Postgres. Good baseline to fork instead of writing ingestion from scratch. |

**Action item:** decide date range (recommend last 24–36 months for recency + manageable size) and whether to include Jersey City files (prefixed `JC`, exclude for an NYC-only story).

### 2.2 MTA (Layer 2)

| Dataset | Source | Notes |
|---|---|---|
| MTA Daily Ridership Data 2020–2025 | https://data.ny.gov/Transportation/MTA-Daily-Ridership-Data-2020-2025/vxuj-8kew | Subway/bus/LIRR/MNR/bridge-tunnel daily totals, good for trend + COVID recovery baseline. |
| MTA Subway Hourly Ridership (2025–) | https://data.ny.gov/Transportation/MTA-Subway-Hourly-Ridership-Beginning-2025/5wq4-mkjj | Station-complex, hourly, by fare payment class. |
| Subway Origin–Destination Ridership Estimates | via mta.info Open Data blog | Estimated rider flow between station pairs (OMNY/MetroCard-based) — closest thing to a "who goes where" dataset, useful for the labor-mobility argument. |
| Fare Card History | data.ny.gov | Historical fare structure changes for context. |

**Gap:** NYC has never run a fare-free pilot, so there's no natural experiment to regress ridership-vs-fare elasticity from local data. Treat Kansas City / Tallinn / Luxembourg as **literature-review inputs**, not datasets to merge in — cite them, don't try to join them.

### 2.3 Economic activity / foot traffic proxies (for the correlation story)

| Dataset | Source | Notes |
|---|---|---|
| DOF Summary of Neighborhood Sales | data.cityofnewyork.us/City-Government/DOF-Summary-of-Neighborhood-Sales-by-Neighborhood-/5ebm-myj7 | Property-sale based, a rough proxy — not retail revenue. Flag limitation clearly in the report. |
| DCA Licensed Businesses | data.cityofnewyork.us/Business/businesses/d8ic-tk4f | Business density by address — can aggregate to station-buffer counts. |
| NYC DOT Bi-Annual Pedestrian Counts | data.cityofnewyork.us/Transportation/Bi-Annual-Pedestrian-Counts/2de2-6x2h | 114 fixed count locations (100 street corridors + bridges + Hudson Greenway), collected since ~2007, restarted 2020. **Best available real foot-traffic proxy** — but only 114 points citywide, so it constrains which neighborhoods can be in the correlation analysis. |
| DCP Storefront Vacancy dataset/report | nyc.gov/planning (Storefronts Report, Nov 2024) | Retail corridor health trend, citywide first-of-its-kind storefront-level dataset. |

**Honest gap:** there is no NYC dataset that directly measures "retail spending near a CitiBike station." The correlation claim in the pitch deck has to be built from these proxies (business density + pedestrian counts + property sales), with the limitation stated explicitly, not implied as direct causation.

### 2.4 Secondary / comparative (Layer 3 narrative, not for merging)

- Kansas City (KCATA) free-bus ridership case
- Tallinn, Estonia fare-free transit (since 2013)
- Luxembourg nationwide free transit (2020)
- Interstate Highway System economic-return literature (for the "induced demand" framing)

These stay as cited sources in the report/slides, not tables in the data pipeline.

---

## 3. Methodology Sketch

1. **Ingest:** CitiBike monthly CSVs (chosen date range) + MTA ridership + NYC Open Data proxies into a local Postgres/SQLite or a set of cleaned Parquet files.
2. **Geo join:** map CitiBike stations and MTA station complexes to NYC Neighborhood Tabulation Areas (NTAs) or ZIP codes so all datasets share a common geography.
3. **Layer 1 analysis:** trip volume by station/time/neighborhood/bike type; e-bike vs. classic (distance, duration, revenue proxy); member vs. casual conversion; station-desert mapping (NTAs with low station density vs. population/job density).
4. **Layer 2 analysis:** compile the cost-savings table (fare collection, enforcement, turnstile maintenance) from public MTA budget documents — cite each figure's source individually, don't reuse the deck's numbers without verifying against current MTA financials.
5. **Correlation layer:** station density vs. DCA business density and pedestrian-count trend, controlling for population — present as correlation, explicitly not causation.
6. **Layer 3 synthesis:** build the "decision engine" dashboard (optimal expansion stations, ROI timeline framing, borough-level impact) as the capstone deliverable.
### 3b. Demand Forecasting (XGBoost)
- Target: daily trip count per station
- Features: calendar (day/month/weekend/holiday) + 1-day and 7-day lag + rolling mean
- Split: chronological (train on earlier months, test on most recent 60 days)
- Output: predicted demand vs. dock capacity → ranked expansion candidate list
- Metrics reported: MAE, RMSE, feature importance plot

---

## 4. Suggested Repo Structure

```
/data/raw/          # untouched downloads (gitignored if large)
/data/processed/    # cleaned parquet/csv
/notebooks/         # exploratory analysis
/sql/                # ingestion + transform scripts
/dashboard/          # Tableau/PowerBI workbook or exported files
/report/             # final write-up, slides, sources.md
plan.md              # this file
```

---

## 5. Open Decisions (need team input)

- Date range for CitiBike data (recommend last 2–3 years for relevance + file size)
- Include Jersey City stations or NYC-only?
- Dashboard tool: Tableau vs. Power BI vs. a lightweight web app?
- How rigorously to fact-check the $1.4B/year fare-collection-cost figure against current MTA budget documents before presenting it as a headline number

---

## 6. Next Steps

1. Fork/adapt `toddwschneider/nyc-citibike-data` for ingestion, or write a lighter custom loader
2. Pull 24–36 months of CitiBike + matching MTA ridership data
3. Build the NTA/ZIP crosswalk for all datasets
4. First deliverable: Layer 1 exploratory notebook (trip volume, e-bike adoption, station deserts)
