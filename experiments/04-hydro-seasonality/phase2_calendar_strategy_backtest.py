"""
Phase 2: Backtest calendar-based seasonal strategies for hydropower stocks.

Tests three "buy weak month, sell strong month" strategies derived from L-009:

  Strategy A: Buy end of February, sell end of July
  Strategy B: Buy end of August, sell end of January (next year)
  Strategy C: Buy end of November, sell end of January (next year)

For each strategy:
  - Compute return per stock per year
  - Win rate (years where strategy made money)
  - Mean return, median return
  - Worst-year drawdown
  - Compare to "buy Jan 1, hold to Dec 31" buy-and-hold benchmark for the same year

Output:
  results/phase2_strategy_returns.csv      — one row per stock × year × strategy
  results/phase2_strategy_summary.csv      — aggregated by strategy
  results/phase2_strategy_review.md        — human-readable report
"""
from __future__ import annotations

import sys
from datetime import date
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from price_loader import load_symbol_prices  # noqa: E402


DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"

HYDRO_SYMBOLS = ["SMHL", "HIDCL", "NGPL", "API", "AKPL", "UPPER"]
BANK_SYMBOLS = ["NABIL", "NBL", "EBL", "HBL", "KBL", "SANIMA", "PRVU", "NIMB"]

STRATEGIES = [
    {
        "name": "A_feb_to_jul",
        "label": "Buy end-of-Feb, sell end-of-Jul",
        "buy_month": 2,
        "sell_month": 7,
        "sell_year_offset": 0,
    },
    {
        "name": "B_aug_to_jan",
        "label": "Buy end-of-Aug, sell end-of-Jan (next year)",
        "buy_month": 8,
        "sell_month": 1,
        "sell_year_offset": 1,
    },
    {
        "name": "C_nov_to_jan",
        "label": "Buy end-of-Nov, sell end-of-Jan (next year)",
        "buy_month": 11,
        "sell_month": 1,
        "sell_year_offset": 1,
    },
]


def main() -> None:
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    # Load all hydro and bank prices
    print("Loading price data...")
    all_prices: dict[str, pd.DataFrame] = {}
    for symbol in HYDRO_SYMBOLS + BANK_SYMBOLS:
        prices = load_symbol_prices(symbol)
        if not prices.empty:
            prices = prices.copy()
            prices["date"] = pd.to_datetime(prices["date"])
            prices["year"] = prices["date"].dt.year
            prices["month"] = prices["date"].dt.month
            all_prices[symbol] = prices

    # Run each strategy for hydro and bank symbols
    rows: list[dict] = []
    for symbol, prices in all_prices.items():
        sector = "Hydropower" if symbol in HYDRO_SYMBOLS else "Commercial Bank"
        for strategy in STRATEGIES:
            strategy_rows = backtest_strategy(symbol, sector, prices, strategy)
            rows.extend(strategy_rows)

        # Buy-and-hold benchmark per calendar year
        rows.extend(buy_and_hold_benchmark(symbol, sector, prices))

    if not rows:
        raise RuntimeError("No strategy returns computed.")

    detail = pd.DataFrame(rows).sort_values(
        ["strategy", "sector", "symbol", "buy_year"]
    ).reset_index(drop=True)
    detail.to_csv(RESULTS_DIR / "phase2_strategy_returns.csv", index=False)

    summary = build_summary(detail)
    summary.to_csv(RESULTS_DIR / "phase2_strategy_summary.csv", index=False)

    review_md = build_review_markdown(detail, summary)
    (RESULTS_DIR / "phase2_strategy_review.md").write_text(review_md, encoding="utf-8")

    print(f"Wrote detail to {RESULTS_DIR / 'phase2_strategy_returns.csv'}")
    print(f"Wrote summary to {RESULTS_DIR / 'phase2_strategy_summary.csv'}")
    print(f"Wrote review to {RESULTS_DIR / 'phase2_strategy_review.md'}")


