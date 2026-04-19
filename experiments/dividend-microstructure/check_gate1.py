"""
Dividend Microstructure — Step 1B: Gate 1 Sample Adequacy Check

Reads event_table.csv (produced by build_event_table.py) and applies the
Gate 1 criteria from PRE_REGISTRATION.md revision 3:

  - Cohort A N >= 80 events
  - Cohort A unique T_ex calendar dates >= 30
  - Cohort A top-3 T_ex date concentration <= 30%
  - Cohort B N >= 20 (soft flag; attribution feasibility)
  - Notice -> T_ex gap distribution documented

Produces a decision memo. Outputs:
  data/gate1_decision.json
  data/gate1_decision.md

Usage:
    python experiments/dividend-microstructure/check_gate1.py
"""
from __future__ import annotations

import csv
import json
import os
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
EVENT_TABLE = SCRIPT_DIR / "data" / "event_table.csv"
OUTPUT_DIR = SCRIPT_DIR / "data"
DECISION_JSON = OUTPUT_DIR / "gate1_decision.json"
DECISION_MD = OUTPUT_DIR / "gate1_decision.md"

# Gate 1 thresholds from PRE_REGISTRATION revision 3
GATE1_MIN_N = 80
GATE1_MIN_UNIQUE_DATES = 30
GATE1_MAX_TOP3_SHARE = 0.30
GATE1_COHORT_B_SOFT_MIN = 20


