# UPPER Dossier — Self-Validation Pass · 2026-05-21

> **⚠️ READING ORDER (post Romeo Review #6, same day):** the canonical
> Rule-11 fingerprint state as of end of 2026-05-21 is in the **Romeo
> Review #6 section near the bottom of this document** and in
> `METHODOLOGY.md` v0.6. **Earlier sections of this document describe the
> pre-#6 state and may contain wording explicitly superseded** (the
> "~50% same-day, ~50% following-days" framing was rejected; the
> "+0.70% AGM" wording was corrected to "−0.70%"; the "INFORMED/FORCED"
> tags are retired in favour of soft bands). Read top-to-bottom for the
> audit trail, but **only the Review #6 section is operative**.

---


After the deep findings of 2026-05-20 (broker fingerprints + Aug 2024 catalyst + named brokers), I asked: **which of my own most-confident claims have NOT been challenged with falsifiable tests?** That produced four specific tests, all of which I could run alone against the existing data. This document records what survived and what didn't.

Discipline note: this self-validation is the same shape Romeo's external reviews take — apply "what would prove this wrong?" to my own outputs. The intent is to catch overclaims before they harden into the dossier's load-bearing assumptions. Same anti-self-deception spine as METHODOLOGY Rule 10 ("grep before declaring impossible") — applied recursively to my own confident outputs.

---

## Test #1 — Broker fingerprint stability + reflexivity

**Question:** are the Rule-11 broker fingerprints (Naasa Securities INFORMED, Dynamic Money Managers FORCED, etc.) stable across sub-periods, or are they masking variance?

**Method:** split the 343-day broker-history window into three equal thirds (P1 2023-06→2025-02, P2 2025-03→2025-11, P3 2025-11→2026-05). Recompute each broker's exact-5-trading-day forward follow-through separately in each third. Also separated same-day move (potentially reflexive) from following-days move (more predictive-leaning).

**Script:** `stability_test.py`

**Results:**

| Broker | Full avg | P1 avg | P2 avg | P3 avg | Verdict |
|---|---:|---:|---:|---:|---|
| **58 Naasa Securities** | +2.86% (n=21) | +3.61% (n=12) | +0.79% (n=7) | +5.59% (n=2) | **STABLE-POS ✅** |
| **44 Dynamic Money Managers** | −6.02% (n=20) | −7.62% (n=15) | −4.21% (n=2) | **+0.80% (n=3)** | **STABLE-NEG (era-bounded)** ⚠️ |
| **49 Online Securities** | +1.30% (n=16) | +3.07% (n=8) | **−0.20% (n=6)** | **−1.24% (n=2)** | **❌ UNSTABLE — flips sign** |
| 42 Sani Securities | −0.19% (n=22) | −2.14% | +2.17% | +0.69% | UNSTABLE (was NOISE anyway) |
| Others | — | thin per third | thin | thin | INSUFFICIENT_DATA |

**Two-measure finding (Naasa specifically) — CORRECTED per Romeo Review #5:**

The original wording said "half of the +2.86% accrues same-day, half over the next 5 days." **That was mathematically misstated.** The two measures are *independent*, not a decomposition of a shared total:

| Measure | What it computes | Value |
|---|---|---:|
| Same-day move | `(event_day_close − prior_day_close) / prior_day_close × 100`, in Naasa's direction | **+1.43%** |
| Post-event +5td move | `(close_at_+5td − event_day_close) / event_day_close × 100`, in Naasa's direction | **+2.86%** |

**Correct framing:** on Naasa's lead days, the same-day moved +1.43% in their direction **AND** the next 5 trading days moved +2.86% in their direction. **Both signals exist independently, both are positive.** The "+1.43% same-day" might be partly reflexive (their flow moving the market) or coincident-information; the "+2.86% post-event" is the continuation that persists after their flow. The same-day data cannot distinguish reflexive from coincident-info; the post-event data cannot distinguish predictive from sector-correlated.

