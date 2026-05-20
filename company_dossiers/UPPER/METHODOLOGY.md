# Single-Company Dossier — Methodology (Transferable Techniques)

**Scope**: rules of thumb earned from real cases, reusable across ANY future
event-case on ANY symbol. Not symbol-specific. Not predictive.
**Discipline**: every rule below is for *reading the past more honestly*, not
for predicting the future. None of these are signals.
**Framing**: per `DOSSIER_CONTRACT.md` §4 and §7 — observation only. The
moment any rule is repurposed into a "therefore buy/sell," it is out of scope.

This document captures the methods we will keep applying. The cases (§5 of the
contract) are *instances*; this file is the *technique library*.

---

## Rule 1 — The round-trip price-check (read forced flow vs smart flow)

**The technique.** When an *episodic* large broker (appears in few of the
trailing-20 days, but in big size when present) shows up on BOTH SIDES of a
stock within a short window (typically 1–3 weeks), check the prices they bought
vs the prices they sold at:

- **Sold higher than they bought** → consistent with informed distribution /
  smart-money exit. Worth noting; watch context.
- **Sold LOWER than they bought** → consistent with forced flow (stop-loss,
  client redemption, risk-mandated exit, program execution closing out, market-
  making book rebalance). **NOT a smart-distribution signal.**
- **Mixed / inconclusive** → say so; resist a story.

**Why it matters.** "Big volume + bearish top-5 concentration" is the
caricature of distribution. The same shape can be created by a forced exit at
a *loss* — which carries an entirely different meaning. Smart-money
distribution implies someone with conviction is leaving; forced flow implies
mechanical pressure that doesn't reflect a view. Treating them as the same
mis-reads the tape.

**When NOT to apply.** Anonymous broker IDs change between sessions for some
clearing systems; on NEPSE they appear stable, but verify the broker ID is the
same entity before chaining trades into a "round trip." If unverifiable, mark
the inference `[broker-identity unverified]`.

**Anti-pattern this avoids.** Adopting a confident "distribution detected"
read from concentration alone.

## Rule 2 — Persistence underneath the surface

**The technique.** For any flagged event day, list the brokers who held the
SAME net side (buy or sell) for ≥2 consecutive days *before* AND ≥2
consecutive days *after* the event. That is the *persistent layer* — flow
that is not random or event-driven.

- Persistent layer **net-buy-leaning** + a single-day sell-concentrated event
  = noisy distribution on top of quiet accumulation underneath.
- Persistent layer **net-sell-leaning** + a sell-concentrated event = the day
  is consistent with multi-week distribution. Worth more weight.
- Persistent layer **mixed** = the event is dominantly an episodic shock.

**Why it matters.** Day-level concentration is *what happened today*.
Persistence is *what is happening over weeks*. The two can disagree, and when
they disagree the persistent layer is the more meaningful frame for character
(though never for prediction).

**Concrete acceptance criterion.** A broker "persists across the event" only
if `before_days ≥ 2 AND after_days ≥ 2 AND same net side`. Don't lower the
threshold to manufacture a story.

**Anti-pattern this avoids.** Mistaking surface noise for underlying flow.

## Rule 3 — Verify the numbers separately from the narrative

**The technique.** When confronted with a confident reassessment / research
note / analyst write-up (even from a trusted reviewer), do TWO independent
checks:

1. **Structural claims** (leverage, PPA terms, cost overrun, regulatory
   status). Verify from primary or near-primary sources (rating agency,
   regulator, court, audited financials).
2. **Specific numbers in the narrative** (e.g. "−82.8% QoQ"). Re-derive them
   from the underlying disclosure. **Confident-sounding percentage changes
   are the #1 place specific numbers go wrong** — particularly cumulative
   vs standalone framings of YTD-reporting companies.

A document can be *directionally correct* on the structure and *specifically
wrong* on a headline number. Both must be checked separately.

**Why it matters.** Acting on an unverified specific number is the textbook
failure mode the discipline closed three other times.

**Concrete protocol.** For any number that drives a verdict:
- Locate the primary disclosure (date + URL).
- Re-derive the percentage / ratio from the raw figure yourself.
- If the disclosure uses cumulative YTD reporting, compute standalone-quarter
  values BEFORE comparing.

