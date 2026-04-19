# Session Log — 2026-04-19

## What Happened

### Reversal Specialist Gate 1 closure

Gate 1 ran and failed on primary direction (N=66 < required 80). Lane closed per pre-registration. Key finding: 53.5% of raw sharp-down symbol-day candidates were Layer B market-wide-shock flagged — the dominant filter. Idiosyncratic event rate too low for a properly-powered H1.

Documented as L-016 in `LEARNINGS.md`. Experiment 08 added to `INDEX.md`.

Romeo reviewed the L-016 draft and returned 6 wording corrections (see L-016 notes in LEARNINGS.md). All corrections applied and verified independently before merge.

Romeo Tier 1 inference from L-016: two successive Gate 1 failures (07, 08) for different reasons — suggests running sample-power checks earlier, before the full pre-registration review cycle, to catch under-powered designs cheaply.

### Universe expansion decision

After two Gate 1 failures, root cause identified: 26-symbol universe is too small for certain signal types. ShareSansar daily CSVs already contain all 335 NEPSE symbols — price data expansion is free.

Romeo approved universe expansion in principle with 6 specific requirements. All 6 completed this session:

1. `experiments/shared/build_universe_v2_candidate.py` — reproducible Python script
2. All 144 eligible symbols: high-confidence sector classification after manual verification of 51 ambiguous cases via parallel web agents
3. `experiments/shared/universe_v2_candidate.csv` — 581 rows, 93 selected
4. `experiments/shared/universe_v1_frozen.csv` — 26-symbol v1 reference, frozen 2026-04-19
5. Archive integrity sweep: 1,595/1,595 daily CSVs clean (see `shared/integrity_sweep_2026-04-19.md`)
6. Scraper wiring deferred (Romeo: do not edit `scrape_symbol_list.json` until registry frozen)

### Universe v2 candidate summary

- 581 total symbols in archive
- 451 pure equity (after debenture/promoter/mutual-fund exclusion)
- 197 with continuous history since 2021-09-01
- 144 with active_days_90 ≥ 30
- 93 selected via per-sector quota (top-N by median 90d turnover)
- Sectors: HYDROPOWER:25, COMMERCIAL_BANK:17, MICROFINANCE:12, FINANCE:8, DEV_BANK:8, NON_LIFE_INSURANCE:6, LIFE_INSURANCE:5, MANUFACTURING:4, HOTEL:4, INFRA_INVEST:2, INVESTMENT:1, TRADING:1, TELECOM:1

### Key corrections caught during sector verification

- LBBL: heuristic said COMMERCIAL_BANK, web confirms Lumbini Bikas Bank = DEV_BANK
- RURU: pattern suggested microfinance, web confirms Ru Ru Jalbidhyut Pariyojana = HYDROPOWER
- NMBMF: "MF" suffix suggested mutual fund, web confirms NMB Laghubitta = MICROFINANCE
- LUK: unclassified, web confirms Laxmi Unnati Kosh = closed-end mutual fund → excluded
- SINDU: bank name pattern match, web confirms Sindhu Bikash Bank = DEV_BANK

### L-001 v2 versioning plan

Written `experiments/shared/L001_V2_VERSIONING_PLAN.md` to close the event-coverage asymmetry hole in the v2 expansion. Key rules: L-001 original stays frozen; L-001-v2 is separate infrastructure covering 93 symbols; experiments must declare which version they use (`L-001-original` / `L-001-v2` / `none`); coverage report required before v2 is usable; no silent reinterpretation of prior results against v2 data.

Ishwor later corrected the numbers: L-001 covers 14 symbols, not 26; only 11 of the 93 selected v2 symbols overlap current L-001 coverage; 82 selected v2 symbols therefore lack coverage. Memo reflects corrected numbers.

### Recent Retrospective Replay — pre-registration evolution

Romeo pivoted away from a 2022-OOS probe in favor of a recent 6-month retrospective replay strictly labeled audit/calibration, not promotion evidence. Pre-registration went through four revisions same session:

- **r1** (my first draft) — Romeo rejected: rule vaguely scoped to "full frozen persistence policy"; calendar error (2026-04-28 was not 10 trading days after 2026-04-17; real cutoff is 2026-05-01).
- **r2** (rule scoped to w7 sub-rule only; calendar corrected; backfill-first sequence added) — Romeo rejected: Step 2 allowed dropping failed-coverage symbols mid-flight (post-hoc scope change).
- **r3** (all-or-nothing gate enforced; any one of NABIL/EBL/SANIMA failing 80% coverage = replay aborts entirely; no subset hit rate, no subset recommendation) — Romeo approved structure.
- **r4** (after w7 code audit) — rule definition tightened to production-code semantics (top-weighted broker, not any-broker); sparse-window behavior explicitly accepted with `prior_days_used` distribution reporting requirement; `replay_cases.csv` columns expanded; fragility labeling rule added.

