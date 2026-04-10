"""
Analyze monthly return seasonality for hydro vs bank stocks.

Reads the monthly_returns.csv built by build_monthly_returns.py.
Produces:
  - Per-month hit rates and mean returns by sector
  - Per-month hit rates by individual stock
  - Cross-stock consistency scores
  - Hydro vs bank comparison
  - Year-by-year stability check

Output:
  results/sector_monthly_summary.csv   — month × sector summary
  results/symbol_monthly_summary.csv   — month × symbol summary
  results/cross_stock_consistency.csv   — which months are consistent across stocks
  results/year_stability.csv            — does the pattern hold across years
  results/findings.md                   — human-readable summary
"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from stats import describe_returns, wilson_interval  # noqa: E402


DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"

MONTH_NAMES = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "May", 6: "Jun",
    7: "Jul", 8: "Aug", 9: "Sep", 10: "Oct", 11: "Nov", 12: "Dec",
}


def main() -> None:
    monthly_path = DATA_DIR / "monthly_returns.csv"
    if not monthly_path.exists():
        raise FileNotFoundError(
            f"Missing monthly returns: {monthly_path}\n"
            "Run build_monthly_returns.py first."
        )

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    monthly = pd.read_csv(monthly_path)

    sector_summary = build_sector_monthly_summary(monthly)
    symbol_summary = build_symbol_monthly_summary(monthly)
    consistency = build_cross_stock_consistency(monthly)
    stability = build_year_stability(monthly)
    findings = build_findings_markdown(sector_summary, symbol_summary, consistency, stability, monthly)

    sector_summary.to_csv(RESULTS_DIR / "sector_monthly_summary.csv", index=False)
    symbol_summary.to_csv(RESULTS_DIR / "symbol_monthly_summary.csv", index=False)
    consistency.to_csv(RESULTS_DIR / "cross_stock_consistency.csv", index=False)
    stability.to_csv(RESULTS_DIR / "year_stability.csv", index=False)
    (RESULTS_DIR / "findings.md").write_text(findings, encoding="utf-8")

    print(f"Wrote sector summary to {RESULTS_DIR / 'sector_monthly_summary.csv'}")
    print(f"Wrote symbol summary to {RESULTS_DIR / 'symbol_monthly_summary.csv'}")
    print(f"Wrote cross-stock consistency to {RESULTS_DIR / 'cross_stock_consistency.csv'}")
    print(f"Wrote year stability to {RESULTS_DIR / 'year_stability.csv'}")
    print(f"Wrote findings to {RESULTS_DIR / 'findings.md'}")


def build_sector_monthly_summary(monthly: pd.DataFrame) -> pd.DataFrame:
    """For each sector × month, compute mean return, positive hit rate, and CI."""
    rows: list[dict] = []
    for (sector, month), group in monthly.groupby(["sector", "month"]):
        returns = group["return_pct"].tolist()
        stats = describe_returns(returns, positive=True)
        neg_stats = describe_returns(returns, positive=False)

        rows.append({
            "sector": sector,
            "month": int(month),
            "month_name": MONTH_NAMES.get(int(month), "?"),
            "count": stats["count"],
            "year_count": int(group["year"].nunique()),
            "symbol_count": int(group["symbol"].nunique()),
            "mean_return": stats["mean_return"],
            "median_return": stats["median_return"],
            "positive_hit_rate": stats["hit_rate"],
            "positive_ci_low": stats["hit_rate_ci_low"],
            "positive_ci_high": stats["hit_rate_ci_high"],
            "negative_hit_rate": neg_stats["hit_rate"],
            "t_stat": stats["t_stat"],
            "p_value": stats["p_value"],
        })

    return pd.DataFrame(rows).sort_values(["sector", "month"]).reset_index(drop=True)


def build_symbol_monthly_summary(monthly: pd.DataFrame) -> pd.DataFrame:
    """For each symbol × month, compute mean return and positive hit rate."""
    rows: list[dict] = []
    for (symbol, month), group in monthly.groupby(["symbol", "month"]):
        returns = group["return_pct"].tolist()
        stats = describe_returns(returns, positive=True)

        rows.append({
            "symbol": symbol,
            "sector": group["sector"].iloc[0],
            "month": int(month),
            "month_name": MONTH_NAMES.get(int(month), "?"),
            "count": stats["count"],
            "mean_return": stats["mean_return"],
            "positive_hit_rate": stats["hit_rate"],
            "positive_count": stats["hit_count"],
        })

    return pd.DataFrame(rows).sort_values(["sector", "symbol", "month"]).reset_index(drop=True)


def build_cross_stock_consistency(monthly: pd.DataFrame) -> pd.DataFrame:
    """For each sector × month, count how many individual stocks agree on direction."""
    rows: list[dict] = []

    for sector in ["Hydropower", "Commercial Bank"]:
        sector_data = monthly[monthly["sector"] == sector]
        for month in range(1, 13):
            month_data = sector_data[sector_data["month"] == month]
            if month_data.empty:
                continue

            # For each stock, compute its hit rate for this month
            stock_directions = []
            for symbol, group in month_data.groupby("symbol"):
                if len(group) < 2:
                    continue
                pos_rate = (group["return_pct"] > 0).mean()
                stock_directions.append({
                    "symbol": symbol,
                    "positive_rate": pos_rate,
                    "n_years": len(group),
                    "leans_positive": pos_rate > 0.5,
                    "leans_negative": pos_rate < 0.5,
                })

            if not stock_directions:
                continue

            n_stocks = len(stock_directions)
            n_positive_lean = sum(1 for s in stock_directions if s["leans_positive"])
            n_negative_lean = sum(1 for s in stock_directions if s["leans_negative"])
            agreement = max(n_positive_lean, n_negative_lean) / n_stocks if n_stocks > 0 else 0

            dominant_direction = "positive" if n_positive_lean >= n_negative_lean else "negative"
            mean_positive_rate = sum(s["positive_rate"] for s in stock_directions) / n_stocks

            rows.append({
                "sector": sector,
                "month": month,
                "month_name": MONTH_NAMES.get(month, "?"),
                "n_stocks": n_stocks,
                "n_positive_lean": n_positive_lean,
                "n_negative_lean": n_negative_lean,
                "stock_agreement": round(agreement, 3),
                "dominant_direction": dominant_direction,
                "mean_stock_positive_rate": round(mean_positive_rate, 3),
                "consistent": agreement >= 0.67 and n_stocks >= 3,
            })

    return pd.DataFrame(rows).sort_values(["sector", "month"]).reset_index(drop=True)


def build_year_stability(monthly: pd.DataFrame) -> pd.DataFrame:
    """For each sector × month × year, check if the direction matches the overall pattern."""
    rows: list[dict] = []

    for sector in ["Hydropower", "Commercial Bank"]:
        sector_data = monthly[monthly["sector"] == sector]
        for month in range(1, 13):
            month_data = sector_data[sector_data["month"] == month]
            if month_data.empty:
                continue

            # Overall direction for this sector-month
            overall_mean = month_data["return_pct"].mean()
            overall_positive = overall_mean > 0

            for year, year_group in month_data.groupby("year"):
                year_mean = year_group["return_pct"].mean()
                year_positive = year_mean > 0
                matches_pattern = year_positive == overall_positive

                rows.append({
                    "sector": sector,
                    "month": int(month),
                    "month_name": MONTH_NAMES.get(int(month), "?"),
                    "year": int(year),
                    "n_symbols": len(year_group),
                    "year_mean_return": round(year_mean, 2),
                    "overall_mean_return": round(overall_mean, 2),
                    "year_direction_matches": matches_pattern,
                })

    return pd.DataFrame(rows).sort_values(["sector", "month", "year"]).reset_index(drop=True)


def build_findings_markdown(
    sector_summary: pd.DataFrame,
    symbol_summary: pd.DataFrame,
    consistency: pd.DataFrame,
    stability: pd.DataFrame,
    monthly: pd.DataFrame,
) -> str:
    lines = [
        "# Hydropower Seasonality Analysis",
        "",
        f"Data: {monthly['symbol'].nunique()} symbols, "
        f"{monthly['year'].min()}-{monthly['year'].max()}, "
        f"{len(monthly)} monthly return observations.",
        "",
    ]

    # Section 1: Hydro sector monthly pattern
    lines.extend(["## Hydropower Monthly Pattern", ""])
    hydro_sector = sector_summary[sector_summary["sector"] == "Hydropower"].sort_values("month")
    if hydro_sector.empty:
        lines.append("No hydropower data.")
    else:
        lines.append("| Month | N | Mean Return | Pos Hit | Neg Hit | p-value | Signal |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for _, row in hydro_sector.iterrows():
            signal = ""
            if row["positive_hit_rate"] and row["positive_hit_rate"] >= 0.65:
                signal = "BULLISH"
            elif row["negative_hit_rate"] and row["negative_hit_rate"] >= 0.65:
                signal = "BEARISH"
            lines.append(
                f"| {row['month_name']} | {row['count']} | "
                f"{row['mean_return']:.2f}% | {row['positive_hit_rate']:.1%} | "
                f"{row['negative_hit_rate']:.1%} | {row['p_value']:.4f} | {signal} |"
            )

    # Section 2: Bank sector monthly pattern (control)
    lines.extend(["", "## Commercial Bank Monthly Pattern (Control)", ""])
    bank_sector = sector_summary[sector_summary["sector"] == "Commercial Bank"].sort_values("month")
    if bank_sector.empty:
        lines.append("No bank data.")
    else:
        lines.append("| Month | N | Mean Return | Pos Hit | Neg Hit | p-value | Signal |")
        lines.append("|---|---:|---:|---:|---:|---:|---|")
        for _, row in bank_sector.iterrows():
            signal = ""
            if row["positive_hit_rate"] and row["positive_hit_rate"] >= 0.65:
                signal = "BULLISH"
            elif row["negative_hit_rate"] and row["negative_hit_rate"] >= 0.65:
                signal = "BEARISH"
            lines.append(
                f"| {row['month_name']} | {row['count']} | "
                f"{row['mean_return']:.2f}% | {row['positive_hit_rate']:.1%} | "
                f"{row['negative_hit_rate']:.1%} | {row['p_value']:.4f} | {signal} |"
            )

    # Section 3: Cross-stock consistency
    lines.extend(["", "## Cross-Stock Consistency", ""])
    lines.append("Months where 67%+ of individual stocks lean the same direction.")
    lines.append("")

    for sector in ["Hydropower", "Commercial Bank"]:
        sector_cons = consistency[consistency["sector"] == sector].sort_values("month")
        lines.append(f"### {sector}")
        lines.append("")
        lines.append("| Month | Stocks | Positive | Negative | Agreement | Direction | Consistent |")
        lines.append("|---|---:|---:|---:|---:|---|---|")
        for _, row in sector_cons.iterrows():
            lines.append(
                f"| {row['month_name']} | {row['n_stocks']} | "
                f"{row['n_positive_lean']} | {row['n_negative_lean']} | "
                f"{row['stock_agreement']:.0%} | {row['dominant_direction']} | "
                f"{'YES' if row['consistent'] else 'no'} |"
            )
        lines.append("")

    # Section 4: Year stability
    lines.extend(["## Year-by-Year Stability", ""])
    lines.append("For each sector-month, how often does the yearly direction match the overall pattern?")
    lines.append("")

    for sector in ["Hydropower", "Commercial Bank"]:
        sector_stab = stability[stability["sector"] == sector]
        if sector_stab.empty:
            continue
        lines.append(f"### {sector}")
        lines.append("")
        lines.append("| Month | Years | Matches | Match Rate |")
        lines.append("|---|---:|---:|---:|")
        for month in range(1, 13):
            month_stab = sector_stab[sector_stab["month"] == month]
            if month_stab.empty:
                continue
            n_years = len(month_stab)
            n_matches = int(month_stab["year_direction_matches"].sum())
            match_rate = n_matches / n_years if n_years > 0 else 0
            lines.append(
                f"| {MONTH_NAMES.get(month, '?')} | {n_years} | {n_matches} | {match_rate:.0%} |"
            )
        lines.append("")

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
