# Experiment Contract: batch-score-playbook

## Purpose

Provide a runnable, single-command decision tool for the persistence shadow batch-score gate at N≥25 resolved cases. Produces a PROMOTE / HOLD / KILL verdict with structured reasoning the user can act on even without Claude available. This is defensive infrastructure, not a new signal.

---

## Inputs (read-only paths)

- `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_cases_v1.csv` (resolved + pending cases)
- `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.json` (current scorecard)
- `market-gist/agents/shared/PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md` (frozen policy, for integrity check)
- `market-gist/automation/score_persistence_shadow_reports.py` (scorer code, for drift check via git log)
- `experiments/signal-decay-tracker/results/latest.json` (decay tracker baseline, if present)

Reads nothing outside Layers 1 and 2.

---

## Outputs (paths this experiment writes to)

- `experiments/batch-score-playbook/results/decision_<YYYY-MM-DD>.json` (structured)
- `experiments/batch-score-playbook/results/decision_<YYYY-MM-DD>.md` (human-readable memo)
- `experiments/batch-score-playbook/results/latest.json` + `latest.md` (convenience)

All outputs inside this folder. Nothing else.

---

## Never Touches

- `market-gist/**` (production + shared, all read-only)
- `experiments/LEARNINGS.md`
- `experiments/BACKLOG.md`
- `experiments/INDEX.md`
- `experiments/MANIFESTO.md`
- `market-gist/agents/shared/PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md` (read-only check only)
- Any other experiment's folder

---

## Kill Condition

Delete `experiments/batch-score-playbook/`. Nothing else breaks.

**What depends on this:** nothing. Tool is read-only; produces decision memos the user reads but no other code imports its output.

---

## Runnable As

```
python experiments/batch-score-playbook/run_batch_score.py
```

Optional flags:
- `--dry-run` — print memo to stdout, do not write files
- `--force` — run the verdict logic even if N < 25 (for testing)

NOT invoked by the production daily routine. Run manually when:
- Resolved case count approaches 25
- You need to re-check the verdict after new cases resolve
- Romeo wants to verify the decision logic

---

## Forward Evidence Gate

This tool operates on already-collected persistence shadow cases. It does not itself have forward evidence requirements. It reads from persistence's forward evidence.

**Gate it enforces:** the tool refuses to produce a PROMOTE verdict until N ≥ 25 resolved `persistence_caution_only` cases exist. Below that, verdict is BELOW_GATE regardless of hit rate.

---

## Naming

Output verdicts use one of: `PROMOTE`, `HOLD`, `KILL`, `BELOW_GATE`. No other verdicts.

Decision memo filenames prefixed with `decision_` — clearly distinguishable from signal-decay `decay_` files and from experimental signal outputs.

---

## Output File Header

Every output markdown/JSON begins with:

```
[EXPERIMENTAL TOOL — decision support for batch-score gate]
Tool: batch-score-playbook
Persistence resolved N: <current> / gate=25
Layer: 3 (research — infrastructure, not a signal)
```

---

## Romeo / Benvolio Verification Status

- **Designed by:** Juliet, 2026-04-17
- **Methodology sources:**
  - Benvolio's 6-class audit checklist (`market-expirement-labs/04_persistence_lookahead_audit.md`)
  - L-012 clustering findings (sample concentration)
  - L-013 benchmark ceiling wording
  - Signal decay tracker's analysis patterns
- **Reviewed by Romeo:** pending — please verify the verdict-threshold logic before first real use.
- **Reviewed by Benvolio:** pending (non-blocking).
- **Promotion path status:** infrastructure tool, not a signal. No forward-evidence promotion path required. Just needs Romeo sign-off on verdict thresholds.
