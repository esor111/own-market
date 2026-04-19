# Live Market Capture — Phase 0 Research Report

> **Status:** Phase 0 completion report. Parked concept remains parked.
> **Date:** 2026-04-19
> **Author:** Benvolio lane (outside research agent)
> **Reads from:** `_parked/LIVE_MARKET_CAPTURE_CONCEPT.md`
> **Reports to:** Romeo review (not a build permission)

---

## Question Researched

For the parked Live Market Capture concept — NABIL, 5 days, 10-second snapshots, absorption + quote-fade labeling — what are the realistic data sources, what fields do they actually expose, what legal/access constraints apply, and can any of them support Phase 1 cleanly if/when the parking gates close?

Secondary: can anything from the parked concept be started earlier using **existing** `own-market` data (daily OHLCV + floorsheet + broker-flow ledgers) without opening a live-capture surface?

---

## Sources Checked

### Official NEPSE
- `https://www.nepalstock.com/` — public site, HTML front.
- `https://newweb.nepalstock.com.np/api/nots/...` — reverse-engineered JSON API. Auth: rotating `Salter <token>` computed client-side from `/authenticate/prove` response.
- NEPSE official Data Usage Procedure, 2077 (2020) — licensed paid API. Advertised <30s delay. Fees per applicant class (individual / institution / news portal / data vendor / foreign researcher). Exact rates only in NEPSE PDF, not public. Application via NEPSE System Operations Dept. Sources: ShareSansar news 2020-12-27, 2022-09-27, 2022-11-07.

### Authorized vendors
- **SmartWealth MDP** — `data.smartwealthpro.com`, docs at `/documentation/`, API base `mdpapi.smartwealthpro.com`. NEPSE-licensed. Endpoints: Market Status, Indices, Sub-Indices, Stock Live, Today Price, Floorsheet, IPO/FPO, Dividend, Rights, Bonds, Auction, M&A, AGM/SGM, Financial Reports. Headers: ApiKey, ApiSecret, AccessId, ApiVersion. Pricing gated behind quote. No L5 depth advertised in public docs.

### TMS (broker trading system)
- `tms01.nepsetms.com.np` … `tms58.nepsetms.com.np` — NEPSE-operated, branded per broker. Post-login exposes **L5 depth**, per-symbol floorsheet with broker IDs, 1–3s polling. No native export. Captcha on login. ToS explicitly prohibits scraping.
- Community TMS extensions (e.g. Suraj Rimal's TMS extension at `surajrimal.dev/tmsextension`, captcha OCR extensions `arpandaze/tms-captcha`) — client-side injection into the user's own logged-in session.

### Third-party data sites
- **Chukul** — `chukul.com` — only site with true intraday broker analytics + post-close accumulation/distribution per broker. Freemium, paid tiers priced per user. No public API.
- **NepseAlpha** — `nepsealpha.com` — broker-by-stock holding time series, floorsheet history, Floorsheet Bot alerts. Cloudflare-protected. No documented API.
- **ShareSansar** — floorsheet + daily OHLCV HTML, scrapeable (already used by `own-market/sharesansar_datascrape/`). No public API.
- **Merolagani** — `merolagani.com/Floorsheet.aspx` — scrapeable floorsheet mirror (already used by `own-market/market-gist/broker_flow_ledger/`).

### Unofficial libraries (GitHub, 2026)
- `basic-bgnr/NepseUnofficialApi` — Python, v0.6.2 released 2026-03-11. Async + sync, CLI, Salter auth. Includes floorsheet, market depth, supply/demand. Most current.
- `surajrimal07/NepseAPI-Unofficial` — REST + WebSocket + MCP wrapper. Endpoints `/LiveMarket`, `/Floorsheet`, `/SupplyDemand`, `/PriceVolume`. 30s cache. "Educational only, commercial use prohibited."
- `dahsameer/nepse-api-document` — docs for Salter auth (archived 2023-06-25, still accurate as base reference).
- Stale: `CaffeineDuck/nepse-api`, `Aabishkar2/NepseAPI`, `samrat/nepse-data`.

### Microstructure references
- Trading hours: pre-open 10:30–10:45, continuous 11:00–15:00, close 15:00–15:05. Days Mon–Fri (recent shift).
- Circuit: stock band ±10% (clip, no halt). IPO day-1 ±50%. Index halts widened April 2026: 5%/15-min morning, 8%/rest-of-day afternoon. Pre-open band widened to 5%. Pending NEPSE operational directive.
- **24-hour order placement went live April 2026** (Kathmandu Post 2026-04-16). Overnight queues are now materially larger.
- Odd-lot orders visible in market depth since July 2025.
- Block trade threshold: 10,000 units, separate manual window, bypasses order book.
- Short selling: not operational as of April 2026.
- Settlement: T+2.
- Typical daily turnover 2025: record Rs 21B (July), normal Rs 7–10B active days.

---

## Fields Available

### From `basic-bgnr/NepseUnofficialApi` (public JSON, free)
- `symbol`, `ltp`, `open`, `high`, `low`, `close`, `prev_close`
- `cumulative_volume`, `cumulative_turnover`, `num_trades`
- **`supplyDemand`** endpoint exists. Level count not verified empirically — treat as **L1 confirmed, L3 possible, L5 unlikely**. Must probe on day one before building detectors.
- Floorsheet: `contract_no`, `symbol`, `buyer_broker`, `seller_broker`, `quantity`, `rate`, `amount` — confirmed per community docs and already validated in `own-market/market-gist/broker_flow_ledger/`.
- Refresh: ~30–60 s polling, not streaming. Below 30 s risks WAF throttle.

### From TMS (broker login, not for this project)
- **L5 depth**, live spread, aggressor side inferable, 1–3 s updates.

### From SmartWealth MDP (paid, licensed)
- Real-time claimed, depth levels unadvertised. Floorsheet present. Redistribution per license.

---

## Fields Missing

- **L5 depth** on the free path. The parked concept's "top 5 bid / top 5 ask levels" field is likely not capturable from the public JSON API. Pilot design must either accept L1/L3 or route through TMS (not allowed under this lab's constraints) or SmartWealth MDP (paid).
- **Explicit aggressor side** (buy-initiated vs sell-initiated). Must be *inferred* from tick direction and trade location relative to mid. Not a clean field.
- **Sub-10-second cadence** without triggering Cloudflare/WAF. 30 s is the practical floor for the free path.
- **Historical intraday depth snapshots.** No third party archives these. Whatever Phase 1 captures is the archive.
- **True streaming feed.** All paths are polling.

