"""Render a UPPER price+volume chart from LOCAL data (no scraping, no auth).
Descriptive-only artifact for the dossier (DOSSIER_CONTRACT.md §5). No advice.
Marks corporate events, the Sept-2024 landslide window, the recent
persistent-broker streak window, and the rolling 52-week high/low.
"""
from __future__ import annotations

import os, sys, datetime as dt
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402

OUT = os.path.join(HERE, "charts", "upper_local_chart.png")
SYM = "UPPER"


def parse(d): return dt.date.fromisoformat(d)


def main():
    x = dd.assemble(SYM)
    rows = x.price
    if not rows:
        raise SystemExit("no price rows")
    dates = [parse(r["date"]) for r in rows]
    closes = [r["close"] for r in rows]
    vols = [r["vol"] or 0 for r in rows]

    # rolling 52-week (252 trading-day) high/low for context
    n = len(rows)
    win = 252
    hi52 = [max(closes[max(0, i - win + 1): i + 1]) for i in range(n)]
    lo52 = [min(closes[max(0, i - win + 1): i + 1]) for i in range(n)]

    fig, (ax1, ax2) = plt.subplots(
        2, 1, figsize=(14, 8), dpi=140, sharex=True,
        gridspec_kw={"height_ratios": [3, 1]})

    ax1.plot(dates, closes, color="#1f77b4", linewidth=1.1, label="Close")
    ax1.plot(dates, hi52, color="#999", linewidth=0.6, linestyle="--",
             alpha=0.7, label="rolling 52w high")
    ax1.plot(dates, lo52, color="#999", linewidth=0.6, linestyle=":",
             alpha=0.7, label="rolling 52w low")
    ax1.set_ylabel("Close (Rs)")
    ax1.set_title(
        f"UPPER — local OHLCV {dates[0]} -> {dates[-1]} "
        f"({n} trading days). NOT corp-action adjusted. "
        "Descriptive observation only.")
    ax1.grid(alpha=0.25)

    # Sept-2024 landslide window (88-day shutdown ~Sep 27 2024 -> Dec 24 2024)
    ax1.axvspan(dt.date(2024, 9, 27), dt.date(2024, 12, 24),
                color="red", alpha=0.10,
                label="Sep'24 landslide / 88-day shutdown")

    # Recent persistent-broker streak window (May 11 -> May 18 2026)
    ax1.axvspan(dt.date(2026, 5, 11), dt.date(2026, 5, 18),
                color="orange", alpha=0.15,
                label="May 11-18'26: persistent net-seller leaders")

    # Mark corporate events from dossier_data (announcements + timeline)
    # Cap labels to keep chart readable; mark all dots, label only the most
    # informative recent ones.
    LABEL_TYPES = {"announcement", "agm_notice", "book_closure",
                   "dividend_notice", "rights_notice", "bonus_notice"}
    labeled = 0
    for e in x.events:
        try:
            d = parse(e["date"])
        except Exception:
            continue
        if d < dates[0] or d > dates[-1]:
            continue
        # plot a small marker on the price line
        try:
            idx = next(i for i, dd_ in enumerate(dates) if dd_ >= d)
            ax1.scatter([d], [closes[idx]], s=22, marker="o",
                        facecolors="none", edgecolors="green",
                        linewidths=0.9, zorder=5)
        except StopIteration:
            continue
        # Label only Q-results from 2025-08 onward (so it's not a mess)
        if labeled < 6 and e["kind"] in LABEL_TYPES and d >= dt.date(2025, 8, 1):
            txt = (e["text"] or "")[:38].replace("Upper Tamakoshi Hydropower",
                                                 "UTHL")
            ax1.annotate(
                txt, xy=(d, closes[idx]),
                xytext=(-30, 22 if labeled % 2 == 0 else -28),
                textcoords="offset points", fontsize=7, color="#137",
                arrowprops=dict(arrowstyle="->", color="#137", lw=0.5),
                bbox=dict(boxstyle="round,pad=0.2", fc="#eef", ec="#aac",
                          lw=0.4))
            labeled += 1

    ax1.legend(loc="upper left", fontsize=8, framealpha=0.85)

    # Volume panel
    ax2.bar(dates, vols, color="#888", width=1.0)
    # 20-day median volume line for "what's normal"
    med = []
    for i in range(n):
        sl = sorted(v for v in vols[max(0, i - 19): i + 1] if v)
        med.append(sl[len(sl) // 2] if sl else 0)
    ax2.plot(dates, med, color="#d62728", linewidth=0.8,
             label="20-day median volume")
    ax2.set_ylabel("Volume")
    ax2.set_xlabel("Date")
    ax2.legend(loc="upper left", fontsize=8)
    ax2.grid(alpha=0.25)
    ax2.xaxis.set_major_locator(mdates.YearLocator())
    ax2.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

    fig.tight_layout()
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    fig.savefig(OUT)
    print("saved:", OUT)
    print(f"price range over series: low={min(closes):.2f} high={max(closes):.2f}")
    print(f"latest: {dates[-1]} close={closes[-1]:.2f} vol={vols[-1]}")


if __name__ == "__main__":
    main()
