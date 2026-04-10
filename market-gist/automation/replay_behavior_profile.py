"""
Profile supportive replay behavior by symbol and sector family.

Usage:
    python replay_behavior_profile.py REPLAY_ID
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime

from config import REPLAYS_DIR
from replay_supportive_diagnostics import TARGET_ALIGNMENT, load_supportive_records


ACTIONABLE_VERDICTS = {"good_call", "bad_call", "mixed_call"}
FILTERED_VERDICTS = {"good_avoid", "neutral_avoid", "missed_opportunity"}


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def _mean(values):
    clean = [float(value) for value in values if value is not None]
    return round(sum(clean) / len(clean), 3) if clean else None


def _rate(numerator, denominator):
    if not denominator:
        return None
    return round(numerator / denominator, 3)


def _sample_confidence(case_count):
    if case_count >= 12:
        return "high"
    if case_count >= 6:
        return "medium"
    return "low"


def _profile_label(case_count, actionable_count, filtered_count, actionable_success_rate, actionable_fragility_rate, filtered_quality_rate):
    if case_count < 4:
        return "insufficient_sample"
    if actionable_count >= 4 and actionable_success_rate is not None and actionable_success_rate >= 0.7 and (actionable_fragility_rate or 0) <= 0.3:
        return "supportive_followthrough_bias"
    if actionable_count >= 4 and actionable_fragility_rate is not None and actionable_fragility_rate >= 0.6:
        return "supportive_fragility_bias"
    if filtered_count >= 4 and filtered_quality_rate is not None and filtered_quality_rate >= 0.7:
        return "supportive_filter_bias"
    return "mixed_or_unclear"


def _build_profile(records, group_key, group_value):
    case_count = len(records)
    verdict_counts = Counter(record["verdict"] for record in records)
    action_counts = Counter(record["action"] for record in records)
    actionable_records = [record for record in records if record["verdict"] in ACTIONABLE_VERDICTS]
    filtered_records = [record for record in records if record["verdict"] in FILTERED_VERDICTS]
    actionable_count = len(actionable_records)
    filtered_count = len(filtered_records)

    actionable_success_rate = _rate(verdict_counts.get("good_call", 0), actionable_count)
    actionable_fragility_rate = _rate(
        verdict_counts.get("bad_call", 0) + verdict_counts.get("mixed_call", 0),
        actionable_count,
    )
    filtered_quality_rate = _rate(verdict_counts.get("good_avoid", 0), filtered_count)
    missed_opportunity_rate = _rate(verdict_counts.get("missed_opportunity", 0), filtered_count)

    metric_averages = {
        "score": _mean(record.get("score") for record in records),
        "risk_reward_ratio": _mean(record.get("risk_reward_ratio") for record in records),
        "return_5d_pct": _mean(record.get("return_5d_pct") for record in records),
        "return_20d_pct": _mean(record.get("return_20d_pct") for record in records),
        "close_position_20d": _mean(record.get("close_position_20d") for record in records),
        "volume_ratio_5d": _mean(record.get("volume_ratio_5d") for record in records),
    }

    leadership_counts = Counter(record.get("leadership_label") or "unknown" for record in records)
    trend_counts = Counter(record.get("trend_label") or "unknown" for record in records)
    liquidity_counts = Counter(record.get("liquidity_label") or "unknown" for record in records)
    reason_counts = Counter(
        reason
        for record in records
        for reason in (record.get("reason_codes") or [])
    )

    sample_confidence = _sample_confidence(case_count)
    profile_label = _profile_label(
        case_count,
        actionable_count,
        filtered_count,
        actionable_success_rate,
        actionable_fragility_rate,
        filtered_quality_rate,
    )

    return {
        group_key: group_value,
        "case_count": case_count,
        "sample_confidence": sample_confidence,
        "profile_label": profile_label,
        "verdict_counts": dict(verdict_counts),
        "action_counts": dict(action_counts),
        "actionable_count": actionable_count,
        "filtered_count": filtered_count,
        "actionable_success_rate": actionable_success_rate,
        "actionable_fragility_rate": actionable_fragility_rate,
        "filtered_quality_rate": filtered_quality_rate,
        "missed_opportunity_rate": missed_opportunity_rate,
        "metric_averages": metric_averages,
        "top_leadership": leadership_counts.most_common(5),
        "top_trends": trend_counts.most_common(5),
        "top_liquidity": liquidity_counts.most_common(5),
        "top_reason_codes": reason_counts.most_common(10),
    }


def _rank_profiles(profiles):
    return sorted(
        profiles,
        key=lambda item: (
            {"high": 0, "medium": 1, "low": 2}.get(item["sample_confidence"], 3),
            -(item["case_count"] or 0),
            item.get("symbol") or item.get("sector_name") or "",
        ),
    )


def _render_markdown(summary):
    lines = [
        "# Supportive Behavior Profile",
        "",
        f"- Replay: `{summary['replay_id']}`",
        f"- Alignment filter: `{summary['alignment_filter']}`",
        f"- Supportive cases analyzed: `{summary['supportive_case_count']}`",
        "",
        "## Symbol Profiles",
    ]

    for item in summary["symbol_profiles"][:10]:
        lines.extend([
            f"### {item['symbol']}",
            f"- profile: `{item['profile_label']}`",
            f"- sample confidence: `{item['sample_confidence']}`",
            f"- case count: `{item['case_count']}`",
            f"- actionable success rate: `{item['actionable_success_rate']}`",
            f"- actionable fragility rate: `{item['actionable_fragility_rate']}`",
            f"- filtered quality rate: `{item['filtered_quality_rate']}`",
            f"- top reasons: `{item['top_reason_codes'][:3]}`",
            "",
        ])

    lines.append("## Sector Profiles")
    for item in summary["sector_profiles"]:
        lines.extend([
            f"### {item['sector_name']}",
            f"- profile: `{item['profile_label']}`",
            f"- sample confidence: `{item['sample_confidence']}`",
            f"- case count: `{item['case_count']}`",
            f"- actionable success rate: `{item['actionable_success_rate']}`",
            f"- actionable fragility rate: `{item['actionable_fragility_rate']}`",
            f"- filtered quality rate: `{item['filtered_quality_rate']}`",
            "",
        ])

    return "\n".join(lines).strip() + "\n"


def build_behavior_profile(replay_id):
    replay_root = os.path.join(REPLAYS_DIR, replay_id)
    supportive_records = load_supportive_records(replay_id, alignment_filter=TARGET_ALIGNMENT)

    symbol_groups = defaultdict(list)
    sector_groups = defaultdict(list)
    for record in supportive_records:
        symbol_groups[record["symbol"]].append(record)
        sector_groups[record["sector_name"]].append(record)

    symbol_profiles = _rank_profiles([
        _build_profile(records, "symbol", symbol)
        for symbol, records in symbol_groups.items()
    ])
    sector_profiles = _rank_profiles([
        _build_profile(records, "sector_name", sector_name)
        for sector_name, records in sector_groups.items()
    ])

    summary = {
        "schema_version": "1.0",
        "replay_id": replay_id,
        "alignment_filter": TARGET_ALIGNMENT,
        "built_at": datetime.now().isoformat(),
        "supportive_case_count": len(supportive_records),
        "symbol_profiles": symbol_profiles,
        "sector_profiles": sector_profiles,
    }

    summaries_dir = os.path.join(replay_root, "summaries")
    dated_json = os.path.join(
        summaries_dir,
        f"{datetime.now().strftime('%Y-%m-%d')}__supportive_behavior_profile_v1.json",
    )
    latest_json = os.path.join(
        summaries_dir,
        "latest__supportive_behavior_profile_v1.json",
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
        print("Usage: python replay_behavior_profile.py REPLAY_ID")
        sys.exit(1)

    replay_id = sys.argv[1]
    dated_json, latest_json, dated_md, latest_md, summary = build_behavior_profile(replay_id)
    print(json.dumps({
        "replay_id": replay_id,
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "supportive_case_count": summary["supportive_case_count"],
    }, indent=2))


if __name__ == "__main__":
    main()
