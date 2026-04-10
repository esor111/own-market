from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

SCRIPT_DIR = Path(__file__).resolve().parent
SHARED_DIR = SCRIPT_DIR.parent / "shared"
if str(SHARED_DIR) not in sys.path:
    sys.path.insert(0, str(SHARED_DIR))

from stats import describe_returns  # noqa: E402


RESULTS_DIR = SCRIPT_DIR / "results"
RETURNS_PATH = RESULTS_DIR / "event_returns.csv"

FORWARD_RULES = [
    {
        "rule_key": "book_closure_notice__announcement_date__drift_2_10",
        "rule_name": "Book Closure Notice Caution",
        "event_types": ["book_closure_notice"],
        "date_field": "announcement_date",
        "window_label": "drift_2_10",
        "scope_hint": "cross-sector candidate",
    },
    {
        "rule_key": "dividend_family__announcement_date__drift_2_10",
        "rule_name": "Dividend Family Caution",
        "event_types": [
            "dividend_notice",
            "cash_dividend_notice",
            "cash_dividend",
            "bonus_and_cash_dividend",
        ],
        "date_field": "announcement_date",
        "window_label": "drift_2_10",
        "scope_hint": "bank-led candidate",
    },
]


def main() -> None:
    if not RETURNS_PATH.exists():
        raise FileNotFoundError(f"Missing event returns file: {RETURNS_PATH}")

    returns = pd.read_csv(RETURNS_PATH)
    returns = returns.dropna(subset=["excess_return_pct"]).copy()

    overall_rows: list[dict] = []
    sector_rows: list[dict] = []
    regime_rows: list[dict] = []

    for rule in FORWARD_RULES:
        matched = select_rule_rows(returns, rule)
        if matched.empty:
            continue

        overall_rows.append(summarize_rule(matched, rule))
        for sector, group in matched.groupby("sector", dropna=False):
            sector_rows.append(summarize_rule(group, rule, {"sector": sector}))
        for regime, group in matched.groupby("market_regime", dropna=False):
            regime_rows.append(summarize_rule(group, rule, {"market_regime": regime}))

    overall = pd.DataFrame(overall_rows).sort_values("rule_key").reset_index(drop=True)
    by_sector = pd.DataFrame(sector_rows).sort_values(["rule_key", "count"], ascending=[True, False]).reset_index(drop=True)
    by_regime = pd.DataFrame(regime_rows).sort_values(["rule_key", "count"], ascending=[True, False]).reset_index(drop=True)

    overall_path = RESULTS_DIR / "phase4_event_caution_overall.csv"
    sector_path = RESULTS_DIR / "phase4_event_caution_by_sector.csv"
    regime_path = RESULTS_DIR / "phase4_event_caution_by_regime.csv"
    review_path = RESULTS_DIR / "phase4_event_caution_review.md"

    overall.to_csv(overall_path, index=False)
    by_sector.to_csv(sector_path, index=False)
    by_regime.to_csv(regime_path, index=False)
    review_path.write_text(build_review_markdown(overall, by_sector, by_regime), encoding="utf-8")

    print(f"Wrote overall rule review to {overall_path}")
    print(f"Wrote sector rule review to {sector_path}")
    print(f"Wrote regime rule review to {regime_path}")
    print(f"Wrote markdown review to {review_path}")


def select_rule_rows(frame: pd.DataFrame, rule: dict) -> pd.DataFrame:
    matched = frame[
        frame["event_type"].isin(rule["event_types"])
        & frame["date_field"].eq(rule["date_field"])
        & frame["window_label"].eq(rule["window_label"])
    ].copy()
    return dedupe_rule_rows(matched)


def dedupe_rule_rows(frame: pd.DataFrame) -> pd.DataFrame:
    if frame.empty:
        return frame
    ranked = frame.copy()
    ranked["source_rank"] = ranked["source_table"].map(
        {
            "company-announcements": 1,
            "company-events": 2,
            "company-dividend": 3,
            "company-agm": 4,
            "company-rightshare": 5,
        }
    ).fillna(99)
    ranked = ranked.sort_values(
        ["symbol", "event_date", "source_rank", "event_type"],
        ascending=[True, True, True, True],
    )
    return ranked.drop_duplicates(subset=["symbol", "event_date"], keep="first").drop(columns=["source_rank"])


