"""
Builds experiments/shared/universe_v2_candidate.csv from the ShareSansar archive.

Reproducible candidate registry for the universe v1 -> v2 expansion (Romeo-reviewed
2026-04-19). This script is the ONLY source of truth for the candidate list. Do not
hand-edit the CSV; rerun this script.

Output columns:
    symbol                      - NEPSE ticker
    first_seen                  - earliest date in archive with this symbol
    last_seen                   - latest date in archive with this symbol
    days_with_data              - total unique trading dates in archive
    continuous_history          - True if first_seen == archive earliest date
    active_days_90              - count of last-90-CSV days with Turnover > 0
    median_turnover_90d         - median NPR turnover on active days (last 90 CSVs)
    median_volume_90d           - median share volume on active days (last 90 CSVs)
    median_close_90d            - median close price on active days (last 90 CSVs)
    pure_equity_flag            - True if not excluded by pattern
    excluded_reason             - why excluded (empty if pure_equity_flag True)
    sector_guess                - high-confidence sector or pattern-based guess
    sector_confidence           - high / medium / low
    sector_source               - how sector was assigned
    selected_v2_candidate       - True if: pure equity AND continuous_history AND
                                  active_days_90 >= 30 AND in sector-quota top-N
    notes                       - free-form flags for manual review

This file is a CANDIDATE. Sectors must be manually verified (sector_verified column
is NOT set here) before freezing as universe_v2.csv. See the review packet from
Romeo 2026-04-19.
"""

from __future__ import annotations
import csv
import glob
import os
import re
import statistics
from collections import defaultdict
from dataclasses import dataclass, field, asdict
from datetime import date, datetime
from pathlib import Path

# --------------------------------------------------------------------------- #
# Config
# --------------------------------------------------------------------------- #

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
ARCHIVE_DIR = REPO_ROOT / "sharesansar_datascrape" / "data"
OUTPUT_CSV = REPO_ROOT / "experiments" / "shared" / "universe_v2_candidate.csv"

ACTIVE_DAYS_MIN_90 = 30          # min active days in last 90 CSVs
RECENT_WINDOW_CSVS = 90          # size of recent window

# --------------------------------------------------------------------------- #
# Exclusion patterns (pure_equity filter)
# --------------------------------------------------------------------------- #

DEBENTURE_PATTERN = re.compile(r"D\d{2}$")       # e.g. ICFCD83, SBD87
PROMOTER_SUFFIX = "PO"                           # e.g. RBCLPO

# Known non-equity instrument codes (mutual funds, ETFs, closed-end funds).
# Conservative: only exclude tickers we have external confirmation are non-equity.
# When in doubt, keep it and flag for manual review.
KNOWN_MUTUAL_FUNDS = {
    "NABBC", "NIBSF2", "KEF", "PSF", "SEF", "SBCF", "SLCF", "NICBF",
    "NBF2", "SIGS2", "SFMF", "CMF2", "NMB50",
    # Added 2026-04-19 after ShareSansar verification
    "LUK",  # Laxmi Unnati Kosh - closed-end fund
}

# --------------------------------------------------------------------------- #
# Sector classification
#
# High-confidence map built from NEPSE/SEBON disclosures and ShareSansar sector
# tags. Anything not in this map falls through to pattern-based medium/low
# confidence guess, and is flagged for manual verification.
# --------------------------------------------------------------------------- #

