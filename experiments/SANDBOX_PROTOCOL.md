# Sandbox Protocol — Rules For Parallel Experimentation

> Written 2026-04-13 to formalize how the lab runs Layer 3 experiments without corrupting Layer 1 production.
> Applies to every new signal, every new agent team, every new pilot after this document.
> Read this before opening a new experiment folder.

---

## Core Principle

**Experiments are physically isolated by construction.** Production and Shared layers are protected not by discipline but by contract. Layer 3 folders can be deleted without consequence; they can be modified freely inside their own boundaries.

If an experiment wants to change something outside its folder, it must go through the serial-promotion path in `PARALLEL_EXPLORATION_SERIAL_PROMOTION.md` — not bypass it.

---

## The Three Layers

### Layer 1: Production (untouchable)

Code and data that the live persistence signal depends on.

```
market-gist/agents/shared/PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md
market-gist/automation/daily_persistence_shadow_report.py
market-gist/automation/score_persistence_shadow_reports.py
market-gist/automation/run_persistence_shadow_daily.py
market-gist/data/validation/persistence_shadow_reports/
market-gist/data/validation/persistence_shadow_reviews/
```

Rules:
- Frozen. Not modified except at promotion gates after forward evidence.
- No experimental signal, tracker, or agent is permitted to write here.
- Structural fixes (e.g. calendar helper, dedupe utility) require Romeo verification before landing.

### Layer 2: Shared (read-only from Layer 3)

Data and utilities that experiments need but must not modify.

```
market-gist/broker_flow_ledger/
market-gist/broker_flow_ledger/raw_merolagani/
sharesansar_datascrape/data/
experiments/shared/
market-gist/automation/nepse_trading_calendar.py
market-gist/automation/scrape_symbol_list.json
```

Rules:
- Layer 3 code may read these paths.
- Layer 3 code must NEVER modify them.
- Shared utilities are imported, not copied; if a utility is broken, it gets fixed via Layer 1 rules, not by forking inside an experiment.

### Layer 3: Research (free zone, sandboxed)

Where all experiments, pilots, and exploration live.

```
experiments/hydro-intelligence/           (existing pilot)
experiments/01-corporate-action/ through /06-hydro-flood-damage/   (numbered experiments)
experiments/XX-signal-decay/              (future)
experiments/XX-dividend-microstructure/   (future)
market-expirement-labs/                   (Benvolio's environment)
```

Rules:
- Free modification, deletion, and iteration inside each experiment's own folder.
- Each folder has its own `CONTRACT.md` stating inputs, outputs, kill condition.
- No experiment imports from another experiment. All cross-experiment sharing goes through Layer 2 (promote utility to `experiments/shared/`).
- Writes outside own folder = contract violation.

---

## The Experiment Contract

Every new experiment folder must contain a `CONTRACT.md` with exactly these fields.

```markdown
# Experiment Contract: <experiment-name>

## Purpose
One sentence: what question this experiment answers.

## Inputs (read-only paths)
- Exact paths or globs of what this experiment reads.

## Outputs (only paths this experiment writes to)
- experiments/XX-name/results/
- experiments/XX-name/shadow_reports/
- experiments/XX-name/alerts/ (optional)

## Never Touches
- market-gist/** (production and shared data are read-only)
- experiments/LEARNINGS.md, BACKLOG.md, INDEX.md, MANIFESTO.md (canonical files)
- Any other experiment's folder

## Kill Condition
Delete this folder. Nothing else breaks.

## Runnable As
python experiments/XX-name/run.py [flags]
or: on-demand, not in any production cron.

## Forward Evidence Gate
The N at which this experiment earns the right to be considered for promotion.
```

If the contract is missing or vague, the experiment is not runnable.

---

## Naming Convention

Experimental signals must be distinguishable from production signals at a glance.

- **Production signal verdicts:** `NABIL CAUTION`, `EBL NO_SIGNAL` (current pattern, unchanged)
- **Experimental signal verdicts:** prefix `x-<experiment-slug>-`
  - Example: `x-decay-NABIL-alert` (signal decay tracker flagging NABIL)
  - Example: `x-dividend-micro-EBL-signal` (dividend microstructure for EBL)

Folder names:
- **Numbered experiments (01-xx):** one-shot research questions. Match the `INDEX.md` table.
- **Named experiments (hydro-intelligence, etc.):** living systems that update continuously.

---

## Run Isolation

Experiments do NOT run inside the daily production routine (`run_persistence_shadow_daily.py`). Reasons:

1. A crash in an experiment cannot delay or corrupt the daily production output.
2. Production runs on market close; experiments may run at any cadence.
3. Mental isolation: the daily routine's output stays pure.

Pattern:
- **Production runner:** `market-gist/automation/run_persistence_shadow_daily.py`. Unchanged.
- **Experiment runner:** `experiments/run_experiments_daily.py` (future). Iterates known experiment folders, calls each one's `run.py` with isolation, collects outputs.
- **On-demand experiments:** invoked manually via `python experiments/XX-name/run.py`.

Weekly batch-review of experimental outputs, not daily. This keeps the attention budget aligned with the maturity of each layer.

---

## Output Labeling

Every experimental output file (markdown, JSON, CSV) must begin with:

```
⚠️ EXPERIMENTAL SIGNAL — shadow only, not a trading decision.
Experiment: <slug>
Forward evidence: N=<current> / required=<gate>
Layer: 3 (research)
```

This prevents future-you from confusing experimental verdicts with production verdicts months from now.

---

## Cross-Experiment Sharing

Experiments do NOT import from other experiments. Period.

If two experiments need the same helper function:
1. First experiment proves the helper works on its own data
2. Helper is promoted to `experiments/shared/` via Romeo verification
3. Both experiments import from `shared/`

This prevents invisible coupling where experiment A breaks experiment B.

---

## Promotion Path (From Layer 3 to Layer 1)

An experiment earns production status only by passing every step:

1. **Own forward evidence.** The experiment has accumulated enough post-launch cases to establish a real hit rate (typically N≥25, the same gate as persistence).
2. **Own audit.** The experiment has been run against a 6-class lookahead/clustering/baseline/leakage audit, not just a headline hit rate.
3. **Romeo verification.** Outside review checks for overclaims, citation errors, wording drift.
4. **Canonical integration.** LEARNINGS.md gets a new L-entry; BACKLOG.md and INDEX.md get updated.
5. **Clean gate landing.** Production code changes land at a clean point, not mid-session.
6. **Retain experiment folder.** The historical record stays in Layer 3 even after promotion, so future work can trace the path.

Steps cannot be skipped, even if a signal looks spectacular. Especially if it looks spectacular.

---

## What This Protocol Prevents

| Risk | Mitigation |
|---|---|
| Experiment corrupts production code | Contract forbids writes to Layer 1 paths |
| Experiment corrupts shared data | Layer 2 is read-only |
| Experiment output confused with production | Naming prefix + explicit "EXPERIMENTAL" label |
| Experiment survives past usefulness | Kill condition documented |
| Experiment couples invisibly to another | No cross-experiment imports |
| Excitement promotes unvalidated signal | Explicit 6-step promotion gate |
| Daily routine destabilized | Separate runners, separate cadence |
| Context rot over time | CONTRACT.md and README.md per folder |

---

## The One Rule That Survives Everything Else

**If in doubt, the experiment is in Layer 3. Never anywhere else.**

This document exists so future-you, future-Claude, and future-team members do not accidentally merge experimental work into the production lane. The doctrine says `search wide, promote narrow`. This protocol operationalizes that sentence.
