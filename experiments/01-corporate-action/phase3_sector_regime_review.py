from __future__ import annotations

import argparse
import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from stats import describe_returns  # noqa: E402


RESULTS_DIR = SCRIPT_DIR / "results"
SHORTLIST_PATH = RESULTS_DIR / "phase2_shortlist.csv"
RETURNS_PATH = RESULTS_DIR / "event_returns.csv"

SIGNAL_COLS = ["event_type", "date_field", "window_label"]


def main() -> None:
    args = parse_args()
    shortlist_path = Path(args.shortlist_path)
    returns_path = Path(args.returns_path)

    if not shortlist_path.exists():
        raise FileNotFoundError(f"Missing shortlist file: {shortlist_path}")
    if not returns_path.exists():
        raise FileNotFoundError(f"Missing event returns file: {returns_path}")

    shortlist = pd.read_csv(shortlist_path)
    returns = pd.read_csv(returns_path)

    filtered = returns.merge(shortlist[SIGNAL_COLS], on=SIGNAL_COLS, how="inner")
    filtered = filtered.dropna(subset=["excess_return_pct"]).copy()
    filtered["signal_key"] = filtered.apply(
        lambda row: f"{row['event_type']} | {row['date_field']} | {row['window_label']}",
        axis=1,
    )

    sector_summary = summarize_groups(filtered, SIGNAL_COLS + ["sector"])
    regime_summary = summarize_groups(filtered[filtered["market_regime"] != "unknown"], SIGNAL_COLS + ["market_regime"])
    sector_regime_summary = summarize_groups(
        filtered[filtered["market_regime"] != "unknown"],
        SIGNAL_COLS + ["sector", "market_regime"],
    )

    sector_summary = sector_summary[sector_summary["count"] >= args.min_sector_count].reset_index(drop=True)
    regime_summary = regime_summary[regime_summary["count"] >= args.min_regime_count].reset_index(drop=True)
    sector_regime_summary = sector_regime_summary[sector_regime_summary["count"] >= args.min_sector_regime_count].reset_index(drop=True)

    sector_path = RESULTS_DIR / "phase3_sector_summary.csv"
    regime_path = RESULTS_DIR / "phase3_regime_summary.csv"
    sector_regime_path = RESULTS_DIR / "phase3_sector_regime_summary.csv"
    review_path = RESULTS_DIR / "phase3_review.md"

    sector_summary.to_csv(sector_path, index=False)
    regime_summary.to_csv(regime_path, index=False)
    sector_regime_summary.to_csv(sector_regime_path, index=False)
    review_path.write_text(
        build_review_markdown(
            shortlist=shortlist,
            sector_summary=sector_summary,
            regime_summary=regime_summary,
            sector_regime_summary=sector_regime_summary,
            min_sector_count=args.min_sector_count,
            min_regime_count=args.min_regime_count,
            min_sector_regime_count=args.min_sector_regime_count,
        ),
        encoding="utf-8",
    )

    print(f"Wrote sector summary to {sector_path}")
    print(f"Wrote regime summary to {regime_path}")
    print(f"Wrote sector+regime summary to {sector_regime_path}")
    print(f"Wrote phase-3 review to {review_path}")