**Anti-pattern this avoids.** Adopting "−82.8%" as a fact when the underlying
disclosure was cumulative and the standalone story was different (in our case,
worse but in a different shape: standalone Q2 and Q3 were each losses, not a
% decline on a positive base).

## Rule 4 — Cross-source triangulation

**The technique.** Before treating any price/volume number as trusted, confirm
it on **two independent sources**. For NEPSE-listed stocks we have shown to
work in this lab:

- **Local OHLCV** (`sharesansar_datascrape/data/*.csv`) — our scraped daily
  data.
- **ShareSansar company page** (https://www.sharesansar.com/company/<SYMBOL>) —
  works without login, has Price History table back ~7+ years.

When both agree to two decimal places on Close / Volume / Turnover, the local
data is calibrated. When they disagree, mark and investigate before using.

**Why it matters.** A scraper bug, a corporate-action mid-series, or a
data-source quirk can quietly corrupt a long history. Triangulation is the
cheapest insurance.

**Anti-pattern this avoids.** Building a multi-year analysis on a series with
an undetected break.

## Rule 5 — Source hierarchy & gated sites

**Source ranking, top-down:**
1. **Primary** — company audited financials, rating agency reports (e.g.
   ICRA Nepal), regulator filings (SEBON), court filings, NEA published data.
2. **Secondary mirroring disclosure** — ShareSansar's republished
   announcements, NEPSE company-news archive, Merolagani filing mirrors.
3. **Secondary news** — reputable Nepali financial outlets (Kathmandu Post,
   myRepublica, Fiscal Nepal, Nepal Energy Forum).
4. **Tertiary** — blog posts, single-author analyses, social media. Use only
   for *leads*, never as the sole citation.

**Known site gates for this lab** (as of 2026-05-20):
- **nepsealpha.com — chart data is login-gated.** The page shell loads without
  auth; the data backend returns HTTP 403 to anonymous clients. UI shows
  "Invalid symbol" / null OHLC even for the default NEPSE index. Confirmed
  via JS console errors + visual screenshots in `charts/np_*.png`.
  Conclusion: not usable as an automated source. Login-based automation is
  out of bounds.
- **sharesansar.com — works clean without auth** for Company pages, Price
  History, News, AGM, Right Share History, Floorsheet listings. **Default
  Nepali secondary source for this dossier.**
- **CEIC — paywalled** and (for our use case) monthly-only on sector indices
  for the recent range, daily-only on a 2018 stub. Not useful here.
- **Direct NEPSE official API** (`api/nots/index/history`) — shallow
  (~20 days). Useful only for forward live values, not history.

**Anti-pattern this avoids.** Burning time scraping a gated source when a
clean source exists; or worse, attempting to circumvent a gate.

## Rule 6 — Mechanical case selection

**The rule.** Historical event cases (DOSSIER_CONTRACT §5) are chosen by a
**fixed external rule**, never by "an interesting day I remember." Valid
selection rules:

- **Volume threshold**: day's volume ≥ N× trailing-20-day median (we use 3-5×).
- **External flag**: a public table highlighted the day (e.g. ShareSansar's
  Price History sorted by turnover).
- **Calendar event**: every dividend / bonus / rights / AGM / quarterly result
  date — *every one*, not selected ones.
- **Structural break**: max single-day absolute price move on the chart
  within a defined window.

A day picked because "it looked interesting after I knew what happened next"
fails the rule. That is hindsight selection and it is forbidden.

**Anti-pattern this avoids.** Building a case library that confirms whatever
the author already believes.

## Rule 7 — Architecture: pull-and-structure beats eyeball-and-narrate

**The observation.** Today's most useful finding (the Apr 22 broker-100
round-trip) was MISSED by a careful visual chart description and FOUND by the
structured analyzer running over the broker fact table. The pulled-and-
structured view caught what the rendered chart did not.

**The rule.** For any flagged event, run the structured analyzer FIRST; only
then look at the chart for context. Eyeballing first plants narrative bias
before the data has spoken.

**Anti-pattern this avoids.** Confirming the chart's first impression with
the data, instead of letting the data correct the chart.

## Rule 15 — Two-measure decomposition (same-day move and post-event follow-through)

**The technique.** When measuring "follow-through" of a broker's lead-day
position, compute TWO INDEPENDENT measures, not one:

- **Same-day move:** `(event_day_close − prior_day_close) / prior_day_close × 100`,
  signed by the broker's net direction. This captures the price action
  *during* the broker's flow day. A large value here may reflect
  *reflexivity* (their flow moving the market) OR coincident-information
  (they and the market both react to the same intraday catalyst).
