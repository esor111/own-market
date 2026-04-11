"""
Score saved persistence shadow reports against forward price returns.

This is a forward evaluation helper for the frozen shadow policy. It does not
change any live logic; it only grades saved report rows that already exist on
disk.

Primary use:
    python score_persistence_shadow_reports.py
"""
from __future__ import annotations

import csv
import json
from datetime import date, datetime
from pathlib import Path
from typing import Iterable

import pandas as pd


BASE = Path(__file__).resolve().parent
ROOT = BASE.parent
SHADOW_REPORTS_DIR = ROOT / "data" / "validation" / "persistence_shadow_reports"
OUTPUT_DIR = ROOT / "data" / "validation" / "persistence_shadow_reviews"
SHARESANSAR_DATA_DIR = ROOT.parent / "sharesansar_datascrape" / "data"

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def main() -> None:
    detail_rows = build_scored_rows()
    if not detail_rows:
        raise RuntimeError("No shadow report rows found to score.")

    detail_frame = pd.DataFrame(detail_rows)
    summary_frame = build_summary(detail_frame)
    pending_frame = detail_frame[detail_frame["outcome_status"] != "resolved"].copy()

    timestamp_prefix = datetime.now().strftime("%Y-%m-%d")
    detail_path = OUTPUT_DIR / f"{timestamp_prefix}__shadow_batch_cases_v1.csv"
    latest_detail_path = OUTPUT_DIR / "latest__shadow_batch_cases_v1.csv"
    summary_path = OUTPUT_DIR / f"{timestamp_prefix}__shadow_batch_scorecard_v1.json"
    latest_summary_path = OUTPUT_DIR / "latest__shadow_batch_scorecard_v1.json"
    markdown_path = OUTPUT_DIR / f"{timestamp_prefix}__shadow_batch_scorecard_v1.md"
    latest_markdown_path = OUTPUT_DIR / "latest__shadow_batch_scorecard_v1.md"

    detail_frame.to_csv(detail_path, index=False)
    detail_frame.to_csv(latest_detail_path, index=False)

    payload = {
        "schema_version": "1.0",
        "built_at": datetime.now().isoformat(),
        "price_data_last_date": (
            detail_frame["price_data_last_date"].dropna().max()
            if not detail_frame["price_data_last_date"].dropna().empty
            else None
        ),
        "report_files": sorted(detail_frame["report_file"].dropna().unique().tolist()),
        "totals": {
            "rows": int(len(detail_frame)),
            "resolved_rows": int((detail_frame["outcome_status"] == "resolved").sum()),
            "pending_rows": int((detail_frame["outcome_status"] != "resolved").sum()),
        },
        "groups": summary_frame.to_dict("records"),
        "pending_examples": pending_frame[
            ["report_date", "symbol", "group_key", "pending_reason"]
        ].head(20).to_dict("records"),
    }

    summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    latest_summary_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    markdown = build_markdown(detail_frame, summary_frame)
    markdown_path.write_text(markdown, encoding="utf-8")
    latest_markdown_path.write_text(markdown, encoding="utf-8")

    print(f"Wrote detail rows to {detail_path}")
    print(f"Wrote scorecard JSON to {summary_path}")
    print(f"Wrote scorecard Markdown to {markdown_path}")


def build_scored_rows() -> list[dict]:
    rows: list[dict] = []
    price_cache: dict[str, pd.DataFrame] = {}

    for report_path in sorted(SHADOW_REPORTS_DIR.glob("*__persistence_shadow_v1.json")):
        payload = json.loads(report_path.read_text(encoding="utf-8"))
        report_date = payload.get("report_date")
        policy_version = payload.get("policy_version")

        for result in payload.get("results", []):
            symbol = str(result.get("symbol") or "").upper().strip()
            if not symbol:
                continue

            prices = price_cache.get(symbol)
            if prices is None:
                prices = load_symbol_prices(symbol)
                price_cache[symbol] = prices

            base_row = {
                "report_file": report_path.name,
                "report_date": report_date,
                "symbol": symbol,
                "policy_version": policy_version,
                "verdict": result.get("verdict"),
                "caution_flag_count": len(result.get("caution_flags") or []),
                "supportive_flag_count": len(result.get("supportive_flags") or []),
                "event_annotation_count": len(result.get("event_annotations") or []),
                "has_dividend_annotation": any(
                    annotation.get("annotation_type") == "dividend_family_caution"
                    for annotation in (result.get("event_annotations") or [])
                ),
                "price_data_last_date": (
                    prices.iloc[-1]["date"].date().isoformat() if not prices.empty else None
                ),
            }
            base_row["group_key"] = classify_group(base_row)

            scored = attach_forward_outcome(base_row, prices)
            rows.append(scored)

    return rows


