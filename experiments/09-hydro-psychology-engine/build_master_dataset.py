"""Build the hydropower psychology master daily dataset.

This is the Phase 1 builder for experiment 09. It reads existing experiment
outputs, joins them by symbol/date, adds lightweight event-window context, and
writes only inside this experiment folder.
"""
from __future__ import annotations

import csv
import json
from collections import Counter, defaultdict
from datetime import date, datetime, timedelta
from pathlib import Path
from statistics import mean
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
CONFIG_PATH = SCRIPT_DIR / "config.json"
DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"

BROKER_DAILY_PATH = ROOT_DIR / "experiments" / "07-hydro-broker-flow" / "data" / "hydro_broker_flow_daily.csv"
VOLUME_DAILY_PATH = ROOT_DIR / "experiments" / "08-hydro-volume-tape-lab" / "data" / "volume_daily.csv"
CORP_EVENTS_PATH = ROOT_DIR / "experiments" / "01-corporate-action" / "data" / "events.csv"
LOCKIN_EVENTS_PATH = ROOT_DIR / "experiments" / "02-lockin-expiry" / "data" / "unlock_events.csv"
NRB_POLICY_PATH = ROOT_DIR / "experiments" / "03-nrb-rate-events" / "data" / "policy_events.csv"
NRB_RATE_PATH = ROOT_DIR / "experiments" / "03-nrb-rate-events" / "data" / "rate_move_events.csv"
SEASONALITY_PATH = ROOT_DIR / "experiments" / "04-hydro-seasonality" / "data" / "monthly_returns.csv"
FLOOD_EVENTS_PATH = ROOT_DIR / "experiments" / "06-hydro-flood-damage" / "data" / "flood_damage_event_table.csv"

OUTPUT_DAILY_PATH = DATA_DIR / "hydro_psychology_daily.csv"
OUTPUT_SUMMARY_PATH = RESULTS_DIR / "build_summary.md"


TAPE_COLUMNS = [
    "open",
    "high",
    "low",
    "close",
    "volume",
    "bars",
    "volume_ratio_20d",
    "return_pct",
    "range_pct",
    "close_position",
    "volume_spike",
    "volume_drought",
    "high_volume_up",
    "high_volume_down",
    "failed_rally",
    "absorption_candle",
]


CORP_DATE_COLUMNS = [
    "announcement_date",
    "approval_date",
    "book_close_date",
    "ex_date",
    "listing_date",
    "distribution_date",
    "meeting_date",
    "right_open_date",
    "right_close_date",
    "right_final_date",
]


def main() -> int:
    config = read_json(CONFIG_PATH)
    symbols = {symbol.upper() for symbol in config["symbols"]}
    windows = config.get("event_windows", {})

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    broker_rows = [row for row in read_csv(BROKER_DAILY_PATH) if row.get("symbol", "").upper() in symbols]
    tape_by_key = load_tape_rows(symbols)
    corp_index = load_corporate_events(symbols, int(windows.get("corporate_action_days", 5)))
    lockin_index = load_lockin_events(symbols, int(windows.get("lockin_days", 20)))
    nrb_index = load_market_events(int(windows.get("nrb_event_days", 3)))
    flood_index = load_flood_events(symbols, int(windows.get("flood_damage_days", 30)))
    seasonality = load_seasonality(symbols)

    output_rows: list[dict[str, Any]] = []
    for base in broker_rows:
        symbol = base["symbol"].upper()
        run_date = parse_iso_date(base["date"])
        if run_date is None:
            continue

        row = dict(base)
        merge_tape(row, tape_by_key.get((symbol, row["date"])))
        add_event_context(row, run_date, corp_index.get((symbol, run_date), []), "corp_action")
        add_event_context(row, run_date, lockin_index.get((symbol, run_date), []), "lockin")
        add_event_context(row, run_date, nrb_index.get(run_date, []), "nrb_event")
        add_event_context(row, run_date, flood_index.get((symbol, run_date), []), "flood_damage")
        row["seasonality_month_avg_return_pct"] = seasonality.get((symbol, run_date.month), "")
        row["quality_flags"] = build_quality_flags(row)
        output_rows.append(row)

    write_csv(OUTPUT_DAILY_PATH, output_rows)
    OUTPUT_SUMMARY_PATH.write_text(build_summary(output_rows, tape_by_key, config), encoding="utf-8")

    print(f"Wrote {OUTPUT_DAILY_PATH} ({len(output_rows)} rows)")
    print(f"Wrote {OUTPUT_SUMMARY_PATH}")
    return 0


