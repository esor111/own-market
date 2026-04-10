"""
LLM Calibration Aggregator: aggregates scored predictions into calibration data.

Produces a calibration bundle with:
- Overall accuracy and Brier score
- Accuracy by action type (buy, watch_only, avoid)
- Accuracy by conviction bucket (0-29, 30-49, 50-69, 70-89, 90-100)
- Accuracy by sector
- Systematic bias detection
- Plain-text prompt instructions that feed back into the prediction prompt

Usage:
    python llm_calibrate.py
    python llm_calibrate.py --source live
    python llm_calibrate.py --source replay
    python llm_calibrate.py --source all
    python llm_calibrate.py --agent agent-1-romeo
    python llm_calibrate.py --agent agent-2-juliet --source all
"""
import json
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from artifact_io import save_json_atomic
from config import BASE_DIR, VALIDATION_DIR, load_json_file as _load_json


def load_json(path):
    return _load_json(path, {})


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PREDICTIONS_DIR = os.path.join(BASE_DIR, "data", "predictions")
PREDICTIONS_SCORES_DIR = os.path.join(PREDICTIONS_DIR, "scores")
CALIBRATION_DIR = os.path.join(VALIDATION_DIR, "llm_calibration")
LATEST_CALIBRATION_PATH = os.path.join(CALIBRATION_DIR, "latest__llm_calibration.json")

CONVICTION_BUCKETS = [
    (0, 29, "0-29"),
    (30, 49, "30-49"),
    (50, 69, "50-69"),
    (70, 89, "70-89"),
    (90, 100, "90-100"),
]

# Sector mapping (reuse from config)
try:
    SECTOR_MAP_PATH = os.path.join(os.path.dirname(__file__), "sector_map.json")
    with open(SECTOR_MAP_PATH, "r", encoding="utf-8") as f:
        SECTOR_MAP = json.load(f)
except Exception:
    SECTOR_MAP = {}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _bucket_label(conviction):
    """Map conviction to bucket label."""
    if conviction is None:
        return "unknown"
    for low, high, label in CONVICTION_BUCKETS:
        if low <= conviction <= high:
            return label
    return "unknown"


def _sector_for_symbol(symbol):
    """Look up sector for a symbol."""
    return SECTOR_MAP.get(symbol, "UNKNOWN")


def _bias_label(gap):
    """Categorize calibration gap into a bias label."""
    if gap is None:
        return "insufficient_data"
    if abs(gap) <= 5:
        return "well_calibrated"
    if gap < -5:
        return "slight_overconfidence" if gap > -15 else "significant_overconfidence"
    return "slight_underconfidence" if gap < 15 else "significant_underconfidence"


# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
def collect_scored_predictions(source="all", agent_id=None):
    """Collect all scored prediction records, optionally filtered by agent."""
    records = []

    def _load_score_dir(score_dir, source_label):
        found = []
        if os.path.isdir(score_dir):
            for fname in os.listdir(score_dir):
                if fname.endswith("__score_v1.json"):
                    path = os.path.join(score_dir, fname)
                    data = load_json(path)
                    if data.get("status") == "scored":
                        data["_source"] = source_label
                        found.append(data)
        return found

    if source in ("live", "all"):
        records.extend(_load_score_dir(PREDICTIONS_SCORES_DIR, "live"))

    # Replay scores
    if source in ("replay", "all"):
        replay_scores_dir = os.path.join(PREDICTIONS_DIR, "replay_scores")
        records.extend(_load_score_dir(replay_scores_dir, "replay"))

    # Filter by agent if specified
    if agent_id:
        records = [r for r in records if r.get("agent_id") == agent_id
                   or r.get("metadata", {}).get("agent_id") == agent_id]

    return records


# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------
def _group_stats(records):
    """Compute accuracy and Brier stats for a group of score records."""
    if not records:
        return {"count": 0, "usable": 0}

    usable = [r for r in records if r.get("conviction_accuracy", {}).get("brier_component") is not None]
    if not usable:
        return {"count": len(records), "usable": 0}

    successes = sum(1 for r in usable if r["conviction_accuracy"]["outcome_binary"] == 1)
    brier_values = [r["conviction_accuracy"]["brier_component"] for r in usable]
    convictions = [r["conviction_accuracy"]["stated_conviction"] for r in usable if r["conviction_accuracy"]["stated_conviction"] is not None]

    accuracy_pct = round((successes / len(usable)) * 100, 1) if usable else None
    avg_conviction = round(sum(convictions) / len(convictions), 1) if convictions else None
    brier_score = round(sum(brier_values) / len(brier_values), 4) if brier_values else None

    calibration_gap = None
    if accuracy_pct is not None and avg_conviction is not None:
        calibration_gap = round(accuracy_pct - avg_conviction, 1)

    return {
        "count": len(records),
        "usable": len(usable),
        "accuracy_pct": accuracy_pct,
        "avg_conviction": avg_conviction,
        "calibration_gap_pct": calibration_gap,
        "brier_score": brier_score,
    }


