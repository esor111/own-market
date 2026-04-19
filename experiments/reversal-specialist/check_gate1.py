"""
Reversal Specialist — Step 2: Gate 1 Sample Adequacy Check

Reads data/trigger_events.csv (produced by build_trigger_events.py) and applies
the Gate 1 criteria from PRE_REGISTRATION.md revision 4:

  - Per-direction N >= 80 events (h1-eligible only)
  - Unique trigger calendar dates >= 30
  - Top-3 trigger-date concentration <= 30%
  - At least 5 symbols contributing >= 1 event each

Produces a decision memo per direction.

DOES NOT RUN UNTIL ROMEO SIGNS OFF ON PRE_REGISTRATION revision 4.

Usage (after sign-off):
    python experiments/reversal-specialist/check_gate1.py
"""
from __future__ import annotations

import csv
import json
import sys
from collections import Counter
from datetime import datetime
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
TRIGGER_CSV = SCRIPT_DIR / "data" / "trigger_events.csv"
OUTPUT_DIR = SCRIPT_DIR / "data"
DECISION_JSON = OUTPUT_DIR / "gate1_decision.json"
DECISION_MD = OUTPUT_DIR / "gate1_decision.md"

GATE1_MIN_N = 80
GATE1_MIN_UNIQUE_DATES = 30
GATE1_MAX_TOP3_SHARE = 0.30
GATE1_MIN_SYMBOLS = 5


