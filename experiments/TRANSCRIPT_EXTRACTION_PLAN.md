# Transcript Extraction Plan — NEPSE Trader Podcast Intelligence

> Written 2026-04-12 by Juliet, during brainstorming session with Ishwor.
> This documents the full context: why we're doing this, what we think it gives us, the extraction framework, the channel research, and the pilot plan.

---

## Why We're Doing This

### The brainstorm that led here

During the April 12 session, after completing the expanded 25-symbol scrape setup and the persistence signal audit, Ishwor raised a question: **what about the human side of the market?** We have mechanical signals, broker flow data, academic research, and a disciplined validation pipeline. But we don't systematically capture what Nepali retail traders actually think, say, and believe.

YouTube is where Nepali retail traders go for stock market analysis. Multiple channels with 70K-580K subscribers post daily/weekly analysis naming specific stocks, giving directional forecasts, discussing broker activity, and making fundamental claims. This is a real-time window into retail sentiment, street knowledge, and market consensus — all of which are potentially useful inputs to our research lab.

### What we think this gives us

1. **Sentiment as a contrarian indicator.** Published research shows retail crowd sentiment is a reliable contrarian signal at extremes. If 80% of YouTube traders are bullish on a sector, that historically correlates with poor forward returns. We can measure this systematically if we extract sentiment per symbol per transcript.

2. **Broker mentions and street knowledge.** Practitioners mention specific broker numbers (e.g., "broker 42 is accumulating NABIL") that never appear in academic literature. This feeds directly into our broker-flow analysis. Street knowledge that complements mechanical signals.

3. **What's already priced in.** If every YouTube trader talks about the hydro November-to-January seasonal, then our Strategy C pattern is widely known and may have less edge. If nobody mentions it, we may have an information advantage. Knowing what the market knows helps us calibrate.

4. **Practitioner hypotheses.** When traders say "I always buy hydro in Mangsir" or "I sell before book closure" or "I watch broker 42 for smart money" — these are testable hypotheses from experienced market participants. Some may overlap with our validated signals. Some may be new and worth testing.

5. **Data sources and tools we missed.** Traders mention websites, apps, Telegram groups, NRB circulars, and tools that our web research may not have found. This is a gap-fill mechanism.

6. **Market structure observations.** Comments about circuit breakers, pre-open auction behavior, IPO listing dynamics, promoter selling patterns, and other structural quirks of NEPSE that may not be documented anywhere else.

### What this does NOT give us

- **Direction calls.** "NABIL is going to 1500" is noise. L-011 says mechanical beats judgment. YouTube trader price targets are not alpha.
- **Technical analysis signals.** Moving average crossovers, support/resistance, candlestick patterns. Published research says near-zero predictive power on thin markets after costs. We capture what levels the crowd watches (useful for reaction triggers), not whether the analysis is correct.
- **Trading signals we act on.** Everything extracted goes into the data layer. Nothing extracted goes into a live trading decision. Same discipline as the expanded scrape — raw material accumulation.

### How this fits into the lab

This is an **exploration activity**, not a production signal. It does not touch the persistence shadow, the frozen policy, the scorer, or any running automation. It produces structured markdown/JSON files that sit on disk. If the pilot produces useful signal density, we scale. If it's mostly noise, we stop. Same pattern as every other exploration in the lab.

### Timing consideration

Ishwor specifically noted that we want **2026 forecasts** — what traders are saying about this year's market, this year's sectors, this year's stocks. Historical transcripts from 2024-2025 would capture sentiment that's already resolved (we could backtest it), but current 2026 transcripts capture live sentiment we can track forward. Both have value, but the pilot focuses on recent (2026) content.

---

## The Extraction Framework

### Level 1: Structured Capture (applied to every transcript)

Every transcript gets processed through these 7 categories. Each category produces structured, aggregatable data.

