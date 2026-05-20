"""Daily-read renderer for a single-company dossier (DOSSIER_CONTRACT.md §3).
Produces one Markdown per trading day combining auto-assembled descriptive
sections (price/vol, anomalies, broker flow, persistence, recent events) +
empty human sections (today's read, later review) — append-only, immutable
once you fill them in.

Symbol-parametric. NO buy/sell, NO targets, NO predictions. Banned-words
discipline + observation-only stamps inherited from the contract.

Usage:  python daily_read.py [SYMBOL] [YYYY-MM-DD]
Defaults: SYMBOL=UPPER, DATE=latest available.
"""
from __future__ import annotations

import os, sys, csv, statistics as st, datetime as dt

HERE = os.path.dirname(__file__)
sys.path.insert(0, os.path.join(HERE, "..", "..", "dossier"))
sys.path.insert(0, os.path.join(HERE, "..", "..", "cockpit"))
import dossier_data as dd  # noqa: E402
import cockpit_lib as ck  # noqa: E402 (frozen thresholds + loader)

OUT_DIR = os.path.join(HERE, "daily_reads")

# Broker number -> firm name + Rule-11 fingerprint tag, for the daily read.
# Sources: merolagani.com/BrokerList.aspx + ShareSansar weekly broker summaries.
# Fingerprints from deep_analysis.py over 343 days of UPPER broker history,
# recomputed 2026-05-20 with exact-5-trading-day forward math + SPARSE tag
# for n<=10 (per Romeo review). Numbers are DESCRIPTIVE CONTEXT only — not
# signals to follow. See METHODOLOGY.md Rule 11.
BROKER_INFO = {
    # Soft-band tags 2026-05-21 (Romeo Review #6). Show NEPSE-residual /
    # hydro-residual where they agree or differ. INFORMED/FORCED labels
    # retired per Romeo #6. Descriptive context, NOT signals.
    "26": ("Asian Securities", "NEPSE-resid-neg / hydro-noise (n=7, benchmark-sensitive)"),
    "28": ("Shree Krishna Securities", "too sparse (3 leads)"),
    "34": ("(unresolved)", "noise both benchmarks (sign-flips vs absolute, n=15)"),
    "38": ("Dipshikha Dhitopatra", "RETIRED — residual noise both benchmarks (n=9; was hydro beta)"),
    "42": ("Sani Securities", "noise both benchmarks (n=22)"),
    "44": ("Dynamic Money Managers", "hydro-near-neg / NEPSE-noise (n=20; weakened from -6% absolute)"),
    "48": ("(unresolved)", "noise both benchmarks (n=11)"),
    "49": ("Online Securities", "NEPSE-residual-pos / hydro-near-pos (n=16; most robust)"),
    "58": ("Naasa Securities", "near-threshold-pos both benchmarks (n=21; most stable)"),
    "88": ("Blue Chip Securities", "borderline noise / near-thr-pos (n=8)"),
}


def _broker_tag(num: str) -> str:
    name, tag = BROKER_INFO.get(num, (None, None))
    if name:
        return f"**{num}** ({name}; {tag})"
    return f"**{num}**"

HEADER = (
    "_Descriptive single-company record. **No buy/sell advice, no return "
    "prediction, no edge claim.** Human notes are Ishwor's own opinion "
    "logged for later honest review, not a signal._\n"
)
FOOTER = (
    "\n---\n_This file describes the past and records opinion. It does not "
    "predict, recommend, or claim an edge._\n"
)


def _fmt(v, dp=2):
    if v is None:
        return "—"
    try:
        return f"{v:,.{dp}f}"
    except Exception:  # noqa: BLE001
        return str(v)


def _close_loc(o, h, l, c):
    if None in (h, l, c) or h <= l:
        return None
    return round((c - l) / (h - l), 2)


