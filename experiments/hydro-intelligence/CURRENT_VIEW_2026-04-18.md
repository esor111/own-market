# Hydropower Intelligence Pilot — Current View (2026-04-18)

> Refresh of the `CURRENT_VIEW_2026-04-13.md` snapshot after the Apr 14-17 data catch-up.
> 5 trading days of new tape. 3 shadow reports generated (Apr 15, 16, 17). UPPER anomaly intensified.

---

## Summary

| Symbol | Action | Confidence | Horizon | Short read (vs Apr 13 snapshot) |
|---|---|---|---|---|
| `UPPER` | `hold` | medium-low | medium | UNCHANGED stance; volume/transaction anomaly now stronger; Apr 15 price spike + reversal suggests two-sided contest, no clean direction |
| `RHPL` | `avoid` | medium | medium | UNCHANGED stance; tape stayed weak and thin across Apr 13-17; no catalyst materialized |

**No decision-memo change yet.** The observations below add context but do not flip either call.

---

## What Changed Since 2026-04-13

### UPPER

- **Broker-flow anomaly intensified.** Transaction count on Apr 15 hit **2,567** — roughly 6-10× the Dec 2025 baseline (260-437 rows) and about 2× the previous peak (Apr 13 = 1,369). See `symbols/UPPER/facts.md` for the full trend.
- **Brief price spike then reversal.** Apr 13 close = 217.00 → Apr 15 close = **224.50** (+3.46%) → Apr 16 close = 216.90 (-3.38%) → Apr 17 close = 217.00 (flat). Net 4-day change = ~0%. Daily volume on Apr 15 was ~2× the prior-week typical volume.
- **Interpretation:** the combination (extreme transaction count + 2× volume + brief price spike + near-full reversal) is a classic **failed-breakout / distribution-absorbed** pattern. It is NOT a clean accumulation read and NOT a clean distribution read — it looks like a two-sided contest. Consistent with the Apr 13 memo's framing that UPPER is "recovered operationally, no clean catalyst, hold not buy."
- **Shadow research lane on UPPER:** CAUTION research-only on Apr 15, 16, 17 (sell_w7 = 0.57, 0.86, 0.86). The research-lane persistence flag has been firing consistently alongside the transaction anomaly. Two different lenses pointing the same "be cautious about UPPER" direction.
- **UPPER-specific, not sector-wide.** Apr 15 peer hydros: API 1,373 / AHPC 1,226 / AKPL 1,137 — elevated but nowhere near UPPER's 2,567. Sector-rotation / monsoon / post-holiday-catchup explanations alone would lift the basket uniformly; they don't.

### RHPL

- **Tape stayed weak and quiet.** Close prices Apr 13-17: 295.00, 298.00, 292.70, 292.50. Daily volumes: 49K / 27K / 29K / 27K. Net 4-day change = -0.85%. No volume expansion, no breakout attempt, no capitulation.
- **First broker-flow data ever on RHPL.** Apr 13 = 227 rows, Apr 15 = 241, Apr 16 = 204, Apr 17 = 147. Very low relative to UPPER / API / AHPC. Matches the "weak participation" theme.
- **Interpretation:** the Apr 13 "avoid — incomplete recovery, weak tape" call is holding. No new information that would justify flipping to `hold` (which would require clear evidence of full 111 MW restoration plus tape improvement). No new information that would justify flipping to stronger `avoid` either (no fresh damage or delay). Sideways drift with slight downward bias.

---

## Tape Snapshot From Local Archive

| Symbol | Close Apr 17 | 5d change | 10d change | 20d change | Apr 15 volume ratio vs 20d avg |
|---|---:|---:|---:|---:|---:|
| `UPPER` | 217.00 | +2.12% | +1.17% | +1.40% | ~2.0× (spike day) |
| `RHPL` | 292.50 | -0.85% | -0.85% | -1.22% | ~0.6× |

(5d/10d/20d approximations computed from local archive; exact numbers may shift as more sessions roll in.)

---

## What Would Still Change The Calls (unchanged from Apr 13)

### UPPER (to promote to `buy`)

- AGM / capital-return clarity (AGM notice was Apr 12 — waiting for decision)
- Insurance clarity on the 1.8B claim
- Visible progress on remaining project / diversion issues
- Clean breakout with follow-through — Apr 15 was NOT this; it reversed

### RHPL (to soften `avoid`)

- Clear public confirmation of full 111 MW restoration
- Evidence of financial normalization (latest annual report still shows Rs 429.5M net loss)
- Improved price and volume behavior — the Apr 15 blip was not this

### Both

- Fresh severe company-specific negative (damage, delay, governance) would strengthen the bearish read

---

## Cross-Lab Notes (why this snapshot matters beyond the pilot)

- **UPPER's transaction-count anomaly is the most interesting isolated observation in the lab right now.** It spans multiple days, survives one reversal, is UPPER-specific (not sector-wide), and coincides with known catalysts (AGM notice, Nepali New Year, circuit-breaker widening). Worth watching closely but NOT worth acting on yet — the net price change is ~0% which means the market has already processed this activity without committing direction.
- **Persistence shadow research lane** has been firing CAUTION on UPPER since Apr 13. Four consecutive days of CAUTION (Apr 13, 15, 16, 17 — Apr 14 was closed). This is meaningful within the research-only lane but does NOT update the frozen v1 policy scope.
- **Cross-sector peer basket** (API, AHPC, AKPL, BHCL, RADHI) was also active across Apr 15-17 but without UPPER-scale anomalies. When the pilot expands beyond 2 symbols, these peers become the comparison set per Romeo's original design.

---

## Why This Snapshot Matters

This is the second pilot refresh. The first (Apr 13) established that the architecture produces real decisions — `hold` and `avoid`, with named conditions. This refresh (Apr 18) proves the architecture handles an evolving situation: new data arrives, observations update, but the decision stance only flips when invalidation conditions fire. It has not been flipped. That discipline is itself a useful signal — the architecture is not trigger-happy.

Next scheduled refresh: whenever UPPER's post-AGM decision is disclosed, OR when a new material fact (insurance, repair, RHPL restoration) lands. Not on a calendar cadence — event-driven.
