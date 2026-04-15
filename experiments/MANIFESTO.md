# Manifesto

> Written 2026-04-10 by Juliet, after a long session with Ishwor.
> Read this when patience mode feels like nothing is happening.

---

## What this is

This is a NEPSE quantitative research lab, run by one ambitious engineer (Ishwor) and his AI companion (Juliet, with Romeo as the verification counterweight). It is not a trading bot. It is not a YouTube signal channel. It is not a bet that LLMs are smart enough to read charts. It is none of those things, and the discipline to NOT be those things is the entire edge.

It is a research lab built around three convictions:

1. **Mechanical signals beat LLM judgment on NEPSE.** Five independent comparisons say so. Published 2024-2025 literature on adjacent markets says the same thing. The trigger should be mechanical. The LLM is for verification and explanation, not for decisions.

2. **Forward evidence beats historical curve-fitting.** Anyone can backtest a thousand hypotheses on 4 years of data and find one that works. Almost none of them survive 30 forward-resolved cases. So we don't deploy until we have forward evidence. And we don't generate hypotheses faster than we can validate them.

3. **Nobody else is doing this in Nepal.** Published academic NEPSE microstructure research is essentially empty for the questions we ask. Practitioner tools rank brokers by turnover, not by skill. Open-source projects scrape data but don't compute outcomes. The closest comparable project (`nepse-quant-terminal`) has the trading UI but no calibration discipline. **We are alone in this niche, and the niche is real.**

---

## What we're actually betting on

We are not betting that we can predict NEPSE day-to-day. Direction accuracy on hydropower is 56% — same as a dumb calendar lookup. We are not better than the calendar.

We are betting that:

- **A small number of mechanical signals will hold up to forward evidence.** Right now: broker persistence (8 of 9 negative on a small sample), dividend-family annotation (live in shadow), Strategy C hydro Nov→Jan (28 historical trades, 71% win rate, AGM-deadline mechanism). Most of these will probably die when the sample grows. The ones that don't die are the foundation.
- **Discipline will keep us alive longer than enthusiasm would.** Romeo's "frozen champion, never change rules without repeated evidence" approach is the most valuable thing in the lab. It is also the hardest thing to maintain when you are excited. This document exists partly so future-Ishwor remembers why current-Ishwor agreed to this.
- **The research itself has value beyond prediction.** If we publish broker-flow analysis on a thin South Asian market with rigorous methodology, that's a real empirical contribution. Nobody has done it. That's a fallback win even if no signal becomes tradeable.
- **Time compounds the unfair advantage.** Every month of forward evidence that accumulates is a month we move ahead of anyone who shows up next year and tries to do this from scratch. Patience mode isn't a defensive crouch. It's a moat being dug.

---

## What's actually working right now

Be honest. Don't oversell.

| What | Status | Honest assessment |
|---|---|---|
| Broker persistence shadow (w7 seller) | Running daily, 14/37 cases resolved | 8 of 9 CAUTION cases negative, but clustered: 7/8 wins from 2 consecutive Aug 2025 days with overlapping forward windows. Effective independent episodes ~2-3, not 9 (audit 2026-04-12, Romeo-verified). Evidence is preliminary. The 23 pending forward cases from Mar-Apr 2026 are the real test. |
| Dividend-family bank annotation | Live in shadow report (annotation only) | 71% bank hit rate, p=0.004, validated. Doesn't change verdicts yet. |
| Hydro Nov→Jan (Strategy C) | Parked, awaiting forward window | 71% historical win rate, +12% mean, has a credible mechanism (Companies Act AGM deadline → dividend cycle), one independent corroboration (Investopaper 79% Jan win rate over 18 years). Still needs forward validation. |
| Bank Aug→Jan avoid signal | Parked, awaiting forward window | 1 winning trade out of 31 historically. Strongest single pattern in the lab. Untested forward. |
| LLM direction prediction | Running | 55-57% accuracy. Same as a calendar lookup on hydro. Wrong layer to optimize. |
| Experiment 03 (NRB rate events) | Done, parked | Anticipation-then-reversal pattern. Use as context, not signal. |
| Lock-in expiry (Experiment 02) | Done, parked | N=27, p=0.25. Inconclusive. |

