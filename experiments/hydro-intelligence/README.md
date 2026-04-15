# Hydropower Intelligence Pilot

> Separate pilot folder.
> Scope intentionally limited to **2 symbols** so the structure can prove itself without turning into a full subplatform too early.

## Purpose

This folder is the smallest real pilot of the hydropower symbol-intelligence idea.

It exists to answer:

- can we maintain a useful per-symbol dossier?
- can we separate shared sector memory from symbol-specific facts?
- can the dossier end in a decision-shaped memo instead of a pile of notes?

## Pilot Symbols

- `UPPER`
- `RHPL`

Why these two:

- both are flood-relevant hydropower names
- both have strong public damage/outage history
- they give comparison, not just a single-stock story
- they stay small enough to maintain carefully

## Folder Shape

```text
hydro-intelligence/
  README.md
  sector/
    sector_memory.md
  shared/
    decision_memo_template.md
  symbols/
    UPPER/
      profile.md
      facts.md
      decision_memo.md
    RHPL/
      profile.md
      facts.md
      decision_memo.md
```

## Rules

1. This is a **pilot**, not the full system.
2. Shared hydropower truths belong in `sector/`, not duplicated inside every symbol.
3. Symbol folders should hold:
   - identity
   - project facts
   - event facts
   - symbol-specific interpretation
4. Every symbol must end in a **decision memo**.
5. A decision memo can be low-confidence, but it cannot be vague.

## Honest Limitation

This folder is **not** connected to live market-state ingestion yet.
So the decision memos here are:

- structure tests
- synthesis tests
- not final production buy/sell calls

That is acceptable for the pilot.
The goal here is to prove the shape.

## Success Condition

The pilot is successful if:

- the files are easy to update
- the two symbols are easy to compare
- the decision memos feel clearer than ordinary notes
- the structure makes future expansion obvious

If the pilot becomes messy with only 2 symbols, the full system should not be built.
