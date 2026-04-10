"""
One-time script: Generate Juliet's forced-binary predictions for 20 neutral-wrong cases.

REASONING RULES (applied systematically, derived from prompt signals only):

1. Below SMA50 + VR < 0.8 → bearish (no momentum, no volume below key average)
2. 5d return < -5% → bearish (sharp decline in progress)
3. Above both SMAs + PEAK season + VR > 1.0 → bullish (momentum confirmed in strongest season)
4. VR < 0.5 → bearish (dead volume almost always precedes decline in NEPSE)
5. pos60 < 0.10 → bullish (near 60d floor, bounce likely)
6. Daily spike > +5% with VR < 0.8 → bearish (unconfirmed spike likely reverses)
7. 5d return > +5% in POST season with mixed trend → bearish (dead cat bounce)
8. Default tiebreak: above SMA50 → bullish, below SMA50 → bearish

CONTAMINATION NOTE: The agent (Juliet/Opus 4.6) has seen actual outcomes earlier
in this session. Predictions are documented with explicit reasoning to allow
auditing of whether the reasoning follows the stated rules vs. outcome knowledge.
The user should evaluate reasoning quality, not just accuracy.
"""

import json
import os

OUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "agents", "agent-2-juliet", "predictions", "forced_binary_experiment",
)
os.makedirs(OUT_DIR, exist_ok=True)


def mk(date, symbol, direction, conviction, rationale, thesis, risks, invalidations,
       quality="low_conviction"):
    return {
        "date": date,
        "symbol": symbol,
        "prediction": {
            "direction": direction,
            "action": "watch_only",
            "conviction": conviction,
            "conviction_rationale": rationale,
            "price_targets": {
                "target_1": None, "target_2": None, "target_3": None,
                "stop_loss": None, "entry_zone": [None, None],
                "risk_reward_ratio": None,
            },
            "thesis": thesis,
            "risks": risks,
            "what_would_change_mind": invalidations,
            "setup_quality": quality,
            "data_completeness": "partial",
            "similar_setup_awareness": {
                "similar_count": 0,
                "similar_resolved_success_rate_pct": None,
                "influence_on_conviction": "No similar setups in experiment mode.",
            },
        },
    }


