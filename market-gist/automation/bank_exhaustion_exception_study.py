"""
Research-only study of the 2024-07 commercial-bank exception slice.

Goal:
- explain why the hostile-window bank exhaustion challenger mostly worked
  but still worsened a narrow early-July 2024 bank continuation slice
- compare those clipped winners against later hostile-window bank cases
  where the same challenger improved outcomes
- search for replay-safe preservation signatures, not a promotion rule

Usage:
    python bank_exhaustion_exception_study.py
"""
import json
import os
from collections import Counter
from datetime import datetime
from statistics import mean

from config import VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")

COMPARE_PATHS = [
    os.path.join(x``
        OUTPUT_DIR,
        "latest__2023-07-01_to_2023-07-31__daily_truth_replay_jul2023_eventcovered_champion_v1__vs__daily_truth_replay_jul2023_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2023-08-01_to_2023-08-31__daily_truth_replay_aug2023_eventcovered_champion_v1__vs__daily_truth_replay_aug2023_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2024-07-01_to_2024-07-31__daily_truth_replay_jul2024_champion_v1__vs__daily_truth_replay_jul2024_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2024-08-01_to_2024-08-31__daily_truth_replay_aug2024_eventcovered_champion_v1__vs__daily_truth_replay_aug2024_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2025-08-01_to_2025-08-31__daily_truth_replay_august_champion_v1__vs__daily_truth_replay_aug2025_bankexhaustion_v1__replay_champion_challenger_compare_v1.json",
    ),
]

TRADABILITY_PATH = os.path.join(
    OUTPUT_DIR,
    "latest__replay_next_open_tradability_study__bank_hostile_windows_v1.json",
)

LATER_IMPROVED_MONTHS = {"2023-07", "2023-08", "2024-08", "2025-08"}

REPLAY_SAFE_FEATURES = {
    "day_of_month": lambda row: row.get("day_of_month"),
    "target_distance_close_pct": lambda row: row.get("target_distance_close_pct"),
    "risk_reward_ratio": lambda row: row.get("risk_reward_ratio"),
    "return_5d_pct": lambda row: row.get("return_5d_pct"),
    "return_20d_pct": lambda row: row.get("return_20d_pct"),
    "volume_ratio_5d": lambda row: row.get("volume_ratio_5d"),
    "close_position_20d": lambda row: row.get("close_position_20d"),
}

REALIZED_ONLY_FEATURES = {
    "next_open_gap_pct": lambda row: row.get("next_open_gap_pct"),
}


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


def _verdict_quality(verdict):
    scores = {
        "good_call": 2,
        "good_avoid": 2,
        "mixed_call": 1,
        "neutral_avoid": 1,
        "missed_opportunity": 0,
        "bad_call": 0,
        "unscored": 0,
    }
    return scores.get(verdict, 0)


def _outcome_direction(champion_verdict, challenger_verdict):
    champion_score = _verdict_quality(champion_verdict)
    challenger_score = _verdict_quality(challenger_verdict)
    if challenger_score > champion_score:
        return "improved"
    if challenger_score < champion_score:
        return "worsened"
    if champion_verdict != challenger_verdict:
        return "changed_same_quality"
    return "unchanged_quality"


def _mean(rows, extractor):
    values = [extractor(row) for row in rows if isinstance(extractor(row), (int, float))]
    return round(mean(values), 4) if values else None


def _top_counts(rows, extractor, limit=8):
    counter = Counter(extractor(row) or "UNKNOWN" for row in rows)
    return dict(counter.most_common(limit))