def build_calibration_bundle(records, source="all", agent_id=None):
    """Build the full calibration bundle from scored predictions."""
    agent_suffix = f"__{agent_id}" if agent_id else ""

    # Find prior calibration for versioning
    latest_path = _agent_latest_path(agent_id)
    prior_id = None
    if os.path.isfile(latest_path):
        prior = load_json(latest_path)
        prior_id = prior.get("calibration_id")

    # Version
    version_num = 1
    if prior_id:
        try:
            version_num = int(prior_id.split("_v")[-1]) + 1
        except (ValueError, IndexError):
            version_num = 1

    cal_id = f"cal_v{version_num}_{datetime.now().strftime('%Y-%m-%d')}{agent_suffix}"

    # Overall stats
    overall = _group_stats(records)

    # By action
    by_action = {}
    for action in ("buy", "watch_only", "avoid"):
        group = [r for r in records if _get_prediction_action(r) == action]
        by_action[action] = _group_stats(group)

    # By conviction bucket
    by_conviction = {}
    for low, high, label in CONVICTION_BUCKETS:
        group = [r for r in records
                 if r.get("conviction_accuracy", {}).get("stated_conviction") is not None
                 and low <= r["conviction_accuracy"]["stated_conviction"] <= high]
        by_conviction[label] = _group_stats(group)

    # By sector
    by_sector = {}
    for record in records:
        symbol = record.get("symbol", "")
        sector = _sector_for_symbol(symbol)
        if sector not in by_sector:
            by_sector[sector] = []
        by_sector[sector].append(record)

    by_sector_stats = {}
    for sector, group in by_sector.items():
        stats = _group_stats(group)
        stats["bias_label"] = _bias_label(stats.get("calibration_gap_pct"))
        by_sector_stats[sector] = stats

    # Systematic biases
    biases = _detect_biases(by_action, by_conviction, by_sector_stats)

    # Prompt instructions
    instructions = _generate_prompt_instructions(by_action, by_conviction, by_sector_stats, biases)

    return {
        "schema_version": "1.0",
        "calibration_id": cal_id,
        "built_at": datetime.now().isoformat(),
        "source_type": source,
        "prediction_count": len(records),
        "scored_prediction_count": len([r for r in records if r.get("status") == "scored"]),
        "overall": overall,
        "by_action": by_action,
        "by_conviction_bucket": by_conviction,
        "by_sector": by_sector_stats,
        "systematic_biases": biases,
        "prompt_instructions": instructions,
        "metadata": {
            "prior_calibration_id": prior_id,
            "min_sample_warning": len(records) < 20,
            "agent_id": agent_id or "all",
        },
    }


def _get_prediction_action(score_record):
    """Extract the prediction action from a score record."""
    stored_action = score_record.get("predicted_action")
    if stored_action in {"buy", "watch_only", "avoid"}:
        return stored_action

    verdict = score_record.get("action_verdict", "")
    if verdict in ("good_call", "bad_call", "mixed_call"):
        return "watch_only"  # Conservative default
    if verdict in ("good_avoid", "missed_opportunity", "neutral_avoid"):
        return "avoid"
    return "unknown"


def _detect_biases(by_action, by_conviction, by_sector):
    """Detect systematic biases from calibration gaps."""
    biases = []

    # Check conviction buckets for overconfidence
    for label, stats in by_conviction.items():
        gap = stats.get("calibration_gap_pct")
        count = stats.get("usable", 0)
        if gap is not None and count >= 5:
            if gap < -10:
                biases.append({
                    "description": f"Conviction bucket {label} has {abs(gap):.0f}% overconfidence gap (n={count}). Predictions in this range are less accurate than claimed.",
                    "severity": "high" if gap < -20 else "moderate",
                    "bucket": label,
                    "gap": gap,
                })
            elif gap > 10:
                biases.append({
                    "description": f"Conviction bucket {label} has {gap:.0f}% underconfidence gap (n={count}). Predictions are more accurate than claimed.",
                    "severity": "moderate",
                    "bucket": label,
                    "gap": gap,
                })

    # Check sectors
    for sector, stats in by_sector.items():
        gap = stats.get("calibration_gap_pct")
        count = stats.get("usable", 0)
        acc = stats.get("accuracy_pct")
        if gap is not None and count >= 5 and acc is not None:
            if acc < 45:
                biases.append({
                    "description": f"{sector} sector predictions are only {acc:.0f}% accurate (n={count}). Consider sector-specific caution.",
                    "severity": "high",
                    "sector": sector,
                    "accuracy": acc,
                })

    # Check action types
    for action, stats in by_action.items():
        count = stats.get("usable", 0)
        acc = stats.get("accuracy_pct")
        if count >= 5 and acc is not None and action in ("buy", "watch_only") and acc < 40:
            biases.append({
                "description": f"'{action}' predictions are only {acc:.0f}% accurate (n={count}). This action type needs significant conviction reduction.",
                "severity": "high",
                "action": action,
                "accuracy": acc,
            })

    return biases


