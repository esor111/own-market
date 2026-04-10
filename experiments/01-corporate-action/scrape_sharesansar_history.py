from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import requests
from bs4 import BeautifulSoup


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"

DEFAULT_SYMBOLS = [
    "NABIL",
    "NBL",
    "EBL",
    "HBL",
    "KBL",
    "SANIMA",
    "PRVU",
    "NIMB",
    "SMHL",
    "HIDCL",
    "NGPL",
    "API",
    "AKPL",
    "UPPER",
]

COMPANY_ENDPOINTS = [
    "company-dividend",
    "company-rightshare",
    "company-agm",
    "company-announcements",
    "company-events",
]


def main() -> None:
    args = parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    symbols = parse_symbol_list(args.symbols) or DEFAULT_SYMBOLS
    manifest: list[dict] = []

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    for index, symbol in enumerate(symbols, start=1):
        print(f"[{index}/{len(symbols)}] scraping {symbol}")
        symbol_dir = RAW_DIR / symbol
        symbol_dir.mkdir(parents=True, exist_ok=True)

        page = session.get(f"https://www.sharesansar.com/company/{symbol}", timeout=45)
        page.raise_for_status()
        html = page.text
        (symbol_dir / "company_page.html").write_text(html, encoding="utf-8")

        company_id = _extract_hidden_value(html, "companyid")
        token = _extract_csrf_token(html)
        if not company_id or not token:
            raise RuntimeError(f"Missing company metadata for {symbol}")

        profile = _parse_company_profile(html)
        profile["symbol"] = symbol
        profile["company_id"] = company_id
        profile["source_url"] = f"https://www.sharesansar.com/company/{symbol}"
        (symbol_dir / "company_profile.json").write_text(
            json.dumps(profile, indent=2),
            encoding="utf-8",
        )

        headers = {
            "User-Agent": "Mozilla/5.0",
            "X-CSRF-Token": token,
            "X-Requested-With": "XMLHttpRequest",
            "Referer": f"https://www.sharesansar.com/company/{symbol}",
        }

        endpoint_counts: dict[str, int] = {}
        for endpoint in COMPANY_ENDPOINTS:
            records = fetch_all_datatable_rows(
                session=session,
                endpoint=endpoint,
                company_id=company_id,
                headers=headers,
                page_size=args.page_size,
            )
            endpoint_counts[endpoint] = len(records)
            (symbol_dir / f"{endpoint}.json").write_text(
                json.dumps(records, indent=2),
                encoding="utf-8",
            )

        manifest.append(
            {
                "symbol": symbol,
                "company_id": company_id,
                "sector": profile.get("sector"),
                "company_name": profile.get("name"),
                "source_url": profile.get("source_url"),
                "endpoint_counts": endpoint_counts,
            }
        )

        if args.sleep_seconds:
            time.sleep(args.sleep_seconds)

    (DATA_DIR / "scrape_manifest.json").write_text(
        json.dumps(manifest, indent=2),
        encoding="utf-8",
    )

    print(f"Saved raw ShareSansar history for {len(symbols)} symbols to {RAW_DIR}")


def fetch_all_datatable_rows(
    session: requests.Session,
    endpoint: str,
    company_id: str,
    headers: dict[str, str],
    page_size: int = 200,
) -> list[dict]:
    page_size = min(page_size, 50)
    start = 0
    all_rows: list[dict] = []
    total = None

    while total is None or start < total:
        payload = {
            "company": company_id,
            "draw": 1,
            "start": start,
            "length": page_size,
        }
        response = session.post(
            f"https://www.sharesansar.com/{endpoint}",
            data=payload,
            headers=headers,
            timeout=45,
        )
        response.raise_for_status()
        data = response.json()
        rows = data.get("data", [])
        total = int(data.get("recordsTotal", 0))
        all_rows.extend(rows)
        start += page_size
        if not rows:
            break

    return all_rows


def _parse_company_profile(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    info_table = soup.select_one("#myTableCInfo")
    profile: dict[str, str] = {}

    if info_table:
        for row in info_table.select("tr"):
            cells = row.find_all("td")
            if len(cells) != 2:
                continue
            key = _normalize_key(cells[0].get_text(" ", strip=True))
            profile[key] = cells[1].get_text(" ", strip=True)

    for hidden_key in ("companyid", "symbol", "sector"):
        value = _extract_hidden_value(html, hidden_key)
        if value:
            profile[hidden_key] = value

    return profile


def _extract_hidden_value(html: str, field_id: str) -> str | None:
    match = re.search(
        rf'<(?:div|span)\s+id="{re.escape(field_id)}"[^>]*>(.*?)</(?:div|span)>',
        html,
        flags=re.IGNORECASE | re.DOTALL,
    )
    if not match:
        return None
    return BeautifulSoup(match.group(1), "html.parser").get_text(" ", strip=True)


def _extract_csrf_token(html: str) -> str | None:
    match = re.search(r'<meta name="_token" content="([^"]+)"', html)
    return match.group(1) if match else None


def _normalize_key(value: str) -> str:
    return (
        value.strip()
        .lower()
        .replace("/", " ")
        .replace(".", "")
        .replace("-", " ")
        .replace("  ", " ")
        .replace(" ", "_")
    )


def parse_symbol_list(value: str | None) -> list[str]:
    if not value:
        return []
    return [item.strip().upper() for item in value.split(",") if item.strip()]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Scrape ShareSansar company corporate-action feeds.")
    parser.add_argument("--symbols", help="Comma-separated symbol list. Default is the 14 seed symbols.")
    parser.add_argument("--page-size", type=int, default=50, help="Datatable page size for ShareSansar feeds. Keep this at 50 or lower; larger values return empty payloads.")
    parser.add_argument("--sleep-seconds", type=float, default=0.0, help="Optional pause between symbols.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
