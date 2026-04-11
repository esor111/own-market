# Thread 1: Nepal Festival and Cash-Flow Cycle Effects on NEPSE

## Question
How do Nepal's festival, religious, and cash-flow calendar events affect stock market behavior in ways mainstream finance research has missed? Specifically: Dashain bonuses, Tihar gifts, Nepali New Year, diaspora remittance peaks tied to Hindu calendar, FD maturity cycles, the August "uncollected dividend" mystery, civil service paydays, insurance premium collection cycles.

## Method
WebSearch across NepJOL, NRB Economic Review, Pravaha journal, Nepalytix, ShareSansar, Kathmandu Post, NRB monthly data references, Nepal labor and company law summaries.

## TL;DR

The Dashain/October effect is published. The Tihar effect is folklore. The Baisakh New Year "rally" is empirically rejected. The August unclaimed-dividend cluster is an AGM-shadow at 5-year lag (solved). The most novel finding is the **Ashad insurance tax-rush hypothesis** — directionally opposite to existing literature, mechanism anchored in tax law, untested.

---

## Finding 1: Dashain Bonus Effects — Published in Aggregate, Decomposition Open

**What is established:**
- **K.C. & Joshi (2004), NRB Economic Review** — the foundational NEPSE calendar paper. Did NOT find a January effect but DID find a statistically significant **October effect** with higher and positive returns. Authors attributed this to (a) Dashain/Tihar falling in October and (b) information-release timing around AGM disclosures. **They did not decompose the bonus mechanism from remittance or settlement effects.**
- **Pravaha (2024), Vol 30 No. 1** — Panel data on 17 listed commercial banks, 9 years daily data (2015-2023). Found month-of-year pattern with **seasonal indices ranging from 0.917 (December low) to 1.083 (August high)**, September also elevated, April and December lowest. Frames it as "fiscal and festive effect" — but does not isolate the bonus mechanism.
- **Kathmandu Post (2014):** turnover dropped from ~Rs 400m pre-festival to ~Rs 100m post-festival during one Dashain window — "wait-and-watch."
- **ShareSansar tally (9 years):** NEPSE gained 5 times in the week before Dashain and lost 4 times, but lost far more often in the week after. Roughly coin-flip pre-, with a negative bias post-.
- **Nepalytix claim:** ~3.5% pre-Dashain price lift, ~2.5% post-Dashain decline. (Dataset not verified.)

**Legal anchor:**
- **Labor Act 2074 (2017), Section 45:** Dashain/festival allowance is **mandatory**, equal to one month's basic salary, payable **at least 7 days before Dashain**. This means the cash injection is a legally forced, date-anchored shock. Exemptions: employers with <10 workers, seasonal workers, government employees (separate regulations). Government employees separately receive a one-month Dashain bonus.

**What is open:**
- Nobody has cleanly decomposed Dashain bonus → demat opening, margin lending growth, IPO subscription rates from contemporaneous remittance peaks and AGM disclosure timing.

**Verdict:** The October/Dashain effect is published. The bonus-specific decomposition is open and worth testing. Tradeable edge is modest because the calendar pattern is already public knowledge.

---

## Finding 2: Tihar / Bhai Tika Secondary Liquidity Wave — REJECTED

**What I found:**
- No academic paper separates Tihar effects from Dashain effects. K.C. & Joshi and Pravaha both lump them into "October effect."
- Kartik month (mid-Oct to mid-Nov, roughly Tihar) records Rs 133.82 bn in remittances vs the Ashoj peak of Rs 201.22 bn — meaning **Tihar is the cooling-off tail of the remittance wave, not an independent peak.**
- Bhai Tika gift money flows intra-household. This circulates existing cash, not new liquidity, so there is **no plausible mechanism** for Tihar gifts to inject net new money into NEPSE independent of the Dashain wave.

**Verdict:** Not a tradeable signal. If our automation detects a "Tihar effect" separate from Dashain it is almost certainly autocorrelation bleed-through.

---

## Finding 3: Nepali New Year (Baisakh 1) Rally — REJECTED

**What I found:**
- **Pravaha (2024) explicitly found April is among the LOWEST months** (alongside December) for commercial bank stock prices, seasonal index ~0.917. This is the **opposite** of a Baisakh rally.
- Plausible mechanism for the April weakness: **advance tax second installment is due Chaitra-end (mid-April, just before Baisakh 1)** — 70% cumulative tax liability, which pulls cash out of the system. Liquidity-drain event, not liquidity-injection.
- K.C. & Joshi rejected a January effect. Pravaha effectively rejects a Nepali-New-Year effect by showing April is negative, not positive.

