"""
LLM Replay Bootstrap: uses existing replay datasets to build initial calibration.

Loads frozen cases + comparison records from replay directories, converts them
to context packages, and either saves prompts (--dry-run) or calls the API
for LLM predictions. Scores against known outcomes and builds calibration.

Usage:
    # Dry-run: save prompts for manual review in Claude Code
    python llm_replay_bootstrap.py REPLAY_ID --dry-run

    # Sample 50 cases and get LLM predictions via API
    python llm_replay_bootstrap.py REPLAY_ID --sample 50

    # Multiple replay IDs
    python llm_replay_bootstrap.py REPLAY_ID_1 REPLAY_ID_2 --sample 100
"""
import json
import os
import random
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from artifact_io import save_json_atomic, save_text_atomic
from config import BASE_DIR, VALIDATION_DIR, REPLAYS_DIR, load_json_file as _load_json


def load_json(path):
    return _load_json(path, {})
from llm_predict import (
    render_prompt,
    format_calibration_block,
    build_macro_context_block,
    load_calibration,
    wrap_prediction,
    validate_prediction,
)
from llm_score import DEFAULT_MIN_BARS, score_prediction


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PREDICTIONS_DIR = os.path.join(BASE_DIR, "data", "predictions")
PREDICTIONS_REPLAY_DIR = os.path.join(PREDICTIONS_DIR, "replay")
REPLAY_SCORES_DIR = os.path.join(PREDICTIONS_DIR, "replay_scores")
CALIBRATION_DIR = os.path.join(VALIDATION_DIR, "llm_calibration")

# Sector mapping
try:
    with open(os.path.join(os.path.dirname(__file__), "sector_map.json"), "r", encoding="utf-8") as f:
        SECTOR_MAP = json.load(f)
except Exception:
    SECTOR_MAP = {}


# ---------------------------------------------------------------------------
# Replay data loading
# ---------------------------------------------------------------------------
def load_replay_cases(replay_id):
    """Load all frozen cases + comparison records from a replay directory."""
    replay_dir = os.path.join(REPLAYS_DIR, replay_id)
    if not os.path.isdir(replay_dir):
        print(f"ERROR: Replay directory not found: {replay_dir}")
        return []

    sessions_dir = os.path.join(replay_dir, "sessions")
    if not os.path.isdir(sessions_dir):
        print(f"ERROR: No sessions directory in {replay_dir}")
        return []

    cases = []
    for date_dir in sorted(os.listdir(sessions_dir)):
        date_path = os.path.join(sessions_dir, date_dir)
        if not os.path.isdir(date_path):
            continue

        for symbol_dir in sorted(os.listdir(date_path)):
            symbol_path = os.path.join(date_path, symbol_dir)
            if not os.path.isdir(symbol_path):
                continue

            # Find frozen case
            norm_dir = os.path.join(symbol_path, "normalized")
            frozen_files = []
            if os.path.isdir(norm_dir):
                frozen_files = [f for f in os.listdir(norm_dir) if "frozen_case" in f and f.endswith(".json")]

            # Find comparison
            comp_dir = os.path.join(symbol_path, "comparisons")
            comp_files = []
            if os.path.isdir(comp_dir):
                comp_files = [f for f in os.listdir(comp_dir) if "comparison" in f and f.endswith(".json")]

            if frozen_files and comp_files:
                frozen = load_json(os.path.join(norm_dir, frozen_files[0]))
                comparison = load_json(os.path.join(comp_dir, comp_files[0]))
                cases.append({
                    "replay_id": replay_id,
                    "session_date": date_dir,
                    "symbol": symbol_dir,
                    "frozen_case": frozen,
                    "comparison": comparison,
                })

    return cases


