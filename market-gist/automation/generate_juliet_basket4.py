"""One-time script: generate Juliet's Basket 4 (sector-rule stress) predictions."""
import json, os

OUT = os.path.join(os.path.dirname(__file__), "..", "agents", "agent-2-juliet", "predictions", "basket4_sector_rule_stress")
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
# JULY 2023 (4 cases)
# ============================================================

ALL[("2023-07-06", "UPPER")] = mk(
    "bullish", "watch_only", 40,
    "10% daily spike closing at day high shows strong demand. Uptrend confirmed. But VR=0.66 and weak sector regime limit conviction.",
    490, 510, None, 440, [465, 478], 1.5,
    "UPPER at 474 after a 9.85% daily gain, closing at the high of the day (474 vs open 426). Uptrend label confirmed, above both SMAs. The close-at-high pattern signals strong buying demand rather than a fade. July fiscal year end window provides seasonal tailwind. However, the volume ratio of 0.66 means 5-day volume is well below 20-day average, and the sector regime is weak. The 10% daily gain on declining relative volume could be a thin-market spike rather than broad-based buying.",
    ["Volume ratio 0.66 — declining participation despite price spike", "Weak sector regime — UPPER may be an outlier, not a sector move", "52-week high at 590, current at 474 — overhead resistance exists"],
    ["Volume ratio dropping further below 0.5 with price stalling", "Break below SMA20 at ~464"],
    "low_conviction", "partial"
)

ALL[("2023-07-17", "NABIL")] = mk(
    "bullish", "watch_only", 48,
    "Mid-July fiscal year end window. Commercial bank improving above both SMAs. Sector bullish. Moderate returns building.",
    635, 650, None, 590, [600, 615], 1.5,
    "NABIL at 611 with improving trend in mid-July fiscal year end window. Above both SMAs. Daily gain of 1.97% and 5-day return of 4.8% show building momentum. Sector regime is bullish per manifest context. Strong liquidity but VR at 0.75 is slightly concerning — 5-day volume below 20-day average. Commercial bank in peak seasonal window.",
    ["VR 0.75 — declining volume participation", "Improving but not yet confirmed uptrend"],
    ["Break below SMA50 at ~598", "5-day return turning negative"],
    "moderate", "partial"
)

ALL[("2023-07-18", "SANIMA")] = mk(
    "bullish", "watch_only", 48,
    "Strong uptrend in July with bullish sector. 14.46% 20d return shows real momentum. Extended (pos=0.94) but July peak supports continuation.",
    295, 310, None, 265, [278, 288], 1.5,
    "SANIMA at 285 in confirmed uptrend with 14.46% 20-day return and 11.11% 5-day return. At 0.939 in 20d range — extended but in peak July with bullish sector regime. Volume ratio 1.31 confirms participation. Acceptable liquidity is the main constraint. The strength of the move and seasonal tailwind support continuation despite extension.",
    ["Very extended at 0.939/0.952 in both ranges", "Acceptable liquidity limits orderly exit on reversal", "14.46% in 20 days — mean reversion risk grows"],
    ["Negative 5-day return while still in July", "Volume ratio dropping below 1.0"],
    "moderate", "partial"
)

ALL[("2023-07-19", "MNBBL")] = mk(
    "bullish", "watch_only", 45,
    "Dev bank in confirmed uptrend, mid-July, bullish sector. Extended (pos=0.93) but moderate 20d return (5%). VR below 1 is a concern.",
    440, 460, None, 405, [415, 428], 1.5,
    "MNBBL at 424.5 in confirmed uptrend during mid-July fiscal year end window. Sector regime bullish. Above both SMAs with position at 0.928/0.95 in both ranges. Volume ratio 0.93 is just below 1 — slightly declining participation. 20-day return of 5.07% is moderate, not extreme. Acceptable liquidity for a development bank. 52-week high at 503, so overhead room exists (~18% to 52w high).",
    ["VR 0.93 — slight volume decline", "Only acceptable liquidity — dev bank execution risk", "Extended position (0.93) in both ranges"],
    ["Break below SMA20 at ~441", "VR dropping below 0.7 with stalling price"],
    "moderate", "partial"
)

# ============================================================
# SEPTEMBER 2025 — COMMERCIAL BANKS (3 cases)
# ============================================================

