# Single-Company Living Dossier — Definitions Contract (v0, FROZEN)

**Subject symbol**: `UPPER` — Upper Tamakoshi Hydropower Ltd. (sector: HYDROPOWER)
**Created**: 2026-05-17
**Status**: v0 — frozen contract. Written BEFORE any dossier is generated, so
its boundaries and language cannot later be loosened to flatter outputs.
**Scope**: a *contract*, not code. Defines what the dossier may assemble, from
which exact files, in what language, and the rules that keep it honest.

> This is a **second brain for manual trading**, not an auto-trading system and
> not a systematic-alpha experiment. The three prior systematic probes (broker
> labels, broker IC, calendar) closed without a confirmable edge; that path is
> closed. This dossier exists only to help Ishwor read ONE company faster and
> more honestly, and to keep an immutable record of his own judgment.

---

## 1. Purpose

Maintain a single, living, mostly-auto-assembled file about UPPER that lets
Ishwor, in a few minutes, see: recent price/volume behaviour, broker-flow
context, corporate actions, sector context — and record his own read and later
honestly check it. The dossier *organises information and memory*. It does not
decide, predict, or score.

## 2. Non-goals (hard boundaries)

The dossier must NEVER:

- Issue or imply buy / sell / hold / entry / exit / target / stop.
- State or imply an expected return, fair value, "cheap/expensive",
  "undervalued/overvalued".
- Claim or imply a systematic edge, backtest, or win-rate.
- Produce a score/rank that orders anything by expected profit.
- Use forward-looking verbs ("will", "should", "set to", "poised to").
- Compute the accuracy of Ishwor's past reads into a number used for position
  sizing or conviction. (Reviewing your own calibration qualitatively is the
  point; turning it into a signal silently reopens the closed alpha machine.)

If any section starts answering "what should I do with UPPER?" instead of
"what happened to UPPER and what did I think at the time?", that section is out
of contract and must be removed.

## 3. Subject & why this symbol

UPPER chosen as the NEPSE hydropower bellwether: richest event/news surface and
sector-reference behaviour (best learning substrate for a discretionary tool),
with a full dossier-grade data stack (OHLCV + ~389 floorsheet days + corporate
actions + sector tag). The contract is symbol-parametric: switching subject is
a single change here plus a new dossier file; the rules below are unchanged.

## 4. Data sources (exact paths) + coverage caveats

All sources are consumed **read-only**. Nothing here modifies data, the scrape
pipeline, the broker ledger, or the archived
`nepse-volume-psychology-lab/` (sealed; never read or reopened).

| Layer | Exact source | Coverage / caveat (must be self-disclosed in the dossier) |
|---|---|---|
| Daily OHLCV | `sharesansar_datascrape/data/MM_DD_YYYY.csv` (per-DATE files; filter `Symbol == UPPER`) | ~2021-01-03 → 2026-05-12, ~1,611 files. **NOT corporate-action adjusted** — ex-bonus/ex-rights days show artificial gaps; flag where a known book-closure exists. |
| Broker floorsheet (raw) | `market-gist/broker_flow_ledger/raw_merolagani/UPPER/YYYY-MM-DD.json` | ~389 trading days, ~2023-06-11 → 2026-05-07. **No broker flow before mid-2023**; not every trading day present. |
| Broker aggregates | `market-gist/data/validation/broker_flow_fact_table/` (CSV + `broker_flow_coverage_by_symbol.csv`) | Consume its **output** only; do not rebuild. Use coverage file to print a per-day coverage caveat. |
| Corporate actions | `market-gist/data/validation/historical_context_backfills/*corporate_action_timeline*.json` + `experiments/01-corporate-action/data/raw/UPPER/company-announcements.json` | 2023–2025, backfill (not live); symbol coverage uneven. Treat as historical context, not a complete registry. |
| Sector context | `market-gist/automation/sector_map.json` (UPPER → HYDROPOWER) | Sub-index *history* exists only in the archived lab (reference only, **not** pulled). Live sub-index level via NEPSE API accrues forward only. |
| News / announcements | NEPSE company-news archive JSONs + ShareSansar announcement JSONs (paths above) | **Backfill / historical only — NOT a live news feed.** Good for corporate-action context; never presented as breaking news. |

## 5. Auto-assembled vs human-written (the split is binding)

**AUTO (descriptive, machine-filled from §4, no judgement):**
- Price/volume snapshot & recent history for UPPER (reuse `cockpit/cockpit_lib.py`
  metrics scoped to UPPER — same frozen thresholds, no new tuning).