def summarize_rule(frame: pd.DataFrame, rule: dict, extra: dict | None = None) -> dict:
    raw_count = int(len(frame))
    raw_negative = describe_returns(frame["return_pct"], positive=False)
    excess_positive = describe_returns(frame["excess_return_pct"], positive=True)
    excess_negative = describe_returns(frame["excess_return_pct"], positive=False)

    row = {
        "rule_key": rule["rule_key"],
        "rule_name": rule["rule_name"],
        "date_field": rule["date_field"],
        "window_label": rule["window_label"],
        "event_types": ",".join(rule["event_types"]),
        "scope_hint": rule["scope_hint"],
        "count": raw_count,
        "symbol_count": int(frame["symbol"].nunique()),
        "unique_symbol_event_count": int(frame[["symbol", "event_date"]].drop_duplicates().shape[0]),
        "mean_event_return": frame["return_pct"].mean(),
        "mean_baseline_return": frame["baseline_mean_return"].mean(),
        "mean_excess_return": frame["excess_return_pct"].mean(),
        "median_excess_return": frame["excess_return_pct"].median(),
        "raw_negative_hit_rate": raw_negative["hit_rate"],
        "baseline_negative_hit_rate": frame["baseline_negative_hit_rate"].mean(),
        "adjusted_negative_hit_rate": excess_negative["hit_rate"],
        "adjusted_positive_hit_rate": excess_positive["hit_rate"],
        "t_stat_excess": excess_positive["t_stat"],
        "p_value_excess": excess_positive["p_value"],
        "regime_unknown_count": int(frame["market_regime"].eq("unknown").sum()) if "market_regime" in frame.columns else 0,
    }
    if extra:
        row.update(extra)
    return row


def build_review_markdown(overall: pd.DataFrame, by_sector: pd.DataFrame, by_regime: pd.DataFrame) -> str:
    lines = [
        "# Phase 4 Event Caution Review",
        "",
        "This pass freezes the forward-actionable corporate caution families and reports their exact validation numbers.",
        "",
    ]

    for row in overall.to_dict("records"):
        sector_rows = by_sector[by_sector["rule_key"] == row["rule_key"]]
        regime_rows = by_regime[by_regime["rule_key"] == row["rule_key"]]

        lines.extend(
            [
                f"## {row['rule_name']}",
                "",
                f"- Rule key: `{row['rule_key']}`",
                f"- Event types: `{row['event_types']}`",
                f"- Trigger: `{row['date_field']}`",
                f"- Window: `{row['window_label']}`",
                f"- Scope hint: {row['scope_hint']}",
                "",
                "### Overall",
                "",
                f"- Cases: `{int(row['count'])}` across `{int(row['symbol_count'])}` symbols",
                f"- Mean event return: `{row['mean_event_return']:.2f}%`",
                f"- Mean baseline return: `{row['mean_baseline_return']:.2f}%`",
                f"- Mean excess return: `{row['mean_excess_return']:.2f}%`",
                f"- Raw negative hit rate: `{row['raw_negative_hit_rate']:.1%}`",
                f"- Adjusted negative hit rate: `{row['adjusted_negative_hit_rate']:.1%}`",
                f"- p-value: `{row['p_value_excess']:.4f}`",
                "",
                "### By Sector",
                "",
                table_or_empty(
                    sector_rows,
                    ["sector", "count", "mean_excess_return", "adjusted_negative_hit_rate", "p_value_excess"],
                ),
                "",
                "### By Regime",
                "",
                table_or_empty(
                    regime_rows,
                    ["market_regime", "count", "mean_excess_return", "adjusted_negative_hit_rate", "p_value_excess"],
                ),
                "",
            ]
        )

    return "\n".join(lines)


def table_or_empty(frame: pd.DataFrame, columns: list[str]) -> str:
    if frame.empty:
        return "_No rows available._"

    header = "| " + " | ".join(columns) + " |"
    separator = "|" + "|".join("---" for _ in columns) + "|"
    rows = [header, separator]
    for row in frame[columns].to_dict("records"):
        rendered = []
        for column in columns:
            value = row.get(column)
            if isinstance(value, float):
                if "hit_rate" in column:
                    rendered.append(f"{value:.1%}")
                elif "p_value" in column:
                    rendered.append(f"{value:.4f}")
                else:
                    rendered.append(f"{value:.2f}")
            else:
                rendered.append(str(value))
        rows.append("| " + " | ".join(rendered) + " |")
    return "\n".join(rows)


if __name__ == "__main__":
    main()
