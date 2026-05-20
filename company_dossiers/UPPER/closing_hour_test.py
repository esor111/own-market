"""Closing-hour signature generalization test.

Apr 22 2026 had 48% of its volume in the final trading hour (14:00 NPT). I
extrapolated from N=1 to a "closing-hour = forced-flow" candidate rule.
This test asks: across all days where we have intraday data, does high
closing-hour concentration actually correlate with a different price-
behaviour pattern than high opening-hour concentration?

Uses the nepsealpha minute bars; computes per-day:
  - opening_hour_share = 11:00-12:00 NPT volume / day volume
  - closing_hour_share = 14:00-15:00 NPT volume / day volume
  - same-day net return (close vs open)
  - +5d forward return
Then splits days into HIGH-OPENING, HIGH-CLOSING, BALANCED and compares.

Descriptive only.
"""
from __future__ import annotations

import os, sys, statistics as st
from collections import defaultdict

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402


def main():
    x = dd.assemble("UPPER")
    intra = x.intraday or {}
    minute = intra.get("minute_bars", [])
    if not minute:
        print("no minute bars")
        return

    # Bucket by date + hour
    day_hour_vol = defaultdict(lambda: defaultdict(float))
    day_total = defaultdict(float)
    for bar in minute:
        d = bar.get("date_np")
        dt_str = bar.get("datetime_np", "")
        # extract HH from "YYYY-MM-DD HH:MM"
        try:
            hh = int(dt_str[11:13])
        except Exception:  # noqa: BLE001
            continue
        v = bar.get("volume") or 0
        day_hour_vol[d][hh] += v
        day_total[d] += v
    print(f"intraday days covered: {len(day_total)}")
    if not day_total:
        return

    # adjusted daily close
    daily = intra.get("direct_daily") or []
    close = {r["date_np"]: r["close"] for r in daily
             if r.get("close") is not None}
    sorted_dates = sorted(close)
    idx = {d: i for i, d in enumerate(sorted_dates)}

    # for each day with intraday data, compute shares + returns
    records = []
    for d, hours in day_hour_vol.items():
        tot = day_total[d]
        if tot < 1000:
            continue
        # NEPSE trades roughly 11:00-15:00. Treat hour 11 = opening, hour
        # 14 = closing.
        open_share = hours.get(11, 0) / tot
        close_share = hours.get(14, 0) / tot
        if d not in close or d not in idx:
            continue
        i = idx[d]
        same_day_ret = None
        if i > 0:
            p_prev = close[sorted_dates[i - 1]]
            p0 = close[d]
            if p_prev and p0:
                same_day_ret = (p0 - p_prev) / p_prev * 100
        fwd_5d = None
        if i + 5 < len(sorted_dates):
            p_fwd = close[sorted_dates[i + 5]]
            p0 = close[d]
            if p0 and p_fwd:
                fwd_5d = (p_fwd - p0) / p0 * 100
        records.append({
            "date": d, "tot": tot, "open_share": open_share,
            "close_share": close_share, "same_day_ret": same_day_ret,
            "fwd_5d": fwd_5d,
        })
    print(f"records with daily-close pairing: {len(records)}")

    # classify
    high_open = [r for r in records if r["open_share"] >= 0.40]
    high_close = [r for r in records if r["close_share"] >= 0.40]
    balanced = [r for r in records
                if r["open_share"] < 0.40 and r["close_share"] < 0.40]
    print(f"  HIGH-OPENING (>=40% in 11:00 hour): {len(high_open)} days")
    print(f"  HIGH-CLOSING (>=40% in 14:00 hour): {len(high_close)} days")
    print(f"  BALANCED:                            {len(balanced)} days")

    def summary(group, label):
        sd = [r["same_day_ret"] for r in group if r["same_day_ret"] is not None]
        f5 = [r["fwd_5d"] for r in group if r["fwd_5d"] is not None]
        if not sd or not f5:
            print(f"  {label}: insufficient")
            return
        print(f"  {label} (n_same_day={len(sd)}, n_fwd={len(f5)}):")
        print(f"      same-day return: mean {st.mean(sd):+.2f}%, "
              f"median {st.median(sd):+.2f}%, "
              f"positive {sum(1 for x in sd if x>0)}/{len(sd)} = "
              f"{sum(1 for x in sd if x>0)/len(sd):.0%}")
        print(f"      +5d forward:     mean {st.mean(f5):+.2f}%, "
              f"median {st.median(f5):+.2f}%, "
              f"positive {sum(1 for x in f5 if x>0)}/{len(f5)} = "
              f"{sum(1 for x in f5 if x>0)/len(f5):.0%}")

    print("\nGroup comparisons:")
    summary(high_open, "HIGH-OPENING")
    summary(high_close, "HIGH-CLOSING")
    summary(balanced, "BALANCED")

    # also show the most extreme ten of each
    print("\nTop 10 HIGH-CLOSING days (by closing-hour share):")
    hc = sorted(records, key=lambda r: r["close_share"], reverse=True)[:10]
    for r in hc:
        print(f"  {r['date']}  close_share={r['close_share']:.1%}  "
              f"same_day={r['same_day_ret']:+.2f}%  "
              f"fwd5d={r['fwd_5d']:+.2f}% "
              if r['same_day_ret'] is not None else f"  {r['date']}")
    print("\nTop 10 HIGH-OPENING days (by opening-hour share):")
    ho = sorted(records, key=lambda r: r["open_share"], reverse=True)[:10]
    for r in ho:
        print(f"  {r['date']}  open_share={r['open_share']:.1%}  "
              f"same_day={r['same_day_ret']:+.2f}%  "
              f"fwd5d={r['fwd_5d']:+.2f}% "
              if r['same_day_ret'] is not None else f"  {r['date']}")


if __name__ == "__main__":
    main()