def read_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def read_csv(path: Path) -> list[dict[str, str]]:
    if not path.exists() or path.stat().st_size == 0:
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames: list[str] = []
    for row in rows:
        for key in row:
            if key not in fieldnames:
                fieldnames.append(key)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def parse_iso_date(value: Any) -> date | None:
    if not value:
        return None
    text = str(value).strip()
    try:
        return datetime.strptime(text[:10], "%Y-%m-%d").date()
    except ValueError:
        return None


def date_range(center: date, radius_days: int) -> list[date]:
    return [center + timedelta(days=offset) for offset in range(-radius_days, radius_days + 1)]


def load_tape_rows(symbols: set[str]) -> dict[tuple[str, str], dict[str, str]]:
    rows = read_csv(VOLUME_DAILY_PATH)
    result: dict[tuple[str, str], dict[str, str]] = {}
    for row in rows:
        symbol = row.get("symbol", "").upper()
        run_date = row.get("date", "")
        if symbol in symbols and run_date:
            result[(symbol, run_date)] = row
    return result


def merge_tape(row: dict[str, Any], tape: dict[str, str] | None) -> None:
    row["tape_available"] = 1 if tape else 0
    for column in TAPE_COLUMNS:
        row[f"tape_{column}"] = tape.get(column, "") if tape else ""


def load_corporate_events(symbols: set[str], window_days: int) -> dict[tuple[str, date], list[str]]:
    index: dict[tuple[str, date], list[str]] = defaultdict(list)
    for row in read_csv(CORP_EVENTS_PATH):
        symbol = row.get("symbol", "").upper()
        if symbol not in symbols:
            continue
        label = event_label(row, "event_type")
        for column in CORP_DATE_COLUMNS:
            event_date = parse_iso_date(row.get(column))
            if event_date is None:
                continue
            for run_date in date_range(event_date, window_days):
                index[(symbol, run_date)].append(f"{label}:{column}:{event_date.isoformat()}")
    return index


def load_lockin_events(symbols: set[str], window_days: int) -> dict[tuple[str, date], list[str]]:
    index: dict[tuple[str, date], list[str]] = defaultdict(list)
    for row in read_csv(LOCKIN_EVENTS_PATH):
        symbol = row.get("symbol", "").upper()
        if symbol not in symbols:
            continue
        event_date = parse_iso_date(row.get("unlock_date_proxy"))
        if event_date is None:
            continue
        label = event_label(row, "event_type")
        for run_date in date_range(event_date, window_days):
            index[(symbol, run_date)].append(f"{label}:{event_date.isoformat()}")
    return index


def load_market_events(window_days: int) -> dict[date, list[str]]:
    index: dict[date, list[str]] = defaultdict(list)
    for path, fallback in [(NRB_POLICY_PATH, "policy"), (NRB_RATE_PATH, "rate_move")]:
        for row in read_csv(path):
            event_date = parse_iso_date(row.get("event_date"))
            if event_date is None:
                continue
            label = event_label(row, "event_type") or fallback
            for run_date in date_range(event_date, window_days):
                index[run_date].append(f"{label}:{event_date.isoformat()}")
    return index


def load_flood_events(symbols: set[str], window_days: int) -> dict[tuple[str, date], list[str]]:
    index: dict[tuple[str, date], list[str]] = defaultdict(list)
    for row in read_csv(FLOOD_EVENTS_PATH):
        symbol = row.get("ticker", "").upper()
        if symbol not in symbols:
            continue
        event_date = parse_iso_date(row.get("event_anchor_date") or row.get("event_start_date"))
        if event_date is None:
            continue
        severity = row.get("severity_bucket", "unknown") or "unknown"
        for run_date in date_range(event_date, window_days):
            index[(symbol, run_date)].append(f"{severity}:{event_date.isoformat()}")
    return index


def load_seasonality(symbols: set[str]) -> dict[tuple[str, int], str]:
    grouped: dict[tuple[str, int], list[float]] = defaultdict(list)
    for row in read_csv(SEASONALITY_PATH):
        symbol = row.get("symbol", "").upper()
        if symbol not in symbols:
            continue
        month = as_int(row.get("month"))
        return_pct = as_float(row.get("return_pct"))
        if month is not None and return_pct is not None:
            grouped[(symbol, month)].append(return_pct)
    return {
        key: f"{mean(values):.4f}"
        for key, values in grouped.items()
        if values
    }


def event_label(row: dict[str, str], preferred: str) -> str:
    for key in [preferred, "event_label", "raw_title", "detail"]:
        value = (row.get(key) or "").strip()
        if value:
            return value.replace("|", "/")
    return "event"


