# UPPER — Event Case #2: March 2026 Rally (2026-03-10 → 2026-03-22)

**Case opened**: 2026-05-20
**Type**: Multi-day directional rally (+29% close-to-close in ~10 trading days)
**Status**: Descriptive only. **Observation, not prediction.** Per `DOSSIER_CONTRACT.md` §5; methodology rules referenced from `METHODOLOGY.md`.

---

## 1. Mechanical selection rule (per METHODOLOGY Rule 6)

This case was surfaced *mechanically*, not by memory:
- **Largest 1Y price move on UPPER:** ~+29% close-to-close in 10 trading days (Mar 10 close 216 → Mar 22 close 238), visible as the dominant feature of the 1Y local chart `charts/upper_1y.png`.
- **Top 3 single-day volume bars in the entire Mar–Apr window** sit inside this rally: Mar 19 (2,548,271), Mar 10 (2,114,315), Mar 22 (1,552,477) — each ~5-6× the size of the Apr 22 anomaly we covered in Case #1.
- Both criteria are external/mechanical: chart-derived top-1Y move + volume threshold. Not hindsight selection.

## 2. Price/volume chronology (local data + ShareSansar agree, Rule 4)

| Date | Close | Δ% | Volume | Note |
|---|---:|---:|---:|---|
| 2026-02-22 | 182.00 | — | low-vol | Pre-rally low |
| 2026-03-10 | 216.00 | +3.55% | **2,114,315** | **RALLY LAUNCH** |
| 2026-03-11 | 215.50 | −0.23% | 989,655 | sustained on heavy vol |
| 2026-03-12 | 218.00 | +1.16% | 1,087,302 | grind up |
| 2026-03-15 | 218.90 | +0.41% | 725,559 | continued |
| 2026-03-16 | 213.00 | −2.70% | 643,694 | first pullback |
| 2026-03-17 | 219.10 | +2.86% | 915,030 | bounce |
| 2026-03-19 | 235.60 | **+7.53%** | **2,548,271** | **BATTLE DAY (max vol)** |
| 2026-03-22 | **238.00** | +1.02% | 1,552,477 | **PEAK** |
| 2026-03-23 | 236.00 | −0.84% | 741,234 | reversal begins |
| 2026-03-25 | 230.00 | −2.91% | 664,956 | drop continues |
| 2026-03-29 | 223.00 | −4.66% | 924,493 | heavy-vol sell |
| 2026-04-01 | 208.10 | −4.76% | 594,242 | retrace continues |
| 2026-04-05 | 198.60 | −4.52% | 528,921 | gain mostly retraced |

**Notes on data hygiene** (per Rule 4): some adjacent dates (Mar 13/14, 17/18, 20/21, Apr 2/3/4) show identical numbers in the OHLCV files — scraper fills on non-trading-day filenames in the Sun-Thu calendar in effect pre-2026-04-10. The broker fact table self-cleans this (only real trading sessions have broker rows), so the analysis here is on confirmed trading days only.

## 3. Broker-flow analysis on the three key dates

### 2026-03-10 — RALLY LAUNCH (+3.55%, 2.11M volume)

- **Top-5 BUY concentration 30.7% > top-5 SELL 21.4%** → buyers more concentrated than sellers.
- **Largest single net position of the day: broker 28 net BUYER +119,250** (~5.6% of day volume).
- Other large net buyers: broker 64 (+71,032, only 3 of trailing 20 baseline days seen → **episodic**), broker 44 (+66,576), broker 42 (+55,119), broker 34 (+47,048).
- Sell side broader, none singularly dominant.
- **Footprint shape:** *concentrated buying into broad selling* — the textbook accumulation-launch profile.

### 2026-03-19 — BATTLE DAY (+7.53%, 2.55M volume, biggest single bar of the rally)

- Top-5 buy 22.7% vs top-5 sell 24.6% — **near-equal concentration; wide participation on both sides.**
- **Largest net sellers:** broker 35 (−95,082), broker 88 (−80,854; broker 88 sold 88k, bought only 7k = almost pure sell).
- **Largest net buyers:** broker 66 (+66,493), broker 49 (+65,861).
- **Price went UP 7.53% on the most aggressive sell-leader day of the rally.** That is the signature of **active absorption**: buyers willing to take everything sellers offered, at higher prices.

### 2026-03-22 — PEAK (+1.02%, 1.55M volume)

