# Fare Equity Fund — Analysis for Team Review

**Status: implemented. Live in the dashboard — Government Investment tab → "Fare equity fund" expander (adjustable discount-depth slider, defaults to $4.4M). The figures below now match the dashboard's live output (`backend/services/revenue_service.py::estimate_fare_equity_fund`), refreshed against current trip data rather than the original hand math.**

---

## The idea

San Francisco's Bay Wheels didn't just get a station-expansion investment from MTC in Feb 2023 — it got two, structured separately:

| Bay Wheels (Feb 2023) | Nominal | In 2026 dollars* |
|---|---|---|
| Station expansion | $16M | $17.5M |
| Fare-equity pilot (college students / economic barriers) | $4M | **$4.4M** |
| **Total** | **$20M** | **~$21.9M** |

\* Inflation adjustment: ~9.375%, derived from the $16M → $17.5M relationship already used elsewhere in the deck. Applied consistently to both line items. This is a back-of-envelope CPI estimate, not a sourced BLS figure — flag if anyone wants it tightened before it's quoted publicly.

**Proposal:** mirror that same two-track structure for NYC, instead of asking for one undifferentiated pool:
- **$17.5M** — the 250-station buildout ($70K/station, pegged so the total matches SF's inflation-adjusted figure exactly)
- **~$4.4M** — a dedicated, ring-fenced fare-equity fund, spent on reducing membership price for members broadly (not folded into general surplus)

---

## What the $4.4M buys

Two members bases were tested; **we're going with "all members, old and new"** (207,500 = 200,000 existing + 7,500 new members from the 250 stations):

**$4.4M ÷ 207,500 members = $21.21/member**

**$239 → $217.79 (~$218)**, an **8.9% cut**, applied system-wide.

### Funding structure

- **Year 1:** the one-time $4.4M pilot fund covers the full $21/member subsidy for all 207,500 members.
- **Year 2 onward:** the 250-station expansion's own recurring profit takes over funding the subsidy — see payback math below. The discount does **not** require a second $4.4M ask; it's designed to make itself permanent.

---

## Revised 250-station revenue projection

The dashboard computes the discount cost as one pool spread across all 207,500 members (existing + new) rather than splitting "new members" and "existing members" into separate costs — cleaner than the original hand math this doc started with, and this is what's actually running:

| | Amount |
|---|---|
| Expansion net profit, full $239 pricing (250 stations, current live data) | **$12.9M/yr** |
| Ongoing cost of the $218 discount, all 207,500 members | **−$4.4M/yr** |
| **Net profit after funding the discount** | **$8.5M/yr** |
| **Payback period** on $17.5M capital cost | **~25 months**, up from 16 months undiscounted |
| **Ongoing annual surplus after payback** | **$8.5M/yr** |

**Bottom line:** the expansion fully self-funds a *permanent* citywide 8.9% membership discount, with capital payback still under 25 months. From year two on there's $8.5M/year of surplus on top of a system that's structurally cheaper to ride.

---

## Who actually benefits: Lyft vs. the city

This is the part most likely to get conflated in the speech — worth being precise with the team before it goes out.

| Beneficiary | Channel | Amount |
|---|---|---|
| **Lyft** | Net operating profit (expansion revenue − operating costs − discount cost, before any revenue share) | **~$8.5M/year** |
| **City** | Revenue share (2.5% of total company revenue — planning assumption, not a verified contract figure) | **+$306K/year** |
| **City** | Public benefit (health + congestion + emissions on new trips, plus 8% tax on new revenue — `estimate_public_benefits` in `revenue_service.py`) | **~$6.03M/year** |
| **City total (revenue share + public benefit)** | | **~$6.34M/year** |

**Do not describe the $8.5M surplus as money the city gets — it isn't.** It's Lyft's margin. The city's real gain here is ~$6.34M/year, split between a modest revenue-share bump ($306K, small because the discount cost is netted against total revenue before the percentage is applied) and the larger, separately-modeled public-benefit figure (health/congestion/emissions/tax).

That $6.34M-to-city vs. $8.5M-to-Lyft split is a fine story — both sides win, Lyft more — but it's a different claim than "the city earns $8.5M more," and someone will do this math live if it's overstated. Both the Lyft-profit and city-revenue-share figures move with the equity-fund slider in the dashboard; only the public-benefit figure is fixed (it depends on trip volume from the 250-station expansion, not the discount depth).

---

## Open questions / before this goes in the speech

1. **One-time vs. recurring fund, confirmed:** we're treating the $4.4M as a one-time seed that the expansion's own profit sustains afterward — confirm this is the intended structure, since it changes what you can promise on stage ("one-time investment" vs. "annual commitment").
2. **Inflation adjustment (~9.375%)** is a rough estimate, not a cited CPI figure. Fine for an internal planning doc; get a sourced number before it's printed in a deck or said to press.
3. **"GDP multiplier effect"** language in the reframed city-benefit section is not backed by any number in this analysis or the model. Either keep it qualitative (as drafted) or find a real citation — don't let it be the one unsourced statistic in an otherwise data-backed pitch.
1
5. ~~None of this lives in the dashboard model yet.~~ **Resolved:** `revenue_service.estimate_fare_equity_fund()` implements this, wired into the Government Investment tab as an adjustable slider ($0–$10M range, defaults to $4.4M). `pricing_assumptions.json` now carries `city_revenue_share_rate` (0.025) as a documented, flagged planning assumption.
6. **The underlying trip data has grown since this doc was first drafted** — live revenue is now ~$212M (not $196M) and the 250-station payback is 16 months (not 17). The $218 target price and 8.9% cut are unchanged (they only depend on membership counts and price, not revenue), but the payback and profit-split figures above have been refreshed to match. Note the station install cost itself was also repegged from $65K to $70K/station specifically so the 250-station total ($17.5M) matches SF's inflation-adjusted figure exactly, rather than being a separate, coincidentally-close number. Re-check this doc against the dashboard before quoting exact dollars, since the underlying data will keep moving as new trip months are added.

---

*Prepared as planning support for the pitch speech; all figures are estimates pending team review, not final numbers for external presentation.*
