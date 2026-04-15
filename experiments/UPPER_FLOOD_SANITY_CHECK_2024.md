# UPPER Flood Sanity Check — Sep 2024

> Written 2026-04-12.
> Purpose: first-pass reality check on the monsoon-flood hydropower idea using local price data only.

## Question

Does the cleanest named flood-damage case in the lab, **UPPER after the September 2024 flood**, show visible underperformance versus undamaged hydropower names?

If yes, the flood-damage lane survives first contact with data.
If no, the lane should probably be killed before a bigger build.

## Event Frame

- **Event used for sanity check:** first credible public report naming damage at Upper Tamakoshi
- **Source/date:** OnlineKhabar, September 29, 2024
- **Why this date:** the report explicitly says the landslide damaged structures in the headworks area and that electricity production had been halted from Friday 7 pm

This is a better sanity-check anchor than a generic flood warning because the market-relevant thing is not "it rained a lot." It is "this listed company's revenue-generating asset has been damaged and taken offline."

## Data and Method

- **Price source:** local archive in `sharesansar_datascrape/data`
- **Window checked:** September 2024 through December 2024
- **Target stock:** `UPPER`
- **Control basket:** `SMHL`, `HIDCL`, `NGPL`, `API`, `AKPL`
- **Deduping rule:** collapse consecutive archive rows with identical `Close`, `Prev. Close`, and `Vol` to remove non-trading-day snapshot repeats
- **Control construction:** equal-weight normalized basket rebased to 100 at the event date

Important note:
I did **not** use a raw average of stock prices, because that would let high-price names dominate the basket mechanically. The control basket here is the cleaner equal-weight normalized version.

## What Happened

### 1. Immediate reaction from the pre-event close was real, but not uniquely huge

Using **2024-09-26** as the pre-event close:

| Date | UPPER | Control basket | Relative |
|---|---:|---:|---:|
| 2024-09-29 | -3.41% | -1.31% | **-2.10 pp** |
| 2024-09-30 | -2.93% | +0.26% | **-3.19 pp** |
| 2024-10-01 | +4.83% | +6.72% | -1.89 pp |
| 2024-10-07 | +7.80% | +7.71% | +0.09 pp |
| 2024-10-17 | +10.73% | +11.56% | -0.83 pp |

Interpretation:

- UPPER **did** underperform on the first reaction day or two.
- But the gap was not cleanly persistent in the first 5-10 trading sessions.
- By early October, the initial underperformance had mostly washed out.

### 2. Medium-horizon drift shows up later

Using **2024-09-29** as the event-day base:

| Date | UPPER | Control basket | Relative |
|---|---:|---:|---:|
| 2024-10-01 | +8.54% | +8.18% | +0.36 pp |
| 2024-10-07 | +11.62% | +9.24% | +2.38 pp |
| 2024-10-17 | +14.65% | +13.13% | +1.52 pp |
| 2024-11-05 | +10.61% | +12.97% | -2.36 pp |
| 2024-11-19 | +9.29% | +20.34% | **-11.05 pp** |
| 2024-12-31 | +1.67% | +9.07% | **-7.40 pp** |

Interpretation:

- In the first 1-10 trading days after the named damage report, UPPER does **not** look like a slam-dunk short-window loser.
- The more interesting effect is a **later lag**.
- By mid-November and year-end, UPPER is clearly behind the rest of the hydro basket.

## Verdict

**The monsoon-flood hydropower lane survives the sanity check, but in a narrower form than the strongest version of the thesis.**

What this result supports:

- A damage-confirmed hydro event can matter.
- UPPER was weaker than peers after the flood over the broader post-event window.
- There is enough signal here to justify continuing to a proper event table.

What this result does **not** support:

- A clean, immediate `[0, +10]` underperformance rule as already proven.
- A claim that the market instantly and cleanly repriced UPPER's damage in the first few sessions.
- A claim that basin-level flood exposure alone is enough.

## Best Reading of the Result

The honest read is:

1. **Market-wide disaster shock hit everyone first.**
   The whole hydro basket sold off around the event.

2. **UPPER-specific damage was not cleanly separable in the first few sessions.**
   That makes the short-window event-study version harder than it first sounds.

3. **But UPPER did lag later.**
   That is consistent with a slower realization process: outage duration, repair difficulty, and winter-generation implications becoming more concrete over time.

## What This Means for the Side Quest

This should **not** be killed.

But it should be reframed as:

- **Primary frame:** confirmed-damage hydropower event study
- **Not:** generic monsoon flood study
- **Not:** pure watershed-exposure diff-in-diff
- **Not:** already-validated 10-day trading signal

## Recommended Next Move

Proceed to the real build, but keep the discipline tight:

1. Build a **damage-confirmation event table** for 2021-2026.
2. For each event, use the **first credible named report** for the specific listed hydro.
3. Test multiple windows, not just `[0, +10]`.
   Include `[0, +5]`, `[0, +10]`, `[0, +20]`, and a slower drift window.
4. Prefer **damaged vs undamaged listed hydros** over basin-only treatment definitions.

## Bottom Line

The sanity check does **not** give us a ready-to-trade signal.

It does give us something important:

**the flood-damage idea is real enough to keep, but not clean enough to overclaim.**

That is exactly the kind of result a good sanity check is supposed to produce.