HIGH_CONFIDENCE_SECTOR = {
    # Commercial banks (verified against NRB Class A bank list)
    "NABIL": "COMMERCIAL_BANK",
    "EBL": "COMMERCIAL_BANK",
    "NBL": "COMMERCIAL_BANK",
    "KBL": "COMMERCIAL_BANK",
    "PRVU": "COMMERCIAL_BANK",
    "NICA": "COMMERCIAL_BANK",
    "SANIMA": "COMMERCIAL_BANK",
    "GBIME": "COMMERCIAL_BANK",
    "SBI": "COMMERCIAL_BANK",
    "SBL": "COMMERCIAL_BANK",
    "SCB": "COMMERCIAL_BANK",
    "NMB": "COMMERCIAL_BANK",
    "MBL": "COMMERCIAL_BANK",
    "PCBL": "COMMERCIAL_BANK",
    "CZBIL": "COMMERCIAL_BANK",
    "ADBL": "COMMERCIAL_BANK",
    "HBL": "COMMERCIAL_BANK",
    "NIMB": "COMMERCIAL_BANK",

    # Development banks (NRB Class B) - verified
    # LBBL = Lumbini Bikas Bank (Romeo correction 2026-04-19)
    "LBBL": "DEV_BANK",
    "SAPDBL": "DEV_BANK",
    "JBBL": "DEV_BANK",
    "MNBBL": "DEV_BANK",
    "GRDBL": "DEV_BANK",
    "KSBBL": "DEV_BANK",
    "SADBL": "DEV_BANK",
    "GBBL": "DEV_BANK",
    "MDB": "DEV_BANK",
    "CORBL": "DEV_BANK",
    "EDBL": "DEV_BANK",
    "SHINE": "DEV_BANK",
    "FMDBL": "DEV_BANK",

    # Life insurance
    "NLIC": "LIFE_INSURANCE",
    "ALICL": "LIFE_INSURANCE",
    "LICN": "LIFE_INSURANCE",
    "PRIN": "LIFE_INSURANCE",
    "NLICL": "LIFE_INSURANCE",

    # Non-life insurance
    "NRIC": "NON_LIFE_INSURANCE",
    "NLG": "NON_LIFE_INSURANCE",
    "IGI": "NON_LIFE_INSURANCE",
    "NICL": "NON_LIFE_INSURANCE",
    "PROFL": "NON_LIFE_INSURANCE",
    "NIL": "NON_LIFE_INSURANCE",
    "SICL": "NON_LIFE_INSURANCE",
    "RBCL": "NON_LIFE_INSURANCE",

    # Hydropower - high-confidence set
    # NGPL = Ngadi Group Power (Romeo verified 2026-04-19)
    "NGPL": "HYDROPOWER",
    "UPPER": "HYDROPOWER",
    "API": "HYDROPOWER",
    "AKPL": "HYDROPOWER",
    "AHPC": "HYDROPOWER",
    "RHPL": "HYDROPOWER",
    "RADHI": "HYDROPOWER",
    "NHPC": "HYDROPOWER",
    "BPCL": "HYDROPOWER",
    "CHCL": "HYDROPOWER",
    "SHPC": "HYDROPOWER",
    "BARUN": "HYDROPOWER",
    "HURJA": "HYDROPOWER",
    "HPPL": "HYDROPOWER",
    "UMHL": "HYDROPOWER",
    "JOSHI": "HYDROPOWER",
    "MEN": "HYDROPOWER",

    # Finance companies (NRB Class C)
    "MFIL": "FINANCE",
    "NFS": "FINANCE",
    "GFCL": "FINANCE",
    "SIFC": "FINANCE",
    "ICFC": "FINANCE",
    "CFCL": "FINANCE",
    "GUFL": "FINANCE",
    "RLFL": "FINANCE",
    "BFC": "FINANCE",
    "MPFL": "FINANCE",
    "GMFIL": "FINANCE",
    "PFL": "FINANCE",
    "JFL": "FINANCE",
    "SFCL": "FINANCE",

    # Microfinance (NRB Class D - laghubitta)
    "CBBL": "MICROFINANCE",
    "DDBL": "MICROFINANCE",
    "NUBL": "MICROFINANCE",
    "SKBBL": "MICROFINANCE",
    "SWBBL": "MICROFINANCE",
    "MLBL": "MICROFINANCE",
    "SLBBL": "MICROFINANCE",
    "GBLBS": "MICROFINANCE",

    # Manufacturing / consumer
    "SHIVM": "MANUFACTURING",   # Shivam Cements
    "UNL": "MANUFACTURING",     # Unilever Nepal
    "BNL": "MANUFACTURING",     # Bottlers Nepal Limited
    "BNT": "MANUFACTURING",     # Bottlers Nepal Terai
    "HDL": "MANUFACTURING",     # Himalayan Distillery
    "NTC": "TELECOM",           # Nepal Telecom - own sector
    "STC": "TRADING",           # Salt Trading Corp - own sector

    # Hotels
    "OHL": "HOTEL",
    "SHL": "HOTEL",
    "TRH": "HOTEL",
    "CGH": "HOTEL",

    # Infrastructure / investment
    "NIFRA": "INFRA_INVEST",
    "HIDCL": "INFRA_INVEST",
    "CIT": "INVESTMENT",

    # Added 2026-04-19 after ShareSansar verification sweep (51 symbols)
    # ---------- HYDROPOWER (newly verified) ----------
    "AKJCL": "HYDROPOWER",   # Ankhukhola Hydropower
    "SSHL": "HYDROPOWER",    # Shiva Shree Hydropower
    "SHEL": "HYDROPOWER",    # Singati Hydro Energy
    "LEC": "HYDROPOWER",     # Liberty Energy Company
    "GHL": "HYDROPOWER",     # Ghalemdi Hydro
    "KKHC": "HYDROPOWER",    # Khani Khola Hydropower
    "SPDL": "HYDROPOWER",    # Synergy Power Development
    "GLH": "HYDROPOWER",     # Greenlife Hydropower
    "CHL": "HYDROPOWER",     # Chhyangdi Hydropower
    "UMRH": "HYDROPOWER",    # United Idi-Mardi and R.B. Hydropower
    "MHNL": "HYDROPOWER",    # Mountain Hydro Nepal
    "SJCL": "HYDROPOWER",    # Sanjen Jalavidhyut
    "HDHPC": "HYDROPOWER",   # Himal Dolakha Hydropower
    "UNHPL": "HYDROPOWER",   # Union Hydropower
    "UPCL": "HYDROPOWER",    # Universal Power Company
    "KPCL": "HYDROPOWER",    # Kalika Power Company
    "PPCL": "HYDROPOWER",    # Panchthar Power Company
    "PMHPL": "HYDROPOWER",   # Panchakanya Mai Hydropower
    "DHPL": "HYDROPOWER",    # Dibyashwari Hydropower
    "NHDL": "HYDROPOWER",    # Nepal Hydro Developer
    "RURU": "HYDROPOWER",    # Ru Ru Jalbidhyut Pariyojana (NOT microfinance despite pattern)

    # ---------- MICROFINANCE (newly verified) ----------
    "USLB": "MICROFINANCE",    # Unnati Sahakarya Laghubitta
    "KMCDB": "MICROFINANCE",   # Kalika Laghubitta
    "MSLB": "MICROFINANCE",    # Mahuli Laghubitta
    "GILB": "MICROFINANCE",    # Global IME Laghubitta
    "ALBSL": "MICROFINANCE",   # Asha Laghubitta
    "NICLBSL": "MICROFINANCE", # NIC Asia Laghubitta
    "ILBS": "MICROFINANCE",    # Infinity Laghubitta
    "MLBBL": "MICROFINANCE",   # Mithila Laghubitta
    "NMFBS": "MICROFINANCE",   # National Laghubitta
    "ACLBSL": "MICROFINANCE",  # Aarambha Chautari Laghubitta
    "GLBSL": "MICROFINANCE",   # Gurans Laghubitta
    "SLBSL": "MICROFINANCE",   # Samudayik Laghubitta
    "VLBS": "MICROFINANCE",    # Vijaya Laghubitta
    "SMFBS": "MICROFINANCE",   # Swabhimaan Laghubitta
    "MLBSL": "MICROFINANCE",   # Mahila Laghubitta
    "GMFBS": "MICROFINANCE",   # Ganapati Laghubitta
    "LLBS": "MICROFINANCE",    # Laxmi Laghubitta
    "JSLBB": "MICROFINANCE",   # Janautthan Samudayic Laghubitta
    "RSDC": "MICROFINANCE",    # RSDC Laghubitta
    "JBLB": "MICROFINANCE",    # Jeevan Bikas Laghubitta
    "MERO": "MICROFINANCE",    # Mero Microfinance Laghubitta
    "SMATA": "MICROFINANCE",   # Samata Gharelu Laghubitta
    "FOWAD": "MICROFINANCE",   # Forward Microfinance Laghubitta
    "NMBMF": "MICROFINANCE",   # NMB Laghubitta (NOT mutual fund despite MF suffix)
    "SMB": "MICROFINANCE",     # Support Laghubitta

    # ---------- DEV_BANK (newly verified) ----------
    "SINDU": "DEV_BANK",       # Sindhu Bikas Bank

    # ---------- INVESTMENT (newly verified) ----------
    "CHDC": "INVESTMENT",      # CEDB Holdings
    "NRN": "INVESTMENT",       # NRN Infrastructure & Development (ShareSansar sector: Investment)

    # ---------- TRADING (newly verified) ----------
    "BBC": "TRADING",          # Bishal Bazar Company (retail/shopping-center operator)
}

