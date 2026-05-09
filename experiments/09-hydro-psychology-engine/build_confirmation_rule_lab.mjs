import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  average,
  groupBy,
  key,
  markdownTable,
  number,
  parseFirstNumber,
  pct,
  readCsv,
  stats,
  writeCsv,
} from "./lib/validation_utils.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const DAILY_PATH = path.join(DATA_DIR, "hydro_psychology_daily.csv");
const INSTANCES_PATH = path.join(DATA_DIR, "pattern_instances.csv");

const TRADES_PATH = path.join(RESULTS_DIR, "confirmation_rule_trades.csv");
const SUMMARY_PATH = path.join(RESULTS_DIR, "confirmation_rule_summary.csv");
const REPORT_PATH = path.join(RESULTS_DIR, "confirmation_rule_report.md");

const BEARISH_STATES = new Set(["distribution", "failed_rally", "markdown_continuation", "panic_selling"]);
const HORIZONS = [3, 5, 10, 20];
const RULES = [
  {
    name: "baseline_reclaim_close",
    description: "Enter on the confirmation-day close after bearish pressure fails.",
    entry: (ctx) => entryAt(ctx.signalIndex, "confirmation close"),
  },
  {
    name: "hold_reclaim_1d",
    description: "Wait one more session; enter only if close still holds the reclaimed level.",
    entry: (ctx) => closeHeldFor(ctx, 1),
  },
  {
    name: "hold_reclaim_2d",
    description: "Wait two sessions; enter only if both closes hold the reclaimed level.",
    entry: (ctx) => closeHeldFor(ctx, 2),
  },
  {
    name: "same_day_peer_strength",
    description: "Enter only if confirmation day also beats same-day hydro peers.",
    entry: (ctx) => peerStrength(ctx.signalRow, ctx.market, ctx.instance.symbol) > 0 ? entryAt(ctx.signalIndex, "confirmation day beat peers") : null,
  },
  {
    name: "strong_close_position",
    description: "Enter only if confirmation day closes in the upper 65% of its range.",
    entry: (ctx) => (number(ctx.signalRow.close_position) ?? -1) >= 0.65 ? entryAt(ctx.signalIndex, "strong close position") : null,
  },
  {
    name: "volume_confirmed_reclaim",
    description: "Enter only if confirmation day volume is at or above its 20-day average.",
    entry: (ctx) => (number(ctx.signalRow.volume_ratio_20d) ?? -1) >= 1 ? entryAt(ctx.signalIndex, "volume ratio >= 1") : null,
  },
  {
    name: "clean_no_event_window",
    description: "Enter only if the source setup is not event-window distorted.",
    entry: (ctx) => hasEventRisk(ctx.instance) ? null : entryAt(ctx.signalIndex, "no event risk flags"),
  },
  {
    name: "buyer_persistence_support",
    description: "Enter only if the setup evidence includes buyer broker persistence.",
    entry: (ctx) => hasText(ctx.instance.positive_evidence, "buyer broker persistence") ? entryAt(ctx.signalIndex, "buyer broker persistence") : null,
  },
  {
    name: "hold_1d_plus_peer_strength",
    description: "Wait one session; enter only if the hold day also beats hydro peers.",
    entry: (ctx) => {
      const held = closeHeldFor(ctx, 1);
      if (!held) return null;
      const row = ctx.series[held.entryIndex];
      return peerStrength(row, ctx.market, ctx.instance.symbol) > 0
        ? { ...held, entry_reason: "held reclaim 1d and beat peers" }
        : null;
    },
  },
  {
    name: "hold_1d_plus_strong_close",
    description: "Wait one session; enter only if the hold day closes strong.",
    entry: (ctx) => {
      const held = closeHeldFor(ctx, 1);
      if (!held) return null;
      const row = ctx.series[held.entryIndex];
      return (number(row.close_position) ?? -1) >= 0.65
        ? { ...held, entry_reason: "held reclaim 1d with strong close" }
        : null;
    },
  },
  {
    name: "strict_clean_hold_peer",
    description: "Wait one session, avoid event risk, require peer strength.",
    entry: (ctx) => {
      if (hasEventRisk(ctx.instance)) return null;
      const held = closeHeldFor(ctx, 1);
      if (!held) return null;
      const row = ctx.series[held.entryIndex];
      return peerStrength(row, ctx.market, ctx.instance.symbol) > 0
        ? { ...held, entry_reason: "clean held reclaim 1d and beat peers" }
        : null;
    },
  },
];

