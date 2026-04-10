"""
LLM Prediction Scorer: compares stored predictions against actual outcomes.

Usage:
    # Score a single prediction
    python llm_score.py EBL 2026-03-30 1W

    # Score all pending predictions
    python llm_score.py --all

    # Score all with minimum 10 future bars required
    python llm_score.py --all --min-bars 10
"""
import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(__file__))

from artifact_io import save_json_atomic
from config import BASE_DIR, load_json_file as _load_json
from replay_cost_realism_study import _simulate_case


def load_json(path):
    return _load_json(path, {})
from data_sources.registry import get_truth_source
from outcome_tracker import OutcomeTracker


# ---------------------------------------------------------------------------
# Paths (must match llm_predict.py)
# ---------------------------------------------------------------------------
PREDICTIONS_DIR = os.path.join(BASE_DIR, "data", "predictions")
PREDICTIONS_LIVE_DIR = os.path.join(PREDICTIONS_DIR, "live")
PREDICTIONS_REPLAY_DIR = os.path.join(PREDICTIONS_DIR, "replay")
PREDICTIONS_SCORES_DIR = os.path.join(PREDICTIONS_DIR, "scores")
PREDICTIONS_REPLAY_SCORES_DIR = os.path.join(PREDICTIONS_DIR, "replay_scores")

DEFAULT_MIN_BARS = 5
TRUTH_SOURCE_CANDIDATES = ("sharesansar_local", "nepse_scraper")
DEFAULT_LOOKAHEAD_DAYS = 60
DEFAULT_LOOKBACK_DAYS = 7
DEFAULT_TICKET_NOTIONAL_NPR = 200_000.0


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _parse_date(value):
    return datetime.strptime(str(value)[:10], "%Y-%m-%d").date()


def _horizon_return(reference_price, future_bars, index):
    """Calculate return at a specific future bar index."""
    if reference_price in (None, 0) or len(future_bars) <= index:
        return None
    future_close = future_bars[index].get("close")
    if future_close in (None, 0):
        return None
    return round(((float(future_close) / float(reference_price)) - 1.0) * 100, 2)


def _normalize_truth_row(row, row_date):
    return {
        "businessDate": row_date.strftime("%Y-%m-%d"),
        "open": row.get("openPrice") or row.get("open"),
        "high": row.get("highPrice") or row.get("high"),
        "low": row.get("lowPrice") or row.get("low"),
        "close": row.get("closePrice") or row.get("close"),
        "volume": row.get("totalTradedQuantity") or row.get("volume"),
        "_row_date": row_date,
    }


def _load_reference_and_future_bars(
    symbol,
    prediction_date,
    lookahead_days=DEFAULT_LOOKAHEAD_DAYS,
    lookback_days=DEFAULT_LOOKBACK_DAYS,
):
    """Load the prediction-day reference bar and ordered future bars."""
    pred_date = _parse_date(prediction_date)
    start_date = (pred_date - timedelta(days=lookback_days)).strftime("%Y-%m-%d")
    end_date = (pred_date + timedelta(days=lookahead_days)).strftime("%Y-%m-%d")

    for source_name in TRUTH_SOURCE_CANDIDATES:
        try:
            truth = get_truth_source(source_name)
            history = truth.get_ticker_history(symbol, start_date, end_date)
        except Exception:
            continue

        all_rows = ((history.get("history") or {}).get("content")) or []
        if not all_rows:
            continue

        normalized_rows = []
        for row in all_rows:
            row_date = None
            for date_field in ("businessDate", "date", "tradeDate"):
                if row.get(date_field):
                    try:
                        row_date = _parse_date(row[date_field])
                        break
                    except Exception:
                        continue
            if row_date is None:
                continue
            normalized_rows.append(_normalize_truth_row(row, row_date))

        normalized_rows.sort(key=lambda item: item["_row_date"])
        if not normalized_rows:
            continue

        reference_bar = None
        for row in normalized_rows:
            if row["_row_date"] <= pred_date:
                reference_bar = row

        if reference_bar is None:
            continue

        reference_date = reference_bar["_row_date"]
        future_bars = []
        for row in normalized_rows:
            if row["_row_date"] > reference_date:
                future_bars.append({k: v for k, v in row.items() if k != "_row_date"})

        clean_reference_bar = {k: v for k, v in reference_bar.items() if k != "_row_date"}
        return clean_reference_bar, future_bars, source_name

    return None, [], None


