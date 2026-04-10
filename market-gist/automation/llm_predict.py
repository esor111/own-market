"""
LLM Prediction Engine: builds context, renders prompt, stores predictions.

Applies code-side calibration to raw LLM conviction (research shows LLMs
cannot self-calibrate reliably - KalshiBench 2025).

Usage:
    # Interactive mode: build prompt for Claude Code
    python llm_predict.py EBL 1W

    # Store a prediction after Claude produces it
    python llm_predict.py EBL 1W --store prediction.json [--date DATE] [--agent AGENT_ID]

    # Batch store all predictions from an agent's folder (replay mode)
    python llm_predict.py --batch-store agents/agent-1-romeo/predictions/ --agent agent-1-romeo

    # Specify a date (default: today)
    python llm_predict.py EBL 1W --date 2026-03-29
"""
import json
import math
import os
import sys
from datetime import datetime
from pathlib import Path

sys.path.insert(0, os.path.dirname(__file__))

from artifact_io import save_json_atomic, save_text_atomic
from config import BASE_DIR, VALIDATION_DIR, get_run_directories, load_json_file as _load_json
from forward_context_enrichment import (
    build_market_breadth_lines,
    build_nrb_macro_lines,
    build_sharesansar_event_lines,
    format_manual_context_block,
    load_live_nrb_macro_snapshot,
    load_manual_context_overlay,
)


def load_json(path):
    """Load JSON, returning empty dict if missing."""
    return _load_json(path, {})


# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
PROMPT_TEMPLATE_PATH = os.path.join(BASE_DIR, "docs", "playbooks", "LLM_PREDICTION_PROMPT.md")
PREDICTIONS_DIR = os.path.join(BASE_DIR, "data", "predictions")
PREDICTIONS_LIVE_DIR = os.path.join(PREDICTIONS_DIR, "live")
PREDICTIONS_REPLAY_DIR = os.path.join(PREDICTIONS_DIR, "replay")
PREDICTIONS_SCORES_DIR = os.path.join(PREDICTIONS_DIR, "scores")
CALIBRATION_DIR = os.path.join(VALIDATION_DIR, "llm_calibration")
LATEST_CALIBRATION_PATH = os.path.join(CALIBRATION_DIR, "latest__llm_calibration.json")
MACRO_CONTEXT_PATH = os.path.join(BASE_DIR, "data", "macro_context.json")

SECTOR_MAP_PATH = os.path.join(os.path.dirname(__file__), "sector_map.json")

PROMPT_VERSION = "pred_v2"


