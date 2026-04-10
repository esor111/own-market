# Experiment 04: Hydropower Seasonality

## Hypothesis
Nepal hydropower stocks follow a reliable seasonal calendar driven by monsoon/dry-season
generation cycles. If confirmed at the individual stock level, this baseline can calibrate
expectations and filter false signals from the persistence and corporate-action layers.

## Why This Matters
- Romeo's agents score 14% direction accuracy on hydro — catastrophically bad
- Hydro is in "research-only" mode in the persistence shadow system
- If a strong seasonal exists, fighting it is the likely source of those errors
- A confirmed seasonal becomes a filter: "only flag deviations FROM the pattern"

## What We're NOT Testing
- Whether you can make money buying hydro in June (everyone knows that)
- Whether this is a standalone trading signal

## What We ARE Testing
1. Is the published sub-index seasonality (Jan strong, Jul strong) real at the individual stock level?
2. Which months are reliably positive or negative across multiple hydro stocks?
3. How does hydro seasonality compare to bank stocks (control group)?
4. Is the pattern consistent enough across years and stocks to use as a calibration baseline?

## Success Criteria
- Find 3+ months with >65% directional consistency across hydro stocks and years
- Show clear separation between hydro and bank seasonal patterns
- If the pattern is noisy/inconsistent at stock level, report that honestly

## Data Sources
- Price data: local Sharesansar CSV archive (2021-2026)
- No external scraping needed

## Symbols
Hydro: SMHL, HIDCL, NGPL, API, AKPL, UPPER
Banks (control): NABIL, NBL, EBL, HBL, KBL, SANIMA, PRVU, NIMB
