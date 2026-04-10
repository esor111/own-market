"""One-time script: generate Juliet's Basket 3 (sector breadth) predictions."""
import json, os

OUT = os.path.join(os.path.dirname(__file__), "..", "agents", "agent-2-juliet", "predictions", "basket3_sector_breadth")
os.makedirs(OUT, exist_ok=True)

def mk(d, a, c, cr, t1, t2, t3, sl, ent, rr, th, ri, wc, q, dc):
    return {
        "direction": d, "action": a, "conviction": c, "conviction_rationale": cr,
        "price_targets": {
            "target_1": t1, "target_2": t2, "target_3": t3,
            "stop_loss": sl, "entry_zone": ent, "risk_reward_ratio": rr,
        },
        "thesis": th, "risks": ri, "what_would_change_mind": wc,
        "setup_quality": q, "data_completeness": dc,
        "similar_setup_awareness": {
            "similar_count": 0, "similar_resolved_success_rate_pct": None,
            "influence_on_conviction": "No similar setups available in replay basket mode.",
        },
    }

ALL = {}

# ============================================================
# JULY 2024 (10 cases) — Fiscal year end window
# ============================================================

ALL[("2024-07-03", "NABIL")] = mk(
    "bullish", "watch_only", 50,
    "Early July fiscal year end window, commercial bank improving above both SMAs. Moderate returns suggest trend is building, not yet confirmed strong.",
    510, 530, None, 460, [478, 488], 2.0,
    "NABIL is a commercial bank in early July — the strongest seasonal window for NEPSE banking stocks. Improving trend with price above both SMA20 (484 vs ~477) and SMA50. Returns are moderate (1.45% daily, 6.14% 5d) suggesting the move is still building rather than extended. Acceptable liquidity is the main constraint.",
    ["Only acceptable liquidity limits execution", "Returns still moderate — could stall before confirming uptrend"],
    ["Break below SMA20 with increasing volume", "5-day return turning negative"],
    "moderate", "partial"
)

ALL[("2024-07-03", "SANIMA")] = mk(
    "bullish", "watch_only", 52,
    "Same July fiscal window as NABIL but stronger positioning (pos20=0.794) and better recent returns. Commercial bank seasonal tailwind intact.",
    275, 290, None, 245, [255, 265], 2.0,
    "SANIMA shows stronger positioning in its 20-day range (0.794) than NABIL, with 5.99% 5-day returns and improving trend. Above both SMAs. Commercial bank in early July fiscal year end window, when banking historically leads NEPSE higher. Volume ratio 1.1 is modest but consistent.",
    ["Acceptable liquidity only", "NEPSE small market execution risk"],
    ["Break below 245 support", "Below SMA20 for 3+ sessions"],
    "moderate", "partial"
)

ALL[("2024-07-10", "EBL")] = mk(
    "bullish", "watch_only", 50,
    "Mid-July commercial bank with improving trend, above both SMAs. Volume ratio rising (1.41) shows increasing participation.",
    575, 600, None, 520, [540, 555], 2.0,
    "EBL at 548 with improving trend in mid-July peak season. Above both SMAs. Volume ratio of 1.41 suggests rising participation, which is positive for continuation. Returns are moderate (2.45% 20d) so extension risk is low. Commercial bank in fiscal year end window.",
    ["Returns still moderate — trend not yet confirmed as uptrend", "Acceptable liquidity only"],
    ["Break below 520 support", "Volume ratio declining below 1.0"],
    "moderate", "partial"
)

ALL[("2024-07-11", "API")] = mk(
    "bullish", "watch_only", 48,
    "Hydropower improving in July peak season. Above both SMAs but only acceptable liquidity and moderate returns.",
    185, 195, None, 165, [172, 178], 1.5,
    "API at 176.1 with improving trend in mid-July. Above both SMAs. Returns are moderate (2.98% 5d, 1.79% 20d) and positioning is mid-range (0.672 in 20d). Hydropower is less dominant than banking in NEPSE but still benefits from July seasonal tailwind.",
    ["Only acceptable liquidity", "Hydropower less market-dominant than banking sector"],
    ["Break below SMA50 at ~166", "5-day return turning negative"],
    "moderate", "partial"
)