- **Post-event follow-through:** `(close_at_+5td − event_day_close) / event_day_close × 100`,
  signed by the broker's net direction. This captures what happens AFTER
  the broker's flow day. Continuation here is more consistent with
  predictive timing.

**These are independent measurements.** Do NOT describe them as
"X% of the total move happened same-day" — they don't share a
denominator. The right framing is: "On Naasa's lead days, same-day moved
+1.43% in their direction AND the next 5 trading days moved +2.86% in
their direction." Both signals exist; both are positive.

**Interpretation:**
- Same-day large, post-event small → likely reflexive / coincident-info.
- Same-day small, post-event large → likely predictive timing.
- Both large → both reflexive AND predictive (or coincident with persistent flow).

**Concrete on UPPER (2026-05-21, `stability_test.py`):**
- Naasa Securities (58): same-day +1.43%, post-event +2.86%. Both positive.
- Dynamic Money Managers (44): same-day −2.42%, post-event −6.02%. Both negative; post-event is larger ⇒ market continues to move against them after their flow day.
- Online Securities (49): same-day −0.35%, post-event +1.30%. Mixed (same-day weakly negative, post-event positive); supports the "unstable signature" classification.

**Anti-pattern this avoids.** Calling a single number "half same-day, half
following" when those are two separate measurements over different windows.
That conflates timing of price impact with size of price impact.

## Rule 14 (CANDIDATE, pending Romeo Review #6) — Stability across sub-periods

**The technique (proposed, not yet promoted).** Before promoting a broker
fingerprint from sparse to confirmed, check sign-consistency across
sub-periods of the broker-history window. **Minimum per-period n must be
≥ 5 lead days** before any per-period verdict is meaningful; smaller
samples are noise, not signal.

**Why this is still a candidate, not a rule:** the test I ran on 2026-05-21
(`stability_test.py`) had several per-third samples below n=5
(Naasa P3 n=2, DMM P3 n=3, Online P3 n=2). Verdicts driven by such thin
samples are noise-driven, not signal-driven, and I almost over-corrected
based on them. A rewritten version of this rule using leave-one-out or
rolling-window diagnostics with explicit minimum-n thresholds is the
right approach but has not been built and tested yet.

**Until promoted:** broker fingerprints carry the caveat *"stability not
proven across subperiods"* but are NOT downgraded on the basis of
sub-sample noise.

## Rule 13 — Sector-context check before claiming idiosyncrasy

**The technique.** Before treating any stock-level move or pattern as
*idiosyncratic to that stock*, compute its correlation with the relevant
sector sub-index over the same window. If correlation is high (e.g. r > 0.6),
a large share of the move was sector beta, not stock-specific.

**Concrete on UPPER (computed 2026-05-21, `sector_correlation_test.py`):**
- Full-window correlation UPPER daily ret vs hydropower sub-index: **r = 0.796 over 1,247 days.**
- 2024 rally (Jun 30 → Aug 27): UPPER +54%, hydro sector +32% → idiosyncratic spread +22%.
- Mar 2026 rally (Mar 1 → Mar 22): UPPER +29%, hydro sector +12% → idiosyncratic spread +16%.
- Apr 22 2026 broker-100 window: UPPER −7%, hydro sector −2% → idiosyncratic spread −5% (Case #1 is the *most* stock-specific event in our case library).
- Sep 2024 landslide window: UPPER −2%, hydro sector +11% → UPPER underperformed sector by ~13%.

**Implication for stock-level analysis:** stock-level findings explain the
idiosyncratic *spread*, not the headline move. Case-narrative weighting should
account for this: Case #1 has the most weight (~71% of its move was
idiosyncratic), Case #2 has less (~57%), Case #3 has even less (~41%).

**Anti-pattern this avoids.** Attributing a sector-wide rally to a stock-
specific catalyst. The 2024 UPPER rally narrative ("FY result positioning")
explains only the +22% spread; the +32% headline portion was the whole
hydropower sector.

