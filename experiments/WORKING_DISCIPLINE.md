# Working Discipline — Juliet's Self-Audit Log

> Written 2026-04-18 after Ishwor flagged a pattern of avoidable mistakes.
> Running log of concrete mistakes I've made on this project. Each entry has
> a date, what cost it, the rule that prevents it, and a specific check I can
> run in under 30 seconds.
> Pre-submit checklist at the bottom.
> Add a new entry whenever I notice myself making a class of error not yet logged.

---

## How To Use This Document

Every entry follows the same shape:

1. **What happened** — concrete, dated example.
2. **What it cost** — why it mattered, in real terms.
3. **Prevention rule** — a specific, actionable rule (not "be careful").
4. **Self-audit step** — a check I can actually run, fast.

At the bottom is a pre-submit checklist derived from the rules. I run it mentally before declaring work complete.

Generic wisdom is worthless here. "Be thorough" means nothing. "Grep the old revision number" means something.

---

## Mistake Patterns (Running Log)

### Pattern 1 — Metadata Drift On Revised Documents

- **What happened (2026-04-18):** Made three rounds of edits to `experiments/dividend-microstructure/PRE_REGISTRATION.md`. Each round bumped "Revision N" in my summaries, but the document's own title, commit-discipline section, and sign-off block kept saying "Revision 2" throughout. Romeo caught it on final review.
- **Cost:** Romeo blocks sign-off on an experiment that was otherwise ready. Days of work waiting on a 2-minute fix.
- **Prevention rule:** When revising a document and bumping a version number, grep the whole document for the old version string BEFORE declaring the revision complete. Replace every occurrence: title, headers, commit message template, sign-off block, cross-references.
- **Self-audit step:** Before saying "revision N is ready," run `grep -n "Revision N-1\|revision N-1" <file>`. Must return zero matches.

### Pattern 2 — Relative Paths After `cd` Lie

- **What happened (2026-04-18):** Claimed the 7 hydropower symbols had no Apr 14-17 broker flow ledgers. Used paths like `market-gist/broker_flow_ledger/<sym>/...`. But I was inside `market-gist/automation/` from an earlier `cd`, so the paths resolved to `market-gist/automation/market-gist/broker_flow_ledger/...` which doesn't exist. All 7 hydros actually had data; my check lied to me.
- **Cost:** Almost re-ran 4 days of scraping for data that already existed. Wasted time + user confusion + had to apologize.
- **Prevention rule:** For any file-existence or path-verification check, always use ABSOLUTE PATHS. Never trust the current working directory, especially after a previous `cd` or a background-process call.
- **Self-audit step:** Before running a file check, either use the full absolute path starting with `C:/Users/ishwor/...`, OR print `pwd` first to confirm working directory.

### Pattern 3 — Blindly Agreeing With External Reviews

- **What happened (ongoing across sessions):** Romeo returns a review with verdicts. I rewrite sections based on them without independently verifying the underlying claims. Works when Romeo is right, but builds a verification loop where the reviewer is never verified.
- **Cost:** Risk of cementing a WRONG claim into lab canon. Also erodes my own reasoning muscle.
- **Prevention rule:** For every claim in any external review (Romeo, Benvolio, research agents), run at least one independent check: verify cited files exist, re-run cited math, spot-check one example. State explicitly in my response what I verified and how.
- **Self-audit step:** In my response to any review, include a "What I verified independently" section. If that section is empty, I didn't do the work. Don't send.

### Pattern 4 — Statistical Language Without Running The Math

- **What happened (2026-04-18):** Reported the persistence signal hit rate as "still above chance" at 72.7% on N=11. Romeo pushed back. When I actually ran the test: one-sided binomial test vs 50% null gives p ≈ 0.11. NOT statistically significant.
- **Cost:** Overclaimed in a decision-grade context. If this were the actual batch-score promotion decision, it would have built a promotion case on noise.
- **Prevention rule:** Don't use words like "significant," "above chance," "statistically different" unless I ran the test myself OR can cite a test someone else ran. For N < 20, default to "directionally suggestive, not decision-grade."
- **Self-audit step:** Before writing "significant" / "above chance" / "statistically X," ask: did I run the test? If not, either run it or remove the word.

