"""Hydropower-sector correlation test for UPPER.

The 2024 rally narrative in Case #3 attributes the +87% move to a UPPER-
specific seasonal-positioning pattern around the Aug 13 FY result print.
But if the entire hydropower sector rallied during the same window, UPPER
was a beta vehicle for sector flow, NOT an idiosyncratic story.

Compares UPPER's daily returns to the hydropower sub-index daily returns
across (a) the full window where both are available and (b) the 2024
rally specifically (2024-06-15 -> 2024-09-30).

Uses the lab's frozen sub-index data (`reports/path_b/subindex_hydro.csv`)
and the same nepsealpha adjusted UPPER daily as the broker analysis.

Descriptive only.
"""
from __future__ import annotations

import csv, os, sys, statistics as st

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402

LAB_HYDRO = os.path.join(
    HERE, "..", "..", "..", "nepse-volume-psychology-lab",
    "reports", "path_b", "subindex_hydro.csv")


def load_hydro():
    rows = []
    with open(LAB_HYDRO, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rows.append({"date": r["published_date"],
                             "close": float(r["current"])})
            except Exception:  # noqa: BLE001
                continue
    rows.sort(key=lambda x: x["date"])
    return rows


def main():
    x = dd.assemble("UPPER")
    intra = x.intraday or {}
    upper_daily = intra.get("direct_daily") or []
    upper_daily = [r for r in upper_daily if r.get("close") is not None]
    upper_daily.sort(key=lambda r: r["date_np"])
    upper_close = {r["date_np"]: r["close"] for r in upper_daily}

    if not os.path.exists(LAB_HYDRO):
        print("WARN: lab hydro CSV not at", LAB_HYDRO)
        return
    hydro = load_hydro()
    hydro_close = {r["date"]: r["close"] for r in hydro}
    print(f"UPPER daily (nepsealpha adj): {len(upper_close)} days "
          f"{min(upper_close)} -> {max(upper_close)}")
    print(f"Hydro sub-index (lab frozen): {len(hydro_close)} days "
          f"{min(hydro_close)} -> {max(hydro_close)}")

    # build daily returns aligned on common dates
    common_dates = sorted(set(upper_close) & set(hydro_close))
    print(f"common dates: {len(common_dates)} "
          f"({common_dates[0]} -> {common_dates[-1]})")

    upper_rets = []
    hydro_rets = []
    paired_dates = []
    for i in range(1, len(common_dates)):
        d0, d1 = common_dates[i - 1], common_dates[i]
        u_ret = (upper_close[d1] - upper_close[d0]) / upper_close[d0]
        h_ret = (hydro_close[d1] - hydro_close[d0]) / hydro_close[d0]
        upper_rets.append(u_ret)
        hydro_rets.append(h_ret)
        paired_dates.append(d1)

    def pearson(x, y):
        n = len(x)
        if n < 3:
            return None
        mx = sum(x) / n
        my = sum(y) / n
        sx = (sum((xi - mx) ** 2 for xi in x) / n) ** 0.5
        sy = (sum((yi - my) ** 2 for yi in y) / n) ** 0.5
        if sx == 0 or sy == 0:
            return None
        cov = sum((xi - mx) * (yi - my) for xi, yi in zip(x, y)) / n
        return cov / (sx * sy)

    full_corr = pearson(upper_rets, hydro_rets)
    print(f"\nFULL-WINDOW correlation (UPPER daily ret vs Hydro sub-index "
          f"daily ret): r = {full_corr:.3f} over n={len(upper_rets)} days")

    # window-specific: 2024 rally window
    def window(lo, hi):
        i_lo = next((i for i, d in enumerate(paired_dates) if d >= lo), None)
        i_hi = next((i for i, d in enumerate(paired_dates) if d > hi),
                    len(paired_dates))
        if i_lo is None:
            return None, 0, 0, 0, 0
        u = upper_rets[i_lo:i_hi]
        h = hydro_rets[i_lo:i_hi]
        r = pearson(u, h)
        # cumulative returns over window
        from math import prod
        u_cum = prod(1 + ur for ur in u) - 1
        h_cum = prod(1 + hr for hr in h) - 1
        return r, len(u), u_cum, h_cum, i_lo

    print("\nWindow-specific correlations + cumulative returns:")
    print(f"{'window':<35}  {'n':>4}  {'corr':>6}  {'UPPER%':>8}  "
          f"{'Hydro%':>8}  {'spread':>8}")
    print("-" * 90)
    windows = [
        ("2024 rally (Jun 30 -> Aug 27)", "2024-06-30", "2024-08-27"),
        ("2024 post-peak slide (Aug 16 -> Sep 26)", "2024-08-16",
         "2024-09-26"),
        ("Sep 2024 landslide window", "2024-09-27", "2024-12-31"),
        ("Mar 2026 rally (Mar 1 -> Mar 22)", "2026-03-01", "2026-03-22"),
        ("Apr 2026 (incl. broker-100 day)", "2026-04-01", "2026-04-30"),
        ("Full 2024", "2024-01-01", "2024-12-31"),
        ("Full 2025", "2025-01-01", "2025-12-31"),
        ("Full 2026 YTD", "2026-01-01", "2026-12-31"),
    ]
    for label, lo, hi in windows:
        r, n, u_cum, h_cum, _ = window(lo, hi)
        if r is None or n < 2:
            print(f"{label:<35}  {n:>4}  insufficient data")
            continue
        print(f"{label:<35}  {n:>4}  {r:>+6.2f}  {u_cum*100:>+7.1f}%  "
              f"{h_cum*100:>+7.1f}%  {(u_cum-h_cum)*100:>+7.1f}%")


if __name__ == "__main__":
    main()