**Known methodological gap (flagged, not yet patched):** Rule 11 broker
fingerprints currently compute follow-through against UPPER's *absolute*
price moves — which are 80% correlated with the sector. The fingerprints
therefore partially measure "broker was bullish during a sector rally" rather
than "broker had stock-specific insight." A refined Rule 11 would compute
follow-through against UPPER's *residual after sector-beta adjustment*. This
is the single biggest methodology hole in the current dossier; it has not
been tested, and its existence should temper confidence in all current
broker fingerprints until tested.

## Rule 12 — Cross-source corp-action awareness

**The technique.** Before cross-comparing price levels between two sources,
explicitly check whether each is corporate-action adjusted. Adjusted and
unadjusted series diverge massively across major events (rights, bonus,
splits) — sometimes by 50%+ for a single 1:1 right-share.

**Concrete on UPPER:**
- Local OHLCV (`sharesansar_datascrape/data/*.csv`): **NOT adjusted.** Shows pre-rights peak of Rs 766 (Feb 2022).
- Nepsealpha daily endpoint: **adjusted.** Shows post-rights-equivalent peak of Rs 504 (Apr 2021).

Both are correct in their own frame. They are NOT comparable on level. They
ARE comparable on percentage moves (mostly).

**Implication for dossier work:**
- Quote levels with the source named ("Rs 504 (adjusted, nepsealpha)" vs "Rs 766 (unadjusted, local OHLCV)").
- For multi-year structural analysis, prefer the adjusted source.
- For recent (<6 months) day-to-day reading where no corp action falls in the
  window, either source is fine.

**Anti-pattern this avoids.** Quoting a price level without naming the source,
then drawing structural conclusions about historic highs/lows that are
artifacts of an adjustment difference.

## Rule 11 — Broker fingerprinting via lead-day follow-through

**The technique.** For any symbol with ≥1 year of broker fact-table data,
compute per-broker:
1. **Lead days (n):** how many times that broker was the day's largest
   absolute net position.
2. **Avg exact-5-trading-day follow-through:** for each lead day, the price
   change exactly **5 trading days forward** (not calendar days) *in that
   broker's net direction*. Sum / count = the broker's signature value.

**Classification (revised 2026-05-20 post Romeo-review for sample-size honesty):**

| Signature value | Lead-day count n | Tag | Interpretation |
|---|---|---|---|
| > +1.0% | n ≥ 11 | INFORMED | Historically positive follow-through context in this sample |
| < −1.0% | n ≥ 11 | FORCED | Historically negative follow-through context in this sample |
| > +1.0% | n ≤ 10 | SPARSE_POSITIVE | Directionally positive but sample too thin to classify confidently |
| < −1.0% | n ≤ 10 | SPARSE_NEGATIVE | Directionally negative but sample too thin to classify confidently |
| ±1.0% | any | NOISE | No reliable follow-through in this sample |

**Use — strictly descriptive context.** Interpretive framing (Romeo Review #5
correction, 2026-05-21): describe Rule 11 outputs as
**"absolute UPPER follow-through context in this sample,"** NOT as
"stock-specific informed broker skill," until sector-residual follow-through
is computed (the gap flagged in Rule 13).

- In the daily read: "today's top buyer is Naasa Securities, which has
  historically positive follow-through context on UPPER in this sample
  (+2.86% avg over 21 lead days)."
- **Never as a signal to follow.** A historical fingerprint is a pattern in
  past data, not a prediction about the next event. Use of words like
  "reliable," "smart money," "stock-specific insight," or "follow them" is
  forbidden — the data does not support that strength of claim.
- Broker identities are stable on NEPSE in the medium term but corporate
  ownership/management of brokerages can change; not safe cross-symbol or
  cross-era.

**Concrete on UPPER (recomputed 2026-05-20 with exact-trading-day math; supersedes prior):**

| # | n | Avg | Tag |
|---|---:|---:|---|
| 58 (Naasa Securities) | 21 | +2.86% | INFORMED |
| 44 (Dynamic Money Managers) | 20 | −6.02% | FORCED |
| 49 (Online Securities) | 16 | +1.30% | INFORMED |
| 34 | 15 | −1.04% | FORCED (mild) |
| 48 | 11 | −1.05% | FORCED (mild) |
| 38 (Dipshikha Dhitopatra) | 9 | +2.79% | SPARSE_POSITIVE |
| 81 | 9 | +1.05% | SPARSE_POSITIVE |
| 88 (Blue Chip) | 8 | +1.61% | SPARSE_POSITIVE |
| 22 | 7 | +1.01% | SPARSE_POSITIVE |
| 26 (Asian Securities) | 7 | −1.17% | SPARSE_NEGATIVE |
| 42, 56, 45, 17, 35 | ≥7 | ±1.0% | NOISE |

