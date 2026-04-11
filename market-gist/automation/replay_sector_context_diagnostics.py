"""
Measure whether replay-sector context adds explanatory value beyond symbol-local metrics.

Usage:
    python replay_sector_context_diagnostics.py REPLAY_ID
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR


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


def _bucket(records, predicate):
    selected = [record for record in records if predicate(record)]
    verdict_counts = Counter(item["comparison_verdict"] for item in selected)
    actionable = [item for item in selected if item["action"] in {"buy", "watch_only"}]
    avoids = [item for item in selected if item["action"] == "avoid"]
    return {
        "count": len(selected),
        "verdict_counts": dict(verdict_counts),
        "actionable_count": len(actionable),
        "good_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] == "good_call"), len(actionable)),
        "bad_or_mixed_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] in {"bad_call", "mixed_call"}), len(actionable)),
        "avoid_count": len(avoids),
        "missed_opportunity_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "missed_opportunity"), len(avoids)),
        "good_avoid_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "good_avoid"), len(avoids)),
    }


def _render_markdown(summary):
    lines = [
        "# Replay Sector Context Diagnostics",
        "",
        f"- replay_id: `{summary['replay_id']}`",
        f"- built_at: `{summary['built_at']}`",
        f"- comparison_count: `{summary['comparison_count']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend(["", "## Sector Profiles", ""])
    for item in summary.get("sector_profiles", []):
        lines.append(
            f"- `{item['sector_name']}`: count `{item['count']}`, good_call_rate `{item['good_call_rate']}`, "
            f"bad_or_mixed_call_rate `{item['bad_or_mixed_call_rate']}`, missed_opportunity_rate `{item['missed_opportunity_rate']}`, "
            f"good_avoid_rate `{item['good_avoid_rate']}`"
        )

    lines.extend(["", "## Alignment Checks", ""])
    for key, value in summary.get("alignment_checks", {}).items():
        lines.append(f"### `{key}`")
        lines.append(f"- {value}")

    return "\n".join(lines) + "\n"


def build_sector_context_diagnostics(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    comparison_paths = glob(os.path.join(replay_root, "sessions", "*", "*", "comparisons", "*__comparison_v1.json"))

    records = []
    for path in sorted(comparison_paths):
        comparison = load_json(path)
        frozen_case_path = path.replace(f"{os.sep}comparisons{os.sep}", f"{os.sep}normalized{os.sep}").replace(
            "__comparison_v1.json", "__frozen_case_v1.json"
        )
        frozen_case = load_json(frozen_case_path) if os.path.exists(frozen_case_path) else {}
        metrics = frozen_case.get("metrics") or {}
        regime_context = frozen_case.get("regime_context") or {}
        derived_sector = (((frozen_case.get("historical_context") or {}).get("derived_context") or {}).get("sector") or {})
        official_sector = (((frozen_case.get("historical_context") or {}).get("official_context") or {}).get("sector_index") or {})
        sector_name = frozen_case.get("sector_name") or "UNKNOWN"

        records.append({
            "record_id": comparison.get("session_id"),
            "symbol": comparison.get("symbol"),
            "sector_name": sector_name,
            "comparison_verdict": comparison.get("comparison_verdict"),
            "action": ((comparison.get("prediction") or {}).get("action")),
            "trend_label": metrics.get("trend_label"),
            "return_20d_pct": metrics.get("return_20d_pct"),
            "close_position_20d": metrics.get("close_position_20d"),
            "volume_ratio_5d": metrics.get("volume_ratio_5d"),
            "sector_alignment": regime_context.get("alignment_label"),
            "sector_proxy_regime": ((regime_context.get("sector_proxy") or {}).get("regime_label")),
            "derived_sector_avg_diff_pct": derived_sector.get("average_diff_pct"),
            "derived_sector_adv_dec_ratio": derived_sector.get("advance_decline_ratio"),
            "official_sector_close": official_sector.get("closingIndex"),
        })

    sector_groups = defaultdict(list)
    for record in records:
        sector_groups[record["sector_name"]].append(record)

    sector_profiles = []
    for sector_name, sector_records in sorted(sector_groups.items()):
        actionable = [item for item in sector_records if item["action"] in {"buy", "watch_only"}]
        avoids = [item for item in sector_records if item["action"] == "avoid"]
        sector_profiles.append({
            "sector_name": sector_name,
            "count": len(sector_records),
            "actionable_count": len(actionable),
            "good_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] == "good_call"), len(actionable)),
            "bad_or_mixed_call_rate": _rate(sum(1 for item in actionable if item["comparison_verdict"] in {"bad_call", "mixed_call"}), len(actionable)),
            "avoid_count": len(avoids),
            "missed_opportunity_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "missed_opportunity"), len(avoids)),
            "good_avoid_rate": _rate(sum(1 for item in avoids if item["comparison_verdict"] == "good_avoid"), len(avoids)),
            "top_trends": Counter(item["trend_label"] or "unknown" for item in sector_records).most_common(3),
            "top_alignments": Counter(item["sector_alignment"] or "unknown" for item in sector_records).most_common(3),
        })

    supportive = _bucket(records, lambda item: item["sector_alignment"] == "both_supportive")
    headwind = _bucket(records, lambda item: item["sector_alignment"] in {"headwind", "both_headwind"})
    mixed = _bucket(records, lambda item: item["sector_alignment"] not in {"both_supportive", "headwind", "both_headwind"})

    notes = [
        "this diagnostic is descriptive only and does not change any replay rule",
        "sector context is useful only if it explains recurring outcome differences better than symbol-local metrics alone",
    ]

    summary = {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "built_at": datetime.now().isoformat(),
        "comparison_count": len(records),
        "notes": notes,
        "sector_profiles": sector_profiles,
        "alignment_checks": {
            "both_supportive": supportive,
            "headwind": headwind,
            "mixed_or_partial": mixed,
        },
    }

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_json_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__sector_context_diagnostics_v1.json",
    )
    latest_json_path = os.path.join(summaries_dir, "latest__sector_context_diagnostics_v1.json")
    dated_md_path = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__sector_context_diagnostics_v1.md",
    )
    latest_md_path = os.path.join(summaries_dir, "latest__sector_context_diagnostics_v1.md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_sector_context_diagnostics.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    summary, latest_json_path, latest_md_path = build_sector_context_diagnostics(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "comparison_count": summary["comparison_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
