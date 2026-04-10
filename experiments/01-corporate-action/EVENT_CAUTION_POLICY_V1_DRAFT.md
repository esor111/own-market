# Event Caution Policy v1 Draft

This document freezes the first corporate-action caution candidates that are
allowed to move forward from the standalone experiment lab into later shadow
testing.

Status: research-shadow only. Not approved for live trading.

## Purpose

Turn the strongest forward-actionable corporate event findings into explicit,
reproducible rules.

These are not prediction prompts. They are mechanical notice-reaction rules:

- see event notice
- apply caution window
- score later

## Frozen Rule Candidates

### 1. Book Closure Notice Caution

- Rule key: `book_closure_notice__announcement_date__drift_2_10`
- Event types included:
  - `book_closure_notice`
- Trigger date:
  - `announcement_date`
- Caution window:
  - next `10` trading days after the notice
- Experimental interpretation:
  - cross-sector caution candidate
  - strongest current corporate-action excess-downside signal

### 2. Dividend Family Caution

- Rule key: `dividend_family__announcement_date__drift_2_10`
- Event types included:
  - `dividend_notice`
  - `cash_dividend_notice`
  - `cash_dividend`
  - `bonus_and_cash_dividend`
- Trigger date:
  - `announcement_date`
- Caution window:
  - next `10` trading days after the notice
- Experimental interpretation:
  - bank-led caution candidate
  - useful only if later validation keeps confirming the bank edge

## Current Evidence Standard

Signals are worth later shadow promotion only if they keep all of these:

- enough cases to matter
- adjusted negative hit rate above baseline
- negative excess return
- statistically significant on the current experiment pass

## Current Research Read

### Book Closure Notice

- strongest forward-actionable corporate signal
- cross-sector across commercial banks and hydropower in current data
- still mostly confirmed in weak-market periods because the archive is regime-imbalanced

### Dividend Family

- forward-actionable
- strengthens when dividend-family notice types are pooled
- clearly bank-led in current data
- not yet confirmed in hydropower

## Promotion Rules

Before these move into any daily shadow overlay, they should pass:

1. exact family validation from raw experiment outputs
2. sector scope confirmation
3. duplicate-event handling check
4. event co-occurrence check with persistence cautions
5. explicit shadow output wording

## Non-Goals

- do not use AGM leakage signals directly for shadow deployment
- do not treat pre-event leakage as tradeable unless announcement timing itself becomes predictable
- do not claim bull-market validity yet
