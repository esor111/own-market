"""
Build context-only family guidance from replay supportive behavior profiles.

Usage:
    python replay_family_guidance.py REPLAY_ID
"""
import json
import os
import sys
from datetime import datetime
from glob import glob

from config import REPLAYS_DIR
from replay_behavior_profile import build_behavior_profile


PROFILE_TO_GUIDANCE = {
    "supportive_followthrough_bias": "supportive_followthrough_support",
    "supportive_fragility_bias": "supportive_fragility_caution",
    "supportive_filter_bias": "supportive_filter_support",
    "mixed_or_unclear": "mixed_or_unclear",
    "insufficient_sample": "insufficient_sample",
}

SECTOR_ALIASES = {
    "BANKING": "COMMERCIAL BANKS",
    "COMMERCIAL BANKS": "COMMERCIAL BANKS",
    "COMMBANK": "COMMERCIAL BANKS",
    "DEVELOPMENT BANKS": "DEVELOPMENT BANKS",
    "DEVBANK": "DEVELOPMENT BANKS",
    "HYDROPOWER": "HYDROPOWER",
}


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _normalize_sector_name(sector_name):
    return SECTOR_ALIASES.get(str(sector_name or "").upper(), str(sector_name or "").upper())


def load_latest_family_guidance_bundle():
    guidance_paths = glob(os.path.join(REPLAYS_DIR, "*", "summaries", "latest__family_guidance_v1.json"))
    latest_payload = None
    latest_path = None
    latest_key = ""

    for path in sorted(guidance_paths):
        try:
            payload = load_json(path)
        except FileNotFoundError:
            continue
        sort_key = str(payload.get("built_at") or "")
        if sort_key >= latest_key:
            latest_key = sort_key
            latest_payload = payload
            latest_path = path

    if not latest_payload:
        return {}

    return {
        "path": latest_path,
        "payload": latest_payload,
    }


def resolve_latest_family_guidance(symbol, sector_name):
    bundle = load_latest_family_guidance_bundle()
    if not bundle:
        return {}

    payload = bundle.get("payload") or {}
    normalized_sector = _normalize_sector_name(sector_name)
    return {
        "source_path": bundle.get("path"),
        "source_replay_id": payload.get("replay_id"),
        "use_as": payload.get("use_as"),
        "do_not_use_as_hard_rule": payload.get("do_not_use_as_hard_rule", True),
        "symbol_guidance": (payload.get("symbol_guidance") or {}).get(str(symbol).upper()),
        "sector_guidance": (payload.get("sector_guidance") or {}).get(normalized_sector),
    }


def _advisory_note(profile):
    label = profile.get("profile_label")
    confidence = profile.get("sample_confidence")
    if label == "supportive_followthrough_bias":
        return "Historical replay suggests supportive setups in this group often follow through. Use as supportive context only, not as a standalone rule."
    if label == "supportive_fragility_bias":
        return "Historical replay suggests supportive setups in this group often turn fragile. Use as a caution flag, not as an automatic rejection rule."
    if label == "supportive_filter_bias":
        return "Historical replay suggests filtered setups in this group were often correctly avoided. Use as caution when forcing actionability."
    if confidence == "low":
        return "Sample size is still low. Treat this as weak context only."
    return "Evidence is mixed. Do not use this as a decision rule."


def _guidance_entry(profile, key_name):
    return {
        key_name: profile.get(key_name),
        "guidance_label": PROFILE_TO_GUIDANCE.get(profile.get("profile_label"), "mixed_or_unclear"),
        "profile_label": profile.get("profile_label"),
        "sample_confidence": profile.get("sample_confidence"),
        "case_count": profile.get("case_count"),
        "actionable_success_rate": profile.get("actionable_success_rate"),
        "actionable_fragility_rate": profile.get("actionable_fragility_rate"),
        "filtered_quality_rate": profile.get("filtered_quality_rate"),
        "use_as": "context_only",
        "advisory_note": _advisory_note(profile),
    }


def _render_markdown(summary):
    lines = [
        "# Replay Family Guidance",
        "",
        f"- Replay: `{summary['replay_id']}`",
        "- Use this as context only.",
        "- Do not convert these directly into hard rules yet.",
        "",
        "## Symbol Guidance",
    ]

    for key, item in summary["symbol_guidance"].items():
        lines.extend([
            f"### {key}",
            f"- guidance: `{item['guidance_label']}`",
            f"- sample confidence: `{item['sample_confidence']}`",
            f"- case count: `{item['case_count']}`",
            f"- actionable success rate: `{item['actionable_success_rate']}`",
            f"- actionable fragility rate: `{item['actionable_fragility_rate']}`",
            f"- note: {item['advisory_note']}",
            "",
        ])

    lines.append("## Sector Guidance")
    for key, item in summary["sector_guidance"].items():
        lines.extend([
            f"### {key}",
            f"- guidance: `{item['guidance_label']}`",
            f"- sample confidence: `{item['sample_confidence']}`",
            f"- case count: `{item['case_count']}`",
            f"- actionable success rate: `{item['actionable_success_rate']}`",
            f"- actionable fragility rate: `{item['actionable_fragility_rate']}`",
            f"- note: {item['advisory_note']}",
            "",
        ])

    return "\n".join(lines).strip() + "\n"


def build_family_guidance(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    profile_path = os.path.join(replay_root, "summaries", "latest__supportive_behavior_profile_v1.json")
    if not os.path.exists(profile_path):
        _, profile_path, _, _, _ = build_behavior_profile(replay_id)
    profile = load_json(profile_path)

    symbol_guidance = {
        item["symbol"]: _guidance_entry(item, "symbol")
        for item in profile.get("symbol_profiles", [])
    }
    sector_guidance = {
        item["sector_name"]: _guidance_entry(item, "sector_name")
        for item in profile.get("sector_profiles", [])
    }

    summary = {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "built_at": datetime.now().isoformat(),
        "source_profile_path": profile_path,
        "use_as": "context_only",
        "do_not_use_as_hard_rule": True,
        "symbol_guidance": symbol_guidance,
        "sector_guidance": sector_guidance,
    }

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_json = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__family_guidance_v1.json",
    )
    latest_json = os.path.join(
        summaries_dir,
        "latest__family_guidance_v1.json",
    )
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")

    save_json(dated_json, summary)
    save_json(latest_json, summary)

    markdown = _render_markdown(summary)
    with open(dated_md, "w", encoding="utf-8") as handle:
        handle.write(markdown)
    with open(latest_md, "w", encoding="utf-8") as handle:
        handle.write(markdown)

    return dated_json, latest_json, dated_md, latest_md, summary


def main():
    if len(sys.argv) < 2:
        print("Usage: python replay_family_guidance.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    dated_json, latest_json, dated_md, latest_md, summary = build_family_guidance(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "symbol_count": len(summary["symbol_guidance"]),
        "sector_count": len(summary["sector_guidance"]),
    }, indent=2))


if __name__ == "__main__":
    main()
