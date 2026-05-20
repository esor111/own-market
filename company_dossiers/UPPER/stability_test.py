"""Stability + reflexivity tests for Rule 11 broker fingerprints.

Built per the 2026-05-21 self-challenge pass: my own most-confident claim
(Naasa Securities INFORMED +2.86%, n=21) hasn't been tested for two
falsifiers that should disqualify it:

  A. STABILITY — is the signature concentrated in one window, or stable
     across multiple sub-periods? If it disappears in any one third, the
     signature is masking variance, not capturing pattern.

  B. REFLEXIVITY — is the +2.86% follow-through happening on day-0
     (alongside their flow, moving the market) or over the next 5 trading
     days (the market waking up to what they saw)? Reflexive flow looks
     identical to informed flow on average but means something completely
     different.

Descriptive only. No buy/sell. Same Rule 11 discipline.
"""
from __future__ import annotations

import os, sys, csv
from collections import defaultdict

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402

SYM = "UPPER"
FACT = os.path.join(HERE, "..", "..", "market-gist", "data", "validation",
                    "broker_flow_fact_table", "broker_flow_fact_table.csv")

# the brokers we want to scrutinise (the top informed/forced claims)
TARGETS = ["58", "44", "49", "34", "48", "38", "42", "26", "88"]


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


def compute_signatures(broker_id: str,
                       date_subset: set | None,
                       by_date: dict, close_by_date: dict,
                       sorted_trading_dates: list,
                       trading_day_index: dict):
    """Return (n_lead, avg_5d_follow_through, mean_day0_move,
    mean_day0_to_5_move) for the broker over the given date subset."""
    lead_dates = []
    for d, recs in by_date.items():
        if date_subset is not None and d not in date_subset:
            continue
        leader = max(recs, key=lambda r: abs(r["net_qty"]))
        if leader["broker"] == broker_id:
            lead_dates.append((d, leader["net_qty"]))

    n5 = 0
    sum_5d = 0.0
    sum_day0 = 0.0  # same-day move (close vs prior close)
    n_day0 = 0
    sum_day0_to_5 = 0.0  # move from day0 close to day+5 close (== existing measure)
    for d, nq in lead_dates:
        if d not in trading_day_index:
            continue
        i = trading_day_index[d]
        # day-0 same-day move
        if i > 0:
            p_prev = close_by_date[sorted_trading_dates[i - 1]]
            p0 = close_by_date[d]
            if p_prev and p0:
                side = 1 if nq > 0 else -1 if nq < 0 else 0
                if side != 0:
                    sum_day0 += side * (p0 - p_prev) / p_prev * 100
                    n_day0 += 1
        # day-0 to day+5
        if i + 5 < len(sorted_trading_dates):
            p0 = close_by_date[d]
            p5 = close_by_date[sorted_trading_dates[i + 5]]
            if p0 and p5:
                side = 1 if nq > 0 else -1 if nq < 0 else 0
                if side != 0:
                    sum_5d += side * (p5 - p0) / p0 * 100
                    sum_day0_to_5 += side * (p5 - p0) / p0 * 100
                    n5 += 1
    return {
        "n_lead": len(lead_dates),
        "avg_5d_followthrough": sum_5d / n5 if n5 else None,
        "n5": n5,
        "mean_same_day_move": sum_day0 / n_day0 if n_day0 else None,
        "n_day0": n_day0,
    }


