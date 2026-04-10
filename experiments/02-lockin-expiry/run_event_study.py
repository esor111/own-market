from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from event_study import rolling_baseline_returns, run_event_study  # noqa: E402
from price_loader import load_symbol_prices  # noqa: E402
from stats import describe_returns  # noqa: E402


DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"
WINDOWS = {
    "pre_-20_-1": (-20, -1),
    "reaction_0_5": (0, 5),
    "post_1_20": (1, 20),
}


def main() -> None:
    unlock_path = DATA_DIR / "unlock_events.csv"
    if not unlock_path.exists():
        raise FileNotFoundError(f"Missing unlock event file: {unlock_path}")

    unlocks = pd.read_csv(unlock_path)
    if unlocks.empty:
        raise RuntimeError("Unlock event table is empty.")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    event_returns: list[pd.DataFrame] = []
    baseline_returns: list[pd.DataFrame] = []

    for symbol in sorted(unlocks["symbol"].dropna().unique()):
        prices = load_symbol_prices(symbol)
        if prices.empty:
            continue

        symbol_events = unlocks[unlocks["symbol"] == symbol].copy()
        symbol_events = symbol_events.rename(columns={"unlock_date_proxy": "event_date"})
        symbol_returns = run_event_study(
            prices=prices,
            events=symbol_events[
                ["symbol", "company_name", "sector", "event_type", "source_url", "data_quality_note", "event_date"]
            ],
            event_date_col="event_date",
            windows=WINDOWS,
        )
        if not symbol_returns.empty:
            event_returns.append(symbol_returns)

        symbol_baseline = rolling_baseline_returns(prices=prices, windows=WINDOWS)
        if not symbol_baseline.empty:
            symbol_baseline["symbol"] = symbol
            baseline_returns.append(symbol_baseline)

    if not event_returns:
        raise RuntimeError("No lock-in event returns were generated.")

    events_frame = pd.concat(event_returns, ignore_index=True)
    baseline_frame = pd.concat(baseline_returns, ignore_index=True) if baseline_returns else pd.DataFrame()
    summary_frame = build_summary(events_frame, baseline_frame)

    events_path = RESULTS_DIR / "event_returns.csv"
    baseline_path = RESULTS_DIR / "baseline_returns.csv"
    summary_path = RESULTS_DIR / "summary.csv"
    findings_path = RESULTS_DIR / "findings.md"

    events_frame.to_csv(events_path, index=False)
    if not baseline_frame.empty:
        baseline_frame.to_csv(baseline_path, index=False)
    summary_frame.to_csv(summary_path, index=False)
    findings_path.write_text(build_findings_markdown(summary_frame), encoding="utf-8")

    print(f"Wrote lock-in event returns to {events_path}")
    print(f"Wrote lock-in summary to {summary_path}")


def build_summary(events_frame: pd.DataFrame, baseline_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for window_label, group in events_frame.groupby("window_label", dropna=False):
        event_stats = describe_returns(group["return_pct"], positive=False)
        baseline_group = baseline_frame[baseline_frame["window_label"] == window_label] if not baseline_frame.empty else pd.DataFrame()
        baseline_stats = describe_returns(baseline_group["return_pct"], positive=False) if not baseline_group.empty else {}

        rows.append(
            {
                "window_label": window_label,
                "event_count": event_stats.get("count"),
                "mean_event_return": event_stats.get("mean_return"),
                "median_event_return": event_stats.get("median_return"),
                "negative_hit_rate": event_stats.get("hit_rate"),
                "negative_ci_low": event_stats.get("hit_rate_ci_low"),
                "negative_ci_high": event_stats.get("hit_rate_ci_high"),
                "baseline_count": baseline_stats.get("count"),
                "baseline_mean_return": baseline_stats.get("mean_return"),
                "baseline_median_return": baseline_stats.get("median_return"),
                "baseline_negative_hit_rate": baseline_stats.get("hit_rate"),
                "delta_mean_return": _safe_subtract(
                    event_stats.get("mean_return"),
                    baseline_stats.get("mean_return"),
                ),
                "delta_negative_hit_rate": _safe_subtract(
                    event_stats.get("hit_rate"),
                    baseline_stats.get("hit_rate"),
                ),
                "t_stat": event_stats.get("t_stat"),
                "p_value": event_stats.get("p_value"),
            }
        )

    return pd.DataFrame(rows).sort_values("window_label").reset_index(drop=True)


def build_findings_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Lock-In Expiry Event Study",
        "",
        "| Window | Event N | Mean Event Return | Negative Hit Rate | Baseline Mean | Baseline Negative Hit | Delta Mean | Delta Negative Hit |",
        "|---|---:|---:|---:|---:|---:|---:|---:|",
    ]
    for row in summary.to_dict("records"):
        lines.append(
            "| {window_label} | {event_count} | {mean_event_return:.2f}% | {negative_hit_rate:.1%} | "
            "{baseline_mean_return:.2f}% | {baseline_negative_hit_rate:.1%} | {delta_mean_return:.2f}% | {delta_negative_hit_rate:.1%} |".format(
                window_label=row["window_label"],
                event_count=int(row["event_count"] or 0),
                mean_event_return=(row["mean_event_return"] or 0.0),
                negative_hit_rate=(row["negative_hit_rate"] or 0.0),
                baseline_mean_return=(row["baseline_mean_return"] or 0.0),
                baseline_negative_hit_rate=(row["baseline_negative_hit_rate"] or 0.0),
                delta_mean_return=(row["delta_mean_return"] or 0.0),
                delta_negative_hit_rate=(row["delta_negative_hit_rate"] or 0.0),
            )
        )
    return "\n".join(lines)


def _safe_subtract(left: float | None, right: float | None) -> float | None:
    if left is None or right is None:
        return None
    return left - right


if __name__ == "__main__":
    main()
