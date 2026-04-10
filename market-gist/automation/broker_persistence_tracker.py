"""
Broker Persistence Tracker

Computes multi-day broker persistence features for each (date, symbol).
Looks back N trading days and identifies:
- Which brokers consistently buy (accumulation)
- Which brokers consistently sell (distribution)
- Which brokers do both (market makers)
- Whether selling is being absorbed by price strength (absorption signal)

All outputs are NUMBERS, not narratives. Test mechanically first.

Usage:
    python broker_persistence_tracker.py --window 5
    python broker_persistence_tracker.py --window 10
    python broker_persistence_tracker.py --window 5 --window 10
"""

import argparse
import json
import os
import sys
from collections import defaultdict
from pathlib import Path

BASE = Path(__file__).resolve().parent
LEDGER_ROOT = BASE.parent / "broker_flow_ledger"
OUTPUT_DIR = BASE.parent / "data" / "validation" / "broker_persistence"


def default_symbols():
    """Discover symbol ledgers dynamically instead of hardcoding a small slice."""
    if not LEDGER_ROOT.exists():
        return []

    symbols = []
    for path in sorted(LEDGER_ROOT.iterdir()):
        if not path.is_dir():
            continue
        if path.name in {"raw_merolagani", "calendar_overrides"}:
            continue
        if not path.name.isupper():
            continue
        symbols.append(path.name)
    return symbols


def load_all_ledgers(symbol):
    """Load all usable daily ledger files for a symbol, keyed by date."""
    sym_dir = LEDGER_ROOT / symbol
    if not sym_dir.is_dir():
        return {}

    ledgers = {}
    for f in sorted(sym_dir.iterdir()):
        if not f.suffix == ".json":
            continue
        date = f.stem
        try:
            data = json.loads(f.read_text())
            ds = data.get("derived_snapshot", {})
            if (ds.get("total_transactions") or 0) <= 0:
                continue

            raw = data.get("raw_snapshot", {})
            fs = raw.get("floorsheet", {})
            buyers = fs.get("buyer_side", {}).get("rows", [])
            sellers = fs.get("seller_side", {}).get("rows", [])

            ledgers[date] = {
                "buyers": [(r["broker"], float(r["share_pct"])) for r in buyers],
                "sellers": [(r["broker"], float(r["share_pct"])) for r in sellers],
                "transactions": ds.get("total_transactions", 0),
                "turnover": ds.get("total_turnover", 0),
                "activity": ds.get("activity_label", "unknown"),
                "buyer_top3": ds.get("buyer_top3_concentration_pct"),
                "seller_top3": ds.get("seller_top3_concentration_pct"),
            }
        except (json.JSONDecodeError, KeyError, ValueError, TypeError) as exc:
            print(
                f"WARNING: load_all_ledgers({symbol}) skipped {f.name}: "
                f"{type(exc).__name__}: {exc}",
                file=sys.stderr,
            )
            continue

    return ledgers