**Verdict:** No Baisakh rally exists. The tradeable angle is **Chaitra-end tax drag** — a short-side or de-risking window in early April tied to the advance-tax deadline. This is the opposite of what Western calendar-effect literature would predict and is genuinely under-studied.

---

## Finding 4: Diaspora Remittance Peaks → NEPSE Lag — Real, Untested

**What is established:**
- **NRB data:** Ashoj (mid-Sep to mid-Oct) is the single largest remittance month every year, now over Rs 200 bn/month. Kartik (mid-Oct to mid-Nov) is the second-largest. NRB attributes the peak to "Dashain, Tihar and Chhath" remittances.
- Nepalytix and other commentary discusses remittance-to-NEPSE causality but does not publish a lag regression.

**Plausible lag mechanism:**
- Remittances hit household accounts in Ashoj
- Festival spending absorbs a chunk immediately
- Residual drifts into bank deposits over Kartik-Mangsir
- The "extra" savings becomes available for margin lending and retail equity buying as Dashain/Tihar holidays end
- Expected NEPSE-turnover response: **~2-6 weeks post-Ashoj**

This timing is consistent with the observed November-December buying pressure and with Pravaha's August-September peak for bank prices (pre-positioning before the money lands).

**Tradeable hypothesis:** monthly NRB remittance print (public data, released mid-month for the prior Nepali month) leads NEPSE turnover by 2-6 weeks. The signal is the **deviation from the seasonal norm**, not the level. Nobody has published this. Cleanly measurable on existing data.

**Verdict:** High-quality candidate. Bookmark.

---

## Finding 5: FD Maturity Rotation — NOT MEASURABLE

**What I found:**
- No research tracks FD maturity cohorts rotating into equity.
- The related effect (FD rate decline → equity inflow) is documented as commentary but not formally tested.
- Current 2026 NEPSE commentary: excess banking liquidity, CD ratio at 73.86% — historically low. Banks are over-deposited and under-lent. This **weakens** the "FD maturity releases marginal equity buyer" story because there is no liquidity constraint to release.
- Banks don't publish FD issuance data by tenor and vintage at usable frequency. NRB doesn't aggregate it. Bank annual reports are too lagged.

**Verdict:** Not measurable from public data. Skip.

---

## Finding 6: August "Uncollected Dividend" Cluster Mystery — SOLVED

**What I found:**
- Nepal's fiscal year ends Ashad (~mid-July). Companies Act 2063 requires AGMs within 6 months of FY-end, so AGMs cluster in **Bhadra-Ashwin-Kartik** (August-November).
- **Companies Act 2063 Section 182:** dividends unclaimed for **5 years** must be transferred to the Investor Protection Fund. Companies must publish a notice in a national daily before the 5-year window expires, with at least 1 month notice.
- **Therefore:** companies that declared dividends 4.5-5 years ago in Bhadra AGMs need to publish "come collect" notices exactly 5 years later → the August "uncollected dividend" cluster is the **delayed mirror** of the Bhadra AGM cluster 5 years prior. **It is not a regulatory deadline that falls in August; it is the shadow of the AGM season.**

**What it tells us:** The August unclaimed-dividend wave is not a signal. It is a reliable marker of when AGM density peaked 5 years previously. Our existing filtering (treating these as housekeeping noise) is correct.

**Verdict:** Mystery solved. No tradeable signal. Confirms our pipeline is right to filter these out.

---

## Finding 7: Civil Service Payday — Untested, Cheap to Test

