"""
Test broker persistence features for robustness:
1. Discovery/validation split
2. Window size comparison (3, 5, 7, 10, 15)
3. Combined features (persistence + VR + pos60)
4. Bear vs mixed months
"""

import json
import os
import glob
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from broker_persistence_tracker import load_all_ledgers, compute_persistence

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

# ============================================================
# LOAD OUTCOMES
# ============================================================

scores_dir = os.path.join(ROOT, "data", "predictions", "replay_scores")
outcomes = {}
for sf in glob.glob(os.path.join(scores_dir, "*.json")):
    s = json.load(open(sf))
    pid = s.get("prediction_id", "")
    parts = pid.split("__")
    if len(parts) < 3:
        continue
    key = (parts[1], parts[2])
    if key not in outcomes:
        hr = s.get("horizon_returns", {})
        r10 = hr.get("return_10d_pct")
        if r10 is not None:
            outcomes[key] = {"positive": r10 > 0, "r10": r10}

ds_path = os.path.join(ROOT, "data", "validation", "learning_reviews",
                        "latest__entry_research_dataset_v1.json")
with open(ds_path) as f:
    dataset = json.load(f)
ds_rows = {(r["session_date"], r["symbol"]): r for r in dataset["rows"]}
for key, row in ds_rows.items():
    if key not in outcomes:
        outcomes[key] = {
            "positive": row["comparison_verdict"] == "good_call",
            "negative": row["comparison_verdict"] == "bad_call",
        }

# ============================================================
# COMPUTE ALL WINDOWS
# ============================================================

persist_dir = os.path.join(ROOT, "data", "validation", "broker_persistence")
os.makedirs(persist_dir, exist_ok=True)

all_windows = {}
for w in [3, 5, 7, 10, 15]:
    cache_path = os.path.join(persist_dir, f"broker_persistence_w{w}.json")
    if os.path.exists(cache_path):
        with open(cache_path) as f:
            all_windows[w] = json.load(f)["features"]
    else:
        feats = []
        for sym in ["NABIL", "EBL", "SANIMA"]:
            ledgers = load_all_ledgers(sym)
            for date in sorted(ledgers.keys()):
                feat = compute_persistence(ledgers, date, w)
                if feat:
                    feat["symbol"] = sym
                    feats.append(feat)
        all_windows[w] = feats
        with open(cache_path, "w") as f:
            json.dump({"window": w, "total_records": len(feats), "features": feats}, f)

print("Windows:", {w: len(f) for w, f in all_windows.items()})


# ============================================================
# JOIN WITH OUTCOMES + STOCK METRICS
# ============================================================

def join_data(features):
    data = []
    for f in features:
        key = (f["date"], f["symbol"])
        oc = outcomes.get(key)
        if not oc:
            continue
        f["_positive"] = oc.get("positive", False)
        f["_negative"] = oc.get("negative", not oc.get("positive", True))
        f["_month"] = f["date"][:7]

        ds = ds_rows.get(key)
        if ds:
            f["_vr"] = ds.get("volume_ratio_5d")
            f["_pos60"] = ds.get("close_position_60d")
            f["_ret20"] = ds.get("return_20d_pct")
        data.append(f)
    return data


# ============================================================
# EXPERIMENT 1: DISCOVERY / VALIDATION SPLIT
# ============================================================

print("\n" + "=" * 90)
print("EXPERIMENT 1: DISCOVERY / VALIDATION SPLIT")
print("=" * 90)

rules = [
    ("seller_persist >= 0.8", lambda f: f["seller_persistence_score"] >= 0.8),
    ("seller_persist = 1.0", lambda f: f["seller_persistence_score"] >= 1.0),
    ("today_buyer AND NOT seller", lambda f: f["today_buyer_is_persistent"] and not f["today_seller_is_persistent"]),
    ("today_seller_persist", lambda f: f["today_seller_is_persistent"]),
]

