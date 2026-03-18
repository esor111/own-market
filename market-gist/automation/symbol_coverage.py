"""
Show whether a symbol list is ready for reliability runs.
Usage: python symbol_coverage.py @core_reliability
   or: python symbol_coverage.py SMHL NABIL
"""
import json
import os
import sys

from config import SECTOR_MAP_FILE, resolve_symbols, load_json_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python symbol_coverage.py SYMBOL_OR_LIST [SYMBOL_OR_LIST ...]")
        sys.exit(1)

    try:
        symbols = resolve_symbols(sys.argv[1:])
    except ValueError as exc:
        print(str(exc))
        sys.exit(1)

    sector_map = {
        str(symbol).upper(): str(sector).upper()
        for symbol, sector in load_json_file(SECTOR_MAP_FILE, {}).items()
    }

    mapped = []
    unmapped = []
    for symbol in symbols:
        sector = sector_map.get(symbol)
        if sector:
            mapped.append({"symbol": symbol, "sector": sector})
        else:
            unmapped.append(symbol)

    summary = {
        "symbols_requested": symbols,
        "total_symbols": len(symbols),
        "sector_mapped_count": len(mapped),
        "sector_unmapped_count": len(unmapped),
        "mapped": mapped,
        "unmapped": unmapped,
        "sector_map_file": os.path.abspath(SECTOR_MAP_FILE)
    }

    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
