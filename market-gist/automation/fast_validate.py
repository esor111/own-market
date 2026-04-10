"""
Run a small representative batch for faster development feedback.
Usage:
    python fast_validate.py
    python fast_validate.py 1W
    python fast_validate.py 1D @core_reliability
"""
import asyncio
import sys

from batch_analyze import main as batch_main


def build_argv():
    args = sys.argv[1:]
    timeframe = args[0] if args else "1W"
    symbol_args = args[1:] if len(args) > 1 else ["@dev_fast"]
    return [sys.argv[0], timeframe, *symbol_args]


if __name__ == "__main__":
    sys.argv = build_argv()
    asyncio.run(batch_main())
