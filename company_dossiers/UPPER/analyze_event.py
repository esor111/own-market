"""Focused broker-flow analysis around a single event date for UPPER (or any
symbol). Descriptive only — no scoring, no advice. Compares the event day's
broker mix vs the trailing 20-day baseline; lists each day's net leaders, top-5
concentration, and persistent streaks crossing the event.

Usage: python analyze_event.py YYYY-MM-DD [SYMBOL]
"""
from __future__ import annotations

import os, sys, csv, datetime as dt

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402

FACT = os.path.join(
    HERE, "..", "..", "market-gist", "data", "validation",
    "broker_flow_fact_table", "broker_flow_fact_table.csv")


def stream_symbol(symbol: str):
    """Yield (date, broker_id, buy_qty, sell_qty, net_qty, day_total_qty,
       is_net_buyer) for `symbol`."""
    with open(FACT, newline="", encoding="utf-8") as f:
        rd = csv.reader(f)
        h = next(rd); ix = {c: i for i, c in enumerate(h)}
        si = ix["symbol"]
        for r in rd:
            if r[si] != symbol:
                continue
            yield (r[ix["date"]], r[ix["broker_id"]],
                   float(r[ix["buy_qty"]] or 0),
                   float(r[ix["sell_qty"]] or 0),
                   float(r[ix["net_qty"]] or 0),
                   float(r[ix["day_total_qty"]] or 0),
                   r[ix["is_net_buyer"]] == "True")


def main():
    if len(sys.argv) < 2:
        raise SystemExit("usage: analyze_event.py YYYY-MM-DD [SYMBOL]")
    event = sys.argv[1]
    sym = sys.argv[2] if len(sys.argv) > 2 else "UPPER"
    edate = dt.date.fromisoformat(event)
    win_lo = (edate - dt.timedelta(days=14)).isoformat()
    win_hi = (edate + dt.timedelta(days=14)).isoformat()

    per_day: dict[str, list] = {}
    for row in stream_symbol(sym):
        d = row[0]
        if win_lo <= d <= win_hi:
            per_day.setdefault(d, []).append(row)

    if event not in per_day:
        print(f"NO broker data for {sym} on {event}")
        return

    # baseline: trailing 20 days of broker mix (the brokers active in
    # any of the prior days, with their average buy_qty/sell_qty share)
    baseline_dates = sorted(d for d in per_day if d < event)[-20:]
    baseline_brokers: dict[str, dict] = {}
    for d in baseline_dates:
        for (_, br, bq, sq, nq, tot, isb) in per_day[d]:
            x = baseline_brokers.setdefault(br, {"days": 0, "buy": 0.0,
                                                 "sell": 0.0})
            x["days"] += 1
            x["buy"] += bq
            x["sell"] += sq

    # event day analysis
    ev = per_day[event]
    tot = ev[0][5] if ev else 0
    print(f"=== {sym} event-day {event} ===")
    print(f"day_total_qty: {tot:,.0f}  (broker rows: {len(ev)})")

    buyers = sorted(ev, key=lambda r: r[2], reverse=True)[:8]
    sellers = sorted(ev, key=lambda r: r[3], reverse=True)[:8]
    net_leaders = sorted(ev, key=lambda r: abs(r[4]), reverse=True)[:5]
    top5_buy = sum(r[2] for r in buyers[:5])
    top5_sell = sum(r[3] for r in sellers[:5])
    print(f"top-5 buy concentration:  {top5_buy/tot:.1%}")
    print(f"top-5 sell concentration: {top5_sell/tot:.1%}")

    print("\nTop 8 BUYERS on event day:")
    for (_, br, bq, sq, nq, _, _) in buyers:
        bl = baseline_brokers.get(br, {"days": 0})
        flag = " *new vs trailing 20d*" if bl["days"] == 0 else ""
        print(f"  broker {br:>3}: buy={bq:8,.0f}  sell={sq:7,.0f}  "
              f"net={nq:+8,.0f}  (baseline days seen={bl['days']}){flag}")

    print("\nTop 8 SELLERS on event day:")
    for (_, br, bq, sq, nq, _, _) in sellers:
        bl = baseline_brokers.get(br, {"days": 0})
        flag = " *new vs trailing 20d*" if bl["days"] == 0 else ""
        print(f"  broker {br:>3}: buy={bq:7,.0f}  sell={sq:8,.0f}  "
              f"net={nq:+8,.0f}  (baseline days seen={bl['days']}){flag}")

    print("\nTop net leaders by |net_qty|:")
    for (_, br, bq, sq, nq, _, _) in net_leaders:
        side = "BUYER" if nq > 0 else "SELLER"
        print(f"  broker {br:>3}: net {nq:+,.0f}  ({side})")

    # +/- 7 trading days context: each day's top5 concentration & net leader
    print("\nSurrounding days context (date | top5_buy | top5_sell | "
          "net_leader_broker | net_qty | total_qty):")
    for d in sorted(per_day):
        rows = per_day[d]
        if not rows:
            continue
        tot_d = rows[0][5]
        b5 = sum(sorted(r[2] for r in rows)[-5:])
        s5 = sum(sorted(r[3] for r in rows)[-5:])
        nl = max(rows, key=lambda r: abs(r[4]))
        flag = "  <-- EVENT" if d == event else ""
        print(f"  {d}  buy5={b5/tot_d:5.1%}  sell5={s5/tot_d:5.1%}  "
              f"leader={nl[1]:>3} net={nl[4]:+8,.0f}  tot={tot_d:>9,.0f}{flag}")

    # Persistence streaks crossing the event: which brokers had a streak of
    # consistent net-side both before and after the event (a "regime" broker)?
    all_dates_sorted = sorted(per_day)
    side_map: dict[str, dict[str, int]] = {}
    for d in all_dates_sorted:
        for (_, br, bq, sq, nq, _, _) in per_day[d]:
            side_map.setdefault(br, {})[d] = (1 if nq > 0 else
                                              -1 if nq < 0 else 0)

    def streak_before_after(br):
        m = side_map[br]
        keys = all_dates_sorted
        idx = keys.index(event) if event in keys else None
        if idx is None or m.get(event, 0) == 0:
            return 0, 0
        side = m[event]
        before = 0
        i = idx - 1
        while i >= 0 and m.get(keys[i], 0) == side:
            before += 1
            i -= 1
        after = 0
        i = idx + 1
        while i < len(keys) and m.get(keys[i], 0) == side:
            after += 1
            i += 1
        return before, after

    print("\nBrokers with persistence ACROSS the event (net side same "
          "for >=2 days before AND after):")
    crossing = []
    for br in side_map:
        b, a = streak_before_after(br)
        if b >= 2 and a >= 2:
            side = "BUYER" if side_map[br][event] == 1 else "SELLER"
            crossing.append((br, b, a, side))
    for br, b, a, side in sorted(crossing, key=lambda x: -(x[1] + x[2])):
        print(f"  broker {br:>3}: {b}d before + {a}d after  ({side})")


if __name__ == "__main__":
    main()
