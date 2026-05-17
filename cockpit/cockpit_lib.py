"""
NEPSE Daily Cockpit — Day-2 layer: read-only loader + market breadth +
per-symbol volume/turnover/transaction/range anomaly flags.

Implements ONLY DEFINITIONS.md v0 sections 3a (breadth) and 3b (per-symbol
anomaly flags). NO sector layer (Day 3), NO broker layer (Day 3), NO report
rendering (Day 4). Thresholds are read FROM the frozen constants below, which
mirror the frozen contract and must not be tuned from outcomes (§6).

Strictly read-only against own-market/sharesansar_datascrape/data/*.csv.
Does not modify the scrape pipeline or any data. Pure computation.
"""
from __future__ import annotations

import csv
import glob
import os
import statistics as st
from dataclasses import dataclass, field

# --- frozen thresholds (mirror DEFINITIONS.md §3; do NOT tune from outcomes) --
LOOKBACK = 20            # trailing trading days, median-based
RVOL_FLAG = 3.0          # volume spike
TURNOVER_FLAG = 3.0      # turnover shock
TRANS_FLAG = 3.0         # transaction-count shock
RANGE_FLAG = 2.0         # range expansion
TOP_N_TURNOVER = 10      # turnover-concentration reporting

DATA_DIR = os.path.join(os.path.dirname(__file__), "..",
                        "sharesansar_datascrape", "data")

NUMERIC_COLS = ("Open", "High", "Low", "Close", "LTP", "VWAP", "Vol",
                "Prev. Close", "Turnover", "Trans.", "Diff", "Range",
                "Diff %", "Range %", "52 Weeks High", "52 Weeks Low")


def _num(v):
    """Parse '7,790,921.90' / '' / '-' -> float or None. Quirk-tolerant."""
    if v is None:
        return None
    s = str(v).strip().strip('"').replace(",", "")
    if s in ("", "-", "N/A", "NA"):
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _date_from_name(path):
    """05_12_2026.csv -> '2026-05-12' (filenames are MM_DD_YYYY)."""
    base = os.path.basename(path)[:-4]
    mm, dd, yyyy = base.split("_")
    return f"{yyyy}-{mm}-{dd}"


def list_trading_days():
    """All available scrape dates, ascending. (date_str, filepath)."""
    out = []
    for p in glob.glob(os.path.join(DATA_DIR, "*.csv")):
        try:
            out.append((_date_from_name(p), p))
        except Exception:  # noqa: BLE001 - skip malformed names
            continue
    out.sort()
    return out


def load_day(path):
    """symbol -> {col: float|str}. Read-only."""
    rows = {}
    with open(path, newline="", encoding="utf-8", errors="replace") as f:
        for r in csv.DictReader(f):
            sym = (r.get("Symbol") or "").strip()
            if not sym:
                continue
            rec = {"Symbol": sym}
            for c in NUMERIC_COLS:
                if c in r:
                    rec[c] = _num(r[c])
            rows[sym] = rec
    return rows


@dataclass
class MarketSnapshot:
    date: str
    symbols_traded: int
    advancers: int
    decliners: int
    unchanged: int
    breadth_pct: float | None
    pct_above_20d_avg: float | None
    new_52w_high: int
    new_52w_low: int
    top10_turnover_concentration: float | None
    history_depth: int           # how many prior days were available
    unusual: list = field(default_factory=list)  # per-symbol flag dicts


def _median(xs):
    xs = [x for x in xs if x is not None]
    return st.median(xs) if xs else None


