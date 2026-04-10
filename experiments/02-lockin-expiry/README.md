# Lock-In Expiry

## Hypothesis

Stocks experience negative returns around promoter lock-in expiry due to supply
pressure once locked shares become eligible to sell.

## Method

This standalone experiment uses a pragmatic listing proxy:

- scrape the full ShareSansar company list
- confirm hydropower companies from the live company page sector field
- fetch each company's full ShareSansar price-history feed
- use the earliest traded date in that feed as a listing-date proxy
- set unlock date as `first_trade_date_proxy + 3 years`

This is not a perfect legal lock-in calendar, but it is good enough for a first
mechanical test and can later be tightened by joining CDSC lock-in notices.

## Success Criteria

More than `65%` of unlock events show negative returns in the `+1` to `+20`
trading-day window.

## What Gets Built

- `scrape_listing_dates.py`
  - discovers hydropower symbols from ShareSansar
  - fetches earliest traded date proxy for each company
- `build_unlock_dates.py`
  - computes unlock dates and filters them to the local price range
- `run_event_study.py`
  - measures return windows around unlock events
  - compares event returns to rolling symbol baselines

## Event Windows

- `pre_-20_-1`
- `reaction_0_5`
- `post_1_20`
