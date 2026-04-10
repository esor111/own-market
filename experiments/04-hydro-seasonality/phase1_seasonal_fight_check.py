"""
Phase 1 sanity check for hydropower seasonality integration.

Question: Are agent hydropower errors correlated with fighting the seasonal calendar?

Logic:
  1. Load all scored hydro predictions from market-gist/data/predictions/replay_scores/
  2. Tag each by the seasonal expectation for its prediction month
  3. For each prediction, compute:
     - Was the agent fighting the seasonal? (e.g. predicted bearish in Jan)
     - Was the prediction correct?
  4. Compare hit rate when AGREEING with the seasonal vs when FIGHTING the seasonal.

If agents perform much worse when fighting the calendar, the seasonal IS the cause
of the 14% accuracy problem and the seasonal context is worth integrating.

If they perform similarly in both buckets, the seasonal isn't the right fix and we
should not build seasonal annotations into the system.

Output:
  results/phase1_seasonal_fight_summary.csv
  results/phase1_seasonal_fight_review.md
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "results"

# market-gist replay_scores directory
ROOT = SCRIPT_DIR.parent.parent
SCORES_DIR = ROOT / "market-gist" / "data" / "predictions" / "replay_scores"

HYDRO_SYMBOLS = {"SMHL", "HIDCL", "NGPL", "API", "AKPL", "UPPER"}

# Seasonal expectations from L-009 (5 confirmed months)
# Months not listed are NEUTRAL — no strong directional expectation.
SEASONAL_EXPECTATION = {
    1: "bullish",     # Jan: 89% positive, +12.0%
    2: "bearish",     # Feb: 82% negative, -5.25%
    7: "bullish",     # Jul: 70% positive, +9.35%
    8: "bearish",     # Aug: 78% negative, -6.78%
    11: "bearish",    # Nov: 71% negative, -2.31%
}

# How agent direction maps to a seasonal stance
def stance_from_direction(direction: str) -> str:
    direction = (direction or "").strip().lower()
    if direction == "bullish":
        return "bullish"
    if direction == "bearish":
        return "bearish"
    return "neutral"


def main() -> None:
    if not SCORES_DIR.exists():
        raise FileNotFoundError(f"Scores dir not found: {SCORES_DIR}")

    rows = load_hydro_score_rows()
    if not rows:
        raise RuntimeError("No hydro score files found.")

    frame = pd.DataFrame(rows)
    print(f"Loaded {len(frame)} hydro predictions across {frame['symbol'].nunique()} symbols")
    print(f"Agents: {frame['agent_id'].value_counts().to_dict()}")
    print(f"Date range: {frame['prediction_date'].min()} to {frame['prediction_date'].max()}")
    print()

    # Tag each row with the seasonal stance for its month and whether the agent fought it
    frame["prediction_month"] = pd.to_datetime(frame["prediction_date"]).dt.month
    frame["seasonal_stance"] = frame["prediction_month"].map(SEASONAL_EXPECTATION).fillna("neutral")
    frame["agent_stance"] = frame["predicted_direction"].apply(stance_from_direction)
    frame["seasonal_relationship"] = frame.apply(classify_seasonal_relationship, axis=1)

    # Save the per-row tagged dataset
    detail_path = RESULTS_DIR / "phase1_seasonal_fight_detail.csv"
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    frame.to_csv(detail_path, index=False)

    # Build the summary
    summary = build_summary(frame)
    summary_path = RESULTS_DIR / "phase1_seasonal_fight_summary.csv"
    summary.to_csv(summary_path, index=False)

    # Per-agent breakdown
    agent_summary = build_agent_summary(frame)
    agent_summary_path = RESULTS_DIR / "phase1_seasonal_fight_by_agent.csv"
    agent_summary.to_csv(agent_summary_path, index=False)

    # Markdown review
    review_md = build_review_markdown(frame, summary, agent_summary)
    review_path = RESULTS_DIR / "phase1_seasonal_fight_review.md"
    review_path.write_text(review_md, encoding="utf-8")

    print(f"Wrote detail rows to {detail_path}")
    print(f"Wrote summary to {summary_path}")
    print(f"Wrote agent summary to {agent_summary_path}")
    print(f"Wrote review to {review_path}")


def load_hydro_score_rows() -> list[dict]:
    rows = []
    for path in sorted(SCORES_DIR.glob("*__score_v1.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue

        symbol = str(payload.get("symbol") or "").upper().strip()
        if symbol not in HYDRO_SYMBOLS:
            continue

        rows.append({
            "file": path.name,
            "symbol": symbol,
            "prediction_date": payload.get("prediction_date"),
            "agent_id": payload.get("agent_id") or payload.get("metadata", {}).get("agent_id"),
            "predicted_action": payload.get("predicted_action"),
            "predicted_direction": payload.get("predicted_direction"),
            "direction_correct": payload.get("direction_correct"),
            "action_verdict": payload.get("action_verdict"),
            "return_5d_pct": (payload.get("horizon_returns") or {}).get("return_5d_pct"),
            "return_10d_pct": (payload.get("horizon_returns") or {}).get("return_10d_pct"),
            "stated_conviction": (payload.get("conviction_accuracy") or {}).get("stated_conviction"),
        })

    return rows


def classify_seasonal_relationship(row) -> str:
    seasonal = row["seasonal_stance"]
    agent = row["agent_stance"]

    if seasonal == "neutral":
        return "no_seasonal"
    if agent == "neutral":
        return "agent_neutral_in_seasonal"
    if agent == seasonal:
        return "agreeing_with_seasonal"
    return "fighting_seasonal"


def build_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for relationship, group in frame.groupby("seasonal_relationship", dropna=False):
        resolved = group[group["direction_correct"].notna()]
        n = len(resolved)
        n_correct = int(resolved["direction_correct"].astype(bool).sum()) if n else 0
        accuracy = n_correct / n if n else None

        # Mean 10-day return when prediction was bullish vs bearish
        bullish = resolved[resolved["agent_stance"] == "bullish"]
        bearish = resolved[resolved["agent_stance"] == "bearish"]

        rows.append({
            "seasonal_relationship": relationship,
            "n": n,
            "n_correct": n_correct,
            "direction_accuracy": accuracy,
            "n_bullish_predictions": len(bullish),
            "n_bearish_predictions": len(bearish),
            "mean_10d_return_pct": (
                resolved["return_10d_pct"].astype(float).mean()
                if not resolved["return_10d_pct"].dropna().empty
                else None
            ),
        })

    return pd.DataFrame(rows).sort_values("seasonal_relationship").reset_index(drop=True)


def build_agent_summary(frame: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for (agent, relationship), group in frame.groupby(["agent_id", "seasonal_relationship"], dropna=False):
        resolved = group[group["direction_correct"].notna()]
        n = len(resolved)
        n_correct = int(resolved["direction_correct"].astype(bool).sum()) if n else 0
        accuracy = n_correct / n if n else None
        rows.append({
            "agent_id": agent,
            "seasonal_relationship": relationship,
            "n": n,
            "n_correct": n_correct,
            "direction_accuracy": accuracy,
        })

    return pd.DataFrame(rows).sort_values(["agent_id", "seasonal_relationship"]).reset_index(drop=True)


def build_review_markdown(frame: pd.DataFrame, summary: pd.DataFrame, agent_summary: pd.DataFrame) -> str:
    lines = [
        "# Phase 1: Are Hydro Errors Correlated With Fighting The Seasonal?",
        "",
        f"Sample: {len(frame)} hydropower predictions across "
        f"{frame['symbol'].nunique()} symbols and {frame['agent_id'].nunique()} agents.",
        f"Date range: {frame['prediction_date'].min()} to {frame['prediction_date'].max()}",
        "",
        "## Seasonal Calendar (from L-009)",
        "",
        "| Month | Expected Stance |",
        "|---|---|",
    ]
    for month, stance in sorted(SEASONAL_EXPECTATION.items()):
        month_name = pd.Timestamp(2024, month, 1).strftime("%b")
        lines.append(f"| {month_name} | {stance} |")
    lines.append("| All other months | neutral (no strong expectation) |")
    lines.append("")

    lines.extend([
        "## Overall Direction Accuracy By Seasonal Relationship",
        "",
        "| Relationship | N | Correct | Accuracy | Bullish Preds | Bearish Preds | Mean 10D Return |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for row in summary.to_dict("records"):
        accuracy_str = f"{row['direction_accuracy']:.1%}" if row["direction_accuracy"] is not None else "-"
        ret_str = f"{row['mean_10d_return_pct']:.2f}%" if row["mean_10d_return_pct"] is not None else "-"
        lines.append(
            f"| {row['seasonal_relationship']} | {row['n']} | {row['n_correct']} | "
            f"{accuracy_str} | {row['n_bullish_predictions']} | {row['n_bearish_predictions']} | {ret_str} |"
        )
    lines.append("")

    lines.extend([
        "## Per-Agent Breakdown",
        "",
        "| Agent | Relationship | N | Correct | Accuracy |",
        "|---|---|---:|---:|---:|",
    ])
    for row in agent_summary.to_dict("records"):
        accuracy_str = f"{row['direction_accuracy']:.1%}" if row["direction_accuracy"] is not None else "-"
        lines.append(
            f"| {row['agent_id']} | {row['seasonal_relationship']} | {row['n']} | "
            f"{row['n_correct']} | {accuracy_str} |"
        )
    lines.append("")

    # Verdict section
    lines.extend(["## Verdict", ""])
    fighting = summary[summary["seasonal_relationship"] == "fighting_seasonal"]
    agreeing = summary[summary["seasonal_relationship"] == "agreeing_with_seasonal"]

    if not fighting.empty and not agreeing.empty:
        f_acc = fighting.iloc[0]["direction_accuracy"] or 0
        a_acc = agreeing.iloc[0]["direction_accuracy"] or 0
        f_n = fighting.iloc[0]["n"]
        a_n = agreeing.iloc[0]["n"]
        gap = a_acc - f_acc
        gap_label = "in favor of agreeing" if gap >= 0 else "in favor of fighting"

        lines.append(f"- Agreeing with seasonal: **{a_acc:.1%}** accuracy (N={a_n})")
        lines.append(f"- Fighting seasonal: **{f_acc:.1%}** accuracy (N={f_n})")
        lines.append(f"- Gap: **{gap:+.1%}** {gap_label}")
        lines.append("")

        if a_n < 10 or f_n < 10:
            lines.append(
                "**INSUFFICIENT DATA:** Either bucket has fewer than 10 cases. "
                "Cannot make a directional claim about whether agents fight the calendar. "
                "Report buckets as appendix only."
            )
        elif gap >= 0.15:
            lines.append(
                "**CONFIRMED:** Agents perform meaningfully better when agreeing with the seasonal. "
                "The seasonal calendar IS a likely cause of hydro errors. Proceed to Phase 2."
            )
        elif gap >= 0.05:
            lines.append(
                "**WEAK SIGNAL:** Some directional improvement when agreeing, but the gap is small. "
                "Worth annotating but do not promote to a hard rule yet."
            )
        else:
            lines.append(
                "**NOT SUPPORTED:** Fighting the seasonal does not predict errors at meaningful sample sizes. "
                "The seasonal is unlikely to be the dominant cause of the hydro accuracy problem."
            )

    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