def classify_group(row: dict) -> str:
    verdict = row.get("verdict")
    has_dividend = bool(row.get("has_dividend_annotation"))
    if verdict == "CAUTION" and has_dividend:
        return "persistence_caution_plus_dividend_annotation"
    if verdict == "CAUTION":
        return "persistence_caution_only"
    if verdict == "SUPPORTIVE":
        return "supportive_only"
    if has_dividend:
        return "dividend_annotation_only"
    return "no_signal"


def attach_forward_outcome(row: dict, prices: pd.DataFrame) -> dict:
    result = dict(row)
    if prices.empty:
        result.update(
            {
                "outcome_status": "pending",
                "pending_reason": "no_price_history",
                "anchor_date": None,
                "return_5d_pct": None,
                "return_10d_pct": None,
                "negative_5d": None,
                "negative_10d": None,
                "success_10d": None,
            }
        )
        return result

    report_day = parse_iso_date(result["report_date"])
    if report_day is None:
        result.update(
            {
                "outcome_status": "pending",
                "pending_reason": "invalid_report_date",
                "anchor_date": None,
                "return_5d_pct": None,
                "return_10d_pct": None,
                "negative_5d": None,
                "negative_10d": None,
                "success_10d": None,
            }
        )
        return result

    trading_dates = list(prices["date"])
    anchor_idx = resolve_anchor_index(trading_dates, pd.Timestamp(report_day), max_forward_gap_days=10)
    if anchor_idx is None:
        result.update(
            {
                "outcome_status": "pending",
                "pending_reason": "no_trading_anchor_within_10d",
                "anchor_date": None,
                "return_5d_pct": None,
                "return_10d_pct": None,
                "negative_5d": None,
                "negative_10d": None,
                "success_10d": None,
            }
        )
        return result

    anchor_date = trading_dates[anchor_idx].date().isoformat()
    result["anchor_date"] = anchor_date

    horizon_5 = compute_forward_return(prices, anchor_idx, 5)
    horizon_10 = compute_forward_return(prices, anchor_idx, 10)

    result["return_5d_pct"] = horizon_5
    result["return_10d_pct"] = horizon_10
    result["negative_5d"] = None if horizon_5 is None else horizon_5 < 0
    result["negative_10d"] = None if horizon_10 is None else horizon_10 < 0

    if horizon_10 is None:
        result["outcome_status"] = "pending"
        result["pending_reason"] = "insufficient_forward_bars_for_10d"
        result["success_10d"] = None
    else:
        result["outcome_status"] = "resolved"
        result["pending_reason"] = None
        if result["group_key"] in {
            "persistence_caution_only",
            "persistence_caution_plus_dividend_annotation",
            "dividend_annotation_only",
        }:
            result["success_10d"] = horizon_10 < 0
        elif result["group_key"] == "supportive_only":
            result["success_10d"] = horizon_10 > 0
        else:
            result["success_10d"] = None

    return result