# ---------------------------------------------------------------------------
# Sector map
# ---------------------------------------------------------------------------
def _load_sector_map():
    if os.path.isfile(SECTOR_MAP_PATH):
        with open(SECTOR_MAP_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


# ---------------------------------------------------------------------------
# Macro context
# ---------------------------------------------------------------------------
def build_macro_context_block(symbol, run_date):
    """Build the macro context block for the prediction prompt.

    Sources (in priority order):
    1. User-maintained macro_context.json (manual, highest signal)
    2. Derived from date (seasonal calendar position)
    """
    sector_map = _load_sector_map()
    sector = sector_map.get(symbol, "UNKNOWN")

    # Parse date for seasonal context
    try:
        dt = datetime.strptime(run_date, "%Y-%m-%d")
        month = dt.month
        month_name = dt.strftime("%B")
        day = dt.day
    except ValueError:
        month, month_name, day = 0, "unknown", 0

    # Seasonal position
    if month in (7, 8):
        seasonal = "PEAK SEASON (July-August). Fiscal year end, earnings, dividends. Historically strongest period."
    elif month == 6:
        seasonal = "Pre-peak buildup. Anticipation for fiscal year end results. Market often starts positioning."
    elif month in (9, 10):
        seasonal = "Dividend season (book closure). Secondary buying wave. Watch for sector-specific strength."
    elif month in (11, 12, 1):
        seasonal = "Quiet season transitioning to Poush quarter earnings (January). Lower activity expected."
    else:
        seasonal = "Quiet season (Feb-May). Limited catalysts. Watch for policy announcements."

    # Sector context
    if sector == "BANKING":
        sector_note = "BANKING sector (40-50% of NEPSE). Leading indicator for market direction. Watch Ashadh quarter earnings closely."
    elif sector == "HYDROPOWER":
        sector_note = "HYDROPOWER sector. Mid-weight sector. More volatile than banking. Watch for project-specific catalysts."
    else:
        sector_note = f"Sector: {sector}."

    lines = [
        f"Date: {run_date} ({month_name} {day})",
        f"Seasonal position: {seasonal}",
        f"Sector: {sector_note}",
    ]

    nrb_macro_snapshot = load_live_nrb_macro_snapshot(run_date)
    macro_lines = build_nrb_macro_lines(nrb_macro_snapshot, indent="  ")
    lines.append("")
    lines.append("Current macro signals (automated + manual):")
    if macro_lines:
        lines.extend(macro_lines)
    else:
        lines.append("  - No macro context available.")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Context building
# ---------------------------------------------------------------------------
def find_manual_package(symbol, timeframe, run_date):
    """Find the manual_llm_package JSON for this symbol/date."""
    run_dirs = get_run_directories(symbol, run_date)
    json_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__{timeframe}__manual_package.json",
    )
    if os.path.isfile(json_path):
        return json_path
    return None


def find_manual_package_markdown(symbol, timeframe, run_date):
    """Find the manual_llm_package markdown for this symbol/date."""
    run_dirs = get_run_directories(symbol, run_date)
    md_path = os.path.join(
        run_dirs["base"],
        f"{run_date}__{symbol}__{timeframe}__manual_package.md",
    )
    if os.path.isfile(md_path):
        return md_path
    return None


def curate_context_markdown(raw_markdown):
    """Reorder and clean context markdown for better LLM attention.

    Research shows LLMs attend most to START and END of context
    (lost-in-the-middle effect). Put highest-signal data first.

    Also strips sections where most values are 'unknown' to reduce noise.
    """
    lines = raw_markdown.split("\n")
    sections = {}
    current_section = "_header"
    sections[current_section] = []

    for line in lines:
        # Detect numbered section headers (e.g., "1. Market Regime")
        stripped = line.strip()
        if stripped and stripped[0].isdigit() and "." in stripped[:4]:
            current_section = stripped
            sections[current_section] = []
        else:
            sections[current_section].append(line)

    # Count "unknown" values per section to identify low-signal sections
    high_signal = []
    medium_signal = []
    low_signal = []

    for section_name, section_lines in sections.items():
        if section_name == "_header":
            high_signal.append((section_name, section_lines))
            continue

        text = "\n".join(section_lines)
        unknown_count = text.lower().count("unknown")
        total_lines = len([l for l in section_lines if l.strip().startswith("-")])

        # Classify by signal quality
        name_lower = section_name.lower()
        if any(k in name_lower for k in ("market", "regime", "trend", "structure", "technical")):
            high_signal.append((section_name, section_lines))
        elif any(k in name_lower for k in ("sector", "relative", "event", "liquidity")):
            if unknown_count < total_lines * 0.5:
                high_signal.append((section_name, section_lines))
            else:
                medium_signal.append((section_name, section_lines))
        elif any(k in name_lower for k in ("similar", "replay", "guidance", "uncertaint")):
            medium_signal.append((section_name, section_lines))
        elif any(k in name_lower for k in ("fundamental", "broker")):
            if unknown_count > total_lines * 0.7:
                low_signal.append((section_name, section_lines))
            else:
                medium_signal.append((section_name, section_lines))
        else:
            medium_signal.append((section_name, section_lines))

    # Rebuild: HIGH signal first, then MEDIUM, then LOW (or skip low)
    result_lines = []
    for section_name, section_lines in high_signal:
        if section_name != "_header":
            result_lines.append(section_name)
        result_lines.extend(section_lines)

    for section_name, section_lines in medium_signal:
        result_lines.append(section_name)
        result_lines.extend(section_lines)

    # Only include low-signal sections if they have SOME data
    for section_name, section_lines in low_signal:
        text = "\n".join(section_lines)
        if text.lower().count("unknown") < len(section_lines) * 0.8:
            result_lines.append(section_name)
            result_lines.extend(section_lines)

    return "\n".join(result_lines)


