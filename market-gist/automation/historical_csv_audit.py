"""
Audit the local Sharesansar CSV archive for one historical year.

Usage:
    python historical_csv_audit.py 2025
    python historical_csv_audit.py 2025 @replay_basket_v1
"""
import csv
import json
import os
import statistics
import sys
from collections import Counter
from datetime import date, datetime, timedelta

from config import VALIDATION_DIR, resolve_symbols, load_symbol_lists
from data_sources.sharesansar_csv_source import DEFAULT_DATA_DIR


REQUIRED_COLUMNS = [
    "Symbol",
    "Open",
    "High",
    "Low",
    "Close",
    "VWAP",
    "Vol",
    "Prev. Close",
    "Turnover",
    "Trans.",
    "Diff %",
    "Range %",
    "120 Days",
    "180 Days",
    "52 Weeks High",
    "52 Weeks Low",
]


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def parse_filename_date(filename):
    stem = os.path.splitext(filename)[0]
    try:
        return datetime.strptime(stem, "%m_%d_%Y").date()
    except ValueError:
        return None


def is_nepal_trading_weekday(day):
    # Transition-aware; see nepse_trading_calendar. Pre-2026-04-10: Sun-Thu.
    # From 2026-04-10: Mon-Fri (Nepal switched to two-day weekend schedule).
    from nepse_trading_calendar import is_trading_weekday as _is_trading_weekday
    return _is_trading_weekday(day)


def daterange(start_day, end_day):
    current = start_day
    while current <= end_day:
        yield current
        current += timedelta(days=1)


def yearly_paths(year):
    audit_dir = os.path.join(VALIDATION_DIR, "historical_data_audits")
    base_name = f"{year}__sharesansar_local__archive_audit_v1"
    return {
        "json": os.path.join(audit_dir, f"{base_name}.json"),
        "latest_json": os.path.join(audit_dir, f"latest__{base_name}.json"),
        "md": os.path.join(audit_dir, f"{base_name}.md"),
        "latest_md": os.path.join(audit_dir, f"latest__{base_name}.md"),
    }


def _row_stat(values):
    if not values:
        return {"min": None, "max": None, "avg": None}
    return {
        "min": min(values),
        "max": max(values),
        "avg": round(statistics.mean(values), 2),
    }


def load_year_files(year, data_dir):
    files = []
    for filename in sorted(os.listdir(data_dir)):
        if not filename.lower().endswith(".csv"):
            continue
        business_date = parse_filename_date(filename)
        if not business_date or business_date.year != year:
            continue
        files.append({
            "filename": filename,
            "business_date": business_date,
            "path": os.path.join(data_dir, filename),
        })
    return files


