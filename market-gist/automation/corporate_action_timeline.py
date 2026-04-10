"""
Replay-safe corporate action timeline helpers.
"""
import os
import re
from datetime import datetime

from config import load_json_file
from data_sources.nepse_scraper_source import NepseScraperTruthSource
from corporate_action_pdf_extractors import extract_rights_summary_pdf_rows


STOPWORDS = {
    "limited",
    "ltd",
    "bank",
    "bikas",
    "development",
    "company",
    "hydropower",
    "power",
    "finance",
    "fund",
    "nepal",
    "public",
    "shares",
    "share",
    "issue",
    "approved",
    "fiscal",
    "year",
    "as",
    "on",
    "right",
    "prospectus",
    "offer",
    "ordinary",
}


def _clean_text(value):
    return re.sub(r"\s+", " ", str(value or "")).strip()


def _normalize_tokens(value):
    cleaned = re.sub(r"[^a-z0-9]+", " ", _clean_text(value).lower())
    return [
        token
        for token in cleaned.split()
        if len(token) >= 3 and token not in STOPWORDS
    ]


def _classify_source_row(source_table, title):
    lowered = _clean_text(title).lower()
    if source_table == "right_share_approved_rows":
        return "rights_issue", "approved", 45, "high"
    if source_table == "right_share_pipeline_rows":
        return "rights_issue", "pipeline", 45, "high"
    if "book closure" in lowered:
        return "book_closure", "announced", 21, "high"
    if "bonus" in lowered and "listing" in lowered:
        return "bonus_share_listing", "listed", 21, "medium"
    if "bonus" in lowered:
        return "bonus_share", "announced", 45, "medium"
    if "debenture" in lowered:
        return "debenture_offer", "announced", 60, "medium"
    if "right" in lowered:
        return "rights_issue", "announced", 45, "high"
    if "listing" in lowered:
        return "listing_notice", "listed", 21, "medium"
    if source_table == "prospectus_rows":
        return "prospectus_offer", "published", 60, "medium"
    return "corporate_notice", "published", 30, "medium"


def _load_symbol_references(symbols):
    source = NepseScraperTruthSource(verify_ssl=False)
    requested_symbols = {str(symbol).upper() for symbol in symbols}
    references = {}
    try:
        listings = source.client.call_endpoint("security_api") or []
    except Exception:
        listings = []

    for listing in listings:
        symbol = str(listing.get("symbol") or "").upper().strip()
        if not symbol:
            continue
        security_name = listing.get("securityName") or listing.get("companyName") or symbol
        company_name = listing.get("companyName") or security_name
        references[symbol] = {
            "symbol": symbol,
            "security_name": security_name,
            "company_name": company_name,
            "sector_name": listing.get("sectorName") or "",
            "requested_symbol": symbol in requested_symbols,
            "tokens": sorted(set(
                _normalize_tokens(symbol)
                + _normalize_tokens(security_name)
                + _normalize_tokens(company_name)
            )),
        }

    for symbol in requested_symbols:
        references.setdefault(symbol, {
            "symbol": symbol,
            "security_name": symbol,
            "company_name": symbol,
            "sector_name": "",
            "requested_symbol": True,
            "tokens": _normalize_tokens(symbol),
        })
    return references


def _match_symbol(title, symbol_references):
    text = _clean_text(title)
    title_tokens = _normalize_tokens(text)
    upper_words = set(re.findall(r"[A-Z]{2,}", text.upper()))
    candidates = []

    for symbol, reference in symbol_references.items():
        symbol_match = symbol in upper_words or f"({symbol})" in text.upper()
        overlap = [token for token in reference["tokens"] if token in title_tokens]
        if not symbol_match and len(overlap) < 2:
            continue
        candidates.append({
            "symbol": symbol,
            "company_name": reference["company_name"],
            "matched_tokens": overlap,
            "match_score": (10 if symbol_match else 0) + len(overlap),
            "symbol_match": symbol_match,
        })

    if not candidates:
        return {}

    candidates.sort(key=lambda item: (-item["match_score"], -len(item["matched_tokens"]), item["symbol"]))
    best = candidates[0]
    return {
        "symbol": best["symbol"],
        "company_name": best["company_name"],
        "matched_tokens": best["matched_tokens"],
        "match_score": best["match_score"],
        "symbol_match": best["symbol_match"],
        "requested_symbol": bool(symbol_references.get(best["symbol"], {}).get("requested_symbol")),
    }


