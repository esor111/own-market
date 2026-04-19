"""
Price data integrity check — Layer 1 production utility.

Verifies CSV files in sharesansar_datascrape/data/ are structurally sound before
the scorer relies on them. Detects:

1. Git merge conflict markers (`<<<<<<<`, `=======`, `>>>>>>>`) — the specific
   failure mode that silently broke the scorer for 16 files on 2026-04-18.
2. Empty files (0 bytes).
3. Files missing the expected CSV header.
4. Files with header but zero data rows.

Designed as a defensive pre-check. Output:
- Exit 0 if clean.
- Exit 1 if any corruption found. Writes a report to stderr.

--------------------------------------------------------------------------------
Ownership note (Romeo 2026-04-18 review):
This file lives in Layer 1 (market-gist/automation/) rather than
experiments/shared/ because Layer 1 code should not long-term depend on
experiments/shared. The scorer calls this check directly; the daily runner
calls it for UX. Keep the primary copy here.

--------------------------------------------------------------------------------
CLI usage:

    # Check the default data dir
    python market-gist/automation/price_data_integrity.py

    # Check a specific directory
    python market-gist/automation/price_data_integrity.py --data-dir <path>

    # Check and delete corrupt files (they'll need to be re-scraped)
    python market-gist/automation/price_data_integrity.py --delete-corrupt

--------------------------------------------------------------------------------
Library usage:

    from price_data_integrity import check_data_dir, IntegrityError

    # Raise on corruption
    check_data_dir(raise_on_corrupt=True)

    # Just inspect
    report = check_data_dir()
    if report["corrupt"]:
        print(f"Corrupt files: {len(report['corrupt'])}")

--------------------------------------------------------------------------------
Where it's wired:
- score_persistence_shadow_reports.py calls check_data_dir(raise_on_corrupt=True)
  at the start of build_scored_rows() so garbage CSVs cannot silently mis-score.
- run_persistence_shadow_daily.py optionally calls it as Step 0 for nicer UX.
"""
from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path


# Default location: repo_root/sharesansar_datascrape/data/
# This file is at repo_root/market-gist/automation/price_data_integrity.py
# So go up 2 levels then into sibling directory.
_SCRIPT_DIR = Path(__file__).resolve().parent
_REPO_ROOT = _SCRIPT_DIR.parent.parent
DEFAULT_DATA_DIR = _REPO_ROOT / "sharesansar_datascrape" / "data"

MERGE_CONFLICT_MARKERS = ("<<<<<<<", "=======", ">>>>>>>")

EXPECTED_HEADER_PREFIX = "Symbol,"


class IntegrityError(Exception):
    """Raised when the price data directory fails integrity checks."""


def _resolve_data_dir(override: str | None) -> Path:
    if override:
        p = Path(override).resolve()
        if not p.exists():
            raise FileNotFoundError(f"Override data dir does not exist: {p}")
        return p
    if DEFAULT_DATA_DIR.exists():
        return DEFAULT_DATA_DIR
    raise FileNotFoundError(
        f"Could not locate sharesansar data dir. Expected at: {DEFAULT_DATA_DIR}"
    )


def _classify_file(path: Path) -> tuple[str, str] | None:
    """Return (severity, reason) if the file is broken, else None.

    severity is 'corrupt' (will break downstream code) or 'suspect' (worth a look).
    """
    try:
        size = path.stat().st_size
    except OSError as exc:
        return "corrupt", f"cannot stat: {exc}"

    if size == 0:
        return "corrupt", "empty file (0 bytes)"

    try:
        with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
            first_line = fh.readline()
            second_line = fh.readline()
    except OSError as exc:
        return "corrupt", f"cannot read: {exc}"

    # Check 1: git merge conflict markers anywhere in the first line
    if any(marker in first_line for marker in MERGE_CONFLICT_MARKERS):
        return "corrupt", "git merge conflict marker on line 1"

    # Check 2: expected header
    if not first_line.startswith(EXPECTED_HEADER_PREFIX):
        return "corrupt", f"unexpected header (first line does not start with '{EXPECTED_HEADER_PREFIX}')"

    # Check 3: scan first N lines for merge markers (some CSVs had conflicts mid-file)
    try:
        with path.open("r", encoding="utf-8-sig", errors="replace") as fh:
            for lineno, line in enumerate(fh, start=1):
                if lineno > 50:
                    break
                if any(marker in line for marker in MERGE_CONFLICT_MARKERS):
                    return "corrupt", f"git merge conflict marker on line {lineno}"
    except OSError as exc:
        return "corrupt", f"cannot scan: {exc}"

    # Check 4: header-only file (no data rows)
    if not second_line.strip():
        return "suspect", "header present but zero data rows (may be a legitimate holiday with no data)"

    return None