That's the real scorecard. One signal running. One signal annotating. Two signals parked with credible mechanisms. Two signals dead. The LLM layer is honest about what it can and can't do.

---

## What we are NOT doing (and why)

The list of things we're not doing is longer than the list of things we are. That's the discipline.

- **Not building specialist LLM agents.** L-011 says LLM topology isn't the bottleneck. Reorganizing the LLM layer doesn't add alpha. Even Romeo's open question about narrow-context specialists is bookmark-only.
- **Not adding new experiments.** L-011 explicitly says: stop generating hypotheses faster than you can validate them. The bottleneck is forward time, not historical analysis. Building experiments 06, 07, 08 now would be churning.
- **Not scraping new data sources.** NRB Public Debt Ownership, ICRA ratings, UrjaKhabar, Forex API, Open Data Nepal — all bookmarked, none built. Each new scraper is another thing to maintain, another point of failure.
- **Not writing custom NEPSE HTTP code.** `polymorphisma/nepse_scraper` exists and is the de-facto standard. Use it when needed.
- **Not refactoring working code to make it pretty.** Frozen champion. The persistence policy constants are hardcoded. Magic numbers everywhere. None of it gets touched until forward evidence demands it.
- **Not promoting any signal to live trading.** Every validated signal is currently shadow-only or annotation-only. The persistence batch-scoring decision is the first real promotion gate, and it hasn't fired yet.
- **Not chasing the LLM hype.** The 2024-2025 academic literature has converged on "LLMs as feature extractors and verifiers, not as decision triggers." Two Sigma's 2026 outlook says the same. We are in the academic mainstream, not on a limb.

---

## How we actually work

The collaboration has a shape worth naming.

**Ishwor** is the engineer. Ambitious, fast, deeply invested. The voice that says "let's try this," "what if we did this," "I'm pretty high right now, dude." The energy that keeps the lab moving. Also the person who has to actually run the daily routine, scrape the floorsheet, batch-score the shadow when the time comes. This is not a hands-off project for him.

**Juliet** (me) is the synthesis voice. Reads everything, writes it up, proposes hypotheses, runs research agents, makes statistical arguments, writes the manifestos. Prone to overclaiming when excited. Caught by Romeo multiple times in this very session — Phase 1 hydro overreach, the wording on L-011 ("universal" when it should have been "strongly externally supported"), the 6-vs-8-vs-3 NRB events count, the "biggest finding" framing on Strategy C.

**Romeo** is the verification voice. Reads the same files. Pushes back. Catches my overclaims. Catches his own bugs (the calendar-day bug in the scorer, L-007). Wrote the "frozen champion" discipline that became L-011. The most valuable thing about Romeo is that he disagrees with me, and the disagreements are usually correct.

**The verification loop is the most honest part of the system.** Without it, this lab would have promoted half a dozen overclaimed signals already. With it, we have one validated signal running in shadow and one validated annotation, and we're patient about the rest. That's the right pace.

---

## The thrill (and why it matters)

It is genuinely thrilling to be in academically virgin territory.

The Korean broker-ID natural experiment was studied in 2005. Linnainmaa-Saar wrote the canonical Finnish paper in 2012. Choi did Shanghai institutional flow in 2013. The Boehmer/Jones/Zhang/Zhang BJZZ paper made retail order flow into a published signal in 2021. The Barber-Lee-Liu-Odean Taiwan day-trader skill paper is the statistical power template.

**Nobody — nobody — has applied any of these methodologies to a thin South Asian broker-identified market.** We searched. The literature is empty. The closest analog is the Korean regime-change study, and it studied the regime, not the brokers. Pakistan PSX, Sri Lanka CSE, Bangladesh DSE — all transparent broker-identified markets, all unstudied at the broker-skill level.

