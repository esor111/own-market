"""
One-time script: Generate 20 forced-binary prompts for the neutral-elimination experiment.
These are the same replay cases where agents originally called neutral and were wrong.
The only change: "neutral" is removed from direction options, and Rule 7 forces binary choice.
"""

import json
import os
import glob

CASES = [
    ("2023-07-06", "UPPER"),
    ("2024-07-16", "UPPER"),
    ("2024-07-23", "JBBL"),
    ("2024-08-06", "UPPER"),
    ("2024-08-18", "NABIL"),
    ("2025-07-06", "JBBL"),
    ("2025-07-20", "AKPL"),
    ("2025-08-03", "AKPL"),
    ("2025-10-01", "API"),
    ("2025-10-02", "NABIL"),
    ("2025-10-02", "UPPER"),
    ("2025-10-06", "EBL"),
    ("2025-10-09", "EBL"),
    ("2025-11-02", "JBBL"),
    ("2025-11-04", "SANIMA"),
    ("2025-11-05", "AKPL"),
    ("2025-11-16", "EBL"),
    ("2025-12-16", "SANIMA"),
    ("2025-12-21", "SANIMA"),
    ("2025-12-30", "API"),
]

BASE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(BASE)

with open(os.path.join(BASE, "sector_map.json")) as f:
    SECTOR_MAP = json.load(f)

with open(os.path.join(ROOT, "data", "macro_context.json")) as f:
    MACRO = json.load(f)

REPLAY_DIRS = glob.glob(os.path.join(ROOT, "data", "replays", "*", "sessions"))
TEMPLATE_PATH = os.path.join(ROOT, "docs", "playbooks", "LLM_PREDICTION_PROMPT.md")
OUT_DIR = os.path.join(ROOT, "agents", "agent-2-juliet", "prompts", "forced_binary_experiment")
os.makedirs(OUT_DIR, exist_ok=True)


def find_frozen_case(date, symbol):
    for rd in REPLAY_DIRS:
        p = os.path.join(rd, date, symbol, "normalized", f"{date}__{symbol}__frozen_case_v1.json")
        if os.path.exists(p):
            return p
    return None


def frozen_case_to_context(fc):
    m = fc.get("metrics", {})
    lt = fc.get("latest_row", {})
    sym = fc.get("symbol", "?")
    dt = fc.get("session_date", "?")
    sec = SECTOR_MAP.get(sym, "UNKNOWN")

    above_sma20 = "above" if m.get("close_price", 0) > (m.get("sma20") or 0) else "below"
    above_sma50 = "above" if m.get("close_price", 0) > (m.get("sma50") or 0) else "below"

    lines = [
        f"# Market Context Package: {sym} (Replay Case)",
        f"Date: {dt}",
        f"Sector: {sec}",
        "Source: Historical replay (truth-layer data only, no browser)",
        "",
        "## 1. Stock Data",
        f"- Symbol: {sym}",
        f"- Close price: {m.get('close_price', 'unknown')}",
        f"- 1-day return: {m.get('return_1d_pct', 'unknown')}%",
        f"- 5-day return: {m.get('return_5d_pct', 'unknown')}%",
        f"- 20-day return: {m.get('return_20d_pct', 'unknown')}%",
        f"- SMA 10: {m.get('sma10', 'unknown')}",
        f"- SMA 20: {m.get('sma20', 'unknown')}",
        f"- SMA 50: {m.get('sma50', 'unknown')}",
        f"- Price vs SMA20: {above_sma20}",
        f"- Price vs SMA50: {above_sma50}",
        "",
        "## 2. Trend & Structure",
        f"- Trend label: {m.get('trend_label', 'unknown')}",
        f"- Close position in 20d range: {m.get('close_position_20d', 'unknown')}",
        f"- Close position in 60d range: {m.get('close_position_60d', 'unknown')}",
        f"- 20-day resistance: {m.get('resistance_20d', 'unknown')}",
        f"- 10-day support: {m.get('support_10d', 'unknown')}",
        f"- 60-day resistance: {m.get('resistance_60d', 'unknown')}",
        f"- 60-day support: {m.get('support_60d', 'unknown')}",
        "",
        "## 3. Liquidity",
        f"- Liquidity label: {m.get('liquidity_label', 'unknown')}",
        f"- Avg traded value (5d): {m.get('avg_value_5d', 'unknown')}",
        f"- Avg traded value (20d): {m.get('avg_value_20d', 'unknown')}",
        f"- Avg trades (5d): {m.get('avg_trades_5d', 'unknown')}",
        f"- Avg trades (20d): {m.get('avg_trades_20d', 'unknown')}",
        f"- Volume ratio (5d vs 20d): {m.get('volume_ratio_5d', 'unknown')}",
        "",
        "## 4. Latest Bar",
        f"- Open: {lt.get('openPrice', 'unknown')}",
        f"- High: {lt.get('highPrice', 'unknown')}",
        f"- Low: {lt.get('lowPrice', 'unknown')}",
        f"- Close: {lt.get('closePrice', 'unknown')}",
        f"- Total traded value: {lt.get('totalTradedValue', 'unknown')}",
        f"- Total trades: {lt.get('totalTrades', 'unknown')}",
        f"- 52-week high: {lt.get('fiftyTwoWeekHigh', 'unknown')}",
        f"- 52-week low: {lt.get('fiftyTwoWeekLow', 'unknown')}",
        "",
        "## 5. Data Quality",
        f"- History bars available: {fc.get('data_quality', {}).get('history_bar_count', 'unknown')}",
        f"- Full 20d context: {fc.get('data_quality', {}).get('has_full_20d_context', 'unknown')}",
        f"- Full 60d context: {fc.get('data_quality', {}).get('has_full_60d_context', 'unknown')}",
    ]

    hist = fc.get("historical_context", {})
    if hist:
        lines.extend(["", "## 6. Historical Context"])
        reg = hist.get("regime_context", {})
        if reg:
            lines.append(f"- Market regime: {reg.get('market_regime', 'unknown')}")
            lines.append(f"- Sector regime: {reg.get('sector_regime', 'unknown')}")
            lines.append(f"- Alignment: {reg.get('alignment_label', 'unknown')}")
        cal = hist.get("calendar_context", {})
        if cal:
            fl = cal.get("calendar_flags", {})
            lines.append(f"- Calendar phase: {fl.get('phase_labels', 'unknown')}")
            lines.append(f"- Hostile window: {fl.get('is_hostile_window', 'unknown')}")
        ev = hist.get("event_context", {})
        if ev:
            lines.append(f"- Event match: {ev.get('event_status', 'unknown')}")
            lines.append(f"- Event type: {ev.get('event_type', 'unknown')}")

    lines.extend([
        "",
        "## Notes",
        "- This is a replay case with truth-layer data only (no browser screenshots or broker flow).",
        "- The market, sector, and indicator data come from historical CSV records.",
        "- Your prediction will be scored against what actually happened after this date.",
    ])
    return "\n".join(lines)


