# Scrape Expansion Decision — 2026-04-12

> Decision made by Ishwor + Juliet during the April 12 Saturday session.
> This documents the why, the what, and the constraints so future sessions have full context.

---

## What We Did

Expanded the daily Merolagani floorsheet scrape from **8 symbols** (3 active banks + 3 research hydro + 2 excluded dev banks) to **25 symbols** across **7 NEPSE sectors**. The 17 new symbols are **data collection only** — scraped and stored to disk with no signal scoring, no shadow report integration, no verdicts.

## Why We Did It

Three reasons, in order of importance:

1. **The audit found sample clustering.** The persistence shadow signal claims 88.9% (8/9) hit rate, but the audit on April 12 revealed that 7 of those 8 wins come from two consecutive days in August 2025 (with overlapping 10-day forward windows), plus 1 win from December 2025. The effective independent episodes are closer to 2-3, not 9. More symbols across more sectors improves **future optionality** — when we eventually expand the signal's scoring scope after the batch-score gate, months of broker flow data will already be on disk. This does not strengthen current evidence; it prepares for faster expansion later.

2. **Raw data collection doesn't violate patience mode.** The MANIFESTO says "the next 90 days are nothing new." The frozen policy says "do not expand scope until 10-15 sessions scored in batch." Scraping is neither expanding scope nor generating new signals. It's collecting raw material that sits on disk. When the batch-score fires and we decide to expand, months of broker flow data across 7 sectors will be ready without needing to backfill.

3. **Cross-sector testing becomes possible.** The persistence signal was developed on banks. We don't know if it works on insurance, microfinance, hydro, dev banks, or finance companies. With daily broker flow on all 7 sectors, we can test this immediately after the batch-score gate, instead of waiting months to accumulate sector data.

## What We Did NOT Do

- **Did not modify the shadow report.** `daily_persistence_shadow_report.py` still only processes NABIL/EBL/SANIMA (active) + AKPL/UPPER/API (research) + JBBL/MNBBL (excluded). Untouched.
- **Did not modify the scorer.** `score_persistence_shadow_reports.py` is unchanged.
- **Did not modify the frozen policy.** `PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md` is unchanged.
- **Did not add any new signals or verdicts.** The 17 new symbols produce raw floorsheet + broker flow ledger files only.

## The 25 Symbols

| Sector | Symbols | Count | Tier |
|---|---|---|---|
| Commercial Banks | NABIL, EBL, SANIMA | 3 | active_shadow |
| Commercial Banks | NBB, NICA, PCBL | 3 | data_collection_only |
| Hydropower | AKPL, UPPER, API | 3 | research |
| Hydropower | BHCL, RADHI, AHPC | 3 | data_collection_only |
| Development Banks | JBBL, MNBBL | 2 | shadow_excluded |
| Development Banks | SAPDBL, EDBL | 2 | data_collection_only |
| Life Insurance | CLI, NLIC, HLI | 3 | data_collection_only |
| Non-Life Insurance | LGIL, NIL | 2 | data_collection_only |
| Microfinance | RMDC, CBBL | 2 | data_collection_only |
| Finance | MFIL, NFS | 2 | data_collection_only |

### How symbols were selected

- **Liquidity-first:** Ranked all NEPSE symbols by average turnover over the last 5 trading days in our CSV archive (Dec 2025 snapshot). Picked the top symbols per sector.
- **Sector coverage:** Chose 7 sectors that have enough daily turnover for meaningful floorsheet data. Excluded Manufacturing (near-zero turnover), Hotels (only 1 active stock), Trading (3 companies total), Mutual Funds (NAV-driven, not broker-flow), Investment/Others (mostly illiquid).
- **Minimum 2 per sector:** Every sector has at least 2 symbols so intra-sector comparison is possible.

### Why these sectors and not others

| Excluded Sector | Reason |
|---|---|
| Manufacturing | Near-zero daily turnover. Floorsheet will be empty. |
| Hotels & Tourism | Only BANDIPUR trades (likely IPO/hype spike). Unreliable. |
| Trading | 3 total companies. Too thin for any analysis. |
| Mutual Fund | NAV-driven pricing. Broker flow doesn't apply the same way. |
| Investment | Mixed bag, mostly illiquid. |

## Files Created

| File | Purpose |
|---|---|
| `scrape_symbol_list.json` | Config: 25 symbols with sector + tier classification. Single source of truth for what gets scraped. |
| `run_daily_scrape.py` | Orchestrator: reads config, skips existing data, calls `backfill_merolagani_floorsheet.py` once with all pending symbols. |
| `SCRAPE_EXPANSION_2026-04-12.md` | This document. |

