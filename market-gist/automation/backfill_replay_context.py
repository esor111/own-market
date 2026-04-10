"""
Backfill replay-safe external context for one historical year.

This script focuses on the layers that are missing from the local CSV archive:
- official NEPSE market summary history
- official NEPSE benchmark and sector/sub-index histories
- official NEPSE holidays listing
- official SEBON right-share / prospectus tables

Usage:
    python backfill_replay_context.py 2025
"""
import html
import json
import os
import re
import ssl
import sys
import urllib.request
from io import StringIO
from datetime import datetime

import pandas as pd

from config import VALIDATION_DIR
from data_sources.nepse_scraper_source import NepseScraperTruthSource


USER_AGENT = "Mozilla/5.0 (compatible; MarketGistBot/1.0)"
UNVERIFIED_SSL_CONTEXT = ssl._create_unverified_context()


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _fetch(url):
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=30, context=UNVERIFIED_SSL_CONTEXT) as response:
        return response.read().decode("utf-8", errors="ignore")


def _clean_text(value):
    text = re.sub(r"<[^>]+>", " ", value or "")
    text = html.unescape(text)
    return re.sub(r"\s+", " ", text).strip()


def _parse_sebon_table(url):
    html_text = _fetch(url)
    tables = pd.read_html(StringIO(html_text))
    if not tables:
        return []

    table = tables[0].fillna("")
    columns = [str(col).strip().lower() for col in table.columns]
    if len(columns) < 2:
        return []

    title_col = table.columns[0]
    date_col = table.columns[1]
    rows = []
    link_pattern = re.compile(
        r"<tr>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>",
        re.IGNORECASE | re.DOTALL,
    )
    link_rows = link_pattern.findall(html_text)

    for index, row in enumerate(table.to_dict(orient="records")):
        english_url = ""
        nepali_url = ""
        if index < len(link_rows):
            _, _, english_col, nepali_col = link_rows[index]
            english_match = re.search(r'href="(.*?)"', english_col or "", re.IGNORECASE)
            nepali_match = re.search(r'href="(.*?)"', nepali_col or "", re.IGNORECASE)
            english_url = _clean_text(english_match.group(1) if english_match else "")
            nepali_url = _clean_text(nepali_match.group(1) if nepali_match else "")
        rows.append({
            "title": _clean_text(str(row.get(title_col, ""))),
            "event_date": _clean_text(str(row.get(date_col, "")))[:10],
            "english_url": english_url,
            "nepali_url": nepali_url,
        })
    return rows


def _parse_holiday_listing(client, year):
    rows = client.session.get("/api/nots/holiday/list", params={"year": year}).json()
    return [
        {
            "title": _clean_text(item.get("holidayDescription", "")),
            "event_date": _clean_text(item.get("holidayDate", ""))[:10],
        }
        for item in rows
        if _clean_text(item.get("holidayDescription", "")) and _clean_text(item.get("holidayDate", ""))
    ]


def _filter_year_rows(rows, year, date_field="businessDate"):
    filtered = []
    for row in rows:
        value = str(row.get(date_field) or "").strip()
        if len(value) >= 4 and value[:4] == str(year):
            filtered.append(row)
    return filtered


def _fetch_index_history(client, index_id):
    response = client.session.get(f"/api/nots/index/history/{index_id}", params={"page": 0, "size": 500})
    payload = response.json()
    return payload.get("content", []) if isinstance(payload, dict) else []


