import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  groupBy,
  markdownTable,
  number,
  readCsv,
  stats,
  writeCsv,
} from "./lib/validation_utils.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const INSTANCES_PATH = path.join(DATA_DIR, "pattern_instances.csv");
const CASES_PATH = path.join(RESULTS_DIR, "failed_bearish_cases.csv");
const SUMMARY_PATH = path.join(RESULTS_DIR, "failed_bearish_summary.csv");
const REPORT_PATH = path.join(RESULTS_DIR, "failed_bearish_report.md");

const BEARISH_STATES = new Set(["distribution", "failed_rally", "markdown_continuation", "panic_selling"]);
const HORIZONS = ["1", "3", "5", "10", "20"];

function main() {
  const instances = readCsv(INSTANCES_PATH);
  const cases = instances
    .filter((row) => row.signal_mode === "next_session_confirmation")
    .filter((row) => BEARISH_STATES.has(row.state))
    .filter((row) => row.confirmation_status === "failed")
    .map(caseRow);

  const summaryRows = [
    ...summaryBy(cases, "all", () => "all_failed_bearish"),
    ...summaryBy(cases, "state", (row) => row.state),
    ...summaryBy(cases, "state_evidence", (row) => `${row.state}|${row.evidence_bucket}`),
    ...summaryBy(cases, "quality_bucket", (row) => row.quality_bucket),
    ...summaryBy(cases, "symbol", (row) => row.symbol),
  ].sort(compareSummary);

  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(CASES_PATH, cases);
  writeCsv(SUMMARY_PATH, summaryRows);
  fs.writeFileSync(REPORT_PATH, buildReport(cases, summaryRows), "utf8");

  console.log(`Wrote ${CASES_PATH} (${cases.length} rows)`);
  console.log(`Wrote ${SUMMARY_PATH} (${summaryRows.length} rows)`);
  console.log(`Wrote ${REPORT_PATH}`);
}

function caseRow(row) {
  const output = {
    symbol: row.symbol,
    source_date: row.source_date,
    signal_date: row.signal_date,
    state: row.state,
    score: row.score,
    confidence: row.confidence,
    pattern_family: row.pattern_family,
    score_bucket: row.score_bucket,
    quality_bucket: row.quality_bucket,
    evidence_bucket: row.evidence_bucket,
    invalidation_level: row.invalidation_level,
    positive_evidence: row.positive_evidence,
    negative_evidence: row.negative_evidence,
    quality_flags: row.quality_flags,
  };

  for (const horizon of HORIZONS) {
    output[`outcome_${horizon}d_date`] = row[`outcome_${horizon}d_date`];
    output[`return_${horizon}d_pct`] = row[`actual_${horizon}d_return_pct`];
    output[`excess_peer_${horizon}d_pct`] = row[`actual_${horizon}d_excess_peer_return_pct`];
  }

  return output;
}

function summaryBy(cases, groupType, keyFn) {
  const rows = [];
  for (const [groupKey, group] of groupBy(cases, keyFn).entries()) {
    for (const horizon of HORIZONS) {
      const rawStats = stats(group.map((row) => number(row[`return_${horizon}d_pct`])).filter((value) => value !== null));
      const excessStats = stats(group.map((row) => number(row[`excess_peer_${horizon}d_pct`])).filter((value) => value !== null));
      rows.push({
        group_type: groupType,
        group_key: groupKey,
        horizon_days: horizon,
        n: excessStats.n,
        avg_return_pct: rawStats.avg,
        raw_hit_rate_pct: rawStats.hit_rate_pct,
        avg_excess_peer_return_pct: excessStats.avg,
        peer_hit_rate_pct: excessStats.hit_rate_pct,
        worst_excess_peer_return_pct: excessStats.worst,
        best_excess_peer_return_pct: excessStats.best,
        verdict: verdict(excessStats),
      });
    }
  }
  return rows;
}

function verdict(excessStats) {
  const n = number(excessStats.n) ?? 0;
  const avg = number(excessStats.avg);
  const hit = number(excessStats.hit_rate_pct);
  if (n < 10 || avg === null || hit === null) return "thin";
  if (avg >= 1.5 && hit >= 58) return "strong_reversal_edge";
  if (avg >= 0.5 && hit >= 52) return "watch_reversal_edge";
  if (avg <= -0.5 && hit <= 45) return "failed_bearish_not_enough";
  return "mixed";
}

function compareSummary(left, right) {
  const typeRank = { all: 5, state: 4, state_evidence: 3, quality_bucket: 2, symbol: 1 };
  const byType = (typeRank[right.group_type] ?? 0) - (typeRank[left.group_type] ?? 0);
  if (byType !== 0) return byType;
  const byHorizon = Number(left.horizon_days) - Number(right.horizon_days);
  if (byHorizon !== 0) return byHorizon;
  return (number(right.avg_excess_peer_return_pct) ?? -999) - (number(left.avg_excess_peer_return_pct) ?? -999);
}

function buildReport(cases, summaryRows) {
  const tenDay = summaryRows.filter((row) => row.horizon_days === "10");
  const allRow = tenDay.find((row) => row.group_type === "all");
  const byState = tenDay.filter((row) => row.group_type === "state");
  const byEvidence = tenDay.filter((row) => row.group_type === "state_evidence").slice(0, 12);
  const recentCases = cases.slice().sort((left, right) => String(right.signal_date).localeCompare(String(left.signal_date))).slice(0, 10);

  const summaryHeaders = [
    { key: "group_key", label: "Group" },
    { key: "n", label: "N", align: "---:" },
    { key: "avg_excess_peer_return_pct", label: "Avg vs peer", align: "---:" },
    { key: "peer_hit_rate_pct", label: "Peer hit", align: "---:" },
    { key: "verdict", label: "Verdict" },
  ];
  const caseHeaders = [
    { key: "symbol", label: "Symbol" },
    { key: "source_date", label: "Source" },
    { key: "signal_date", label: "Signal" },
    { key: "state", label: "State" },
    { key: "evidence_bucket", label: "Evidence" },
    { key: "excess_peer_10d_pct", label: "10d vs peer", align: "---:" },
    { key: "invalidation_level", label: "Reclaim/Invalidation" },
  ];

  const lines = [
    "# Experiment 09.5 Failed Bearish Pattern Lab",
    "",
    "Research only. This isolates bearish psychology states that failed on the next session, because those failures can reveal absorption or trapped sellers.",
    "",
    "## Main Read",
    "",
    `- failed bearish cases: ${cases.length}`,
    allRow
      ? `- 10-session all-case result: ${allRow.avg_excess_peer_return_pct}% vs peers, ${allRow.peer_hit_rate_pct}% peer hit, verdict ${allRow.verdict}`
      : "- 10-session all-case result: not enough completed outcomes",
    "",
    "## 10-Session By State",
    "",
    ...markdownTable(byState, summaryHeaders, "No state summary."),
    "",
    "## 10-Session By State + Evidence",
    "",
    ...markdownTable(byEvidence, summaryHeaders, "No evidence summary."),
    "",
    "## Most Recent Cases",
    "",
    ...markdownTable(recentCases, caseHeaders, "No recent cases."),
    "",
    "## How To Use",
    "",
    "- This lab is not saying every distribution day is bullish.",
    "- It is testing the narrower idea: bearish pressure appears, then the next session invalidates it.",
    "- The cleanest future trade rule should come from this family only if entry/exit simulation also confirms it.",
  ];

  return `${lines.join("\n")}\n`;
}

main();
