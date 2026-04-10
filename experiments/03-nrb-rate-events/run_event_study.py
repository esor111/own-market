from __future__ import annotations

import sys
from datetime import datetime
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from event_study import rolling_baseline_returns, run_event_study  # noqa: E402
from price_loader import list_available_dates, load_market_rows, load_symbol_prices  # noqa: E402
from stats import describe_returns  # noqa: E402


DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"
BASELINE_LOOKBACK = 120
BASELINE_MIN_HISTORY = 30
TARGET_SYMBOLS = {
    "NABIL": "COMMERCIAL BANKS",
    "NBL": "COMMERCIAL BANKS",
    "EBL": "COMMERCIAL BANKS",
    "HBL": "COMMERCIAL BANKS",
    "KBL": "COMMERCIAL BANKS",
    "SANIMA": "COMMERCIAL BANKS",
    "PRVU": "COMMERCIAL BANKS",
    "NIMB": "COMMERCIAL BANKS",
    "SMHL": "HYDROPOWER",
    "HIDCL": "HYDROPOWER",
    "NGPL": "HYDROPOWER",
    "API": "HYDROPOWER",
    "AKPL": "HYDROPOWER",
    "UPPER": "HYDROPOWER",
}
EVENT_WINDOWS = {
    "pre_-5_-1": (-5, -1),
    "reaction_0_5": (0, 5),
    "drift_5_20": (5, 20),
}


def main() -> None:
    policy_path = DATA_DIR / "policy_events.csv"
    rate_move_path = DATA_DIR / "rate_move_events.csv"
    if not policy_path.exists():
        raise FileNotFoundError(f"Missing policy event table: {policy_path}")
    if not rate_move_path.exists():
        raise FileNotFoundError(f"Missing rate-move event table: {rate_move_path}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    policy_events = pd.read_csv(policy_path)
    rate_move_events = pd.read_csv(rate_move_path)
    market_proxy = build_market_regime_proxy()

    policy_returns = run_track(policy_events, track_name="policy_event", market_proxy=market_proxy)
    rate_returns = run_track(rate_move_events, track_name="rate_move", market_proxy=market_proxy)
    returns_frame = pd.concat([policy_returns, rate_returns], ignore_index=True)
    if returns_frame.empty:
        raise RuntimeError("No NRB event-study rows were generated.")

    returns_path = RESULTS_DIR / "event_returns.csv"
    returns_frame.to_csv(returns_path, index=False)

    policy_summary = build_baseline_adjusted_summary(
        returns_frame[returns_frame["track_name"] == "policy_event"],
        group_cols=["track_name", "event_type", "window_label", "direction"],
    )
    rate_summary = build_baseline_adjusted_summary(
        returns_frame[returns_frame["track_name"] == "rate_move"],
        group_cols=["track_name", "event_type", "window_label", "threshold"],
    )
    policy_sector_summary = build_baseline_adjusted_summary(
        returns_frame[returns_frame["track_name"] == "policy_event"],
        group_cols=["track_name", "event_type", "window_label", "sector"],
    )
    rate_sector_summary = build_baseline_adjusted_summary(
        returns_frame[returns_frame["track_name"] == "rate_move"],
        group_cols=["track_name", "event_type", "window_label", "threshold", "sector"],
    )

    policy_summary_path = RESULTS_DIR / "policy_summary.csv"
    rate_summary_path = RESULTS_DIR / "rate_move_summary.csv"
    policy_sector_path = RESULTS_DIR / "policy_sector_summary.csv"
    rate_sector_path = RESULTS_DIR / "rate_move_sector_summary.csv"
    findings_path = RESULTS_DIR / "findings.md"

    policy_summary.to_csv(policy_summary_path, index=False)
    rate_summary.to_csv(rate_summary_path, index=False)
    policy_sector_summary.to_csv(policy_sector_path, index=False)
    rate_sector_summary.to_csv(rate_sector_path, index=False)
    findings_path.write_text(
        build_findings_markdown(policy_summary, rate_summary),
        encoding="utf-8",
    )

    print(f"Wrote event-level returns to {returns_path}")
    print(f"Wrote policy summary to {policy_summary_path}")
    print(f"Wrote rate-move summary to {rate_summary_path}")


def run_track(events: pd.DataFrame, track_name: str, market_proxy: pd.DataFrame) -> pd.DataFrame:
    rows: list[pd.DataFrame] = []
    if events.empty:
        return pd.DataFrame()

    for symbol, sector in TARGET_SYMBOLS.items():
        prices = load_symbol_prices(symbol)
        if prices.empty:
            continue
        baseline_frame = rolling_baseline_returns(prices, windows=EVENT_WINDOWS)
        symbol_events = events.copy()
        symbol_events["symbol"] = symbol
        symbol_events["sector"] = sector
        symbol_events["track_name"] = track_name

        returns = run_event_study(
            prices=prices,
            events=symbol_events,
            event_date_col="event_date",
            windows=EVENT_WINDOWS,
            max_forward_gap_days=10,
        )
        if returns.empty:
            continue

        returns = attach_local_baselines(returns, baseline_frame)
        returns = merge_market_regime(returns, market_proxy)
        rows.append(returns)

    if not rows:
        return pd.DataFrame()
    return pd.concat(rows, ignore_index=True)


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
    negative_hit_values: list[float | None] = []
    obs_counts: list[int] = []
    excess_values: list[float | None] = []

    for row in returns.to_dict("records"):
        baseline_group = baseline_groups.get(row["window_label"])
        if baseline_group is None or baseline_group.empty:
            mean_values.append(None)
            negative_hit_values.append(None)
            obs_counts.append(0)
            excess_values.append(None)
            continue

        prior = baseline_group[baseline_group["anchor_date"] < row["anchor_date"]].tail(lookback)
        if len(prior) < min_history:
            mean_values.append(None)
            negative_hit_values.append(None)
            obs_counts.append(len(prior))
            excess_values.append(None)
            continue

        stats = describe_returns(prior["return_pct"], positive=False)
        baseline_mean = stats["mean_return"]
        mean_values.append(baseline_mean)
        negative_hit_values.append(stats["hit_rate"])
        obs_counts.append(int(stats["count"] or 0))
        excess_values.append(None if baseline_mean is None else row["return_pct"] - baseline_mean)

    returns["baseline_obs_count"] = obs_counts
    returns["baseline_mean_return"] = mean_values
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


def build_baseline_adjusted_summary(frame: pd.DataFrame, group_cols: list[str]) -> pd.DataFrame:
    if frame.empty:
        return pd.DataFrame()

    adjusted = frame.dropna(subset=["excess_return_pct"]).copy()
    if adjusted.empty:
        return pd.DataFrame()

    rows: list[dict] = []
    for keys, group in adjusted.groupby(group_cols, dropna=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        row = {column: value for column, value in zip(group_cols, keys)}
        raw_positive = describe_returns(group["return_pct"], positive=True)
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
                "raw_positive_hit_rate": raw_positive["hit_rate"],
                "raw_negative_hit_rate": raw_negative["hit_rate"],
                "excess_positive_hit_rate": excess_positive["hit_rate"],
                "excess_negative_hit_rate": excess_negative["hit_rate"],
                "best_adjusted_direction": best_direction,
                "best_adjusted_hit_rate": best_hit_rate,
                "p_value_excess": excess_positive["p_value"],
            }
        )
        rows.append(row)

    return pd.DataFrame(rows).sort_values(
        ["count", "best_adjusted_hit_rate", "mean_excess_return"],
        ascending=[False, False, True],
    ).reset_index(drop=True)


