"""
Coverage report generator for the w7 seller-persistence replay backfill.

Produces `data/backfill_coverage_report.md` from the current state of the
broker_flow_ledger directory. Runs safely mid-scrape (for draft inspection)
or post-scrape (for the final deliverable).

Window: 2025-10-19 to 2026-04-18 (locked per PRE_REGISTRATION r4).
Symbols: NABIL, EBL, SANIMA (locked).
Gate: >=80% per symbol (all-or-nothing).

This script does NOT compute any signal, return, hit rate, or recommendation.
It is pure coverage accounting.
"""

from __future__ import annotations

import json
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path

# Make the nepse_trading_calendar module importable
AUTOMATION_DIR = Path(__file__).resolve().parents[2] / "market-gist" / "automation"
sys.path.insert(0, str(AUTOMATION_DIR))
from nepse_trading_calendar import is_trading_weekday  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parents[2]
LEDGER_ROOT = REPO_ROOT / "market-gist" / "broker_flow_ledger"
OUTPUT_PATH = Path(__file__).resolve().parent / "data" / "backfill_coverage_report.md"

SYMBOLS = ["NABIL", "EBL", "SANIMA"]
WINDOW_START = date(2025, 10, 19)
WINDOW_END = date(2026, 4, 18)
COVERAGE_GATE = 0.80


def enumerate_trading_days(start: date, end: date) -> list[date]:
    days = []
    current = start
    while current <= end:
        if is_trading_weekday(current):
            days.append(current)
        current += timedelta(days=1)
    return days


def symbol_ledger_dates(symbol: str) -> set[date]:
    sym_dir = LEDGER_ROOT / symbol
    if not sym_dir.exists():
        return set()
    dates = set()
    for p in sym_dir.iterdir():
        if p.suffix != ".json":
            continue
        stem = p.stem  # YYYY-MM-DD
        try:
            d = datetime.strptime(stem, "%Y-%m-%d").date()
            dates.add(d)
        except ValueError:
            continue
    return dates


def classify_missing(symbol: str, missing_dates: list[date]) -> dict[str, list[date]]:
    """Classify missing dates by inspecting the raw_merolagani payloads (if any)
    to distinguish 'scraped but empty' from 'never scraped'."""
    raw_root = LEDGER_ROOT / "raw_merolagani" / symbol
    categorized = {"never_scraped": [], "scraped_empty": [], "scraped_error": []}
    for d in missing_dates:
        iso = d.strftime("%Y-%m-%d")
        raw_path = raw_root / f"{iso}.json"
        if not raw_path.exists():
            categorized["never_scraped"].append(d)
            continue
        # Try to read pager/row info
        try:
            with open(raw_path, encoding="utf-8") as f:
                payload = json.load(f)
            row_count = int(payload.get("row_count_collected", 0) or 0)
            if row_count == 0:
                categorized["scraped_empty"].append(d)
            else:
                # Raw payload has rows but no canonical ledger written — odd case
                categorized["scraped_error"].append(d)
        except Exception:
            categorized["scraped_error"].append(d)
    return categorized