def assemble(symbol: str, target_date: str | None = None) -> str:
    """Build the Markdown for `symbol` on `target_date` (default: latest).
    Returns the rendered Markdown text."""
    x = dd.assemble(symbol)
    if not x.price:
        return f"# {symbol} — daily read\n\nNo price data."

    rows = x.price
    if target_date is None:
        target_date = rows[-1]["date"]
    idx = next((i for i, r in enumerate(rows) if r["date"] == target_date), None)
    if idx is None:
        return f"# {symbol} — daily read\n\nNo data for {target_date}."
    today = rows[idx]
    prior20 = rows[max(0, idx - 20):idx]
    prior5 = rows[max(0, idx - 5):idx]

    # 1. core today figures
    close = today["close"]; open_ = today["open"]; hi = today["high"]
    lo = today["low"]; vol = today["vol"]; turn = today["turnover"]
    diff = today["diff_pct"]
    cloc = _close_loc(open_, hi, lo, close)

    # 2. anomaly flags vs trailing 20d medians (cockpit thresholds, frozen)
    def med(seq, k):
        vs = [r[k] for r in seq if r[k] is not None]
        return st.median(vs) if vs else None

    mv = med(prior20, "vol")
    mt = med(prior20, "turnover")
    mr = med(prior20, "range_pct")
    flags = {}
    if mv and vol and mv > 0 and vol / mv >= ck.RVOL_FLAG:
        flags["volume_spike"] = round(vol / mv, 2)
    if mt and turn and mt > 0 and turn / mt >= ck.TURNOVER_FLAG:
        flags["turnover_shock"] = round(turn / mt, 2)
    if mr and today["range_pct"] and mr > 0 and (
            today["range_pct"] / mr >= ck.RANGE_FLAG):
        flags["range_expansion"] = round(today["range_pct"] / mr, 2)

    # 3. multi-window context
    closes20 = [r["close"] for r in prior20 if r["close"] is not None]
    n = len(rows)
    win252 = [r["close"] for r in rows[max(0, idx - 251):idx + 1]
              if r["close"] is not None]
    hi52 = max(win252) if win252 else None
    lo52 = min(win252) if win252 else None
    ma20 = st.mean(closes20 + [close]) if closes20 else None
    ret_5d = None
    if len(prior5) >= 5 and prior5[0]["close"]:
        ret_5d = round((close / prior5[0]["close"] - 1) * 100, 2)
    ret_20d = None
    if closes20 and closes20[0]:
        ret_20d = round((close / closes20[0] - 1) * 100, 2)

    # 4. broker layer
    bd = x.broker.get("by_date", {}).get(target_date)
    pb = x.broker.get("persistent_brokers", {})
    cov = x.broker.get("coverage") or {}

    # 5. recent events (past 60d)
    cutoff = (dt.date.fromisoformat(target_date) -
              dt.timedelta(days=60)).isoformat()
    recent_events = [e for e in x.events
                     if e.get("date") and e["date"] >= cutoff
                     and e["date"] <= target_date]

    # ---- render markdown ----
    L = []
    L.append(f"# {symbol} — Daily Read · {target_date}\n")
    L.append(HEADER)

    L.append(f"\n**Coverage line:** OHLCV through "
             f"{rows[-1]['date']} (NOT corp-action adjusted) · "
             f"broker flow through {cov.get('last_date','NA')} "
             f"({cov.get('files_with_rows','0')} days covered, "
             f"{cov.get('unique_brokers','0')} brokers) · "
             f"events backfill through latest known announcement.\n")

    L.append("\n## 1. Today's snapshot (descriptive)\n")
    L.append(f"- Close **{_fmt(close)}** · day Δ {_fmt(diff)}%")
    L.append(f"- Open {_fmt(open_)} · High {_fmt(hi)} · Low {_fmt(lo)} "
             f"· Volume {_fmt(vol,0)} · Turnover Rs {_fmt(turn,0)}")
    if cloc is not None:
        L.append(f"- Close-in-range: **{cloc}** (0 = at low, 1 = at high)")

    L.append("\n## 2. Vs its own recent history (observation only)\n")
    L.append(f"- 5-day return: {_fmt(ret_5d)}% · 20-day return: "
             f"{_fmt(ret_20d)}%")
    if ma20 and close is not None:
        L.append(f"- 20-day mean close: {_fmt(ma20)} "
                 f"({'ABOVE' if close > ma20 else 'BELOW'} by "
                 f"{_fmt((close-ma20)/ma20*100)}%)")
    if hi52 and lo52:
        pos = (close - lo52) / (hi52 - lo52) * 100 if hi52 > lo52 else None
        L.append(f"- 52-week range: low {_fmt(lo52)} ↔ high {_fmt(hi52)} "
                 f"· current position **{_fmt(pos,1)}%** of range")
    if mv:
        L.append(f"- Volume vs trailing 20-day median: "
                 f"**{_fmt(vol/mv if vol else 0,2)}×** "
                 f"(threshold for 'spike' = {ck.RVOL_FLAG}× — frozen)")

    L.append("\n## 3. Anomaly flags (frozen thresholds, descriptive only)\n")
    if flags:
        for k, v in flags.items():
            L.append(f"- 🔔 **{k}** = {v}× normal")
    else:
        L.append("- No anomaly flags today (volume/turnover/range all within "
                "normal vs 20-day median).")

    L.append("\n## 4. Broker flow (today, where coverage exists)\n")
    if not bd:
        L.append("_No broker-flow coverage for this date._")
    else:
        nlb, nlq = bd.get("net_leader") or ("—", 0)
        side = "BUYER" if nlq and nlq > 0 else "SELLER" if nlq else "—"
        L.append(f"- Day total qty (floorsheet): {_fmt(bd['day_total_qty'],0)}")
        L.append(f"- Top-5 BUY concentration: "
                 f"**{_fmt((bd.get('top5_buy_share') or 0)*100,1)}%**")
        L.append(f"- Top-5 SELL concentration: "
                 f"**{_fmt((bd.get('top5_sell_share') or 0)*100,1)}%**")
        L.append(f"- Net leader today: broker {_broker_tag(str(nlb))} "
                 f"({side}, net {nlq:+,.0f})")
        # top 3 buyers / sellers from the day's record
        if bd.get("top_buyers"):
            buys = " · ".join(f"{_broker_tag(str(b))} buy {q:,.0f}"
                              for b, q in bd["top_buyers"][:3])
            L.append(f"- Top 3 buyers: {buys}")
        if bd.get("top_sellers"):
            sells = " · ".join(f"{_broker_tag(str(s))} sell {q:,.0f}"
                               for s, q in bd["top_sellers"][:3])
            L.append(f"- Top 3 sellers: {sells}")

    L.append("\n## 5. Persistent brokers (descriptive — METHODOLOGY Rule 2 + 11)\n")
    if pb:
        L.append("Brokers currently on the same net side for ≥3 days "
                 "(named where Rule-11 history known):\n")
        for br, n_signed in list(pb.items())[:8]:
            side = "BUYER" if n_signed > 0 else "SELLER"
            L.append(f"- broker {_broker_tag(str(br))} — "
                     f"{abs(n_signed)} days {side}")
    else:
        L.append("_No broker on a ≥3-day persistent same-side streak._")

    L.append("\n## 6. Recent corporate events (past 60 days)\n")
    if not recent_events:
        L.append("_No corporate events in the last 60 days from our events "
                 "file._")
    else:
        for e in recent_events[-8:]:
            L.append(f"- **{e['date']}** · {e.get('kind','event')} · "
                     f"{(e.get('text') or '')[:120]}")

    L.append("\n## 7. My daily read (HUMAN — append-only, write BEFORE the "
             "outcome is known)\n")
    L.append("> Fill in **one or two lines** of your own read. Examples of "
             "honest framings: 'looks like absorption,' 'distribution into "
             "strength,' 'no opinion,' 'too quiet to tell.'\n")
    L.append("- **Date written:** _(fill in)_")
    L.append("- **What I see:** _(your read, one line)_")
    L.append("- **Why it matters:** _(why this read, one line)_")
    L.append("- **What would prove me wrong:** _(your invalidation — be "
             "specific, e.g. 'close above 220 on >150k vol' or 'close below "
             "200 sustained')_")
    L.append("- **Risk level:** low / med / high")
    L.append("- **Revisit date:** _(when you'll check back)_")
    L.append("\n_Once written, this entry is **immutable**. Do not edit it "
             "later. Per DOSSIER_CONTRACT §6._\n")

    L.append("\n## 8. Later review (HUMAN — added on revisit; never edits §7)\n")
    L.append("- **Date reviewed:** _(fill in later)_")
    L.append("- **What actually happened:** _(plain description)_")
    L.append("- **One-line self-note:** _(was my read right, wrong, partially? "
             "what's the qualitative lesson? NO hit-rate calculation, NO "
             "sizing implication — per DOSSIER_CONTRACT §6 + Guardrail §7.)_\n")

    L.append(FOOTER)
    return "\n".join(L)


def main():
    sym = sys.argv[1] if len(sys.argv) > 1 else "UPPER"
    tgt = sys.argv[2] if len(sys.argv) > 2 else None
    md = assemble(sym, tgt)
    # determine date used for the filename
    if tgt is None:
        # peek at the first H1 line to extract the date
        for line in md.split("\n"):
            if line.startswith("# "):
                parts = line.split("·")
                tgt = parts[-1].strip() if len(parts) > 1 else "latest"
                break
    os.makedirs(OUT_DIR, exist_ok=True)
    out_path = os.path.join(OUT_DIR, f"{sym}_{tgt}.md")
    with open(out_path, "w", encoding="utf-8") as f:
        f.write(md)
    print(f"wrote {out_path} ({len(md)} chars)")


if __name__ == "__main__":
    main()
