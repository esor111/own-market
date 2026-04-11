"""
Validate mechanical avoid rules on the full 526-row entry research dataset.

Discovery/validation split by month:
  Discovery: 2023-07 through 2025-05 (372 rows, 12 months)
  Validation: 2025-06 through 2025-12 (154 rows, 6 months)

"Bad" = entry_outcome_family == 'strict_negative' (the entry would have lost money)
"Good" = entry_outcome_family == 'strict_positive' (the entry would have made money)
"Gap" = entry_outcome_family == 'nontradable_favorable' (couldn't enter, direction was right)
"""

import json
import os

BASE = os.path.dirname(os.path.abspath(__file__))
DATASET_PATH = os.path.join(
    os.path.dirname(BASE), "market-gist", "data", "validation",
    "learning_reviews", "latest__entry_research_dataset_v1.json",
)

# Try alternate path if running from market-gist/
if not os.path.exists(DATASET_PATH):
    DATASET_PATH = os.path.join(
        BASE, "..", "data", "validation", "learning_reviews",
        "latest__entry_research_dataset_v1.json",
    )


def load_dataset():
    with open(DATASET_PATH) as f:
        data = json.load(f)
    return data["rows"]


def split_discovery_validation(rows):
    """Split by month: discovery = 2023-07 through 2025-05, validation = 2025-06+"""
    cutoff = "2025-06"
    discovery = [r for r in rows if r["month_key"] < cutoff]
    validation = [r for r in rows if r["month_key"] >= cutoff]
    return discovery, validation


def evaluate_rule(rows, rule_fn, label="rule"):
    """Evaluate a single rule on a set of rows."""
    flagged = [r for r in rows if rule_fn(r)]
    not_flagged = [r for r in rows if not rule_fn(r)]

    total = len(rows)
    n_flagged = len(flagged)
    if n_flagged == 0:
        return {"label": label, "total": total, "flagged": 0,
                "precision": None, "recall": None, "note": "no cases flagged"}

    # Bad = strict_negative (would have lost money)
    total_bad = sum(1 for r in rows if r["entry_outcome_family"] == "strict_negative")
    flagged_bad = sum(1 for r in flagged if r["entry_outcome_family"] == "strict_negative")
    flagged_good = sum(1 for r in flagged if r["entry_outcome_family"] == "strict_positive")
    not_flagged_bad = sum(1 for r in not_flagged if r["entry_outcome_family"] == "strict_negative")
    not_flagged_good = sum(1 for r in not_flagged if r["entry_outcome_family"] == "strict_positive")

    precision = flagged_bad / n_flagged if n_flagged > 0 else 0
    recall = flagged_bad / total_bad if total_bad > 0 else 0

    # False positive rate: how many good cases does it wrongly flag?
    total_good = sum(1 for r in rows if r["entry_outcome_family"] == "strict_positive")
    false_pos_rate = flagged_good / total_good if total_good > 0 else 0

    # Remaining pool quality: of NOT flagged, what % are good?
    remaining_good_rate = not_flagged_good / len(not_flagged) if not_flagged else 0
    remaining_bad_rate = not_flagged_bad / len(not_flagged) if not_flagged else 0

    return {
        "label": label,
        "total": total,
        "flagged": n_flagged,
        "flagged_pct": n_flagged / total * 100,
        "flagged_bad": flagged_bad,
        "flagged_good": flagged_good,
        "precision": precision * 100,
        "recall": recall * 100,
        "false_pos_rate": false_pos_rate * 100,
        "remaining_count": len(not_flagged),
        "remaining_good_rate": remaining_good_rate * 100,
        "remaining_bad_rate": remaining_bad_rate * 100,
    }