# Medium-confidence patterns (applied only if symbol not in high-confidence map)
MEDIUM_CONFIDENCE_PATTERNS = [
    # Order matters: more specific first
    (re.compile(r"LBSL?$"), "MICROFINANCE"),
    (re.compile(r"LBBL?$"), "MICROFINANCE"),
    (re.compile(r"LBB$"),   "MICROFINANCE"),
    (re.compile(r"LBS$"),   "MICROFINANCE"),
    (re.compile(r"BSL$"),   "MICROFINANCE"),
    (re.compile(r"MFBS$"),  "MICROFINANCE"),
    (re.compile(r"MFIL$"),  "FINANCE"),
    (re.compile(r"DBL$"),   "DEV_BANK"),
    (re.compile(r"BBL$"),   "DEV_BANK"),
    (re.compile(r"HPC$"),   "HYDROPOWER"),
    (re.compile(r"HPL$"),   "HYDROPOWER"),
    (re.compile(r"HDL$"),   "HYDROPOWER"),   # low confidence but common
    (re.compile(r"PCL$"),   "HYDROPOWER"),
]

# --------------------------------------------------------------------------- #
# Core
# --------------------------------------------------------------------------- #

@dataclass
class SymbolStats:
    symbol: str
    first_seen: str = ""
    last_seen: str = ""
    days_with_data: int = 0
    continuous_history: bool = False
    active_days_90: int = 0
    median_turnover_90d: float = 0.0
    median_volume_90d: float = 0.0
    median_close_90d: float = 0.0
    pure_equity_flag: bool = True
    excluded_reason: str = ""
    sector_guess: str = "UNKNOWN"
    sector_confidence: str = "low"
    sector_source: str = ""
    selected_v2_candidate: bool = False
    notes: str = ""