ALL[("2025-09-01", "EBL")] = mk(
    "bullish", "watch_only", 52,
    "Strong setup: confirmed uptrend, VR=1.33, strong liquidity, high in both ranges. Best technical quality in this batch.",
    790, 810, None, 740, [755, 770], 1.5,
    "EBL at 765.33 in confirmed uptrend with 6.75% 20-day return. Strong liquidity and volume ratio of 1.33 confirms rising participation. Position at 0.846 in 20d and 0.923 in 60d shows consistent strength across timeframes. This is the cleanest technical setup in the September batch — everything aligns. Commercial bank in dividend/book-closure secondary season.",
    ["Extended in 60d range (0.923)", "September is secondary season, not peak July"],
    ["Break below SMA20", "Volume ratio dropping below 1.0 with price decline"],
    "moderate", "partial"
)

ALL[("2025-09-03", "EBL")] = mk(
    "bullish", "watch_only", 45,
    "Pullback in confirmed uptrend. -1.45% daily but still above SMAs, 20d return positive. Structure intact.",
    780, 800, None, 725, [742, 758], 1.5,
    "EBL at 750.39 after a -1.45% daily pullback. Position dropped from 0.846 to 0.62 in 20d range. Still in confirmed uptrend, still above both SMAs, still strong liquidity (VR=1.23). The 5d return is barely negative (-0.16%) while 20d return remains positive (6.34%). This looks like a healthy pullback in an uptrend rather than a reversal — but the daily weakness reduces conviction from the Sep 1 call.",
    ["Daily pullback could continue into multi-session correction", "5d return just turned negative — early momentum loss signal"],
    ["5-day return exceeding -3%", "Break below SMA50"],
    "moderate", "partial"
)

ALL[("2025-09-28", "NABIL")] = mk(
    "bullish", "watch_only", 45,
    "Late September commercial bank, improving above both SMAs. Moderate returns, decent VR. Book-closure window provides catalyst.",
    540, 555, None, 510, [520, 530], 1.5,
    "NABIL at 527 with improving trend, above both SMAs. 3.3% 5-day return shows recent momentum. VR 1.24 is healthy. Position at 0.833 in 20d range is elevated but not extreme. pos60=0.615 shows mid-range broader positioning with room to run. Late September book-closure window. Acceptable liquidity is the main limitation.",
    ["Only acceptable liquidity", "Improving but not confirmed uptrend — still building"],
    ["Break below SMA50", "Negative 5-day return"],
    "moderate", "partial"
)

# ============================================================
# SEPTEMBER 2025 — DEVELOPMENT BANKS (10 cases)
# ============================================================

ALL[("2025-09-21", "MNBBL")] = mk(
    "bullish", "watch_only", 45,
    "5.83% daily spike shows buying interest. Improving trend above both SMAs. Mid-range position (0.57) provides room to run.",
    465, 477, None, 425, [440, 455], 1.5,
    "MNBBL at 450.84 after a 5.83% daily gain. Improving trend above both SMAs. Position at 0.57 in 20d range is mid-range — NOT extended — which is unusual after a big daily gain. This means the stock still has room to the 20d resistance at 477. VR 1.08 is modest. Strong liquidity. The key question is whether this spike marks the start of a sustained move or a one-day event. Market regime is weak but sector regime is improving — positive divergence for dev banks.",
    ["Weak market regime overall", "VR only 1.08 — modest volume confirmation", "Dev bank spikes can be one-day events in thin markets"],
    ["Negative daily close on next session erasing the gain", "VR dropping below 0.8"],
    "moderate", "partial"
)

ALL[("2025-09-22", "MNBBL")] = mk(
    "bullish", "watch_only", 42,
    "Flat follow-through (0% daily) after yesterday's spike. VR rising to 1.34 is positive. Consolidation rather than reversal.",
    465, 477, None, 430, [445, 455], 1.5,
    "MNBBL at 450.84 for the second consecutive session (unchanged close). VR increased from 1.08 to 1.34 — volume is actually rising even though price is flat. This is classic consolidation: the spike held, volume confirms interest, and the stock isn't giving back the gain. Still above both SMAs, improving trend. The lack of follow-through is slightly concerning but the volume signal is encouraging.",
    ["Zero follow-through after a 5.83% spike", "Weak market regime", "Could be trapped buyers with no follow-on demand"],
    ["Break below SMA50 at ~445", "VR declining below 1.0 on next session"],
    "moderate", "partial"
)

