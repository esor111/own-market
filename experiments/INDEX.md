# Experiment Index

| # | Name | Hypothesis | Status | Result | Next Action |
|---|------|-----------|--------|--------|-------------|
| 01 | Corporate Action Timing | Event dates create measurable price moves | reviewed | full 14-symbol seed run corrected for valid anchoring + baseline drift; 768 in-range events scored, 4 baseline-adjusted families survived phase 2, and only 1 family held cross-sector in phase 3 | keep as research-only until we test above-SMA periods or fresh forward data |
| 02 | Lock-in Expiry | Promoter unlock causes negative returns | tested | full hydropower proxy run completed; 154 listing proxies -> 27 in-range unlocks | review signal quality and consider CDSC notice dates as a sharper upgrade |
| 03 | NRB Rate Events | Discrete NRB policy events create measurable short-term market moves | tested | official NRB endpoint run completed; policy-event effects are real but not a clean market-wide easing-bullish rule, and interbank large-move effects are mostly hydro-heavy | treat as regime/context research, not a promoted trigger |
| 04 | Hydro Seasonality | Hydro stocks inherit seasonal performance from water and generation cycles | completed | historical seasonal pattern in 2021-2026 window: Jan bullish (89%), Feb/Aug/Nov bearish (78-82%), Jul bullish (70%); cross-stock consistent and year-stable within that window; forward validation still required | use as calibration baseline for hydro agent interpretation; do not treat as validated out-of-sample |
| 05 | Raw Text Context | Policy/disclosure text improves structured prediction context | not started | - | define extraction schema |
| 06 | Hydro Flood Damage | Named flood damage to listed hydro assets creates peer-relative underperformance | structured | UPPER Sep 2024 sanity check kept the lane alive but narrowed it: short-window effect is noisy, slower lag looks more plausible | build full hydro symbol registry and damage-confirmation event table before any scoring pass |
| 07 | Dividend Microstructure | T_ex date creates actionable short-window drift beyond L-001 notice effect | closed at Gate 1 | Cohort A N=24 (gate≥80), 71% L-001 overlap — structurally measures the same corp-action cycle as L-001 | preserved as historical record; no H1 run (see L-016 companion closure) |
| 08 | Reversal Specialist | NEPSE stocks mean-revert after sharp ≤-5% daily moves | closed at Gate 1 | Primary N=66 h1-eligible (gate≥80); 53% of raw sharp-down days were Layer B market-wide shocks — idiosyncratic event rate too low for properly-powered test | preserved (see L-016) |

## Doctrine Docs

- `BIG_GOAL.md` — the shortest statement of the lab's north star: what the whole system is actually for
- `HYDRO_SYMBOL_INTELLIGENCE_ARCHITECTURE.md` — parked architecture for a future symbol-intelligence system; save now, build later
- `_parked/LIVE_MARKET_CAPTURE_CONCEPT.md` — parked future execution-awareness layer for structured intraday depth/tape capture and independent-agent source research
- `MANIFESTO.md` — what the lab is betting on and what discipline it refuses to abandon
- `ORCHESTRATOR_DOCTRINE.md` — the AI leverage / researcher mindset layer
- `PARALLEL_EXPLORATION_SERIAL_PROMOTION.md` — the operating law for running many side quests without promoting noise
- `SANDBOX_PROTOCOL.md` — the three-layer architecture and contract every Layer 3 experiment must follow
- `_CONTRACT_TEMPLATE.md` — copy this when starting a new experiment folder
- `SIDE_QUEST_MAP.md` — the current exploration dashboard: now, next, later, and deliberately parked
- `WORKING_DISCIPLINE.md` — Juliet's running mistake log + pre-submit checklist (added 2026-04-18)

## Shared Infrastructure

- `shared/build_universe_v2_candidate.py` — reproducible script producing universe_v2_candidate.csv from ShareSansar archive
- `shared/universe_v2_candidate.csv` — 581 symbols, 93 selected; pending Romeo final sign-off before freeze
- `shared/universe_v1_frozen.csv` — 26-symbol v1 reference frozen 2026-04-19; out-of-sample anchor for L-009/L-010
- `shared/integrity_sweep_2026-04-19.md` — archive integrity sweep result (1,595 clean, 0 corrupt)
- `shared/L001_V2_VERSIONING_PLAN.md` — rules for extending corporate-action coverage to 93-symbol universe without rewriting L-001 conclusions

## Session Logs

- `SESSION_LOG_2026-04-12.md` — initial sandbox-protocol session
- `SESSION_LOG_2026-04-13.md` — first Monday under new Mon-Fri schedule
- `SESSION_LOG_2026-04-18.md` — data-integrity incident + scorecard correction + multiple Layer 3 tools built
- `SESSION_LOG_2026-04-19.md` — reversal-specialist Gate 1 closure (L-016) + universe expansion v2 candidate registry built