---

## Legal / Access Risk

| Path | Risk | Notes |
|---|---|---|
| `basic-bgnr/NepseUnofficialApi` against public JSON | Medium | NEPSE ToS historically forbids automated access. Enforcement is WAF rate-limiting, not legal action. Dahsameer repo archived 2023 with "may change" warning. Library keeps shipping salt-function patches, implying NEPSE breaks auth periodically. |
| TMS scraping | **High — prohibited** | Explicit ToS violation, captcha gate, broker-credential required. **Out of scope for this lab regardless of parking gates.** |
| SmartWealth MDP | Low | Licensed redistribution. Costs money; pricing via quote. |
| NEPSE official license | Low | Paid, formal application, slow. Fees only in PDF. Redistribution-grade. |
| Third-party sites (Chukul, NepseAlpha) scraping | Medium | Cloudflare-protected. No public API. Same risk class as scraping NEPSE directly. |

Two additional risks worth flagging:
1. **Salt-function breakage:** NEPSE has broken the Salter token algorithm at least twice (2021, 2022). If Phase 1 runs during a break, capture halts until the community patches the library. Build a break-detection alarm into any future poller.
2. **24-hour order placement (new April 2026)** changes pre-open dynamics. Any pre-open volume baseline derived from pre-2026-04 data is stale.

---

## Pilot Implication

**Can the free path (`NepseUnofficialApi`) support the parked Phase 1 pilot as written?**

Partially. Concrete adjustments needed:

