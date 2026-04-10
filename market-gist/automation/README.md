# Stock Analysis Automation

Automated stock analysis using Playwright browser automation.

## Setup

1. Install Python dependencies:
```bash
cd market-gist/automation
pip install -r requirements.txt
```

2. Install Playwright browsers:
```bash
playwright install chromium
```

## Usage

### Basic Analysis
```bash
python analyze_stock.py SMHL 1W
```

### Parameters
- `SYMBOL`: Stock symbol (e.g., SMHL, NABIL)
- `TIMEFRAME`: Chart timeframe (1D, 1W, 1M) - default is 1W

### Examples
```bash
# Analyze SMHL on weekly chart
python analyze_stock.py SMHL 1W

# Analyze NABIL on daily chart
python analyze_stock.py NABIL 1D

# Batch analyze a saved list
python batch_analyze.py 1W '@core_reliability'

# Run a fast truth-only shortlist scan before a browser deep-dive
python light_scan.py 1W '@controlled_expansion_v1'

# Run the deep-dive automatically from the latest shortlist
python deep_dive_shortlist.py 1W '@controlled_expansion_v1'

# Build one LLM-ready manual package with extra browser-only edge data
python manual_llm_package.py JBBL 1W

# Build the reusable setup-memory store from saved decisions/model-inputs/outcomes
python memory_store.py

# Retrieve similar historical setups for a saved symbol run
python similar_setup_retrieval.py EBL 2026-03-19 1W

# Build a case-critique bundle for one saved run
python llm_case_critique.py EBL 2026-03-19 1W

# Aggregate critique suggestions into one improvement log
python improvement_log.py

# Fast development validation on a tiny representative list
python fast_validate.py

# Fast validation on a custom list or timeframe
python fast_validate.py 1W '@expanded_reliability'

# Run the full reliability cycle for a saved list
python run_reliability_cycle.py 1W '@core_reliability'

# Check which symbols in a list have sector mappings
python symbol_coverage.py '@core_reliability'

# Re-evaluate only pending outcomes for an existing run
python reevaluate_pending_outcomes.py 2026-03-18 1W '@expanded_reliability'

# Build a simple follow-up queue from the latest cycle
python followup_queue.py 2026-03-18 1W

# Run the full daily follow-up in one command
python daily_followup.py 2026-03-18 1W '@expanded_reliability'

# Compare an external truth source against an existing browser run
python compare_nepse_truth.py EBL 2026-03-18 1W nepse_scraper

# Compare using the local Sharesansar historical adapter
python compare_nepse_truth.py EBL 2026-03-18 1W sharesansar_local

# Audit the local 2025 Sharesansar CSV archive before replay work
python historical_csv_audit.py 2025 '@replay_basket_v1'

# Backfill replay-safe 2025 official context like benchmarks, sub-indices, holidays, and SEBON event tables
python backfill_replay_context.py 2025

# Backfill full-year derived replay context like breadth, turnover concentration, and replay-sector summaries
python backfill_replay_derived_context.py 2025 '@replay_basket_v1'

# Backfill replay-safe 2025 corporate-action timeline for a tracked replay list
python backfill_corporate_actions_2025.py 2025 '@replay_basket_v1'

# Backfill the official NEPSE company-news archive for a tracked replay list
python backfill_nepse_company_news_2025.py 2025 '@replay_basket_v1'

# Measure whether derived market breadth context helps explain replay outcomes
python replay_market_breadth_diagnostics.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_context_v1

# Measure whether replay-sector context helps explain replay outcomes
python replay_sector_context_diagnostics.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_context_v1

# Measure whether official benchmark/sub-index context helps on a March+ replay window
python replay_official_context_diagnostics.py 2025-03-17_to_2025-03-31__replay_basket_v1__daily_truth_replay_march_context_v1

# Measure whether replay corporate-action context helps explain one replay window
python replay_event_context_diagnostics.py 2025-09-01_to_2025-09-30__replay_basket_v1__daily_truth_replay_september_promotedchampion_v1 '@replay_basket_v1'

# Aggregate event-context diagnostics across saved replay windows
python aggregate_event_context_diagnostics.py '@replay_basket_v1' 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_context_v1 2025-03-17_to_2025-03-31__replay_basket_v1__daily_truth_replay_march_context_v1

# Measure whether replay-safe liquidity/execution context helps explain one replay window
python replay_liquidity_diagnostics.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_liquiditycontext_v1

# Aggregate liquidity only inside actionable replay cases across multiple liquidity-context runs
python aggregate_liquidity_slice_diagnostics.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_liquiditycontext_v1 2025-04-01_to_2025-04-30__replay_basket_v1__daily_truth_replay_april_liquiditycontext_v1

# Aggregate multiple completed replay windows into one reusable broad validation summary
python aggregate_replay_validation.py 2025-01-01_to_2025-03-31__replay_basket_v1__daily_truth_replay_2025_q1_broadchampion_v1 2025-04-01_to_2025-04-30__replay_basket_v1__daily_truth_replay_apr_liqslicechampion_v1

# Audit official NRB macro sources before building the replay-safe macro adapter
python nrb_macro_source_audit.py

# Discover fiscal-year current macro assets (xlsx/pdf) before parsing
python nrb_current_macro_discovery.py 2081-82

# Build raw replay-safe NRB macro monthly rows for a Gregorian year
python backfill_nrb_macro_context.py 2025

# Study how after-close failure labels drift across discovery and untouched validation periods
python replay_after_close_label_drift_study.py

# Compare earlier commercial-bank upside-gap cases against July 2025 bank downside damage
python commercial_bank_after_close_regime_drift_study.py '@replay_basket_v1'

# Study whether SANIMA was the early-July bank leader and whether that leadership later turned into exhaustion
python july_2025_bank_leadership_trajectory_study.py

# Audit whether NEPSE company-news attachments actually add usable event-timing fields
python event_timing_source_gap_audit.py

# OCR feasibility pass for timing-heavy NEPSE notices
automation\\.venv_ocr\\Scripts\\python event_attachment_ocr_feasibility.py

# OCR enrichment prototype for timing-heavy NEPSE notices
automation\\.venv_ocr\\Scripts\\python event_attachment_ocr_enrichment.py --year 2025 --run-label replay_basket_v1 --max-per-event-type 3

# Normalize OCR-derived BS timing lines into Gregorian hint dates
automation\\.venv_ocr\\Scripts\\python event_bs_date_normalization_study.py --year 2025 --run-label replay_basket_v1

# Run the full program-level safe cycle across both the frozen risk engine and the guarded entry lane
python run_system_program_cycle.py

# Run only the short top-level summary output
python run_system_program_cycle.py --summary-only

# Force only the frozen risk-engine lane
python run_system_program_cycle.py --force-monitoring

# Force only the guarded entry lane
python run_system_program_cycle.py --force-entry

# Force both the risk-engine cycle and the entry-lane cycle even if freshness says no
python run_system_program_cycle.py --force-all

# Run the safe next-open entry lane cycle
# If the buy-side monitor source is newer than the entry dataset, this now rebuilds the dataset first
python run_entry_next_open_cycle.py

# Force a full next-open entry refresh even if freshness says no
python run_entry_next_open_cycle.py --force-refresh

# Check whether future exact-texture evidence has appeared for the current best next-open candidate
python entry_next_open_exact_texture_monitor.py

# Check whether future months contain the broader target slice even when the exact texture is absent
python entry_next_open_future_coverage_report.py

# Explain why future commercial-bank rows miss the exact next-open texture
python entry_next_open_future_near_miss_report.py

# Get the explicit current branch decision for the next-open entry lane
python entry_next_open_decision_gate.py
```