def _build_trade_plan(prediction):
    targets = prediction.get("price_targets", {}) or {}
    return {
        "action": prediction.get("action"),
        "entry_zone": targets.get("entry_zone", []),
        "stop_loss": targets.get("stop_loss"),
        "invalidation_level": targets.get("stop_loss"),
        "targets": [
            target
            for target in (
                targets.get("target_1"),
                targets.get("target_2"),
                targets.get("target_3"),
            )
            if target is not None
        ],
        "session_id": prediction.get("prediction_id"),
    }


def _comparison_verdict(prediction, horizon_returns, outcome_data=None, execution=None):
    """
    Determine verdict for an LLM prediction.
    Aligns with replay-style target/stop semantics where possible, then falls
    back to return thresholds.
    """
    action = prediction.get("action", "avoid")
    return_10d = horizon_returns.get("return_10d_pct")
    outcome_label = (outcome_data or {}).get("outcome_label")
    execution_status = (execution or {}).get("status")
    execution_exit_type = (execution or {}).get("exit_type")
    execution_net_return = (execution or {}).get("net_return_pct")

    if action in ("buy", "watch_only"):
        if execution_status == "entered":
            if execution_exit_type in {"gap_target_1", "target_1_hit"}:
                return "good_call"
            if execution_exit_type in {"gap_stop", "stop_hit"}:
                return "bad_call"
            if execution_net_return is not None and execution_net_return >= 5:
                return "good_call"
            if execution_net_return is not None and execution_net_return <= -4:
                return "bad_call"
        elif execution_status == "skip_gap_below_stop":
            return "bad_call"
        elif execution_status == "skip_gap_above_first_target":
            return "mixed_call"

        if outcome_label in {"target_1_hit", "target_2_hit", "target_3_hit"}:
            return "good_call"
        if outcome_label == "stopped_out":
            return "bad_call"
        if return_10d is not None and return_10d >= 5:
            return "good_call"
        if return_10d is not None and return_10d <= -4:
            return "bad_call"
        return "mixed_call"

    if action == "avoid":
        if return_10d is not None and return_10d >= 5:
            return "missed_opportunity"
        if return_10d is not None and return_10d <= 3:
            return "good_avoid"
        return "neutral_avoid"

    return "unscored"


def _direction_correct(prediction, horizon_returns):
    """Check if the predicted direction matched reality."""
    direction = prediction.get("direction", "neutral")
    return_5d = horizon_returns.get("return_5d_pct")
    return_10d = horizon_returns.get("return_10d_pct")

    best_return = return_10d if return_10d is not None else return_5d
    if best_return is None:
        return None

    if direction == "bullish" and best_return > 0:
        return True
    if direction == "bearish" and best_return < 0:
        return True
    if direction == "neutral" and abs(best_return) <= 2:
        return True
    return False


def _brier_component(conviction, outcome_binary):
    """Calculate single-case Brier score component."""
    if conviction is None or outcome_binary is None:
        return None
    p = conviction / 100.0
    return round((p - outcome_binary) ** 2, 4)


def _execution_summary(prediction, future_bars):
    """Return an explicit next-open execution model for actionable trade plans."""
    if prediction.get("action") not in ("buy", "watch_only"):
        return {
            "status": "not_applicable_action",
            "entry_price": None,
            "exit_price": None,
            "exit_type": None,
            "gross_return_pct": None,
            "net_return_pct": None,
            "next_open_gap_pct_vs_optimistic_entry": None,
            "recomputed_rr_at_entry": None,
            "cost_components": None,
        }

    return _simulate_case(_build_trade_plan(prediction), future_bars, DEFAULT_TICKET_NOTIONAL_NPR)


