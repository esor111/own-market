"""
Research-only OCR enrichment prototype for timing-heavy NEPSE event notices.

Goal:
- enrich timing-heavy company-news notices with OCR-derived evidence lines
- keep OCR output as evidence only
- avoid changing replay rules or replacing the current publication-date event anchor

Usage:
    python event_attachment_ocr_enrichment.py

Recommended interpreter:
    automation\\.venv_ocr\\Scripts\\python event_attachment_ocr_enrichment.py
"""
import argparse
import json
import os
import re
import ssl
import urllib.request
from collections import Counter
from datetime import datetime
from io import BytesIO

import numpy as np
from PIL import Image
import pypdfium2 as pdfium

from config import VALIDATION_DIR

try:
    import easyocr
except Exception as exc:  # pragma: no cover - environment-dependent
    raise RuntimeError(
        "easyocr could not be imported in this environment. "
        "Run this script from the local OCR sandbox: automation\\.venv_ocr\\Scripts\\python."
    ) from exc


BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")
LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
USER_AGENT = "Mozilla/5.0 (compatible; MarketGistBot/1.0)"
UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()
NP_DIGIT_TRANSLATION = str.maketrans("०१२३४५६७८९", "0123456789")
TIMING_TYPES = {"book_closure", "agm_notice"}


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _load_company_news_records(year, run_label):
    path = os.path.join(
        BACKFILL_DIR,
        f"latest__{year}__{run_label}__nepse_company_news_backfill_v1.json",
    )
    if not os.path.exists(path):
        return []
    with open(path, "r", encoding="utf-8") as handle:
        payload = json.load(handle)
    return payload.get("records") or []


def _fetch_bytes(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=45, context=UNVERIFIED_SSL_CONTEXT) as response:
        return response.read()


def _render_notice_image(url):
    data = _fetch_bytes(url)
    lower = str(url).lower()
    if lower.endswith((".jpg", ".jpeg", ".png")):
        return Image.open(BytesIO(data)).convert("RGB"), "image_attachment"
    if lower.endswith(".pdf"):
        pdf = pdfium.PdfDocument(BytesIO(data))
        page = pdf[0]
        return page.render(scale=3).to_pil().convert("RGB"), "pdf_first_page"
    raise ValueError(f"Unsupported attachment type: {url}")


def _normalized_line(line):
    return str(line or "").translate(NP_DIGIT_TRANSLATION).strip()


def _semantic_hit(line):
    lowered = _normalized_line(line).lower()
    return any(token in lowered for token in ("book", "close", "agm", "record", "last trading"))


def _date_context_hit(line):
    normalized = _normalized_line(line)
    lowered = normalized.lower()
    has_date = bool(re.search(r"\b20\d{2}\b|\b\d{1,2}/\d{1,2}/\d{2,4}\b", normalized))
    has_context = any(token in lowered for token in ("book", "close", "agm", "record", "date")) or any(
        token in line for token in ("मिति", "गते", "सभा", "बन्द", "खारेज")
    )
    return has_date and has_context


def _select_records(records, max_per_event_type):
    records = [row for row in records if row.get("event_type") in TIMING_TYPES]
    records.sort(key=lambda row: (row.get("event_type") or "", row.get("published_date") or "", row.get("symbol") or ""))
    if not max_per_event_type or max_per_event_type < 0:
        return records
    kept = Counter()
    selected = []
    for row in records:
        event_type = row.get("event_type") or "unknown"
        if kept[event_type] >= max_per_event_type:
            continue
        kept[event_type] += 1
        selected.append(row)
    return selected


