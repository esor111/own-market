import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  format,
  groupBy,
  key,
  markdownTable,
  number,
  periodBucket,
  readCsv,
  stats,
  writeCsv,
} from "./lib/validation_utils.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const INSTANCES_PATH = path.join(DATA_DIR, "pattern_instances.csv");
const ROBUSTNESS_PATH = path.join(RESULTS_DIR, "pattern_robustness.csv");

const TRADES_PATH = path.join(RESULTS_DIR, "robust_pattern_trades.csv");
const SUMMARY_PATH = path.join(RESULTS_DIR, "robust_pattern_trade_summary.csv");
const LATEST_PATH = path.join(RESULTS_DIR, "latest_robust_pattern_watchlist.csv");
const REPORT_PATH = path.join(RESULTS_DIR, "robust_pattern_trade_report.md");

const ROBUST_GRADES = new Set(["robust_positive", "robust_negative"]);
const PRIMARY_HORIZON = "10";

function main() {
  const instances = readCsv(INSTANCES_PATH);
  const robustPatterns = readCsv(ROBUSTNESS_PATH)
    .filter((row) => ROBUST_GRADES.has(row.robustness_grade))
    .filter((row) => row.history_level !== "global");

  const trades = buildTrades(instances, robustPatterns);
  const summaryRows = buildSummary(trades);
  const latestWatchlist = buildLatestWatchlist(instances, robustPatterns);

  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(TRADES_PATH, trades);
  writeCsv(SUMMARY_PATH, summaryRows);
  writeCsv(LATEST_PATH, latestWatchlist);
  fs.writeFileSync(REPORT_PATH, buildReport(robustPatterns, trades, summaryRows, latestWatchlist), "utf8");

  console.log(`Wrote ${TRADES_PATH} (${trades.length} rows)`);
  console.log(`Wrote ${SUMMARY_PATH} (${summaryRows.length} rows)`);
  console.log(`Wrote ${LATEST_PATH} (${latestWatchlist.length} rows)`);
  console.log(`Wrote ${REPORT_PATH}`);
}

function buildTrades(instances, robustPatterns) {
  const rows = [];
  for (const pattern of robustPatterns) {
    const horizon = String(pattern.horizon_days);
    const decision = decisionFor(pattern);
    for (const instance of instances) {
      if (!matchesPattern(instance, pattern)) continue;
      const raw = number(instance[`actual_${horizon}d_return_pct`]);
      const excess = number(instance[`actual_${horizon}d_excess_peer_return_pct`]);
      if (raw === null || excess === null) continue;

      const decisionEdge = decision === "long" ? excess : -excess;
      rows.push({
        decision,
        decision_label: decision === "long" ? "long robust outperform pattern" : "avoid robust underperform pattern",
        robustness_grade: pattern.robustness_grade,
        signal_mode: pattern.signal_mode,
        history_level: pattern.history_level,
        history_key: pattern.history_key,
        horizon_days: horizon,
        pattern_n: pattern.n,
        pattern_avg_excess_peer_return_pct: pattern.avg_excess_peer_return_pct,
        pattern_peer_hit_rate_pct: pattern.peer_hit_rate_pct,
        period_direction_consistency_pct: pattern.period_direction_consistency_pct,
        symbol_direction_consistency_pct: pattern.symbol_direction_consistency_pct,
        symbol: instance.symbol,
        source_date: instance.source_date,
        signal_date: instance.signal_date,
        period: periodBucket(instance.signal_date),
        state: instance.state,
        confirmation_status: instance.confirmation_status,
        score_bucket: instance.score_bucket,
        quality_bucket: instance.quality_bucket,
        evidence_bucket: instance.evidence_bucket,
        actual_return_pct: raw.toFixed(4),
        actual_excess_peer_return_pct: excess.toFixed(4),
        decision_edge_pct: decisionEdge.toFixed(4),
        hit: decisionEdge > 0 ? "1" : "0",
        invalidation_level: instance.invalidation_level,
        quality_flags: instance.quality_flags,
      });
    }
  }
  return rows.sort(compareTrades);
}

function buildSummary(trades) {
  return [
    ...summaryBy(trades, "decision_horizon", (row) => `${row.decision}|${row.horizon_days}`),
    ...summaryBy(trades, "grade_horizon", (row) => `${row.robustness_grade}|${row.horizon_days}`),
    ...summaryBy(trades, "mode_horizon", (row) => `${row.signal_mode}|${row.horizon_days}`),
    ...summaryBy(trades, "state_horizon", (row) => `${row.state}|${row.horizon_days}`),
    ...summaryBy(trades, "pattern_horizon", (row) => `${row.history_key}|${row.horizon_days}`),
  ].sort(compareSummary);
}

