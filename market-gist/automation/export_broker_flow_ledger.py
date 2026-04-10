"""
Export a normalized broker-flow ledger from an existing daily manual package.

This script is intentionally separate from the live prediction pipeline.
It writes one file per symbol/day under broker_flow_ledger/<SYMBOL>/<DATE>.json.

Usage:
    python export_broker_flow_ledger.py NABIL 2026-03-31 1D
    python export_broker_flow_ledger.py NABIL 2026-03-31 1D --manual-package C:\\path\\to\\manual_package.json
"""
from __future__ import annotations

import argparse
import os
import sys

from broker_flow_ledger_utils import (
    build_broker_flow_ledger,
    build_ledger_output_path,
    load_manual_package,
    write_json,
)


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export a broker-flow ledger from a manual package JSON.")
    parser.add_argument("symbol", help="Symbol to export, e.g. NABIL")
    parser.add_argument("run_date", help="Run date in YYYY-MM-DD format")
    parser.add_argument("timeframe", nargs="?", default="1D", help="Timeframe used to locate the manual package, default: 1D")
    parser.add_argument(
        "--manual-package",
        dest="manual_package",
        default=None,
        help="Optional explicit path to a manual_package.json file",
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Overwrite an existing broker ledger file if it already exists",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    package = load_manual_package(
        args.symbol,
        args.run_date,
        args.timeframe,
        manual_package_path=args.manual_package,
    )
    ledger = build_broker_flow_ledger(package)
    output_path = build_ledger_output_path(args.symbol, args.run_date)
    created = write_json(output_path, ledger, overwrite=args.force)
    if created:
        print(f"Created: {output_path}")
    else:
        print(f"Skipped existing: {output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
