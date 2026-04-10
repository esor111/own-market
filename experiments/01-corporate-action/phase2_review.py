from __future__ import annotations

import argparse
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"

EVENT_FAMILY = {
    "agm_notice": "agm",
    "agm": "agm",
    "agm_minutes": "agm",
    "book_closure_notice": "book_closure",
    "right_share_notice": "right_share",
    "right_share": "right_share",
    "right_share_listing_notice": "right_share_listing",
    "dividend_notice": "dividend_notice",
    "cash_dividend_notice": "cash_dividend",
    "cash_dividend": "cash_dividend",
    "bonus_share_notice": "bonus_share",
    "bonus_share": "bonus_share",
    "bonus_and_cash_dividend": "bonus_and_cash_dividend",
    "bonus_listing_notice": "bonus_listing",
}

EVENT_PRIORITY = {
    "agm_notice": 1,
    "agm": 2,
    "agm_minutes": 3,
    "book_closure_notice": 1,
    "right_share_notice": 1,
    "right_share": 2,
    "right_share_listing_notice": 1,
    "dividend_notice": 1,
    "cash_dividend_notice": 1,
    "cash_dividend": 2,
    "bonus_share_notice": 1,
    "bonus_share": 2,
    "bonus_and_cash_dividend": 1,
    "bonus_listing_notice": 1,
}

STAGE_LABELS = {
    "announcement_date": "announcement",
    "approval_date": "approval",
    "book_close_date": "book_close",
    "listing_date": "listing",
}

WINDOW_PRIORITY = {
    "drift_2_10": 1,
    "reaction_0_1": 2,
    "pre_-10_-1": 3,
}


def main() -> None:
    args = parse_args()
    summary_path = Path(args.summary_path) if args.summary_path else RESULTS_DIR / "baseline_summary.csv"
    events_path = DATA_DIR / "events.csv"
    if not summary_path.exists():
        raise FileNotFoundError(f"Missing summary file: {summary_path}")
    if not events_path.exists():
        raise FileNotFoundError(f"Missing events file: {events_path}")

    summary = pd.read_csv(summary_path)
    events = pd.read_csv(events_path)

    prepared = prepare_summary(summary, events)
    shortlist, dropped = build_shortlist(
        prepared,
        min_count=args.min_count,
        min_hit_rate=args.min_hit_rate,
        max_p_value=args.max_p_value,
    )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    shortlist_path = RESULTS_DIR / "phase2_shortlist.csv"
    dropped_path = RESULTS_DIR / "phase2_dropped.csv"
    review_path = RESULTS_DIR / "phase2_review.md"

    shortlist.to_csv(shortlist_path, index=False)
    dropped.to_csv(dropped_path, index=False)
    review_path.write_text(build_review_markdown(shortlist, dropped), encoding="utf-8")

    print(f"Wrote shortlist to {shortlist_path}")
    print(f"Wrote dropped groups to {dropped_path}")
    print(f"Wrote review note to {review_path}")


def prepare_summary(summary: pd.DataFrame, events: pd.DataFrame) -> pd.DataFrame:
    event_source = (
        events.groupby(["event_type", "source_table"])
        .size()
        .reset_index(name="source_rows")
        .sort_values(["event_type", "source_rows"], ascending=[True, False])
        .drop_duplicates(subset=["event_type"])
        .rename(columns={"source_table": "primary_source_table"})
        [["event_type", "primary_source_table"]]
    )

    frame = summary.merge(event_source, on="event_type", how="left")
    frame = normalize_review_columns(frame)
    frame["family"] = frame["event_type"].map(EVENT_FAMILY).fillna(frame["event_type"])
    frame["stage"] = frame["date_field"].map(STAGE_LABELS).fillna(frame["date_field"])
    frame["event_priority"] = frame["event_type"].map(EVENT_PRIORITY).fillna(99)
    frame["window_priority"] = frame["window_label"].map(WINDOW_PRIORITY).fillna(99)
    frame["signal_strength"] = (frame["review_hit_rate"] - 0.5).abs()
    frame["signal_score"] = frame["signal_strength"] * frame["count"].pow(0.5)
    return frame


def normalize_review_columns(frame: pd.DataFrame) -> pd.DataFrame:
    result = frame.copy()
    if "best_adjusted_hit_rate" in result.columns:
        result["review_mode"] = "baseline_adjusted"
        result["review_direction"] = result["best_adjusted_direction"]
        result["review_hit_rate"] = result["best_adjusted_hit_rate"]
        result["review_p_value"] = result["p_value_excess"]
        result["review_mean_return"] = result["mean_event_return"]
        result["review_context_mean"] = result["mean_baseline_return"]
        result["review_excess_mean"] = result["mean_excess_return"]
    else:
        result["review_mode"] = "raw"
        result["review_direction"] = result["best_direction"]
        result["review_hit_rate"] = result["best_directional_hit_rate"]
        result["review_p_value"] = result["p_value"]
        result["review_mean_return"] = result["mean_return"]
        result["review_context_mean"] = None
        result["review_excess_mean"] = result["mean_return"]
    return result