1. **Cadence:** 10-second snapshots as specified will likely trigger WAF. Relax to **30 s** for Phase 1 and re-probe.
2. **Depth:** parked concept assumes L5. Verify the actual level count on day one. If only L1/L3, the **absorption detector must be redefined** to rely on:
   - bid price persistence (price doesn't fall despite large cumulative sell volume),
   - cumulative buy-initiated volume at support,
   - broker-identity confirmation post-close,
   rather than on "bid refill at level 2/3/4/5."
3. **Quote-fade detector:** likely infeasible on the free path. Quote fade needs sub-second depth snapshots; 30 s polling will miss most fades. **Recommend dropping quote-fade from v1 and replacing with a detector that is actually buildable from L1 + trade tape** (candidate: **tape imbalance + price non-response = absorption-candidate**; keep the second slot open until day-one empirical check).
4. **Baseline:** per-symbol intraday volume baseline cannot be built at all until capture runs for ≥10 sessions. Phase 1 can detect events relative to *same-day cumulative average* only, not cross-day normal.
5. **Circuit / block-trade / odd-lot filters** must be applied from day one or detectors will misfire.

**Can anything be started earlier using existing `own-market` data?**

Yes — this is the useful finding. A **daily-resolution** version of absorption and distribution is detectable **today** from the existing assets:

- 4 years of daily OHLCV at `sharesansar_datascrape/data/` (1,595 CSVs, 2022-01-01 to 2026-04-19).
- 2 months of floorsheet + broker-flow ledgers at `market-gist/broker_flow_ledger/` (4,207 JSON files, 30 symbols, buyer/seller broker IDs on every trade).

Studies runnable without opening a live-capture surface:
1. Per-symbol daily relative-volume baseline.
2. Wyckoff-style daily accumulation/distribution day classifier.
3. Broker concentration (top-1, top-3) as confirmation layer per day.
4. Persistent-broker streaks.
5. Retrospective daily absorption proxy (turnover ≥ 2× normal, |close − open| < X%, top buyer = 1 broker taking ≥ 30% of buy volume).
6. Circuit-day signatures.
7. Block-trade filter + odd-lot filter.
8. Volume-by-price zones at daily resolution.

These are **not** the live microscope. They are a *daily fingerprint* of the same phenomena. They can:
- validate detector **definitions** before Phase 1 runs a single poll,
- produce a labeled set of historical days to calibrate thresholds against,
- test the broker-flow confirmation hypothesis on 2 months of existing data.

This does not violate the parking. It uses only Layer 1/2 data already present, reads read-only, writes nothing to `market-gist/`, and produces research output only. It fits the doctrine: "agents explore independently; they may not promote independently."

---

## Recommendation

**Parked concept stays parked.** Do not open Phase 1 until the revisit triggers fire:
- forward persistence N=25 scored,
- universe v2 frozen or rejected,
- w7 recent replay/backfill closed,
- L-001 v2 coverage executed or parked.

**Allow one thing to start now, inside the sandbox rules:** a daily-resolution study of the same two target states (absorption, distribution) using existing `own-market` data. This is Phase 0½ — research-only, read-only, no new capture surface, no promotion.

If Romeo approves Phase 0½, the right form is a new experiment folder **following `_CONTRACT_TEMPLATE.md`**, slug `volume-psychology-daily` (not `volume-psychology` — leave that slug reserved for Phase 1 when unparked), numbered per whatever convention Romeo prefers. Candidate number: **09**.

If Romeo does not approve Phase 0½, this report stands alone as source research and the concept remains fully parked.

---

## Uncertainty

Open questions that require **direct empirical check** on day one of any future Phase 1 or Phase 0½ capture:

1. How many depth levels does the public `supplyDemand` endpoint actually return for NABIL? L1, L3, or L5?
2. What is the true sub-WAF minimum cadence? Start at 30 s, probe down only with explicit Romeo sign-off.
3. Is the intraday floorsheet JSON endpoint paginated *within* session, or only available post-close? If intraday, a polling strategy based purely on trade tape (no depth) becomes viable and changes the project shape.
4. Are the April 2026 circuit-rule changes live in NOTS yet, or still pending the operational directive? Affects band widths used by detectors.
5. For the daily-resolution Phase 0½ study: is 2 months of broker-flow-ledger coverage (March–April 2026) enough to validate the broker-concentration confirmation layer, or must backfill to 2022 happen first?

---

## What This Report Is Not

- Not a build permission.
- Not an expansion of the parking.
- Not a claim that Phase 1 is ready.
- Not a promise that `NepseUnofficialApi` will still work tomorrow.
- Not a trading signal, not a prediction, not a recommendation about NABIL or any other symbol.

It is source research, filed in `_parked/` next to the concept it supports, awaiting Romeo review.

---

## Companion Artifact

A longer scratch document produced during the research (`C:/Users/ishwor/Music/own-organize/market-volume/PROPOSAL.md`) contains an earlier Track A / Track B framing written before this report discovered the parked concept. That document overreached — it proposed opening Phase 1 directly. It should be treated as **superseded by this report** and may be deleted. The useful content from it (daily-resolution study list, data dictionary) is merged into §"Pilot Implication" above.
