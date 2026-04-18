# Experiment Contract: <EXPERIMENT-NAME>

> Copy this file to `experiments/XX-your-name/CONTRACT.md` when starting a new experiment.
> Fill in every field. If a field is empty, the experiment is not runnable.
> See `SANDBOX_PROTOCOL.md` for the rules this contract enforces.

---

## Purpose

One sentence stating the exact question this experiment answers.

Example: "Does NEPSE broker persistence decay materially within 4 weeks of a stable-verdict streak?"

---

## Inputs (read-only paths)

List every data source this experiment reads. Use exact paths or globs.

- `market-gist/broker_flow_ledger/<SYMBOL>/<DATE>.json`
- `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.json`
- `sharesansar_datascrape/data/<MM_DD_YYYY>.csv`

Never list paths outside Layers 1 and 2 as inputs.

---

## Outputs (paths this experiment writes to)

Every path must be inside this experiment's own folder.

- `experiments/XX-your-name/results/<date>.json`
- `experiments/XX-your-name/alerts/<date>.md` (optional)
- `experiments/XX-your-name/logs/run_<date>.log`

Never write to `market-gist/**` or any other experiment's folder.

---

## Never Touches

- `market-gist/**` (production + shared, all read-only)
- `experiments/LEARNINGS.md`
- `experiments/BACKLOG.md`
- `experiments/INDEX.md`
- `experiments/MANIFESTO.md`
- Any other experiment's folder (`experiments/XX-other/**`)

---

## Kill Condition

Delete this folder (`rm -rf experiments/XX-your-name`). Nothing else breaks.

Confirm by naming what depends on this experiment's outputs (should be nothing):

- **What depends on this:** nothing / [list if you somehow created a dependency]

---

## Runnable As

```
python experiments/XX-your-name/run.py [--flags]
```

Example invocations:

```
python experiments/XX-signal-decay/run.py                    # default: current week
python experiments/XX-signal-decay/run.py --week 2026-W16    # specific week
python experiments/XX-signal-decay/run.py --full-history     # rebuild from scratch
```

NOT invoked by the production daily routine. Optionally invoked by `experiments/run_experiments_daily.py` if present.

---

## Forward Evidence Gate

What N does this experiment need before it earns the right to be considered for promotion?

Example: "N ≥ 25 resolved cases (same as persistence signal), plus a 4-week rolling stability check."

Current state: N = 0.

---

## Naming

All signal outputs from this experiment must use the prefix `x-<slug>-` so they are distinguishable from production signals at a glance.

Slug: `your-name` (lowercase, hyphens).

Example output signal names:
- `x-your-name-NABIL-alert`
- `x-your-name-EBL-weak`

---

## Output File Header

Every markdown/JSON/CSV output file must begin with this block:

```
⚠️ EXPERIMENTAL SIGNAL — shadow only, not a trading decision.
Experiment: your-name
Forward evidence: N=<current> / required=<gate>
Layer: 3 (research)
```

---

## Romeo / Benvolio Verification Status

- **Designed by:** [name]
- **Reviewed by Romeo:** [date / pending]
- **Reviewed by Benvolio:** [date / pending]
- **Promotion path status:** [pre-evidence / evidence-gathering / audit-pending / canon-ready / promoted]
