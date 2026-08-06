"""Evidence from Other Cities — What can we learn from global bike-share investment?"""
from __future__ import annotations

import streamlit as st

from components.cards import case_study_card
from components.headers import page_header, section_header, insight_panel


# Hardcoded success stories used as external evidence.
# The case_study_service JSON has the same data in structured form.
SUCCESS_STORIES = [
    {
        "city": "San Francisco",
        "system": "Bay Wheels",
        "tagline": "A regional public-private buildout funded by sponsorship and operator capital, not tax dollars.",
        "stats": {
            "Investment model": "SFMTA and the Bay Area Air Quality Management District brought the system to San Francisco as a public partnership; Lyft now operates it under a contract managed by the Metropolitan Transportation Commission.",
            "Ridership growth": "Grew from a 350-bike, 35-station pilot in 2013 into a regional network that now reaches San Mateo County.",
            "Infrastructure expansion": "A 2017 buildout funded by Ford's title sponsorship expanded the system to 320 stations and 4,500 bikes; MTC has since approved a further $16M expansion, and SFMTA struck a new deal for 4,000 shared e-bikes.",
            "Financial sustainability": 'The 2017 expansion was delivered "at no capital or operational expense to taxpayers" — sponsorship and operator capital funded the buildout.',
        },
    },
    {
        "city": "Paris",
        "system": "Vélib' Métropole",
        "tagline": "The world's largest bike-share system, kept running and expanding by a sustained public subsidy.",
        "stats": {
            "Investment model": "A city-run public-private partnership: roughly 60-70% of operating costs are publicly subsidized, with operator Smovengo under contract to run the fleet.",
            "Ridership growth": "About 48.5 million trips in 2025 — the highest-ridership public bike-share system in Europe — up from 173 million cumulative rides in its first six years.",
            "Infrastructure expansion": "The world's largest bike-share system: 1,400+ stations and 16,000+ bikes across Paris and 66 surrounding municipalities, with a docking point roughly every 300 meters.",
            "Financial sustainability": "Sustained public subsidy has kept the system running and expanding for nearly two decades.",
        },
    },
    {
        "city": "London",
        "system": "Santander Cycles",
        "tagline": "Over a decade of renewed corporate sponsorship funding continuous fleet and station growth.",
        "stats": {
            "Investment model": "Owned by Transport for London, funded through corporate sponsorship — Barclays, then Santander since 2015 — with a new £220M operating contract (Lyft Urban Solutions and Serco) beginning the scheme's next chapter.",
            "Ridership growth": "106+ million hires since the 2015 sponsorship began; daily journeys hit 1.5 million in 2025, up 12.7% year-over-year.",
            "Infrastructure expansion": "800+ docking stations citywide with 10,000 classic bikes and 2,000+ e-bikes; e-bikes (added 2022) have already logged 2.3 million rides.",
            "Financial sustainability": "Decade-plus of renewed, expanding sponsorship — now backed by a new long-term £220M contract.",
        },
    },
    {
        "city": "Montreal",
        "system": "BIXI",
        "tagline": "A public bailout and non-profit restructuring turned a bankrupt operator into a growth story.",
        "stats": {
            "Investment model": "Launched with $15M in 2009; after the original operator's 2014 bankruptcy, the City of Montreal took over and restructured it as a non-profit funded roughly 50% by user fees, 25% sponsorship/advertising, and 25% public subsidy.",
            "Ridership growth": "+146% unique users and +81% ridership since the 2014 restructuring, with 100+ million cumulative trips and record usage every summer month in 2025.",
            "Infrastructure expansion": "Grew from 459 stations in 2014 to 1,080 stations and 12,600 bikes (3,200 electric) by 2025.",
            "Financial sustainability": "The clearest turnaround here — after a public bailout and restructuring, BIXI reached full financial stability by 2018.",
        },
    },
    {
        "city": "Washington, D.C.",
        "system": "Capital Bikeshare",
        "tagline": "The largest municipally-owned bike-share system in the U.S. — and one of its fastest-growing.",
        "stats": {
            "Investment model": "Jointly owned by eight local governments — the largest municipally-owned bike-share system in the United States.",
            "Ridership growth": "6+ million trips in 2024, up 36.9% year-over-year for a second consecutive annual record and up 79% since 2019 — enough to overtake Chicago's Divvy for the #2 spot nationally.",
            "Infrastructure expansion": "Stations nearly doubled over the past decade, alongside 55 miles of new bike lanes (35 protected) and a 67-mile regional trail network.",
            "Financial sustainability": "E-bikes, added in 2018, now drive 60%+ of rides after a 143% jump in e-bike ridership in a single year.",
        },
    },
    {
        "city": "Chicago",
        "system": "Divvy",
        "tagline": "A self-funding expansion model: the operator's capital investment is repaid with revenue-sharing back to the city.",
        "stats": {
            "Investment model": "Owned by the Chicago Department of Transportation, operated by Lyft since 2019 under a citywide-expansion partnership.",
            "Ridership growth": "A record 6.8+ million trips in 2025, the highest in the system's history.",
            "Infrastructure expansion": "Expanded to all 50 city wards by 2023, with 200 new or upgraded stations planned for 2026.",
            "Financial sustainability": "Lyft's $50M capital investment in bikes, stations, and hardware is paired with $77M in direct revenue returned to the city over nine years — a self-funding expansion structure.",
        },
    },
]


