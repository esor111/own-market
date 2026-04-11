"""
Cross-sector validation of broker persistence signals.

Tests whether signals found on commercial banks (NABIL/EBL/SANIMA)
hold on hydropower (AKPL/UPPER/API) and dev banks (JBBL/MNBBL).

This is the most important test: if the signal generalizes across sectors,
it's real. If it doesn't, it was bank-specific.
"""

import json
import os
import glob

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
PERSIST_DIR = os.path.join(ROOT, "data", "validation", "broker_persistence")
SCORES_DIR = os.path.join(ROOT, "data", "predictions", "replay_scores")
DATASET_PATH = os.path.join(ROOT, "data", "validation", "learning_reviews",
                            "latest__entry_research_dataset_v1.json")

SECTORS = {
    "COMMERCIAL": ["NABIL", "EBL", "SANIMA"],
    "HYDROPOWER": ["AKPL", "UPPER", "API"],
    "DEV_BANKS": ["JBBL", "MNBBL"],
}

BEAR_MONTHS = {"2023-07", "2023-08", "2023-10", "2024-09", "2025-05",
               "2025-06", "2025-07", "2025-09", "2025-10", "2025-11"}


def load_outcomes():
    outcomes = {}
    for sf in glob.glob(os.path.join(SCORES_DIR, "*.json")):
        s = json.load(open(sf))
        pid = s.get("prediction_id", "")
        parts = pid.split("__")
        if len(parts) >= 3:
            key = (parts[1], parts[2])
            if key not in outcomes:
                hr = s.get("horizon_returns", {})
                r10 = hr.get("return_10d_pct")
                if r10 is not None:
                    outcomes[key] = {"positive": r10 > 0, "r10": r10}

    with open(DATASET_PATH) as f:
        dataset = json.load(f)
    for row in dataset["rows"]:
        key = (row["session_date"], row["symbol"])
        if key not in outcomes:
            outcomes[key] = {
                "positive": row["comparison_verdict"] == "good_call",
                "negative": row["comparison_verdict"] == "bad_call",
            }
    return outcomes


def load_persistence(window):
    path = os.path.join(PERSIST_DIR, f"broker_persistence_all8_w{window}.json")
    with open(path) as f:
        return json.load(f)["features"]


def join(features, outcomes):
    data = []
    for f in features:
        key = (f["date"], f["symbol"])
        oc = outcomes.get(key)
        if not oc:
            continue
        f["_positive"] = oc.get("positive", False)
        f["_month"] = f["date"][:7]
        data.append(f)
    return data


def sector_of(symbol):
    for sec, syms in SECTORS.items():
        if symbol in syms:
            return sec
    return "OTHER"


def eval_rule(data, rule_fn):
    flagged = [d for d in data if rule_fn(d)]
    n = len(flagged)
    if n < 3:
        return None
    pos = sum(1 for d in flagged if d["_positive"])
    return {"n": n, "pos": pos, "pos_pct": pos / n * 100}


