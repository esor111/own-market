# Session Log — 2026-04-13 (Monday)

> First trading day under the new Monday-Friday schedule.
> Full session. Covered: daily routine, hydro-intelligence enrichment, RHPL gap closure, brainstorm + research validation, sandbox protocol, signal decay tracker build.

---

## What Ran Today

### Daily Routine (first Mon-Fri day)
- Scraped 26 symbols (added RHPL mid-session); all hydropower covered
- Shadow report: NABIL CAUTION (3rd consecutive day), EBL + SANIMA NO_SIGNAL
- Research lane: AKPL + UPPER CAUTION (research only)
- UPPER transaction count flagged: 1102 → 1255 → 1369 over Apr 9-13, 3-4× normal

### Pilot Enrichment
- RHPL added to `scrape_symbol_list.json` (new tier `hydro_intelligence_pilot` created)
- RHPL scraped for Apr 13 (227 rows) — first broker-flow data on this symbol ever
- UPPER facts.md updated with Apr 9-13 volume anomaly observation

---

## What Was Built Today

### Sandbox Protocol (foundation)
- `experiments/SANDBOX_PROTOCOL.md` — formal three-layer architecture (Production / Shared / Research), contract rules, naming convention, run isolation, promotion path
- `experiments/_CONTRACT_TEMPLATE.md` — copy-paste template for new experiments
- `experiments/INDEX.md` — updated with references to both new docs

### Signal Decay Tracker (first reference sandbox)
- `experiments/signal-decay-tracker/` — complete folder
  - `CONTRACT.md` — contract per protocol
  - `README.md` — purpose, severity tiers, runbook
  - `run.py` — working implementation
  - `results/decay_2026-04-17.json` + `.md` + `latest.*` — first baseline snapshot
  - `alerts/` — empty (no alerts fired; below sample gate)

First run confirmed the L-012 clustering finding mechanically:
- 9 resolved `persistence_caution_only` cases
- 88.9% hit rate BUT 5/9 from Aug 4, 3/9 from Aug 5, 1/9 from Dec 7
- Below sample gate (N=14 < 20); tracker correctly declines to fire alerts

**Verified isolation:** no files in `market-gist/automation/` or `market-gist/data/validation/` were modified. Contract enforced.

---

## Research + Validation Work

### Research-backed tier reset (Benvolio/Romeo verification)
Received a literature pass that tiered my original 7-direction brainstorm. Material corrections:

1. **Regime detection should be a FILTER, not a predictor** — literature supports it as a gate over other signals, weak as standalone
2. **Three signals I under-weighted are the most validated in all my proposals:**
   - Retail pile-in contrarian (validated in Ho Chi Minh frontier market)
   - Dividend / book-closure microstructure (one of finance's most robust findings)
   - Mean reversion / reversal specialist (thin markets favor reversion, multi-country support)
3. **Signal decay tracker is Tier 1, not a meta-idea** — build from day one

### Revised priority stack (documented in `linked-popping-quokka.md`)
```
TIER 1 — Build first. Academic-backed. Existing data.
  1. Retail pile-in contrarian signal
  2. Dividend / book-closure microstructure
  3. Reversal specialist
  4. Signal decay tracker   ← DONE TODAY
```

---

## Doctrine / Architecture Decisions Made

1. **Sandbox Protocol is canonical.** Every new experiment folder must follow it.
2. **Layer 3 experiments physically isolated by contract.** Can be deleted without side effects.
3. **Naming prefix `x-<slug>-` for experimental signal verdicts.** Never confused with production.
4. **Weekly review cadence for experiments**, not daily. Daily production report stays pure.
5. **Signal Decay Tracker does not itself need full 6-step promotion** because it does not predict; it monitors. Romeo reviews threshold sensibility, that's enough.

---

## What Patience Mode Allows (Resolved Tension)

Earlier question: "should we do nothing for 10 days waiting for persistence to resolve, or is that wasting Claude time?"

**Answer: patience mode applies to PROMOTION, not to EXPLORATION.** Parallel Layer 3 exploration is explicitly permitted by `PARALLEL_EXPLORATION_SERIAL_PROMOTION.md`. Waiting for persistence to resolve does NOT mean the lab stops. It means no promotion decisions until the gate fires.

So the 10-day arc is: build Tier 1 signals as Layer 3 sandboxes, each generating its own forward evidence independently of persistence.

---

## Current State At End Of Session

### Signals Live
| Signal | Layer | State | Evidence |
|---|---|---|---|
| Persistence shadow (w7 seller) | Production | Running, frozen | 14/37 resolved, 9 CAUTION cases, 88.9% but clustered |
| Dividend-family annotation | Production | Annotation only | 71% bank hit rate, p=0.004 |
| Signal Decay Tracker | Research (Layer 3) | Running weekly | Baseline snapshot today; N=14 below gate of 20 |

### Pending Evidence
- 23 persistence cases resolving over next ~10 trading days
- Batch-score gate at 25+ resolved cases (expected ~April 23-24)

### Ready To Build Next
- **Dividend Microstructure** signal (Tier 1, Benvolio's literature pass flagged as highest validation)
- Research phase BEFORE building: understand ex-dividend literature, define clean hypothesis, define methodology
- Target folder: `experiments/dividend-microstructure/` following SANDBOX_PROTOCOL

---

## Claude Access Constraint

Ishwor flagged: ~10 days of Claude premium remaining, then access pauses until subscription renewed. Session-preserved context via this log + CONTRACT.md + README.md in each experiment folder. Future-Claude reads these first.

**The lab runs without Claude after this window.** Automated daily routine + weekly decay tracker run + waiting for forward evidence. When Claude returns, pick up from this log.

---

## Open Items For Next Session

1. **Build Dividend Microstructure sandbox** (research first, then scaffold)
2. **Optional: build Retail Pile-in Contrarian sandbox** (3rd Tier 1 signal, trade-size classification)
3. **Document the April 24 batch-score decision playbook** (how to execute alone if Claude is unavailable)
4. **Review Signal Decay Tracker weekly output** — watch for concentration or decay alerts

---

*Written 2026-04-13 by Juliet.*
*Protocol in `SANDBOX_PROTOCOL.md`. Doctrine in `PARALLEL_EXPLORATION_SERIAL_PROMOTION.md`. Big goal in `BIG_GOAL.md`.*