def _build_markdown(summary):
    benchmark = summary.get("benchmark_history") or {}
    sector = summary.get("sector_index_history") or {}
    events = summary.get("event_tables") or {}
    holidays = summary.get("holiday_calendar") or {}
    lines = [
        "# Replay Context Backfill",
        "",
        f"- year: `{summary['year']}`",
        f"- built at: `{summary['built_at']}`",
        "",
        "## Coverage",
        "",
        f"- market summary rows: `{benchmark.get('market_summary_history_count')}`",
        f"- benchmark index families fetched: `{benchmark.get('index_count')}`",
        f"- benchmark rows for target year: `{benchmark.get('filtered_row_count')}`",
        f"- sector rows for target year: `{sector.get('filtered_row_count')}`",
        f"- holiday rows for target year: `{holidays.get('filtered_count')}`",
        f"- right-share approved rows for target year: `{events.get('right_share_approved_count')}`",
        f"- right-share pipeline rows for target year: `{events.get('right_share_pipeline_count')}`",
        f"- prospectus rows for target year: `{events.get('prospectus_count')}`",
        "",
        "## Important Notes",
        "",
    ]
    for note in summary.get("notes", []):
        lines.append(f"- {note}")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python backfill_replay_context.py YEAR")
        sys.exit(1)

    year = int(sys.argv[1])
    client = NepseScraperTruthSource(verify_ssl=False).client

    market_summary_history = client.get_market_summary_history()
    sector_indices = client.get_sector_indices()
    index_overview = client.call_endpoint("nepse_index_api")

    index_histories = []
    for item in (index_overview or []):
        index_id = item.get("id")
        if index_id is None:
            continue
        rows = _fetch_index_history(client, index_id)
        index_histories.append({
            "id": index_id,
            "index_name": item.get("index"),
            "rows": rows,
            "filtered_rows": _filter_year_rows(rows, year),
        })

    sector_histories = []
    for item in (sector_indices or []):
        index_id = item.get("id")
        if index_id is None:
            continue
        rows = _fetch_index_history(client, index_id)
        sector_histories.append({
            "id": index_id,
            "index_code": item.get("indexCode"),
            "index_name": item.get("indexName"),
            "sector_name": ((item.get("sectorMaster") or {}).get("sectorDescription")),
            "rows": rows,
            "filtered_rows": _filter_year_rows(rows, year),
        })

    holiday_rows = _parse_holiday_listing(client, year)
    right_share_approved = _parse_sebon_table("https://www.sebon.gov.np/right-share-approved")
    right_share_pipeline = _parse_sebon_table("https://www.sebon.gov.np/right-share-pipeline")
    prospectus_rows = _parse_sebon_table("https://www.sebon.gov.np/prospectus")

    market_summary_2025 = _filter_year_rows(market_summary_history, year)
    holiday_rows_year = _filter_year_rows(holiday_rows, year, date_field="event_date")
    right_approved_year = _filter_year_rows(right_share_approved, year, date_field="event_date")
    right_pipeline_year = _filter_year_rows(right_share_pipeline, year, date_field="event_date")
    prospectus_year = _filter_year_rows(prospectus_rows, year, date_field="event_date")

    benchmark_filtered_count = sum(len(item["filtered_rows"]) for item in index_histories)
    sector_filtered_count = sum(len(item["filtered_rows"]) for item in sector_histories)

    notes = []
    if not market_summary_2025:
        notes.append("official market summary history returned no rows for the target year")
    else:
        earliest_market_summary_date = min(row["businessDate"] for row in market_summary_2025)
        if not earliest_market_summary_date.startswith(f"{year}-01"):
            notes.append(
                f"official market summary history appears to be rolling and starts at `{earliest_market_summary_date}` for target year `{year}`"
            )
    if benchmark_filtered_count == 0:
        notes.append("official benchmark/sub-index history source returned no rows for the target year")
    else:
        earliest_benchmark_date = min(
            row["businessDate"]
            for item in index_histories for row in item["filtered_rows"]
        )
        if not earliest_benchmark_date.startswith(f"{year}-01"):
            notes.append(
                f"official benchmark/sub-index history appears to be rolling and starts at `{earliest_benchmark_date}` for target year `{year}`"
            )
    if not holiday_rows_year:
        notes.append("holiday listing parser did not find target-year holiday rows and may need refinement")

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "year": year,
        "notes": notes,
        "benchmark_history": {
            "market_summary_history_count": len(market_summary_2025),
            "index_count": len(index_histories),
            "filtered_row_count": benchmark_filtered_count,
            "indices": [
                {
                    "id": item["id"],
                    "index_name": item["index_name"],
                    "row_count": len(item["rows"]),
                    "filtered_row_count": len(item["filtered_rows"]),
                    "first_filtered_date": item["filtered_rows"][-1]["businessDate"] if item["filtered_rows"] else None,
                    "last_filtered_date": item["filtered_rows"][0]["businessDate"] if item["filtered_rows"] else None,
                }
                for item in index_histories
            ],
            "market_summary_history_rows": market_summary_2025,
            "index_history_rows": [
                {
                    "id": item["id"],
                    "index_name": item["index_name"],
                    "rows": item["filtered_rows"],
                }
                for item in index_histories
            ],
        },
        "sector_index_history": {
            "index_count": len(sector_histories),
            "filtered_row_count": sector_filtered_count,
            "indices": [
                {
                    "id": item["id"],
                    "index_code": item["index_code"],
                    "index_name": item["index_name"],
                    "sector_name": item["sector_name"],
                    "row_count": len(item["rows"]),
                    "filtered_row_count": len(item["filtered_rows"]),
                    "first_filtered_date": item["filtered_rows"][-1]["businessDate"] if item["filtered_rows"] else None,
                    "last_filtered_date": item["filtered_rows"][0]["businessDate"] if item["filtered_rows"] else None,
                }
                for item in sector_histories
            ],
            "index_history_rows": [
                {
                    "id": item["id"],
                    "index_code": item["index_code"],
                    "index_name": item["index_name"],
                    "sector_name": item["sector_name"],
                    "rows": item["filtered_rows"],
                }
                for item in sector_histories
            ],
        },
        "holiday_calendar": {
            "filtered_count": len(holiday_rows_year),
            "rows": holiday_rows_year,
        },
        "event_tables": {
            "right_share_approved_count": len(right_approved_year),
            "right_share_pipeline_count": len(right_pipeline_year),
            "prospectus_count": len(prospectus_year),
            "right_share_approved_rows": right_approved_year,
            "right_share_pipeline_rows": right_pipeline_year,
            "prospectus_rows": prospectus_year,
        },
    }

    target_dir = os.path.join(VALIDATION_DIR, "historical_context_backfills")
    base = f"{year}__official_replay_context_backfill_v1"
    json_path = os.path.join(target_dir, f"{base}.json")
    latest_json_path = os.path.join(target_dir, f"latest__{base}.json")
    md_path = os.path.join(target_dir, f"{base}.md")
    latest_md_path = os.path.join(target_dir, f"latest__{base}.md")
    markdown = _build_markdown(payload)

    save_json(json_path, payload)
    save_json(latest_json_path, payload)
    save_text(md_path, markdown)
    save_text(latest_md_path, markdown)

    print(json.dumps({
        "saved_json": os.path.abspath(json_path),
        "saved_latest_json": os.path.abspath(latest_json_path),
        "saved_md": os.path.abspath(md_path),
        "saved_latest_md": os.path.abspath(latest_md_path),
        "notes": notes,
        "benchmark_filtered_row_count": benchmark_filtered_count,
        "sector_filtered_row_count": sector_filtered_count,
        "market_summary_history_count": len(market_summary_2025),
        "holiday_count": len(holiday_rows_year),
        "right_share_approved_count": len(right_approved_year),
        "right_share_pipeline_count": len(right_pipeline_year),
        "prospectus_count": len(prospectus_year),
    }, indent=2))


if __name__ == "__main__":
    main()
