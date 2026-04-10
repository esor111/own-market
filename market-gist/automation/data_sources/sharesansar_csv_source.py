"""Local truth-source adapter backed by sharesansar daily CSV snapshots."""
import csv
import json
import os
from datetime import datetime, timedelta

from .base import TruthSource


DEFAULT_DATA_DIR = os.path.abspath(
    os.path.join(
        os.path.dirname(__file__),
        "..",
        "..",
        "..",
        "sharesansar_datascrape",
        "data",
    )
)


class SharesansarCsvTruthSource(TruthSource):
    """Read historical daily market rows from local Sharesansar CSV files."""

    def __init__(self, data_dir=None, **_kwargs):
        self.data_dir = os.path.abspath(data_dir or DEFAULT_DATA_DIR)
        if not os.path.isdir(self.data_dir):
            raise FileNotFoundError(f"Sharesansar data directory not found: {self.data_dir}")

    def get_market_snapshot(self):
        latest_date = self._get_latest_available_date()
        latest_rows = self._load_rows_for_date(latest_date) if latest_date else []
        return {
            "market_open": None,
            "market_summary": [],
            "sectorwise_summary": [],
            "latest_business_date": latest_date.isoformat() if latest_date else None,
            "listed_symbol_count": len(latest_rows),
            "captured_at": datetime.now().isoformat(),
            "source_note": "Local Sharesansar CSV archive; market-level summary unavailable.",
        }

    def get_ticker_snapshot(self, symbol):
        symbol = str(symbol).upper()
        latest_market_date = self._get_latest_available_date()
        latest_symbol_date = self._find_latest_symbol_date(symbol)
        row = self._get_symbol_row_for_date(symbol, latest_market_date) if latest_market_date else None
        return {
            "symbol": symbol,
            "today_price_row": self._normalize_row(row, latest_market_date) if row else None,
            "ticker_info": {
                "security": {
                    "symbol": symbol,
                    "securityName": symbol,
                },
            },
            "captured_at": datetime.now().isoformat(),
            "latest_market_business_date": (
                latest_market_date.isoformat() if latest_market_date else None
            ),
            "latest_symbol_business_date": (
                latest_symbol_date.isoformat() if latest_symbol_date else None
            ),
            "source_note": "Ticker metadata is limited in Sharesansar CSV snapshots.",
        }

    def get_ticker_history(self, symbol, start_date, end_date):
        symbol = str(symbol).upper()
        start_dt = self._parse_iso_date(start_date)
        end_dt = self._parse_iso_date(end_date)
        content = []

        for business_date in self._iter_available_dates(start_dt, end_dt):
            row = self._get_symbol_row_for_date(symbol, business_date)
            if row:
                content.append(self._normalize_row(row, business_date))

        content.sort(key=lambda item: item["businessDate"], reverse=True)
        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "history": {
                "content": content,
                "totalElements": len(content),
            },
            "captured_at": datetime.now().isoformat(),
            "source_note": "Historical rows are reconstructed from local daily CSV files.",
        }

    def get_broker_directory(self):
        return {
            "brokers": [],
            "captured_at": datetime.now().isoformat(),
            "source_note": "Broker metadata is not present in Sharesansar daily CSV snapshots.",
        }

    def get_supply_demand(self, show_all=False):
        return {
            "show_all": bool(show_all),
            "supply_demand": [],
            "captured_at": datetime.now().isoformat(),
            "source_note": "Supply/demand data is not present in Sharesansar daily CSV snapshots.",
        }

    def build_truth_bundle(self, symbol, history_days=400):
        end_dt = self._get_latest_available_date()
        if not end_dt:
            raise RuntimeError("No Sharesansar CSV files were found.")

        end_date = end_dt.strftime("%Y-%m-%d")
        start_date = (end_dt - timedelta(days=history_days)).strftime("%Y-%m-%d")

        return {
            "provider": "sharesansar_local",
            "symbol": str(symbol).upper(),
            "market": self.get_market_snapshot(),
            "ticker": self.get_ticker_snapshot(symbol),
            "history": self.get_ticker_history(symbol, start_date, end_date),
            "brokers": self.get_broker_directory(),
            "supply_demand": self.get_supply_demand(show_all=True),
        }

    @staticmethod
    def save_json(filepath, payload):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as file_handle:
            json.dump(payload, file_handle, indent=2)

    def _get_latest_available_date(self):
        dates = list(self._iter_available_dates())
        return dates[-1] if dates else None

    def _find_latest_symbol_date(self, symbol):
        for business_date in reversed(list(self._iter_available_dates())):
            if self._get_symbol_row_for_date(symbol, business_date):
                return business_date
        return None

    def _iter_available_dates(self, start_dt=None, end_dt=None):
        for filename in sorted(os.listdir(self.data_dir)):
            if not filename.lower().endswith(".csv"):
                continue
            business_date = self._parse_filename_date(filename)
            if not business_date:
                continue
            if start_dt and business_date < start_dt:
                continue
            if end_dt and business_date > end_dt:
                continue
            yield business_date

    def _load_rows_for_date(self, business_date):
        path = self._csv_path_for_date(business_date)
        if not os.path.exists(path):
            return []
        with open(path, "r", encoding="utf-8-sig", newline="") as file_handle:
            return list(csv.DictReader(file_handle))

    def _get_symbol_row_for_date(self, symbol, business_date):
        if not business_date:
            return None
        rows = self._load_rows_for_date(business_date)
        return next((row for row in rows if str(row.get("Symbol", "")).upper() == symbol), None)

    def _csv_path_for_date(self, business_date):
        filename = business_date.strftime("%m_%d_%Y.csv")
        return os.path.join(self.data_dir, filename)

    @staticmethod
    def _parse_filename_date(filename):
        stem = os.path.splitext(filename)[0]
        try:
            return datetime.strptime(stem, "%m_%d_%Y").date()
        except ValueError:
            return None

    @staticmethod
    def _parse_iso_date(value):
        return datetime.strptime(value, "%Y-%m-%d").date()

    def _normalize_row(self, row, business_date):
        return {
            "businessDate": business_date.strftime("%Y-%m-%d"),
            "symbol": str(row.get("Symbol", "")).upper(),
            "openPrice": self._parse_number(row.get("Open")),
            "highPrice": self._parse_number(row.get("High")),
            "lowPrice": self._parse_number(row.get("Low")),
            "closePrice": self._parse_number(row.get("Close")),
            "lastTradedPrice": self._parse_number(row.get("LTP")),
            "vwap": self._parse_number(row.get("VWAP")),
            "totalTradedQuantity": self._parse_number(row.get("Vol")),
            "previousDayClosePrice": self._parse_number(row.get("Prev. Close")),
            "totalTradedValue": self._parse_number(row.get("Turnover")),
            "totalTrades": self._parse_number(row.get("Trans.")),
            "pointChange": self._parse_number(row.get("Diff")),
            "percentageChange": self._parse_number(row.get("Diff %")),
            "range": self._parse_number(row.get("Range")),
            "rangePercentage": self._parse_number(row.get("Range %")),
            "vwapPercentage": self._parse_number(row.get("VWAP %")),
            "fiftyTwoWeekHigh": self._parse_number(row.get("52 Weeks High")),
            "fiftyTwoWeekLow": self._parse_number(row.get("52 Weeks Low")),
            "oneHundredTwentyDayAverage": self._parse_number(row.get("120 Days")),
            "oneHundredEightyDayAverage": self._parse_number(row.get("180 Days")),
            "confirmation": row.get("Conf."),
        }

    @staticmethod
    def _parse_number(value):
        if value is None:
            return None
        text = str(value).strip()
        if not text or text == "-":
            return None
        text = text.replace(",", "")
        try:
            number = float(text)
        except ValueError:
            return None
        return int(number) if number.is_integer() else number