def backtest_strategy(
    symbol: str,
    sector: str,
    prices: pd.DataFrame,
    strategy: dict,
) -> list[dict]:
    """Run a single strategy across all available years for a symbol."""
    rows: list[dict] = []
    buy_month = strategy["buy_month"]
    sell_month = strategy["sell_month"]
    sell_year_offset = strategy["sell_year_offset"]

    years_in_data = sorted(prices["year"].unique())

    for buy_year in years_in_data:
        sell_year = buy_year + sell_year_offset

        buy_close = last_close_in_month(prices, buy_year, buy_month)
        sell_close = last_close_in_month(prices, sell_year, sell_month)

        if buy_close is None or sell_close is None:
            continue
        if buy_close <= 0:
            continue

        return_pct = ((sell_close / buy_close) - 1.0) * 100.0

        rows.append({
            "strategy": strategy["name"],
            "strategy_label": strategy["label"],
            "sector": sector,
            "symbol": symbol,
            "buy_year": int(buy_year),
            "sell_year": int(sell_year),
            "buy_close": float(buy_close),
            "sell_close": float(sell_close),
            "return_pct": round(return_pct, 4),
            "win": return_pct > 0,
        })

    return rows


def buy_and_hold_benchmark(
    symbol: str,
    sector: str,
    prices: pd.DataFrame,
) -> list[dict]:
    """Buy first trading day of year, sell last trading day of year. Benchmark."""
    rows: list[dict] = []
    for year in sorted(prices["year"].unique()):
        year_data = prices[prices["year"] == year].sort_values("date")
        if len(year_data) < 2:
            continue
        buy = year_data.iloc[0]
        sell = year_data.iloc[-1]
        if buy["close"] is None or buy["close"] <= 0 or sell["close"] is None:
            continue
        return_pct = ((sell["close"] / buy["close"]) - 1.0) * 100.0
        rows.append({
            "strategy": "Z_buy_and_hold_year",
            "strategy_label": "Buy first day of year, sell last day of year",
            "sector": sector,
            "symbol": symbol,
            "buy_year": int(year),
            "sell_year": int(year),
            "buy_close": float(buy["close"]),
            "sell_close": float(sell["close"]),
            "return_pct": round(return_pct, 4),
            "win": return_pct > 0,
        })
    return rows


def last_close_in_month(prices: pd.DataFrame, year: int, month: int) -> float | None:
    """Return the last close in (year, month) or None if missing."""
    subset = prices[(prices["year"] == year) & (prices["month"] == month)]
    if subset.empty:
        return None
    last_row = subset.sort_values("date").iloc[-1]
    close = last_row["close"]
    return float(close) if close is not None and not pd.isna(close) else None


