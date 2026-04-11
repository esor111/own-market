# Nepal Market Source Pack

Date assembled: `2026-04-08`  
Purpose: collect the Nepal-market references used to define high-value, non-random experiment verticals for NEPSE research.

This pack is meant to answer:

- What actually drives the Nepal market?
- Which drivers are worth experimenting on?
- Which public sources can we scrape, download, or revisit later?
- Which sources are official, academic, or community-market mirrors?

## Contents

- `source_catalog_2026-04-08.json`
  Machine-readable catalog of sources with vertical, type, date, URL, gist, and experiment use.
- `raw/`
  Local copies of high-value PDFs we want to keep available even if websites change.

## Current Best Vertical Map

Ranked by Nepal-specific relevance, data availability, and how cleanly each lane can be tested:

1. `Liquidity / rate regime`
   NRB liquidity, interbank, T-bill, lending/deposit rates, remittance, and margin-lending rules.
2. `Corporate action surprise`
   Rights, bonus, dividend, earnings, book-close, AGM, listing/distribution windows.
3. `Broker / microstructure`
   Floorsheet broker flow, breadth, turnover, sector rotation, retail herding proxies.
4. `Sector-specific structural lanes`
   Banking fundamentals, hydropower monsoon/generation/policy effects.
5. `Supply shock / issuance`
   IPO approvals, pipeline, lock-in release overhang.
6. `Secondary macro / real economy`
   Fiscal capex, procurement, FX/import pressure, tourism.

## How To Use This Pack

When starting a new experiment:

1. Pick one vertical from the catalog.
2. Use the official sources first.
3. Use academic papers to shape the hypothesis, not to claim the hypothesis is already proven in our dataset.
4. Use community-market mirrors only as access helpers, not as the final source of truth when official data exists.

## Core Local PDFs

- [NRB Monetary Policy 2025/26](raw/NRB_Monetary_Policy_2025_26.pdf)
- [NRB Determinants of Stock Market Performance in Nepal](raw/NRB_Determinants_of_Stock_Market_Performance_in_Nepal.pdf)
- [SEBON Investors Handbook](raw/SEBON_Investors_Handbook.pdf)
- [CDSC Book Close Disclosure Form](raw/CDSC_Book_Close_Disclosure_Form.pdf)
- [Nepal Climate Context (UNFCCC)](raw/Nepal_Climate_Context_UNFCCC.pdf)

## Vertical Guide

### 1. Liquidity / Rate Regime

Why it matters:

- NEPSE is highly liquidity-sensitive.
- Financial stocks are directly exposed to NRB policy, lending rules, and money-market conditions.
- Remittance is an upstream liquidity driver in Nepal.

Best first tests:

- Monthly NEPSE and sector returns vs `M2`, deposits, interbank, T-bill, lending/deposit rates.
- Event study around margin-lending rule changes and monetary policy releases.

Catalog IDs:

- `LQ-001` to `LQ-008`

### 2. Corporate Action Surprise

Why it matters:

- Nepal reacts strongly to rights, bonus, dividend, and earnings disclosures.
- The `announcement` often matters more than the administrative processing date.

Best first tests:

- Separate event study for `announcement`, `approval`, `book close`, `ex-date`, `listing`.
- Compare rights vs bonus vs cash dividend vs earnings.

Catalog IDs:

- `EV-001` to `EV-010`

### 3. Broker / Microstructure

Why it matters:

- NEPSE is retail-led and thin relative to larger markets.
- Floorsheet, breadth, turnover, and sector-rotation effects are likely first-order.

Best first tests:

- Broker net-flow imbalance.
- Breadth and turnover extremes.
- Sector-relative-strength rotation.
- Small-lot / clustered same-side activity as a retail-herding proxy.

Catalog IDs:

- `MS-001` to `MS-008`

### 4. Banking + Hydropower Structural Lanes

Why it matters:

- Banks are sensitive to profitability, spreads, NPLs, rates, and credit conditions.
- Hydropower is sensitive to monsoon, water flow, generation seasonality, FX, and project events.

Best first tests:

- Bank panel on `EPS`, `DPS`, `BVPS`, `ROE`, `NPL`, spreads, base rate.
- Hydro panel on `EPS`, rainfall/streamflow anomaly, generation seasonality, FX, project events.

Catalog IDs:

- `SC-001` to `SC-009`

### 5. Supply Shock / Issuance

Why it matters:

- Nepal’s IPO and lock-in culture creates retail supply/demand distortions.
- Unlock windows can create measurable overhang.

Best first tests:

- Lock-in expiry event study.
- IPO approval / pipeline crowding effects.

Catalog IDs:

- `SP-001` to `SP-003`

### 6. Secondary Macro / Real Economy

Why it matters:

- Fiscal capex cadence, procurement flow, import cost pressure, and tourism can matter for narrower slices of NEPSE.

Best first tests:

- Budget / procurement pulse for infra and industrial names.
- Customs/FX pass-through for import-heavy names.
- Tourism arrivals for tourism/hotel proxies.

Catalog IDs:

- `RM-001` to `RM-005`

## Notes

- Some websites are best treated as reference pages rather than stable downloadable documents.
- Some sectors will need unofficial mirrors for cleaner historical data access, but official sources should stay primary whenever possible.
- This pack is a reference base, not a conclusion file. We still need to test each lane empirically.
