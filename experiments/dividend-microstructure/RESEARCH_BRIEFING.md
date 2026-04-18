# Research Briefing — Dividend / Book-Closure Microstructure Signal

> Produced 2026-04-17 by a research agent for the dividend-microstructure sandbox.
> This is the literature + methodology foundation for the signal build. Do not modify without Romeo review.
> Full briefing archived as-written, with one citation correction flagged inline.

---

## Citation Correction Upfront

The original research pass referred to "Choy & Wei" for the short-selling/ex-dividend paper. The correct attribution is **Blau, Fuller & Van Ness (2011), "Short Selling around Dividend Announcements and Ex-Dividend Days"**, published in the Journal of Corporate Finance. The Ole Miss PDF the lab held was from Van Ness's faculty page. This is now documented; any lab reference to "Choy & Wei" in the dividend context should be corrected.

Also corrected: the "Dhaoui SSRN paper" referenced earlier. The actual paper is **Ducret, Eugster, Isakov & Weisskopf (2025)**, "The Behavior of Stock Prices Around the Ex-day During a Dividend Shortage" — the attribution "Dhaoui" appears to have been a transcription error in prior lab notes.

---

## 1. Literature Summary

The ex-dividend literature splits into four clusters.

### Foundational — tax clientele
**Elton & Gruber (1970); Elton, Gruber & Blake (2003).** Across April 1966–March 1967 dividends, the ex-day price drop averaged **77.7% of the dividend**, not 100%. The residual 22.3% gap is read as evidence that marginal holders are taxed differently on dividends vs capital gains.