def strip_old_system_decision(markdown):
    """Remove the old system's decision/score from context to prevent anchoring.

    Research shows LLMs anchor on prior numbers (Anchoring Bias, 2025).
    We want the LLM to reason independently.
    """
    filtered_lines = []
    skip_section = False

    for line in markdown.split("\n"):
        stripped = line.strip().lower()
        # Skip lines that anchor on the old system's output
        if any(phrase in stripped for phrase in (
            "system summary:",
            "current system decision:",
            "current system confidence:",
            "current setup quality:",
            "recommended task for another llm:",
        )):
            skip_section = True
            continue
        if skip_section:
            if stripped.startswith("-") or stripped.startswith("based on"):
                continue
            skip_section = False
        filtered_lines.append(line)

    return "\n".join(filtered_lines)


def load_calibration(agent_id=None):
    """Load the latest calibration bundle for a specific agent, or the shared bundle.

    Priority:
    1. Agent-specific calibration (latest__{agent_id}__llm_calibration.json) if agent_id given
    2. Shared calibration (latest__llm_calibration.json) as fallback
    3. None if neither exists

    This ensures each agent uses its own historical accuracy data, not whoever
    ran llm_calibrate.py last.
    """
    if agent_id:
        agent_path = os.path.join(CALIBRATION_DIR, f"latest__{agent_id}__llm_calibration.json")
        if os.path.isfile(agent_path):
            return load_json(agent_path)
    if os.path.isfile(LATEST_CALIBRATION_PATH):
        return load_json(LATEST_CALIBRATION_PATH)
    return None


def format_calibration_block(calibration):
    """Format calibration as reference context (NOT as adjustment instructions)."""
    if calibration is None:
        return "No historical accuracy data available yet. First prediction cycle."

    lines = [
        f"Based on {calibration.get('scored_prediction_count', 0)} scored predictions:",
    ]

    overall = calibration.get("overall", {})
    if overall:
        lines.append(f"  Overall accuracy: {overall.get('accuracy_pct', 'N/A')}%")

    by_action = calibration.get("by_action", {})
    if by_action:
        for action, stats in by_action.items():
            count = stats.get("count", 0)
            acc = stats.get("accuracy_pct", "N/A")
            if count > 0:
                lines.append(f"  {action}: {acc}% accuracy (n={count})")

    by_sector = calibration.get("by_sector", {})
    if by_sector:
        for sector, stats in by_sector.items():
            acc = stats.get("accuracy_pct", "N/A")
            count = stats.get("usable", 0)
            if count > 0:
                lines.append(f"  {sector}: {acc}% accuracy (n={count})")

    return "\n".join(lines)