ALL[("2024-07-14", "AKPL")] = mk(
    "bullish", "watch_only", 42,
    "Extreme momentum (8% daily, at top of all ranges) but mid-July seasonal tailwind. Extension reduces conviction significantly.",
    195, None, None, 165, [175, 182], 1.5,
    "AKPL shows extreme momentum with 7.98% daily gain and 10.68% 5-day return, sitting at the absolute top of both 20d and 60d ranges. While July peak season supports continuation, the degree of extension makes the next 5-10 sessions unpredictable. Close is at 181.4 vs 52-week high of 242.7, so there is overhead room, but the pace of advance is unsustainable.",
    ["Extreme overextension at top of all ranges", "Mean reversion risk is high after 8% daily move", "Acceptable liquidity limits orderly exit on pullback"],
    ["Any single-day decline exceeding 5%", "Break below SMA10 at ~165"],
    "low_conviction", "partial"
)

ALL[("2024-07-15", "UPPER")] = mk(
    "bullish", "watch_only", 48,
    "Strong volume surge (vr=2.7) validates the July momentum. Extended but volume confirms real buying interest.",
    190, 200, None, 160, [170, 180], 1.5,
    "UPPER at 176.7 with 12.55% 5-day return and volume ratio of 2.7 — the strongest volume signal in this batch. While the extension is significant (pos20=0.882), the volume surge suggests genuine institutional or large-block buying rather than retail chasing. July peak season supports continuation. Improving trend above both SMAs.",
    ["12.5% 5-day return is steep, pullback likely at some point", "Execution risk in NEPSE small market"],
    ["Volume ratio dropping below 1.5 without price follow-through", "Break below SMA20"],
    "moderate", "partial"
)

ALL[("2024-07-16", "MNBBL")] = mk(
    "bullish", "watch_only", 48,
    "Dev bank in confirmed uptrend (not just improving) during fiscal year end window. Extended but trend structure is solid.",
    400, 420, None, 355, [370, 385], 1.5,
    "MNBBL is a development bank in confirmed uptrend with 10.79% 20-day return. Price at 380, well above both SMAs. Volume ratio 1.68 shows healthy participation. Fiscal year end window provides structural tailwind. Position is extended (0.95 in 20d range) but uptrend classification suggests sustained buying pressure.",
    ["Extended at 0.95 in 20d range", "Only acceptable liquidity for a dev bank"],
    ["Trend degrading from uptrend to mixed", "Break below 10-day support at ~362"],
    "moderate", "partial"
)

ALL[("2024-07-16", "UPPER")] = mk(
    "neutral", "watch_only", 38,
    "Parabolic extension (18% 5d, 17% 20d, pos=0.991). July is strong but this pace makes next 5-10 sessions a coin flip.",
    None, None, None, None, [None, None], None,
    "UPPER at 186.7 has gained 18.16% in 5 days and 16.83% in 20 days, sitting at 0.991 in both ranges. Volume ratio 2.87 confirms massive participation but at parabolic pace. While July seasonal tailwind is real, this degree of extension makes mean reversion as probable as continuation over the next 5-10 sessions. Cannot call direction with honest conviction.",
    ["Parabolic extension — mean reversion risk extreme", "A -7% single-day reversal is plausible", "Gap between close and SMAs is widening unsustainably"],
    ["N/A — neutral call reflects genuine uncertainty, not lack of analysis"],
    "no_edge", "partial"
)

ALL[("2024-07-23", "JBBL")] = mk(
    "neutral", "watch_only", 35,
    "23% gain in 20 days, pos=0.988. Late July uptrend is extreme. Direction for next 5-10 sessions is not predictable at this extension.",
    None, None, None, None, [None, None], None,
    "JBBL at 355 with 22.84% 20-day return and 8.56% 5-day return in late July. Confirmed uptrend with strong liquidity (vr=1.6). At 0.988 position in both ranges, making new highs. While the uptrend structure is intact and July peak season persists, the degree of extension makes the direction of the next 5-10 sessions genuinely uncertain. Calling bullish at this level would be overconfident.",
    ["Extreme extension at 23% in 20 days", "Late July — approaching end of fiscal year window", "Mean reversion could be sharp given the run"],
    ["N/A — neutral reflects honest uncertainty at extreme extension"],
    "no_edge", "partial"
)

