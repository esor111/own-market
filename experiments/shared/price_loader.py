from __future__ import annotations

import csv
from datetime import date, datetime
from functools import lru_cache
from pathlib import Path
from typing import Iterable

import pandas as pd


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_DATA_DIR = ROOT_DIR / "sharesansar_datascrape" / "data"


def parse_date(value: str | date | datetime | pd.Timestamp | None) -> date | None:
    if value is None or value == "":
        return None
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, pd.Timestamp):
        return value.date()
    if isinstance(value, date):
        return value
    return datetime.strptime(str(value), "%Y-%m-%d").date()


def list_available_dates(data_dir: str | Path | None = None) -> list[date]:
    base_dir = Path(data_dir or DEFAULT_DATA_DIR)
    dates: list[date] = []
    for csv_path in sorted(base_dir.glob("*.csv")):
        try:
            dates.append(datetime.strptime(csv_path.stem, "%m_%d_%Y").date())
        except ValueError:
            continue
    return dates


def load_symbol_prices(
    symbol: str,
    start_date: str | date | datetime | pd.Timestamp | None = None,
    end_date: str | date | datetime | pd.Timestamp | None = None,
    data_dir: str | Path | None = None,
    collapse_duplicate_sessions: bool = True,
) -> pd.DataFrame:
    target = str(symbol).upper().strip()
    start_dt = parse_date(start_date)
    end_dt = parse_date(end_date)
    base_dir = Path(data_dir or DEFAULT_DATA_DIR)

    rows: list[dict] = []
    for business_date in list_available_dates(base_dir):
        if start_dt and business_date < start_dt:
            continue
        if end_dt and business_date > end_dt:
            continue

        daily_rows = _load_daily_rows(_csv_path_for_date(base_dir, business_date))
        match = next((row for row in daily_rows if row["symbol"] == target), None)
        if match:
            rows.append(match)

    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "symbol",
                "open",
                "high",
                "low",
                "close",
                "ltp",
                "vwap",
                "volume",
                "previous_close",
                "turnover",
                "trades",
                "diff",
                "diff_pct",
                "range",
                "range_pct",
                "vwap_pct",
                "confirmation",
            ]
        )

    frame["date"] = pd.to_datetime(frame["date"])
    frame = frame.sort_values("date").reset_index(drop=True)
    if collapse_duplicate_sessions:
        frame = _collapse_duplicate_sessions(frame)
    return frame


def load_market_rows(
    business_date: str | date | datetime | pd.Timestamp,
    data_dir: str | Path | None = None,
) -> pd.DataFrame:
    target_date = parse_date(business_date)
    if target_date is None:
        raise ValueError("business_date is required")

    base_dir = Path(data_dir or DEFAULT_DATA_DIR)
    rows = _load_daily_rows(_csv_path_for_date(base_dir, target_date))
    frame = pd.DataFrame(rows)
    if frame.empty:
        return frame
    frame["date"] = pd.to_datetime(frame["date"])
    return frame.sort_values("symbol").reset_index(drop=True)


def available_symbol_range(
    symbol: str,
    data_dir: str | Path | None = None,
) -> tuple[date | None, date | None]:
    prices = load_symbol_prices(symbol, data_dir=data_dir)
    if prices.empty:
        return None, None
    return prices.iloc[0]["date"].date(), prices.iloc[-1]["date"].date()


def _csv_path_for_date(base_dir: Path, business_date: date) -> Path:
    return base_dir / f"{business_date.strftime('%m_%d_%Y')}.csv"


@lru_cache(maxsize=512)
def _load_daily_rows(csv_path: Path | str) -> tuple[dict, ...]:
    path = Path(csv_path)
    if not path.exists():
        return tuple()

    business_date = datetime.strptime(path.stem, "%m_%d_%Y").date().isoformat()
    rows: list[dict] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            rows.append(
                {
                    "date": business_date,
                    "symbol": _clean_text(raw.get("Symbol")).upper(),
                    "open": _parse_number(raw.get("Open")),
                    "high": _parse_number(raw.get("High")),
                    "low": _parse_number(raw.get("Low")),
                    "close": _parse_number(raw.get("Close")),
                    "ltp": _parse_number(raw.get("LTP")),
                    "vwap": _parse_number(raw.get("VWAP")),
                    "volume": _parse_number(raw.get("Vol")),
                    "previous_close": _parse_number(raw.get("Prev. Close")),
                    "turnover": _parse_number(raw.get("Turnover")),
                    "trades": _parse_number(raw.get("Trans.")),
                    "diff": _parse_number(raw.get("Diff")),
                    "diff_pct": _parse_number(raw.get("Diff %")),
                    "range": _parse_number(raw.get("Range")),
                    "range_pct": _parse_number(raw.get("Range %")),
                    "vwap_pct": _parse_number(raw.get("VWAP %")),
                    "confirmation": _clean_text(raw.get("Conf.")),
                }
            )
    return tuple(rows)


def _parse_number(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip()
    if not text or text == "-":
        return None
    text = text.replace(",", "")
    try:
        return float(text)
    except ValueError:
        return None


def _clean_text(value: object) -> str:
    return "" if value is None else str(value).strip()


def _collapse_duplicate_sessions(frame: pd.DataFrame) -> pd.DataFrame:
    comparison_cols = [
        "open",
        "high",
        "low",
        "close",
        "ltp",
        "vwap",
        "volume",
        "previous_close",
        "turnover",
        "trades",
        "diff",
        "diff_pct",
        "range",
        "range_pct",
        "vwap_pct",
    ]
    current = frame[comparison_cols].copy()
    previous = current.shift(1)
    duplicate_mask = current.fillna("__MISSING__").eq(previous.fillna("__MISSING__")).all(axis=1)
    return frame.loc[~duplicate_mask].reset_index(drop=True)
