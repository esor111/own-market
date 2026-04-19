"""
Batch-Score Decision Playbook — Layer 3 infrastructure tool.

Automates the persistence shadow batch-score decision at N >= 25 resolved cases.
Produces a PROMOTE / HOLD / KILL / BELOW_GATE verdict with structured reasoning.

Read CONTRACT.md for the sandbox contract, README.md for verdict thresholds.

Usage:
    python experiments/batch-score-playbook/run_batch_score.py
    python experiments/batch-score-playbook/run_batch_score.py --dry-run
    python experiments/batch-score-playbook/run_batch_score.py --force
"""
from __future__ import annotations

import argparse
import csv
import hashlib
import json
import os
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

SCORECARD_JSON = (
    REPO_ROOT
    / "market-gist"
    / "data"
    / "validation"
    / "persistence_shadow_reviews"
    / "latest__shadow_batch_scorecard_v1.json"
)

FROZEN_POLICY = (
    REPO_ROOT
    / "market-gist"
    / "agents"
    / "shared"
    / "PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md"
)

SCORER_CODE = (
    REPO_ROOT
    / "market-gist"
    / "automation"
    / "score_persistence_shadow_reports.py"
)

DECAY_TRACKER_LATEST = (
    EXPERIMENT_DIR.parent
    / "signal-decay-tracker"
    / "results"
    / "latest.json"
)

RESULTS_DIR = EXPERIMENT_DIR / "results"

# Verdict thresholds. See README.md for rationale.
GATE_MIN_N = 25
PROMOTE_HIT_RATE = 0.65
PROMOTE_TOP3_MAX = 0.40
PROMOTE_MIN_EPISODES = 5
KILL_HIT_RATE = 0.55
KILL_TOP1_MAX = 0.50
KILL_MIN_EPISODES = 3

FROZEN_POLICY_EXPECTED_DATE_CUTOFF = datetime(2026, 4, 6)  # policy must predate this
PRIMARY_GROUP = "persistence_caution_only"


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
            raw["_success_bool"] = success == "true" if success in ("true", "false") else None
            rows.append(raw)
    rows.sort(key=lambda r: (r.get("anchor_date") or "", r.get("symbol") or ""))
    return rows


def compute_hit_rate(cases: list[dict]) -> float | None:
    scored = [c["_success_bool"] for c in cases if c["_success_bool"] is not None]
    if not scored:
        return None
    return sum(1 for s in scored if s) / len(scored)


def sample_concentration(cases: list[dict]) -> dict:
    report_dates = [c.get("report_date") for c in cases if c.get("report_date")]
    symbols = [c.get("symbol") for c in cases if c.get("symbol")]
    date_counts = Counter(report_dates)
    symbol_counts = Counter(symbols)
    total = len(cases) or 1

    sorted_dates = sorted(date_counts.values(), reverse=True)
    top1 = sorted_dates[0] / total if sorted_dates else 0.0
    top3 = sum(sorted_dates[:3]) / total if sorted_dates else 0.0
    top5 = sum(sorted_dates[:5]) / total if sorted_dates else 0.0

    return {
        "total_cases": len(cases),
        "unique_report_dates": len(date_counts),
        "top1_share": round(top1, 3),
        "top3_share": round(top3, 3),
        "top5_share": round(top5, 3),
        "report_date_distribution": dict(date_counts),
        "symbol_distribution": dict(symbol_counts),
    }


def effective_independent_episodes(cases: list[dict]) -> int:
    """Count unique report dates among wins. A rough proxy for effective N."""
    win_dates = set()
    for c in cases:
        if c["_success_bool"] is True and c.get("report_date"):
            win_dates.add(c["report_date"])
    return len(win_dates)


def sub_period_stability(cases: list[dict]) -> dict:
    """Split cases by quarter (YYYY-Qn) and report hit rate per quarter."""
    def case_quarter(c: dict) -> str | None:
        d = c.get("anchor_date") or c.get("report_date")
        if not d:
            return None
        try:
            dt = datetime.strptime(d, "%Y-%m-%d")
        except ValueError:
            return None
        return f"{dt.year}-Q{(dt.month - 1) // 3 + 1}"

    buckets: dict[str, list[dict]] = defaultdict(list)
    for c in cases:
        q = case_quarter(c)
        if q:
            buckets[q].append(c)

    per_quarter = {}
    for q, group in sorted(buckets.items()):
        hr = compute_hit_rate(group)
        per_quarter[q] = {
            "n": len(group),
            "hit_rate": round(hr, 3) if hr is not None else None,
        }

    quarters_with_wins = [
        q for q, info in per_quarter.items()
        if info["hit_rate"] is not None and info["hit_rate"] > 0
    ]

    return {
        "per_quarter": per_quarter,
        "quarters_with_any_wins": len(quarters_with_wins),
        "quarters_with_strong_wins": sum(
            1 for q, info in per_quarter.items()
            if info["hit_rate"] is not None and info["hit_rate"] >= 0.60
        ),
    }


