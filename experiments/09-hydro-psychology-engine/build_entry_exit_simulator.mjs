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

const TRADES_PATH = path.join(RESULTS_DIR, "entry_exit_trades.csv");
const SUMMARY_PATH = path.join(RESULTS_DIR, "entry_exit_summary.csv");
const REPORT_PATH = path.join(RESULTS_DIR, "entry_exit_report.md");

const BEARISH_STATES = new Set(["distribution", "failed_rally", "markdown_continuation", "panic_selling"]);
const HORIZONS = [3, 5, 10, 20];

function main() {
  const dailyRows = readCsv(DAILY_PATH).filter((row) => row.symbol && row.date);
  const instances = readCsv(INSTANCES_PATH);
  const market = buildMarket(dailyRows);

  const tradeRows = [];
  for (const instance of instances) {
    if (instance.signal_mode !== "next_session_confirmation") continue;
    if (!BEARISH_STATES.has(instance.state)) continue;
    if (instance.confirmation_status !== "failed") continue;
    for (const horizon of HORIZONS) {
      const trade = simulateFailedBearishReclaim(instance, horizon, market);
      if (trade) tradeRows.push(trade);
    }
  }

  const summaryRows = buildSummary(tradeRows);

  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(TRADES_PATH, tradeRows);
  writeCsv(SUMMARY_PATH, summaryRows);
  fs.writeFileSync(REPORT_PATH, buildReport(tradeRows, summaryRows), "utf8");

  console.log(`Wrote ${TRADES_PATH} (${tradeRows.length} rows)`);
  console.log(`Wrote ${SUMMARY_PATH} (${summaryRows.length} rows)`);
  console.log(`Wrote ${REPORT_PATH}`);
}

function simulateFailedBearishReclaim(instance, horizon, market) {
  const series = market.bySymbol.get(instance.symbol) ?? [];
  const entryIndex = series.findIndex((row) => row.date === instance.signal_date);
  if (entryIndex < 0) return null;

  const entryRow = series[entryIndex];
  const entryClose = number(entryRow.close);
  const stopLevel = parseFirstNumber(instance.invalidation_level);
  if (entryClose === null || stopLevel === null) return null;

  let exitRow = series[entryIndex + horizon];
  let exitReason = `time_${horizon}d`;

  for (let offset = 1; offset <= horizon; offset += 1) {
    const row = series[entryIndex + offset];
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
    strategy: "failed_bearish_reclaim_long",
    symbol: instance.symbol,
    state: instance.state,
    source_date: instance.source_date,
    entry_date: entryRow.date,
    entry_close: entryClose,
    reclaim_stop_level: stopLevel,
    horizon_days: horizon,
    exit_date: exitRow.date,
    exit_close: exitClose,
    exit_reason: exitReason,
    raw_return_pct: rawReturn.toFixed(4),
    peer_return_pct: peerReturn === null ? "" : peerReturn.toFixed(4),
    excess_peer_return_pct: excessPeer === null ? "" : excessPeer.toFixed(4),
    win: rawReturn > 0 ? "1" : "0",
    peer_win: excessPeer !== null && excessPeer > 0 ? "1" : "0",
    score_bucket: instance.score_bucket,
    quality_bucket: instance.quality_bucket,
    evidence_bucket: instance.evidence_bucket,
    quality_flags: instance.quality_flags,
  };
}

function buildSummary(trades) {
  return [
    ...summaryBy(trades, "all", () => "all_failed_bearish_reclaim"),
    ...summaryBy(trades, "state", (row) => row.state),
    ...summaryBy(trades, "state_evidence", (row) => `${row.state}|${row.evidence_bucket}`),
    ...summaryBy(trades, "quality_bucket", (row) => row.quality_bucket),
    ...summaryBy(trades, "symbol", (row) => row.symbol),
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
  if (avg <= -0.5 && hit <= 45) return "bad_trade_rule";
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

function compareSummary(left, right) {
  const typeRank = { all: 5, state: 4, state_evidence: 3, quality_bucket: 2, symbol: 1 };
  const byType = (typeRank[right.group_type] ?? 0) - (typeRank[left.group_type] ?? 0);
  if (byType !== 0) return byType;
  const byHorizon = Number(left.horizon_days) - Number(right.horizon_days);
  if (byHorizon !== 0) return byHorizon;
  return (number(right.avg_excess_peer_return_pct) ?? -999) - (number(left.avg_excess_peer_return_pct) ?? -999);
}

function buildReport(trades, summaryRows) {
  const tenDay = summaryRows.filter((row) => Number(row.horizon_days) === 10);
  const allRow = tenDay.find((row) => row.group_type === "all");
  const byState = tenDay.filter((row) => row.group_type === "state");
  const byEvidence = tenDay.filter((row) => row.group_type === "state_evidence").slice(0, 12);

  const headers = [
    { key: "group_key", label: "Group" },
    { key: "n", label: "N", align: "---:" },
    { key: "avg_return_pct", label: "Avg raw", align: "---:" },
    { key: "avg_excess_peer_return_pct", label: "Avg vs peer", align: "---:" },
    { key: "peer_win_rate_pct", label: "Peer win", align: "---:" },
    { key: "stopped_pct", label: "Stopped", align: "---:" },
    { key: "verdict", label: "Verdict" },
  ];

  const lines = [
    "# Experiment 09.4 Entry/Exit Simulator",
    "",
    "Research only. This first simulator tests one concrete rule: buy only after a bearish psychology read fails by reclaiming its level, then exit by time or by a close back below the reclaim level.",
    "",
    "## Rule",
    "",
    "```text",
    "candidate: bearish state + next_session_confirmation = failed",
    "entry: confirmation day close",
    "stop: later close below the reclaimed level from the prior bearish state's invalidation text",
    "exit: stop or 3/5/10/20-session time exit",
    "benchmark: same-date hydro peers",
    "```",
    "",
    "## Main Read",
    "",
    `- simulated trade rows: ${trades.length}`,
    allRow
      ? `- 10-session rule result: ${allRow.avg_excess_peer_return_pct}% vs peers, ${allRow.peer_win_rate_pct}% peer win, ${allRow.stopped_pct}% stopped, verdict ${allRow.verdict}`
      : "- 10-session rule result: not enough completed trades",
    "",
    "## 10-Session By State",
    "",
    ...markdownTable(byState, headers, "No state rows."),
    "",
    "## 10-Session By State + Evidence",
    "",
    ...markdownTable(byEvidence, headers, "No evidence rows."),
    "",
    "## How To Use",
    "",
    "- This is the first trade-rule layer, not a final trading system.",
    "- If this rule beats the failed-bearish lab, the entry/stop adds value.",
    "- If it does not, the psychology is interesting but the execution rule needs redesign.",
  ];

  return `${lines.join("\n")}\n`;
}

main();