def _build_record(
    year,
    source_table,
    record_index,
    title,
    event_date,
    source_link,
    match,
    event_type,
    event_status,
    impact_window_days,
    risk_level,
    source_type="official_table_index",
    extra_fields=None,
):
    return {
        "record_id": f"{year}__{source_table}__{record_index}",
        "year": year,
        "source_table": source_table,
        "source_type": source_type,
        "source_link": source_link or "",
        "title": _clean_text(title),
        "event_date": _clean_text(event_date)[:10],
        "event_type": event_type,
        "event_status": event_status,
        "impact_window_days": impact_window_days,
        "risk_level": risk_level,
        "symbol": match.get("symbol"),
        "company_name": match.get("company_name"),
        "match_score": match.get("match_score", 0),
        "matched_tokens": match.get("matched_tokens") or [],
        "symbol_match": bool(match.get("symbol_match")),
        "requested_symbol": bool(match.get("requested_symbol")),
        "timeline_quality": "matched_symbol" if match else "unmatched_symbol",
        "captured_at": datetime.now().isoformat(),
        **(extra_fields or {}),
    }


def _load_company_news_ocr_hints(year, run_label_token=None):
    clean_label = str(run_label_token or "").strip()
    if not clean_label:
        return {}

    enrichment_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "validation",
        "learning_reviews",
        f"latest__{year}__{clean_label}__event_attachment_ocr_enrichment_v1.json",
    )
    normalization_path = os.path.join(
        os.path.dirname(__file__),
        "..",
        "data",
        "validation",
        "learning_reviews",
        f"latest__{year}__{clean_label}__event_bs_date_normalization_study_v1.json",
    )
    enrichment_payload = load_json_file(os.path.abspath(enrichment_path), {})
    normalization_payload = load_json_file(os.path.abspath(normalization_path), {})

    enrichment_lookup = {}
    for row in enrichment_payload.get("records") or []:
        key = (
            str(row.get("symbol") or "").upper(),
            _clean_text(row.get("headline")),
            _clean_text(row.get("published_date"))[:10],
        )
        enrichment_lookup[key] = {
            "ocr_status": row.get("ocr_status"),
            "ocr_timing_evidence_flag": bool(row.get("ocr_timing_evidence_flag")),
            "ocr_render_source": row.get("ocr_render_source"),
            "ocr_semantic_lines": row.get("ocr_semantic_lines") or [],
            "ocr_date_context_lines": row.get("ocr_date_context_lines") or [],
            "ocr_date_context_lines_normalized": row.get("ocr_date_context_lines_normalized") or [],
            "ocr_date_context_hit_count": int(row.get("ocr_date_context_hit_count") or 0),
            "ocr_semantic_hit_count": int(row.get("ocr_semantic_hit_count") or 0),
        }

    normalization_lookup = {}
    for row in normalization_payload.get("records") or []:
        key = (
            str(row.get("symbol") or "").upper(),
            _clean_text(row.get("headline")),
        )
        converted = []
        for item in row.get("parsed_candidates") or []:
            if item.get("conversion_status") != "ok":
                continue
            converted.append({
                "raw_match": item.get("raw_match"),
                "parse_type": item.get("parse_type"),
                "bs_iso": item.get("bs_iso"),
                "ad_iso": item.get("ad_iso"),
                "source_line": item.get("source_line"),
            })
        normalization_lookup[key] = converted

    return {
        "enrichment_lookup": enrichment_lookup,
        "normalization_lookup": normalization_lookup,
    }