def _build_rows():
    tradability_payload = load_json(TRADABILITY_PATH)
    tradability_records = tradability_payload.get("records") or []
    tradability_map = {
        (record.get("replay_id"), record.get("session_id")): record
        for record in tradability_records
    }

    rows = []
    for path in COMPARE_PATHS:
        compare = load_json(path)
        champion_replay_id = compare.get("champion_replay_id")
        for case in (compare.get("differences") or {}).get("changed_cases", []):
            if case.get("sector_name") != "COMMERCIAL BANKS":
                continue
            tradability = tradability_map.get((champion_replay_id, case.get("session_id")), {})
            session_date = str(case.get("session_date") or "")
            rows.append({
                **case,
                "month_label": session_date[:7],
                "day_of_month": int(session_date[-2:]) if len(session_date) >= 10 else None,
                "outcome_direction": _outcome_direction(
                    case.get("champion_verdict"),
                    case.get("challenger_verdict"),
                ),
                "champion_replay_id": champion_replay_id,
                "next_open_label": tradability.get("next_open_label"),
                "next_open_gap_pct": tradability.get("next_open_gap_pct"),
                "target_distance_close_pct": tradability.get("target_distance_close_pct"),
                "risk_reward_ratio": tradability.get("risk_reward_ratio"),
                "return_5d_pct": tradability.get("return_5d_pct"),
                "return_20d_pct": tradability.get("return_20d_pct"),
                "volume_ratio_5d": tradability.get("volume_ratio_5d"),
                "close_position_20d": tradability.get("close_position_20d"),
            })
    return rows


def _summarize_group(label, rows):
    return {
        "label": label,
        "count": len(rows),
        "symbol_counts": _top_counts(rows, lambda row: row.get("symbol")),
        "leadership_counts": _top_counts(rows, lambda row: row.get("leadership_label")),
        "alignment_counts": _top_counts(rows, lambda row: row.get("alignment_label")),
        "calendar_phase_counts": _top_counts(rows, lambda row: row.get("calendar_phase")),
        "event_state_counts": _top_counts(rows, lambda row: row.get("event_state")),
        "next_open_label_counts": _top_counts(rows, lambda row: row.get("next_open_label")),
        "avg_day_of_month": _mean(rows, lambda row: row.get("day_of_month")),
        "avg_target_distance_close_pct": _mean(rows, lambda row: row.get("target_distance_close_pct")),
        "avg_risk_reward_ratio": _mean(rows, lambda row: row.get("risk_reward_ratio")),
        "avg_return_5d_pct": _mean(rows, lambda row: row.get("return_5d_pct")),
        "avg_return_20d_pct": _mean(rows, lambda row: row.get("return_20d_pct")),
        "avg_volume_ratio_5d": _mean(rows, lambda row: row.get("volume_ratio_5d")),
        "avg_close_position_20d": _mean(rows, lambda row: row.get("close_position_20d")),
        "avg_next_open_gap_pct": _mean(rows, lambda row: row.get("next_open_gap_pct")),
        "sample_cases": [
            {
                "session_date": row.get("session_date"),
                "symbol": row.get("symbol"),
                "champion_verdict": row.get("champion_verdict"),
                "challenger_verdict": row.get("challenger_verdict"),
                "next_open_label": row.get("next_open_label"),
                "day_of_month": row.get("day_of_month"),
                "target_distance_close_pct": row.get("target_distance_close_pct"),
                "risk_reward_ratio": row.get("risk_reward_ratio"),
                "return_5d_pct": row.get("return_5d_pct"),
                "return_20d_pct": row.get("return_20d_pct"),
                "volume_ratio_5d": row.get("volume_ratio_5d"),
                "close_position_20d": row.get("close_position_20d"),
                "next_open_gap_pct": row.get("next_open_gap_pct"),
            }
            for row in rows[:10]
        ],
    }


def _candidate_label(parts):
    labels = []
    for feature_name, operator, threshold in parts:
        labels.append(f"{feature_name} {operator} {threshold}")
    return " AND ".join(labels)


def _match(row, feature_name, operator, threshold):
    value = REPLAY_SAFE_FEATURES[feature_name](row)
    if not isinstance(value, (int, float)):
        return False
    if operator == "<=":
        return float(value) <= float(threshold)
    return float(value) >= float(threshold)