ALL[("2024-07-28", "JBBL")] = mk(
    "bearish", "avoid", 52,
    "34% in 20 days, 8% daily, at 52-week high. End of July approaching August correction window. Classic blow-off top pattern.",
    None, None, None, None, [None, None], None,
    "JBBL at 378 (52-week high 378.4) has gained 33.81% in 20 days and 8.31% today alone. This is extreme by any standard. With the fiscal year ending and August historically being a correction month, the probability of mean reversion in the next 5-10 sessions is elevated. The stock has literally nowhere to go but make new all-time highs or pull back, and at this extension, pullback is more probable.",
    ["Parabolic moves can extend further than expected", "July fiscal year end could provide one more push"],
    ["Sustained positive 5-day returns through first week of August", "No single-day decline exceeding 3% in next 5 sessions"],
    "moderate", "partial"
)

# ============================================================
# AUGUST 2024 (8 cases) — Post-fiscal results window
# ============================================================

ALL[("2024-08-01", "AKPL")] = mk(
    "neutral", "watch_only", 38,
    "38% in 20 days with first negative daily close. Post-fiscal window beginning. Extension too extreme for a directional call.",
    None, None, None, None, [None, None], None,
    "AKPL at 224.9 with 37.98% 20-day return but first negative daily close (-0.49%). Still in confirmed uptrend, strong liquidity (vr=1.39), above both SMAs. However, the degree of extension (38% in 20 days) combined with the start of August post-fiscal window makes the next 5-10 sessions genuinely unpredictable. The first negative daily close could be noise or the start of a reversal.",
    ["Extreme 38% 20-day extension", "Post-fiscal window historically sees profit-taking", "First negative daily close may signal fatigue"],
    ["N/A — neutral reflects genuine uncertainty"],
    "no_edge", "partial"
)

ALL[("2024-08-05", "API")] = mk(
    "bullish", "watch_only", 40,
    "At 52-week high with massive volume and 58% 20d return. Parabolic but breakout to new highs with strong volume suggests momentum could persist short-term.",
    280, None, None, 240, [260, 270], 1.0,
    "API at 269.7, literally at its 52-week high of 270, with 58.27% 20-day return and 6.22% daily gain. This is a parabolic move but the stock is making new highs with strong volume (avg traded value 270M vs 170M 20d avg). In NEPSE, breakouts to new 52-week highs in early August post-fiscal window can carry for a few more sessions before reversal. Calling bullish with very low conviction because momentum is undeniable but extension makes this extremely risky.",
    ["58% in 20 days — any reversal will be violent", "Post-fiscal window profit-taking risk", "Parabolic moves end without warning"],
    ["Any single-day decline exceeding 5%", "Volume drying up below 100M daily traded value"],
    "low_conviction", "partial"
)

ALL[("2024-08-06", "UPPER")] = mk(
    "neutral", "watch_only", 40,
    "Sharp 7% daily drop but still 27% up on 20d. Pullback in uptrend — could be dip opportunity or start of reversal. Cannot call direction.",
    None, None, None, None, [None, None], None,
    "UPPER at 200 after a sharp -7.02% daily decline, but still 26.58% up on 20 days. The uptrend label persists and price remains above both SMAs. This -7% drop could be a healthy pullback in a strong uptrend (dip-buy opportunity) or the start of a multi-session correction. In post-fiscal August, the correction interpretation is more likely but not certain enough to call bearish given the still-strong 20d return.",
    ["Could be start of multi-session correction", "Post-fiscal August seasonality favors correction", "Sharp single-day drops sometimes cascade in NEPSE small market"],
    ["N/A — neutral reflects genuine ambiguity between pullback and reversal"],
    "no_edge", "partial"
)

