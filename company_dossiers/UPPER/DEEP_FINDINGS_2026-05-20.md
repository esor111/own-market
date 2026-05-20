# UPPER — Deep 5-Year Analysis · 2026-05-20

**Source**: full 5-year nepsealpha daily series (1,668 bars, 2019-01-13 → 2026-05-19) + full broker fact table (343 days, 92 brokers) + corporate-action timeline + local OHLCV cross-source.
**Status**: descriptive only. Observation, not prediction. No buy/sell.

---

## TL;DR (the three things this analysis added)

1. **The single largest structural event in UPPER's recent history is the July-August 2024 rally** (153 → 286, +87% in ~6 weeks). 19 of the top 30 volume days in 5 years cluster in this window. We had not seen it before because our local OHLCV starts later AND because nepsealpha applies corporate-action adjustment that our local raw data doesn't.
2. **Broker fingerprinting across 343 days now shows clear "informed vs forced" patterns.** Broker 58 = consistently informed (price followed their lead by +3.58% avg over 5 days, n=21). Broker 44 = consistently forced (price went against their lead by −7.05% avg over 5 days, n=20). Two clean ends of a spectrum.
3. **Our local OHLCV (unadjusted) and nepsealpha's daily series (corp-action adjusted) diverge structurally on the pre-2023 history.** Local shows 766 peak (Feb 2022); nepsealpha shows 504 peak (Apr 2021). Both are correct in their own frame. For cross-source comparison, only the adjusted (nepsealpha) version represents true return-equivalent levels.

---

## 1. Multi-source data status (after today's refresh)

| Layer | Source | Range | Detail | Adjustment |
|---|---|---|---|---|
| EOD OHLCV | local scrape | 2021-09-01 → 2026-05-18 | 1,615 days | **Not** corp-action adjusted |
| Broker fact table | local from Merolagani | 2023-06-11 → 2026-05-18 | 343 days · 92 brokers · 261k rows | n/a |
| **EOD daily (adjusted)** | **nepsealpha** | **2019-01-13 → 2026-05-19** | **1,668 days** | **Corp-action adjusted** |
| Minute / hourly intraday | nepsealpha | 2021-05-20 → 2026-05-19 | 96,763 min bars · 570 days | Same as daily |
| Corporate events | timeline backfill + announcements | 2015-Feb → 2026-04 | 92 events | n/a |

All four layers are now wired into `dossier_data.assemble("UPPER")` and refreshable via the documented commands in `README.md`.

## 2. The 5-year structural picture (corrected)

From nepsealpha (corporate-action adjusted):

- **All-time high: Rs 504.00 on 2021-04-05** (pre-pandemic post-listing surge)
- **All-time low: Rs 153.10 on 2024-06-30** (3.3 years of grinding decline from the 2021 peak)
- **Latest: Rs 204.00 on 2026-05-19**
- Recovery from the 153 trough has been **uneven and incomplete**: rallied to 286 in Aug 2024, gave most back, hit ~169 in Sep 2025, rallied to 238 in Mar 2026, back to 204 now.

