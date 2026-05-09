"""Build the hydro volume/tape dataset from raw scraper outputs.

Reads `raw/<SYMBOL>/<symbol>_volume_daily.csv` files produced by
`refresh_hydro_volumes.ps1` (which wraps the existing Node scraper).

Writes:
    data/volume_daily.csv     - multi-symbol daily rows with derived labels
    data/volume_events.csv    - rows flagged with volume/tape labels
    data/volume_summary.json  - per-symbol rollups, coverage, latest state
    results/volume_findings.md
    results/<focus_lower>_volume_read.md  (when --focus given)

Clean experiment lane. Does not touch live prediction or persistence shadow.
"""
from __future__ import annotations

import argparse
import csv
import json
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
CONFIG_PATH = SCRIPT_DIR / "config.json"
RAW_DIR = SCRIPT_DIR / "raw"
DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"


VOLUME_SPIKE_RATIO = 2.0
VOLUME_DROUGHT_RATIO = 0.5
HIGH_VOLUME_RATIO = 1.5
WIDE_RANGE_PCT = 5.0
ABSORPTION_CLOSE_POSITION = 0.60
FAILED_RALLY_CLOSE_POSITION = 0.40


VOLUME_LABELS = [
    "volume_spike",
    "volume_drought",
    "high_volume_up",
    "high_volume_down",
    "failed_rally",
    "absorption_candle",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build the hydro volume/tape dataset.")
    parser.add_argument("--focus", help="Optional focus symbol for a dedicated volume-read markdown.")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    symbols = [symbol.upper() for symbol in config["symbols"]]
    focus = args.focus.upper().strip() if args.focus else None
    if focus and focus not in symbols:
        raise SystemExit(f"--focus {focus} is not in config.symbols ({symbols}).")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    all_rows: list[dict[str, Any]] = []
    coverage: list[dict[str, Any]] = []
    for symbol in symbols:
        symbol_rows = load_symbol_daily(symbol)
        decorate_rows(symbol_rows)
        all_rows.extend(symbol_rows)
        coverage.append(coverage_for(symbol, symbol_rows))

    event_rows = [row for row in all_rows if any(row.get(label) == 1 for label in VOLUME_LABELS)]

    daily_path = DATA_DIR / "volume_daily.csv"
    events_path = DATA_DIR / "volume_events.csv"
    summary_path = DATA_DIR / "volume_summary.json"
    findings_path = RESULTS_DIR / "volume_findings.md"

    write_csv(daily_path, all_rows)
    write_csv(events_path, event_rows)

    summary = {
        "symbols": symbols,
        "coverage": coverage,
        "label_counts": label_counts(all_rows),
        "thresholds": {
            "volume_spike_ratio": VOLUME_SPIKE_RATIO,
            "volume_drought_ratio": VOLUME_DROUGHT_RATIO,
            "high_volume_ratio": HIGH_VOLUME_RATIO,
            "wide_range_pct": WIDE_RANGE_PCT,
            "absorption_close_position": ABSORPTION_CLOSE_POSITION,
            "failed_rally_close_position": FAILED_RALLY_CLOSE_POSITION,
        },
    }
    summary_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    findings_path.write_text(build_findings(summary, all_rows), encoding="utf-8")

    print(f"Wrote {daily_path} ({len(all_rows)} rows)")
    print(f"Wrote {events_path} ({len(event_rows)} rows)")
    print(f"Wrote {summary_path}")
    print(f"Wrote {findings_path}")

    if focus:
        focus_rows = sorted(
            [row for row in all_rows if row["symbol"] == focus],
            key=lambda row: row["date"],
        )
        focus_path = RESULTS_DIR / f"{focus.lower()}_volume_read.md"
        focus_path.write_text(build_focus_read(focus, focus_rows, coverage), encoding="utf-8")
        print(f"Wrote {focus_path}")

    return 0


def load_symbol_daily(symbol: str) -> list[dict[str, Any]]:
    symbol_dir = RAW_DIR / symbol
    path = symbol_dir / f"{symbol.lower()}_volume_daily.csv"
    if not path.exists():
        return []
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            rows.append({
                "symbol": symbol,
                "date": (raw.get("date_np") or raw.get("date") or "").strip(),
                "open": as_float(raw.get("open")),
                "high": as_float(raw.get("high")),
                "low": as_float(raw.get("low")),
                "close": as_float(raw.get("close")),
                "volume": as_float(raw.get("volume")),
                "bars": as_int(raw.get("bars")),
            })
    return sorted(rows, key=lambda row: row["date"])


def decorate_rows(rows: list[dict[str, Any]]) -> None:
    recent_volumes: list[float] = []
    previous_close: float | None = None
    for row in rows:
        volume = row.get("volume")
        avg_20 = mean(recent_volumes[-20:]) if recent_volumes else None
        row["volume_ratio_20d"] = round(volume / avg_20, 4) if (volume and avg_20) else None
        row["return_pct"] = (
            round(((row["close"] - previous_close) / previous_close) * 100, 4)
            if row.get("close") is not None and previous_close else None
        )
        row["range_pct"] = (
            round(((row["high"] - row["low"]) / row["close"]) * 100, 4)
            if row.get("high") and row.get("low") and row.get("close") else None
        )
        row["close_position"] = (
            round((row["close"] - row["low"]) / (row["high"] - row["low"]), 4)
            if row.get("high") is not None and row.get("low") is not None
            and row["high"] != row["low"] else None
        )
        apply_volume_labels(row)

        if volume:
            recent_volumes.append(float(volume))
        if row.get("close") is not None:
            previous_close = row["close"]


def apply_volume_labels(row: dict[str, Any]) -> None:
    vratio = row.get("volume_ratio_20d")
    ret = row.get("return_pct")
    close_pos = row.get("close_position")
    range_pct = row.get("range_pct")

    def flag(cond: bool) -> int:
        return 1 if cond else 0

    row["volume_spike"] = flag(vratio is not None and vratio >= VOLUME_SPIKE_RATIO)
    row["volume_drought"] = flag(vratio is not None and vratio <= VOLUME_DROUGHT_RATIO)
    row["high_volume_up"] = flag(
        vratio is not None and vratio >= HIGH_VOLUME_RATIO
        and ret is not None and ret > 0
    )
    row["high_volume_down"] = flag(
        vratio is not None and vratio >= HIGH_VOLUME_RATIO
        and ret is not None and ret < 0
    )
    row["failed_rally"] = flag(
        range_pct is not None and range_pct >= WIDE_RANGE_PCT
        and close_pos is not None and close_pos <= FAILED_RALLY_CLOSE_POSITION
        and vratio is not None and vratio >= 1.0
    )
    row["absorption_candle"] = flag(
        range_pct is not None and range_pct >= WIDE_RANGE_PCT
        and close_pos is not None and close_pos >= ABSORPTION_CLOSE_POSITION
        and vratio is not None and vratio >= 1.0
    )


def coverage_for(symbol: str, rows: list[dict[str, Any]]) -> dict[str, Any]:
    if not rows:
        return {
            "symbol": symbol,
            "days": 0,
            "first_date": None,
            "last_date": None,
            "total_volume": 0,
            "latest_close": None,
            "latest_labels": [],
        }
    first = rows[0]
    last = rows[-1]
    latest_labels = [label for label in VOLUME_LABELS if last.get(label) == 1]
    return {
        "symbol": symbol,
        "days": len(rows),
        "first_date": first["date"],
        "last_date": last["date"],
        "total_volume": int(sum((row.get("volume") or 0) for row in rows)),
        "latest_close": last.get("close"),
        "latest_labels": latest_labels,
    }


def label_counts(rows: list[dict[str, Any]]) -> dict[str, int]:
    return {label: sum(1 for row in rows if row.get(label) == 1) for label in VOLUME_LABELS}


def build_findings(summary: dict[str, Any], rows: list[dict[str, Any]]) -> str:
    lines = [
        "# Hydro Volume / Tape Lab Findings",
        "",
        "Clean experiment lane. Research only. Not wired to live prediction or persistence shadow.",
        "",
        "## Coverage",
        "",
        "| Symbol | Days | First | Last | Total volume | Latest close | Latest labels |",
        "|---|---:|---|---|---:|---:|---|",
    ]
    for item in summary["coverage"]:
        lines.append(
            f"| {item['symbol']} | {item['days']} | {item['first_date'] or 'n/a'} | "
            f"{item['last_date'] or 'n/a'} | {item['total_volume']:,} | "
            f"{item['latest_close'] if item['latest_close'] is not None else 'n/a'} | "
            f"{', '.join(item['latest_labels']) or 'none'} |"
        )

    lines.extend([
        "",
        "## Label Counts (across all loaded symbols)",
        "",
        "| Label | Count |",
        "|---|---:|",
    ])
    for label, count in summary["label_counts"].items():
        lines.append(f"| {label} | {count} |")

    missing = [item["symbol"] for item in summary["coverage"] if item["days"] == 0]
    if missing:
        lines.extend([
            "",
            "## Missing Raw Data",
            "",
            "The following symbols have no raw volume CSV under `raw/<SYMBOL>/`. "
            "Run `refresh_hydro_volumes.ps1` for them when live capture is available.",
            "",
        ])
        for symbol in missing:
            lines.append(f"- {symbol}")

    lines.extend([
        "",
        "## Notes",
        "",
        "- This lab looks only at volume/tape structure. It does not load broker-flow data (see experiment 07).",
        "- The cross-reference of volume labels against experiment 07 broker labels is the intended next step.",
    ])
    return "\n".join(lines) + "\n"


def build_focus_read(focus: str, rows: list[dict[str, Any]], coverage: list[dict[str, Any]]) -> str:
    focus_cov = next((item for item in coverage if item["symbol"] == focus), None)
    lines = [
        f"# {focus} Volume Read",
        "",
        "Research output. Not financial advice.",
        "",
    ]
    if not rows:
        lines.extend([
            f"No raw volume CSV found for {focus} at "
            f"`raw/{focus}/{focus.lower()}_volume_daily.csv`. "
            f"Run `refresh_hydro_volumes.ps1 -Symbol {focus}` when live capture is available.",
        ])
        return "\n".join(lines) + "\n"

    lines.extend([
        f"- Coverage: {focus_cov['days']} days from {focus_cov['first_date']} to {focus_cov['last_date']}",
        f"- Latest close: {focus_cov['latest_close']}",
        f"- Latest labels: {', '.join(focus_cov['latest_labels']) or 'none'}",
        "",
        "## Recent Tape (last 15 sessions)",
        "",
        "| Date | Close | Return | Range% | Close pos | Vol ratio | Labels |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in rows[-15:]:
        labels = [label for label in VOLUME_LABELS if row.get(label) == 1]
        lines.append(
            f"| {row['date']} | {fmt(row.get('close'))} | {fmt(row.get('return_pct'))}% | "
            f"{fmt(row.get('range_pct'))} | {fmt(row.get('close_position'))} | "
            f"{fmt(row.get('volume_ratio_20d'))} | {', '.join(labels) or 'none'} |"
        )

    spike_rows = [row for row in rows if row.get("volume_spike") == 1]
    lines.extend([
        "",
        f"## Volume Spike Days (>= {VOLUME_SPIKE_RATIO}x 20-day avg)",
        "",
    ])
    if not spike_rows:
        lines.append("- none")
    else:
        lines.extend([
            "| Date | Close | Return | Vol ratio | Direction |",
            "|---|---:|---:|---:|---|",
        ])
        for row in spike_rows[-10:]:
            direction = "UP" if (row.get("return_pct") or 0) > 0 else "DOWN"
            lines.append(
                f"| {row['date']} | {fmt(row.get('close'))} | {fmt(row.get('return_pct'))}% | "
                f"{fmt(row.get('volume_ratio_20d'))} | {direction} |"
            )

    lines.extend([
        "",
        "## Caveats",
        "",
        "- This read does not incorporate broker-flow evidence (experiment 07).",
        "- Minute/hourly microstructure is available in the raw JSON but not parsed here yet.",
        "- Thresholds are fixed by config. Tune them in code, re-run, and version the change.",
    ])
    return "\n".join(lines) + "\n"


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def as_int(value: Any) -> int | None:
    number = as_float(value)
    return int(number) if number is not None else None


def fmt(value: Any) -> str:
    if value is None or value == "":
        return "n/a"
    if isinstance(value, float):
        return f"{value:.4f}"
    return str(value)


if __name__ == "__main__":
    raise SystemExit(main())