ALL[("2024-08-14", "MNBBL")] = mk(
    "bullish", "watch_only", 45,
    "Mid-August confirmed uptrend continuing. Moderate extension (14% 20d) with strong liquidity. Seasonal risk rising but momentum intact.",
    470, 490, None, 425, [440, 455], 1.5,
    "MNBBL at 449.2 in confirmed uptrend with 13.87% 20-day return. Strong liquidity and 7.72% 5-day return show continued momentum. Position at 0.941 in 20d range is extended but the uptrend structure is solid. Mid-August is getting late for the seasonal window, but the trend hasn't shown reversal signals yet.",
    ["August is typically when post-fiscal correction begins", "Extended at 0.941 in 20d range", "Dev bank liquidity can thin quickly on reversal"],
    ["5-day return turning negative", "Trend degrading from uptrend to mixed or below"],
    "moderate", "partial"
)

ALL[("2024-08-18", "NABIL")] = mk(
    "neutral", "watch_only", 40,
    "Momentum fading (0.3% daily vs 3.58% 5d). Still in uptrend but late August danger zone. Direction uncertain for next 5-10 sessions.",
    None, None, None, None, [None, None], None,
    "NABIL at 662 in uptrend but showing deceleration: daily return only 0.3% while 5-day is 3.58% and 20-day is 14.73%. The pace is slowing. Position at 0.723 has pulled back from recent highs. Late August is historically when NEPSE post-fiscal correction sets in. The uptrend structure is intact but momentum fade makes the next 5-10 sessions unpredictable.",
    ["Late August seasonal risk — correction window", "Momentum deceleration (daily << 5d return)", "Commercial bank may be shifting from accumulation to distribution"],
    ["N/A — neutral reflects momentum uncertainty in late seasonal window"],
    "low_conviction", "partial"
)

ALL[("2024-08-22", "JBBL")] = mk(
    "bearish", "avoid", 50,
    "10% single-day spike in late August at 52-week high. Blow-off signal in post-fiscal window. Mean reversion highly probable.",
    None, None, None, None, [None, None], None,
    "JBBL at 418 after a 10% single-day spike, making a new 52-week high (418 vs prior 52w high). This type of explosive single-day gain in late August is characteristic of a blow-off top rather than sustained breakout. The post-fiscal results window is ending, seasonal buying pressure is fading, and this kind of move attracts profit-taking. Still in uptrend with strong volume, but the 10% daily spike is more likely exhaustion than continuation.",
    ["Parabolic moves can extend — could gap up again next session", "Strong volume suggests genuine interest not just retail chasing"],
    ["Sustained positive returns for 3+ sessions after this spike", "No single-day decline >3% in next 5 sessions"],
    "moderate", "partial"
)

ALL[("2024-08-22", "NABIL")] = mk(
    "bearish", "avoid", 45,
    "Negative 5d return, losing momentum in late August. Commercial bank fading from post-fiscal peak.",
    None, None, None, None, [None, None], None,
    "NABIL at 654 with -0.65% daily and -0.91% 5-day return. The 20-day return (13.56%) masks the recent weakness. Position has dropped to 0.591 in 20d range — well off recent highs. Late August is the danger zone for NEPSE commercial banks as post-fiscal buying exhausts. The negative 5d return confirms momentum reversal is underway.",
    ["Book-closure season (Sep-Oct) could bring renewed buying", "Still above both SMAs — uptrend structure not fully broken"],
    ["Recovery above 670 with positive 5d return", "Volume surge with upward price action"],
    "moderate", "partial"
)

ALL[("2024-08-25", "MNBBL")] = mk(
    "bearish", "avoid", 48,
    "Trend downgraded from uptrend to improving. Sharp daily loss. Dev bank losing momentum at end of August.",
    None, None, None, None, [None, None], None,
    "MNBBL at 451 with -2.78% daily return and near-flat 5-day (+0.42%). Trend has been downgraded from uptrend to improving, which is a significant structural change. 20-day return has compressed to only 2.71% — most of the prior gains have been given back in relative terms. Position at 0.613 and falling. End of August for a dev bank means seasonal support is fading.",
    ["Still above both SMAs — structure not fully broken", "Oversold bounce possible after sharp daily loss"],
    ["5-day return turning positive above 2%", "Trend upgrading back to uptrend"],
    "moderate", "partial"
)

# ============================================================
# JULY 2025 (8 cases) — Fiscal year end window
# ============================================================

