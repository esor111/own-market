# Parallel Exploration, Serial Promotion

> Written 2026-04-12 to clarify how this lab should use AI parallelism without
> turning into random experimentation.
> This document refines the operating direction of the lab. It does not weaken
> the frozen-champion discipline.

---

## The Core Law

We are allowed to explore widely.
We are not allowed to promote widely.

AI makes search cheap.
It does **not** make truth cheap.

That means the lab should behave like this:

- run many research threads in parallel
- challenge claims aggressively
- document what survives
- promote only a very small number of things
- require forward evidence before anything becomes trusted

This is the direction.
Not "do fewer things."
Not "do everything."
**Search wide. Promote narrow.**

---

## Why This Exists

Without a doctrine, parallel AI work creates confusion:

- too many side quests
- duplicated work
- seductive results with weak evidence
- literature numbers repeated without checking
- research findings treated like production truth
- excitement outrunning validation

With a doctrine, parallel AI work becomes a compounding advantage:

- more hypotheses searched
- more errors caught early
- more weak ideas killed cheaply
- more context preserved on disk
- fewer bad promotions into the real system

The goal is not to look busy.
The goal is to build a research engine that gets smarter without getting sloppier.

---

## The Three Layers

### 1. Exploration

This is where we use AI aggressively.

Purpose:
- generate hypotheses
- run literature checks
- design experiments
- stress-test assumptions
- collect raw infrastructure
- write completion reports

Properties:
- can run in parallel
- can fail often
- should be cheap
- should produce learning even when the signal dies

Exploration is allowed to be broad.
It is **not** allowed to silently become canonical truth.

### 2. Verification

This is the truth filter.

Purpose:
- catch overclaims
- check citations
- inspect code paths
- test whether the framing matches the evidence
- distinguish "interesting" from "credible"

Properties:
- adversarial by design
- slower than exploration
- required before canonical integration

Romeo and Benvolio live here in different ways:
- Romeo = inside verifier with code and data access
- Benvolio = outside verifier with documentation and web research access

### 3. Validation

This is where reality gets the final vote.

Purpose:
- decide whether a signal earns promotion
- require forward evidence
- prevent historical curve-fit excitement from touching the live lane too early

Properties:
- serial
- conservative
- small in scope
- tied to real decision gates

This is where patience mode still rules.

---

## The Funnel

Every serious idea should move through the same funnel:

`idea -> side quest -> completion report -> verification -> canonical learning/backlog -> shadow candidate -> forward validation -> promotion or kill`

If an idea skips steps, it should not be trusted.

Especially important:

- a research result is **not** a production result
- a documented result is **not** a validated result
- a historically strong signal is **not** a promoted signal

---

## What Belongs Where

To keep the lab coherent, each type of work belongs in a different place.

### Production layer

This includes:
- daily shadow routine
- frozen policy
- scorer
- report generation
- anything that affects the running system

Rules:
- small surface area
- minimal changes
- no side-quest experimentation inside this layer
- no promotion based on excitement

### Canonical layer

This includes:
- `LEARNINGS.md`
- `BACKLOG.md`
- `INDEX.md`
- doctrine files
- current-state memos

Rules:
- only verified findings enter
- uncertain claims must be labeled honestly
- benchmark numbers must be sourced or clearly marked as lab estimates

### Exploration layer

This includes:
- side-quest writeups
- completion reports
- research memos
- pilot plans
- web research bundles

Rules:
- breadth is fine
- disagreement is fine
- incompleteness is fine
- nothing here becomes canonical automatically

---

## The Anti-Randomness Rules

Parallel work is only good if it stays disciplined.

Every side quest should answer these before it starts:

1. What exact question is being tested?
2. What would count as success?
3. What would count as failure?
4. What file will hold the result?
5. What existing learning or backlog item does it connect to?
6. What is the cheapest useful version of this test?

If those are missing, the side quest is probably too vague.

Additional hard rules:

- no benchmark numbers presented as published facts unless they are actually in the paper
- no direct jump from literature enthusiasm to lab promotion
- no changes to frozen policies without explicit evidence and documentation
- no treating raw data collection as signal validation
- no treating many correlated rows as many independent observations
- no hiding uncertainty when the sample is thin

---

## How Many Things We Should Run

Parallelism is good.
Unbounded concurrency is not.

The real bottleneck is not idea generation.
It is synthesis and verification.

So the lab should think in terms of a portfolio:

- **1 production lane** that must stay stable
- **a small number of active verified research threads**
- **a larger backlog of parked ideas**

A good heuristic:

- if we cannot summarize why each active side quest matters in one sentence, we have too many
- if no one is available to verify a result, it is not ready to matter
- if a side quest does not connect to an existing learning, decision, or backlog line, it is probably drift

The lab does not win by maximizing concurrent experiments.
It wins by maximizing learning per unit of confusion.

---

## What AI Is Actually For

AI should be used to:

- search the literature fast
- generate candidate hypotheses
- compare sources
- challenge assumptions
- draft completion reports
- synthesize findings across threads
- preserve memory in files

AI should **not** be trusted to:

- convert weak evidence into strong truth
- promote signals by narrative force
- replace forward validation
- make benchmark numbers up because they "sound right"

AI is the hypothesis factory.
The lab must still supply the truth filter.

---

## Promotion Law

Promotion should always be narrower than exploration.

A finding can be:

- interesting
- documented
- replicated
- verified
- still **not promoted**

Promotion requires more than being clever.
It requires:

1. a clean definition
2. code-path integrity
3. adversarial review
4. honest writeup
5. forward evidence at the right gate

This is the load-bearing law of the lab:

**Many things may be researched. Few things may be trusted.**

---

## Cadence

The lab should run on different clocks for different layers.

### Daily

- run the production routine
- preserve the outputs
- avoid unnecessary production changes

### Weekly

- synthesize side-quest findings
- verify what deserves canonical updates
- kill weak ideas quickly

### At evidence gates

- review whether anything deserves promotion
- do not hold promotion reviews just because we are excited
- hold them when the evidence is actually ready

This is how we stay thoughtful instead of reactive.

---

## What Success Looks Like

The success condition is not:
"we ran a lot of experiments."

The success condition is:

- the production lane stayed stable
- the lab explored more of the search space than one human could alone
- bad claims were caught before they hardened
- good findings were preserved clearly
- only the strongest things reached the promotion gate

If we do that, the system gets sharper over time.
If we do not, we are just generating intelligent-looking noise.

---

## Relationship To Other Docs

- `MANIFESTO.md` explains the bet.
- `ORCHESTRATOR_DOCTRINE.md` explains the human/AI mindset shift.
- `EXPLORATION_CHARTER.md` explains how outside research agents should behave.
- **This file explains how the whole lab should move from exploration to trust.**

Read this file when:
- the lab feels scattered
- too many side quests are competing for attention
- a new finding feels exciting enough to over-promote
- we need to remember the difference between research and reality

---

## One Sentence

**Use AI to widen the search, use verification to narrow the truth, and use forward evidence to decide what earns the right to matter.**
