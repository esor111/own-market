# Effective-N / Correlation Analysis — v2 candidate (93 symbols)

**Written:** 2026-04-19
**Window:** 2023-01-01 to 2026-04-17 daily closes → log returns
**Source:** `sharesansar_datascrape/data/` daily CSVs
**Method:** Pearson correlation on log returns, effective N = n^2 / sum(|corr|)

## Per-sector effective N

| Sector | Naive N | Effective N | Effective / Naive | Mean \|corr\| | Top pair |
|---|---:|---:|---:|---:|---|
| COMMERCIAL_BANK | 16 | 1.58 | 0.10 | 0.61 | KBL-PRVU (0.86) |
| DEV_BANK | 8 | 1.88 | 0.24 | 0.46 | JBBL-KSBBL (0.71) |
| FINANCE | 8 | 1.35 | 0.17 | 0.70 | ICFC-MFIL (0.82) |
| HOTEL | 4 | 1.50 | 0.38 | 0.55 | OHL-SHL (0.65) |
| HYDROPOWER | 25 | 2.05 | 0.08 | 0.47 | HDHPC-NHPC (0.82) |
| INFRA_INVEST | 2 | 1.10 | 0.55 | 0.82 | HIDCL-NIFRA (0.82) |
| INVESTMENT | 1 | 1.00 | 1.00 | n/a | n/a |
| LIFE_INSURANCE | 5 | 1.75 | 0.35 | 0.46 | NLIC-NLICL (0.72) |
| MANUFACTURING | 4 | 2.30 | 0.58 | 0.25 | HDL-SHIVM (0.53) |
| MICROFINANCE | 12 | 1.94 | 0.16 | 0.47 | NICLBSL-RSDC (0.66) |
| NON_LIFE_INSURANCE | 6 | 1.96 | 0.33 | 0.41 | IGI-NICL (0.65) |
| TELECOM | 1 | 1.00 | 1.00 | n/a | n/a |
| TRADING | 1 | 1.00 | 1.00 | n/a | n/a |

**Aggregate:** naive N = 93, effective N across all sectors ≈ 20.4 (ratio 0.22)

## Market-wide (all 93 symbols jointly)

- Rows of common data: 996
- Mean |off-diagonal correlation|: 0.376
- Effective N: **2.6** (vs naive 93)
- Effective / Naive ratio: 0.03

## What this means for Gate 1 sizing

Gate 1 thresholds (e.g. N≥80 for reversal-specialist, N≥80 for dividend-micro) assume statistical independence. The measured ratios show NEPSE is nowhere near independent.

### Two separate effective-N numbers, two different uses

- **Sector-pooled experiments** (each sector analyzed independently): sum of per-sector effective N ≈ **20.4**. This applies to experiments like the v2 corporate-action event study where you want to know "how many independent bets do I have across sectors."
- **Market-wide experiments** (all symbols pooled into one analysis): joint effective N ≈ **2.6**. NEPSE as a whole trades on roughly 2–3 macro risk factors. This number applies ONLY when the whole universe is pooled as one bag of symbols. It does NOT mean all 93-symbol experiments have 2.6 useful observations — for sector-aware or stock-specific event studies, the sector-pooled figure (~20.4) or the trigger-specific effective N is the correct denominator.

**Note on scope vs the current persistence-shadow v1 policy:** the current persistence-shadow v1 policy runs only on the active_shadow symbols {NABIL, EBL, SANIMA}; its independence gate is governed by the existing effective-independent-episodes check in the playbook (unique report dates contributing wins, ≥5 required; top-3 date share ≤ 30%), not by the 93-symbol sector-pooled effective-N numbers in this memo. The effective-N figures here apply to any **future v2-universe** experiment that pools events across the expanded symbol set; they do not retroactively re-score the forward persistence-shadow evidence.

### What the per-sector ratios actually tell us

- **Commercial banks:** 16 symbols → 1.58 effective (ratio 0.10). Mean |corr| = 0.61. They essentially move as one asset. Doubling the commercial-bank count barely adds any statistical power.
- **Hydropower:** 25 symbols → 2.05 effective (ratio 0.08). Heterogeneous by watershed and season, but market-wide moves dominate the correlation.
- **Microfinance:** 12 symbols → 1.94 (ratio 0.16). NRB policy-driven cluster.
- **Manufacturing:** 4 symbols → 2.30 (ratio 0.58). Highest ratio — the only sector where naive N and effective N are close. Mean |corr| = 0.25.

### Practical consequence for reversal-specialist v2

Reversal-specialist closed at N=66 (gate ≥80). A universe-v2 re-run using naive event counts might look like: 93/26 × 66 ≈ 236 events. But the correlation-adjusted version:

- Market-wide-shock Layer B cuts already remove co-moving events (per L-016). Those cuts will bite even harder on v2 because commercial banks and microfinance cluster tightly.
- Sector-pooled adjustment: 66 × (20.4/5.7) ≈ 236 naive → 66 × (effective-ratio) ≈ 50-ish effective events under pessimistic assumptions, up to ~130 under optimistic.
- Under pessimistic effective-ratio assumption: v2 reversal-specialist does NOT clear 80 effective events. Gate 1 fails for the same structural reason as v1.

**Takeaway:** universe expansion alone does NOT solve the sample-size problem for signals that depend on idiosyncratic per-symbol events. What would solve it: longer time windows, cross-sector pooling with explicit correlation adjustment, or abandoning sector-clustered triggers in favor of stock-specific event definitions.

### Implication for any v2-based pre-registration