def stratified_sample(cases, n):
    """Sample N cases stratified by action + sector."""
    if len(cases) <= n:
        return cases

    # Group by action + sector
    groups = {}
    for case in cases:
        action = case["comparison"].get("prediction", {}).get("action", "unknown")
        sector = SECTOR_MAP.get(case["symbol"], "UNKNOWN")
        key = f"{action}__{sector}"
        if key not in groups:
            groups[key] = []
        groups[key].append(case)

    # Sample proportionally from each group
    sampled = []
    per_group = max(1, n // len(groups)) if groups else n
    remaining = n

    for key, group in groups.items():
        take = min(per_group, len(group), remaining)
        sampled.extend(random.sample(group, take))
        remaining -= take

    # Fill remaining from any group
    all_unsampled = [c for c in cases if c not in sampled]
    if remaining > 0 and all_unsampled:
        sampled.extend(random.sample(all_unsampled, min(remaining, len(all_unsampled))))

    return sampled


# ---------------------------------------------------------------------------
# Context building from frozen cases
# ---------------------------------------------------------------------------
def frozen_case_to_context_markdown(frozen_case, comparison):
    """Convert a replay frozen case into context markdown for LLM prediction."""
    metrics = frozen_case.get("metrics", {})
    latest = frozen_case.get("latest_row", {})
    symbol = frozen_case.get("symbol", "?")
    session_date = frozen_case.get("session_date", "?")
    sector = SECTOR_MAP.get(symbol, "UNKNOWN")

    lines = [
        f"# Market Context Package: {symbol} (Replay Case)",
        f"Date: {session_date}",
        f"Sector: {sector}",
        f"Source: Historical replay (truth-layer data only, no browser)",
        "",
        "## 1. Stock Data",
        f"- Symbol: {symbol}",
        f"- Close price: {metrics.get('close_price', 'unknown')}",
        f"- 1-day return: {metrics.get('return_1d_pct', 'unknown')}%",
        f"- 5-day return: {metrics.get('return_5d_pct', 'unknown')}%",
        f"- 20-day return: {metrics.get('return_20d_pct', 'unknown')}%",
        f"- SMA 10: {metrics.get('sma10', 'unknown')}",
        f"- SMA 20: {metrics.get('sma20', 'unknown')}",
        f"- SMA 50: {metrics.get('sma50', 'unknown')}",
        f"- Price vs SMA20: {'above' if metrics.get('close_price', 0) > (metrics.get('sma20') or 0) else 'below'}",
        f"- Price vs SMA50: {'above' if metrics.get('close_price', 0) > (metrics.get('sma50') or 0) else 'below'}",
        "",
        "## 2. Trend & Structure",
        f"- Trend label: {metrics.get('trend_label', 'unknown')}",
        f"- Close position in 20d range: {metrics.get('close_position_20d', 'unknown')}",
        f"- Close position in 60d range: {metrics.get('close_position_60d', 'unknown')}",
        f"- 20-day resistance: {metrics.get('resistance_20d', 'unknown')}",
        f"- 10-day support: {metrics.get('support_10d', 'unknown')}",
        f"- 60-day resistance: {metrics.get('resistance_60d', 'unknown')}",
        f"- 60-day support: {metrics.get('support_60d', 'unknown')}",
        "",
        "## 3. Liquidity",
        f"- Liquidity label: {metrics.get('liquidity_label', 'unknown')}",
        f"- Avg traded value (5d): {metrics.get('avg_value_5d', 'unknown')}",
        f"- Avg traded value (20d): {metrics.get('avg_value_20d', 'unknown')}",
        f"- Avg trades (5d): {metrics.get('avg_trades_5d', 'unknown')}",
        f"- Avg trades (20d): {metrics.get('avg_trades_20d', 'unknown')}",
        f"- Volume ratio (5d vs 20d): {metrics.get('volume_ratio_5d', 'unknown')}",
        "",
        "## 4. Latest Bar",
        f"- Open: {latest.get('openPrice', 'unknown')}",
        f"- High: {latest.get('highPrice', 'unknown')}",
        f"- Low: {latest.get('lowPrice', 'unknown')}",
        f"- Close: {latest.get('closePrice', 'unknown')}",
        f"- Total traded value: {latest.get('totalTradedValue', 'unknown')}",
        f"- Total trades: {latest.get('totalTrades', 'unknown')}",
        f"- 52-week high: {latest.get('fiftyTwoWeekHigh', 'unknown')}",
        f"- 52-week low: {latest.get('fiftyTwoWeekLow', 'unknown')}",
        "",
        "## 5. Data Quality",
        f"- History bars available: {frozen_case.get('data_quality', {}).get('history_bar_count', 'unknown')}",
        f"- Full 20d context: {frozen_case.get('data_quality', {}).get('has_full_20d_context', 'unknown')}",
        f"- Full 60d context: {frozen_case.get('data_quality', {}).get('has_full_60d_context', 'unknown')}",
    ]

    # Add historical context if available
    hist_ctx = frozen_case.get("historical_context", {})
    if hist_ctx:
        lines.extend(["", "## 6. Historical Context"])
        regime = hist_ctx.get("regime_context", {})
        if regime:
            lines.append(f"- Market regime: {regime.get('market_regime', 'unknown')}")
            lines.append(f"- Sector regime: {regime.get('sector_regime', 'unknown')}")
            lines.append(f"- Alignment: {regime.get('alignment_label', 'unknown')}")

        calendar = hist_ctx.get("calendar_context", {})
        if calendar:
            flags = calendar.get("calendar_flags", {})
            lines.append(f"- Calendar phase: {flags.get('phase_labels', 'unknown')}")
            lines.append(f"- Hostile window: {flags.get('is_hostile_window', 'unknown')}")

        event_ctx = hist_ctx.get("event_context", {})
        if event_ctx:
            lines.append(f"- Event match: {event_ctx.get('event_status', 'unknown')}")
            lines.append(f"- Event type: {event_ctx.get('event_type', 'unknown')}")

    lines.extend([
        "",
        "## Notes",
        "- This is a replay case with truth-layer data only (no browser screenshots or broker flow).",
        "- The market, sector, and indicator data come from historical CSV records.",
        "- Your prediction will be scored against what actually happened after this date.",
    ])

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    args = sys.argv[1:]

    # Parse flags
    dry_run = "--dry-run" in args
    args = [a for a in args if a != "--dry-run"]

    sample_size = None
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] == "--sample" and i + 1 < len(args):
            sample_size = int(args[i + 1])
            i += 2
        else:
            filtered_args.append(args[i])
            i += 1

    replay_ids = filtered_args
    if not replay_ids:
        print("Usage:")
        print("  python llm_replay_bootstrap.py REPLAY_ID [REPLAY_ID ...] [--sample N] [--dry-run]")
        print()
        print("Options:")
        print("  --dry-run    Save prompts to disk only (no API calls)")
        print("  --sample N   Sample N cases (stratified by action + sector)")
        print()
        print("Available replays:")
        if os.path.isdir(REPLAYS_DIR):
            for name in sorted(os.listdir(REPLAYS_DIR))[-10:]:
                print(f"  {name}")
        sys.exit(1)

    # Load all cases
    all_cases = []
    for rid in replay_ids:
        cases = load_replay_cases(rid)
        all_cases.extend(cases)
        print(f"Loaded {len(cases)} cases from {rid}")

    if not all_cases:
        print("No cases found.")
        sys.exit(1)

    # Sample
    if sample_size and sample_size < len(all_cases):
        all_cases = stratified_sample(all_cases, sample_size)
        print(f"Sampled {len(all_cases)} cases (stratified)")

    # Load calibration (may be None on first run)
    calibration = load_calibration()
    cal_version = calibration.get("calibration_id") if calibration else None
    cal_block = format_calibration_block(calibration)

    # Process each case
    prompts_saved = 0
    predictions_stored = 0

    for case in all_cases:
        symbol = case["symbol"]
        session_date = case["session_date"]
        frozen = case["frozen_case"]
        comparison = case["comparison"]

        # Build context
        context_md = frozen_case_to_context_markdown(frozen, comparison)
        similar_block = "No similar past setups available (replay bootstrap mode)."
        macro_block = build_macro_context_block(symbol, session_date)

        # Render prompt
        prompt = render_prompt(context_md, cal_block, similar_block, macro_block)

        # Save prompt
        prompt_path = os.path.join(
            PREDICTIONS_REPLAY_DIR,
            f"{session_date}__{symbol}__1D__bootstrap_prompt.md",
        )
        save_text_atomic(prompt_path, prompt)
        prompts_saved += 1

        if dry_run:
            continue

        # API mode: call Anthropic API
        try:
            import anthropic

            client = anthropic.Anthropic()
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1500,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = response.content[0].text.strip()
            # Parse JSON from response
            if raw_text.startswith("```"):
                lines = raw_text.split("\n")
                if lines[0].startswith("```"):
                    lines = lines[1:]
                if lines and lines[-1].strip() == "```":
                    lines = lines[:-1]
                raw_text = "\n".join(lines)

            raw_prediction = json.loads(raw_text)

            # Wrap and store
            envelope = wrap_prediction(symbol, "1D", session_date, raw_prediction, cal_version, mode="api", calibration=calibration)
            pred_path = os.path.join(
                PREDICTIONS_REPLAY_DIR,
                f"{session_date}__{symbol}__1D__prediction_v1.json",
            )
            save_json_atomic(pred_path, envelope)

            # Score immediately using the same truth-backed scorer as live predictions.
            score = score_prediction(envelope, min_bars=DEFAULT_MIN_BARS, score_source="replay_bootstrap")
            if "metadata" not in score:
                score["metadata"] = {}
            score["metadata"]["replay_id"] = case["replay_id"]
            score_path = os.path.join(
                REPLAY_SCORES_DIR,
                f"{session_date}__{symbol}__1D__score_v1.json",
            )
            save_json_atomic(score_path, score)
            predictions_stored += 1

            print(
                f"  {symbol} {session_date}: {envelope.get('action')} "
                f"(conv={envelope.get('conviction')}) -> {score.get('status')} / {score.get('action_verdict')}"
            )

        except ImportError:
            print("ERROR: anthropic package not installed. Run: pip install anthropic")
            print("Or use --dry-run to save prompts for manual review.")
            sys.exit(1)
        except json.JSONDecodeError as e:
            print(f"  WARNING: {symbol} {session_date}: Failed to parse LLM response as JSON: {e}")
            continue
        except Exception as e:
            print(f"  WARNING: {symbol} {session_date}: API error: {e}")
            continue

    print(f"\nDone: {prompts_saved} prompts saved, {predictions_stored} predictions stored+scored")

    if dry_run:
        print(f"\nPrompts saved to: {PREDICTIONS_REPLAY_DIR}")
        print("Review a few, then re-run without --dry-run to call the API.")
    elif predictions_stored > 0:
        print("\nBuilding calibration from bootstrap scores...")
        from llm_calibrate import collect_scored_predictions, build_calibration_bundle
        records = collect_scored_predictions(source="replay")
        if records:
            bundle = build_calibration_bundle(records, source="replay")
            cal_dated = os.path.join(CALIBRATION_DIR, f"{datetime.now().strftime('%Y-%m-%d')}__{bundle['calibration_id']}.json")
            latest = os.path.join(CALIBRATION_DIR, "latest__llm_calibration.json")
            save_json_atomic(cal_dated, bundle)
            save_json_atomic(latest, bundle)
            print(f"Initial calibration built: {bundle['calibration_id']}")
            print(f"  Scored: {bundle['scored_prediction_count']}")
            print(f"  Accuracy: {bundle.get('overall', {}).get('accuracy_pct', 'N/A')}%")
        else:
            print("No scored predictions found for calibration.")


if __name__ == "__main__":
    main()
