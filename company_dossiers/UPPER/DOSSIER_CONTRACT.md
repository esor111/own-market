# UPPER — Single-Company Dossier Contract (v0.1, FROZEN, SPEC-ONLY)

**Subject**: `UPPER` — Upper Tamakoshi Hydropower Ltd. (sector: HYDROPOWER)
**Created**: 2026-05-17 · **Status**: v0.1 spec, frozen before any v0.1 code.
**Supersedes**: `dossier/DOSSIER_DEFINITIONS.md` v0 (kept for history). The
read-only data layer `dossier/dossier_data.py` is REUSED unchanged.

> **Framing — read before anything else.**
> This is a **discretionary decision-support dossier for ONE company.**
> It is **NOT** a prediction engine. It is **NOT** a re-run of the failed
> accumulation/distribution pilot (Pilot 1 already tested those labels as
> predictors — they did **not** beat plain price/volume; that question is
> closed). Here such labels are **descriptive observations only**, to help a
> human reason — never a signal, score, or call. The value is depth of
> context + decision discipline, not an edge claim.

Why UPPER (not switched): verified data supports it well — OHLCV from
2021-09-01 (~1,611 trading days), broker flow 2023-06-11→2026-05-07
(336 covered days, 92 brokers), 92 corporate events. It is the hydro
bellwether. No data reason to prefer API/AKPL over it for a first dossier.

---

## 1. Purpose

- Help Ishwor understand ONE company deeply.
- Build market memory, context, and decision discipline around it.
- Strictly: **no buy/sell calls, no expected return, no alpha/edge claim.**
- Success = "did this help Ishwor think more clearly and honestly about
  UPPER" — never a P&L or accuracy score.

## 2. Company Context  *(human-curated; NOT auto-generated, NOT from model memory)*

A one-time curated page, updated only on real events. Every field is filled
from a **primary source with the source noted**; unknown fields stay marked
`[unverified]` rather than guessed. Fields:

- Business model (run-of-river hydro; revenue mechanics).
- Hydro type / installed capacity / units & status.
- PPA terms / NEA off-take & payment-delay exposure.
- Debt / finance cost (if disclosed) — else `[unverified]`.
- Promoter lock-in status / free float.
- Dividend / bonus / right-share / AGM / quarterly-result history
  (seeded from `dossier_data.corporate_actions("UPPER")`, then
  human-verified).
- Monsoon / hydrology / operational & regulatory risks.

**Rule:** no fabricated financials. If it isn't in a cited document or the
data layer, it is `[unverified]`.

## 3. Daily Market Read  *(auto-assembled, descriptive)*

From `dossier/dossier_data.py` (read-only) + frozen `cockpit/` metrics
(inherited thresholds, no new tuning):

- Price / volume / prev-close / day Δ%.
- Relative volume (vs own 20-day median) + turnover/transaction shock.
- Range / candle behaviour (range% vs own median; close location in range).
- Broker flow where coverage exists: top buyers/sellers, top-5 buy/sell
  concentration, net leader, current net-side persistence streaks.
- Sector context (HYDROPOWER tag; descriptive note).
- Market context (breadth from the cockpit layer).
- News / announcements (historical-backfill caveat shown).
- A coverage line every render (OHLCV not corp-action adjusted; broker flow
  only from 2023-06; news historical-only).

## 4. Pattern Notes  *(observation, not prediction)*

Allowed labels, each defined by a FIXED descriptive condition (reusing
cockpit metrics) and each printed with the mandatory suffix
**"— observation, not prediction"**:

- `accumulation-like`
- `distribution-like`
- `panic-like`
- `absorption-like`
- `liquidity-vacuum-like`

These are *shapes to look at and reason about*, never a reason to act.
**Pilot-1 callback (binding):** these labels were already tested as
forward-return predictors and failed. They appear here ONLY as descriptive
context. Treating any label as "therefore it will move" re-opens a closed,
failed experiment and is forbidden.

## 5. Chart + Event Casebook

- Render **price + volume from local data** (reuse `scripts/render_volume_chart.py`
  pattern; our own clean data, not a scraped chart site).
- Overlay markers: announcements, AGM, dividends, bonus/right shares, the
  largest-volume days, and high broker-concentration days.
- **Mechanical case selection (no memory, no cherry-picking):** cases are
  exactly — (a) every dividend/bonus/right/AGM/result date from the events
  list; (b) the N largest single-day volume-spike days by a fixed rule;
  (c) every day a fixed broker-concentration threshold is crossed. Each case
  shows what price/volume/broker-flow *did*, with an explicit
  "historical context, not a rule; tiny sample" caveat.

## 6. Thesis Journal  *(human, append-only, immutable)*

Each entry, written **before** the outcome is known, must include:

- **What I see** (one or two lines).
- **Why it matters.**
- **What would prove me wrong** (defined in advance — invalidation).
- **Risk level** (low / med / high).
- **Revisit date.**
- **Later review** (added on revisit; the original entry is never edited).

Calibration is reviewed *qualitatively* ("I keep mislabelling X"). It is
**never** turned into an accuracy number that feeds conviction or sizing.

## 7. Guardrails (binding)

- No expected return, fair value, or price target.
- No "this means buy / sell / hold."
- No tuning of any label or threshold based on how UPPER subsequently traded
  (outcome-driven tuning forbidden; CHANGELOG-gated, structural reasons only).
- No hit-rate / accuracy scoreboard, ever.
- No expansion to more symbols until ONE dossier has been genuinely useful
  to Ishwor for **2 continuous weeks** (self-assessed, qualitatively).
- Banned words in any rendered output: buy, sell, hold, target, stop, entry,
  exit, undervalued, overvalued, cheap, expensive, opportunity, expected
  return, edge, signal, "will", "should", "poised to".
- Read-only: never modifies data, the scrape pipeline, the broker ledger,
  or the archived `nepse-volume-psychology-lab` (never touched).

## 8. First 7-day plan

| Day | Deliverable | Boundary |
|---|---|---|
| 1 | This contract (frozen) | spec only — DONE on commit |
| 2 | Company-context page (§2), human-curated, sources cited | no fabricated data |
| 3 | Local price+volume chart with event markers (§5) | render from local data only |
| 4 | Daily broker/volume read template (§3) | reuse dossier_data + cockpit; no new tuning |
| 5 | First historical event case (§5), mechanically selected | no cherry-picking |
| 6 | First real daily read + first thesis-journal entry (§3/§6) | append-only, immutable |
| 7 | Honest review: did this help Ishwor think better? | qualitative only; no P&L/accuracy metric |

Day 7 is a genuine go/no-go: if it did not measurably help thinking, we
stop and reconsider — not expand.

---

## Change-control

Sections, labels, thresholds are **frozen**. Changes require a dated
`CHANGELOG` entry with a **structural** justification (NEPSE rule change,
data-schema change, new data source, or a definitional error) — never
because output "looks better" or in reaction to UPPER's price. New auto
sections must be descriptive and non-forward-looking. Removing a section
that drifted toward advice is always allowed.

## CHANGELOG
- 2026-05-17 — v0.1 created and frozen (spec only; subject = UPPER;
  supersedes dossier/DOSSIER_DEFINITIONS.md v0; reuses dossier_data.py).