def summarize_groups(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for keys, group in frame.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {column: value for column, value in zip(group_cols, keys)}
        raw_negative = describe_returns(group["return_pct"], positive=False)
        excess_positive = describe_returns(group["excess_return_pct"], positive=True)
        excess_negative = describe_returns(group["excess_return_pct"], positive=False)

        best_direction = "positive"
        best_hit_rate = excess_positive["hit_rate"]
        if (excess_negative["hit_rate"] or 0.0) > (excess_positive["hit_rate"] or 0.0):
            best_direction = "negative"
            best_hit_rate = excess_negative["hit_rate"]

        row.update(
            {
                "count": int(len(group)),
                "symbol_count": int(group["symbol"].nunique()),
                "mean_event_return": group["return_pct"].mean(),
                "mean_baseline_return": group["baseline_mean_return"].mean(),
                "mean_excess_return": group["excess_return_pct"].mean(),
                "median_excess_return": group["excess_return_pct"].median(),
                "raw_negative_hit_rate": raw_negative["hit_rate"],
                "baseline_negative_hit_rate": group["baseline_negative_hit_rate"].mean(),
                "excess_positive_hit_rate": excess_positive["hit_rate"],
                "excess_negative_hit_rate": excess_negative["hit_rate"],
                "best_adjusted_direction": best_direction,
                "best_adjusted_hit_rate": best_hit_rate,
                "t_stat_excess": excess_positive["t_stat"],
                "p_value_excess": excess_positive["p_value"],
            }
        )
        rows.append(row)

    return pd.DataFrame(rows).sort_values(
        ["count", "best_adjusted_hit_rate", "mean_excess_return"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_review_markdown(
    shortlist: pd.DataFrame,
    sector_summary: pd.DataFrame,
    regime_summary: pd.DataFrame,
    sector_regime_summary: pd.DataFrame,
    min_sector_count: int,
    min_regime_count: int,
    min_sector_regime_count: int,
) -> str:
    lines = [
        "# Phase 3 Corporate Review",
        "",
        "This pass tests the phase-2 survivors by sector and by broad market regime.",
        "",
        f"- Sector rows require at least `{min_sector_count}` baseline-adjusted cases.",
        f"- Regime rows require at least `{min_regime_count}` baseline-adjusted cases.",
        f"- Sector+regime rows require at least `{min_sector_regime_count}` baseline-adjusted cases.",
        "",
    ]

    for signal in shortlist.to_dict("records"):
        signal_filter = (
            (sector_summary["event_type"] == signal["event_type"])
            & (sector_summary["date_field"] == signal["date_field"])
            & (sector_summary["window_label"] == signal["window_label"])
        )
        sector_rows = sector_summary[signal_filter].copy()

        regime_filter = (
            (regime_summary["event_type"] == signal["event_type"])
            & (regime_summary["date_field"] == signal["date_field"])
            & (regime_summary["window_label"] == signal["window_label"])
        )
        regime_rows = regime_summary[regime_filter].copy()

        combo_filter = (
            (sector_regime_summary["event_type"] == signal["event_type"])
            & (sector_regime_summary["date_field"] == signal["date_field"])
            & (sector_regime_summary["window_label"] == signal["window_label"])
        )
        combo_rows = sector_regime_summary[combo_filter].copy()

        lines.extend(
            [
                f"## {signal['event_type']} | {signal['date_field']} | {signal['window_label']}",
                "",
                f"Phase-2 winner: `{signal['best_adjusted_direction']}` with adjusted hit rate `{signal['best_adjusted_hit_rate']:.1%}` over `{int(signal['count'])}` cases.",
                "",
                verdict_line(signal, sector_rows, regime_rows),
                "",
                "### Sector Split",
                "",
                table_or_empty(
                    sector_rows,
                    columns=[
                        "sector",
                        "count",
                        "mean_excess_return",
                        "best_adjusted_direction",
                        "best_adjusted_hit_rate",
                        "p_value_excess",
                    ],
                ),
                "",
                "### Regime Split",
                "",
                table_or_empty(
                    regime_rows,
                    columns=[
                        "market_regime",
                        "count",
                        "mean_excess_return",
                        "best_adjusted_direction",
                        "best_adjusted_hit_rate",
                        "p_value_excess",
                    ],
                ),
                "",
                "### Sector + Regime",
                "",
                table_or_empty(
                    combo_rows,
                    columns=[
                        "sector",
                        "market_regime",
                        "count",
                        "mean_excess_return",
                        "best_adjusted_direction",
                        "best_adjusted_hit_rate",
                        "p_value_excess",
                    ],
                ),
                "",
            ]
        )

    return "\n".join(lines)


def verdict_line(signal: dict, sector_rows: pd.DataFrame, regime_rows: pd.DataFrame) -> str:
    banks = best_row_for(sector_rows, "sector", "Commercial Bank")
    hydro = best_row_for(sector_rows, "sector", "Hydropower")
    below = best_row_for(regime_rows, "market_regime", "below_sma200")
    above = best_row_for(regime_rows, "market_regime", "above_sma200")

    sector_verdict = "sector evidence unclear"
    if is_supported(banks) and is_supported(hydro) and banks["best_adjusted_direction"] == hydro["best_adjusted_direction"]:
        sector_verdict = f"cross-sector between banks and hydropower ({banks['best_adjusted_direction']})"
    elif is_supported(banks) and not is_supported(hydro):
        sector_verdict = "bank-led; hydropower not confirmed"
    elif is_supported(hydro) and not is_supported(banks):
        sector_verdict = "hydropower-led; banks not confirmed"

    regime_verdict = "regime evidence unclear"
    if is_supported(below) and not is_supported(above):
        regime_verdict = "mostly below-SMA200 / weak-market dependent"
    elif is_supported(below) and is_supported(above) and below["best_adjusted_direction"] == above["best_adjusted_direction"]:
        regime_verdict = f"present in both regimes ({below['best_adjusted_direction']})"
    elif is_supported(above) and not is_supported(below):
        regime_verdict = "mostly above-SMA200 dependent"

    return f"Verdict: {sector_verdict}; {regime_verdict}."


def best_row_for(frame: pd.DataFrame, column: str, value: str) -> dict | None:
    if frame.empty:
        return None
    subset = frame[frame[column] == value]
    if subset.empty:
        return None
    return subset.sort_values(["best_adjusted_hit_rate", "count"], ascending=[False, False]).iloc[0].to_dict()


def is_supported(row: dict | None) -> bool:
    if not row:
        return False
    hit_rate = row.get("best_adjusted_hit_rate")
    p_value = row.get("p_value_excess")
    count = row.get("count", 0)
    if hit_rate is None or p_value is None:
        return False
    return count >= 20 and hit_rate >= 0.60 and p_value <= 0.05


def table_or_empty(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows met the minimum count._"

    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    rows = [header, separator]
    for row in frame[columns].to_dict("records"):
        rendered = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float):
                if column.endswith("hit_rate"):
                    rendered.append(f"{value:.1%}")
                elif column == "p_value_excess":
                    rendered.append(f"{value:.4f}")
                else:
                    rendered.append(f"{value:.2f}")
            else:
                rendered.append(str(value))
        rows.append("| " + " | ".join(rendered) + " |")
    return "\n".join(rows)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate corporate-action survivors by sector and regime.")
    parser.add_argument(
        "--shortlist-path",
        default=str(SHORTLIST_PATH),
        help="Path to the phase-2 shortlist CSV.",
    )
    parser.add_argument(
        "--returns-path",
        default=str(RETURNS_PATH),
        help="Path to the event-level returns CSV.",
    )
    parser.add_argument("--min-sector-count", type=int, default=15, help="Minimum cases for sector rows.")
    parser.add_argument("--min-regime-count", type=int, default=15, help="Minimum cases for regime rows.")
    parser.add_argument(
        "--min-sector-regime-count",
        type=int,
        default=10,
        help="Minimum cases for sector+regime rows.",
    )
    return parser.parse_args()


if __name__ == "__main__":
    main()
