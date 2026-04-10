"""
Inject broker flow ledger data into an LLM prediction prompt.

Usage:
    python inject_broker_flow_into_prompt.py SYMBOL DATE
    python inject_broker_flow_into_prompt.py NABIL 2025-12-01

This reads the broker flow ledger for SYMBOL on DATE and generates a
"Broker Flow Context" block that can be injected into the prediction prompt.

The LLM sees: who is buying/selling, how concentrated the flow is,
activity patterns, and accumulation/distribution signals.
These are things a simple price/volume rule CANNOT process.
"""

import json
import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parent
LEDGER_ROOT = BASE.parent / "broker_flow_ledger"


def load_broker_flow(symbol: str, date: str) -> dict | None:
    """Load the broker flow ledger for a symbol on a given date."""
    ledger_path = LEDGER_ROOT / symbol / f"{date}.json"
    if not ledger_path.exists():
        return None
    with open(ledger_path) as f:
        return json.load(f)


def broker_flow_to_context_block(ledger: dict) -> str:
    """Convert a broker flow ledger into a prompt-injectable context block."""
    ds = ledger.get("derived_snapshot", {})
    raw = ledger.get("raw_snapshot", {})
    fs = raw.get("floorsheet", {})
    edge = raw.get("broker_edge_summary", {})

    symbol = ledger.get("symbol", "?")
    date = ledger.get("run_date", "?")

    # Core signals
    activity = ds.get("activity_label", "unknown")
    phase = ds.get("phase_hint", "unknown")
    concentration = ds.get("concentration_signal", "unknown")
    closing_flow = ds.get("closing_flow") or "unknown"

    # Buyer/seller concentration
    buyer_top3 = ds.get("buyer_top3_concentration_pct")
    seller_top3 = ds.get("seller_top3_concentration_pct")
    buyer_count = ds.get("visible_buyer_count")
    seller_count = ds.get("visible_seller_count")

    # Top brokers
    top_buyer = ds.get("top_buyer_broker", "unknown")
    top_seller = ds.get("top_seller_broker", "unknown")

    # Same broker buying and selling = possible wash / market making
    same_top = top_buyer == top_seller and top_buyer != "unknown"

    # Volume
    turnover = ds.get("total_turnover")
    qty = ds.get("total_traded_quantity")
    txns = ds.get("total_transactions")

    # Holdings signals
    weekly_hold = ds.get("weekly_holdings_signal", "unknown")
    monthly_hold = ds.get("monthly_holdings_signal", "unknown")
    hold_change = ds.get("holding_change_signal", "unknown")

    # Build buyer/seller summary from raw data
    buyer_rows = fs.get("buyer_side", {}).get("rows", [])
    seller_rows = fs.get("seller_side", {}).get("rows", [])

    lines = [
        f"## Broker Flow Context: {symbol} ({date})",
        f"Source: Merolagani floorsheet (daily broker-level transaction data)",
        "",
        "### Activity Summary",
        f"- Activity label: {activity}",
        f"- Phase hint: {phase}",
        f"- Concentration signal: {concentration}",
        f"- Closing flow (last 15 min): {closing_flow}",
        "",
        "### Buyer Side",
        f"- Unique buyer brokers: {buyer_count}",
        f"- Top 3 buyer concentration: {buyer_top3}%" if buyer_top3 else "- Top 3 buyer concentration: unknown",
        f"- Top buyer broker: #{top_buyer}" if top_buyer != "unknown" else "- Top buyer broker: unknown",
    ]

    if buyer_rows:
        lines.append(f"- Top 5 buyers:")
        for row in buyer_rows[:5]:
            lines.append(f"    Broker #{row['broker']}: {row['qty']} shares ({row['share_pct']}%) at avg {row.get('avg_price', '?')}")

    lines.extend([
        "",
        "### Seller Side",
        f"- Unique seller brokers: {seller_count}",
        f"- Top 3 seller concentration: {seller_top3}%" if seller_top3 else "- Top 3 seller concentration: unknown",
        f"- Top seller broker: #{top_seller}" if top_seller != "unknown" else "- Top seller broker: unknown",
    ])

    if seller_rows:
        lines.append(f"- Top 5 sellers:")
        for row in seller_rows[:5]:
            lines.append(f"    Broker #{row['broker']}: {row['qty']} shares ({row['share_pct']}%) at avg {row.get('avg_price', '?')}")

    lines.extend([
        "",
        "### Flow Interpretation Signals",
        f"- Same broker is top buyer AND seller: {'YES — possible market making or wash' if same_top else 'No'}",
        f"- Weekly holdings signal: {weekly_hold}",
        f"- Monthly holdings signal: {monthly_hold}",
        f"- Holding change signal: {hold_change}",
    ])

    if turnover:
        lines.extend([
            "",
            "### Volume",
            f"- Total turnover: NPR {turnover:,.0f}",
            f"- Total traded quantity: {qty:,}" if qty else "",
            f"- Total transactions: {txns}" if txns else "",
        ])

    lines.extend([
        "",
        "### How to Use This Data",
        "- Concentrated buying (top 3 > 40%) with broad selling = potential accumulation by informed players",
        "- Concentrated selling (top 3 > 40%) with broad buying = potential distribution",
        "- Same broker as top buyer and seller = likely market making, not directional signal",
        "- High transaction count with balanced concentration = genuine market participation",
        "- Low transaction count with high concentration = few large players dominating",
        "- This data tells you WHO is trading, not just WHAT the price did. Use it to assess whether the price action is backed by informed flow or retail noise.",
    ])

    return "\n".join(line for line in lines if line is not None)


def main():
    if len(sys.argv) < 3:
        print("Usage: python inject_broker_flow_into_prompt.py SYMBOL DATE")
        print("Example: python inject_broker_flow_into_prompt.py NABIL 2026-03-30")
        sys.exit(1)

    symbol = sys.argv[1].upper()
    date = sys.argv[2]

    ledger = load_broker_flow(symbol, date)
    if ledger is None:
        print(f"No broker flow ledger found for {symbol} on {date}")
        print(f"Expected: {LEDGER_ROOT / symbol / f'{date}.json'}")
        print()
        print("To backfill historical data:")
        print(f"  python backfill_merolagani_floorsheet.py --symbol {symbol} --start-date {date} --end-date {date}")
        sys.exit(1)

    block = broker_flow_to_context_block(ledger)
    print(block)


if __name__ == "__main__":
    main()
