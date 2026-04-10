"""
Research-only event timing refinement study that includes OCR-derived date hints.

Goal:
- reuse the earlier event timing refinement framing
- let OCR-derived Gregorian hint dates participate as auxiliary effective dates
- measure whether stale event rows become more informative

Usage:
    python event_timing_refinement_with_ocr_study.py
"""
import json
import os
from collections import Counter, defaultdict
from datetime import datetime

from bank_hostile_window_gap_study import build_rows
from config import VALIDATION_DIR, load_json_file


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
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


def _parse_iso_date(value):
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def _coarse_event_state(context):
    if context.get("has_active_event"):
        return "active_event"
    if int(context.get("recent_event_count_90d") or 0) > 0:
        return "recent_event_no_active"
    if int(context.get("matched_event_count") or 0) > 0:
        return "matched_but_stale"
    return "no_symbol_event_match"


def _collect_aux_dates(event):
    aux_candidates = []
    for field_name in ("book_close_date", "agm_date"):
        parsed = _parse_iso_date(event.get(field_name))
        if parsed:
            aux_candidates.append((field_name, parsed))
    for candidate in event.get("ocr_date_hint_candidates") or []:
        parsed = _parse_iso_date(candidate.get("ad_iso"))
        if parsed:
            aux_candidates.append(("ocr_hint", parsed))
    return aux_candidates


def _refined_timing_bucket_with_ocr(row):
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
            "nearest_future_aux_days": None,
            "nearest_future_aux_basis": None,
        }

    nearest_future_days = None
    nearest_future_basis = None
    past_or_same_aux = False
    ocr_hint_event_count = 0

    for event in matched_events:
        aux_candidates = _collect_aux_dates(event)
        if any(basis == "ocr_hint" for basis, _ in aux_candidates):
            ocr_hint_event_count += 1
        for basis, parsed_date in aux_candidates:
            delta_days = (parsed_date - session_date).days
            if delta_days >= 0:
                if nearest_future_days is None or delta_days < nearest_future_days:
                    nearest_future_days = delta_days
                    nearest_future_basis = basis
            else:
                past_or_same_aux = True

    extra = {
        "coarse_event_state": coarse_state,
        "nearest_future_aux_days": nearest_future_days,
        "nearest_future_aux_basis": nearest_future_basis,
        "ocr_hint_event_count": ocr_hint_event_count,
    }

    if nearest_future_days is not None:
        if nearest_future_days <= 7:
            return "stale_upcoming_effective_0_7d", extra
        if nearest_future_days <= 14:
            return "stale_upcoming_effective_8_14d", extra
        if nearest_future_days <= 30:
            return "stale_upcoming_effective_15_30d", extra
        return "stale_upcoming_effective_31d_plus", extra

    if past_or_same_aux:
        return "stale_effective_date_already_passed", extra
    return "stale_no_aux_effective_date", extra


def build_event_timing_refinement_with_ocr_study():
    rows = build_rows(ACTIVE_COMPARE_PATHS)
    bank_rows = [row for row in rows if row.get("sector_name") in BANK_SECTORS]

    bucket_counts = Counter()
    direction_bucket_counts = defaultdict(Counter)
    basis_counts = Counter()
    ocr_hint_rows = 0
    sample_rows = []

    for row in bank_rows:
        bucket, extra = _refined_timing_bucket_with_ocr(row)
        direction = row.get("outcome_direction") or "unknown"
        bucket_counts.update([bucket])
        direction_bucket_counts[direction].update([bucket])
        if extra.get("nearest_future_aux_basis"):
            basis_counts.update([extra["nearest_future_aux_basis"]])
        if int(extra.get("ocr_hint_event_count") or 0) > 0:
            ocr_hint_rows += 1
        if len(sample_rows) < 20:
            sample_rows.append({
                "session_id": row.get("session_id"),
                "symbol": row.get("symbol"),
                "outcome_direction": direction,
                "refined_event_timing_bucket": bucket,
                "nearest_future_aux_days": extra.get("nearest_future_aux_days"),
                "nearest_future_aux_basis": extra.get("nearest_future_aux_basis"),
                "ocr_hint_event_count": extra.get("ocr_hint_event_count"),
            })

    notes = [
        "This study re-runs stale-event refinement with OCR-derived Gregorian hint dates allowed as auxiliary effective-date candidates.",
        "This is still research-only and does not change replay rules.",
    ]
    if basis_counts.get("ocr_hint", 0):
        notes.append("At least some stale cases now surface OCR-derived future-effective timing hints.")
    else:
        notes.append("OCR-derived hints did not materially change the active hostile-window bank stale buckets in this run.")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "study_name": "event_timing_refinement_with_ocr_study_v1",
        "comparison_count": len(rows),
        "bank_case_count": len(bank_rows),
        "ocr_hint_rows": ocr_hint_rows,
        "refined_bucket_counts": dict(bucket_counts),
        "direction_bucket_counts": {key: dict(value) for key, value in direction_bucket_counts.items()},
        "nearest_future_basis_counts": dict(basis_counts),
        "notes": notes,
        "sample_rows": sample_rows,
    }


def _render_markdown(payload):
    lines = [
        "# Event Timing Refinement With OCR Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- comparison_count: `{payload['comparison_count']}`",
        f"- bank_case_count: `{payload['bank_case_count']}`",
        f"- ocr_hint_rows: `{payload['ocr_hint_rows']}`",
        f"- refined_bucket_counts: `{payload['refined_bucket_counts']}`",
        f"- nearest_future_basis_counts: `{payload['nearest_future_basis_counts']}`",
        "",
        "## Notes",
        "",
    ]
    for note in payload.get("notes") or []:
        lines.append(f"- {note}")
    lines.extend(["", "## Sample Rows", ""])
    for row in payload.get("sample_rows") or []:
        lines.append(f"- `{row}`")
    return "\n".join(lines) + "\n"


def main():
    payload = build_event_timing_refinement_with_ocr_study()

    dated_json_path = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_timing_refinement_with_ocr_study_v1.json",
    )
    latest_json_path = os.path.join(OUTPUT_DIR, "latest__event_timing_refinement_with_ocr_study_v1.json")
    dated_md_path = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_timing_refinement_with_ocr_study_v1.md",
    )
    latest_md_path = os.path.join(OUTPUT_DIR, "latest__event_timing_refinement_with_ocr_study_v1.md")

    markdown = _render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)

    print(json.dumps({
        "bank_case_count": payload["bank_case_count"],
        "ocr_hint_rows": payload["ocr_hint_rows"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
