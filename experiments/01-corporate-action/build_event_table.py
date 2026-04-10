from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

import pandas as pd
from bs4 import BeautifulSoup


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"


def main() -> None:
    args = parse_args()
    raw_symbol_dirs = sorted(path for path in RAW_DIR.iterdir() if path.is_dir())
    if args.symbols:
        wanted = {symbol.strip().upper() for symbol in args.symbols.split(",") if symbol.strip()}
        raw_symbol_dirs = [path for path in raw_symbol_dirs if path.name.upper() in wanted]

    rows: list[dict] = []
    for symbol_dir in raw_symbol_dirs:
        profile = _load_json(symbol_dir / "company_profile.json")
        if not profile:
            continue

        symbol = str(profile.get("symbol", symbol_dir.name)).upper()
        sector = profile.get("sector", "")
        company_name = profile.get("name") or profile.get("company_name")
        base = {
            "symbol": symbol,
            "sector": sector,
            "company_name": company_name,
        }

        for item in _load_json(symbol_dir / "company-dividend.json"):
            bonus_pct = _to_float(item.get("bonus_share"))
            cash_pct = _to_float(item.get("cash_dividend"))
            rows.append(
                {
                    **base,
                    "event_type": _classify_dividend_event(bonus_pct, cash_pct),
                    "source_table": "company-dividend",
                    "event_label": f"{symbol} dividend history row",
                    "raw_title": "",
                    "source_url": profile.get("source_url"),
                    "announcement_date": _clean_date(item.get("announcement_date")),
                    "approval_date": "",
                    "book_close_date": _clean_date(item.get("bookclose_date")),
                    "ex_date": "",
                    "listing_date": _clean_date(item.get("bonus_listing_date")),
                    "distribution_date": _clean_date(item.get("distribution_date")),
                    "meeting_date": "",
                    "right_open_date": "",
                    "right_close_date": "",
                    "right_final_date": "",
                    "fiscal_year": item.get("year", ""),
                    "bonus_share_pct": bonus_pct,
                    "cash_dividend_pct": cash_pct,
                    "total_dividend_pct": _to_float(item.get("total_dividend")),
                    "right_share_ratio": "",
                    "right_share_units": None,
                    "agenda": "",
                    "notes": "",
                }
            )

        for item in _load_json(symbol_dir / "company-rightshare.json"):
            link = item.get("announcement_link", "")
            rows.append(
                {
                    **base,
                    "event_type": "right_share",
                    "source_table": "company-rightshare",
                    "event_label": f"{symbol} right share history row",
                    "raw_title": "",
                    "source_url": link or profile.get("source_url"),
                    "announcement_date": _extract_trailing_date(link),
                    "approval_date": "",
                    "book_close_date": _clean_date(item.get("final_date")),
                    "ex_date": "",
                    "listing_date": _clean_date(item.get("listing_date")),
                    "distribution_date": "",
                    "meeting_date": "",
                    "right_open_date": _clean_date(item.get("opening_date")),
                    "right_close_date": _clean_date(item.get("closing_date")),
                    "right_final_date": _clean_date(item.get("final_date")),
                    "fiscal_year": "",
                    "bonus_share_pct": None,
                    "cash_dividend_pct": None,
                    "total_dividend_pct": None,
                    "right_share_ratio": item.get("ratio_value", ""),
                    "right_share_units": _to_float(item.get("total_units")),
                    "agenda": "",
                    "notes": item.get("issue_manager", ""),
                }
            )

        for item in _load_json(symbol_dir / "company-agm.json"):
            rows.append(
                {
                    **base,
                    "event_type": "agm",
                    "source_table": "company-agm",
                    "event_label": item.get("agm", ""),
                    "raw_title": "",
                    "source_url": profile.get("source_url"),
                    "announcement_date": "",
                    "approval_date": _clean_date(item.get("meeting_date")),
                    "book_close_date": _clean_date(item.get("bookclose_date")),
                    "ex_date": "",
                    "listing_date": "",
                    "distribution_date": "",
                    "meeting_date": _clean_date(item.get("meeting_date")),
                    "right_open_date": "",
                    "right_close_date": "",
                    "right_final_date": "",
                    "fiscal_year": "",
                    "bonus_share_pct": None,
                    "cash_dividend_pct": None,
                    "total_dividend_pct": None,
                    "right_share_ratio": "",
                    "right_share_units": None,
                    "agenda": _strip_html(item.get("agenda", "")),
                    "notes": _strip_html(item.get("venue_time", "")),
                }
            )

        for source_table in ("company-announcements", "company-events"):
            for item in _load_json(symbol_dir / f"{source_table}.json"):
                title_text, href = _extract_anchor(item.get("title", ""))
                event_type = _classify_feed_item(title_text)
                if not event_type:
                    continue
                rows.append(
                    {
                        **base,
                        "event_type": event_type,
                        "source_table": source_table,
                        "event_label": title_text,
                        "raw_title": item.get("title", ""),
                        "source_url": href,
                        "announcement_date": _clean_date(item.get("published_date")),
                        "approval_date": "",
                        "book_close_date": "",
                        "ex_date": "",
                        "listing_date": "",
                        "distribution_date": "",
                        "meeting_date": "",
                        "right_open_date": "",
                        "right_close_date": "",
                        "right_final_date": "",
                        "fiscal_year": "",
                        "bonus_share_pct": None,
                        "cash_dividend_pct": None,
                        "total_dividend_pct": None,
                        "right_share_ratio": "",
                        "right_share_units": None,
                        "agenda": "",
                        "notes": "",
                    }
                )

    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError(f"No event rows were built from {RAW_DIR}")

    frame = frame.drop_duplicates(
        subset=[
            "symbol",
            "event_type",
            "source_table",
            "announcement_date",
            "approval_date",
            "book_close_date",
            "listing_date",
            "event_label",
        ]
    ).sort_values(
        ["symbol", "announcement_date", "approval_date", "book_close_date", "listing_date", "event_type"],
        na_position="last",
    )

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    events_csv = DATA_DIR / "events.csv"
    events_json = DATA_DIR / "events.json"
    frame.to_csv(events_csv, index=False)
    events_json.write_text(frame.to_json(orient="records", indent=2), encoding="utf-8")

    print(f"Wrote {len(frame)} events to {events_csv}")