def load_similar_setups_text(symbol, timeframe, run_date):
    """Load similar setups summary, or return placeholder."""
    run_dirs = get_run_directories(symbol, run_date)
    similar_path = os.path.join(
        run_dirs["raw_tables"],
        f"{run_date}__{symbol}__{timeframe}__similar_setups.json",
    )
    if os.path.isfile(similar_path):
        data = load_json(similar_path)
        human = data.get("human_summary", {})
        headline = human.get("headline", "No similar setups found.")
        key_points = human.get("key_points", [])
        summary = data.get("summary", {})

        lines = [headline, ""]
        for point in key_points:
            lines.append(f"- {point}")

        if summary.get("resolved_match_count", 0) > 0:
            lines.append("")
            lines.append(f"Resolved similar setups: {summary['resolved_match_count']}")
            lines.append(f"Success rate: {summary.get('resolved_success_rate_pct', 'N/A')}%")

        top = data.get("top_matches", [])
        if top:
            lines.append("")
            lines.append("Top similar cases:")
            for match in top[:3]:
                sym = match.get("symbol", "?")
                dt = match.get("run_date", "?")
                sim = match.get("similarity_pct", 0)
                outcome = match.get("outcome", {})
                label = outcome.get("outcome_label", "?") if outcome else "?"
                lines.append(f"  - {sym} on {dt}: {sim:.0f}% similar, outcome={label}")

        return "\n".join(lines)

    # Try loading from manual package
    pkg_path = find_manual_package(symbol, timeframe, run_date)
    if pkg_path:
        pkg = load_json(pkg_path)
        similar = pkg.get("similar_setups", {})
        human = similar.get("human_summary", {})
        if human.get("headline"):
            lines = [human["headline"]]
            for pt in human.get("key_points", []):
                lines.append(f"- {pt}")
            return "\n".join(lines)

    return "No similar past setups available for this symbol/date."


def render_prompt(context_markdown, calibration_block, similar_block, macro_block):
    """Fill the prompt template with all injection blocks."""
    if os.path.isfile(PROMPT_TEMPLATE_PATH):
        with open(PROMPT_TEMPLATE_PATH, "r", encoding="utf-8") as f:
            template = f.read()
    else:
        raise FileNotFoundError(f"Prompt template not found: {PROMPT_TEMPLATE_PATH}")

    prompt = template.replace("{{MACRO_CONTEXT_BLOCK}}", macro_block)
    prompt = prompt.replace("{{CONTEXT_PACKAGE}}", context_markdown)
    prompt = prompt.replace("{{SIMILAR_SETUPS_BLOCK}}", similar_block)
    prompt = prompt.replace("{{CALIBRATION_BLOCK}}", calibration_block)
    return prompt


# ---------------------------------------------------------------------------
# Code-side calibration
# ---------------------------------------------------------------------------
def apply_code_calibration(raw_conviction, action, symbol, calibration):
    """Apply mathematical calibration to raw LLM conviction.

    Research (KalshiBench 2025, Self-Improving LLMs 2025) shows that asking
    LLMs to self-calibrate has no effect or amplifies overconfidence.
    Instead, we apply a mapping function based on observed accuracy data.

    Returns (calibrated_conviction, adjustment, reason).
    """
    if calibration is None:
        return raw_conviction, 0, "no calibration data yet"

    sector_map = _load_sector_map()
    sector = sector_map.get(symbol, "UNKNOWN")
    adjustment = 0
    reasons = []

    # 1. Conviction bucket adjustment
    by_bucket = calibration.get("by_conviction_bucket", {})
    for bucket_label, stats in by_bucket.items():
        try:
            low, high = bucket_label.split("-")
            low, high = int(low), int(high)
        except (ValueError, AttributeError):
            continue

        if low <= raw_conviction <= high:
            gap = stats.get("calibration_gap_pct")
            usable = stats.get("usable", 0)
            if gap is not None and usable >= 5 and abs(gap) > 8:
                bucket_adj = round(gap * 0.5)  # Apply half the gap (conservative)
                adjustment += bucket_adj
                reasons.append(f"bucket {bucket_label}: gap={gap:.0f}%, adj={bucket_adj:+d}")
            break

    # 2. Sector adjustment
    by_sector = calibration.get("by_sector", {})
    sector_stats = by_sector.get(sector, {})
    sector_acc = sector_stats.get("accuracy_pct")
    sector_count = sector_stats.get("usable", 0)
    if sector_acc is not None and sector_count >= 5 and sector_acc < 50:
        sector_adj = -round((50 - sector_acc) * 0.5)
        adjustment += sector_adj
        reasons.append(f"sector {sector}: {sector_acc:.0f}% accuracy, adj={sector_adj:+d}")

    # 3. Action-type adjustment
    by_action = calibration.get("by_action", {})
    action_stats = by_action.get(action, {})
    action_acc = action_stats.get("accuracy_pct")
    action_count = action_stats.get("usable", 0)
    if action_acc is not None and action_count >= 5 and action in ("buy", "watch_only") and action_acc < 45:
        action_adj = -round((45 - action_acc) * 0.3)
        adjustment += action_adj
        reasons.append(f"action {action}: {action_acc:.0f}% accuracy, adj={action_adj:+d}")

    calibrated = max(0, min(100, raw_conviction + adjustment))
    reason = "; ".join(reasons) if reasons else "no significant adjustment needed"

    return calibrated, adjustment, reason