PowerShell note:

- quote list names that start with `@`, like `'@replay_basket_v1'`, so they are passed to Python correctly

## Output

The script generates:

### Raw Evidence Files
- `data/raw/screenshots/` - Chart screenshots
- `data/raw/snapshots/` - Page snapshots
- `data/raw/tables/` - Extracted data JSON
  This now includes external truth bundles and browser-vs-truth comparison records when a truth provider is available.

### Normalized Records
- `data/normalized/sessions/` - Session metadata
- `data/normalized/market/` - Market context
- `data/normalized/sectors/` - Sector data
- `data/normalized/stocks/` - Stock chart data
- `data/normalized/indicators/` - Technical indicators
- `data/normalized/relative_strength/` - RS analysis
- `data/normalized/decisions/` - Trading decisions
- `data/normalized/events/` - Corporate events
- `data/normalized/broker_flow/` - Broker flow data

### Feature Scores
- `data/features/setup_scores/` - Setup quality scores

## Configuration

Edit `config.py` to customize:
- Browser settings (headless mode, timeouts)
- Indicator configuration
- Scoring rules
- Decision thresholds

Maintain reusable symbols in `symbol_lists.json`.

Current saved lists:
- `@dev_fast` for quick development checks
- `@event_validated` for symbols with confirmed official-event coverage
- `@controlled_expansion_v1` for the next four liquid, low-risk additions
- `@core_reliability` for the smallest reliability cycle
- `@expanded_reliability` for the broader tracked batch
 - `@replay_basket_v1` for a balanced February replay basket across commercial banks, development banks, and hydropower