def build_findings_markdown(policy_summary: pd.DataFrame, rate_summary: pd.DataFrame) -> str:
    lines = [
        "# NRB Rate Events",
        "",
        "Baseline-adjusted summary of macro policy events and interbank rate-move events.",
        "",
        "## Policy Events",
        "",
    ]
    if policy_summary.empty:
        lines.append("No baseline-adjusted policy-event groups survived minimum-history filtering.")
    else:
        lines.append("| Event Type | Window | Direction | N | Mean Excess | Best Dir | Best Hit | p-value |")
        lines.append("|---|---|---|---:|---:|---|---:|---:|")
        for row in policy_summary.head(20).to_dict("records"):
            lines.append(
                "| {event_type} | {window_label} | {direction} | {count} | {mean_excess_return:.2f}% | {best_adjusted_direction} | {best_adjusted_hit_rate:.1%} | {p_value_excess:.4f} |".format(
                    event_type=row["event_type"],
                    window_label=row["window_label"],
                    direction=row["direction"],
                    count=int(row["count"]),
                    mean_excess_return=row["mean_excess_return"] or 0.0,
                    best_adjusted_direction=row["best_adjusted_direction"],
                    best_adjusted_hit_rate=row["best_adjusted_hit_rate"] or 0.0,
                    p_value_excess=(row["p_value_excess"] if row["p_value_excess"] is not None else float("nan")),
                )
            )

    lines.extend(["", "## Rate-Move Events", ""])
    if rate_summary.empty:
        lines.append("No baseline-adjusted rate-move groups survived minimum-history filtering.")
    else:
        lines.append("| Event Type | Window | Threshold | N | Mean Excess | Best Dir | Best Hit | p-value |")
        lines.append("|---|---|---:|---:|---:|---|---:|---:|")
        for row in rate_summary.head(20).to_dict("records"):
            lines.append(
                "| {event_type} | {window_label} | {threshold} | {count} | {mean_excess_return:.2f}% | {best_adjusted_direction} | {best_adjusted_hit_rate:.1%} | {p_value_excess:.4f} |".format(
                    event_type=row["event_type"],
                    window_label=row["window_label"],
                    threshold=row["threshold"],
                    count=int(row["count"]),
                    mean_excess_return=row["mean_excess_return"] or 0.0,
                    best_adjusted_direction=row["best_adjusted_direction"],
                    best_adjusted_hit_rate=row["best_adjusted_hit_rate"] or 0.0,
                    p_value_excess=(row["p_value_excess"] if row["p_value_excess"] is not None else float("nan")),
                )
            )

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