- Top-5 buy 25.5% vs top-5 sell 25.8% — balanced.
- Largest net seller: broker 44 (−63,996).
- Largest net buyers: broker 58 (+50,850), broker 26 (+42,030), broker 10 (+36,375).
- The day after (Mar 23) was net-buy-led (broker 6 +46k) — final upward push before exhaustion.

## 4. Persistence layer across the whole rally (per METHODOLOGY Rule 2)

Combining the persistence analyses around Mar 19 and Mar 22 (overlapping windows):

| Broker | Persistence span | Side | Interpretation |
|---|---|---|---|
| **88** | **6-7 days before + 6-7 days after** (both events) | **SELLER** | **Structural distributor of the rally** — sold continuously through and across the peak |
| **37** | 6-7 days before + 4-5 days after | BUYER | Structural buyer counterparty |
| **18** | 2-3 days before + 7-8 days after | BUYER | Post-peak persistent accumulator |
| 51, 82 | 3 days before + 2 days after | SELLER | Secondary persistent sellers |
| 3, 6 | 2 days before + 2-3 days after | both sides | Smaller persistent presence |

**This is the key methodological finding:** broker 88 was *persistently selling for ~2 weeks* across the entire rally, including the peak. They were not caught long — they fed supply into rising prices.

## 5. Round-trip price-check on broker 88 (per METHODOLOGY Rule 1)

Broker 88 sold persistently across **rising** prices (Mar 17 close 219 → Mar 19 close 236 → Mar 22 close 238). They did **not** appear as a major buyer on the post-peak weakness either — pure one-direction flow.

**Verdict per Rule 1:** broker 88 was selling *higher* than they would have bought (had they been net long earlier) → this is the **smart-money distribution signature** (informed exit into strength). This is the **opposite** of broker 100 on Apr 22 (loss-making round trip = forced flow).

## 6. Side-by-side: Case #1 (Apr 22) vs Case #2 (Mar rally) — the contrast that matters

| | Case #1: Apr 22 anomaly | Case #2: Mar rally |
|---|---|---|
| Protagonist | broker 100 (episodic) | broker 88 (persistent) |
| Pattern | One-week round-trip BUY then SELL | Two-week persistent SELL only |
| Round-trip price | Bought ~224, sold ~207 → **loss** | Sold into rising 219→236→238 → **profit** |
| Rule 1 verdict | Forced flow / stop / redemption | Informed distribution into strength |
| Underlying persistent layer | Net-BUY-leaning underneath | Counterparty buyers absorbed; eventually exhausted |
| Net effect on price | Accelerated a pre-existing slide | Rally peaked exactly during this distribution |

**The contrast IS the value.** A naive "big volume + sell concentration = distribution" reading would have called both events identically. The data shows they were structurally different events with different actors, different motivations, and (likely) different counterparty types.

## 7. Catalyst — what we DO and DO NOT know

**Known (data-confirmed):**
- The rally launched on a *concentrated buy-led day* (Mar 10, broker 28 +119k), not on diffuse retail interest.
- The peak day's biggest absolute volume came with both heavy buying AND heavy selling — absorption battle.
- Broker 88 was a multi-week structural distributor.
- Post-peak retrace was on continued heavy volume with no fresh buyer interest after a brief Mar 23-24 bounce.

**Unknown (`[unverified]` per Rule 8):**
- **The actual catalyst for Mar 10.** Our `dossier_data.corporate_actions("UPPER")` events list shows no corporate action / announcement on that day. The Q2 result was Feb 13, the AGM announcement came April 6 — neither aligns. Candidates worth checking but not yet verified: (a) NEPSE-wide rally that day, (b) hydro-sector flow, (c) an unrecorded news item, (d) inflow/redemption flow from a fund. **Genuinely open.**
- **Broker 28's identity** (the Mar 10 buy protagonist) and **broker 88's identity** (the rally-long seller). Anonymous broker IDs.

## 8. What this case adds to the dossier methodology

1. **Rule 1 (round-trip price-check) now has BOTH ends of its spectrum demonstrated:** broker 100 (forced, loss-making) vs broker 88 (informed, profitable). Confidence in the rule rises.
2. **Rule 2 (persistence layer) caught the structural distributor (broker 88)** that day-level views during the rally itself would have called "noise on a +7.5% up day."
3. **"Wide participation + balanced top-5 + price strongly up = active absorption"** — descriptive observation worth keeping as a transferable pattern. Candidate addition to METHODOLOGY.md as Rule 9 ("absorption signature"): balanced concentration on heavy volume with price moving sharply in one direction = the absorbing side is winning.

