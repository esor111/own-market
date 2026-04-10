"""
Combine live and replay learning signals into one top-level review summary.

Usage:
    python combined_learning_summary.py
"""
import json
import os
from collections import Counter
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR, VALIDATION_DIR, get_latest_validation_filename


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _load_live_learning():
    latest_path = os.path.join(
        VALIDATION_DIR,
        "improvement_proposals",
        get_latest_validation_filename("improvement_log_v1"),
    )
    if not os.path.exists(latest_path):
        return None
    payload = load_json(latest_path)
    return {
        "path": latest_path,
        "critique_count": payload.get("critique_count", 0),
        "proposal_counts": Counter(payload.get("proposal_counts") or {}),
        "risk_counts": Counter(payload.get("risk_counts") or {}),
        "status_counts": payload.get("status_counts") or {},
        "records": payload.get("records") or [],
    }


def _load_replay_learning():
    review_paths = glob(os.path.join(REPLAYS_DIR, "*", "summaries", "latest__replay_review_summary_v1.json"))
    replays = []
    for path in sorted(review_paths):
        payload = load_json(path)
        replay_id = payload.get("replay_id") or ""
        if any(
            marker in replay_id
            for marker in [
                "_baseline_",
                "_rrwatch",
                "_strictbuy",
                "_improvingwatch",
                "_xsection_",
                "_regime_",
            ]
        ):
            continue
        replays.append({
            "path": path,
            "replay_id": replay_id,
            "comparison_count": payload.get("comparison_count", 0),
            "critique_count": payload.get("critique_count", 0),
            "proposal_counts": Counter(payload.get("proposal_counts") or {}),
            "reason_code_counts": Counter(payload.get("reason_code_counts") or {}),
            "verdict_counts": payload.get("verdict_counts") or {},
            "high_priority_candidates": payload.get("high_priority_candidates") or [],
        })
    return replays


def _proposal_overlap(live_counter, replay_counter):
    overlap = []
    for proposal in sorted(set(live_counter.keys()) | set(replay_counter.keys())):
        live_count = live_counter.get(proposal, 0)
        replay_count = replay_counter.get(proposal, 0)
        if live_count or replay_count:
            overlap.append({
                "proposal": proposal,
                "live_count": live_count,
                "replay_count": replay_count,
                "combined_count": live_count + replay_count,
                "seen_in_both": live_count > 0 and replay_count > 0,
            })
    overlap.sort(key=lambda item: (-item["combined_count"], item["proposal"]))
    return overlap


def _build_priority_candidates(live_data, replay_data):
    live_counter = live_data["proposal_counts"] if live_data else Counter()
    replay_counter = Counter()
    for replay in replay_data:
        replay_counter.update(replay["proposal_counts"])

    candidates = []
    for item in _proposal_overlap(live_counter, replay_counter):
        if item["combined_count"] < 2 and not item["seen_in_both"]:
            continue
        priority = "high" if item["seen_in_both"] or item["combined_count"] >= 4 else "medium"
        candidates.append({
            "proposal": item["proposal"],
            "priority": priority,
            "live_count": item["live_count"],
            "replay_count": item["replay_count"],
            "combined_count": item["combined_count"],
            "rationale": (
                "seen in both live and replay learning"
                if item["seen_in_both"]
                else "repeats enough in one lane to justify review"
            ),
        })
    return candidates


def build_combined_learning_summary():
    live_data = _load_live_learning()
    replay_data = _load_replay_learning()

    combined_live_proposals = live_data["proposal_counts"] if live_data else Counter()
    combined_live_risks = live_data["risk_counts"] if live_data else Counter()
    combined_replay_proposals = Counter()
    combined_replay_reasons = Counter()

    for replay in replay_data:
        combined_replay_proposals.update(replay["proposal_counts"])
        combined_replay_reasons.update(replay["reason_code_counts"])

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "lanes": {
            "live": {
                "available": bool(live_data),
                "critique_count": live_data["critique_count"] if live_data else 0,
                "top_proposals": combined_live_proposals.most_common(10),
                "top_risks": combined_live_risks.most_common(10),
                "source_path": live_data["path"] if live_data else None,
            },
            "replay": {
                "available": bool(replay_data),
                "replay_count": len(replay_data),
                "total_comparisons": sum(item["comparison_count"] for item in replay_data),
                "total_critiques": sum(item["critique_count"] for item in replay_data),
                "top_proposals": combined_replay_proposals.most_common(10),
                "top_reason_codes": combined_replay_reasons.most_common(10),
                "source_paths": [item["path"] for item in replay_data],
            },
        },
        "proposal_overlap": _proposal_overlap(combined_live_proposals, combined_replay_proposals),
        "priority_candidates": _build_priority_candidates(live_data, replay_data),
        "replay_ids": [item["replay_id"] for item in replay_data],
    }

    output_dir = os.path.join(VALIDATION_DIR, "learning_reviews")
    dated_path = os.path.join(
        output_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__combined_learning_summary_v1.json",
    )
    latest_path = os.path.join(
        output_dir,
        get_latest_validation_filename("combined_learning_summary_v1"),
    )
    save_json(dated_path, summary)
    save_json(latest_path, summary)
    return dated_path, latest_path, summary


def main():
    dated_path, latest_path, summary = build_combined_learning_summary()
    print(json.dumps({
        "dated_path": dated_path,
        "latest_path": latest_path,
        "live_available": summary["lanes"]["live"]["available"],
        "replay_available": summary["lanes"]["replay"]["available"],
        "priority_candidates": summary["priority_candidates"][:5],
    }, indent=2))


if __name__ == "__main__":
    main()
