from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from event_study import DEFAULT_WINDOWS, rolling_baseline_returns, run_event_study  # noqa: E402
from price_loader import list_available_dates, load_market_rows, load_symbol_prices  # noqa: E402
from stats import describe_returns  # noqa: E402


DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"
DATE_FIELDS = ["announcement_date", "approval_date", "book_close_date", "listing_date"]
BASELINE_LOOKBACK = 120
BASELINE_MIN_HISTORY = 30


def main() -> None:
    events_path = DATA_DIR / "events.csv"
    if not events_path.exists():
        raise FileNotFoundError(f"Missing event table: {events_path}")

    events = pd.read_csv(events_path)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    market_proxy = build_market_regime_proxy()
    event_returns: list[pd.DataFrame] = []

    for symbol in sorted(events["symbol"].dropna().unique()):
        prices = load_symbol_prices(symbol)
        if prices.empty:
            continue

        baseline_frame = rolling_baseline_returns(prices, windows=DEFAULT_WINDOWS)
        symbol_events = events[events["symbol"] == symbol].copy()
        for date_field in DATE_FIELDS:
            subset = symbol_events[symbol_events[date_field].notna() & (symbol_events[date_field] != "")]
            if subset.empty:
                continue

            study_input = subset[
                [
                    "symbol",
                    "company_name",
                    "sector",
                    "event_type",
                    "source_table",
                    "event_label",
                    "source_url",
                    date_field,
                ]
            ].rename(columns={date_field: "event_date"})

            returns = run_event_study(
                prices=prices,
                events=study_input,
                event_date_col="event_date",
                windows=DEFAULT_WINDOWS,
                max_forward_gap_days=10,
            )
            if returns.empty:
                continue

            returns["date_field"] = date_field
            returns = attach_local_baselines(returns, baseline_frame)
            event_returns.append(returns)

    if not event_returns:
        raise RuntimeError("No event-study returns were generated after valid-date anchoring.")

    returns_frame = pd.concat(event_returns, ignore_index=True)
    returns_frame = merge_market_regime(returns_frame, market_proxy)

    raw_summary = build_directional_summary(returns_frame, return_col="return_pct")
    baseline_summary = build_baseline_adjusted_summary(returns_frame)
    regime_summary = build_baseline_adjusted_summary(
        returns_frame[returns_frame["market_regime"] != "unknown"],
        group_cols=["event_type", "date_field", "window_label", "market_regime"],
    )

    returns_path = RESULTS_DIR / "event_returns.csv"
    raw_summary_path = RESULTS_DIR / "summary.csv"
    baseline_summary_path = RESULTS_DIR / "baseline_summary.csv"
    regime_summary_path = RESULTS_DIR / "baseline_regime_summary.csv"
    market_proxy_path = RESULTS_DIR / "market_regime_proxy.csv"
    findings_path = RESULTS_DIR / "findings.md"

    returns_frame.to_csv(returns_path, index=False)
    raw_summary.to_csv(raw_summary_path, index=False)
    baseline_summary.to_csv(baseline_summary_path, index=False)
    regime_summary.to_csv(regime_summary_path, index=False)
    market_proxy.to_csv(market_proxy_path, index=False)
    findings_path.write_text(build_findings_markdown(baseline_summary), encoding="utf-8")

    print(f"Wrote event-level returns to {returns_path}")
    print(f"Wrote raw summary to {raw_summary_path}")
    print(f"Wrote baseline-adjusted summary to {baseline_summary_path}")
    print(f"Wrote baseline regime summary to {regime_summary_path}")


def attach_local_baselines(
    returns_frame: pd.DataFrame,
    baseline_frame: pd.DataFrame,
    lookback: int = BASELINE_LOOKBACK,
    min_history: int = BASELINE_MIN_HISTORY,
) -> pd.DataFrame:
    if returns_frame.empty:
        return returns_frame

    baseline = baseline_frame.copy()
    baseline["anchor_date"] = pd.to_datetime(baseline["anchor_date"], errors="coerce")
    returns = returns_frame.copy()
    returns["anchor_date"] = pd.to_datetime(returns["anchor_date"], errors="coerce")

    baseline_groups = {
        window_label: group.sort_values("anchor_date").reset_index(drop=True)
        for window_label, group in baseline.groupby("window_label", dropna=False)
    }

    mean_values: list[float | None] = []
    median_values: list[float | None] = []
    negative_hit_values: list[float | None] = []
    obs_counts: list[int] = []
    excess_values: list[float | None] = []

    for row in returns.to_dict("records"):
        baseline_group = baseline_groups.get(row["window_label"])
        if baseline_group is None or baseline_group.empty:
            mean_values.append(None)
            median_values.append(None)
            negative_hit_values.append(None)
            obs_counts.append(0)
            excess_values.append(None)
            continue

        prior = baseline_group[baseline_group["anchor_date"] < row["anchor_date"]].tail(lookback)
        if len(prior) < min_history:
            mean_values.append(None)
            median_values.append(None)
            negative_hit_values.append(None)
            obs_counts.append(len(prior))
            excess_values.append(None)
            continue

        stats = describe_returns(prior["return_pct"], positive=False)
        baseline_mean = stats["mean_return"]
        mean_values.append(baseline_mean)
        median_values.append(stats["median_return"])
        negative_hit_values.append(stats["hit_rate"])
        obs_counts.append(int(stats["count"] or 0))
        excess_values.append(None if baseline_mean is None else row["return_pct"] - baseline_mean)

    returns["baseline_obs_count"] = obs_counts
    returns["baseline_mean_return"] = mean_values
    returns["baseline_median_return"] = median_values
    returns["baseline_negative_hit_rate"] = negative_hit_values
    returns["excess_return_pct"] = excess_values
    return returns


