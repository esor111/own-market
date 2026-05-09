import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  average,
  format,
  groupBy,
  markdownTable,
  number,
  pct,
  periodBucket,
  readCsv,
  stats,
  writeCsv,
} from "./lib/validation_utils.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const INSTANCES_PATH = path.join(DATA_DIR, "pattern_instances.csv");
const EDGE_PATH = path.join(RESULTS_DIR, "pattern_edge_report.csv");

const OUTPUT_PATH = path.join(RESULTS_DIR, "pattern_robustness.csv");
const REPORT_PATH = path.join(RESULTS_DIR, "pattern_robustness_report.md");

const MIN_TOTAL_N = 20;
const MIN_SLICE_N = 5;
const PRIMARY_HORIZON = "10";

function main() {
  const instances = readCsv(INSTANCES_PATH);
  const edgeRows = readCsv(EDGE_PATH)
    .filter((row) => (number(row.n) ?? 0) >= MIN_TOTAL_N)
    .filter((row) => row.history_level !== "global");

  const robustnessRows = edgeRows.map((edge) => robustnessFor(edge, instances)).sort(compareRows);

  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(OUTPUT_PATH, robustnessRows);
  fs.writeFileSync(REPORT_PATH, buildReport(robustnessRows), "utf8");

  console.log(`Wrote ${OUTPUT_PATH} (${robustnessRows.length} rows)`);
  console.log(`Wrote ${REPORT_PATH}`);
}

function robustnessFor(edge, instances) {
  const horizon = String(edge.horizon_days);
  const matching = instances.filter((instance) => matchesEdge(instance, edge));
  const values = matching.map((row) => number(row[`actual_${horizon}d_excess_peer_return_pct`])).filter((value) => value !== null);
  const totalAvg = number(edge.avg_excess_peer_return_pct) ?? average(values) ?? 0;
  const totalDirection = totalAvg >= 0 ? "positive" : "negative";
  const periodSlices = sliceStats(matching, horizon, (row) => periodBucket(row.signal_date), totalDirection);
  const symbolSlices = sliceStats(matching, horizon, (row) => row.symbol, totalDirection);

  return {
    signal_mode: edge.signal_mode,
    history_level: edge.history_level,
    history_key: edge.history_key,
    horizon_days: horizon,
    n: edge.n,
    avg_excess_peer_return_pct: edge.avg_excess_peer_return_pct,
    peer_hit_rate_pct: edge.peer_hit_rate_pct,
    edge_rating: edge.edge_rating,
    forecast_bias: edge.forecast_bias,
    tested_period_slices: periodSlices.tested,
    period_direction_consistency_pct: periodSlices.consistency_pct,
    period_slice_detail: periodSlices.detail,
    tested_symbol_slices: symbolSlices.tested,
    symbol_direction_consistency_pct: symbolSlices.consistency_pct,
    symbol_slice_detail: symbolSlices.detail,
    robustness_grade: gradeRobustness(edge, periodSlices, symbolSlices, totalDirection),
  };
}

function matchesEdge(instance, edge) {
  if (instance.signal_mode !== edge.signal_mode) return false;
  if (edge.history_level === "specific") return instance.specific_history_key === edge.history_key;
  if (edge.history_level === "state") return instance.state_history_key === edge.history_key;
  if (edge.history_level === "family") return instance.family_history_key === edge.history_key;
  return instance.global_history_key === edge.history_key;
}

function sliceStats(rows, horizon, keyFn, totalDirection) {
  const slices = [];
  for (const [sliceKey, sliceRows] of groupBy(rows, keyFn).entries()) {
    const values = sliceRows
      .map((row) => number(row[`actual_${horizon}d_excess_peer_return_pct`]))
      .filter((value) => value !== null);
    if (values.length < MIN_SLICE_N) continue;
    const sliceStatsValue = stats(values);
    const avg = number(sliceStatsValue.avg) ?? 0;
    const direction = avg >= 0 ? "positive" : "negative";
    slices.push({
      slice: sliceKey,
      n: values.length,
      avg,
      hit_rate: number(sliceStatsValue.hit_rate_pct) ?? 0,
      direction,
      agrees: direction === totalDirection,
    });
  }

  const agrees = slices.filter((slice) => slice.agrees).length;
  return {
    tested: slices.length,
    consistency_pct: pct(agrees, slices.length),
    detail: slices
      .sort((left, right) => String(left.slice).localeCompare(String(right.slice)))
      .map((slice) => `${slice.slice}:n=${slice.n},avg=${format(slice.avg)},hit=${format(slice.hit_rate, 2)}`)
      .join("; "),
  };
}

