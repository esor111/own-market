"""
Build a calibration summary from stored decisions and outcomes.
Usage: python calibration_report.py
"""
import json
import os
from glob import glob
from statistics import mean

from config import SYMBOLS_DIR, VALIDATION_DIR


def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def confidence_bucket(confidence):
    if confidence is None:
        return "unknown"
    start = int(confidence // 10) * 10
    end = min(start + 9, 100)
    return f"{start}-{end}"


def score_bucket(score):
    if score is None:
        return "unknown"
    start = int(score // 10) * 10
    end = min(start + 9, 100)
    return f"{start}-{end}"


def outcome_to_success(outcome_record):
    label = outcome_record.get("outcome_label")
    if label in {"target_1_hit", "target_2_hit", "target_3_hit"}:
        return True
    if label == "stopped_out":
        return False
    return None


def build_index(paths, key_field):
    indexed = {}
    for path in paths:
        try:
            payload = load_json(path)
        except Exception:
            continue
        key = payload.get(key_field)
        if key:
            indexed[key] = {"path": path, "data": payload}
    return indexed


def summarize_bucket(records, bucket_key):
    buckets = {}
    for record in records:
        bucket = record[bucket_key]
        buckets.setdefault(bucket, []).append(record)

    summarized = {}
    for bucket, items in buckets.items():
        successes = [item["success"] for item in items if item["success"] is not None]
        avg_confidence = mean(item["confidence"] for item in items if item["confidence"] is not None) if items else None
        avg_score = mean(item["score"] for item in items if item["score"] is not None) if items else None
        observed_hit_rate = round((sum(1 for value in successes if value) / len(successes)) * 100, 2) if successes else None
        summarized[bucket] = {
            "count": len(items),
            "usable_outcomes": len(successes),
            "average_confidence": round(avg_confidence, 2) if avg_confidence is not None else None,
            "average_score": round(avg_score, 2) if avg_score is not None else None,
            "observed_hit_rate_pct": observed_hit_rate
        }
    return summarized


def build_calibration_summary():
    decision_paths = glob(os.path.join(SYMBOLS_DIR, "*", "*", "normalized", "decisions", "*.json"))
    outcome_paths = glob(os.path.join(SYMBOLS_DIR, "*", "*", "outcomes", "realized_results", "*.json"))

    decisions = build_index(decision_paths, "session_id")
    outcomes = build_index(outcome_paths, "decision_session_id")

    joined = []
    excluded = []
    for session_id, decision in decisions.items():
        decision_data = decision["data"]
        outcome = outcomes.get(session_id)
        outcome_data = outcome["data"] if outcome else None
        success = outcome_to_success(outcome_data or {})

        record = {
            "session_id": session_id,
            "symbol": decision_data.get("symbol"),
            "action": decision_data.get("action"),
            "setup_type": decision_data.get("setup_type"),
            "score": decision_data.get("score"),
            "confidence": decision_data.get("confidence"),
            "confidence_bucket": confidence_bucket(decision_data.get("confidence")),
            "score_bucket": score_bucket(decision_data.get("score")),
            "outcome_label": outcome_data.get("outcome_label") if outcome_data else "missing",
            "success": success
        }
        joined.append(record)

        if success is None:
            excluded.append({
                "session_id": session_id,
                "symbol": decision_data.get("symbol"),
                "reason": record["outcome_label"]
            })

    usable_records = [record for record in joined if record["success"] is not None]

    summary = {
        "total_decisions": len(joined),
        "decisions_with_usable_outcomes": len(usable_records),
        "decisions_excluded_from_calibration": len(excluded),
        "minimum_sample_warning": len(usable_records) < 20,
        "confidence_buckets": summarize_bucket(usable_records, "confidence_bucket"),
        "score_buckets": summarize_bucket(usable_records, "score_bucket"),
        "excluded_records": excluded,
        "records": joined
    }

    os.makedirs(VALIDATION_DIR, exist_ok=True)
    output_path = os.path.join(VALIDATION_DIR, "confidence_calibration_summary.json")
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    return output_path, summary


def main():
    output_path, summary = build_calibration_summary()

    print(f"Calibration summary saved: {output_path}")
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
