# Experiment Contract: reversal-specialist

## Purpose

Test whether NEPSE stocks that experience a single-day price move beyond a threshold exhibit statistically measurable mean-reversion over the next 5 trading days. This is a price-only signal with no dependence on corporate actions, broker flow, or any other lab signal.

---

## Inputs (read-only paths)

- `sharesansar_datascrape/data/<MM_DD_YYYY>.csv` (price CSVs)
- `market-gist/automation/nepse_trading_calendar.py` (regime-aware trading-day helper)
- `market-gist/automation/price_data_integrity.py` (pre-run integrity check)
- `market-gist/automation/score_persistence_shadow_reports.py::load_symbol_prices` (reuse the same price-loading + dedupe path for consistency with L-007)
- `market-gist/automation/scrape_symbol_list.json` (symbol universe)
- `experiments/01-corporate-action/data/events.csv` (L-001 event table — read-only, used for corporate-action ex-date overlap filter in revision 2)

**Cross-experiment dependency disclosure (per SANDBOX_PROTOCOL):** reversal-specialist reads L-001's `events.csv` output. This is a cross-experiment dependency between two Layer 3 sandboxes, which the protocol generally discourages. Accepted here because (a) L-001 is a stable, validated data product, (b) the alternative (copying events.csv into reversal-specialist) creates stale-data divergence, (c) reversal-specialist's dependence is read-only. If L-001 is ever deleted or its schema changes, reversal-specialist fails gracefully (the overlap filter becomes a no-op, flagged in console output) rather than silently producing wrong results.

Reads nothing outside Layers 1, 2, and the L-001 output file above.

---

## Outputs (paths this experiment writes to)

- `experiments/reversal-specialist/data/trigger_events.csv` — one row per detected sharp-move event
- `experiments/reversal-specialist/data/gate1_decision.json` + `.md` — sample-adequacy decision
- `experiments/reversal-specialist/results/H1_<date>.json` + `.md` — primary test (only if Gate 1 passes)
- `experiments/reversal-specialist/results/diagnostic_<date>.json` — secondary windows, sensitivity (only after primary)

All outputs inside this experiment's folder. Nothing else.

---

## Never Touches

- `market-gist/**` (production + shared, all read-only)
- `experiments/LEARNINGS.md`, `BACKLOG.md`, `INDEX.md`, `MANIFESTO.md`
- Any other experiment's folder

---

## Kill Condition

Delete `experiments/reversal-specialist/`. Nothing else breaks.

**What depends on this:** nothing. Results may eventually inform LEARNINGS.md via serial promotion.

---

## Runnable As

Planned runner commands:

```
python experiments/reversal-specialist/build_trigger_events.py   # Step 1
python experiments/reversal-specialist/check_gate1.py            # Gate 1 decision
python experiments/reversal-specialist/run_h1.py                 # Step 3 (after Gate 1 pass)
```

NOT invoked by the production daily routine. Manual invocation only.

---

## Forward Evidence Gate

**Gate 1 (sample adequacy, pre-H1):** see `PRE_REGISTRATION.md` for thresholds. Must confirm:
- Per-direction N ≥ 80 events
- Unique trigger calendar dates ≥ 30
- Top-3 trigger date concentration ≤ 30%
- At least 5 symbols contributing events

**Gate 2 (H1 historical pass):** see `PRE_REGISTRATION.md`. Requires economic magnitude + hit rate + block-bootstrap CI excluding zero.

**Gate 3 (forward evidence for promotion):** post-pre-registration trigger events with completed [T+1, T+5] windows, N ≥ 25, passing primary criteria.

**Gate 4 (audit + Romeo):** 6-class audit before any canon integration.

---

## Naming

All signal outputs from this experiment use the prefix `x-reversal-`:
- `x-reversal-NABIL-down-trigger`
- `x-reversal-UPPER-up-trigger`

---

## Output File Header

Every output markdown/JSON/CSV file begins with:

```
[EXPERIMENTAL SIGNAL] shadow only, not a trading decision.
Experiment: reversal-specialist
Historical-test sample: N=<current> / minimum=80 per direction for Gate 1
Forward evidence (post-pre-registration): N=<current> / required=25 for promotion
Layer: 3 (research)
```

---

## Romeo / Benvolio Verification Status

- **Designed by:** Juliet, 2026-04-18
- **Methodology:** textbook mean-reversion / variance-ratio family. Academic anchors in `PRE_REGISTRATION.md`.
- **Reviewed by Romeo:** pending — please confirm thresholds + scope before Gate 1 code runs.
- **Reviewed by Benvolio:** pending (non-blocking).
- **Promotion path status:** pre-code, pre-evidence. Awaiting Romeo sign-off on pre-registration.
