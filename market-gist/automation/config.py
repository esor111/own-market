"""
Configuration for stock analysis automation
"""
import json
import os
from datetime import datetime

# Base paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
SYMBOLS_DIR = os.path.join(DATA_DIR, "symbols")
VALIDATION_DIR = os.path.join(DATA_DIR, "validation")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")
AUTOMATION_DIR = os.path.dirname(os.path.abspath(__file__))
SECTOR_MAP_FILE = os.path.join(AUTOMATION_DIR, "sector_map.json")
SYMBOL_LISTS_FILE = os.path.join(AUTOMATION_DIR, "symbol_lists.json")

# Data subdirectories
RAW_DIR = os.path.join(DATA_DIR, "raw")
NORMALIZED_DIR = os.path.join(DATA_DIR, "normalized")
FEATURES_DIR = os.path.join(DATA_DIR, "features")

RAW_SCREENSHOTS_DIR = os.path.join(RAW_DIR, "screenshots")
RAW_SNAPSHOTS_DIR = os.path.join(RAW_DIR, "snapshots")
RAW_TABLES_DIR = os.path.join(RAW_DIR, "tables")

# NEPSE Alpha configuration
NEPSE_ALPHA_URL = "https://nepsealpha.com/nepse-chart"
DEFAULT_SYMBOL = "NEPSE"
DEFAULT_TIMEFRAME = "1D"

# Browser configuration
HEADLESS = False  # Set to True for production
BROWSER_TIMEOUT = 60000  # 60 seconds
SLOW_MO = 200  # Slow down by 200ms for stability

# Indicator configuration
INDICATORS = {
    "ema_20": {"name": "Moving Average Exponential", "search": "EMA", "period": 20},
    "ma_50": {"name": "Moving Average", "search": "MA", "period": 50},
    "macd": {"name": "MACD", "search": "MACD"},
    "rsi": {"name": "Relative Strength Index", "search": "Relative Strength Index"}
}

# Scoring thresholds
SCORING_RULES = {
    "market_alignment": {
        "strong_up": 10,
        "up": 7,
        "sideways": 5,
        "down": 3,
        "strong_down": 1
    },
    "trend_filter": {
        "above_both": 10,
        "above_ema20": 7,
        "above_ma50": 5,
        "below_both": 2
    },
    "rsi": {
        "oversold_bullish": 8,
        "neutral": 5,
        "overbought_bearish": 3
    },
    "relative_strength": {
        "outperforming_both": 10,
        "outperforming_one": 6,
        "underperforming_both": 2
    }
}

# Decision thresholds
DECISION_THRESHOLDS = {
    "strong_buy": 80,
    "buy": 65,
    "watch": 50,
    "avoid": 0
}


def normalize_timeframe_token(timeframe):
    """Return a filesystem-safe timeframe token."""
    return str(timeframe).upper().replace("/", "_")


def get_session_id(symbol, timeframe=None, date=None):
    """Generate a timeframe-safe session ID."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    symbol = str(symbol).upper()
    if timeframe:
        timeframe = normalize_timeframe_token(timeframe)
        return f"{date}__{symbol}__{timeframe}__v2"
    return f"{date}__{symbol}__v2"

def get_file_prefix(symbol, date=None):
    """Generate file prefix for naming"""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    return f"{date}__{symbol}"


def get_session_filename(symbol, timeframe, date=None):
    """Return the timeframe-safe session record filename."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    symbol = str(symbol).upper()
    timeframe = normalize_timeframe_token(timeframe)
    return f"{date}__{symbol}__{timeframe}__session_v2.json"


def get_decision_filename(symbol, timeframe, date=None):
    """Return the timeframe-safe decision record filename."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    symbol = str(symbol).upper()
    timeframe = normalize_timeframe_token(timeframe)
    return f"{date}__{symbol}__{timeframe}__decision_v2.json"


def get_model_input_filename(symbol, timeframe, date=None):
    """Return the timeframe-safe model-input filename."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")
    symbol = str(symbol).upper()
    timeframe = normalize_timeframe_token(timeframe)
    return f"{date}__{symbol}__{timeframe}__model_input_v1.json"


def get_run_directories(symbol, date=None):
    """Return symbol/date-scoped directories for a single analysis run."""
    if date is None:
        date = datetime.now().strftime("%Y-%m-%d")

    symbol = symbol.upper()
    base = os.path.join(SYMBOLS_DIR, symbol, date)

    return {
        "base": base,
        "raw": os.path.join(base, "raw"),
        "raw_screenshots": os.path.join(base, "raw", "screenshots"),
        "raw_snapshots": os.path.join(base, "raw", "snapshots"),
        "raw_tables": os.path.join(base, "raw", "tables"),
        "normalized": os.path.join(base, "normalized"),
        "normalized_sessions": os.path.join(base, "normalized", "sessions"),
        "normalized_market": os.path.join(base, "normalized", "market"),
        "normalized_sectors": os.path.join(base, "normalized", "sectors"),
        "normalized_candidates": os.path.join(base, "normalized", "candidates"),
        "normalized_stocks": os.path.join(base, "normalized", "stocks"),
        "normalized_indicators": os.path.join(base, "normalized", "indicators"),
        "normalized_events": os.path.join(base, "normalized", "events"),
        "normalized_broker_flow": os.path.join(base, "normalized", "broker_flow"),
        "normalized_relative_strength": os.path.join(base, "normalized", "relative_strength"),
        "normalized_decisions": os.path.join(base, "normalized", "decisions"),
        "features": os.path.join(base, "features"),
        "features_setup_scores": os.path.join(base, "features", "setup_scores"),
        "features_model_inputs": os.path.join(base, "features", "model_inputs"),
        "outcomes": os.path.join(base, "outcomes"),
        "outcomes_realized_results": os.path.join(base, "outcomes", "realized_results")
    }


def load_json_file(path, default):
    """Load JSON from disk, returning a default value when file is missing."""
    if not os.path.exists(path):
        return default
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def load_symbol_lists():
    """Return named symbol lists from automation/symbol_lists.json."""
    raw = load_json_file(SYMBOL_LISTS_FILE, {})
    symbol_lists = {}
    for name, values in raw.items():
        if isinstance(values, list):
            symbol_lists[str(name)] = [str(value).upper() for value in values if str(value).strip()]
    return symbol_lists


def resolve_symbols(args):
    """
    Resolve CLI symbol arguments into a unique ordered list.

    Supports:
    - plain symbols: SMHL NABIL
    - named lists: @core_reliability
    """
    symbol_lists = load_symbol_lists()
    resolved = []

    for arg in args:
        token = str(arg).strip()
        if not token:
            continue

        if token.startswith("@"):
            list_name = token[1:]
            symbols = symbol_lists.get(list_name)
            if symbols is None:
                raise ValueError(f"Unknown symbol list: {token}")
            resolved.extend(symbols)
        else:
            resolved.append(token.upper())

    unique_symbols = []
    seen = set()
    for symbol in resolved:
        if symbol not in seen:
            seen.add(symbol)
            unique_symbols.append(symbol)
    return unique_symbols
