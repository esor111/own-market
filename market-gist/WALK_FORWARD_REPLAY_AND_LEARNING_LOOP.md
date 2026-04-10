# Walk-Forward Replay And Learning Loop

## Purpose

This document defines the safest and smartest way to move from:

- "we can generate structured decisions"

to:

- "we can test those decisions honestly, learn from them, and improve carefully"

The goal is not fake backtesting.

The goal is:

1. freeze what the system would have known on a past trading session
2. make the decision exactly as if we were there
3. move forward one real session at a time
4. compare prediction vs reality
5. store the comparison clearly
6. let the LLM critique the result
7. improve the system only when repeated evidence supports a change


## Why This Is The Right Next Step

The project already has a strong base:

- current data collection
- truth-layer cross-checking
- browser-edge extraction
- decision logic
- LLM-ready packages
- memory store
- similar-setup retrieval
- critique and improvement-log layers

What it still does **not** have is enough resolved evidence to prove edge.

That means the next phase should be:

- replay
- compare
- learn

not:

- add random new features
- keep rewriting logic from intuition alone


## Core Idea

We should run the system in **walk-forward replay mode**.

That means:

- choose a historical month or period
- step through the market one real trading session at a time
- for each session, freeze only the data that would have been available then
- make the system decision
- save it permanently
- then move to the next session and score what happened

This protects us from:

- look-ahead leakage
- fake hindsight confidence
- overreacting to one recent miss


## Nepal Market Fit

This replay should match Nepal market reality.

Working operating assumptions:

- regular trading days: `Sunday-Thursday`
- regular trading hours: about `11:00 AM-3:00 PM` Nepal time
- Friday and Saturday: closed
- holidays override the normal weekday pattern

Important rule:

- replay should use **actual trading sessions from data**
- not just weekday assumptions

That means:

- if the market was closed for a holiday, replay skips that date
- the system should think in terms of session closes
- Thursday close should carry weekend-gap caution


## What A Replay Unit Is

The clean replay unit is:

- one symbol
- one decision date
- one timeframe package
- one frozen decision snapshot
- one later outcome record
- one comparison record
- one critique record

In simple words:

- "what did we know then?"
- "what did we decide then?"
- "what happened later?"
- "what do we learn from that?"


## Golden Rules

### 1. Freeze Point-In-Time Truth

A replay case must only use data that would have existed on that session close.

Never allow:

- future price bars
- future event knowledge
- later broker context
- later floorsheet context
- later sector outcome knowledge


### 2. Save Every Stage Separately

Each replay case should save:

- raw case input
- normalized case input
- derived decision
- later outcome
- comparison
- critique

Nothing should be silently replaced.


### 3. Keep History And Latest Pointers

Replay artifacts should follow the same rule as the current validation layer:

- dated files for history
- stable `latest__...` files for convenience


### 4. LLMs Critique, Humans Approve

The LLM should:

- explain failure patterns
- summarize success patterns
- suggest improvements

The LLM should not:

- auto-edit code
- auto-change thresholds
- overwrite architecture decisions


## The Replay Flow

### Step 1. Select A Period

Example:

- February 2026

The replay engine should identify:

- all real trading sessions in that month


### Step 2. Build A Session Snapshot

For each session `T`, build the point-in-time package using only that session's available data.

That package should include:

- market regime
- sector regime
- symbol structure
- event state
- liquidity state
- trade plan
- broker-edge summary if reconstructable
- session context


### Step 3. Freeze The Prediction

Save the final replay prediction for session `T`.

This should include:

- action: `buy`, `watch_only`, `avoid`, or `incomplete_data`
- score
- confidence
- entry zone
- stop
- targets
- invalidation
- reason list
- uncertainties


### Step 4. Move Forward To Session `T+1`

After the next real session exists, score the earlier case.

Do not mutate the old prediction.

Only add new linked records:

- outcome
- comparison
- critique


### Step 5. Score Multiple Horizons

Do not score only one way.

Each replay case should track:

- `T+1` session result
- `T+5` session result
- `T+10` session result
- stop hit or not
- target hit or not
- max favorable excursion
- max adverse excursion
- still open / unresolved if needed


### Step 6. Build The Comparison Record

For each case, generate a rich comparison record.

That record should answer:

- what did we predict?
- what actually happened?
- was the action good?
- what changed between prediction and outcome?
- why did this likely work or fail?


### Step 7. Run Critique

Then the LLM critique layer should read:

- frozen case snapshot
- actual outcome
- comparison record
- similar past cases

And produce:

- likely success/failure drivers
- misleading signals
- missing context
- suggested filter changes
- suggested packaging improvements


### Step 8. Aggregate Improvement Signals

Then the improvement log should aggregate:

- recurring failure reasons
- recurring missing data
- repeated weak thresholds
- repeated packaging confusion

This should guide future updates.


## What Must Be Stored For Each Replay Case

Each replay case should save the following artifact types.

### A. Frozen Case

Purpose:

- the exact point-in-time case

Should contain:

- session date
- symbol
- timeframe
- run label
- provider context
- browser-edge availability flag
- market / sector / stock features
- decision-ready package


### B. Replay Decision

Purpose:

- the actual system call on that date

Should contain:

- action
- score
- confidence
- trade plan
- actionability flags
- reasoning summary


### C. Replay Outcome

Purpose:

- what later happened

Should contain:

- next-session result
- 5-session result
- 10-session result
- target/stop state
- excursion stats
- resolution status


### D. Comparison Record

Purpose:

- turn prediction vs outcome into a structured learning object

Should contain:

- predicted action vs realized usefulness
- confidence vs realized quality
- risk/reward vs actual path
- what worked
- what failed
- reason codes


### E. Critique Record

Purpose:

