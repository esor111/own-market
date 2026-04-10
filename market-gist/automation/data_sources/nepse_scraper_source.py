"""Truth-source adapter backed by the external nepse_scraper repository."""
import json
import os
import sys
from datetime import datetime, timedelta

from .base import TruthSource


EXTERNAL_REPO_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..", "..", "external", "nepse_scraper")
)


class NepseScraperTruthSource(TruthSource):
    """Fetch normalized raw truth data from the NEPSE scraper client."""

    def __init__(self, verify_ssl=False):
        if EXTERNAL_REPO_DIR not in sys.path:
            sys.path.insert(0, EXTERNAL_REPO_DIR)

        from nepse_scraper import NepseScraper  # noqa: WPS433

        self.client = NepseScraper(verify_ssl=verify_ssl)

    def get_market_snapshot(self):
        market_open = self.client.is_market_open()
        market_summary = self.client.get_market_summary()
        sectorwise_summary = self.client.get_sectorwise_summary()

        return {
            "market_open": market_open,
            "market_summary": market_summary,
            "sectorwise_summary": sectorwise_summary,
            "captured_at": datetime.now().isoformat(),
        }

    def get_ticker_snapshot(self, symbol):
        symbol = str(symbol).upper()
        ticker_info = self.client.get_ticker_info(symbol)
        today_prices = self.client.get_today_price()
        today_row = next((item for item in today_prices if item.get("symbol") == symbol), None)

        return {
            "symbol": symbol,
            "today_price_row": today_row,
            "ticker_info": ticker_info,
            "captured_at": datetime.now().isoformat(),
        }

    def get_ticker_history(self, symbol, start_date, end_date):
        symbol = str(symbol).upper()
        history = self.client.get_ticker_price_history(symbol, start_date, end_date)
        return {
            "symbol": symbol,
            "start_date": start_date,
            "end_date": end_date,
            "history": history,
            "captured_at": datetime.now().isoformat(),
        }

    def get_broker_directory(self):
        brokers = self.client.get_brokers()
        return {
            "brokers": brokers,
            "captured_at": datetime.now().isoformat(),
        }

    def get_supply_demand(self, show_all=False):
        supply_demand = self.client.get_supply_demand(show_all=show_all)
        return {
            "show_all": show_all,
            "supply_demand": supply_demand,
            "captured_at": datetime.now().isoformat(),
        }

    def get_company_disclosures(self):
        disclosures = self.client.get_company_disclosures()
        return {
            "disclosures": disclosures,
            "captured_at": datetime.now().isoformat(),
        }

    def get_notices(self):
        notices = self.client.get_notices()
        return {
            "notices": notices,
            "captured_at": datetime.now().isoformat(),
        }

    def build_truth_bundle(self, symbol, history_days=400):
        end_date = datetime.now().strftime("%Y-%m-%d")
        start_date = (datetime.now() - timedelta(days=history_days)).strftime("%Y-%m-%d")

        return {
            "provider": "nepse_scraper",
            "symbol": str(symbol).upper(),
            "market": self.get_market_snapshot(),
            "ticker": self.get_ticker_snapshot(symbol),
            "history": self.get_ticker_history(symbol, start_date, end_date),
            "brokers": self.get_broker_directory(),
            "supply_demand": self.get_supply_demand(show_all=True),
            "disclosures": self.get_company_disclosures(),
            "notices": self.get_notices(),
        }

    @staticmethod
    def save_json(filepath, payload):
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(payload, f, indent=2)