def audit_file(file_info, tracked_symbols):
    with open(file_info["path"], "r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        fieldnames = reader.fieldnames or []
        rows = list(reader)

    symbols = [str(row.get("Symbol", "")).strip().upper() for row in rows]
    non_blank_symbols = [symbol for symbol in symbols if symbol]
    duplicates = [symbol for symbol, count in Counter(non_blank_symbols).items() if count > 1]
    missing_columns = [column for column in REQUIRED_COLUMNS if column not in fieldnames]
    tracked_missing = [symbol for symbol in tracked_symbols if symbol not in non_blank_symbols]

    return {
        "business_date": file_info["business_date"].isoformat(),
        "filename": file_info["filename"],
        "weekday_name": file_info["business_date"].strftime("%A"),
        "is_nepal_trading_weekday": is_nepal_trading_weekday(file_info["business_date"]),
        "row_count": len(rows),
        "unique_symbol_count": len(set(non_blank_symbols)),
        "blank_symbol_count": sum(1 for symbol in symbols if not symbol),
        "duplicate_symbol_count": len(duplicates),
        "duplicate_symbols_sample": duplicates[:10],
        "missing_required_columns": missing_columns,
        "tracked_symbols_missing": tracked_missing,
        "tracked_symbols_present_count": len(tracked_symbols) - len(tracked_missing),
        "tracked_symbols_total": len(tracked_symbols),
    }


def build_summary(year, file_audits, tracked_symbols, data_dir):
    file_dates = [datetime.strptime(item["business_date"], "%Y-%m-%d").date() for item in file_audits]
    if not file_dates:
        raise RuntimeError(f"No CSV files found for {year} in {data_dir}")

    weekday_files = [item for item in file_audits if item["is_nepal_trading_weekday"]]
    weekend_files = [item for item in file_audits if not item["is_nepal_trading_weekday"]]
    weekday_date_set = {datetime.strptime(item["business_date"], "%Y-%m-%d").date() for item in weekday_files}
    weekday_gaps = [
        day.isoformat()
        for day in daterange(min(file_dates), max(file_dates))
        if day.year == year and is_nepal_trading_weekday(day) and day not in weekday_date_set
    ]

    schema_issue_files = [item for item in file_audits if item["missing_required_columns"]]
    duplicate_issue_files = [item for item in file_audits if item["duplicate_symbol_count"] > 0]
    blank_symbol_files = [item for item in file_audits if item["blank_symbol_count"] > 0]
    tracked_gap_files = [item for item in file_audits if item["tracked_symbols_missing"]]

    tracked_missing_counter = Counter()
    for item in tracked_gap_files:
        tracked_missing_counter.update(item["tracked_symbols_missing"])

    monthly_counts = Counter(item["business_date"][:7] for item in file_audits)
    row_counts = [item["row_count"] for item in file_audits]
    unique_symbol_counts = [item["unique_symbol_count"] for item in file_audits]

    confidence = "high"
    warnings = []
    if schema_issue_files:
        confidence = "medium"
        warnings.append("some files are missing required columns")
    if duplicate_issue_files:
        confidence = "medium"
        warnings.append("some files contain duplicate symbols")
    if blank_symbol_files:
        confidence = "medium"
        warnings.append("some files contain blank symbol rows")
    if weekday_gaps:
        warnings.append("weekday gaps exist and should be treated as unverified until holiday calendars are checked")

    return {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "year": year,
        "data_dir": os.path.abspath(data_dir),
        "tracked_symbols": tracked_symbols,
        "summary": {
            "total_csv_files": len(file_audits),
            "weekday_file_count": len(weekday_files),
            "weekend_file_count": len(weekend_files),
            "start_date": min(file_dates).isoformat(),
            "end_date": max(file_dates).isoformat(),
            "weekday_gap_count_unverified": len(weekday_gaps),
            "schema_issue_file_count": len(schema_issue_files),
            "duplicate_issue_file_count": len(duplicate_issue_files),
            "blank_symbol_file_count": len(blank_symbol_files),
            "tracked_gap_file_count": len(tracked_gap_files),
            "row_count_stats": _row_stat(row_counts),
            "unique_symbol_count_stats": _row_stat(unique_symbol_counts),
            "archive_confidence": confidence,
            "warnings": warnings,
        },
        "monthly_file_counts": dict(sorted(monthly_counts.items())),
        "weekend_files_sample": [item["business_date"] for item in weekend_files[:25]],
        "weekday_gaps_unverified_sample": weekday_gaps[:50],
        "schema_issue_files": [
            {
                "business_date": item["business_date"],
                "missing_required_columns": item["missing_required_columns"],
            }
            for item in schema_issue_files[:50]
        ],
        "duplicate_issue_files": [
            {
                "business_date": item["business_date"],
                "duplicate_symbol_count": item["duplicate_symbol_count"],
                "duplicate_symbols_sample": item["duplicate_symbols_sample"],
            }
            for item in duplicate_issue_files[:50]
        ],
        "blank_symbol_files": [
            {
                "business_date": item["business_date"],
                "blank_symbol_count": item["blank_symbol_count"],
            }
            for item in blank_symbol_files[:50]
        ],
        "tracked_symbol_missing_frequency": tracked_missing_counter.most_common(),
        "tracked_symbol_gap_files": [
            {
                "business_date": item["business_date"],
                "missing_symbols": item["tracked_symbols_missing"],
            }
            for item in tracked_gap_files[:100]
        ],
        "per_file_audits": file_audits,
    }


def build_markdown(summary):
    top_missing = summary.get("tracked_symbol_missing_frequency") or []
    warnings = summary["summary"].get("warnings") or []
    lines = [
        "# Historical CSV Audit",
        "",
        f"- year: `{summary['year']}`",
        f"- data dir: `{summary['data_dir']}`",
        f"- tracked symbols: `{', '.join(summary['tracked_symbols']) if summary['tracked_symbols'] else 'none'}`",
        f"- total csv files: `{summary['summary']['total_csv_files']}`",
        f"- weekday files: `{summary['summary']['weekday_file_count']}`",
        f"- weekend files: `{summary['summary']['weekend_file_count']}`",
        f"- start date: `{summary['summary']['start_date']}`",
        f"- end date: `{summary['summary']['end_date']}`",
        f"- row count avg: `{summary['summary']['row_count_stats']['avg']}`",
        f"- unique symbol avg: `{summary['summary']['unique_symbol_count_stats']['avg']}`",
        f"- archive confidence: `{summary['summary']['archive_confidence']}`",
        "",
        "## Warnings",
        "",
    ]
    if warnings:
        lines.extend(f"- {warning}" for warning in warnings)
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Top Tracked Symbol Gaps",
        "",
    ])
    if top_missing:
        lines.extend(f"- `{symbol}` missing on `{count}` files" for symbol, count in top_missing[:15])
    else:
        lines.append("- none")

    lines.extend([
        "",
        "## Key Interpretation",
        "",
        "- weekend files are expected from this archive and should not be treated as Nepal trading sessions",
        "- weekday gaps are only 'unverified' gaps until checked against a holiday calendar",
        "- this audit is for historical replay trust, not live market correctness",
        "",
    ])
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python historical_csv_audit.py YEAR [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    year = int(sys.argv[1])
    symbol_args = sys.argv[2:]
    if symbol_args:
        tracked_symbols = resolve_symbols(symbol_args)
    else:
        symbol_lists = load_symbol_lists()
        tracked_symbols = symbol_lists.get("replay_basket_v1", [])

    files = load_year_files(year, DEFAULT_DATA_DIR)
    file_audits = [audit_file(file_info, tracked_symbols) for file_info in files]
    summary = build_summary(year, file_audits, tracked_symbols, DEFAULT_DATA_DIR)
    markdown = build_markdown(summary)
    paths = yearly_paths(year)

    save_json(paths["json"], summary)
    save_json(paths["latest_json"], summary)
    save_text(paths["md"], markdown)
    save_text(paths["latest_md"], markdown)

    result = {
        "saved_json": os.path.abspath(paths["json"]),
        "saved_latest_json": os.path.abspath(paths["latest_json"]),
        "saved_md": os.path.abspath(paths["md"]),
        "saved_latest_md": os.path.abspath(paths["latest_md"]),
        "summary": summary["summary"],
    }
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