# ---------------------------------------------------------------------------
# Core scoring
# ---------------------------------------------------------------------------
def score_prediction(prediction_data, min_bars=DEFAULT_MIN_BARS, score_source="live"):
    """Score a single prediction against actual outcomes."""
    symbol = prediction_data.get("symbol")
    pred_date = prediction_data.get("run_date")
    timeframe = prediction_data.get("timeframe")
    prediction_id = prediction_data.get("prediction_id")

    reference_bar, future_bars, truth_source_used = _load_reference_and_future_bars(symbol, pred_date)

    if reference_bar is None:
        return {
            "schema_version": "1.1",
            "prediction_id": prediction_id,
            "symbol": symbol,
            "prediction_date": pred_date,
            "evaluation_date": datetime.now().strftime("%Y-%m-%d"),
            "timeframe": timeframe,
            "status": "pending_missing_reference_bar",
            "future_bars_available": len(future_bars),
            "min_bars_required": min_bars,
            "predicted_action": prediction_data.get("action"),
            "predicted_direction": prediction_data.get("direction"),
            "metadata": {
                "truth_source_used": truth_source_used,
                "score_source": score_source,
            },
        }

    if len(future_bars) < min_bars:
        return {
            "schema_version": "1.1",
            "prediction_id": prediction_id,
            "symbol": symbol,
            "prediction_date": pred_date,
            "evaluation_date": datetime.now().strftime("%Y-%m-%d"),
            "timeframe": timeframe,
            "status": "pending_insufficient_bars",
            "future_bars_available": len(future_bars),
            "min_bars_required": min_bars,
            "predicted_action": prediction_data.get("action"),
            "predicted_direction": prediction_data.get("direction"),
            "metadata": {
                "truth_source_used": truth_source_used,
                "score_source": score_source,
            },
        }

    ref_price = reference_bar.get("close")

    horizon_returns = {
        "return_1d_pct": _horizon_return(ref_price, future_bars, 0),
        "return_5d_pct": _horizon_return(ref_price, future_bars, 4),
        "return_10d_pct": _horizon_return(ref_price, future_bars, 9),
    }

    tracker = OutcomeTracker()
    decision_like = _build_trade_plan(prediction_data)
    outcome = tracker.evaluate(decision_like, future_bars, datetime.now().strftime("%Y-%m-%d"), timeframe)
    execution = _execution_summary(prediction_data, future_bars)

    verdict = _comparison_verdict(prediction_data, horizon_returns, outcome_data=outcome, execution=execution)

    dir_correct = _direction_correct(prediction_data, horizon_returns)

    conviction = prediction_data.get("conviction")
    action = prediction_data.get("action", "avoid")
    if action in ("buy", "watch_only"):
        outcome_binary = 1 if verdict == "good_call" else 0
    else:
        outcome_binary = 1 if verdict == "good_avoid" else 0
    brier = _brier_component(conviction, outcome_binary)

    return {
        "schema_version": "1.1",
        "prediction_id": prediction_id,
        "symbol": symbol,
        "prediction_date": pred_date,
        "evaluation_date": datetime.now().strftime("%Y-%m-%d"),
        "timeframe": timeframe,
        "status": "scored",
        "predicted_action": action,
        "predicted_direction": prediction_data.get("direction"),
        "direction_correct": dir_correct,
        "action_verdict": verdict,
        "reference_bar": {
            "business_date": reference_bar.get("businessDate"),
            "close": ref_price,
            "model": "prediction_day_close",
        },
        "target_outcomes": {
            "target_1_hit": outcome.get("target_1_hit"),
            "target_2_hit": outcome.get("target_2_hit"),
            "target_3_hit": outcome.get("target_3_hit"),
            "stop_hit": outcome.get("stop_hit", False),
            "outcome_label": outcome.get("outcome_label"),
        },
        "horizon_returns": horizon_returns,
        "trade_plan_execution": execution,
        "excursions": {
            "max_favorable_excursion_pct": outcome.get("max_favorable_excursion_pct"),
            "max_adverse_excursion_pct": outcome.get("max_adverse_excursion_pct"),
        },
        "conviction_accuracy": {
            "stated_conviction": conviction,
            "outcome_binary": outcome_binary,
            "brier_component": brier,
        },
        "future_bars_used": len(future_bars),
        "metadata": {
            "score_source": score_source,
            "truth_source_used": truth_source_used,
            "prompt_version": prediction_data.get("metadata", {}).get("prompt_version"),
            "calibration_version": prediction_data.get("metadata", {}).get("calibration_version"),
            "agent_id": prediction_data.get("metadata", {}).get("agent_id", "unknown"),
        },
        "agent_id": prediction_data.get("metadata", {}).get("agent_id", "unknown"),
    }


def score_path_from_prediction_path(prediction_file_path):
    """Derive score file path directly from prediction file path.

    Routes to the correct scores directory based on prediction source:
      .../live/...   -> .../scores/...
      .../replay/... -> .../replay_scores/...

    Mirrors the prediction filename (which includes agent_id) so two agents
    predicting on the same case produce separate score files.
    """
    fname = os.path.basename(prediction_file_path)
    score_fname = fname.replace("__prediction_v1.json", "__score_v1.json")
    parent_dir = os.path.basename(os.path.dirname(prediction_file_path))
    if parent_dir == "replay":
        return os.path.join(PREDICTIONS_REPLAY_SCORES_DIR, score_fname)
    return os.path.join(PREDICTIONS_SCORES_DIR, score_fname)


def score_path(prediction_id):
    """Return the score file path for a prediction (legacy, no agent_id).

    Prefer score_path_from_prediction_path() for multi-agent use.
    """
    return os.path.join(PREDICTIONS_SCORES_DIR, f"{prediction_id.replace('llmpred__', '')}__score_v1.json")