def main():
    outcomes = load_outcomes()

    # The signals to test (from Juliet + Romeo convergence)
    signals = [
        ("seller_persist >= 1.0 (BEARISH)", lambda f: f["seller_persistence_score"] >= 1.0),
        ("seller_persist >= 0.8 (BEARISH)", lambda f: f["seller_persistence_score"] >= 0.8),
        ("seller_persist <= 0.6 (BULLISH)", lambda f: f["seller_persistence_score"] <= 0.6),
        ("persistent_seller_count >= 4 (BEARISH)", lambda f: f["persistent_seller_count"] >= 4),
        ("today_buyer AND NOT seller (BULLISH)", lambda f: f["today_buyer_is_persistent"] and not f["today_seller_is_persistent"]),
        ("today_seller_persist (BEARISH)", lambda f: f["today_seller_is_persistent"]),
        ("net_bias <= -2.0 (ABSORPTION/BULL)", lambda f: f["net_persistence_bias"] <= -2.0),
    ]

    for w in [7, 10, 15]:
        features = load_persistence(w)
        data = join(features, outcomes)

        print(f"\n{'=' * 100}")
        print(f"WINDOW {w}: {len(data)} cases with outcomes")
        print(f"{'=' * 100}")

        # Base rates by sector
        for sec_name, sec_syms in SECTORS.items():
            sec_data = [d for d in data if d["symbol"] in sec_syms]
            if not sec_data:
                continue
            pos = sum(1 for d in sec_data if d["_positive"])
            print(f"  {sec_name}: {len(sec_data)} cases, base_positive={pos}/{len(sec_data)} = {pos/len(sec_data)*100:.1f}%")
        all_pos = sum(1 for d in data if d["_positive"])
        print(f"  ALL: {len(data)} cases, base_positive={all_pos}/{len(data)} = {all_pos/len(data)*100:.1f}%")
        print()

        # Test each signal on each sector
        header = f"{'Signal':<45s}"
        for sec_name in list(SECTORS.keys()) + ["ALL"]:
            header += f" | {sec_name:>12s}"
        print(header)
        print("-" * len(header))

        for sig_name, sig_fn in signals:
            row = f"{sig_name:<45s}"
            for sec_name in list(SECTORS.keys()) + ["ALL"]:
                if sec_name == "ALL":
                    sec_data = data
                else:
                    sec_data = [d for d in data if d["symbol"] in SECTORS[sec_name]]

                if not sec_data:
                    row += f" | {'N/A':>12s}"
                    continue

                base = sum(1 for d in sec_data if d["_positive"]) / len(sec_data) * 100
                result = eval_rule(sec_data, sig_fn)
                if result is None:
                    row += f" | {'<3':>12s}"
                else:
                    delta = result["pos_pct"] - base
                    row += f" | {result['pos_pct']:5.1f}%({delta:+.0f}) n={result['n']:>3d}"
            print(row)

        # Discovery/validation split BY SECTOR
        print(f"\n--- DISCOVERY/VALIDATION SPLIT (window {w}) ---")
        for sig_name, sig_fn in signals:
            print(f"\n  {sig_name}:")
            for sec_name in list(SECTORS.keys()) + ["ALL"]:
                if sec_name == "ALL":
                    sec_data = data
                else:
                    sec_data = [d for d in data if d["symbol"] in SECTORS[sec_name]]

                disc = [d for d in sec_data if d["_month"] < "2025-06"]
                val = [d for d in sec_data if d["_month"] >= "2025-06"]

                d_result = eval_rule(disc, sig_fn)
                v_result = eval_rule(val, sig_fn)

                if d_result is None and v_result is None:
                    continue

                d_base = sum(1 for d in disc if d["_positive"]) / len(disc) * 100 if disc else 0
                v_base = sum(1 for d in val if d["_positive"]) / len(val) * 100 if val else 0

                d_str = f"D:{d_result['n']:3d} {d_result['pos_pct']:5.1f}%({d_result['pos_pct']-d_base:+5.1f})" if d_result else "D: <3"
                v_str = f"V:{v_result['n']:3d} {v_result['pos_pct']:5.1f}%({v_result['pos_pct']-v_base:+5.1f})" if v_result else "V: <3"

                stable = ""
                if d_result and v_result:
                    d_delta = d_result["pos_pct"] - d_base
                    v_delta = v_result["pos_pct"] - v_base
                    if (d_delta < -3 and v_delta < -3) or (d_delta > 3 and v_delta > 3):
                        stable = "STABLE"
                    elif abs(d_delta) < 3 or abs(v_delta) < 3:
                        stable = "WEAK"
                    else:
                        stable = "FLIP"

                print(f"    {sec_name:>12s}: {d_str} | {v_str} | {stable}")


if __name__ == "__main__":
    main()