def parse_date_from_filename(fn: str) -> date | None:
    m = re.match(r"(\d{2})_(\d{2})_(\d{4})\.csv$", os.path.basename(fn))
    if not m:
        return None
    mm, dd, yyyy = m.groups()
    try:
        return date(int(yyyy), int(mm), int(dd))
    except ValueError:
        return None


def to_float(s: str) -> float | None:
    if s is None:
        return None
    s = s.strip().replace(",", "").replace('"', "")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def classify_pure_equity(symbol: str) -> tuple[bool, str]:
    """Return (pure_equity_flag, excluded_reason)."""
    if DEBENTURE_PATTERN.search(symbol):
        return False, "debenture_pattern"
    if symbol.endswith(PROMOTER_SUFFIX):
        return False, "promoter_share"
    if symbol in KNOWN_MUTUAL_FUNDS:
        return False, "known_mutual_fund"
    return True, ""


def classify_sector(symbol: str) -> tuple[str, str, str]:
    """Return (sector_guess, sector_confidence, sector_source)."""
    if symbol in HIGH_CONFIDENCE_SECTOR:
        return HIGH_CONFIDENCE_SECTOR[symbol], "high", "curated_lookup"
    for pat, sector in MEDIUM_CONFIDENCE_PATTERNS:
        if pat.search(symbol):
            return sector, "medium", f"pattern:{pat.pattern}"
    return "UNKNOWN", "low", "unclassified"