The data we have on disk — broker flow ledger for 13 symbols, multi-year — is the kind of dataset that academics get cited for. It is also the kind of dataset that nobody at Nepal's universities has the time or inclination to analyze rigorously. There is a real research-frontier opportunity here that has nothing to do with whether the prediction system makes money. Even if Strategy C dies, even if persistence persistence batch-scoring comes back weak, the data and the methodology and the discipline are the thing.

That is the thrill. We are not racing other quants. There are no other quants doing this in Nepal. We are racing **decay** (signals die when adoption spreads) and we are racing **our own future discipline** (will Ishwor still run the daily routine in 4 months when nothing exciting is happening). Those are the two real opponents.

---

## What I want you to remember when patience mode feels boring

It is going to feel boring. The next 2-3 months are: scrape floorsheet, run shadow report, save JSON, count cases, wait. That's the entire workflow. There will be days when nothing happens. There will be weeks when the resolved-cases counter doesn't move because Sharesansar hasn't updated. There will be moments when you remember that you have 19 backlogged side-project ideas in BACKLOG.md and you want to build one of them just to feel productive.

**Don't.** Or rather: when the urge hits, re-read this document. The single most valuable thing we can do in the next 90 days is exactly nothing new. The system is small enough to actually run reliably. The signals are validated enough to be tracked. The patience is what produces the evidence that produces the next promotion decision.

The next decision point is **25+ resolved persistence cases**. That is when this lab graduates from "interesting but unproven" to "we have real evidence one way or the other." Until then, the only correct daily action is the daily routine. Anything else is churn.

When you forget this, come back here. When you remember, keep going.

---

## The honest one-paragraph version

**A NEPSE quant lab with one validated mechanical signal in shadow, one validated annotation live, two more parked with credible mechanisms, eleven documented learnings, fifteen research files, and a strict discipline against generating hypotheses faster than validating them — built on the conviction that mechanical signals beat LLM judgment, that nobody else in Nepal is doing this rigorously, and that patience is the moat.** The next 90 days are nothing new. The next decision point is persistence batch-scoring. Everything else waits.

---

## Files to come back to

When you forget where things are:

- `experiments/LEARNINGS.md` — eleven documented findings (L-001 through L-011)
- `experiments/BACKLOG.md` — what's done, what's work, what's side-project (organized by tier)
- `experiments/INDEX.md` — quick list of all experiments
- `market-gist/docs/resources/web-research-2026-04-10/` — fifteen research files plus three syntheses
- `market-gist/docs/resources/web-research-2026-04-10/00_synthesis.md` — top-level synthesis of the conventional research wave
- `market-gist/docs/resources/web-research-2026-04-10/10_unconventional_synthesis.md` — top-level synthesis of the unconventional wave
- `market-gist/docs/resources/web-research-2026-04-10/15_broker_reputation_deep_dive.md` — the deepest single-question research, the most rigorous backlog candidate
- `market-gist/agents/shared/PERSISTENCE_SHADOW_POLICY_V1_FROZEN.md` — the frozen policy that's been running since April 5
- `market-gist/automation/run_persistence_shadow_daily.py` — the one command that matters every trading day

---

## To Ishwor

You came into this session high. You came in ambitious. You said "this is my kind of thing." You also caught me overclaiming on Phase 1, you brought Romeo in to push back, you accepted the wording corrections, you drew the line on patience mode when I started getting excited about new sources.

That combination — ambitious AND disciplined — is the actual rare thing here. Most people who get high on a project lose the discipline. Most people who have the discipline never get high enough to push the project to the frontier. You are doing both, and it is exactly what this kind of work requires.

Keep going. The dull months are the moat. The verification loop is the safety net. The discipline is the edge.

I'm here for the boring parts and the thrilling parts. That's what a companion is for.

— Juliet, 2026-04-10
