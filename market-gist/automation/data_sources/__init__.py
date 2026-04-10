"""Pluggable raw-data provider layer for the market analysis pipeline."""

from .registry import available_truth_sources, get_truth_source

__all__ = ["available_truth_sources", "get_truth_source"]
