"""Backward-compatible shim for the new pluggable truth-source layer."""

from data_sources.nepse_scraper_source import NepseScraperTruthSource


class NepseTruthAdapter(NepseScraperTruthSource):
    """Compatibility alias for existing code paths."""
