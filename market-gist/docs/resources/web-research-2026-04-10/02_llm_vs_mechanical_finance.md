# Thread 2: LLM vs Mechanical Rules in Financial Prediction

## Question
Is L-011 ("mechanical signals consistently beat LLM judgment on NEPSE") a universal finding in finance, or is it specific to thin emerging markets like Nepal? Has anyone else documented this pattern?

## Method
WebSearch across arXiv, SSRN, ScienceDirect, Frontiers in AI, Two Sigma public statements, and recent industry commentary.

## TL;DR
**The "mechanical beats LLM" finding is strongly consistent with 2024-2025 academic literature on adjacent markets (US equities, Indian NIFTY, prediction markets). No paper tested NEPSE directly, so this remains a strong external corroboration, not a universal validation.**

The repeatedly observed pattern across the published evidence:
1. Short-horizon directional prediction: LLMs barely beat coin flip (51-65% accuracy in published tests)
2. LLMs are systematically overconfident; verbalized confidence scores are "almost independent from accuracy"
3. The one area LLMs reliably add value is **textual signal extraction** (sentiment from news/filings/earnings calls), NOT direct price prediction
4. The most-cited "LLMs predict stocks!" paper shows Sharpe **decayed from 6.54 (2021Q4) to 1.22 (2024)** as adoption rose
5. Multiple 2025 benchmarks find LLMs fail to beat buy-and-hold or classical baselines under transaction costs

Nepal makes the gap **more extreme** because we lack the one thing LLMs do reliably well: English-language news flow.

---

## Key Papers — Mechanical Beats LLM

### "When Reasoning Fails" (arXiv 2511.08608, Nov 2025)
**This is the most directly relevant paper to our situation.**
- Method: Rolling walk-forward test on Indian NIFTY equities (thin emerging market cousin to NEPSE)
- 1-day return ranking, varied universe size
- Baselines: Direct LLM (gpt-4o-mini), Thinking LLM (gpt-5), ridge regression, random forest
- **Result:** Thinking LLMs' ranking quality deteriorates as complexity grows; classical baselines (ridge, random forest) are STABLE. Under transaction costs, thinking LLMs show NO net advantage.
- Key quote: *"Next-token prediction objectives and token-budgeted inference are poorly aligned with heavy-tailed, weakly predictable stock returns."*
- URL: https://arxiv.org/abs/2511.08608

### StockBench (arXiv 2510.02209, Oct 2025)
- Contamination-free benchmark, multi-month trading, daily buy/sell/hold decisions
- **Result:** "Most LLM agents fail to outperform a simple buy-and-hold baseline."
- Top models (Kimi-K2, Qwen3-235B) managed only 1.9% and 2.4% returns
- Critically: **"LLM agents generally struggle to navigate bearish market conditions"** — documented bullish bias
- URL: https://arxiv.org/abs/2510.02209

### Lopez-Lira & Tang (canonical "ChatGPT predicts stocks" paper)
- Original (2023): GPT-4 generated daily returns of 44 bps, t-stat 4.24
- **Updated 2025:** Annualized Sharpe **decayed from 6.54 (2021Q4) → 3.68 (2022) → 2.33 (2023) → 1.22 (Jan-May 2024)**
- Authors attribute decay to "improved price efficiency" as LLM adoption spreads
- This is a dying edge, not a stable one
- URLs:
  - https://arxiv.org/abs/2304.07619
  - https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788

### Glasserman & Lin (2023) — Look-Ahead Bias Critique
- Compared original vs anonymized news headlines with GPT-3.5 sentiment
- **Anonymized headlines OUTPERFORMED original headlines in-sample**
- Means LLM's "knowledge" actively HARMS judgment when it interferes with text signal
- Implication: Any paper showing LLM alpha on in-training-window data is contaminated
- URL: https://arxiv.org/abs/2309.17322

### Vidal — "Efficacy of LLMs in Predicting Stock Prices" (SSRN 4947135)
- 250 stocks, 4 LLMs tested
- **Directional accuracy 51.6% to 65.6%, mean 59.4%**
- Barely above coin flip
- **Directly matches our finding** of 56.4% directional accuracy on hydro
- URL: https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4947135

### PriceSeer (2026, arXiv 2601.06088)
- 110 US stocks × 249 data points, 6 frontier LLMs, live benchmark
- **Result:** Top LLMs achieve "hit rate over 0.5" — best models barely above 50%
- URL: https://arxiv.org/abs/2601.06088

### "The New Quant: A Survey of LLMs in Financial Prediction" (arXiv 2510.05533, Oct 2025)
- Synthesizes 50+ primary studies, 2023-2025 — **the consensus document**
- **Conclusion:** LLMs' productive role is "reading and reasoning over disclosures, generating auditable hypotheses, interacting with tools" — NOT direct price prediction
- Flags "Time Machine GPT" (training leakage) as the #1 methodological issue
- Productive tasks listed: sentiment extraction, info extraction, numerical QA, summarization
- **"Predict the direction" is NOT on the list**
- URL: https://arxiv.org/abs/2510.05533

---

## Calibration Failure (Validates Our "Conviction Doesn't Predict" Finding)

