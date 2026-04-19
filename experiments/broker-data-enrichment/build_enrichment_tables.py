"""
Build broker-flow enrichment tables.

Layer 3 research infrastructure only. This script reads existing broker-flow and
corporate-action tables, then writes enriched copies inside this sandbox folder.
It does not touch production scoring or persistence shadow outputs.
"""
from __future__ import annotations

import argparse
import json
import re
from datetime import datetime, timezone
from io import StringIO
from pathlib import Path
from typing import Iterable
from urllib.request import Request, urlopen

import pandas as pd


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]

FACT_TABLE = REPO_ROOT / "market-gist" / "data" / "validation" / "broker_flow_fact_table" / "broker_flow_fact_table.csv"
EVENTS_CSV = REPO_ROOT / "experiments" / "01-corporate-action" / "data" / "events.csv"
OUTPUT_DIR = SCRIPT_DIR / "data"
RAW_SOURCE_DIR = OUTPUT_DIR / "raw_sources"

NEPSE_BAJAR_BROKER_CONTACT = "https://www.nepsebajar.com/broker-contact"

DATE_ROLE_COLUMNS = [
    "announcement_date",
    "approval_date",
    "book_close_date",
    "ex_date",
    "listing_date",
    "distribution_date",
    "meeting_date",
    "right_open_date",
    "right_close_date",
    "right_final_date",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--fact-table", default=str(FACT_TABLE))
    parser.add_argument("--events-csv", default=str(EVENTS_CSV))
    parser.add_argument("--output-dir", default=str(OUTPUT_DIR))
    parser.add_argument("--event-window-days", type=int, default=10)
    parser.add_argument("--skip-broker-web", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "raw_sources").mkdir(parents=True, exist_ok=True)

    fact = pd.read_csv(args.fact_table, dtype={"broker_id": "string", "symbol": "string", "date": "string"})
    fact["broker_id"] = fact["broker_id"].astype(str).str.strip()
    fact["symbol"] = fact["symbol"].astype(str).str.upper().str.strip()
    fact["date"] = fact["date"].astype(str).str.slice(0, 10)

    events = pd.read_csv(args.events_csv, dtype="string").fillna("")
    event_calendar = build_event_calendar(events)
    symbol_day_context = build_symbol_day_context(fact, event_calendar, args.event_window_days)
    broker_master, broker_source_note = build_broker_master(fact, skip_web=args.skip_broker_web, output_dir=output_dir)

    enriched = fact.merge(broker_master, on="broker_id", how="left")
    enriched = enriched.merge(symbol_day_context, on=["date", "symbol"], how="left")
    enriched = fill_context_defaults(enriched)

    broker_master_path = output_dir / "broker_master.csv"
    event_calendar_path = output_dir / "event_calendar.csv"
    symbol_day_context_path = output_dir / "symbol_day_event_context.csv"
    enriched_path = output_dir / "broker_flow_fact_table_enriched.csv"
    summary_json_path = output_dir / "enrichment_summary.json"
    summary_md_path = output_dir / "enrichment_summary.md"

    broker_master.to_csv(broker_master_path, index=False)
    event_calendar.to_csv(event_calendar_path, index=False)
    symbol_day_context.to_csv(symbol_day_context_path, index=False)
    enriched.to_csv(enriched_path, index=False)

    summary = build_summary(
        fact=fact,
        enriched=enriched,
        broker_master=broker_master,
        event_calendar=event_calendar,
        symbol_day_context=symbol_day_context,
        broker_source_note=broker_source_note,
        event_window_days=args.event_window_days,
        paths={
            "broker_master": broker_master_path,
            "event_calendar": event_calendar_path,
            "symbol_day_event_context": symbol_day_context_path,
            "broker_flow_fact_table_enriched": enriched_path,
        },
    )
    summary_json_path.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    summary_md_path.write_text(render_summary_markdown(summary), encoding="utf-8")

    print(f"Wrote broker master: {broker_master_path}")
    print(f"Wrote event calendar: {event_calendar_path}")
    print(f"Wrote symbol-day context: {symbol_day_context_path}")
    print(f"Wrote enriched broker-flow table: {enriched_path}")
    print(f"Wrote summary: {summary_md_path}")


def build_broker_master(fact: pd.DataFrame, skip_web: bool, output_dir: Path) -> tuple[pd.DataFrame, str]:
    observed = pd.DataFrame({"broker_id": sorted(fact["broker_id"].dropna().astype(str).unique(), key=broker_sort_key)})
    observed["broker_name"] = ""
    observed["broker_phone"] = ""
    observed["broker_address"] = ""
    observed["broker_source_url"] = ""
    observed["broker_source_quality"] = "observed_id_unmapped"
    observed["tms_url_guess"] = observed["broker_id"].map(make_tms_url_guess)

    if skip_web:
        return observed, "Broker web fetch skipped; broker_master contains observed IDs only."

    try:
        source = fetch_text(NEPSE_BAJAR_BROKER_CONTACT)
        raw_path = output_dir / "raw_sources" / "nepsebajar_broker_contact.html"
        raw_path.write_text(source, encoding="utf-8")
        tables = pd.read_html(StringIO(source))
    except Exception as exc:  # noqa: BLE001 - source failure should not kill enrichment.
        return observed, f"Broker web fetch failed ({type(exc).__name__}: {exc}); observed IDs retained unmapped."

    broker_tables = [table for table in tables if {"BROKER CODE", "BROKER NAME"}.issubset(set(map(str, table.columns)))]
    if not broker_tables:
        return observed, "Broker contact page fetched, but no broker table was detected; observed IDs retained unmapped."

    source_table = broker_tables[0].copy()
    source_table.to_csv(output_dir / "raw_sources" / "nepsebajar_broker_contact.csv", index=False)
    source_table["broker_id"] = source_table["BROKER CODE"].map(normalize_numeric_broker_code)
    source_table = source_table.dropna(subset=["broker_id"])
    source_table["broker_id"] = source_table["broker_id"].astype(str)
    source_table = source_table.drop_duplicates(subset=["broker_id"], keep="first")
    source_table = source_table.rename(
        columns={
            "BROKER NAME": "broker_name",
            "LANDLINE": "broker_phone",
            "ADDRESS": "broker_address",
        }
    )[["broker_id", "broker_name", "broker_phone", "broker_address"]]
    source_table["broker_source_url"] = NEPSE_BAJAR_BROKER_CONTACT
    source_table["broker_source_quality"] = "third_party_contact_page"
    source_table["tms_url_guess"] = source_table["broker_id"].map(make_tms_url_guess)

    mapped = observed.drop(columns=["broker_name", "broker_phone", "broker_address", "broker_source_url", "broker_source_quality", "tms_url_guess"])
    mapped = mapped.merge(source_table, on="broker_id", how="left")
    mapped["broker_name"] = mapped["broker_name"].fillna("")
    mapped["broker_phone"] = mapped["broker_phone"].fillna("")
    mapped["broker_address"] = mapped["broker_address"].fillna("")
    mapped["broker_source_url"] = mapped["broker_source_url"].fillna("")
    mapped["broker_source_quality"] = mapped["broker_source_quality"].fillna("observed_id_unmapped")
    mapped["tms_url_guess"] = mapped["broker_id"].map(make_tms_url_guess)
    return mapped, "Broker names sourced from Nepse Bajar where available; unmapped observed IDs retained."


def build_event_calendar(events: pd.DataFrame) -> pd.DataFrame:
    rows: list[dict[str, object]] = []
    for _, row in events.iterrows():
        base = {
            "symbol": str(row.get("symbol", "")).upper().strip(),
            "sector": row.get("sector", ""),
            "company_name": row.get("company_name", ""),
            "event_type": row.get("event_type", ""),
            "event_family": classify_event_family(str(row.get("event_type", ""))),
            "source_table": row.get("source_table", ""),
            "event_label": row.get("event_label", ""),
            "source_url": row.get("source_url", ""),
            "bonus_share_pct": row.get("bonus_share_pct", ""),
            "cash_dividend_pct": row.get("cash_dividend_pct", ""),
            "total_dividend_pct": row.get("total_dividend_pct", ""),
            "right_share_ratio": row.get("right_share_ratio", ""),
            "right_share_units": row.get("right_share_units", ""),
        }
        if not base["symbol"]:
            continue
        for role in DATE_ROLE_COLUMNS:
            date_text = clean_date(row.get(role, ""))
            if not date_text:
                continue
            rows.append(
                {
                    **base,
                    "event_date": date_text,
                    "event_date_role": role,
                    "event_importance": classify_event_importance(str(base["event_type"]), role),
                }
            )

    if not rows:
        return pd.DataFrame(
            columns=[
                "symbol",
                "event_date",
                "event_date_role",
                "event_type",
                "event_family",
                "event_importance",
                "source_table",
                "event_label",
                "source_url",
            ]
        )

    calendar = pd.DataFrame(rows)
    calendar = calendar.drop_duplicates(
        subset=["symbol", "event_date", "event_date_role", "event_type", "event_label", "source_url"]
    ).sort_values(["symbol", "event_date", "event_date_role", "event_type"])
    return calendar


def build_symbol_day_context(fact: pd.DataFrame, event_calendar: pd.DataFrame, event_window_days: int) -> pd.DataFrame:
    symbol_days = fact[["date", "symbol"]].drop_duplicates().copy()
    symbol_days["date_dt"] = pd.to_datetime(symbol_days["date"], errors="coerce")

    calendar = event_calendar.copy()
    if calendar.empty:
        return empty_symbol_day_context(symbol_days)

    calendar["event_date_dt"] = pd.to_datetime(calendar["event_date"], errors="coerce")
    calendar = calendar.dropna(subset=["event_date_dt"])
    event_by_symbol = {symbol: group.copy() for symbol, group in calendar.groupby("symbol")}

    rows: list[dict[str, object]] = []
    for _, day in symbol_days.iterrows():
        symbol = day["symbol"]
        date_text = day["date"]
        date_dt = day["date_dt"]
        events = event_by_symbol.get(symbol)
        if events is None or pd.isna(date_dt):
            rows.append(default_context_row(date_text, symbol, "no_l001_symbol_events"))
            continue

        days_from_event = (date_dt - events["event_date_dt"]).dt.days
        working = events.assign(days_from_event_to_trade=days_from_event)
        nearby = working[working["days_from_event_to_trade"].abs() <= event_window_days]
        recent = working[(working["days_from_event_to_trade"] >= 0) & (working["days_from_event_to_trade"] <= 30)]
        upcoming = working[(working["days_from_event_to_trade"] < 0) & (working["days_from_event_to_trade"] >= -event_window_days)]
        same_day = working[working["days_from_event_to_trade"] == 0]

        if nearby.empty:
            rows.append(
                {
                    **default_context_row(date_text, symbol, "l001_symbol_no_nearby_event"),
                    "event_recent_30d_count": int(len(recent)),
                }
            )
            continue

        closest = nearby.assign(abs_days=nearby["days_from_event_to_trade"].abs()).sort_values(
            ["abs_days", "event_importance", "event_date"]
        ).iloc[0]
        rows.append(
            {
                "date": date_text,
                "symbol": symbol,
                "event_context_quality": "l001_symbol_nearby_event",
                "event_contamination_flag": True,
                "event_nearby_10d_count": int(len(nearby)),
                "event_recent_30d_count": int(len(recent)),
                "event_upcoming_10d_count": int(len(upcoming)),
                "event_same_day_count": int(len(same_day)),
                "closest_event_date": closest["event_date"],
                "closest_event_days": int(closest["days_from_event_to_trade"]),
                "closest_event_type": closest["event_type"],
                "closest_event_family": closest["event_family"],
                "closest_event_role": closest["event_date_role"],
                "nearby_event_types_10d": join_unique(nearby["event_type"]),
                "nearby_event_families_10d": join_unique(nearby["event_family"]),
                "has_dividend_bonus_10d": has_family(nearby, "dividend_bonus"),
                "has_rights_10d": has_family(nearby, "rights"),
                "has_agm_10d": has_family(nearby, "agm"),
                "has_listing_10d": has_family(nearby, "listing"),
            }
        )

    return pd.DataFrame(rows).sort_values(["symbol", "date"])


def fill_context_defaults(enriched: pd.DataFrame) -> pd.DataFrame:
    int_cols = [
        "event_nearby_10d_count",
        "event_recent_30d_count",
        "event_upcoming_10d_count",
        "event_same_day_count",
    ]
    bool_cols = [
        "event_contamination_flag",
        "has_dividend_bonus_10d",
        "has_rights_10d",
        "has_agm_10d",
        "has_listing_10d",
    ]
    text_cols = [
        "event_context_quality",
        "closest_event_date",
        "closest_event_type",
        "closest_event_family",
        "closest_event_role",
        "nearby_event_types_10d",
        "nearby_event_families_10d",
        "broker_name",
        "broker_phone",
        "broker_address",
        "broker_source_url",
        "broker_source_quality",
        "tms_url_guess",
    ]
    for col in int_cols:
        if col in enriched.columns:
            enriched[col] = enriched[col].fillna(0).astype(int)
    if "closest_event_days" in enriched.columns:
        enriched["closest_event_days"] = enriched["closest_event_days"].fillna("").astype(str).str.replace(r"\.0$", "", regex=True)
    for col in bool_cols:
        if col in enriched.columns:
            enriched[col] = enriched[col].fillna(False).astype(bool)
    for col in text_cols:
        if col in enriched.columns:
            enriched[col] = enriched[col].fillna("")
    return enriched


def build_summary(
    fact: pd.DataFrame,
    enriched: pd.DataFrame,
    broker_master: pd.DataFrame,
    event_calendar: pd.DataFrame,
    symbol_day_context: pd.DataFrame,
    broker_source_note: str,
    event_window_days: int,
    paths: dict[str, Path],
) -> dict:
    mapped = broker_master[broker_master["broker_source_quality"] != "observed_id_unmapped"]
    contaminated = enriched[enriched["event_contamination_flag"] == True]  # noqa: E712 - pandas identity comparison.
    by_symbol = []
    for symbol, group in enriched.groupby("symbol"):
        contaminated_count = int(group["event_contamination_flag"].sum())
        by_symbol.append(
            {
                "symbol": symbol,
                "rows": int(len(group)),
                "event_contaminated_rows": contaminated_count,
                "event_contaminated_pct": round((contaminated_count / len(group)) * 100, 2) if len(group) else 0.0,
            }
        )
    by_symbol.sort(key=lambda item: (-item["event_contaminated_pct"], item["symbol"]))

    unmapped = broker_master[broker_master["broker_source_quality"] == "observed_id_unmapped"]["broker_id"].tolist()
    event_symbols = sorted(event_calendar["symbol"].dropna().astype(str).unique().tolist()) if not event_calendar.empty else []
    fact_symbols = sorted(fact["symbol"].dropna().astype(str).unique().tolist())
    fact_symbols_with_event_coverage = sorted(set(fact_symbols).intersection(event_symbols))
    fact_symbols_without_event_coverage = sorted(set(fact_symbols).difference(event_symbols))
    context_quality_counts = (
        symbol_day_context["event_context_quality"].value_counts().to_dict()
        if "event_context_quality" in symbol_day_context.columns
        else {}
    )
    return {
        "generated_at": datetime.now(timezone.utc).replace(microsecond=0).isoformat(),
        "layer": "3 research infrastructure",
        "event_window_days": event_window_days,
        "broker_source_note": broker_source_note,
        "fact_rows": int(len(fact)),
        "enriched_rows": int(len(enriched)),
        "symbols": int(fact["symbol"].nunique()),
        "observed_broker_ids": int(fact["broker_id"].nunique()),
        "mapped_broker_ids": int(mapped["broker_id"].nunique()),
        "unmapped_broker_ids": int(len(unmapped)),
        "unmapped_broker_id_list": unmapped,
        "source_event_rows": int(event_calendar[["symbol", "event_type", "event_label", "source_url"]].drop_duplicates().shape[0])
        if not event_calendar.empty
        else 0,
        "event_calendar_rows": int(len(event_calendar)),
        "event_symbols": event_symbols,
        "fact_symbols_with_event_coverage": fact_symbols_with_event_coverage,
        "fact_symbols_without_event_coverage": fact_symbols_without_event_coverage,
        "event_context_quality_counts": {str(key): int(value) for key, value in context_quality_counts.items()},
        "symbol_day_context_rows": int(len(symbol_day_context)),
        "event_contaminated_fact_rows": int(len(contaminated)),
        "event_contaminated_fact_pct": round((len(contaminated) / len(enriched)) * 100, 2) if len(enriched) else 0.0,
        "event_contamination_by_symbol": by_symbol,
        "paths": {name: str(path) for name, path in paths.items()},
    }


def render_summary_markdown(summary: dict) -> str:
    lines = [
        "# Broker Data Enrichment Summary",
        "",
        "> Layer 3 research infrastructure. Not a trading signal.",
        "",
        "## Totals",
        "",
        f"- Generated at: `{summary['generated_at']}`",
        f"- Broker-flow fact rows read: `{summary['fact_rows']}`",
        f"- Enriched rows written: `{summary['enriched_rows']}`",
        f"- Symbols: `{summary['symbols']}`",
        f"- Observed broker IDs: `{summary['observed_broker_ids']}`",
        f"- Broker IDs mapped to public names: `{summary['mapped_broker_ids']}`",
        f"- Broker IDs still unmapped: `{summary['unmapped_broker_ids']}`",
        f"- Event calendar rows: `{summary['event_calendar_rows']}`",
        f"- Fact-table symbols with L-001 event coverage: `{len(summary['fact_symbols_with_event_coverage'])}`",
        f"- Fact-table symbols without L-001 event coverage: `{len(summary['fact_symbols_without_event_coverage'])}`",
        f"- Event window: `+/-{summary['event_window_days']} calendar days`",
        f"- Broker-flow rows with nearby event context: `{summary['event_contaminated_fact_rows']}` ({summary['event_contaminated_fact_pct']}%)",
        "",
        "## Read This Before Interpreting The Zeros",
        "",
        "`0% nearby-event rows` means different things depending on coverage:",
        "",
        "- For symbols with L-001 event coverage, it means no event was found within the configured window.",
        "- For symbols without L-001 event coverage, it means the event table has no symbol records yet. That is `unknown`, not clean.",
        "",
        f"Symbols with event coverage: `{', '.join(summary['fact_symbols_with_event_coverage'])}`",
        "",
        f"Symbols without event coverage yet: `{', '.join(summary['fact_symbols_without_event_coverage'])}`",
        "",
        "## Symbol-Day Context Quality",
        "",
        "| Quality | Symbol-days |",
        "|---|---:|",
    ]
    for key, value in summary["event_context_quality_counts"].items():
        lines.append(f"| {key} | {value} |")
    lines.extend(
        [
            "",
            "## Broker Source Note",
            "",
            summary["broker_source_note"],
            "",
            "## Event Contamination By Symbol",
            "",
            "| Symbol | Rows | Nearby-event rows | Nearby-event % |",
            "|---|---:|---:|---:|",
        ]
    )
    for row in summary["event_contamination_by_symbol"]:
        lines.append(
            f"| {row['symbol']} | {row['rows']} | {row['event_contaminated_rows']} | {row['event_contaminated_pct']}% |"
        )
    lines.extend(
        [
            "",
            "## Unmapped Broker IDs",
            "",
            ", ".join(summary["unmapped_broker_id_list"]) if summary["unmapped_broker_id_list"] else "None",
            "",
            "## Output Files",
            "",
        ]
    )
    for name, path in summary["paths"].items():
        lines.append(f"- `{name}`: `{path}`")
    lines.append("")
    return "\n".join(lines)


def fetch_text(url: str) -> str:
    request = Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 (compatible; broker-data-enrichment/1.0; research use)",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        },
    )
    with urlopen(request, timeout=30) as response:
        return response.read().decode("utf-8", errors="replace")


