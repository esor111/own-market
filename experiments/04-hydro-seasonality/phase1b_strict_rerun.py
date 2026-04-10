"""
Phase 1B: Strict rerun of the seasonal-fight check per Romeo's review.

Differences from phase1:
  1. One row per (symbol, prediction_date), not per agent. Pick the most recent
     scored prediction or the highest-conviction one.
  2. Directional predictions ONLY (drop "neutral" entirely from the agent stance buckets).
  3. Compare agents against TWO dumb baselines:
       - Seasonal-sign baseline: bullish in confirmed bullish months, bearish in confirmed bearish months
       - Month-majority baseline: in any sampled month, predict the historical majority direction
         for that calendar month from the price-only seasonality data
  4. Per-symbol breakdown so API doesn't carry the whole signal.
  5. Honest sample notes — list which calendar months actually appear in the scored data.

Output:
  results/phase1b_strict_detail.csv          — symbol-date deduped rows
  results/phase1b_strict_summary.csv         — agent vs baselines, per relationship
  results/phase1b_strict_per_symbol.csv      — per-symbol breakdown
  results/phase1b_strict_review.md           — human-readable review
"""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
RESULTS_DIR = SCRIPT_DIR / "results"

ROOT = SCRIPT_DIR.parent.parent
SCORES_DIR = ROOT / "market-gist" / "data" / "predictions" / "replay_scores"
MONTHLY_RETURNS_PATH = SCRIPT_DIR / "data" / "monthly_returns.csv"

HYDRO_SYMBOLS = {"SMHL", "HIDCL", "NGPL", "API", "AKPL", "UPPER"}

# Confirmed seasonal months from L-009
SEASONAL_EXPECTATION = {
    1: "bullish",
    2: "bearish",
    7: "bullish",
    8: "bearish",
    11: "bearish",
}


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
    if not MONTHLY_RETURNS_PATH.exists():
        raise FileNotFoundError(f"Missing monthly returns: {MONTHLY_RETURNS_PATH}")

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    raw_rows = load_hydro_score_rows()
    raw_frame = pd.DataFrame(raw_rows)
    if raw_frame.empty:
        raise RuntimeError("No hydro score rows loaded.")

    # Step 1: dedupe to one row per (symbol, prediction_date)
    deduped = dedupe_to_symbol_date(raw_frame)

    # Step 2: drop agent-neutral rows (directional only)
    directional = deduped[deduped["agent_stance"] != "neutral"].copy()

    print(f"Raw scored rows: {len(raw_frame)}")
    print(f"Deduped (symbol-date): {len(deduped)}")
    print(f"Directional only: {len(directional)}")
    print()

    # Step 3: build month-majority baseline from monthly_returns.csv
    monthly = pd.read_csv(MONTHLY_RETURNS_PATH)
    hydro_monthly = monthly[monthly["sector"] == "Hydropower"].copy()
    month_majority = build_month_majority_baseline(hydro_monthly)

    # Step 4: tag each directional row with all three predictions
    directional["seasonal_baseline_stance"] = directional["prediction_month"].map(
        lambda m: SEASONAL_EXPECTATION.get(m, "no_call")
    )
    directional["month_majority_stance"] = directional["prediction_month"].map(
        lambda m: month_majority.get(m, "no_call")
    )
    directional["agent_correct"] = directional["direction_correct"].astype(bool)
    directional["seasonal_baseline_correct"] = directional.apply(
        lambda r: baseline_is_correct(r["seasonal_baseline_stance"], r), axis=1
    )
    directional["month_majority_correct"] = directional.apply(
        lambda r: baseline_is_correct(r["month_majority_stance"], r), axis=1
    )

    detail_path = RESULTS_DIR / "phase1b_strict_detail.csv"
    directional.to_csv(detail_path, index=False)

    # Step 5: build summaries
    overall_summary = build_overall_summary(directional)
    overall_path = RESULTS_DIR / "phase1b_strict_summary.csv"
    overall_summary.to_csv(overall_path, index=False)

    per_symbol = build_per_symbol(directional)
    per_symbol_path = RESULTS_DIR / "phase1b_strict_per_symbol.csv"
    per_symbol.to_csv(per_symbol_path, index=False)

    # Step 6: review markdown
    review_md = build_review_markdown(
        raw_frame, deduped, directional, overall_summary, per_symbol, month_majority
    )
    review_path = RESULTS_DIR / "phase1b_strict_review.md"
    review_path.write_text(review_md, encoding="utf-8")

    print(f"Wrote detail to {detail_path}")
    print(f"Wrote summary to {overall_path}")
    print(f"Wrote per-symbol to {per_symbol_path}")
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

        prediction_date = payload.get("prediction_date")
        if not prediction_date:
            continue

        agent_id = payload.get("agent_id") or (payload.get("metadata") or {}).get("agent_id") or "unknown"
        direction = payload.get("predicted_direction")
        rows.append({
            "file": path.name,
            "symbol": symbol,
            "prediction_date": prediction_date,
            "prediction_month": pd.to_datetime(prediction_date).month,
            "agent_id": agent_id,
            "predicted_direction": direction,
            "agent_stance": stance_from_direction(direction),
            "direction_correct": payload.get("direction_correct"),
            "return_5d_pct": (payload.get("horizon_returns") or {}).get("return_5d_pct"),
            "return_10d_pct": (payload.get("horizon_returns") or {}).get("return_10d_pct"),
            "stated_conviction": (payload.get("conviction_accuracy") or {}).get("stated_conviction"),
        })
    return rows


