"""
Build a replay-safe 2025 corporate action timeline from official backfill tables.

Usage:
    python backfill_corporate_actions_2025.py 2025 '@replay_basket_v1'
"""
import json
import os
import sys
from datetime import datetime

from config import VALIDATION_DIR, build_run_label, normalize_filename_token, resolve_symbols
from corporate_action_timeline import build_corporate_action_timeline
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
        "# Corporate Action Timeline Backfill",
        "",
        f"- year: `{payload['year']}`",
        f"- run_label: `{run_label}`",
        f"- built_at: `{payload['built_at']}`",
        f"- matched_record_count: `{payload['matched_record_count']}`",
        f"- unmatched_record_count: `{payload['unmatched_record_count']}`",
        f"- requested_symbol_match_count: `{payload.get('requested_symbol_match_count')}`",
        f"- match_universe_symbol_count: `{payload.get('match_universe_symbol_count')}`",
        f"- source_counts: `{payload['source_counts']}`",
        f"- enrichment_counts: `{payload.get('enrichment_counts')}`",
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
        lines.append("- no matched symbol-level records")
    else:
        for symbol, count in sorted(symbol_counts.items()):
            lines.append(f"- `{symbol}`: `{count}`")
    lines.extend([
        "",
        "## Requested Symbol Event Counts",
    ])
    requested_counts = payload.get("requested_symbol_event_counts") or {}
    if not requested_counts:
        lines.append("- no matched requested-symbol records")
    else:
        for symbol, count in sorted(requested_counts.items()):
            lines.append(f"- `{symbol}`: `{count}`")
    return "\n".join(lines) + "\n"


def main():
    if len(sys.argv) < 2:
        print("Usage: python backfill_corporate_actions_2025.py YEAR [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    year = int(sys.argv[1])
    symbol_args = sys.argv[2:] or ["@replay_basket_v1"]
    symbols = resolve_symbols(symbol_args)
    run_label = build_run_label(symbol_args, symbols)
    clean_label = normalize_filename_token(run_label)
    official_backfill_path = os.path.join(BACKFILL_DIR, f"latest__{year}__official_replay_context_backfill_v1.json")

    company_news_payload = build_nepse_company_news_backfill(year, symbols)
    company_news_base = f"{year}__{clean_label}__nepse_company_news_backfill_v1"
    save_json(os.path.join(BACKFILL_DIR, f"{company_news_base}.json"), company_news_payload)
    save_json(os.path.join(BACKFILL_DIR, f"latest__{company_news_base}.json"), company_news_payload)
    save_text(
        os.path.join(BACKFILL_DIR, f"{company_news_base}.md"),
        "\n".join([
            "# NEPSE Company News Backfill",
            "",
            f"- year: `{company_news_payload['year']}`",
            f"- run_label: `{run_label}`",
            f"- filtered_record_count: `{company_news_payload['filtered_record_count']}`",
            f"- event_type_counts: `{company_news_payload['event_type_counts']}`",
            "",
        ]) + "\n",
    )
    save_text(
        os.path.join(BACKFILL_DIR, f"latest__{company_news_base}.md"),
        "\n".join([
            "# NEPSE Company News Backfill",
            "",
            f"- year: `{company_news_payload['year']}`",
            f"- run_label: `{run_label}`",
            f"- filtered_record_count: `{company_news_payload['filtered_record_count']}`",
            f"- event_type_counts: `{company_news_payload['event_type_counts']}`",
            "",
        ]) + "\n",
    )

    payload = build_corporate_action_timeline(
        year,
        symbols,
        official_backfill_path,
        run_label_token=clean_label,
    )

    base = f"{year}__{clean_label}__corporate_action_timeline_v1"
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
        "matched_record_count": payload["matched_record_count"],
        "unmatched_record_count": payload["unmatched_record_count"],
        "notes": payload["notes"],
    }, indent=2))


if __name__ == "__main__":
    main()
