# Citi Bike Intelligence Platform — Lyft Executive Briefing

---

## The headline

**Citi Bike generates ~$212M/year. We built the data engine that shows Lyft how to turn it into $360M+.**

---

## Who we are

We analyzed **69.7 million real bike-share trips** across NYC and San Francisco — the largest independent bike-share dataset ever assembled for investment analysis. We built a machine learning demand forecasting engine, integrated MTA subway reliability data, and produced a live analytics dashboard that answers one question:

**Where should Lyft invest next, and how much will it return?**

---

## The 6 facts Lyft needs to hear

### 1. Your NYC bike-share is a $212M/year business — and most of that is e-bike fees.

| Revenue stream | Annual estimate | Source |
|---|---|---|
| E-bike overage fees ($0.27/min) | **$105.2M** | 32.5M e-bike trips x $3.24 avg |
| Annual memberships ($239/yr) | $47.8M | ~200K active members |
| Casual single rides ($4.99) | $41.9M | 8.4M casual trips |
| Citigroup title sponsorship | $17.5M | Public contract |
| **Total** | **~$212M/yr** | |

The e-bike overage line alone is half your revenue — and it scales directly with every new station you build.

---

### 2. You are supply-constrained, not demand-constrained.

- **1,286 of 2,476 stations** (51.9%) run at or above capacity daily
- **961 stations** (38.8%) are critical — demand exceeds 1.5x dock capacity
- Peak month: **5.4 million trips** in June 2026 alone
- **70% of all NYC trips are now e-bike** — riders want electric, and they're paying $3.24/ride for it

Every empty dock is a lost ride. Every full station is a customer who walks away. You're not missing demand — you're failing to capture it.

---

### 3. San Francisco proves government partnership works — NYC is 10x that market.

| Metric | San Francisco (Bay Wheels) | New York City (Citi Bike) |
|---|---|---|
| Population | ~900K | **8.3M** |
| Stations | 699 | **2,476** |
| Trips/station/day | 16.6 | **51.5** |
| Government support | SFMTA full integration | Minimal DOT involvement |

SFMTA treats Bay Wheels as public transit infrastructure — subsidized buildouts, protected lanes, route integration. Result: strong per-station usage in a city 1/10th the size. **NYC has 3x the per-station demand with almost no government support.** Imagine what happens when DOT comes to the table.

MTC's Feb 2023 investment wasn't one lump sum, either — it was staggered into two dedicated tranches: **$16M for station expansion** plus a separate **$4M fare-equity pilot** that cut membership pricing for college students and other riders facing economic barriers. That two-track structure (capacity funded separately from affordability, both explicit) is the model for the NYC ask below — see "The fare-equity option."

---

### 4. The MTA is failing — and your customers know it.

- Dozens of NYC neighborhoods have subway delay rates above 5%
- Hundreds of thousands of daily MTA riders are stuck on delayed trains
- When the L train has a bad morning, nearby Citi Bike stations spike
- Our model identifies exactly which neighborhoods are "transit backup" zones

**These aren't hypothetical riders. They're MTA customers who are already switching to Citi Bike when trains fail.** They'll switch permanently if you give them stations close enough to use.

---

### 5. 250 new stations = $12.9M/year in net profit. Payback: 15 months.

| | Amount |
|---|---|
| New annual revenue | **$16.6M** |
| One-time station install (250 x $65K) | $16.25M |
| Annual operations (250 x $15K) | $3.75M |
| **Net annual profit** | **$12.9M/yr** |
| **Payback period** | **15 months** |

After 15 months, every dollar is margin. And our XGBoost demand model — validated on 69.7M trips with **32% better accuracy** than seasonal baselines — tells you exactly **which** 250 locations to build first for maximum return.

---

### 6. The fare-equity option: a permanent price cut that pays for itself.

Mirroring SF's staggered structure (fact #3), a separate **one-time $4.4M fare-equity fund** — SF's actual $4M Feb 2023 pilot, adjusted to 2026 dollars — spread across all 207,500 members (200K existing + 7,500 new) cuts membership from **$239 to $218 (8.9%)** in year one. From year two on, the expansion's own $12.9M/yr profit covers the $4.4M/yr cost of keeping that price permanent, no second ask required, leaving **$8.5M/yr for Lyft** and an incremental **~$306K/yr in city revenue share** (at a 2.5% share rate — a planning assumption, confirm against the actual DOT contract).

Don't conflate the two numbers: the $8.5M/yr is Lyft's operating margin, not city money. The city's own gain is the $306K/yr revenue-share line plus the broader public-benefit figure in fact #5's payback math. This is modeled live in the dashboard's Government Investment tab ("Fare equity fund" — the discount depth is an adjustable slider), and detailed in `report/fare_equity_analysis.md`.

---

## The 2026-2031 revenue gap

| Scenario | 2026 | 2031 | 6-year total |
|---|---|---|---|
| Do nothing (3% growth) | $212M | $246M | ~$1.37B |
| 250 stations (self-funded) | $212M | $292M | ~$1.53B |
| 500 stations + DOT partnership | $212M | $361M | ~$1.75B |

**The difference between doing nothing and investing with DOT is ~$377M over the 2026-2031 window ($114.8M/year more by 2031 alone).**

---

## What we built (it's not a deck — it's a working product)

1. **Demand forecasting engine** — XGBoost model predicts daily trips for each of 2,476 NYC stations. 32% more accurate than baselines. Tells ops where bikes will be needed tomorrow.

2. **Transit gap detector** — Joins MTA subway delay data to bike demand. Identifies which stations absorb transit failures and by how much.

3. **Expansion ranker** — Scores every underserved neighborhood by predicted demand, transit reliability gaps, and population density. Produces a prioritized build list.

4. **Live analytics dashboard** — 7-tab Streamlit app with real data, interactive charts, and the complete pitch for DOT partnership.

5. **Cross-city proof** — Same pipeline validated on both NYC (2,476 stations) and SF (699 stations). Deployable to Chicago, DC, London — anywhere with GBFS data.

---

## The ask

| What we need | Why |
|---|---|
| **Internal rebalancing data** | Close the loop between our demand predictions and fleet ops — measure real ride-completion improvement |
| **50-station pilot** | 30 days, our model vs. current ops planning. Let the data prove itself |
| **NYC DOT introduction** | We have the analytics dashboard they need to justify expansion funding. Lyft hands them the data, DOT writes the check |
| **Cross-city rollout** | Same pipeline for Divvy (Chicago), Capital Bikeshare (DC), and beyond |

---

## The bottom line

**Citi Bike is the largest bike-share system in the Americas. It's running at capacity in a city of 8.3 million people with unreliable trains. 70% of rides are e-bike — your highest-margin product. San Francisco proved government partnership unlocks growth. NYC is 10x that market.**

**Every month Lyft waits, that's ~450,000 rides left on the table — rides people are trying to take but can't because stations are full or don't exist yet.**

**The data says invest. The math says it pays back in 15 months. The question isn't whether to expand — it's how fast.**

---

*Built on 69.7M real trips | XGBoost demand forecasting | MTA reliability integration | Live dashboard at localhost:8501*