def load_triggers() -> list[dict]:
    if not TRIGGER_CSV.exists():
        raise SystemExit(
            f"Trigger events not found at {TRIGGER_CSV}. "
            "Run build_trigger_events.py first."
        )
    with TRIGGER_CSV.open("r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return [row for row in reader]


def direction_stats(trigger_rows: list[dict]) -> dict:
    n = len(trigger_rows)
    dates = [r["trigger_date"] for r in trigger_rows]
    symbols = [r["symbol"] for r in trigger_rows]

    date_counts = Counter(dates)
    symbol_counts = Counter(symbols)
    total = n or 1
    sorted_counts = sorted(date_counts.values(), reverse=True)
    top1 = sorted_counts[0] / total if sorted_counts else 0.0
    top3 = sum(sorted_counts[:3]) / total if sorted_counts else 0.0
    top5 = sum(sorted_counts[:5]) / total if sorted_counts else 0.0

    symbols_with_events = sum(1 for _, c in symbol_counts.items() if c > 0)

    return {
        "n": n,
        "unique_trigger_dates": len(date_counts),
        "top1_share": round(top1, 3),
        "top3_share": round(top3, 3),
        "top5_share": round(top5, 3),
        "symbols_with_events": symbols_with_events,
        "symbol_distribution": dict(symbol_counts),
        "date_distribution_top_10": dict(date_counts.most_common(10)),
    }


def apply_gate1(stats: dict, direction_label: str) -> tuple[str, list[str]]:
    verdict = "PASS"
    checks: list[str] = []

    if stats["n"] < GATE1_MIN_N:
        verdict = "FAIL"
        checks.append(f"FAIL [{direction_label}]: N = {stats['n']} < required {GATE1_MIN_N}")
    else:
        checks.append(f"PASS [{direction_label}]: N = {stats['n']} >= {GATE1_MIN_N}")

    if stats["unique_trigger_dates"] < GATE1_MIN_UNIQUE_DATES:
        verdict = "FAIL"
        checks.append(
            f"FAIL [{direction_label}]: unique dates = {stats['unique_trigger_dates']} "
            f"< required {GATE1_MIN_UNIQUE_DATES}"
        )
    else:
        checks.append(
            f"PASS [{direction_label}]: unique dates = {stats['unique_trigger_dates']} "
            f">= {GATE1_MIN_UNIQUE_DATES}"
        )

    if stats["top3_share"] > GATE1_MAX_TOP3_SHARE:
        verdict = "FAIL"
        checks.append(
            f"FAIL [{direction_label}]: top-3 date concentration = "
            f"{stats['top3_share']:.1%} > max {GATE1_MAX_TOP3_SHARE:.0%}"
        )
    else:
        checks.append(
            f"PASS [{direction_label}]: top-3 date concentration = "
            f"{stats['top3_share']:.1%} <= {GATE1_MAX_TOP3_SHARE:.0%}"
        )

    if stats["symbols_with_events"] < GATE1_MIN_SYMBOLS:
        verdict = "FAIL"
        checks.append(
            f"FAIL [{direction_label}]: symbols contributing events = "
            f"{stats['symbols_with_events']} < required {GATE1_MIN_SYMBOLS}"
        )
    else:
        checks.append(
            f"PASS [{direction_label}]: symbols contributing events = "
            f"{stats['symbols_with_events']} >= {GATE1_MIN_SYMBOLS}"
        )

    return verdict, checks


def compute_gate_drift_diagnostic(triggers: list[dict]) -> dict:
    """Gate-drift diagnostic (Romeo 2026-04-18 Rev-4 item).

    Counts how many rows pass `include_in_primary` but fail `h1_eligible`, broken
    down by the reason (no forward window / insufficient baseline). Reports per
    direction. If this number is large, Gate 1 is shrinking the sample meaningfully
    between filters and H1 — the exposure is now visible, not hidden.
    """
    def is_truthy(v):
        return v in ("True", "1", True)

    def is_falsy(v):
        return v in ("False", "0", False)

    stats: dict = {"all_directions": {}, "sharp_down": {}, "sharp_up": {}}
    for label, direction in (("all_directions", None), ("sharp_down", "down"), ("sharp_up", "up")):
        subset = (
            triggers if direction is None
            else [t for t in triggers if t.get("direction") == direction]
        )
        in_primary = [t for t in subset if is_truthy(t.get("include_in_primary"))]
        h1_ok = [t for t in in_primary if is_truthy(t.get("h1_eligible"))]
        drifted = [t for t in in_primary if is_falsy(t.get("h1_eligible"))]
        drifted_no_forward = [t for t in drifted if is_falsy(t.get("has_forward_5d"))]
        # Baseline count stored as string in the CSV; parse defensively.
        def baseline_count(t):
            try:
                return int(float(t.get("baseline_obs_count", 0) or 0))
            except (TypeError, ValueError):
                return 0
        drifted_low_baseline = [
            t for t in drifted
            if is_truthy(t.get("has_forward_5d")) and baseline_count(t) < 30
        ]
        stats[label] = {
            "include_in_primary": len(in_primary),
            "h1_eligible": len(h1_ok),
            "gate_drift_count": len(drifted),
            "gate_drift_reason_no_forward_window": len(drifted_no_forward),
            "gate_drift_reason_insufficient_baseline": len(drifted_low_baseline),
            "gate_drift_share": (
                round(len(drifted) / len(in_primary), 3) if in_primary else 0.0
            ),
        }
    return stats


def build_decision() -> dict:
    triggers = load_triggers()
    # Apply inclusion per PRE_REGISTRATION revision 4:
    # include only rows with `h1_eligible == True`. Romeo's rev-3 catch: counting
    # `include_in_primary` caused gate drift — rows could pass Gate 1 that H1 later
    # drops for lack of forward data or baseline observations. `h1_eligible` already
    # folds in all three conditions (filters pass + has_forward_5d + baseline_obs >= 30).
    included = [t for t in triggers if t.get("h1_eligible") in ("True", "1", True)]
    excluded_count = len(triggers) - len(included)

    gate_drift = compute_gate_drift_diagnostic(triggers)

    down = [t for t in included if t["direction"] == "down"]
    up = [t for t in included if t["direction"] == "up"]

    down_stats = direction_stats(down)
    up_stats = direction_stats(up)

    down_verdict, down_checks = apply_gate1(down_stats, "sharp-down (primary H1)")
    up_verdict, up_checks = apply_gate1(up_stats, "sharp-up (secondary H1b)")

    # Overall: primary H1 goes ahead only if down direction passes
    primary_verdict = down_verdict
    if primary_verdict == "PASS":
        overall = "PASS (H1 sharp-down can proceed)"
    else:
        overall = "FAIL (H1 sharp-down blocked — lane closed per pre-registration)"

    if up_verdict == "PASS":
        overall += "; H1b sharp-up can run as secondary"
    else:
        overall += "; H1b sharp-up blocked by Gate 1 (secondary, reported as descriptive only)"

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "trigger_csv": str(TRIGGER_CSV),
        "pre_registration_revision": "4",
        "gate1_thresholds": {
            "min_n_per_direction": GATE1_MIN_N,
            "min_unique_dates": GATE1_MIN_UNIQUE_DATES,
            "max_top3_share": GATE1_MAX_TOP3_SHARE,
            "min_symbols_contributing": GATE1_MIN_SYMBOLS,
        },
        "total_triggers_all": len(triggers),
        "not_h1_eligible_count": excluded_count,
        "total_triggers_after_exclusion": len(included),
        "primary_direction_verdict": primary_verdict,
        "primary_direction_checks": down_checks,
        "secondary_direction_verdict": up_verdict,
        "secondary_direction_checks": up_checks,
        "overall_verdict": overall,
        "sharp_down_stats": down_stats,
        "sharp_up_stats": up_stats,
        "gate_drift_diagnostic": gate_drift,
    }