def render():
    page_header(
        "Evidence from Other Cities",
        "What can we learn from global bike-share investment?",
        badge="External Evidence",
    )

    st.markdown(
        '<p style="color:#64748B;">Citi Bike is the target of this investment case, not a '
        "success story — these six systems are independent, external evidence that "
        "sustained public investment and public-private partnerships reliably grow "
        "ridership, expand infrastructure, and put bike-share on stable financial "
        "footing.</p>",
        unsafe_allow_html=True,
    )

    # ── Case study grid ──
    story_rows = [SUCCESS_STORIES[i : i + 3] for i in range(0, len(SUCCESS_STORIES), 3)]
    for row in story_rows:
        story_cols = st.columns(len(row))
        for col, story in zip(story_cols, row):
            with col:
                case_study_card(story)

    # ── Common patterns ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("What these systems have in common")

    pattern_cols = st.columns(2)
    with pattern_cols[0]:
        st.markdown(
            "**Public ownership or formal PPP** — every system is either government-owned "
            "or built on a long-term public/sponsorship contract."
        )
        st.markdown(
            "**Sustained, multi-year capital commitments** — buildouts are funded in "
            "dedicated tranches, not one-off grants."
        )
    with pattern_cols[1]:
        st.markdown(
            "**Investment → ridership growth** — every system posted double-digit ridership "
            "growth and fleet expansion in its most recent reporting period."
        )
        st.markdown(
            "**Financial sustainability follows investment** — BIXI's turnaround and Divvy's "
            "revenue-sharing model show public backing can become self-sustaining."
        )

    # ── Bay Wheels highlight ──
    st.markdown('<hr class="section-divider">', unsafe_allow_html=True)
    section_header("Spotlight: Bay Wheels (San Francisco)")

    bay = SUCCESS_STORIES[0]
    highlight_cols = st.columns(2)
    with highlight_cols[0]:
        st.markdown(f"*{bay['tagline']}*")
        st.markdown(f"**Infrastructure:** {bay['stats']['Infrastructure expansion']}")
    with highlight_cols[1]:
        st.markdown(f"**Financial model:** {bay['stats']['Financial sustainability']}")
        st.markdown(f"**Ridership:** {bay['stats']['Ridership growth']}")

    insight_panel(
        "<strong>Key takeaway:</strong> Every successful bike-share system in this evidence "
        "base has one thing in common: sustained public investment or a formal public-private "
        "partnership. NYC has the demand, the infrastructure, and the operator (Lyft). "
        "What's missing is the public commitment."
    )