ALL[("2025-07-01", "SANIMA")] = mk(
    "bullish", "watch_only", 55,
    "Strong July day-1 setup. Confirmed uptrend, strong volume (vr=1.71), above both SMAs. Peak season just starting.",
    350, 365, None, 310, [325, 338], 2.0,
    "SANIMA at 334 on the first day of July — historically the strongest seasonal window for NEPSE. Confirmed uptrend with 5.96% 5-day return. Strong liquidity (vr=1.71) validates the move. Above both SMAs. Position is extended (0.962) but early July gives room for further seasonal gains. This is the strongest technical setup in the July 2025 batch.",
    ["Extended at 0.962 in 20d range", "Peak season could already be priced in"],
    ["Break below 310 support", "Volume ratio declining below 1.0"],
    "moderate", "partial"
)

ALL[("2025-07-02", "EBL")] = mk(
    "bullish", "watch_only", 45,
    "Improving commercial bank in early July but very low volume ratio (0.6) dampens conviction significantly.",
    670, 690, None, 625, [640, 655], 1.5,
    "EBL at 649.79 with improving trend in early July fiscal year end window. Above both SMAs. However, the volume ratio of 0.6 is very weak — 5-day average is well below 20-day average, suggesting declining participation despite the seasonal window. 20-day return is only 0.48%. The seasonal tailwind is real but the lack of volume support limits conviction.",
    ["Very low volume ratio (0.6) signals weak participation", "20d return only 0.48% — almost flat"],
    ["Volume ratio dropping further below 0.5", "Break below SMA20"],
    "low_conviction", "partial"
)

ALL[("2025-07-03", "NABIL")] = mk(
    "bullish", "watch_only", 48,
    "Commercial bank in July peak season, improving trend, above both SMAs. Mixed range signals (pos20=0.906 but pos60=0.456) moderate conviction.",
    520, 535, None, 480, [490, 502], 1.5,
    "NABIL at 498.22 shows divergent range positioning: high in 20-day range (0.906) but only mid-range in 60-day (0.456). This suggests a recent short-term rally that hasn't yet established broader strength. Above both SMAs with improving trend. Early July commercial bank benefits from fiscal year end window. Acceptable liquidity.",
    ["pos60=0.456 shows lack of broader trend conviction", "Only acceptable liquidity"],
    ["Break below 480", "Negative 5-day return while still in July"],
    "moderate", "partial"
)

ALL[("2025-07-10", "MNBBL")] = mk(
    "bullish", "watch_only", 50,
    "Dev bank in confirmed uptrend mid-July. 7.85% 20d return with moderate extension. Peak season supports continuation.",
    410, 425, None, 370, [382, 395], 1.5,
    "MNBBL at 389.25 in confirmed uptrend with 7.85% 20-day return. Price above both SMAs with position at 0.908 in 20d range. Volume ratio 1.32 shows healthy participation. Dev bank in mid-July fiscal year end window — seasonal tailwind intact. Extension is moderate compared to some of the 2024 July cases.",
    ["Dev bank liquidity can dry up quickly", "Extended at 0.908 in 20d range"],
    ["Break below SMA20", "Volume dropping below 20d average"],
    "moderate", "partial"
)

ALL[("2025-07-16", "MNBBL")] = mk(
    "bullish", "watch_only", 48,
    "Accelerating uptrend (13% 20d) with good volume (vr=1.73) but getting extended (pos=0.963). Late-July caution warranted.",
    425, 440, None, 385, [395, 410], 1.5,
    "MNBBL at 405.92 shows accelerating uptrend: 13.12% 20-day return, 5.88% 5-day, 3.25% daily. Volume ratio 1.73 confirms strong participation. However, position at 0.963 is very extended and mid-July is approaching the late window. The acceleration pattern often precedes exhaustion. Bullish but with reduced conviction due to extension.",
    ["Very extended at 0.963 — correction risk increasing", "Approaching late July when momentum typically peaks"],
    ["Negative 5-day return", "Volume ratio declining while price stalls"],
    "moderate", "partial"
)

