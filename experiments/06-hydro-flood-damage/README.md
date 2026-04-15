# Experiment 06 — Confirmed-Damage Hydropower Event Study

> Status: structured, not yet run.
> Purpose: turn the hydropower flood idea into a clean symbol-by-symbol research lane.

## Core Question

When a **specific listed hydropower company's revenue-generating asset** is publicly confirmed damaged or forced offline by flood or landslide, does that stock underperform **undamaged listed hydropower peers** over the next few trading sessions or weeks?

This is **not** a generic "monsoon effect" study.
This is **not** a basin-only study.
This is a **damage-confirmed company-level event study**.

## Why This Exists

The UPPER sanity check kept the idea alive, but narrowed the claim:

- there is **some** evidence of post-damage weakness
- the effect was **not** a clean instant [0, +10] rule
- the better frame is "named damage to a listed hydro asset" rather than "floods are bad for hydros"

The note that established this is:

- `experiments/UPPER_FLOOD_SANITY_CHECK_2024.md`

## What Counts as an Event

An event starts when there is a **first credible public report** that:

1. names a specific listed hydropower company or project
2. confirms physical damage and/or forced outage
3. is public enough that the market could react to it

Acceptable anchor sources:

- Kathmandu Post
- OnlineKhabar
- ShareSansar
- myRepublica
- IPPAN statements quoted in reputable media

What does **not** count as the anchor:

- generic rainfall warnings
- basin-level flood alerts with no listed company named
- later retrospective articles if an earlier named report exists

## Trading-Calendar Integrity

All event windows must use the true NEPSE session regime for the date range:

- **Sun-Thu**: default regime before June 15, 2022
- **Sun-Fri**: June 15, 2022 through late Bhadra 2079
- **Sun-Thu**: from Ashoj 2079 onward
- **Mon-Fri**: from April 10, 2026 onward

Why this matters:

- event studies fail quietly when session calendars are wrong
- flood windows are short, so even one fake session can distort the result
- the exact 2022 reversion note should stay precise, not fuzzy

## Build Order

### Step 1. Symbol registry

Create one row per listed hydro symbol in:

- `data/hydro_symbol_registry.csv`

The registry is the universe definition. It tells us:

- which companies are single-project vs multi-project
- which names are clean treatment candidates
- which names are clean controls
- which basin / project mapping each ticker belongs to

### Step 2. Event table

Create one row per **ticker-event** in:

- `data/flood_damage_event_table.csv`

This is not one row per flood.
It is one row per **listed hydro affected by a flood-related event**, plus optional control tags.

### Step 3. First-pass scoring

For each event row, compute:

- event-day return
- [0, +5] return
- [0, +10] return
- [0, +20] return
- slower drift window if needed
- relative performance vs undamaged hydro controls

### Step 4. Only then decide design strength

Possible outcomes:

- no effect -> kill the lane
- only slow drift -> keep as medium-horizon context lane
- consistent short-window underperformance -> promote to a real experiment

## Design Rules

1. **Treatment must be damage-confirmed.**
   Do not use rainfall alone.

2. **Use peer-relative comparisons.**
   Damaged hydros vs undamaged hydros is the core control.

3. **Prefer single-project companies when possible.**
   Multi-project companies dilute the signal.

4. **Do not overclaim short windows.**
   The UPPER sanity check suggests the market may process the damage more slowly than a textbook event study assumes.

5. **Track severity explicitly.**
   Minor road blockage is different from a multi-week plant outage.

## Minimum Success Standard

This lane is worth keeping only if at least one of these survives:

- repeated damaged-vs-undamaged underperformance in [0, +5] or [0, +10]
- repeated medium-horizon lag in [0, +20] or later drift windows
- stronger effects in severe-outage cases than mild-damage cases

If nothing survives, the lane becomes a dead end and should be documented honestly.

## Files In This Folder

- `README.md` — operating note for the lane
- `data/hydro_symbol_registry.csv` — symbol-by-symbol universe registry
- `data/flood_damage_event_table.csv` — event-by-event build sheet

## Current Honest Status

- The idea is **mechanistically credible**
- The UPPER case says it is **not fake enough to kill**
- The lane is **not yet validated**
- The next move is **data structure first, not conclusion first**