def format_markdown(decision: dict) -> str:
    d = decision["sharp_down_stats"]
    u = decision["sharp_up_stats"]
    lines = [
        "[EXPERIMENTAL TOOL] Gate 1 decision memo for reversal-specialist sandbox.",
        "Historical-test sample, not forward evidence.",
        "PRE_REGISTRATION revision 4.",
        "",
        "# Gate 1 Decision",
        "",
        f"- Generated: {decision['generated_at']}",
        f"- Total triggers detected: {decision['total_triggers_all']}",
        f"- Not h1-eligible (any of: volume fail, price-limit, corp-action, regime, no forward window, insufficient baseline): {decision['not_h1_eligible_count']}",
        f"- Triggers h1-eligible (pass all filters AND forward window AND baseline): {decision['total_triggers_after_exclusion']}",
        "",
        f"- **Primary (sharp-down H1) verdict: `{decision['primary_direction_verdict']}`**",
        f"- **Secondary (sharp-up H1b) verdict: `{decision['secondary_direction_verdict']}`**",
        f"- **Overall: {decision['overall_verdict']}**",
        "",
        "## Primary Direction — Sharp-Down (-5% or worse)",
        "",
        f"- N: **{d['n']}** (gate: >= {decision['gate1_thresholds']['min_n_per_direction']})",
        f"- Unique trigger dates: **{d['unique_trigger_dates']}** (gate: >= {decision['gate1_thresholds']['min_unique_dates']})",
        f"- Top-1 date share: {d['top1_share']:.1%}",
        f"- Top-3 date share: **{d['top3_share']:.1%}** (gate: <= {decision['gate1_thresholds']['max_top3_share']:.0%})",
        f"- Top-5 date share: {d['top5_share']:.1%}",
        f"- Symbols contributing events: **{d['symbols_with_events']}** (gate: >= {decision['gate1_thresholds']['min_symbols_contributing']})",
        "",
        "### Sharp-down checks",
        "",
    ]
    for c in decision["primary_direction_checks"]:
        lines.append(f"- {c}")

    lines.extend([
        "",
        "### Sharp-down symbol distribution (top 10)",
        "",
    ])
    sd_dist = dict(sorted(d["symbol_distribution"].items(), key=lambda x: x[1], reverse=True)[:10])
    for sym, n in sd_dist.items():
        lines.append(f"- {sym}: {n}")

    lines.extend([
        "",
        "### Sharp-down top-10 trigger dates",
        "",
    ])
    for dt, n in list(d["date_distribution_top_10"].items())[:10]:
        lines.append(f"- {dt}: {n} symbol(s)")

    lines.extend([
        "",
        "## Secondary Direction — Sharp-Up (+5% or better)",
        "",
        f"- N: **{u['n']}** (gate: >= {decision['gate1_thresholds']['min_n_per_direction']})",
        f"- Unique trigger dates: **{u['unique_trigger_dates']}**",
        f"- Top-1 date share: {u['top1_share']:.1%}",
        f"- Top-3 date share: **{u['top3_share']:.1%}**",
        f"- Symbols contributing events: **{u['symbols_with_events']}**",
        "",
        "### Sharp-up checks",
        "",
    ])
    for c in decision["secondary_direction_checks"]:
        lines.append(f"- {c}")

    # Gate-drift diagnostic (Romeo rev-4 item)
    gd = decision.get("gate_drift_diagnostic", {})
    lines.extend([
        "",
        "## Gate-Drift Diagnostic",
        "",
        "How many rows pass `include_in_primary` but fail `h1_eligible`, and why.",
        "If this number is large, the sample is shrinking meaningfully between filters",
        "and the H1 test — the exposure should be visible, not hidden.",
        "",
        "| Subset | include_in_primary | h1_eligible | drift | drift share | no_forward | low_baseline |",
        "|---|---:|---:|---:|---:|---:|---:|",
    ])
    for label in ("all_directions", "sharp_down", "sharp_up"):
        g = gd.get(label, {})
        lines.append(
            f"| {label} | {g.get('include_in_primary', 0)} | {g.get('h1_eligible', 0)} | "
            f"{g.get('gate_drift_count', 0)} | {g.get('gate_drift_share', 0):.1%} | "
            f"{g.get('gate_drift_reason_no_forward_window', 0)} | "
            f"{g.get('gate_drift_reason_insufficient_baseline', 0)} |"
        )

    lines.extend([
        "",
        "## Recommended Next Action",
        "",
    ])
    if decision["primary_direction_verdict"] == "PASS":
        lines.extend([
            "- Gate 1 (primary direction) passes. Proceed to Step 3: write `run_h1.py` with date-cluster block-bootstrap on sharp-down triggers.",
            "- If secondary direction also passes, run H1b in the same session but label as secondary.",
            "- Commit pre-registration revision 4 to git BEFORE `run_h1.py` executes.",
        ])
    else:
        lines.extend([
            "- Gate 1 (primary direction) FAILS. Per pre-registration, the primary lane is killed.",
            "- Do not run H1. Do not attempt to rescue by relaxing thresholds (that would violate pre-registration).",
            "- Document the failure in a SESSION_LOG addendum or LEARNINGS addendum.",
            "- Pivot to the next Tier 1 candidate signal, or conclude the Tier 1 exploration round.",
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
    print(f"OVERALL: {decision['overall_verdict']}")
    print()
    print("Primary direction (sharp-down):")
    for c in decision["primary_direction_checks"]:
        print(f"  {c}")
    print()
    print("Secondary direction (sharp-up):")
    for c in decision["secondary_direction_checks"]:
        print(f"  {c}")

    return 0 if decision["primary_direction_verdict"] == "PASS" else 1


if __name__ == "__main__":
    sys.exit(main())
