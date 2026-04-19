"""
Dividend Microstructure — Step 1A: Build Event Table

Produces the event-table.csv used by check_gate1.py and (later) run_h1.py.
Reads L-001's existing events.csv as the upstream source. Does not write anywhere
outside experiments/dividend-microstructure/. Does not modify any production file.

See PRE_REGISTRATION.md (revision 3) for the hypothesis this feeds.
See CONTRACT.md for isolation rules.

Usage:
    python experiments/dividend-microstructure/build_event_table.py

Output:
    experiments/dividend-microstructure/data/event_table.csv

--------------------------------------------------------------------------------
Data-reality adaptations flagged for Romeo review:

1. The pre-registration says "cash dividend events." L-001's event table has two
   event types with populated book_close_date: `cash_dividend` (16 events in
   target sectors) and `bonus_and_cash_dividend` (76 events in target sectors).
   Since both have a cash component and the ex-date mechanics apply to the cash
   portion, BOTH are included. Bonus-only events (`bonus_share`) remain excluded
   per pre-reg. A diagnostic `has_bonus_component` column flags compound events
   for sensitivity analysis (not for primary-test splitting).

2. L-001's `book_closure_notice` events (266 total) only have announcement_date
   populated, NOT book_close_date. To build the Cohort A / Cohort B split
   (which depends on whether an L-001 notice falls in [T_ex - 10, T_ex + 10]),
   we use an approximate matching heuristic: for each target event (symbol X,
   book_close_date D), find book_closure_notices for same symbol X with
   announcement_date within the window [D - 60, D - 1]. If any such notice
   exists with announcement_date within [D - 10 trading days, D + 10 trading
   days], the event is Cohort B. Otherwise Cohort A.

   This is the best reconstruction available from L-001's data. Flagged here
   so Romeo can review. If the reconstruction is wrong, Cohort A/B labels are
   suspect but individual event data is still correct.
"""
from __future__ import annotations

import csv
import os
import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Iterable

# Allow import of nepse_trading_calendar (lives in market-gist/automation/)
SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parent.parent
AUTOMATION_DIR = REPO_ROOT / "market-gist" / "automation"
sys.path.insert(0, str(AUTOMATION_DIR))
from nepse_trading_calendar import is_trading_weekday  # noqa: E402


L001_EVENTS_CSV = REPO_ROOT / "experiments" / "01-corporate-action" / "data" / "events.csv"
OUTPUT_DIR = SCRIPT_DIR / "data"
OUTPUT_CSV = OUTPUT_DIR / "event_table.csv"

# Pre-reg scope
TARGET_SECTORS = {"Commercial Bank", "Hydropower"}
PRIMARY_EVENT_TYPES = {"cash_dividend", "bonus_and_cash_dividend"}

# Event types that create same-symbol overlap (hard drop if within +/-10 trading days).
#
# Rationale: the AGM meeting is the generating event for the cash dividend being
# tested — AGM and its declared dividend are the SAME corporate-action cycle,
# not independent events. Dropping them would drop every dividend (they always
# co-occur). AGM MINUTES / RESULT PUBLICATION (etype `agm_minutes`) is kept as an
# overlap because it's a distinct event timing-wise; similarly `agm_notice` is a
# pre-meeting communication.
#
# Rights issues, bonus-only events, and other dividend events on the same symbol
# within the window represent genuine confounds (multi-cycle overlap) and are
# dropped.
OVERLAP_EVENT_TYPES = {
    "agm_minutes",
    "right_share",
    "right_share_notice",
    "right_share_listing_notice",
    "bonus_share",
    "bonus_share_notice",
    "bonus_listing_notice",
}

# Event type used for cohort split (L-001 anchor)
NOTICE_EVENT_TYPE = "book_closure_notice"

# Number of trading days for the overlap / cohort-split window
OVERLAP_WINDOW_DAYS = 10

# Calendar-day window for matching notice to a dividend event (notice publishes before book close)
NOTICE_MATCH_CALENDAR_DAYS_BACK = 60


def parse_iso(value: str) -> date | None:
    value = (value or "").strip()
    if not value:
        return None
    try:
        return datetime.strptime(value, "%Y-%m-%d").date()
    except ValueError:
        return None


