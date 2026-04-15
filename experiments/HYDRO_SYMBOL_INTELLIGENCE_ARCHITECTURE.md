# Hydropower Symbol Intelligence Architecture

> Design doc only.
> This is a saved architecture for later scaling, not an active build commitment.
> Written so the idea survives without silently becoming a distraction project.

## Status

- **State:** parked architecture
- **When to build:** after the current core validation gates fire and after a single-symbol template proves useful
- **Immediate use:** conceptual guide only

## Why This Exists

The raw idea is powerful:

What if each important hydropower stock had a living intelligence system around it?

Not just price history.
Not just a folder of notes.
But a system that continuously organizes:

- company facts
- project facts
- weather and flood exposure
- policy context
- corporate actions
- market behavior
- news flow
- derived signals
- current decision stance

That idea is worth preserving.

But the full version is a **project**, not a side quest.
So this file captures the architecture without pretending we should build all of it right now.

## The Core Goal

Build a per-symbol intelligence layer that improves the actual decision question:

- should I buy this stock?
- should I avoid this stock?
- if I hold it, should I keep holding it?
- when should I sell?

This is not an academic archive.
It is a decision-support architecture.

## The Right Unit

Not one giant folder for one stock.
Not the entire hydropower universe at once.

The right build order is:

1. **Shared sector memory**
2. **Small basket of symbol dossiers**
3. **Decision synthesis layer**

Recommended pilot basket:

- `UPPER` — deepest damage-tested symbol
- `RHPL` — flood-sensitive peer
- `API` or `AKPL` — cleaner liquid hydro benchmark
- 1-2 cleaner controls

This is better than one symbol alone because comparison is where insight becomes visible.

## The Four-Layer Data Model

Every important fact should flow through the same ladder:

### 1. Raw source

Examples:

- article
- filing
- weather bulletin
- corporate-action page
- price record
- broker-flow row

### 2. Structured fact

Examples:

- damage confirmed
- outage started
- AGM announced
- dividend declared
- promoter sold shares
- project restart reported

### 3. Derived feature

Examples:

- severe damage event
- seasonal tailwind active
- post-flood recovery candidate
- dividend-window support
- structurally weak technical profile

### 4. Decision implication

Examples:

- avoid early entry
- buy only after repair confirmation
- hold through dividend window
- sell if event drift breaks

This is the load-bearing architecture.
Without it, the system becomes a note pile.

## The Three Layers of the System

### A. Sector layer

Shared hydropower memory that every symbol inherits.

Examples:

- AGM/dividend cycle
- rainfall and flood context
- dry-season generation constraints
- NEA arrears / payment stress
- PPA / take-and-pay policy
- hydrology / basin structure
- sector seasonal behavior

### B. Symbol layer

Deep dossier for each stock.

Examples:

- company identity
- project identity
- basin / river / district
- single-project vs multi-project
- outage and repair history
- project-specific news timeline
- shareholder and promoter context
- corporate-action history
- price / volume / event behavior

### C. Decision layer

This is the part that matters most.

Each symbol should end in a forced decision output, not endless context.

Required fields:

- current stance: `buy` / `avoid` / `hold` / `sell`
- horizon: short / medium / seasonal
- confidence level
- top 3 reasons
- top 3 risks
- what would invalidate the view
- what would flip the decision
- next review date

If the system cannot produce this layer, it is incomplete.

## Agent-Team Design

If multi-agent specialization is used later, split by function:

### 1. Asset / project team

Tracks:

- project outages
- damage reports
- restoration progress
- generation-impact facts

### 2. Corporate / shareholder team

Tracks:

- promoter context
- AGM / dividend / rights issues
- capital raises
- financing and governance changes

### 3. Market behavior team

Tracks:

- price structure
- volume behavior
- peer-relative moves
- seasonal context
- event-window drift

### 4. News / narrative team

Tracks:

- what the market is being told
- when it was told
- whether the narrative is changing

### 5. Skeptic / verifier team

Checks:

- source quality
- anchor-date correctness
- duplicated claims
- overclaim risk
- false precision

### 6. Orchestrator / synthesis layer

Combines the above into the current symbol memo and decision stance.

## Minimal Folder Shape

If this is eventually built, the smallest sane structure is:

```text
experiments/
  hydro-intelligence/
    sector/
      sector_memory.md
      sector_events.csv
      sector_features.csv
    symbols/
      UPPER/
        profile.md
        raw_sources/
        facts.csv
        features.csv
        decision_memo.md
      RHPL/
      API/
      AKPL/
```

Important:

- raw material and interpreted output should be separated
- every symbol should have one current `decision_memo.md`
- sector memory should not be duplicated inside each symbol folder

## Recommended Build Sequence

### Phase 0. Save the architecture

Do now.
That is what this file is.

### Phase 1. Prove the template on one symbol

Build one proper `UPPER` profile using the 4-layer model.

Success condition:

- the template feels useful
- it ends in a real decision memo
- it reduces confusion instead of increasing it

### Phase 2. Expand to a small basket

Add:

- `RHPL`
- `API` or `AKPL`
- 1-2 controls

Success condition:

- comparison creates better insight than single-symbol reading

### Phase 3. Only then consider the full multi-agent system

Do not build the full cathedral before the brick stands.

## Why This Is Parked

This architecture is good.
It is also expensive.

If built too early, it becomes exactly the kind of exciting infrastructure detour the doctrine warns about.

That is why the rule is:

- **document now**
- **template next**
- **full system later**

## Relationship to Current Work

This architecture should not replace the current hydro flood lane.

Current hydro flood lane:

- tests whether named damage creates peer-relative underperformance
- uses small structured tables
- aims to reduce uncertainty about whether a real signal exists

This architecture:

- is a future operating system for symbol-level intelligence
- sits above validated lanes
- should absorb validated findings later, not leap ahead of them now

## Bottom Line

The architecture is worth keeping.
The timing matters.

The right reading is:

**Romeo designed the cathedral. Juliet is right that we should save the blueprint now, prove one brick later, and only build the full thing after the current lab earns that complexity.**