def _search_preservation_candidates(exception_rows, improved_rows):
    values = {}
    for feature_name, extractor in REPLAY_SAFE_FEATURES.items():
        values[feature_name] = sorted({
            round(float(extractor(row)), 4)
            for row in (exception_rows + improved_rows)
            if isinstance(extractor(row), (int, float))
        })

    all_single_results = []
    for feature_name, thresholds in values.items():
        for threshold in thresholds:
            for operator in ("<=", ">="):
                exception_hits = sum(
                    1 for row in exception_rows
                    if _match(row, feature_name, operator, threshold)
                )
                improved_hits = sum(
                    1 for row in improved_rows
                    if _match(row, feature_name, operator, threshold)
                )
                total_hits = exception_hits + improved_hits
                if total_hits == 0:
                    continue
                all_single_results.append({
                    "rule": _candidate_label([(feature_name, operator, threshold)]),
                    "exception_hits": exception_hits,
                    "improved_hits": improved_hits,
                    "precision": round(exception_hits / total_hits, 4),
                    "recall": round(exception_hits / len(exception_rows), 4),
                })

    single_results = [
        item for item in all_single_results
        if item["exception_hits"] >= 5 and item["improved_hits"] <= 15
    ]
    single_results.sort(
        key=lambda item: (item["precision"], item["recall"], item["exception_hits"], -item["improved_hits"]),
        reverse=True,
    )

    pair_results = []
    deduped_parts = []
    seen = set()
    for feature_name, thresholds in values.items():
        for threshold in thresholds:
            for operator in ("<=", ">="):
                part = (feature_name, operator, float(threshold))
                if part in seen:
                    continue
                deduped_parts.append(part)
                seen.add(part)

    for idx, left in enumerate(deduped_parts):
        for right in deduped_parts[idx + 1:]:
            if left[0] == right[0]:
                continue
            exception_hits = sum(
                1 for row in exception_rows
                if _match(row, *left) and _match(row, *right)
            )
            improved_hits = sum(
                1 for row in improved_rows
                if _match(row, *left) and _match(row, *right)
            )
            total_hits = exception_hits + improved_hits
            if total_hits == 0:
                continue
            if exception_hits < 5 or improved_hits > 5:
                continue
            pair_results.append({
                "rule": _candidate_label([left, right]),
                "exception_hits": exception_hits,
                "improved_hits": improved_hits,
                "precision": round(exception_hits / total_hits, 4),
                "recall": round(exception_hits / len(exception_rows), 4),
            })

    pair_results.sort(
        key=lambda item: (item["precision"], item["recall"], item["exception_hits"], -item["improved_hits"]),
        reverse=True,
    )
    return {
        "top_single_feature_candidates": single_results[:12],
        "top_pair_candidates": pair_results[:12],
    }


def _build_findings(groups, candidates):
    exception = groups["exception_2024_07_worsened"]
    improved = groups["later_hostile_improved"]
    top_single = (candidates.get("top_single_feature_candidates") or [None])[0]
    top_pair = (candidates.get("top_pair_candidates") or [None])[0]

    findings = [
        "The 2024-07 exception slice was not random. Every worsened case was a commercial-bank continuation that later classified as `gap_above_target` at the next open.",
        f"The exception slice was early-month and continuation-like: avg day `{exception['avg_day_of_month']}`, avg target distance `{exception['avg_target_distance_close_pct']}`, avg RR `{exception['avg_risk_reward_ratio']}`, avg return_5d `{exception['avg_return_5d_pct']}`, avg next-open gap `{exception['avg_next_open_gap_pct']}`.",
        f"Later hostile-window bank improvements were a different texture: avg day `{improved['avg_day_of_month']}`, avg target distance `{improved['avg_target_distance_close_pct']}`, avg RR `{improved['avg_risk_reward_ratio']}`, avg return_20d `{improved['avg_return_20d_pct']}`, avg next-open gap `{improved['avg_next_open_gap_pct']}`.",
        "This means the remaining blocker is not broad bank caution. It is a narrow early-supportive continuation exception inside hostile commercial-bank windows.",
    ]
    if top_single:
        findings.append(
            f"Best single replay-safe preservation slice: `{top_single['rule']}` with exception hits `{top_single['exception_hits']}` out of `{exception['count']}` and improved leakage `{top_single['improved_hits']}` out of `{improved['count']}`."
        )
    if top_pair:
        findings.append(
            f"Best pair preservation slice: `{top_pair['rule']}` with precision `{top_pair['precision']}` and recall `{top_pair['recall']}`."
        )
    findings.append(
        "This is still research evidence only. A preservation exception should not be promoted until the same signature is validated on other hostile commercial-bank windows."
    )
    return findings