def compute_t_ex(book_close: date) -> date:
    """T_ex = first trading session on or after book_close per the regime-aware calendar.

    book_close itself may be a non-trading day; advance forward to the next trading session.
    """
    cursor = book_close
    # Advance to the next trading weekday per nepse_trading_calendar
    # (this handles the April 2026 Sun-Thu -> Mon-Fri transition correctly).
    max_hops = 10
    for _ in range(max_hops):
        if is_trading_weekday(cursor):
            return cursor
        cursor = cursor + timedelta(days=1)
    raise RuntimeError(
        f"Could not find a trading weekday within {max_hops} days of {book_close}"
    )


def trading_days_between(a: date, b: date) -> int:
    """Count trading days between a and b, inclusive on both ends if a==b, else exclusive of a,
    per the regime-aware calendar. Negative if a > b.

    Returns the count with the sign of (b - a).
    """
    if a == b:
        return 0
    step = timedelta(days=1) if b > a else timedelta(days=-1)
    sign = 1 if b > a else -1
    count = 0
    cursor = a
    while cursor != b:
        cursor = cursor + step
        if is_trading_weekday(cursor):
            count += 1
    return sign * count


def load_l001_events() -> list[dict]:
    if not L001_EVENTS_CSV.exists():
        raise SystemExit(f"L-001 event table not found at {L001_EVENTS_CSV}")
    with L001_EVENTS_CSV.open("r", encoding="utf-8-sig") as fh:
        reader = csv.DictReader(fh)
        return [row for row in reader]


def build_target_events(all_events: list[dict]) -> list[dict]:
    """Filter to banks+hydros, cash_dividend + bonus_and_cash_dividend, with book_close_date."""
    targets = []
    for row in all_events:
        if row.get("sector") not in TARGET_SECTORS:
            continue
        if row.get("event_type") not in PRIMARY_EVENT_TYPES:
            continue
        bcd = parse_iso(row.get("book_close_date", ""))
        if bcd is None:
            continue
        targets.append({
            "symbol": row["symbol"],
            "sector": row["sector"],
            "event_type": row["event_type"],
            "event_id_source": row.get("source_url", ""),
            "fiscal_year": row.get("fiscal_year", ""),
            "announcement_date": row.get("announcement_date", ""),
            "book_close_date": row["book_close_date"],
            "ex_date": row.get("ex_date", ""),
            "distribution_date": row.get("distribution_date", ""),
            "cash_dividend_pct": row.get("cash_dividend_pct", ""),
            "bonus_share_pct": row.get("bonus_share_pct", ""),
            "total_dividend_pct": row.get("total_dividend_pct", ""),
            "raw_title": row.get("raw_title", ""),
            "agenda": row.get("agenda", ""),
            "has_bonus_component": row["event_type"] == "bonus_and_cash_dividend",
        })
    return targets


def detect_same_symbol_overlap(
    target: dict, all_events: list[dict]
) -> tuple[bool, list[str]]:
    """Return (has_overlap, list of offending event descriptions)."""
    sym = target["symbol"]
    t_ex = compute_t_ex(parse_iso(target["book_close_date"]))

    offenders = []
    for row in all_events:
        if row.get("symbol") != sym:
            continue
        etype = row.get("event_type")
        if etype not in OVERLAP_EVENT_TYPES:
            continue

        # Need some date to anchor the other event. Try in priority order.
        candidate_dates = [
            parse_iso(row.get("book_close_date", "")),
            parse_iso(row.get("ex_date", "")),
            parse_iso(row.get("meeting_date", "")),
            parse_iso(row.get("right_open_date", "")),
            parse_iso(row.get("distribution_date", "")),
            parse_iso(row.get("announcement_date", "")),
        ]
        other_date = next((d for d in candidate_dates if d is not None), None)
        if other_date is None:
            continue

        # Skip if it's the event itself (same sector+type+bcd string indicates the same row)
        if (
            etype == target["event_type"]
            and row.get("book_close_date", "") == target["book_close_date"]
        ):
            continue

        try:
            gap = trading_days_between(other_date, t_ex)
        except Exception:
            continue

        if abs(gap) <= OVERLAP_WINDOW_DAYS:
            offenders.append(f"{etype}@{other_date.isoformat()}(gap={gap}td)")

    return (bool(offenders), offenders)


