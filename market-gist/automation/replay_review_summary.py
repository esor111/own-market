"""
Aggregate replay critiques and comparisons into one review summary.

Usage:
    python replay_review_summary.py 2025-12-21_to_2025-12-31__EBL__JBBL__daily_truth_replay_v1
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR
from replay_confidence_remap import lookup_replay_calibrated_confidence


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def build_replay_review_summary(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))
    critique_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "critiques", "*__replay_case_critique_v1.json"))

    comparisons = []
    critiques = []
    verdict_counter = Counter()
    reason_counter = Counter()
    proposal_counter = Counter()
    symbol_verdict_counter = Counter()
    sector_verdict_counter = Counter()
    leadership_counter = Counter()
    market_regime_counter = Counter()
    sector_regime_counter = Counter()
    alignment_counter = Counter()
    status_counter = Counter()

    for path in sorted(comparison_paths):
        try:
            item = load_json(path)
        except FileNotFoundError:
            continue
        decision_path = path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}derived{os.sep}").replace(
            "__comparison_v1.json", "__replay_decision_v1.json"
        )
        decision = load_json(decision_path) if os.path.exists(decision_path) else {}
        frozen_case_path = path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__comparison_v1.json", "__frozen_case_v1.json"
        )
        try:
            frozen_case = load_json(frozen_case_path) if os.path.exists(frozen_case_path) else {}
        except FileNotFoundError:
            frozen_case = {}
        cross = frozen_case.get("cross_sectional_context") or {}
        regime = frozen_case.get("regime_context") or {}
        sector_name = frozen_case.get("sector_name") or "UNKNOWN"
        leadership_label = cross.get("leadership_label") or "unknown"
        market_regime = (regime.get("market_proxy") or {}).get("regime_label") or "unknown"
        sector_regime = (regime.get("sector_proxy") or {}).get("regime_label") or "unknown"
        alignment_label = regime.get("alignment_label") or "unknown"
        confidence_interpretation = lookup_replay_calibrated_confidence(
            (item.get("prediction") or {}).get("action"),
            (item.get("prediction") or {}).get("confidence"),
        )
        comparisons.append({"path": path, "data": item, "frozen_case": frozen_case, "decision": decision, "confidence_interpretation": confidence_interpretation})
        verdict = item.get("comparison_verdict", "unknown")
        symbol = item.get("symbol", "unknown")
        verdict_counter[verdict] += 1
        symbol_verdict_counter[f"{symbol}:{verdict}"] += 1
        sector_verdict_counter[f"{sector_name}:{verdict}"] += 1
        leadership_counter[f"{leadership_label}:{verdict}"] += 1
        market_regime_counter[f"{market_regime}:{verdict}"] += 1
        sector_regime_counter[f"{sector_regime}:{verdict}"] += 1
        alignment_counter[f"{alignment_label}:{verdict}"] += 1
        reason_counter.update(item.get("reason_codes") or [])

    for path in sorted(critique_paths):
        try:
            item = load_json(path)
        except FileNotFoundError:
            continue
        critiques.append({"path": path, "data": item})
        status_counter[item.get("summary", {}).get("status", "unknown")] += 1
        proposal_counter.update(item.get("proposals") or [])

    high_priority_candidates = []
    for proposal, count in proposal_counter.most_common():
        if count >= 2:
            high_priority_candidates.append({
                "proposal": proposal,
                "count": count,
                "priority": "high" if count >= 4 else "medium",
            })

    summary = {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "built_at": datetime.now().isoformat(),
        "comparison_count": len(comparisons),
        "critique_count": len(critiques),
        "verdict_counts": dict(verdict_counter),
        "critique_status_counts": dict(status_counter),
        "reason_code_counts": dict(reason_counter),
        "proposal_counts": dict(proposal_counter),
        "top_reason_codes": reason_counter.most_common(10),
        "top_proposals": proposal_counter.most_common(10),
        "high_priority_candidates": high_priority_candidates,
        "symbol_verdict_counts": dict(symbol_verdict_counter),
        "sector_verdict_counts": dict(sector_verdict_counter),
        "leadership_verdict_counts": dict(leadership_counter),
        "market_regime_verdict_counts": dict(market_regime_counter),
        "sector_regime_verdict_counts": dict(sector_regime_counter),
        "alignment_verdict_counts": dict(alignment_counter),
        "records": [
            {
                "symbol": item["data"].get("symbol"),
                "session_date": item["data"].get("session_date"),
                "comparison_verdict": item["data"].get("comparison_verdict"),
                "reason_codes": item["data"].get("reason_codes") or [],
                "return_10d_pct": item["data"].get("horizon_returns", {}).get("return_10d_pct"),
                "sector_name": item.get("frozen_case", {}).get("sector_name", "UNKNOWN"),
                "leadership_label": (item.get("frozen_case", {}).get("cross_sectional_context") or {}).get("leadership_label"),
                "market_regime": ((item.get("frozen_case", {}).get("regime_context") or {}).get("market_proxy") or {}).get("regime_label"),
                "sector_regime": ((item.get("frozen_case", {}).get("regime_context") or {}).get("sector_proxy") or {}).get("regime_label"),
                "alignment_label": (item.get("frozen_case", {}).get("regime_context") or {}).get("alignment_label"),
                "raw_confidence": (item["data"].get("prediction") or {}).get("confidence"),
                "calibrated_confidence_pct": (item.get("confidence_interpretation") or {}).get("calibrated_confidence_pct"),
                "confidence_interpretation_label": (item.get("confidence_interpretation") or {}).get("confidence_interpretation_label"),
                "confidence_reference_group": (item.get("confidence_interpretation") or {}).get("reference_group"),
                "path": item["path"],
            }
            for item in comparisons
        ],
    }

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_review_summary_v1.json",
    )
    latest_path = os.path.join(
        summaries_dir,
        "latest__replay_review_summary_v1.json",
    )
    save_json(dated_path, summary)
    save_json(latest_path, summary)
    return dated_path, latest_path, summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_review_summary.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    dated_path, latest_path, summary = build_replay_review_summary(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "dated_path": dated_path,
        "latest_path": latest_path,
        "comparison_count": summary["comparison_count"],
        "critique_count": summary["critique_count"],
        "top_proposals": summary["top_proposals"][:3],
    }, indent=2))


if __name__ == "__main__":
    main()