This is the new METHODOLOGY Rule 15 in action: separate same-day from post-event when measuring follow-through, don't conflate.

**Patches earned from Test #1:**
- Online Securities (#49): **DOWNGRADE from INFORMED to UNSTABLE**.
- Dynamic Money Managers (#44): **add "primarily 2023-2024 era" caveat**; recent behavior is closer to noise.
- Naasa Securities (#58): **add "~50% same-day, ~50% following-days" character note**.
- **New METHODOLOGY Rule 14 candidate:** stability requirement — before promoting a tag from sparse to confirmed, check sign-consistency across thirds.
- **New METHODOLOGY Rule 15 candidate:** decomposition — separate same-day move from following-days move when computing follow-through.

## Test #2 — UPPER vs hydro sub-index correlation

**Question:** are UPPER's moves idiosyncratic (broker-driven, stock-specific) or is UPPER a beta vehicle for hydro sector flow?

**Method:** compute Pearson correlation between UPPER daily returns (nepsealpha adjusted) and hydropower sub-index daily returns (lab frozen data) over the full common window and key event windows.

**Script:** `sector_correlation_test.py`

**Results:**

**Full-window correlation: r = 0.796 over 1,247 days.** Very strong sector beta.

| Window | n | corr | UPPER | Hydro | **Idiosyncratic spread** |
|---|---:|---:|---:|---:|---:|
| **2024 rally (Jun 30 → Aug 27)** | 39 | +0.77 | **+54.2%** | **+31.9%** | **+22.3%** |
| **Mar 2026 rally (Mar 1 → Mar 22)** | 11 | +0.80 | **+28.7%** | **+12.4%** | **+16.3%** |
| Sep 2024 landslide window | 56 | +0.84 | −1.8% | +11.4% | **−13.2%** |
| Apr 2026 (broker-100 window) | 21 | +0.87 | −6.7% | −2.0% | **−4.7%** |
| **Full 2024** | 232 | +0.76 | −1.6% | +41.4% | −42.9% |
| Full 2025 | 225 | +0.78 | −13.8% | −1.0% | −12.7% |

**Major implication: ~60-70% of UPPER's headline moves on rally days are sector beta, not stock-specific.**

| Case | UPPER move | Sector portion | Idiosyncratic portion (what stock-level analysis explains) |
|---|---:|---:|---:|
| Case #3 (Aug 2024) | +54% | ~+32% | **only +22%** |
| Case #2 (Mar 2026) | +28% | ~+12% | **only +16%** |
| Case #1 (Apr 22 2026) | −7% | ~−2% | **−5%** ← most idiosyncratic |

**Patches earned from Test #2:**
- **Case #1 (Apr 22) is the most stock-specific event in our case library.** Its narrative explains the biggest idiosyncratic share.
- **Case #2 narrative needs sector addendum** — the +28% headline was mostly sector; the broker work explains the +16% spread.
- **Case #3 narrative needs sector addendum** — the +54% headline was mostly sector; the FY-result-rally interpretation explains the +22% spread. **Case #3's evidence weight drops further.**
- **Sept 2024 landslide context corrected:** UPPER did NOT simply "drift while already unwinding" — it underperformed the sector by 13% during the disaster window. The landslide had a real relative cost.
- **New METHODOLOGY Rule 13 candidate:** sector-context check — any stock-level finding deserves a sector-index correlation check before being treated as idiosyncratic.
- **Broker fingerprints partially capture sector beta, not pure stock-picking.** A refined Rule 11 would use UPPER's residual-after-sector-beta. Recorded as a future improvement, not patched today.

## Test #3 — AGM-announcement reaction pattern ✅ FIXED & RERUN (Romeo Review #5)

**Bugs found and fixed:**
1. **Pre-data event contamination** — original code mapped events pre-2019-01-13 to the first available trading day, producing 4 bogus identical rows. **FIXED:** pre-data events now filtered out.
2. **Same-date duplicates** — e.g. multiple announcements on the same day double-counted. **FIXED:** events on the same date now deduped.
3. **Sign error in my first writeup** — I'd typed +0.70% for 2026-04-06 +1d; script output is **−0.70%**. **CORRECTED.**

**Rerun result (12 valid deduped events):**

| Horizon | n | mean | % positive |
|---|---:|---:|---:|
| +1 trading day | 12 | −0.22% | 33% (4/12) |
| +5 trading days | 12 | −2.11% | 25% (3/12) |
| **+10 trading days** | **12** | **−4.39%** | **8% (1/12)** |

After the bug fix, **the pattern is actually STRONGER than my first reporting**: 11 of 12 AGM-post-events are negative at +10 days. Mean is −4.39%; range is wide (−14.8% to +2.5%) and dominated by some outliers, but the directional pattern (11/12 negative) is real and consistent. The 2026-04-06 AGM (Case #1's anchor) fits: +1d −0.70%, +5d +1.88%, +10d −1.41%.

**On Case #1's "Apr 7 sharp drop" wording:** the close-to-close was a small −0.70%, not the "sharp drop" framing the case used. But Case #1 may describe the **intraday low**, which this test doesn't measure. Without intraday verification the Case #1 sub-claim is left as-is — that's an intraday-data follow-up, not a wording rewrite from close-to-close numbers.

### Historical (superseded) content of Test #3 below

The earlier "INVALID — pending script fix" framing has been resolved by the bug-fix rerun above. Original problem statement retained for audit.

---

**Original status before fix:** Aggregate results unreliable. Romeo correctly identified the two bugs above.

**Status: aggregate results unreliable.** Romeo correctly identified two bugs in `agm_rhythm_test.py`:

1. **Pre-data event contamination:** `agm_rhythm_test.py:48` maps any event before the price data start (2019-01-13) to the first available trading day. So the 2015, 2016, 2017, 2018 AGM events all get measured starting from 2019-01-13 — producing 4 bogus identical rows that contaminate the aggregate stats.
2. **No deduplication of related notices.** Events like "AGM announced" + "AGM date set" + "minutes published" can all be tagged AGM-related for the same actual AGM; they get triple-counted.
3. **Sign mismatch:** the script output for 2026-04-06 shows −0.70% at +1d but I originally wrote +0.70% in the first version of this doc (now corrected above).

**Until the script is fixed** (filter pre-data events, dedupe related notices, verify sign handling) and rerun, the aggregate statistics below should be treated as **unreliable** and the "weak negative drift at +10d" conclusion is **not earned**.

The Case #1 "Apr 7 sharp drop" wording is NOT corrected on the basis of this test — the test's close-to-close measure says −0.70%, but Case #1 may describe an intraday low; only intraday data can confirm or deny that.

**Question:** Case #1 implicitly hypothesised an "AGM rhythm" (post-announcement drop). Does every AGM announcement on UPPER produce that pattern?

**Method:** find all AGM-related events in UPPER's history (n=17 raw, n=13 with valid trading-day data since data starts 2019-01). Compute +1d, +3d, +5d, +10d, +20d price moves around each.

**Script:** `agm_rhythm_test.py`

**Results:**

| Horizon | n valid | Mean | % positive | Range |
|---|---:|---:|---:|---:|
| +1 trading day | 13 | ~0% | mixed | −4.3% to +2.6% |
| +5 trading days | 13 | weakly negative | 38% | −9.8% to +3.1% |
| +10 trading days | 13 | **clearly negative** | **23% (3/13 positive)** | −14.8% to +2.5% |
| +20 trading days | 13 | negative | low | −19.98% to +2.47% |

**The 2026-04-06 AGM (Case #1's anchor) specifically — SIGN CORRECTED per Romeo Review #5:** +1d was actually **−0.70%** (I had written +0.70% in error — the test output shows minus), +3d +1.64%, +5d +1.88%, +10d −1.41%. So there *was* a small close-to-close drop on Apr 7 (not "sharp" but not the "+0.70% bounce" I had reported). Case #1's "sharp drop to 199" framing still cannot be verified at intraday resolution from this test (close-to-close was −0.70%, but Case #1 may be describing intraday low). **The Case #1 wording correction should wait for an intraday verification pass.**

**Patches earned from Test #3:**
- **Case #1 wording correction:** "Apr 7 sharp drop to 199" was overstated. Close-to-close on Apr 7 (the +1 trading day) was +0.70%, not a sharp drop. There was an intraday dip but it closed up. The +10d picture is weakly negative (consistent with the overall AGM-history pattern).
- **The AGM rhythm IS supported but weakly** — 10 of 13 events negative at +10d, but range is wide and 5d is only 38% positive. It's a tendency, not a rule. Worth noting as descriptive context but not as a pattern to act on.

## Test #4 — Closing-hour signature generalization

**Question:** Apr 22 had 48% of volume in the final hour and was framed as a "forced-flow" event. Does this signature generalize across all UPPER trading days with intraday data?

**Method:** for all 570 days with intraday minute bars, compute opening-hour share (11:00 NPT) and closing-hour share (14:00 NPT). Classify days as HIGH-OPENING, HIGH-CLOSING, or BALANCED. Compare same-day returns and +5d forward returns.

**Script:** `closing_hour_test.py`

**Results:**

| Group | n days | Mean same-day | % positive same-day | Mean +5d fwd | % positive +5d |
|---|---:|---:|---:|---:|---:|
| HIGH-OPENING (≥40% 11:00) | 37 | +0.67% | 51% | +0.47% | 43% |
| **HIGH-CLOSING (≥40% 14:00)** | **200** | **−0.36%** | **30%** | +0.11% | 39% |
| BALANCED | 333 | +0.20% | 45% | +0.19% | 43% |

**Key findings:**
- **200 of 570 days (35%) hit the ≥40% closing-hour threshold.** Apr 22's 48% was *common*, not exceptional. NEPSE has a structural closing-bias.
- **HIGH-CLOSING days ARE weakly down same-day** (mean −0.36%, only 30% positive) — real but mild closing-hour-selling bias.
- **But +5d forward is essentially flat across all groups** — the "closing-hour forced flow → reversal afterwards" interpretation does NOT hold up at population scale.
- Top-10 individual high-closing days look noisy (Mar 9 2026 was +9.96% on 95% closing-hour share; same group has multiple negative days). No clean signature.

**Patches earned from Test #4:**
- **DROP the "closing-hour signature" candidate rule** from Case #1. It doesn't generalize. Apr 22's reading was reasonable as descriptive context for that single day but not as a transferable methodology.
- The opening-hour ≥50% extreme (Mar 10, Mar 19, Mar 11 — the Case #2 rally launch days) is rare and lightly positive same-day, but +5d is mixed. **Opening-hour signature also weakened** — it's a *describer* of "this was a positioning event" but not a tradeable pattern.
- **Case #1 retains its multi-evidence convergence** (round-trip price-check + persistent layer + concentration) without the closing-hour add-on.

---

## Net what changed in the dossier after 4 self-tests

**Confidence INCREASED on:**
- Naasa Securities (#58) INFORMED tag — survived stability test across three thirds.
- Case #1 (Apr 22) as the strongest case — confirmed most idiosyncratic by sector test.

**Confidence DECREASED on:**
- Dynamic Money Managers (#44) — still FORCED on average but era-bounded; recent (P3) data shows the pattern weakening.
- Naasa's interpretation — ~50% reflexive component means "INFORMED" overstates the predictive share.
- Online Securities (#49) — DOWNGRADED from INFORMED to UNSTABLE.
- Case #2 and Case #3 narratives — both events were mostly sector flow; the idiosyncratic story explains a minority of the move.
- The "closing-hour signature" — DROPPED as a candidate rule.
- The "Apr 7 sharp drop" framing in Case #1 — corrected to the actual +0.70%.

**New methodology candidates earned (Rules 13, 14, 15):** sector-context check; stability requirement before promoting tags; same-day-vs-following decomposition.

**The pattern across all four tests:** when I apply "what would prove this wrong?" to my own confident outputs, **about half my claims survive and about half get demoted or qualified.** That ratio is consistent with the Romeo review track record (he's caught patches in every review). The lesson: confident outputs need to be self-challenged before they harden, and the testing infrastructure (`stability_test.py`, `sector_correlation_test.py`, etc.) should be re-run any time we add new data or events.

## ⚠️ Honest revision after over-correction check (user caught this)

Before applying patches the user paused me with: *"don't overdo to make this claim wrong or right. Maybe you missed the biggest piece."* That was the right pause. Re-examining my own four tests under their own discipline:

**Test #1 (stability)** — per-third n's are too small to draw confident verdicts. Naasa P3 n=2, DMM P3 n=3, Online P3 n=2. The "Online → UNSTABLE" verdict rests on n=2 in one third; the "DMM era-bounded" rests on n=3. These are noise-driven verdicts pretending to be signal-driven. **Decision: do NOT downgrade Online #49 or add era-bound caveat to DMM #44.**

**Test #2 (sector correlation)** — r=0.796 is robust (large n). The interpretation "broker work only explains the spread" is overclaim — broker fingerprints work on UPPER's actual moves, which is what a discretionary UPPER trader cares about. The cases' weight notes ARE worth adding. **Decision: add Rule 13 (sector-context check) and brief addenda to Cases #2 and #3; that's robust enough.**

**Test #3 (AGM rhythm)** — 13 events, wide dispersion (range −15% to +3% at +10d), driven by a few outliers. Weak evidence at best. The "Apr 7 sharp drop overstated" correction may itself be wrong: Case #1 might be describing intraday low, my test measured close-to-close. **Decision: do NOT modify Case #1's Apr 7 wording without intraday verification.**

**Test #4 (closing-hour signature)** — I tested it as standalone; Case #1 used it as one piece of multi-evidence convergence. Different claim. **Decision: do NOT drop the candidate. Already a candidate not a rule.**

### Rule candidates NOT promoted (need external review #5)
- Rule 14 candidate (stability requirement before tag promotion) — methodology direction is right but per-third n's in my own test were too small to make this binding.
- Rule 15 candidate (same-day vs following decomposition) — directionally interesting but earned from one round; needs corroboration.

### THE BIGGEST PIECE I missed in my own tests

None of my four tests address **market-beta contamination of Rule 11 broker fingerprints.** UPPER has r=0.80 with hydro sector. So when Naasa is bullish during a sector rally, the +2.86% follow-through is partly "the sector kept moving" — not necessarily "Naasa was informed." A proper test computes follow-through against UPPER's **residual after sector-beta adjustment**, not absolute moves. **I have not done this. None of the four tests above do it.**

If sector-beta contamination is large, Naasa's "INFORMED" tag is overstated — it's measuring "Naasa was active during up days in a generally up sector" rather than stock-specific skill. This is the kind of methodological hole that, if confirmed, would mean **the whole Rule-11 fingerprint set is partially measuring sector beta**, not broker skill. It would be a bigger correction than any patch I was about to apply.

**Current dossier status under this honest reckoning:**
- Naasa Securities #58 INFORMED — survives stability (the robust part), but the interpretation has a sector-beta-contamination caveat that hasn't been tested.
- Dynamic Money Managers #44 FORCED — survives, with the same contamination caveat.
- All other broker fingerprints — same caveat applies.
- Rule 13 (sector-context check) — confidently promoted; clean general lesson.
- Rules 14 and 15 — candidates pending external review.
- Cases #1, #2, #3 — sector addenda added to #2 and #3; #1 left as-is until intraday wording check.

## Romeo Review #5 — three additional correctness fixes applied 2026-05-21 (later same day)

After the minimal-patch commit, Romeo Review #5 caught three specific
correctness issues:

1. **Naasa reflexivity wording was mathematically misstated.** The +2.86% is the
   post-event move (event close → +5td); the +1.43% is the same-day move
   (prior close → event close). They are independent measurements over
   different windows, NOT a 50/50 decomposition. **PATCHED in COMPANY_CONTEXT
   broker watchlist; this is the actual finding promoted to Rule 15.**
2. **AGM test had script bugs** (pre-data event contamination + same-date
   duplicates + sign error in my writeup). **PATCHED `agm_rhythm_test.py`;
   rerun shows the AGM pattern is actually stronger than my first reporting
   (11/12 negative at +10d).**
3. **"Idiosyncratic spread" overstates what the arithmetic computes.** It's
   a raw cumulative-return difference, not a beta-adjusted residual. **PATCHED
   case files to use "spread versus hydro" with explicit math caveat.**

**Other Romeo #5 decisions:**
- Rule 11 interpretation **RENAMED** to "absolute UPPER follow-through context"
  (not "stock-specific informed broker skill") until residual follow-through
  is computed.
- Rule 15 **PROMOTED** (with corrected math language).
- Rule 14 stays CANDIDATE with explicit min-per-period n≥5 requirement.
- Lighter caveat **ADDED** to all broker tags: "stability not proven across subperiods."
- Did NOT downgrade Online #49 or era-bound DMM #44 (sub-sample n too thin).

## What got patched in the original 2026-05-21 minimal set

| Originally planned | Actually applied | Why minimal |
|---|---|---|
| Downgrade Online #49 → UNSTABLE | **NO** | n=2 in P3, noise |
| Era-bound caveat on DMM #44 | **NO** | n=3 in P3, noise |
| Naasa same-day reflexivity note | **YES (small)** | n=21, robust |
| Add Rule 13 sector-context | **YES** | r=0.80, robust |
| Add Rules 14, 15 | **NO — candidates** | Earned from one round, need Romeo #5 |
| Apr 7 sharp drop correction in Case #1 | **NO** | Need intraday verification first |
| Sector addendum on Case #2 | **YES (brief)** | r=0.80 finding is robust |
| Sector addendum on Case #3 | **YES (brief)** | r=0.80 finding is robust |
| Drop closing-hour candidate | **NO** | Was already a candidate, not promoted |
| Memory file overhaul | **NO (keep current)** | Most of the planned softening dissolved |

Single biggest output of this session: **the sector-beta-contamination methodology gap is now explicitly named in METHODOLOGY Rule 13** as "the single biggest methodology hole in the current dossier; it has not been tested, and its existence should temper confidence in all current broker fingerprints until tested." That's the honest landing.

This document is the canonical record. See git log for the minimal-patch commit.

---

## ⭐ ROMEO REVIEW #6 SECTION (2026-05-21, later same day) — CANONICAL

After the minimal-patch section above, I ran `sector_residual_test.py` to actually close the sector-beta-contamination gap that Rule 13 had flagged. Romeo Review #6 caught three correctness issues in the first version, plus a P2 cleanup. **All four are applied here. This section supersedes everything above for broker-fingerprint tags.**

### What Romeo #6 caught and was applied

1. **Compounding inconsistency (P1)** — absolute return was compounded across +5 trading days, but residual was summed. Now both compounded.
2. **Threshold fragility (P1)** — hard "STOCK-SPECIFIC ≥70%" vs "NOISE ≤1%" categories were too rigid. Replaced with soft bands per Romeo's scheme: ≥+1.5% residual-positive, +1.0% to +1.5% near-threshold-pos, |x|<1.0% noise, mirrors negative.
3. **Hydro-index self-inclusion (P1)** — UPPER is a constituent of the NEPSE hydropower sub-index, so the hydro-residual is not fully independent. Added explicit caveat AND a sensitivity check against the broader NEPSE-index.
4. **Stale wording (P2)** — flagged at the top of this doc; Reading-Order banner added.

### The residual numbers (final, dual-benchmark)

Regression: UPPER vs hydro sub-index (n=666, 2023-06-11 → 2026-05-18), **β = 1.002, α = −0.099%/day**. UPPER vs NEPSE-index, **β = 1.279, α = −0.096%/day**. UPPER moves essentially 1:1 with hydro and 1.28:1 with NEPSE.

| # | Firm | n | Absolute | Hydro-adj | NEPSE-adj | Combined verdict |
|---|---|---:|---:|---:|---:|---|
| **49** | **Online Securities** | 16 | +1.30% | +1.05% (near-thr-pos) | **+1.90% (residual-pos)** | **Most robust signal; strengthens under NEPSE** |
| **58** | **Naasa Securities** | 21 | +2.86% | +1.23% (near-thr-pos) | +1.12% (near-thr-pos) | **Most stable; consistent near-threshold-pos in both** |
| 44 | Dynamic Money Managers | 20 | −6.02% | −1.35% (near-thr-neg) | −0.60% (noise) | Weak negative; ~80% of absolute was hydro beta |
| 26 | Asian Securities | 7 | −1.17% | +0.07% (noise) | **−1.55% (residual-neg)** | Surprise NEPSE emergence; benchmark-sensitive; n thin |
| 34 | (unresolved) | 15 | −1.04% | +1.06% (sign-flip) | +0.62% (noise) | Sign-flip + noise = low-confidence (Romeo: probably noise) |
| 38 | Dipshikha Dhitopatra | 9 | +2.79% | −0.11% (noise) | −0.09% (noise) | **RETIRED from positive context** (Romeo #6 direct call) |
| 88 | Blue Chip Securities | 8 | +1.61% | +0.86% (noise) | +1.04% (near-thr-pos) | Borderline; benchmark-sensitive |
| 42, 48, 45, 17, 35, 81, 22, 56, 28 | various | various | various | noise/near-noise | noise/near-noise | Not currently classifiable |

### Net broker watchlist as of 2026-05-21 evening (Romeo #6 final)

- **Online Securities (#49)** — single most robust positive context on UPPER. Survives both benchmarks; strengthens to residual-positive (+1.90%) under NEPSE adjustment. Caveat: n=16, "stability not proven across subperiods."
- **Naasa Securities (#58)** — most stable positive context. Near-threshold-pos in both benchmarks. Caveat: half of the absolute +2.86% was hydro beta.
- **Dynamic Money Managers (#44)** — weak negative context, weakening to noise under broader benchmark. The "FORCED −6%" label is retired; reality is much milder.
- **Asian Securities (#26)** — benchmark-dependent; under NEPSE-adjustment, surprise residual-negative. n=7 thin.
- **Dipshikha (#38)** — RETIRED. Was hydro beta.

### What Romeo #6 ultimately said

Final: ACCEPT-WITH-MOD. The residual test is directionally right; broker fingerprints are real but milder after sector adjustment. Keep broker fingerprinting (option b), but with soft framing: hydro-adjusted mild positive/negative context, absolute-only context, noise. Drop INFORMED/FORCED from the daily surface. All four patches applied.

### The next external check

If we want a sixth+ pass: have someone document UPPER's actual weight in the NEPSE hydropower sub-index (NEPSE publishes index methodology). That single fact would either confirm or refute the "hydro residual is partially circular" caveat. Until then, NEPSE-adjusted is the cleaner column.

This document is now canonical through Romeo Review #6.