def build() -> list[SymbolStats]:
    csv_files = sorted(
        (p for p in glob.glob(str(ARCHIVE_DIR / "*.csv"))
         if parse_date_from_filename(p) is not None),
        key=parse_date_from_filename,
    )
    if not csv_files:
        raise RuntimeError(f"No CSVs found in {ARCHIVE_DIR}")

    archive_first = parse_date_from_filename(csv_files[0])
    archive_last = parse_date_from_filename(csv_files[-1])
    print(f"Archive: {len(csv_files)} CSVs, {archive_first} -> {archive_last}")

    recent_files = csv_files[-RECENT_WINDOW_CSVS:]

    # Pass 1: full archive scan for first_seen / last_seen / days_with_data
    first_seen: dict[str, date] = {}
    last_seen: dict[str, date] = {}
    days_count: dict[str, int] = defaultdict(int)
    for path in csv_files:
        d = parse_date_from_filename(path)
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            seen_today = set()
            for row in reader:
                sym = row.get("Symbol", "").strip()
                if not sym or sym in seen_today:
                    continue
                seen_today.add(sym)
                if sym not in first_seen:
                    first_seen[sym] = d
                last_seen[sym] = d
                days_count[sym] += 1

    # Pass 2: recent-window scan for activity + liquidity stats
    recent_turnover: dict[str, list[float]] = defaultdict(list)
    recent_volume: dict[str, list[float]] = defaultdict(list)
    recent_close: dict[str, list[float]] = defaultdict(list)
    for path in recent_files:
        with open(path, newline="", encoding="utf-8") as fh:
            reader = csv.DictReader(fh)
            for row in reader:
                sym = row.get("Symbol", "").strip()
                if not sym:
                    continue
                turn = to_float(row.get("Turnover", ""))
                vol = to_float(row.get("Vol", ""))
                close = to_float(row.get("Close", ""))
                if turn is not None:
                    recent_turnover[sym].append(turn)
                if vol is not None:
                    recent_volume[sym].append(vol)
                if close is not None and close > 0:
                    recent_close[sym].append(close)

    # Build stats
    rows: list[SymbolStats] = []
    for sym, fs in first_seen.items():
        s = SymbolStats(symbol=sym)
        s.first_seen = fs.isoformat()
        s.last_seen = last_seen[sym].isoformat()
        s.days_with_data = days_count[sym]
        s.continuous_history = (fs == archive_first)

        active = [t for t in recent_turnover.get(sym, []) if t > 0]
        s.active_days_90 = len(active)
        s.median_turnover_90d = statistics.median(active) if active else 0.0
        vols = [v for v in recent_volume.get(sym, []) if v > 0]
        s.median_volume_90d = statistics.median(vols) if vols else 0.0
        closes = recent_close.get(sym, [])
        s.median_close_90d = statistics.median(closes) if closes else 0.0

        s.pure_equity_flag, s.excluded_reason = classify_pure_equity(sym)
        s.sector_guess, s.sector_confidence, s.sector_source = classify_sector(sym)

        # Notes: flag anything needing manual review
        note_parts = []
        if s.sector_confidence != "high":
            note_parts.append("SECTOR_UNVERIFIED")
        if s.pure_equity_flag and s.active_days_90 < ACTIVE_DAYS_MIN_90:
            note_parts.append("LOW_ACTIVITY")
        if s.pure_equity_flag and not s.continuous_history:
            note_parts.append("POST_2021_LISTING")
        if (s.pure_equity_flag and s.continuous_history
                and s.active_days_90 >= ACTIVE_DAYS_MIN_90
                and s.sector_guess == "UNKNOWN"):
            note_parts.append("MUST_CLASSIFY_BEFORE_FREEZE")
        s.notes = ";".join(note_parts)

        rows.append(s)

    # Pass 3: sector-quota selection (top-N per sector by median_turnover_90d)
    # Romeo's recommended move: registry first, selection second. We mark
    # selected_v2_candidate here but this is a PROVISIONAL flag - sectors must
    # be manually verified before these flags are trusted.
    sector_quota = {
        "COMMERCIAL_BANK": 17,
        "HYDROPOWER": 25,
        "MICROFINANCE": 12,
        "FINANCE": 8,
        "DEV_BANK": 8,
        "LIFE_INSURANCE": 5,
        "NON_LIFE_INSURANCE": 6,
        "MANUFACTURING": 6,
        "HOTEL": 4,
        "INFRA_INVEST": 3,
        "INVESTMENT": 1,
        "TELECOM": 1,
        "TRADING": 1,
    }

    eligible = [
        s for s in rows
        if s.pure_equity_flag
        and s.continuous_history
        and s.active_days_90 >= ACTIVE_DAYS_MIN_90
    ]
    by_sector: dict[str, list[SymbolStats]] = defaultdict(list)
    for s in eligible:
        by_sector[s.sector_guess].append(s)
    for sector, members in by_sector.items():
        members.sort(key=lambda x: -x.median_turnover_90d)
        quota = sector_quota.get(sector, 0)
        for m in members[:quota]:
            m.selected_v2_candidate = True

    rows.sort(key=lambda x: (-x.median_turnover_90d, x.symbol))
    return rows


