"""Sector-residual Rule-11 fingerprint test (Romeo Review #5 follow-up).

KNOWN GAP from METHODOLOGY Rule 13: UPPER has r=0.80 with hydropower sub-
index. Rule-11 broker fingerprints currently compute follow-through against
UPPER's ABSOLUTE returns — so a "+2.86% INFORMED" tag could be measuring
"broker was bullish during sector rally" not "broker had stock-specific
insight."

This test fits a beta vs the hydro sub-index using the BROKER-HISTORY-OVERLAP
period (2023-06 to 2026-05), computes UPPER's RESIDUAL returns, and re-runs
each broker's exact-5-trading-day forward follow-through against BOTH the
absolute and the residual return. The difference tells us how much of each
fingerprint is sector beta vs stock-specific.

Descriptive only. No buy/sell. Same Rule 11 discipline.
"""
from __future__ import annotations

import csv, os, sys, statistics as st
from collections import defaultdict

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
import dossier_data as dd  # noqa: E402

LAB_HYDRO = os.path.join(
    HERE, "..", "..", "..", "nepse-volume-psychology-lab",
    "reports", "path_b", "subindex_hydro.csv")
LAB_NEPSE = os.path.join(
    HERE, "..", "..", "..", "nepse-volume-psychology-lab",
    "reports", "path_b", "subindex_nepse.csv")
FACT = os.path.join(HERE, "..", "..", "market-gist", "data", "validation",
                    "broker_flow_fact_table", "broker_flow_fact_table.csv")
SYM = "UPPER"

FIRM = {
    "26": "Asian Securities", "28": "Shree Krishna", "34": "(unresolved)",
    "38": "Dipshikha Dhitopatra", "42": "Sani Securities",
    "44": "Dynamic Money Managers", "48": "(unresolved)",
    "49": "Online Securities", "58": "Naasa Securities",
    "88": "Blue Chip Securities",
}


