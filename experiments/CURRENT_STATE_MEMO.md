# Current State Memo

Date: 2026-04-10

## Purpose

This memo captures the current project state after:

- the broker persistence shadow build
- the corporate-action experiment corrections
- the bank-only dividend annotation addition
- the first forward shadow scoring pass
- the first completed NRB rate-events experiment

The goal is to separate:

- what is already working
- what is promising but not yet proven forward
- what remains research-only
- what we should do next

## What Is Proven Enough To Keep Running

### 1. Broker persistence shadow

This is still the strongest live lane in the project.

Current forward scorecard:

- source: `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.json`
- resolved rows: `14`
- persistence caution only:
  - resolved cases: `9`
  - 10-day negative hit rate: `88.9%` (`8/9`)
  - mean 10-day return: `-1.65%`

Interpretation:

- the sample is still small
- the resolved cases are clustered across only a few report dates, so they are not fully independent observations
- but this is the cleanest forward evidence we have
- persistence remains the best mechanical avoid lane

Status:

- keep running daily
- do not change the frozen caution logic yet

### 2. Shadow batch scoring itself

We now have a working forward scorer for saved shadow reports:

- script: `market-gist/automation/score_persistence_shadow_reports.py`
- outputs:
  - `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_cases_v1.csv`
  - `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.json`
  - `market-gist/data/validation/persistence_shadow_reviews/latest__shadow_batch_scorecard_v1.md`

What it does:

- scores saved shadow report rows against forward price returns
- uses the same per-symbol duplicate-session collapse logic as the experiment framework
- marks unresolved rows as pending if forward price data is not available yet
- separates:
  - `persistence_caution_only`
  - `persistence_caution_plus_dividend_annotation`
  - `supportive_only`
  - `no_signal`

Interpretation:

- we now have a real evaluation loop, not just daily logging

## What Looks Strong In Research But Is Not Yet Forward-Proven

### 3. Bank dividend declaration caution

This is the best corporate-action signal we found after:

- anchoring fix
- baseline adjustment
- sector split
- duplicate-event cleanup
- housekeeping notice filtering

Validated research result:

- source: `experiments/01-corporate-action/results/phase4_event_caution_review.md`
- signal: dividend-family announcement -> drift 2 to 10 trading days
- commercial banks only:
  - cases: `50`
  - adjusted negative hit rate: `76.0%`
  - mean excess return: `-2.27%`
  - p-value: `0.0002`

Operational status:

- added to the daily shadow report as annotation-only
- it does not change verdicts
- it is bank-only
- housekeeping / unclaimed-dividend notices are filtered out

Forward status:

- still under-sampled in live shadow scoring
- current resolved overlap sample is only `1` case

Interpretation:

- strong research signal
- not enough forward live evidence yet to promote beyond annotation

## What Is Interesting But Should Stay Research-Only

### 4. Book-closure notice caution

Earlier framing that this was a clean cross-sector signal was wrong.

After dedup and sector split:

- commercial banks: weak / not significant
- hydropower: strong

Current interpretation:

- not a bank rule
- maybe a hydro research note
- not ready for promotion into the active bank shadow lane

### 5. Lock-in expiry

This lane was worth testing, but the result is still thin.

Interpretation:

- mechanically valid experiment
- not enough strength to promote
- keep parked unless sharper date sources are added later

### 6. NRB rate events

Experiment 03 is now complete:

- official AJAX rate endpoint used
- official policy archive dates used
- baseline-adjusted study run

Main finding:

- NRB effects are real
- but they do **not** form a simple market-wide rule like:
  - `easing = bullish for everything`

Observed shape:

- commercial banks often show a buy-the-rumor / sell-the-news pattern around easing policy-rate events
- hydropower often shows stronger positive immediate reaction
- large daily interbank moves show cleaner hydro-heavy effects than bank-heavy effects
- daily interbank rate moves are mostly too noisy to promote as a mechanical signal

Interpretation:

- useful as regime/context research
- not clean enough to promote as a standalone trigger

Status:

- keep as research-only
- do not wire into shadow yet

## What We Should Not Claim

We should not currently claim:

- that corporate actions are generally bearish
- that book-closure notice is a clean cross-sector bank signal
- that dividend annotation already improves live shadow performance
- that NRB easing gives a simple bullish market trigger
- that supportive persistence logic is validated yet

## Current Operating State

### Active daily lane

- broker flow scrape / backfill
- persistence shadow report
- bank-only dividend annotation

### Forward evaluation lane

- shadow batch scorer

### Research lab

- experiment 01: reviewed
- experiment 02: tested but weak
- experiment 03: tested, context-only
- experiment 04: not started
- experiment 05: not started

## Best Next Step

The next priority is **not** a new experiment.

The next priority is:

1. keep generating shadow reports daily
2. rerun the shadow scorer whenever new forward price data arrives
3. let Juliet validate:
   - the shadow scorer
   - Experiment 03
4. once more forward cases accumulate, compare:
   - persistence only
   - dividend annotation only
   - persistence + dividend together

## Bottom Line

Right now the project has:

- one genuinely strong live signal lane: broker persistence
- one strong research-side event lane: bank dividend declaration caution
- one completed but non-promoted macro lane: NRB rate events

The correct posture is:

- keep collecting
- keep scoring
- promote slowly
- do not invent new lanes until the current forward evidence grows
