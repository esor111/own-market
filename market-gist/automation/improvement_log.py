"""
Aggregate case critique proposals into one reviewable improvement log.

Usage:
    python improvement_log.py
"""
import json
import os
from collections import Counter
from datetime import datetime
from glob import glob

from config import SYMBOLS_DIR, VALIDATION_DIR, get_latest_validation_filename


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def build_improvement_log():
    critique_paths = glob(os.path.join(SYMBOLS_DIR, "*", "*", "features", "case_critiques", "*__case_critique_v1.json"))
    critiques = []
    proposal_counter = Counter()
    risk_counter = Counter()
    status_counter = Counter()

    for path in critique_paths:
        try:
            critique = load_json(path)
        except Exception:
            continue
        critiques.append({"path": path, "data": critique})
        status_counter[critique.get("summary", {}).get("status", "unknown")] += 1
        for proposal in critique.get("proposals", []):
            proposal_counter[proposal] += 1
        for risk in critique.get("risks", []):
            risk_counter[risk] += 1

    summary = {
        "schema_version": "1.0",
        "critique_count": len(critiques),
        "status_counts": dict(status_counter),
        "proposal_counts": dict(proposal_counter),
        "risk_counts": dict(risk_counter),
        "top_proposals": proposal_counter.most_common(10),
        "top_risks": risk_counter.most_common(10),
        "records": [
            {
                "path": item["path"],
                "summary": item["data"].get("summary", {}),
                "proposals": item["data"].get("proposals", []),
                "risks": item["data"].get("risks", []),
            }
            for item in critiques
        ],
    }

    dated_path = os.path.join(
        VALIDATION_DIR,
        "improvement_proposals",
        f"{datetime.now().strftime('%Y-%m-%d')}__improvement_log_v1.json",
    )
    latest_path = os.path.join(
        VALIDATION_DIR,
        "improvement_proposals",
        get_latest_validation_filename("improvement_log_v1"),
    )
    save_json(dated_path, summary)
    save_json(latest_path, summary)
    return dated_path, latest_path, summary


def main():
    dated_path, latest_path, summary = build_improvement_log()
    print(json.dumps({
        "dated_path": dated_path,
        "latest_path": latest_path,
        "critique_count": summary["critique_count"],
        "top_proposals": summary["top_proposals"][:3],
    }, indent=2))


if __name__ == "__main__":
    main()