- [Marginal Stockholder Tax Effects and Ex-Dividend Day Behavior — Thirty-Two Years Later (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=363620)
- [Stern working paper PDF](http://people.stern.nyu.edu/mgruber/working%20papers/tax_effects.pdf)

### Dividend capture / short-term arbitrage
**Lakonishok & Vermaelen (1986); Blau, Fuller & Van Ness (2011).** Positive abnormal returns before the ex-day, negative abnormal returns after — classic run-up / run-down signature. Blau et al. document abnormally low short-selling before the ex-day and abnormally high short-selling on and just after, concentrated in high-yield names. **The negative relation between current short selling and future returns is stronger around the ex-dividend day than during non-event days**, strengthened further by dividend size.

- [SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1138382)
- [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0929119910000866)
- [Ole Miss working PDF](http://faculty.bus.olemiss.edu/rvanness/Working%20Papers/ShortDividend.pdf)

### Shortage amplification
**Ducret, Eugster, Isakov & Weisskopf (2025, SSRN).** 2018-2022 European sample, 14,844 dividend payments, 17 countries. **High-yield firms show +2.4% cumulative abnormal return in the [T-5, T-1] window during the COVID dividend shortage vs low-yield controls.** The ex-day abnormal return gap between low- and high-yield stocks rose from 0.6% (pre-COVID) to 0.8% (during shortage). Amplified further in countries with temporary short-selling bans.

- [SSRN abstract](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5101091)
- Earlier "Chasing Dividends during COVID-19" [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3716174)

### South Asian / emerging market evidence
- **Pakistan (PSX, 2001-2020, 500 ex-days, 41-day window):** positive abnormal returns before the ex-day, negative after; headline ARR of 4.9%, t=12.96. Explicitly attributed to dividend-capture arbitrage. [ResearchGate](https://www.researchgate.net/publication/357274029_The_ex-dividend_day_stock_price_behavior_Evidence_from_Pakistan) | [IBA Business Review](https://ir.iba.edu.pk/cgi/viewcontent.cgi?article=1311&context=businessreview)

- **India (NIFTY, 2011-2015):** AAR statistically significant on 31-day window; pre-announcement AAR ≈ +0.094, post-announcement ≈ −0.096. Consistent run-up / run-down shape. [ResearchGate](https://www.researchgate.net/publication/308277131_EFFECT_OF_EX-DIVIDEND_DATE_ON_STOCK_RETURNS_OF_NIFTY_STOCKS_IN_INDIA)

- **Jamaica (tax-free emerging market; Robinson & Glean):** even without tax heterogeneity, ex-day price drop remains below dividend and abnormal returns persist — pointing at **liquidity**, not tax, as a driver in frontier markets. [SSRN](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2887305)

- **Nepal (Joshi, NRB Economic Review; IJIRT 158229):** both exist but could not extract the PDFs cleanly during the research pass. Both would need to be read in hand before next phase. [NRB paper](https://www.nrb.org.np/red/vol24-1_art5/) | [IJIRT paper](https://ijirt.org/publishedpaper/IJIRT158229_PAPER.pdf)

### BJZZ and its decay
**BJZZ (2021); Ardia, Aymard & Cenesizoglu (2025).** BJZZ found ~10 bps/week spread between high- and low-retail-imbalance stocks. Ardia et al. replicated on 2016-2021 data and showed **the signal no longer predicts weekly returns on large caps** and the long-short strategy is no longer profitable. Decay is real.

- [Tracking Retail Investor Activity (JoF 2021)](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13033)
- [Revisiting BJZZ (Springer 2025)](https://link.springer.com/article/10.1007/s11408-025-00487-4)
- [arXiv preprint](https://arxiv.org/abs/2403.17095)

---

## 2. Best-Supported Mechanism For NEPSE

Four candidates ranked for NEPSE applicability:

| Mechanism | Fit to NEPSE | Why |
|---|---|---|
| Tax clientele (Elton-Gruber) | **Weak** | Nepal's dividend tax is 5% flat withholding, effectively zero capital gains for most retail. Tax wedge is shallow and uniform. Jamaica evidence suggests tax is weak in frontier markets. |
| Dividend capture / arbitrage (Lakonishok-Vermaelen; PSX) | **Strong** | Pakistan 4.9% ARR with t=12.96 is structurally closest to NEPSE (heavy retail, thin institutional, limited derivatives, book-closure mechanism). |
| Shortage amplification (Ducret et al.) | **Strong** | AGM/Companies Act Section 76 window (L-010) compresses most NEPSE dividends into Mangsir-Poush. Capture flows chase a temporary-but-constrained supply. |
| Liquidity / inventory (Robinson-Glean) | **Moderate** | Small market with broker inventory frictions. Secondary modifier. |

**Composite prediction:** dividend capture drives pre-ex run-up → post-ex price drops by approximately dividend amount plus unwind of capture-driven overshoot → shortage/clustering amplifies during AGM season. Tax clientele is second-order.

---

## 3. Proposed Primary Hypothesis For NEPSE

**H1 (falsifiable, pre-registered in `PRE_REGISTRATION.md`):**

> For NEPSE-listed banks and hydropower firms that announce a cash dividend, the excess return (event minus per-symbol trailing 120-day baseline) in the **[T+1, T+5]** window after the **book-closure date** is statistically negative at p < 0.01, with a directionally negative hit rate ≥ 60% after baseline adjustment.

**Why this hypothesis, not another:**
- Uses the **ex-book-closure date**, not the notice date. L-001 already validated the notice; academic literature centers on the ex-date. They are separate events on NEPSE.
- [T+1, T+5] is the cleanest "post-run-down" window from international literature (PSX, Blau-Fuller-Van Ness).
- Baseline adjustment is non-negotiable per L-003.

**Secondary hypotheses — test only if H1 survives:**
- **H2:** post-ex drift magnitude scales with dividend yield (top tercile ~2× bottom).
- **H3:** broker net flow in [T-5, T-1] predicts post-ex drift cross-sectionally (negative slope).
- **H4:** effect concentrates in banks (per L-001), not hydros.

**Do NOT test:** bonus shares, rights issues, interim vs final dividends.

---

## 4. Methodology

**Event definition.**
- Event = first official book-closure date for a cash dividend, from ShareSansar feed (Experiment 01 existing scraper).
- Drop events whose [T-10, T+10] window overlaps any other event (AGM notice, rights, bonus, earnings, policy-rate change). **This is the L-001 overlap fix promoted to preprocessing rule.**
- Pre-register full event list before computing any return.

**Baseline.** Per-symbol trailing 120 daily observations, matched to same window type. Minimum 30 observations. L-001 / L-003 convention.

**Windows.**
- Primary: `post_1_5` (pre-registered).
- Diagnostic (report, do not promote): `pre_-5_-1`, `post_1_10`, `post_6_10`.

**Controls.**
- Sector fixed effect.
- Market regime (above/below SMA-200).
- Size bucket (terciles).

**Success criterion (pre-registered):**
Both must hold:
1. Post_1_5 baseline-adjusted hit rate ≥ 60% with N ≥ 80.
2. Mean excess return t-stat ≤ −2.5 (two-sided p ≤ 0.013).

**Failure criterion (pre-registered):**
Kill the lane if hit rate < 55% OR |t| < 2.0.

---

## 5. Confounds + Overclaim Risks

Adversarial checklist:

1. **L-001 overlap.** If most book-closure dates fall within 10 days of book-closure notices, the signal is not independent. L-001 showed 90% of book-closures arrive within 12 days of AGM notice. **Gate 1: must compute notice→date gap distribution and overlap count before study.**

2. **AGM / bonus / rights clustering.** NEPSE corporate actions cluster heavily. Mandatory no-overlap preprocessing.

3. **Survivorship.** Only dividend-paying companies in sample. Explicitly frame as "dividend-paying banks and hydros 2021-2026."

4. **Bear-market contamination.** 95% of 2021-2026 data is below SMA-200 (L-001). Report effect size relative to same-sector market drift.

5. **Announcement vs ex-date.** Lab has conflated these in prior drafts. Document exact field, exact ShareSansar page.

6. **Multiple testing.** Only primary hypothesis on primary window gets promotion decision. All else diagnostic or not reported.

7. **L-012 clustering trap.** If 80+ events cluster on 3-5 book-closure dates, effective N is much smaller. Report unique-date count alongside N.

8. **Dividend yield endogeneity.** H2 must be framed as "association with yield," not "high-yield causes drift."

9. **No short-selling on NEPSE.** Blau-Fuller-Van Ness mechanism needs shorts to fade post-ex overshoot. NEPSE lacks this. **Expect smaller, slower drift** than Pakistan's 4.9%.

10. **Re-verify "71% bank hit rate at p=0.004" headline.** Lab had one scare already (L-013). Double-check underlying number before citing.

---

## 6. NEPSE-Specific Considerations

- **No short-selling.** Mechanism asymmetric. Pre-ex run-up may be stronger (no shorts fade it), post-ex drift slower to unwind. Expected outcome: single-digit drift, not Pakistan's 4.9%.

- **Book-closure ≠ US ex-dividend.** NEPSE book closure is a multi-day period; eligible holders are those on books at start of closure. "Ex-date" = first book-closure trading day. Use first book-closure date as anchor.

- **Mon-Fri regime (April 2026+).** Any event study spanning April 10, 2026 must use the regime-aware calendar module (`nepse_trading_calendar.py`). Trading-day offsets per actual calendar, not calendar days (L-007).

- **Thin dividend clienteles.** Tax-clientele weak. Effect driven by capture/liquidity.

- **Retail-dominant flow with broker-identified trades.** Structural lab edge. H3 broker-flow test only possible because of this. Where NEPSE research can uniquely extend international literature.

- **Bonus shares distinct.** Mechanically dilute, not pay cash. Exclude from H1.

- **Cash dividend tax:** 5% flat withholding; no capital gains for most retail. Tax wedge favors dividend income over capital gains — **opposite** of US setup. If tax-clientele mattered, it would push drop *above* dividend amount, not below.

- **AGM Section 76 window.** Dividends cluster Mangsir-Poush. Creates shortage-amplification conditions structurally every year — also creates independent-observation problems.

---

## 7. Recommended Next Action — The Smallest Useful Experiment

**"Ex-Book-Closure Drift" — gated, multi-step build:**

### Step 1 (2-3 days): Event table + Gate 1 check

Using existing L-001 event table, isolate cash-dividend book-closure **dates** (distinct from notice). Produce:
- List with: symbol, sector, book-closure date, dividend %, yield, overlap flag
- Apply overlap-fix preprocessing
- Report count of unique calendar dates vs total N

**Gate 1: PAUSE if unique-date count < 20 OR post-overlap N < 50.** Don't run the study on insufficient effective sample; either do more scraping or kill the lane.

### Step 2 (2 days): Pre-register H1

Commit `PRE_REGISTRATION.md` file to git **before** any return is computed. Lock in:
- H1 exact statement
- Success criterion (≥60% hit, t≤−2.5)
- Failure criterion (<55% hit OR |t|<2.0)

### Step 3 (1 day): Run H1 test

Use `experiments/shared/event_study.py`. Report results with unique-date count alongside N.

### Decision point

- **H1 passes:** proceed to H3 (broker-flow cross-section).
- **H1 directionally correct but weak (55-60%, weak t):** document as "directionally supportive of L-001, not independent." Do not build further.
- **H1 fails:** kill the lane. Focus forward-evidence budget on persistence shadow (L-012).

### Kill criteria for broader lane

If H1 fails AND L-001 notice-driven signal fails to confirm on 2026 forward data (30+ resolved cases), the entire corporate-action-timing lane is over. Pivot attention to other Tier 1 signals.

### What this deliberately does NOT recommend yet

- No broker-flow layer (H3) until H1 passes
- No universe expansion beyond banks + hydros
- No new policy document until 25+ forward-resolved cases exist

---

## Expected Outcome

Given Pakistan's 4.9% and India's ~0.1% daily AAR:
- NEPSE banks post-ex drift: **−1.5% to −3% over 5 days**
- Hit rate: **60-68%**
- Close to but not stronger than L-001's notice-driven number

Absence of short-selling + overlap with AGM notices = don't expect a blowout.

---

## Full Source List

- [BJZZ (JoF 2021)](https://onlinelibrary.wiley.com/doi/abs/10.1111/jofi.13033)
- [Ardia et al. BJZZ decay (FMPM 2025)](https://link.springer.com/article/10.1007/s11408-025-00487-4) | [arXiv](https://arxiv.org/abs/2403.17095)
- [Blau, Fuller & Van Ness — Short Selling around Dividends (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=1138382) | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0929119910000866)
- [Ducret et al. — Dividend Shortage (SSRN 2025)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5101091) | [earlier COVID version](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3716174)
- [Elton-Gruber 32 Years Later (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=363620) | [Stern PDF](http://people.stern.nyu.edu/mgruber/working%20papers/tax_effects.pdf)
- [Pakistan ex-dividend study (ResearchGate)](https://www.researchgate.net/publication/357274029_The_ex-dividend_day_stock_price_behavior_Evidence_from_Pakistan) | [IBA PDF](https://ir.iba.edu.pk/cgi/viewcontent.cgi?article=1311&context=businessreview)
- [India NIFTY ex-dividend (ResearchGate)](https://www.researchgate.net/publication/308277131_EFFECT_OF_EX-DIVIDEND_DATE_ON_STOCK_RETURNS_OF_NIFTY_STOCKS_IN_INDIA)
- [Robinson-Glean Jamaica tax-free (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2887305)
- [Dupuis tax-free emerging (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=3129995)
- [Joshi NRB Economic Review](https://www.nrb.org.np/red/vol24-1_art5/)
- [IJIRT 158229](https://ijirt.org/publishedpaper/IJIRT158229_PAPER.pdf)
- [Nepalytix — Book Closure Primer](https://nepalytix.com/blog/what-is-book-closure-date-in-nepse-and-why-it-matters-for-investors)
- Internal references: `experiments/LEARNINGS.md` L-001, L-003, L-007, L-010, L-011, L-012, L-013
