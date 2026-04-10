"""
Research-only validation of OCR-aware event timing on targeted fresh replay windows.

Goal:
- inspect fresh frozen cases built after OCR timing integration
- compare coarse stale-event state against OCR-aware refined timing buckets
- see whether `matched_but_stale` becomes more informative on windows where OCR hints should matter

Usage:
    python event_timing_ocr_window_validation.py REPLAY_ID [REPLAY_ID ...]
"""
import json
import os
import sys
from collections import Counter
from datetime import datetime

from config import REPLAYS_DIR, VALIDATION_DIR


OUTPUT_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def load_json(path):
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _parse_date(value):
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
        parsed = _parse_date(event.get(field_name))
        if parsed:
            aux_candidates.append((field_name, parsed))
    for candidate in event.get("ocr_date_hint_candidates") or []:
        parsed = _parse_date(candidate.get("ad_iso"))
        if parsed:
            aux_candidates.append(("ocr_hint", parsed))
    return aux_candidates


def _refined_bucket(context, session_date):
    coarse_state = _coarse_event_state(context)
    if coarse_state in {"no_symbol_event_match", "active_event"}:
        return coarse_state, {"nearest_future_aux_days": None, "nearest_future_aux_basis": None, "ocr_hint_event_count": 0}

    matched_events = []
    seen = set()
    for event in (context.get("active_events") or []) + (context.get("recent_events") or []):
        record_id = event.get("record_id")
        if record_id in seen:
            continue
        seen.add(record_id)
        matched_events.append(event)

    nearest_future_days = None
    nearest_future_basis = None
    ocr_hint_event_count = 0
    past_or_same = False

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
                past_or_same = True

    extra = {
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

    if past_or_same:
        return "stale_effective_date_already_passed", extra
    return "stale_no_aux_effective_date", extra


def _load_frozen_case(replay_id, session_date, symbol):
    path = os.path.join(
        REPLAYS_DIR,
        replay_id,
        "sessions",
        session_date,
        symbol,
        "normalized",
        f"{session_date}__{symbol}__frozen_case_v1.json",
    )
    return load_json(path)


def build_validation(replay_ids):
    rows = []
    for replay_id in replay_ids:
        summary = load_json(os.path.join(REPLAYS_DIR, replay_id, "summaries", "latest__replay_summary_v1.json"))
        for record in summary.get("records", []):
            session_id = record.get("session_id") or ""
            session_date = record.get("session_date")
            symbol = record.get("symbol")
            if not session_date or not symbol:
                continue
            frozen_case = _load_frozen_case(replay_id, session_date, symbol)
            context = (((frozen_case.get("historical_context") or {}).get("corporate_action_context")) or {})
            session_dt = _parse_date(session_date)
            if not session_dt:
                continue
            coarse = _coarse_event_state(context)
            refined, extra = _refined_bucket(context, session_dt)
            rows.append({
                "replay_id": replay_id,
                "session_id": session_id,
                "session_date": session_date,
                "symbol": symbol,
                "coarse_event_state": coarse,
                "refined_event_timing_bucket": refined,
                "matched_event_count": int(context.get("matched_event_count") or 0),
                "active_event_count": int(context.get("active_event_count") or 0),
                "recent_event_count_90d": int(context.get("recent_event_count_90d") or 0),
                "nearest_future_aux_days": extra.get("nearest_future_aux_days"),
                "nearest_future_aux_basis": extra.get("nearest_future_aux_basis"),
                "ocr_hint_event_count": int(extra.get("ocr_hint_event_count") or 0),
            })

    coarse_counts = Counter(row["coarse_event_state"] for row in rows)
    refined_counts = Counter(row["refined_event_timing_bucket"] for row in rows)
    basis_counts = Counter(row["nearest_future_aux_basis"] for row in rows if row.get("nearest_future_aux_basis"))
    moved_rows = [
        row for row in rows
        if row["coarse_event_state"] == "matched_but_stale"
        and row["refined_event_timing_bucket"].startswith("stale_upcoming_effective_")
    ]
    informative_rows = [
        row for row in rows
        if row["coarse_event_state"] in {"matched_but_stale", "recent_event_no_active"}
        and row["refined_event_timing_bucket"].startswith("stale_upcoming_effective_")
    ]

    notes = [
        "This study only validates fresh replay windows built after OCR timing integration.",
        "It measures whether previously coarse stale-event cases become more informative when OCR-derived date hints are available.",
    ]
    if moved_rows:
        notes.append("At least some `matched_but_stale` cases now become explicit upcoming-effective-date buckets.")
    else:
        notes.append("No `matched_but_stale` cases moved into OCR-aware upcoming-effective buckets in this run.")
    if informative_rows:
        notes.append("OCR-aware timing did improve the broader stale-event family in this run, even where the strict `matched_but_stale` subset did not move.")
    else:
        notes.append("No broader stale-event-family cases became OCR-aware upcoming-effective buckets in this run.")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "study_name": "event_timing_ocr_window_validation_v1",
        "replay_ids": replay_ids,
        "case_count": len(rows),
        "coarse_event_state_counts": dict(coarse_counts),
        "refined_event_timing_bucket_counts": dict(refined_counts),
        "nearest_future_basis_counts": dict(basis_counts),
        "moved_case_count": len(moved_rows),
        "moved_symbol_counts": dict(Counter(row["symbol"] for row in moved_rows)),
        "stale_family_informative_case_count": len(informative_rows),
        "stale_family_informative_symbol_counts": dict(Counter(row["symbol"] for row in informative_rows)),
        "notes": notes,
        "sample_rows": moved_rows[:12],
        "sample_informative_rows": informative_rows[:12],
    }


