# Broker Data Enrichment Source Map

> Working map for richer broker-flow context. Use this to decide what to add next, not as a signal document.

## Now

### Broker-flow fact table
- **Local source:** `market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table.csv`
- **What it gives:** broker_id, symbol, date, buy/sell quantity, buy/sell amount, net quantity, net amount, gross activity.
- **Prediction value:** core microstructure spine.
- **Caveat:** broker_id is not client identity; prop vs client flow is unknown.

### L-001 corporate-action events
- **Local source:** `experiments/01-corporate-action/data/events.csv`
- **What it gives:** dividend, bonus, book-close, AGM, right-share, listing, and related date fields.
- **Prediction value:** tells us when broker-flow may be contaminated by known public events.
- **Caveat:** strong seed table, but not a complete official filing archive.

### Broker contact/code mapping
- **Public source:** [Nepse Bajar broker contact](https://www.nepsebajar.com/broker-contact)
- **Official cross-check:** [SEBON intermediaries](https://www.sebon.gov.np/intermediaries), [SEBON stock brokers](https://www.sebon.gov.np/intermediaries/stock-brokers)
- **What it gives:** broker code/name/address/phone where available.
- **Prediction value:** makes broker-flow reports readable and supports later broker-type segmentation.
- **Caveat:** third-party code/name mapping must be treated as convenience data until reconciled with official SEBON/NEPSE records.

## Next

### Official issue/corporate-action tables
- **Sources:** [SEBON IPO Approved](https://www.sebon.gov.np/ipo-approved), [SEBON Right Share Approved](https://www.sebon.gov.np/right-share-approved), [SEBON Bonus Share Registered](https://www.sebon.gov.np/bonus-share-segistered), [SEBON Public Issues Data](https://www.sebon.gov.np/public-issues-data)
- **What it gives:** official approval/registration context for IPO, rights, bonus shares, and public issues.
- **Prediction value:** separates public-event-driven broker flow from clean flow.
- **Caveat:** approval/registration date is not the same as allotment/listing/trading impact date.

### NEPSE filing PDFs
- **Source:** [NEPSE security file endpoint](https://www.nepalstock.com.np/api/nots/security/fetchFiles)
- **What it gives:** notices, annual reports, book-closure notices, margin-related PDFs, and company disclosures.
- **Prediction value:** higher-quality event calendar and document evidence.
- **Caveat:** PDFs are unstructured; OCR and duplicate handling are required.

## Later

### NRB liquidity context
- **Sources:** [NRB Economic Research Department](https://www.nrb.org.np/departments/red/), [NRB Monetary Management Department](https://www.nrb.org.np/departments/pdm/)
- **What it gives:** interbank rate, repo/reverse repo, deposits, credit growth, remittance, reserves, and policy context.
- **Prediction value:** explains when broker selling may be market liquidity stress, not broker-specific alpha.

### Hydro physical context
- **Sources:** [DOED hydropower registry](https://doed.gov.np/pages/appclhydro/), [DHM hydrology network](https://www.dhm.gov.np/hydology/hydrological-data-network), [NEA notices](https://www.nea.org.np/index.php/notice)
- **What it gives:** river basin, plant location, capacity, flood/weather/outage context.
- **Prediction value:** crucial for hydro-specific buy/avoid/sell reasoning.

### Credit rating actions
- **Sources:** [CARE Ratings Nepal](https://www.careratingsnepal.com/find-ratings), ICRA Nepal PDFs mirrored by issuers.
- **What it gives:** issuer/facility ratings, reaffirmations, upgrades/downgrades, outlook/watch changes.
- **Prediction value:** slow-moving credit-quality context.
- **Caveat:** mostly PDF-heavy and issuer-hosted; needs careful source tracking.

## Do Not Treat As Available Yet

- Public client-level identity behind broker trades.
- Reliable split between broker proprietary trades and client orders.
- Stable official public live orderbook/floorsheet JSON API.
- Broker inventory/holdings unless a source is explicitly verified.