Maintain symbol-to-sector coverage in `sector_map.json`.
Maintain replay-only sector grouping in `replay_sector_groups.json` so historical replay can use broader sector buckets without changing the live browser sector map.
Use `symbol_coverage.py` for live browser-sector readiness and `replay_symbol_coverage.py` for replay-sector readiness.

Validation artifacts are now label-scoped, for example:
- `2026-03-19__1W__dev_fast__batch_validation.json`
- `2026-03-19__1W__event_validated__batch_validation.json`
- `2026-03-19__1W__controlled_expansion_v1__light_scan.json`

This keeps fast runs and broader batches from overwriting each other.

Recommended fast workflow:
1. Run `light_scan.py` on a larger list to produce a shortlist from the truth provider only.
2. Run `deep_dive_shortlist.py` to launch the slower browser deep-dive only on shortlisted symbols.

This keeps development and iteration much faster than running a full browser batch for every symbol.

The grouped shortlist deep-dive writes a labeled batch summary such as:
- `latest__1W__expanded_reliability__shortlist__batch_validation.json`

The LLM-ready manual package flow writes:
- `data/symbols/<SYMBOL>/<DATE>/<DATE>__<SYMBOL>__<TIMEFRAME>__manual_package.md`
- `data/symbols/<SYMBOL>/<DATE>/raw/tables/<DATE>__<SYMBOL>__<TIMEFRAME>__manual_package.json`

That package uses the separate browser-edge layer to add slower portal-only context such as:
- floorsheet summary
- last 15-minute trades
- broker holdings (weekly/monthly)
- broker holding changes
- compact broker-edge summary
- market session / next tradable session context
- similar historical setup summary when the memory store is available
- replay-derived family guidance as context-only caution/support

The memory layer writes:
- `data/validation/YYYY-MM-DD__setup_memory_store_v1.json`
- `data/validation/latest__setup_memory_store_v1.json`

Per-run similar-setup retrieval writes:
- `data/symbols/<SYMBOL>/<DATE>/raw/tables/<DATE>__<SYMBOL>__<TIMEFRAME>__similar_setups.json`

The critique layer writes:
- `data/symbols/<SYMBOL>/<DATE>/features/case_critiques/<DATE>__<SYMBOL>__<TIMEFRAME>__case_critique_v1.json`
- `data/symbols/<SYMBOL>/<DATE>/features/case_critiques/<DATE>__<SYMBOL>__<TIMEFRAME>__case_critique_v1.md`

The improvement layer writes:
- `data/validation/improvement_proposals/YYYY-MM-DD__improvement_log_v1.json`
- `data/validation/improvement_proposals/latest__improvement_log_v1.json`

The combined learning layer writes:
- `data/validation/learning_reviews/YYYY-MM-DD__combined_learning_summary_v1.json`
- `data/validation/learning_reviews/latest__combined_learning_summary_v1.json`

The replay layer writes under its own namespace:
- `data/replays/<REPLAY_ID>/sessions/<DATE>/<SYMBOL>/raw/...`
- `data/replays/<REPLAY_ID>/sessions/<DATE>/<SYMBOL>/normalized/...`
- `data/replays/<REPLAY_ID>/sessions/<DATE>/<SYMBOL>/derived/...`
- `data/replays/<REPLAY_ID>/sessions/<DATE>/<SYMBOL>/comparisons/...`
- `data/replays/<REPLAY_ID>/summaries/YYYY-MM-DD__replay_summary_v1.json`
- `data/replays/<REPLAY_ID>/summaries/latest__replay_summary_v1.json`

Replay commands:
- `python replay_symbol_coverage.py '@replay_basket_v1'`
- `python historical_csv_audit.py 2025 '@replay_basket_v1'`
- `python replay_calendar.py 2025-12-21 2025-12-31`
- `python replay_case_builder.py EBL 2025-12-31`
- `python walk_forward_replay.py 2025-12-21 2025-12-31 EBL JBBL`
- `python walk_forward_replay.py 2025-02-01 2025-02-28 '@replay_basket_v1'`
- `python replay_case_critique.py 2025-12-21_to_2025-12-31__EBL__JBBL__daily_truth_replay_v1`
- `python replay_review_summary.py 2025-12-21_to_2025-12-31__EBL__JBBL__daily_truth_replay_v1`
- `python replay_supportive_diagnostics.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_regime_v1`
- `python replay_behavior_profile.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_regime_v1`
- `python replay_family_guidance.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_regime_v1`
- `python replay_validated_sector_guidance.py 2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_context_v1 2025-04-01_to_2025-04-30__replay_basket_v1__daily_truth_replay_april_context_v1`
- `python replay_champion_challenger_compare.py 2025-05-01_to_2025-05-31__replay_basket_v1__daily_truth_replay_may_champion_v1 2025-05-01_to_2025-05-31__replay_basket_v1__daily_truth_replay_may_sectorsoft_v1`
- `python replay_challenger_validation_summary.py <COMPARE_JSON> <COMPARE_JSON> <COMPARE_JSON>`
- `python replay_calibration_report.py REPLAY_ID [REPLAY_ID ...]`
- `python replay_confidence_remap.py`
- `python aggregate_replay_validation.py REPLAY_ID [REPLAY_ID ...]`
- `python aggregate_hostile_window_monitor.py REPLAY_ID [REPLAY_ID ...]`
- `python nrb_macro_source_audit.py`
- `python nrb_current_macro_discovery.py FY_TOKEN`
- `python backfill_nrb_macro_context.py YEAR`
- `python replay_macro_context_diagnostics.py REPLAY_ID`
- `python aggregate_macro_context_diagnostics.py REPLAY_ID [REPLAY_ID ...]`
- `python aggregate_replay_context_review.py REPLAY_ID [REPLAY_ID ...]`
- `python combined_learning_summary.py`

