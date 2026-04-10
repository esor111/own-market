# Web Research: Next-Phase Data And Learning

## Purpose

This note captures what outside research suggests we should do next for this project.

The goal is not to copy a generic trading system.

The goal is to answer:

- what extra data is actually missing for our replay and learning loop
- what world-class system builders do to avoid going in the wrong direction
- how to add learning without overfitting


## Current Project Reality

Right now the replay system is still mostly built from:

- per-symbol daily history
- simple rolling trend and liquidity metrics
- replay basket cross-sectional context
- replay market/sector proxy regime context

That is a strong start, but it is still missing some of the highest-value point-in-time context.


## Main Research-Based Conclusion

The next phase should **not** be:

- more threshold tuning
- more random technical indicators
- more browser scraping just because it is possible

The next phase should be:

- better point-in-time context data
- stronger walk-forward validation discipline
- explicit calibration and monitoring


## What Data Is Still Missing

### 1. Point-In-Time Market And Sector Benchmarks

Why it matters:

- Research shows relative returns are often more predictable than aggregate returns.
- Predicting each stock alone can hide the more useful cross-sectional signal.

What we need:

- NEPSE benchmark history at the same replay dates
- sector index histories at the same replay dates
- relative strength features:
  - stock vs market over 5d, 20d, 60d
  - stock vs sector over 5d, 20d, 60d
  - sector vs market

Why this is better than current replay proxies:

- our current replay regime is inferred from the replay basket itself
- that is useful, but weaker than true market and sector benchmark histories


### 2. Point-In-Time Corporate Action Timeline

Why it matters:

- In Nepal, rights, bonus shares, book closure, AGM, prospectus approval, listing notices, and similar events can distort price action.
- These are exactly the kinds of situations where a clean-looking chart can be misleading.

What we need:

- dated corporate action timeline per symbol
- status fields such as:
  - pipeline
  - approved
  - book closure announced
  - listing in progress
  - recently listed
  - event absorbed

Best sources:

- SEBON prospectus and right-share pages
- CDSC book-closure disclosure process
- NEPSE notices / listing files


### 3. Better Liquidity And Execution Proxies

Why it matters:

- Research from emerging markets and recent work on volume prediction both suggest liquidity and tradability are not side details.
- They are part of the edge.

What we should add:

- zero-return-day share or no-move frequency
- turnover persistence
- trade-count persistence
- gap frequency
- average true range / volatility relative to turnover
- next-session tradability proxies
- Thursday-close / weekend-gap tag

Important note:

- simple turnover alone is not enough
- we need execution-quality context, not only “is it liquid today?”


### 4. Market Breadth And Sentiment

Why it matters:

- Research suggests sentiment changes the cross-section of returns
- this is especially important when weaker / more story-driven names behave differently from stronger names

What we should add:

- daily advancers vs decliners
- up-volume vs down-volume
- new highs vs new lows
- sector breadth
- turnover concentration across sectors
- simple sentiment proxy tags for the replay date

Nepal-specific version:

- broad market euphoria / weakness
- event-heavy weeks
- political or policy shock days tagged manually at first


### 5. High-Level Fundamental Quality Snapshots

Why it matters:

- outside research does not support using only price and volume forever
- earnings quality and fundamental momentum can matter

What we should add:

- quarterly EPS direction
- capital raising / dilution risk
- book value / capital adequacy where relevant
- earnings quality proxy if available
- “results improved / weakened / unclear” style tags

This does **not** mean building a huge fundamental model first.
It means giving the replay system a few high-signal quality flags.


### 6. Historical Order-Flow Features If Reconstructable

Why it matters:

- order flow and institutional flow have predictive content

What to add only if we can reconstruct it historically:

- broker concentration
- net accumulation / distribution
- last-15-minute close pressure
- holding changes

Important:

- these are valuable, but they are **not** the best next historical replay backbone unless we can reconstruct them point-in-time
- for replay, benchmark / event / liquidity data is more urgent


## What World-Class System Builders Actually Do

### 1. They Use Time-Ordered Validation

They do not:

- train on the future
- tune inside the same test month
- celebrate one lucky backtest

They do:

- frozen time-order splits
- walk-forward testing
- holdout periods
- challenger vs champion comparisons


### 2. They Treat Backtest Overfitting As A Major Risk

The lesson is simple:

- a better-looking backtest is not enough
- a strategy can look smarter only because it overfit the test window

That means our current policy is correct:

