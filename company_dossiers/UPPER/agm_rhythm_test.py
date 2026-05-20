"""AGM-announcement reaction-pattern test for UPPER.

Case #1 (Apr 22 2026) implicitly hypothesised an "AGM rhythm" — sharp drop
the next trading day after AGM announcement, then recovery rally. This test
finds every AGM-related event in UPPER's history and measures the actual
+/−5 day price reaction. If there's a consistent rhythm across N events
the hypothesis lives; if not, Case #1's pattern was a coincidence.

Descriptive only.
"""
from __future__ import annotations

import os, sys, datetime as dt

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402


def main():
    x = dd.assemble("UPPER")
    # find AGM-related events
    AGM_KEYWORDS = ("agm", "annual general meeting")
    agm_events = []
    for e in x.events:
        text = (e.get("text") or "").lower()
        kind = (e.get("kind") or "").lower()
        if any(k in text for k in AGM_KEYWORDS) or "agm" in kind:
            agm_events.append(e)
    agm_events.sort(key=lambda e: e.get("date", ""))
    print(f"Found {len(agm_events)} AGM-related events in UPPER history:")
    for e in agm_events:
        print(f"  {e['date']}  {e.get('kind','')[:30]:<30}  "
              f"{(e.get('text') or '')[:90]}")

    # use nepsealpha adjusted daily series
    intra = x.intraday or {}
    rows = intra.get("direct_daily") or []
    rows = [r for r in rows if r.get("close") is not None]
    rows.sort(key=lambda r: r["date_np"])
    close_by_date = {r["date_np"]: r["close"] for r in rows}
    sorted_trading_dates = sorted(close_by_date)
    idx = {d: i for i, d in enumerate(sorted_trading_dates)}

    def move(d_event, k):
        """% move from event-day close to event+k trading days."""
        # find the trading day on or after d_event
        evt_i = next((i for i, d in enumerate(sorted_trading_dates)
                      if d >= d_event), None)
        if evt_i is None:
            return None, None, None
        ev_d = sorted_trading_dates[evt_i]
        if evt_i + k >= len(sorted_trading_dates):
            return None, None, ev_d
        d_target = sorted_trading_dates[evt_i + k]
        p0 = close_by_date[ev_d]
        pk = close_by_date[d_target]
        if not p0 or not pk:
            return None, None, ev_d
        return (pk - p0) / p0 * 100, d_target, ev_d

    print(f"\n{'event':<12}  {'first td':<12}  {'+1d':>7}  {'+3d':>7}  "
          f"{'+5d':>7}  {'+10d':>7}  {'+20d':>7}")
    print("-" * 80)
    results_1d = []
    results_5d = []
    results_10d = []
    for e in agm_events:
        d_evt = e.get("date")
        m1, _, ev_td = move(d_evt, 1)
        m3, _, _ = move(d_evt, 3)
        m5, _, _ = move(d_evt, 5)
        m10, _, _ = move(d_evt, 10)
        m20, _, _ = move(d_evt, 20)
        if m1 is not None: results_1d.append(m1)
        if m5 is not None: results_5d.append(m5)
        if m10 is not None: results_10d.append(m10)
        def f(x): return f"{x:>+6.2f}%" if x is not None else "    — "
        print(f"{d_evt or '?':<12}  {ev_td or '?':<12}  "
              f"{f(m1)}  {f(m3)}  {f(m5)}  {f(m10)}  {f(m20)}")

    def stats(arr, lab):
        if not arr:
            print(f"  {lab}: no data")
            return
        mean = sum(arr) / len(arr)
        pos = sum(1 for x in arr if x > 0)
        print(f"  {lab}: n={len(arr)}  mean={mean:+.2f}%  "
              f"positive {pos}/{len(arr)} = {pos/len(arr):.0%}  "
              f"range [{min(arr):+.2f}%, {max(arr):+.2f}%]")

    print("\nAggregate stats:")
    stats(results_1d, "+1 trading day")
    stats(results_5d, "+5 trading days")
    stats(results_10d, "+10 trading days")


if __name__ == "__main__":
    main()