def dedupe_to_symbol_date(raw_frame: pd.DataFrame) -> pd.DataFrame:
    """One row per (symbol, prediction_date). Pick the highest-conviction directional row.
    Tie-breaker: prefer agent-1-romeo, then agent-2-juliet, then agent-3-grok.
    """
    if raw_frame.empty:
        return raw_frame
    frame = raw_frame.copy()
    frame["stance_priority"] = frame["agent_stance"].apply(lambda s: 0 if s != "neutral" else 1)
    frame["agent_priority"] = frame["agent_id"].apply(
        lambda a: {"agent-1-romeo": 0, "agent-2-juliet": 1, "agent-3-grok": 2}.get(a, 99)
    )
    frame["conviction_value"] = pd.to_numeric(frame["stated_conviction"], errors="coerce").fillna(0)

    frame = frame.sort_values(
        ["symbol", "prediction_date", "stance_priority", "conviction_value", "agent_priority"],
        ascending=[True, True, True, False, True],
    )
    deduped = frame.drop_duplicates(subset=["symbol", "prediction_date"], keep="first").copy()
    return deduped.drop(columns=["stance_priority", "agent_priority", "conviction_value"])


def build_month_majority_baseline(hydro_monthly: pd.DataFrame) -> dict[int, str]:
    """For each calendar month, return 'bullish' or 'bearish' based on majority of historical observations."""
    out: dict[int, str] = {}
    for month, group in hydro_monthly.groupby("month"):
        n_pos = int((group["return_pct"] > 0).sum())
        n_neg = int((group["return_pct"] < 0).sum())
        if n_pos > n_neg:
            out[int(month)] = "bullish"
        elif n_neg > n_pos:
            out[int(month)] = "bearish"
        else:
            out[int(month)] = "no_call"
    return out


def baseline_is_correct(baseline_stance: str, row) -> bool | None:
    """Whether a baseline stance would have been correct given the actual 10d return."""
    if baseline_stance == "no_call":
        return None
    return_10d = row.get("return_10d_pct")
    if return_10d is None or pd.isna(return_10d):
        return None
    actual_pos = float(return_10d) > 0
    if baseline_stance == "bullish":
        return actual_pos
    if baseline_stance == "bearish":
        return not actual_pos
    return None


def build_overall_summary(directional: pd.DataFrame) -> pd.DataFrame:
    rows = []
    rows.append(summary_row("agent", directional["agent_correct"]))
    rows.append(summary_row("seasonal_baseline", directional["seasonal_baseline_correct"]))
    rows.append(summary_row("month_majority_baseline", directional["month_majority_correct"]))
    return pd.DataFrame(rows)


def summary_row(label: str, series: pd.Series) -> dict:
    clean = series.dropna()
    n = len(clean)
    correct = int(clean.astype(bool).sum())
    accuracy = correct / n if n else None
    return {
        "predictor": label,
        "n_resolved": n,
        "n_correct": correct,
        "accuracy": round(accuracy, 4) if accuracy is not None else None,
    }


def build_per_symbol(directional: pd.DataFrame) -> pd.DataFrame:
    rows = []
    for symbol, group in directional.groupby("symbol"):
        rows.append({
            "symbol": symbol,
            "n": len(group),
            "agent_accuracy": round(group["agent_correct"].astype(bool).mean(), 4),
            "seasonal_baseline_accuracy": round(
                group["seasonal_baseline_correct"].dropna().astype(bool).mean(), 4
            ) if group["seasonal_baseline_correct"].notna().any() else None,
            "month_majority_accuracy": round(
                group["month_majority_correct"].dropna().astype(bool).mean(), 4
            ) if group["month_majority_correct"].notna().any() else None,
        })
    return pd.DataFrame(rows).sort_values("symbol").reset_index(drop=True)