Important replay note:
- the first replay slice is intentionally truth-only and uses `sharesansar_local`
- it excludes Friday/Saturday sessions to match Nepal trading weekdays
- it is separate from the live browser pipeline and does not overwrite live symbol runs
- the default replay champion now includes the validated `fragility-only` caution:
  - validated fragile sector families can demote borderline `watch_only` setups to `avoid`
  - validated supportive families do **not** auto-promote setups
- the default replay champion now also includes the validated sector-aware calendar-confidence caution:
  - active only in `fiscal_year_end_window` and `post_fiscal_results_window`
  - requires `matched_but_stale` event context
  - requires `strongly_overconfident` calibrated actionable confidence
  - allowed sectors:
    - `COMMERCIAL BANKS`
    - `DEVELOPMENT BANKS`
  - blocked sector:
    - `HYDROPOWER`
  - action change stays narrow:
    - `buy -> watch_only`
    - `watch_only -> avoid`
- an optional slice-specific liquidity challenger also exists in `walk_forward_replay.py`:
  - enable with `use_validated_liquidity_guidance=True`
  - it is currently research-only and is **not** promoted into the champion
- yearly archive audits are saved under:
  - `data/validation/historical_data_audits/YYYY__sharesansar_local__archive_audit_v1.json`
  - `data/validation/historical_data_audits/latest__YYYY__sharesansar_local__archive_audit_v1.json`
- yearly replay-context backfills are saved under:
  - `data/validation/historical_context_backfills/YYYY__official_replay_context_backfill_v1.json`
  - `data/validation/historical_context_backfills/latest__YYYY__official_replay_context_backfill_v1.json`
  - `data/validation/historical_context_backfills/YYYY__<LIST>__derived_replay_context_backfill_v1.json`
  - `data/validation/historical_context_backfills/latest__YYYY__<LIST>__derived_replay_context_backfill_v1.json`
- `data/validation/historical_context_backfills/YYYY__<LIST>__corporate_action_timeline_v1.json`
- `data/validation/historical_context_backfills/latest__YYYY__<LIST>__corporate_action_timeline_v1.json`
  These timeline files can now include company-level right-share rows extracted from official SEBON summary PDFs.
  They can also include symbol-tagged rows from the official NEPSE company-news archive.
  Important caution:
  - they currently use the official publication date as the replay-safe `event_date`
  - the NEPSE company-news archive is now the preferred historical disclosure source for replay-basket coverage
  - separate company-news backfill artifacts are saved under:
    - `data/validation/historical_context_backfills/YYYY__<LIST>__nepse_company_news_backfill_v1.json`
    - `data/validation/historical_context_backfills/latest__YYYY__<LIST>__nepse_company_news_backfill_v1.json`

## Architecture

