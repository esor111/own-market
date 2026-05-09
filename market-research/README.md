# Market Research Folder

Persistent home for free-range, web-sourced research on Nepal's market context, NEPSE-specific developments, named individuals, sectors, and trade ideas.

This folder is **separate from the experiments lab.** Lab work follows pre-registration discipline. Research here does not — it is opinion, web-sourced context, and trade-idea capture. Lab work consumes research; research does not pre-commit to gates.

---

## Folder layout

```
market-research/
  README.md                      ← this file (master index)
  INDEX.md                       ← chronological list of every research dossier
  dossiers/
    YYYY-MM-DD__short-slug.md    ← one dossier per research session
  tracking/
    watch_signals.md             ← live signals being tracked across dossiers
    probability_stack.md         ← rolling probability-stack updated session by session
  scenario-engine/               ← prediction tracking system w/ calibration loop
    README.md                    ← system principles + how to add/resolve predictions
    INDEX.md                     ← master table of scenarios + predictions
    scenarios/                   ← conditional scenario trees (if X → then Y)
    predictions/                 ← individual falsifiable predictions w/ Brier scoring
    calibration/                 ← brier_log.csv + quarterly calibration_report.md
  raw_agent_outputs/             ← optional, raw sub-agent outputs for traceability
```

**Difference between `tracking/` and `scenario-engine/`:**
- `tracking/probability_stack.md` is the **live dashboard** — current beliefs, updated session-by-session
- `scenario-engine/` is the **calibration system** — predictions made at a point in time, locked, and scored against outcomes when they resolve. It tells you whether your stated probabilities match your actual hit rates over time.

---

## Naming convention for dossiers

`dossiers/YYYY-MM-DD__short-slug.md`

Examples:
- `2026-05-05__nepal-market-context-and-trade-ideas.md`
- `2026-05-12__nepse-chairman-appointment-followup.md`
- `2026-06-01__chandra-dhakal-status-check.md`

---

## Required structure for every dossier

Every dossier must contain these sections in order:

1. **Header block** — date, time, who/what triggered the research, scope statement
2. **Question(s) being answered** — bullet list of the specific questions
3. **Method** — agents spawned, search strategies, data sources, what was excluded
4. **Headline findings** — the top 5-10 facts surfaced, dated and sourced
5. **Probability updates** — what priors moved, by how much, with reasoning
6. **Trade ideas / opportunities** — concrete tickers + entry/stop/target/horizon, OR explicit "no trade"
7. **Watch signals added** — leading indicators to monitor (these get copied to `tracking/watch_signals.md`)
8. **Honest gaps** — what was searched but not found, what would falsify the read
9. **Sources** — URLs grouped by topic, with publication dates

---

## Discipline rules for research

These are NOT pre-registrations. They are research dossiers. So:

- **Strong opinions allowed.** "I think X with probability Y%" is the format.
- **Sources required.** Every claim that's not labeled opinion needs a URL.
- **Date everything.** Markets move fast; a research finding from 3 weeks ago may already be stale.
- **Honest gaps explicit.** If an agent couldn't verify a claim, say so.
- **Probability updates carry forward.** Each new dossier should reference the previous probability stack and explicitly update it.
- **No silent overwrites.** When updating an earlier read, write a new dossier; don't edit the old one. The chronological trail is the audit trail.

---

## When to spawn a new dossier

- Major news event that materially shifts a probability (>10pp move)
- New scandal/arrest/regulatory action
- Targeted research on a specific symbol or sector
- Pre-trade verification before committing real money
- Quarterly market-state reset

Don't spawn a dossier for routine market noise. Each dossier should be substantive enough to stand alone.