def check_frozen_policy_f1() -> dict:
    """F.1 — pre-registration artifact check."""
    if not FROZEN_POLICY.exists():
        return {
            "f1_pass": False,
            "f1_reason": f"Frozen policy file not found at {FROZEN_POLICY}",
            "policy_path": str(FROZEN_POLICY),
            "policy_mtime": None,
            "policy_sha256": None,
            "cutoff_satisfied": False,
        }

    stat = FROZEN_POLICY.stat()
    mtime = datetime.fromtimestamp(stat.st_mtime)
    cutoff_ok = mtime < FROZEN_POLICY_EXPECTED_DATE_CUTOFF

    try:
        content = FROZEN_POLICY.read_bytes()
        sha = hashlib.sha256(content).hexdigest()
    except Exception as exc:
        return {
            "f1_pass": False,
            "f1_reason": f"Could not read frozen policy: {exc}",
            "policy_path": str(FROZEN_POLICY),
            "policy_mtime": mtime.isoformat(),
            "policy_sha256": None,
            "cutoff_satisfied": cutoff_ok,
        }

    return {
        "f1_pass": cutoff_ok,
        "f1_reason": (
            "policy mtime is before 2026-04-06 cutoff"
            if cutoff_ok
            else f"policy mtime {mtime.isoformat()} is AFTER 2026-04-06 cutoff — policy may have been modified post-freeze"
        ),
        "policy_path": str(FROZEN_POLICY),
        "policy_mtime": mtime.isoformat(),
        "policy_sha256": sha,
        "cutoff_satisfied": cutoff_ok,
    }


def check_scorer_dedupe_a1() -> dict:
    """A.1 — does the scorer define or import collapse_duplicate_sessions?"""
    if not SCORER_CODE.exists():
        return {
            "a1_pass": False,
            "a1_reason": f"Scorer not found at {SCORER_CODE}",
        }
    try:
        content = SCORER_CODE.read_text(encoding="utf-8")
    except Exception as exc:
        return {"a1_pass": False, "a1_reason": f"Could not read scorer: {exc}"}

    has_local_def = "def collapse_duplicate_sessions" in content or "def _collapse_duplicate_sessions" in content
    has_import = (
        "from experiments.shared.price_loader import" in content
        and "collapse_duplicate_sessions" in content
    )
    a1_pass = has_local_def or has_import
    return {
        "a1_pass": a1_pass,
        "a1_reason": (
            f"scorer defines collapse_duplicate_sessions locally (has_local_def={has_local_def}) "
            f"or imports it from shared (has_import={has_import})"
        ),
        "has_local_def": has_local_def,
        "has_import": has_import,
    }


def verdict_from_state(state: dict) -> tuple[str, list[str]]:
    """Apply the verdict rules to the full state and return (verdict, reasons)."""
    n = state["resolved_n"]
    hit_rate = state["hit_rate"]
    conc = state["concentration"]
    episodes = state["effective_independent_episodes"]
    stability = state["sub_period_stability"]
    f1 = state["f1"]
    a1 = state["a1"]

    if n < GATE_MIN_N and not state["forced"]:
        return "BELOW_GATE", [
            f"N={n} < gate={GATE_MIN_N}: descriptive stats only, no verdict yet"
        ]

    kill_reasons = []
    if hit_rate is not None and hit_rate < KILL_HIT_RATE:
        kill_reasons.append(f"hit rate {hit_rate:.1%} < kill threshold {KILL_HIT_RATE:.0%}")
    if not f1["f1_pass"]:
        kill_reasons.append(f"F.1 pre-registration check failed: {f1['f1_reason']}")
    if conc["top1_share"] > KILL_TOP1_MAX:
        kill_reasons.append(
            f"top-1 report date share {conc['top1_share']:.1%} > kill threshold {KILL_TOP1_MAX:.0%}"
        )
    if episodes < KILL_MIN_EPISODES:
        kill_reasons.append(
            f"effective independent episodes {episodes} < kill threshold {KILL_MIN_EPISODES}"
        )
    if kill_reasons:
        return "KILL", kill_reasons

    promote_conditions = {
        "hit_rate_ge_65": (hit_rate is not None and hit_rate >= PROMOTE_HIT_RATE),
        "top3_le_40": conc["top3_share"] <= PROMOTE_TOP3_MAX,
        "episodes_ge_5": episodes >= PROMOTE_MIN_EPISODES,
        "stability_ge_2_quarters": stability["quarters_with_strong_wins"] >= 2,
        "f1_pass": f1["f1_pass"],
        "a1_pass": a1["a1_pass"],
    }
    promote_reasons = [k for k, v in promote_conditions.items() if v]
    promote_failures = [k for k, v in promote_conditions.items() if not v]

    if all(promote_conditions.values()):
        return "PROMOTE", [
            f"hit rate {hit_rate:.1%} >= {PROMOTE_HIT_RATE:.0%}",
            f"top-3 concentration {conc['top3_share']:.1%} <= {PROMOTE_TOP3_MAX:.0%}",
            f"effective episodes {episodes} >= {PROMOTE_MIN_EPISODES}",
            f"{stability['quarters_with_strong_wins']} quarters with strong wins",
            "F.1 and A.1 audit gates passed",
        ]

    hold_reasons = [f"fails promote condition: {f}" for f in promote_failures]
    hold_reasons.append(
        f"hit rate {hit_rate:.1%} is between kill ({KILL_HIT_RATE:.0%}) "
        f"and promote ({PROMOTE_HIT_RATE:.0%}) thresholds"
        if hit_rate is not None else "hit rate unknown"
    )
    return "HOLD", hold_reasons