- `analyze_stock.py` - Main automation script
- `browser_actions.py` - Playwright browser automation
- `browser_edge_features.py` - Optional browser-only edge extraction for LLM packages
- `memory_store.py` - Builds the reusable historical setup memory store
- `similar_setup_retrieval.py` - Finds similar historical setups for a current run
- `llm_case_critique.py` - Builds a reviewable critique bundle for one finished case
- `improvement_log.py` - Aggregates critique risks and proposed improvements
- `combined_learning_summary.py` - Combines live and replay lessons into one ranked review layer
- `replay_calendar.py` - Builds a Nepal-session replay calendar from local historical data
- `historical_csv_audit.py` - Audits yearly Sharesansar CSV archive coverage, schema quality, and tracked-symbol availability
- `backfill_replay_context.py` - Backfills replay-safe official context layers for one historical year
- `backfill_replay_derived_context.py` - Derives full-year replay-safe market breadth and replay-sector context from the local CSV archive
- `corporate_action_pdf_extractors.py` - Extracts company-level right-share rows from official summary PDFs
- `corporate_action_timeline.py` - Normalizes replay-safe corporate-action records from official tables and enriched PDF rows
- `nepse_company_news_archive.py` - Builds replay-safe historical disclosure records from the official NEPSE company-news archive
- `backfill_corporate_actions_2025.py` - Builds a replay-safe corporate-action timeline for a tracked historical universe
- `replay_backfill_context.py` - Loads official and derived historical backfills into replay cases as context-only evidence
- `replay_corporate_action_context.py` - Loads symbol/date-scoped corporate-action context into replay cases as context-only evidence
- `replay_case_builder.py` - Freezes one historical truth-only case and decision
- `replay_cross_section.py` - Adds basket-relative and sector-relative replay context
- `replay_regime_context.py` - Adds replay-only market-proxy and sector-proxy regime context
- `walk_forward_replay.py` - Runs point-in-time replay and stores comparison artifacts
- `replay_case_critique.py` - Builds replay-specific critique records from comparison artifacts
- `replay_review_summary.py` - Aggregates replay critiques into recurring learning signals
- `replay_supportive_diagnostics.py` - Compares strong vs weak cases inside the replay's most supportive regime slice
- `replay_behavior_profile.py` - Profiles supportive-case behavior by symbol and sector family with sample-size awareness
- `replay_family_guidance.py` - Turns replay behavior evidence into context-only symbol and sector caution/support guidance
- `replay_validated_sector_guidance.py` - Combines repeated month-level sector/alignment evidence into a validated replay guidance bundle
- `replay_champion_challenger_compare.py` - Compares one challenger replay against the frozen champion and saves a reusable evidence summary
- `replay_challenger_validation_summary.py` - Aggregates multiple month-level challenger comparisons into one trust summary
- `replay_calibration_report.py` - Builds an action-aware replay calibration summary from frozen champion replay runs
- `replay_confidence_remap.py` - Builds a separate action-aware confidence remap bundle from replay calibration
- calibrated confidence is now surfaced in replay summaries, replay critiques, and replay review summary records
- current guarded champion rules now include:
  - fragile-sector caution
  - sector-aware calendar-confidence caution
  - narrow hostile-window commercial-bank watch-only caution
- `replay_market_breadth_diagnostics.py` - Measures whether derived market breadth context explains replay outcomes
- `replay_sector_context_diagnostics.py` - Measures whether replay-sector context explains replay outcomes
- `replay_official_context_diagnostics.py` - Measures whether official benchmark/sub-index context explains replay outcomes on March+ windows
- `replay_event_context_diagnostics.py` - Measures whether replay-safe corporate-action context explains outcomes in one replay window
- `aggregate_event_context_diagnostics.py` - Aggregates event-context diagnostics across multiple saved replay windows
- `replay_liquidity_upgrade.py` - Derives replay-safe liquidity and execution metrics from point-in-time local history
- `replay_liquidity_diagnostics.py` - Measures whether replay-safe liquidity/execution context explains outcomes in one replay window
- `aggregate_liquidity_slice_diagnostics.py` - Measures liquidity only inside actionable replay cases across multiple replay windows
- `replay_macro_context_diagnostics.py` - Measures whether replay-safe macro and calendar context explains outcomes in one replay window
- `aggregate_macro_context_diagnostics.py` - Aggregates macro/context diagnostics across multiple replay windows for month-level review
- `aggregate_replay_context_review.py` - Combines sector, event, liquidity, calendar, and calibrated-confidence context into repeated replay success/failure slices
- `aggregate_replay_validation.py` - Aggregates completed replay windows into one reusable year-scale validation summary
- `aggregate_hostile_window_monitor.py` - Focuses only on hostile fiscal/results windows and shows where the frozen champion is still triggering or drifting
- `derive_hostile_watchlist.py` - Converts the hostile monitor into a reusable warning/watch baseline for future hostile-window refreshes
- `monitoring_watchlist_checkpoint.py` - Combines the latest hostile and buy-side watchlists into one compact monitoring checkpoint
- `hostile_window_buy_failure_study.py` - Compares the remaining hostile-window `buy` cases against the few winners to see whether a narrow buy-failure texture is emerging
- `q3_regime_gap_study.py` - Compares why the promoted hostile-window caution behaved less cleanly in Q3 2024 than Q3 2025
- `bank_hostile_window_gap_study.py` - Compares clipped 2024 bank hostile-window setups against 2025 improved bank setups
- `bank_elite_setup_separability_study.py` - Tests whether elite hostile-window bank setups are separable from middling ones using simple replay-safe features
- `bank_texture_signature_validation.py` - Validates the hostile-window bank texture signature on other active bank hostile windows outside the original Q3 study
- `event_timing_refinement_study.py` - Studies whether replay stale-event buckets should split by effective timing or whether source/timeline quality is the main blocker
- `replay_cost_realism_study.py` - Re-scores frozen actionable replay cases with next-open entry realism and Nepal equity cost scenarios to separate paper wins from realistically tradable wins
- `replay_next_open_tradability_study.py` - Studies which decision-time features separate target-too-close paper wins from after-close setups that are still tradable at the next open
  - supports `--output-id` for dedicated study variants
  - supports `--sector-name` to constrain simulations before future-bar loading
