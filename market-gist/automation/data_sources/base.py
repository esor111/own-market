"""Base interface for external raw-data truth providers."""
from abc import ABC, abstractmethod


class TruthSource(ABC):
    """Abstract interface for pluggable market truth providers."""

    @abstractmethod
    def get_market_snapshot(self):
        """Return market-level truth data."""

    @abstractmethod
    def get_ticker_snapshot(self, symbol):
        """Return latest symbol-level truth data."""

    @abstractmethod
    def get_ticker_history(self, symbol, start_date, end_date):
        """Return historical symbol data for a date range."""

    @abstractmethod
    def get_broker_directory(self):
        """Return broker/member metadata if available."""

    @abstractmethod
    def get_supply_demand(self, show_all=False):
        """Return supply/demand style data if available."""

    @abstractmethod
    def build_truth_bundle(self, symbol, history_days=400):
        """Return a full truth bundle for one symbol."""