## 9. Limits (per DOSSIER_CONTRACT §7, binding)

- This case **does not say** "the next Mar 10-shaped event on UPPER is a buy" or "watch broker 88 to short."
- Broker identities are anonymous and may not persist as same-entity over years.
- The Mar 10 catalyst is **unknown**. A pattern with an unidentified driver should not be relied on.
- Generalising broker 88's behaviour to other Nepali hydros from N=1 case is data-snooping.

## Addendum (2026-05-20): intraday finding from nepsealpha minute data

Source: `experiments/08-hydro-volume-tape-lab/raw/UPPER/upper_volume_last_month_full.json` (scraped 2026-04-27 via `refresh_upper_data.ps1` + `scripts/refresh_nepse_symbol.js`; CDP-attach to a real Chrome session, `fsk`-token sniff, iframe-context fetch — the *working* nepsealpha pipeline I previously declared impossible; see METHODOLOGY Rule 10).

The minute-bar data adds a single decisive observation the EOD analysis could not see:

| Date | Day volume | **Opening hour (11:00 NPT) volume** | **Opening hour share** |
|---|---:|---:|---:|
| 2026-03-10 (rally launch) | 2,114,315 | 1,147,960 | **54.3%** |
| 2026-03-19 (battle/absorption day) | 2,548,271 | 1,305,441 | **51.2%** |
| 2026-03-22 (peak) | 1,552,477 | 597,112 | 38.5% |

**The March rally was an OPENING-HOUR phenomenon.** On the two biggest-volume rally days, **>50% of the entire day's volume traded in the first hour after the 11:00 NPT open.** That is the timing-fingerprint of an institutional or coordinated retail-app order flow opening the day with a positioning trade, not a diffuse intraday accumulation.

Combined with §4's finding that broker 88 was a *persistent multi-week seller across* this same period, the intraday data sharpens the picture: the rally days were *opening-print absorption events* where buyers pushed price up in the first 60 minutes through the day's largest sell-leader (broker 88 / 35) supply. The peak day (Mar 22) shows opening-hour share dropping to 38.5% — by then the absorption was exhausted; selling spread across the session, not concentrated at the open.

**Methodological add-on candidate (not yet promoted to METHODOLOGY.md):** for any heavy-volume rally day, check `(opening_hour_volume / day_volume)`. >50% concentration in the first hour = "opening-print event" (institutional / app-flow positioning); <30% = "intraday accumulation" (more diffuse, more retail-shaped). Worth observing on the next case before formalising as a rule.

## Sector-context addendum (2026-05-21, per Rule 13)

Per `sector_correlation_test.py`: during the Mar 1 → Mar 22 2026 rally window, **UPPER was +28.7%, hydropower sub-index was +12.4%, correlation r=0.80, spread versus hydro +16.3%.**

**Important caveat on the math (Romeo Review #5):** the +16.3% is the *arithmetic spread* between UPPER's cumulative return and the hydro sub-index's cumulative return — NOT a true beta-adjusted residual. A proper residual requires fitting β and computing UPPER_ret − β × hydro_ret. The spread is suggestive of UPPER-specific outperformance over the window but should not be precisely interpreted as "the idiosyncratic portion" until residual-adjustment is computed.

**Directional implication (descriptive, not precise):** the headline +29% UPPER move occurred during a sector-wide hydro rally (+12% sector). UPPER outperformed the sector by ~16% (raw spread). The broker fingerprint analysis above (Naasa accumulated, Dynamic Money Managers persistently sold) describes the price action on UPPER itself; how much of that is sector beta vs UPPER-specific is *not precisely decomposable from this data*.

Reader-weight: this case's evidence weight should be moderate — the rally happened during a sector wave, so attributing all of the broker behavior to a UPPER-specific catalyst overstates the case. See SELF_VALIDATION_2026-05-21.md.

## Sources & references

- Local OHLCV: `sharesansar_datascrape/data/*.csv`.
- Broker flow: `market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table.csv` (rebuilt 2026-05-19, UPPER through 2026-05-18).
- Cross-source verification: ShareSansar Price History (https://www.sharesansar.com/company/upper) — numbers match exactly (Rule 4).
- Analyzer: `company_dossiers/UPPER/analyze_event.py 2026-03-10 UPPER` (and -03-19, -03-22).
- Focused chart: `company_dossiers/UPPER/charts/upper_case_2026-03-10.png`.
- Methodology: `company_dossiers/UPPER/METHODOLOGY.md` (Rules 1, 2, 4, 6, 7, 8 applied).
