"""
Research-only study of July 2025 commercial-bank leadership trajectory.

Usage:
    python july_2025_bank_leadership_trajectory_study.py
"""
import json
import os
import sys
from collections import Counter, defaultdict
from datetime import datetime
from statistics import mean

from config import VALIDATION_DIR
from replay_after_close_label_drift_study import LATEST_TRADABILITY_STUDY_PATH, load_json, save_json, save_text


LEARNING_REVIEWS_DIR = os.path.join(VALIDATION_DIR, "learning_reviews")


def _rank_desc(values_by_symbol):
    ranked = sorted(
        [(symbol, value) for symbol, value in values_by_symbol.items() if value is not None],
        key=lambda item: item[1],
        reverse=True,
    )
    return {symbol: index + 1 for index, (symbol, _value) in enumerate(ranked)}


def _phase_name(session_date):
    return "early_july" if str(session_date) <= "2025-07-10" else "late_july"


def _mean(rows, key):
    values = [row.get(key) for row in rows if row.get(key) is not None]
    return round(mean(values), 4) if values else None


def _render_markdown(summary):
    lines = [
        "# July 2025 Bank Leadership Trajectory Study",
        "",
        f"- built_at: `{summary['built_at']}`",
        f"- source_path: `{summary['source_path']}`",
        "",
        "## Short Answer",
        "",
        "This study checks whether SANIMA behaved like the strongest early-July bank leader and whether that leadership later turned into exhaustion.",
        "",
    ]

    for phase in summary.get("phase_summaries", []):
        lines.extend([
            f"## Phase `{phase['phase_name']}`",
            "",
            f"- case_count: `{phase['case_count']}`",
            f"- label_counts: `{phase['label_counts']}`",
            "",
        ])
        for symbol_summary in phase.get("symbols", []):
            lines.extend([
                f"### `{symbol_summary['symbol']}`",
                "",
                f"- case_count: `{symbol_summary['case_count']}`",
                f"- label_counts: `{symbol_summary['label_counts']}`",
                f"- verdict_counts: `{symbol_summary['verdict_counts']}`",
                f"- avg_return_5d_pct: `{symbol_summary['avg_return_5d_pct']}`",
                f"- avg_return_20d_pct: `{symbol_summary['avg_return_20d_pct']}`",
                f"- avg_volume_ratio_5d: `{symbol_summary['avg_volume_ratio_5d']}`",
                f"- avg_close_position_20d: `{symbol_summary['avg_close_position_20d']}`",
                f"- avg_target_distance_close_pct: `{symbol_summary['avg_target_distance_close_pct']}`",
                f"- avg_next_open_gap_pct: `{symbol_summary['avg_next_open_gap_pct']}`",
                f"- avg_return_5d_rank: `{symbol_summary['avg_return_5d_rank']}`",
                f"- avg_volume_ratio_rank: `{symbol_summary['avg_volume_ratio_rank']}`",
                f"- avg_close_position_rank: `{symbol_summary['avg_close_position_rank']}`",
                "",
            ])

    lines.extend(["## Per-Date Leadership Table", ""])
    for row in summary.get("date_rows", []):
        lines.append(
            f"- `{row['session_date']}`: leader_5d `{row['leader_return_5d_symbol']}`, "
            f"leader_volume `{row['leader_volume_symbol']}`, "
            f"leader_close_position `{row['leader_close_position_symbol']}`, "
            f"labels `{row['symbol_labels']}`"
        )
    return "\n".join(lines) + "\n"