- Any pre-registration that inherits the N≥80 Gate 1 threshold from v1 must justify it against effective N, not naive N
- If effective-N is the true denominator, Gate 1 thresholds either tighten (to 80 effective) or the gate remains the same (80 naive) with the understanding that passing Gate 1 does not mean 80 independent events
- An honest v2 pre-registration should compute pre-expected effective N for the planned trigger definition BEFORE the Gate 1 event-detection runs, and state the effective-N assumption up front

### Three tiers of independence (added 2026-04-19 reviewer follow-up)

Effective N is not a single axis. At least three distinct tiers of independence must be reported before any v2 experiment can claim Gate 1 sample adequacy:

| Tier | Axis | Diagnostic | When it matters |
|---|---|---|---|
| 1 | **Market-wide** | Joint effective N across the whole universe (this memo: 2.6) | Experiments pooling the whole universe as one bag |
| 2 | **Sector** | Per-sector effective N, sector-pooled sum (this memo: 20.4) | Experiments pooling events within a sector (e.g., bank-sector event study) |
| 3 | **Within-trigger / per-symbol** | For stock-specific events: unique trigger dates, top-1 date share, top-3 date share | Stock-specific event studies where events cluster by date (L-007 persistence, reversal-specialist, dividend-micro) |

Tier 3 is orthogonal to Tiers 1 and 2. Even a stock-specific event signal can have clustering: L-007 persistence resolved 11 cases but only ~3 independent episodes because triggers clustered by date. Reversal-specialist's Gate 1 already requires top-3 date share ≤ 30% — that rule generalizes to all stock-specific event studies on v2.

**Rule for v2 pre-registrations:** for stock-specific triggers, always report unique trigger dates and top-1 / top-3 date share alongside naive N. For sector-pooled triggers, report Tier 2. For market-wide triggers, report Tier 1. Ambiguous cases default to the most conservative (smallest) denominator.

## Method notes and caveats

- Effective N formula: `N^2 / sum(|correlation_matrix|)`. This is one of several valid formulations. Bai-Ng and Kaiser-Guttman give similar qualitative answers.
- Common-dates alignment drops any date where ANY symbol is missing. Symbols with short history (< 250 return observations in window) were excluded from the matrix before alignment.
- Absolute correlation is used (Pearson). Tail/extreme co-movement would need copula analysis, not done here.
- This is a diagnostic memo, not a pre-registration. It does not authorize any experiment decision by itself.

### Tail-correlation caveat (added 2026-04-19 reviewer follow-up)

Pearson |corr| is computed across all daily returns in the window, which means it is dominated by the body of the distribution — typical-day behavior. On extreme days (sharp-down shocks, regime breaks, large liquidity events), NEPSE correlations cluster toward 1 much more tightly than the Pearson number suggests. This is the exact regime where signals like reversal-specialist and shock-event studies actually fire.

**Practical consequence:** the effective N numbers in this memo are upper bounds for shock/reversal-style tests. Real tail effective N is plausibly 1–2 for market-wide tests and materially lower per-sector on extreme days. Future pre-registrations for extreme-event studies should assume worse effective N than the diagnostic numbers here, and should state this assumption up front.

No copula study is authorized by this memo. The caveat is a qualitative ceiling, not a re-measurement. When (if ever) a future reversal-specialist v2 or similar extreme-event experiment pre-registers, it should bake the tail-dependence ceiling into its Gate 1 threshold explicitly.

---

## Romeo Interpretation (added 2026-04-19)

Romeo reviewed this memo and locked the following interpretation of the findings:

**Frame**
- Universe v2 is still useful as **infrastructure and coverage expansion**.
- Universe v2 does NOT by itself solve the sample-size constraints.
- Naive N and independent evidence are different things.
- Rows are cheap; independent evidence is rare.

**Canonical takeaway**
> Universe expansion increases coverage and optionality, but independent evidence grows much more slowly than row count. Future v2 experiments must pre-register effective-N assumptions before H1.

**Required reporting for any future v2 pre-registration.** Every pre-registration that uses the v2 symbol universe (or any extension thereof) must report, BEFORE H1 runs:

1. Naive event count (raw count of trigger events)
2. Unique event dates
3. Sector distribution of events (AND of contributing symbols)
4. Expected effective N / correlation adjustment, with the method used (e.g. trace-based, Bai-Ng, block-diagonal per-sector)
5. Whether the test is market-wide, sector-pooled, or stock-specific
6. **Signal classification (added by reviewer follow-up, pre-registered BEFORE Gate 1):** one of `idiosyncratic` (stock-specific), `sector-common` (event that concentrates within one sector), or `market-common` (event that moves many sectors together). This classification determines which effective-N denominator is the valid one. Doing the classification AFTER seeing the event distribution creates post-hoc denominator selection. Ambiguous cases default to the most conservative (smallest) denominator.
7. For stock-specific / idiosyncratic triggers: unique trigger dates, top-1 date share, top-3 date share (Tier 3 within-trigger independence diagnostic) — this determines which effective-N figure is the valid denominator

**Rule for the universe v2 freeze package.** Added as an explicit rule to be honored by all v2 experiments:

> No v2 experiment may claim Gate 1 sample adequacy from naive N alone. Gate 1 thresholds must be stated against the effective-N denominator appropriate to the test type (market-wide / sector-pooled / stock-specific), with the method used disclosed.

**What this memo does and does not do**
- This memo IS diagnostic infrastructure: a reusable baseline for effective-N / correlation reasoning across the v2 universe.
- This memo does NOT authorize any experiment.
- This memo does NOT modify `universe_v2_candidate.csv`.
- This memo does NOT authorize a rerun of reversal-specialist, dividend-micro, or any other prior Gate-1-failed experiment.

Any future v2 experiment requires its own pre-registration, which must honor the reporting and gate rules above. Those pre-registrations go through the normal Romeo review cycle.