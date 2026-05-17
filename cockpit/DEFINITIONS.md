# NEPSE Daily Cockpit — Definitions Contract (v0, FROZEN)

**Created**: 2026-05-17
**Status**: v0 — frozen contract. Thresholds here are pre-committed BEFORE any
report is generated, so they cannot later be tuned to make outputs "look good."
**Scope**: this file is a *contract*, not code. It defines what the cockpit may
compute, how, and the language it must use. Code is a later, separate step.

> This is decision-support, not an alpha machine. The three prior systematic
> probes (broker labels, broker IC, calendar) closed without a confirmable
> systematic edge. This tool exists to help Ishwor *read the market faster and
> more honestly* — never to decide for him.

---

## 1. Purpose

Help Ishwor see the entire NEPSE market in a few minutes each day, and build an
honest record of what was unusual — so discretionary decisions are made on a
fast, complete, consistent picture instead of memory and vibes.

The cockpit answers only: **"What happened today, and how unusual was it
relative to its own recent history?"** It never answers "what should I buy."

It *is* allowed to flag attention-worthy behavior (unusual volume/turnover,
sector pressure, broker concentration/imbalance, and descriptive
accumulation/distribution/panic *resemblance* tags) — as **watch items, not
trade calls**. It must be useful, not so timid it says nothing.

## 2. Non-goals (hard boundaries)

The cockpit must NEVER:

- Issue a buy, sell, hold, entry, exit, target, or stop.
- State or imply an expected return, fair value, "undervalued/overvalued."
- Claim or imply a systematic edge, backtested performance, or win-rate.
- Rank symbols by predicted profit or "opportunity."
- Use forward-looking verbs ("will", "should rise", "is likely to").
- Aggregate the Forward Diary or any label into an accuracy/P&L score used
  for sizing or conviction.

If any output starts answering "what should I buy?" instead of "what happened
and how unusual was it?" — that output is out of contract and must be removed.

## 3. Fixed v0 metrics and thresholds

All thresholds are chosen **by convention** (round, defensible, simple). They
are NOT optimized against any outcome. Lookback for every "vs its own history"
metric = **trailing 20 trading days**, median-based (robust to spikes).

### 3a. Market-level (breadth)
| Metric | Definition | Display rule |
|---|---|---|
| Advancers / Decliners / Unchanged | count of symbols Close >/</= Prev. Close | always shown |
| Breadth % | advancers ÷ traded symbols | always shown |
| % above own 20d avg | share of symbols with Close > own 20-day mean close | always shown |
| New 52w highs / lows | from `52 Weeks High` / `52 Weeks Low` columns touched today | always shown |
| Index level & day Δ% | NEPSE + covered sub-indices (live API; accrues forward) | always shown; mark history depth |

### 3b. Per-symbol anomaly flags (descriptive)
| Flag | Definition | Trigger (fixed) |
|---|---|---|
| Volume spike | RVOL = today Vol ÷ median(Vol, 20d) | RVOL ≥ **3.0** |
| Turnover shock | today Turnover ÷ median(Turnover, 20d) | ≥ **3.0** |
| Transaction shock | today `Trans.` ÷ median(`Trans.`, 20d) | ≥ **3.0** |
| Range expansion | today `Range %` ÷ median(`Range %`, 20d) | ≥ **2.0** |
| Close location | (Close − Low) ÷ (High − Low), 0–1 | reported, no threshold |
| Turnover concentration | top-10 symbols' share of total market turnover | reported, no threshold |

### 3c. Sector pressure (covered sectors only)
- Sub-index day Δ% for sectors with data (live NEPSE sub-index API; the partial
  `sector_map.json` covers Banking + Hydropower well — others are explicitly
  marked **"not covered"**, never silently omitted).

### 3d. Broker layer (only where floorsheet coverage exists)
| Metric | Definition |
|---|---|
| Buyer concentration | top-5 buyer brokers' share of buy quantity in the symbol that day |
| Seller concentration | top-5 seller brokers' share of sell quantity |
| Net broker imbalance | (largest single broker net buy qty) ÷ symbol volume |
| Persistence count | consecutive days a given broker is net buyer (or net seller) in the symbol |
| Coverage % | floorsheet quantity ÷ reported exchange volume for that symbol/day |

Concentration is flagged "high" at a fixed **top-5 ≥ 60%** of side quantity.
If Coverage % < **80%**, the symbol's broker block is tagged
**"low floorsheet coverage — interpret cautiously."**

### 3e. Behavioral resemblance tags (mechanical, watch-only)
Each tag is a fixed conjunction of 3a–3d metrics. Tags describe *resemblance to
a historical pattern shape*, never a prediction. Every tag is rendered with the
suffix **"— resemblance only; watch item, not a trade call."**

