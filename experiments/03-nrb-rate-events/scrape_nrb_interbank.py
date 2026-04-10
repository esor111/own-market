"""
Fetch official NRB short-term rate series via the public AJAX endpoint.

Primary target:
  - Weighted Average Interbank Rate (Daily), rate_id=62

Secondary context series:
  - Weighted Average Repo Rate, rate_id=63

Usage:
    python experiments/03-nrb-rate-events/scrape_nrb_interbank.py
"""
from __future__ import annotations

import argparse
import csv
from datetime import datetime
from pathlib import Path

import requests


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
AJAX_URL = "https://www.nrb.org.np/wp-admin/admin-ajax.php"

SERIES = [
    {
        "rate_type": "SHORT_TERM_RATE",
        "rate_id": "62",
        "series_key": "weighted_average_interbank_rate_daily",
    },
    {
        "rate_type": "SHORT_TERM_RATE",
        "rate_id": "63",
        "series_key": "weighted_average_repo_rate",
    },
]


def main() -> None:
    args = parse_args()
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    session = requests.Session()
    session.headers.update({"User-Agent": "Mozilla/5.0"})

    all_rows: list[dict] = []
    for spec in SERIES:
        rows = fetch_rate_series(
            session=session,
            date_from=args.date_from,
            date_to=args.date_to,
            rate_type=spec["rate_type"],
            rate_id=spec["rate_id"],
            series_key=spec["series_key"],
        )
        all_rows.extend(rows)

    if not all_rows:
        raise RuntimeError("NRB returned no rate rows from the official AJAX endpoint.")

    all_rows.sort(key=lambda row: (row["series_key"], row["date"]))
    output_path = DATA_DIR / "interbank_daily.csv"
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(
            handle,
            fieldnames=[
                "date",
                "series_key",
                "rate_name",
                "rate_type",
                "rate_id",
                "rate_pct",
                "change_from_prev",
                "source_url",
            ],
        )
        writer.writeheader()
        writer.writerows(all_rows)

    interbank_rows = [row for row in all_rows if row["series_key"] == "weighted_average_interbank_rate_daily"]
    print(f"Wrote {len(all_rows)} total rows to {output_path}")
    if interbank_rows:
        print(
            "Interbank range: "
            f"{interbank_rows[0]['date']} to {interbank_rows[-1]['date']} "
            f"({len(interbank_rows)} rows)"
        )


def fetch_rate_series(
    session: requests.Session,
    date_from: str,
    date_to: str,
    rate_type: str,
    rate_id: str,
    series_key: str,
) -> list[dict]:
    payload = {
        "action": "get_rates",
        "date_from": date_from,
        "date_to": date_to,
        "rate_type": rate_type,
        "rate_id": rate_id,
    }
    response = session.post(AJAX_URL, data=payload, timeout=60)
    response.raise_for_status()

    body = response.json()
    if not body.get("success"):
        raise RuntimeError(f"NRB AJAX returned unsuccessful payload for rate_id={rate_id}: {body}")

    data = body.get("data") or {}
    labels = data.get("label") or []
    values = data.get("values") or []
    if len(labels) != len(values):
        raise RuntimeError(
            f"Length mismatch for rate_id={rate_id}: {len(labels)} labels vs {len(values)} values"
        )

    rows: list[dict] = []
    previous_value: float | None = None
    for label, raw_value in zip(labels, values):
        business_date = datetime.strptime(label, "%B %d, %Y").date().isoformat()
        rate_value = float(raw_value)
        rows.append(
            {
                "date": business_date,
                "series_key": series_key,
                "rate_name": data.get("rate_name") or series_key,
                "rate_type": rate_type,
                "rate_id": rate_id,
                "rate_pct": round(rate_value, 4),
                "change_from_prev": (
                    None if previous_value is None else round(rate_value - previous_value, 4)
                ),
                "source_url": AJAX_URL,
            }
        )
        previous_value = rate_value

    return rows


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Fetch official NRB interbank/repo rate series.")
    parser.add_argument("--date-from", default="2022-01-01")
    parser.add_argument("--date-to", default="2025-12-31")
    return parser.parse_args()


if __name__ == "__main__":
    main()
