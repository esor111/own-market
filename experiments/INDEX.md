# Experiment Index

| # | Name | Hypothesis | Status | Result | Next Action |
|---|------|-----------|--------|--------|-------------|
| 01 | Corporate Action Timing | Event dates create measurable price moves | reviewed | full 14-symbol seed run corrected for valid anchoring + baseline drift; 768 in-range events scored, 4 baseline-adjusted families survived phase 2, and only 1 family held cross-sector in phase 3 | keep as research-only until we test above-SMA periods or fresh forward data |
| 02 | Lock-in Expiry | Promoter unlock causes negative returns | tested | full hydropower proxy run completed; 154 listing proxies -> 27 in-range unlocks | review signal quality and consider CDSC notice dates as a sharper upgrade |
| 03 | NRB Rate Events | Discrete NRB policy events create measurable short-term market moves | tested | official NRB endpoint run completed; policy-event effects are real but not a clean market-wide easing-bullish rule, and interbank large-move effects are mostly hydro-heavy | treat as regime/context research, not a promoted trigger |
| 04 | Hydro Seasonality | Hydro stocks inherit seasonal performance from water and generation cycles | completed | strong seasonal confirmed: Jan bullish (89%), Feb/Aug/Nov bearish (78-82%), Jul bullish (70%); cross-stock consistent; year-stable | use as calibration baseline for hydro agent interpretation |
| 05 | Raw Text Context | Policy/disclosure text improves structured prediction context | not started | - | define extraction schema |
| 06 | Hydro Flood Damage | Named flood damage to listed hydro assets creates peer-relative underperformance | structured | UPPER Sep 2024 sanity check kept the lane alive but narrowed it: short-window effect is noisy, slower lag looks more plausible | build full hydro symbol registry and damage-confirmation event table before any scoring pass |

## Doctrine Docs

- `BIG_GOAL.md` — the shortest statement of the lab's north star: what the whole system is actually for
- `HYDRO_SYMBOL_INTELLIGENCE_ARCHITECTURE.md` — parked architecture for a future symbol-intelligence system; save now, build later
- `MANIFESTO.md` — what the lab is betting on and what discipline it refuses to abandon
- `ORCHESTRATOR_DOCTRINE.md` — the AI leverage / researcher mindset layer
- `PARALLEL_EXPLORATION_SERIAL_PROMOTION.md` — the operating law for running many side quests without promoting noise
- `SANDBOX_PROTOCOL.md` — the three-layer architecture and contract every Layer 3 experiment must follow
- `_CONTRACT_TEMPLATE.md` — copy this when starting a new experiment folder
- `SIDE_QUEST_MAP.md` — the current exploration dashboard: now, next, later, and deliberately parked