def build_summary(detail_frame: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict] = []

    for group_key, group in detail_frame.groupby("group_key", dropna=False):
        resolved = group[group["outcome_status"] == "resolved"].copy()
        row = {
            "group_key": group_key,
            "total_rows": int(len(group)),
            "resolved_rows": int(len(resolved)),
            "pending_rows": int(len(group) - len(resolved)),
            "mean_return_5d_pct": None,
            "mean_return_10d_pct": None,
            "negative_hit_rate_5d": None,
            "negative_hit_rate_10d": None,
            "success_rate_10d": None,
        }
        if not resolved.empty:
            row["mean_return_5d_pct"] = safe_mean(resolved["return_5d_pct"])
            row["mean_return_10d_pct"] = safe_mean(resolved["return_10d_pct"])
            row["negative_hit_rate_5d"] = safe_rate(resolved["negative_5d"])
            row["negative_hit_rate_10d"] = safe_rate(resolved["negative_10d"])
            row["success_rate_10d"] = safe_rate(resolved["success_10d"])
        rows.append(row)

    return pd.DataFrame(rows).sort_values("group_key").reset_index(drop=True)


def build_markdown(detail_frame: pd.DataFrame, summary_frame: pd.DataFrame) -> str:
    resolved = detail_frame[detail_frame["outcome_status"] == "resolved"].copy()
    pending = detail_frame[detail_frame["outcome_status"] != "resolved"].copy()

    lines = [
        "# Shadow Batch Scorecard",
        "",
        f"- Built: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
        f"- Total rows: {len(detail_frame)}",
        f"- Resolved rows: {len(resolved)}",
        f"- Pending rows: {len(pending)}",
        "",
        "## Group Summary",
        "",
        "| Group | Total | Resolved | Pending | Mean 5D | Mean 10D | Neg 5D | Neg 10D | Success 10D |",
        "|---|---:|---:|---:|---:|---:|---:|---:|---:|",
    ]

    for row in summary_frame.to_dict("records"):
        lines.append(
            "| {group_key} | {total_rows} | {resolved_rows} | {pending_rows} | {mean5} | {mean10} | {neg5} | {neg10} | {succ10} |".format(
                group_key=row["group_key"],
                total_rows=row["total_rows"],
                resolved_rows=row["resolved_rows"],
                pending_rows=row["pending_rows"],
                mean5=format_pct(row["mean_return_5d_pct"]),
                mean10=format_pct(row["mean_return_10d_pct"]),
                neg5=format_rate(row["negative_hit_rate_5d"]),
                neg10=format_rate(row["negative_hit_rate_10d"]),
                succ10=format_rate(row["success_rate_10d"]),
            )
        )

    lines.extend(
        [
            "",
            "## Pending Examples",
            "",
        ]
    )

    if pending.empty:
        lines.append("No pending rows.")
    else:
        lines.append("| Date | Symbol | Group | Reason |")
        lines.append("|---|---|---|---|")
        for row in pending[["report_date", "symbol", "group_key", "pending_reason"]].head(20).to_dict("records"):
            lines.append(
                f"| {row['report_date']} | {row['symbol']} | {row['group_key']} | {row['pending_reason']} |"
            )

    return "\n".join(lines) + "\n"


def load_symbol_prices(symbol: str) -> pd.DataFrame:
    target = str(symbol).upper().strip()
    rows: list[dict] = []
    for business_date in list_available_dates():
        csv_path = SHARESANSAR_DATA_DIR / f"{business_date.strftime('%m_%d_%Y')}.csv"
        if not csv_path.exists():
            continue
        match = load_row_for_symbol(csv_path, target)
        if match:
            rows.append(match)

    frame = pd.DataFrame(rows)
    if frame.empty:
        return pd.DataFrame(
            columns=[
                "date",
                "symbol",
                "open",
                "high",
                "low",
                "close",
                "ltp",
                "vwap",
                "volume",
                "previous_close",
                "turnover",
                "trades",
                "diff",
                "diff_pct",
                "range",
                "range_pct",
                "vwap_pct",
            ]
        )

    frame["date"] = pd.to_datetime(frame["date"], errors="coerce")
    frame = frame.dropna(subset=["date", "close"]).sort_values("date").reset_index(drop=True)
    return collapse_duplicate_sessions(frame)