ALL[("2025-07-17", "API")] = mk(
    "bullish", "watch_only", 48,
    "Hydropower improving in July peak season. Good volume, above both SMAs. Moderate positioning provides room to run.",
    320, 335, None, 290, [298, 308], 1.5,
    "API at 304.55 with improving trend, 2.92% daily gain, and 3.66% 5-day return. Above both SMAs. Volume ratio 1.29 is healthy. Position at 0.836 in 20d range but only 0.508 in 60d range — room for broader trend development. Hydropower in July peak season benefits from general market tailwind.",
    ["pos60=0.508 suggests mid-range in broader context — could stall", "Hydropower less dominant than banking in NEPSE"],
    ["Break below 290 (near SMA50)", "Trend degrading from improving to mixed"],
    "moderate", "partial"
)

ALL[("2025-07-20", "AKPL")] = mk(
    "neutral", "watch_only", 40,
    "Negative daily return despite positive 5d. Mid-range positioning. Mixed signals suggest wait-and-see.",
    None, None, None, None, [None, None], None,
    "AKPL at 265.02 with -1.48% daily return, which contradicts the positive 5-day (4.46%) and 20-day (2.55%) returns. Position at 0.602 in 20d range is mid-range, not providing a clear direction signal. Still above both SMAs with improving trend, but the negative daily in the context of late July suggests momentum may be fading for this name.",
    ["Daily weakness could be start of reversal", "Late July — seasonal window narrowing"],
    ["N/A — neutral reflects mixed daily vs weekly signals"],
    "low_conviction", "partial"
)

ALL[("2025-07-20", "UPPER")] = mk(
    "bullish", "watch_only", 48,
    "Good volume surge (vr=2.02) in July peak season. Improving trend, moderate positioning. Volume validates buying interest.",
    220, 230, None, 195, [202, 212], 1.5,
    "UPPER at 207.8 with 5.02% 5-day return and volume ratio of 2.02 — strong volume surge. Improving trend above both SMAs. Position at 0.698 in 20d range provides room for upside. Late July but volume surge suggests fresh buying interest. Hydropower benefiting from seasonal tailwind.",
    ["Late July — seasonal window narrowing", "Improving trend not yet confirmed as uptrend"],
    ["Volume ratio dropping below 1.0", "Break below 195 support area"],
    "moderate", "partial"
)

# ============================================================
# AUGUST 2025 (6 cases) — hostile avoid supplement
# ============================================================

ALL[("2025-08-03", "API")] = mk(
    "bearish", "avoid", 55,
    "Below SMA20, mixed trend, -5.61% 5d return, near bottom of 20d range. Clear post-fiscal correction underway.",
    None, None, None, None, [None, None], None,
    "API at 302.47 with mixed trend, below SMA20, and -5.61% 5-day return. Position at 0.277 in 20d range — near the bottom. Volume ratio 0.99 is flat, not showing the kind of volume surge that would indicate capitulation/reversal. Post-fiscal August correction is underway. The structure has clearly weakened from the July setup.",
    ["Oversold bounce possible", "Still above SMA50 — structural floor not broken"],
    ["Recovery above SMA20 with positive 5d return", "Volume surge with upward price action"],
    "moderate", "partial"
)

ALL[("2025-08-03", "JBBL")] = mk(
    "bearish", "avoid", 50,
    "Despite uptrend label, 5d return is -5.33%. Dev bank pulling back hard in post-fiscal August.",
    None, None, None, None, [None, None], None,
    "JBBL at 370.24 still carries an uptrend label but the 5-day return is -5.33% and daily is -1.83%. Position at 0.525 in 20d range has dropped to mid-range. Still above both SMAs, which prevents a higher conviction bearish call, but the momentum reversal is clear. Post-fiscal August historically brings correction to dev banks that ran hard in July.",
    ["Uptrend label still intact — could be a pullback in trend", "Still above both SMAs"],
    ["5-day return turning positive", "Reclaiming 380+ level with volume"],
    "moderate", "partial"
)

ALL[("2025-08-03", "NABIL")] = mk(
    "bearish", "avoid", 55,
    "Below SMA20, mixed trend, -4.28% 5d. Commercial bank weakening clearly in post-fiscal August.",
    None, None, None, None, [None, None], None,
    "NABIL at 524.4 with mixed trend and price below SMA20. 5-day return of -4.28% and daily of -2.25% confirm active selling pressure. Position at 0.455 in 20d range has dropped to lower half. This is a clean weakening pattern in a major commercial bank during post-fiscal August. The structure has broken down from the improving July setup.",
    ["Oversold bounce possible from key support levels", "Commercial bank may attract dip buyers"],
    ["Recovery above SMA20 with positive 5d return", "Volume surge with price recovery above 535"],
    "moderate", "partial"
)

