from __future__ import annotations

import argparse
import json
import re
import time
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
RAW_DIR = DATA_DIR / "raw"


def main() -> None:
    args = parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    company_list_html = session.get("https://www.sharesansar.com/company-list", timeout=45).text
    (RAW_DIR / "company_list.html").write_text(company_list_html, encoding="utf-8")

    companies = _extract_company_list(company_list_html)
    candidates = [item for item in companies if _is_hydropower_name(item.get("companyname", ""))]
    if args.limit:
        candidates = candidates[: args.limit]

    rows: list[dict] = []
    for index, item in enumerate(candidates, start=1):
        symbol = str(item.get("symbol", "")).upper().strip()
        if not symbol:
            continue

        print(f"[{index}/{len(candidates)}] hydropower candidate {symbol}")
        page = session.get(f"https://www.sharesansar.com/company/{symbol}", timeout=45)
        if page.status_code != 200:
            continue
        html = page.text
        company_dir = RAW_DIR / symbol
        company_dir.mkdir(parents=True, exist_ok=True)
        (company_dir / "company_page.html").write_text(html, encoding="utf-8")

        company_id = _extract_hidden_value(html, "companyid")
        sector = _extract_hidden_value(html, "sector")
        if str(sector).strip().lower() != "hydropower":
            continue

        token = _extract_csrf_token(html)
        if not company_id or not token:
            continue

        profile = _parse_company_profile(html)
        first_trade_date, latest_trade_date, record_count = fetch_price_history_range(
            session=session,
            symbol=symbol,
            company_id=company_id,
            token=token,
        )

        row = {
            "symbol": symbol,
            "company_id": company_id,
            "company_name": profile.get("name") or item.get("companyname"),
            "sector": sector,
            "first_trade_date_proxy": first_trade_date,
            "latest_trade_date": latest_trade_date,
            "price_history_records": record_count,
            "listed_shares": profile.get("listed_shares"),
            "total_paid_up_value": profile.get("total_paid_up_value"),
            "source_url": f"https://www.sharesansar.com/company/{symbol}",
            "data_quality_note": "first_trade_date_proxy_from_sharesansar_price_history",
        }
        rows.append(row)

        (company_dir / "company_profile.json").write_text(json.dumps(profile, indent=2), encoding="utf-8")
        (company_dir / "price_history_range.json").write_text(json.dumps(row, indent=2), encoding="utf-8")

        if args.sleep_seconds:
            time.sleep(args.sleep_seconds)

    if rows:
        frame = pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)
    else:
        frame = pd.DataFrame(
            columns=[
                "symbol",
                "company_id",
                "company_name",
                "sector",
                "first_trade_date_proxy",
                "latest_trade_date",
                "price_history_records",
                "listed_shares",
                "total_paid_up_value",
                "source_url",
                "data_quality_note",
            ]
        )
    csv_path = DATA_DIR / "listing_dates.csv"
    json_path = DATA_DIR / "listing_dates.json"
    frame.to_csv(csv_path, index=False)
    json_path.write_text(frame.to_json(orient="records", indent=2), encoding="utf-8")

    print(f"Wrote {len(frame)} hydropower listing proxies to {csv_path}")


def fetch_price_history_range(
    session: requests.Session,
    symbol: str,
    company_id: str,
    token: str,
) -> tuple[str, str, int]:
    headers = {
        "User-Agent": "Mozilla/5.0",
        "X-CSRF-Token": token,
        "X-Requested-With": "XMLHttpRequest",
        "Referer": f"https://www.sharesansar.com/company/{symbol}",
    }

    first_page = session.post(
        "https://www.sharesansar.com/company-price-history",
        data={"company": company_id, "draw": 1, "start": 0, "length": 1},
        headers=headers,
        timeout=45,
    ).json()
    total = int(first_page.get("recordsTotal", 0))
    first_page_rows = first_page.get("data", [])
    latest_trade_date = first_page_rows[0].get("published_date", "") if first_page_rows else ""
    if total <= 0 or not first_page_rows:
        return "", latest_trade_date, 0

    last_page = session.post(
        "https://www.sharesansar.com/company-price-history",
        data={"company": company_id, "draw": 1, "start": max(total - 1, 0), "length": 1},
        headers=headers,
        timeout=45,
    ).json()
    last_page_rows = last_page.get("data", [])
    first_trade_date = last_page_rows[0].get("published_date", "") if last_page_rows else ""
    return first_trade_date, latest_trade_date, total


def _extract_company_list(html: str) -> list[dict]:
    match = re.search(r'(\[\{"id":.*?\}\])', html, flags=re.DOTALL)
    if not match:
        raise RuntimeError("Could not find company list JSON on ShareSansar company-list page")
    return json.loads(match.group(1))


def _is_hydropower_name(company_name: str) -> bool:
    text = company_name.lower()
    keywords = ["hydro", "hydropower", "hydroelectric", "jalbidhyut", "jalvidhyut", "jalbidhut"]
    return any(keyword in text for keyword in keywords)


def _parse_company_profile(html: str) -> dict:
    soup = BeautifulSoup(html, "html.parser")
    info_table = soup.select_one("#myTableCInfo")
    profile: dict[str, str] = {}
    if info_table:
        for row in info_table.select("tr"):
            cells = row.find_all("td")
            if len(cells) != 2:
                continue
            key = (
                cells[0]
                .get_text(" ", strip=True)
                .strip()
                .lower()
                .replace("/", " ")
                .replace(".", "")
                .replace("-", " ")
                .replace("  ", " ")
                .replace(" ", "_")
            )
            profile[key] = cells[1].get_text(" ", strip=True)
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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Discover hydropower listing-date proxies from ShareSansar.")
    parser.add_argument("--limit", type=int, help="Optional limit for smoke testing.")
    parser.add_argument("--sleep-seconds", type=float, default=0.0, help="Optional pause between company requests.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