def find_notice_for_event(
    target: dict, all_events: list[dict]
) -> tuple[str, int | None, str]:
    """For the target event, find the best-matching L-001 book_closure_notice.

    Returns (cohort_label, notice_to_t_ex_gap_trading_days, notice_details).
    cohort_label is 'A' (no notice within +/-10 trading days) or 'B' (notice within).
    """
    sym = target["symbol"]
    t_ex = compute_t_ex(parse_iso(target["book_close_date"]))
    window_start = t_ex - timedelta(days=NOTICE_MATCH_CALENDAR_DAYS_BACK)
    window_end = t_ex + timedelta(days=OVERLAP_WINDOW_DAYS + 5)  # small buffer

    best_notice = None
    best_notice_date = None
    best_gap_td = None
    for row in all_events:
        if row.get("symbol") != sym:
            continue
        if row.get("event_type") != NOTICE_EVENT_TYPE:
            continue
        ad = parse_iso(row.get("announcement_date", ""))
        if ad is None:
            continue
        if not (window_start <= ad <= window_end):
            continue

        try:
            gap = trading_days_between(ad, t_ex)
        except Exception:
            continue

        # Pick the notice closest to T_ex (smallest absolute gap)
        if best_gap_td is None or abs(gap) < abs(best_gap_td):
            best_notice = row
            best_notice_date = ad
            best_gap_td = gap

    if best_gap_td is not None and abs(best_gap_td) <= OVERLAP_WINDOW_DAYS:
        details = f"notice@{best_notice_date.isoformat()} ({best_gap_td}td from T_ex)"
        return ("B", best_gap_td, details)

    if best_gap_td is not None:
        details = f"notice@{best_notice_date.isoformat()} ({best_gap_td}td from T_ex, outside cohort window)"
        return ("A", best_gap_td, details)

    return ("A", None, "no matching notice found")


def build_event_table() -> list[dict]:
    all_events = load_l001_events()
    targets = build_target_events(all_events)
    print(f"Total target events before drops: {len(targets)}")

    rows = []
    n_dropped_overlap = 0
    for t in targets:
        bcd = parse_iso(t["book_close_date"])
        if bcd is None:
            continue
        t_ex = compute_t_ex(bcd)
        t_ex_offset_days = (t_ex - bcd).days

        has_overlap, offenders = detect_same_symbol_overlap(t, all_events)
        if has_overlap:
            n_dropped_overlap += 1
            continue

        cohort, notice_gap_td, notice_details = find_notice_for_event(t, all_events)

        rows.append({
            "symbol": t["symbol"],
            "sector": t["sector"],
            "event_type": t["event_type"],
            "fiscal_year": t["fiscal_year"],
            "announcement_date": t["announcement_date"],
            "book_close_date": t["book_close_date"],
            "t_ex": t_ex.isoformat(),
            "t_ex_offset_from_book_close_days": t_ex_offset_days,
            "cash_dividend_pct": t["cash_dividend_pct"],
            "bonus_share_pct": t["bonus_share_pct"],
            "total_dividend_pct": t["total_dividend_pct"],
            "has_bonus_component": t["has_bonus_component"],
            "cohort": cohort,
            "notice_to_t_ex_gap_trading_days": notice_gap_td if notice_gap_td is not None else "",
            "notice_details": notice_details,
            "raw_title": t["raw_title"],
        })

    print(f"Events dropped due to same-symbol overlap: {n_dropped_overlap}")
    print(f"Events in final table: {len(rows)}")
    cohort_a = [r for r in rows if r["cohort"] == "A"]
    cohort_b = [r for r in rows if r["cohort"] == "B"]
    print(f"  Cohort A (pure date-led, no notice overlap): {len(cohort_a)}")
    print(f"  Cohort B (notice overlap): {len(cohort_b)}")
    return rows


def write_output(rows: list[dict]) -> None:
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    if not rows:
        print(f"No rows to write. Creating empty file at {OUTPUT_CSV}")
        OUTPUT_CSV.write_text("", encoding="utf-8")
        return
    fieldnames = list(rows[0].keys())
    with OUTPUT_CSV.open("w", encoding="utf-8", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fieldnames)
        writer.writeheader()
        for r in rows:
            writer.writerow(r)
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


def main() -> int:
    rows = build_event_table()
    write_output(rows)
    return 0


if __name__ == "__main__":
    sys.exit(main())
