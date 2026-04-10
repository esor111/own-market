# Experiment 03: NRB Rate Events

## Hypothesis
Discrete NRB policy changes (rate cuts, margin lending rule changes, CRR adjustments) create measurable short-term moves in NEPSE banking and hydropower stocks.

## Why
Our earlier monthly regime filter was busted (flat error rates). But that tested NRB data as a continuous variable. Discrete policy announcements are different — they're sudden shocks, not slow drifts. The July 2025 margin lending changes caused a 66% surge in share-backed lending. That's real market impact.

## Success Criteria
- Track A (policy events): Find at least one event type with >60% directional hit rate after baseline adjustment, or honestly report that N is too small.
- Track B (interbank rate moves): Find whether large daily rate changes predict next-week bank stock returns with >55% hit rate.

## Key Risk
Small N. NRB makes 5-10 major policy decisions per year. Across 3 years that's 15-30 events. May be statistically inconclusive like Experiment 02 (lock-in, N=27, p=0.25).

## Data Sources
- Policy events: hand-curated from NRB monetary policy archives, news reports
- Daily interbank rates: NRB CMFM pages (nrb.org.np/cmfm_rates/)
- Price data: local Sharesansar CSV archive (1,570 daily files, 2021-2026)

## Symbols
Banks: NABIL, NBL, EBL, HBL, KBL, SANIMA, PRVU, NIMB
Hydro: SMHL, HIDCL, NGPL, API, AKPL, UPPER