ALL[("2025-09-23", "MNBBL")] = mk(
    "bullish", "watch_only", 45,
    "Follow-through confirmed: +1.37% daily, 4.43% 5d, VR rising to 1.41. Building momentum after consolidation.",
    470, 485, None, 435, [448, 460], 1.5,
    "MNBBL at 457 with 1.37% daily gain — finally showing follow-through after the Sep 21 spike and Sep 22 consolidation. 5-day return now 4.43%. VR climbed to 1.41 from 1.34 — volume continues to build. Position at 0.672 in 20d range still has room to 20d resistance at 477. Sector regime improving. This three-day sequence (spike → hold → advance) is a constructive pattern for a development bank.",
    ["Weak overall market could cap upside", "Approaching 20d resistance at 477"],
    ["Volume ratio declining while price stalls at resistance", "Negative daily return wiping out the 3-day build"],
    "moderate", "partial"
)

ALL[("2025-09-25", "MNBBL")] = mk(
    "bullish", "watch_only", 48,
    "Strongest VR of the MNBBL sequence (1.79). 7.86% 5d return confirms real momentum. Best dev bank setup this batch.",
    475, 490, None, 440, [452, 462], 1.5,
    "MNBBL at 459.5 with 7.86% 5-day return and VR of 1.79 — the strongest volume signal in the entire September MNBBL sequence. Position at 0.884 in 20d range is extended but the volume surge validates the move. Above both SMAs. This is the peak-confidence moment of the MNBBL September rally: prices advancing with rising volume, clear improving trend. Sector improving while market is mixed.",
    ["Very extended at 0.884 — approaching 20d resistance", "Volume surges in dev banks can peak abruptly", "Market regime is mixed — not supportive"],
    ["VR declining below 1.2 with price failing at 20d resistance (~477)", "Negative 5d return"],
    "moderate", "partial"
)

ALL[("2025-09-28", "MNBBL")] = mk(
    "bullish", "watch_only", 42,
    "Flat daily (0.04%) but 20d return grew to 4.09%. Momentum slowing from VR=1.79 peak. Still above SMAs but decelerating.",
    470, 480, None, 440, [452, 462], 1.5,
    "MNBBL at 459.7 with only 0.04% daily gain after the strong Sep 25 session. VR dropped from 1.79 to 1.46 — still above 1 but declining. 5d return compressed from 7.86% to 1.97%. The rally is clearly decelerating. Still above both SMAs, still improving trend, still bullish on structure. But the momentum fade reduces conviction. Position at 0.888 is near resistance.",
    ["Momentum clearly decelerating (VR 1.79→1.46, 5d return 7.86→1.97)", "Near 20d resistance at 477", "Stalling at resistance is common for dev banks"],
    ["Two consecutive negative daily closes", "VR dropping below 1.0"],
    "moderate", "partial"
)

ALL[("2025-09-29", "MNBBL")] = mk(
    "neutral", "watch_only", 38,
    "Second flat day (0% daily). VR declining (1.13). Momentum dead. Can no longer honestly call bullish with stalled price and fading volume.",
    None, None, None, None, [None, None], None,
    "MNBBL at 459.7 for the second consecutive flat close. VR dropped further from 1.46 to 1.13. 5d return compressed to 1.97%. The three-day momentum fade is clear: Sep 25 peak (VR=1.79) → Sep 28 (VR=1.46) → Sep 29 (VR=1.13). Still above both SMAs and still in improving trend, but there is no honest basis for calling bullish when both price and volume are stalling. The stock appears to have found a ceiling near 460.",
    ["Could resume upward if new buying appears", "Still above both SMAs — no bearish structure yet"],
    ["N/A — neutral reflects honest assessment of stalling momentum"],
    "low_conviction", "partial"
)

