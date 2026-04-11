"""
Build validated sector/alignment guidance from multiple replay sector-context diagnostics.

Usage:
    python replay_validated_sector_guidance.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import defaultdict
from datetime import datetime

from config import VALIDATION_DIR, REPLAYS_DIR


GUIDANCE_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


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


def _mean(values):
    values = [float(value) for value in values if value is not None]
    return round(sum(values) / len(values), 4) if values else None


def _sector_guidance_label(month_count, actionable_count, good_call_rate, bad_or_mixed_rate, good_avoid_rate, missed_opportunity_rate):
    if month_count < 2:
        return "insufficient_validation"
    if actionable_count >= 15 and good_call_rate is not None and good_call_rate >= 0.8 and (bad_or_mixed_rate or 0) <= 0.2:
        return "validated_actionable_support"
    if actionable_count == 0 and good_avoid_rate is not None and good_avoid_rate >= 0.85 and (missed_opportunity_rate or 0) <= 0.05:
        return "validated_avoid_support"
    if actionable_count <= 6 and good_avoid_rate is not None and good_avoid_rate >= 0.85 and (missed_opportunity_rate or 0) <= 0.05:
        return "validated_fragility_caution"
    return "mixed_or_context_only"


def _alignment_guidance_label(month_count, actionable_count, good_call_rate, bad_or_mixed_rate, good_avoid_rate, missed_opportunity_rate):
    if month_count < 2:
        return "insufficient_validation"
    if actionable_count == 0 and good_avoid_rate is not None and good_avoid_rate >= 0.7 and (missed_opportunity_rate or 0) <= 0.05:
        return "validated_avoid_zone"
    if actionable_count >= 20 and good_call_rate is not None and good_call_rate >= 0.72 and (bad_or_mixed_rate or 0) <= 0.28:
        return "validated_constructive_zone"
    return "mixed_or_context_only"


def _advisory_note(label):
    notes = {
        "validated_actionable_support": "Repeated replay evidence suggests this sector family is supportive for actionable setups. Use as context support, not as an automatic buy rule.",
        "validated_avoid_support": "Repeated replay evidence suggests this sector family was mostly correct to avoid in this validation set. Use as avoid support, not as a blanket blacklist.",
        "validated_fragility_caution": "Repeated replay evidence suggests actionable setups in this sector family often stayed fragile. Use as a caution flag before promoting borderline setups.",
        "validated_avoid_zone": "Repeated replay evidence suggests this alignment behaves like a clean avoid zone. Use as strong context caution, not as a hard ban without further validation.",
        "validated_constructive_zone": "Repeated replay evidence suggests this alignment is often constructive. Use as supportive context only, not as a standalone trigger.",
        "mixed_or_context_only": "Evidence is mixed. Keep this as low-weight context only.",
        "insufficient_validation": "There is not enough repeated validation yet. Treat this as weak context only.",
    }
    return notes.get(label, "Evidence is mixed. Keep this as context only.")


def _build_markdown(summary):
    lines = [
        "# Validated Sector Guidance",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- source_replays: `{summary['source_replays']}`",
        "- Use this as context only.",
        "- Do not convert this directly into a hard trading rule.",
        "",
        "## Sector Guidance",
    ]
    for key, item in summary.get("sector_guidance", {}).items():
        lines.extend([
            f"### {key}",
            f"- guidance: `{item['guidance_label']}`",
            f"- validated_month_count: `{item['validated_month_count']}`",
            f"- actionable_count: `{item['actionable_count']}`",
            f"- good_call_rate: `{item['good_call_rate']}`",
            f"- bad_or_mixed_call_rate: `{item['bad_or_mixed_call_rate']}`",
            f"- good_avoid_rate: `{item['good_avoid_rate']}`",
            f"- missed_opportunity_rate: `{item['missed_opportunity_rate']}`",
            f"- note: {item['advisory_note']}",
            "",
        ])
    lines.append("## Alignment Guidance")
    for key, item in summary.get("alignment_guidance", {}).items():
        lines.extend([
            f"### {key}",
            f"- guidance: `{item['guidance_label']}`",
            f"- validated_month_count: `{item['validated_month_count']}`",
            f"- actionable_count: `{item['actionable_count']}`",
            f"- good_call_rate: `{item['good_call_rate']}`",
            f"- bad_or_mixed_call_rate: `{item['bad_or_mixed_call_rate']}`",
            f"- good_avoid_rate: `{item['good_avoid_rate']}`",
            f"- missed_opportunity_rate: `{item['missed_opportunity_rate']}`",
            f"- note: {item['advisory_note']}",
            "",
        ])
    return "\n".join(lines).strip() + "\n"


def build_validated_sector_guidance(replay_ids):
    sector_rollup = defaultdict(list)
    alignment_rollup = defaultdict(list)

    for replay_id in replay_ids:
        path = os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__sector_context_diagnostics_v1.json")
        if not os.path.exists(path):
            continue
        payload = load_json(path)
        for item in payload.get("sector_profiles", []):
            sector_rollup[item["sector_name"]].append(item)
        for key, item in (payload.get("alignment_checks") or {}).items():
            alignment_rollup[key].append(item)

    sector_guidance = {}
    for sector_name, items in sector_rollup.items():
        actionable_count = sum(item.get("actionable_count", 0) or 0 for item in items)
        guidance_label = _sector_guidance_label(
            len(items),
            actionable_count,
            _mean(item.get("good_call_rate") for item in items),
            _mean(item.get("bad_or_mixed_call_rate") for item in items),
            _mean(item.get("good_avoid_rate") for item in items),
            _mean(item.get("missed_opportunity_rate") for item in items),
        )
        sector_guidance[sector_name] = {
            "sector_name": sector_name,
            "guidance_label": guidance_label,
            "validated_month_count": len(items),
            "actionable_count": actionable_count,
            "good_call_rate": _mean(item.get("good_call_rate") for item in items),
            "bad_or_mixed_call_rate": _mean(item.get("bad_or_mixed_call_rate") for item in items),
            "good_avoid_rate": _mean(item.get("good_avoid_rate") for item in items),
            "missed_opportunity_rate": _mean(item.get("missed_opportunity_rate") for item in items),
            "use_as": "context_only",
            "advisory_note": _advisory_note(guidance_label),
        }

    alignment_guidance = {}
    for alignment_name, items in alignment_rollup.items():
        actionable_count = sum(item.get("actionable_count", 0) or 0 for item in items)
        guidance_label = _alignment_guidance_label(
            len(items),
            actionable_count,
            _mean(item.get("good_call_rate") for item in items),
            _mean(item.get("bad_or_mixed_call_rate") for item in items),
            _mean(item.get("good_avoid_rate") for item in items),
            _mean(item.get("missed_opportunity_rate") for item in items),
        )
        alignment_guidance[alignment_name] = {
            "alignment_name": alignment_name,
            "guidance_label": guidance_label,
            "validated_month_count": len(items),
            "actionable_count": actionable_count,
            "good_call_rate": _mean(item.get("good_call_rate") for item in items),
            "bad_or_mixed_call_rate": _mean(item.get("bad_or_mixed_call_rate") for item in items),
            "good_avoid_rate": _mean(item.get("good_avoid_rate") for item in items),
            "missed_opportunity_rate": _mean(item.get("missed_opportunity_rate") for item in items),
            "use_as": "context_only",
            "advisory_note": _advisory_note(guidance_label),
        }

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_replays": replay_ids,
        "use_as": "context_only",
        "do_not_use_as_hard_rule": True,
        "sector_guidance": sector_guidance,
        "alignment_guidance": alignment_guidance,
    }

    dated_json = os.path.join(
        GUIDANCE_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__validated_sector_guidance_v1.json",
    )
    latest_json = os.path.join(
        GUIDANCE_DIR,
        "latest__validated_sector_guidance_v1.json",
    )
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    save_json(dated_json, summary)
    save_json(latest_json, summary)
    markdown = _build_markdown(summary)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return dated_json, latest_json, dated_md, latest_md, summary


def load_latest_validated_sector_guidance():
    path = os.path.join(GUIDANCE_DIR, "latest__validated_sector_guidance_v1.json")
    if not os.path.exists(path):
        return {}
    return load_json(path)


def resolve_validated_sector_guidance(sector_name, alignment_name):
    payload = load_latest_validated_sector_guidance()
    if not payload:
        return {}
    return {
        "source_replays": payload.get("source_replays") or [],
        "use_as": payload.get("use_as"),
        "do_not_use_as_hard_rule": payload.get("do_not_use_as_hard_rule", True),
        "sector_guidance": (payload.get("sector_guidance") or {}).get(str(sector_name or "").upper()),
        "alignment_guidance": (payload.get("alignment_guidance") or {}).get(str(alignment_name or "")),
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_validated_sector_guidance.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    replay_ids = sys.argv[1:]
    dated_json, latest_json, dated_md, latest_md, summary = build_validated_sector_guidance(replay_ids)
    print(json.dumps({
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "sector_count": len(summary["sector_guidance"]),
        "alignment_count": len(summary["alignment_guidance"]),
    }, indent=2))


if __name__ == "__main__":
    main()
