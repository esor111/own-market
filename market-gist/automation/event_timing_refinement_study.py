"""
Research-only event timing refinement study.

Goal:
- determine whether the current replay bucket `matched_but_stale` is too broad
- measure whether richer timing fields (book_close_date / agm_date) are usable
- see whether changed bank hostile-window cases cluster in a more refined timing bucket

Usage:
    python event_timing_refinement_study.py
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

from bank_hostile_window_gap_study import build_rows
from config import VALIDATION_DIR, load_json_file


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")
BANK_SECTORS = {"COMMERCIAL BANKS", "DEVELOPMENT BANKS"}

ACTIVE_COMPARE_PATHS = [
    os.path.join(
        OUTPUT_DIR,
        "latest__2023-07-01_to_2023-07-31__daily_truth_replay_jul2023_eventcovered_champion_v1__vs__daily_truth_replay_jul2023_eventcovered_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2023-08-01_to_2023-08-31__daily_truth_replay_aug2023_eventcovered_champion_v1__vs__daily_truth_replay_aug2023_eventcovered_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2024-08-01_to_2024-08-31__daily_truth_replay_aug2024_eventcovered_champion_v1__vs__daily_truth_replay_aug2024_eventcovered_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
    ),
    os.path.join(
        OUTPUT_DIR,
        "latest__2025-08-01_to_2025-08-31__daily_truth_replay_august_champion_v1__vs__daily_truth_replay_aug2025_calendarconfidence_sectoraware_v1__replay_champion_challenger_compare_v1.json",
    ),
]


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _parse_session_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _parse_aux_date(value):
    text = str(value or "").strip()
    if not text:
        return None, "missing"
    if "-" in text:
        try:
            return datetime.strptime(text, "%Y-%m-%d").date(), "iso"
        except ValueError:
            return None, "unparseable"

    parts = text.split("/")
    if len(parts) != 3:
        return None, "unparseable"

    try:
        a, b, year = [int(part) for part in parts]
    except ValueError:
        return None, "unparseable"

    if year >= 2070:
        return None, "bs_like"

    if a > 12:
        day, month = a, b
        fmt_label = "dmy"
    elif b > 12:
        month, day = a, b
        fmt_label = "mdy"
    else:
        return None, "ambiguous_slash"

    try:
        return datetime(year, month, day).date(), fmt_label
    except ValueError:
        return None, "unparseable"


def _coarse_event_state(context):
    if context.get("has_active_event"):
        return "active_event"
    if int(context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _collect_event_rows():
    rows = []
    for year in (2023, 2024, 2025):
        payload = load_json_file(
            os.path.join(BACKFILL_DIR, f"latest__{year}__replay_basket_v1__corporate_action_timeline_v1.json"),
            {},
        )
        rows.extend(payload.get("records") or [])
    return rows


def _timeline_aux_coverage():
    summary = {
        "record_count": 0,
        "event_date_basis_counts": Counter(),
        "has_any_aux_date_count": 0,
        "book_close_parse_status": Counter(),
        "agm_parse_status": Counter(),
        "records_with_parseable_aux": 0,
        "records_with_only_unusable_aux": 0,
    }
    for row in _collect_event_rows():
        summary["record_count"] += 1
        summary["event_date_basis_counts"].update([row.get("event_date_basis") or "unknown"])
        aux_statuses = []
        if row.get("book_close_date"):
            _, status = _parse_aux_date(row.get("book_close_date"))
            summary["book_close_parse_status"].update([status])
            aux_statuses.append(status)
        if row.get("agm_date"):
            _, status = _parse_aux_date(row.get("agm_date"))
            summary["agm_parse_status"].update([status])
            aux_statuses.append(status)
        if aux_statuses:
            summary["has_any_aux_date_count"] += 1
            if any(status in {"iso", "dmy", "mdy"} for status in aux_statuses):
                summary["records_with_parseable_aux"] += 1
            elif all(status in {"bs_like", "ambiguous_slash", "unparseable"} for status in aux_statuses):
                summary["records_with_only_unusable_aux"] += 1

    summary["event_date_basis_counts"] = dict(summary["event_date_basis_counts"])
    summary["book_close_parse_status"] = dict(summary["book_close_parse_status"])
    summary["agm_parse_status"] = dict(summary["agm_parse_status"])
    return summary


def _refined_timing_bucket(row):
    session_date = _parse_session_date(row.get("session_date"))
    if not session_date:
        return "missing_session_date", {}

    event_context = row.get("event_context") or {}
    coarse_state = _coarse_event_state(event_context)
    if coarse_state == "no_symbol_event_match":
        return coarse_state, {"coarse_event_state": coarse_state}
    if coarse_state == "active_event":
        return "active_publication_window", {"coarse_event_state": coarse_state}

    matched_events = []
    seen = set()
    for event in (event_context.get("active_events") or []) + (event_context.get("recent_events") or []):
        record_id = event.get("record_id")
        if record_id in seen:
            continue
        seen.add(record_id)
        matched_events.append(event)

    if not matched_events:
        return "stale_no_recent_event_payload", {
            "coarse_event_state": coarse_state,
            "aux_parse_status_counts": {},
            "nearest_future_aux_days": None,
            "nearest_future_aux_basis": None,
        }

    parse_status_counter = Counter()
    nearest_future_days = None
    nearest_future_basis = None
    past_or_same_aux = False

    for event in matched_events:
        for field_name in ("book_close_date", "agm_date"):
            raw_value = event.get(field_name)
            if not raw_value:
                continue
            parsed_date, status = _parse_aux_date(raw_value)
            parse_status_counter.update([status])
            if not parsed_date:
                continue
            delta_days = (parsed_date - session_date).days
            if delta_days >= 0:
                if nearest_future_days is None or delta_days < nearest_future_days:
                    nearest_future_days = delta_days
                    nearest_future_basis = field_name
            else:
                past_or_same_aux = True

    extra = {
        "coarse_event_state": coarse_state,
        "aux_parse_status_counts": dict(parse_status_counter),
        "nearest_future_aux_days": nearest_future_days,
        "nearest_future_aux_basis": nearest_future_basis,
    }

    if nearest_future_days is not None:
        if nearest_future_days <= 7:
            return "stale_upcoming_effective_0_7d", extra
        if nearest_future_days <= 14:
            return "stale_upcoming_effective_8_14d", extra
        if nearest_future_days <= 30:
            return "stale_upcoming_effective_15_30d", extra
        return "stale_upcoming_effective_31d_plus", extra

    if parse_status_counter:
        if any(status in {"bs_like", "ambiguous_slash", "unparseable"} for status in parse_status_counter):
            return "stale_aux_present_but_unusable", extra
        if past_or_same_aux:
            return "stale_effective_date_already_passed", extra

    return "stale_no_aux_effective_date", extra


def _study_changed_bank_cases():
    rows = build_rows(ACTIVE_COMPARE_PATHS)
    bank_rows = [row for row in rows if row.get("sector_name") in BANK_SECTORS]

    bucket_counts = Counter()
    direction_bucket_counts = defaultdict(Counter)
    symbol_counts = defaultdict(Counter)
    sample_rows = []

    for row in bank_rows:
        bucket, extra = _refined_timing_bucket(row)
        direction = row.get("outcome_direction") or "unknown"
        bucket_counts.update([bucket])
        direction_bucket_counts[direction].update([bucket])
        symbol_counts[bucket].update([row.get("symbol") or "UNKNOWN"])
        if len(sample_rows) < 20:
            sample_rows.append({
                "session_id": row.get("session_id"),
                "symbol": row.get("symbol"),
                "outcome_direction": direction,
                "coarse_event_state": extra.get("coarse_event_state"),
                "refined_event_timing_bucket": bucket,
                "nearest_future_aux_days": extra.get("nearest_future_aux_days"),
                "nearest_future_aux_basis": extra.get("nearest_future_aux_basis"),
                "aux_parse_status_counts": extra.get("aux_parse_status_counts"),
            })

    return {
        "case_count": len(bank_rows),
        "refined_bucket_counts": dict(bucket_counts),
        "direction_bucket_counts": {key: dict(value) for key, value in direction_bucket_counts.items()},
        "bucket_symbol_counts": {
            bucket: [{"label": label, "count": count} for label, count in counter.most_common(8)]
            for bucket, counter in symbol_counts.items()
        },
        "sample_rows": sample_rows,
    }


def _build_findings(timeline_summary, case_summary):
    findings = []
    findings.append(
        f"Across replay-basket corporate-action records, `{timeline_summary['has_any_aux_date_count']}` records contain auxiliary timing fields, but only `{timeline_summary['records_with_parseable_aux']}` have clearly parseable Gregorian auxiliary dates."
    )
    findings.append(
        f"In the active bank hostile-window changed cases, the refined timing buckets were `{case_summary['refined_bucket_counts']}`."
    )
    if case_summary["refined_bucket_counts"].get("stale_aux_present_but_unusable", 0) > 0:
        findings.append(
            "A meaningful share of stale matched cases carry auxiliary timing fields that are currently unusable because they are ambiguous or BS-like, which means source/timeline quality is part of the problem."
        )
    if case_summary["refined_bucket_counts"].get("stale_upcoming_effective_0_7d", 0) or case_summary["refined_bucket_counts"].get("stale_upcoming_effective_8_14d", 0):
        findings.append(
            "Some stale publication-date cases still sit close to an upcoming effective date, so `matched_but_stale` is too coarse and should eventually split that subcase out."
        )
    else:
        findings.append(
            "In the active bank hostile-window validation cases we studied, there was little or no evidence that `matched_but_stale` was masking many near-term upcoming effective dates."
        )
    findings.append(
        "The next likely improvement is to refine the timeline source and parsing quality first, then revisit bucket splitting with better effective-date coverage."
    )
    return findings


def _build_markdown(payload):
    lines = [
        "# Event Timing Refinement Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        "",
        "## Findings",
    ]
    for finding in payload["findings"]:
        lines.append(f"- {finding}")

    lines.extend([
        "",
        "## Timeline Coverage",
        f"- event_date_basis_counts: `{payload['timeline_aux_coverage']['event_date_basis_counts']}`",
        f"- has_any_aux_date_count: `{payload['timeline_aux_coverage']['has_any_aux_date_count']}`",
        f"- records_with_parseable_aux: `{payload['timeline_aux_coverage']['records_with_parseable_aux']}`",
        f"- records_with_only_unusable_aux: `{payload['timeline_aux_coverage']['records_with_only_unusable_aux']}`",
        f"- book_close_parse_status: `{payload['timeline_aux_coverage']['book_close_parse_status']}`",
        f"- agm_parse_status: `{payload['timeline_aux_coverage']['agm_parse_status']}`",
        "",
        "## Active Bank Hostile-Window Changed Cases",
        f"- case_count: `{payload['changed_bank_case_study']['case_count']}`",
        f"- refined_bucket_counts: `{payload['changed_bank_case_study']['refined_bucket_counts']}`",
        f"- direction_bucket_counts: `{payload['changed_bank_case_study']['direction_bucket_counts']}`",
        "",
        "## Sample Rows",
    ])
    for item in payload["changed_bank_case_study"]["sample_rows"]:
        lines.append(f"- `{item}`")
    return "\n".join(lines).strip() + "\n"


def run_study():
    timeline_summary = _timeline_aux_coverage()
    case_summary = _study_changed_bank_cases()
    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "timeline_aux_coverage": timeline_summary,
        "changed_bank_case_study": case_summary,
    }
    payload["findings"] = _build_findings(timeline_summary, case_summary)

    dated_json = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_timing_refinement_study_v1.json",
    )
    latest_json = os.path.join(OUTPUT_DIR, "latest__event_timing_refinement_study_v1.json")
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
        "findings": payload["findings"],
    }, indent=2))


if __name__ == "__main__":
    main()
