"""
Signal Decay Tracker — Layer 3 sandbox experiment.

Monitors the persistence shadow signal's rolling hit rate and flags decay.
Reads from production scorecard outputs (read-only). Writes only to this
experiment's own folder.

See CONTRACT.md for the full contract. See README.md for intent.

Usage:
    python experiments/signal-decay-tracker/run.py
    python experiments/signal-decay-tracker/run.py --dry-run
"""
from __future__ import annotations

import argparse
import csv
import json
import sys
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


EXPERIMENT_DIR = Path(__file__).resolve().parent
REPO_ROOT = EXPERIMENT_DIR.parent.parent

CASES_CSV = (
    REPO_ROOT
    / "market-gist"
    / "data"
    / "validation"
    / "persistence_shadow_reviews"
    / "latest__shadow_batch_cases_v1.csv"
)

RESULTS_DIR = EXPERIMENT_DIR / "results"
ALERTS_DIR = EXPERIMENT_DIR / "alerts"

# Thresholds from README.md. At N < GATE the tracker reports but does not alert.
SAMPLE_GATE = 20

# Rolling windows reported in every run.
ROLLING_WINDOWS = [5, 10, 20]

# Severity trigger thresholds.
YELLOW_DROP_PP = 10.0
ORANGE_DROP_PP = 20.0
RED_DROP_PP = 30.0
YELLOW_FLOOR = 0.65
ORANGE_FLOOR = 0.55
RED_FLOOR = 0.50

# Groups for which a negative forward return is "success."
NEGATIVE_SUCCESS_GROUPS = {
    "persistence_caution_only",
    "persistence_caution_plus_dividend_annotation",
    "dividend_annotation_only",
}
POSITIVE_SUCCESS_GROUPS = {"supportive_only"}


def load_resolved_cases() -> list[dict]:
    if not CASES_CSV.exists():
        raise SystemExit(f"Cases CSV not found: {CASES_CSV}")

    rows: list[dict] = []
    with CASES_CSV.open("r", encoding="utf-8") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            if raw.get("outcome_status") != "resolved":
                continue
            success = raw.get("success_10d", "").strip().lower()
            if success in ("true", "false"):
                raw["_success_bool"] = success == "true"
            else:
                raw["_success_bool"] = None
            rows.append(raw)

    rows.sort(key=lambda r: (r.get("anchor_date") or "", r.get("symbol") or ""))
    return rows


def compute_hit_rate(cases: list[dict]) -> float | None:
    scored = [c["_success_bool"] for c in cases if c["_success_bool"] is not None]
    if not scored:
        return None
    return sum(1 for s in scored if s) / len(scored)


def sample_concentration(cases: list[dict]) -> dict:
    """Compute report-date and symbol clustering metrics."""
    report_dates = [c.get("report_date") for c in cases if c.get("report_date")]
    symbols = [c.get("symbol") for c in cases if c.get("symbol")]

    date_counts = Counter(report_dates)
    symbol_counts = Counter(symbols)

    total = len(cases) or 1
    top_date_share = max(date_counts.values()) / total if date_counts else 0.0
    unique_dates = len(date_counts)

    return {
        "total_cases": len(cases),
        "unique_report_dates": unique_dates,
        "top_date_share": round(top_date_share, 3),
        "report_date_distribution": dict(date_counts),
        "symbol_distribution": dict(symbol_counts),
    }


