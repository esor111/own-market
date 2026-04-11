# Thread 5: Hydropower Nepal Economic Deep Dive

## Question
Why does the Nov→Jan hydro calendar trade work (71% historical win rate, +12% mean return)? What is the fundamental economic story behind it? Is it generation cycle, PPA pricing, dividend cycle, or calendar effect?

## Method
Deep web research on Nepal hydropower PPA economics, generation seasonality, India/Bangladesh export dynamics, AGM/dividend regulatory cycle, and listed company specifics.

## TL;DR — The Candidate Answer

**The most credible candidate explanation for the Nov→Jan hydro rally is the AGM/dividend cycle (option C from the original hypothesis). Generation seasonality (A) and PPA pricing (B) both argue AGAINST a winter rally, which makes them unlikely as primary drivers.**

The candidate mechanism is **Nepal's Companies Act 2063 Section 76**, which forces every public company to hold its AGM within **6 months of fiscal year end** (Ashadh = mid-July). The hard statutory deadline is **Poush 31 ≈ mid-January**.

Hydropower dividends are observably concentrated in Mangsir-Poush (mid-Nov to mid-Jan).

**One independent corroborating dataset:** Investopaper found the NEPSE Hydropower Index has a **79% January win rate** over 2007-2025. Our 71% Nov→Jan figure on a smaller, different sample is consistent with this published finding. **One independent corroboration is not the same as multiple independent confirmations.** The candidate mechanism explains the pattern; it does not yet prove the pattern will continue.

**Status of Strategy C: still "promising, needs forward validation."** The mechanism is now a credible candidate, not a confirmed driver. Strategy C remains parked until forward evidence accumulates in the actual Nov 2026 → Jan 2027 window.

---

## Each Hypothesis Examined

### A. Generation cycle — REJECTED

