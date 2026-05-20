# UPPER — Event Case #3: 2024 July–August FY-Result Rally

**Case opened**: 2026-05-20
**Type**: Multi-week directional rally (+87% in 6 weeks) into an annual result print
**Status**: Descriptive only. **Observation, not prediction.** Per `DOSSIER_CONTRACT.md` §5. Methodology references inline.

---

## 1. Mechanical selection rule (per METHODOLOGY Rule 6)

- **19 of the top-30 highest-volume days in UPPER's last 5 years** (computed in `deep_analysis.py` 2026-05-20) sit inside the July-15 → August-27 2024 window. That's the largest volume-event cluster in the entire 5-year series, and it dwarfs any other window.
- **+87% close-to-close move in 32 trading days** is the largest single price advance in 5 years.
- The cluster + the move both flag this window mechanically — no hindsight selection.

## 2. Price/volume chronology

| Date | Close | Δ% | Volume | Note |
|---|---:|---:|---:|---|
| **2024-06-30** | **153.10** | — | low | **5-year absolute low** |
| 2024-07-15 | 176.70 | +3.33% | 2,174,728 | Rally launch on heavy vol |
| 2024-07-18 | 188.60 | −0.53% | 2,082,349 | Sustained on volume |
| 2024-07-23 | 203.60 | +6.32% | 967,741 | Break above 200 |
| 2024-07-24 | 213.90 | +5.06% | 1,376,794 | Continued |
| 2024-08-06 | 200.00 | **−7.02%** | 956,826 | Sharp pullback |
| 2024-08-08 | 213.00 | +1.87% | 888,517 | Recovery |
| 2024-08-11 | 234.30 | **+10.00%** | 2,451,686 | **LIMIT-UP** |
| 2024-08-12 | 254.90 | +8.79% | 1,958,240 | Continuation |
| **2024-08-13** | **256.80** | +0.75% | 1,419,070 | **FY RESULT RELEASED: net loss Rs 2.68b** |
| 2024-08-14 | 270.50 | +5.33% | 1,839,917 | Rally accelerates AFTER loss print |
| **2024-08-15** | **286.00** | +5.73% | 1,718,044 | **PEAK** |
| 2024-08-18 | 276.00 | −3.50% | 1,540,050 | First reversal |
| 2024-08-21 | 266.10 | −3.59% | 1,001,536 | Slide |
| 2024-08-25 | 254.20 | −4.79% | 975,373 | Slide |
| 2024-08-27 | 238.00 | −6.37% | 1,309,527 | Rally capitulation |

**The decisive fact: UPPER rallied 153 → 256 INTO a Rs 2.68 BILLION ANNUAL LOSS PRINT, then continued rallying another +12% to 286 in the two trading days AFTER the loss announcement.** A record annual loss was the rally's *acceleration*, not its end.

## 3. The catalyst (per our own events file)

> **2024-08-13 — local events list entry:** "Upper Tamakoshi Hydropower Limited has posted a **net LOSS of Rs 2.68 billion** and published its 4th quarter [annual] analysis of the fiscal year 2080/81."

Source: ShareSansar announcement (mirrors NEPSE disclosure), captured in
`dossier_data.corporate_actions("UPPER")` events list.

## 4. Why this happened — descriptive interpretation only

This is the textbook NEPSE **"fiscal-year-end → August result positioning rally"** pattern documented in `..\market-research\research_nepse_local_practitioner_2026.md` §9.1. The mechanism cited by the source:

