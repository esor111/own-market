"""
Rank positive buy-side watch slices by how close they are to the current branch-opening gate.

This is a monitoring aid for the frozen-buy-side phase. It does not change the
champion. It shows which positive slices are closest to becoming research-worthy
under the current buy-side emergent gate.

Usage:
    python buy_side_branch_readiness_queue.py
"""
import json
import math
import os
from datetime import datetime

from config import VALIDATION_DIR
from monitoring_decision_gate import (
    BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN,
    BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN,
)


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BUY_WATCHLIST_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__buy_side_watchlist_v1.json")


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


def _additional_clean_successes_needed(row):
    success_count = row.get("success_count") or 0
    count = row.get("count") or 0

    count_gap = max(0, BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN - success_count)
    if success_count >= BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN and (row.get("success_rate") or 0) >= BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN:
        return 0

    rate_gap = max(0, math.ceil((BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN * count - success_count) / (1 - BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN)))
    return max(count_gap, rate_gap)


def _readiness_bucket(row):
    needed = row["additional_clean_successes_needed"]
    if needed == 0:
        return "gate_ready_now"
    if needed <= 2:
        return "near_gate"
    if needed <= 5:
        return "watch_closely"
    return "far_from_gate"


def _top_share(pairs, total_count):
    if not pairs or not total_count:
        return None
    return round((pairs[0][1] or 0) / total_count, 4)


def _quality_risks(row):
    risks = []
    count = row.get("count") or 0
    symbol_share = _top_share(row.get("symbols") or [], count)
    month_share = _top_share(row.get("months") or [], count)

    if count < 8:
        risks.append("thin_sample")
    if symbol_share is not None and symbol_share > 0.6:
        risks.append("symbol_concentration")
    if month_share is not None and month_share > 0.5:
        risks.append("month_concentration")
    success_rate = row.get("success_rate")
    if success_rate is not None and success_rate < BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN:
        risks.append("below_success_rate_gate")
    return risks


def _quality_status(row):
    risks = row.get("quality_risks") or []
    if not risks:
        return "cleaner_candidate"
    if row.get("additional_clean_successes_needed") == 0:
        return "gate_ready_but_guarded"
    return "guarded_candidate"


def render_markdown(payload):
    lines = [
        "# Buy-Side Branch Readiness Queue",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- success_count_gate: `{payload['success_count_gate']}`",
        f"- success_rate_gate: `{payload['success_rate_gate']}`",
        "",
        "## Queue",
        "",
    ]
    if not payload.get("queue_rows"):
        lines.append("- none")
    else:
        for row in payload["queue_rows"]:
            lines.append(
                f"- `{row['slice']}`: readiness `{row['readiness_bucket']}`, quality `{row['quality_status']}`, "
                f"success_count `{row['success_count']}`, failure_count `{row['failure_count']}`, "
                f"success_rate `{row['success_rate']}`, additional_clean_successes_needed `{row['additional_clean_successes_needed']}`, "
                f"top_symbol_share `{row['top_symbol_share']}`, top_month_share `{row['top_month_share']}`, "
                f"quality_risks `{row['quality_risks']}`, symbols `{row['symbols']}`, months `{row['months']}`"
            )

    lines.extend([
        "",
        "## Current Decision",
        "",
        "- champion stays frozen",
        "- no buy-side branch opens from this queue alone",
        "- use this queue to decide what positive slice to watch on the next replay refresh",
    ])
    return "\n".join(lines) + "\n"


def build_queue():
    watchlist = load_json(BUY_WATCHLIST_PATH)
    rows = []
    for row in watchlist.get("positive_watch_slices") or []:
        enriched = dict(row)
        enriched["additional_clean_successes_needed"] = _additional_clean_successes_needed(row)
        enriched["readiness_bucket"] = _readiness_bucket(enriched)
        enriched["top_symbol_share"] = _top_share(row.get("symbols") or [], row.get("count") or 0)
        enriched["top_month_share"] = _top_share(row.get("months") or [], row.get("count") or 0)
        enriched["quality_risks"] = _quality_risks(enriched)
        enriched["quality_status"] = _quality_status(enriched)
        rows.append(enriched)

    rows.sort(
        key=lambda item: (
            item["additional_clean_successes_needed"],
            -(item.get("success_rate") or 0),
            -(item.get("success_count") or 0),
        )
    )

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "success_count_gate": BUY_POSITIVE_EMERGENT_SUCCESS_COUNT_MIN,
        "success_rate_gate": BUY_POSITIVE_EMERGENT_SUCCESS_RATE_MIN,
        "queue_rows": rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__buy_side_branch_readiness_queue_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__buy_side_branch_readiness_queue_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__buy_side_branch_readiness_queue_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__buy_side_branch_readiness_queue_v1.md")

    markdown = render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return payload, latest_json_path, latest_md_path


def main():
    payload, latest_json_path, latest_md_path = build_queue()
    print(json.dumps({
        "queue_size": len(payload["queue_rows"]),
        "top_slice": (payload["queue_rows"] or [{}])[0].get("slice"),
        "top_slice_additional_clean_successes_needed": (payload["queue_rows"] or [{}])[0].get("additional_clean_successes_needed"),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
