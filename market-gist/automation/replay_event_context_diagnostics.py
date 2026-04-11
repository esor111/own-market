"""
Measure whether replay corporate-action context adds explanatory value.

Usage:
    python replay_event_context_diagnostics.py REPLAY_ID [REPLAY_LIST_NAME]
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR
from replay_corporate_action_context import load_replay_corporate_action_context


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


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 4)


def _summarize_bucket(records):
    verdict_counts = Counter(item["comparison_verdict"] for item in records)
    actionable = [item for item in records if item["action"] in {"buy", "watch_only"}]
    avoids = [item for item in records if item["action"] == "avoid"]
    return {
        "count": len(records),
        "verdict_counts": dict(verdict_counts),
        "actionable_count": len(actionable),
        "good_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] == "good_call"), len(actionable)),
        "bad_or_mixed_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] in {"bad_call", "mixed_call"}), len(actionable)),
        "avoid_count": len(avoids),
        "missed_opportunity_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "missed_opportunity"), len(avoids)),
        "good_avoid_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "good_avoid"), len(avoids)),
        "top_symbols": Counter(item["symbol"] for item in records).most_common(5),
    }


def _event_state_label(context):
    if context.get("has_active_event"):
        return "active_event"
    if int(context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _infer_replay_list_name(replay_id, explicit_list_name=None):
    if explicit_list_name:
        return explicit_list_name
    if "__replay_basket_v1__" in replay_id:
        return "@replay_basket_v1"
    return None


def collect_event_context_records(replay_id, replay_list_name=None):
    replay_list_name = _infer_replay_list_name(replay_id, replay_list_name)
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))

    records = []
    for path in sorted(comparison_paths):
        comparison = load_json(path)
        symbol = comparison.get("symbol")
        session_date = comparison.get("session_date")
        event_context = load_replay_corporate_action_context(symbol, session_date, replay_list_name)
        dominant_event = None
        if event_context.get("has_active_event"):
            dominant_event = (event_context.get("active_events") or [None])[0]
        elif event_context.get("recent_events"):
            dominant_event = event_context["recent_events"][0]

        records.append({
            "replay_id": replay_id,
            "record_id": comparison.get("session_id"),
            "symbol": symbol,
            "session_date": session_date,
            "comparison_verdict": comparison.get("comparison_verdict"),
            "action": ((comparison.get("prediction") or {}).get("action")),
            "event_context": event_context,
            "event_state": _event_state_label(event_context),
            "dominant_event_type": (dominant_event or {}).get("event_type"),
            "dominant_event_status": (dominant_event or {}).get("event_status"),
            "days_since_event": (dominant_event or {}).get("days_since_event"),
        })
    return replay_list_name, records


def summarize_event_context_records(records, replay_id, replay_list_name, notes=None):
    state_groups = defaultdict(list)
    for record in records:
        state_groups[record["event_state"]].append(record)

    event_state_buckets = {
        state_name: _summarize_bucket(state_records)
        for state_name, state_records in sorted(state_groups.items())
    }

    type_groups = defaultdict(list)
    for record in records:
        event_type = record.get("dominant_event_type")
        if not event_type:
            continue
        type_groups[event_type].append(record)

    event_type_profiles = []
    for event_type, event_records in sorted(type_groups.items()):
        summary = _summarize_bucket(event_records)
        event_type_profiles.append({
            "event_type": event_type,
            "count": summary["count"],
            "active_count": sum(1 for item in event_records if item["event_state"] == "active_event"),
            "good_call_rate": summary["good_call_rate"],
            "bad_or_mixed_call_rate": summary["bad_or_mixed_call_rate"],
            "missed_opportunity_rate": summary["missed_opportunity_rate"],
            "good_avoid_rate": summary["good_avoid_rate"],
            "top_symbols": summary["top_symbols"],
            "verdict_counts": summary["verdict_counts"],
        })

    return {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "replay_list_name": replay_list_name,
        "built_at": datetime.now().isoformat(),
        "comparison_count": len(records),
        "event_context_count": len(records),
        "notes": notes or [],
        "event_state_buckets": event_state_buckets,
        "event_type_profiles": event_type_profiles,
    }


def _render_markdown(summary):
    lines = [
        "# Replay Event Context Diagnostics",
        "",
        f"- replay_id: `{summary['replay_id']}`",
        f"- replay_list_name: `{summary['replay_list_name']}`",
        f"- built_at: `{summary['built_at']}`",
        f"- comparison_count: `{summary['comparison_count']}`",
        f"- event_context_count: `{summary['event_context_count']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Event State Buckets", ""])
    for key, value in summary.get("event_state_buckets", {}).items():
        lines.append(
            f"- `{key}`: count `{value['count']}`, actionable `{value['actionable_count']}`, "
            f"good_call_rate `{value['good_call_rate']}`, bad_or_mixed_call_rate `{value['bad_or_mixed_call_rate']}`, "
            f"missed_opportunity_rate `{value['missed_opportunity_rate']}`, good_avoid_rate `{value['good_avoid_rate']}`"
        )

    lines.extend(["", "## Event Type Profiles", ""])
    for item in summary.get("event_type_profiles", []):
        lines.append(
            f"- `{item['event_type']}`: count `{item['count']}`, active_count `{item['active_count']}`, "
            f"good_call_rate `{item['good_call_rate']}`, bad_or_mixed_call_rate `{item['bad_or_mixed_call_rate']}`, "
            f"missed_opportunity_rate `{item['missed_opportunity_rate']}`, good_avoid_rate `{item['good_avoid_rate']}`"
        )

    return "\n".join(lines) + "\n"


def build_event_context_diagnostics(replay_id, replay_list_name=None):
    replay_list_name, records = collect_event_context_records(replay_id, replay_list_name)
    notes = [
        "this diagnostic is descriptive only and does not change any replay rule",
        "event_date currently uses the replay-safe publication date for the historical disclosure sources",
    ]
    if replay_list_name:
        notes.append(f"event context was loaded using replay list `{replay_list_name}`")
    else:
        notes.append("no replay list name was inferred; event-context matching may be incomplete for non-list replays")

    summary = summarize_event_context_records(records, replay_id, replay_list_name, notes=notes)

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_json_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_context_diagnostics_v1.json",
    )
    latest_json_path = os.path.join(summaries_dir, "latest__event_context_diagnostics_v1.json")
    dated_md_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_context_diagnostics_v1.md",
    )
    latest_md_path = os.path.join(summaries_dir, "latest__event_context_diagnostics_v1.md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_event_context_diagnostics.py REPLAY_ID [REPLAY_LIST_NAME]")
        sys.exit(1)

    replay_id = sys.argv[1]
    replay_list_name = sys.argv[2] if len(sys.argv) > 2 else None
    summary, latest_json_path, latest_md_path = build_event_context_diagnostics(replay_id, replay_list_name)
    print(json.dumps({
        "replay_id": replay_id,
        "replay_list_name": summary["replay_list_name"],
        "comparison_count": summary["comparison_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