ALL[("2025-09-30", "MNBBL")] = mk(
    "neutral", "watch_only", 36,
    "Third flat day. VR now 0.99 — essentially dead volume. The September rally is over for MNBBL. No edge in either direction.",
    None, None, None, None, [None, None], None,
    "MNBBL at 459.7 for the third consecutive flat close. VR has dropped to 0.99 — effectively 1:1 with 20-day average, meaning the earlier volume surge has completely faded. 5d return compressed to 0.59%. The September MNBBL sequence tells a clear story: spike (Sep 21) → build (Sep 23-25) → stall and fade (Sep 28-30). Still above both SMAs with improving trend label, but these are lagging indicators. The forward signal is dead momentum.",
    ["Improving trend structure still intact", "Could be accumulation at higher level before next leg"],
    ["N/A — neutral reflects three-day stall pattern"],
    "no_edge", "partial"
)

ALL[("2025-09-23", "JBBL")] = mk(
    "neutral", "watch_only", 38,
    "Below SMA50, pos60=0.283 (near 60d low). Improving label but weak broader structure. No confident directional call.",
    None, None, None, None, [None, None], None,
    "JBBL at 332 with improving trend above SMA20 but below SMA50. Position at 0.283 in 60d range — near the bottom of the broader range. 20-day return is essentially zero (0.04%). VR barely above 1 (1.05). Acceptable liquidity. The improving label and above-SMA20 position suggest possible basing, but below SMA50 with near-zero 20d returns doesn't justify a bullish call. This is a structurally weak dev bank showing early signs of possible recovery, not yet confirmed.",
    ["Below SMA50 means broader trend is still down", "Dev bank with acceptable liquidity — thin execution"],
    ["N/A — neutral reflects unconfirmed basing pattern"],
    "no_edge", "partial"
)

ALL[("2025-09-30", "JBBL")] = mk(
    "neutral", "watch_only", 32,
    "Dead volume (VR=0.54). Below SMA50. 5d return slightly negative. No signal, no edge.",
    None, None, None, None, [None, None], None,
    "JBBL at 331 with VR of 0.54 — the lowest in this entire basket. Below SMA50. 5d return of -0.3%, 20d return of 0.14%. Improving trend label persists but every volume and return metric says there is zero momentum. Position at 0.274 in 60d range confirms broader weakness. This is a no-information setup where any directional bet is random.",
    ["Dead volume means sharp moves possible in either direction", "Below SMA50 with negative 5d return"],
    ["N/A — neutral reflects dead-volume no-edge environment"],
    "no_edge", "partial"
)

# ============================================================
# SEPTEMBER 2025 — HYDROPOWER (2 cases)
# ============================================================

ALL[("2025-09-23", "AKPL")] = mk(
    "bullish", "watch_only", 42,
    "Positive momentum (2.51% daily, 3.29% 5d) in improving trend. Below SMA50 but above SMA20. Recovery pattern from a bottom.",
    270, 280, None, 250, [255, 264], 1.5,
    "AKPL at 261 with 2.51% daily gain and 3.29% 5-day return. Improving trend above SMA20. Below SMA50 at ~265, which is a concern, but the stock is recovering toward it. Position at 0.695 in 20d range shows room to push higher. pos60=0.424 means lower half of broader range — this is a recovery from a bottom, not continuation of a trend. VR 1.04 is neutral. September book-closure window could provide catalyst for hydropower names.",
    ["Below SMA50 — structural weakness not yet resolved", "Low in 60d range means this is a recovery bet, not a trend bet"],
    ["Break below SMA20", "5d return turning negative"],
    "low_conviction", "partial"
)

ALL[("2025-09-28", "API")] = mk(
    "neutral", "watch_only", 35,
    "Below SMA50, near-zero 20d return (0.13%). High in 20d range but low in 60d. Short-term bounce in broader weakness.",
    None, None, None, None, [None, None], None,
    "API at 292 with improving trend, above SMA20 but below SMA50. 20d return is essentially zero (0.13%). Position at 0.869 in 20d range seems elevated but pos60=0.436 reveals the broader weakness — the stock is in the lower half of its 60d range. VR 1.05 is neutral. This is a short-term bounce that hasn't yet proven it can break above the medium-term trend (SMA50). Without that confirmation, direction for the next 5-10 sessions is uncertain.",
    ["Could break above SMA50 and confirm recovery", "Still above SMA20 with improving label"],
    ["N/A — neutral reflects unresolved structural weakness"],
    "no_edge", "partial"
)

