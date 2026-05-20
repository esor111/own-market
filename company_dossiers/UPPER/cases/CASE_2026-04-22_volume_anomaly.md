# UPPER — Event Case #1: 2026-04-22 Volume Anomaly

**Case opened**: 2026-05-20
**Type**: Volume / participation anomaly (single trading day)
**Status**: Descriptive only. **Observation, not prediction.** Per DOSSIER_CONTRACT.md §5.

---

## 1. Mechanical selection rule (why this day, not "an interesting day I remembered")

This case was surfaced *mechanically*, not by memory:
- **External public table** (ShareSansar's UPPER Price History): single-day volume **408,969** with turnover **Rs 85.17 million** — visibly the largest bar in the Apr–May 2026 window of that table.
- **Local cockpit threshold** would also flag it: ~5× the trailing 20-day median UPPER volume.
- **Both criteria are external/mechanical** — no post-hoc storytelling. Source: [ShareSansar UPPER Price History](https://www.sharesansar.com/company/upper).

## 2. Price/volume facts (cross-verified — local data + ShareSansar agree exactly)

| Date | Open | High | Low | Close | Volume | Turnover (Rs) |
|---|---:|---:|---:|---:|---:|---:|
| **2026-04-22 (event)** | **210.00** | **215.00** | **204.00** | **207.00** | **408,969** | **85,171,894** |
| 2026-04-21 (prior) | 215.00 | 215.00 | 208.10 | 210.00 | 257,415 | 54,365,451 |
| 2026-04-15 (one wk prior, related) | — | — | — | 224.50 | **771,030** | — |
| 2026-04-06 (AGM announced) | — | — | — | ~213 | — | — |

- Intraday range Apr 22: 11 NPR (~5.2% of close) — a real range, not noise.
- **April 15 had higher absolute volume (771k) than April 22 (409k).** Both stand out vs the ~70–100k normal of surrounding days.

## 3. Broker-flow analysis (from refreshed local fact table)

Source: `market-gist/data/validation/broker_flow_fact_table/broker_flow_fact_table.csv` (rebuilt 2026-05-19, UPPER coverage through 2026-05-18).

### Day-level
- **77 broker rows on the event day** — wide participation, not one-sided.
- **Top-5 sell concentration: 42.6%** · **Top-5 buy concentration: 30.3%** → sell side noticeably more concentrated than buy side.

### The day's protagonist — broker 100
- **Net seller of −43,935 on Apr 22** (sold 43,935, bought zero).
- **Largest single absolute net position of the day.**
- **Appeared only 2 of 20 trailing days** in the baseline — i.e., broker 100 is **episodic, not regular**. When present, they trade in large size.

### The round-trip that broker 100 ran (descriptive, not interpretive)
- **Apr 15** (771k-volume day): broker 100 was the day's **lead BUYER** at **+44,100**. UPPER closed that day at **~224.50**.
- **Apr 22** (409k-volume day): broker 100 was the day's **lead SELLER** at **−43,935**. UPPER closed at **207.00**.
- **A 1-week round trip from ~224 → ~207** at the close level on the lead days = a **face-value loss of ~7-8% on the round-trip** for broker 100.
- **This pattern is NOT the signature of "smart-money distribution"** (which would typically *sell* into higher prices than they bought). It is more consistent with: (a) a forced execution / stop-loss / risk exit, (b) a redemption-driven outflow, (c) a program/algorithmic execution closing a position, or (d) a market-making book rebalance. **The data cannot distinguish among these.**

### Brokers persistently active across the event (≥2 days same net side on both sides of Apr 22)
| Broker | Days net-side before | Days net-side after | Side |
|---|---:|---:|---|
| 22 | 4 | 5 | BUYER |
| 8 | 2 | 7 | BUYER |
| 54 | 4 | 3 | BUYER |
| 13 | 3 | 2 | BUYER |
| 6 | 2 | 2 | SELLER |

→ **The persistent flow across the event is net-BUY-leaning** (four persistent buyers vs one persistent seller). The Apr 22 sell pressure was an **episodic** burst (broker 100 + rotational sellers 38/45/34/21), **not** a multi-week distribution from the same hands.

### Surrounding-window net-leader sequence
A net-seller-leader appears on Apr 16, 20, 21, 22, 27, 29, 30 — a multi-day sell-leader streak. Net-buyer-leader days in the same window: Apr 8, 9, 13, 15, 24, 28. So the broader Apr 16 → May 1 period leans net-seller-led with intermittent buying — consistent with the visible chart slide from 224 → 200.

## 4. Plain-English summary of what this day actually was

- A **broad-participation distribution-shaped day** (77 brokers active, sell-side more concentrated than buy-side).
- Driven by **one episodic large broker (100)** taking a sell position of 44k shares with zero buys.
- That same broker had **bought 44k a week earlier at higher prices** — making the Apr 22 sell look like a **closing/exit move, not a fresh "smart-money" distribution call**.
- Underneath, **four other brokers were persistently accumulating** across the event window.
- **Net effect on price**: the spike sit in the middle of a slide from 224 to 200 → it accelerated a pre-existing decline rather than initiating it.

## 5. What this case teaches the dossier (observation, not prediction)

1. **"Big volume + bearish-looking concentration" ≠ smart distribution by default.** Cross-checking who's selling and at what prices changes the read. A loss-making round-trip is more "forced flow" than "smart flow."
2. **Broker 100 is an episodic block-mover** for UPPER — worth flagging as a *descriptive watch-broker* in the daily read. Their presence on a day indicates outsized impact; absence indicates a more retail-flavored tape.
3. **Top-N concentration is informative ONLY in combination with*who* and *when*** — concentration alone can mislead. The persistent-streak view caught what the day-only top-5 number missed: a *net-buy-leaning persistent layer* under the surface noise.
4. **AGM announcement timing** (Apr 6) — the chart shows a sharp drop *the next trading day* (Apr 7, 198.50 close), then a recovery rally peaking exactly on Apr 15 (~224), then the slide back. **This is a real, datable rhythm worth checking on future AGM announcements** for UPPER (and only UPPER — generalising is data-snooping). Not predictive; pattern-noted.

## 6. Open questions / what the data cannot tell us

- **Who is broker 100?** Floorsheet IDs are anonymous numeric. Their identity would change the interpretation (foreign fund? merchant bank market-maker? specific large client?). `[unverified — needs broker-ID-to-name mapping; SEBON or NEPSE broker register]`.
- **Was there a news catalyst** on Apr 6 / Apr 15 / Apr 22 we haven't logged? `[unverified — needs full news scan of the window]`.
- **Where did broker 100's shares end up?** Did the persistent buyers (22, 8, 54, 13) absorb them, or did retail? The broker fact table does not pair buy/sell counterparties.

## 7. Disciplined limits (binding per DOSSIER_CONTRACT §7)

- This case **does not say "UPPER will rise/fall."** The post-Apr-22 path is in §3's surrounding-window context — price drifted 207 → 204, then chopped flat. That's history, not prediction.
- The "broker 100 loss-making round-trip" observation **does not mean "follow broker 100."** A single episodic actor's behaviour, even when interpretable, is not a signal.
- **No buy/sell, no target, no stop emerges from this case.** Its value is *pattern memory + better questions to ask of the next anomaly*.

## Sources

- ShareSansar UPPER Price History (today's snapshot): https://www.sharesansar.com/company/upper
- Local cockpit/dossier data layer: `dossier/dossier_data.py` (reads `sharesansar_datascrape/data/*.csv` + `broker_flow_fact_table/broker_flow_fact_table.csv`)
- Analysis script: `company_dossiers/UPPER/analyze_event.py 2026-04-22 UPPER`
- Focused chart: `company_dossiers/UPPER/charts/upper_case_2026-04-22.png`