function main() {
  const dailyRows = readCsv(DAILY_PATH).filter((row) => row.symbol && row.date);
  const instances = readCsv(INSTANCES_PATH);
  const market = buildMarket(dailyRows);

  const candidates = instances
    .filter((row) => row.signal_mode === "next_session_confirmation")
    .filter((row) => row.confirmation_status === "failed")
    .filter((row) => BEARISH_STATES.has(row.state));

  const trades = [];
  for (const instance of candidates) {
    for (const rule of RULES) {
      for (const horizon of HORIZONS) {
        const trade = simulateRule(instance, rule, horizon, market);
        if (trade) trades.push(trade);
      }
    }
  }

  const summaryRows = buildSummary(trades);

  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(TRADES_PATH, trades);
  writeCsv(SUMMARY_PATH, summaryRows);
  fs.writeFileSync(REPORT_PATH, buildReport(candidates, trades, summaryRows), "utf8");

  console.log(`Wrote ${TRADES_PATH} (${trades.length} rows)`);
  console.log(`Wrote ${SUMMARY_PATH} (${summaryRows.length} rows)`);
  console.log(`Wrote ${REPORT_PATH}`);
}

function simulateRule(instance, rule, horizon, market) {
  const series = market.bySymbol.get(instance.symbol) ?? [];
  const signalIndex = series.findIndex((row) => row.date === instance.signal_date);
  if (signalIndex < 0) return null;

  const stopLevel = parseFirstNumber(instance.invalidation_level);
  if (stopLevel === null) return null;

  const ctx = {
    instance,
    rule,
    horizon,
    market,
    series,
    signalIndex,
    signalRow: series[signalIndex],
    stopLevel,
  };

  const entry = rule.entry(ctx);
  if (!entry) return null;

  const entryRow = series[entry.entryIndex];
  const entryClose = number(entryRow?.close);
  if (!entryRow || entryClose === null) return null;

  let exitRow = series[entry.entryIndex + horizon];
  let exitReason = `time_${horizon}d`;

  for (let offset = 1; offset <= horizon; offset += 1) {
    const row = series[entry.entryIndex + offset];
    if (!row) break;
    const close = number(row.close);
    if (close !== null && close < stopLevel) {
      exitRow = row;
      exitReason = "stop_close_below_reclaim";
      break;
    }
  }

  if (!exitRow) return null;
  const exitClose = number(exitRow.close);
  if (exitClose === null) return null;

  const rawReturn = (exitClose - entryClose) / entryClose * 100;
  const peerReturn = peerReturnPct(market, instance.symbol, entryRow.date, exitRow.date);
  const excessPeer = peerReturn === null ? null : rawReturn - peerReturn;

  return {
    rule: rule.name,
    rule_description: rule.description,
    symbol: instance.symbol,
    state: instance.state,
    source_date: instance.source_date,
    signal_date: instance.signal_date,
    entry_date: entryRow.date,
    entry_reason: entry.entry_reason,
    entry_close: entryClose,
    reclaim_stop_level: stopLevel,
    horizon_days: horizon,
    exit_date: exitRow.date,
    exit_close: exitClose,
    exit_reason: exitReason,
    raw_return_pct: rawReturn.toFixed(4),
    peer_return_pct: peerReturn === null ? "" : peerReturn.toFixed(4),
    excess_peer_return_pct: excessPeer === null ? "" : excessPeer.toFixed(4),
    peer_win: excessPeer !== null && excessPeer > 0 ? "1" : "0",
    signal_peer_strength_pct: formatNullable(peerStrength(ctx.signalRow, market, instance.symbol)),
    entry_peer_strength_pct: formatNullable(peerStrength(entryRow, market, instance.symbol)),
    entry_close_position: entryRow.close_position ?? "",
    entry_volume_ratio_20d: entryRow.volume_ratio_20d ?? "",
    score_bucket: instance.score_bucket,
    quality_bucket: instance.quality_bucket,
    evidence_bucket: instance.evidence_bucket,
    quality_flags: instance.quality_flags,
  };
}