for w in sorted(all_windows.keys()):
    data = join_data(all_windows[w])
    disc = [d for d in data if d["_month"] < "2025-06"]
    val = [d for d in data if d["_month"] >= "2025-06"]
    if len(disc) < 10 or len(val) < 10:
        continue

    disc_base = sum(1 for d in disc if d["_positive"]) / len(disc) * 100
    val_base = sum(1 for d in val if d["_positive"]) / len(val) * 100

    print(f"\nWindow {w}: disc={len(disc)} (base={disc_base:.1f}%), val={len(val)} (base={val_base:.1f}%)")

    for name, fn in rules:
        d_flag = [d for d in disc if fn(d)]
        v_flag = [d for d in val if fn(d)]
        if len(d_flag) < 3 or len(v_flag) < 3:
            print(f"  {name:<40s} | disc={len(d_flag)} val={len(v_flag)} -- too few")
            continue
        d_pos = sum(1 for d in d_flag if d["_positive"]) / len(d_flag) * 100
        v_pos = sum(1 for d in v_flag if d["_positive"]) / len(v_flag) * 100
        d_vs = d_pos - disc_base
        v_vs = v_pos - val_base
        same_dir = "STABLE" if (d_vs < -3 and v_vs < -3) or (d_vs > 3 and v_vs > 3) else "WEAK" if abs(d_vs) < 3 or abs(v_vs) < 3 else "FLIP"
        print(f"  {name:<40s} | D:{len(d_flag):3d} pos={d_pos:5.1f}% ({d_vs:+5.1f}) | V:{len(v_flag):3d} pos={v_pos:5.1f}% ({v_vs:+5.1f}) | {same_dir}")


# ============================================================
# EXPERIMENT 2: WINDOW COMPARISON
# ============================================================

print("\n" + "=" * 90)
print("EXPERIMENT 2: SELLER PERSISTENCE ACROSS WINDOWS")
print("=" * 90)

for threshold_name, threshold_fn in [
    ("seller >= 0.8", lambda f: f["seller_persistence_score"] >= 0.8),
    ("seller = 1.0", lambda f: f["seller_persistence_score"] >= 1.0),
    ("today_buyer NOT seller", lambda f: f["today_buyer_is_persistent"] and not f["today_seller_is_persistent"]),
]:
    print(f"\n{threshold_name}:")
    print(f"  {'Win':>3s} | {'N':>5s} | {'Flag':>4s} | {'Pos%':>5s} | {'Base':>5s} | {'Delta':>6s} | {'Consistent?'}")
    print("  " + "-" * 60)
    for w in sorted(all_windows.keys()):
        data = join_data(all_windows[w])
        flagged = [d for d in data if threshold_fn(d)]
        if len(flagged) < 5:
            print(f"  {w:>3d} | {len(data):>5d} | {len(flagged):>4d} | {'<5':>5s} |")
            continue
        pos = sum(1 for d in flagged if d["_positive"]) / len(flagged) * 100
        base = sum(1 for d in data if d["_positive"]) / len(data) * 100
        delta = pos - base
        direction = "BEARISH" if delta < -5 else ("BULLISH" if delta > 5 else "FLAT")
        print(f"  {w:>3d} | {len(data):>5d} | {len(flagged):>4d} | {pos:>4.1f}% | {base:>4.1f}% | {delta:>+5.1f}% | {direction}")


# ============================================================
# EXPERIMENT 3: COMBINED FEATURES
# ============================================================

print("\n" + "=" * 90)
print("EXPERIMENT 3: PERSISTENCE + STOCK FEATURES (window 5)")
print("=" * 90)

data5 = join_data(all_windows[5])
base5 = sum(1 for d in data5 if d["_positive"]) / len(data5) * 100
print(f"Base: {base5:.1f}% positive ({len(data5)} cases)")