def check_data_dir(
    data_dir: str | Path | None = None,
    raise_on_corrupt: bool = False,
) -> dict:
    """Inspect all .csv files in data_dir. Return a structured report.

    Report shape:
        {
            "data_dir": str,
            "total_files": int,
            "clean_files": int,
            "corrupt": [{"path": str, "reason": str}, ...],
            "suspect": [{"path": str, "reason": str}, ...],
        }

    If raise_on_corrupt is True and any corrupt files exist, raises IntegrityError.
    """
    resolved_dir = _resolve_data_dir(str(data_dir) if data_dir else None)

    corrupt: list[dict[str, str]] = []
    suspect: list[dict[str, str]] = []
    clean_count = 0

    csv_files = sorted(p for p in resolved_dir.iterdir() if p.suffix == ".csv")
    for path in csv_files:
        result = _classify_file(path)
        if result is None:
            clean_count += 1
            continue
        severity, reason = result
        entry = {"path": str(path), "reason": reason}
        if severity == "corrupt":
            corrupt.append(entry)
        else:
            suspect.append(entry)

    report = {
        "data_dir": str(resolved_dir),
        "total_files": len(csv_files),
        "clean_files": clean_count,
        "corrupt": corrupt,
        "suspect": suspect,
    }

    if raise_on_corrupt and corrupt:
        preview = ", ".join(os.path.basename(c["path"]) for c in corrupt[:5])
        more = "" if len(corrupt) <= 5 else f" (+{len(corrupt) - 5} more)"
        raise IntegrityError(
            f"{len(corrupt)} corrupt price CSV(s) in {resolved_dir}: {preview}{more}. "
            "Run `python market-gist/automation/price_data_integrity.py` to see details. "
            "Likely fix: delete corrupt files and re-scrape via "
            "`python sharesansar_datascrape/scrape_nepse.py --start-date <d1> --end-date <d2>`."
        )

    return report


def _format_report(report: dict, verbose: bool) -> str:
    lines = [
        f"Price data integrity check: {report['data_dir']}",
        f"  Total CSVs: {report['total_files']}",
        f"  Clean: {report['clean_files']}",
        f"  Corrupt: {len(report['corrupt'])}",
        f"  Suspect: {len(report['suspect'])}",
    ]
    if report["corrupt"]:
        lines.append("")
        lines.append("CORRUPT FILES (will break the scorer):")
        for entry in report["corrupt"]:
            lines.append(f"  - {os.path.basename(entry['path'])}: {entry['reason']}")
    if verbose and report["suspect"]:
        lines.append("")
        lines.append("SUSPECT FILES (worth a look, may be legitimate):")
        for entry in report["suspect"]:
            lines.append(f"  - {os.path.basename(entry['path'])}: {entry['reason']}")
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data-dir", help="Override the default sharesansar data directory")
    parser.add_argument(
        "--delete-corrupt",
        action="store_true",
        help="Delete files flagged as corrupt. Suspect files are never deleted. Dangerous — only use before re-scraping.",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Also show suspect files in the console output.",
    )
    args = parser.parse_args()

    try:
        report = check_data_dir(data_dir=args.data_dir, raise_on_corrupt=False)
    except FileNotFoundError as exc:
        print(f"FAILED: {exc}", file=sys.stderr)
        return 2

    print(_format_report(report, verbose=args.verbose))

    if report["corrupt"] and args.delete_corrupt:
        print("", file=sys.stderr)
        print("--delete-corrupt enabled. Deleting corrupt files...", file=sys.stderr)
        for entry in report["corrupt"]:
            try:
                os.remove(entry["path"])
                print(f"  deleted: {os.path.basename(entry['path'])}", file=sys.stderr)
            except OSError as exc:
                print(f"  FAILED to delete {entry['path']}: {exc}", file=sys.stderr)
        print("Now re-scrape the deleted dates:", file=sys.stderr)
        print("  python sharesansar_datascrape/scrape_nepse.py --start-date <first> --end-date <last>", file=sys.stderr)

    if report["corrupt"]:
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