def is_scored_file(prediction_file_path):
    """Check if a prediction file already has a corresponding score file."""
    return os.path.isfile(score_path_from_prediction_path(prediction_file_path))


def is_scored(prediction_id):
    """Check if a prediction already has a score file (legacy, no agent_id)."""
    path = score_path(prediction_id)
    return os.path.isfile(path)


def find_all_predictions():
    """Find all prediction files in live and replay directories."""
    predictions = []
    for pred_dir in (PREDICTIONS_LIVE_DIR, PREDICTIONS_REPLAY_DIR):
        if os.path.isdir(pred_dir):
            for fname in os.listdir(pred_dir):
                if fname.endswith("__prediction_v1.json"):
                    predictions.append(os.path.join(pred_dir, fname))
    return sorted(predictions)


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_score_single(symbol, run_date, timeframe, min_bars):
    """Score a single prediction. Finds the file by scanning live+replay dirs."""
    # Search live then replay for a matching prediction file
    path = None
    for pred_dir in (PREDICTIONS_LIVE_DIR, PREDICTIONS_REPLAY_DIR):
        if not os.path.isdir(pred_dir):
            continue
        for fname in os.listdir(pred_dir):
            if (fname.endswith("__prediction_v1.json")
                    and f"__{symbol}__" in fname
                    and run_date in fname
                    and f"__{timeframe}__" in fname):
                path = os.path.join(pred_dir, fname)
                break
        if path:
            break

    if not path:
        print(f"ERROR: No prediction found for {symbol} {timeframe} {run_date}")
        sys.exit(1)

    prediction_data = load_json(path)
    result = score_prediction(prediction_data, min_bars)

    if result.get("status") != "scored":
        print(
            f"PENDING: {symbol} {run_date} - status={result.get('status')} "
            f"(future_bars={result.get('future_bars_available')}, need={min_bars})"
        )
        return

    out_path = score_path_from_prediction_path(path)
    save_json_atomic(out_path, result)
    print(f"Scored: {symbol} {run_date} -> {result['action_verdict']} (direction_correct={result['direction_correct']})")
    print(f"  Returns: 1d={result['horizon_returns']['return_1d_pct']}%, 5d={result['horizon_returns']['return_5d_pct']}%, 10d={result['horizon_returns']['return_10d_pct']}%")
    print(f"  Conviction: {result['conviction_accuracy']['stated_conviction']} -> Brier: {result['conviction_accuracy']['brier_component']}")
    print(f"  Saved: {out_path}")


def cmd_score_all(min_bars):
    """Score all pending predictions."""
    predictions = find_all_predictions()
    if not predictions:
        print("No predictions found.")
        return

    scored = 0
    pending = 0
    already = 0

    for path in predictions:
        data = load_json(path)

        if is_scored_file(path):
            already += 1
            continue

        result = score_prediction(data, min_bars)

        if result.get("status") != "scored":
            pending += 1
            print(
                f"  PENDING: {data.get('symbol')} {data.get('run_date')} - "
                f"status={result.get('status')} future_bars={result.get('future_bars_available')}"
            )
            continue

        out_path = score_path_from_prediction_path(path)
        save_json_atomic(out_path, result)
        scored += 1
        agent = data.get("metadata", {}).get("agent_id", "")
        agent_label = f" [{agent}]" if agent and agent != "unknown" else ""
        print(f"  SCORED: {data.get('symbol')} {data.get('run_date')}{agent_label} -> {result['action_verdict']}")

    print(f"\nSummary: {scored} scored, {pending} pending, {already} already scored")


def main():
    min_bars = DEFAULT_MIN_BARS

    # Parse --min-bars
    args = sys.argv[1:]
    filtered_args = []
    i = 0
    while i < len(args):
        if args[i] == "--min-bars" and i + 1 < len(args):
            min_bars = int(args[i + 1])
            i += 2
        else:
            filtered_args.append(args[i])
            i += 1

    if "--all" in filtered_args:
        cmd_score_all(min_bars)
    elif len(filtered_args) >= 3:
        symbol = filtered_args[0].upper()
        run_date = filtered_args[1]
        timeframe = filtered_args[2].upper()
        cmd_score_single(symbol, run_date, timeframe, min_bars)
    else:
        print("Usage:")
        print("  python llm_score.py SYMBOL DATE TIMEFRAME [--min-bars N]")
        print("  python llm_score.py --all [--min-bars N]")
        sys.exit(1)


if __name__ == "__main__":
    main()