def normalize_numeric_broker_code(value: object) -> str | None:
    text = str(value or "").strip()
    if not re.fullmatch(r"\d+", text):
        return None
    return str(int(text))


def broker_sort_key(value: object) -> tuple[int, str]:
    text = str(value)
    return (int(text), text) if text.isdigit() else (9999, text)


def make_tms_url_guess(broker_id: object) -> str:
    text = str(broker_id or "").strip()
    if not text.isdigit():
        return ""
    return f"https://tms{int(text):02d}.nepsetms.com.np"


def clean_date(value: object) -> str:
    text = str(value or "").strip()
    match = re.search(r"\d{4}-\d{2}-\d{2}", text)
    return match.group(0) if match else ""


def classify_event_family(event_type: str) -> str:
    text = event_type.lower()
    if "listing" in text:
        return "listing"
    if "right" in text:
        return "rights"
    if "agm" in text:
        return "agm"
    if "dividend" in text or "bonus" in text or "book_closure" in text:
        return "dividend_bonus"
    return "other"


def classify_event_importance(event_type: str, role: str) -> str:
    text = event_type.lower()
    if role in {"book_close_date", "ex_date", "listing_date", "right_open_date", "right_close_date", "right_final_date"}:
        return "high"
    if "dividend" in text or "bonus" in text or "right" in text or "book_closure" in text:
        return "high"
    if "agm" in text:
        return "medium"
    return "low"


