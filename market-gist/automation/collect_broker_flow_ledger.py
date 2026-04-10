"""
Collect a separate broker-flow ledger from daily manual-package outputs.

This stays outside the live Romeo/Juliet prompt path. It can:
- export a ledger from an already-built manual package
- optionally build missing manual packages first using the proven
  manual_llm_package.py flow
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List

from broker_flow_market_calendar import get_market_day_context
from broker_flow_ledger_utils import (
    build_broker_flow_ledger,
    build_ledger_output_path,
    find_manual_package_path,
    load_manual_package,
    write_json,
)


REPO_ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = REPO_ROOT / "data"
LEDGER_ROOT = REPO_ROOT / "broker_flow_ledger"
DEFAULT_SYMBOLS_PATH = LEDGER_ROOT / "COMMERCIAL_BANK_SYMBOLS.json"
DEFAULT_TIMEFRAME = "1D"
DEFAULT_RUN_DATE = datetime.now().strftime("%Y-%m-%d")


def read_json(path: Path):
    with path.open("r", encoding="utf-8") as handle:
        return json.load(handle)


def load_symbols(path: Path) -> List[str]:
    payload = read_json(path)
    if isinstance(payload, dict):
        symbols = payload.get("symbols", [])
    else:
        symbols = payload
    if not isinstance(symbols, list):
        raise ValueError(f"Invalid symbol list in {path}")
    return [str(symbol).upper().strip() for symbol in symbols if str(symbol).strip()]


def build_missing_manual_package(symbol: str, timeframe: str, run_date: str) -> bool:
    script_path = REPO_ROOT / "automation" / "manual_llm_package.py"
    cmd = [sys.executable, str(script_path), symbol.upper(), timeframe.upper(), run_date]
    result = subprocess.run(cmd, cwd=str(REPO_ROOT / "automation"))
    return result.returncode == 0


def collect_for_symbol(
    symbol: str,
    timeframe: str,
    run_date: str,
    build_missing: bool,
    force: bool,
    market_day_context: dict,
) -> dict:
    manual_package_path = Path(find_manual_package_path(symbol, run_date, timeframe))
    result = {
        "symbol": symbol,
        "run_date": run_date,
        "timeframe": timeframe,
        "manual_package_path": str(manual_package_path),
        "market_day_context": market_day_context,
        "status": None,
        "ledger_path": None,
    }
    if not manual_package_path.exists() and build_missing:
        print(f"[BUILD] {symbol}: building missing {timeframe} manual package for {run_date}")
        if not build_missing_manual_package(symbol, timeframe, run_date):
            print(f"[WARN] {symbol}: manual package build failed")
            result["status"] = "build_failed"
            return result

    if not manual_package_path.exists():
        day_hint = "expected_market_session" if market_day_context.get("expected_market_session") else "non_trading_or_unverified_day"
        print(f"[MISS] {symbol}: no {timeframe} manual package JSON found for {run_date} ({day_hint})")
        result["status"] = "missing_manual_package"
        return result

    try:
        package = load_manual_package(
            symbol,
            run_date,
            timeframe,
            manual_package_path=str(manual_package_path),
        )
    except Exception as exc:
        print(f"[WARN] {symbol}: failed to load {manual_package_path}: {exc}")
        result["status"] = "load_failed"
        result["error"] = str(exc)
        return result

    ledger = build_broker_flow_ledger(package)
    output_path = Path(build_ledger_output_path(symbol, run_date))
    created = write_json(str(output_path), ledger, overwrite=force)
    result["ledger_path"] = str(output_path)
    if created:
        print(f"[OK] {symbol}: wrote {output_path}")
        result["status"] = "exported"
    else:
        print(f"[SKIP] {symbol}: existing ledger kept at {output_path}")
        result["status"] = "existing_kept"
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description="Collect the separate broker-flow ledger from daily manual-package outputs.")
    parser.add_argument("--symbols-path", default=str(DEFAULT_SYMBOLS_PATH), help="Path to COMMERCIAL_BANK_SYMBOLS.json")
    parser.add_argument("--timeframe", default=DEFAULT_TIMEFRAME, help="Manual package timeframe to collect")
    parser.add_argument("--run-date", default=DEFAULT_RUN_DATE, help="Run date in YYYY-MM-DD format")
    parser.add_argument("--symbol", action="append", dest="symbols", help="Restrict to one or more symbols")
    parser.add_argument("--build-missing", action="store_true", help="Build missing manual packages before export")
    parser.add_argument("--force", action="store_true", help="Overwrite an existing ledger JSON")
    args = parser.parse_args()

    symbols_path = Path(args.symbols_path).resolve()
    if args.symbols:
        symbols = [s.upper().strip() for s in args.symbols if s.strip()]
    else:
        symbols = load_symbols(symbols_path)

    market_day_context = get_market_day_context(args.run_date)
    results = []
    for symbol in symbols:
        result = collect_for_symbol(
            symbol=symbol,
            timeframe=args.timeframe,
            run_date=args.run_date,
            build_missing=args.build_missing,
            force=args.force,
            market_day_context=market_day_context,
        )
        results.append(result)

    status_counts = {}
    for item in results:
        status = str(item.get("status") or "unknown")
        status_counts[status] = status_counts.get(status, 0) + 1

    summary = {
        "symbols": symbols,
        "timeframe": args.timeframe,
        "run_date": args.run_date,
        "build_missing": args.build_missing,
        "market_day_context": market_day_context,
        "written_files": sum(1 for item in results if item.get("status") == "exported"),
        "status_counts": status_counts,
        "results": results,
        "ledger_root": str(LEDGER_ROOT.resolve()),
        "data_root": str(DATA_ROOT.resolve()),
    }
    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