combos = [
    ("seller>=0.8 AND VR<0.8", lambda f: f["seller_persistence_score"] >= 0.8 and (f.get("_vr") or 99) < 0.8),
    ("seller>=0.8 AND VR<1.0", lambda f: f["seller_persistence_score"] >= 0.8 and (f.get("_vr") or 99) < 1.0),
    ("seller>=0.8 AND pos60<0.5", lambda f: f["seller_persistence_score"] >= 0.8 and (f.get("_pos60") or 0.5) < 0.5),
    ("seller=1.0 AND VR<1.0", lambda f: f["seller_persistence_score"] >= 1.0 and (f.get("_vr") or 99) < 1.0),
    ("seller=1.0 AND pos60<0.5", lambda f: f["seller_persistence_score"] >= 1.0 and (f.get("_pos60") or 0.5) < 0.5),
    ("seller>=0.8 AND ret20<3%", lambda f: f["seller_persistence_score"] >= 0.8 and (f.get("_ret20") or 0) < 3),
    ("seller>=0.8 AND ret20>5% (absorb?)", lambda f: f["seller_persistence_score"] >= 0.8 and (f.get("_ret20") or 0) > 5),
    ("buyer_pers AND NOT seller AND VR>1", lambda f: f["today_buyer_is_persistent"] and not f["today_seller_is_persistent"] and (f.get("_vr") or 0) > 1.0),
    ("buyer_pers AND NOT seller AND pos60>0.5", lambda f: f["today_buyer_is_persistent"] and not f["today_seller_is_persistent"] and (f.get("_pos60") or 0) > 0.5),
]

print(f"\n{'Combo':<50s} | {'N':>4s} | {'Pos%':>5s} | {'Delta':>6s}")
print("-" * 75)
for name, fn in combos:
    flagged = [d for d in data5 if fn(d)]
    n = len(flagged)
    if n < 5:
        print(f"{name:<50s} | {n:>4d} | {'<5':>5s} |")
        continue
    pos = sum(1 for d in flagged if d["_positive"]) / n * 100
    print(f"{name:<50s} | {n:>4d} | {pos:>4.1f}% | {pos - base5:>+5.1f}%")


# ============================================================
# EXPERIMENT 4: BEAR VS MIXED MONTHS
# ============================================================

print("\n" + "=" * 90)
print("EXPERIMENT 4: BEAR VS MIXED MONTHS (window 5)")
print("=" * 90)

bear_months = {"2023-07", "2023-08", "2023-10", "2024-09", "2025-05",
               "2025-06", "2025-07", "2025-09", "2025-10", "2025-11"}

for label, subset_fn in [
    ("MIXED months", lambda d: d["_month"] not in bear_months),
    ("BEAR months", lambda d: d["_month"] in bear_months),
    ("ALL months", lambda d: True),
]:
    subset = [d for d in data5 if subset_fn(d)]
    if len(subset) < 10:
        print(f"\n{label}: too few ({len(subset)})")
        continue
    base = sum(1 for d in subset if d["_positive"]) / len(subset) * 100
    print(f"\n{label}: {len(subset)} cases, base_pos={base:.1f}%")

    for name, fn in [
        ("seller_persist >= 0.8", lambda f: f["seller_persistence_score"] >= 0.8),
        ("seller_persist = 1.0", lambda f: f["seller_persistence_score"] >= 1.0),
        ("today_buyer AND NOT seller", lambda f: f["today_buyer_is_persistent"] and not f["today_seller_is_persistent"]),
        ("today_seller_persist", lambda f: f["today_seller_is_persistent"]),
    ]:
        flagged = [d for d in subset if fn(d)]
        if len(flagged) < 3:
            print(f"  {name:<40s} | {len(flagged)} -- too few")
            continue
        pos = sum(1 for d in flagged if d["_positive"]) / len(flagged) * 100
        delta = pos - base
        print(f"  {name:<40s} | {len(flagged):3d} cases, pos={pos:.1f}% ({delta:+.1f}pp)")


if __name__ == "__main__":
    pass