def build_corporate_action_timeline(year, symbols, official_backfill_path, run_label_token=None):
    payload = load_json_file(official_backfill_path, {})
    event_tables = (payload.get("event_tables") or {})
    symbol_references = _load_symbol_references(symbols)
    requested_symbols = {str(symbol).upper() for symbol in symbols}
    company_news_paths = [
        os.path.join(
            os.path.dirname(official_backfill_path),
            f"latest__{year}__{run_label_token}__nepse_company_news_backfill_v1.json",
        ),
    ]
    if run_label_token != "replay_basket_v1":
        company_news_paths.append(
            os.path.join(
                os.path.dirname(official_backfill_path),
                f"latest__{year}__replay_basket_v1__nepse_company_news_backfill_v1.json",
            )
        )
    company_news_payload = {}
    for candidate_path in company_news_paths:
        candidate_payload = load_json_file(candidate_path, {})
        if candidate_payload:
            company_news_payload = candidate_payload
            break

    records = []
    unmatched_records = []
    source_counts = {}
    enrichment_counts = {
        "pdf_rows_extracted": 0,
        "pdf_rows_matched": 0,
        "pdf_rows_requested_symbol_matched": 0,
    }
    notes = []

    for source_table in ("right_share_approved_rows", "right_share_pipeline_rows", "prospectus_rows"):
        rows = event_tables.get(source_table) or []
        source_counts[source_table] = len(rows)
        for index, row in enumerate(rows):
            title = _clean_text(row.get("title"))
            event_date = _clean_text(row.get("event_date"))[:10]
            if not title or not event_date.startswith(str(year)):
                continue

            event_type, event_status, impact_window_days, risk_level = _classify_source_row(source_table, title)
            source_link = row.get("english_url") or row.get("nepali_url") or ""

            pdf_rows = []
            if source_table in {"right_share_approved_rows", "right_share_pipeline_rows"} and source_link.lower().endswith(".pdf"):
                pdf_payload = extract_rights_summary_pdf_rows(source_link, publication_date=event_date)
                notes.extend(note for note in (pdf_payload.get("notes") or []) if note not in notes)
                pdf_rows = pdf_payload.get("rows") or []
                enrichment_counts["pdf_rows_extracted"] += len(pdf_rows)

            if pdf_rows:
                notes.append("company-level right-share rows were extracted from official summary PDFs")
                notes.append("summary-PDF rows currently use the official publication date as the replay-safe event_date")
                for pdf_index, pdf_row in enumerate(pdf_rows):
                    granular_title = f"{pdf_row.get('company_name')} {event_status.replace('_', ' ')}"
                    match = _match_symbol(pdf_row.get("company_name"), symbol_references)
                    record = _build_record(
                        year=year,
                        source_table=source_table,
                        record_index=f"{index}__pdf__{pdf_index}",
                        title=granular_title,
                        event_date=pdf_row.get("publication_date") or event_date,
                        source_link=source_link,
                        match=match,
                        event_type=event_type,
                        event_status=event_status,
                        impact_window_days=impact_window_days,
                        risk_level=risk_level,
                        source_type="official_pdf_summary",
                        extra_fields={
                            "publication_date": pdf_row.get("publication_date") or event_date,
                            "approval_date_bs": pdf_row.get("approval_date_bs"),
                            "sector": pdf_row.get("sector"),
                            "ratio": pdf_row.get("ratio"),
                            "issue_share_count": pdf_row.get("issue_share_count"),
                            "issue_amount": pdf_row.get("issue_amount"),
                            "issue_manager": pdf_row.get("issue_manager"),
                            "event_date_basis": "publication_date",
                            "source_summary_title": title,
                        },
                    )
                    if match:
                        enrichment_counts["pdf_rows_matched"] += 1
                        if match.get("requested_symbol"):
                            enrichment_counts["pdf_rows_requested_symbol_matched"] += 1
                        records.append(record)
                    else:
                        unmatched_records.append(record)
                continue

            match = _match_symbol(title, symbol_references)
            record = _build_record(
                year=year,
                source_table=source_table,
                record_index=index,
                title=title,
                event_date=event_date,
                source_link=source_link,
                match=match,
                event_type=event_type,
                event_status=event_status,
                impact_window_days=impact_window_days,
                risk_level=risk_level,
            )
            if match:
                records.append(record)
            else:
                unmatched_records.append(record)

    company_news_records = company_news_payload.get("records") or []
    source_counts["nepse_company_news_rows"] = len(company_news_records)
    if company_news_records:
        notes.append("symbol-tagged NEPSE company-news archive rows were included in the replay-safe timeline")
    ocr_hint_payload = _load_company_news_ocr_hints(year, run_label_token=run_label_token)
    ocr_enrichment_lookup = ocr_hint_payload.get("enrichment_lookup") or {}
    ocr_normalization_lookup = ocr_hint_payload.get("normalization_lookup") or {}
    if ocr_enrichment_lookup:
        notes.append("OCR-derived timing evidence was attached to company-news rows when a matching enrichment artifact was available")
    for index, row in enumerate(company_news_records):
        symbol = str(row.get("symbol") or "").upper()
        match = symbol_references.get(symbol) or {}
        ocr_key = (
            symbol,
            _clean_text(row.get("headline")),
            _clean_text(row.get("published_date"))[:10],
        )
        normalization_key = (
            symbol,
            _clean_text(row.get("headline")),
        )
        ocr_enrichment = ocr_enrichment_lookup.get(ocr_key) or {}
        ocr_date_hints = ocr_normalization_lookup.get(normalization_key) or []
        record = _build_record(
            year=year,
            source_table="nepse_company_news_rows",
            record_index=index,
            title=row.get("headline") or row.get("event_type") or "",
            event_date=row.get("event_date") or "",
            source_link=row.get("source_link") or "",
            match={
                "symbol": symbol,
                "company_name": row.get("company_name") or match.get("company_name") or symbol,
                "match_score": 100,
                "matched_tokens": [symbol],
                "symbol_match": True,
                "requested_symbol": symbol in requested_symbols,
            },
            event_type=row.get("event_type") or "corporate_notice",
            event_status=row.get("event_status") or "published",
            impact_window_days=int(row.get("impact_window_days") or 14),
            risk_level=row.get("risk_level") or "medium",
            source_type="official_nepse_company_news_archive",
            extra_fields={
                "publication_date": row.get("published_date"),
                "headline": row.get("headline"),
                "body": row.get("body"),
                "book_close_date": row.get("book_close_date"),
                "agm_date": row.get("agm_date"),
                "cash_dividend": row.get("cash_dividend"),
                "bonus_shares": row.get("bonus_shares"),
                "right_shares": row.get("right_shares"),
                "file_path": row.get("file_path"),
                "event_date_basis": row.get("event_date_basis") or "published_date",
                "ocr_status": ocr_enrichment.get("ocr_status"),
                "ocr_timing_evidence_flag": bool(ocr_enrichment.get("ocr_timing_evidence_flag")),
                "ocr_render_source": ocr_enrichment.get("ocr_render_source"),
                "ocr_semantic_lines": ocr_enrichment.get("ocr_semantic_lines") or [],
                "ocr_date_context_lines_normalized": ocr_enrichment.get("ocr_date_context_lines_normalized") or [],
                "ocr_date_hint_candidates": ocr_date_hints,
            },
        )
        records.append(record)

    records.sort(key=lambda item: (item["event_date"], item["symbol"] or "", item["event_type"]))
    unmatched_records.sort(key=lambda item: (item["event_date"], item["event_type"], item["title"]))

    symbol_counts = {}
    requested_symbol_counts = {}
    for record in records:
        symbol = record["symbol"]
        symbol_counts[symbol] = symbol_counts.get(symbol, 0) + 1
        if symbol in requested_symbols:
            requested_symbol_counts[symbol] = requested_symbol_counts.get(symbol, 0) + 1

    if not records:
        notes.append("no symbol-level corporate action matches were found from the current official table-index sources")
    if unmatched_records:
        notes.append("some official event rows could not be mapped to symbols from their index-page titles alone")
    if sum(source_counts.values()) == 0:
        notes.append("official event tables were empty for the target year")
    if not requested_symbol_counts:
        notes.append("the current requested replay symbol set still has no matched corporate-action rows")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "year": year,
        "source_backfill_path": os.path.abspath(official_backfill_path),
        "symbols": [str(symbol).upper() for symbol in symbols],
        "match_universe_symbol_count": len(symbol_references),
        "source_counts": source_counts,
        "enrichment_counts": enrichment_counts,
        "matched_record_count": len(records),
        "unmatched_record_count": len(unmatched_records),
        "symbol_event_counts": symbol_counts,
        "requested_symbol_match_count": sum(requested_symbol_counts.values()),
        "requested_symbol_event_counts": requested_symbol_counts,
        "notes": notes,
        "records": records,
        "unmatched_records": unmatched_records,
    }