def _render_markdown(payload):
    lines = [
        "# Event Timing OCR Window Validation",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- replay_ids: `{payload['replay_ids']}`",
        f"- case_count: `{payload['case_count']}`",
        f"- coarse_event_state_counts: `{payload['coarse_event_state_counts']}`",
        f"- refined_event_timing_bucket_counts: `{payload['refined_event_timing_bucket_counts']}`",
        f"- nearest_future_basis_counts: `{payload['nearest_future_basis_counts']}`",
        f"- moved_case_count: `{payload['moved_case_count']}`",
        f"- moved_symbol_counts: `{payload['moved_symbol_counts']}`",
        f"- stale_family_informative_case_count: `{payload['stale_family_informative_case_count']}`",
        f"- stale_family_informative_symbol_counts: `{payload['stale_family_informative_symbol_counts']}`",
        "",
        "## Notes",
        "",
    ]
    for note in payload.get("notes") or []:
        lines.append(f"- {note}")
    lines.extend(["", "## Sample Moved Cases", ""])
    if not payload.get("sample_rows"):
        lines.append("- no moved cases in this run")
    else:
        for row in payload["sample_rows"]:
            lines.append(f"- `{row}`")
    lines.extend(["", "## Sample Informative Stale-Family Cases", ""])
    if not payload.get("sample_informative_rows"):
        lines.append("- no informative stale-family cases in this run")
    else:
        for row in payload["sample_informative_rows"]:
            lines.append(f"- `{row}`")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python event_timing_ocr_window_validation.py REPLAY_ID [REPLAY_ID ...]")
        sys.exit(1)

    replay_ids = sys.argv[1:]
    payload = build_validation(replay_ids)

    dated_json_path = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_timing_ocr_window_validation_v1.json",
    )
    latest_json_path = os.path.join(OUTPUT_DIR, "latest__event_timing_ocr_window_validation_v1.json")
    dated_md_path = os.path.join(
        OUTPUT_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_timing_ocr_window_validation_v1.md",
    )
    latest_md_path = os.path.join(OUTPUT_DIR, "latest__event_timing_ocr_window_validation_v1.md")

    markdown = _render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)

    print(json.dumps({
        "case_count": payload["case_count"],
        "moved_case_count": payload["moved_case_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