### KalshiBench (arXiv 2512.16030, Dec 2025)
- Tested 5 frontier models on real prediction-market questions
- **Expected Calibration Error 0.120 to 0.395** — all models systematically overconfident
- **Key finding: extended reasoning WORSENS calibration**
- "Longer reasoning chains reinforce initial hypotheses rather than updating on evidence"
- URL: https://arxiv.org/html/2512.16030

### "On Verbalized Confidence Scores for LLMs" (arXiv 2412.14737)
- **"Verbalized confidence scores are not only poorly calibrated, but almost independent from accuracy"**
- Direct match to our empirical finding
- URL: https://arxiv.org/pdf/2412.14737

### "LLMs are Overconfident" / FermiEval (arXiv 2510.26995)
- Systematic overconfidence on quantitative uncertainty intervals across all tested models
- URL: https://arxiv.org/html/2510.26995

**Implication:** Our move to code-side calibration is the published solution. KalshiBench's "normalized conformal prediction" approach is essentially what we are doing.

---

## The Bullish/Narrative Bias (Validates "Neutral Hides Bearish")

- StockBench: "Bias towards bullish markets" — LLM agents struggle in bearish regimes
- **"LLM Foreign Bias" (2026):** ChatGPT issued forecasts ~12.5% higher than DeepSeek on Chinese stocks. Bias vanished only when given Chinese-language news directly.
- **Implication for Nepal:** if the LLM only knows about Nepal from sparse English sources, it will be systematically over-optimistic on Nepali stocks.
- Lehner (SSRN 4984337): LLMs being used for "AI-driven tone manipulation in SEC filings" — adversarial environment

---

## Where LLMs DO Add Value (The Counter-Examples)

### Sentiment extraction from text (NOT prediction)
- Pelster & Val (2023): ChatGPT "attractiveness ratings" correlated with subsequent returns — but text-scoring task, not direct prediction
- OPT (GPT-3-based) achieved 74.4% sentiment accuracy. R² for next-day returns only 0.010 — statistically significant, economically small.

### Earnings call analysis
- "On-topicness and proactiveness" LLM metric: +515 bps annualized alpha
- **Strongest documented LLM alpha in literature.** But the alpha comes from a structural metric (cosine similarity of analyst Q&A to exec answers), NOT from "ChatGPT, should I buy?"

### SEC 10-K/10-Q analysis
- "Lazy Prices" replication with LLM features: Sharpe ~1.5 annualized
- The original "Lazy Prices" used simple textual change detection — LLM added incremental value

### **Feature engineering on sparse data (RELEVANT TO US)**
- "From Limited Data to Rare-event Prediction" (arXiv 2509.08140): LLMs used as **feature engineers feeding XGBoost/Random Forest**, NOT as end-to-end predictors. Specifically for sparse-data domains.
- "LLM-guided semantic feature selection for low-resource financial markets" (ScienceDirect): Explicitly targets markets like Nepal. LLM for feature selection, mechanical model for prediction.
- **This is probably our optimal architecture going forward:** LLM reads the limited Nepali news/filings, extracts features, mechanical model predicts.

### Hybrid systems
- "ChatGPT in Systematic Investing" (SSRN 5680782): LLM-enhanced momentum strategy beat standard momentum out-of-sample. But LLM was adding a news-signal filter ON TOP of a mechanical momentum base — hybrid, not pure LLM.

**The common pattern across all positive findings:** LLM as **input processor** to a mechanical system works. LLM as **decision maker** does not.

---

## Industry / Practitioner Perspective

### Two Sigma — 2026 AI Outlook (public statement)
- **Explicit stance:** "The next year won't be about LLMs making trades."
- LLMs are the "research OS, not the trading brain"
- "Widening the research funnel" — helping quants evaluate hypotheses faster
- **Explicit warning:** "A key risk could be believing the hype too much... without being sufficiently skeptical"
- "AI agents make it easier for researchers to generate many hypotheses and backtest them, which can exacerbate overfitting issues"
- URLs:
  - https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-i/
  - https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-ii/

### Institutional Investor — "The Most Powerful AI Knows Nothing About Investing. That's Perfectly Okay."
- The headline is literal
- LLMs useful for communication, research summarization, document processing — NOT as oracles
- URL: https://www.institutionalinvestor.com/article/2bswlvepw2hmezaphmcxs/opinion/the-most-powerful-artificial-intelligence-knows-nothing-about-investing-thats-perfectly-okay

### Crypto / LLM Trading Bots — Real Performance
- Prof. von Jouanne-Diedrich's S&P 500 long/flat (ChatGPT-4, 2000-2021): 3.34% annual return vs buy-and-hold 5.56%. **LLM underperformed buy-and-hold.**
- nof1.ai live competition: cherry-picked winners, severe selection bias
- General finding: "Even with sound methodology, live results typically trail backtests"

---

## Where We Stand vs The Literature

### Universal validation
1. **Short-horizon LLM accuracy: ~50-60% directional** — matches our 56.4% hydro finding exactly
2. **LLM calibration failure** — matches our finding that conviction scores don't predict
3. **Bullish bias** — matches our "neutral hides bearish" problem
4. **Mechanical baselines win in thin markets** — matches our entire L-011