def load_events() -> list[dict]:
    if not EVENT_TABLE.exists():
        raise SystemExit(
            f"Event table not found at {EVENT_TABLE}. "
            "Run build_event_table.py first."
        )
    with EVENT_TABLE.open("r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return [row for row in reader]


def cohort_stats(cohort_rows: list[dict]) -> dict:
    n = len(cohort_rows)
    t_exes = [r["t_ex"] for r in cohort_rows if r.get("t_ex")]
    date_counts = Counter(t_exes)
    unique_dates = len(date_counts)

    total = n or 1
    sorted_counts = sorted(date_counts.values(), reverse=True)
    top1 = sorted_counts[0] / total if sorted_counts else 0.0
    top3 = sum(sorted_counts[:3]) / total if sorted_counts else 0.0
    top5 = sum(sorted_counts[:5]) / total if sorted_counts else 0.0

    sectors = Counter(r["sector"] for r in cohort_rows)
    event_types = Counter(r["event_type"] for r in cohort_rows)
    bonus_components = sum(1 for r in cohort_rows if r.get("has_bonus_component") == "True")

    return {
        "n": n,
        "unique_t_ex_dates": unique_dates,
        "top1_share": round(top1, 3),
        "top3_share": round(top3, 3),
        "top5_share": round(top5, 3),
        "date_distribution_top_10": dict(date_counts.most_common(10)),
        "sector_distribution": dict(sectors),
        "event_type_distribution": dict(event_types),
        "events_with_bonus_component": bonus_components,
        "pure_cash_dividend_count": n - bonus_components,
    }


def gap_distribution(cohort_b_rows: list[dict]) -> dict:
    gaps = []
    for row in cohort_b_rows:
        g = row.get("notice_to_t_ex_gap_trading_days", "")
        if g == "":
            continue
        try:
            gaps.append(int(g))
        except ValueError:
            continue

    if not gaps:
        return {"count": 0}

    gaps.sort()
    n = len(gaps)
    median = gaps[n // 2]
    p25 = gaps[n // 4]
    p75 = gaps[(3 * n) // 4]

    within_5 = sum(1 for g in gaps if abs(g) <= 5)
    within_10 = sum(1 for g in gaps if abs(g) <= 10)
    within_15 = sum(1 for g in gaps if abs(g) <= 15)

    return {
        "count": n,
        "min": gaps[0],
        "max": gaps[-1],
        "p25": p25,
        "median": median,
        "p75": p75,
        "share_within_5_trading_days": round(within_5 / n, 3),
        "share_within_10_trading_days": round(within_10 / n, 3),
        "share_within_15_trading_days": round(within_15 / n, 3),
    }


def apply_gate1(cohort_a_stats: dict, cohort_b_n: int, overlap_rate: float) -> tuple[str, list[str]]:
    checks: list[str] = []
    verdict = "PASS"

    if cohort_a_stats["n"] < GATE1_MIN_N:
        verdict = "FAIL"
        checks.append(
            f"FAIL: Cohort A N = {cohort_a_stats['n']} < required {GATE1_MIN_N}"
        )
    else:
        checks.append(f"PASS: Cohort A N = {cohort_a_stats['n']} >= {GATE1_MIN_N}")

    if cohort_a_stats["unique_t_ex_dates"] < GATE1_MIN_UNIQUE_DATES:
        verdict = "FAIL"
        checks.append(
            f"FAIL: Cohort A unique T_ex dates = {cohort_a_stats['unique_t_ex_dates']} "
            f"< required {GATE1_MIN_UNIQUE_DATES}"
        )
    else:
        checks.append(
            f"PASS: Cohort A unique T_ex dates = {cohort_a_stats['unique_t_ex_dates']} "
            f">= {GATE1_MIN_UNIQUE_DATES}"
        )

    if cohort_a_stats["top3_share"] > GATE1_MAX_TOP3_SHARE:
        verdict = "FAIL"
        checks.append(
            f"FAIL: Cohort A top-3 T_ex date concentration = "
            f"{cohort_a_stats['top3_share']:.1%} > max {GATE1_MAX_TOP3_SHARE:.0%}"
        )
    else:
        checks.append(
            f"PASS: Cohort A top-3 T_ex date concentration = "
            f"{cohort_a_stats['top3_share']:.1%} <= {GATE1_MAX_TOP3_SHARE:.0%}"
        )

    # Soft flag
    if cohort_b_n < GATE1_COHORT_B_SOFT_MIN:
        checks.append(
            f"FLAG (soft): Cohort B N = {cohort_b_n} < recommended {GATE1_COHORT_B_SOFT_MIN} "
            "— attribution evidence will be thin"
        )
    else:
        checks.append(
            f"OK (soft): Cohort B N = {cohort_b_n} >= {GATE1_COHORT_B_SOFT_MIN}"
        )

    # Independence disclosure
    if overlap_rate >= 0.50:
        checks.append(
            f"FLAG: Overlap rate {overlap_rate:.1%} >= 50% — "
            "per PRE_REGISTRATION Gate 2, label any downstream Cohort A result as "
            "'structurally weak independence'"
        )
    else:
        checks.append(
            f"OK: Overlap rate {overlap_rate:.1%} < 50%"
        )

    return verdict, checks


def build_decision() -> dict:
    events = load_events()
    cohort_a_rows = [r for r in events if r.get("cohort") == "A"]
    cohort_b_rows = [r for r in events if r.get("cohort") == "B"]

    total = len(events) or 1
    overlap_rate = len(cohort_b_rows) / total

    a_stats = cohort_stats(cohort_a_rows)
    b_stats = cohort_stats(cohort_b_rows)
    b_gap_dist = gap_distribution(cohort_b_rows)

    verdict, checks = apply_gate1(a_stats, b_stats["n"], overlap_rate)

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "event_table": str(EVENT_TABLE),
        "pre_registration_revision": "3",
        "gate1_thresholds": {
            "cohort_a_min_n": GATE1_MIN_N,
            "cohort_a_min_unique_dates": GATE1_MIN_UNIQUE_DATES,
            "cohort_a_max_top3_share": GATE1_MAX_TOP3_SHARE,
            "cohort_b_soft_min_n": GATE1_COHORT_B_SOFT_MIN,
        },
        "verdict": verdict,
        "checks": checks,
        "total_events": len(events),
        "overlap_rate": round(overlap_rate, 3),
        "cohort_a": a_stats,
        "cohort_b": b_stats,
        "cohort_b_notice_to_t_ex_gap_distribution": b_gap_dist,
    }


def format_markdown(decision: dict) -> str:
    a = decision["cohort_a"]
    b = decision["cohort_b"]
    bg = decision["cohort_b_notice_to_t_ex_gap_distribution"]
    lines = [
        "[EXPERIMENTAL TOOL] Gate 1 decision memo for dividend-microstructure sandbox.",
        "Historical-test sample, not forward evidence.",
        "PRE_REGISTRATION revision 3.",
        "",
        "# Gate 1 Decision",
        "",
        f"- Generated: {decision['generated_at']}",
        f"- **Verdict: `{decision['verdict']}`**",
        f"- Total events after overlap-drop: {decision['total_events']}",
        f"- Overlap rate (Cohort B / total): {decision['overlap_rate']:.1%}",
        "",
        "## Check-By-Check Result",
        "",
    ]
    for c in decision["checks"]:
        lines.append(f"- {c}")

    lines.extend([
        "",
        "## Cohort A — Pure Date-Led",
        "",
        f"- N: **{a['n']}** (gate: >= {decision['gate1_thresholds']['cohort_a_min_n']})",
        f"- Unique T_ex dates: **{a['unique_t_ex_dates']}** (gate: >= {decision['gate1_thresholds']['cohort_a_min_unique_dates']})",
        f"- Top-1 date share: {a['top1_share']:.1%}",
        f"- Top-3 date share: **{a['top3_share']:.1%}** (gate: <= {decision['gate1_thresholds']['cohort_a_max_top3_share']:.0%})",
        f"- Top-5 date share: {a['top5_share']:.1%}",
        f"- Sector breakdown: {a['sector_distribution']}",
        f"- Event-type breakdown: {a['event_type_distribution']}",
        f"- Pure cash dividend (no bonus component): {a['pure_cash_dividend_count']}",
        f"- Compound bonus+cash dividend: {a['events_with_bonus_component']}",
        "",
        "## Cohort B — Notice-Overlap (L-001 notice within +/-10 trading days of T_ex)",
        "",
        f"- N: **{b['n']}**",
        f"- Unique T_ex dates: {b['unique_t_ex_dates']}",
        f"- Sector breakdown: {b['sector_distribution']}",
        f"- Event-type breakdown: {b['event_type_distribution']}",
        "",
        "### Notice -> T_ex Gap Distribution (trading days)",
        "",
    ])
    if bg["count"] > 0:
        lines.extend([
            f"- Count with gap data: {bg['count']}",
            f"- Min / Max: {bg['min']} / {bg['max']}",
            f"- Quartiles (p25 / median / p75): {bg['p25']} / {bg['median']} / {bg['p75']}",
            f"- Share within +/-5 trading days: {bg['share_within_5_trading_days']:.1%}",
            f"- Share within +/-10 trading days: {bg['share_within_10_trading_days']:.1%}",
            f"- Share within +/-15 trading days: {bg['share_within_15_trading_days']:.1%}",
        ])
    else:
        lines.append("- No notice gap data available")

    lines.extend([
        "",
        "## Interpretation",
        "",
    ])

    if decision["verdict"] == "PASS":
        lines.extend([
            "- Gate 1 passes. The experiment can proceed to Step 2 (run_h1.py).",
            "- Write PRE_REGISTRATION into git commit before running H1 if not already done.",
            "- Proceed with date-cluster block-bootstrap H1 test on Cohort A.",
        ])
    else:
        lines.extend([
            "- **Gate 1 FAILS.** Per PRE_REGISTRATION revision 3, the lane is killed.",
            "- Do not run `run_h1.py`. Do not promote any finding from the event table.",
            "- The failure is informative: the event universe for book-closure-date analysis on NEPSE banks+hydros is small AND heavily overlapping with existing L-001 notice events.",
            "- Specifically: ~71% of cash-dividend events have an L-001 notice within +/-10 trading days of T_ex, meaning the two anchors measure largely the same underlying corporate-action cycle.",
            "- The appropriate next move is to pivot to a Tier 1 signal that is structurally independent of L-001 (e.g., reversal specialist using variance-ratio on price data only).",
            "",
            "## Recommended Next Action",
            "",
            "1. Close this experiment lane per pre-registration.",
            "2. Document outcome in L-xxx addendum and SESSION_LOG (when next written).",
            "3. Do NOT write run_h1.py. Do NOT attempt to rescue by relaxing thresholds (that would violate pre-registration).",
            "4. Pivot Claude time to the next Tier 1 signal (reversal specialist is the cleanest candidate).",
        ])

    return "\n".join(lines) + "\n"


def main() -> int:
    decision = build_decision()
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    DECISION_JSON.write_text(json.dumps(decision, indent=2, default=str), encoding="utf-8")
    DECISION_MD.write_text(format_markdown(decision), encoding="utf-8")
    print(f"Wrote {DECISION_JSON}")
    print(f"Wrote {DECISION_MD}")
    print()
    print(f"VERDICT: {decision['verdict']}")
    print()
    for c in decision["checks"]:
        print(f"  {c}")
    return 0 if decision["verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