Coverage state per Romeo's own check: NABIL 27.5%, EBL 49.6%, SANIMA 41.2% — all three fail 80% gate. Replay blocked on backfill.

### Backfill Authorization

Written and patched `BACKFILL_AUTHORIZATION_REQUEST.md`. After Romeo verdict on w7 audit:
- Source locked to existing `market-gist/automation/backfill_merolagani_floorsheet.py` (no new scraper code)
- No fallback source without re-authorization
- No force-overwrite of existing broker-flow files
- Only two deliverables: schema-match memo and coverage report

### w7 Sub-Rule Code Audit (pre-flight)

Before committing to backfill, audited the w7 rule code against Romeo's spec. Written `experiments/persistence-recent-replay/data/w7_rule_code_audit.md`. Core match confirmed (top-10 sellers per day, prior-7 ledger sessions, anchor-day independent). Two ambiguities flagged for Romeo:
- Code uses `max(frac × avg_share)` broker selection (not "any broker with frac=1.0")
- Sparse-window behavior: `frac = days_present / n_days` where `n_days` can be < 7 if data gaps exist

Romeo verdict: accept current production-code semantics for this replay; stricter variants become future challenger rules; add fragility labeling to replay bands (>30% sparse-window share → fragile).

### Schema-Match Test

Ran `backfill_merolagani_floorsheet.py` for NABIL 2025-11-03 with `--max-pages 1`. Produced 319 rows. Diffed against live reference `NABIL/2026-04-17.json`: 124 common key paths, 0 missing, 0 extra. Critical identifiers (`schema_version`, `ledger_type`, `source.kind`) all match.

Schema-match is trivial because the reference file was itself produced by the same Merolagani backfill code path (live scrape and backfill share `build_broker_flow_ledger`). No drift. Written `experiments/persistence-recent-replay/data/schema_match_memo.md` with verdict `match`.

### Self-audit protocol adopted

Ishwor imposed an 8-point pre-handover checklist (metadata, scope, paths, data-state, evidence-label, all-or-nothing gates, outcome leakage, language discipline) plus mandatory SELF-AUDIT block format and explicit Romeo-review triggers. Updated `feedback_working_discipline.md` memory. Proposed-path convention applied retroactively to both in-flight docs (PRE_REGISTRATION r3 at the time, BACKFILL_AUTHORIZATION_REQUEST).

Later correction from Ishwor: stop over-applying the protocol. Diagnostic analyses don't need SELF-AUDIT ceremony or Romeo approval. Save discipline for actual Romeo triggers.

### External reviewer critique

External reviewer posted a 6-point critique plus a bigger-frame reframe (Goal A: personal alpha; Goal B: first NEPSE quant research lab). Verified two claims directly: (a) zero cost-related terms in `score_persistence_shadow_reports.py` — critique stood; (b) 14 lanes in SIDE_QUEST_MAP — close to reviewer's claim of "~12". Assessed each point for validity and urgency:

- Point 1 (cost model in scorer): SEVERE, reviewer right, would invalidate N=25 gate.
- Point 2 (effective-N / correlation): SERIOUS, reviewer right, 30-min script could have caught 07/08 failures.
- Point 3 (hit rate → EV): OVERSTATED — lab does track mean return; EV improvement is correct but gap is smaller than framed.
- Point 4 (surface too wide): directionally fair, reviewer overcounted.
- Point 5 (system-level kill date): strategically critical, reviewer right.
- Point 6 (structural info asymmetry): philosophically sharp, partially self-neutralized by reviewer's own orthogonal-bet suggestion.

### INTERPRETATION_GATE.md v1

Romeo's response to reviewer Points 1 and 3: harden the batch-score playbook with actionability metrics. Added 8 metrics (avg win/loss, payoff ratio, pre-cost mean return, post-cost EV, avoid-buy value vs baseline, exit/sell value, actionability label), 2 new verdicts (`FORECAST_VALID_CONTEXT_ONLY`, `HOLD_PENDING_ACTIONABILITY`), and a three-lens CAUTION interpretation rule (avoid-buy default, exit-sell secondary, research-only short-like for forecast content only). Wrote as pre-code contract in `experiments/batch-score-playbook/INTERPRETATION_GATE.md`; no code changes.

### Effective-N / Correlation Analysis

Addressed reviewer Point 2 autonomously (no ceremony). Computed pairwise correlation of daily log returns across the 93 v2 candidate symbols over 2023-01-01 to 2026-04-17 (996 common dates). Written `experiments/shared/effective_n_analysis_2026-04-19.md`.

Headline findings:
- **Market-wide effective N = 2.6** (when whole universe is pooled as one bag). NEPSE trades on ~2–3 macro factors.
- **Sector-pooled effective N = 20.4** summed across sectors (when each sector is analyzed independently).
- Commercial banks: 16 symbols → 1.58 effective (ratio 0.10). Mean |corr| = 0.61.
- Hydropower: 25 → 2.05 (ratio 0.08).
- Manufacturing: 4 → 2.3 (ratio 0.58) — only sector where naive and effective are close.