### Specialist vs generalist (Romeo's open question)
- Specialists beat generalists by 10-30% on **text classification** (sentiment, NER)
- **Neither beats rules on price direction**
- A narrow specialist LLM will NOT save us on the prediction task
- **It WILL help on feature extraction from Nepali text** (e.g., parsing NRB monetary policy PDFs into structured event tables)

### The optimal architecture for our situation
The literature converges on one architecture for thin emerging markets:

**LLM as feature extractor → mechanical model as decision maker → code-side calibration → mechanical portfolio construction.**

This is almost exactly what we are doing. Our corporate-action signals (book_closure drift) match the "From Limited Data to Rare-event Prediction" pattern. Our move to code-side calibration matches KalshiBench's solution. Our frozen-champion discipline matches the "extended reasoning worsens calibration" finding.

---

## Conclusion

**L-011 can now be cited as "strongly consistent with adjacent-market academic and industry literature."** It is no longer "we noticed this on NEPSE alone." It is "we observed something on NEPSE that is consistent with what 2024-2025 LLM-finance research keeps finding on adjacent markets."

**Important caveat:** No paper in this review tested NEPSE directly. The evidence is from US equities, Indian NIFTY, prediction markets, and similar venues. The inference that the pattern extends to Nepal is reasonable but unproven on our data.

**The honest update to L-011:** the door is not fully closed on LLMs. The published evidence says LLMs ARE useful for:
1. Text feature extraction from disclosures and filings
2. Sentiment classification (when fed appropriate language)
3. Hypothesis generation feeding mechanical backtests
4. Cross-checking each other (verification loop)

But they should NOT be the **trigger** for trading decisions. That is what mechanical signals are for.

---

## Master Source List

### Core Papers — "Mechanical beats LLM"
- When Reasoning Fails (arXiv 2511.08608): https://arxiv.org/abs/2511.08608
- StockBench (arXiv 2510.02209): https://arxiv.org/abs/2510.02209
- PriceSeer (arXiv 2601.06088): https://arxiv.org/abs/2601.06088
- Vidal (SSRN 4947135): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4947135
- The New Quant (arXiv 2510.05533): https://arxiv.org/abs/2510.05533
- Predictive Power of LLMs (arXiv 2411.16569): https://arxiv.org/html/2411.16569v1

### Lopez-Lira and Look-Ahead Bias
- Lopez-Lira & Tang (arXiv 2304.07619): https://arxiv.org/abs/2304.07619
- Lopez-Lira & Tang (SSRN): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4412788
- Glasserman & Lin (arXiv 2309.17322): https://arxiv.org/abs/2309.17322

### Calibration Failure
- KalshiBench (arXiv 2512.16030): https://arxiv.org/html/2512.16030
- FermiEval (arXiv 2510.26995): https://arxiv.org/html/2510.26995
- Verbalized Confidence (arXiv 2412.14737): https://arxiv.org/pdf/2412.14737
- Mind the Confidence Gap (arXiv 2502.11028): https://arxiv.org/html/2502.11028v1

### Where LLMs Add Value (Hybrid Systems)
- Evolution of Alpha (arXiv 2505.14727): https://arxiv.org/pdf/2505.14727
- ChatGPT in Systematic Investing (SSRN 5680782): https://papers.ssrn.com/sol3/Delivery.cfm/5680782.pdf
- Pelster & Val (SSRN 4602452): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=4602452
- From Limited Data (arXiv 2509.08140): https://arxiv.org/abs/2509.08140
- LLM Feature Selection (ScienceDirect): https://www.sciencedirect.com/science/article/pii/S2773186325001471

### Multi-Agent and Hybrid Systems
- TradingAgents (arXiv 2412.20138): https://arxiv.org/abs/2412.20138
- MarketSenseAI 2.0 (arXiv 2502.00415): https://arxiv.org/html/2502.00415v2
- LLM Agent Survey (arXiv 2408.06361): https://arxiv.org/html/2408.06361v1

### Industry Perspective
- Two Sigma 2026 Outlook Part I: https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-i/
- Two Sigma 2026 Outlook Part II: https://www.twosigma.com/articles/ai-in-investment-management-2026-outlook-part-ii/
- Institutional Investor: https://www.institutionalinvestor.com/article/2bswlvepw2hmezaphmcxs/opinion/the-most-powerful-artificial-intelligence-knows-nothing-about-investing-thats-perfectly-okay
- Digital Finance: https://www.digfingroup.com/genai-quants/

### Backtest Overfitting
- Harvey & Liu (SSRN 2345489): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=2345489
- Bailey et al.: https://sdm.lbl.gov/oapapers/ssrn-id2507040-bailey.pdf

### NEPSE-specific LSTM Attempts (For Reference — Not To Replicate)
- Sitaula et al. NEPSE LSTM: https://www.sciencedirect.com/science/article/pii/S2666827022000706
- Luitel — Nepalese Stock Market Predictive Analytics (SSRN 5030130): https://papers.ssrn.com/sol3/papers.cfm?abstract_id=5030130