def build_market_regime_proxy() -> pd.DataFrame:
    rows: list[dict] = []
    previous_signature = None

    for business_date in list_available_dates():
        market_rows = load_market_rows(business_date)
        if market_rows.empty:
            continue

        diff_series = pd.to_numeric(market_rows["diff_pct"], errors="coerce").dropna()
        turnover_series = pd.to_numeric(market_rows["turnover"], errors="coerce").fillna(0.0)
        volume_series = pd.to_numeric(market_rows["volume"], errors="coerce").fillna(0.0)
        if diff_series.empty:
            continue

        row = {
            "date": pd.Timestamp(business_date),
            "symbol_count": int(market_rows["symbol"].nunique()),
            "median_diff_pct": float(diff_series.median()),
            "mean_diff_pct": float(diff_series.mean()),
            "total_turnover": float(turnover_series.sum()),
            "total_volume": float(volume_series.sum()),
        }
        signature = (
            row["symbol_count"],
            round(row["median_diff_pct"], 4),
            round(row["mean_diff_pct"], 4),
            round(row["total_turnover"], 2),
            round(row["total_volume"], 2),
        )
        if signature == previous_signature:
            continue
        previous_signature = signature
        rows.append(row)

    frame = pd.DataFrame(rows).sort_values("date").reset_index(drop=True)
    if frame.empty:
        return pd.DataFrame(columns=["anchor_date", "market_proxy", "market_proxy_sma200", "market_regime"])

    frame["market_proxy"] = 100.0 * (1.0 + frame["median_diff_pct"] / 100.0).cumprod()
    frame["market_proxy_sma200"] = frame["market_proxy"].rolling(200, min_periods=200).mean()
    frame["market_regime"] = "unknown"
    mask = frame["market_proxy_sma200"].notna()
    frame.loc[mask, "market_regime"] = frame.loc[mask].apply(
        lambda row: "above_sma200" if row["market_proxy"] >= row["market_proxy_sma200"] else "below_sma200",
        axis=1,
    )
    frame["anchor_date"] = frame["date"].dt.strftime("%Y-%m-%d")
    return frame[["anchor_date", "market_proxy", "market_proxy_sma200", "market_regime"]]


def merge_market_regime(returns_frame: pd.DataFrame, market_proxy: pd.DataFrame) -> pd.DataFrame:
    if returns_frame.empty:
        return returns_frame

    merged = returns_frame.copy()
    merged["anchor_date"] = pd.to_datetime(merged["anchor_date"], errors="coerce").dt.strftime("%Y-%m-%d")
    if market_proxy.empty:
        merged["market_proxy"] = None
        merged["market_proxy_sma200"] = None
        merged["market_regime"] = "unknown"
        return merged

    merged = merged.merge(market_proxy, on="anchor_date", how="left")
    merged["market_regime"] = merged["market_regime"].fillna("unknown")
    return merged


def build_directional_summary(frame: pd.DataFrame, return_col: str = "return_pct") -> pd.DataFrame:
    rows: list[dict] = []
    grouped = frame.groupby(["event_type", "date_field", "window_label"], dropna=False)
    for (event_type, date_field, window_label), group in grouped:
        returns = group[return_col].tolist()
        positive = describe_returns(returns, positive=True)
        negative = describe_returns(returns, positive=False)

        direction = "positive"
        best_hit_rate = positive["hit_rate"]
        if (negative["hit_rate"] or 0) > (positive["hit_rate"] or 0):
            direction = "negative"
            best_hit_rate = negative["hit_rate"]

        rows.append(
            {
                "event_type": event_type,
                "date_field": date_field,
                "window_label": window_label,
                "count": positive["count"],
                "mean_return": positive["mean_return"],
                "median_return": positive["median_return"],
                "positive_hit_rate": positive["hit_rate"],
                "positive_ci_low": positive["hit_rate_ci_low"],
                "positive_ci_high": positive["hit_rate_ci_high"],
                "negative_hit_rate": negative["hit_rate"],
                "negative_ci_low": negative["hit_rate_ci_low"],
                "negative_ci_high": negative["hit_rate_ci_high"],
                "t_stat": positive["t_stat"],
                "p_value": positive["p_value"],
                "best_direction": direction,
                "best_directional_hit_rate": best_hit_rate,
            }
        )

    return pd.DataFrame(rows).sort_values(
        ["count", "best_directional_hit_rate", "mean_return"],
        ascending=[False, False, False],
    ).reset_index(drop=True)