def compute_persistence(ledgers, target_date, window):
    """Compute broker persistence features for a given date using N prior days.

    Returns dict of numeric features, or None if insufficient data.
    """
    all_dates = sorted(ledgers.keys())
    if target_date not in all_dates:
        return None

    idx = all_dates.index(target_date)
    # Get the prior `window` dates (not including target_date itself)
    prior_dates = all_dates[max(0, idx - window):idx]

    if len(prior_dates) < 3:
        return None  # Need at least 3 prior days

    # Track which brokers appear on which days and their share
    buyer_appearances = defaultdict(list)   # broker -> [(date, share_pct), ...]
    seller_appearances = defaultdict(list)

    for d in prior_dates:
        day = ledgers[d]
        # Top 10 buyers/sellers per day
        for broker, share in day["buyers"][:10]:
            buyer_appearances[broker].append((d, share))
        for broker, share in day["sellers"][:10]:
            seller_appearances[broker].append((d, share))

    n_days = len(prior_dates)
    all_brokers = set(buyer_appearances.keys()) | set(seller_appearances.keys())

    # === FEATURE 1: Buyer persistence ===
    # What fraction of lookback days did the most persistent buyer appear?
    buyer_persistence = {}
    for broker, appearances in buyer_appearances.items():
        days_present = len(set(d for d, _ in appearances))
        avg_share = sum(s for _, s in appearances) / len(appearances)
        buyer_persistence[broker] = {
            "days": days_present,
            "frac": days_present / n_days,
            "avg_share": avg_share,
            "total_weighted": days_present / n_days * avg_share,
        }

    # === FEATURE 2: Seller persistence ===
    seller_persistence = {}
    for broker, appearances in seller_appearances.items():
        days_present = len(set(d for d, _ in appearances))
        avg_share = sum(s for _, s in appearances) / len(appearances)
        seller_persistence[broker] = {
            "days": days_present,
            "frac": days_present / n_days,
            "avg_share": avg_share,
            "total_weighted": days_present / n_days * avg_share,
        }

    # Top persistent buyer/seller
    top_buyer = max(buyer_persistence.values(), key=lambda x: x["total_weighted"]) if buyer_persistence else None
    top_seller = max(seller_persistence.values(), key=lambda x: x["total_weighted"]) if seller_persistence else None

    # === FEATURE 3: Market maker detection ===
    # Brokers who appear on BOTH sides across the window
    both_side_brokers = set(buyer_appearances.keys()) & set(seller_appearances.keys())
    market_maker_count = 0
    for broker in both_side_brokers:
        buy_days = len(set(d for d, _ in buyer_appearances[broker]))
        sell_days = len(set(d for d, _ in seller_appearances[broker]))
        if buy_days >= 2 and sell_days >= 2:
            market_maker_count += 1

    # === FEATURE 4: Concentration trend ===
    # Is buyer concentration increasing or decreasing over the window?
    buyer_conc_series = []
    seller_conc_series = []
    for d in prior_dates:
        day = ledgers[d]
        b3 = day.get("buyer_top3")
        s3 = day.get("seller_top3")
        if b3 is not None:
            buyer_conc_series.append(b3)
        if s3 is not None:
            seller_conc_series.append(s3)

    def trend_slope(series):
        if len(series) < 3:
            return 0.0
        n = len(series)
        x_mean = (n - 1) / 2
        y_mean = sum(series) / n
        num = sum((i - x_mean) * (y - y_mean) for i, y in enumerate(series))
        den = sum((i - x_mean) ** 2 for i in range(n))
        return num / den if den > 0 else 0.0

    buyer_conc_trend = trend_slope(buyer_conc_series)
    seller_conc_trend = trend_slope(seller_conc_series)

    # === FEATURE 5: Net persistence bias ===
    top_buyer_score = top_buyer["total_weighted"] if top_buyer else 0
    top_seller_score = top_seller["total_weighted"] if top_seller else 0
    net_persistence_bias = top_buyer_score - top_seller_score

    # === FEATURE 6: Absorption signal ===
    # High seller persistence + price holding = absorption (bullish)
    # We don't have price here, so we compute seller intensity and let the
    # test script combine with price features
    seller_intensity = top_seller_score if top_seller else 0
    buyer_intensity = top_buyer_score if top_buyer else 0

    # === FEATURE 7: Unique persistent buyers vs sellers ===
    persistent_buyers = sum(1 for b in buyer_persistence.values() if b["frac"] >= 0.6)
    persistent_sellers = sum(1 for s in seller_persistence.values() if s["frac"] >= 0.6)

    # === FEATURE 8: Today's flow relative to persistence ===
    today = ledgers.get(target_date)
    today_top_buyer = today["buyers"][0][0] if today and today["buyers"] else None
    today_top_seller = today["sellers"][0][0] if today and today["sellers"] else None

    # Is today's top buyer a persistent buyer?
    today_buyer_is_persistent = False
    if today_top_buyer and today_top_buyer in buyer_persistence:
        today_buyer_is_persistent = buyer_persistence[today_top_buyer]["frac"] >= 0.6

    today_seller_is_persistent = False
    if today_top_seller and today_top_seller in seller_persistence:
        today_seller_is_persistent = seller_persistence[today_top_seller]["frac"] >= 0.6

    return {
        "symbol": None,  # filled by caller
        "date": target_date,
        "window": window,
        "prior_days_used": n_days,

        # Buyer persistence
        "buyer_persistence_score": top_buyer["frac"] if top_buyer else 0,
        "buyer_persistence_avg_share": top_buyer["avg_share"] if top_buyer else 0,
        "buyer_persistence_weighted": top_buyer_score,
        "persistent_buyer_count": persistent_buyers,

        # Seller persistence
        "seller_persistence_score": top_seller["frac"] if top_seller else 0,
        "seller_persistence_avg_share": top_seller["avg_share"] if top_seller else 0,
        "seller_persistence_weighted": top_seller_score,
        "persistent_seller_count": persistent_sellers,

        # Net bias
        "net_persistence_bias": net_persistence_bias,

        # Market makers
        "market_maker_count": market_maker_count,

        # Concentration trends
        "buyer_conc_trend": buyer_conc_trend,
        "seller_conc_trend": seller_conc_trend,

        # Today's alignment with persistence
        "today_buyer_is_persistent": today_buyer_is_persistent,
        "today_seller_is_persistent": today_seller_is_persistent,

        # Intensity (for absorption computation)
        "buyer_intensity": buyer_intensity,
        "seller_intensity": seller_intensity,
    }


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--window", type=int, action="append", default=[],
                        help="Lookback window(s) in trading days (default: 5 and 10)")
    parser.add_argument("--symbol", help="Only process one symbol")
    args = parser.parse_args()

    windows = args.window or [5, 10]
    symbols = [args.symbol.upper()] if args.symbol else default_symbols()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for window in windows:
        all_features = []

        for sym in symbols:
            print(f"Processing {sym} (window={window})...", end=" ")
            ledgers = load_all_ledgers(sym)
            if not ledgers:
                print("no data")
                continue

            computed = 0
            skipped = 0
            for date in sorted(ledgers.keys()):
                features = compute_persistence(ledgers, date, window)
                if features is None:
                    skipped += 1
                    continue
                features["symbol"] = sym
                all_features.append(features)
                computed += 1

            print(f"{computed} computed, {skipped} skipped (insufficient history)")

        # Save
        out_path = OUTPUT_DIR / f"broker_persistence_w{window}.json"
        with open(out_path, "w") as f:
            json.dump({
                "window": window,
                "total_records": len(all_features),
                "symbols": symbols,
                "features": all_features,
            }, f, indent=2)

        print(f"\nWindow {window}: {len(all_features)} records saved to {out_path}")

        # Quick stats
        if all_features:
            bp = [f["buyer_persistence_score"] for f in all_features]
            sp = [f["seller_persistence_score"] for f in all_features]
            nb = [f["net_persistence_bias"] for f in all_features]
            print(f"  Buyer persistence: min={min(bp):.2f} mean={sum(bp)/len(bp):.2f} max={max(bp):.2f}")
            print(f"  Seller persistence: min={min(sp):.2f} mean={sum(sp)/len(sp):.2f} max={max(sp):.2f}")
            print(f"  Net bias: min={min(nb):.2f} mean={sum(nb)/len(nb):.2f} max={max(nb):.2f}")
        print()


if __name__ == "__main__":
    main()