function entryAt(entryIndex, entryReason) {
  return { entryIndex, entry_reason: entryReason };
}

function closeHeldFor(ctx, sessions) {
  for (let offset = 1; offset <= sessions; offset += 1) {
    const row = ctx.series[ctx.signalIndex + offset];
    const close = number(row?.close);
    if (!row || close === null || close < ctx.stopLevel) return null;
  }
  return entryAt(ctx.signalIndex + sessions, `held reclaim for ${sessions} session${sessions === 1 ? "" : "s"}`);
}

function buildSummary(trades) {
  return [
    ...summaryBy(trades, "rule", (row) => row.rule),
    ...summaryBy(trades, "rule_state", (row) => `${row.rule}|${row.state}`),
    ...summaryBy(trades, "rule_evidence", (row) => `${row.rule}|${row.evidence_bucket}`),
    ...summaryBy(trades, "rule_quality", (row) => `${row.rule}|${row.quality_bucket}`),
  ].sort(compareSummary);
}

function summaryBy(trades, groupType, keyFn) {
  const rows = [];
  for (const [groupKey, group] of groupBy(trades, keyFn).entries()) {
    for (const horizon of HORIZONS) {
      const scoped = group.filter((row) => Number(row.horizon_days) === horizon);
      const raw = stats(scoped.map((row) => number(row.raw_return_pct)).filter((value) => value !== null));
      const excess = stats(scoped.map((row) => number(row.excess_peer_return_pct)).filter((value) => value !== null));
      rows.push({
        group_type: groupType,
        group_key: groupKey,
        horizon_days: horizon,
        n: scoped.length,
        avg_return_pct: raw.avg,
        raw_win_rate_pct: raw.hit_rate_pct,
        avg_excess_peer_return_pct: excess.avg,
        peer_win_rate_pct: excess.hit_rate_pct,
        stopped_pct: pct(scoped.filter((row) => row.exit_reason === "stop_close_below_reclaim").length, scoped.length),
        verdict: verdict(scoped.length, excess),
      });
    }
  }
  return rows;
}

function verdict(n, excess) {
  const avg = number(excess.avg);
  const hit = number(excess.hit_rate_pct);
  if (n < 10 || avg === null || hit === null) return "thin";
  if (avg >= 1.0 && hit >= 55) return "tradable_candidate";
  if (avg >= 0.35 && hit >= 52) return "watch_candidate";
  if (avg <= -0.5 && hit <= 45) return "bad_rule";
  return "mixed";
}

function buildMarket(rows) {
  const bySymbol = new Map();
  const byKey = new Map();
  for (const [symbol, group] of groupBy(rows, (row) => row.symbol).entries()) {
    const ordered = group.slice().sort((left, right) => String(left.date).localeCompare(String(right.date)));
    bySymbol.set(symbol, ordered);
    for (const row of ordered) byKey.set(key(symbol, row.date), row);
  }
  return { bySymbol, byKey, symbols: [...bySymbol.keys()] };
}

function peerReturnPct(market, symbol, startDate, endDate) {
  const values = [];
  for (const peer of market.symbols) {
    if (peer === symbol) continue;
    const start = market.byKey.get(key(peer, startDate));
    const end = market.byKey.get(key(peer, endDate));
    const startClose = number(start?.close);
    const endClose = number(end?.close);
    if (startClose === null || startClose === 0 || endClose === null) continue;
    values.push((endClose - startClose) / startClose * 100);
  }
  return average(values);
}