def severity_for_group(
    baseline: float | None, rolling_5: float | None, sample_size: int
) -> tuple[str, list[str]]:
    reasons: list[str] = []

    if sample_size < SAMPLE_GATE:
        return "below_gate", [
            f"N={sample_size} < gate={SAMPLE_GATE}: descriptive only, no alert fired"
        ]
    if baseline is None or rolling_5 is None:
        return "unknown", ["insufficient data for baseline or rolling window"]

    drop_pp = (baseline - rolling_5) * 100.0

    if drop_pp >= RED_DROP_PP or rolling_5 < RED_FLOOR:
        reasons.append(
            f"rolling-5 = {rolling_5:.1%}, dropped {drop_pp:.1f}pp vs baseline {baseline:.1%}"
        )
        return "red", reasons
    if drop_pp >= ORANGE_DROP_PP or rolling_5 < ORANGE_FLOOR:
        reasons.append(
            f"rolling-5 = {rolling_5:.1%}, dropped {drop_pp:.1f}pp vs baseline {baseline:.1%}"
        )
        return "orange", reasons
    if drop_pp >= YELLOW_DROP_PP or rolling_5 < YELLOW_FLOOR:
        reasons.append(
            f"rolling-5 = {rolling_5:.1%}, dropped {drop_pp:.1f}pp vs baseline {baseline:.1%}"
        )
        return "yellow", reasons

    reasons.append(
        f"rolling-5 = {rolling_5:.1%}, baseline {baseline:.1%}, drop {drop_pp:.1f}pp"
    )
    return "green", reasons


def group_analysis(group_key: str, cases: list[dict]) -> dict:
    baseline = compute_hit_rate(cases)
    rolling = {}
    for window in ROLLING_WINDOWS:
        window_cases = cases[-window:] if len(cases) >= window else cases
        rolling[f"rolling_{window}"] = compute_hit_rate(window_cases)

    concentration = sample_concentration(cases)
    severity, reasons = severity_for_group(baseline, rolling["rolling_5"], len(cases))

    return {
        "group_key": group_key,
        "resolved_count": len(cases),
        "baseline_hit_rate": round(baseline, 3) if baseline is not None else None,
        "rolling_hit_rate": {
            k: (round(v, 3) if v is not None else None) for k, v in rolling.items()
        },
        "sample_concentration": concentration,
        "severity": severity,
        "reasons": reasons,
    }


def run_tracker() -> dict:
    cases = load_resolved_cases()

    by_group: dict[str, list[dict]] = defaultdict(list)
    for row in cases:
        key = row.get("group_key") or "unknown"
        by_group[key].append(row)

    group_reports = [
        group_analysis(group, group_cases)
        for group, group_cases in sorted(by_group.items())
    ]

    any_alert = any(
        g["severity"] in ("yellow", "orange", "red") for g in group_reports
    )
    max_severity = max(
        (g["severity"] for g in group_reports),
        key=lambda s: ["below_gate", "unknown", "green", "yellow", "orange", "red"].index(s)
        if s in ["below_gate", "unknown", "green", "yellow", "orange", "red"]
        else 0,
        default="green",
    )

    return {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "cases_csv": str(CASES_CSV),
        "total_resolved_cases": len(cases),
        "sample_gate": SAMPLE_GATE,
        "any_alert_fired": any_alert,
        "max_severity": max_severity,
        "groups": group_reports,
    }