- no threshold changes from weak evidence
- no tuning inside the same month we are judging


### 3. They Optimize For Ranking And Conditional Edge

A strong system often focuses on:

- which stocks are strongest relative to peers
- which setups should be filtered out
- where confidence should be lower

not only:

- exact next-day direction


### 4. They Calibrate Confidence

Strong systems do not stop at:

- score = 72
- confidence = 78

They ask:

- when we said 70-80 confidence, how often were we actually right?
- was the model overconfident in mixed or event-heavy regimes?


### 5. They Monitor Live Performance After Deployment

They do not assume:

- a model that passed replay is safe forever

They keep:

- post-deployment monitoring
- performance drift tracking
- regime-specific review
- organized documentation for changes and limits


## What This Means For Our System

### The Best Next Data Layer

The next high-value data layer for **historical replay** is:

1. point-in-time market and sector benchmark histories
2. point-in-time corporate action timeline
3. stronger liquidity / execution proxies
4. market breadth / sentiment proxies

This is more justified than:

- more threshold tuning
- more raw chart indicators
- more browser-only live features


### The Best Learning Loop

The smart loop should be:

1. freeze one system version
2. run a full discovery month unchanged
3. record errors, reason codes, and regime breakdown
4. make at most one justified change
5. test that challenger on the next untouched month
6. promote only if it holds up out of sample

This is the correct way to learn without drifting.


### What We Should Not Do

We should not:

- keep changing thresholds every few days
- treat February and March as one giant tuning set
- use live-only browser features as if they existed historically
- mistake more complexity for more edge


## Recommended Implementation Order

### Phase 1

Add replay-safe data first:

- market benchmark history
- sector benchmark history
- corporate action timeline
- improved liquidity / execution features


### Phase 2

Rerun the walk-forward process:

- February as discovery
- March as untouched holdout
- compare champion vs challenger


### Phase 3

Only if the evidence improves:

- promote the new version
- then repeat on the next block


## Short Bottom Line

If the current replay is based mainly on CSV historical price/turnover/trade data, that is enough to start.

It is **not** enough to finish.

The most valuable missing data is:

- true market/sector benchmarks
- corporate action timeline
- richer liquidity / execution context
- breadth / sentiment context

And the most valuable missing process is:

- versioned walk-forward champion/challenger testing with calibration and monitoring


## Sources

- [scikit-learn TimeSeriesSplit](https://scikit-learn.org/stable/modules/generated/sklearn.model_selection.TimeSeriesSplit.html)
- [scikit-learn Probability Calibration](https://scikit-learn.org/stable/modules/calibration.html)
- [The Probability of Backtest Overfitting (SSRN)](https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2326253)
- [Seemingly Virtuous Complexity in Return Prediction (NBER)](https://www.nber.org/papers/w34104)
- [Predicting Relative Returns (NBER)](https://www.nber.org/papers/w23886)
- [How and When are High-Frequency Stock Returns Predictable? (NBER)](https://www.nber.org/papers/w30366)
- [Caught On Tape: Institutional Order Flow and Stock Returns (NBER)](https://www.nber.org/papers/w11439)
- [Trading Volume Alpha (NBER)](https://www.nber.org/papers/w33037)
- [Liquidity and Expected Returns: Lessons from Emerging Markets (NBER)](https://www.nber.org/papers/w11413)
- [Investor Sentiment and the Cross-Section of Stock Returns (NBER)](https://www.nber.org/papers/w10449)
- [Earnings Quality and Stock Returns (NBER)](https://www.nber.org/papers/w8308)
- [NIST AI RMF Manage](https://airc.nist.gov/airmf-resources/playbook/manage/)
- [NIST: Challenges to the Monitoring of Deployed AI Systems](https://www.nist.gov/publications/challenges-monitoring-deployed-ai-systems-center-ai-standards-and-innovation)
- [Federal Reserve SR 11-7 Model Risk Management](https://www.federalreserve.gov/supervisionreg/srletters/sr1107a1.pdf)
- [SEBON Right Share Approved](https://www.sebon.gov.np/right-share-approved)
- [SEBON Right Share Pipeline](https://www.sebon.gov.np/right-share-pipeline)
- [SEBON Prospectus Portal](https://sebon.gov.np/prospectus)
- [CDSC Book Closure Disclosure Form](https://cdsc.com.np/downloads_files/2021_01_03_04_34_13_book_close_discloser_information_form.pdf)