def list_available_dates() -> list[date]:
    dates: list[date] = []
    for csv_path in SHARESANSAR_DATA_DIR.glob("*.csv"):
        try:
            current_date = datetime.strptime(csv_path.stem, "%m_%d_%Y").date()
        except ValueError:
            continue
        dates.append(current_date)
    return sorted(dates)


def load_row_for_symbol(csv_path: Path, symbol: str) -> dict | None:
    with csv_path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        for raw in reader:
            current_symbol = str(raw.get("Symbol") or "").strip().upper()
            if current_symbol != symbol:
                continue
            return {
                "date": datetime.strptime(csv_path.stem, "%m_%d_%Y").date().isoformat(),
                "symbol": current_symbol,
                "open": parse_number(raw.get("Open")),
                "high": parse_number(raw.get("High")),
                "low": parse_number(raw.get("Low")),
                "close": parse_number(raw.get("Close")),
                "ltp": parse_number(raw.get("LTP")),
                "vwap": parse_number(raw.get("VWAP")),
                "volume": parse_number(raw.get("Vol")),
                "previous_close": parse_number(raw.get("Prev. Close")),
                "turnover": parse_number(raw.get("Turnover")),
                "trades": parse_number(raw.get("Trans.")),
                "diff": parse_number(raw.get("Diff")),
                "diff_pct": parse_number(raw.get("Diff %")),
                "range": parse_number(raw.get("Range")),
                "range_pct": parse_number(raw.get("Range %")),
                "vwap_pct": parse_number(raw.get("VWAP %")),
            }
    return None


def collapse_duplicate_sessions(frame: pd.DataFrame) -> pd.DataFrame:
    comparison_cols = [
        "open",
        "high",
        "low",
        "close",
        "ltp",
        "vwap",
        "volume",
        "previous_close",
        "turnover",
        "trades",
        "diff",
        "diff_pct",
        "range",
        "range_pct",
        "vwap_pct",
    ]
    current = frame[comparison_cols].copy()
    previous = current.shift(1)
    duplicate_mask = current.fillna("__MISSING__").eq(previous.fillna("__MISSING__")).all(axis=1)
    return frame.loc[~duplicate_mask].reset_index(drop=True)


def resolve_anchor_index(
    trading_dates: Iterable[pd.Timestamp],
    event_date: pd.Timestamp,
    max_forward_gap_days: int = 10,
) -> int | None:
    target = pd.Timestamp(event_date).normalize()
    date_list = list(trading_dates)
    for idx, trading_date in enumerate(date_list):
        if trading_date.normalize() >= target:
            if (trading_date.normalize() - target).days > max_forward_gap_days:
                return None
            return idx
    return None


def compute_forward_return(prices: pd.DataFrame, anchor_idx: int, offset: int) -> float | None:
    end_idx = anchor_idx + offset
    if anchor_idx < 0 or end_idx >= len(prices):
        return None
    start_price = prices.iloc[anchor_idx]["close"]
    end_price = prices.iloc[end_idx]["close"]
    if start_price in (None, 0) or pd.isna(start_price) or pd.isna(end_price):
        return None
    return ((float(end_price) / float(start_price)) - 1.0) * 100.0


def parse_number(value: object) -> float | None:
    if value is None:
        return None
    text = str(value).strip().replace(",", "")
    if not text or text == "-":
        return None
    try:
        return float(text)
    except ValueError:
        return None


def parse_iso_date(value: object) -> date | None:
    if value is None:
        return None
    try:
        return datetime.strptime(str(value), "%Y-%m-%d").date()
    except ValueError:
        return None


def safe_mean(values: pd.Series) -> float | None:
    clean = pd.to_numeric(values, errors="coerce").dropna()
    if clean.empty:
        return None
    return float(clean.mean())


def safe_rate(values: pd.Series) -> float | None:
    clean = values.dropna()
    if clean.empty:
        return None
    numeric = clean.astype(bool).astype(int)
    return float(numeric.mean())


def format_pct(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.2f}%"


def format_rate(value: float | None) -> str:
    if value is None or pd.isna(value):
        return "-"
    return f"{value:.1%}"


if __name__ == "__main__":
    main()