## Files NOT Modified

| File | Status |
|---|---|
| `run_persistence_shadow_daily.py` | Untouched. Its ACTIVE_SYMBOLS and RESEARCH_SYMBOLS are hardcoded and unchanged. |
| `daily_persistence_shadow_report.py` | Untouched. |
| `score_persistence_shadow_reports.py` | Untouched. |
| `PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md` | Untouched. |
| `backfill_merolagani_floorsheet.py` | Untouched (the orchestrator calls it as-is). |

## Daily Routine (new, from April 13 onward)

```bash
# Step 1: Scrape all 25 symbols (~5 min)
python run_daily_scrape.py --date <DATE>

# Step 2: Shadow report for active banks only (~1 min, unchanged)
python run_persistence_shadow_daily.py --date <DATE>
```

The scraper automatically skips symbols that already have data for the date. Running it twice is safe.

## Performance

| Metric | Observed on Apr 9-10 |
|---|---|
| Full 25-symbol scrape time | ~5-6 minutes |
| Symbols per minute | ~4-5 |
| Rate limiting | Not needed — Merolagani's page navigation provides natural pacing |
| Browser sessions | 1 (reused across all symbols per run) |

## Calendar Fix (same session)

Also in this session: fixed the NEPSE trading calendar across 9 files. Nepal switched from Sunday-Thursday to Monday-Friday on April 10, 2026. Created `nepse_trading_calendar.py` as the single source of truth. All 9 files that hardcoded `TRADING_WEEKDAYS = {6,0,1,2,3}` now use the transition-aware helper. See the module docstring for details.

## Audit Results (same session)

Ran Benvolio's 6-class persistence signal audit checklist against the real code. Key findings:

- **F.1 (pre-registration):** PARTIAL PASS — frozen policy doc exists, dated Apr 5, names w7/seller. But never committed to git.
- **F.2 (search space):** FAIL — not documented what other parameter combos were tested.
- **A.1-A.3 (calendar/dedupe/regime):** PASS — code is correct.
- **A.4 + D (sample geometry):** FAIL — 7 of 8 winning cases from 2 consecutive Aug 2025 days (overlapping forward windows), plus 1 from Dec 2025. Effective independent episodes are closer to 2-3, not 9 (Romeo-verified). The current evidence is clustered and preliminary.
- **C (baseline):** FLAG — raw returns only, baseline comparison has only 3 resolved no_signal cases.
- **B (frozen policy drift):** UNVERIFIABLE — no git history.

**Conclusion:** The code is clean. The sample is not. The 23 pending cases (Mar 31 → Apr 10, 2026) are the real test. Keep running the daily routine.

## What Happens Next

1. **Monday Apr 13:** First full daily routine with expanded scrape (25 symbols) + shadow report (3 active banks).
2. **~10 more trading days:** Pending persistence cases resolve as forward price data accumulates.
3. **At 25+ resolved cases:** Batch-score decision. The audit findings and the expanded sector data will both be available at that point.
4. **If signal passes:** Consider expanding persistence scoring to new sectors using the data we're now collecting.
5. **If signal fails:** Diagnose using the audit findings before changing anything.

## Romeo's Review (2026-04-12)

Romeo reviewed the full April 12 session. Verdict: **mostly agree.** Four precision corrections applied:

1. **"2-3 independent episodes" not "2"** — Dec 7 is a genuine third independent period. Applied above.
2. **Scrape expansion = future optionality, not current evidence** — the 17 new symbols don't strengthen the persistence claim yet. Framing corrected above.
3. **April 10 confirmed as canonical transition date** — April 6 is the policy announcement; April 10 is the first day where weekday membership actually differs. Code is correct.
4. **Citation corrections should use softer language** — don't replace "52-57% from papers" with another precise number ("50.5-51.5%"). Say: "papers report modest return spreads; the lab's implied directional accuracy estimate is ~50-52%, but this is our inference, not a published benchmark."

Romeo also confirmed:
- The scorer code is correct (trading-day arithmetic, per-row dedupe)
- The scrape expansion is consistent with patience mode (infrastructure, not experimentation)
- Benvolio's 6/8 citation corrections are strong-agree
- Transcript extraction framework is well designed; keep parked until real pilot

---

*Written 2026-04-12 by Juliet, documenting decisions from the Saturday brainstorming session with Ishwor.*
*Romeo review appended same day.*
