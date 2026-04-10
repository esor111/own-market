"""
Build an action-aware replay confidence remap bundle from replay calibration.

Usage:
    python replay_confidence_remap.py
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
CALIBRATION_PATH = os.path.join(LEARNING_REVIEWS_DIR, "latest__replay_champion_calibration_v1.json")
DEFAULT_PRIOR_STRENGTH = 25
DIRECT_BUCKET_MIN_USABLE = 20
PRIMARY_ACTION_GROUPS = ("watch_only", "avoid")


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


def confidence_bucket(confidence):
    if confidence is None:
        return "unknown"
    start = int(confidence // 10) * 10
    end = min(start + 9, 100)
    return f"{start}-{end}"


def _confidence_interpretation_label(raw_confidence, calibrated_confidence):
    if raw_confidence is None or calibrated_confidence is None:
        return "unknown"
    gap = float(calibrated_confidence) - float(raw_confidence)
    if abs(gap) <= 7:
        return "well_aligned"
    if gap <= -25:
        return "strongly_overconfident"
    if gap < -7:
        return "overconfident"
    if gap >= 25:
        return "strongly_underconfident"
    if gap > 7:
        return "underconfident"
    return "roughly_aligned"


def _rate_to_pct(rate_value):
    if rate_value is None:
        return None
    return round(float(rate_value), 2)


def _pct_to_rate(pct_value):
    if pct_value is None:
        return None
    return float(pct_value) / 100.0


def _build_group_remap(group_name, group_summary, prior_strength):
    overall_hit_rate_pct = group_summary.get("observed_hit_rate_pct")
    overall_rate = _pct_to_rate(overall_hit_rate_pct)
    buckets = group_summary.get("confidence_buckets") or {}

    remap_buckets = {}
    for bucket_name, bucket_summary in sorted(buckets.items()):
        usable = int(bucket_summary.get("usable_outcomes") or 0)
        success_count = int(bucket_summary.get("success_count") or 0)
        observed_hit_rate_pct = bucket_summary.get("observed_hit_rate_pct")
        if overall_rate is None or usable <= 0:
            calibrated_pct = observed_hit_rate_pct
            source = "observed_only"
        else:
            calibrated_rate = (success_count + (prior_strength * overall_rate)) / (usable + prior_strength)
            calibrated_pct = round(calibrated_rate * 100, 2)
            source = "shrunk_bucket" if usable >= DIRECT_BUCKET_MIN_USABLE else "shrunk_low_sample_bucket"

        remap_buckets[bucket_name] = {
            "usable_outcomes": usable,
            "success_count": success_count,
            "average_confidence": bucket_summary.get("average_confidence"),
            "observed_hit_rate_pct": observed_hit_rate_pct,
            "calibrated_confidence_pct": calibrated_pct,
            "calibration_gap_pct": None if calibrated_pct is None or bucket_summary.get("average_confidence") is None else round(calibrated_pct - float(bucket_summary["average_confidence"]), 2),
            "confidence_interpretation_label": _confidence_interpretation_label(bucket_summary.get("average_confidence"), calibrated_pct),
            "remap_source": source,
        }

    return {
        "group_name": group_name,
        "overall_hit_rate_pct": overall_hit_rate_pct,
        "prior_strength": prior_strength,
        "bucket_count": len(remap_buckets),
        "buckets": remap_buckets,
    }


def build_replay_confidence_remap(prior_strength=DEFAULT_PRIOR_STRENGTH):
    if not os.path.exists(CALIBRATION_PATH):
        raise FileNotFoundError(f"Replay calibration summary not found: {CALIBRATION_PATH}")

    calibration = load_json(CALIBRATION_PATH)
    action_groups = calibration.get("action_groups") or {}

    remap = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_calibration_path": CALIBRATION_PATH,
        "source_replay_ids": calibration.get("replay_ids") or [],
        "policy": {
            "prior_strength": prior_strength,
            "direct_bucket_min_usable": DIRECT_BUCKET_MIN_USABLE,
            "primary_action_groups": list(PRIMARY_ACTION_GROUPS),
            "buy_policy": "insufficient_sample_use_watch_only_reference_only",
            "notes": [
                "this is an interpretation layer only",
                "it does not change replay actions or champion rules",
                "watch_only and avoid are the primary calibrated action groups",
                "buy sample is too small to support a stable direct remap",
            ],
        },
        "action_group_remap": {},
        "fallbacks": {
            "buy": {
                "status": "insufficient_sample",
                "recommended_reference_group": "watch_only",
            },
            "actionable": {
                "status": "reference_only",
                "recommended_primary_group": "watch_only",
            },
        },
    }

    for group_name in PRIMARY_ACTION_GROUPS:
        group_summary = action_groups.get(group_name) or {}
        remap["action_group_remap"][group_name] = _build_group_remap(group_name, group_summary, prior_strength)

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__replay_confidence_remap_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__replay_confidence_remap_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")

    markdown = render_markdown(remap)
    save_json(dated_json_path, remap)
    save_json(latest_json_path, remap)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return remap, latest_json_path, latest_md_path


def render_markdown(remap):
    lines = [
        "# Replay Confidence Remap",
        "",
        f"- built_at: `{remap['built_at']}`",
        f"- source_calibration_path: `{remap['source_calibration_path']}`",
        f"- prior_strength: `{remap['policy']['prior_strength']}`",
        "",
        "## Notes",
        "",
    ]
    for note in remap.get("policy", {}).get("notes", []):
        lines.append(f"- {note}")

    for group_name, group_payload in remap.get("action_group_remap", {}).items():
        lines.extend([
            "",
            f"## {group_name.title()} Remap",
            "",
            f"- overall_hit_rate_pct: `{group_payload['overall_hit_rate_pct']}`",
        ])
        for bucket_name, bucket_payload in group_payload.get("buckets", {}).items():
            lines.append(
                f"- `{bucket_name}`: usable `{bucket_payload['usable_outcomes']}`, "
                f"avg_confidence `{bucket_payload['average_confidence']}`, "
                f"observed `{bucket_payload['observed_hit_rate_pct']}`, "
                f"calibrated `{bucket_payload['calibrated_confidence_pct']}`, "
                f"interpretation `{bucket_payload['confidence_interpretation_label']}`, "
                f"source `{bucket_payload['remap_source']}`"
            )

    lines.extend([
        "",
        "## Fallbacks",
        "",
        f"- `buy`: `{remap['fallbacks']['buy']}`",
        f"- `actionable`: `{remap['fallbacks']['actionable']}`",
    ])
    return "\n".join(lines) + "\n"


def load_latest_replay_confidence_remap():
    path = os.path.join(LEARNING_REVIEWS_DIR, "latest__replay_confidence_remap_v1.json")
    if not os.path.exists(path):
        return None
    return load_json(path)


def lookup_replay_calibrated_confidence(action, raw_confidence, remap_payload=None):
    payload = remap_payload or load_latest_replay_confidence_remap()
    if not payload:
        return {
            "action": action,
            "raw_confidence": raw_confidence,
            "confidence_bucket": confidence_bucket(raw_confidence),
            "calibrated_confidence_pct": None,
            "status": "remap_unavailable",
        }

    action = str(action or "")
    bucket_name = confidence_bucket(raw_confidence)
    group_name = action if action in PRIMARY_ACTION_GROUPS else None
    fallback_used = None

    if group_name is None:
        if action == "buy":
            group_name = payload.get("fallbacks", {}).get("buy", {}).get("recommended_reference_group")
            fallback_used = "buy_to_watch_only_reference"
        elif action in {"strong_buy", "actionable"}:
            group_name = payload.get("fallbacks", {}).get("actionable", {}).get("recommended_primary_group")
            fallback_used = "actionable_to_watch_only_reference"

    group_payload = ((payload.get("action_group_remap") or {}).get(group_name or ""))
    bucket_payload = ((group_payload or {}).get("buckets") or {}).get(bucket_name)
    return {
        "action": action,
        "raw_confidence": raw_confidence,
        "confidence_bucket": bucket_name,
        "reference_group": group_name,
        "fallback_used": fallback_used,
        "calibrated_confidence_pct": (bucket_payload or {}).get("calibrated_confidence_pct"),
        "observed_hit_rate_pct": (bucket_payload or {}).get("observed_hit_rate_pct"),
        "confidence_interpretation_label": _confidence_interpretation_label(raw_confidence, (bucket_payload or {}).get("calibrated_confidence_pct")),
        "status": "ok" if bucket_payload else "bucket_unavailable",
    }


def main():
    remap, latest_json_path, latest_md_path = build_replay_confidence_remap()
    print(json.dumps({
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
        "action_groups": list(remap.get("action_group_remap", {}).keys()),
    }, indent=2))


if __name__ == "__main__":
    main()