def build_state(forced: bool) -> dict:
    all_cases = load_resolved_cases()
    caution_cases = [c for c in all_cases if c.get("group_key") == PRIMARY_GROUP]
    all_groups_n = Counter(c.get("group_key") for c in all_cases)

    state = {
        "generated_at": datetime.now().isoformat(timespec="seconds"),
        "cases_csv": str(CASES_CSV),
        "primary_group": PRIMARY_GROUP,
        "resolved_n": len(caution_cases),
        "all_groups_resolved": dict(all_groups_n),
        "gate_min_n": GATE_MIN_N,
        "forced": forced,
        "hit_rate": compute_hit_rate(caution_cases),
        "concentration": sample_concentration(caution_cases),
        "effective_independent_episodes": effective_independent_episodes(caution_cases),
        "sub_period_stability": sub_period_stability(caution_cases),
        "f1": check_frozen_policy_f1(),
        "a1": check_scorer_dedupe_a1(),
    }

    verdict, reasons = verdict_from_state(state)
    state["verdict"] = verdict
    state["reasons"] = reasons
    return state


def format_memo(state: dict) -> str:
    hr = state["hit_rate"]
    conc = state["concentration"]
    stab = state["sub_period_stability"]

    lines = [
        "[EXPERIMENTAL TOOL — decision support for batch-score gate]",
        "Tool: batch-score-playbook",
        f"Persistence resolved N: {state['resolved_n']} / gate={state['gate_min_n']}",
        "Layer: 3 (research — infrastructure, not a signal)",
        "",
        "# Batch-Score Decision Memo",
        "",
        f"- Generated: {state['generated_at']}",
        f"- **Verdict: `{state['verdict']}`**",
        "",
        "## Reasons",
        "",
    ]
    for r in state["reasons"]:
        lines.append(f"- {r}")

    lines.extend([
        "",
        "## Headline Numbers",
        "",
        f"- Resolved cases in `{PRIMARY_GROUP}`: **{state['resolved_n']}** (gate {state['gate_min_n']})",
        f"- All groups resolved counts: {state['all_groups_resolved']}",
        f"- Hit rate: **{f'{hr:.1%}' if hr is not None else 'n/a'}**",
        f"- Effective independent episodes (unique win dates): **{state['effective_independent_episodes']}**",
        f"- Unique report dates (all cases, not just wins): {conc['unique_report_dates']}",
        f"- Top-1 date share: {conc['top1_share']:.1%} (kill if > {KILL_TOP1_MAX:.0%})",
        f"- Top-3 date share: {conc['top3_share']:.1%} (promote if <= {PROMOTE_TOP3_MAX:.0%})",
        "",
        "## Report-Date Distribution",
        "",
    ])
    for d, n in sorted(conc["report_date_distribution"].items()):
        lines.append(f"- {d}: {n} case(s)")

    lines.extend([
        "",
        "## Symbol Distribution",
        "",
    ])
    for sym, n in sorted(conc["symbol_distribution"].items()):
        lines.append(f"- {sym}: {n} case(s)")

    lines.extend([
        "",
        "## Sub-Period Stability (quarterly)",
        "",
        f"- Quarters with any wins: {stab['quarters_with_any_wins']}",
        f"- Quarters with hit rate >= 60%: {stab['quarters_with_strong_wins']} (promote requires >= 2)",
        "",
        "| Quarter | N | Hit Rate |",
        "|---|---:|---:|",
    ])
    for q, info in sorted(stab["per_quarter"].items()):
        hrq = f"{info['hit_rate']:.1%}" if info["hit_rate"] is not None else "-"
        lines.append(f"| {q} | {info['n']} | {hrq} |")

    lines.extend([
        "",
        "## Audit Checks",
        "",
        f"### F.1 — Pre-registration Artifact: {'PASS' if state['f1']['f1_pass'] else 'FAIL'}",
        f"- Policy path: {state['f1']['policy_path']}",
        f"- Policy mtime: {state['f1']['policy_mtime']}",
        f"- Policy SHA-256: {state['f1']['policy_sha256']}",
        f"- Cutoff satisfied (mtime < 2026-04-06): {state['f1']['cutoff_satisfied']}",
        f"- Reason: {state['f1']['f1_reason']}",
        "",
        f"### A.1 — Scorer Dedupe Function: {'PASS' if state['a1']['a1_pass'] else 'FAIL'}",
        f"- Reason: {state['a1']['a1_reason']}",
        "",
        "### F.2, A.2, A.3, B, C (descriptive only)",
        "- F.2 (search space documentation): automated check not available; verify manually by checking if `search_space_enumeration.md` or equivalent exists",
        "- A.2 (trading-day arithmetic): manual code inspection required; confirm `anchor_idx + offset` is used on dedupe'd price frames",
        "- A.3 (regime break handling): scorer uses CSV file dates; immune by construction",
        "- B (frozen policy drift): SHA-256 recorded above; compare against any earlier hash on record",
        "- C (baseline adjustment): scorer computes raw returns; promote decision should acknowledge this",
        "",
        "## Recommended Next Action",
        "",
    ])

    if state["verdict"] == "BELOW_GATE":
        lines.extend([
            "- No action. Wait for more cases to resolve.",
            "- Re-run this tool when case count is within 5 of the gate (i.e. at N=20).",
        ])
    elif state["verdict"] == "PROMOTE":
        lines.extend([
            "- **Do NOT promote immediately.** Send this memo to Romeo for adversarial review first.",
            "- Romeo-review prompt: \"Romeo, the batch-score playbook returned PROMOTE at N=<N>. Verify verdict logic and all audit classes before the lab treats this as a promotion decision. Specific checks: F.2 search space documentation, A.2 code inspection, B frozen-policy SHA comparison to first shadow-report-date state.\"",
            "- If Romeo confirms: follow the serial-promotion path in `PARALLEL_EXPLORATION_SERIAL_PROMOTION.md`.",
            "- Do not promote to live trading without Romeo sign-off.",
        ])
    elif state["verdict"] == "KILL":
        lines.extend([
            "- Document the kill decision in LEARNINGS.md with a new L-xxx entry.",
            "- Include specific kill condition triggered and numeric evidence.",
            "- Persistence shadow can CONTINUE running in shadow mode; kill is about promotion, not monitoring.",
            "- Redirect lab forward-evidence budget to other Tier 1 signals.",
        ])
    elif state["verdict"] == "HOLD":
        lines.extend([
            "- Continue the daily routine unchanged.",
            "- Re-run this tool after ~10 more trading days or 10 more resolved cases.",
            "- If verdict remains HOLD across 2-3 re-runs, treat as implicit KILL.",
        ])

    lines.extend([
        "",
        "## Full State (JSON)",
        "",
        "See `decision_<date>.json` next to this file for the full machine-readable state.",
    ])

    return "\n".join(lines) + "\n"


def write_outputs(state: dict, dry_run: bool) -> None:
    if dry_run:
        print(format_memo(state))
        return
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    stamp = datetime.now().strftime("%Y-%m-%d")
    for path, payload in [
        (RESULTS_DIR / f"decision_{stamp}.json", json.dumps(state, indent=2)),
        (RESULTS_DIR / "latest.json", json.dumps(state, indent=2)),
        (RESULTS_DIR / f"decision_{stamp}.md", format_memo(state)),
        (RESULTS_DIR / "latest.md", format_memo(state)),
    ]:
        path.write_text(payload, encoding="utf-8")
        print(f"Wrote {path}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="Print memo to stdout, do not write files.")
    parser.add_argument("--force", action="store_true", help="Run verdict logic even if N < gate (for testing).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    state = build_state(forced=args.force)
    write_outputs(state, args.dry_run)
    return 0


if __name__ == "__main__":
    sys.exit(main())