def main():
    x = dd.assemble(SYM)
    # use nepsealpha adjusted daily series (consistent across the full
    # broker-data window 2023-06 -> 2026-05)
    intra = x.intraday or {}
    rows = intra.get("direct_daily") or []
    rows = [r for r in rows if r.get("close") is not None]
    rows.sort(key=lambda r: r["date_np"])
    close_by_date = {r["date_np"]: r["close"] for r in rows}
    sorted_trading_dates = sorted(close_by_date)
    trading_day_index = {d: i for i, d in enumerate(sorted_trading_dates)}

    by_date = defaultdict(list)
    for row in stream_symbol(SYM):
        by_date[row["date"]].append(row)
    dates = sorted(by_date)
    print(f"broker-history dates: {dates[0]} -> {dates[-1]} ({len(dates)} days)")

    # Split into three equal-time thirds
    n = len(dates)
    third = n // 3
    p1 = set(dates[:third])
    p2 = set(dates[third:2 * third])
    p3 = set(dates[2 * third:])
    print(f"\nThirds: P1 {dates[0]}->{dates[third-1]} ({len(p1)}d)  "
          f"P2 {dates[third]}->{dates[2*third-1]} ({len(p2)}d)  "
          f"P3 {dates[2*third]}->{dates[-1]} ({len(p3)}d)")

    print("\n" + "=" * 110)
    print("STABILITY TEST — avg_5d_follow_through computed separately in each third")
    print("=" * 110)
    print(f"{'broker':>7}  {'firm':<25}  {'full n':>7} {'full avg%':>10}  "
          f"{'P1 n':>5} {'P1 avg%':>9}  {'P2 n':>5} {'P2 avg%':>9}  "
          f"{'P3 n':>5} {'P3 avg%':>9}  {'verdict'}")
    print("-" * 145)

    FIRM = {
        "26": "Asian Securities", "28": "Shree Krishna", "34": "(unresolved)",
        "38": "Dipshikha Dhitopatra", "42": "Sani Securities",
        "44": "Dynamic Money Managers", "48": "(unresolved)",
        "49": "Online Securities", "58": "Naasa Securities",
        "88": "Blue Chip Securities",
    }

    for br in TARGETS:
        full = compute_signatures(br, None, by_date, close_by_date,
                                  sorted_trading_dates, trading_day_index)
        s1 = compute_signatures(br, p1, by_date, close_by_date,
                                sorted_trading_dates, trading_day_index)
        s2 = compute_signatures(br, p2, by_date, close_by_date,
                                sorted_trading_dates, trading_day_index)
        s3 = compute_signatures(br, p3, by_date, close_by_date,
                                sorted_trading_dates, trading_day_index)

        # verdict logic: signatures > +1% or < -1% need consistent sign in
        # all three thirds where the broker led ≥2 times. Otherwise UNSTABLE.
        signs = []
        for s in (s1, s2, s3):
            if s["n5"] >= 2 and s["avg_5d_followthrough"] is not None:
                if s["avg_5d_followthrough"] > 1.0:
                    signs.append("+")
                elif s["avg_5d_followthrough"] < -1.0:
                    signs.append("-")
                else:
                    signs.append("0")
            else:
                signs.append("?")

        if "+" in signs and "-" in signs:
            verdict = "*** UNSTABLE — flips sign across thirds ***"
        elif signs.count("+") >= 2 and "-" not in signs:
            verdict = "STABLE-POS"
        elif signs.count("-") >= 2 and "+" not in signs:
            verdict = "STABLE-NEG"
        elif signs.count("0") >= 2:
            verdict = "STABLE-NOISE"
        else:
            verdict = "INSUFFICIENT_DATA"

        def fmt(s):
            if s["avg_5d_followthrough"] is None:
                return ("  -", "      —  ")
            return (f"{s['n5']:>5}", f"{s['avg_5d_followthrough']:>+8.2f}%")

        n_full, a_full = (f"{full['n5']:>7}",
                          f"{full['avg_5d_followthrough']:>+9.2f}%"
                          if full["avg_5d_followthrough"] is not None
                          else "      — ")
        n1, a1 = fmt(s1); n2, a2 = fmt(s2); n3, a3 = fmt(s3)
        print(f"{br:>7}  {FIRM.get(br,'')[:25]:<25}  {n_full} {a_full}  "
              f"{n1} {a1}  {n2} {a2}  {n3} {a3}  {verdict}")

    print("\n" + "=" * 110)
    print("REFLEXIVITY TEST — same-day move vs day+5 move on lead days")
    print("=" * 110)
    print("If same-day ≈ day+5 cumulative move, the signature is reflexive")
    print("(price moved alongside the broker's flow that day). If day+5 >>")
    print("same-day, the market 'wakes up' over the following days — closer")
    print("to predictive/informed behaviour.\n")
    print(f"{'broker':>7}  {'firm':<25}  {'n':>4}  {'same-day avg%':>14}  "
          f"{'+5d cumul avg%':>16}  {'+5d − same-day':>16}  {'interpretation'}")
    print("-" * 130)
    for br in TARGETS:
        s = compute_signatures(br, None, by_date, close_by_date,
                               sorted_trading_dates, trading_day_index)
        d0 = s["mean_same_day_move"]
        d5 = s["avg_5d_followthrough"]
        if d0 is None or d5 is None:
            print(f"{br:>7}  {FIRM.get(br,'')[:25]:<25}  insufficient data")
            continue
        delta = d5 - d0
        if abs(d0) > abs(d5) * 1.5:
            interp = "REFLEXIVE? (same-day dominates)"
        elif abs(d5) > abs(d0) * 1.5:
            interp = "PREDICTIVE-LEANING (move continues after)"
        else:
            interp = "MIXED (both same-day and following days)"
        print(f"{br:>7}  {FIRM.get(br,'')[:25]:<25}  {s['n5']:>4}  "
              f"{d0:>+13.2f}%  {d5:>+15.2f}%  {delta:>+15.2f}%  {interp}")


if __name__ == "__main__":
    main()