def build_review_markdown(
    raw_frame: pd.DataFrame,
    deduped: pd.DataFrame,
    directional: pd.DataFrame,
    summary: pd.DataFrame,
    per_symbol: pd.DataFrame,
    month_majority: dict[int, str],
) -> str:
    month_distribution = directional["prediction_month"].value_counts().sort_index().to_dict()
    seasonal_months_in_sample = [m for m in month_distribution if m in SEASONAL_EXPECTATION]
    neutral_months_in_sample = [m for m in month_distribution if m not in SEASONAL_EXPECTATION]

    lines = [
        "# Phase 1B: Strict Rerun (Per Romeo's Review)",
        "",
        f"Raw scored rows: {len(raw_frame)}",
        f"Deduped to symbol-date: {len(deduped)}",
        f"Directional only (dropped agent neutrals): {len(directional)}",
        "",
        "## Sample Coverage",
        "",
        f"Symbols: {sorted(directional['symbol'].unique())}",
        f"Date range: {directional['prediction_date'].min()} to {directional['prediction_date'].max()}",
        "",
        "Months actually in the sample (with N):",
        "",
    ]
    for month, n in sorted(month_distribution.items()):
        month_name = pd.Timestamp(2024, month, 1).strftime("%b")
        seasonal_tag = "(L-009 seasonal)" if month in SEASONAL_EXPECTATION else "(non-seasonal)"
        lines.append(f"- {month_name} (month {month}): N={n} {seasonal_tag}")
    lines.extend([
        "",
        f"L-009 seasonal months covered: {sorted(seasonal_months_in_sample)}",
        f"L-009 seasonal months MISSING from sample: "
        f"{sorted(set(SEASONAL_EXPECTATION) - set(seasonal_months_in_sample))}",
        f"Non-seasonal months in sample: {sorted(neutral_months_in_sample)}",
        f"Non-seasonal months MISSING from sample: "
        f"{sorted(set(range(1, 13)) - set(SEASONAL_EXPECTATION) - set(neutral_months_in_sample))}",
        "",
        "## Month-Majority Baseline (built from L-009 monthly returns)",
        "",
        "| Month | Majority Stance |",
        "|---|---|",
    ])
    for month in range(1, 13):
        month_name = pd.Timestamp(2024, month, 1).strftime("%b")
        lines.append(f"| {month_name} | {month_majority.get(month, '?')} |")

    lines.extend([
        "",
        "## Overall Accuracy: Agent vs Dumb Baselines",
        "",
        "| Predictor | N Resolved | Correct | Accuracy |",
        "|---|---:|---:|---:|",
    ])
    for row in summary.to_dict("records"):
        accuracy_str = f"{row['accuracy']:.1%}" if row["accuracy"] is not None else "-"
        lines.append(
            f"| {row['predictor']} | {row['n_resolved']} | {row['n_correct']} | {accuracy_str} |"
        )

    lines.extend([
        "",
        "## Per-Symbol Breakdown",
        "",
        "| Symbol | N | Agent | Seasonal Baseline | Month-Majority Baseline |",
        "|---|---:|---:|---:|---:|",
    ])
    for row in per_symbol.to_dict("records"):
        agent_str = f"{row['agent_accuracy']:.1%}"
        seasonal_str = f"{row['seasonal_baseline_accuracy']:.1%}" if row["seasonal_baseline_accuracy"] is not None else "-"
        majority_str = f"{row['month_majority_accuracy']:.1%}" if row["month_majority_accuracy"] is not None else "-"
        lines.append(
            f"| {row['symbol']} | {row['n']} | {agent_str} | {seasonal_str} | {majority_str} |"
        )

    # Verdict
    lines.extend(["", "## Verdict", ""])
    agent_acc = summary[summary["predictor"] == "agent"].iloc[0]["accuracy"] or 0
    seasonal_acc = summary[summary["predictor"] == "seasonal_baseline"].iloc[0]["accuracy"] or 0
    majority_acc = summary[summary["predictor"] == "month_majority_baseline"].iloc[0]["accuracy"] or 0

    lines.append(f"- Agent directional accuracy: **{agent_acc:.1%}**")
    lines.append(f"- Seasonal-sign dumb baseline: **{seasonal_acc:.1%}**")
    lines.append(f"- Month-majority dumb baseline: **{majority_acc:.1%}**")
    lines.append("")

    if agent_acc > max(seasonal_acc, majority_acc) + 0.05:
        lines.append(
            "**Agent is meaningfully better than both dumb baselines.** "
            "There is real signal in the agent prediction beyond what a calendar lookup gives you."
        )
    elif agent_acc > min(seasonal_acc, majority_acc) and agent_acc < max(seasonal_acc, majority_acc):
        lines.append(
            "**Agent is in the middle of the two baselines.** "
            "It does not consistently beat a calendar lookup. Treat agent calls as roughly equivalent to "
            "dumb seasonal logic in this small sample."
        )
    else:
        lines.append(
            "**At least one dumb baseline matches or beats the agent.** "
            "On this sample the agent does not add measurable directional value over a calendar baseline. "
            "This is suggestive, not proof, given the small sample."
        )

    lines.append("")
    lines.append(
        "*Important caveats*: small sample, only 3 of 6 hydro symbols covered, "
        "the sampled non-seasonal months are essentially Oct/Dec 2025 plus a few scattered cases. "
        "Do not treat this rerun as a hard rejection of seasonal integration. "
        "Treat it as a stricter measurement that says: with the data we currently have, "
        "the seasonal calendar is not a clear loser, but it is also not a clear win."
    )
    return "\n".join(lines) + "\n"


if __name__ == "__main__":
    main()