| Tag | Fixed definition |
|---|---|
| POSSIBLE ACCUMULATION | Close ≥ Prev.Close AND RVOL ≥ 3 AND close-location ≥ 0.66 AND (where data) buyer concentration high OR a broker net-buyer persistence ≥ 3 days |
| POSSIBLE DISTRIBUTION | Close ≤ Prev.Close AND RVOL ≥ 3 AND close-location ≤ 0.33 AND (where data) seller concentration high OR broker net-seller persistence ≥ 3 days |
| POSSIBLE PANIC | day Δ ≤ −8% (or at/again lower circuit) AND RVOL ≥ 3 AND close-location ≤ 0.25 AND market decliners ≥ 2× advancers |
| POSSIBLE FAILED MOVE | intraday High > prior 20-day high BUT Close < that prior high AND RVOL ≥ 2 |

Circuit reference: NEPSE band is ±10%, widened to ±15% effective 2026-04-17;
the −8% panic trigger is a fixed convention, not tuned, and is reviewed only on
a *structural* rule change (see §6).

## 4. Blind spots / coverage caveats (the report must self-disclose these)

Every report shows a coverage line. Known limits, stated honestly each day:

- **No intraday.** All metrics are end-of-day; "close location" approximates
  intraday behavior from OHLC only.
- **Floorsheet coverage is uneven.** Broker metrics appear only where coverage
  is sufficient; otherwise the block is omitted with a stated reason.
- **Sector map is partial.** Reliable sub-index labeling for Banking +
  Hydropower; other sectors marked "not covered."
- **Sub-index history is shallow forward-only** via the live API (~20 days at
  start; deepens daily). The frozen 1,249-row lab dataset is *reference history
  only* and is NOT pulled live (lab stays archived).
- **No corporate-action adjustment in raw OHLCV.** Ex-bonus/ex-rights days can
  show artificial gaps; flagged where a known book-closure date exists, else
  noted as a generic caveat.
- **Survivorship/lag.** Newly listed / suspended symbols may distort breadth;
  reported counts are "as scraped," not curated.

## 5. Report language rules

- Mandatory header on every report: *"Descriptive market observation. No
  buy/sell advice, no return prediction, no edge claim. Watch items are things
  to look at, not trade."*
- Allowed verbs/words: "was", "is", "resembles", "unusual vs its own 20-day
  history", "watch item", "observation", "coverage caveat", "POSSIBLE …".
- Banned words/phrases: buy, sell, hold, target, stop, entry, exit,
  undervalued, overvalued, cheap, expensive, opportunity, expected return,
  edge, signal, "will", "should", "set to", "poised to".
- Every behavioral tag carries the fixed suffix from §3e.
- Lists are ordered by a neutral key (e.g., symbol or RVOL magnitude), never by
  any implied profitability.
- The word "watchlist" is always rendered "watch list (observations, not buy
  candidates)".

## 6. Change-control rule (anti-overfitting, binding)

- Thresholds in §3 are **frozen**. They may be changed ONLY by appending a
  dated entry to a `CHANGELOG` section with an explicit **structural**
  justification — e.g., a NEPSE rule change (circuit band, lot size, trading
  hours), a data-schema change, or a definitional error.
- A threshold may **never** be changed because outputs "look better," to
  improve any hit-rate, to make a label fire more/less, or in response to how
  any symbol subsequently performed. That is outcome-driven tuning and is
  forbidden — it is the exact failure mode the prior probes were built to avoid.
- New metrics may be added only if they are descriptive and non-forward-looking
  (pass the §2 test). Adding a metric does not unfreeze existing ones.
- Removing an out-of-contract output (one that drifted toward "what to buy") is
  always allowed and encouraged.

## 7. First report shape (sections the daily cockpit will show)

1. **Header & disclaimer** (fixed text, §5) + date + data-coverage line
   (feeds present, floorsheet coverage %, sectors covered, index history depth).
2. **Market snapshot** — NEPSE & covered sub-index levels/Δ%, advancers/
   decliners/unchanged, breadth %, % above own 20d avg, new 52w highs/lows,
   top-10 turnover concentration.
3. **Unusual activity** — table of symbols tripping any §3b flag, with the raw
   metric values, ordered by RVOL; purely descriptive, no profit ranking.
4. **Sector pressure** — covered sectors' day Δ%; uncovered sectors listed
   explicitly as "not covered."
5. **Broker notes** — only symbols with sufficient floorsheet coverage: high
   concentration, net imbalance, persistence counts; each with coverage caveat.
6. **Resemblance tags** — symbols matching a §3e definition, each printed with
   the mandatory "resemblance only; watch item, not a trade call" suffix.
7. **Watch list (observations, not buy candidates)** — the de-duplicated union
   of flagged/tagged symbols, with *why it was flagged*, nothing more.
8. **Footer** — blind-spots reminder (§4) + fixed line: *"This report describes
   the past. It does not predict, recommend, or claim an edge."*

---

**End of v0 contract.** Nothing in §3 may be tuned from outcomes. Next step
(separate, on approval): implement the read-only report generator in
`own-market/cockpit/` against existing scrape outputs. The
`nepse-volume-psychology-lab` archive and the existing scrape pipeline are not
touched.

## CHANGELOG
- 2026-05-17 — v0 created and frozen (pre-implementation contract).