def build_july_2025_bank_leadership_trajectory_study():
    payload = load_json(LATEST_TRADABILITY_STUDY_PATH)
    records = [
        record for record in (payload.get("records") or [])
        if record.get("sector_name") == "COMMERCIAL BANKS"
        and str(record.get("session_date") or "").startswith("2025-07")
    ]

    grouped_by_date = defaultdict(list)
    for record in records:
        grouped_by_date[record["session_date"]].append(record)

    date_rows = []
    enriched_records = []
    for session_date, items in sorted(grouped_by_date.items()):
        rank_return_5d = _rank_desc({item["symbol"]: item.get("return_5d_pct") for item in items})
        rank_volume = _rank_desc({item["symbol"]: item.get("volume_ratio_5d") for item in items})
        rank_close_position = _rank_desc({item["symbol"]: item.get("close_position_20d") for item in items})

        leader_return_5d_symbol = min(rank_return_5d, key=rank_return_5d.get) if rank_return_5d else None
        leader_volume_symbol = min(rank_volume, key=rank_volume.get) if rank_volume else None
        leader_close_position_symbol = min(rank_close_position, key=rank_close_position.get) if rank_close_position else None

        date_rows.append({
            "session_date": session_date,
            "phase_name": _phase_name(session_date),
            "leader_return_5d_symbol": leader_return_5d_symbol,
            "leader_volume_symbol": leader_volume_symbol,
            "leader_close_position_symbol": leader_close_position_symbol,
            "symbol_labels": {
                item["symbol"]: item.get("next_open_label") for item in sorted(items, key=lambda row: row["symbol"])
            },
        })

        for item in items:
            enriched_records.append({
                **item,
                "phase_name": _phase_name(session_date),
                "return_5d_rank": rank_return_5d.get(item["symbol"]),
                "volume_ratio_rank": rank_volume.get(item["symbol"]),
                "close_position_rank": rank_close_position.get(item["symbol"]),
            })

    phase_summaries = []
    for phase_name in ("early_july", "late_july"):
        phase_records = [record for record in enriched_records if record["phase_name"] == phase_name]
        symbol_rows = []
        for symbol in sorted(set(record["symbol"] for record in phase_records)):
            symbol_records = [record for record in phase_records if record["symbol"] == symbol]
            symbol_rows.append({
                "symbol": symbol,
                "case_count": len(symbol_records),
                "label_counts": dict(Counter(record.get("next_open_label") for record in symbol_records)),
                "verdict_counts": dict(Counter(record.get("comparison_verdict") for record in symbol_records)),
                "avg_return_5d_pct": _mean(symbol_records, "return_5d_pct"),
                "avg_return_20d_pct": _mean(symbol_records, "return_20d_pct"),
                "avg_volume_ratio_5d": _mean(symbol_records, "volume_ratio_5d"),
                "avg_close_position_20d": _mean(symbol_records, "close_position_20d"),
                "avg_target_distance_close_pct": _mean(symbol_records, "target_distance_close_pct"),
                "avg_next_open_gap_pct": _mean(symbol_records, "next_open_gap_pct"),
                "avg_return_5d_rank": _mean(symbol_records, "return_5d_rank"),
                "avg_volume_ratio_rank": _mean(symbol_records, "volume_ratio_rank"),
                "avg_close_position_rank": _mean(symbol_records, "close_position_rank"),
            })
        phase_summaries.append({
            "phase_name": phase_name,
            "case_count": len(phase_records),
            "label_counts": dict(Counter(record.get("next_open_label") for record in phase_records)),
            "symbols": symbol_rows,
        })

    summary = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "source_path": LATEST_TRADABILITY_STUDY_PATH,
        "phase_summaries": phase_summaries,
        "date_rows": date_rows,
    }

    dated_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        f"{datetime.now().strftime('%Y-%m-%d')}__july_2025_bank_leadership_trajectory_study_v1.json",
    )
    latest_json_path = os.path.join(
        LEARNING_REVIEWS_DIR,
        "latest__july_2025_bank_leadership_trajectory_study_v1.json",
    )
    dated_md_path = dated_json_path.replace(".json", ".md")
    latest_md_path = latest_json_path.replace(".json", ".md")
    markdown = _render_markdown(summary)
    save_json(dated_json_path, summary)
    save_json(latest_json_path, summary)
    save_text(dated_md_path, markdown)
    save_text(latest_md_path, markdown)
    return summary, latest_json_path, latest_md_path


def main():
    if len(sys.argv) > 1:
        print("This study takes no positional arguments.")
        sys.exit(1)

    summary, latest_json_path, latest_md_path = build_july_2025_bank_leadership_trajectory_study()
    print(json.dumps({
        "phase_count": len(summary.get("phase_summaries") or []),
        "latest_json_path": latest_json_path,
        "latest_md_path": latest_md_path,
    }, indent=2))


if __name__ == "__main__":
    main()