def build_baseline_adjusted_summary(
    frame: pd.DataFrame,
    group_cols: list[str] | None = None,
) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    groups = group_cols or ["event_type", "date_field", "window_label"]
    adjusted = frame.dropna(subset=["excess_return_pct"]).copy()
    if adjusted.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for keys, group in adjusted.groupby(groups, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {column: value for column, value in zip(groups, keys)}

        raw_negative = describe_returns(group["return_pct"], positive=False)
        excess_positive = describe_returns(group["excess_return_pct"], positive=True)
        excess_negative = describe_returns(group["excess_return_pct"], positive=False)

        best_direction = "positive"
        best_hit_rate = excess_positive["hit_rate"]
        if (excess_negative["hit_rate"] or 0) > (excess_positive["hit_rate"] or 0):
            best_direction = "negative"
            best_hit_rate = excess_negative["hit_rate"]

        row.update(
            {
                "count": int(len(group)),
                "mean_event_return": group["return_pct"].mean(),
                "mean_baseline_return": group["baseline_mean_return"].mean(),
                "mean_excess_return": group["excess_return_pct"].mean(),
                "median_excess_return": group["excess_return_pct"].median(),
                "raw_negative_hit_rate": raw_negative["hit_rate"],
                "baseline_negative_hit_rate": group["baseline_negative_hit_rate"].mean(),
                "excess_positive_hit_rate": excess_positive["hit_rate"],
                "excess_positive_ci_low": excess_positive["hit_rate_ci_low"],
                "excess_positive_ci_high": excess_positive["hit_rate_ci_high"],
                "excess_negative_hit_rate": excess_negative["hit_rate"],
                "excess_negative_ci_low": excess_negative["hit_rate_ci_low"],
                "excess_negative_ci_high": excess_negative["hit_rate_ci_high"],
                "t_stat_excess": excess_positive["t_stat"],
                "p_value_excess": excess_positive["p_value"],
                "best_adjusted_direction": best_direction,
                "best_adjusted_hit_rate": best_hit_rate,
            }
        )
        rows.append(row)

    return pd.DataFrame(rows).sort_values(
        ["count", "best_adjusted_hit_rate", "mean_excess_return"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_findings_markdown(summary: pd.DataFrame) -> str:
    lines = [
        "# Corporate Action Event Study (Baseline Adjusted)",
        "",
        "Ranked by baseline-adjusted separation, not just raw event drift.",
        "",
    ]

    interesting = summary[summary["count"] >= 3].head(20)
    if interesting.empty:
        lines.append("No adjusted event groups with at least 3 scored cases yet.")
        return "\n".join(lines)

    lines.append("| Event Type | Date Field | Window | N | Mean Event | Mean Baseline | Mean Excess | Raw Neg Hit | Adjusted Best Dir | Adjusted Best Hit |")
    lines.append("|---|---|---:|---:|---:|---:|---:|---:|---|---:|")
    for row in interesting.to_dict("records"):
        lines.append(
            "| {event_type} | {date_field} | {window_label} | {count} | {mean_event_return:.2f}% | {mean_baseline_return:.2f}% | "
            "{mean_excess_return:.2f}% | {raw_negative_hit_rate:.1%} | {best_adjusted_direction} | {best_adjusted_hit_rate:.1%} |".format(
                event_type=row["event_type"],
                date_field=row["date_field"],
                window_label=row["window_label"],
                count=int(row["count"]),
                mean_event_return=(row["mean_event_return"] or 0.0),
                mean_baseline_return=(row["mean_baseline_return"] or 0.0),
                mean_excess_return=(row["mean_excess_return"] or 0.0),
                raw_negative_hit_rate=(row["raw_negative_hit_rate"] or 0.0),
                best_adjusted_direction=row["best_adjusted_direction"],
                best_adjusted_hit_rate=(row["best_adjusted_hit_rate"] or 0.0),
            )
        )

    return "\n".join(lines)


if __name__ == "__main__":
    main()
