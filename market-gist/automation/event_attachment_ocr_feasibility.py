"""
Research-only OCR feasibility audit for NEPSE event attachments.

Goal:
- check whether OCR can recover timing-relevant lines from scan-style NEPSE notices
- focus on timing-heavy event types like book closure and AGM notices
- measure feasibility before any source-upgrade implementation

Usage:
    python event_attachment_ocr_feasibility.py

Recommended interpreter:
    automation\\.venv_ocr\\Scripts\\python event_attachment_ocr_feasibility.py
"""
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


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")
USER_AGENT = "Mozilla/5.0 (compatible; MarketGistBot/1.0)"
UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()
NP_DIGIT_TRANSLATION = str.maketrans("०१२३४५६७८९", "0123456789")
TIMING_TYPES = {"book_closure", "agm_notice"}
TARGET_YEAR = 2025
TARGET_RUN_LABEL = "replay_basket_v1"
MAX_PER_EVENT_TYPE = 2


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _load_company_news_records():
    path = os.path.join(
        BACKFILL_DIR,
        f"latest__{TARGET_YEAR}__{TARGET_RUN_LABEL}__nepse_company_news_backfill_v1.json",
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


def build_event_attachment_ocr_feasibility():
    raw_records = [row for row in _load_company_news_records() if row.get("event_type") in TIMING_TYPES]
    raw_records.sort(key=lambda row: (row.get("event_type") or "", row.get("published_date") or "", row.get("symbol") or ""))
    kept = Counter()
    records = []
    for row in raw_records:
        event_type = row.get("event_type") or "unknown"
        if kept[event_type] >= MAX_PER_EVENT_TYPE:
            continue
        kept[event_type] += 1
        records.append(row)
    reader = easyocr.Reader(["en", "ne"], gpu=False, verbose=False)

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "study_name": "event_attachment_ocr_feasibility_v1",
        "target_year": TARGET_YEAR,
        "target_run_label": TARGET_RUN_LABEL,
        "record_count": len(records),
        "source_candidate_count": len(raw_records),
        "max_per_event_type": MAX_PER_EVENT_TYPE,
        "event_type_counts": dict(Counter(row.get("event_type") for row in records)),
        "render_source_counts": Counter(),
        "ocr_status_counts": Counter(),
        "semantic_hit_count": 0,
        "date_context_hit_count": 0,
        "semantic_and_date_context_hit_count": 0,
        "examples": {
            "semantic_and_date_hits": [],
            "semantic_only_hits": [],
            "ocr_failures": [],
        },
        "notes": [],
    }

    for row in records:
        sample = {
            "symbol": row.get("symbol"),
            "headline": row.get("headline"),
            "event_type": row.get("event_type"),
            "source_link": row.get("source_link"),
        }
        try:
            image, render_source = _render_notice_image(row.get("source_link"))
            summary["render_source_counts"].update([render_source])
        except Exception as exc:
            summary["ocr_status_counts"].update(["render_error"])
            if len(summary["examples"]["ocr_failures"]) < 5:
                sample["error"] = repr(exc)
                summary["examples"]["ocr_failures"].append(sample)
            continue

        try:
            lines = reader.readtext(np.array(image), detail=0, paragraph=False)
            summary["ocr_status_counts"].update(["ocr_ok"])
        except Exception as exc:
            summary["ocr_status_counts"].update(["ocr_error"])
            if len(summary["examples"]["ocr_failures"]) < 5:
                sample["error"] = repr(exc)
                summary["examples"]["ocr_failures"].append(sample)
            continue

        semantic_lines = [line for line in lines if _semantic_hit(line)]
        date_context_lines = [line for line in lines if _date_context_hit(line)]

        if semantic_lines:
            summary["semantic_hit_count"] += 1
        if date_context_lines:
            summary["date_context_hit_count"] += 1
        if semantic_lines and date_context_lines:
            summary["semantic_and_date_context_hit_count"] += 1

        if semantic_lines and date_context_lines and len(summary["examples"]["semantic_and_date_hits"]) < 5:
            sample["semantic_lines"] = semantic_lines[:5]
            sample["date_context_lines"] = date_context_lines[:5]
            summary["examples"]["semantic_and_date_hits"].append(sample)
        elif semantic_lines and len(summary["examples"]["semantic_only_hits"]) < 5:
            sample["semantic_lines"] = semantic_lines[:5]
            summary["examples"]["semantic_only_hits"].append(sample)

    summary["render_source_counts"] = dict(summary["render_source_counts"])
    summary["ocr_status_counts"] = dict(summary["ocr_status_counts"])

    if summary["semantic_and_date_context_hit_count"]:
        summary["notes"].append(
            "OCR can recover timing-relevant semantic lines plus date-context lines from at least some scan-style NEPSE notices."
        )
    if summary["semantic_hit_count"] and not summary["semantic_and_date_context_hit_count"]:
        summary["notes"].append(
            "OCR is reading the notices semantically, but date recovery is still too weak for immediate timeline refinement."
        )
    if summary["semantic_and_date_context_hit_count"] < summary["record_count"]:
        summary["notes"].append(
            "OCR feasibility is partial, not universal. A future source upgrade should treat OCR as enrichment, not as a guaranteed parser."
        )
    summary["notes"].append(
        "This is still research-only and does not change any replay rule or event bucket."
    )

    return summary


def _render_markdown(summary):
    lines = [
        "# Event Attachment OCR Feasibility",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- target_year: `{summary['target_year']}`",
        f"- target_run_label: `{summary['target_run_label']}`",
        f"- source_candidate_count: `{summary['source_candidate_count']}`",
        f"- record_count: `{summary['record_count']}`",
        f"- max_per_event_type: `{summary['max_per_event_type']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Counts",
        "",
        f"- event_type_counts: `{summary.get('event_type_counts')}`",
        f"- render_source_counts: `{summary.get('render_source_counts')}`",
        f"- ocr_status_counts: `{summary.get('ocr_status_counts')}`",
        f"- semantic_hit_count: `{summary.get('semantic_hit_count')}`",
        f"- date_context_hit_count: `{summary.get('date_context_hit_count')}`",
        f"- semantic_and_date_context_hit_count: `{summary.get('semantic_and_date_context_hit_count')}`",
        "",
        "## Examples",
        "",
    ])
    for key, values in summary.get("examples", {}).items():
        lines.append(f"### `{key}`")
        lines.append("")
        for value in values:
            lines.append(f"- `{value}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def main():
    summary = build_event_attachment_ocr_feasibility()

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_attachment_ocr_feasibility_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__event_attachment_ocr_feasibility_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_attachment_ocr_feasibility_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__event_attachment_ocr_feasibility_v1.md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)

    print(json.dumps({
        "record_count": summary["record_count"],
        "semantic_hit_count": summary["semantic_hit_count"],
        "date_context_hit_count": summary["date_context_hit_count"],
        "semantic_and_date_context_hit_count": summary["semantic_and_date_context_hit_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