| Code | Category | What to extract | Why it matters for the lab |
|---|---|---|---|
| **S1** | **Sentiment** | For each stock/sector mentioned: symbol, direction (bullish/bearish/neutral), conviction strength (strong/moderate/weak), specific claim or reasoning | Aggregatable across transcripts. Consensus extremes = contrarian signal candidates. |
| **S2** | **Broker Mentions** | Broker number, symbol context, action (buying/selling/accumulating/distributing), any claim about the broker's identity or reputation | Direct input to broker-flow analysis. Street knowledge about which brokers are "smart money." |
| **S3** | **Price Levels** | Support/resistance levels, price targets, expected ranges. Symbol + level + direction + timeframe | Not for trading — for predicting where crowd reactions amplify when levels break. Crowd consensus levels are event triggers. |
| **S4** | **Trading Rules** | Any stated rule the trader follows. "I always buy hydro in Mangsir." "I sell before book closure." "I watch broker X for signals." Capture verbatim + paraphrase. | Practitioner hypotheses. Cross-reference with our validated signals. Some may be testable new hypotheses. |
| **S5** | **Data Sources & Tools** | Every website, app, Telegram group, NRB circular, tool, or information source mentioned. Name + URL if given + context of how they use it. | Gap search — what data feeds exist in the Nepal trading ecosystem that we don't know about? |
| **S6** | **Fundamental Claims** | Earnings expectations, dividend forecasts, AGM dates, management changes, regulatory impacts, sector outlook. Symbol + claim + timeframe + source if stated. | Verifiable claims. Cross-check against actual data. Tells us what the market expects vs what happens. |
| **S7** | **Market Structure** | Comments about circuit breakers, pre-open auction behavior, IPO listing dynamics, promoter selling patterns, settlement quirks, how institutions operate, NEPSE system behavior. | How NEPSE actually works from a practitioner perspective. May reveal structural patterns not in documentation. |

### Level 2: Anomaly Capture

| Code | Category | What to capture |
|---|---|---|
| **A1** | **Surprises** | Anything that doesn't fit S1-S7 but is interesting. A pattern nobody else mentions. An unusual data source. A claim about market manipulation. A historical anecdote with testable implications. |
| **A2** | **Contradictions** | Where this trader explicitly disagrees with the consensus or with another named trader. Disagreements are more informative than agreements. |

### Level 3: Extensible (added when patterns emerge)

The framework is explicitly designed to grow. If we process 20 transcripts and notice a recurring theme that doesn't fit S1-S7 or A1-A2, we add a new category. Examples that might emerge:

- **Regulatory anticipation** — traders predicting NRB or SEBON actions before they happen
- **Political trading** — explicit discussion of trading around political events
- **Seasonal rules** — specific month/festival-based trading calendars practitioners follow
- **Insider signals** — coded language about insider information (capture with legal caution per EXPLORATION_CHARTER rule #7)

We don't pre-build these. We let them emerge from the data.

---

## Output Format

### Per-transcript file

One structured file per processed transcript, saved to `experiments/transcript_extractions/`:

```
Filename: YYYY-MM-DD__<channel_slug>__<video_title_slug>.md

---
metadata:
  channel: <channel name>
  personality: <analyst name>
  date_published: <YYYY-MM-DD>
  date_extracted: <YYYY-MM-DD>
  video_url: <YouTube URL>
  duration_minutes: <number>
  language: <Nepali / English / mixed>
  transcript_source: <auto-caption / manual / STT tool>
  transcript_quality: <good / partial / poor>
  overall_signal_density: <high / medium / low>
  confidence_note: <free text about reliability>

S1_sentiment:
  - symbol: NABIL
    direction: bullish
    conviction: strong
    claim: "expects 1500 within 3 months due to dividend announcement"
    timestamp: "3:42"

S2_broker_mentions:
  - broker: 42
    symbol: NABIL
    action: accumulating
    context: "smart money has been buying through broker 42 for 2 weeks"

S3_price_levels:
  - symbol: NABIL
    level: 1200
    type: support
    claim: "strong support at 1200, if it breaks we see 1050"

S4_trading_rules:
  - rule: "always buy hydro before Mangsir"
    verbatim: true
    testable: true
    overlaps_with: "Strategy C (L-009/L-010)"

S5_data_sources:
  - name: "NepseAlpha broker holding page"
    url: "https://nepsealpha.com/broker-holding"
    context: "checks daily for broker accumulation signals"

S6_fundamental_claims:
  - symbol: EBL
    claim: "expects 30% dividend this year"
    timeframe: "FY 2082/83"
    verifiable: true

S7_market_structure:
  - observation: "pre-open auction is rigged by big players who place orders and cancel"
    verifiable: partially
    relates_to: "14_nepse_structural_quirks.md"

A1_surprises:
  - note: "claims NRB is about to change margin lending rules again in Shrawan"
    significance: high
    action: "cross-check with NRB monetary policy calendar"

A2_contradictions:
  - disagrees_with: "Ram Hari Nepal's bullish hydro view from last week"
    on_topic: "hydropower sector outlook Q1 2083"
    their_view: "bearish due to water level concerns"
```

### Aggregation (after 10+ transcripts)

Periodic aggregation files that combine across transcripts:

- **Sentiment heat map** — which symbols/sectors are consensus bullish/bearish, and how extreme
- **Broker mention frequency** — which broker numbers keep appearing, in what context
- **Common trading rules** — which practitioner rules are mentioned by 3+ independent traders
- **Price level consensus** — where does the crowd agree on support/resistance
- **New data sources** — every tool/website/channel discovered, deduplicated
- **Surprise log** — all A1 items sorted by significance

---

## Channel Research (conducted 2026-04-12)

### Tier 1: Highest Extraction Priority

These channels name specific stocks, give directional views, and post frequently enough for regular extraction.

#### 1. RAM HARI NEPAL
- **Subscribers:** 137,000
- **Videos:** 2,361+
- **Frequency:** 5-6 videos/week
- **Average length:** 17 minutes
- **Content type:** Daily market analysis, specific stock picks, technical + fundamental
- **Why Tier 1:** Most prolific daily NEPSE creator. High signal density — names stocks, gives directions, discusses broker activity. Perfect for S1 (sentiment) and S2 (broker mentions).
- **Stats source:** https://vidiq.com/youtube-stats/channel/UCIkVIHAYHalmpfn0ZtW1IdA/
- **Growth:** ~1K new subscribers + 360K views monthly (active and growing in 2026)

#### 2. Artha Sarokar (Suraj Pyakurel)
- **Subscribers:** 66,000 YouTube + 1.2M TikTok
- **Content type:** Panel-style economic news discussions. Nepal's #1 economic news portal.
- **Why Tier 1:** Panel format means 3-4 analysts per video, each giving views. Gold for S1 (multiple sentiment data points per transcript) and S6 (fundamental claims from different perspectives).
- **Website:** https://arthasarokar.com/
- **TikTok:** https://www.tiktok.com/@arthasarokar (1.2M followers)

#### 3. Share Durbar (Shakti Koirala)
- **Subscribers:** ~85,000
- **Content type:** Positional trading strategies with specific stock picks
- **Personality:** Shakti Koirala, trading since 2018, former investment analyst
- **Why Tier 1:** Names specific entry/exit levels. Good for S3 (price levels) and S4 (trading rules). Caught UNL, TRH moves in 2023.
- **Website:** https://sharedurbar.com.np/
- **About:** https://sharedurbar.com.np/about/

#### 4. Stock Guru (Raju Paudel)
- **Subscribers:** ~71,000
- **Content type:** Fundamental + technical analysis for beginners and advanced
- **Why Tier 1:** Good for S6 (fundamental claims) with specific stock analysis
- **Stats:** https://playboard.co/en/channel/UC4C4SrT-Ja9goDwr3J1obJg

### Tier 2: Secondary Extraction Value

#### 5. share market in nepal
- **Subscribers:** 245,000
- **Videos:** 1,652
- **Average length:** 14 minutes
- **Status:** Possibly inactive in 2026 (0 uploads in last 30 days as of research date)
- **Why Tier 2:** Huge backlog corpus for historical sentiment extraction. Lower priority if inactive.
- **Stats:** https://vidiq.com/youtube-stats/channel/UCM3G0qLnOD3NEI2ixgXUi7Q/

#### 6. Ideapreneur Nepal (Sanjog Koirala)
- **Subscribers:** 583,000 (LARGEST channel in this space)
- **Videos:** 202
- **Average length:** 32 minutes
- **Content type:** Financial literacy, education, long-form
- **Why Tier 2:** Most popular but more education than daily stock calls. Long-form content may embed specific stock/sector discussion within educational framing. Good for understanding what mass retail is learning.
- **Website:** https://ideapreneurnepal.com/
- **Also runs:** Money Mitra platform (https://moneymitra.com/) which includes Gurumantra stock analysis, Broker Chirfaar, paid courses
- **Stats:** https://vidiq.com/youtube-stats/channel/UCuv3IZ2RpS657pt5aL7TVtQ/

#### 7. NEPSE Trading / Sandeep Kumar Chaudhary
- **Background:** Pioneer of formal technical analysis in Nepal, 15+ years experience, runs SMAARC
- **Content type:** Smart money concepts, advanced TA
- **Website:** https://nepsetrading.com/
- **Why Tier 2:** Deep TA knowledge but likely lower S1 signal density (more methodology than daily calls)
- **Source:** https://nepsetrading.com/blog/best-technical-analysis-training-in-nepal-by-expert-sandeep-kumar-chaudhary

### Key Personalities (across all platforms)

| Name | Channel/Platform | Focus | Relevance |
|---|---|---|---|
| Ram Hari Nepal | RAM HARI NEPAL (YouTube) | Daily market calls | Highest extraction priority |
| Suraj Pyakurel | Artha Sarokar (YouTube/TikTok) | Economic news panels | Multi-analyst sentiment |
| Shakti Koirala | Share Durbar (YouTube) | Positional trades | Specific entry/exit levels |
| Raju Paudel | Stock Guru (YouTube) | FA + TA | Fundamental claims |
| Sanjog Koirala | Ideapreneur Nepal (YouTube) | Financial education | Mass retail sentiment baseline |
| Sandeep Kumar Chaudhary | NEPSE Trading (YouTube/web) | Advanced TA | Smart money methodology |
| Dipendra Agrawal | TikTok/YouTube | Market discussion | Emerging voice |
| Nabaraj Dahal | TikTok/YouTube | Market discussion | Emerging voice |
| Keshab Koirala | TikTok/YouTube | Market discussion | Emerging voice |

### Non-YouTube Platforms

| Platform | Presence | Notes |
|---|---|---|
| **Facebook** | Likely MORE influential than YouTube for real-time NEPSE discussion. Share Nepal (@sharenepalfb), Artha Kendra groups, Merolagani investor forum. | Harder to extract from — mostly discussion threads, not structured content. |
| **TikTok** | Growing fast. Artha Sarokar (1.2M), @nepse.trader, @nepse_info, @nepsestockmarket, @ideapreneurnepal | Short-form. Lower signal density per video but high reach. |
| **Telegram** | Nepal Share Market channel: https://t.me/s/NepalStockExchange | Real-time updates. Could be a scraping target later. |
| **Viber** | Private stock discussion groups. Most actual insider gossip happens here. | Inaccessible to extraction. |
| **X/Twitter** | Not significant for Nepali NEPSE discussion. | Skip. |

### Web Platforms Referenced by Traders

| Platform | URL | What it provides |
|---|---|---|
| NepseAlpha | https://nepsealpha.com/ | Broker holding, buy-sell depth, floorsheet analysis |
| ShareSansar | https://www.sharesansar.com | Market data, news, company financials |
| MeroLagani | https://merolagani.com/ | Market data, floorsheet, portfolio tracking |
| ShareHub Nepal | https://sharehubnepal.com/ | Market discussion and analysis |
| NEPSE Broker Analysis | https://nepsebrokeranalysis.com/ | Broker-level analysis tools |
| Nepalytix | https://nepalytix.com/ | Market analytics |
| npstocks | https://npstocks.com/ | Market data |
| Money Mitra | https://moneymitra.com/ | Courses, Gurumantra, Broker Chirfaar |
| NepseTrading | https://nepsetrading.com/ | TA training, smart money analysis |

---

## Pilot Plan

### Phase 1: Feasibility Test (5 transcripts)

1. **Channel:** RAM HARI NEPAL (highest signal density, most frequent)
2. **Videos:** 5 most recent from 2026 (ideally covering different trading weeks)
3. **Transcript source:** Test YouTube auto-captions first. If Nepali auto-caption quality is poor, fall back to manual transcription or Nepali STT tool.
4. **Extraction:** Apply full S1-S7 + A1-A2 framework to each transcript
5. **Output:** 5 structured extraction files in `experiments/transcript_extractions/`
6. **Evaluation:** After 5 transcripts, assess:
   - Signal density: how many S1-S7 items per transcript?
   - Aggregation value: do patterns emerge across 5 transcripts?
   - Feasibility: how long does extraction take per transcript?
   - Transcript quality: is auto-caption usable or do we need manual?
7. **Decision gate:** If signal density is high (5+ items per category per transcript), scale to Phase 2. If mostly filler, stop.

### Phase 2: Scale (if pilot succeeds)

- Expand to 20 transcripts across Tier 1 channels (RAM HARI NEPAL, Artha Sarokar, Share Durbar)
- Build first aggregation report (sentiment heat map, broker mentions, trading rules)
- Evaluate whether to add Tier 2 channels
- Consider whether another agent team should handle extraction systematically

### Phase 3: Ongoing Collection (if Phase 2 succeeds)

- Weekly extraction cadence: process 3-5 new transcripts per week from Tier 1 channels
- Monthly aggregation reports
- Cross-reference with persistence shadow data and broker flow ledger
- Track forecast accuracy: did the bullish/bearish calls from Month X play out by Month X+3?

---

## Critical Feasibility Risk

**YouTube auto-transcript quality in Nepali is untested.** Most of these channels speak Nepali with some English financial terms mixed in. YouTube's auto-caption for Nepali may be:
- Good enough (readable with some errors) → proceed with auto-captions
- Partially usable (key stock names captured, but context garbled) → may need manual correction
- Unusable → need manual transcription or a dedicated Nepali STT pipeline

This is the single biggest risk to the pipeline. The pilot will answer it.

### Backup if auto-transcript fails

1. Ishwor manually transcribes key sections (slow, doesn't scale)
2. Use a Nepali speech-to-text tool (e.g., OpenAI Whisper with Nepali support)
3. Focus on channels that mix more English into their Nepali (some analysts do this)
4. Switch to text-based sources instead (Facebook posts, Telegram messages, ShareSansar articles)

---

## Parked Ideas (from the brainstorm, saved for later)

These came up during brainstorming but were parked under patience-mode discipline. Documented here so they don't get lost.

### News Portal Monitoring
- **Idea:** Systematically capture financial news from Nepali news portals (ShareSansar, MeroLagani, Artha Sarokar articles, Online Khabar business section)
- **Value:** Event detection, regulatory announcement tracking, corporate action news
- **Status:** Parked. Evaluate after YouTube pilot.

### Source Curation
- **Idea:** Build a comprehensive catalog of every website, tool, data feed, Telegram channel, and information source in the Nepal trading ecosystem
- **Value:** Gap search, ecosystem mapping, discovering data we don't have
- **Status:** Parked. The YouTube extraction S5 (data sources) category will naturally surface sources. Formalize after pilot.

### Facebook Group Extraction
- **Idea:** Monitor key NEPSE Facebook groups for retail sentiment
- **Value:** Facebook may be more influential than YouTube for real-time NEPSE discussion
- **Status:** Parked. Harder to extract (discussion threads, not structured content). Evaluate after YouTube pilot.

### TikTok Short-Form Extraction
- **Idea:** Process short-form TikTok market takes from Artha Sarokar (1.2M), nepse.trader, etc.
- **Value:** High reach to retail crowd, but very low signal density per video
- **Status:** Parked. Low priority — YouTube long-form has much higher extraction value.

### Forecast Accuracy Tracking
- **Idea:** For each directional call extracted (S1), track whether it was right or wrong after 30/60/90 days
- **Value:** Measures whether any individual trader or the consensus has predictive power
- **Status:** Parked. Requires 3+ months of extraction before first accuracy check is meaningful. Build into Phase 3 if we get there.

---

## Connection to Existing Lab Work

| Lab component | How transcript extraction connects |
|---|---|
| **Persistence shadow signal** | S2 (broker mentions) may surface the same brokers our signal tracks. Street knowledge about "which brokers are smart money" is a cross-validation source. |
| **Strategy C (hydro seasonal)** | S1 (sentiment) tells us if the Nov-Jan hydro pattern is widely known. If it is, the edge is smaller. S4 (trading rules) may surface practitioners who explicitly follow this calendar. |
| **Broker reputation research (BACKLOG Tier A0)** | S2 directly feeds this. If multiple independent traders name the same broker numbers as "institutional" or "manipulative," that's practitioner consensus about broker types — exactly what the Linnainmaa-Saar segmentation approach needs. |
| **Experiment 03 (NRB rate events)** | S6 (fundamental claims) captures trader expectations about NRB policy. A1 (surprises) may surface anticipation of specific NRB actions before announcements. |
| **L-011 (mechanical beats LLM)** | The transcript extraction is NOT about following trader advice. It's about measuring what the crowd believes, which is an input to mechanical signals (contrarian sentiment), not a replacement for them. |

---

## What Success Looks Like

After the 5-transcript pilot, we know:
1. Whether YouTube auto-transcripts in Nepali are usable
2. How many structured data points per transcript (signal density)
3. Whether multiple traders mention the same broker numbers (convergence)
4. Whether any trader mentions patterns we've validated but not published (information advantage check)
5. Whether the extraction effort is worth scaling

If all 5 transcripts produce 2+ items per S-category on average, the pilot is a success and we scale. If most categories are empty, the signal density is too low and we either switch channels or park the project.

---

*Written 2026-04-12 by Juliet. Context from brainstorming session with Ishwor.*
*This is an exploration plan, not a production commitment. Everything here is subject to the pilot gate.*