**Caveats (binding):**
- N is small. Even at n=21, the signature is "context for this sample,"
  not a confirmed property of the broker.
- Path-dependence: one big day can dominate the average. The script does
  not yet check dispersion — that's a known gap.
- Survivorship: only brokers active in the broker-history window appear.
- Anonymous broker IDs may not be stable cross-symbol.

**Anti-pattern this avoids.** Treating every appearance of a "big broker" as
informed flow. Without the historical follow-through check, there is no
basis to distinguish informed from forced from noise. Equally avoided:
treating the historical signature as if it predicts the next event.

## Rule 10 — Grep the codebase before declaring a probe impossible

**The technique.** Before concluding "this can't be done" / "the site is gated"
/ "no working approach exists," **search the existing codebase for any
script that already does the thing.** A 30-second `Grep` against the repo
beats hours of reinventing — and beats wrong conclusions that go into the
record.

**Concrete checklist before any "this is impossible" verdict:**
- `Grep <site or feature name>` across the whole project tree.
- Look for `.ps1`, `.sh`, `.js`, `.py` wrappers as well as docs / READMEs.
- Read any `SOLUTION.md` / `KNOWN_GOTCHAS.md` / `RESOURCES.md` you find.
- Check for `.playwright-mcp`, `.cdp`, `chrome-automation` or similar
  artifacts indicating a working browser-automation flow.

**Why it matters.** Reinventing is expensive; declaring something impossible
when a working solution lives in the repo is *worse than expensive* — it
puts a false fact into the dossier. This rule exists because exactly that
happened on nepsealpha: I declared the site fully gated in three separate
write-ups before someone pointed at `refresh_upper_data.ps1` + `scripts/
refresh_nepse_symbol.js`, which had been quietly pulling 37,347 minute bars
of UPPER intraday data for weeks. The mistake wasn't the failed probe; it
was *not searching the codebase before writing up the conclusion*.

**Anti-pattern this avoids.** Confident "impossible" conclusions written into
the dossier when a working solution already exists nearby.

## Rule 9 — The absorption signature (added from Case #2, Mar 19 2026)

**The technique.** On a heavy-volume day where (a) top-5 buy concentration and
top-5 sell concentration are **approximately equal** (e.g. both 22–26%, neither
side singularly dominant) and (b) price moves **sharply in one direction**,
the side moving the price is *actively absorbing* the other side's flow.

- **Heavy vol + balanced concentration + sharp UP move** = buyers absorbing
  every share offered. Sellers are present and large, but the buyers are
  *taking everything they put up*. Descriptive: "active buyer absorption."
- **Heavy vol + balanced concentration + sharp DOWN move** = sellers absorbing
  every bid. Buyers are present, just being overwhelmed.

**Why it matters.** Without this lens, "balanced concentration" looks like
"nothing interesting — no side dominates." But when paired with a large
directional move, balanced concentration is the *most* informative footprint:
both sides showed up in size, and one side decisively won.

**Concrete on UPPER Mar 19 2026:** top-5 buy 22.7%, top-5 sell 24.6% — looks
balanced — but price closed +7.53% on the day's largest volume of the rally
(2.55M). Two large net sellers (broker 35 −95k, broker 88 −81k) AND two large
net buyers (broker 66 +66k, broker 49 +66k) collided. The buyers won.

**When NOT to apply.** On low-volume days, "balanced + small move" is just
noise. The signature requires *heavy volume + sharp move* together. Don't
read it into a quiet tape.

**Anti-pattern this avoids.** Calling a heavy-volume up-day "consolidation" or
"no clear winner" when in fact one side was demonstrably absorbing the other.

## Rule 8 — Mark [unverified] explicitly; never guess

**The rule.** When a fact is not located in a verifiable open source, mark it
`[unverified — needs <specific document>]`. Do not estimate. Do not infer
from memory. Do not write a plausible number with no source.

The known-unknown list IS the dossier value. A dossier full of confident
unverified numbers is worse than a dossier with an honest gap list — because
the former gets *used*, and the inaccuracy compounds.

**Anti-pattern this avoids.** Fabricating a clean-looking document.

---

## How to use this file