Romeo reviewed, locked canonical takeaway ("rows are cheap; independent evidence is rare"), and required 5-item reporting for any v2 pre-registration: naive count, unique dates, sector distribution, expected effective N / correlation adjustment, test type (market-wide / sector-pooled / stock-specific). Rule for v2 freeze package: no v2 experiment may claim Gate 1 sample adequacy from naive N alone. Memo patched with Romeo Interpretation section.

### Live Market Capture — parked

Brainstorm request from Ishwor (forwarded to Romeo/Codex). Assessed: genuinely interesting, wrong time. If built, best pilot is 1 symbol (NABIL), 5 days, 10-second interval, structured DOM only, 2 patterns (absorption + quote fade). Biggest edge = execution awareness (not prediction). Biggest risk = displayed depth is intention, not truth.

Parked in `SIDE_QUEST_MAP.md` under Later (Ishwor moved it) with concept note at `_parked/LIVE_MARKET_CAPTURE_CONCEPT.md`. Revisit trigger: when at least 2 of (N=25 resolves, universe v2 freezes, w7 replay completes).

### Full backfill started (end of session)

Full Merolagani backfill for NABIL/EBL/SANIMA across 2025-10-19 to 2026-04-18 kicked off in background using `backfill_merolagani_floorsheet.py`. No `--force`, no `--max-pages`, sequential. Expected 2–4 hour runtime. Single deliverable on completion: `backfill_coverage_report.md`.

## Open Items

- Romeo final verdict on universe v2 freeze (package now includes effective-N memo)
- Romeo review of `INTERPRETATION_GATE.md` v1 before any batch-score-playbook code changes
- Full backfill completion + coverage report
- If backfill delivers ≥80% per symbol: r4 Step 3 (w7 code verification — informed by audit memo) → Step 4 (replay run) → Step 5 (publish results)
- Persistence N=25 forward gate: ~10-14 trading days away (late April to early May)
- MANIFESTO system-level kill date (queued, needs Ishwor to pick date + threshold)
- Reviewer Points 4, 6 still open (surface narrowing, structural-info measurement)

## Files Changed (full-day total)

```
Morning:
  experiments/LEARNINGS.md              — L-016 added
  experiments/INDEX.md                  — experiments 07, 08 added
  experiments/shared/build_universe_v2_candidate.py  — new
  experiments/shared/universe_v2_candidate.csv       — new (581 rows)
  experiments/shared/universe_v1_frozen.csv          — new (26 rows, frozen reference)
  experiments/shared/integrity_sweep_2026-04-19.md   — new (sweep report)

Afternoon:
  experiments/shared/L001_V2_VERSIONING_PLAN.md      — new (event-coverage rules for v2)
  experiments/shared/effective_n_analysis_2026-04-19.md  — new (correlation memo + Romeo Interpretation)
  experiments/persistence-recent-replay/PRE_REGISTRATION.md  — new, evolved r1 → r2 → r3 → r4
  experiments/persistence-recent-replay/BACKFILL_AUTHORIZATION_REQUEST.md  — new, patched post-w7-audit
  experiments/persistence-recent-replay/data/w7_rule_code_audit.md  — new
  experiments/persistence-recent-replay/data/schema_match_memo.md  — new
  experiments/batch-score-playbook/INTERPRETATION_GATE.md  — new (pre-code gate contract)
  experiments/_parked/LIVE_MARKET_CAPTURE_CONCEPT.md — new (Ishwor-added; parked design note)
  experiments/SIDE_QUEST_MAP.md — Live market capture added under Later
  experiments/INDEX.md — shared infrastructure + session log references updated
  memory/feedback_working_discipline.md — 8-point self-audit protocol + SELF-AUDIT block + Romeo-review triggers
  memory/MEMORY.md — working-discipline entry updated

Scrape artifacts (from schema-match test, preserved as real data):
  market-gist/broker_flow_ledger/NABIL/2025-11-03.json
  market-gist/broker_flow_ledger/raw_merolagani/NABIL/2025-11-03.json
```

## Meta-observations from the day

- **Discipline scaled.** One pre-registration went through 4 revisions in a single session, each catching a real methodology bug Romeo spotted (rule scope, calendar math, subset rescue, production-code semantics). The review loop is working.
- **Reviewer surfaced two real gaps** that were verified in code (no cost model in scorer; no correlation analysis). Both are cheap fixes. Romeo converted Point 1 into `INTERPRETATION_GATE.md`; Juliet converted Point 2 into the effective-N memo. Points 4, 5, 6 remain.
- **Self-audit protocol** needs calibration. Over-applying it to diagnostic work generates Romeo-review ceremony where none is warranted. Save the discipline for the actual triggers.
- **Key new infrastructure:** effective-N reasoning, interpretation-gate contract, v2 universe registry, L-001 versioning rules. None of these are signals; all of them are load-bearing for future signal claims.
