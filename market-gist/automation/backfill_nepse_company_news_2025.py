"""
Build a replay-safe 2025 NEPSE company-news backfill for a tracked list.

Usage:
    python backfill_nepse_company_news_2025.py 2025 '@replay_basket_v1'
"""
import json
import os
import sys

from config import VALIDATION_DIR, build_run_label, normalize_filename_token, resolve_symbols
from nepse_company_news_archive import build_nepse_company_news_backfill


BACKFILL_DIR = os.path.join(VALIDATION_DIR, "historical_context_backfills")


def save_json(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, indent=2)


def save_text(path, payload):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(payload)


def _build_markdown(payload, run_label):
    lines = [
        "# NEPSE Company News Backfill",
        "",
        f"- year: `{payload['year']}`",
        f"- run_label: `{run_label}`",
        f"- built_at: `{payload['built_at']}`",
        f"- raw_row_count: `{payload['raw_row_count']}`",
        f"- filtered_record_count: `{payload['filtered_record_count']}`",
        f"- skipped_irrelevant_count: `{payload['skipped_irrelevant_count']}`",
        f"- event_type_counts: `{payload['event_type_counts']}`",
        "",
        "## Notes",
    ]
    for note in payload.get("notes") or []:
        lines.append(f"- {note}")
    lines.extend([
        "",
        "## Symbol Event Counts",
    ])
    symbol_counts = payload.get("symbol_event_counts") or {}
    if not symbol_counts:
        lines.append("- no symbol-level records")
    else:
        for symbol, count in sorted(symbol_counts.items()):
            lines.append(f"- `{symbol}`: `{count}`")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python backfill_nepse_company_news_2025.py YEAR [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    year = int(sys.argv[1])
    symbol_args = sys.argv[2:] or ["@replay_basket_v1"]
    symbols = resolve_symbols(symbol_args)
    run_label = build_run_label(symbol_args, symbols)
    clean_label = normalize_filename_token(run_label)

    payload = build_nepse_company_news_backfill(year, symbols)

    base = f"{year}__{clean_label}__nepse_company_news_backfill_v1"
    dated_json = os.path.join(BACKFILL_DIR, f"{base}.json")
    latest_json = os.path.join(BACKFILL_DIR, f"latest__{base}.json")
    dated_md = os.path.join(BACKFILL_DIR, f"{base}.md")
    latest_md = os.path.join(BACKFILL_DIR, f"latest__{base}.md")
    markdown = _build_markdown(payload, run_label)

    save_json(dated_json, payload)
    save_json(latest_json, payload)
    save_text(dated_md, markdown)
    save_text(latest_md, markdown)

    print(json.dumps({
        "dated_json": os.path.abspath(dated_json),
        "latest_json": os.path.abspath(latest_json),
        "dated_md": os.path.abspath(dated_md),
        "latest_md": os.path.abspath(latest_md),
        "filtered_record_count": payload["filtered_record_count"],
        "event_type_counts": payload["event_type_counts"],
        "symbol_event_counts": payload["symbol_event_counts"],
        "notes": payload["notes"],
    }, indent=2))


if __name__ == "__main__":
    main()
