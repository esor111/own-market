"""
Broader untouched validation for the refined hydropower next-open watch policy.

Usage:
    python hydropower_watch_next_open_broader_validation.py
    python hydropower_watch_next_open_broader_validation.py REPLAY_ID [REPLAY_ID ...]
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
SOURCE_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__hydropower_watch_next_open_leakage_refinement_v1.json")
DEFAULT_REPLAY_IDS = [
    "2024-09-01_to_2024-09-30__replay_basket_v1__daily_truth_replay_sep2024_promoted_calendar_v1",
    "2025-01-01_to_2025-01-31__replay_basket_v1__daily_truth_replay_v1",
    "2025-02-01_to_2025-02-28__replay_basket_v1__daily_truth_replay_feb2025_champion_v1",
    "2025-03-01_to_2025-03-31__replay_basket_v1__daily_truth_replay_v1",
    "2025-04-01_to_2025-04-30__replay_basket_v1__daily_truth_replay_apr_liqslicechampion_v1",
    "2025-05-01_to_2025-05-31__replay_basket_v1__daily_truth_replay_may_champion_v1",
    "2025-06-01_to_2025-06-30__replay_basket_v1__daily_truth_replay_june_champion_v1",
]
DEFAULT_TICKET_NOTIONAL_NPR = 200_000.0


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


def _load_candidate():
    with open(SOURCE_PATH, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    best = payload.get("best_refinement") or {}
    base = payload.get("base_candidate") or {}
    return {
        "gap_min": base.get("gap_min"),
        "rr_max": base.get("rr_max"),
        "rr_min": best.get("rr_min"),
    }


def _collect_rows(replay_ids):
    rows = []
    for record in collect_actionable_records(replay_ids):
        if record.get("action") != "watch_only" or record.get("sector_name") != "HYDROPOWER":
            continue
        simulation = _simulate_case(record["decision"], record["future_bars"], DEFAULT_TICKET_NOTIONAL_NPR)
        next_open_label = legacy_next_open_label(simulation)
        executable_label = executable_entry_label(simulation)
        rows.append({
            "replay_id": record["replay_id"],
            "session_date": record["session_date"],
            "month_key": str(record["session_date"])[:7],
            "symbol": record["symbol"],
            "calendar_phase": record["calendar_phase"],
            "comparison_verdict": record["comparison_verdict"],
            "next_open_label": next_open_label,
            "executable_entry_label": executable_label,
            "next_open_gap_pct": simulation.get("next_open_gap_pct_vs_optimistic_entry"),
            "recomputed_rr_at_entry": simulation.get("recomputed_rr_at_entry"),
            "gross_return_pct": simulation.get("gross_return_pct"),
            "net_return_pct": simulation.get("net_return_pct"),
            "is_success": (
                record["comparison_verdict"] == "good_call"
                and executable_label == "tradable_positive_after_costs"
            ),
        })
    return rows


def _is_allowed(row, candidate):
    gap = row.get("next_open_gap_pct")
    rr = row.get("recomputed_rr_at_entry")
    if gap is None or rr is None:
        return False
    return (
        gap >= candidate["gap_min"]
        and rr <= candidate["rr_max"]
        and rr >= candidate["rr_min"]
    )


def _summarize(rows, candidate):
    allowed = [row for row in rows if _is_allowed(row, candidate)]
    success_rows = [row for row in rows if row["is_success"]]
    other_rows = [row for row in rows if not row["is_success"]]
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
        "next_open_label_counts": dict(Counter(row["next_open_label"] for row in rows)),
        "allowed_label_counts": dict(Counter(row["next_open_label"] for row in allowed)),
        "avg_next_open_gap_pct": _avg(rows, "next_open_gap_pct"),
        "avg_recomputed_rr_at_entry": _avg(rows, "recomputed_rr_at_entry"),
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
                "net_return_pct": row["net_return_pct"],
                "is_success": row["is_success"],
            }
            for row in allowed[:12]
        ],
    }


def _render_markdown(payload):
    lines = [
        "# Hydropower Watch Next-Open Broader Validation",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- replay_id_count: `{len(payload['replay_ids'])}`",
        f"- source_path: `{payload['source_path']}`",
        f"- candidate: `gap >= {payload['candidate']['gap_min']}, rr <= {payload['candidate']['rr_max']}, rr >= {payload['candidate']['rr_min']}`",
        "",
        "## Overall",
        "",
    ]
    overall = payload["overall"]
    for key in (
        "count",
        "success_count",
        "other_count",
        "allow_count",
        "allow_success_count",
        "allow_other_count",
        "allow_precision",
        "success_recall",
        "other_allow_rate",
        "other_block_rate",
        "next_open_label_counts",
        "allowed_label_counts",
    ):
        lines.append(f"- {key}: `{overall[key]}`")

    lines.extend(["", "## By Month", ""])
    for month_key in sorted(payload["by_month"]):
        summary = payload["by_month"][month_key]
        lines.extend([
            f"### `{month_key}`",
            f"- count: `{summary['count']}`",
            f"- success_count: `{summary['success_count']}`",
            f"- allow_count: `{summary['allow_count']}`",
            f"- allow_success_count: `{summary['allow_success_count']}`",
            f"- allow_other_count: `{summary['allow_other_count']}`",
            f"- allow_precision: `{summary['allow_precision']}`",
            f"- success_recall: `{summary['success_recall']}`",
            f"- next_open_label_counts: `{summary['next_open_label_counts']}`",
            f"- allowed_label_counts: `{summary['allowed_label_counts']}`",
            "",
        ])

    lines.extend(["## Sample Allowed Rows", ""])
    for row in overall["allowed_examples"]:
        lines.append(
            f"- `{row['session_date']} {row['symbol']}`: phase `{row['calendar_phase']}`, verdict `{row['comparison_verdict']}`, "
            f"next_open `{row['next_open_label']}`, gap `{row['next_open_gap_pct']}`, rr_at_entry `{row['recomputed_rr_at_entry']}`, "
            f"net `{row['net_return_pct']}`, success `{row['is_success']}`"
        )
    return "\n".join(lines) + "\n"


def build_broader_validation(replay_ids):
    candidate = _load_candidate()
    rows = _collect_rows(replay_ids)
    by_month = {}
    for month_key in sorted({row["month_key"] for row in rows}):
        month_rows = [row for row in rows if row["month_key"] == month_key]
        by_month[month_key] = _summarize(month_rows, candidate)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": SOURCE_PATH,
        "replay_ids": replay_ids,
        "candidate": candidate,
        "overall": _summarize(rows, candidate),
        "by_month": by_month,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hydropower_watch_next_open_broader_validation_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hydropower_watch_next_open_broader_validation_v1.json",
    )
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__hydropower_watch_next_open_broader_validation_v1.md",
    )
    latest_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__hydropower_watch_next_open_broader_validation_v1.md",
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
    payload, latest_json_path, latest_md_path = build_broader_validation(replay_ids)
    print(json.dumps({
        "overall": payload["overall"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
