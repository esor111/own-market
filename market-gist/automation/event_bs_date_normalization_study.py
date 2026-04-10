"""
Research-only BS-date normalization study for OCR-derived timing evidence.

Goal:
- parse BS-style date snippets from OCR timing evidence lines
- convert them to Gregorian hints using a tested BS calendar library
- keep the result as evidence only

Usage:
    python event_bs_date_normalization_study.py --year 2025 --run-label replay_basket_v1

Recommended interpreter:
    automation\\.venv_ocr\\Scripts\\python event_bs_date_normalization_study.py
"""
import argparse
import json
import os
import re
from datetime import datetime

from config import VALIDATION_DIR

try:
    import bikram_sambat as bs
except Exception as exc:  # pragma: no cover - environment-dependent
    raise RuntimeError(
        "bikram_sambat could not be imported in this environment. "
        "Run this script from the local OCR sandbox: automation\\.venv_ocr\\Scripts\\python."
    ) from exc


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
NP_DIGIT_TRANSLATION = str.maketrans("०१२३४५६७८९", "0123456789")
MONTH_MAP = {
    "बैशाख": 1,
    "बैसाख": 1,
    "वैशाख": 1,
    "जेठ": 2,
    "जेष्ठ": 2,
    "असार": 3,
    "आषाढ": 3,
    "श्रावण": 4,
    "साउन": 4,
    "भाद्र": 5,
    "भदौ": 5,
    "भाद्रपद": 5,
    "असोज": 6,
    "आश्विन": 6,
    "कार्तिक": 7,
    "कात्तिक": 7,
    "मंसिर": 8,
    "मार्ग": 8,
    "पुष": 9,
    "पुस": 9,
    "माघ": 10,
    "फागुन": 11,
    "फाल्गुण": 11,
    "चैत": 12,
    "चैत्र": 12,
}


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _load_ocr_enrichment_payload(year, run_label):
    path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"latest__{year}__{run_label}__event_attachment_ocr_enrichment_v1.json",
    )
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _normalize_text(value):
    return str(value or "").translate(NP_DIGIT_TRANSLATION).strip()


def _parse_bs_dates_from_line(line):
    text = _normalize_text(line)
    candidates = []

    for year, month, day in re.findall(r"\b(20\d{2})/(\d{1,2})/(\d{1,2})\b", text):
        candidates.append({
            "raw_match": f"{year}/{month}/{day}",
            "parse_type": "slash_numeric",
            "year": int(year),
            "month": int(month),
            "day": int(day),
        })

    month_pattern = "|".join(sorted((re.escape(name) for name in MONTH_MAP), key=len, reverse=True))
    for year, month_name, day in re.findall(rf"\b(20\d{{2}})\s+({month_pattern})\s+(\d{{1,2}})\b", text):
        candidates.append({
            "raw_match": f"{year} {month_name} {day}",
            "parse_type": "named_month",
            "year": int(year),
            "month": MONTH_MAP[month_name],
            "day": int(day),
            "month_name": month_name,
        })

    return candidates


def _convert_bs_candidate(candidate):
    try:
        bs_date = bs.date(candidate["year"], candidate["month"], candidate["day"])
        ad_date = bs_date.togregorian()
    except Exception as exc:
        return {
            **candidate,
            "conversion_status": "conversion_error",
            "error": repr(exc),
        }

    return {
        **candidate,
        "conversion_status": "ok",
        "bs_iso": str(bs_date),
        "ad_iso": ad_date.isoformat(),
    }


def build_event_bs_date_normalization_study(year, run_label):
    payload = _load_ocr_enrichment_payload(year, run_label)
    records = payload.get("records") or []
    summary_rows = []
    conversion_status_counts = {}
    parsed_line_count = 0
    converted_date_count = 0

    for row in records:
        record_summary = {
            "symbol": row.get("symbol"),
            "headline": row.get("headline"),
            "event_type": row.get("event_type"),
            "ocr_timing_evidence_flag": bool(row.get("ocr_timing_evidence_flag")),
            "normalized_line_count": len(row.get("ocr_date_context_lines_normalized") or []),
            "parsed_candidates": [],
        }
        for line in row.get("ocr_date_context_lines_normalized") or []:
            parsed = _parse_bs_dates_from_line(line)
            if parsed:
                parsed_line_count += 1
            for candidate in parsed:
                converted = _convert_bs_candidate(candidate)
                record_summary["parsed_candidates"].append({
                    "source_line": line,
                    **converted,
                })
                status = converted["conversion_status"]
                conversion_status_counts[status] = conversion_status_counts.get(status, 0) + 1
                if status == "ok":
                    converted_date_count += 1
        summary_rows.append(record_summary)

    notes = [
        "This study only normalizes OCR-derived timing evidence and does not alter replay event fields.",
        "Named-month parsing currently targets common Nepali BS month names seen in OCR outputs.",
    ]
    if converted_date_count:
        notes.append("At least some OCR-derived BS dates can now be converted into Gregorian hints successfully.")
    else:
        notes.append("No OCR-derived BS dates converted successfully in this run, so OCR evidence remains text-only for now.")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "study_name": "event_bs_date_normalization_study_v1",
        "year": year,
        "run_label": run_label,
        "record_count": len(summary_rows),
        "parsed_line_count": parsed_line_count,
        "converted_date_count": converted_date_count,
        "conversion_status_counts": conversion_status_counts,
        "notes": notes,
        "records": summary_rows,
    }


def _render_markdown(payload):
    lines = [
        "# Event BS-Date Normalization Study",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- year: `{payload['year']}`",
        f"- run_label: `{payload['run_label']}`",
        f"- record_count: `{payload['record_count']}`",
        f"- parsed_line_count: `{payload['parsed_line_count']}`",
        f"- converted_date_count: `{payload['converted_date_count']}`",
        f"- conversion_status_counts: `{payload['conversion_status_counts']}`",
        "",
        "## Notes",
        "",
    ]
    for note in payload.get("notes") or []:
        lines.append(f"- {note}")

    lines.extend(["", "## Converted Candidates", ""])
    any_rows = False
    for row in payload.get("records") or []:
        converted = [item for item in row.get("parsed_candidates") or [] if item.get("conversion_status") == "ok"]
        if not converted:
            continue
        any_rows = True
        lines.append(f"### `{row['symbol']}` `{row['headline']}`")
        lines.append("")
        for item in converted:
            lines.append(
                f"- `{item['raw_match']}` -> BS `{item['bs_iso']}` -> AD `{item['ad_iso']}`"
            )
            lines.append(f"  source: `{item['source_line']}`")
        lines.append("")
    if not any_rows:
        lines.append("- no converted candidates in this run")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--run-label", default="replay_basket_v1")
    args = parser.parse_args()

    payload = build_event_bs_date_normalization_study(args.year, args.run_label)

    base = f"{args.year}__{args.run_label}__event_bs_date_normalization_study_v1"
    dated_json_path = os.path.join(LEARNING_REVIEWS_DIR, f"{base}.json")
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, f"latest__{base}.json")
    dated_md_path = os.path.join(LEARNING_REVIEWS_DIR, f"{base}.md")
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, f"latest__{base}.md")

    markdown = _render_markdown(payload)
    save_json(dated_json_path, payload)
    save_json(latest_json_path, payload)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)

    print(json.dumps({
        "record_count": payload["record_count"],
        "parsed_line_count": payload["parsed_line_count"],
        "converted_date_count": payload["converted_date_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