ALL[("2025-09-29", "API")] = mk(
    "neutral", "watch_only", 33,
    "Flat (0% daily), VR dropped to 0.73. Same structural weakness as yesterday but now with declining volume. No signal.",
    None, None, None, None, [None, None], None,
    "API at 292 for the second session, completely flat. VR dropped from 1.05 to 0.73 — declining participation. Still below SMA50, still near-zero 20d return. The declining volume on a flat day below SMA50 doesn't support any directional conviction. Improving label persists but it is a lagging indicator when current price action and volume are dead.",
    ["Could resume if broader market or sector rally materializes", "Still above SMA20"],
    ["N/A — neutral reflects dead momentum below SMA50"],
    "no_edge", "partial"
)

# ============================================================
# DECEMBER 2025 — COMMERCIAL BANKS (5 cases)
# ============================================================

ALL[("2025-12-16", "SANIMA")] = mk(
    "bullish", "watch_only", 42,
    "Confirmed uptrend, above both SMAs. Quiet season but structure is positive. Low VR (0.67) and low pos60 (0.32) limit conviction.",
    320, 330, None, 298, [305, 315], 1.5,
    "SANIMA at 311 in confirmed uptrend above both SMAs. 20d return of 3.98% is modest but positive. The concern is the VR at 0.67 — 5-day volume well below 20-day average — and pos60 at 0.32, meaning the stock is still in the lower portion of its 60d range despite the uptrend label. This suggests a recent recovery from a decline. December is quiet season but the uptrend structure provides a baseline bullish lean.",
    ["Very low VR (0.67) — declining participation", "pos60=0.32 means still near 60d low structurally", "December quiet season — limited catalyst"],
    ["VR dropping below 0.5", "Break below SMA20"],
    "low_conviction", "partial"
)

ALL[("2025-12-17", "SANIMA")] = mk(
    "bullish", "watch_only", 42,
    "Uptrend continues with small daily gain. Still low VR (0.68). Consistent with Dec 16 read — positive structure, weak participation.",
    322, 332, None, 300, [307, 316], 1.5,
    "SANIMA at 313, slight advance from 311 on Dec 16. Uptrend persists, 1.43% 5d return. Still above both SMAs. VR still low (0.68). pos60 improved slightly to 0.41 but remains in the lower half. The day-over-day confirmation is mildly positive — the stock isn't pulling back, just advancing slowly. Conviction unchanged from Dec 16.",
    ["Persistent low VR — market doesn't believe in the move yet", "pos60 still below 0.5"],
    ["VR dropping further while price stalls", "Negative 5d return"],
    "low_conviction", "partial"
)

ALL[("2025-12-24", "SANIMA")] = mk(
    "bullish", "watch_only", 43,
    "2.24% daily gain and VR finally above 1 (1.07). First volume confirmation in the SANIMA December sequence. Improving trend.",
    330, 340, None, 308, [315, 322], 1.5,
    "SANIMA at 319 after a 2.24% daily gain. VR has finally risen above 1.0 to 1.07 — the first volume confirmation in this December sequence (Dec 16: 0.67, Dec 17: 0.68, Dec 24: 1.07). Trend label switched from uptrend to improving (likely due to 20d return compression to 1.59%), but the daily and VR signals are the most positive of the three December SANIMA dates. pos60 at 0.547 — above mid-range for the first time.",
    ["Trend downgraded from uptrend to improving", "December quiet season limits upside catalyst"],
    ["VR dropping back below 0.8", "Break below SMA20"],
    "moderate", "partial"
)

ALL[("2025-12-29", "EBL")] = mk(
    "bullish", "watch_only", 40,
    "Improving above both SMAs, VR=1.05. Low pos60 (0.324) suggests recovery from decline. Modest returns, no strong signal.",
    670, 685, None, 640, [650, 660], 1.5,
    "EBL at 657.5 with improving trend, above both SMAs. 20d return 1.15%, VR 1.05. Position at 0.762 in 20d range but only 0.324 in 60d — the stock is recovering from a broader decline but still low in the 60d structure. The improving trend and positive VR are modest positives. Acceptable liquidity in late December. Not a strong setup but lean bullish on structure.",
    ["pos60=0.324 — still near 60d low", "Acceptable liquidity in late December — thin trading", "Modest returns don't signal strong momentum"],
    ["Break below SMA50", "Negative 5d return"],
    "low_conviction", "partial"
)