**What I found:**
- No published date-of-month convention for Nepal civil service payroll.
- Multiple sources confirm monthly payroll and month-end custom, but no official document specifies "paid on day X of Nepali month Y."
- Civil servants receive their one-month Dashain bonus before Dashain (adds to the Dashain wave, doesn't open a separate channel).
- "Payday effect" relies on reliable month-end concentration and high retail participation. Nepal's retail base has exploded recently (demat accounts ~6.9m by 2024) so the mechanism could exist.

**Key insight:** Nepal uses **both** Western and Nepali month calendars for paydays. Government is the largest single employer → **Nepali month start (Baisakh 1, Jeth 1, etc.) is the relevant date, not January 1.** This is the **key reason** prior researchers may have found "no turn-of-month effect" — they probably used Gregorian dates.

**Verdict:** This is worth re-testing using **Bikram Sambat month-start dates**, which is a twist no published researcher seems to have tried. Could be a genuinely novel finding. Cheap — uses existing data, just a calendar conversion.

---

## Finding 8: Insurance Premium Tax-Rush → NEPSE Drain — HIGHEST NOVELTY

**What I pieced together:**
- Nepal allows life insurance premium as an income tax deduction (Rs 25,000 per resident natural person; verify against latest Finance Act).
- Income tax year = fiscal year = Shrawan to Ashad. Advance tax installments: Poush-end (40%), Chaitra-end (70%), Ashad-end (100%). Final reconciliation after Ashad-end.
- This creates a **tax-motivated rush to pay premiums before Ashad-end** each year, particularly for first-year new business. **Structurally identical to India's 80C rush before March 31.**
- **Investopaper:** life insurers collected Rs 124.72 bn in 8 months Shrawan-Falgun of FY2082/83. Distinct Chaitra-Baisakh-Ashad lift from the tax rush is implied but no published paper quantifies this.

**The hypothesis:**
If retail households have a fixed savings pool they are allocating between equities (NEPSE) and tax-advantaged life insurance, then the **Chaitra-Ashad window is a structural liquidity drain from NEPSE into life insurance.** This is the second support for Pravaha's finding that April is a low month, and it would predict continued weakness through Baisakh-Jestha-Ashad (mid-April to mid-July).

**Cross-check:** if Pravaha's seasonal index for May-June-July is also below 1.0, that's consistent with a tax-drain story spanning the full Chaitra-Ashad window.

**Testable claim:** monthly NEPSE turnover in Jestha-Ashad is depressed relative to seasonal baseline in years with high life insurance premium growth, and the correlation is asymmetric (insurance high → NEPSE low, but not vice versa).

**Verdict:** **The single most novel hypothesis from this thread.** Mechanism anchored in tax law. Directional-opposite to festival literature. Measurable from NIA monthly premium prints + NEPSE turnover. No published paper. Bookmark for after persistence batch-scoring.

---

## Ranked Priority (Within This Thread)

By novelty × measurability × clean mechanism:

1. **Ashad insurance tax-rush → NEPSE drain (#8)** — highest novelty, law-anchored, directional-opposite
2. **Monthly remittance-deviation lag to NEPSE turnover (#4)** — medium novelty, fully measurable
3. **Dashain bonus decomposition from remittance & settlement effects (#1)** — extends K.C. & Joshi
4. **Chaitra-end advance-tax drag (part of #3/#8)** — explains Pravaha's April low
5. **Day-of-Nepali-month payday effect (#7)** — untested, cheap
6. **August unclaimed-dividend cluster as AGM-lag indicator (#6)** — confirms our filtering, not a signal
7. **FD maturity rotation (#5)** — skip
8. **Tihar cash-gift secondary wave (#2)** — skip

## Honest Limitations

- Could not access SSRN PDFs directly via WebFetch (permission denied)
- K.C. & Joshi sample period and exact methodology come from search snippets, not full paper reads
- Pravaha 2024 numbers (17 banks, 2015-2023, indices 0.917-1.083) come from a search summary, not the full PDF
- Rs 25,000 life insurance premium deduction ceiling needs verification against current Finance Act
- Nepalytix is a blog, not peer-reviewed; treated as practitioner folklore
- "Could not find any paper connecting civil service payday to NEPSE" — could be absence of research or absence of search hits

## Master Source List

- [K.C. & Joshi, The Nepalese Stock Market: Efficiency and Calendar Anomalies — NRB Economic Review](https://www.nrb.org.np/er-article/the-nepalese-stock-market-efficient-and-calendar-anomalies/)
- [K.C. & Joshi SSRN listing](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=743666)
- [Pravaha 2024 Vol 30 No 1 — fiscal and festive effects on commercial bank stock prices](https://nepjol.info/index.php/pravaha/article/download/76887/58848)
- [Month-of-the-year Effects in Nepalese Stock Market — NepJol](https://www.nepjol.info/index.php/pycnjm/article/download/35919/28084)
- [Nepalytix — Dashain & Tihar Effect on NEPSE](https://nepalytix.com/blog/dashain-tihar-effect-on-nepse-do-festivals-really-bring-a-stock-market-rally)
- [Nepalytix — Dashain Bonuses and NEPSE](https://nepalytix.com/blog/dashain-bonuses-and-nepse-how-festival-payouts-influence-stock-market-liquidity-and-trading)
- [Nepalytix — Seasonal Trends / Dashain Rally](https://nepalytix.com/blog/seasonal-trends-in-nepse-is-there-really-a-dashain-rally)
- [Nepalytix — How Remittance Inflows Shape Nepal's Stock Market](https://nepalytix.com/blog/how-remittance-inflows-shape-nepals-stock-market)
- [Nepalytix — Interest Rate Trends and NEPSE](https://nepalytix.com/blog/interest-rate-trends-and-nepse-how-borrowing-costs-shape-market-movements)
- [ShareSansar — Dashain Effect in NEPSE](https://www.sharesansar.com/newsdetail/unfinalized-draft-dashain-effect-in-nepse-what-happens-before-and-after-the-holidays-2020-10-20)
- [Kathmandu Post — Nepse turnover dives after Dashain (2014)](https://kathmandupost.com/money/2014/10/10/nepse-turnover-dives-for-two-days-after-dashain)
- [Kathmandu Post — Nepse Dashain hangover (2017)](https://kathmandupost.com/money/2017/10/15/nepse-in-dashain-hangover-down-3263-points)
- [Kathmandu Post — Banks have unclaimed dividends worth Rs1.77b](https://kathmandupost.com/money/2015/09/06/banks-have-unclaimed-dividends-worth-rs177b)
- [Nepal Labor Act Dashain bonus — Nepal Lawyer](https://www.nepallawyer.com/blog/dashain-bonus-in-nepal)
- [Festival Allowance Nepal — Sushil Parajuli](https://sushilparajuli.com/festival-allowance-in-nepal-under-labor-law/)
- [Companies Act Section 182 Dividend — actnepal.com](https://actnepal.com/en/section/182/0/section-182-dividend-of-companies-act-2063)
- [AGM Process in Nepal — Tax Consultant Nepal](https://taxconsultantnepal.com/annual-general-meeting-agm-process-in-nepal/)
- [Conducting AGMs for Public Companies in Nepal](https://nepallaws.com/conducting-annual-general-meetings-agms-of-public-companies-in-nepal/)
- [NepseTrading — Nepal Receives Record Remittance in Ashoj](https://nepsetrading.com/blog/nepal-receives-record-remittance-in-ashoj-surging-past-npr-200-billion-in-a-month)
- [Kathmandu Post — Remittances top Rs200 billion a month (2025)](https://kathmandupost.com/money/2025/11/16/nepal-s-monthly-remittances-top-rs200-billion-for-first-time)
- [Himalayan Times — Remittances soar 35% in Q1 2025/26](https://thehimalayantimes.com/business/remittances-soar-35-in-q1-of-202526-nrb-data-shows)
- [NRB — Remittance Inflows to Nepal: Economic Impact and Policy](https://www.nrb.org.np/er-article/remittance-inflows-to-nepal-economic-impact-and-policy/)
- [NepseTrading — Non-Life Insurance Premium Collection Crosses NPR 28 Billion by Magh](https://news.nepsetrading.com/non-life-insurance-premium-collection-crosses-npr-28-billion-by-magh?lang=en)
- [Investopaper — Life Insurance Premium Collection](https://www.investopaper.com/news/life-insurance-companies-premium-collection/)
- [Investopaper — Non-Life Premium Collection 6 Months](https://www.investopaper.com/news/non-life-insurance-premium-collection/)
- [Annapurna Express — Life insurers collect over Rs 100bn](https://www.theannapurnaexpress.com/story/52995/)
- [Income Tax in Nepal 2026 — courtmarriageinnepal](https://courtmarriageinnepal.com/blog/income-tax-in-nepal)
- [NepseTrading — NEPSE Liquidity Analysis 2025/26](https://nepsetrading.com/insights/nepal-stock-market-liquidity-analysis)
- [clickmandu — Banks face liquidity glut, CD ratios slide (2026)](https://english.clickmandu.com/2026/03/7452/)
- [Edusanjal — Salary of Civil Servants FY 2082/83](https://edusanjal.com/blog/salary-civil-servants-nepal/)
- [Nepal Economic Forum — Retail Investors in Nepal's Bull Market](https://nepaleconomicforum.org/are-retail-investors-ignoring-risk-in-nepals-bull-market/)
- [Short run performance of IPOs in Nepal — NepJol](https://nepjol.info/index.php/jnma/article/download/62096/46883/182934)