function peerStrength(row, market, symbol) {
  if (!row) return null;
  const ownReturn = number(row.return_pct);
  if (ownReturn === null) return null;

  const peers = [];
  for (const peer of market.symbols) {
    if (peer === symbol) continue;
    const peerRow = market.byKey.get(key(peer, row.date));
    const value = number(peerRow?.return_pct);
    if (value !== null) peers.push(value);
  }
  const peerAvg = average(peers);
  return peerAvg === null ? null : ownReturn - peerAvg;
}

function hasEventRisk(instance) {
  const flags = String(instance.quality_flags ?? "");
  return ["event_window", "lockin_window", "nrb_event_window", "flood_damage_window"].some((flag) => flags.includes(flag));
}

function hasText(value, needle) {
  return String(value ?? "").toLowerCase().includes(needle.toLowerCase());
}

function formatNullable(value) {
  const parsed = number(value);
  return parsed === null ? "" : parsed.toFixed(4);
}

function compareSummary(left, right) {
  const typeRank = { rule: 4, rule_state: 3, rule_evidence: 2, rule_quality: 1 };
  const byType = (typeRank[right.group_type] ?? 0) - (typeRank[left.group_type] ?? 0);
  if (byType !== 0) return byType;
  const byHorizon = Number(left.horizon_days) - Number(right.horizon_days);
  if (byHorizon !== 0) return byHorizon;
  return (number(right.avg_excess_peer_return_pct) ?? -999) - (number(left.avg_excess_peer_return_pct) ?? -999);
}

function buildReport(candidates, trades, summaryRows) {
  const tenDayRuleRows = summaryRows
    .filter((row) => row.group_type === "rule" && Number(row.horizon_days) === 10)
    .sort((left, right) => (number(right.avg_excess_peer_return_pct) ?? -999) - (number(left.avg_excess_peer_return_pct) ?? -999));
  const fiveDayRuleRows = summaryRows
    .filter((row) => row.group_type === "rule" && Number(row.horizon_days) === 5)
    .sort((left, right) => (number(right.avg_excess_peer_return_pct) ?? -999) - (number(left.avg_excess_peer_return_pct) ?? -999));
  const ruleStateRows = summaryRows
    .filter((row) => row.group_type === "rule_state" && Number(row.horizon_days) === 10)
    .sort((left, right) => (number(right.avg_excess_peer_return_pct) ?? -999) - (number(left.avg_excess_peer_return_pct) ?? -999))
    .slice(0, 12);

  const headers = [
    { key: "group_key", label: "Rule" },
    { key: "n", label: "N", align: "---:" },
    { key: "avg_return_pct", label: "Avg raw", align: "---:" },
    { key: "avg_excess_peer_return_pct", label: "Avg vs peer", align: "---:" },
    { key: "peer_win_rate_pct", label: "Peer win", align: "---:" },
    { key: "stopped_pct", label: "Stopped", align: "---:" },
    { key: "verdict", label: "Verdict" },
  ];

  const lines = [
    "# Experiment 09.6 Confirmation Rule Lab",
    "",
    "Research only. This tests stricter confirmations after a failed bearish psychology setup. The point is to learn what must happen after the label before the setup becomes worth trading.",
    "",
    "## What Was Tested",
    "",
    `- failed bearish setup candidates: ${candidates.length}`,
    `- simulated confirmation-rule trades: ${trades.length}`,
    "- benchmark: same-date hydropower peer return",
    "- stop: close back below the reclaimed level",
    "",
    "## 10-Session Rule Ranking",
    "",
    ...markdownTable(tenDayRuleRows, headers, "No 10-session rule rows."),
    "",
    "## 5-Session Rule Ranking",
    "",
    ...markdownTable(fiveDayRuleRows, headers, "No 5-session rule rows."),
    "",
    "## Best 10-Session Rule + State Combos",
    "",
    ...markdownTable(ruleStateRows, headers, "No rule/state rows."),
    "",
    "## Interpretation",
    "",
    "- If a stricter rule still has negative peer-relative returns, the psychology idea is not enough.",
    "- If waiting for a hold improves peer-relative return, confirmation is adding value.",
    "- If filters only work with tiny N, treat them as ideas, not evidence.",
  ];

  return `${lines.join("\n")}\n`;
}

main();