ALL[("2025-12-31", "EBL")] = mk(
    "bullish", "watch_only", 43,
    "Continuation from Dec 29. Higher close (663 vs 657.5), VR=1.19, pos20=0.963. Momentum building but pos60 still low.",
    680, 695, None, 645, [655, 668], 1.5,
    "EBL at 663, advancing from 657.5 on Dec 29. VR increased from 1.05 to 1.19 — volume building. pos20 at 0.963 is very extended in the 20d range but pos60 at 0.37 shows the broader recovery is still early. 2.43% 5d return and 2.95% 20d return are modest but consistently positive. Improving trend, above both SMAs. The day-over-day improvement in both price and volume justifies slightly higher conviction than Dec 29.",
    ["Very extended in 20d range (0.963)", "pos60 still low — could stall", "Year-end thin trading"],
    ["Break below SMA20", "VR dropping below 0.8"],
    "moderate", "partial"
)

# ============================================================
# DECEMBER 2025 — HYDROPOWER (6 cases)
# ============================================================

ALL[("2025-12-01", "API")] = mk(
    "bullish", "watch_only", 45,
    "High VR (1.62) stands out — volume surge with improving trend, above both SMAs. Flat returns could mean accumulation.",
    298, 308, None, 275, [283, 292], 1.5,
    "API at 289 with improving trend, above both SMAs. Returns are flat (0.35% 20d) but VR of 1.62 is the highest in this batch — 5-day volume significantly exceeds 20-day average. This divergence between flat price and rising volume can indicate accumulation: buyers are active but not yet pushing price. Position at 0.609 in 20d range has room to resistance at 298. pos60=0.733 is healthy. 52-week high at 335 provides upside room.",
    ["Flat returns despite high volume could also mean distribution, not accumulation", "December quiet season", "Resistance at 298-300 is close"],
    ["VR declining below 1.0 with no price advance", "Break below SMA20 at ~283"],
    "moderate", "partial"
)

ALL[("2025-12-04", "API")] = mk(
    "bullish", "watch_only", 45,
    "Confirmed uptrend label despite -1.71% 5d pullback. Above both SMAs, strong liquidity, VR=1.34. Pullback in uptrend.",
    298, 310, None, 272, [280, 290], 1.5,
    "API at 288 in confirmed uptrend — a stronger label than the improving trend on Dec 1. Above both SMAs with 3.23% 20d return. The -1.71% 5d pullback is concerning at face value but the uptrend label surviving that pullback suggests the broader structure is intact. VR 1.34 still shows elevated volume. Position at 0.565 in 20d range means it has pulled back to mid-range — reasonable entry zone if the uptrend thesis holds. Resistance at 298.",
    ["5d return negative — short-term momentum lost", "Could be start of larger correction", "API close to 20d support area"],
    ["Break below SMA50 at ~282", "Uptrend label degrading to mixed"],
    "moderate", "partial"
)

ALL[("2025-12-17", "API")] = mk(
    "bullish", "watch_only", 45,
    "Uptrend continues with positive returns across all timeframes. VR=0.87 is below 1 but 2.47% 5d shows recovery from the Dec 4 pullback.",
    300, 312, None, 278, [284, 293], 1.5,
    "API at 290, recovered from the Dec 4 pullback (288→290). Confirmed uptrend label persists. 5d return back to positive (2.47%), 20d return 3.02%. Above both SMAs. VR at 0.87 is the concern — declining from the 1.62 on Dec 1. The volume is fading even as price recovers, which could mean the recovery is on lower conviction. Still, the uptrend label and consistent above-SMA positioning justify a lean bullish.",
    ["VR declining (1.62→1.34→0.87) across the December API sequence", "Volume fading while price recovers is a bearish volume divergence"],
    ["VR dropping below 0.6", "Break below SMA50"],
    "moderate", "partial"
)