def build_macro_block(date, sector):
    month = int(date.split("-")[1])
    if month in (7, 8):
        seasonal = "PEAK SEASON (July-August). Fiscal year end, earnings, dividends. Historically strongest period."
    elif month in (9, 10):
        seasonal = "Secondary season (Sep-Oct). Dividend book-closure buying. Moderate strength."
    elif month in (11, 12):
        seasonal = "Post-season (Nov-Dec). Declining seasonal support. Often consolidation or correction."
    else:
        seasonal = "Quiet season."

    sector_notes = {
        "COMMERCIAL BANKS": "Heavyweight sector, 40-50% of market cap. Moves with NEPSE index.",
        "DEVELOPMENT BANKS": "Mid-weight sector. More volatile than commercial banks. Watch for extension patterns.",
        "HYDROPOWER": "Mid-weight sector. More volatile than banking. Watch for project-specific catalysts.",
    }
    sec_note = sector_notes.get(sector, "Unknown sector.")

    lines = [
        f"Date: {date}",
        f"Seasonal position: {seasonal}",
        f"Sector: {sector} sector. {sec_note}",
        "",
        "Current macro signals (manually maintained):",
    ]
    for k, v in MACRO.get("signals", {}).items():
        val = v.get("value", "unknown")
        note = v.get("note", "")
        lines.append(f"  - {k}: {val} - {note}")
    return "\n".join(lines)


def main():
    with open(TEMPLATE_PATH, encoding="utf-8") as f:
        base_template = f.read()

    # Modify template: remove neutral
    base_template = base_template.replace(
        '"direction": "bullish | bearish | neutral"',
        '"direction": "bullish | bearish"',
    )

    # Add forced binary rule
    rule_7 = (
        "7. FORCED BINARY: You must choose either bullish or bearish. "
        "There is no neutral option. If you are genuinely uncertain, pick the "
        "direction that is MORE LIKELY even if your conviction is low. "
        "A low-conviction directional call (e.g., bearish at conviction 25) is "
        "more useful than hedging. Express uncertainty through conviction level, "
        "not direction."
    )
    base_template = base_template.replace(
        "6. Focus your analysis on REASONING QUALITY:",
        "6. Focus your analysis on REASONING QUALITY:",
    )
    # Insert Rule 7 after Rule 6 line
    base_template = base_template.replace(
        "These matter more than the conviction number.\n",
        "These matter more than the conviction number.\n" + rule_7 + "\n",
    )

    generated = 0
    for date, symbol in CASES:
        fc_path = find_frozen_case(date, symbol)
        if not fc_path:
            print(f"MISSING: {date} {symbol}")
            continue

        with open(fc_path) as f:
            fc_data = json.load(f)

        sector = SECTOR_MAP.get(symbol, "UNKNOWN")
        context = frozen_case_to_context(fc_data)
        macro_block = build_macro_block(date, sector)

        prompt = base_template
        prompt = prompt.replace("{{MACRO_CONTEXT_BLOCK}}", macro_block)
        prompt = prompt.replace("{{CONTEXT_PACKAGE}}", context)
        prompt = prompt.replace(
            "{{SIMILAR_SETUPS_BLOCK}}",
            "No similar past setups available (curated replay basket mode).",
        )
        prompt = prompt.replace(
            "{{CALIBRATION_BLOCK}}",
            "No calibration data provided for this experiment. Output your genuine raw prediction.",
        )

        fname = f"{date}__{symbol}__forced_binary_prompt.md"
        with open(os.path.join(OUT_DIR, fname), "w", encoding="utf-8") as f:
            f.write(prompt)
        generated += 1
        print(f"  [{generated:2d}] {date} {symbol}")

    print(f"\nGenerated {generated}/20 prompts in {OUT_DIR}/")


if __name__ == "__main__":
    main()
