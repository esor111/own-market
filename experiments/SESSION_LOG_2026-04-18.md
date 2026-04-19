# Session Log — 2026-04-18 (Saturday)

> Long session. Ishwor + Juliet + Romeo all active.
> Started as "catch up the daily routine" — turned into the session that found the silent git-merge data-corruption bug, materially revised the persistence hit rate, and built multiple Layer 3 tools.

---

## What Ran Today (End State)

### Catch-Up Data Pipeline
- Scraped broker flow for 26 symbols × Apr 14-17 (Apr 14 = Nepali New Year holiday, correctly empty).
- Backfilled sharesansar price CSVs Jan 1 – Apr 17, 2026 (most already existed; 5 new, 3 legit no-data for weekend/holiday).
- **Discovered 16 corrupted price CSVs** with unresolved git merge conflict markers — see L-015.
- Deleted 16 corrupt CSVs, re-scraped clean (15 saved, 1 legit no-data for Mar 20).
- Generated shadow reports for Apr 15, 16, 17 (Apr 14 skipped — holiday).
- Re-ran scorer against clean data.

### Scorecard Delta

| | Before today | After today |
|---|---|---|
| Total resolved rows | 14 | 20 |
| `persistence_caution_only` resolved | 9 | 11 |
| Hit rate (CAUTION only) | 88.9% | **72.7%** |
| Hit rate (all CAUTION including dividend-annotation) | 88.9% | **66.7%** |
| Unique report dates | 3 | 5 |
| Unique WIN dates | 3 | 3 (new cases both losses) |

Both newly-resolved cases (Mar 31 NABIL +0.17%, Apr 1 NABIL +1.53%) were LOSSES for the CAUTION signal. Romeo-verified: not statistically significant at N=11 (one-sided binomial p ≈ 0.11).

---

## What Got Built Today

### 1. Sandbox Protocol (Layer 3 architecture)
- `experiments/SANDBOX_PROTOCOL.md` — three-layer architecture + contract + promotion path
- `experiments/_CONTRACT_TEMPLATE.md` — copy-template for new experiments
- `experiments/INDEX.md` — updated references

### 2. Signal Decay Tracker (first reference sandbox)
- `experiments/signal-decay-tracker/` complete — CONTRACT, README, run.py, baseline snapshot
- Below sample gate (N=11, gate=20); descriptive stats only, no alerts fire yet

### 3. Batch-Score Playbook (second reference sandbox)
- `experiments/batch-score-playbook/` complete — CONTRACT, README, run.py, baseline decision memo
- Current verdict: BELOW_GATE (N=11 < 25)
- Forced verdict on current data returns KILL (top-1 date share 45.5%, top-3 81.8% — still clustered)

### 4. Price Data Integrity Utility (Layer 1 infrastructure)
- `market-gist/automation/price_data_integrity.py` — scans for merge markers, empty files, bad headers
- Wired into `score_persistence_shadow_reports.py main()` — fails loudly on corruption
- Tested: clean-data pass, corrupt-file fail, both produce correct behavior

### 5. Dividend Microstructure PRE_REGISTRATION (Revision 3)
- Romeo's first review (2026-04-17): rev 2 integrated blocking items
- Romeo's second review (2026-04-17): rev 3 fixed bootstrap p-value sign, cohort event-type clarification, metadata staleness
- Romeo's third review (2026-04-18): signed off with recommendation to patch rev labels
- Ishwor independently validated Romeo's 2026-04-18 review; approved with small framing nuances
- All metadata now reads Revision 3 (grep audit: zero stale references)
- Ready for Step 1 code next session

### 6. Hydro-Intelligence Pilot Update
- `experiments/hydro-intelligence/CURRENT_VIEW_2026-04-18.md` — new snapshot, Apr 13 version preserved
- `symbols/UPPER/facts.md` — added dated entries for Apr 15-17 anomaly continuation (Apr 15 peak = 2,567 rows, ~6-10× Dec baseline) + price spike + reversal
- `symbols/RHPL/facts.md` — added dated entries for Apr 13-17 tape (weak, consistent with existing "avoid" stance)
- Decision memos UNCHANGED (UPPER=hold, RHPL=avoid) — invalidation conditions did not fire

### 7. Working Discipline (self-audit framework)
- `experiments/WORKING_DISCIPLINE.md` — running log of 8 concrete mistake patterns with dated examples, costs, prevention rules, and 30-second self-audit steps. Pre-submit checklist at bottom.
- `memory/feedback_working_discipline.md` — survives across Claude sessions. Points to the full discipline doc.
- `memory/MEMORY.md` — updated index.

---

## What Got Documented Today

