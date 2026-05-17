"""
Single-company dossier — Day-2 SAFE DATA LAYER (read-only, symbol-parametric).

Given a ticker, returns its: (1) daily OHLCV history, (2) per-day broker-flow
summary where coverage exists, (3) merged corporate-action / announcement
timeline. PURE DATA ACCESS — no rendering, no scoring, no ranking, no advice
(see dossier/DOSSIER_DEFINITIONS.md §2/§5). The final human-facing sections
depend on the trader friend's feedback and are intentionally NOT built here.

Strictly read-only. Does not modify any data, the scrape pipeline, the broker
ledger, or the archived nepse-volume-psychology-lab (never touched).

Reuses cockpit/cockpit_lib.py for OHLCV loading so the comma/`Prev. Close`/
`MM_DD_YYYY` quirk-handling stays single-sourced and consistent.
"""
from __future__ import annotations

import csv
import glob
import json
import os
import re
import sys
from dataclasses import dataclass, field

_HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(_HERE, "..", "cockpit"))
import cockpit_lib as ck  # noqa: E402  (read-only reuse of frozen loaders)

OWN = os.path.join(_HERE, "..")
FACT_CSV = os.path.join(OWN, "market-gist", "data", "validation",
                        "broker_flow_fact_table", "broker_flow_fact_table.csv")
COVERAGE_CSV = os.path.join(OWN, "market-gist", "data", "validation",
                            "broker_flow_fact_table",
                            "broker_flow_coverage_by_symbol.csv")
TIMELINE_GLOB = os.path.join(OWN, "market-gist", "data", "validation",
                             "historical_context_backfills",
                             "*corporate_action_timeline*.json")
ANNOUNCE = os.path.join(OWN, "experiments", "01-corporate-action", "data",
                        "raw", "{sym}", "company-announcements.json")

_TAG = re.compile(r"<[^>]+>")
_HREF = re.compile(r"href=['\"]([^'\"]+)['\"]")


# ---------------------------------------------------------------- price ----
def price_history(symbol: str) -> list[dict]:
    """Ascending list of {date, open, high, low, close, prev_close, vol,
    turnover, trans, range_pct, diff_pct} for `symbol`. Read-only."""
    rows = []
    for date, path in ck.list_trading_days():
        day = ck.load_day(path)
        r = day.get(symbol)
        if not r:
            continue
        rows.append({
            "date": date,
            "open": r.get("Open"), "high": r.get("High"),
            "low": r.get("Low"), "close": r.get("Close"),
            "prev_close": r.get("Prev. Close"), "vol": r.get("Vol"),
            "turnover": r.get("Turnover"), "trans": r.get("Trans."),
            "range_pct": r.get("Range %"), "diff_pct": r.get("Diff %"),
        })
    return rows


# ----------------------------------------------------------- broker flow ----
def _coverage(symbol: str) -> dict | None:
    if not os.path.exists(COVERAGE_CSV):
        return None
    with open(COVERAGE_CSV, newline="", encoding="utf-8") as f:
        for row in csv.DictReader(f):
            if row.get("symbol") == symbol:
                return row
    return None


def broker_flow(symbol: str) -> dict:
    """Per-day broker aggregates for `symbol`, streamed from the 41MB fact
    table (filtered, never loaded whole). Returns {coverage, by_date} where
    by_date[d] = {day_total_qty, top_buyers[], top_sellers[],
    top5_buy_share, top5_sell_share, net_leader} + a per-broker current
    net-side streak summary. Descriptive only."""
    cov = _coverage(symbol)
    per_date: dict[str, list[dict]] = {}
    if os.path.exists(FACT_CSV):
        with open(FACT_CSV, newline="", encoding="utf-8") as f:
            rd = csv.reader(f)
            header = next(rd)
            ix = {c: i for i, c in enumerate(header)}
            si = ix["symbol"]
            for row in rd:
                if row[si] != symbol:
                    continue
                d = row[ix["date"]]
                per_date.setdefault(d, []).append({
                    "broker": row[ix["broker_id"]],
                    "buy_qty": float(row[ix["buy_qty"]] or 0),
                    "sell_qty": float(row[ix["sell_qty"]] or 0),
                    "net_qty": float(row[ix["net_qty"]] or 0),
                    "day_total_qty": float(row[ix["day_total_qty"]] or 0),
                    "is_net_buyer": row[ix["is_net_buyer"]] == "True",
                })

    by_date = {}
    for d, recs in per_date.items():
        tot = recs[0]["day_total_qty"] if recs else 0.0
        buyers = sorted(recs, key=lambda x: x["buy_qty"], reverse=True)[:5]
        sellers = sorted(recs, key=lambda x: x["sell_qty"], reverse=True)[:5]
        leader = max(recs, key=lambda x: abs(x["net_qty"])) if recs else None
        by_date[d] = {
            "day_total_qty": tot,
            "top_buyers": [(b["broker"], b["buy_qty"]) for b in buyers],
            "top_sellers": [(s["broker"], s["sell_qty"]) for s in sellers],
            "top5_buy_share": (round(sum(b["buy_qty"] for b in buyers) / tot, 4)
                               if tot else None),
            "top5_sell_share": (round(sum(s["sell_qty"] for s in sellers)
                                      / tot, 4) if tot else None),
            "net_leader": ((leader["broker"], leader["net_qty"])
                           if leader else None),
        }

    # current net-side streak per broker (descriptive; no scoring)
    dates_desc = sorted(by_date, reverse=True)
    streaks: dict[str, int] = {}
    if dates_desc:
        side_by_day = {}
        for d, recs in per_date.items():
            for r in recs:
                side_by_day.setdefault(r["broker"], {})[d] = (
                    1 if r["net_qty"] > 0 else -1 if r["net_qty"] < 0 else 0)
        for br, m in side_by_day.items():
            first = m.get(dates_desc[0])
            if not first:
                continue
            n = 0
            for d in dates_desc:
                if m.get(d) == first and first != 0:
                    n += 1
                else:
                    break
            if n >= 3:
                streaks[br] = first * n  # sign encodes side, |n| length
    return {"coverage": cov, "by_date": by_date,
            "persistent_brokers": dict(sorted(
                streaks.items(), key=lambda kv: abs(kv[1]), reverse=True))}