ALL[("2025-08-04", "AKPL")] = mk(
    "bearish", "avoid", 52,
    "Sharp -7.79% 5d pullback despite uptrend label. Position dropped to 0.38 in 20d range. Post-fiscal correction.",
    None, None, None, None, [None, None], None,
    "AKPL at 272.08 with -7.79% 5-day return — a sharp pullback. Despite the uptrend label persisting (likely lagging), position has dropped to 0.38 in the 20d range, well into the lower half. Still above both SMAs technically. The post-fiscal August correction is hitting hydropower. Volume ratio 0.95 doesn't show panic selling but the trend is clearly weakening.",
    ["Still above both SMAs — structural floor intact", "Could be a dip opportunity if July uptrend resumes"],
    ["5-day return turning positive above 2%", "Position recovering above 0.7 in 20d range"],
    "moderate", "partial"
)

ALL[("2025-08-04", "EBL")] = mk(
    "bearish", "avoid", 52,
    "Below SMA20, mixed trend, very low volume (vr=0.65). Commercial bank losing momentum in post-fiscal window.",
    None, None, None, None, [None, None], None,
    "EBL at 716.91 with mixed trend, below SMA20, and very low volume ratio (0.65). The 5-day return of -2.36% confirms weakening. Position at 0.528 in 20d range is mid-range but trending down. The low volume is particularly concerning — it suggests sellers are not being met by buyers. Post-fiscal August is the expected correction window for commercial banks.",
    ["EBL is a major bank — could attract institutional dip buying", "Still above SMA50 — broader structure intact"],
    ["Volume surge above vr=1.5 with positive price action", "Recovery above SMA20"],
    "moderate", "partial"
)

ALL[("2025-08-04", "MNBBL")] = mk(
    "bearish", "avoid", 52,
    "Sharp -7.38% 5d pullback. Dev bank momentum reversing in post-fiscal August despite uptrend label.",
    None, None, None, None, [None, None], None,
    "MNBBL at 455.07 with -7.38% 5-day return despite uptrend label and price above both SMAs. The 20-day return of 21.7% masks the sharp recent reversal. Position at 0.639 is declining. Dev banks with thin liquidity can correct faster than commercial banks once momentum shifts. Post-fiscal August correction underway.",
    ["Uptrend label still intact — could resume", "Still above both SMAs by a margin", "20d return still strongly positive"],
    ["5-day return turning positive", "Volume ratio increasing with upward price action"],
    "moderate", "partial"
)

# ============================================================
# OCTOBER 2025 (3 cases) — Book-closure/dividend window
# ============================================================

ALL[("2025-10-01", "AKPL")] = mk(
    "neutral", "watch_only", 35,
    "Below SMA50, extremely low volume (vr=0.48). No directional conviction. Market participation minimal.",
    None, None, None, None, [None, None], None,
    "AKPL at 260 with improving trend but below SMA50 and extremely low volume ratio (0.48). Position at 0.869 in 20d range seems bullish but 0.411 in 60d range tells the real story — the stock is in the lower half of its broader range. The 0% daily return and near-zero 20d return (0.73%) show complete inertia. In book-closure window but no participation to support a directional call.",
    ["Very low volume makes any move potentially sharp and illiquid", "Below SMA50 suggests structural weakness"],
    ["N/A — neutral reflects no-edge setup with dead volume"],
    "no_edge", "partial"
)

ALL[("2025-10-01", "API")] = mk(
    "neutral", "watch_only", 35,
    "Same dead-volume pattern as AKPL. Below SMA50, flat returns, no participation. No edge.",
    None, None, None, None, [None, None], None,
    "API at 292 mirrors AKPL's setup: improving trend but below SMA50, low volume ratio (0.59), flat returns (0.26% 20d). Position at 0.436 in 60d range confirms broader weakness. Book-closure window could provide a catalyst but current volume suggests the market isn't positioning for it. No honest basis for a directional call.",
    ["Low volume means sharp moves possible in either direction", "Below SMA50 structural weakness"],
    ["N/A — neutral reflects dead-volume no-edge setup"],
    "no_edge", "partial"
)

