"""Two self-tests in one script — Romeo Review #6 follow-ups.

Test A — DISPERSION / BOOTSTRAP CI on broker residual fingerprints.
   Right now we publish "+1.23% near-threshold-pos" as a point estimate.
   Compute the bootstrap 95% CI around that mean to tell whether the
   number is precise or just noise.

Test B — HYDRO INDEX SELF-INCLUSION CHECK.
   Romeo flagged: UPPER may be a heavy constituent of the hydropower
   sub-index, so the hydro-adjusted residual is partially circular.
   Quantify: correlation, variance ratio, and lag-1 relationships.

Descriptive only. No buy/sell.
"""
from __future__ import annotations

import csv, os, sys, random, statistics as st
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
TOP_BROKERS = ["58", "49", "44", "26", "34", "38", "42", "48", "88"]
FIRM = {
    "26": "Asian Securities", "28": "Shree Krishna", "34": "(unresolved)",
    "38": "Dipshikha Dhitopatra", "42": "Sani Securities",
    "44": "Dynamic Money Managers", "48": "(unresolved)",
    "49": "Online Securities", "58": "Naasa Securities",
    "88": "Blue Chip Securities",
}
N_BOOTSTRAP = 2000
SEED = 42


def load_index_close(path):
    rows = []
    with open(path, newline="", encoding="utf-8") as f:
        for r in csv.DictReader(f):
            try:
                rows.append((r["published_date"], float(r["current"])))
            except Exception:  # noqa: BLE001
                continue
    return dict(rows)


def stream_symbol(symbol: str):
    with open(FACT, newline="", encoding="utf-8") as f:
        rd = csv.reader(f); h = next(rd); ix = {c: i for i, c in enumerate(h)}
        for r in rd:
            if r[ix["symbol"]] != symbol:
                continue
            yield {"date": r[ix["date"]], "broker": r[ix["broker_id"]],
                   "net_qty": float(r[ix["net_qty"]] or 0)}


