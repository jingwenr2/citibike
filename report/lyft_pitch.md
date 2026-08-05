# Citi Bike Intelligence Platform — Lyft Executive Briefing

---

## The headline

**Citi Bike generates ~$196M/year. We built the data engine that shows Lyft how to turn it into $300M+.**

---

## Who we are

We analyzed **69.7 million real bike-share trips** across NYC and San Francisco — the largest independent bike-share dataset ever assembled for investment analysis. We built a machine learning demand forecasting engine, integrated MTA subway reliability data, and produced a live analytics dashboard that answers one question:

**Where should Lyft invest next, and how much will it return?**

---

## The 5 facts Lyft needs to hear

### 1. Your NYC bike-share is a $196M/year business — and most of that is e-bike fees.

| Revenue stream | Annual estimate | Source |
|---|---|---|
| E-bike overage fees ($0.27/min) | **$97.2M** | 30M e-bike trips x $3.24 avg |
| Annual memberships ($239/yr) | $47.8M | ~200K active members |
| Casual single rides ($4.49) | $33.4M | 7.4M casual trips |
| Citigroup title sponsorship | $17.5M | Public contract |
| **Total** | **~$196M/yr** | |

The e-bike overage line alone is half your revenue — and it scales directly with every new station you build.

---

### 2. You are supply-constrained, not demand-constrained.

- **1,247 of 2,466 stations** (50.6%) run at or above capacity daily
- **923 stations** (37.4%) are critical — demand exceeds 1.5x dock capacity
- Peak month: **5.4 million trips** in June 2026 alone
- **70% of all NYC trips are now e-bike** — riders want electric, and they're paying $3.24/ride for it

Every empty dock is a lost ride. Every full station is a customer who walks away. You're not missing demand — you're failing to capture it.

---

### 3. San Francisco proves government partnership works — NYC is 10x that market.

| Metric | San Francisco (Bay Wheels) | New York City (Citi Bike) |
|---|---|---|
| Population | ~900K | **8.3M** |
| Stations | 699 | **2,466** |
| Trips/station/day | 16.6 | **47.7** |
| Government support | SFMTA full integration | Minimal DOT involvement |

SFMTA treats Bay Wheels as public transit infrastructure — subsidized buildouts, protected lanes, route integration. Result: strong per-station usage in a city 1/10th the size. **NYC has 3x the per-station demand with almost no government support.** Imagine what happens when DOT comes to the table.

---

### 4. The MTA is failing — and your customers know it.

- Dozens of NYC neighborhoods have subway delay rates above 5%
- Hundreds of thousands of daily MTA riders are stuck on delayed trains
- When the L train has a bad morning, nearby Citi Bike stations spike
- Our model identifies exactly which neighborhoods are "transit backup" zones

**These aren't hypothetical riders. They're MTA customers who are already switching to Citi Bike when trains fail.** They'll switch permanently if you give them stations close enough to use.

---

### 5. 250 new stations = $11.3M/year in net profit. Payback: 17 months.

| | Amount |
|---|---|
| New annual revenue | **$15.0M** |
| One-time station install (250 x $65K) | $16.25M |
| Annual operations (250 x $15K) | $3.75M |
| **Net annual profit** | **$11.3M/yr** |
| **Payback period** | **17 months** |

After 17 months, every dollar is margin. And our XGBoost demand model — validated on 69.7M trips with **32% better accuracy** than seasonal baselines — tells you exactly **which** 250 locations to build first for maximum return.

---

## The 5-year revenue gap

| Scenario | 2026 | 2031 | 5-year total |
|---|---|---|---|
| Do nothing (3% growth) | $196M | $227M | ~$1.1B |
| 250 stations (self-funded) | $196M | $281M | ~$1.3B |
| 500 stations + DOT partnership | $196M | $352M | ~$1.5B |

**The difference between doing nothing and investing with DOT is ~$400M over 5 years.**

---

## What we built (it's not a deck — it's a working product)

1. **Demand forecasting engine** — XGBoost model predicts daily trips for each of 2,466 NYC stations. 32% more accurate than baselines. Tells ops where bikes will be needed tomorrow.

2. **Transit gap detector** — Joins MTA subway delay data to bike demand. Identifies which stations absorb transit failures and by how much.

3. **Expansion ranker** — Scores every underserved neighborhood by predicted demand, transit reliability gaps, and population density. Produces a prioritized build list.

4. **Live analytics dashboard** — 7-tab Streamlit app with real data, interactive charts, and the complete pitch for DOT partnership.

5. **Cross-city proof** — Same pipeline validated on both NYC (2,466 stations) and SF (699 stations). Deployable to Chicago, DC, London — anywhere with GBFS data.

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

**The data says invest. The math says it pays back in 17 months. The question isn't whether to expand — it's how fast.**

---

*Built on 69.7M real trips | XGBoost demand forecasting | MTA reliability integration | Live dashboard at localhost:8501*