def build_summary(detail: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []
    for (strategy, sector), group in detail.groupby(["strategy", "sector"]):
        n = len(group)
        n_wins = int(group["win"].sum())
        rows.append({
            "strategy": strategy,
            "strategy_label": group["strategy_label"].iloc[0],
            "sector": sector,
            "n_trades": n,
            "n_wins": n_wins,
            "win_rate": round(n_wins / n, 4) if n else None,
            "mean_return_pct": round(float(group["return_pct"].mean()), 4),
            "median_return_pct": round(float(group["return_pct"].median()), 4),
            "best_return_pct": round(float(group["return_pct"].max()), 4),
            "worst_return_pct": round(float(group["return_pct"].min()), 4),
            "std_return_pct": round(float(group["return_pct"].std()), 4) if n > 1 else None,
        })
    return pd.DataFrame(rows).sort_values(["sector", "strategy"]).reset_index(drop=True)


def build_review_markdown(detail: pd.DataFrame, summary: pd.DataFrame) -> str:
    lines = [
        "# Phase 2: Calendar Strategy Backtest",
        "",
        "Tests whether 'buy seasonally weak month, sell seasonally strong month' actually makes money.",
        "",
        "## Strategies Tested",
        "",
        "- **Strategy A**: Buy end-of-Feb, sell end-of-Jul (~5 months)",
        "- **Strategy B**: Buy end-of-Aug, sell end-of-Jan next year (~5 months)",
        "- **Strategy C**: Buy end-of-Nov, sell end-of-Jan next year (~2 months)",
        "- **Benchmark Z**: Buy first day of year, sell last day of year (calendar year buy-and-hold)",
        "",
        "## Hydropower Results",
        "",
        "| Strategy | N | Wins | Win Rate | Mean | Median | Best | Worst | Std |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    hydro = summary[summary["sector"] == "Hydropower"]
    for row in hydro.to_dict("records"):
        lines.append(
            f"| {row['strategy']} | {row['n_trades']} | {row['n_wins']} | "
            f"{row['win_rate']:.1%} | {row['mean_return_pct']:.2f}% | "
            f"{row['median_return_pct']:.2f}% | {row['best_return_pct']:.2f}% | "
            f"{row['worst_return_pct']:.2f}% | "
            f"{row['std_return_pct']:.2f}% |"
        )

    lines.extend([
        "",
        "## Commercial Bank Results (Control)",
        "",
        "| Strategy | N | Wins | Win Rate | Mean | Median | Best | Worst | Std |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ])

    bank = summary[summary["sector"] == "Commercial Bank"]
    for row in bank.to_dict("records"):
        lines.append(
            f"| {row['strategy']} | {row['n_trades']} | {row['n_wins']} | "
            f"{row['win_rate']:.1%} | {row['mean_return_pct']:.2f}% | "
            f"{row['median_return_pct']:.2f}% | {row['best_return_pct']:.2f}% | "
            f"{row['worst_return_pct']:.2f}% | "
            f"{row['std_return_pct']:.2f}% |"
        )

    # Per-symbol detail tables for hydro strategies
    lines.extend(["", "## Per-Symbol Hydropower Detail", ""])
    for strategy_name in ["A_feb_to_jul", "B_aug_to_jan", "C_nov_to_jan"]:
        strat_data = detail[
            (detail["strategy"] == strategy_name) & (detail["sector"] == "Hydropower")
        ]
        if strat_data.empty:
            continue
        label = strat_data["strategy_label"].iloc[0]
        lines.append(f"### {strategy_name}: {label}")
        lines.append("")
        lines.append("| Symbol | Year | Buy Close | Sell Close | Return | Result |")
        lines.append("|---|---:|---:|---:|---:|---|")
        for row in strat_data.sort_values(["symbol", "buy_year"]).to_dict("records"):
            result = "WIN" if row["win"] else "loss"
            lines.append(
                f"| {row['symbol']} | {row['buy_year']} | {row['buy_close']:.2f} | "
                f"{row['sell_close']:.2f} | {row['return_pct']:+.2f}% | {result} |"
            )
        lines.append("")

    # Honest verdict section
    lines.extend(["## Honest Verdict", ""])
    for strategy_name in ["A_feb_to_jul", "B_aug_to_jan", "C_nov_to_jan"]:
        hydro_row = hydro[hydro["strategy"] == strategy_name]
        if hydro_row.empty:
            continue
        r = hydro_row.iloc[0]
        verdict = "PROMISING" if r["win_rate"] >= 0.65 and r["mean_return_pct"] > 0 else (
            "WEAK" if r["win_rate"] >= 0.55 else "FAILED"
        )
        lines.append(
            f"- **{strategy_name}** ({r['strategy_label']}): "
            f"win rate {r['win_rate']:.1%}, mean {r['mean_return_pct']:.2f}%, N={r['n_trades']} → **{verdict}**"
        )

    lines.append("")
    lines.append(
        "*Caution*: small sample (4-5 years per stock × 6 hydro stocks). "
        "A win rate of 70%+ on N<30 is suggestive, not proven."
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
