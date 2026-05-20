"""Deep 5-year structural + smart-money fingerprinting analysis for UPPER.
Combines: full intraday history (nepsealpha) + broker fact table +
corporate-action events + local OHLCV. Descriptive only.
"""
from __future__ import annotations

import os, sys, csv, json, statistics as st, datetime as dt
from collections import defaultdict

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402

SYM = "UPPER"
FACT = os.path.join(HERE, "..", "..", "market-gist", "data", "validation",
                    "broker_flow_fact_table", "broker_flow_fact_table.csv")


def stream_symbol(symbol: str):
    with open(FACT, newline="", encoding="utf-8") as f:
        rd = csv.reader(f); h = next(rd); ix = {c: i for i, c in enumerate(h)}
        si = ix["symbol"]
        for r in rd:
            if r[si] != symbol:
                continue
            yield {
                "date": r[ix["date"]],
                "broker": r[ix["broker_id"]],
                "buy_qty": float(r[ix["buy_qty"]] or 0),
                "sell_qty": float(r[ix["sell_qty"]] or 0),
                "net_qty": float(r[ix["net_qty"]] or 0),
                "day_total_qty": float(r[ix["day_total_qty"]] or 0),
                "is_net_buyer": r[ix["is_net_buyer"]] == "True",
            }


