"""
Build rate-move event table from daily interbank data.

Flags days where the interbank rate moved significantly.
Tests multiple thresholds to find the right sensitivity.

Input: data/interbank_daily.csv
Output: data/rate_move_events.csv
"""
from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"


def main() -> None:
    args = parse_args()
    interbank_path = DATA_DIR / "interbank_daily.csv"
    if not interbank_path.exists():
        raise FileNotFoundError(
            f"Missing interbank data: {interbank_path}\n"
            "Run scrape_nrb_interbank.py first."
        )

    rates = pd.read_csv(interbank_path)
    rates = rates.dropna(subset=["rate_pct", "change_from_prev"]).copy()
    rates["abs_change"] = rates["change_from_prev"].abs()

    print(f"Loaded {len(rates)} interbank rate records")
    print(f"Change distribution:")
    print(f"  Mean abs change: {rates['abs_change'].mean():.4f}%")
    print(f"  Median abs change: {rates['abs_change'].median():.4f}%")
    print(f"  Max abs change: {rates['abs_change'].max():.4f}%")
    print()

    # Flag events at multiple thresholds
    thresholds = [float(t) for t in args.thresholds.split(",")]
    all_events = []

    for threshold in thresholds:
        large_moves = rates[rates["abs_change"] >= threshold].copy()
        large_moves["event_type"] = large_moves["change_from_prev"].apply(
            lambda x: "interbank_rate_spike" if x > 0 else "interbank_rate_drop"
        )
        large_moves["event_label"] = large_moves.apply(
            lambda r: f"Interbank rate {'rose' if r['change_from_prev'] > 0 else 'fell'} "
                      f"{abs(r['change_from_prev']):.3f}% to {r['rate_pct']:.3f}%",
            axis=1,
        )
        large_moves["threshold"] = threshold
        large_moves["event_date"] = large_moves["date"]
        large_moves["direction"] = large_moves["change_from_prev"].apply(
            lambda x: "tightening" if x > 0 else "easing"
        )
        all_events.append(large_moves)
        print(f"  Threshold >= {threshold}%: {len(large_moves)} events "
              f"({len(large_moves[large_moves['change_from_prev'] > 0])} spikes, "
              f"{len(large_moves[large_moves['change_from_prev'] < 0])} drops)")

    if not all_events:
        print("No rate-move events found at any threshold.")
        return

    events = pd.concat(all_events, ignore_index=True)
    events = events[[
        "event_date", "event_type", "event_label", "direction",
        "rate_pct", "change_from_prev", "threshold", "source_url",
    ]].sort_values(["threshold", "event_date"]).reset_index(drop=True)

    output_path = DATA_DIR / "rate_move_events.csv"
    events.to_csv(output_path, index=False)
    print(f"\nWrote {len(events)} rate-move events to {output_path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Build rate-move event table from interbank data.")
    parser.add_argument(
        "--thresholds",
        default="0.1,0.2,0.5",
        help="Comma-separated absolute change thresholds in percent. Default: 0.1,0.2,0.5",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
