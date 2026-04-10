"""
Replay-safe backfill helpers for the official NEPSE company-news archive.
"""
import re
from datetime import datetime
from urllib.parse import quote

from data_sources.nepse_scraper_source import NepseScraperTruthSource


FETCH_FILES_BASE = "https://www.nepalstock.com/api/nots/security/fetchFiles?fileLocation="


def _clean_text(value):
    text = re.sub(r"\s+", " ", str(value or "")).strip()
    return re.sub(r"<[^>]+>", " ", text)


def _normalize_key(value):
    return re.sub(r"\s+", " ", re.sub(r"[^a-z0-9]+", " ", str(value or "").lower())).strip()


def _build_file_url(file_path):
    if not file_path:
        return ""
    return FETCH_FILES_BASE + quote(str(file_path), safe="")


def _classify_company_news(headline, body):
    text = f"{headline or ''} {body or ''}".lower()
    if "book close" in text or "book closed" in text or "book closure" in text:
        return "book_closure", "announced", 21, "high"
    if "right share" in text or "right shares" in text:
        return "rights_issue", "announced", 45, "high"
    if "bonus share" in text or "bonus shares" in text or "bonus dividend" in text:
        return "bonus_share", "announced", 45, "medium"
    if "dividend" in text:
        return "dividend_notice", "announced", 21, "medium"
    if "annual general meeting" in text or re.search(r"\bagm\b", text):
        return "agm_notice", "announced", 14, "medium"
    if "listing" in text:
        return "listing_notice", "listed", 21, "medium"
    if "allotment" in text or "preference shares" in text:
        return "capital_allotment", "published", 14, "low"
    return None


def _extract_field(body, field_name):
    match = re.search(rf"{re.escape(field_name)}\s*:\s*([^\n\r]+)", str(body or ""), re.IGNORECASE)
    return _clean_text(match.group(1)) if match else ""


def build_nepse_company_news_backfill(year, symbols):
    symbol_set = {str(symbol).upper() for symbol in symbols}
    source = NepseScraperTruthSource(verify_ssl=False)
    raw_rows = source.client.session.get("/api/nots/news/media/company-news").json()

    filtered_rows = []
    skipped_irrelevant = 0
    seen = set()
    event_type_counts = {}
    symbol_counts = {}

    for row in raw_rows or []:
        published_date = str(row.get("publishedDate") or "")[:10]
        symbol = str(row.get("symbol") or "").upper().strip()
        if not published_date.startswith(str(year)) or symbol not in symbol_set:
            continue

        classification = _classify_company_news(row.get("newsHeadline"), row.get("newsBody"))
        if not classification:
            skipped_irrelevant += 1
            continue

        event_type, event_status, impact_window_days, risk_level = classification
        dedupe_key = (
            symbol,
            published_date,
            event_type,
            _normalize_key(row.get("newsHeadline")),
            _normalize_key(row.get("newsBody"))[:160],
        )
        if dedupe_key in seen:
            continue
        seen.add(dedupe_key)

        record = {
            "record_id": f"{year}__{symbol}__{len(filtered_rows)}",
            "symbol": symbol,
            "security_id": row.get("securityId"),
            "security_name": row.get("securityName") or "",
            "company_name": row.get("companyName") or row.get("securityName") or "",
            "published_date": published_date,
            "event_date": published_date,
            "event_date_basis": "published_date",
            "event_type": event_type,
            "event_status": event_status,
            "impact_window_days": impact_window_days,
            "risk_level": risk_level,
            "headline": _clean_text(row.get("newsHeadline")),
            "body": _clean_text(row.get("newsBody")),
            "file_path": row.get("filePath") or "",
            "source_link": _build_file_url(row.get("filePath")),
            "book_close_date": _extract_field(row.get("newsBody"), "Book Close Date"),
            "agm_date": _extract_field(row.get("newsBody"), "AGM Date"),
            "cash_dividend": _extract_field(row.get("newsBody"), "Cash Dividend"),
            "bonus_shares": _extract_field(row.get("newsBody"), "Bonus Shares"),
            "right_shares": _extract_field(row.get("newsBody"), "Right Shares"),
            "approved_date": str(row.get("approvedDate") or "")[:19],
        }
        filtered_rows.append(record)
        event_type_counts[event_type] = event_type_counts.get(event_type, 0) + 1
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1

    filtered_rows.sort(key=lambda item: (item["event_date"], item["symbol"], item["event_type"]))

    notes = []
    if filtered_rows:
        notes.append("official NEPSE company-news archive provides symbol-tagged historical disclosures")
        notes.append("company-news records use publication date as the replay-safe event_date")
    else:
        notes.append("no relevant company-news records were found for the target year and symbol set")
    if skipped_irrelevant:
        notes.append("irrelevant governance-style notices were skipped unless they matched a tracked corporate-action pattern")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "year": year,
        "symbols": sorted(symbol_set),
        "source_url": "https://www.nepalstock.com/api/nots/news/media/company-news",
        "raw_row_count": len(raw_rows or []),
        "filtered_record_count": len(filtered_rows),
        "skipped_irrelevant_count": skipped_irrelevant,
        "event_type_counts": event_type_counts,
        "symbol_event_counts": symbol_counts,
        "notes": notes,
        "records": filtered_rows,
    }
