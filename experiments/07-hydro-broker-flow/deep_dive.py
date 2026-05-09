from __future__ import annotations

import argparse
import csv
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from statistics import mean
from typing import Any


SCRIPT_DIR = Path(__file__).resolve().parent
ROOT_DIR = SCRIPT_DIR.parents[1]
CONFIG_PATH = SCRIPT_DIR / "config.json"
DATA_DIR = SCRIPT_DIR / "data"
RESULTS_DIR = SCRIPT_DIR / "results"
DAILY_CSV = DATA_DIR / "hydro_broker_flow_daily.csv"
RAW_FLOORSHEET_DIR = ROOT_DIR / "market-gist" / "broker_flow_ledger" / "raw_merolagani"


PATTERN_COLUMNS = [
    "high_volume_up",
    "high_volume_down",
    "buyer_concentrated",
    "seller_concentrated",
    "supply_pressure",
    "absorption_attempt",
    "failed_rally_candidate",
    "two_sided_churn",
    "distribution_like",
    "accumulation_like",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Focus-symbol deep dive over the hydro broker-flow dataset.")
    parser.add_argument("--focus", default="UPPER", help="Symbol to treat as the case study (default UPPER).")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    focus = args.focus.upper().strip()
    focus_lower = focus.lower()

    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    symbols = [symbol.upper() for symbol in config["symbols"]]
    if focus not in symbols:
        raise SystemExit(f"--focus {focus} is not in config.symbols ({symbols}).")

    rows = read_csv(DAILY_CSV)
    rows_by_symbol = {symbol: sorted([row for row in rows if row["symbol"] == symbol], key=lambda row: row["date"]) for symbol in symbols}
    common_dates = current_common_dates(rows_by_symbol, symbols)
    if not common_dates:
        raise SystemExit("No common broker-flow dates found.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    phase_rows = build_phase_summary(rows_by_symbol, symbols, common_dates)
    focus_recent_rows = build_focus_recent_rows(rows_by_symbol[focus], common_dates)
    broker_rows = build_broker_persistence(focus, rows_by_symbol[focus], common_dates)
    markdown = build_markdown(focus, phase_rows, focus_recent_rows, broker_rows, common_dates)
    as_of = focus_recent_rows[-1]["date"] if focus_recent_rows else common_dates[-1]
    trade_plan_md = build_trade_plan(
        focus=focus,
        as_of=as_of,
        phase_rows=phase_rows,
        focus_rows_in_window=[row for row in rows_by_symbol[focus] if row["date"] in set(common_dates)],
        broker_rows=broker_rows,
        recent_tape_rows=focus_recent_rows,
    )

    phase_path = DATA_DIR / "phase_summary.csv"
    recent_path = DATA_DIR / f"{focus_lower}_recent_days.csv"
    broker_path = DATA_DIR / f"{focus_lower}_broker_persistence.csv"
    iteration_path = RESULTS_DIR / f"{focus_lower}_deep_iteration.md"
    trade_plan_path = RESULTS_DIR / f"{focus_lower}_trade_plan_{as_of}.md"

    write_csv(phase_path, phase_rows)
    write_csv(recent_path, focus_recent_rows)
    write_csv(broker_path, broker_rows)
    iteration_path.write_text(markdown, encoding="utf-8")
    trade_plan_path.write_text(trade_plan_md, encoding="utf-8")

    if focus == "UPPER":
        write_csv(DATA_DIR / "broker_persistence.csv", broker_rows)
        (RESULTS_DIR / "deep_iteration.md").write_text(markdown, encoding="utf-8")

    print(f"Wrote {phase_path} ({len(phase_rows)} rows)")
    print(f"Wrote {recent_path} ({len(focus_recent_rows)} rows)")
    print(f"Wrote {broker_path} ({len(broker_rows)} rows)")
    print(f"Wrote {iteration_path}")
    print(f"Wrote {trade_plan_path}")
    return 0


def read_csv(path: Path) -> list[dict[str, Any]]:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return list(csv.DictReader(handle))


def write_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    if not rows:
        path.write_text("", encoding="utf-8")
        return
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)


def current_common_dates(rows_by_symbol: dict[str, list[dict[str, Any]]], symbols: list[str]) -> list[str]:
    date_sets = []
    for symbol in symbols:
        date_sets.append({row["date"] for row in rows_by_symbol[symbol] if row.get("broker_available") == "1"})
    return sorted(set.intersection(*date_sets))


def build_phase_summary(
    rows_by_symbol: dict[str, list[dict[str, Any]]],
    symbols: list[str],
    common_dates: list[str],
) -> list[dict[str, Any]]:
    output = []
    common_date_set = set(common_dates)
    for symbol in symbols:
        rows = [row for row in rows_by_symbol[symbol] if row["date"] in common_date_set]
        peak_idx, peak = max(enumerate(rows), key=lambda item: as_float(item[1].get("close")) or 0)
        first = rows[0]
        last = rows[-1]
        post_peak_rows = rows[peak_idx + 1 :]
        output.append({
            "symbol": symbol,
            "window_start": rows[0]["date"],
            "window_end": rows[-1]["date"],
            "days": len(rows),
            "start_close": first["close"],
            "peak_date": peak["date"],
            "peak_close": peak["close"],
            "latest_close": last["close"],
            "window_return_pct": pct_change(first.get("close"), last.get("close")),
            "rally_to_peak_pct": pct_change(first.get("close"), peak.get("close")),
            "post_peak_return_pct": pct_change(peak.get("close"), last.get("close")),
            "post_peak_days": len(post_peak_rows),
            "post_peak_down_days": count_condition(post_peak_rows, lambda row: (as_float(row.get("return_pct")) or 0) < 0),
            "post_peak_supply_pressure_days": count_flag(post_peak_rows, "supply_pressure"),
            "post_peak_absorption_days": count_flag(post_peak_rows, "absorption_attempt"),
            "post_peak_distribution_days": count_flag(post_peak_rows, "distribution_like"),
            "post_peak_accumulation_days": count_flag(post_peak_rows, "accumulation_like"),
            "avg_post_peak_buyer_top3_pct": avg(row.get("top3_buyer_pct") for row in post_peak_rows),
            "avg_post_peak_seller_top3_pct": avg(row.get("top3_seller_pct") for row in post_peak_rows),
            "latest_labels": labels_for(last),
        })
    return sorted(output, key=lambda row: as_float(row.get("window_return_pct")) or 0, reverse=True)


def build_focus_recent_rows(rows: list[dict[str, Any]], common_dates: list[str]) -> list[dict[str, Any]]:
    common_date_set = set(common_dates)
    selected = [row for row in rows if row["date"] in common_date_set][-15:]
    output = []
    for row in selected:
        output.append({
            "date": row["date"],
            "close": row["close"],
            "return_pct": row["return_pct"],
            "volume_ratio_20d": row["volume_ratio_20d"],
            "raw_rows": row["raw_rows"],
            "top3_buyer_pct": row["top3_buyer_pct"],
            "top3_seller_pct": row["top3_seller_pct"],
            "buyer_seller_top3_gap": row["buyer_seller_top3_gap"],
            "top_net_buyers": row["top_net_buyers"],
            "top_net_sellers": row["top_net_sellers"],
            "labels": labels_for(row),
        })
    return output


def build_broker_persistence(
    symbol: str,
    symbol_rows: list[dict[str, Any]],
    common_dates: list[str],
) -> list[dict[str, Any]]:
    common_date_set = set(common_dates)
    common_rows = [row for row in symbol_rows if row["date"] in common_date_set]
    peak_idx, peak = max(enumerate(common_rows), key=lambda item: as_float(item[1].get("close")) or 0)
    periods = {
        "common_window": [row["date"] for row in common_rows],
        "rally_to_peak": [row["date"] for row in common_rows[: peak_idx + 1]],
        "pullback_after_peak": [row["date"] for row in common_rows[peak_idx + 1 :]],
        "last_10_broker_days": [row["date"] for row in common_rows[-10:]],
        "last_5_broker_days": [row["date"] for row in common_rows[-5:]],
    }

    output = []
    for period, dates in periods.items():
        aggregate = aggregate_brokers(symbol, dates)
        ranked_buyers = sorted(aggregate.items(), key=lambda item: item[1]["net_qty"], reverse=True)
        ranked_sellers = sorted(aggregate.items(), key=lambda item: item[1]["net_qty"])
        for side, ranked in [("net_buy", ranked_buyers), ("net_sell", ranked_sellers)]:
            for rank, (broker, item) in enumerate(ranked[:10], start=1):
                net_qty = int(item["net_qty"])
                if side == "net_buy" and net_qty <= 0:
                    continue
                if side == "net_sell" and net_qty >= 0:
                    continue
                gross_qty = int(item["buy_qty"] + item["sell_qty"])
                output.append({
                    "symbol": symbol,
                    "period": period,
                    "start_date": dates[0] if dates else "",
                    "end_date": dates[-1] if dates else "",
                    "dates": len(dates),
                    "side": side,
                    "rank": rank,
                    "broker": broker,
                    "buy_qty": int(item["buy_qty"]),
                    "sell_qty": int(item["sell_qty"]),
                    "net_qty": net_qty,
                    "gross_qty": gross_qty,
                    "net_to_gross_pct": round_float((abs(net_qty) / gross_qty) * 100 if gross_qty else None),
                })
    return output


def aggregate_brokers(symbol: str, dates: list[str]) -> dict[str, dict[str, float]]:
    aggregate: dict[str, dict[str, float]] = defaultdict(lambda: {"buy_qty": 0.0, "sell_qty": 0.0, "net_qty": 0.0})
    for business_date in dates:
        path = RAW_FLOORSHEET_DIR / symbol / f"{business_date}.json"
        if not path.exists():
            continue
        payload = json.loads(path.read_text(encoding="utf-8"))
        for row in payload.get("rows") or []:
            qty = parse_int(row.get("quantity"))
            buyer = str(row.get("buyer_broker") or "").strip()
            seller = str(row.get("seller_broker") or "").strip()
            if buyer:
                aggregate[buyer]["buy_qty"] += qty
                aggregate[buyer]["net_qty"] += qty
            if seller:
                aggregate[seller]["sell_qty"] += qty
                aggregate[seller]["net_qty"] -= qty
    return aggregate


def build_markdown(
    focus: str,
    phase_rows: list[dict[str, Any]],
    focus_recent_rows: list[dict[str, Any]],
    broker_rows: list[dict[str, Any]],
    common_dates: list[str],
) -> str:
    focus_phase = next(row for row in phase_rows if row["symbol"] == focus)
    pullback_buyers = top_period_rows(broker_rows, "pullback_after_peak", "net_buy", 5)
    pullback_sellers = top_period_rows(broker_rows, "pullback_after_peak", "net_sell", 5)
    last5_buyers = top_period_rows(broker_rows, "last_5_broker_days", "net_buy", 5)
    last5_sellers = top_period_rows(broker_rows, "last_5_broker_days", "net_sell", 5)

    lines = [
        "# Hydro Broker-Flow Deep Iteration",
        "",
        f"Focus symbol: `{focus}`",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        f"Common peer window with real broker rows: `{common_dates[0]}` to `{common_dates[-1]}` ({len(common_dates)} dates).",
        "",
        f"## {focus} Phase Read",
        "",
        f"- Window return: `{focus_phase['window_return_pct']}`% from `{focus_phase['start_close']}` to `{focus_phase['latest_close']}`.",
        f"- Peak: `{focus_phase['peak_close']}` on `{focus_phase['peak_date']}`.",
        f"- Post-peak move: `{focus_phase['post_peak_return_pct']}`% over `{focus_phase['post_peak_days']}` broker-backed dates.",
        f"- Post-peak pressure mix: `{focus_phase['post_peak_supply_pressure_days']}` supply-pressure days, `{focus_phase['post_peak_absorption_days']}` absorption days, `{focus_phase['post_peak_distribution_days']}` distribution-like days, `{focus_phase['post_peak_accumulation_days']}` accumulation-like days.",
        f"- Latest labels: `{focus_phase['latest_labels']}`.",
        "",
        f"Interpretation: read the pressure mix and latest labels together. A clean accumulation would show absorption-days outweighing distribution-days and the latest label leaning accumulation_like. Clean distribution would show persistent supply_pressure with no meaningful bid. Anything in between is a contested post-peak regime.",
        "",
        "## Peer Phase Ranking",
        "",
        "| Symbol | Window return | Peak date | Post-peak return | Supply | Absorb | Distribution | Accumulation | Latest labels |",
        "|---|---:|---|---:|---:|---:|---:|---:|---|",
    ]
    for row in phase_rows:
        lines.append(
            f"| {row['symbol']} | {row['window_return_pct']}% | {row['peak_date']} | "
            f"{row['post_peak_return_pct']}% | {row['post_peak_supply_pressure_days']} | "
            f"{row['post_peak_absorption_days']} | {row['post_peak_distribution_days']} | "
            f"{row['post_peak_accumulation_days']} | {row['latest_labels']} |"
        )

    lines.extend([
        "",
        f"## {focus} Pullback Broker Net",
        "",
        "Top net buyers after the peak:",
        "",
    ])
    lines.extend(format_broker_list(pullback_buyers))
    lines.extend(["", "Top net sellers after the peak:", ""])
    lines.extend(format_broker_list(pullback_sellers))
    lines.extend(["", f"## {focus} Last 5 Broker Days", "", "Top recent net buyers:", ""])
    lines.extend(format_broker_list(last5_buyers))
    lines.extend(["", "Top recent net sellers:", ""])
    lines.extend(format_broker_list(last5_sellers))

    lines.extend([
        "",
        f"## Recent {focus} Tape",
        "",
        "| Date | Close | Return | Vol ratio | Rows | B3/S3 | Labels |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in focus_recent_rows:
        lines.append(
            f"| {row['date']} | {row['close']} | {row['return_pct']}% | {row['volume_ratio_20d']} | "
            f"{row['raw_rows']} | {row['top3_buyer_pct']}/{row['top3_seller_pct']} | {row['labels']} |"
        )

    lines.extend([
        "",
        "## Working Verdict",
        "",
        "- Clean accumulation would usually show repeated absorption days, improving closes, and less urgent seller concentration.",
        "- Clean distribution would usually show persistent high-volume sell pressure and no meaningful bid.",
        f"- Read the `{focus.lower()}_trade_plan_*.md` file in this folder for the mechanical trade plan derived from this deep dive.",
    ])
    return "\n".join(lines) + "\n"


def build_trade_plan(
    focus: str,
    as_of: str,
    phase_rows: list[dict[str, Any]],
    focus_rows_in_window: list[dict[str, Any]],
    broker_rows: list[dict[str, Any]],
    recent_tape_rows: list[dict[str, Any]],
) -> str:
    """Produce a mechanical, evidence-anchored trade plan. Research, not advice.

    Level derivation rules:
      - support_price   = min(low)  over last 20 sessions
      - resistance_price= max(high) over last 20 sessions
      - add_trigger     = round(resistance_price * 1.005, 2)  -> close above recent high
      - invalidation    = round(support_price    * 0.97,  2)  -> 3% break of support
      - wait_zone       = [support_price, resistance_price]
    Confidence score is rule-based, bounded to LOW/MEDIUM/HIGH.
    """
    focus_phase = next(row for row in phase_rows if row["symbol"] == focus)
    last_20 = focus_rows_in_window[-20:] if len(focus_rows_in_window) >= 1 else []
    lows = [as_float(row.get("low")) for row in last_20]
    highs = [as_float(row.get("high")) for row in last_20]
    closes = [as_float(row.get("close")) for row in last_20]
    lows = [value for value in lows if value is not None]
    highs = [value for value in highs if value is not None]
    closes = [value for value in closes if value is not None]

    support_price = round(min(lows), 2) if lows else None
    resistance_price = round(max(highs), 2) if highs else None
    current_close = closes[-1] if closes else as_float(focus_phase.get("latest_close"))
    add_trigger = round(resistance_price * 1.005, 2) if resistance_price else None
    invalidation = round(support_price * 0.97, 2) if support_price else None

    supply_days = parse_int(focus_phase.get("post_peak_supply_pressure_days"))
    absorb_days = parse_int(focus_phase.get("post_peak_absorption_days"))
    dist_days = parse_int(focus_phase.get("post_peak_distribution_days"))
    acc_days = parse_int(focus_phase.get("post_peak_accumulation_days"))
    avg_buy_top3 = as_float(focus_phase.get("avg_post_peak_buyer_top3_pct")) or 0.0
    avg_sell_top3 = as_float(focus_phase.get("avg_post_peak_seller_top3_pct")) or 0.0
    latest_labels = focus_phase.get("latest_labels") or ""
    post_peak_ret = as_float(focus_phase.get("post_peak_return_pct")) or 0.0

    signals: list[tuple[str, int, str]] = []
    signals.append((
        "post_peak_pressure_mix",
        +1 if absorb_days + acc_days > supply_days + dist_days else
        -1 if supply_days + dist_days > absorb_days + acc_days else 0,
        f"absorb+acc={absorb_days + acc_days} vs supply+dist={supply_days + dist_days}",
    ))
    signals.append((
        "broker_concentration_lean",
        +1 if avg_buy_top3 - avg_sell_top3 > 1.5 else
        -1 if avg_sell_top3 - avg_buy_top3 > 1.5 else 0,
        f"avg buyer top3 {avg_buy_top3:.2f}% vs seller {avg_sell_top3:.2f}%",
    ))
    signals.append((
        "post_peak_return",
        +1 if post_peak_ret >= -3 else -1 if post_peak_ret < -10 else 0,
        f"post_peak_return={post_peak_ret:.2f}%",
    ))
    bull_labels = {"accumulation_like", "absorption_attempt"}
    bear_labels = {"supply_pressure", "failed_rally_candidate", "distribution_like"}
    latest_label_set = {label.strip() for label in latest_labels.split(",") if label.strip()}
    signals.append((
        "latest_label_tilt",
        +1 if latest_label_set & bull_labels and not latest_label_set & bear_labels else
        -1 if latest_label_set & bear_labels and not latest_label_set & bull_labels else 0,
        f"latest={sorted(latest_label_set) or ['none']}",
    ))

    recent_supply = sum(1 for row in recent_tape_rows if "supply_pressure" in (row.get("labels") or ""))
    recent_absorb = sum(1 for row in recent_tape_rows if "absorption_attempt" in (row.get("labels") or ""))
    signals.append((
        "recent_tape_tilt",
        +1 if recent_absorb > recent_supply else -1 if recent_supply > recent_absorb else 0,
        f"last {len(recent_tape_rows)} sessions: supply={recent_supply}, absorb={recent_absorb}",
    ))

    score = sum(direction for _, direction, _ in signals)
    agree_count = sum(1 for _, direction, _ in signals if direction != 0 and (direction > 0) == (score > 0))
    if score >= 3:
        bias = "LEAN BULLISH (contested)"
    elif score <= -3:
        bias = "LEAN BEARISH (contested)"
    elif score > 0:
        bias = "SLIGHT BULLISH TILT"
    elif score < 0:
        bias = "SLIGHT BEARISH TILT"
    else:
        bias = "NEUTRAL / CONTESTED"

    abs_score = abs(score)
    confidence = "LOW" if abs_score <= 1 else "MEDIUM" if abs_score <= 3 else "HIGH"

    last5_buyers = top_period_rows(broker_rows, "last_5_broker_days", "net_buy", 5)
    last5_sellers = top_period_rows(broker_rows, "last_5_broker_days", "net_sell", 5)
    last10_buyers = top_period_rows(broker_rows, "last_10_broker_days", "net_buy", 5)
    last10_sellers = top_period_rows(broker_rows, "last_10_broker_days", "net_sell", 5)
    pullback_buyers = top_period_rows(broker_rows, "pullback_after_peak", "net_buy", 5)
    pullback_sellers = top_period_rows(broker_rows, "pullback_after_peak", "net_sell", 5)

    if score > 0:
        phase_label = "post-peak contested pullback with buy-side absorption present"
    elif score < 0:
        phase_label = "post-peak contested pullback with supply pressure still dominant"
    else:
        phase_label = "post-peak two-sided churn, no clean edge"

    peer_phase_rows = [row for row in phase_rows if row["symbol"] != focus]
    peer_ranked = sorted(peer_phase_rows, key=lambda row: as_float(row.get("post_peak_return_pct")) or 0, reverse=True)
    focus_rank = 1 + sum(
        1 for row in peer_phase_rows
        if (as_float(row.get("post_peak_return_pct")) or 0) > post_peak_ret
    )

    lines = [
        f"# {focus} Trade Plan — {as_of}",
        "",
        "> **Research output. Not financial advice.** This plan is a mechanical read of the",
        "> hydro broker-flow experiment lane (experiment 07). Level thresholds are derived from",
        "> price history by fixed rules, not subjective interpretation.",
        "",
        "## Bias and Confidence",
        "",
        f"- **Bias:** `{bias}`",
        f"- **Confidence:** `{confidence}` (score={score:+d}, {agree_count}/5 signals agree with sign)",
        f"- **Current phase:** `{phase_label}`",
        "",
        "## Price Structure (last 20 sessions)",
        "",
        f"- Current close: `{fmt_price(current_close)}`",
        f"- 20-day support (min low): `{fmt_price(support_price)}`",
        f"- 20-day resistance (max high): `{fmt_price(resistance_price)}`",
        f"- Distance to support: `{fmt_pct_distance(current_close, support_price)}`",
        f"- Distance to resistance: `{fmt_pct_distance(current_close, resistance_price)}`",
        "",
        "## Trade Plan Levels",
        "",
        "| Action | Trigger | Price | Rule |",
        "|---|---|---:|---|",
        f"| **Wait zone** | inside the 20-day range | `{fmt_price(support_price)} - {fmt_price(resistance_price)}` | price is between support and resistance |",
        f"| **Add trigger** | close above recent resistance | `>= {fmt_price(add_trigger)}` | resistance × 1.005 |",
        f"| **Invalidation** | close below support by 3% | `<= {fmt_price(invalidation)}` | support × 0.97 |",
        "",
        "## Signal Breakdown",
        "",
        "| Signal | Direction | Evidence |",
        "|---|:---:|---|",
    ]
    for name, direction, evidence in signals:
        arrow = "+" if direction > 0 else "-" if direction < 0 else "0"
        lines.append(f"| {name} | {arrow} | {evidence} |")

    lines.extend([
        "",
        "## Broker Buyers / Sellers",
        "",
        "**Post-peak pullback — top net buyers:**",
        "",
    ])
    lines.extend(format_broker_list(pullback_buyers))
    lines.extend(["", "**Post-peak pullback — top net sellers:**", ""])
    lines.extend(format_broker_list(pullback_sellers))
    lines.extend(["", "**Last 10 broker days — top net buyers:**", ""])
    lines.extend(format_broker_list(last10_buyers))
    lines.extend(["", "**Last 10 broker days — top net sellers:**", ""])
    lines.extend(format_broker_list(last10_sellers))
    lines.extend(["", "**Last 5 broker days — top net buyers:**", ""])
    lines.extend(format_broker_list(last5_buyers))
    lines.extend(["", "**Last 5 broker days — top net sellers:**", ""])
    lines.extend(format_broker_list(last5_sellers))

    lines.extend([
        "",
        "## Peer Context",
        "",
        f"{focus} ranks **#{focus_rank}** of {len(peer_phase_rows) + 1} hydro peers by `post_peak_return_pct`.",
        "",
        "| Rank | Symbol | Post-peak return | Supply | Absorb | Latest labels |",
        "|---:|---|---:|---:|---:|---|",
    ])
    all_ranked = sorted(phase_rows, key=lambda row: as_float(row.get("post_peak_return_pct")) or 0, reverse=True)
    for rank, row in enumerate(all_ranked, start=1):
        marker = " **(focus)**" if row["symbol"] == focus else ""
        lines.append(
            f"| {rank} | {row['symbol']}{marker} | {row['post_peak_return_pct']}% | "
            f"{row['post_peak_supply_pressure_days']} | {row['post_peak_absorption_days']} | "
            f"{row['latest_labels']} |"
        )

    lines.extend([
        "",
        "## Evidence Trail",
        "",
        f"- Phase row for {focus}: [data/phase_summary.csv](../data/phase_summary.csv) — filter `symbol={focus}`",
        f"- Peer summary row: [data/current_window_peer_summary.csv](../data/current_window_peer_summary.csv) — filter `symbol={focus}`",
        f"- Recent tape (last 15 sessions): [data/{focus.lower()}_recent_days.csv](../data/{focus.lower()}_recent_days.csv)",
        f"- Broker persistence rankings: [data/{focus.lower()}_broker_persistence.csv](../data/{focus.lower()}_broker_persistence.csv)",
        f"- Full daily dataset with pattern flags: [data/hydro_broker_flow_daily.csv](../data/hydro_broker_flow_daily.csv) — filter `symbol={focus}`",
        f"- Raw Merolagani floorsheet captures: `market-gist/broker_flow_ledger/raw_merolagani/{focus}/`",
        "",
        "## Caveats",
        "",
        "- All thresholds here are mechanical rules from fixed formulas. A human reviewer can and should override them when context warrants.",
        "- Confidence score is bounded by the 5 signals in this lab. Missing signals (sector flow, macro flow, insider news, upcoming events) are NOT factored in.",
        "- This plan does NOT look at volume/tape microstructure. Cross-check with experiment 08 when that lane is live.",
        "- Research/experiment lane only. Do not wire directly into live trading prompts or persistence shadow policy.",
    ])
    return "\n".join(lines) + "\n"


def fmt_price(value: Any) -> str:
    number = as_float(value)
    if number is None:
        return "n/a"
    return f"{number:.2f}"


def fmt_pct_distance(current: Any, target: Any) -> str:
    current_num = as_float(current)
    target_num = as_float(target)
    if not current_num or target_num is None:
        return "n/a"
    return f"{(target_num - current_num) / current_num * 100:+.2f}%"


def top_period_rows(rows: list[dict[str, Any]], period: str, side: str, limit: int) -> list[dict[str, Any]]:
    selected = [row for row in rows if row["period"] == period and row["side"] == side]
    return sorted(selected, key=lambda row: int(row["rank"]))[:limit]


def format_broker_list(rows: list[dict[str, Any]]) -> list[str]:
    if not rows:
        return ["- none"]
    return [
        f"- Broker `{row['broker']}`: net `{row['net_qty']}`, buy `{row['buy_qty']}`, sell `{row['sell_qty']}`, net/gross `{row['net_to_gross_pct']}`%"
        for row in rows
    ]


def labels_for(row: dict[str, Any]) -> str:
    labels = [key for key in PATTERN_COLUMNS if row.get(key) in {"1", 1}]
    return ", ".join(labels) if labels else "none"


def count_flag(rows: list[dict[str, Any]], flag: str) -> int:
    return sum(1 for row in rows if row.get(flag) == "1")


def count_condition(rows: list[dict[str, Any]], predicate: Any) -> int:
    return sum(1 for row in rows if predicate(row))


def pct_change(start_value: Any, end_value: Any) -> Any:
    start = as_float(start_value)
    end = as_float(end_value)
    if not start or end is None:
        return ""
    return round_float(((end - start) / start) * 100)


def avg(values: Any) -> Any:
    numbers = [as_float(value) for value in values]
    numbers = [number for number in numbers if number is not None]
    return round_float(mean(numbers)) if numbers else ""


def parse_int(value: Any) -> int:
    number = as_float(str(value).replace(",", "") if value is not None else "")
    return int(number) if number is not None else 0


def as_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def round_float(value: Any, digits: int = 4) -> Any:
    if value is None or value == "":
        return ""
    return round(float(value), digits)


if __name__ == "__main__":
    raise SystemExit(main())