def main():
    rows = load_dataset()
    discovery, validation = split_discovery_validation(rows)

    print(f"Total rows: {len(rows)}")
    print(f"Discovery: {len(discovery)} rows ({len(set(r['month_key'] for r in discovery))} months)")
    print(f"Validation: {len(validation)} rows ({len(set(r['month_key'] for r in validation))} months)")
    print()

    # Baseline rates
    for name, subset in [("Discovery", discovery), ("Validation", validation)]:
        bad = sum(1 for r in subset if r["entry_outcome_family"] == "strict_negative")
        good = sum(1 for r in subset if r["entry_outcome_family"] == "strict_positive")
        gap = sum(1 for r in subset if r["entry_outcome_family"] == "nontradable_favorable")
        print(f"{name}: {bad} bad ({bad/len(subset)*100:.1f}%), {good} good ({good/len(subset)*100:.1f}%), {gap} gap ({gap/len(subset)*100:.1f}%)")
    print()

    # Define rules
    rules = [
        # Single signal rules
        ("VR < 0.8", lambda r: (r.get("volume_ratio_5d") or 99) < 0.8),
        ("VR < 0.6", lambda r: (r.get("volume_ratio_5d") or 99) < 0.6),
        ("VR < 0.5", lambda r: (r.get("volume_ratio_5d") or 99) < 0.5),
        ("pos60 < 0.3", lambda r: (r.get("close_position_60d") or 0.5) < 0.3),
        ("pos60 < 0.2", lambda r: (r.get("close_position_60d") or 0.5) < 0.2),
        ("pos60 > 0.95", lambda r: (r.get("close_position_60d") or 0.5) > 0.95),
        ("pos20 > 0.95", lambda r: (r.get("close_position_20d") or 0.5) > 0.95),
        ("trend=mixed", lambda r: r.get("trend_label") == "mixed"),
        ("trend=downtrend", lambda r: r.get("trend_label") == "downtrend"),
        ("trend=mixed|down", lambda r: r.get("trend_label") in ("mixed", "downtrend")),
        ("calendar=post_season", lambda r: r.get("month_key", "")[:7] >= "2025-11" or r.get("month_key", "")[-2:] in ("11", "12")),
        ("RR < 1.0", lambda r: (r.get("risk_reward_ratio") or 99) < 1.0),
        ("ret20d < -2%", lambda r: (r.get("return_20d_pct") or 0) < -2),
        ("ret5d < -5%", lambda r: (r.get("return_5d_pct") or 0) < -5),

        # Combination rules
        ("VR<0.8 AND pos60<0.4", lambda r: (r.get("volume_ratio_5d") or 99) < 0.8 and (r.get("close_position_60d") or 0.5) < 0.4),
        ("VR<0.8 AND trend=mixed|down", lambda r: (r.get("volume_ratio_5d") or 99) < 0.8 and r.get("trend_label") in ("mixed", "downtrend")),
        ("VR<0.8 AND ret20d<0", lambda r: (r.get("volume_ratio_5d") or 99) < 0.8 and (r.get("return_20d_pct") or 0) < 0),
        ("pos60<0.3 AND trend=mixed|down", lambda r: (r.get("close_position_60d") or 0.5) < 0.3 and r.get("trend_label") in ("mixed", "downtrend")),
        ("pos60<0.3 AND VR<0.8", lambda r: (r.get("close_position_60d") or 0.5) < 0.3 and (r.get("volume_ratio_5d") or 99) < 0.8),
        ("VR<0.8 AND pos60<0.4 AND ret20d<0", lambda r: (r.get("volume_ratio_5d") or 99) < 0.8 and (r.get("close_position_60d") or 0.5) < 0.4 and (r.get("return_20d_pct") or 0) < 0),
        ("ret5d<-5% OR (VR<0.6 AND pos60<0.3)", lambda r: (r.get("return_5d_pct") or 0) < -5 or ((r.get("volume_ratio_5d") or 99) < 0.6 and (r.get("close_position_60d") or 0.5) < 0.3)),
        ("VR<0.8 AND pos60>0.9", lambda r: (r.get("volume_ratio_5d") or 99) < 0.8 and (r.get("close_position_60d") or 0.5) > 0.9),

        # Broader combination (potential Layer 1 filter)
        ("ANY: VR<0.6 OR ret5d<-5% OR (trend=down AND pos60<0.3)", lambda r:
            (r.get("volume_ratio_5d") or 99) < 0.6 or
            (r.get("return_5d_pct") or 0) < -5 or
            (r.get("trend_label") == "downtrend" and (r.get("close_position_60d") or 0.5) < 0.3)),
    ]

    # Run all rules on both splits
    print("=" * 130)
    print(f"{'Rule':<45s} | {'Split':<5s} | {'Flagged':>7s} | {'Flag%':>5s} | {'Prec':>5s} | {'Recall':>6s} | {'FP%':>5s} | {'Remain':>6s} | {'RemGood%':>8s} | {'RemBad%':>7s}")
    print("=" * 130)

    for label, fn in rules:
        for split_name, split_data in [("DISC", discovery), ("VAL", validation)]:
            result = evaluate_rule(split_data, fn, label)
            if result.get("note"):
                print(f"{label:<45s} | {split_name:<5s} | {'0':>7s} | {'0.0':>5s} | {'N/A':>5s} | {'N/A':>6s} | {'N/A':>5s} | {result['total']:>6d} | {'N/A':>8s} | {'N/A':>7s}")
            else:
                print(f"{label:<45s} | {split_name:<5s} | {result['flagged']:>7d} | {result['flagged_pct']:>4.1f}% | {result['precision']:>4.1f}% | {result['recall']:>5.1f}% | {result['false_pos_rate']:>4.1f}% | {result['remaining_count']:>6d} | {result['remaining_good_rate']:>7.1f}% | {result['remaining_bad_rate']:>6.1f}%")
        print("-" * 130)

    # Find best rules by validation precision (with min 10 flagged cases)
    print()
    print("=== TOP RULES BY VALIDATION PRECISION (min 10 flagged) ===")
    val_results = []
    for label, fn in rules:
        result = evaluate_rule(validation, fn, label)
        if result.get("flagged", 0) >= 10 and result.get("precision") is not None:
            val_results.append(result)
    val_results.sort(key=lambda x: x["precision"], reverse=True)
    for r in val_results[:10]:
        print(f"  {r['label']:<45s}: precision={r['precision']:.1f}%, recall={r['recall']:.1f}%, flagged={r['flagged']}, FP%={r['false_pos_rate']:.1f}%")

    print()
    print("=== TOP RULES BY VALIDATION RECALL (min 50% precision) ===")
    val_filtered = [r for r in val_results if r["precision"] >= 50]
    val_filtered.sort(key=lambda x: x["recall"], reverse=True)
    for r in val_filtered[:10]:
        print(f"  {r['label']:<45s}: recall={r['recall']:.1f}%, precision={r['precision']:.1f}%, flagged={r['flagged']}")

    # Best combined: F1 score
    print()
    print("=== TOP RULES BY VALIDATION F1 (precision + recall balance) ===")
    for r in val_results:
        p, rec = r["precision"] / 100, r["recall"] / 100
        r["f1"] = 2 * p * rec / (p + rec) if (p + rec) > 0 else 0
    val_results.sort(key=lambda x: x["f1"], reverse=True)
    for r in val_results[:10]:
        print(f"  {r['label']:<45s}: F1={r['f1']:.3f}, precision={r['precision']:.1f}%, recall={r['recall']:.1f}%, flagged={r['flagged']}")


if __name__ == "__main__":
    main()