function summaryBy(trades, groupType, keyFn) {
  const rows = [];
  for (const [groupKey, group] of groupBy(trades, keyFn).entries()) {
    const edgeStats = stats(group.map((row) => number(row.decision_edge_pct)).filter((value) => value !== null));
    const rawStats = stats(group.map((row) => number(row.actual_return_pct)).filter((value) => value !== null));
    const excessStats = stats(group.map((row) => number(row.actual_excess_peer_return_pct)).filter((value) => value !== null));
    const [mainKey, horizonDays = "mixed"] = groupKey.split(/\|(?!.*\|)/);
    rows.push({
      group_type: groupType,
      group_key: mainKey,
      horizon_days: horizonDays,
      n: group.length,
      avg_decision_edge_pct: edgeStats.avg,
      decision_hit_rate_pct: edgeStats.hit_rate_pct,
      avg_actual_return_pct: rawStats.avg,
      avg_actual_excess_peer_return_pct: excessStats.avg,
      peer_hit_rate_pct: excessStats.hit_rate_pct,
      verdict: verdict(group.length, edgeStats),
    });
  }
  return rows;
}

function buildLatestWatchlist(instances, robustPatterns) {
  const latestDate = instances.reduce((latest, row) => row.signal_date > latest ? row.signal_date : latest, "");
  const latest = instances.filter((row) => row.signal_date === latestDate);
  const rowsByKey = new Map();

  for (const pattern of robustPatterns) {
    for (const instance of latest) {
      if (!matchesPattern(instance, pattern)) continue;
      const decision = decisionFor(pattern);
      const row = {
        symbol: instance.symbol,
        signal_date: instance.signal_date,
        decision,
        robustness_grade: pattern.robustness_grade,
        horizon_days: pattern.horizon_days,
        expected_excess_peer_return_pct: pattern.avg_excess_peer_return_pct,
        historical_peer_hit_rate_pct: pattern.peer_hit_rate_pct,
        pattern_n: pattern.n,
        period_direction_consistency_pct: pattern.period_direction_consistency_pct,
        symbol_direction_consistency_pct: pattern.symbol_direction_consistency_pct,
        state: instance.state,
        confirmation_status: instance.confirmation_status,
        signal_mode: instance.signal_mode,
        history_level: pattern.history_level,
        history_key: pattern.history_key,
        invalidation_level: instance.invalidation_level,
        watch_read: decision === "long"
          ? "robust historical outperform pattern; still require risk control"
          : "robust historical underperform pattern; avoid unless pattern fails",
        quality_flags: instance.quality_flags,
      };
      const rowKey = key(row.symbol, row.decision, row.horizon_days);
      const previous = rowsByKey.get(rowKey);
      if (!previous || watchStrength(row) > watchStrength(previous)) rowsByKey.set(rowKey, row);
    }
  }

  return [...rowsByKey.values()].sort((left, right) => {
    const byDecision = String(left.decision).localeCompare(String(right.decision));
    if (byDecision !== 0) return byDecision;
    return (number(right.expected_excess_peer_return_pct) ?? 0) - (number(left.expected_excess_peer_return_pct) ?? 0);
  });
}

function watchStrength(row) {
  const expected = number(row.expected_excess_peer_return_pct) ?? 0;
  const directionalExpected = row.decision === "avoid" ? -expected : expected;
  const hit = number(row.historical_peer_hit_rate_pct) ?? 0;
  const n = number(row.pattern_n) ?? 0;
  return directionalExpected * 10000 + hit * 10 + Math.min(n, 999);
}

function matchesPattern(instance, pattern) {
  if (instance.signal_mode !== pattern.signal_mode) return false;
  if (pattern.history_level === "specific") return instance.specific_history_key === pattern.history_key;
  if (pattern.history_level === "state") return instance.state_history_key === pattern.history_key;
  if (pattern.history_level === "family") return instance.family_history_key === pattern.history_key;
  return instance.global_history_key === pattern.history_key;
}

function decisionFor(pattern) {
  return pattern.robustness_grade === "robust_positive" ? "long" : "avoid";
}

function verdict(n, edgeStats) {
  const avg = number(edgeStats.avg);
  const hit = number(edgeStats.hit_rate_pct);
  if (n < 20 || avg === null || hit === null) return "thin";
  if (avg >= 1 && hit >= 58) return "strong_candidate";
  if (avg >= 0.35 && hit >= 52) return "watch_candidate";
  if (avg <= -0.35 && hit <= 48) return "bad_after_trade_test";
  return "mixed";
}