function gradeRobustness(edge, periodSlices, symbolSlices, direction) {
  const avg = number(edge.avg_excess_peer_return_pct) ?? 0;
  const hit = number(edge.peer_hit_rate_pct) ?? 0;
  const periodConsistency = number(periodSlices.consistency_pct) ?? 0;
  const symbolConsistency = number(symbolSlices.consistency_pct) ?? 0;
  const enoughSlices = periodSlices.tested >= 2 && symbolSlices.tested >= 3;

  if (!enoughSlices) return "thin_slices";
  if (direction === "positive" && avg >= 0.5 && hit >= 52 && periodConsistency >= 67 && symbolConsistency >= 60) {
    return "robust_positive";
  }
  if (direction === "negative" && avg <= -0.5 && hit <= 45 && periodConsistency >= 67 && symbolConsistency >= 60) {
    return "robust_negative";
  }
  if (periodConsistency < 60 || symbolConsistency < 55) return "unstable";
  return "mixed_but_usable";
}

function compareRows(left, right) {
  const gradeRank = {
    robust_positive: 5,
    robust_negative: 4,
    mixed_but_usable: 3,
    unstable: 2,
    thin_slices: 1,
  };
  const byGrade = (gradeRank[right.robustness_grade] ?? 0) - (gradeRank[left.robustness_grade] ?? 0);
  if (byGrade !== 0) return byGrade;
  const byHorizon = Number(left.horizon_days) - Number(right.horizon_days);
  if (byHorizon !== 0) return byHorizon;
  return Math.abs(number(right.avg_excess_peer_return_pct) ?? 0) - Math.abs(number(left.avg_excess_peer_return_pct) ?? 0);
}

function buildReport(rows) {
  const primary = rows.filter((row) => row.horizon_days === PRIMARY_HORIZON);
  const robust = primary.filter((row) => ["robust_positive", "robust_negative"].includes(row.robustness_grade)).slice(0, 12);
  const unstable = primary.filter((row) => row.robustness_grade === "unstable").slice(0, 12);
  const gradeCounts = [...groupBy(rows, (row) => row.robustness_grade).entries()]
    .map(([grade, group]) => ({ grade, rows: group.length }))
    .sort((left, right) => right.rows - left.rows);

  const headers = [
    { key: "history_level", label: "Level" },
    { key: "horizon_days", label: "H", align: "---:" },
    { key: "n", label: "N", align: "---:" },
    { key: "avg_excess_peer_return_pct", label: "Avg vs peer", align: "---:" },
    { key: "peer_hit_rate_pct", label: "Peer hit", align: "---:" },
    { key: "period_direction_consistency_pct", label: "Period agree", align: "---:" },
    { key: "symbol_direction_consistency_pct", label: "Symbol agree", align: "---:" },
    { key: "robustness_grade", label: "Grade" },
    { key: "history_key", label: "Pattern" },
  ];

  const gradeHeaders = [
    { key: "grade", label: "Grade" },
    { key: "rows", label: "Rows", align: "---:" },
  ];

  const lines = [
    "# Experiment 09.3 Pattern Robustness",
    "",
    "Research only. This checks whether pattern edges repeat across time periods and symbols, not just in one convenient sample.",
    "",
    "## Grade Counts",
    "",
    ...markdownTable(gradeCounts, gradeHeaders, "No grade rows."),
    "",
    "## Robust 10-Session Patterns",
    "",
    ...markdownTable(robust, headers, "No robust 10-session patterns."),
    "",
    "## Unstable 10-Session Patterns",
    "",
    ...markdownTable(unstable, headers, "No unstable 10-session patterns."),
    "",
    "## How To Use",
    "",
    "- Prefer robust patterns over one-off high averages.",
    "- Treat `thin_slices` as interesting but unproven.",
    "- Treat `unstable` as dangerous for live decision-making unless a separate reason explains the regime shift.",
  ];

  return `${lines.join("\n")}\n`;
}

main();