- LLM-readable case review

Should contain:

- concise case summary
- similar setups
- critique prompts
- improvement suggestions
- confidence notes


## Recommended Replay Storage Shape

The safest shape is a separate replay area under `data/`.

Suggested structure:

```text
data/
  replays/
    2026-02__monthly_replay_v1/
      metadata/
      sessions/
        2026-02-02/
          JBBL/
            raw/
            normalized/
            derived/
            comparisons/
            critiques/
      summaries/
        latest__replay_summary.json
        latest__reason_frequency.json
        latest__improvement_candidates.json
```

Rules:

- replay data must not overwrite live daily-run data
- replay should have its own namespace
- replay summaries should have dated files plus `latest__...` pointers


## Comparison Dimensions

Each comparison should evaluate five dimensions.

### 1. Data Quality

Questions:

- was truth aligned?
- was the data complete?
- were there provider gaps?
- was the case partially reconstructed?


### 2. Context Quality

Questions:

- did the market support the trade?
- did the sector support the trade?
- was there event distortion?
- was liquidity good enough?


### 3. Setup Quality

Questions:

- was the structure actually actionable?
- was the entry too extended?
- was RR too thin?
- did timeframes conflict?


### 4. Execution Reality

Questions:

- would this have been practically tradable?
- did Thursday/weekend risk matter?
- did close-session behavior change the risk?


### 5. Outcome Quality

Questions:

- did the trade thesis work?
- did it fail fast?
- did it drift without follow-through?
- did it work but with worse-than-expected path?


## Reason Code Taxonomy

The comparison layer should use consistent reason codes.

Suggested initial set:

- `truth_mismatch`
- `provider_gap`
- `event_distortion`
- `timeframe_conflict`
- `sector_headwind`
- `market_headwind`
- `liquidity_weak`
- `rr_too_thin`
- `breakout_too_extended`
- `late_entry`
- `broker_distribution`
- `valid_setup_no_followthrough`
- `target_unrealistic`
- `stop_too_loose`
- `stop_too_tight`
- `thursday_gap_risk`
- `insufficient_confirmation`

Rules:

- use fixed codes first
- allow free-text notes second
- do not rely on only free-form explanations

This is important because recurring reason-code frequency is one of the cleanest ways to improve the system.


## Metrics That Matter

The replay should produce rich metrics, not just one win rate.

### Decision Metrics

- buy precision
- watchlist usefulness
- avoid precision
- incomplete-data rate


### Ranking Metrics

- top-ranked average outcome
- shortlist vs non-shortlist outcome gap
- sector-relative ranking quality


### Trade-Plan Metrics

- target-hit rate
- stop-hit rate
- average max favorable excursion
- average max adverse excursion
- average realized vs expected RR


### Confidence Metrics

- confidence bucket hit rate
- calibration drift
- overconfident misses
- underconfident wins


### Reason Metrics

- most common failure reason
- most common success reason
- reasons by sector
- reasons by regime


## When To Change What

This is one of the most important parts of the whole system.

### Change The LLM Package Quickly When:

- the LLM keeps missing context
- the current package is too noisy
- a signal is present but buried
- summary wording keeps creating confusion


### Change Thresholds Or Rules Only After Repetition

Examples:

- RR threshold looks consistently too loose
- one setup type repeatedly fails
- a specific event window should become a harder block

Suggested cadence:

- weekly review
- monthly threshold change

Do not change thresholds after one or two bad cases.


### Change Architecture Only For Structural Problems

Examples:

- replay cases cannot be frozen safely
- artifacts are getting overwritten
- comparison records cannot trace source evidence
- browser-edge logic is contaminating core runs
- outcome scoring is not reproducible

Suggested cadence:

- only after repeated structural pain
- and only with a documented decision


## What The LLM Should Actually Do In Replay

The LLM should be used as a **case reviewer**, not a magical oracle.

Best LLM questions:

- what was the main success or failure driver here?
- which signals were genuinely helpful?
- which signals were misleading?
- was the action itself wrong, or only the timing?
- what one filter or summary change would have improved this case?

Best LLM outputs:

- short case thesis
- failure reason summary
- confidence-quality note
- suggested package improvement
- suggested rule-review candidate


## What The LLM Should Not Do

Do not let the LLM:

- auto-change code
- auto-rewrite thresholds
- auto-promote weak one-off patterns into rules
- pretend unresolved outcomes are final truth


## Recommended Review Cadence

To avoid overfitting and chaos:

### Daily

- generate replay decisions
- score newly available short-horizon outcomes
- save comparison records


### Weekly

- review recurring reason codes
- review best and worst cases
- review LLM critique quality


### Monthly

- review metric drift
- decide on threshold or package changes
- decide whether architecture needs adjustment


## Definition Of Success For This Replay Phase

This phase is successful when we can do all of the following reliably:

- replay one historical month session by session
- save frozen decisions without leakage
- score outcomes on multiple horizons
- produce structured comparison records
- produce critique records
- aggregate recurring improvement signals

At that point, the system becomes:

- not just a decision engine
- but a learning engine


## Best Next Implementation Order

If we build this, the clean order should be:

1. `replay_calendar.py`
2. `replay_case_builder.py`
3. `replay_decision_runner.py`
4. `replay_outcome_scoring.py`
5. `comparison_record.py`
6. `reason_codes.py`
7. `replay_review_summary.py`

Then connect that to:

- `llm_case_critique.py`
- `improvement_log.py`
- `memory_store.py`


## Final Principle

The smartest version of this project is not:

- predict once
- patch randomly
- hope more indicators solve it

The smartest version is:

- freeze reality
- predict honestly
- compare carefully
- critique clearly
- improve slowly and deliberately

That is how this becomes reliable.