### Pattern 5 — Misreading `ls | tail` Output

- **What happened (2026-04-18):** Checked latest price CSVs with `ls sharesansar_datascrape/data/*.csv | tail -8`. Got back 12_31_2023 through 12_31_2025. Concluded "price data is 3.5 months behind." **Wrong** — `ls` sorts alphabetically, and "12_31" sorts after "04_17" alphabetically. Data was actually up-to-date through Apr 10.
- **Cost:** False alarm about data pipeline. Raised the "3.5 months missing" claim publicly. Had to walk it back.
- **Prevention rule:** For date-sensitive file listings, never use shell `ls | tail` without explicitly sorting by date. Use Python with `datetime.strptime` on the filename, or `ls -1 --sort=time`, or sort the list numerically.
- **Self-audit step:** Before claiming "latest" or "most recent" from any directory listing, verify the sort order was chronological not alphabetical.

### Pattern 6 — Answering Coverage Questions From Memory

- **What happened (2026-04-18):** User asked "did we scrape the hydros?" I first answered based on a broken check (Pattern 2) without enumerating the full set.
- **Cost:** False claim requiring corrective work.
- **Prevention rule:** When the user asks a coverage question ("did we do X?" / "did we cover all Y?"), ALWAYS enumerate the full set and check each element explicitly. Never answer coverage questions from memory or partial checks.
- **Self-audit step:** If user asks "did we do X for all Y?", write the full list of Y and mechanically verify each one.

### Pattern 7 — Stale Status/Next-Step Lines After Edits

- **What happened (2026-04-13, 2026-04-17):** After editing PRE_REGISTRATION.md and CONTRACT.md for the dividend-microstructure experiment, the `README.md` for the same folder still said "Pre-registration pending" and "Write PRE_REGISTRATION.md before any code is written." Romeo flagged these as stale.
- **Cost:** Confuses future readers about the actual state of the experiment.
- **Prevention rule:** When I modify any document in an experiment sandbox, refresh the "Status" / "Next Step" lines in the README and any CURRENT_VIEW document in the same session.
- **Self-audit step:** Before finishing a session that touched an experiment folder, read the folder's README.md and verify its status line matches actual state.

### Pattern 8 — Over-Writing The Session Without Consolidating

- **What happened (2026-04-18):** Built sandbox protocol + signal decay tracker + batch-score playbook + price_data_integrity + hydro pilot update + 16-CSV fix + shadow-report catch-up in one session. Lots of output. Didn't stop to write a session log or update LEARNINGS.md. Risk of context loss when Claude access ends.
- **Cost:** Potential orphan work — future sessions might not find the thread.
- **Prevention rule:** Budget 20% of any long session for consolidation: session log, LEARNINGS updates, INDEX refresh. Don't chain more than ~4 substantive deliverables without writing them up.
- **Self-audit step:** At the end of any session with 3+ deliverables, ask: can future-Claude or future-Ishwor find this work without my context? If not, stop and document.

### Pattern 9 — Writing The Discipline Instead Of Using It

- **What happened (2026-04-18):** Wrote `WORKING_DISCIPLINE.md` with 8 patterns and a pre-submit checklist in the morning. Wrote `reversal-specialist/PRE_REGISTRATION.md` revision 1 in the afternoon. **Never ran the pre-submit checklist against it.** Sent to Romeo, who caught 5 issues: calendar-vs-trading-day bug, corp-action contamination, regime-exclusion scope, return-construction ambiguity, circuit-limit operational definition. All five were the kind of issue a disciplined self-review would surface.
- **Cost:** Burned a Romeo cycle. With Claude time limited, each extra review round is 1-2 sessions of budget. Also: meta-embarrassment — the discipline document was written the same day as the discipline failure.
- **Prevention rule:** Writing discipline is not the same as running it. Before sending any pre-registration or revision to Romeo, perform an **adversarial self-review** using the pre-registration checklist below. If the checklist is empty or not applicable, I haven't thought about what Romeo will hammer on.
- **Self-audit step:** Run the pre-registration-specific checklist (below) before the word "Romeo" appears in an outgoing prompt.

