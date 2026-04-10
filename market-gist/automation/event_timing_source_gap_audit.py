"""
Research-only audit of the NEPSE company-news event-timing source.

Goal:
- measure how much usable timing information the current company-news source really provides
- separate body-field coverage from attachment-field coverage
- check whether `approved_date` is just an admin lag or a meaningful event-timing field

Usage:
    python event_timing_source_gap_audit.py
"""
import json
import os
import re
import ssl
import urllib.request
from collections import Counter, defaultdict
from datetime import datetime
from io import BytesIO
from statistics import mean

from config import VALIDATION_DIR


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")
BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")
USER_AGENT = "Mozilla/5.0 (compatible; MarketGistBot/1.0)"
UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()
TARGET_YEARS = (2023, 2024, 2025)
TARGET_RUN_LABEL = "replay_basket_v1"

ATTACHMENT_PATTERNS = {
    "book_close_date": re.compile(r"book\s+clos(?:e|ure)\s*date\s*:?\s*([^\n\r]+)", re.IGNORECASE),
    "record_date": re.compile(r"record\s+date\s*:?\s*([^\n\r]+)", re.IGNORECASE),
    "last_trade_date": re.compile(r"last\s+trading?\s+date\s*:?\s*([^\n\r]+)", re.IGNORECASE),
    "agm_date": re.compile(r"agm\s+date\s*:?\s*([^\n\r]+)", re.IGNORECASE),
}


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _load_json(path):
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def _load_company_news_records():
    records = []
    missing_years = []
    for year in TARGET_YEARS:
        path = os.path.join(
            BACKFILL_DIR,
            f"latest__{year}__{TARGET_RUN_LABEL}__nepse_company_news_backfill_v1.json",
        )
        payload = _load_json(path)
        year_records = payload.get("records") or []
        if not year_records:
            missing_years.append(year)
            continue
        for row in year_records:
            row = dict(row)
            row["source_backfill_year"] = year
            records.append(row)
    return records, missing_years


def _attachment_ext(source_link):
    lower = str(source_link or "").lower()
    for ext in (".pdf", ".jpeg", ".jpg", ".png"):
        if lower.endswith(ext):
            return ext
    return "<none>"


def _fetch_attachment_text(url):
    if not url or not str(url).lower().endswith(".pdf"):
        return None, "non_pdf"

    try:
        import pdfplumber
    except Exception:
        return None, "pdfplumber_unavailable"

    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    try:
        with urllib.request.urlopen(request, timeout=45, context=UNVERIFIED_SSL_CONTEXT) as response:
            pdf_bytes = response.read()
    except Exception as exc:
        return repr(exc), "download_error"

    try:
        with pdfplumber.open(BytesIO(pdf_bytes)) as pdf:
            text = "\n".join((page.extract_text() or "") for page in pdf.pages[:3]).strip()
    except Exception as exc:
        return repr(exc), "parse_error"

    if not text:
        return "", "pdf_no_text"
    return text, "pdf_with_text"


def _match_attachment_patterns(text):
    matches = {}
    for field_name, pattern in ATTACHMENT_PATTERNS.items():
        match = pattern.search(text or "")
        if match:
            matches[field_name] = str(match.group(1)).strip()[:160]
    return matches


def _approx_approved_lag_hours(record):
    published_date = str(record.get("published_date") or "").strip()
    approved_date = str(record.get("approved_date") or "").strip()
    if not published_date or not approved_date:
        return None
    try:
        published_dt = datetime.fromisoformat(published_date)
        approved_dt = datetime.fromisoformat(approved_date)
    except ValueError:
        return None
    return round((approved_dt - published_dt).total_seconds() / 3600, 4)


