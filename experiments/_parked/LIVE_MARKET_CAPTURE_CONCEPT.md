# Live Market Capture Concept

> **Status:** Parked future architecture. Do not build yet.
> **Written:** 2026-04-19
> **Purpose:** Preserve the live-market-capture idea without letting it interrupt the current validation gates.

---

## One-Line Thesis

Live market capture is not primarily a new prediction engine. It is a future **execution-awareness layer**: a way to decide whether a signal is tradable right now, whether to wait, or whether the visible order book is warning us that the trade is unsafe.

Example:

- After-close broker flow says: "NABIL has persistent seller pressure."
- Live depth can later ask: "Are sellers breaking bids, or are bids repeatedly absorbing the sell pressure?"
- The first is a stronger exit warning. The second may mean patience.

That distinction cannot be seen from the daily floorsheet alone.

---

## Why It Is Parked

The idea is real, but the lab already has enough open fronts:

- Forward persistence evidence still needs the N=25 gate.
- Universe v2 is awaiting freeze/reject.
- The w7 seller-persistence replay/backfill is not closed.
- L-001 v2 corporate-action coverage is still only a plan.

Starting live capture now would widen the active surface before the current gates resolve. The correct move is to document the architecture and let independent agents research it without touching the running system.

---

## The Agent-Lab Framing

Ishwor's instinct is right: in the AI age, the lab should not be limited to one linear session. Multiple agents can work independently if each agent has a sealed lane.

The model:

- **Main lane:** Romeo/Codex protects the current validation gates, codebase integrity, and promotion discipline.
- **Juliet lane:** synthesis, scaffolding, research docs, and controlled implementation after review.
- **Benvolio lane:** outside exploration, web research, source discovery, critique, and completion reports.
- **Future specialist lanes:** source/legal researcher, market-microstructure researcher, data-schema designer, skeptical reviewer.

The rule:

**Agents may explore independently. They may not promote independently.**

Every independent agent must return a report, not a production change.

---

## What An Independent Agent Can Do Now

An outside agent can safely research live capture without touching the lab:

- Identify clean live market data sources: licensed API, vendor DOM, official TMS DOM.
- Check terms-of-service and legal/access constraints.
- Compare which platform exposes top-of-book, depth, tape, volume, turnover, and timestamps.
- Draft a field dictionary for a future capture file.
- Draft a pilot pre-registration.
- Produce screenshots or source notes if legally allowed.
- Write a completion report with uncertainties and blockers.

This is useful because it prepares the future layer while the main lane stays focused.

---

## What An Independent Agent Must Not Do

No side agent should:

- scrape live market data without explicit approval
- use credentials or authenticated TMS access
- build production code
- modify `market-gist/automation`
- modify canonical files directly
- claim predictive edge from screenshots or anecdotes
- expand the pilot beyond the locked design
- add the idea to `BACKLOG.md` as imminent work

If an agent wants to cross any of those boundaries, it must write a request for Romeo review first.

---

## Best Future Pilot

When greenlit, the first pilot should be deliberately small.

| Item | Decision |
|---|---|
| Symbol | NABIL |
| Duration | 5 trading days |
| Capture interval | 10 seconds |
| Source | Structured vendor DOM or licensed API |
| OCR | Fail condition, not fallback |
| Primary goal | Prove the microscope works |
| Prediction claim | Not allowed in Phase 1 |

Why NABIL:

- high tick density
- already active in the persistence-shadow lane
- cleaner comparison to existing broker-flow evidence
- less hydro-specific seasonality noise than UPPER

---

## Capture Fields

Minimum useful fields:

- timestamp
- symbol
- LTP
- cumulative volume
- cumulative turnover
- best bid price and quantity
- best ask price and quantity
- top 5 bid levels
- top 5 ask levels
- latest executed trade quantity if visible
- aggressor side if visible
- source platform
- capture status / gap flag

Displayed depth is intention. Executed trade tape is fact. The pilot should preserve both.

---

## First Two Behaviors To Label

Only two patterns belong in v1.

### 1. Absorption

Sustained selling appears in the tape, but the bid refills repeatedly and price holds.

Interpretation:

- sellers are active
- buyers are absorbing
- daily broker-flow weakness may be less immediately executable than it looks

### 2. Quote Fade / Spoof-Like Behavior

A large visible order appears, price or behavior reacts, and the order disappears before execution. The pattern repeats.

Interpretation:

- displayed depth may be fake pressure
- naive order-book reading may be dangerous
- execution should wait for trade confirmation

Do not add panic selling, fake breakout, liquidity vacuum, or retail-trap detectors in v1. Those are either regime states or higher-order interpretations. Build the microscope first.

---

## Phase Plan

### Phase 0 — Parked Research

Owner: Benvolio or another outside agent.

Output:

- source map
- legal/access notes
- field dictionary
- proposed pilot pre-registration
- no scraping
- no code

### Phase 1 — Microscope Pilot

Owner: Juliet after Romeo sign-off.

Question:

Can we capture clean structured live data and label absorption / quote-fade events reliably?

Success:

- capture completeness is acceptable
- at least 5 high-confidence labeled events across 5 days
- each event has depth + execution context where possible
- no predictive claim

Failure:

- source is unstable
- data cannot be structured
- events cannot be labeled consistently
- OCR is required

### Phase 2 — Baseline Comparison

Question:

Do labeled live events add information beyond after-close floorsheet signals?

Only after Phase 1 passes.

### Phase 3 — Execution Filter

Question:

Can live-capture labels improve trade timing for an already validated signal?

Only after an underlying signal has forward evidence.

---

## Revisit Trigger

Reopen this concept only after at least two of these close:

- forward persistence reaches N=25 and gets scored
- universe v2 is frozen or rejected
- w7 recent replay/backfill is completed or formally closed
- L-001 v2 coverage plan is executed or parked

Until then, only Phase 0 research is allowed.

---

## Completion Report Template For A Side Agent

An independent agent researching this must return:

- **Question researched:** what exact source/design issue was investigated
- **Sources checked:** URLs, platform names, access constraints
- **Fields available:** what the platform exposes cleanly
- **Fields missing:** what cannot be captured
- **Legal/access risk:** ToS, login, rate limits, credential concerns
- **Pilot implication:** whether the source can support Phase 1
- **Recommendation:** proceed / parked / reject source
- **Uncertainty:** what still requires direct observation

The report is input to Romeo. It is not permission to build.

---

## Core Reminder

The lab can use many agents.

But the hierarchy must stay clear:

- agents explore
- reports preserve
- Romeo verifies
- Juliet integrates
- forward evidence validates
- production changes only after gates

That is how independent intelligence becomes leverage instead of noise.