def build_event_attachment_ocr_enrichment(year, run_label, max_per_event_type):
    all_records = _load_company_news_records(year, run_label)
    records = _select_records(all_records, max_per_event_type)
    reader = easyocr.Reader(["en", "ne"], gpu=False, verbose=False)

    enriched_records = []
    status_counts = Counter()
    render_source_counts = Counter()

    for row in records:
        enriched = {
            "symbol": row.get("symbol"),
            "headline": row.get("headline"),
            "event_type": row.get("event_type"),
            "published_date": row.get("published_date"),
            "event_date": row.get("event_date"),
            "source_link": row.get("source_link"),
            "file_path": row.get("file_path"),
            "existing_book_close_date": row.get("book_close_date"),
            "existing_agm_date": row.get("agm_date"),
            "ocr_status": "pending",
            "ocr_render_source": None,
            "ocr_semantic_lines": [],
            "ocr_date_context_lines": [],
            "ocr_date_context_lines_normalized": [],
            "ocr_date_context_hit_count": 0,
            "ocr_semantic_hit_count": 0,
            "ocr_timing_evidence_flag": False,
        }

        try:
            image, render_source = _render_notice_image(row.get("source_link"))
            enriched["ocr_render_source"] = render_source
            render_source_counts.update([render_source])
        except Exception as exc:
            enriched["ocr_status"] = "render_error"
            enriched["ocr_error"] = repr(exc)
            status_counts.update([enriched["ocr_status"]])
            enriched_records.append(enriched)
            continue

        try:
            lines = reader.readtext(np.array(image), detail=0, paragraph=False)
        except Exception as exc:
            enriched["ocr_status"] = "ocr_error"
            enriched["ocr_error"] = repr(exc)
            status_counts.update([enriched["ocr_status"]])
            enriched_records.append(enriched)
            continue

        semantic_lines = [line for line in lines if _semantic_hit(line)]
        date_context_lines = [line for line in lines if _date_context_hit(line)]

        enriched["ocr_status"] = "ocr_ok"
        enriched["ocr_semantic_lines"] = semantic_lines[:8]
        enriched["ocr_date_context_lines"] = date_context_lines[:8]
        enriched["ocr_date_context_lines_normalized"] = [_normalized_line(line) for line in date_context_lines[:8]]
        enriched["ocr_date_context_hit_count"] = len(date_context_lines)
        enriched["ocr_semantic_hit_count"] = len(semantic_lines)
        enriched["ocr_timing_evidence_flag"] = bool(semantic_lines and date_context_lines)

        status_counts.update([enriched["ocr_status"]])
        enriched_records.append(enriched)

    notes = [
        "OCR evidence is stored as enrichment only and does not override published_date or existing body fields.",
        "This prototype focuses only on timing-heavy event types and the first page of each notice.",
    ]
    if any(record.get("ocr_timing_evidence_flag") for record in enriched_records):
        notes.append("Some notices produced both timing semantics and date-context lines, so OCR enrichment is worth keeping as a source-improvement path.")
    else:
        notes.append("No notices produced strong combined timing evidence in this run, so OCR remains exploratory.")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "prototype_name": "event_attachment_ocr_enrichment_v1",
        "year": year,
        "run_label": run_label,
        "source_candidate_count": len([row for row in all_records if row.get("event_type") in TIMING_TYPES]),
        "record_count": len(records),
        "max_per_event_type": max_per_event_type,
        "status_counts": dict(status_counts),
        "render_source_counts": dict(render_source_counts),
        "timing_evidence_record_count": sum(1 for record in enriched_records if record.get("ocr_timing_evidence_flag")),
        "notes": notes,
        "records": enriched_records,
    }


def _render_markdown(payload):
    lines = [
        "# Event Attachment OCR Enrichment",
        "",
        f"- built_at: `{payload['built_at']}`",
        f"- year: `{payload['year']}`",
        f"- run_label: `{payload['run_label']}`",
        f"- source_candidate_count: `{payload['source_candidate_count']}`",
        f"- record_count: `{payload['record_count']}`",
        f"- max_per_event_type: `{payload['max_per_event_type']}`",
        f"- status_counts: `{payload['status_counts']}`",
        f"- render_source_counts: `{payload['render_source_counts']}`",
        f"- timing_evidence_record_count: `{payload['timing_evidence_record_count']}`",
        "",
        "## Notes",
        "",
    ]
    for note in payload.get("notes") or []:
        lines.append(f"- {note}")

    lines.extend(["", "## Records With Timing Evidence", ""])
    evidence_rows = [row for row in payload.get("records") or [] if row.get("ocr_timing_evidence_flag")]
    if not evidence_rows:
        lines.append("- no strong timing-evidence records in this run")
    else:
        for row in evidence_rows:
            lines.append(
                f"- `{row['symbol']}` `{row['headline']}`: semantic_hits `{row['ocr_semantic_hit_count']}`, "
                f"date_context_hits `{row['ocr_date_context_hit_count']}`"
            )
            for line in row.get("ocr_date_context_lines_normalized") or []:
                lines.append(f"  evidence: `{line}`")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--year", type=int, default=2025)
    parser.add_argument("--run-label", default="replay_basket_v1")
    parser.add_argument("--max-per-event-type", type=int, default=3)
    args = parser.parse_args()

    payload = build_event_attachment_ocr_enrichment(
        year=args.year,
        run_label=args.run_label,
        max_per_event_type=args.max_per_event_type,
    )

    base = f"{args.year}__{args.run_label}__event_attachment_ocr_enrichment_v1"
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
        "timing_evidence_record_count": payload["timing_evidence_record_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