function compareTrades(left, right) {
  const byDate = String(left.signal_date).localeCompare(String(right.signal_date));
  if (byDate !== 0) return byDate;
  const bySymbol = String(left.symbol).localeCompare(String(right.symbol));
  if (bySymbol !== 0) return bySymbol;
  return Number(left.horizon_days) - Number(right.horizon_days);
}

function compareSummary(left, right) {
  const typeRank = {
    decision_horizon: 5,
    grade_horizon: 4,
    mode_horizon: 3,
    state_horizon: 2,
    pattern_horizon: 1,
  };
  const byType = (typeRank[right.group_type] ?? 0) - (typeRank[left.group_type] ?? 0);
  if (byType !== 0) return byType;
  const byHorizon = Number(left.horizon_days) - Number(right.horizon_days);
  if (byHorizon !== 0) return byHorizon;
  return (number(right.avg_decision_edge_pct) ?? -999) - (number(left.avg_decision_edge_pct) ?? -999);
}

function buildReport(robustPatterns, trades, summaryRows, latestWatchlist) {
  const primaryRows = summaryRows
    .filter((row) => row.group_type === "decision_horizon" && row.horizon_days === PRIMARY_HORIZON)
    .sort((left, right) => (number(right.avg_decision_edge_pct) ?? -999) - (number(left.avg_decision_edge_pct) ?? -999));
  const topPatterns = summaryRows
    .filter((row) => row.group_type === "pattern_horizon" && row.horizon_days === PRIMARY_HORIZON)
    .sort((left, right) => (number(right.avg_decision_edge_pct) ?? -999) - (number(left.avg_decision_edge_pct) ?? -999))
    .slice(0, 12);
  const stateRows = summaryRows
    .filter((row) => row.group_type === "state_horizon" && row.horizon_days === PRIMARY_HORIZON)
    .sort((left, right) => (number(right.avg_decision_edge_pct) ?? -999) - (number(left.avg_decision_edge_pct) ?? -999));
  const latestPrimary = latestWatchlist
    .filter((row) => String(row.horizon_days) === PRIMARY_HORIZON)
    .slice(0, 16);

  const summaryHeaders = [
    { key: "group_key", label: "Group" },
    { key: "n", label: "N", align: "---:" },
    { key: "avg_decision_edge_pct", label: "Decision edge", align: "---:" },
    { key: "decision_hit_rate_pct", label: "Hit", align: "---:" },
    { key: "avg_actual_excess_peer_return_pct", label: "Actual vs peer", align: "---:" },
    { key: "verdict", label: "Verdict" },
  ];
  const latestHeaders = [
    { key: "symbol", label: "Symbol" },
    { key: "decision", label: "Decision" },
    { key: "horizon_days", label: "H", align: "---:" },
    { key: "expected_excess_peer_return_pct", label: "Expected vs peer", align: "---:" },
    { key: "historical_peer_hit_rate_pct", label: "Hit hist", align: "---:" },
    { key: "state", label: "State" },
    { key: "watch_read", label: "Read" },
  ];

  const robustPositive = robustPatterns.filter((row) => row.robustness_grade === "robust_positive").length;
  const robustNegative = robustPatterns.filter((row) => row.robustness_grade === "robust_negative").length;

  const lines = [
    "# Experiment 09.7 Robust Pattern Trade Lab",
    "",
    "Research only. This lab ignores weak and unstable patterns, then tests whether robust patterns can be used as long or avoid decisions.",
    "",
    "## What Was Tested",
    "",
    `- robust positive patterns: ${robustPositive}`,
    `- robust negative patterns: ${robustNegative}`,
    `- robust pattern decision rows: ${trades.length}`,
    `- latest robust watchlist rows: ${latestWatchlist.length}`,
    "",
    "## 10-Session Decision Summary",
    "",
    ...markdownTable(primaryRows, summaryHeaders, "No 10-session decision rows."),
    "",
    "## 10-Session By State",
    "",
    ...markdownTable(stateRows, summaryHeaders, "No state rows."),
    "",
    "## Top 10-Session Robust Patterns After Trade Test",
    "",
    ...markdownTable(topPatterns, summaryHeaders, "No robust pattern rows."),
    "",
    "## Latest Robust Watchlist",
    "",
    ...markdownTable(latestPrimary, latestHeaders, "No latest robust rows."),
    "",
    "## Interpretation",
    "",
    "- `long` means the robust pattern historically outperformed peers.",
    "- `avoid` means the robust pattern historically underperformed peers; the edge is avoiding that relative weakness.",
    "- This is not yet position sizing. It is the bridge between robust psychology and a practical watchlist.",
  ];

  return `${lines.join("\n")}\n`;
}

main();