def main():
    x = dd.assemble(SYM)
    print("=== UPPER deep 5-year analysis ===")
    print("coverage:", x.coverage_note)
    print()

    # =================== Phase A — structural / event scan ===================
    intra = x.intraday or {}
    daily_full = intra.get("direct_daily", [])  # from nepsealpha daily endpoint
    if not daily_full:
        print("no intraday daily — falling back to local")
        rows = [{"date_np": r["date"], "open": r["open"], "high": r["high"],
                 "low": r["low"], "close": r["close"], "volume": r["vol"] or 0}
                for r in x.price]
    else:
        rows = daily_full
    rows = [r for r in rows if r.get("close") is not None]
    rows.sort(key=lambda r: r["date_np"])

    n = len(rows)
    print(f"Phase A — 5yr daily series: {n} bars, "
          f"{rows[0]['date_np']} -> {rows[-1]['date_np']}")
    closes = [r["close"] for r in rows]
    vols = [r["volume"] or 0 for r in rows]
    print(f"  All-time high: {max(closes):.2f} ({rows[max(range(n), key=lambda i: closes[i])]['date_np']})")
    print(f"  All-time low : {min(closes):.2f} ({rows[min(range(n), key=lambda i: closes[i])]['date_np']})")
    print(f"  Latest:        {closes[-1]:.2f} ({rows[-1]['date_np']})")

    # top 30 daily volume bars over 5 years
    indexed = list(enumerate(rows))
    indexed.sort(key=lambda kv: kv[1]["volume"] or 0, reverse=True)
    print("\nTop 30 highest-volume days across 5 years:")
    print("  rank  date         close   diff%    vol         year")
    for rank, (i, r) in enumerate(indexed[:30], 1):
        prev = rows[i-1]["close"] if i > 0 else r["close"]
        diff = ((r["close"] - prev) / prev * 100) if prev else 0
        yr = r["date_np"][:4]
        print(f"  {rank:>3}.  {r['date_np']}  {r['close']:>6.2f}  "
              f"{diff:>+6.2f}%  {(r['volume'] or 0):>10,.0f}  {yr}")

    # bucket those top 30 by year
    year_bucket = defaultdict(list)
    for i, r in indexed[:30]:
        year_bucket[r["date_np"][:4]].append(r["date_np"])
    print("\nTop-30 by year (volume-event clustering):")
    for yr in sorted(year_bucket):
        print(f"  {yr}: {len(year_bucket[yr])} days  ({', '.join(year_bucket[yr][:6])}{'...' if len(year_bucket[yr])>6 else ''})")

    # ====== Phase B — broker fingerprinting (informed vs forced over full data) ======
    print("\n\nPhase B — Broker fingerprinting across full broker history")
    by_date = defaultdict(list)
    for row in stream_symbol(SYM):
        by_date[row["date"]].append(row)
    dates = sorted(by_date)
    print(f"  broker history: {dates[0]} -> {dates[-1]} ({len(dates)} days)")

    # build close-by-date map (from intraday daily if available, else local price)
    close_by_date = {r["date_np"]: r["close"] for r in rows}

    # For each broker: appearances, days as net leader (|net_qty| was max that day),
    # mean 5-day forward price move following their LEAD day in their net direction
    broker_stats = defaultdict(lambda: {
        "appearances": 0,
        "lead_days": 0,
        "lead_dates": [],
        "lead_direction_sum_5d": 0.0,  # +ve = price moved their way
        "lead_dir_count": 0,
        "max_abs_net": 0.0,
        "total_buy": 0.0, "total_sell": 0.0,
    })
    for d, recs in by_date.items():
        # who was the day's net leader?
        leader = max(recs, key=lambda r: abs(r["net_qty"]))
        for r in recs:
            s = broker_stats[r["broker"]]
            s["appearances"] += 1
            s["total_buy"] += r["buy_qty"]
            s["total_sell"] += r["sell_qty"]
            if abs(r["net_qty"]) > s["max_abs_net"]:
                s["max_abs_net"] = abs(r["net_qty"])
        # mark the leader
        s = broker_stats[leader["broker"]]
        s["lead_days"] += 1
        s["lead_dates"].append(d)
        # forward 5d price change in their direction
        if d in close_by_date:
            d_dt = dt.date.fromisoformat(d)
            d5 = (d_dt + dt.timedelta(days=10)).isoformat()  # ~5 trading days
            forward = None
            for dd_ in sorted(close_by_date):
                if dd_ > d and dd_ <= d5:
                    forward = close_by_date[dd_]
            if forward and close_by_date[d]:
                move = (forward - close_by_date[d]) / close_by_date[d] * 100
                side = 1 if leader["net_qty"] > 0 else -1 if leader["net_qty"] < 0 else 0
                if side != 0:
                    s["lead_direction_sum_5d"] += side * move
                    s["lead_dir_count"] += 1

    # Print brokers ranked by lead_days, with informed-vs-forced classification
    leaders = sorted(broker_stats.items(),
                     key=lambda kv: kv[1]["lead_days"], reverse=True)
    print("\nTop 15 brokers by 'day net-leader' appearances (descriptive):")
    print(f"  {'broker':>6}  {'lead':>5}  {'appear':>6}  {'max_net':>10}  "
          f"{'avg_5d_dir%':>11}  {'n':>3}  {'classification'}")
    for br, s in leaders[:15]:
        avg = (s["lead_direction_sum_5d"] / s["lead_dir_count"]
               if s["lead_dir_count"] else None)
        # classification: +avg = informed (price followed them), -avg = forced
        if avg is None:
            kind = "—"
        elif avg > 1.0:
            kind = "INFORMED  (price followed by avg +%g%% over 5d)" % round(avg, 2)
        elif avg < -1.0:
            kind = "FORCED?   (price went avg %g%% AGAINST them)" % round(avg, 2)
        else:
            kind = "NOISE     (~flat follow-through)"
        print(f"  {br:>6}  {s['lead_days']:>5}  {s['appearances']:>6}  "
              f"{s['max_abs_net']:>10,.0f}  "
              f"{(f'{avg:+.2f}' if avg is not None else 'NA'):>11}  "
              f"{s['lead_dir_count']:>3}  {kind}")

    # =========== Phase C — what's going on in current persistent layer ===========
    print("\n\nPhase C — current persistent layer (last 30 days):")
    recent_dates = dates[-30:]
    side_by_broker: dict[str, dict[str, int]] = defaultdict(dict)
    for d in recent_dates:
        for r in by_date[d]:
            side_by_broker[r["broker"]][d] = (
                1 if r["net_qty"] > 0 else -1 if r["net_qty"] < 0 else 0)
    streaks = {}
    last_d = recent_dates[-1]
    for br, m in side_by_broker.items():
        first = m.get(last_d, 0)
        if first == 0:
            continue
        n_streak = 0
        for d in reversed(recent_dates):
            if m.get(d, 0) == first and first != 0:
                n_streak += 1
            else:
                break
        if n_streak >= 5:
            streaks[br] = first * n_streak
    print("Brokers currently on ≥5-day persistent same-side streak:")
    for br, n_signed in sorted(streaks.items(), key=lambda kv: -abs(kv[1])):
        side = "BUYER" if n_signed > 0 else "SELLER"
        ms = broker_stats[br]
        avg = (ms["lead_direction_sum_5d"] / ms["lead_dir_count"]
               if ms["lead_dir_count"] else None)
        kind = ("INFORMED" if (avg and avg > 1.0) else
                "FORCED?" if (avg and avg < -1.0) else "NOISE")
        print(f"  broker {br:>3}: {abs(n_signed)} days {side}  "
              f"(history: lead_days={ms['lead_days']}, "
              f"avg5d_following_lead={avg:+.2f}% [{kind}])"
              if avg is not None else
              f"  broker {br:>3}: {abs(n_signed)} days {side}  "
              f"(history: lead_days={ms['lead_days']}, no follow-through data)")


if __name__ == "__main__":
    main()