# ------------------------------------------------------ corporate actions ----
def _clean(title: str) -> tuple[str, str | None]:
    url = None
    m = _HREF.search(title or "")
    if m:
        url = m.group(1)
    return _TAG.sub("", title or "").strip(), url


def corporate_actions(symbol: str) -> list[dict]:
    """Merged, date-sorted events for `symbol`: ShareSansar announcements
    (HTML stripped) + structured timeline records (typed dividend/bonus/agm/
    book-close). De-duplicates the `latest__` timeline copies."""
    events = []

    ap = ANNOUNCE.format(sym=symbol)
    if os.path.exists(ap):
        for a in json.load(open(ap, encoding="utf-8")):
            text, url = _clean(a.get("title", ""))
            events.append({"date": a.get("published_date"),
                           "kind": "announcement", "text": text,
                           "url": url, "source": "sharesansar_announcements"})

    seen = set()
    for f in sorted(glob.glob(TIMELINE_GLOB)):
        try:
            d = json.load(open(f, encoding="utf-8"))
        except Exception:  # noqa: BLE001
            continue
        for r in d.get("records", []):
            if r.get("symbol") != symbol:
                continue
            key = (r.get("event_date"), r.get("event_type"),
                   r.get("headline") or r.get("title"))
            if key in seen:
                continue
            seen.add(key)
            events.append({
                "date": r.get("event_date"),
                "kind": r.get("event_type") or "timeline_event",
                "text": (r.get("headline") or r.get("title")
                         or r.get("body", "")).strip(),
                "cash_dividend": r.get("cash_dividend") or None,
                "bonus_shares": r.get("bonus_shares") or None,
                "right_shares": r.get("right_shares") or None,
                "book_close_date": r.get("book_close_date") or None,
                "agm_date": r.get("agm_date") or None,
                "source": "corporate_action_timeline"})

    events = [e for e in events if e.get("date")]
    events.sort(key=lambda e: e["date"])
    return events


# ------------------------------------------------------------- assemble ----
@dataclass
class DossierData:
    symbol: str
    price: list = field(default_factory=list)
    broker: dict = field(default_factory=dict)
    events: list = field(default_factory=list)
    coverage_note: str = ""


def assemble(symbol: str) -> DossierData:
    p = price_history(symbol)
    b = broker_flow(symbol)
    e = corporate_actions(symbol)
    cov = b.get("coverage") or {}
    note = (
        f"OHLCV {p[0]['date'] if p else 'NA'}->{p[-1]['date'] if p else 'NA'} "
        f"({len(p)} days, NOT corp-action adjusted) | "
        f"broker flow {cov.get('first_date','NA')}->{cov.get('last_date','NA')}"
        f" ({cov.get('files_with_rows','0')} days, "
        f"{cov.get('unique_brokers','0')} brokers) | "
        f"events {len(e)} (announcements + timeline backfill, historical)")
    return DossierData(symbol, p, b, e, note)


if __name__ == "__main__":
    sym = sys.argv[1] if len(sys.argv) > 1 else "UPPER"
    dd = assemble(sym)
    print(f"=== dossier data smoke: {dd.symbol} ===")
    print("coverage:", dd.coverage_note)
    if dd.price:
        last = dd.price[-1]
        print("latest price row:", {k: last[k] for k in
              ("date", "close", "diff_pct", "vol", "turnover")})
    bd = dd.broker.get("by_date", {})
    if bd:
        ld = sorted(bd)[-1]
        x = bd[ld]
        print(f"latest broker day {ld}: top5_buy={x['top5_buy_share']} "
              f"top5_sell={x['top5_sell_share']} net_leader={x['net_leader']}")
        pb = dd.broker.get("persistent_brokers", {})
        print("persistent brokers (sign=side, |n|=days):",
              dict(list(pb.items())[:6]))
    print("events:", len(dd.events),
          "| first:", dd.events[0]["date"] if dd.events else "NA",
          "| last:", dd.events[-1]["date"] if dd.events else "NA")
    for ev in dd.events[-3:]:
        print("  -", ev["date"], ev["kind"], "|", ev["text"][:80])