> "Banks pump credit before fiscal-year-end to meet asset growth targets, push profits, then the *announcement of full-year results in August* drives the post-July relief rally. Loan-book quality is recognised only after the fiscal-year-end audit." (Source's §9.1 mechanism for banking — but the pattern empirically spills into hydro and other sectors.)

For UPPER specifically, the rally pricing-in seems to combine three things, all *positioning-based, not fundamentals-driven*:

1. **Anticipation of next-FY monsoon Q1 profitability** — UPPER's only profitable quarter (mechanical, given fixed PPA + heavy interest + dry quarters lose money). The market was buying the recovery ahead.
2. **"Bad news already priced in"** — when the FY result confirmed a large loss but didn't deliver further negative surprise, the rally accelerated rather than reversed.
3. **Pure seasonal retail-flow** — the §9.1 pattern is a long-standing NEPSE behavioral pattern documented across BFI sectors; it apparently activates on hydro too in years where the setup is right.

**Important honest caveat:** the calendar lab (`nepse-volume-psychology-lab/CALENDAR_*.md`) tested whether this seasonal pattern can be *statistically confirmed* at retail-available N. Verdict: **suggestive but unconfirmable** — every sector-year of the pattern came up positive, but 5–6 years of data cannot clear an honest α=0.01 bar (needs ≥9 same-sign years). So this is *real history* but **NOT a tradeable systematic rule.** It's discretionary context, not a signal.

## 5. Broker-flow analysis — Rule 11 fingerprints VALIDATED on the actual rally

Source: `analyze_event.py` snapshot output for the Jul 15 → Aug 20 2024 window
(from `broker_flow_fact_table.csv`).

### Naasa Securities (#58) — confirmed INFORMED

- **Top-3 BUYER on essentially every single rally day** in late July → mid-August 2024. Consistent buying of 40k–120k shares per day.
- Net-buyer day-leader on **Aug 14 at +108,066 shares** (close 270.50) — one trading day before the absolute peak of 286.
- **Flipped to net-seller day-leader on Aug 18 at −70,674 shares** (close 276) — right after the peak.
- **Pattern: accumulated through the rally, sold lead the day right after the top.** Textbook informed trading.

This is the *exact* behavior the Rule-11 fingerprint (+3.58% avg follow-through, n=21 across 343 days) statistically captured. The August 2024 case is the strongest single empirical confirmation of the fingerprint.

### Dynamic Money Managers Securities (#44) — confirmed FORCED

- Was net-seller day-leader on **8 of the rally days**: Jul 15 (−77k), Jul 18 (**−260,306**), Jul 22, Jul 23, Jul 30, Jul 31, Aug 1 (−165k), Aug 11 (−169,867), Aug 12 (−208,048).
- **Jul 18 2024: −260,306 shares is the largest single-broker net position on UPPER in 343 days of broker history.** Their max position in our dataset. At a close of 188.60. Price proceeded to rally another ~50% to the 286 peak.
- **Sold into the limit-up day (Aug 11, +10.00%): net −169,867.** Selling 169k into a limit-up locked-bid day.
- **Pattern: sold consistently into a rising rally, took the largest position right when the rally still had ~50% to run.** Textbook forced flow.

The Rule-11 fingerprint of −7.05% avg follow-through (n=20 over 343 days) is *exactly* the kind of pattern this 2024 case displays at maximum severity.

## 6. The Sep 2024 landslide context

The September 27-28, 2024 landslide (88-day shutdown, 4 deaths, Rs 1.78b insurance claim still unresolved mid-2025 — see `COMPANY_CONTEXT.md` §8a) hit ~6 weeks **after** the Aug 15 peak. By then UPPER had already given back from 286 → ~238 (Aug 27). **The disaster hit a stock that was already unwinding the rally, not initiating the collapse.** The September shutdown is the catalyst for the *floor* that held into 2025; the rally giving-back was a separate, earlier phenomenon driven by the rally exhausting.

## 7. What this case teaches (observation, not prediction)

1. **The §9.1 pattern is empirically real on UPPER 2024.** It is also statistically unconfirmable at retail N (calendar lab proved this). Both true. Use as context, never as a rule.
2. **Rule 11 fingerprints work.** Naasa #58 INFORMED and Dynamic Money Managers #44 FORCED — the statistical averages match the day-by-day reality of the largest single move in 5 years. Confidence in the fingerprints is materially higher after this case.
3. **A loss announcement does not automatically mean a price drop.** Rs 2.68b loss + the price *accelerating* in the following 2 days is a real fact about how NEPSE retail flow interacts with seasonal patterns. Worth remembering for future result-day reads.
4. **Big-volume rally-on-loss days are a candidate "absorption" pattern** (METHODOLOGY Rule 9) — Aug 11's limit-up day had broker 44 selling 169k into it while broker 58 and others absorbed. The absorbing buyers won decisively.

## 8. Open questions / `[unverified]`

- **Were broker 58 / 44's identities the same legal entities in 2024 as in 2026?** Broker IDs are stable on NEPSE in the medium term but corporate ownership/management of brokerages can change. `[unverified — would need SEBON registry history]`.
- **What share of the absorbing buy-side flow was retail vs institutional?** Floorsheet shows broker counterparties but not their underlying clients. `[unverified — not available in our data]`.

## 9. Limits (per DOSSIER_CONTRACT §7, binding)

- This case **does not say** "next August on UPPER is a buy" — N=1 named event of this pattern on UPPER, even though the source's §9.1 cites 14 years of cross-sector data. Calendar lab already proved the systematic version is unconfirmable.
- The Naasa-accumulating + Dynamic-Money-Managers-selling pattern of this case is **descriptive**; the next equivalent setup could look identical and resolve differently.
- No buy/sell, no target, no stop emerges. Pattern memory only.

## Sources

- `dossier_data.corporate_actions("UPPER")` events list (the 2024-08-13 entry).
- `broker_flow_fact_table.csv` (Jul–Aug 2024 broker rows).
- `analyze_event.py` outputs.
- Source pattern: `..\market-research\research_nepse_local_practitioner_2026.md` §9.1.
- ShareSansar announcement: net-loss FY2080/81 result, 2024-08-13.
- Broker identity mapping: `https://www.merolagani.com/BrokerList.aspx` + ShareSansar weekly broker summaries.
- Calendar-lab honest verdict: `..\..\nepse-volume-psychology-lab\CALENDAR_VERDICT.md`.