def add_event_context(row: dict[str, Any], run_date: date, events: list[str], prefix: str) -> None:
    row[f"{prefix}_window"] = 1 if events else 0
    row[f"{prefix}_events"] = "|".join(sorted(set(events)))


def build_quality_flags(row: dict[str, Any]) -> str:
    flags: list[str] = []
    if str(row.get("broker_available", "")).strip() != "1":
        flags.append("missing_broker_flow")
    if str(row.get("tape_available", "")).strip() != "1":
        flags.append("missing_intraday_volume")
    if str(row.get("corp_action_window", "")).strip() == "1":
        flags.append("event_window")
    if str(row.get("lockin_window", "")).strip() == "1":
        flags.append("lockin_window")
    if str(row.get("nrb_event_window", "")).strip() == "1":
        flags.append("nrb_event_window")
    if str(row.get("flood_damage_window", "")).strip() == "1":
        flags.append("flood_damage_window")
    if not row.get("fwd_10d_return_pct"):
        flags.append("no_forward_outcome_yet")
    return "|".join(flags)


def build_summary(rows: list[dict[str, Any]], tape_by_key: dict[tuple[str, str], dict[str, str]], config: dict[str, Any]) -> str:
    symbol_counts = Counter(row["symbol"] for row in rows)
    flag_counts: Counter[str] = Counter()
    for row in rows:
        for flag in str(row.get("quality_flags", "")).split("|"):
            if flag:
                flag_counts[flag] += 1

    tape_matches = sum(1 for row in rows if str(row.get("tape_available", "")) == "1")
    broker_rows = sum(1 for row in rows if str(row.get("broker_available", "")) == "1")
    event_rows = sum(1 for row in rows if str(row.get("corp_action_window", "")) == "1")
    lockin_rows = sum(1 for row in rows if str(row.get("lockin_window", "")) == "1")
    nrb_rows = sum(1 for row in rows if str(row.get("nrb_event_window", "")) == "1")
    flood_rows = sum(1 for row in rows if str(row.get("flood_damage_window", "")) == "1")

    lines = [
        "# Experiment 09 Build Summary",
        "",
        "Phase 1 master daily table build.",
        "",
        "## Inputs",
        "",
        f"- Broker-flow daily: `{relative(BROKER_DAILY_PATH)}`",
        f"- Volume/tape daily: `{relative(VOLUME_DAILY_PATH)}`",
        f"- Corporate events: `{relative(CORP_EVENTS_PATH)}`",
        f"- Lock-in events: `{relative(LOCKIN_EVENTS_PATH)}`",
        f"- NRB policy events: `{relative(NRB_POLICY_PATH)}`",
        f"- NRB rate events: `{relative(NRB_RATE_PATH)}`",
        f"- Seasonality: `{relative(SEASONALITY_PATH)}`",
        f"- Flood damage events: `{relative(FLOOD_EVENTS_PATH)}`",
        "",
        "## Coverage",
        "",
        f"- Symbols: {', '.join(config['symbols'])}",
        f"- Output rows: {len(rows):,}",
        f"- Broker-backed rows: {broker_rows:,}",
        f"- Tape-matched rows: {tape_matches:,}",
        f"- Loaded tape keys: {len(tape_by_key):,}",
        f"- Corporate-action window rows: {event_rows:,}",
        f"- Lock-in window rows: {lockin_rows:,}",
        f"- NRB event window rows: {nrb_rows:,}",
        f"- Flood damage window rows: {flood_rows:,}",
        "",
        "## Rows By Symbol",
        "",
        "| Symbol | Rows |",
        "|---|---:|",
    ]
    for symbol in config["symbols"]:
        lines.append(f"| {symbol} | {symbol_counts.get(symbol, 0):,} |")

    lines.extend([
        "",
        "## Quality Flags",
        "",
        "| Flag | Rows |",
        "|---|---:|",
    ])
    for flag, count in sorted(flag_counts.items()):
        lines.append(f"| {flag} | {count:,} |")

    lines.extend([
        "",
        "## Notes",
        "",
        "- This build is read-only toward upstream experiments.",
        "- Tape coverage is expected to be sparse until experiment 08 captures more hydropower symbols.",
        "- This file is not a trading signal yet. Phase 2 will add transparent psychology scoring.",
    ])
    return "\n".join(lines) + "\n"


def relative(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT_DIR)).replace("\\", "/")
    except ValueError:
        return str(path)


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(str(value).replace(",", ""))
    except ValueError:
        return None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    return int(number) if number is not None else None


if __name__ == "__main__":
    raise SystemExit(main())
