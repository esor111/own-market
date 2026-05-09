from __future__ import annotations

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


def main() -> int:
    config = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
    symbols = [symbol.upper() for symbol in config["symbols"]]
    rows = read_csv(DAILY_CSV)
    rows_by_symbol = {symbol: sorted([row for row in rows if row["symbol"] == symbol], key=lambda row: row["date"]) for symbol in symbols}
    common_dates = current_common_dates(rows_by_symbol, symbols)
    if not common_dates:
        raise SystemExit("No common broker-flow dates found.")

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)

    phase_rows = build_phase_summary(rows_by_symbol, symbols, common_dates)
    upper_recent_rows = build_upper_recent_rows(rows_by_symbol["UPPER"], common_dates)
    broker_rows = build_broker_persistence("UPPER", rows_by_symbol["UPPER"], common_dates)
    markdown = build_markdown(phase_rows, upper_recent_rows, broker_rows, common_dates)

    write_csv(DATA_DIR / "phase_summary.csv", phase_rows)
    write_csv(DATA_DIR / "upper_recent_days.csv", upper_recent_rows)
    write_csv(DATA_DIR / "broker_persistence.csv", broker_rows)
    (RESULTS_DIR / "deep_iteration.md").write_text(markdown, encoding="utf-8")

    print(f"Wrote {DATA_DIR / 'phase_summary.csv'} ({len(phase_rows)} rows)")
    print(f"Wrote {DATA_DIR / 'upper_recent_days.csv'} ({len(upper_recent_rows)} rows)")
    print(f"Wrote {DATA_DIR / 'broker_persistence.csv'} ({len(broker_rows)} rows)")
    print(f"Wrote {RESULTS_DIR / 'deep_iteration.md'}")
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


def build_upper_recent_rows(rows: list[dict[str, Any]], common_dates: list[str]) -> list[dict[str, Any]]:
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
    phase_rows: list[dict[str, Any]],
    upper_recent_rows: list[dict[str, Any]],
    broker_rows: list[dict[str, Any]],
    common_dates: list[str],
) -> str:
    upper = next(row for row in phase_rows if row["symbol"] == "UPPER")
    pullback_buyers = top_period_rows(broker_rows, "pullback_after_peak", "net_buy", 5)
    pullback_sellers = top_period_rows(broker_rows, "pullback_after_peak", "net_sell", 5)
    last5_buyers = top_period_rows(broker_rows, "last_5_broker_days", "net_buy", 5)
    last5_sellers = top_period_rows(broker_rows, "last_5_broker_days", "net_sell", 5)

    lines = [
        "# Hydro Broker-Flow Deep Iteration",
        "",
        f"Generated: `{datetime.now().isoformat(timespec='seconds')}`",
        "",
        f"Common peer window with real broker rows: `{common_dates[0]}` to `{common_dates[-1]}` ({len(common_dates)} dates).",
        "",
        "## UPPER Phase Read",
        "",
        f"- Window return: `{upper['window_return_pct']}`% from `{upper['start_close']}` to `{upper['latest_close']}`.",
        f"- Peak: `{upper['peak_close']}` on `{upper['peak_date']}`.",
        f"- Post-peak move: `{upper['post_peak_return_pct']}`% over `{upper['post_peak_days']}` broker-backed dates.",
        f"- Post-peak pressure mix: `{upper['post_peak_supply_pressure_days']}` supply-pressure days, `{upper['post_peak_absorption_days']}` absorption days, `{upper['post_peak_distribution_days']}` distribution-like days, `{upper['post_peak_accumulation_days']}` accumulation-like days.",
        f"- Latest labels: `{upper['latest_labels']}`.",
        "",
        "Interpretation: UPPER is still positive across the aligned window, but the psychology after the peak is not clean accumulation. It looks like a rally that got marked up hard, then entered a contested pullback where buyers are still present but sellers keep meeting them.",
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
        "## UPPER Pullback Broker Net",
        "",
        "Top net buyers after the peak:",
        "",
    ])
    lines.extend(format_broker_list(pullback_buyers))
    lines.extend(["", "Top net sellers after the peak:", ""])
    lines.extend(format_broker_list(pullback_sellers))
    lines.extend(["", "## UPPER Last 5 Broker Days", "", "Top recent net buyers:", ""])
    lines.extend(format_broker_list(last5_buyers))
    lines.extend(["", "Top recent net sellers:", ""])
    lines.extend(format_broker_list(last5_sellers))

    lines.extend([
        "",
        "## Recent UPPER Tape",
        "",
        "| Date | Close | Return | Vol ratio | Rows | B3/S3 | Labels |",
        "|---|---:|---:|---:|---:|---:|---|",
    ])
    for row in upper_recent_rows:
        lines.append(
            f"| {row['date']} | {row['close']} | {row['return_pct']}% | {row['volume_ratio_20d']} | "
            f"{row['raw_rows']} | {row['top3_buyer_pct']}/{row['top3_seller_pct']} | {row['labels']} |"
        )

    lines.extend([
        "",
        "## Working Verdict",
        "",
        "- Clean accumulation would usually show repeated absorption days, improving closes, and less urgent seller concentration. That is not the dominant recent pattern.",
        "- Clean distribution would usually show persistent high-volume sell pressure and no meaningful bid. That is also too simple, because buyers remain active and the whole aligned window is still positive.",
        "- Best current label: `contested post-rally absorption with supply pressure`. It is a watch setup, not a confirmed long setup by this lab.",
    ])
    return "\n".join(lines) + "\n"


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