# ---------------------------------------------------------------------------
# Prediction storage
# ---------------------------------------------------------------------------
def prediction_path(symbol, timeframe, run_date, mode="live", agent_id=None):
    """Return the storage path for a prediction.

    Includes agent_id in filename to prevent overwrite when both agents
    store predictions for the same symbol/date/timeframe.
    """
    base = PREDICTIONS_LIVE_DIR if mode == "live" else PREDICTIONS_REPLAY_DIR
    agent_tag = f"__{agent_id}" if agent_id and agent_id != "unknown" else ""
    return os.path.join(base, f"{run_date}__{symbol}__{timeframe}{agent_tag}__prediction_v1.json")


def prompt_output_path(symbol, timeframe, run_date):
    """Return the path where the rendered prompt is saved."""
    return os.path.join(PREDICTIONS_LIVE_DIR, f"{run_date}__{symbol}__{timeframe}__prompt.md")


def validate_prediction(prediction):
    """Validate that a prediction has all required fields."""
    required = ["direction", "action", "conviction", "thesis", "risks", "what_would_change_mind"]
    missing = [f for f in required if f not in prediction or prediction[f] is None]
    if missing:
        return False, f"Missing required fields: {', '.join(missing)}"

    if prediction["direction"] not in ("bullish", "bearish", "neutral"):
        return False, f"Invalid direction: {prediction['direction']}"

    if prediction["action"] not in ("buy", "watch_only", "avoid"):
        return False, f"Invalid action: {prediction['action']}"

    conviction = prediction.get("conviction")
    if not isinstance(conviction, (int, float)) or conviction < 0 or conviction > 100:
        return False, f"Invalid conviction: {conviction} (must be 0-100)"

    if not isinstance(prediction.get("risks"), list) or len(prediction["risks"]) < 1:
        return False, "Must include at least one risk"

    if not isinstance(prediction.get("what_would_change_mind"), list) or len(prediction["what_would_change_mind"]) < 1:
        return False, "Must include at least one invalidation condition"

    return True, "ok"