def main():
    random.seed(SEED)

    x = dd.assemble(SYM)
    upper_daily = (x.intraday or {}).get("direct_daily") or []
    upper_close = {r["date_np"]: r["close"] for r in upper_daily
                   if r.get("close") is not None}
    hydro_close = load_index_close(LAB_HYDRO)
    nepse_close = load_index_close(LAB_NEPSE)

    common_h = sorted(set(upper_close) & set(hydro_close))
    common_n = sorted(set(upper_close) & set(nepse_close))

    # daily returns
    u_ret = {}; h_ret = {}; n_ret = {}
    for i in range(1, len(common_h)):
        d0, d1 = common_h[i-1], common_h[i]
        u_ret[d1] = (upper_close[d1] - upper_close[d0]) / upper_close[d0]
        h_ret[d1] = (hydro_close[d1] - hydro_close[d0]) / hydro_close[d0]
    for i in range(1, len(common_n)):
        d0, d1 = common_n[i-1], common_n[i]
        if d1 not in n_ret:
            n_ret[d1] = (nepse_close[d1] - nepse_close[d0]) / nepse_close[d0]

    # ===================================================================
    # TEST B — HYDRO INDEX SELF-INCLUSION CHECK (do this first so it
    # informs how we interpret the residuals in Test A)
    # ===================================================================
    print("=" * 80)
    print("TEST B — Hydro index self-inclusion check")
    print("=" * 80)
    # Use the broker-history window for the analysis
    window_dates = [d for d in u_ret
                    if d in h_ret and "2023-06-11" <= d <= "2026-05-18"]
    if len(window_dates) < 100:
        print("insufficient overlap"); return
    u_w = [u_ret[d] for d in window_dates]
    h_w = [h_ret[d] for d in window_dates]
    n_w = [n_ret[d] for d in window_dates if d in n_ret]

    def pearson(a, b):
        if len(a) < 3 or len(a) != len(b):
            return None
        n = len(a); ma = sum(a)/n; mb = sum(b)/n
        sa = (sum((x-ma)**2 for x in a)/n) ** 0.5
        sb = (sum((y-mb)**2 for y in b)/n) ** 0.5
        if sa == 0 or sb == 0: return None
        return sum((a[i]-ma)*(b[i]-mb) for i in range(n))/(n*sa*sb)

    r_uh = pearson(u_w, h_w)
    var_u = st.variance(u_w)
    var_h = st.variance(h_w)
    var_ratio = var_u / var_h if var_h > 0 else None

    # Lag-1 check: does UPPER lead hydro (UPPER today vs hydro tomorrow)
    # or does hydro lead UPPER (hydro today vs UPPER tomorrow)?
    paired_dates = window_dates
    upper_today_hydro_tmrw = []
    hydro_today_upper_tmrw = []
    for i in range(len(paired_dates) - 1):
        d_today = paired_dates[i]; d_tmrw = paired_dates[i+1]
        upper_today_hydro_tmrw.append((u_ret[d_today], h_ret[d_tmrw]))
        hydro_today_upper_tmrw.append((h_ret[d_today], u_ret[d_tmrw]))
    r_upper_lead = pearson([x[0] for x in upper_today_hydro_tmrw],
                           [x[1] for x in upper_today_hydro_tmrw])
    r_hydro_lead = pearson([x[0] for x in hydro_today_upper_tmrw],
                           [x[1] for x in hydro_today_upper_tmrw])

    print(f"window: {window_dates[0]} -> {window_dates[-1]} (n={len(window_dates)})")
    print(f"UPPER vs HYDRO same-day correlation:    r = {r_uh:.3f}")
    if r_uh > 0.95:
        verdict_corr = "VERY HIGH — UPPER and hydro move nearly identically"
    elif r_uh > 0.85:
        verdict_corr = "HIGH — UPPER is likely a heavy hydro-index constituent"
    elif r_uh > 0.70:
        verdict_corr = "MODERATE — UPPER follows hydro but with idiosyncrasy"
    else:
        verdict_corr = "LOW — UPPER is mostly idiosyncratic"
    print(f"  → {verdict_corr}")
    print(f"Variance ratio (UPPER var / hydro var):  {var_ratio:.3f}")
    if var_ratio > 1.5:
        verdict_var = "UPPER more volatile than hydro index (consistent with single-stock vs basket; hydro is diversified)"
    elif 0.8 < var_ratio < 1.2:
        verdict_var = "UPPER and hydro have similar variance — suggests UPPER is a dominant weight, OR hydro has very few constituents"
    else:
        verdict_var = "UPPER less volatile than hydro — unusual, likely a weighting effect"
    print(f"  → {verdict_var}")
    print()
    print(f"Lag-1 cross-correlations:")
    print(f"  UPPER today → HYDRO tomorrow: r = {r_upper_lead:+.3f}")
    print(f"  HYDRO today → UPPER tomorrow: r = {r_hydro_lead:+.3f}")
    if abs(r_upper_lead) > abs(r_hydro_lead) + 0.05:
        verdict_lag = "UPPER leads hydro → UPPER moves first; hydro index price-incorporates UPPER → STRONG self-inclusion signal"
    elif abs(r_hydro_lead) > abs(r_upper_lead) + 0.05:
        verdict_lag = "HYDRO leads UPPER → sector moves first; UPPER follows → weaker self-inclusion concern"
    else:
        verdict_lag = "Roughly contemporaneous → indeterminate from lag alone"
    print(f"  → {verdict_lag}")
    print()

    # Comparison: UPPER vs NEPSE same-day
    r_un = pearson([u_ret[d] for d in window_dates if d in n_ret],
                   [n_ret[d] for d in window_dates if d in n_ret])
    print(f"For comparison — UPPER vs NEPSE-index r = {r_un:.3f} "
          f"(NEPSE is broader; UPPER is much smaller weight there)")

    # ===================================================================
    # TEST A — BOOTSTRAP CI ON BROKER RESIDUAL FINGERPRINTS
    # ===================================================================
    # First need to refit beta + compute residuals (same as the original
    # sector_residual_test.py)
    n = len(u_w); mu_u = sum(u_w)/n; mu_h = sum(h_w)/n
    cov_uh = sum((u_w[i]-mu_u)*(h_w[i]-mu_h) for i in range(n))/n
    beta_h = cov_uh / var_h
    alpha_h = mu_u - beta_h * mu_h
    h_residual_ret = {d: u_ret[d] - (alpha_h + beta_h * h_ret[d])
                      for d in window_dates}

    # Same for NEPSE
    common_un = [d for d in window_dates if d in n_ret]
    u_un = [u_ret[d] for d in common_un]
    n_un = [n_ret[d] for d in common_un]
    nn = len(u_un); mu_u2 = sum(u_un)/nn; mu_n = sum(n_un)/nn
    cov_un = sum((u_un[i]-mu_u2)*(n_un[i]-mu_n) for i in range(nn))/nn
    var_n_arr = st.variance(n_un)
    beta_n = cov_un / var_n_arr if var_n_arr > 0 else 0
    alpha_n = mu_u2 - beta_n * mu_n
    n_residual_ret = {d: u_ret[d] - (alpha_n + beta_n * n_ret[d])
                      for d in common_un}

    # broker leads
    by_date = defaultdict(list)
    for row in stream_symbol(SYM):
        by_date[row["date"]].append(row)

    sorted_dates = sorted(window_dates)
    idx_h = {d: i for i, d in enumerate(sorted_dates)}

    sorted_dates_n = sorted(common_un)
    idx_n = {d: i for i, d in enumerate(sorted_dates_n)}

    def compute_lead_returns(broker_id, residual_map, sorted_d, idx_map):
        """Return list of side-signed compounded 5-trading-day residual
        returns for each lead day of broker_id."""
        out = []
        for d, recs in by_date.items():
            if d not in idx_map:
                continue
            leader = max(recs, key=lambda r: abs(r["net_qty"]))
            if leader["broker"] != broker_id:
                continue
            side = (1 if leader["net_qty"] > 0
                    else -1 if leader["net_qty"] < 0 else 0)
            if side == 0:
                continue
            i = idx_map[d]
            if i + 5 >= len(sorted_d):
                continue
            cum = 1.0
            for j in range(1, 6):
                cum *= (1 + residual_map.get(sorted_d[i + j], 0))
            out.append(side * (cum - 1) * 100)
        return out

    def bootstrap_ci(values, n_iter=N_BOOTSTRAP, q=(2.5, 97.5)):
        if len(values) < 2:
            return None, None, None
        means = []
        N = len(values)
        for _ in range(n_iter):
            sample = [values[random.randint(0, N - 1)] for _ in range(N)]
            means.append(sum(sample) / N)
        means.sort()
        lo = means[int(q[0] / 100 * len(means))]
        hi = means[int(q[1] / 100 * len(means))]
        return sum(values) / N, lo, hi

    print()
    print("=" * 80)
    print("TEST A — Bootstrap 95% CI on broker residual fingerprints")
    print("=" * 80)
    print(f"(n_bootstrap = {N_BOOTSTRAP}, seed = {SEED})")
    print()
    print(f"{'broker':>7}  {'firm':<22}  {'n':>3}  "
          f"{'hydro-residual mean':>21}  {'95% CI':>22}  "
          f"{'NEPSE-residual mean':>21}  {'95% CI':>22}  {'verdict'}")
    print("-" * 175)

    for br in TOP_BROKERS:
        h_vals = compute_lead_returns(br, h_residual_ret, sorted_dates, idx_h)
        n_vals = compute_lead_returns(br, n_residual_ret, sorted_dates_n, idx_n)
        if not h_vals:
            continue
        h_mean, h_lo, h_hi = bootstrap_ci(h_vals)
        n_mean, n_lo, n_hi = bootstrap_ci(n_vals) if n_vals else (None, None, None)

        # verdict on whether CI is tight vs wide
        def width(lo, hi):
            return hi - lo if (lo is not None and hi is not None) else None
        h_width = width(h_lo, h_hi)

        # is the CI tight enough to make the mean meaningful?
        # CI width <= 3 percentage points = tight; > 6 = very wide
        if h_width is None:
            verdict = "—"
        elif h_lo > 0 and h_hi > 0:
            verdict = "CI excludes zero on positive side"
        elif h_lo < 0 and h_hi < 0:
            verdict = "CI excludes zero on negative side"
        else:
            verdict = "CI straddles zero — mean is NOT significant"

        h_ci_str = f"[{h_lo:+5.2f}, {h_hi:+5.2f}]" if h_lo is not None else "—"
        n_ci_str = f"[{n_lo:+5.2f}, {n_hi:+5.2f}]" if n_lo is not None else "—"
        h_mean_str = f"{h_mean:+6.2f}%" if h_mean is not None else "—"
        n_mean_str = f"{n_mean:+6.2f}%" if n_mean is not None else "—"

        print(f"{br:>7}  {FIRM.get(br,'')[:22]:<22}  {len(h_vals):>3}  "
              f"{h_mean_str:>21}  {h_ci_str:>22}  "
              f"{n_mean_str:>21}  {n_ci_str:>22}  {verdict}")

    print()
    print("=== Interpretation ===")
    print("- CI EXCLUDES ZERO on positive side: residual mean is significantly")
    print("  positive at 95% (relative to bootstrap distribution). Tag holds.")
    print("- CI EXCLUDES ZERO on negative side: residual mean is significantly")
    print("  negative. Tag holds.")
    print("- CI STRADDLES ZERO: the mean is not statistically distinguishable")
    print("  from noise; the tag should be softened or dropped.")
    print("- This is a bootstrap, NOT a parametric significance test.")
    print("  Assumes lead days are exchangeable (no autocorrelation effects).")


if __name__ == "__main__":
    main()
