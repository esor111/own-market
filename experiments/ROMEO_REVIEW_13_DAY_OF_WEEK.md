# Romeo Review — Day-of-Week Regime Report

> Review of Benvolio's external file:
> `C:\Users\ishwor\Music\own-organize\market-expirement-labs\13_day_of_week_regime_replication_plan.md`
>
> Written 2026-04-12 so Juliet can patch canon without re-running the whole audit.

---

## Verdict

Use the report's **main conclusion**, but do **not** merge it into canon unchanged.

What survives:

- The old lab wording was too confident.
- The published NEPSE weekday literature is **mixed**, not cleanly validated.
- The April 2026 Mon-Fri schedule change makes old Sun-Thu findings less directly tradeable.
- The best framing is **calibration / characterization**, not "signal validation."

What must be patched first:

1. KC & Joshi's Thursday evidence is overstated in the report.
2. Maharjan and Pant are still secondary-source rows, not fully verified primary-source rows.
3. The 2022 Sun-Fri -> Sun-Thu reversion can be dated more tightly than the report currently says.

---

## The Three Corrections

### 1. KC & Joshi (2005): Thursday is negative, but not at t=-2.81

The report says KC & Joshi found Thursday negative with `t=-2.81`.

That is the wrong number for the day-of-week result.

From the MPRA full text:

- Full-sample Thursday-vs-Sunday coefficient: `-0.1248%`
- Full-sample t-statistic: `-1.87`
- Significance: 10% level

The `-2.81` number belongs to a different result, not the full-sample Thursday day-of-week coefficient.

**Correct takeaway:** KC & Joshi still support a negative Thursday effect, but the evidence is weaker than Benvolio's current writeup implies.

### 2. Maharjan and Pant should be labeled as secondary-source evidence

The report currently says the table is verified from the original paper or best accessible text.

That is too strong for:

- Pant (2010)
- Maharjan (2013)

Those rows are still based on secondary citations, thesis references, or inaccessible sources.

**Correct takeaway:** Their directional contradiction is still useful, but it should not be written as equally grounded to:

- KC & Joshi (2005)
- Shrestha & Kayastha (2024)
- Madai, Sharma & Dangol (2026)

### 3. The 2022 schedule reversion should be tightened

The report says the Sun-Fri regime lasted until `~Sep 2022` and still needs verification.

We now have a sharper public source:

- ShareSansar, September 4, 2022: Friday trading would stop from **Ashoj**, with the remaining Fridays of **Bhadra** still trading

So the cleaner wording is:

- Sun-Fri from **June 15, 2022 through late Bhadra 2079**
- Sun-Thu from **Ashoj 2079 onward**

If a stricter NEPSE circular is found later, use that, but the schedule note should no longer read as fully unresolved.

---

## Canonical Reading After Patch

The honest canonical position should now be:

**The day-of-week effect is the most-studied NEPSE calendar anomaly, but the published findings are inconsistent across papers and schedule regimes, so it should be treated as a characterization / calibration lane, not a validated signal.**

That is the sentence I would want the lab to stand behind.

---

## Exact Patch Language For Juliet

### 1. Patch for `10_unconventional_synthesis.md`

Replace the current weekday bullet with:

> **Day-of-week effect is the most-studied NEPSE calendar anomaly, not the most-validated one.** KC & Joshi (2005) found Thursday negative in the Sun-Thu regime; Madai et al. (2026) found Sunday/Monday weak and Wednesday strongest; Shrestha & Kayastha (2024) found no meaningful weekday difference through VaR/ES risk measures. Practitioner tallies like Investopaper and ShareSansar are useful summaries, not independent academic confirmation. Status: inconsistent across papers, worth replicating, not canonically validated.

### 2. Patch for `13_retail_psychology_signals.md`

Replace the TL;DR sentence:

Current:

> The strongest finding is the **Sun/Thu day-of-week effect** which is published and replicated.

Use:

> The most-studied Nepal-specific anomaly is the **day-of-week effect**, but the literature is mixed rather than cleanly replicated.

Replace the section header and status block:

Current:

> ### 5. Sun/Thu Day-of-Week Effect — PUBLISHED
> **Most empirically grounded signal in this wave.**

Use:

> ### 5. Day-of-Week Effect — Most-Studied, Not Yet Settled
> **Best read as a mixed literature cluster, not a validated signal.**

Replace the synthesis/status wording with:

> **Synthesis:** The weekday literature points to a real possibility of schedule-linked return asymmetry in NEPSE, but the sign and strongest day are not stable across papers. Thursday is negative in KC & Joshi (2005), positive in Maharjan (2013, secondary-source only), Wednesday is strongest in Madai et al. (2026), and Shrestha & Kayastha (2024) find no meaningful weekday effect through VaR/ES. The right next step is replication on our own data, not stronger prose.
>
> **Schedule complication:** Nepal has switched between Sun-Thu, brief Sun-Fri, and Mon-Fri regimes. Any analysis must treat these as separate regimes.
>
> **Status:** Worth replicating as a calibration / regime-characterization exercise. Not validated enough for a canonical learning or trading rule.

### 3. Patch for `README.md`

Replace the weekday bullet with:

> **Day-of-week effect** is the most-studied NEPSE calendar anomaly, but published findings are inconsistent across papers and all historical work is from older trading-week regimes. Treat as a replication / calibration lane, not a validated signal.

### 4. Optional patch for `SIDE_QUEST_MAP.md`

Replace the current description:

> Re-run the weekday anomaly question using the corrected schedule regimes and our local data.

With:

> Characterize weekday patterns across NEPSE schedule regimes using our local data; primary value is pipeline calibration and regime-change analysis, not signal hunting.

---

## Suggested Patch To Benvolio's Report

If Juliet wants to preserve Benvolio's external report but tighten it, the minimum changes are:

- Change KC & Joshi row from `t=-2.81` to the full-sample Thursday-vs-Sunday result `-0.1248%, t=-1.87`
- Change "Every entry is verified from the original paper or the best accessible text" to wording that explicitly separates:
  - primary-source rows
  - secondary-source rows
- Change the 2022 schedule note from `~Sep 2022` plus "needs verification" to:
  - `June 15, 2022 through late Bhadra 2079`
  - `Ashoj 2079 onward`

---

## Bottom Line

Benvolio's main insight is right:

- the weekday lane is **mixed**
- our docs are **too strong**
- the next value is in **replication**

After patching the three issues above, the report is good enough to guide canonical wording.
