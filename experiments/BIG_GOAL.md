# The Big Goal

> Short north-star note for the lab.
> Read this when the work starts feeling fragmented, overexciting, or overly tactical.

## One Sentence

**Build an AI-accelerated, evidence-disciplined NEPSE research lab that can separate real edge from seductive noise.**

That is the main goal.

Not:

- a trading bot
- an LLM stock picker
- a random collection of clever experiments
- a beautiful data warehouse with no decision value

## The Applied Product Goal

The practical goal of the whole lab is simpler and more concrete:

**build the best possible system for deciding whether a stock should be bought, avoided, held, or sold, and when that action should happen.**

That is the user-facing goal.

In plain language, the system should get better and better at answering:

- should I buy this stock?
- should I avoid this stock?
- if I already hold it, should I keep holding it?
- when is the right time to sell?

The research-lab framing is not a replacement for that goal.
It is the way we avoid fooling ourselves while trying to reach it.

## What We Are Actually Building

We are building a system where:

- **mechanical signals** do first-pass detection
- **LLMs** help with search, synthesis, critique, and explanation
- **verification** catches overclaim, weak framing, and citation drift
- **forward evidence** decides what deserves trust

This means the product is not just "predictions."

The deeper product is:

**a lab that gets better at telling truth from story**

And the reason that deeper product matters is that better truth filtering is what eventually produces better buy / avoid / sell decisions.

## Why This Matters

AI makes exploration cheap.

We can now:

- search many papers
- run many side quests
- compare many hypotheses
- generate many explanations
- document much more than one person could document alone

But AI does **not** make truth cheap.

Reality still costs:

- correct timestamps
- clean data
- careful baselines
- independent review
- forward time

So the whole game is:

**use AI to widen the search, then use discipline to narrow the truth**

## The Three-Layer Goal Stack

### Layer 1. The immediate goal

Find small NEPSE signals that are actually real and useful for buy / avoid / sell decisions.

Examples:

- broker persistence
- dividend-event drift
- hydro seasonal calendar
- flood-damage hydropower lag

Most candidate signals will die.
That is expected.

The survivors become pieces of the actual decision engine.

### Layer 2. The lab goal

Build a repeatable process that promotes only what survives evidence.

That means:

- baseline adjustment
- calendar discipline
- no benchmark laundering
- no folklore hardening
- Romeo-style verification before canon hardens
- serial promotion even when exploration is parallel

### Layer 3. The deepest goal

Become the kind of research system that can look at a seductive idea and answer:

- true
- false
- maybe, but narrower than it sounded
- promising, but not yet

That is a rarer capability than prediction itself.

## What Success Looks Like

Success does **not** require every side quest to become a signal.

Success looks like:

- a few signals survive
- the surviving signals improve real decision quality on buy / avoid / sell timing
- weak ideas get killed honestly
- documentation stays tighter than excitement
- the system becomes more calibrated over time
- future decisions get faster because the lab has memory

If a side quest dies cleanly and teaches us something real, that is still success.

## What Failure Looks Like

Failure is not "the signal didn't work."

Failure is:

- promoting noise because it sounded elegant
- letting LLM fluency impersonate evidence
- building more than we can verify
- losing the thread of what the lab is for
- optimizing for activity instead of truth

It is also failure if we build an impressive research stack that never becomes better at the actual decision question:

**buy, avoid, hold, or sell?**

## The Operating Principle

When in doubt, ask:

**Does this reduce uncertainty about whether a real edge exists?**

If yes, it probably belongs.
If no, it is probably drift, decoration, or premature infrastructure.

## How This Applies Right Now

For the current hydropower flood lane, the big goal means:

- we are **not** trying to build a full hydropower encyclopedia
- we **are** trying to test whether named physical damage to listed hydro assets creates a real peer-relative effect

So the correct next move is not endless symbol expansion.
It is the move that most reduces uncertainty:

- build a small, honest damage-confirmation event table
- test damaged vs undamaged hydros
- keep, narrow, or kill the lane based on what survives

## Final Compression

If this whole project had to be compressed into one line, it would be:

**Use AI to explore widely, use evidence to believe narrowly, and build a NEPSE lab that earns the right to trust its own conclusions.**