def wrap_prediction(symbol, timeframe, run_date, raw_prediction, calibration_version,
                    mode="interactive", calibration=None, agent_id=None):
    """Wrap a raw LLM prediction in the full schema envelope with code-side calibration."""
    prediction_id = f"llmpred__{run_date}__{symbol}__{timeframe}"
    raw_conviction = raw_prediction.get("conviction", 50)

    # Apply code-side calibration
    calibrated_conviction, adjustment, reason = apply_code_calibration(
        raw_conviction, raw_prediction.get("action", "avoid"), symbol, calibration
    )

    return {
        "schema_version": "2.0",
        "prediction_id": prediction_id,
        "symbol": symbol,
        "run_date": run_date,
        "timeframe": timeframe,
        "captured_at": datetime.now().isoformat(),
        "direction": raw_prediction.get("direction"),
        "action": raw_prediction.get("action"),
        "conviction_raw": raw_conviction,
        "conviction": calibrated_conviction,
        "conviction_rationale": raw_prediction.get("conviction_rationale", ""),
        "price_targets": raw_prediction.get("price_targets", {}),
        "thesis": raw_prediction.get("thesis", ""),
        "risks": raw_prediction.get("risks", []),
        "what_would_change_mind": raw_prediction.get("what_would_change_mind", []),
        "setup_quality": raw_prediction.get("setup_quality", "unknown"),
        "data_completeness": raw_prediction.get("data_completeness", "unknown"),
        "calibration": {
            "raw_conviction": raw_conviction,
            "calibrated_conviction": calibrated_conviction,
            "adjustment": adjustment,
            "reason": reason,
            "calibration_version": calibration_version or "none",
            "method": "code_side_v1",
        },
        "similar_setup_awareness": raw_prediction.get("similar_setup_awareness", {
            "similar_count": 0,
            "similar_resolved_success_rate_pct": None,
            "influence_on_conviction": "no similar setups available",
        }),
        "metadata": {
            "prompt_version": PROMPT_VERSION,
            "calibration_version": calibration_version or "none",
            "context_source": "manual_package",
            "mode": mode,
            "agent_id": agent_id or "unknown",
        },
    }


def store_prediction_file(symbol, timeframe, run_date, prediction_envelope, mode="live"):
    """Save the prediction envelope to disk."""
    agent_id = prediction_envelope.get("metadata", {}).get("agent_id")
    path = prediction_path(symbol, timeframe, run_date, mode, agent_id=agent_id)
    save_json_atomic(path, prediction_envelope)
    return path


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def cmd_interactive(symbol, timeframe, run_date, agent_id=None):
    """Interactive mode: build and render prompt for Claude Code."""
    # Check for manual package
    md_path = find_manual_package_markdown(symbol, timeframe, run_date)
    pkg_path = find_manual_package(symbol, timeframe, run_date)
    pkg = load_json(pkg_path) if pkg_path and os.path.isfile(pkg_path) else {}

    if md_path and os.path.isfile(md_path):
        with open(md_path, "r", encoding="utf-8") as f:
            context_markdown = f.read()
    elif pkg_path:
        context_markdown = json.dumps(pkg, indent=2)
    else:
        print(f"ERROR: No manual package found for {symbol} {timeframe} on {run_date}.")
        print(f"Run first: python manual_llm_package.py {symbol} {timeframe} {run_date}")
        print()
        # Try to find any existing normalized data
        run_dirs = get_run_directories(symbol, run_date)
        existing = []
        for subdir_key in ["normalized_stocks", "normalized_indicators",
                           "normalized_sectors", "normalized_market",
                           "normalized_decisions"]:
            d = run_dirs.get(subdir_key)
            if d and os.path.isdir(d):
                for fname in os.listdir(d):
                    if fname.endswith(".json"):
                        existing.append(os.path.join(d, fname))
        if existing:
            print(f"Found {len(existing)} normalized files. Building minimal context...")
            context_parts = {}
            for fpath in existing:
                data = load_json(fpath)
                basename = os.path.basename(fpath)
                context_parts[basename] = data
            context_markdown = json.dumps(context_parts, indent=2)
        else:
            sys.exit(1)

    # Curate context: reorder for signal quality, remove noise
    context_markdown = strip_old_system_decision(context_markdown)
    context_markdown = curate_context_markdown(context_markdown)

    # Explicit prompt-time injection for new forward enrichments. This keeps the
    # live prompt faithful to the structured package even if markdown curation
    # or older package variants do not surface these sections prominently.
    prompt_enrichment_sections = []
    if pkg and "1.75 Market Breadth / Participation" not in context_markdown:
        market_breadth_lines = build_market_breadth_lines(pkg.get("market_breadth_snapshot") or {})
        if market_breadth_lines:
            prompt_enrichment_sections.extend([
                "1.75 Market Breadth / Participation",
                *market_breadth_lines,
                "",
            ])
    if pkg and "7.5 ShareSansar Event Timing Snapshot" not in context_markdown:
        sharesansar_event_lines = build_sharesansar_event_lines(pkg.get("sharesansar_event_timing") or {})
        if sharesansar_event_lines:
            prompt_enrichment_sections.extend([
                "7.5 ShareSansar Event Timing Snapshot",
                *sharesansar_event_lines,
                "",
            ])
    if prompt_enrichment_sections:
        context_markdown = context_markdown.rstrip() + "\n\n" + "\n".join(prompt_enrichment_sections).rstrip() + "\n"

    manual_context_overlay = load_manual_context_overlay(symbol, run_date, timeframe)
    manual_context_block = format_manual_context_block(
        manual_context_overlay,
        heading="15. Manual Context Overlay (auto-loaded at prompt time)",
    )
    if manual_context_block:
        context_markdown = context_markdown.rstrip() + "\n\n" + manual_context_block + "\n"

    # Build macro context
    macro_block = build_macro_context_block(symbol, run_date)

    # Load calibration (agent-specific if agent_id given)
    calibration = load_calibration(agent_id)
    calibration_version = calibration.get("calibration_id") if calibration else None
    calibration_block = format_calibration_block(calibration)

    # Load similar setups
    similar_block = load_similar_setups_text(symbol, timeframe, run_date)

    # Render prompt
    prompt = render_prompt(context_markdown, calibration_block, similar_block, macro_block)

    # Save prompt
    out_path = prompt_output_path(symbol, timeframe, run_date)
    save_text_atomic(out_path, prompt)

    print(f"Prediction prompt ready for {symbol} {timeframe} ({run_date})")
    print(f"Saved to: {out_path}")
    print()
    print("Next steps:")
    print(f'  1. Ask Claude: "Read {out_path} and produce the prediction JSON"')
    print(f"  2. Save Claude's JSON response to a file (e.g., pred.json)")
    print(f'  3. Store it: python llm_predict.py {symbol} {timeframe} --store pred.json --date {run_date}')
    print()
    print(f"Calibration: {calibration_version or 'none (first run)'}")
    if calibration_version:
        print(f"Code-side calibration will be applied when storing the prediction.")