def _generate_prompt_instructions(by_action, by_conviction, by_sector, biases):
    """Generate plain-text instructions for the prediction prompt."""
    instructions = []

    # Conviction bucket adjustments
    for label, stats in by_conviction.items():
        gap = stats.get("calibration_gap_pct")
        count = stats.get("usable", 0)
        if gap is not None and count >= 5 and abs(gap) > 8:
            adjustment = -round(gap)
            if adjustment > 0:
                instructions.append(
                    f"When your raw conviction falls in the {label} range, reduce it by {adjustment} points. "
                    f"Historical data shows this bucket is overconfident by {abs(gap):.0f}% (n={count})."
                )
            elif adjustment < 0:
                instructions.append(
                    f"When your raw conviction falls in the {label} range, you may increase it by {abs(adjustment)} points. "
                    f"Historical data shows this bucket is underconfident by {gap:.0f}% (n={count})."
                )

    # Sector adjustments
    for sector, stats in by_sector.items():
        acc = stats.get("accuracy_pct")
        count = stats.get("usable", 0)
        if count >= 5 and acc is not None and acc < 50:
            reduction = round(50 - acc)
            instructions.append(
                f"For {sector} stocks, reduce conviction by {reduction} points. "
                f"This sector has shown only {acc:.0f}% prediction accuracy (n={count})."
            )

    # General action-type warnings
    for action, stats in by_action.items():
        count = stats.get("usable", 0)
        acc = stats.get("accuracy_pct")
        if count >= 5 and acc is not None:
            if action == "avoid" and acc >= 80:
                instructions.append(
                    f"Your 'avoid' calls are well calibrated at {acc:.0f}% accuracy (n={count}). No adjustment needed for avoids."
                )
            elif action in ("buy", "watch_only") and acc < 45:
                instructions.append(
                    f"Your '{action}' calls have only {acc:.0f}% accuracy (n={count}). Be especially cautious with positive predictions."
                )

    # Min sample warning
    total = sum(s.get("usable", 0) for s in by_conviction.values())
    if total < 20:
        instructions.insert(0,
            f"WARNING: Calibration is based on only {total} scored predictions. "
            "Treat all adjustments as tentative until more data accumulates."
        )

    if not instructions:
        instructions.append("Insufficient scored predictions for calibration. State raw conviction without adjustment.")

    return instructions


# ---------------------------------------------------------------------------
# Paths (per-agent support)
# ---------------------------------------------------------------------------
def _agent_latest_path(agent_id=None):
    """Return the path to the latest calibration file (agent-specific or shared)."""
    if agent_id:
        return os.path.join(CALIBRATION_DIR, f"latest__{agent_id}__llm_calibration.json")
    return LATEST_CALIBRATION_PATH


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    source = "all"
    agent_id = None
    args = sys.argv[1:]
    i = 0
    while i < len(args):
        if args[i] == "--source" and i + 1 < len(args):
            source = args[i + 1]
            i += 2
        elif args[i] == "--agent" and i + 1 < len(args):
            agent_id = args[i + 1]
            i += 2
        else:
            i += 1

    agent_label = f" (agent: {agent_id})" if agent_id else ""
    records = collect_scored_predictions(source, agent_id=agent_id)
    print(f"Loaded {len(records)} scored predictions (source: {source}{agent_label})")

    if not records:
        print("No scored predictions found. Run llm_score.py --all first.")
        return

    bundle = build_calibration_bundle(records, source, agent_id=agent_id)

    # Save dated and latest (per-agent or shared)
    dated_path = os.path.join(CALIBRATION_DIR, f"{datetime.now().strftime('%Y-%m-%d')}__{bundle['calibration_id']}.json")
    latest_path = _agent_latest_path(agent_id)
    save_json_atomic(dated_path, bundle)
    save_json_atomic(latest_path, bundle)
    # Only update the shared latest when running WITHOUT --agent (combined run).
    # Per-agent runs must NOT overwrite the shared file — that would contaminate
    # the other agent's next prediction round with a different agent's calibration.
    if not agent_id:
        save_json_atomic(LATEST_CALIBRATION_PATH, bundle)

    print(f"\nCalibration bundle: {bundle['calibration_id']}")
    print(f"  Scored predictions: {bundle['scored_prediction_count']}")
    overall = bundle.get("overall", {})
    print(f"  Overall accuracy: {overall.get('accuracy_pct', 'N/A')}%")
    print(f"  Overall Brier score: {overall.get('brier_score', 'N/A')}")

    biases = bundle.get("systematic_biases", [])
    if biases:
        print(f"\n  Systematic biases detected ({len(biases)}):")
        for bias in biases:
            print(f"    [{bias['severity']}] {bias['description']}")

    instructions = bundle.get("prompt_instructions", [])
    if instructions:
        print(f"\n  Prompt instructions ({len(instructions)}):")
        for inst in instructions:
            print(f"    * {inst}")

    print(f"\n  Saved: {dated_path}")
    print(f"  Latest: {latest_path}")


if __name__ == "__main__":
    main()