- `replay_buy_side_scorecard.py` - Measures whether the current champion's actionable and strict-buy side survives next-open realism and honest confidence calibration
- `aggregate_buy_side_pattern_monitor.py` - Ranks repeated realistic winner slices and repeated failure slices across saved actionable replay windows so new buy-side branches only open when a pattern truly repeats
- `derive_buy_side_watchlist.py` - Converts the aggregate buy-side monitor into a reusable watchlist baseline of candidate-positive slices and warning slices for future replay refreshes
- `monitor_watchlist_diff.py` - Compares the current hostile/buy monitors against the saved watchlist baselines and flags stable, worsening, missing, or emergent slices before new research opens
- `refresh_monitoring_stack.py` - Runs the hostile monitor, buy-side monitor, watchlists, combined checkpoint, and baseline diff in the correct sequence for future frozen-monitoring refreshes
- `refresh_monitoring_stack.py --stage core` - Rebuilds the heavy monitor layer only
- `refresh_monitoring_stack.py --stage tail` - Rebuilds the downstream decision bundle from existing monitor outputs
- `refresh_monitoring_stack.py --stage all` - Runs both in sequence
- `monitoring_refresh_freshness_gate.py` - Checks whether any replay input is newer than the current core build before rerunning the heavy monitoring layer
- `monitoring_operating_state.py` - Combines freshness, decision, readiness, and priority focuses into one top-level “what now” artifact
- `monitoring_replay_coverage_ledger.py` - Shows which replay windows and months are already covered by the hostile monitor, the buy-side monitor, or both
- `monitoring_candidate_replay_gap_report.py` - Scans replay directories for monthly final-champion candidates that are not yet covered by the monitoring stack
- `monitoring_gap_triage.py` - Splits uncovered monitoring candidate gaps into “include now” versus “needs current-champion rerun first”
- `monitoring_cycle_packet.py` - Builds one readable cycle packet that combines the current monitoring answer and next action into a single handoff file
- `monitoring_executive_status.py` - Builds one plain executive summary of where the system stands, what is working, what is blocked, and what the next refresh must prove
- `monitoring_artifact_consistency_check.py` - Verifies that the current monitoring packet, operating state, decision gate, and priorities still agree with each other
- `run_monitoring_cycle.py` - Safe monitoring entrypoint that checks freshness first and only runs the heavy staged refresh when justified
- `run_monitoring_cycle.ps1` - PowerShell wrapper that finds a usable Python executable and runs the monitoring cycle without manual interpreter guessing
- `monitoring_decision_gate.py` - Reads the latest monitoring diff and returns the explicit next-step decision: keep frozen, open hostile-side research, or open buy-side research
- `monitoring_cycle_summary.py` - Condenses the latest checkpoint, diff, and decision gate into one short monitoring-cycle summary for fast review
- `system_reliability_readiness_scorecard.py` - Measures which trust/readiness thresholds are currently passed and what still blocks higher-trust overall prediction and buy-side prediction
- `buy_side_branch_readiness_queue.py` - Ranks the current positive buy-side watch slices by how many clean new successes they still need before they are close to a buy-side research trigger
- `branch_priority_queue.py` - Combines the buy-side readiness queue and hostile watchlist into one unified next-refresh priority artifact
- `priority_slice_focus_pack.py` - Converts the current top buy-side and hostile-side priorities into a concrete next-refresh inspection checklist
- `priority_slice_drilldown.py` - Breaks the current top buy-side and hostile-side priorities down by symbol, month, and recent case texture so the next refresh can judge slice quality, not just slice size
- `next_refresh_trigger_sheet.py` - Converts the current focus pack, drilldown, and readiness state into exact pass/fail conditions for what the next refresh must prove before research opens
- `build_entry_research_dataset.py` - Builds the first reusable execution-aware Entry Research v1 dataset from the monitored actionable replay windows, including concentration tracking and canonical executable labels
- `backfill_replay_liquidity_context.py` - Backfills missing replay-safe liquidity context into existing frozen replay cases without changing any replay decision
- `entry_baseline_ranking_study.py` - Tests simple top-1 ranking baselines on the execution-aware entry dataset to see whether any low-complexity entry candidate family shows real life before deeper modeling
- `entry_relative_feature_study.py` - Tests session-relative and sector-relative leadership ranks on the entry dataset to see whether relative strength beats absolute feature ordering
- `entry_cross_sectional_context_study.py` - Tests richer replay cross-sectional context like `leadership_label`, `relative_return_vs_sector`, and `relative_score_vs_basket` as a separate entry baseline family
- `entry_liquidity_execution_context_study.py` - Tests replay-safe liquidity, gap-stability, and weekend-gap-carry features as a genuinely different Entry Research v2 family on the enterable next-open set
- `entry_thursday_weekend_gap_drag_study.py` - Tests whether Thursday / weekend-gap carry creates a real negative entry branch in bank sectors or only a broad descriptive friction
- `entry_market_regime_context_study.py` - Tests whether market breadth, market median move, and official sector/benchmark context create a reusable execution-aware entry family or only descriptive regime effects
- `entry_next_open_decision_study.py` - Tests whether moving the actual entry decision point to the next tradable open materially improves executable entry quality before any ranking/filter logic is added
- `entry_next_open_slice_monitor.py` - Finds repeated positive and negative pockets inside the next-open enterable universe so the entry track can study real next-open regimes instead of one-off examples
- `entry_next_open_branch_readiness_queue.py` - Ranks the repeated next-open positive slices by how research-ready they are, while penalizing single-month and symbol-concentrated pockets
- `entry_next_open_commercial_bank_candidate_study.py` - Studies the first repeated commercial-bank next-open candidate slice and tests whether any simple decision-time texture survives the later month without claiming a rule too early
- `entry_next_open_commercial_bank_texture_validation.py` - Validates the strongest commercial-bank next-open texture on the exact slice, neighboring same-structure rows, and nearest future probe so we can tell whether it is weak or simply sample-limited
- `entry_next_open_commercial_bank_attribution_study.py` - Explains whether the guarded commercial-bank next-open candidate widens cleanly beyond the exact texture or stays symbol-dependent inside the residual broadening pocket
- `entry_next_open_trigger_sheet.py` - Converts the best current next-open candidate into explicit future-evidence gates so the entry track knows exactly what must happen before trust increases
- `entry_next_open_executive_status.py` - Builds one short executive summary of the current next-open entry lane, the best candidate, the blockers, and what future data must prove
- `refresh_entry_next_open_stack.py` - Runs the next-open entry studies in the correct order and refreshes the full current entry-lane bundle in one command
- `entry_next_open_cycle_packet.py` - Builds one readable handoff packet for the current next-open entry lane so the shortest current answer lives in one file
- `refresh_monitoring_stack.py` now also rebuilds the priority focus pack so the full frozen-monitoring cycle ends with an explicit inspection checklist
- `refresh_monitoring_stack.py` now also rebuilds the priority slice drilldown so the full frozen-monitoring cycle includes symbol/month quality for the two top watched slices
- `refresh_monitoring_stack.py` now also rebuilds the next refresh trigger sheet so each cycle ends with explicit evidence gates for the next one
- `refresh_monitoring_stack.py` now also rebuilds the readiness scorecard so each refresh includes the current trust/readiness view
- `system_program_status.py` - Builds one unified whole-project status across the frozen risk engine and the guarded entry lane
- `system_program_status_consistency_check.py` - Verifies that the unified whole-project status matches the risk and entry handoff bundles
- `run_system_program_cycle.py` - Safe top-level entrypoint that runs both lanes and refreshes the unified whole-project status
- `run_system_program_cycle.py --summary-only` - Prints only the concise whole-project summary instead of the full nested result
- `run_system_program_cycle.ps1` - PowerShell wrapper that finds a usable Python executable and runs the whole-project cycle in one command
- `system_program_executive_status.py` - Builds the shortest whole-project plain-English summary of where the project stands, what is working, and what to do now
- `system_program_refresh_freshness_gate.py` - Builds one explicit whole-project freshness gate across the frozen risk lane and guarded entry lane
- `system_program_operating_state.py` - Builds the whole-project operating-state artifact that answers whether anything actually needs rerunning
- `system_program_decision_gate.py` - Converts the whole-project state into one explicit current decision such as `keep_operating` or rerun-only decisions
- `system_program_cycle_packet.py` - Builds one readable whole-project packet that says what to do now and why
- `system_program_artifact_recency_check.py` - Verifies that the whole-project top-level artifacts were rebuilt close enough together to trust the current handoff bundle
- `system_program_final_gate.py` - Builds the final post-recency whole-project verdict so the top-level run ends with one safe decision to trust
- current top-level reading order is:
  - `latest__system_program_executive_status_v1.md`
  - `latest__system_program_refresh_freshness_gate_v1.md`
  - `latest__system_program_artifact_recency_check_v1.md`
  - `latest__system_program_final_gate_v1.md`
  - `latest__system_program_decision_gate_v1.md`
  - `latest__system_program_cycle_packet_v1.md`
