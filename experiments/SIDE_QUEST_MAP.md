# Side Quest Map

> Working map for parallel exploration.
> This is [PARALLEL_EXPLORATION_SERIAL_PROMOTION.md] applied to the current lab.
> Short version: search wide, verify hard, promote narrow.

---

## Portfolio Balance

At any given time, the lab should try to hold this balance:

- **1 market-structure quest**
- **1 culture/behavior quest**
- **1 truth-discipline quest**
- **1 gated heavyweight in reserve**

If all four slots are already conceptually filled, new side quests should wait.

---

## Now

These are the best research-only side quests to run without touching the production lane.

| Quest | One-line description | Connects to | Layer | Owner |
|---|---|---|---|---|
| Festival / Dashain-Tihar-election effects | Test Nepal-specific calendar windows for repeatable market behavior. | `BACKLOG.md` C6 | exploration | Benvolio |
| Transcript extraction pilot | Pilot 5 trader transcripts for sentiment, broker mentions, and market-structure clues. | `TRANSCRIPT_EXTRACTION_PLAN.md` (adjacent to `BACKLOG.md` Tier E sentiment ideas) | exploration | Juliet |
| Lab self-audit | Re-check the lab's strongest claims, wording, and benchmarks before they harden into doctrine. | `BACKLOG.md` C5 | verification | joint |

---

## Next

These are worthwhile, but should queue behind the `Now` set so we do not widen the active surface too fast.

| Quest | One-line description | Connects to | Layer | Owner |
|---|---|---|---|---|
| Day-of-week / schedule-regime replication | Characterize weekday patterns across NEPSE schedule regimes using our local data; primary value is pipeline calibration and regime-change analysis, not signal hunting. | Benvolio `06_day_of_week_validation.md`, `RESOURCES.md` Nepal calendar papers | exploration | joint |
| Hydro flood-damage event study | Structure a listed-hydro symbol registry and damage-confirmation event table, then test damaged names vs undamaged hydro peers. | `UPPER_FLOOD_SANITY_CHECK_2024.md`, Benvolio `12_monsoon_flood_hydro_watershed_study.md` | exploration | joint |
| Broker reputation feasibility spike | Test whether broker-level or broker-type-level persistence is stable enough to justify a full experiment. | `BACKLOG.md` A0 Track A | exploration | joint |
| Insider-pipeline detection | Check whether the same brokers repeatedly position ahead of public corporate-action events. | `BACKLOG.md` A0 Track B | exploration | joint |

---

## Later

These are real projects, but they either depend on future timing, more evidence, or more implementation effort.

| Quest | One-line description | Connects to | Layer | Owner |
|---|---|---|---|---|
| NRB event patch | Add the missing NRB dates and re-run Experiment 03 with the corrected event table. | `BACKLOG.md` A1 | exploration | Juliet |
| Public debt ownership signal | Test whether banks shifting in or out of T-bills predicts NEPSE liquidity and direction. | `BACKLOG.md` A2 | exploration | Benvolio |
| ICRA rating actions lane | Build a new event-study lane for Nepal credit rating upgrades and downgrades. | `BACKLOG.md` A3 | exploration | Juliet |
| Strategy C forward watchlist | Track AGM/dividend/policy conditions ahead of the Nov 2026 hydro window. | `BACKLOG.md` A4 | validation | Juliet |
| Personal NEPSE data API | Wrap the data assets in a local interface so future work reads one source of truth. | `BACKLOG.md` B2 | exploration | Juliet |
| Hydropower symbol intelligence system | Shared sector memory plus per-symbol dossiers and forced decision memos for a small hydro basket. | `HYDRO_SYMBOL_INTELLIGENCE_ARCHITECTURE.md` | exploration | joint |

---

## Do Not Touch Yet

These are explicitly parked. Some are bad fits. Some are good ideas at the wrong time.

| Quest | One-line description | Connects to | Layer | Owner |
|---|---|---|---|---|
| Specialist LLM agents | Re-architect the agent layer into specialists and an orchestrator. | `BACKLOG.md` Tier D | validation | joint |
| Raw text context for LLM predictions | Use unstructured text to improve the prediction lane directly. | `INDEX.md` 05, `BACKLOG.md` Tier D | validation | Juliet |
| Large social scraping builds | Reddit / Twitter / Facebook / TikTok sentiment pipelines. | `BACKLOG.md` Tier D and Tier E | exploration | Benvolio |
| Big infrastructure moonshots | Full NEPSE floorsheet archive, broker graph, or other large-scale builds before current gates fire. | `BACKLOG.md` Tier E | exploration | joint |

---

## Reading Rule

- **Now** = safe to explore as research-only
- **Next** = queue, do not activate all at once
- **Later** = good ideas, wrong moment
- **Do Not Touch Yet** = deliberately parked until evidence or priorities change

If a side quest does not fit this map, it should not silently start.