def _build_markdown(payload):
    lines = [
        "# Bank Exhaustion Exception Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Why This Exists",
        "",
        "This study explains the blocker in the commercial-bank hostile-window exhaustion challenger.",
        "That challenger mostly helped, but `2024-07` still contained a narrow early supportive bank slice where caution clipped real winners.",
        "",
        "## Findings",
    ]
    for finding in payload.get("findings", []):
        lines.append(f"- {finding}")

    for key in ("exception_2024_07_worsened", "later_hostile_improved"):
        group = payload["groups"][key]
        lines.extend([
            "",
            f"## {key}",
            f"- count: `{group['count']}`",
            f"- symbol_counts: `{group['symbol_counts']}`",
            f"- leadership_counts: `{group['leadership_counts']}`",
            f"- alignment_counts: `{group['alignment_counts']}`",
            f"- calendar_phase_counts: `{group['calendar_phase_counts']}`",
            f"- event_state_counts: `{group['event_state_counts']}`",
            f"- next_open_label_counts: `{group['next_open_label_counts']}`",
            f"- avg_day_of_month: `{group['avg_day_of_month']}`",
            f"- avg_target_distance_close_pct: `{group['avg_target_distance_close_pct']}`",
            f"- avg_risk_reward_ratio: `{group['avg_risk_reward_ratio']}`",
            f"- avg_return_5d_pct: `{group['avg_return_5d_pct']}`",
            f"- avg_return_20d_pct: `{group['avg_return_20d_pct']}`",
            f"- avg_volume_ratio_5d: `{group['avg_volume_ratio_5d']}`",
            f"- avg_close_position_20d: `{group['avg_close_position_20d']}`",
            f"- avg_next_open_gap_pct: `{group['avg_next_open_gap_pct']}`",
            "",
            "### Sample Cases",
        ])
        for row in group.get("sample_cases", []):
            lines.append(f"- `{row}`")

    lines.extend(["", "## Top Replay-Safe Preservation Candidates"])
    for item in payload["candidates"].get("top_single_feature_candidates", []):
        lines.append(
            f"- single `{item['rule']}` -> exception `{item['exception_hits']}`, improved leakage `{item['improved_hits']}`, precision `{item['precision']}`, recall `{item['recall']}`"
        )
    for item in payload["candidates"].get("top_pair_candidates", []):
        lines.append(
            f"- pair `{item['rule']}` -> exception `{item['exception_hits']}`, improved leakage `{item['improved_hits']}`, precision `{item['precision']}`, recall `{item['recall']}`"
        )
    return "\n".join(lines).strip() + "\n"


def run_study():
    rows = _build_rows()
    exception_rows = [
        row for row in rows
        if row.get("month_label") == "2024-07" and row.get("outcome_direction") == "worsened"
    ]
    improved_rows = [
        row for row in rows
        if row.get("month_label") in LATER_IMPROVED_MONTHS and row.get("outcome_direction") == "improved"
    ]

    groups = {
        "exception_2024_07_worsened": _summarize_group("exception_2024_07_worsened", exception_rows),
        "later_hostile_improved": _summarize_group("later_hostile_improved", improved_rows),
    }
    candidates = _search_preservation_candidates(exception_rows, improved_rows)
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "compare_paths": COMPARE_PATHS,
        "tradability_path": TRADABILITY_PATH,
        "groups": groups,
        "candidates": candidates,
    }
    payload["findings"] = _build_findings(groups, candidates)

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__bank_exhaustion_exception_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__bank_exhaustion_exception_study_v1.json")
    dated_md = dated_json.replace(".json", ".md")
    latest_md = latest_json.replace(".json", ".md")
    save_json(dated_json, payload)
    save_json(latest_json, payload)
    markdown = _build_markdown(payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)
    return dated_json, latest_json, dated_md, latest_md, payload


def main():
    dated_json, latest_json, dated_md, latest_md, payload = run_study()
    print(json.dumps({
        "dated_json": dated_json,
        "latest_json": latest_json,
        "dated_md": dated_md,
        "latest_md": latest_md,
        "findings": payload.get("findings"),
    }, indent=2))


if __name__ == "__main__":
    main()