- **L-012 addendum (2026-04-18):** Clean-data correction reveals 88.9% → 72.7% (or 66.7% all-CAUTION). Signal directionally suggestive but not statistically significant at current N. Headline "still above chance" framing retired.
- **L-015 new entry:** Silent data corruption (git merge conflict markers) can hide for months and break the evidence base. Fix landed. Prevention rules documented.
- Romeo review (2026-04-18) captured inline in sign-off section of PRE_REGISTRATION.md and referenced in L-012 addendum.

---

## Hydro Pilot Highlight

**UPPER volume anomaly intensified:**
```
Dec 2025 baseline:    260 – 437 rows/day
Apr 9:               1,102 rows (first flag)
Apr 10:              1,255 rows
Apr 13:              1,369 rows
Apr 15:              2,567 rows  ← NEW PEAK, ~6-10× baseline
Apr 16:              1,437 rows
Apr 17:              1,052 rows
```

Apr 15 price: spiked +3.46% intraday on 2× normal volume, then fully reversed over Apr 16-17. Net 4-day price change: ~0%. Pattern = failed-breakout / distribution-absorbed / two-sided contest. Peer hydros (API, AHPC, AKPL) also elevated but nowhere near UPPER levels → anomaly is UPPER-specific, not sector-wide. Pilot stance stays `hold`; invalidation conditions did not fire.

---

## Key Discoveries Today

1. **16-file silent data corruption** (biggest finding). Explains why persistence cases weren't resolving on schedule. Fix landed, integrity guard wired.

2. **Hit rate drop from 88.9% to 72.7%** on clean data. Not a revision — a CORRECTION. L-012 addendum captures.

3. **UPPER anomaly is UPPER-specific and intensifying.** Not sector rotation, not monsoon, not holiday catch-up alone. The story is genuinely localized to one symbol.

4. **Two new independent persistence cases (Mar 31, Apr 1 NABIL) were losses.** The signal failed in its first independent-data test post-Aug-cluster. Sample is still thin; not conclusive.

5. **I was making preventable mistakes repeatedly.** Ishwor flagged the pattern. Built `WORKING_DISCIPLINE.md` + memory entry to formalize prevention.

---

## What's Queued For Next Session

1. **Dividend Microstructure Step 1 code** (`build_event_table.py` + `check_gate1.py`) — Romeo signed off, path clear.
2. **Reversal Specialist sandbox** — Tier 1 signal guaranteed independent of L-001; next cleanest Layer 3 experiment.
3. **Optional Layer 1 UX addition** — wire `price_data_integrity` into `run_persistence_shadow_daily.py` as Step 0 for nicer failure messages (not critical; scorer already guards).
4. **Expected N=25 gate firing around April 27 – May 5** — batch-score playbook ready to use when resolved count hits 25.

---

## What's Still Live

| | Status |
|---|---|
| Persistence signal | Running daily, 11 resolved CAUTION, 14 pending, hit rate 72.7% preliminary |
| Daily scrape (26 symbols) | Running |
| Signal decay tracker | Baseline snapshot set, below sample gate |
| Batch-score playbook | Ready for use when gate fires |
| Hydro-intelligence pilot | UPPER hold, RHPL avoid, Apr 18 snapshot live |
| Dividend microstructure | Pre-code, rev 3 signed off, ready for Step 1 |
| Data integrity guard | Live in scorer |

---

## Self-Audit (per WORKING_DISCIPLINE pre-submit checklist)

- [x] **Paths absolute.** Every file check in this session used absolute paths after the hydros-missing mistake.
- [x] **Metadata consistent.** PRE_REGISTRATION.md title now matches content (rev 3 throughout). Grep-verified.
- [x] **Math shown.** Binomial test p ≈ 0.11 cited explicitly before retiring "above chance" framing.
- [x] **Sort order verified.** Corrected the 3.5-months-missing false alarm; prefer Python filename parsing over `ls | tail`.
- [x] **Scope enumerated.** All 7 hydro symbols individually checked for Apr 14-17 coverage. Confirmed all present.
- [x] **Independent verification.** Romeo's 2026-04-18 review validated independently; documented in my reply to Ishwor.
- [x] **Status lines updated.** PRE_REGISTRATION sign-off, CONTRACT.md gates, README.md status, hydro CURRENT_VIEW all refreshed.
- [x] **Consolidation.** This session log + L-012 addendum + L-015 entry + WORKING_DISCIPLINE = today's consolidation artifacts.

---

*Written 2026-04-18 by Juliet.*
*Before: lab state was "N=14 resolved, 88.9% hit rate, quiet." After: lab state is "N=20 resolved, 72.7% hit rate, preliminary not significant, data pipeline hardened, discipline formalized."*
*The lab is more robust and more honest than it was at session start.*