ALL[("2025-10-06", "EBL")] = mk(
    "neutral", "watch_only", 32,
    "Extremely low volume (vr=0.4), completely flat (0% 5d), below SMA50. No signal whatsoever.",
    None, None, None, None, [None, None], None,
    "EBL at 720 with 0% 5-day return and volume ratio of 0.4 — the lowest in this entire basket. Below SMA50. Position at 0.511 in 60d range is mid-range but the complete lack of volume makes any technical signal meaningless. The improving trend label and high 20d position (0.941) contradict the dead volume. This is a no-information setup.",
    ["Dead volume means any directional bet is random", "Below SMA50 despite high 20d position — conflicting signals"],
    ["N/A — neutral reflects absence of any usable signal"],
    "no_edge", "partial"
)

# ============================================================
# NOVEMBER 2025 (3 cases) — Book-closure window
# ============================================================

ALL[("2025-11-16", "EBL")] = mk(
    "neutral", "watch_only", 35,
    "Near bottom of 60d range (pos60=0.08), below SMA50. Improving trend and above SMA20 suggest possible basing but not confirmed.",
    None, None, None, None, [None, None], None,
    "EBL at 632 with pos60=0.08 — near the absolute bottom of its 60-day range. Below SMA50 but above SMA20 with improving trend label. This divergence suggests the stock may be basing after a decline (above short-term average but well below medium-term). 20-day return is nearly flat (0.16%). Could be accumulation, could continue drifting. Not enough confirmation for a directional call.",
    ["pos60=0.08 means near 60d low — could continue declining", "Below SMA50 shows broader weakness"],
    ["N/A — neutral reflects possible-but-unconfirmed basing pattern"],
    "no_edge", "partial"
)

ALL[("2025-11-23", "UPPER")] = mk(
    "neutral", "watch_only", 38,
    "Below SMA50, pos60=0.395. Some positive daily momentum but structure still weak. Not enough for a directional call.",
    None, None, None, None, [None, None], None,
    "UPPER at 179 with 1.7% daily and 2.87% 5-day return — showing some positive momentum. Improving trend above SMA20 but below SMA50. Position at 0.395 in 60d range means still in lower half of broader range. The positive daily action is encouraging but the structural weakness (below SMA50) and November seasonality don't support a bullish call yet.",
    ["Below SMA50 — structural weakness persists", "November is typically quiet for NEPSE"],
    ["N/A — neutral reflects improving but insufficient setup"],
    "low_conviction", "partial"
)

ALL[("2025-11-24", "API")] = mk(
    "bullish", "watch_only", 45,
    "Above both SMAs, 5.37% 20d return, improving trend. Strongest November case. Book-closure window may provide catalyst.",
    300, 310, None, 272, [280, 290], 1.5,
    "API at 286.5, above both SMA20 and SMA50, with 5.37% 20-day return. Improving trend with position at 0.672 in 60d range — in the upper half of the broader range, unlike the October AKPL/API/EBL cases which were below SMA50. Acceptable liquidity (vr=0.86 is not ideal but not dead). This is the strongest November setup with genuine structural support.",
    ["Acceptable liquidity only — execution risk", "November is seasonally quiet"],
    ["Break below SMA50", "5-day return turning negative"],
    "moderate", "partial"
)


# ============================================================
# Write all 38 predictions
# ============================================================
written = 0
for (date, symbol), pred in sorted(ALL.items()):
    path = os.path.join(OUT, f"{date}__{symbol}__1D__prediction.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pred, f, indent=2)
    written += 1

print(f"Wrote {written} predictions to {OUT}")

# Summary stats
dirs = [p["direction"] for p in ALL.values()]
acts = [p["action"] for p in ALL.values()]
convs = [p["conviction"] for p in ALL.values()]
print(f"Direction: bull={dirs.count('bullish')} bear={dirs.count('bearish')} neut={dirs.count('neutral')}")
print(f"Action:    buy={acts.count('buy')} watch={acts.count('watch_only')} avoid={acts.count('avoid')}")
print(f"Conviction: mean={sum(convs)/len(convs):.1f} min={min(convs)} max={max(convs)}")
