from __future__ import annotations

from datetime import date
from pathlib import Path

import pandas as pd
import sys

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from price_loader import list_available_dates  # noqa: E402


DATA_DIR = SCRIPT_DIR / "data"


def main() -> None:
    listing_path = DATA_DIR / "listing_dates.csv"
    if not listing_path.exists():
        raise FileNotFoundError(f"Missing listing proxy file: {listing_path}")

    listing_frame = pd.read_csv(listing_path)
    listing_frame = listing_frame[listing_frame["first_trade_date_proxy"].notna() & (listing_frame["first_trade_date_proxy"] != "")]
    if listing_frame.empty:
        raise RuntimeError("No usable listing-date proxies found.")

    available_dates = list_available_dates()
    if not available_dates:
        raise RuntimeError("No local Sharesansar CSV dates found for unlock-date filtering.")

    local_start = available_dates[0]
    local_end = available_dates[-1]

    rows: list[dict] = []
    for item in listing_frame.to_dict("records"):
        first_trade_date = pd.Timestamp(item["first_trade_date_proxy"]).date()
        unlock_date = add_years(first_trade_date, 3)
        if unlock_date < local_start or unlock_date > local_end:
            continue

        rows.append(
            {
                "symbol": item["symbol"],
                "company_name": item["company_name"],
                "sector": item["sector"],
                "listing_date_proxy": first_trade_date.isoformat(),
                "unlock_date_proxy": unlock_date.isoformat(),
                "event_type": "promoter_lockin_expiry_proxy",
                "source_url": item.get("source_url", ""),
                "data_quality_note": item.get("data_quality_note", ""),
            }
        )

    if rows:
        unlock_frame = pd.DataFrame(rows).sort_values(["unlock_date_proxy", "symbol"]).reset_index(drop=True)
    else:
        unlock_frame = pd.DataFrame(
            columns=[
                "symbol",
                "company_name",
                "sector",
                "listing_date_proxy",
                "unlock_date_proxy",
                "event_type",
                "source_url",
                "data_quality_note",
            ]
        )
    csv_path = DATA_DIR / "unlock_events.csv"
    json_path = DATA_DIR / "unlock_events.json"
    unlock_frame.to_csv(csv_path, index=False)
    json_path.write_text(unlock_frame.to_json(orient="records", indent=2), encoding="utf-8")

    print(
        f"Wrote {len(unlock_frame)} unlock events inside local archive range "
        f"{local_start.isoformat()} to {local_end.isoformat()}."
    )


def add_years(value: date, years: int) -> date:
    try:
        return value.replace(year=value.year + years)
    except ValueError:
        return value.replace(month=2, day=28, year=value.year + years)


if __name__ == "__main__":
    main()
