# Broker-Flow Backfill — Authorization Request

**Written:** 2026-04-19
**Patched:** 2026-04-19 after Romeo w7-audit verdict — source is now explicitly the existing `backfill_merolagani_floorsheet.py`; no new scraper code; no force-overwrite of existing broker-flow files
**Status:** Pending Romeo sign-off. No code written until authorization granted.
**Scope owner:** Juliet
**Parent pre-registration:** `PRE_REGISTRATION.md` r4 (w7 seller-persistence replay)

---

## Purpose

Fill missing broker-flow data for three symbols over a fixed historical window, so the pre-registered replay can later run Step 2's all-or-nothing coverage gate (≥80% per symbol). This is data-collection only. It does not run the replay, compute any signal, or produce any hit rate.

---

## Locked Scope

| Parameter | Value |
|---|---|
| Symbols | NABIL, EBL, SANIMA (no others) |
| Window | 2025-10-19 to 2026-04-18 |
| Coverage target | ≥80% of trading days in window, per symbol |
| Source (primary) | existing `market-gist/automation/backfill_merolagani_floorsheet.py` — use this script, do NOT write new scraper code |
| Source fallback | not authorized under this request; any fallback requires a new authorization written and reviewed |
| Output format | raw broker-flow JSON / ledger files matching current live-scrape schema |
| Output location | same storage layout as current broker-flow data (to be confirmed in Step 1 below) |

Any deviation from this scope requires a new authorization request, not an amendment.

---

## Required Pre-Scrape Steps

**Step 1 — Schema-match verification**
- Run the existing `market-gist/automation/backfill_merolagani_floorsheet.py` for a single representative date in the window
- Compare every column and field in the resulting output against the current live-scrape schema
- Confirm broker-code presence, format, and pagination behavior
- Produce a one-page schema-match memo before any multi-date scrape begins
- If schema diverges materially, stop and escalate to Romeo. A new authorization is required before writing any scraper code or trying a fallback source.

**Step 2 — Rate-limit discipline**
- Throttle requests conservatively (sequential, bounded delay between dates)
- No parallel hammering of the source
- Abort and report if the source returns rate-limit, block, or sustained error responses

**Step 3 — Full backfill scrape**
- Proceed only if Step 1 schema-match passes
- Use ONLY `market-gist/automation/backfill_merolagani_floorsheet.py`. No new scraper code permitted under this authorization.
- Scrape every trading day in the window that is currently missing for each of the three symbols
- **Do NOT overwrite** any existing broker-flow file. If a file exists for a date+symbol, skip it; reasons for force-overwrite (if ever needed) require a separate justification memo
- Store raw output only *(proposed output files; storage location matches current broker-flow layout, confirmed in Step 1)*; no computation on the data

**Step 4 — Coverage report (required first deliverable)**
- Produce `experiments/persistence-recent-replay/data/backfill_coverage_report.md` *(proposed output)*
- Per-symbol: total trading days, days with broker-flow data, coverage %, pass/fail 80% gate
- Per-symbol: list of dates still missing after backfill, reason categorized where possible (source gap, holiday, scraper failure)
- Aggregate verdict: all three pass / one or more fail

---

## Explicitly Out of Scope

- Does NOT modify `scrape_symbol_list.json`
- Does NOT alter the daily scrape pipeline
- Does NOT touch production shadow reports, the forward-shadow scorecard, or the `persistence_shadow_reports/` directory
- Does NOT compute the w7 seller-persistence signal
- Does NOT compute forward returns
- Does NOT produce any hit rate or recommendation
- Does NOT run the replay (that is gated on the r4 pre-reg flow and the coverage gate passing)
- Does NOT expand to universe v2 symbols
- Does NOT backfill any symbol beyond NABIL, EBL, SANIMA
- Does NOT write any new scraper code — uses ONLY `market-gist/automation/backfill_merolagani_floorsheet.py`
- Does NOT force-overwrite existing broker-flow files. Any overwrite requires a separate justification memo before execution
- Does NOT use a fallback source without a new authorization

---

## Abort Conditions

Backfill aborts with coverage report only — no workaround attempts — if any of:

- Merolagani schema diverges materially from the live-scrape format
- Merolagani rate-limits or blocks the scraper
- After full scrape attempt, any symbol remains below 80% coverage (reported honestly, not rescued by fallback source without re-authorization)
- Unexpected data corruption or malformed responses for >5% of requested dates

In any abort case, the coverage report is produced and the replay's Step 2 gate consumes it as-is. No cherry-picking. No scope relaxation.

---

## Ask

Romeo approval for:
1. Running `market-gist/automation/backfill_merolagani_floorsheet.py` within the locked scope above
2. Running the schema-match verification step
3. If schema-match passes, running the full backfill scrape (skip-on-exist, no overwrite)
4. Producing the two deliverables below

Per Romeo's w7-audit verdict, if these wording/reporting patches match Romeo's instructions exactly, no new Romeo round is needed before schema-match/backfill proceeds.

All subsequent steps (replay code verification per r4 Step 3, replay run, results) remain gated on the pre-registration r4 flow and are not included in this authorization.

---

## What Romeo Signs Off On

- Scope: exactly as locked above
- Use of `market-gist/automation/backfill_merolagani_floorsheet.py` only
- Evidence label for any future artifact from this work: `w7_replay_backfill_2025-10_2026-04`
- No signal work, no promotion language, no subset rescue, no force-overwrite, no fallback source
- Only two outputs produced under this authorization: schema-match memo and coverage report. Both feed r4 Step 2 and nothing else.

---

## What Happens Next On Approval

- Schema-match memo within one work session
- If memo passes: full backfill scrape via `backfill_merolagani_floorsheet.py` (courtesy-throttled; may span multiple sessions depending on source response; skip-on-exist)
- Coverage report delivered to Romeo
- Replay proceeds only if all three symbols cross 80% and r4 Step 3 (code verification) completes under its own gate

On rejection: the replay track is closed at this gate. The pre-registration r4 is preserved as documentation of the attempt; no silent retry without a new authorization.