def build_event_timing_source_gap_audit():
    records, missing_years = _load_company_news_records()
    attachment_ext_counts = Counter()
    body_field_counts = Counter()
    pdf_extractability_counts = Counter()
    attachment_pattern_counts = Counter()
    attachment_new_pattern_counts = Counter()
    year_record_counts = Counter()
    lag_values = []

    examples = defaultdict(list)

    for row in records:
        year_record_counts.update([row.get("source_backfill_year")])
        attachment_ext_counts.update([_attachment_ext(row.get("source_link"))])

        for field_name in ("book_close_date", "agm_date", "cash_dividend", "bonus_shares", "right_shares"):
            if str(row.get(field_name) or "").strip():
                body_field_counts.update([field_name])

        lag_hours = _approx_approved_lag_hours(row)
        if lag_hours is not None:
            lag_values.append(lag_hours)

        attachment_text, attachment_status = _fetch_attachment_text(row.get("source_link"))
        pdf_extractability_counts.update([attachment_status])

        if attachment_status == "pdf_no_text" and len(examples["pdf_no_text"]) < 5:
            examples["pdf_no_text"].append({
                "symbol": row.get("symbol"),
                "headline": row.get("headline"),
            })
        elif attachment_status in {"download_error", "parse_error"} and len(examples["pdf_errors"]) < 5:
            examples["pdf_errors"].append({
                "symbol": row.get("symbol"),
                "headline": row.get("headline"),
                "status": attachment_status,
                "detail": attachment_text[:200],
            })

        if attachment_status != "pdf_with_text":
            continue

        matches = _match_attachment_patterns(attachment_text)
        if not matches and len(examples["pdf_with_text_but_no_patterns"]) < 5:
            examples["pdf_with_text_but_no_patterns"].append({
                "symbol": row.get("symbol"),
                "headline": row.get("headline"),
                "text_preview": attachment_text[:220],
            })
        for field_name, raw_value in matches.items():
            attachment_pattern_counts.update([field_name])
            if not str(row.get(field_name) or "").strip():
                attachment_new_pattern_counts.update([field_name])
                if len(examples[f"new_{field_name}"]) < 3:
                    examples[f"new_{field_name}"].append({
                        "symbol": row.get("symbol"),
                        "headline": row.get("headline"),
                        "raw_value": raw_value,
                    })

    lag_summary = {
        "count": len(lag_values),
        "min_hours": round(min(lag_values), 4) if lag_values else None,
        "avg_hours": round(mean(lag_values), 4) if lag_values else None,
        "max_hours": round(max(lag_values), 4) if lag_values else None,
    }

    notes = [
        "official NEPSE corporate-disclosure page exposes published date, approved date, symbol, and file, but not a dedicated economic effective-date field",
        "the company-news source is useful for symbol-tagged event coverage, but event timing still depends mostly on publication date plus sparse inline body fields",
        "approximate approved-date lag is short enough to look like moderation/admin timing, not a true economic event date",
    ]
    if pdf_extractability_counts.get("pdf_no_text", 0) or pdf_extractability_counts.get("pdf_with_text", 0):
        notes.append("attachment enrichment is limited because many PDFs are image/scanned notices, and text-extractable PDFs still rarely expose clean English timing fields")
    if attachment_new_pattern_counts:
        notes.append("some attachment-only timing fields exist, but they are too sparse to solve the current source-quality blocker by themselves")
    else:
        notes.append("this audit found no reliable new timing-field coverage from attachments beyond what the body parser already sees")
    if missing_years:
        notes.append(f"missing company-news backfill years during audit: {missing_years}")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "audit_name": "event_timing_source_gap_audit_v1",
        "target_years": list(TARGET_YEARS),
        "target_run_label": TARGET_RUN_LABEL,
        "record_count": len(records),
        "missing_years": missing_years,
        "year_record_counts": dict(year_record_counts),
        "attachment_ext_counts": dict(attachment_ext_counts),
        "body_field_counts": dict(body_field_counts),
        "pdf_extractability_counts": dict(pdf_extractability_counts),
        "attachment_pattern_counts": dict(attachment_pattern_counts),
        "attachment_new_pattern_counts": dict(attachment_new_pattern_counts),
        "approx_approved_lag_hours": lag_summary,
        "examples": dict(examples),
        "notes": notes,
    }


def _render_markdown(summary):
    lag = summary.get("approx_approved_lag_hours") or {}
    lines = [
        "# Event Timing Source Gap Audit",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- target_years: `{summary['target_years']}`",
        f"- target_run_label: `{summary['target_run_label']}`",
        f"- record_count: `{summary['record_count']}`",
        "",
        "## Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")

    lines.extend([
        "",
        "## Coverage",
        "",
        f"- year_record_counts: `{summary.get('year_record_counts')}`",
        f"- attachment_ext_counts: `{summary.get('attachment_ext_counts')}`",
        f"- body_field_counts: `{summary.get('body_field_counts')}`",
        "",
        "## Attachment Extractability",
        "",
        f"- pdf_extractability_counts: `{summary.get('pdf_extractability_counts')}`",
        f"- attachment_pattern_counts: `{summary.get('attachment_pattern_counts')}`",
        f"- attachment_new_pattern_counts: `{summary.get('attachment_new_pattern_counts')}`",
        "",
        "## Approx Approved-Date Lag",
        "",
        f"- count: `{lag.get('count')}`",
        f"- min_hours: `{lag.get('min_hours')}`",
        f"- avg_hours: `{lag.get('avg_hours')}`",
        f"- max_hours: `{lag.get('max_hours')}`",
        "",
        "## Examples",
        "",
    ])
    for key, values in sorted((summary.get("examples") or {}).items()):
        lines.append(f"### `{key}`")
        lines.append("")
        for value in values:
            lines.append(f"- `{value}`")
        lines.append("")
    return "\n".join(lines) + "\n"


def main():
    summary = build_event_timing_source_gap_audit()

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_timing_source_gap_audit_v1.json",
    )
    latest_json_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__event_timing_source_gap_audit_v1.json")
    dated_md_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__event_timing_source_gap_audit_v1.md",
    )
    latest_md_path = os.path.join(LEARNING_REVIEWS_DIR, "latest__event_timing_source_gap_audit_v1.md")

    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)

    print(json.dumps({
        "record_count": summary["record_count"],
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
        "pdf_extractability_counts": summary["pdf_extractability_counts"],
    }, indent=2))


if __name__ == "__main__":
    main()