def write_csv(rows: list[SymbolStats], path: Path) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fields = list(SymbolStats.__dataclass_fields__.keys())
    with open(path, "w", newline="", encoding="utf-8") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        for r in rows:
            row = asdict(r)
            for k, v in row.items():
                if isinstance(v, float):
                    row[k] = f"{v:.2f}"
            writer.writerow(row)


def summarize(rows: list[SymbolStats]) -> None:
    total = len(rows)
    pure = [r for r in rows if r.pure_equity_flag]
    cont = [r for r in pure if r.continuous_history]
    active = [r for r in cont if r.active_days_90 >= ACTIVE_DAYS_MIN_90]
    selected = [r for r in rows if r.selected_v2_candidate]

    print()
    print(f"Total symbols seen in archive:        {total}")
    print(f"Pure-equity (after filter):           {len(pure)}")
    print(f"  + continuous history since start:   {len(cont)}")
    print(f"  + active_days_90 >= {ACTIVE_DAYS_MIN_90}:            {len(active)}")
    print(f"Provisional selected_v2_candidate:    {len(selected)}")
    print()
    print("Provisional selection by sector (requires manual verification):")
    by_sector: dict[str, int] = defaultdict(int)
    for r in selected:
        by_sector[r.sector_guess] += 1
    for sector in sorted(by_sector, key=lambda s: -by_sector[s]):
        print(f"  {sector:20s} {by_sector[sector]:>3d}")

    unknown = [r for r in active if r.sector_guess == "UNKNOWN"]
    if unknown:
        print()
        print(f"{len(unknown)} eligible symbols with UNKNOWN sector — MUST classify before freeze:")
        for r in unknown:
            print(f"  {r.symbol:10s}  turn={r.median_turnover_90d:>14,.0f}")

    unverified = [r for r in active if r.sector_confidence != "high"]
    if unverified:
        print()
        print(f"{len(unverified)} eligible symbols with non-high sector confidence — verify before freeze:")
        for r in unverified:
            print(f"  {r.symbol:10s}  guess={r.sector_guess:18s} conf={r.sector_confidence}  source={r.sector_source}")


def main() -> None:
    rows = build()
    write_csv(rows, OUTPUT_CSV)
    summarize(rows)
    print()
    print(f"Wrote {len(rows)} rows to {OUTPUT_CSV}")


if __name__ == "__main__":
    main()