def cmd_store(symbol, timeframe, run_date, store_path, mode="live", agent_id=None):
    """Store a prediction from a JSON file with code-side calibration."""
    if not os.path.isfile(store_path):
        print(f"ERROR: File not found: {store_path}")
        sys.exit(1)

    with open(store_path, "r", encoding="utf-8") as f:
        raw_text = f.read().strip()

    # Handle markdown code fences
    if raw_text.startswith("```"):
        lines = raw_text.split("\n")
        if lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        raw_text = "\n".join(lines)

    try:
        raw_prediction = json.loads(raw_text)
    except json.JSONDecodeError as e:
        print(f"ERROR: Invalid JSON in {store_path}: {e}")
        sys.exit(1)

    # Validate
    valid, msg = validate_prediction(raw_prediction)
    if not valid:
        print(f"WARNING: Prediction validation: {msg}")
        print("Storing anyway with quality_flag: incomplete")

    # Load calibration (agent-specific if agent_id given)
    calibration = load_calibration(agent_id)
    calibration_version = calibration.get("calibration_id") if calibration else None

    # Wrap with code-side calibration
    envelope = wrap_prediction(
        symbol, timeframe, run_date, raw_prediction,
        calibration_version, calibration=calibration,
        agent_id=agent_id,
    )
    if not valid:
        envelope["quality_flag"] = "incomplete"

    path = store_prediction_file(symbol, timeframe, run_date, envelope, mode=mode)
    print(f"Prediction stored: {path}")
    print(f"  Direction: {envelope['direction']}")
    print(f"  Action: {envelope['action']}")
    print(f"  Raw conviction: {envelope['conviction_raw']}")
    print(f"  Calibrated conviction: {envelope['conviction']}")
    cal = envelope.get("calibration", {})
    print(f"  Calibration: {cal.get('reason', 'none')}")
    print(f"  Thesis: {envelope['thesis'][:80]}...")


