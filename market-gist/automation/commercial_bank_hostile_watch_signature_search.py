"""
Search simple separators between hostile-window commercial-bank watch winners and
the exact matched_but_stale + strongly_overconfident watch failure slice.

Usage:
    python commercial_bank_hostile_watch_signature_search.py
    python commercial_bank_hostile_watch_signature_search.py STUDY_JSON
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_STUDY_JSON = os.path.join(
    LEARNING_REVIEWS_DIR,
    "latest__commercial_bank_hostile_watch_study_v1.json",
)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _candidate_thresholds(values):
    unique = sorted(set(round(float(value), 4) for value in values if value is not None))
    return unique


def _search_single_feature(failures, winners, feature_name):
    rows = []
    all_values = [row.get(feature_name) for row in failures + winners if row.get(feature_name) is not None]
    for threshold in _candidate_thresholds(all_values):
        for comparator in ("<=", ">="):
            if comparator == "<=":
                failure_match = [row for row in failures if row.get(feature_name) is not None and row[feature_name] <= threshold]
                winner_match = [row for row in winners if row.get(feature_name) is not None and row[feature_name] <= threshold]
            else:
                failure_match = [row for row in failures if row.get(feature_name) is not None and row[feature_name] >= threshold]
                winner_match = [row for row in winners if row.get(feature_name) is not None and row[feature_name] >= threshold]

            if not failure_match:
                continue
            rows.append({
                "feature_name": feature_name,
                "comparator": comparator,
                "threshold": threshold,
                "failure_hits": len(failure_match),
                "winner_hits": len(winner_match),
                "failure_hit_rate": round(len(failure_match) / len(failures), 4) if failures else None,
                "winner_leak_rate": round(len(winner_match) / len(winners), 4) if winners else None,
            })
    rows.sort(key=lambda row: (row["failure_hit_rate"], -(row["winner_leak_rate"] or 0), row["failure_hits"]), reverse=True)
    return rows[:10]


def _render_markdown(payload):
    lines = [
        "# Commercial-Bank Hostile Watch Signature Search",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- matched_but_stale_winner_count: `{payload['matched_but_stale_winner_count']}`",
        f"- exact_failure_slice_count: `{payload['exact_failure_slice_count']}`",
        "",
        "## Top Single-Feature Separators",
        "",
    ]
    for row in payload.get("top_single_feature_rows", []):
        lines.append(
            f"- `{row['feature_name']} {row['comparator']} {row['threshold']}`: "
            f"failure_hits `{row['failure_hits']}`, winner_hits `{row['winner_hits']}`, "
            f"failure_hit_rate `{row['failure_hit_rate']}`, winner_leak_rate `{row['winner_leak_rate']}`"
        )
    return "\n".join(lines) + "\n"


def build_signature_search(study_json_path):
    study = load_json(study_json_path)
    rows = study.get("rows") or []
    matched_but_stale_winners = [
        row for row in rows
        if row.get("comparison_verdict") == "good_call"
        and row.get("event_state") == "matched_but_stale"
    ]
    exact_failure_slice = [
        row for row in rows
        if row.get("comparison_verdict") in {"bad_call", "mixed_call"}
        and row.get("event_state") == "matched_but_stale"
        and row.get("confidence_interpretation_label") == "strongly_overconfident"
    ]

    feature_names = [
        "return_5d_pct",
        "return_20d_pct",
        "volume_ratio_5d",
        "close_position_20d",
        "risk_reward_ratio",
        "bank_return_5d_rank",
    ]
    candidates = []
    for feature_name in feature_names:
        candidates.extend(_search_single_feature(exact_failure_slice, matched_but_stale_winners, feature_name))
    candidates.sort(key=lambda row: (row["failure_hit_rate"], -(row["winner_leak_rate"] or 0), row["failure_hits"]), reverse=True)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_study_json": study_json_path,
        "matched_but_stale_winner_count": len(matched_but_stale_winners),
        "exact_failure_slice_count": len(exact_failure_slice),
        "top_single_feature_rows": candidates[:12],
    }

    dated_json = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__commercial_bank_hostile_watch_signature_search_v1.json",
    )
    latest_json = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__commercial_bank_hostile_watch_signature_search_v1.json",
    )
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    markdown = _render_markdown(payload)
    save_json(dated_json, payload)
    save_json(latest_json, payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return payload, latest_json, latest_md


def main():
    study_json_path = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_STUDY_JSON
    payload, latest_json, latest_md = build_signature_search(study_json_path)
    print(json.dumps({
        "matched_but_stale_winner_count": payload["matched_but_stale_winner_count"],
        "exact_failure_slice_count": payload["exact_failure_slice_count"],
        "top_single_feature_rows": payload["top_single_feature_rows"][:5],
        "latest_json": latest_json,
        "latest_md": latest_md,
    }, indent=2))


if __name__ == "__main__":
    main()