---

## Pre-Registration Specific Checklist

Use this BEFORE sending any pre-registration (new or revised) to Romeo. General pre-submit checklist (above) is necessary but not sufficient; pre-regs have failure modes the general one misses.

- [ ] **Every threshold has a numerical implementation.** "Near the price limit" is not operational; "|daily_return| > 9.5%" is. For every qualitative phrase in the pre-reg, grep the code for the corresponding numerical check.
- [ ] **Code matches pre-reg semantically.** If pre-reg says "±5 trading days," code uses a trading-day counter, not a calendar-day approximation. Grep for `.days` attribute usage and verify it's appropriate context.
- [ ] **Exclusion rules handle unknown unknowns.** If the exclusion is hand-picked (e.g., known regime dates), add a data-driven filter too. Hand-picked is provenance; data-driven is operational.
- [ ] **Contamination from OTHER data sources.** If the experiment uses price data, is there any OTHER data source (corporate actions, macro events, calendar shifts) that could mechanically trigger the signal? Enumerate the candidates.
- [ ] **Return construction explicit.** For any test involving returns, state: close-to-close vs executable, which closes, which offsets, what happens on non-trading days.
- [ ] **Circuit-breaker / price-limit handling.** For any market with intraday price limits, exclude or tag triggers at the limit. If the limit changed during the window (e.g., NEPSE 10%→15% on April 17, 2026), handle the regime shift.
- [ ] **Scope: all time periods.** Any threshold or exclusion that only covers a recent time window (e.g., "2026 regime events") misses earlier historical events. Either broaden or add data-driven filter.
- [ ] **Romeo-imagination step.** Silently role-play Romeo reviewing this pre-reg. What's the first thing he'd flag? If the answer is "nothing," I'm not looking hard enough.

If any item is unclear or un-answered, fix BEFORE sending to Romeo. Romeo's time is cheap relative to a wasted review cycle.

---

## Pre-Submit Checklist

Run through this mentally before declaring work complete or asking for user/Romeo review.

- [ ] **Paths absolute.** Every file-existence / path check uses an absolute path, not relative.
- [ ] **Metadata consistent.** Every document I edited has consistent version numbers, dates, and status lines throughout.
- [ ] **Math shown.** Every statistical claim (significance, above-chance, hit rate) has visible math behind it or an explicit "descriptive only" caveat.
- [ ] **Sort order verified.** Any "latest" or "most recent" claim from `ls` was checked for sort order.
- [ ] **Scope enumerated.** Any coverage claim ("all X") was enumerated and individually checked.
- [ ] **Independent verification.** Any external review was accepted only after I checked at least one claim independently.
- [ ] **Status lines updated.** Any doc I touched has its status / next-step / date line refreshed.
- [ ] **Consolidation.** If the session produced 3+ deliverables, a session log exists.

---

## When To Add A New Pattern

Add an entry when:
- I catch myself making a mistake not already in the log.
- Ishwor or Romeo explicitly flags a mistake pattern.
- I notice a near-miss that could have become a real mistake if not caught.

Do NOT add generic lessons like "be careful" or "pay attention." Every pattern must have:
- A date
- A concrete example (symbols, file paths, exact wording)
- A cost statement (what it broke)
- A prevention rule (a specific action)
- A self-audit step (a thing I can check fast)

If a pattern can't be reduced to a 30-second check, I haven't thought hard enough about prevention.

---

## Meta-Rule

**This document is only valuable if I actually consult it.** Putting rules on paper doesn't enforce them. I will:
- Read this at the START of every session when I'm working on a non-trivial change
- Run the pre-submit checklist at the END, before handing work to the user or Romeo
- Add new entries as they come up, same session

If I go three sessions without referencing this document, it means I'm coasting on habit instead of discipline. Reset.