def format_report_md(report: dict) -> str:
    lines = [
        "[EXPERIMENTAL SIGNAL] shadow only, not a trading decision.",
        "Experiment: signal-decay-tracker",
        f"Forward evidence: N={report['total_resolved_cases']} / required={report['sample_gate']}",
        "Layer: 3 (research)",
        "",
        "# Signal Decay Tracker Report",
        "",
        f"- Generated: {report['generated_at']}",
        f"- Resolved cases total: {report['total_resolved_cases']}",
        f"- Max severity: **{report['max_severity']}**",
        "",
    ]

    if report["total_resolved_cases"] < report["sample_gate"]:
        lines.extend(
            [
                "> Below sample gate. Descriptive stats only. No alert will fire even if thresholds look breached.",
                "",
            ]
        )

    lines.extend(
        [
            "## Per-Group Summary",
            "",
            "| Group | N | Baseline | R-5 | R-10 | R-20 | Unique dates | Top date % | Severity |",
            "|---|---:|---:|---:|---:|---:|---:|---:|---|",
        ]
    )

    for g in report["groups"]:
        baseline = (
            f"{g['baseline_hit_rate']:.1%}"
            if g["baseline_hit_rate"] is not None
            else "-"
        )
        r5 = g["rolling_hit_rate"].get("rolling_5")
        r10 = g["rolling_hit_rate"].get("rolling_10")
        r20 = g["rolling_hit_rate"].get("rolling_20")
        conc = g["sample_concentration"]
        lines.append(
            "| {grp} | {n} | {baseline} | {r5} | {r10} | {r20} | {dates} | {topshare} | {sev} |".format(
                grp=g["group_key"],
                n=g["resolved_count"],
                baseline=baseline,
                r5=f"{r5:.1%}" if r5 is not None else "-",
                r10=f"{r10:.1%}" if r10 is not None else "-",
                r20=f"{r20:.1%}" if r20 is not None else "-",
                dates=conc["unique_report_dates"],
                topshare=f"{conc['top_date_share']:.1%}",
                sev=g["severity"],
            )
        )

    lines.extend(["", "## Per-Group Detail", ""])

    for g in report["groups"]:
        lines.extend(
            [
                f"### {g['group_key']} — {g['severity']}",
                "",
            ]
        )
        for r in g["reasons"]:
            lines.append(f"- {r}")
        conc = g["sample_concentration"]
        lines.extend(
            [
                f"- Report-date distribution: {conc['report_date_distribution']}",
                f"- Symbol distribution: {conc['symbol_distribution']}",
                "",
            ]
        )

    lines.extend(
        [
            "## Interpretation",
            "",
            "- Severity `below_gate`: sample too small for reliable decay inference; report is descriptive only.",
            "- Severity `green`: rolling hit rate close to baseline; no action required.",
            "- Severity `yellow`: monitor, no action required.",
            "- Severity `orange`: review the recent cases; flag to Romeo.",
            "- Severity `red`: pause any promotion discussion; open formal audit.",
            "",
            "Thresholds are intentionally conservative at this sample size. See README.md.",
        ]
    )

    return "\n".join(lines) + "\n"


def format_alert_md(report: dict, group: dict) -> str:
    return "\n".join(
        [
            "[EXPERIMENTAL SIGNAL] shadow only, not a trading decision.",
            "Experiment: signal-decay-tracker",
            f"Forward evidence: N={report['total_resolved_cases']} / required={report['sample_gate']}",
            "Layer: 3 (research)",
            "",
            f"# ALERT: {group['group_key']} decay at {group['severity']}",
            "",
            f"- Baseline: {group['baseline_hit_rate']}",
            f"- Rolling-5: {group['rolling_hit_rate'].get('rolling_5')}",
            f"- Rolling-10: {group['rolling_hit_rate'].get('rolling_10')}",
            f"- Reasons:",
            *[f"  - {r}" for r in group["reasons"]],
            "",
            "Action required: see README.md for severity response.",
        ]
    ) + "\n"


def write_outputs(report: dict, dry_run: bool) -> None:
    if dry_run:
        print(format_report_md(report))
        return

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    ALERTS_DIR.mkdir(parents=True, exist_ok=True)

    stamp = datetime.now().strftime("%Y-%m-%d")
    snapshot_json = RESULTS_DIR / f"decay_{stamp}.json"
    snapshot_md = RESULTS_DIR / f"decay_{stamp}.md"
    latest_json = RESULTS_DIR / "latest.json"
    latest_md = RESULTS_DIR / "latest.md"

    snapshot_json.write_text(json.dumps(report, indent=2), encoding="utf-8")
    latest_json.write_text(json.dumps(report, indent=2), encoding="utf-8")

    md = format_report_md(report)
    snapshot_md.write_text(md, encoding="utf-8")
    latest_md.write_text(md, encoding="utf-8")

    print(f"Wrote {snapshot_json}")
    print(f"Wrote {snapshot_md}")
    print(f"Wrote {latest_json}")
    print(f"Wrote {latest_md}")

    alerts_written = 0
    for g in report["groups"]:
        if g["severity"] in ("yellow", "orange", "red"):
            alert_path = ALERTS_DIR / f"{stamp}_{g['severity']}_{g['group_key']}.md"
            alert_path.write_text(format_alert_md(report, g), encoding="utf-8")
            print(f"ALERT written: {alert_path}")
            alerts_written += 1

    if alerts_written == 0:
        print("No alerts fired.")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Print report to stdout but do not write files.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    report = run_tracker()
    write_outputs(report, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