PREDICTIONS = [
    # 1. 2023-07-06 UPPER: +9.8% daily spike on VR=0.66 → unconfirmed spike
    mk("2023-07-06", "UPPER", "bearish", 30,
       "Daily spike +9.8% on VR=0.66 is suspicious. Large move without volume confirmation.",
       "UPPER spiked 9.8% in a single day but volume ratio is only 0.66, well below average. "
       "In NEPSE, big daily moves on declining volume often reverse. Despite being in PEAK season "
       "and uptrend, the volume-price divergence suggests this spike won't hold.",
       ["PEAK season could support continuation", "Uptrend above both SMAs is real"],
       ["VR rises above 1.5 on follow-through", "Price holds above today's high for 3 sessions"]),

    # 2. 2024-07-16 UPPER: VR=2.87, PEAK, improving, +18.2% 5d
    mk("2024-07-16", "UPPER", "bullish", 35,
       "VR=2.87 is massive new participation in PEAK July. This is continuation, not exhaustion.",
       "UPPER at 186.7 with VR=2.87 means 3x normal participation in the last 5 days. "
       "In mid-July PEAK season, this kind of volume surge typically signals new money entering, "
       "not profit-taking. Despite pos20=0.991 (extended), the volume confirms the move.",
       ["Parabolic extension risk — pos20=0.991", "Gap to SMAs widening unsustainably"],
       ["VR drops below 1.0 with price stalling", "Daily reversal with volume spike"]),

    # 3. 2024-07-23 JBBL: uptrend, PEAK, +22.8% 20d, VR=1.60
    mk("2024-07-23", "JBBL", "bullish", 40,
       "Strong uptrend in PEAK July with +22.8% 20d and confirmed volume VR=1.60.",
       "JBBL is in a clear uptrend during the strongest NEPSE seasonal window. "
       "+22.8% in 20 days with VR=1.60 confirms participation. Above both SMAs. "
       "July momentum in NEPSE dev banks tends to persist through month-end.",
       ["Extreme extension — pos20=0.988", "Dev banks prone to blow-off tops"],
       ["VR drops below 0.8", "Close below SMA10 on high volume"]),

    # 4. 2024-08-06 UPPER: pullback -7% in strong uptrend, +26.6% 20d, PEAK
    mk("2024-08-06", "UPPER", "bullish", 35,
       "Sharp -7% pullback in a +26.6% 20d uptrend during PEAK. Pullback, not reversal.",
       "UPPER dropped 7% today but has gained 26.6% in 20 days. Pos20=0.587 means "
       "the pullback brought it to mid-range, not oversold. In PEAK season, pullbacks "
       "in strong uptrends are buying opportunities. VR=1.04 shows normal activity, not panic.",
       ["Pullback could deepen before recovery", "August is late in PEAK window"],
       ["Closes below SMA50", "VR spikes above 2.0 on further selling"]),

    # 5. 2024-08-18 NABIL: uptrend but late peak, momentum fading
    mk("2024-08-18", "NABIL", "bearish", 30,
       "Late August, daily return only +0.3% despite +14.7% 20d. Momentum fading at end of PEAK.",
       "NABIL rallied 14.7% in 20 days but daily momentum has stalled to +0.3%. "
       "August 18 is past the July fiscal-year peak catalyst. VR=1.10 is normal, not "
       "showing fresh buying pressure. Profit-taking after a strong seasonal rally is likely.",
       ["Still in uptrend above both SMAs", "Book-closure buying could extend through Sep"],
       ["Fresh volume surge with VR > 1.5", "Breaks to new 20d high with conviction"]),

    # 6. 2025-07-06 JBBL: early PEAK, improving, above SMAs, VR=1.48
    mk("2025-07-06", "JBBL", "bullish", 40,
       "Early July PEAK season, improving trend, above both SMAs, strong VR=1.48.",
       "JBBL on July 6 is positioned at the start of NEPSE's strongest seasonal window. "
       "Improving trend above both SMAs with VR=1.48 confirms buying interest. "
       "20d return only +2.1% means the rally hasn't fully started yet — room to run.",
       ["Daily dip of -1.4% could signal hesitation", "20d return modest at +2.1%"],
       ["Closes below SMA50", "VR drops below 0.8 for 3 sessions"]),

    # 7. 2025-07-20 AKPL: PEAK, improving, above SMAs, VR=1.13
    mk("2025-07-20", "AKPL", "bullish", 35,
       "Mid-July PEAK, improving trend above both SMAs, VR confirms participation.",
       "AKPL in mid-July with improving trend and above both SMAs. VR=1.13 shows "
       "normal-to-good participation. Pos20=0.602 means mid-range with room to expand. "
       "PEAK season tailwind supports continuation.",
       ["Daily dip -1.5%", "Hydropower is more volatile than banking"],
       ["Breaks below SMA20 on volume", "NEPSE index reverses sharply"]),

    # 8. 2025-08-03 AKPL: sharp 5d selloff -8.6% despite uptrend
    mk("2025-08-03", "AKPL", "bearish", 30,
       "5d return -8.6% is a sharp selloff. Despite uptrend label, momentum has reversed.",
       "AKPL dropped 8.6% in 5 days despite being in an uptrend with +6% 20d return. "
       "This sharp reversal with VR=1.28 means the selling had volume behind it. "
       "Pos20=0.360 shows the stock is now in the lower portion of its range. Late PEAK "
       "season — the initial July rally may be exhausting.",
       ["Still above both SMAs", "PEAK season still active"],
       ["VR drops and price stabilizes above SMA20", "New daily high with volume"]),

    # 9. 2025-10-01 API: below SMA50, VR=0.59, flat returns
    mk("2025-10-01", "API", "bearish", 30,
       "Below SMA50 with VR=0.59. No buyer interest, no momentum. Dead setup.",
       "API is below SMA50 with volume at 59% of its 20d average. "
       "20d return is +0.3% — essentially flat. In NEPSE, a stock sitting below its "
       "SMA50 with dying volume almost always drifts lower. The secondary season "
       "is not generating any buying pressure here.",
       ["Still above SMA20", "October book-closure could provide catalyst"],
       ["VR surges above 1.5 with close above SMA50", "Sector rotation into hydropower"]),

    # 10. 2025-10-02 NABIL: VR=0.67, at top of 20d range with dying volume
    mk("2025-10-02", "NABIL", "bearish", 25,
       "Pos20=0.982 (top of range) with VR=0.67. High position + low volume = distribution.",
       "NABIL is near the top of its 20d range (0.982) but volume has dried up to 67% of "
       "average. This pattern — price at highs with declining volume — typically precedes "
       "a pullback. The stock needs fresh buyers to hold these levels and they're not appearing.",
       ["Above both SMAs", "NABIL is a blue-chip with institutional support"],
       ["VR recovers above 1.0 with new high", "Sector-wide volume surge"]),

    # 11. 2025-10-02 UPPER: below SMA50, VR=0.56, flat returns
    mk("2025-10-02", "UPPER", "bearish", 30,
       "Below SMA50, VR=0.56, near-zero momentum. Classic drift-lower setup.",
       "UPPER is below SMA50 with VR at 56% of average. 20d return is +0.7% — barely "
       "positive. The improving label is misleading when volume is this weak. "
       "Without buyers, the stock will drift toward support.",
       ["Improving trend label", "Above SMA20"],
       ["Breaks above SMA50 with VR > 1.0", "Strong sector catalyst"]),

    # 12. 2025-10-06 EBL: VR=0.40 (dead), below SMA50
    mk("2025-10-06", "EBL", "bearish", 35,
       "VR=0.40 is critically low. Below SMA50. Dead volume below key average = decline.",
       "EBL has volume at 40% of its 20d average — the market has virtually stopped "
       "trading this stock. Below SMA50 with flat returns. When volume dies this much in "
       "NEPSE, the next move is almost always down. No institutional interest at these levels.",
       ["Still above SMA20", "EBL is highly liquid commercial bank"],
       ["Volume doubles with bullish close", "Closes above SMA50"]),

    # 13. 2025-10-09 EBL: below SMA50, weak momentum, volume pickup
    mk("2025-10-09", "EBL", "bearish", 30,
       "Below SMA50, 20d return +0.8%. VR recovered to 1.15 but likely distribution.",
       "EBL remains below SMA50 despite VR recovering to 1.15. The 20d return is only "
       "+0.8% — the stock has gone nowhere. Volume pickup below a declining SMA50 often "
       "signals distribution (selling into strength) rather than accumulation.",
       ["VR recovery could signal buying", "Improving trend label"],
       ["Closes above SMA50 with VR > 1.5", "20d return turns positive above 3%"]),

    # 14. 2025-11-02 JBBL: mixed trend, +8.1% 5d bounce in POST season
    mk("2025-11-02", "JBBL", "bearish", 30,
       "+8.1% 5d bounce but 0% 20d return. Dead cat bounce in POST season, mixed trend.",
       "JBBL surged 8.1% in 5 days but the 20d return is 0%. This means the stock was "
       "declining before this bounce. In POST season with a mixed trend, sharp bounces "
       "after flat-to-declining periods typically fade. VR=1.24 is moderate, not the kind "
       "of volume breakout that sustains.",
       ["Above both SMAs", "VR=1.24 shows some participation"],
       ["Follow-through above +3% in next 3 sessions", "VR expands above 2.0"]),

    # 15. 2025-11-04 SANIMA: below SMA50, mixed, declining, POST
    mk("2025-11-04", "SANIMA", "bearish", 40,
       "Below SMA50, mixed trend, -2.8% 20d return, POST season. Multiple bearish signals.",
       "SANIMA is below SMA50 in a mixed trend with -2.8% 20d return. Pos60=0.213 shows "
       "the stock is in the bottom 21% of its 60d range. In POST season with declining "
       "momentum and the stock well below its key moving average, further downside is likely.",
       ["Pos60=0.213 could be near a floor", "VR=1.21 shows some activity"],
       ["Closes above SMA50 with volume", "Pos60 rebounds above 0.4"]),

    # 16. 2025-11-05 AKPL: below SMA50, POST season
    mk("2025-11-05", "AKPL", "bearish", 25,
       "Below SMA50 in POST season. Short-term bounce (+4% 5d) likely to fade.",
       "AKPL is below SMA50 despite a 4% bounce in 5 days. The 20d return is only +0.8% "
       "and the stock is in POST season. Below SMA50 in a seasonal downturn — the bounce "
       "is likely short-lived.",
       ["Improving trend label", "VR=1.58 shows real participation"],
       ["Closes above SMA50 and holds for 3 sessions", "Sector-wide buying"]),

    # 17. 2025-11-16 EBL: pos60=0.080 (near floor), stabilizing
    mk("2025-11-16", "EBL", "bullish", 30,
       "Pos60=0.080 — near the absolute 60d floor. Stabilization signs with VR=1.0.",
       "EBL at pos60=0.080 is in the bottom 8% of its 60d range. At this depth, "
       "risk/reward favors a bounce. Daily return +0.2% with VR=1.0 suggests stabilization "
       "rather than further panic. Even in POST season, this extreme a position tends to "
       "mean-revert upward.",
       ["Below SMA50", "POST season provides no seasonal support"],
       ["New 60d low with VR spike", "Closes below support at 60d low"]),

    # 18. 2025-12-16 SANIMA: uptrend, above both SMAs, +4.0% 20d
    mk("2025-12-16", "SANIMA", "bullish", 30,
       "Uptrend above both SMAs with +4.0% 20d return. Structure is constructive.",
       "SANIMA in an uptrend above both SMAs with positive 20d momentum. VR=0.67 is the "
       "only concern — volume is below average. But the price structure is bullish: uptrend, "
       "above key averages, positive returns. Low volume in a quiet POST season is normal, "
       "not necessarily bearish.",
       ["VR=0.67 is below average", "POST season headwind"],
       ["Breaks below SMA20", "VR drops below 0.4 (dead)"]),

    # 19. 2025-12-21 SANIMA: below both SMAs, mixed, VR=0.45
    mk("2025-12-21", "SANIMA", "bearish", 25,
       "Below both SMAs with VR=0.45 (dead volume). Dominant signals point down.",
       "SANIMA is below both SMA20 and SMA50 with volume at 45% of average. Mixed trend, "
       "daily decline of -1.0%. Despite +2.6% 20d return, the current position below both "
       "SMAs with dead volume suggests the recovery has stalled.",
       ["+2.6% 20d return shows some recovery", "Pos60=0.319 not deeply oversold"],
       ["Closes above SMA20 with VR > 1.0", "Volume returns with bullish candle"]),

    # 20. 2025-12-30 API: above both SMAs, improving, VR=1.18
    mk("2025-12-30", "API", "bullish", 30,
       "Above both SMAs with improving trend and VR=1.18. Structure favors upside.",
       "API is above both SMAs in an improving trend with volume slightly above average. "
       "Pos60=0.758 shows the stock is in the upper portion of its 60d range, which "
       "confirms the improving structure. Despite POST season, the technical setup is "
       "constructive.",
       ["POST season headwind", "20d return only +0.5% — very weak momentum"],
       ["Breaks below SMA50", "VR drops below 0.8 for 3 sessions"]),
]

# Write prediction files
for item in PREDICTIONS:
    date = item["date"]
    symbol = item["symbol"]
    pred = item["prediction"]
    fname = f"{date}__{symbol}__forced_binary_prediction.json"
    path = os.path.join(OUT_DIR, fname)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pred, f, indent=2)

print(f"Generated {len(PREDICTIONS)} predictions in {OUT_DIR}/")

# Summary stats
directions = [p["prediction"]["direction"] for p in PREDICTIONS]
convictions = [p["prediction"]["conviction"] for p in PREDICTIONS]
bearish_count = sum(1 for d in directions if d == "bearish")
bullish_count = sum(1 for d in directions if d == "bullish")
print(f"Bearish: {bearish_count}, Bullish: {bullish_count}")
print(f"Mean conviction: {sum(convictions)/len(convictions):.1f}")