Major phases:
- **2019 → early 2021**: long base around 100-150 (post-listing era)
- **Apr 2021**: surge to 504 (post-COVID retail boom in NEPSE; pre-rights)
- **Apr 2021 → Jun 2024**: 3-year secular decline, dominated by the 2023 1:1 rights-share dilution which mechanically halved the price
- **Jun 2024**: bottom at 153
- **Jul-Aug 2024**: see §3 (the dominant event)
- **Sep 2024**: landslide, 88-day shutdown (chart shows price drifted but did not crash further — see Case #1 surroundings)
- **2025-H1**: recovery wave to ~250, then drift
- **Sep 2025**: re-test of 169 (the post-trough re-test of the basing zone)
- **Mar 2026**: rally to 238 (Case #2)
- **Apr-May 2026**: drift back to 204

## 3. The dominant structural event we'd been missing: July–August 2024

19 of the top 30 highest-volume days in 5 years sit in this 6-week window. The shape:

| Date | Close | Δ% | Volume | What happened |
|---|---:|---:|---:|---|
| 2024-06-30 | 153.10 | — | — | **5-year absolute low** |
| 2024-07-15 | 176.70 | +3.33% | 2,174,728 | Rally launch on heavy vol |
| 2024-07-18 | 188.60 | −0.53% | 2,082,349 | Sustained on volume |
| 2024-07-22 | 191.50 | +1.16% | 932,595 | Grinding up |
| 2024-07-23 | 203.60 | +6.32% | 967,741 | Breakout above 200 |
| 2024-07-24 | 213.90 | +5.06% | 1,376,794 | Continued |
| 2024-07-31 | 215.70 | +2.23% | 986,904 | End-of-month |
| 2024-08-06 | 200.00 | **−7.02%** | 956,826 | Sharp pullback day |
| 2024-08-08 | 213.00 | +1.87% | 888,517 | Recovery |
| 2024-08-11 | 234.30 | **+10.00%** | 2,451,686 | **LIMIT-UP** |
| 2024-08-12 | 254.90 | +8.79% | 1,958,240 | Continuation |
| 2024-08-13 | 256.80 | +0.75% | 1,419,070 | Stalling |
| 2024-08-14 | 270.50 | +5.33% | 1,839,917 | Re-acceleration |
| **2024-08-15** | **286.00** | **+5.73%** | 1,718,044 | **PEAK** |
| 2024-08-18 | 276.00 | −3.50% | 1,540,050 | First reversal |
| 2024-08-21 | 266.10 | −3.59% | 1,001,536 | Slide |
| 2024-08-25 | 254.20 | −4.79% | 975,373 | Slide |
| 2024-08-27 | 238.00 | **−6.37%** | 1,309,527 | Capitulation of the rally |
| 2024-03-14 | 187.90 | +2.34% | **2,768,765** | (separate March anomaly day, #1 by volume) |

**Net move June 30 → August 15: 153 → 286 = +86.9% in 32 trading days.**

This is the *kind* of move the source's §9.1 fiscal-year-end → August result rally describes. Whether it was *that* (a sector-wide BFI/Aug pattern spilling into hydro) or UPPER-specific can't be determined from price alone. It is also worth noting that this rally happened ~6 weeks **before** the September 27, 2024 landslide — meaning when the disaster hit, UPPER was already in a giving-back pattern from a doubled price. The landslide shutdown is what reset the post-rally narrative.

Catalyst remains `[unverified]`. Sector-wide flow into hydro post-monsoon-anticipation is a plausible narrative; web search didn't surface a specific UPPER-company catalyst from July 2024.

## 4. Broker fingerprinting (the major methodology advance)

Computed across the full 343-day broker fact table: for each broker, every time they were the *day's net leader* (largest |net_qty|), the average forward-5-day price move *in their direction* (positive = price followed them; negative = price went against them).

### Top "INFORMED" brokers (price tends to follow when they lead)

| Broker | Lead days (n) | Avg follow-through 5d | Max single net position |
|---|---:|---:|---:|
| **58** | **21** | **+3.58%** | 164,236 |
| 49 | 16 | +1.92% | 66,243 |
| 38 | 9 | +2.13% | 64,648 |

### Top "FORCED?" brokers (price tends to reverse against them)

| Broker | Lead days (n) | Avg follow-through 5d | Max single net position |
|---|---:|---:|---:|
| **44** | **20** | **−7.05%** | 260,306 |
| 48 | 11 | −1.31% | 76,653 |
| 42 | 23 | −1.14% | 75,536 |
| 45 | 12 | −1.12% | 48,953 |
| 26 | 7 | −1.10% | 42,030 |

### Strongest single fingerprints (by signal-to-noise)

- **Broker 58** is the standout informed signature. 21 lead days with avg follow-through of +3.58%. When they take the day's biggest net position, price moves an average of 3.58% in their direction over the next 5 days. Largest single position was 164k shares — significant institutional size.
- **Broker 44** is the standout forced/wrong-side. 20 lead days, max position **260k shares (the largest of any broker)**, but price moves an average of **−7.05% against** them over the next 5 days. Big positions, bad timing. Strong "forced flow" candidate.

### Critical caveats
- **N is small.** 7-23 lead days per broker. Confidence is moderate, not high.
- **Anonymous broker IDs** — we don't know who "broker 58" or "broker 44" is. They are not stable cross-source identities.
- **Survivorship**: this analysis only sees brokers who *appeared* in our fact-table window (2023-06 onwards). A broker active 2021-2022 wouldn't show.
- **Path-dependence**: a broker's avg may be dominated by 1-2 outsized days. Worth checking dispersion before any heavy reliance.

### What this changes for the recent dossier cases

**Case #1 (Apr 22 anomaly, broker 100)**: broker 100 had only 2 baseline days → too sparse to fingerprint. The forced-flow verdict came from Rule 1 (round-trip price-check) + closing-hour timing. Fingerprint can't add anything for this broker.

**Case #2 (March 2026 rally)**:
- Broker 28 (Mar 10 launch buyer, +119k) → only 3 lead days in 343, +0.something — too sparse, can't classify.
- Broker 88 (rally-long persistent seller) → 8 lead days, +0.46% (NOISE) — *not* clearly informed despite being the persistent distributor. Worth noting.
- Broker 49 (Mar 19 absorption buyer) → 16 lead days, **+1.92% (INFORMED)**. This is meaningful: broker 49 absorbed at the peak and price followed up... no, wait, it doesn't follow that direction at the peak — price went down. Need to look at this case-by-case, the +1.92 is an average across all their leads.

**Daily-read context (2026-05-18)**:
- **Broker 58** appeared as today's top-2 buyer (+8,454). 4-day net buyer streak. **History: INFORMED, +3.58% avg follow-through.** That's a real descriptive observation now: an informed-fingerprint broker is on the buy side in the current quiet tape.
- Broker 49 (top buyer today, +11,426) — also INFORMED signature historically (+1.92% avg).

These are descriptive observations, not signals. But they go in the daily read.

## 5. The opening-vs-closing-hour timing fingerprint (Candidate Rule 11)

From the earlier intraday work:
- **Opening-hour concentration ≥50%** on a heavy-volume day = positioning event (institutional/coordinated entry at the open). Examples: Mar 10 2026 (54.3%), Mar 19 2026 (51.2%).
- **Closing-hour concentration ≥40%** on a heavy-volume day = forced-flow event (mandatory execution / stop / margin / VWAP). Example: Apr 22 2026 (48%).

Not yet promoted to METHODOLOGY (N=1 on the closing-hour side). The Aug 2024 limit-up days would be perfect tests for this — when we get the intraday data for those days verified, we can promote or reject.

## 6. Open questions (what we still don't know)

1. **What lit the July 2024 → August 2024 rally?** The biggest move in 5 years has no documented catalyst in our events file. Hypothesis (unverified): sector-wide BFI fiscal-year-end + result-rally pattern spilling into hydro, possibly amplified by retail-channel flows. Worth a focused web search across nepsetrading / kathmandupost / fiscal nepal for July-August 2024 NEPSE coverage.
2. **What lit the March 10 2026 rally?** Still unknown after Case #2. The broker-58 informed signature was likely involved (he was active in that window).
3. **Who is broker 58?** A reliable informed-side actor on UPPER. With a broker-ID-to-name mapping (SEBON/NEPSE broker register), this becomes a *named* watch entity.
4. **Does broker 44's forced-side pattern generalize to other Nepali hydros?** If yes, broker 44 is a systematic forced-trader candidate worth a cross-symbol study. Cannot do this until UPPER dossier has 2 weeks of useful daily use (contract guardrail).

## 7. What I'd add to the methodology

Two candidate new rules earned from today:

- **Rule 11 (Broker fingerprinting via lead-day follow-through):** For any symbol with ≥1 year of broker data, compute per-broker: lead_days + average forward-5-day price move IN their net direction following their lead days. >+1% avg = INFORMED signature; <−1% = FORCED signature; ±1% = NOISE. Use only as descriptive context in daily reads ("today's top buyer is a historically-informed-signature broker"), never as a signal to follow.
- **Rule 12 (Cross-source corp-action awareness):** Always check whether a price series is corp-action-adjusted before cross-comparing levels. Our local OHLCV is NOT adjusted; nepsealpha IS. Pre-rights-share historical highs differ by ~50% between the two on UPPER. Always cite which source's level you're quoting.

These should be added to `METHODOLOGY.md` after a review pass.

---

## Sources

- `upper_volume_last_month_full.json` (2026-05-20 scrape, 5-year window, 1,668 daily bars).
- `broker_flow_fact_table.csv` (rebuilt 2026-05-19, UPPER 343 days).
- `dossier_data.assemble("UPPER")`.
- `company_dossiers/UPPER/deep_analysis.py` (the script).
- ShareSansar UPPER company page (https://www.sharesansar.com/company/upper).
- Web search for July-Aug 2024 UPPER catalyst — no specific result; sector-wide hypothesis only.