1. When starting a new case (§5 in the contract), open this file first.
2. Apply the relevant rules. Reference them by number in the case's findings.
3. If a case produces a new transferable technique, **add it here** with the
   same shape (the technique / why / when not / anti-pattern). The
   methodology grows from real cases, not from theory.
4. Never tune a rule based on whether it would have given a profitable signal.
   These are reading rules, not trading rules. The discipline is the asset.

## CHANGELOG

- 2026-05-20 — v0. Rules 1-8 distilled from the Apr 22 2026 UPPER event case
  (CASE_2026-04-22_volume_anomaly.md), the broader UPPER §2 sourcing pass,
  and the nepsealpha probe. Eight rules; future cases will extend.
- 2026-05-20 — v0.1. Added Rule 9 ("absorption signature") derived from the
  March 2026 rally case (CASE_2026-03-10_rally.md, specifically the Mar 19
  +7.53% / 2.55M-vol battle day with balanced top-5 concentration). First
  example of the methodology growing from a real case, as designed.
- 2026-05-20 — v0.2. Added Rule 10 ("grep before declaring impossible")
  after I wrongly declared nepsealpha fully gated three times before
  discovering `refresh_upper_data.ps1` + `scripts/refresh_nepse_symbol.js`
  already in the repo, working perfectly via CDP-attach + fsk-token sniff +
  iframe-context fetch. Meta-lesson: the canonical-source-first discipline
  applies to the codebase itself, not just data.
- 2026-05-20 — v0.3. Promoted Rules 11 and 12 from the deep 5-year analysis
  (`DEEP_FINDINGS_2026-05-20.md`). Rule 11 (broker fingerprinting via
  lead-day follow-through) earned its place by producing clean signal-vs-
  forced signatures on UPPER (broker 58 +3.58% INFORMED; broker 44 −7.05%
  FORCED). Rule 12 (cross-source corp-action awareness) earned its place
  from the local-vs-nepsealpha level divergence (Rs 766 unadj vs Rs 504 adj).
- 2026-05-21 — v0.5 (self-validation pass; minimal patch after user caught
  over-correction risk). Promoted Rule 13 (sector-context check) — earned
  from the r=0.796 UPPER-vs-hydro-sub-index finding (`sector_correlation_test.py`).
  Recorded two CANDIDATE rules NOT yet promoted (need Romeo Review #5):
  Rule 14 candidate (stability requirement before promoting tags) — held
  back because per-third n's in `stability_test.py` were too small (n=2-3
  in some thirds) to draw confident verdicts from; Rule 15 candidate
  (same-day vs following-days decomposition) — held back as a candidate
  not yet earned. Naasa #58 received a reflexivity note in COMPANY_CONTEXT
  (the ~50%-same-day finding is real and worth flagging). NO downgrades
  applied to Online Securities #49 or Dynamic Money Managers #44, because
  the per-third samples driving those verdicts were too thin (P3 n=2-3).
  Major methodological gap flagged: Rule 11 broker fingerprints likely have
  market-beta contamination (UPPER r=0.80 with hydro sector); proper test
  requires sector-residual follow-through, not yet done. Two case files
  (Cases #2 and #3) received brief sector-context addenda; Case #1 NOT
  modified (the "Apr 7 sharp drop" wording cannot be checked without
  intraday data which was not in this pass).
- 2026-05-20 — v0.4 (Romeo review #4 patches). THREE corrections:
  (a) Rule 11 forward-window math fixed from "calendar +10 days, take last"
      to **exact +5 trading days** in the sorted trading-date list, matching
      the prose claim. Recomputed all fingerprints; magnitudes shifted
      modestly downward (broker 58 +3.58% → +2.86%; broker 44 −7.05% → −6.02%);
      rank-order of top signatures unchanged. Several prior "mildly forced"
      tags reclassified to NOISE post-fix.
  (b) Added SPARSE_POSITIVE / SPARSE_NEGATIVE tags for n ≤ 10 — fixes the
      inconsistency where broker 38 was tagged INFORMED at n=9 despite the
      methodology stating n ≤ 10 is too thin to classify confidently.
  (c) Softened the prose throughout: "reliable informed-side actor" →
      "historically positive follow-through context in this sample"; "signal"
      → "context"; "validated cleanly" → "supported descriptively in this
      single case." The tags themselves are kept; the surrounding language
      no longer drifts toward trading-signal territory.