def build_shortlist(
    prepared: pd.DataFrame,
    min_count: int,
    min_hit_rate: float,
    max_p_value: float,
) -> tuple[pd.DataFrame, pd.DataFrame]:
    frame = prepared.copy()
    frame["drop_reason"] = ""

    frame.loc[frame["count"] < min_count, "drop_reason"] = f"count_below_{min_count}"
    frame.loc[
        frame["drop_reason"].eq("") & (frame["review_hit_rate"] < min_hit_rate),
        "drop_reason",
    ] = f"hit_rate_below_{min_hit_rate:.2f}"
    frame.loc[
        frame["drop_reason"].eq("") & frame["review_p_value"].fillna(1.0).gt(max_p_value),
        "drop_reason",
    ] = f"p_value_above_{max_p_value:.2f}"

    passing = frame[frame["drop_reason"].eq("")].copy()
    failing = frame[frame["drop_reason"].ne("")].copy()

    passing = passing.sort_values(
        [
            "family",
            "stage",
            "signal_score",
            "count",
            "event_priority",
            "window_priority",
            "review_p_value",
        ],
        ascending=[True, True, False, False, True, True, True],
    )

    winners = passing.drop_duplicates(subset=["family", "stage"], keep="first").copy()
    passing["winner_key"] = passing["family"] + "::" + passing["stage"]
    winners["winner_key"] = winners["family"] + "::" + winners["stage"]

    winning_signature = {
        (row["family"], row["stage"], row["event_type"], row["window_label"])
        for row in winners.to_dict("records")
    }

    redundant_mask = ~passing.apply(
        lambda row: (row["family"], row["stage"], row["event_type"], row["window_label"]) in winning_signature,
        axis=1,
    )
    redundant = passing[redundant_mask].copy()
    redundant["drop_reason"] = "redundant_family_stage_alternative"

    shortlist = winners.drop(columns=["winner_key"]).reset_index(drop=True)
    dropped = pd.concat([failing, redundant], ignore_index=True).sort_values(
        ["drop_reason", "family", "stage", "count"],
        ascending=[True, True, True, False],
    ).reset_index(drop=True)
    return shortlist, dropped


def build_review_markdown(shortlist: pd.DataFrame, dropped: pd.DataFrame) -> str:
    review_mode = "baseline-adjusted" if not shortlist.empty and shortlist["review_mode"].eq("baseline_adjusted").any() else "raw"
    lines = [
        "# Phase 2 Corporate Review",
        "",
        f"This review keeps one best window per family/stage after filtering out thin, weak, or redundant groups. Active mode: {review_mode}.",
        "",
        "## Shortlist",
        "",
        "| Family | Stage | Event Type | Window | N | Event Mean | Baseline Mean | Excess Mean | Direction | Hit Rate | p-value | Source |",
        "|---|---|---|---|---:|---:|---:|---:|---|---:|---:|---|",
    ]

    for row in shortlist.to_dict("records"):
        lines.append(
            "| {family} | {stage} | {event_type} | {window_label} | {count} | {review_mean_return:.2f}% | {review_context_mean:.2f}% | {review_excess_mean:.2f}% | {review_direction} | "
            "{review_hit_rate:.1%} | {review_p_value:.4f} | {primary_source_table} |".format(
                family=row["family"],
                stage=row["stage"],
                event_type=row["event_type"],
                window_label=row["window_label"],
                count=int(row["count"]),
                review_mean_return=(row["review_mean_return"] or 0.0),
                review_context_mean=(row["review_context_mean"] or 0.0),
                review_excess_mean=(row["review_excess_mean"] or 0.0),
                review_direction=row["review_direction"],
                review_hit_rate=(row["review_hit_rate"] or 0.0),
                review_p_value=(row["review_p_value"] or 0.0),
                primary_source_table=row.get("primary_source_table", ""),
            )
        )

    lines.extend(
        [
            "",
            "## Drop Summary",
            "",
            "| Drop Reason | Groups |",
            "|---|---:|",
        ]
    )
    if dropped.empty:
        lines.append("| none | 0 |")
    else:
        counts = dropped["drop_reason"].value_counts()
        for reason, count in counts.items():
            lines.append(f"| {reason} | {count} |")

    return "\n".join(lines)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Review corporate-action summary and keep the strongest groups.")
    parser.add_argument(
        "--summary-path",
        default=str(RESULTS_DIR / "baseline_summary.csv"),
        help="Summary CSV to review. Defaults to baseline-adjusted summary.",
    )
    parser.add_argument("--min-count", type=int, default=30, help="Minimum group size to keep.")
    parser.add_argument("--min-hit-rate", type=float, default=0.60, help="Minimum directional hit rate to keep.")
    parser.add_argument("--max-p-value", type=float, default=0.05, help="Maximum p-value to keep.")
    return parser.parse_args()


if __name__ == "__main__":
    main()
