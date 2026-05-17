# What I've Been Building — In Plain Words (for my trader friend)

Hey — here's the honest story of what I've tried, what flopped, and what we're
doing now. No tech-speak. Tell me where you think I'm wrong. I want your gut
reaction as a trader.

---

## What I was trying to do

The dream: build a system that looks at all of NEPSE and tells me what's going
to go up. An automatic edge. A money machine.

I tested that dream properly — not by guessing, but by actually checking if it
holds. Here's what I tried and what happened.

## The 3 things I tried (and what actually happened)

**1. "Follow the smart brokers" — using broker buy/sell data as labels.**
Idea: floor-sheet shows which broker bought/sold. Maybe tagging days as
"panic", "accumulation" etc. using broker behaviour beats just watching price
and volume.
👉 Result: it did **not** beat plain price-and-volume watching. No real
improvement. Dropped.

**2. "Score the brokers, follow the good ones" — rank brokers by who's usually right.**
Idea: figure out which brokers have historically been on the right side, build
a "smart-money pressure" score, follow it.
👉 Result: looked amazing at first, then collapsed when I tested it honestly.
The "skill" didn't repeat — a broker who looked good in one period was random
in the next. It was basically noise dressed up as a signal. Closed for 6 months
so I don't keep fooling myself.

**3. "Seasonal patterns" — banks rise in July, microfinance in January, etc.**
This is the one you'll find interesting. I pulled the real sub-index data and
checked it. The pattern *is there*: Banking went up **every July, 5 years
straight**; Microfinance up **every January, 6 years straight**. Looks real.
👉 But here's the catch: 5–6 years is too few to *prove* it's a rule and not
luck. Even a perfect 5-out-of-5 isn't enough certainty to bet a system on it.
So: **suggestive, but not provable** with the data we can get. To really prove
it you'd need ~15–20 years of clean data, which doesn't exist for us.

## The honest lesson

A predictive "money machine" on NEPSE, built from the data a normal trader can
get, **can't be proven to work**. That's not me giving up — I tested it three
ways and got a clear answer. The seasonal stuff might be real, but I refuse to
pretend "looks real" equals "proven". That discipline is the whole point — it
stopped me wasting months building on noise.

Important: this does **not** mean NEPSE has no opportunity. It means *a
backtested robot* isn't the way in for us. The way in is sharper *human*
trading — which is the pivot.

## What we're doing now (the pivot)

We stopped building a robot that trades. We're building a **second brain** that
makes *me* a faster, more honest trader on stocks I actually watch.

No predictions. No "buy this". Just: organise everything about one stock in one
place, and keep an honest record of my own calls so I can see — with proof —
what I'm actually good at and where I kid myself.

## What's actually built right now

Plain inventory:

- **Daily data collector** — already running for years; pulls every NEPSE
  stock's daily prices/volume. Solid.
- **Market cockpit** — a daily one-glance summary of the *whole* market: what
  was unusually active, breadth, where volume spiked. Describes only — never
  says buy/sell. Early version working.
- **Single-stock dossier (the new focus)** — a living file on **ONE** stock.
  We picked **UPPER (Upper Tamakoshi)** — the big, well-watched hydropower
  name. Right now the *rulebook* for it is done (the safety rules so it never
  drifts into fake "buy" advice). The actual tool is the next step.

## The next thing — the UPPER dossier (with an example)

Goal: every day, one file shows me everything about UPPER + forces me to log my
own read honestly. Here's what a day looks like:

**The file auto-shows (just facts, no advice):**
> UPPER, today. Close 512, down 1.2%. Volume 4× its normal. Closed near the
> day's low. Brokers: top-5 sellers were 71% of selling; one broker has been
> dumping 4 days straight. Note: AGM book-close was 11 days ago.

**Then I write ONE line (locked, I can't edit it later):**
> "Looks like distribution into a tired stock. Medium confidence."

**Three weeks later I add a review line (original stays untouched):**
> "UPPER fell 9% after. My read was right; the persistent-seller clue is one I
> should trust more."

Do that for months → I get a *proven, un-editable track record of my own
judgment*, and I learn which of my reads actually work. That's a human edge, and
it's honest.

## What I want your opinion on

You're the trader, not the tech guy — so tell me straight:

1. Does the "seasonal pattern is real but unprovable" match what *you* see in
   the market? Would you still trade July banks / January microfinance on feel?
2. Is **UPPER** the right first stock for a daily dossier, or would you pick a
   different one (and why)?
3. In a daily one-pager on a stock, what 3 things would *you* most want to see?
4. The "write your read, can't edit it, review later" habit — would you
   actually use that, or is it too much work?

That's it. Tear it apart. I'd rather hear it now than after I build the thing.