**The volume story:**
- 80% of Nepal's annual precipitation falls between June and September
- **Run-of-river plants (>90% of Nepal's operating MW) generate only ~30% of installed capacity in dry months**
- Discharge in mid-Feb to mid-March falls to 30-40% of annual average
- March/April is actually the low point per Khimti basin study
- Upper Tamakoshi peaking RoR runs full 456 MW only ~4 hours/day in dry season
- Snowmelt contributes ~20.8% annually but ~59% of dry-season flow (March-May) — does NOT help November-January specifically

**Implication:** Pure generation economics argue AGAINST a Nov→Jan rally. November is end of wet season (best month, already in the price). December-January is when volumes start collapsing. If the market were efficient and fundamentally driven, you would expect the *worst* months for hydros to be Dec-Jan-Feb-Mar.

Sources:
- Evolution and future prospects of hydropower sector in Nepal — ScienceDirect: https://www.sciencedirect.com/science/article/pii/S2405844024071706
- Impact of variation in climatic parameters on hydropower generation — PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9792739/
- Impacts of climate change on hydrological patterns in Khimti River Basin — Springer (2025): https://link.springer.com/article/10.1007/s42452-025-07304-7
- Seasonal Decline in River Flow Drives Hydropower Output Down — Nepal Energy Forum: http://www.nepalenergyforum.com/seasonal-decline-in-river-flow-drives-hydropower-output-down/

### B. PPA revenue recognition timing — REJECTED (minor offset at best)

**The standard run-of-river PPA tariff structure:**

| Project type | Wet (Jestha-Mangsir, ~May-Nov) | Dry (Poush-Baisakh, ~Dec-May) |
|---|---|---|
| **Standard RoR** | NPR 4.80/unit | NPR 8.40/unit (1.75x wet) |
| **Peaking RoR** | NPR 8.40/unit | NPR 10.55/unit |
| **Upper Tamakoshi (UPPER)** | NPR 3.63/unit | NPR 6.96/unit |

- Base rates set 2011, 3% simple escalation for 8 years
- Ministry definition: Dec-May = dry, Jun-Nov = wet
- **Take-or-pay** structure (NEA must buy whatever is generated up to contracted volume)

**Why this doesn't explain a rally:**
- Dry-season tariffs are 1.75x wet, but volumes fall to ~30% of wet
- Net revenue in dry season is still meaningfully lower
- The "dry kicks in Dec 1" timing doesn't match a Nov-Jan rally

Sources:
- Energy Ministry fixes power purchase rates — Kathmandu Post (Jan 2017): https://kathmandupost.com/money/2017/01/10/energy-ministry-fixes-power-purchase-rates
- Deconstructing the Storage Hydro PPA Pricing Framework — Santosh Thapa Blog: https://santoshthapa123.blogspot.com/2025/06/deconstructing-storage-hydro-ppa.html
- Flash Alert on NEA's PPA Decision — PKF Trunco: https://pkf.trunco.com.np/files/publications/1708424392_03_2024_Flash%20Alert%20on%20NEA's%20Decision%20to%20sign%20PPAs%20with%20small%20Hydropower%20Projects%20.pdf

### C. Dividend / AGM corporate action cycle — ACCEPTED ⭐

**Three hard facts stacked together:**

#### Fact 1: Fiscal year timing
- Nepal fiscal year: Shrawan 1 (~July 16) → Ashadh 31 (~July 15)
- Audited financials must be delivered to regulator within 6 months
- **Companies Act 2063, Section 76: AGM must be held within 6 months of fiscal year end**
- This means **Poush 31 (~mid-January) is the hard statutory deadline for every listed company's AGM**

#### Fact 2: Dividends are endorsed AT the AGM
- "Dividends are paid after the company conducts its yearly shareholders' meeting (AGM), and once the AGM endorses the dividends, they are paid out."
- **Book closure** is set shortly before the AGM
- AGM notices must be published 15 days before in a national daily
- This creates a **dividend-capture demand pulse** in the weeks leading up to each AGM

#### Fact 3: Hydropower AGMs cluster in Poush

Verified concrete examples (FY 2080/81 cycle):

| Company | Symbol | Dividend | AGM Date |
|---|---|---|---|
| Chilime Hydropower | CHCL | 12% (10% bonus + 2% cash) | Poush 28, 2081 |
| Sanima Mai Hydropower | SHPC | 10.52% (10% bonus + 0.52% cash) | Poush 28, 2081 |
| Butwal Power Company | BPCL | 5% cash | Poush 28, 2081 |
| HIDCL | HIDCL | 5.25% cash | Poush 24, 2081 |

**Historical pattern (prior years):**
- Chilime FY 2078/79 AGM: Poush 03
- Chilime FY 2079/80 AGM: Poush 20 (15% dividend)
- Same Poush concentration year after year

Sources:
- Conducting AGMs for Public Companies in Nepal — NepalLaws: https://nepallaws.com/conducting-annual-general-meetings-agms-of-public-companies-in-nepal/
- Companies Act 2063 Section 76: https://actnepal.com/en/section/76/0/section-76-annual-general-meeting-of-companies-act-2063
- Dividend Announcement by Hydropower Companies — Investopaper: https://www.investopaper.com/news/dividend-announcement-by-hydropower-companies-in-nepal/
- Chilime 12% Dividend FY 2080/81 — Sharesansar: https://www.sharesansar.com/newsdetail/chilime-hydropower-proposes-12-dividend-for-fy-208081-calls-agm-on-poush-28-2024-12-17
- Sanima Mai 10.52% Dividend — Sharesansar: https://www.sharesansar.com/newsdetail/sanima-mai-hydropower-proposes-1052-dividend-for-fy-208081-calls-agm-on-poush-28-2024-12-10
- HIDCL 5.25% Cash Dividend — Sharesansar: https://www.sharesansar.com/newsdetail/hydroelectricity-investment-and-development-company-proposes-525-cash-dividend-calls-agm-on-poush-24-2024-12-11
- Butwal Power 32nd AGM — Sharesansar: https://www.sharesansar.com/newsdetail/butwal-power-company-limited-holds-32nd-annual-general-meeting-approves-dividend-2025-01-13

### D. Calendar effect / general market behavior — ACCEPTED as secondary

January is strong across multiple NEPSE sub-indices, but hydropower's Jan is notably stronger than most sectors, suggesting sector-specific amplification. The regulatory AGM deadline is the reason hydros amplify it.

### E. Other explanations — Partial accept
- Dividend-capture buying by retail (Nepal retail is very dividend-sensitive)
- Bonus shares are worth more than cash dividend for tax reasons
- End of calendar year foreign-broker activity / NRN repatriation cycles

---

## Independent Corroboration of the Seasonal

**ShareSansar Sept 2024 NEPSE sub-index seasonal study + Investopaper Hydropower Index study (2007-2025):**

- **NEPSE Hydropower Index: January wins 79% of years**
- January and July are the two strongest months
- Cumulative change in January: 86.56%

**Our Phase 2 backtest result: 71% Nov→Jan win rate over 2021-2026**

These two numbers from two different samples and two different time windows are **directly consistent**. We are not finding noise.

Sources:
- In-Depth Analysis of NEPSE Historical Data: Seasonal Trends — Sharesansar (Sep 2024): https://www.sharesansar.com/newsdetail/in-depth-analysis-of-nepse-historical-data-seasonal-trends-across-sub-indices-2024-09-15
- Analysis of Performance of Hydropower Index Compared to NEPSE Index (2007-2025) — Investopaper: https://www.investopaper.com/news/analysis-of-performance-of-hydropower-index-compared-to-nepse-index-2007-2025/

---

## Listed Company Architecture (Key Detail)

| Symbol | Type | Notes |
|---|---|---|
| UPPER (456 MW) | Peaking RoR | NOT a reservoir; Tamakoshi river fundamentally monsoon-driven |
| Chilime (CHCL) | Peaking RoR, 22.1 MW | Owns stakes in Rasuwagadhi (111 MW), Sanjen (42.5 MW), Middle Bhotekoshi |
| Sanjen (SJCL, ~42.5 MW) | RoR | Chilime holds ~38% |
| Rasuwagadhi (RHPL, 111 MW) | RoR | Gandaki tributary |
| API Power | RoR | 8.5 MW operational + 40 MW Upper Chameliya in approval |
| AKPL | RoR | Negative reserves (-1.49 crore) — stressed issuer |
| HIDCL | **Financing vehicle** | NOT a generator. Revenue is interest income from loans to hydro projects. Closer to a bank than a generator. |

**Critical detail:** Nepal has **ZERO operating large storage/reservoir projects** in the listed universe. The big proposed storage projects (Dudhkoshi, Budhi Gandaki, West Seti, Upper Arun 1,063 MW) are not online and not listed. **All listed hydros are RoR-exposed and share the same monsoon curve.**

---

## India/Bangladesh Export Dynamics

**Crushing for Nov-Jan fundamentals:**

- **Highest monthly export revenue: NPR 5.03 billion in Ashoj (Sep 17 - Oct 17)**
- **Lowest monthly export revenue: NPR 1.10 billion in Mangsir (Nov 17 - Dec 15)** — an 80% drop
- Nepal exports from late May to mid-November only
- Bangladesh export window: only June 15 - November 15
- Dhalkebar-Muzaffarpur 400kV: just upgraded from ~600 MW to 1,000-1,100 MW bi-directional
- Butwal-Gorakhpur 400kV under construction: will add up to 3,500 MW additional trade capacity
- NEA exports at avg NPR 8.96/unit; **imports cost up to NPR 16/unit (29% premium)**

**This argues that Nov-Jan is BAD fundamentally.** Which strengthens the case that the rally is dividend-cycle-driven, not generation-driven.

Sources:
- Nepal earns over Rs. 18.2 billion from electricity exports — Rising Nepal: https://risingnepaldaily.com/news/73684
- NEA Plans 200 MW Imports / 500 MW Exports — Nepal Energy Forum: http://www.nepalenergyforum.com/nepal-electricity-authority-plans-200-mw-imports-in-dry-season-and-500-mw-exports-in-monsoon/
- Nepal paying 29% higher tariff for imports — myRepublica: https://myrepublica.nagariknetwork.com/news/nepal-pays-29-percent-higher-tariff-rate-on-india-s-imported-electricity-that-its-export-to-southern-neighbor

---

## Robustness of the Signal

### Robust under
- **Drought years**: AGM deadline is fixed by law — generation volume doesn't matter for the buying pulse
- **New transmission opening**: Helps exports but irrelevant to dividend cycle
- **Individual company bad year**: Other hydros still declare dividends; sector pulse remains

### Fragile under
- **Take-and-pay policy fully implemented** → bank financing freezes → dividends shrink → next year's AGM pulse weakens. **This is the single biggest threat to Strategy C for FY 2082/83 (2025/26) onwards.** Watch if the budget reversal holds.
- **Companies Act amendment extending AGM deadline** (discussed but not passed)
- **Systemic NEA payment default** crushing dividend capacity across the sector
- **A big enough NEPSE-wide bear market** drowning out the corporate-action pulse (the historical 29% loss rate is probably clustered in NEPSE-negative Januaries)

---

## The Take-and-Pay PPA Crisis (Watch Item)

**May 29, 2025: Finance Minister proposed scrapping take-or-pay PPA structure** in the FY 2082/83 budget.

IPPAN warned this would freeze:
- 350+ projects
- NPR 109 billion already invested
- NPR 3.3 trillion in future investment

**Partial reversal:** Small hydros (≤10 MW) and export-oriented retained take-or-pay. The full reversal is still politically live.

Energy Minister Khadka publicly disagreed with Finance Minister Paudel — active political risk.

**For Strategy C: this is the watch item.** If take-and-pay fully kicks in and bank financing freezes, dividend capacity for the next AGM cycle (Poush 2082, ~mid-Jan 2026) shrinks meaningfully. The seasonal effect could attenuate or disappear.

Sources:
- Nepal's energy sector rocked by 'take-and-pay' budget policy — Kathmandu Post: https://kathmandupost.com/national/2025/06/05/nepal-s-energy-sector-rocked-by-take-and-pay-budget-policy
- IPAN Urges Government to Scrap 'Take and Pay' — Fiscal Nepal: https://www.fiscalnepal.com/2025/06/04/20622/ipan-urges-government-to-scrap-take-and-pay-policy-in-ppa-energy-minister-khadka-expresses-concerns/
- New PPA model puts Rs 109bn at risk — Annapurna Express: https://theannapurnaexpress.com/story/55401/

---

## Predictive Checks We Can Build (Forward Watchlist)

For tracking whether Strategy C will fire in the upcoming season:

1. **Count of hydro AGMs announced Nov-Dec each year** — leading indicator. A sparse AGM calendar = weak signal year.
2. **Cumulative dividend % announced by NEPSE hydros as of Mangsir 15** — cross-section strength gauge
3. **NEA payment-arrears reports to IPPAN** — if arrears blow out, expect smaller dividends and a weaker January
4. **Take-and-pay policy status** — currently partially reversed but unresolved. Treat as binary risk toggle.
5. **Ashadh (June-July) rainfall anomaly** — drought year means weak FY and smaller dividends declared in Dec-Jan. Expect muted but still-present seasonal.
6. **Companies that already paid big dividends in previous Poush** — check if two-year smoothing applies

---

## Project Pipeline Context

As of March 2025 (IPPAN Energy Statistics 2025):
- **Total installed capacity: 3,421.956 MW**
- **204 operational hydro projects: 2,948 MW**
- **143 projects under construction: 4,303 MW** (will nearly triple operational capacity)
- 576 projects in survey/study/design: 27,535 MW potential
- Private sector owns >80% of current generation capacity
- 91 listed hydropower companies on NEPSE as of 2025

**Implication:** New supply (4,303 MW coming online) is a structural headwind — depresses scarcity value and puts pressure on PPA terms for new projects. For existing listed companies with locked PPAs, this is less direct but affects sentiment.

---

## Recent Regulatory Changes Affecting Hydro

- **Tax holiday:** Full income tax exemption for 10 years from commercial operation + 50% for next 5 years
- **Corporate tax on hydros:** 20% (vs 25-30% standard); dividend WHT 5%; CGT 10%
- **Take-and-pay shift (May 29, 2025):** Partially rolled back
- **Competitive bidding bill (2023):** Proposed making competitive bidding mandatory for electricity purchases — would fundamentally change PPA economics
- **Time-based electricity tariffs introduced 2025:** NPR 86.01 bn allocated to energy sector

---

## Conclusion

**Strategy C (hydro Nov→Jan calendar buy) now has a credible candidate mechanism: Nepal's Companies Act AGM deadline forces dividend declarations into the Mangsir-Poush window, which plausibly drives a dividend-capture demand pulse.**

The signal is:
- **Consistent with one independent dataset** (Investopaper Hydropower Index 2007-2025, 79% January win rate)
- **Plausibly explained** by securities law (still a hypothesis; not statistically isolated)
- **Plausibly robust** under drought years, transmission changes, and individual company stress (untested)
- **Plausibly fragile** under the take-and-pay PPA reform (currently partially reversed)

**This upgrades L-009/L-010 from "pattern of unknown origin" to "pattern with a credible mechanism, still pending forward validation."** Strategy C's status remains parked until live forward evidence accumulates in November 2026 → January 2027.

The watch item before Strategy C goes live: **track whether take-and-pay PPA reform stays partially reversed** through the next AGM cycle (Poush 2082 = mid-Jan 2026).

---

## Master Source List

### PPA Economics
- Flash Alert on PPA Decision — PKF Trunco: https://pkf.trunco.com.np/files/publications/1708424392_03_2024_Flash%20Alert%20on%20NEA's%20Decision%20to%20sign%20PPAs%20with%20small%20Hydropower%20Projects%20.pdf
- Energy Ministry fixes power purchase rates — Kathmandu Post: https://kathmandupost.com/money/2017/01/10/energy-ministry-fixes-power-purchase-rates
- Deconstructing the Storage Hydro PPA Pricing Framework: https://santoshthapa123.blogspot.com/2025/06/deconstructing-storage-hydro-ppa.html
- Government's Competitive PPA — Nepal Energy Forum: http://www.nepalenergyforum.com/nepals-competitive-ppa-challenges-and-policy-shifts-for-private-energy/

### Generation Seasonality
- Evolution and future prospects of hydropower sector — ScienceDirect: https://www.sciencedirect.com/science/article/pii/S2405844024071706
- Climatic parameters on hydropower generation — PMC: https://pmc.ncbi.nlm.nih.gov/articles/PMC9792739/
- Khimti River Basin climate change — Springer: https://link.springer.com/article/10.1007/s42452-025-07304-7
- Winter Dry Spell Drains Hydropower — NepalConnect: https://nepalconnect.world/winter-dry-spell-drains-hydropower/

### Export Dynamics
- Nepal earns Rs 18.2 billion from electricity exports — Rising Nepal: https://risingnepaldaily.com/news/73684
- Nepal-India power trade boost: Dhalkebar-Muzaffarpur 1,000 MW: https://www.fiscalnepal.com/2025/02/12/19493/nepal-india-power-trade-boosted-dhalkebar-muzaffarpur-line-capacity-increased-to-1000-mw/
- Nepal-India endorse 400 kV transmission lines — Kathmandu Post: https://kathmandupost.com/national/2025/02/13/nepal-india-endorse-investment-plan-for-two-400-kv-transmission-lines

### AGM/Dividend Cycle
- Companies Act 2063 Section 76 — actnepal: https://actnepal.com/en/section/76/0/section-76-annual-general-meeting-of-companies-act-2063
- Conducting AGMs for Public Companies — NepalLaws: https://nepallaws.com/conducting-annual-general-meetings-agms-of-public-companies-in-nepal/
- AGM Process in Nepal — Tax Consultant Nepal: https://taxconsultantnepal.com/annual-general-meeting-agm-process-in-nepal/

### Verified Hydropower AGM Examples
- Chilime 12% FY 2080/81 — Sharesansar: https://www.sharesansar.com/newsdetail/chilime-hydropower-proposes-12-dividend-for-fy-208081-calls-agm-on-poush-28-2024-12-17
- Sanima Mai 10.52% — Sharesansar: https://www.sharesansar.com/newsdetail/sanima-mai-hydropower-proposes-1052-dividend-for-fy-208081-calls-agm-on-poush-28-2024-12-10
- HIDCL 5.25% — Sharesansar: https://www.sharesansar.com/newsdetail/hydroelectricity-investment-and-development-company-proposes-525-cash-dividend-calls-agm-on-poush-24-2024-12-11
- Butwal 32nd AGM — Sharesansar: https://www.sharesansar.com/newsdetail/butwal-power-company-limited-holds-32nd-annual-general-meeting-approves-dividend-2025-01-13

### Independent Seasonal Corroboration
- NEPSE Sub-Index Seasonal Trends — Sharesansar (Sep 2024): https://www.sharesansar.com/newsdetail/in-depth-analysis-of-nepse-historical-data-seasonal-trends-across-sub-indices-2024-09-15
- Hydropower vs NEPSE 2007-2025 — Investopaper: https://www.investopaper.com/news/analysis-of-performance-of-hydropower-index-compared-to-nepse-index-2007-2025/

### Take-and-Pay Crisis
- Nepal's energy sector rocked by 'take-and-pay' — Kathmandu Post: https://kathmandupost.com/national/2025/06/05/nepal-s-energy-sector-rocked-by-take-and-pay-budget-policy
- IPAN Urges Scrap of Take and Pay — Fiscal Nepal: https://www.fiscalnepal.com/2025/06/04/20622/ipan-urges-government-to-scrap-take-and-pay-policy-in-ppa-energy-minister-khadka-expresses-concerns/
- New PPA model Rs 109bn at risk — Annapurna Express: https://theannapurnaexpress.com/story/55401/

### Project Pipeline
- IPPAN Energy Statistics 2025 (Sept): https://www.ippan.org.np/wp-content/uploads/2025/09/Energy-statics-of-Nepal-2025-1.pdf
- IPPAN Energy Statistics 2025 (Mar): https://www.ippan.org.np/wp-content/uploads/2025/03/Energy-Statistics-2025.pdf

### Listed Company Specifics
- Electricity Production by Listed Hydropower Companies — Investopaper: https://www.investopaper.com/news/electricity-production-in-mw-by-hydropower-companies-listed-in-nepse/
- Top Hydropower Companies by Market Cap — Investopaper: https://www.investopaper.com/news/top-hydropower-companies-listed-in-nepal-stock-exchange-based-on-market-cap/
- Upper Tamakoshi resumes full power — Kathmandu Post: https://kathmandupost.com/money/2025/06/30/upper-tamakoshi-project-resumes-full-power-generation
