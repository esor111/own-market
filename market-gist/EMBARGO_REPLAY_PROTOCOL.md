# Embargo Replay Protocol

## Purpose

This file defines how replay experiments must be structured so they stay trustworthy.

The goal is simple:

- no look-ahead leakage
- no month-by-month overfitting
- no promotion from weak evidence

This protocol should be followed before any important replay rule change or feature-driven challenger test.


## Core Rule

We do **not** improve the system inside the same month we are judging.

We do:

1. freeze one version
2. run one or more full historical blocks unchanged
3. study the result after the block is complete
4. build one challenger only if the evidence is strong
5. test that challenger on untouched later blocks
6. promote only if it survives those untouched blocks


## What Embargo Means Here

In this project, embargo means:

- keep a safety gap between the months used to **discover** a pattern
- and the months used to **validate** or **promote** a change

Why:

- our replay scores setups over up to `10` future sessions
- if we tune too close to the next test window, outcomes and context can overlap in a misleading way

So the working protocol is:

- use at least a `10-trading-session` conceptual gap between discovery and promotion judgment
- and do not promote from a single immediately adjacent discovery window alone

In practice for this project:

- treat full months as the main unit
- use separate untouched months for validation


## Standard Month Roles

Each replay month should have one clear role.

### 1. Discovery Month

Purpose:

- measure the frozen champion
- diagnose repeated failure patterns
- identify one candidate challenger

Allowed:

- diagnostics
- summaries
- challenger design

Not allowed:

- champion promotion from that month alone


### 2. Validation Month

Purpose:

- test the challenger on untouched data

Allowed:

- champion vs challenger comparison
- critique and review

Not allowed:

- retune the challenger inside the same validation month


### 3. Promotion Check Month

Purpose:

- confirm the promoted default on a fresh untouched month

Allowed:

- legacy champion vs promoted champion comparison

Not allowed:

- multiple new changes at once


## Recommended Workflow

### Step 1. Freeze Champion

Freeze the current replay champion.

No rule edits while the chosen discovery window is running.


### Step 2. Run Discovery Window

Example:

- February and April used to identify sector-context behavior

The point is not to promote from one month.
The point is to find repeated gaps.


### Step 3. Build One Challenger

Only after repeated evidence.

Example:

- full sectorsoft challenger
- then narrower fragility-only challenger

Only one meaningful challenger at a time.


### Step 4. Validate On Untouched Months

Run the challenger against the frozen champion on later untouched months.

Example:

- May
- June
- July
- August

No challenger changes during this phase.


### Step 5. Aggregate Evidence

Before promotion, summarize:

- changed case count
- improved vs worsened cases
- action deltas
- verdict deltas
- whether gains are broad or concentrated


### Step 6. Promote Only If The Gain Is Trustworthy

A challenger can be promoted only if:

1. it improves untouched months repeatedly
2. it does not create a bigger new problem
3. the change is understandable
4. the gain is not obviously just one lucky month


### Step 7. Revalidate After Promotion

After promotion:

- run one fresh untouched month
- compare legacy champion vs promoted champion
- confirm the promoted rule still behaves well


## Promotion Checklist

Before promotion, all of these should be true:

1. the challenger is based on a repeated pattern
2. the challenger was tested on untouched months
3. results improved more than they worsened
4. the effect is understandable
5. the effect is not caused by a broken file or comparison bug
6. the change can be described in one or two clear sentences

If any of these fail:

- no promotion


## Current Project Interpretation

Right now the project should follow this exact logic:

- champion changes happen slowly
- diagnostics can happen often
- challenger experiments can happen carefully
- promotion requires repeated untouched-month success

That means:

- do not change rules day by day
- do not change rules inside the same replay month being judged
- do not promote from one interesting replay slice


## Current Example

The fragility-only replay rule is the current reference example of the correct protocol:

1. sector behavior was discovered across earlier months
2. a broader challenger was tested and narrowed
3. the narrower challenger was validated across untouched months
4. only then was it promoted
5. then September was used as a fresh post-promotion check

That is the model to follow for future changes.


## What This Protocol Prevents

This protocol protects us from:

- overfitting one month
- rewriting logic too quickly
- mixing discovery and validation
- promoting changes we do not really understand


## Next Rule

Before building the next challenger, ask:

- what discovery months support it?
- what untouched months will validate it?
- what month will act as the post-promotion check?

If those are not clear, the challenger is not ready yet.