- `artifact_io.py` - Shared atomic-write helpers for generated JSON and markdown artifacts in the current operating stack
- `commercial_bank_nonhostile_watch_success_study.py` - Tests whether the strongest positive non-hostile commercial-bank watch-only slice can be separated cleanly enough to justify a future buy-side branch
- `watch_only_winner_texture_study.py` - Compares realistic watch-only winners against fragile watch-only cases to see whether any future buy-promotion texture exists
- `hydropower_watch_next_open_policy_study.py` - Tests research-only next-open/live-entry policy candidates for hydropower watch-only setups across discovery, validation, and out-of-regime probe months
- `hydropower_watch_next_open_leakage_refinement.py` - Tests whether a minimum open-RR floor removes the known hydropower next-open leakage without breaking the earlier positive continuation subset
- `hydropower_watch_next_open_broader_validation.py` - Runs broader untouched non-hostile validation for the refined hydropower next-open candidate to see whether it generalizes beyond the original continuation regime
- `replay_after_close_entry_policy_study.py` - Validates research-only target-distance and RR allow/block policies on discovery versus untouched replay months before any challenger is considered
- `replay_slice_aware_after_close_policy_study.py` - Tests whether target-distance and RR policy candidates become stable inside narrower sector, momentum, and participation slices
- `replay_after_close_label_drift_study.py` - Explains whether after-close failure modes stay stable or drift across periods inside the strongest actionable slices
- `commercial_bank_after_close_regime_drift_study.py` - Compares earlier commercial-bank upside-gap paper wins against July 2025 bank downside damage and July survivors
- `july_2025_bank_leadership_trajectory_study.py` - Studies whether early bank leadership later turned into exhaustion inside July 2025 commercial-bank setups
- `bank_exhaustion_exception_study.py` - Explains the `2024-07` hostile-window commercial-bank exception slice and searches for replay-safe preservation signatures
- `bank_exhaustion_preservation_signature_validation.py` - Validates those `2024-07` preservation signatures on other hostile commercial-bank windows before any challenger refinement
- `bank_leadership_exhaustion_signature_validation.py` - Derives a July 2025 commercial-bank exhaustion signature and validates it on non-July bank history before any new rule is considered
  - supports `--source-path` and `--output-id` for dedicated hostile-window validation variants