ALL[("2025-12-28", "AKPL")] = mk(
    "bullish", "watch_only", 42,
    "Improving, above both SMAs, 2% daily, VR=1.13. Extended in 20d range (0.991) but only mid-range in 60d.",
    258, 265, None, 238, [244, 252], 1.5,
    "AKPL at 248.9 after a 2.01% daily gain, at 0.991 in 20d range — nearly the top. Improving trend, above both SMAs. VR 1.13 is healthy. pos60=0.558 is mid-range, indicating the stock has room in the broader context. 52-week high at 335 means significant overhead room. The extreme 20d extension is concerning for immediate follow-through but the broader structure supports continuation. Acceptable liquidity.",
    ["At 0.991 in 20d range — could stall at resistance", "Only acceptable liquidity", "Improving not yet uptrend"],
    ["Negative daily close tomorrow giving back today's gain", "VR declining below 0.8"],
    "low_conviction", "partial"
)

ALL[("2025-12-29", "AKPL")] = mk(
    "bullish", "watch_only", 40,
    "Minor pullback (-0.76%) after hitting 20d range top. Still improving above both SMAs. Positive 5d (1.69%). Normal consolidation.",
    255, 265, None, 235, [242, 250], 1.5,
    "AKPL at 247 after a small pullback from 248.9 on Dec 28. Position dropped from 0.991 to 0.688 in 20d range — the pullback was actually a healthy correction from the extreme extension. Still above both SMAs with improving trend. 5d return positive (1.69%). VR 1.17 is healthy. This is normal consolidation after pushing to range resistance. pos60=0.498 — exactly mid-range in the broader context.",
    ["20d return compressing to 0.82% — modest momentum", "Mid-range positioning means no strong trend signal"],
    ["Negative 5d return", "Break below SMA20"],
    "low_conviction", "partial"
)

ALL[("2025-12-31", "AKPL")] = mk(
    "bullish", "watch_only", 42,
    "Flat close, VR rose to 1.3. Same structural read as Dec 29 but volume building. Above both SMAs, improving.",
    255, 265, None, 235, [242, 250], 1.5,
    "AKPL at 247 for the second consecutive session (flat). VR increased from 1.17 to 1.3 — volume rising on flat price is a mild accumulation signal, similar to MNBBL Sep 22 pattern. Improving trend, above both SMAs. pos60=0.498 is exactly mid-range. The stock is consolidating near 247 with rising volume participation. If history of the Sep MNBBL sequence applies, the volume build could lead to a follow-through move.",
    ["Flat close means no price follow-through yet", "Year-end thin trading", "Only acceptable liquidity"],
    ["VR declining below 0.8 without price advance", "Break below SMA20"],
    "low_conviction", "partial"
)


# ============================================================
# Write all 30 predictions
# ============================================================
written = 0
for (date, symbol), pred in sorted(ALL.items()):
    path = os.path.join(OUT, f"{date}__{symbol}__1D__prediction.json")
    with open(path, "w", encoding="utf-8") as f:
        json.dump(pred, f, indent=2)
    written += 1

print(f"Wrote {written} predictions to {OUT}")

dirs = [p["direction"] for p in ALL.values()]
acts = [p["action"] for p in ALL.values()]
convs = [p["conviction"] for p in ALL.values()]
print(f"Direction: bull={dirs.count('bullish')} bear={dirs.count('bearish')} neut={dirs.count('neutral')}")
print(f"Action:    buy={acts.count('buy')} watch={acts.count('watch_only')} avoid={acts.count('avoid')}")
print(f"Conviction: mean={sum(convs)/len(convs):.1f} min={min(convs)} max={max(convs)}")

# Sector breakdown
import json as jmod
with open("../agents/shared/BASKET4_SECTOR_RULE_STRESS_2026-03-30.json") as f:
    manifest = jmod.load(f)
sector_map = {}
for c in manifest["cases"]:
    sector_map[(c["session_date"], c["symbol"])] = c["sector"]

for sector in ["COMMERCIAL BANKS", "DEVELOPMENT BANKS", "HYDROPOWER"]:
    sector_preds = [(k, v) for k, v in ALL.items() if sector_map.get(k) == sector]
    if sector_preds:
        sd = [v["direction"] for _, v in sector_preds]
        sc = [v["conviction"] for _, v in sector_preds]
        print(f"\n{sector} ({len(sector_preds)}):")
        print(f"  dir: bull={sd.count('bullish')} bear={sd.count('bearish')} neut={sd.count('neutral')}")
        print(f"  conv: mean={sum(sc)/len(sc):.1f}")