def _load_json(path: Path) -> list[dict] | dict:
    if not path.exists():
        return []
    return json.loads(path.read_text(encoding="utf-8"))


def _classify_dividend_event(bonus_pct: float | None, cash_pct: float | None) -> str:
    if (bonus_pct or 0) > 0 and (cash_pct or 0) > 0:
        return "bonus_and_cash_dividend"
    if (bonus_pct or 0) > 0:
        return "bonus_share"
    if (cash_pct or 0) > 0:
        return "cash_dividend"
    return "dividend"


def _classify_feed_item(title_text: str) -> str | None:
    text = title_text.lower()
    if "book closure" in text or "book close" in text:
        return "book_closure_notice"
    if "minutes of" in text and ("annual general meeting" in text or "agm" in text):
        return "agm_minutes"
    if "annual general meeting" in text or "agm" in text:
        return "agm_notice"
    if "right" in text and "listing" in text:
        return "right_share_listing_notice"
    if "bonus" in text and "listing" in text:
        return "bonus_listing_notice"
    if "right share" in text or "rights share" in text or ("offer letter" in text and "ratio" in text):
        return "right_share_notice"
    if "cash dividend" in text:
        return "cash_dividend_notice"
    if "bonus share" in text or ("bonus" in text and "dividend" in text):
        return "bonus_share_notice"
    if "dividend" in text:
        return "dividend_notice"
    return None


def _extract_anchor(html_fragment: str) -> tuple[str, str]:
    soup = BeautifulSoup(html_fragment, "html.parser")
    anchor = soup.find("a")
    if not anchor:
        text = soup.get_text(" ", strip=True)
        return text, ""
    return anchor.get_text(" ", strip=True), anchor.get("href", "")


def _extract_trailing_date(value: str) -> str:
    match = re.search(r"(\d{4}-\d{2}-\d{2})/?$", value or "")
    return match.group(1) if match else ""


def _clean_date(value: object) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if not text:
        return ""
    match = re.search(r"(\d{4}-\d{2}-\d{2})", text)
    return match.group(1) if match else ""


def _strip_html(value: str) -> str:
    text = value or ""
    if "<" not in text and ">" not in text:
        return str(text).strip()
    return BeautifulSoup(text, "html.parser").get_text(" ", strip=True)


def _to_float(value: object) -> float | None:
    if value in (None, ""):
        return None
    text = str(value).replace(",", "").strip()
    if not text:
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build a standardized corporate-action event table.")
    parser.add_argument("--symbols", help="Optional comma-separated symbol filter.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