- `nrb_macro_source_audit.py` - Audits official NRB macro sources before building a replay-safe macro adapter
- `nrb_current_macro_discovery.py` - Discovers fiscal-year NRB current macro month windows and resolves their xlsx/pdf assets
- `backfill_nrb_macro_context.py` - Builds raw monthly NRB macro rows from discovered current macro table assets
- `replay_macro_calendar_context.py` - Loads the latest replay-safe macro snapshot and descriptive calendar flags for a replay session date
- `data_sources/` - Pluggable external truth providers owned by this project
- `data_extractor.py` - Data extraction and parsing
- `analyzer.py` - Scoring and decision logic
- `file_generator.py` - JSON file generation
- `config.py` - Configuration settings

## External Provider Layer

External repos should not be merged into the core analysis code.

The project now treats outside data sources as pluggable adapters:

- this project owns the provider interface and registry
- external repos stay outside the main codebase
- each provider is wrapped behind a thin adapter in `data_sources/`

Current provider:

- `nepse_scraper` via `data_sources/nepse_scraper_source.py`
- `sharesansar_local` via `data_sources/sharesansar_csv_source.py`

`sharesansar_local` is intentionally a separate file-backed historical adapter.
It is useful for offline history/backfill/calibration work and should not be
treated as a guaranteed live current-truth replacement.

This lets us:

- compare browser truth vs external truth
- swap providers later
- add more providers without rewriting the pipeline

## Troubleshooting

### Browser not found
```bash
playwright install chromium
```

### Timeout errors
Increase `BROWSER_TIMEOUT` in `config.py`

### Element not found
The script may need adjustments if NEPSE Alpha UI changes

## Limitations

- Data extraction is partially automated (some values are placeholders)
- Pattern recognition for support/resistance is simplified
- Broker flow data requires login (not automated)
- OCR not implemented for text extraction from charts

## Future Improvements

- [ ] Full OCR integration for data extraction
- [ ] Advanced pattern recognition
- [ ] Historical data comparison
- [ ] Multi-symbol batch processing
- [ ] Email/Slack notifications
- [ ] Database storage
- [ ] REST API wrapper
