# L-001 Versioning Plan

**Written:** 2026-04-19
**Status:** Plan only. No scraping. No building. No reinterpretation of prior results.

---

## The Problem This Solves

L-001 (corporate-action event table) was built for the original **14-symbol seed event universe**, not the full 26-symbol scrape universe. If the lab expands to 93 symbols without expanding event coverage, event-contamination filters become asymmetric: symbols with known events get filtered; symbols without known events look falsely clean. That asymmetry would silently poison reversal-specialist, broker-flow, and any future experiment that relies on "idiosyncratic" event classification.

As of 2026-04-19:
- `universe_v2_candidate.csv` has 93 selected symbols.
- The current L-001 event table covers 14 symbols total.
- Only 11 of the 93 selected v2 symbols overlap current L-001 coverage.
- Therefore 82 selected v2 symbols currently lack L-001 event coverage.

The fix is versioning, not rewriting.

---

## Rule 1 — L-001 Original Is Frozen

The existing L-001 event table is historical evidence for the 14-symbol seed event experiment. It does not change. No rows added. No rows removed. Any finding already published against L-001 remains valid as-is, with its original scope.

## Rule 2 — L-001-v2 Is Infrastructure, Not a Rewrite

L-001-v2 is a separate corporate-action event table covering the 93-symbol `universe_v2` scope. It does not retroactively change L-001 conclusions. It is new infrastructure that future experiments must opt into explicitly.

## Rule 3 — Scope Equals Universe v2

L-001-v2 covers every symbol in `universe_v2_candidate.csv` where `selected_v2_candidate=True`. Scope is locked to that list. If universe_v2 is amended before Romeo freezes it, L-001-v2 scope updates with it. After freeze, both are stable together.

## Rule 4 — Outputs Are Versioned Separately

| Artifact | Path |
|---|---|
| Original | `experiments/01-corporate-action/data/events.csv` |
| v2 preferred folder | `experiments/01-corporate-action-v2/` |
| v2 event table | `experiments/01-corporate-action-v2/data/events.csv` |
| v2 coverage report | `experiments/01-corporate-action-v2/data/coverage_report.md` |

The coverage report is mandatory before any experiment may use L-001-v2. It must state: symbols attempted, symbols with ≥1 event found, symbols with zero events (data gap vs. genuinely no events), and date range covered.

## Rule 5 — Experiments Must Declare Which Version They Use

Every future experiment pre-registration must include one of:

- `event_coverage: L-001-original` — uses the 14-symbol seed event table; universe must stay within that event-coverage scope
- `event_coverage: L-001-v2` — uses 93-symbol event table; coverage report must be attached
- `event_coverage: none` — signal does not use event-contamination filtering; must justify why contamination risk is acceptable

Silence is not allowed. An experiment that silently inherits old event coverage with a larger universe is a pre-registration defect.

## Rule 6 — No Silent Reinterpretation

L-001 original results (dividend microstructure, reversal-specialist event filters) are not rerun against L-001-v2 data unless a new pre-registration is written. Rerunning with expanded event coverage is a new experiment, not a correction to an old one.

## Rule 7 — v2 Build Must Produce Coverage Report First

Before any experiment uses L-001-v2, the build script must output the coverage report (Rule 4). If coverage is materially incomplete (e.g., >20% of symbols have zero events despite active trading), the data gap must be documented and the experiment's contamination-filter logic must account for it explicitly.

---

## What Happens Next (Sequencing)

This plan does not authorize scraping. The sequencing is:

1. Romeo freezes `universe_v2_candidate.csv` → becomes `universe_v2.csv`
2. Broker-flow scraper wiring updated to cover 93 symbols (Romeo gate)
3. L-001-v2 corporate-action scrape/build runs in a separate versioned folder
4. Preferred: rebuild corporate-action coverage for all 93 v2 symbols in one clean v2 table
5. Minimum acceptable fallback: scrape/build the 82 selected v2 symbols that currently lack L-001 coverage, then merge only inside the v2 folder
6. Coverage report generated
7. First expanded-universe experiment may then declare `event_coverage: L-001-v2`

Nothing in steps 2–7 happens until step 1 is signed off.

---

## Why This Matters For Reversal Specialist (If Reopened)

If reversal-specialist is ever reopened with the 93-symbol universe (new pre-registration required), it must use L-001-v2 to filter corporate-action overlaps. Running it with L-001-original over 93 symbols would leave 82 selected v2 symbols outside current event coverage — the "clean" label on those triggers would be meaningless.

This is the same asymmetry that caused L-015-class silent corruption. Known by name. Prevented by rule, not by memory.