def cmd_batch_store(agent_folder, agent_id, mode="replay"):
    """Batch store all prediction JSONs from an agent's predictions folder.

    Parses filenames like: {date}__{symbol}__{tf}__prediction.json
    """
    predictions_folder = Path(agent_folder)
    if not predictions_folder.is_dir():
        # Try relative to BASE_DIR
        predictions_folder = Path(BASE_DIR) / agent_folder
    if not predictions_folder.is_dir():
        print(f"ERROR: Folder not found: {agent_folder}")
        sys.exit(1)

    pred_files = sorted(predictions_folder.glob("*__prediction.json"))
    if not pred_files:
        print(f"No *__prediction.json files found in {predictions_folder}")
        sys.exit(1)

    print(f"Found {len(pred_files)} prediction files in {predictions_folder}")
    print(f"Agent: {agent_id or 'unknown'}, Mode: {mode}")
    print()

    stored = 0
    skipped = 0
    for pred_file in pred_files:
        # Parse: 2025-12-01__EBL__1D__prediction.json
        parts = pred_file.stem.split("__")
        if len(parts) < 3:
            print(f"  SKIP (can't parse filename): {pred_file.name}")
            skipped += 1
            continue
        run_date, symbol, timeframe = parts[0], parts[1], parts[2]
        print(f"  Storing {run_date} {symbol} {timeframe} ...")
        cmd_store(symbol, timeframe, run_date, str(pred_file), mode=mode, agent_id=agent_id)
        stored += 1

    print()
    print(f"Done: {stored} stored, {skipped} skipped")


def main():
    args = sys.argv[1:]

    # Batch store mode: python llm_predict.py --batch-store FOLDER --agent AGENT_ID
    if args and args[0] == "--batch-store":
        if len(args) < 2:
            print("Usage: python llm_predict.py --batch-store FOLDER [--agent AGENT_ID] [--mode live|replay]")
            sys.exit(1)
        batch_folder = args[1]
        agent_id = None
        mode = "replay"
        i = 2
        while i < len(args):
            if args[i] == "--agent" and i + 1 < len(args):
                agent_id = args[i + 1]
                i += 2
            elif args[i] == "--mode" and i + 1 < len(args):
                mode = args[i + 1]
                i += 2
            else:
                i += 1
        cmd_batch_store(batch_folder, agent_id, mode=mode)
        return

    if len(args) < 2:
        print("Usage:")
        print("  python llm_predict.py SYMBOL TIMEFRAME [--date DATE] [--agent AGENT_ID]")
        print("  python llm_predict.py SYMBOL TIMEFRAME --store FILE [--date DATE] [--agent AGENT_ID]")
        print("  python llm_predict.py --batch-store FOLDER [--agent AGENT_ID] [--mode live|replay]")
        sys.exit(1)

    symbol = args[0].upper()
    timeframe = args[1].upper()

    run_date = datetime.now().strftime("%Y-%m-%d")
    store_path = None
    agent_id = None

    i = 2
    while i < len(args):
        if args[i] == "--date" and i + 1 < len(args):
            run_date = args[i + 1]
            i += 2
        elif args[i] == "--store" and i + 1 < len(args):
            store_path = args[i + 1]
            i += 2
        elif args[i] == "--agent" and i + 1 < len(args):
            agent_id = args[i + 1]
            i += 2
        else:
            i += 1

    if store_path:
        cmd_store(symbol, timeframe, run_date, store_path, agent_id=agent_id)
    else:
        cmd_interactive(symbol, timeframe, run_date, agent_id=agent_id)


if __name__ == "__main__":
    main()