def load_index_close(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rows.append((r["published_date"], float(r["current"])))
            except Exception:  # noqa: BLE001
                continue
    return dict(rows)


def load_hydro_close():
    return load_index_close(LAB_HYDRO)


def stream_symbol(symbol: str):
    with open(FACT, newline="", encoding="utf-8") as f:
        rd = csv.reader(f); h = next(rd); ix = {c: i for i, c in enumerate(h)}
        si = ix["symbol"]
        for r in rd:
            if r[si] != symbol:
                continue
            yield {"date": r[ix["date"]], "broker": r[ix["broker_id"]],
                   "net_qty": float(r[ix["net_qty"]] or 0)}


def main():
    x = dd.assemble(SYM)
    upper_daily = (x.intraday or {}).get("direct_daily") or []
    upper_close = {r["date_np"]: r["close"] for r in upper_daily
                   if r.get("close") is not None}
    hydro_close = load_hydro_close()
    common = sorted(set(upper_close) & set(hydro_close))
    if len(common) < 100:
        raise SystemExit("not enough common dates")

    # build daily returns
    upper_ret = {}
    hydro_ret = {}
    for i in range(1, len(common)):
        d0, d1 = common[i-1], common[i]
        upper_ret[d1] = (upper_close[d1] - upper_close[d0]) / upper_close[d0]
        hydro_ret[d1] = (hydro_close[d1] - hydro_close[d0]) / hydro_close[d0]

    # fit beta on the broker-history window (2023-06-11 -> 2026-05-15)
    fit_dates = [d for d in upper_ret
                 if "2023-06-11" <= d <= "2026-05-18"]
    if len(fit_dates) < 100:
        raise SystemExit("not enough fit dates")
    u = [upper_ret[d] for d in fit_dates]
    h = [hydro_ret[d] for d in fit_dates]
    mu_u, mu_h = sum(u) / len(u), sum(h) / len(h)
    cov = sum((u[i] - mu_u) * (h[i] - mu_h) for i in range(len(u))) / len(u)
    var_h = sum((h[i] - mu_h) ** 2 for i in range(len(h))) / len(h)
    beta = cov / var_h
    alpha = mu_u - beta * mu_h
    # residual returns: what UPPER did beyond sector beta
    residual_ret = {d: upper_ret[d] - (alpha + beta * hydro_ret[d])
                    for d in fit_dates}

    print(f"=== UPPER vs Hydro sub-index regression "
          f"({fit_dates[0]} -> {fit_dates[-1]}, n={len(fit_dates)}) ===")
    print(f"  beta = {beta:.3f}   alpha (daily) = {alpha*100:.4f}%")
    print(f"  → UPPER daily return ≈ {beta:.2f} × hydro daily return")

    # convert to forward-5-trading-day cumulative returns (both flavors)
    sorted_dates = sorted(upper_ret)
    idx = {d: i for i, d in enumerate(sorted_dates)}

    def fwd_5(d, ret_dict):
        i = idx.get(d)
        if i is None or i + 5 >= len(sorted_dates):
            return None
        # compound the 5-day return
        cum = 1.0
        for j in range(1, 6):
            cum *= (1 + ret_dict.get(sorted_dates[i + j], 0))
        return (cum - 1) * 100

    # broker leads
    by_date = defaultdict(list)
    for row in stream_symbol(SYM):
        by_date[row["date"]].append(row)

    # per-broker stats
    stats = defaultdict(lambda: {
        "n": 0, "abs_sum": 0.0, "res_sum": 0.0,
        "abs_n": 0, "res_n": 0,
    })
    for d, recs in by_date.items():
        leader = max(recs, key=lambda r: abs(r["net_qty"]))
        side = (1 if leader["net_qty"] > 0
                else -1 if leader["net_qty"] < 0 else 0)
        if side == 0 or d not in fit_dates:
            continue
        s = stats[leader["broker"]]
        s["n"] += 1
        # absolute fwd 5d
        f_abs = fwd_5(d, upper_ret)
        if f_abs is not None:
            s["abs_sum"] += side * f_abs
            s["abs_n"] += 1
        # residual fwd 5d — COMPOUNDED to match absolute (Romeo Review #6
        # fix: previous version summed residual daily returns while absolute
        # was compounded, causing threshold-sensitive inconsistency).
        i = idx.get(d)
        if i is not None and i + 5 < len(sorted_dates):
            cum_res = 1.0
            for j in range(1, 6):
                cum_res *= (1 + residual_ret.get(sorted_dates[i + j], 0))
            res_pct = (cum_res - 1) * 100
            s["res_sum"] += side * res_pct
            s["res_n"] += 1

    # Print comparison table for top brokers by lead count.
    # Verdict scheme per Romeo Review #6: band by residual magnitude+sign,
    # not by % of absolute. Drop hard INFORMED/FORCED in favour of soft
    # bands: residual-positive (>=+1.5%), near-threshold-positive
    # (+1.0% to +1.5%), residual-noise (|x|<1.0%), near-threshold-negative
    # (-1.5% to -1.0%), residual-negative (<=-1.5%). Sign-flip is its
    # own marker.
    top = sorted(stats.items(), key=lambda kv: kv[1]["n"], reverse=True)[:15]
    print(f"\n=== Rule-11 fingerprint: ABSOLUTE vs HYDRO-ADJUSTED RESIDUAL "
          f"+5td follow-through ===")
    print(f"(Both compounded. Hydro index likely includes UPPER as a "
          f"constituent — 'hydro-adjusted' is more accurate than "
          f"'stock-specific'; see Romeo Review #6.)\n")
    print(f"{'broker':>7}  {'firm':<25}  {'n':>4}  "
          f"{'absolute %':>11}  {'residual %':>11}  "
          f"{'sector-share':>13}  {'verdict (Romeo #6 bands)'}")
    print("-" * 125)
    for br, s in top:
        if s["abs_n"] == 0:
            continue
        abs_avg = s["abs_sum"] / s["abs_n"]
        res_avg = s["res_sum"] / s["res_n"] if s["res_n"] else None
        if res_avg is None:
            continue
        sector_share = (1 - res_avg / abs_avg) * 100 if abs(abs_avg) > 0.01 else None

        # residual-band classification
        if abs(res_avg) < 1.0:
            band = "residual-noise"
        elif 1.0 <= res_avg < 1.5:
            band = "near-threshold-pos"
        elif res_avg >= 1.5:
            band = "residual-positive"
        elif -1.5 < res_avg <= -1.0:
            band = "near-threshold-neg"
        else:
            band = "residual-negative"

        # sign-flip flag (independent of band)
        signed_abs = 1 if abs_avg > 0 else -1 if abs_avg < 0 else 0
        signed_res = 1 if res_avg > 0 else -1 if res_avg < 0 else 0
        flip = " (SIGN-FLIP vs absolute)" if (signed_abs != 0 and signed_res != 0
                                              and signed_abs != signed_res) else ""

        sec_str = f"{sector_share:+5.0f}%" if sector_share is not None else "  —"
        print(f"{br:>7}  {FIRM.get(br,'')[:25]:<25}  {s['n']:>4}  "
              f"{abs_avg:>+10.2f}%  {res_avg:>+10.2f}%  "
              f"{sec_str:>13}  {band}{flip}")

    # =============================================================
    # SENSITIVITY CHECK — same analysis but with NEPSE index (broader
    # benchmark) instead of hydropower sub-index. Romeo Review #6:
    # since UPPER is likely a constituent of hydro, the hydro-residual
    # is not fully independent of UPPER. NEPSE-index regression is the
    # cleaner sanity check.
    # =============================================================
    if not os.path.exists(LAB_NEPSE):
        print("\n[NEPSE-index sensitivity skipped — file not found]")
    else:
        nepse_close = load_index_close(LAB_NEPSE)
        common2 = sorted(set(upper_close) & set(nepse_close))
        if len(common2) < 100:
            print("\n[NEPSE-index sensitivity skipped — too few common dates]")
        else:
            n_ret = {}
            for i in range(1, len(common2)):
                d0, d1 = common2[i-1], common2[i]
                n_ret[d1] = (nepse_close[d1] - nepse_close[d0]) / nepse_close[d0]
            fit2 = [d for d in upper_ret
                    if d in n_ret and "2023-06-11" <= d <= "2026-05-18"]
            u2 = [upper_ret[d] for d in fit2]
            n2 = [n_ret[d] for d in fit2]
            mu_u2, mu_n2 = sum(u2)/len(u2), sum(n2)/len(n2)
            cov2 = sum((u2[i] - mu_u2) * (n2[i] - mu_n2) for i in range(len(u2))) / len(u2)
            var_n2 = sum((n2[i] - mu_n2) ** 2 for i in range(len(n2))) / len(n2)
            beta2 = cov2 / var_n2 if var_n2 > 0 else 0
            alpha2 = mu_u2 - beta2 * mu_n2
            res2_ret = {d: upper_ret[d] - (alpha2 + beta2 * n_ret[d])
                        for d in fit2}
            print(f"\n=== SENSITIVITY: UPPER vs NEPSE-index regression "
                  f"({fit2[0]} -> {fit2[-1]}, n={len(fit2)}) ===")
            print(f"  beta (vs NEPSE) = {beta2:.3f}   "
                  f"alpha (daily) = {alpha2*100:.4f}%")
            print(f"  → UPPER daily ret ≈ {beta2:.2f} × NEPSE-index daily ret")

            print(f"\n=== Naasa, DMM, Online and others — NEPSE-residual "
                  f"+5td check ===")
            print(f"{'broker':>7}  {'firm':<25}  {'n':>4}  "
                  f"{'absolute':>10}  {'hydro-res':>10}  "
                  f"{'NEPSE-res':>10}  {'NEPSE-band'}")
            print("-" * 105)
            for br, s in top:
                if s["abs_n"] == 0:
                    continue
                abs_avg = s["abs_sum"] / s["abs_n"]
                hres = s["res_sum"] / s["res_n"] if s["res_n"] else None
                # recompute residual against NEPSE for this broker
                lead_dates = []
                for d, recs in by_date.items():
                    leader = max(recs, key=lambda r: abs(r["net_qty"]))
                    if leader["broker"] != br:
                        continue
                    side = (1 if leader["net_qty"] > 0
                            else -1 if leader["net_qty"] < 0 else 0)
                    if side == 0 or d not in fit2:
                        continue
                    i = idx.get(d)
                    if i is None or i + 5 >= len(sorted_dates):
                        continue
                    cum = 1.0
                    for j in range(1, 6):
                        cum *= (1 + res2_ret.get(sorted_dates[i + j], 0))
                    lead_dates.append(side * (cum - 1) * 100)
                if not lead_dates:
                    continue
                n_res = sum(lead_dates) / len(lead_dates)
                if abs(n_res) < 1.0:
                    nband = "noise"
                elif 1.0 <= n_res < 1.5:
                    nband = "near-thr-pos"
                elif n_res >= 1.5:
                    nband = "residual-positive"
                elif -1.5 < n_res <= -1.0:
                    nband = "near-thr-neg"
                else:
                    nband = "residual-negative"
                hres_s = f"{hres:+9.2f}%" if hres is not None else "      —"
                print(f"{br:>7}  {FIRM.get(br,'')[:25]:<25}  {s['n']:>4}  "
                      f"{abs_avg:>+9.2f}%  {hres_s}  "
                      f"{n_res:>+9.2f}%  {nband}")

    # Summary
    print("\n=== Interpretation (Romeo Review #6 banded scheme) ===")
    print("- 'residual-positive' (>=+1.5%): hydro-adjusted positive context.")
    print("- 'near-threshold-pos' (+1.0% to +1.5%): hydro-adjusted positive "
          "but near the noise floor; treat softly.")
    print("- 'residual-noise' (|x|<1.0%): the absolute fingerprint, if any, "
          "was mostly hydro beta and does not survive adjustment.")
    print("- 'near-threshold-neg' (-1.5% to -1.0%): near noise floor on the "
          "negative side; treat softly.")
    print("- 'residual-negative' (<=-1.5%): hydro-adjusted negative context.")
    print("- '(SIGN-FLIP vs absolute)': absolute and residual disagree on "
          "direction; usually means absolute was sector-driven in the wrong "
          "direction; should be treated as low-confidence on small samples.")
    print()
    print("Important caveat (Romeo Review #6 P1): UPPER is likely a "
          "constituent of the hydropower sub-index, so the residual is not "
          "fully independent of UPPER. Frame as 'hydro-adjusted residual', "
          "NOT 'pure stock-specific skill'. A secondary check against the "
          "broader NEPSE index is recommended before treating these as "
          "final authoritative tags.")


if __name__ == "__main__":
    main()