def default_context_row(date_text: str, symbol: str, quality: str) -> dict[str, object]:
    return {
        "date": date_text,
        "symbol": symbol,
        "event_context_quality": quality,
        "event_contamination_flag": False,
        "event_nearby_10d_count": 0,
        "event_recent_30d_count": 0,
        "event_upcoming_10d_count": 0,
        "event_same_day_count": 0,
        "closest_event_date": "",
        "closest_event_days": "",
        "closest_event_type": "",
        "closest_event_family": "",
        "closest_event_role": "",
        "nearby_event_types_10d": "",
        "nearby_event_families_10d": "",
        "has_dividend_bonus_10d": False,
        "has_rights_10d": False,
        "has_agm_10d": False,
        "has_listing_10d": False,
    }


def empty_symbol_day_context(symbol_days: pd.DataFrame) -> pd.DataFrame:
    return pd.DataFrame([default_context_row(row["date"], row["symbol"], "event_calendar_empty") for _, row in symbol_days.iterrows()])


def join_unique(values: Iterable[object]) -> str:
    clean = sorted({str(value).strip() for value in values if str(value).strip()})
    return "|".join(clean)


def has_family(frame: pd.DataFrame, family: str) -> bool:
    return bool((frame["event_family"] == family).any())


if __name__ == "__main__":
    main()
