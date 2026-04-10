"""
Build monthly return tables for hydro and bank stocks.

For each symbol, computes the return from first trading day of the month
to last trading day of the month. Groups by calendar month (1-12).

Output:
  data/monthly_returns.csv     — one row per symbol × year × month
  data/monthly_returns.json    — same in JSON
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from price_loader import load_symbol_prices  # noqa: E402


DATA_DIR = SCRIPT_DIR / "data"

HYDRO_SYMBOLS = ["SMHL", "HIDCL", "NGPL", "API", "AKPL", "UPPER"]
BANK_SYMBOLS = ["NABIL", "NBL", "EBL", "HBL", "KBL", "SANIMA", "PRVU", "NIMB"]

SECTOR_MAP = {}
for s in HYDRO_SYMBOLS:
    SECTOR_MAP[s] = "Hydropower"
for s in BANK_SYMBOLS:
    SECTOR_MAP[s] = "Commercial Bank"


def main() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    all_symbols = HYDRO_SYMBOLS + BANK_SYMBOLS
    rows: list[dict] = []

    for symbol in all_symbols:
        print(f"Loading {symbol}...")
        prices = load_symbol_prices(symbol)
        if prices.empty:
            print(f"  No price data for {symbol}, skipping.")
            continue

        monthly = compute_monthly_returns(prices, symbol)
        rows.extend(monthly)
        print(f"  {len(monthly)} monthly return rows for {symbol}")

    if not rows:
        raise RuntimeError("No monthly returns computed for any symbol.")

    frame = pd.DataFrame(rows).sort_values(
        ["sector", "symbol", "year", "month"]
    ).reset_index(drop=True)

    csv_path = DATA_DIR / "monthly_returns.csv"
    json_path = DATA_DIR / "monthly_returns.json"
    frame.to_csv(csv_path, index=False)
    json_path.write_text(frame.to_json(orient="records", indent=2), encoding="utf-8")

    print(f"\nWrote {len(frame)} monthly return rows to {csv_path}")
    print(f"Symbols: {frame['symbol'].nunique()}")
    print(f"Year range: {frame['year'].min()} - {frame['year'].max()}")


def compute_monthly_returns(prices: pd.DataFrame, symbol: str) -> list[dict]:
    """Compute one return per calendar month from first-to-last close in that month."""
    frame = prices.copy()
    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)

    if frame.empty:
        return []

    frame["year"] = frame["date"].dt.year
    frame["month"] = frame["date"].dt.month

    rows: list[dict] = []
    for (year, month), group in frame.groupby(["year", "month"]):
        group = group.sort_values("date")
        if len(group) < 2:
            continue

        first_row = group.iloc[0]
        last_row = group.iloc[-1]
        open_price = first_row["close"]
        close_price = last_row["close"]

        if open_price is None or open_price == 0 or close_price is None:
            continue

        return_pct = ((close_price / open_price) - 1.0) * 100.0

        rows.append({
            "symbol": symbol,
            "sector": SECTOR_MAP.get(symbol, "Unknown"),
            "year": int(year),
            "month": int(month),
            "month_name": first_row["date"].strftime("%b"),
            "first_date": first_row["date"].date().isoformat(),
            "last_date": last_row["date"].date().isoformat(),
            "trading_days": len(group),
            "open_price": open_price,
            "close_price": close_price,
            "return_pct": round(return_pct, 4),
            "positive": return_pct > 0,
        })

    return rows


if __name__ == "__main__":
    main()