def compute(target_date=None):
    """Build breadth + per-symbol anomaly flags for target_date
    (default: latest). Uses trailing LOOKBACK days for the medians."""
    days = list_trading_days()
    if not days:
        raise RuntimeError(f"no data files under {DATA_DIR}")
    idx = (len(days) - 1 if target_date is None
           else next(i for i, (d, _) in enumerate(days) if d == target_date))

    today_date, today_path = days[idx]
    today = load_day(today_path)
    prior_paths = [p for _, p in days[max(0, idx - LOOKBACK):idx]]
    prior = [load_day(p) for p in prior_paths]
    depth = len(prior)

    # per-symbol trailing series (prior days only, for medians)
    series: dict[str, dict[str, list]] = {}
    closes_for_ma: dict[str, list] = {}
    for day in prior:
        for sym, rec in day.items():
            s = series.setdefault(sym, {"Vol": [], "Turnover": [],
                                        "Trans.": [], "Range %": []})
            for k in ("Vol", "Turnover", "Trans.", "Range %"):
                s[k].append(rec.get(k))
            closes_for_ma.setdefault(sym, []).append(rec.get("Close"))

    adv = dec = unch = 0
    n_hi = n_lo = 0
    above = total_ma = 0
    turnovers = []
    unusual = []

    for sym, rec in today.items():
        close, prev = rec.get("Close"), rec.get("Prev. Close")
        if close is not None and prev is not None:
            if close > prev:
                adv += 1
            elif close < prev:
                dec += 1
            else:
                unch += 1

        # % above own 20d avg close (trailing incl. today)
        ma_hist = [c for c in closes_for_ma.get(sym, []) if c is not None]
        if close is not None and ma_hist:
            ma = st.mean((ma_hist + [close])[-LOOKBACK:])
            total_ma += 1
            if close > ma:
                above += 1

        hi52, lo52 = rec.get("52 Weeks High"), rec.get("52 Weeks Low")
        high, low = rec.get("High"), rec.get("Low")
        if high is not None and hi52 is not None and high >= hi52:
            n_hi += 1
        if low is not None and lo52 is not None and low <= lo52:
            n_lo += 1

        if rec.get("Turnover") is not None:
            turnovers.append(rec["Turnover"])

        # per-symbol anomaly flags vs own trailing medians
        s = series.get(sym)
        flags = {}
        if s and depth >= 5:
            mv = _median(s["Vol"])
            mt = _median(s["Turnover"])
            mtr = _median(s["Trans."])
            mr = _median(s["Range %"])
            v, t, tr, rg = (rec.get("Vol"), rec.get("Turnover"),
                            rec.get("Trans."), rec.get("Range %"))
            if mv and v is not None and mv > 0 and v / mv >= RVOL_FLAG:
                flags["volume_spike"] = round(v / mv, 2)
            if mt and t is not None and mt > 0 and t / mt >= TURNOVER_FLAG:
                flags["turnover_shock"] = round(t / mt, 2)
            if mtr and tr is not None and mtr > 0 and tr / mtr >= TRANS_FLAG:
                flags["transaction_shock"] = round(tr / mtr, 2)
            if mr and rg is not None and mr > 0 and rg / mr >= RANGE_FLAG:
                flags["range_expansion"] = round(rg / mr, 2)
        if flags:
            hi, lo = rec.get("High"), rec.get("Low")
            cl = rec.get("Close")
            loc = ((cl - lo) / (hi - lo)
                   if None not in (cl, hi, lo) and hi > lo else None)
            unusual.append({"symbol": sym, "close": close,
                            "day_change_pct": rec.get("Diff %"),
                            "close_location": (round(loc, 2)
                                               if loc is not None else None),
                            **flags})

    traded = len(today)
    top10 = None
    if turnovers:
        ts = sorted(turnovers, reverse=True)
        tot = sum(ts)
        if tot > 0:
            top10 = round(sum(ts[:TOP_N_TURNOVER]) / tot, 4)

    unusual.sort(key=lambda d: d.get("volume_spike", 0), reverse=True)

    return MarketSnapshot(
        date=today_date, symbols_traded=traded,
        advancers=adv, decliners=dec, unchanged=unch,
        breadth_pct=(round(adv / traded, 4) if traded else None),
        pct_above_20d_avg=(round(above / total_ma, 4) if total_ma else None),
        new_52w_high=n_hi, new_52w_low=n_lo,
        top10_turnover_concentration=top10,
        history_depth=depth, unusual=unusual)


if __name__ == "__main__":
    # Day-2 smoke check: latest day summary + a few unusual rows.
    snap = compute()
    print(f"Cockpit Day-2 smoke | date={snap.date} "
          f"history_depth={snap.history_depth}")
    print(f"  traded={snap.symbols_traded} "
          f"adv={snap.advancers} dec={snap.decliners} unch={snap.unchanged} "
          f"breadth={snap.breadth_pct} above20dMA={snap.pct_above_20d_avg}")
    print(f"  new52wH={snap.new_52w_high} new52wL={snap.new_52w_low} "
          f"top10_turnover_conc={snap.top10_turnover_concentration}")
    print(f"  unusual symbols flagged: {len(snap.unusual)}")
    for row in snap.unusual[:8]:
        print("   ", row)
