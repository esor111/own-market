"""
Research-only study of next-open/live-entry policy candidates for hydropower watch_only setups.

Usage:
    python hydropower_watch_next_open_policy_study.py
    python hydropower_watch_next_open_policy_study.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import VALIDATION_DIR
from entry_label_taxonomy import executable_entry_label, next_open_label as legacy_next_open_label
from replay_cost_realism_study import collect_actionable_records, _simulate_case


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
DEFAULT_TICKET_NOTIONAL_NPR = 200_000.0
DEFAULT_REPLAY_IDS = [
    "2023-07-01_to_2023-07-31__replay_basket_v1__jul2023_currentchampion_v1",
    "2023-08-01_to_2023-08-31__replay_basket_v1__aug2023_currentchampion_v1",
    "2023-10-01_to_2023-10-31__replay_basket_v1__oct2023_postbankwatchpromotion_v1",
    "2024-07-01_to_2024-07-31__replay_basket_v1__jul2024_currentchampion_v1",
    "2024-08-01_to_2024-08-31__replay_basket_v1__aug2024_currentchampion_v1",
    "2025-07-01_to_2025-07-31__replay_basket_v1__jul2025_currentchampion_v1",
    "2025-08-01_to_2025-08-31__replay_basket_v1__aug2025_currentchampion_v1",
    "2023-12-01_to_2023-12-31__EBL__NABIL__SANIMA__JBBL__MNBBL__API__AKPL__UPPER__dec2023_promoted_calendar_v1",
    "2025-09-01_to_2025-09-30__replay_basket_v1__daily_truth_replay_september_promotedchampion_v1",
]
DISCOVERY_MONTHS = {"2023-10", "2024-07"}
VALIDATION_MONTHS = {"2024-08"}
FUTURE_STRESS_MONTHS = {"2025-07"}
POSITIVE_PROBE_MONTHS = {"2023-12"}
NEGATIVE_PROBE_MONTHS = {"2025-09"}


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _avg(rows, key):
    values = [row.get(key) for row in rows if isinstance(row.get(key), (int, float))]
    if not values:
        return None
    return round(sum(values) / len(values), 4)


def _month_key(session_date):
    return str(session_date or "")[:7]


def _candidate_thresholds(rows, key):
    return sorted(
        set(
            round(float(row[key]), 4)
            for row in rows
            if row.get(key) is not None
        )
    )


def _assemble_rows(replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        if record.get("action") != "watch_only" or record.get("sector_name") != "HYDROPOWER":
            continue
        decision = record["decision"]
        simulation = _simulate_case(decision, record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        is_success = (
            record["comparison_verdict"] == "good_call"
            and executable_label == "tradable_positive_after_costs"
        )
        rows.append({
            "replay_id": record["replay_id"],
            "session_id": record["session_id"],
            "session_date": record["session_date"],
            "month_key": _month_key(record["session_date"]),
            "symbol": record["symbol"],
            "calendar_phase": record["calendar_phase"],
            "comparison_verdict": record["comparison_verdict"],
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "raw_confidence": record["confidence"],
            "score": record["score"],
            "risk_reward_ratio": record["risk_reward_ratio"],
            "gross_return_pct": simulation.get("gross_return_pct"),
            "net_return_pct": simulation.get("net_return_pct"),
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "is_success": is_success,
        })
    return rows


def _summarize_split(rows):
    success_rows = [row for row in rows if row["is_success"]]
    other_rows = [row for row in rows if not row["is_success"]]
    return {
        "count": len(rows),
        "success_count": len(success_rows),
        "other_count": len(other_rows),
        "next_open_label_counts": dict(Counter(row["next_open_label"] for row in rows)),
        "avg_next_open_gap_pct": _avg(rows, "next_open_gap_pct"),
        "avg_recomputed_rr_at_entry": _avg(rows, "recomputed_rr_at_entry"),
        "avg_risk_reward_ratio": _avg(rows, "risk_reward_ratio"),
    }


def _candidate_from_rows(discovery_rows, min_success_hits=5):
    success_rows = [row for row in discovery_rows if row["is_success"]]
    if not success_rows:
        return []
    gap_thresholds = _candidate_thresholds(discovery_rows, "next_open_gap_pct")
    rr_thresholds = _candidate_thresholds(discovery_rows, "recomputed_rr_at_entry")
    candidates = []
    for gap_min in gap_thresholds:
        for rr_max in rr_thresholds:
            matched = [
                row for row in discovery_rows
                if row.get("next_open_gap_pct") is not None
                and row.get("recomputed_rr_at_entry") is not None
                and row["next_open_gap_pct"] >= gap_min
                and row["recomputed_rr_at_entry"] <= rr_max
            ]
            success_hits = sum(1 for row in matched if row["is_success"])
            if success_hits < min_success_hits:
                continue
            other_hits = len(matched) - success_hits
            candidates.append({
                "gap_min": gap_min,
                "rr_max": rr_max,
                "matched_count": len(matched),
                "success_hits": success_hits,
                "other_hits": other_hits,
                "success_recall": _rate(success_hits, len(success_rows)),
                "allow_precision": _rate(success_hits, len(matched)),
                "other_allow_rate": _rate(other_hits, len(discovery_rows) - len(success_rows)),
                "other_block_rate": _rate((len(discovery_rows) - len(success_rows)) - other_hits, len(discovery_rows) - len(success_rows)),
            })
    candidates.sort(
        key=lambda item: (
            item["allow_precision"] or -1,
            item["success_recall"] or -1,
            item["other_block_rate"] or -1,
            item["matched_count"],
        ),
        reverse=True,
    )
    return candidates


def _evaluate_candidate(rows, candidate):
    success_rows = [row for row in rows if row["is_success"]]
    other_rows = [row for row in rows if not row["is_success"]]
    allowed = [
        row for row in rows
        if row.get("next_open_gap_pct") is not None
        and row.get("recomputed_rr_at_entry") is not None
        and row["next_open_gap_pct"] >= candidate["gap_min"]
        and row["recomputed_rr_at_entry"] <= candidate["rr_max"]
    ]
    allowed_success = [row for row in allowed if row["is_success"]]
    allowed_other = [row for row in allowed if not row["is_success"]]
    return {
        "count": len(rows),
        "success_count": len(success_rows),
        "other_count": len(other_rows),
        "allow_count": len(allowed),
        "allow_success_count": len(allowed_success),
        "allow_other_count": len(allowed_other),
        "allow_precision": _rate(len(allowed_success), len(allowed)),
        "success_recall": _rate(len(allowed_success), len(success_rows)),
        "other_allow_rate": _rate(len(allowed_other), len(other_rows)),
        "other_block_rate": _rate(len(other_rows) - len(allowed_other), len(other_rows)),
        "allowed_label_counts": dict(Counter(row["next_open_label"] for row in allowed)),
        "avg_allowed_next_open_gap_pct": _avg(allowed, "next_open_gap_pct"),
        "avg_allowed_recomputed_rr_at_entry": _avg(allowed, "recomputed_rr_at_entry"),
        "allowed_examples": [
            {
                "session_date": row["session_date"],
                "symbol": row["symbol"],
                "calendar_phase": row["calendar_phase"],
                "comparison_verdict": row["comparison_verdict"],
                "next_open_label": row["next_open_label"],
                "next_open_gap_pct": row["next_open_gap_pct"],
                "recomputed_rr_at_entry": row["recomputed_rr_at_entry"],
                "net_return_pct": row.get("net_return_pct"),
                "is_success": row["is_success"],
            }
            for row in allowed[:10]
        ],
    }


def _render_markdown(payload):
    lines = [
        "# Hydropower Watch Next-Open Policy Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- replay_id_count: `{len(payload['replay_ids'])}`",
        f"- hydropower_watch_count: `{payload['hydropower_watch_count']}`",
        "",
        "## Split Design",
        "",
        f"- discovery_months: `{payload['split_design']['discovery_months']}`",
        f"- validation_months: `{payload['split_design']['validation_months']}`",
        f"- future_stress_months: `{payload['split_design']['future_stress_months']}`",
        "",
        "## Split Summaries",
        "",
    ]
    for split_name in ("discovery", "validation", "future_stress", "positive_probe", "negative_probe"):
        summary = payload["split_summaries"][split_name]
        lines.extend([
            f"### `{split_name}`",
            f"- count: `{summary['count']}`",
            f"- success_count: `{summary['success_count']}`",
            f"- other_count: `{summary['other_count']}`",
            f"- next_open_label_counts: `{summary['next_open_label_counts']}`",
            f"- avg_next_open_gap_pct: `{summary['avg_next_open_gap_pct']}`",
            f"- avg_recomputed_rr_at_entry: `{summary['avg_recomputed_rr_at_entry']}`",
            f"- avg_risk_reward_ratio: `{summary['avg_risk_reward_ratio']}`",
            "",
        ])

    lines.extend(["## Top Discovery Candidates", ""])
    for candidate in payload.get("top_discovery_candidates", []):
        lines.append(
            f"- `next_open_gap_pct >= {candidate['gap_min']} AND recomputed_rr_at_entry <= {candidate['rr_max']}`: "
            f"precision `{candidate['allow_precision']}`, success_recall `{candidate['success_recall']}`, "
            f"other_block_rate `{candidate['other_block_rate']}`, matched `{candidate['matched_count']}`"
        )

    best = payload.get("best_candidate") or {}
    if best:
        lines.extend([
            "",
            "## Best Candidate",
            "",
            f"- gap_min: `{best['gap_min']}`",
            f"- rr_max: `{best['rr_max']}`",
            "",
            "### Discovery",
        ])
        for key in ("allow_count", "allow_success_count", "allow_other_count", "allow_precision", "success_recall", "other_block_rate", "allowed_label_counts"):
            lines.append(f"- {key}: `{best['discovery_metrics'][key]}`")
        lines.extend(["", "### Validation"])
        for key in ("allow_count", "allow_success_count", "allow_other_count", "allow_precision", "success_recall", "other_block_rate", "allowed_label_counts"):
            lines.append(f"- {key}: `{best['validation_metrics'][key]}`")
        lines.extend(["", "### Future Stress"])
        for key in ("allow_count", "allow_success_count", "allow_other_count", "allow_precision", "success_recall", "other_block_rate", "allowed_label_counts"):
            lines.append(f"- {key}: `{best['future_stress_metrics'][key]}`")
        lines.extend(["", "### Positive Probe"])
        for key in ("allow_count", "allow_success_count", "allow_other_count", "allow_precision", "success_recall", "other_block_rate", "allowed_label_counts"):
            lines.append(f"- {key}: `{best['positive_probe_metrics'][key]}`")
        lines.extend(["", "### Negative Probe"])
        for key in ("allow_count", "allow_success_count", "allow_other_count", "allow_precision", "success_recall", "other_block_rate", "allowed_label_counts"):
            lines.append(f"- {key}: `{best['negative_probe_metrics'][key]}`")

    lines.extend(["", "## Sample Allowed Rows", ""])
    for row in (best.get("validation_metrics", {}) or {}).get("allowed_examples", []):
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: phase `{row['calendar_phase']}`, verdict `{row['comparison_verdict']}`, "
            f"next_open `{row['next_open_label']}`, gap `{row['next_open_gap_pct']}`, rr_at_entry `{row['recomputed_rr_at_entry']}`, "
            f"net `{row['net_return_pct']}`, success `{row['is_success']}`"
        )
    for row in (best.get("negative_probe_metrics", {}) or {}).get("allowed_examples", []):
        lines.append(
            f"- `NEGATIVE_PROBE {row['session_date']} {row['symbol']}`: phase `{row['calendar_phase']}`, verdict `{row['comparison_verdict']}`, "
            f"next_open `{row['next_open_label']}`, gap `{row['next_open_gap_pct']}`, rr_at_entry `{row['recomputed_rr_at_entry']}`, "
            f"net `{row['net_return_pct']}`, success `{row['is_success']}`"
        )

    return "\n".join(lines) + "\n"


def build_hydropower_watch_next_open_policy_study(replay_ids):
    rows = _assemble_rows(replay_ids)
    discovery_rows = [row for row in rows if row["month_key"] in DISCOVERY_MONTHS]
    validation_rows = [row for row in rows if row["month_key"] in VALIDATION_MONTHS]
    future_stress_rows = [row for row in rows if row["month_key"] in FUTURE_STRESS_MONTHS]
    positive_probe_rows = [row for row in rows if row["month_key"] in POSITIVE_PROBE_MONTHS]
    negative_probe_rows = [row for row in rows if row["month_key"] in NEGATIVE_PROBE_MONTHS]

    top_candidates = _candidate_from_rows(discovery_rows)
    best_candidate = None
    if top_candidates:
        evaluated = []
        for candidate in top_candidates[:20]:
            candidate_payload = dict(candidate)
            candidate_payload["discovery_metrics"] = _evaluate_candidate(discovery_rows, candidate)
            candidate_payload["validation_metrics"] = _evaluate_candidate(validation_rows, candidate)
            candidate_payload["future_stress_metrics"] = _evaluate_candidate(future_stress_rows, candidate)
            candidate_payload["positive_probe_metrics"] = _evaluate_candidate(positive_probe_rows, candidate)
            candidate_payload["negative_probe_metrics"] = _evaluate_candidate(negative_probe_rows, candidate)
            evaluated.append(candidate_payload)
        evaluated.sort(
            key=lambda item: (
                item["validation_metrics"]["allow_precision"] or -1,
                item["validation_metrics"]["success_recall"] or -1,
                item["future_stress_metrics"]["other_block_rate"] or -1,
                item["discovery_metrics"]["allow_precision"] or -1,
            ),
            reverse=True,
        )
        best_candidate = evaluated[0]
        top_candidates = evaluated[:10]

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "replay_ids": replay_ids,
        "hydropower_watch_count": len(rows),
        "split_design": {
            "discovery_months": sorted(DISCOVERY_MONTHS),
            "validation_months": sorted(VALIDATION_MONTHS),
            "future_stress_months": sorted(FUTURE_STRESS_MONTHS),
            "positive_probe_months": sorted(POSITIVE_PROBE_MONTHS),
            "negative_probe_months": sorted(NEGATIVE_PROBE_MONTHS),
        },
        "split_summaries": {
            "discovery": _summarize_split(discovery_rows),
            "validation": _summarize_split(validation_rows),
            "future_stress": _summarize_split(future_stress_rows),
            "positive_probe": _summarize_split(positive_probe_rows),
            "negative_probe": _summarize_split(negative_probe_rows),
        },
        "top_discovery_candidates": top_candidates[:10],
        "best_candidate": best_candidate,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hydropower_watch_next_open_policy_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hydropower_watch_next_open_policy_study_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hydropower_watch_next_open_policy_study_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hydropower_watch_next_open_policy_study_v1.md",
    )

    markdown = _render_markdown(payload)
    for path in (dated_json_path, latest_json_path):
        save_json(path, payload)
    for path in (dated_md_path, latest_md_path):
        save_text(path, markdown)

    return payload, latest_json_path, latest_md_path


def main(argv=None):
    argv = argv or sys.argv[1:]
    replay_ids = argv or DEFAULT_REPLAY_IDS
    payload, latest_json_path, latest_md_path = build_hydropower_watch_next_open_policy_study(replay_ids)
    print(json.dumps({
        "hydropower_watch_count": payload["hydropower_watch_count"],
        "best_candidate": payload["best_candidate"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
