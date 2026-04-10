# System Change Policy

## Purpose

This file defines how we change this project.

The goal is simple:

- do not move randomly
- do not change the system because a result feels interesting
- do not follow raw intuition if the evidence does not support it
- improve the system in small, testable, reliable steps

This policy should be treated as a permanent rule for future work.


## What We Are Building

We are building:

- a reliable market-analysis system
- a replay and learning system
- a system that can improve over time

We are **not** building:

- a random collection of scripts
- a system that changes direction every day
- a system that keeps patching itself from weak evidence


## Core Principle

Every important system change must follow this sequence:

1. freeze the current rules
2. measure the current behavior
3. replay or review real cases
4. compare prediction vs reality
5. identify the repeated gap
6. make one small change
7. rerun the same test
8. keep the change only if the evidence is clearly better

Short version:

`freeze -> measure -> replay -> compare -> identify repeated gap -> change one thing -> rerun -> keep or revert`


## What Counts As Good Evidence

A change is justified only when one of these is true:

- the same failure pattern repeats across many replay cases
- the same issue appears in both replay and live learning
- there is a clear structural bug in the code or data flow
- a change improves results without creating a larger new problem

A change is **not** justified because:

- it sounds smart
- it matches a hunch
- one symbol looked interesting
- one small replay window gave a dramatic result
- a model or user suggested it without repeated evidence


## Rules For Changing The System

### 1. Do Not Change Multiple Things At Once

If we change too many things together:

- we stop knowing what caused the result
- learning becomes noisy
- mistakes become hard to trace

Rule:

- one meaningful change at a time


### 2. Do Not Change Thresholds From Weak Evidence

Thresholds should change only after repeated replay or live evidence.

Example:

- not after one bad week
- not after one symbol
- not after one interesting replay case


### 3. Separate Structural Changes From Rule Changes

There are two kinds of changes:

- structural changes
  - storage
  - replay architecture
  - critique pipeline
  - adapter safety
- rule changes
  - thresholds
  - gating logic
  - scoring conditions

These should not be mixed carelessly.


### 4. Keep Replay And Live Separate

Replay and live runs must stay separate in raw storage.

We combine:

- lessons
- reason codes
- proposals

We do **not** combine:

- raw replay files
- raw live files


### 5. LLMs Critique, Humans Decide

The LLM can:

- explain failures
- explain successes
- summarize repeated patterns
- suggest changes

The LLM should not:

- auto-change thresholds
- auto-edit architecture
- invent missing data
- overrule evidence


## Current Project Decision

Based on the experiments so far, the current decision is:

- freeze the current rules for now
- do **not** raise the global `watch_only` RR threshold
- do **not** loosen the global improving-watch gate
- do **not** make a broad threshold change yet

Why:

- the replay experiments showed that simple threshold changes were not reliably better
- some experiments made the system much worse
- that means the current problem is not a simple one-threshold problem


## Current Best Next Phase

The most justified next phase is:

- add cross-sectional context

This likely means:

- stock vs peer basket
- stock vs sector proxy
- stock vs market proxy
- ranking inside the replay basket

Why this next:

- repeated misses were concentrated in specific names, not everywhere
- that suggests missing context, not one magic threshold


## Change Cadence

### Fast Changes

These can change faster:

- summaries
- package formatting
- critique wording
- documentation


### Medium Changes

These should change only after repeated evidence:

- thresholds
- action gates
- scoring logic


### Slow Changes

These should change only when there is structural proof:

- architecture
- storage model
- provider strategy
- replay framework shape


## Standard Review Questions

Before changing anything important, ask:

1. What repeated problem are we solving?
2. Is this problem visible in replay, live, or both?
3. Are we changing one thing or many things?
4. How will we measure before vs after?
5. What result would prove the change helped?
6. What result would prove the change hurt?

If we cannot answer these clearly, we should not change the system yet.


## Practical Working Rule

If we are uncertain:

- do another experiment
- do not do another threshold change

If the signal is weak:

- gather more evidence
- do not force a decision

If the result is mixed:

- prefer no change over a random change


## Unclear-Direction Rule

If the direction is unclear, or an assumption would meaningfully affect the system, we must **not** guess our way forward.

We must do this in order:

1. inspect the current codebase and current replay/live artifacts
2. inspect the latest project learnings and research notes
3. identify what is still unknown in the current system
4. search the web using sources that are relevant to this exact system and problem
5. compare outside research against what the system already does
6. write down the decision before opening a new rule or architecture change

This means:

- no blind assumptions
- no changing direction from raw intuition alone
- no copying generic trading advice into the system

Short version:

`codebase first -> current evidence -> web research -> system-specific comparison -> written decision -> only then change or continue`

If this process still does not produce a clear direction:

- keep the champion frozen
- continue research
- do not force a rule change


## Final Principle

This project should improve by:

- evidence
- repetition
- comparison
- careful iteration

Not by:

- pressure
- noise
- excitement
- random ideas

That is the policy.
