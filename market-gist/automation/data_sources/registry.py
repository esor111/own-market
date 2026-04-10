"""Registry for pluggable truth providers."""
from .nepse_scraper_source import NepseScraperTruthSource
from .sharesansar_csv_source import SharesansarCsvTruthSource


TRUTH_SOURCE_FACTORIES = {
    "nepse_scraper": lambda **kwargs: NepseScraperTruthSource(**kwargs),
    "sharesansar_local": lambda **kwargs: SharesansarCsvTruthSource(**kwargs),
}


def available_truth_sources():
    """Return the list of registered truth providers."""
    return sorted(TRUTH_SOURCE_FACTORIES.keys())


def get_truth_source(name, **kwargs):
    """Instantiate a truth provider by name."""
    key = str(name).strip().lower()
    if key not in TRUTH_SOURCE_FACTORIES:
        raise ValueError(f"Unknown truth source: {name}")
    return TRUTH_SOURCE_FACTORIES[key](**kwargs)
