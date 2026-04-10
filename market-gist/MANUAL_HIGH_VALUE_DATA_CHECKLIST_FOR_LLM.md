# Manual High-Value Data Checklist For LLM

Use this when you want to manually give a stock setup to an LLM.

Goal:
- reduce entropy
- give the LLM only the highest-value context
- improve reasoning quality without dumping random data

Do not try to fill everything perfectly.
If a field is unknown, write `unknown`.

## Copy-Paste Template

```text
SYMBOL:
DATE:
PRIMARY_TIMEFRAME:
HORIZON:

1. Market Regime
- NEPSE 1D change:
- NEPSE 1W trend:
- NEPSE 1M trend:
- Market condition:
  trending_up / trending_down / choppy / high_volatility / unclear

2. Sector Regime
- Sector:
- Sector 1D change:
- Sector 1W trend:
- Sector 1M trend:
- Sector relative strength vs market:
  stronger / weaker / equal / unknown

3. Multi-Timeframe Structure
- 1M trend:
- 1M structure:
- 1W trend:
- 1W structure:
- 1D trend:
- 1D trigger/setup:
- Alignment:
  fully_aligned / mostly_aligned / mixed / conflicted

4. Current Technical Plan
- Current price:
- Key support zone:
- Key resistance zone:
- Breakout level:
- Invalidation level:
- Entry zone:
- Stop loss:
- Targets:
- Risk/reward:

5. Relative Strength
- Stock vs NEPSE on 1W:
- Stock vs sector on 1W:
- Stock vs NEPSE on 1D:
- Stock vs sector on 1D:
- Leader or laggard:

6. Liquidity / Tradability
- Daily traded value:
- Average traded value:
- Total trades:
- Liquidity quality:
  strong / acceptable / weak
- Spread/slippage concern:
  low / medium / high / unknown

7. Corporate Action / Event State
- Rights issue:
- Bonus:
- Dividend:
- Book closure:
- AGM:
- Listing notice:
- Other official notice:
- Event status:
  upcoming / active / recently_absorbed / none / unknown
- Is event likely to distort technicals?:
  yes / no / maybe

8. Broker / Floorsheet Context
- Buying concentrated or broad:
- Selling concentrated or broad:
- Signs of accumulation:
- Signs of distribution:
- Floorsheet confidence:
  high / medium / low / unknown

9. High-Level Fundamentals
- EPS trend:
- Book value trend:
- Recent quarterly result direction:
- Dilution/capital risk:
- Major quality red flag:

10. Similar Past Setup Context
- Have similar setups worked recently for this symbol?:
- Have similar setups worked recently for this sector?:
- Outcome confidence from history:
  high / medium / low / unknown

11. Main Uncertainties
- Biggest uncertainty 1:
- Biggest uncertainty 2:
- Biggest uncertainty 3:

Task:
Based on the above data, give:
1. final action: buy / watch_only / avoid
2. confidence out of 100
3. strongest reason for the decision
4. strongest risk against the decision
5. whether the setup is early, valid, extended, or low-quality
6. whether the trade plan is practical in the real market
7. what must happen next to upgrade confidence
```

## Most Important Fields

If you are in a hurry, fill these first:

1. Market regime
2. Sector regime
3. 1M / 1W / 1D alignment
4. Entry / stop / invalidation / targets
5. Liquidity quality
6. Corporate-action status
7. Broker/floorsheet context
8. Main uncertainties

## What Usually Improves LLM Output The Most

These tend to matter more than extra indicators:

- corporate-action state
- multi-timeframe alignment
- liquidity/tradability
- sector relative strength
- broker/floorsheet concentration
- similar past setup outcomes

## What Not To Overload The LLM With

Avoid dumping:

- too many indicators
- every candle detail
- random annotations
- decorative chart tool output
- long unstructured market commentary

Prefer:

- short structured facts
- explicit uncertainty
- clear regime labels
- clean trade plan

## Recommended Workflow

1. Use your automation output first.
2. Add the missing high-value fields manually.
3. Paste the completed template into the LLM.
4. Save the LLM answer beside the system decision if it is useful.