- Recent anomaly flags (volume/turnover/transaction/range) per the cockpit
  contract — descriptive, never ranked by profit.
- Broker-flow summary where coverage exists: top-buyer/seller concentration,
  net imbalance, persistence count — each with a coverage caveat.
- Corporate-action / announcement timeline (chronological list, verbatim).
- Sector tag + sector context note.

**HUMAN (Ishwor-written, append-only, immutable):**
- **"My daily read"** — one or two lines of his own hypothesis
  ("looks like absorption", "distribution into strength", "no opinion"),
  with date and a confidence word (low/med/high). Written *before* the outcome
  is known.
- **"Later review"** — written days/weeks later: what actually happened, and a
  one-line honest self-note. **The original read is never edited or deleted.**

## 6. Anti-self-deception rules (binding)

1. The human log is **append-only and immutable**. Entries are timestamped;
   originals are never rewritten after an outcome is known. Editing a past read
   to look smarter is the cardinal sin.
2. **No hit-rate → sizing.** Calibration is reviewed *qualitatively*
   ("I keep calling absorption that turns into dumps"). A numeric accuracy that
   feeds conviction or position size is forbidden.
3. **No outcome tuning.** Auto thresholds are inherited frozen from
   `cockpit/DEFINITIONS.md`. They are not re-tuned here; not because outputs
   "look better"; not to make a flag fire more/less.
4. The dossier **never ranks, sizes, or recommends**. It assembles and records.
5. Changes are CHANGELOG-gated (see §9): structural reasons only.
6. The dossier self-discloses its blind spots every time (§4 caveats + §7).

## 7. Language rules

- Mandatory header on every dossier render: *"Descriptive single-company
  record. No buy/sell advice, no return prediction, no edge claim. Human notes
  are Ishwor's own opinion logged for later honest review, not a signal."*
- Allowed: "was", "is", "resembles", "unusual vs its own 20-day history",
  "observation", "coverage caveat", "POSSIBLE …" (for the inherited cockpit
  resemblance tags only).
- Banned: buy, sell, hold, target, stop, entry, exit, undervalued, overvalued,
  cheap, expensive, opportunity, expected return, edge, signal, "will",
  "should", "set to", "poised to".
- Human sections are always clearly labelled as opinion logged for review, not
  analysis output.

## 8. Dossier file shape (the sections the living file will show)

1. **Header & disclaimer** (fixed text, §7) + symbol + render date + a
   data-coverage line (OHLCV through date X; floorsheet coverage %; corp-action
   data through year Y; news = historical-backfill-only).
2. **Company snapshot** — UPPER, HYDROPOWER, latest close, day Δ%, recent
   range; all descriptive.
3. **Price / volume** — recent N-day OHLCV summary + any inherited anomaly
   flags, with values.
4. **Broker notes** — where floorsheet coverage exists: concentration /
   imbalance / persistence, each with coverage caveat; "no coverage" stated
   plainly when absent.
5. **Corporate-action & announcement timeline** — chronological, verbatim,
   dated; backfill caveat shown.
6. **Sector context** — HYDROPOWER tag + brief descriptive sector note.
7. **My daily read** — append-only human log (date · read · confidence).
8. **Later review** — append-only human log (date · what happened · self-note),
   never altering §7 entries.
9. **Footer** — blind-spots reminder + fixed line: *"This file describes the
   past and records opinion. It does not predict, recommend, or claim an edge."*

## 9. Change-control rule (anti-overfitting, binding)

- Sections, sources, and inherited thresholds are **frozen**. Changes require a
  dated `CHANGELOG` entry with an explicit **structural** justification (a
  NEPSE rule change, a data-schema change, a new data source becoming
  available, or a definitional error).
- Never changed because output "looks better", to improve apparent calibration,
  or in reaction to how UPPER subsequently traded. That is outcome-driven
  tuning and is forbidden.
- New auto sections must be descriptive and non-forward-looking (pass §2).
  Removing an out-of-contract (drifted-to-advice) section is always allowed.

---

**End of v0 contract.** Next step (separate, on approval): a read-only
assembler that fills the AUTO sections for UPPER from §4 and leaves the HUMAN
sections as an append-only log. No code is written until this contract is
frozen. The lab archive and the scrape pipeline remain untouched.

## CHANGELOG
- 2026-05-17 — v0 created and frozen (pre-implementation contract; subject = UPPER).