def main() -> int:
    trading_days = enumerate_trading_days(WINDOW_START, WINDOW_END)
    total_tds = len(trading_days)

    per_symbol = {}
    for sym in SYMBOLS:
        have = symbol_ledger_dates(sym)
        # Restrict to dates within window
        have_in_window = {d for d in have if WINDOW_START <= d <= WINDOW_END}
        covered = sorted(have_in_window & set(trading_days))
        missing = sorted(set(trading_days) - have_in_window)
        classified = classify_missing(sym, missing)
        coverage_pct = len(covered) / total_tds if total_tds else 0
        per_symbol[sym] = {
            "covered": covered,
            "missing": missing,
            "classified": classified,
            "coverage_pct": coverage_pct,
            "pass_gate": coverage_pct >= COVERAGE_GATE,
        }

    all_pass = all(s["pass_gate"] for s in per_symbol.values())

    # Determine scrape completeness: for each symbol, every trading day in window must have
    # EITHER a canonical ledger OR a raw_merolagani payload (meaning the scraper actually reached it).
    # "missing from ledger but also missing from raw_merolagani" = not yet attempted = scrape incomplete.
    def symbol_scrape_complete(sym: str) -> bool:
        raw_root = LEDGER_ROOT / "raw_merolagani" / sym
        raw_dates = set()
        if raw_root.exists():
            for p in raw_root.iterdir():
                if p.suffix == ".json":
                    try:
                        raw_dates.add(datetime.strptime(p.stem, "%Y-%m-%d").date())
                    except ValueError:
                        continue
        attempted = set(per_symbol[sym]["covered"]) | raw_dates
        # All trading days in window must be attempted for this symbol's backfill to be complete.
        return all(td in attempted for td in trading_days)

    all_complete = all(symbol_scrape_complete(sym) for sym in SYMBOLS)
    scrape_status = "COMPLETE" if all_complete else "IN PROGRESS (draft)"

    lines = []
    lines.append("# Backfill Coverage Report — w7 Seller-Persistence Replay")
    lines.append("")
    lines.append(f"**Generated:** {datetime.now().isoformat(timespec='seconds')}")
    lines.append(f"**Scrape status:** {scrape_status}")
    lines.append(f"**Window:** {WINDOW_START.isoformat()} to {WINDOW_END.isoformat()}")
    lines.append(f"**Symbols:** {', '.join(SYMBOLS)}")
    lines.append(f"**Trading days in window:** {total_tds}")
    lines.append(f"**Gate:** >={int(COVERAGE_GATE*100)}% per symbol, all-or-nothing")
    lines.append("")
    lines.append("---")
    lines.append("")
    lines.append("## Per-symbol coverage")
    lines.append("")
    lines.append("| Symbol | Covered | Missing | Coverage % | Pass 80% gate? |")
    lines.append("|---|---:|---:|---:|---|")
    for sym in SYMBOLS:
        s = per_symbol[sym]
        lines.append(
            f"| {sym} | {len(s['covered'])} | {len(s['missing'])} | "
            f"{s['coverage_pct']*100:.1f}% | "
            f"{'**PASS**' if s['pass_gate'] else '**FAIL**'} |"
        )
    lines.append("")
    lines.append(f"**All-three-symbols gate:** {'**PASS**' if all_pass else '**FAIL**'}")
    lines.append("")

    # Missing-date classification per symbol
    lines.append("## Missing dates by category")
    lines.append("")
    for sym in SYMBOLS:
        s = per_symbol[sym]
        c = s["classified"]
        lines.append(f"### {sym}")
        lines.append(f"- Never scraped (no raw payload): **{len(c['never_scraped'])}**")
        lines.append(f"- Scraped but empty (0 rows, likely holiday or no trading): **{len(c['scraped_empty'])}**")
        lines.append(f"- Scraped with rows but canonical ledger missing (unexpected): **{len(c['scraped_error'])}**")
        if c["scraped_empty"]:
            sample = ", ".join(d.isoformat() for d in c["scraped_empty"][:5])
            more = f" (+{len(c['scraped_empty']) - 5} more)" if len(c['scraped_empty']) > 5 else ""
            lines.append(f"  - Empty-day examples: {sample}{more}")
        if c["scraped_error"]:
            sample = ", ".join(d.isoformat() for d in c["scraped_error"][:5])
            more = f" (+{len(c['scraped_error']) - 5} more)" if len(c['scraped_error']) > 5 else ""
            lines.append(f"  - Ledger-missing-despite-rows examples: {sample}{more}")
        lines.append("")

    # Holiday-API-401 note per the authorization
    lines.append("## Operational notes")
    lines.append("")
    lines.append("- **Holiday API 401:** `https://www.nepalstock.com/api/nots/holiday/list` returned HTTP 401 during the scrape.")
    lines.append(
        "  The scraper falls back to `weekday_only_unverified` status. Affected dates are still counted as trading days "
        "if `is_trading_weekday` returns True under the NEPSE calendar module. No coverage interpretation change."
    )
    lines.append("- **Scope discipline:** this report computes coverage only. No signal computation, no forward returns, "
                 "no hit rate, no recommendation. Per PRE_REGISTRATION r4 and backfill authorization.")
    lines.append("")

    # Verdict on what the replay can do next
    lines.append("## Gate decision (per PRE_REGISTRATION r4 Step 2)")
    lines.append("")
    if scrape_status == "IN PROGRESS (draft)":
        lines.append("**This is a DRAFT report generated mid-scrape.** The gate decision below is provisional "
                     "and will be finalized when the scrape completes.")
        lines.append("")
    if all_pass:
        lines.append("All three symbols meet the >=80% coverage gate. Replay may proceed to r4 Step 3 "
                     "(w7 sub-rule code verification — pre-flight already completed in "
                     "`w7_rule_code_audit.md`, accepted by Romeo). Replay remains gated on Romeo's final sign-off "
                     "and INTERPRETATION_GATE.md post-cost actionability.")
    else:
        failing = [sym for sym, s in per_symbol.items() if not s["pass_gate"]]
        lines.append(f"Not all three symbols pass the >=80% gate. Failing: {', '.join(failing)}.")
        lines.append("")
        lines.append(
            "Per PRE_REGISTRATION r4 (all-or-nothing rule), the replay aborts. No subset hit rate. "
            "No subset recommendation. A per-symbol diagnostic requires a separate pre-registration."
        )

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")

    print(f"Wrote: {OUTPUT_PATH}")
    print(f"Scrape status: {scrape_status}")
    for sym in SYMBOLS:
        s = per_symbol[sym]
        print(f"  {sym}: {len(s['covered'])}/{total_tds} "
              f"({s['coverage_pct']*100:.1f}%) {'PASS' if s['pass_gate'] else 'FAIL'}")
    print(f"All-three-pass: {all_pass}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
