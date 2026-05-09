import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";
import {
  format,
  groupBy,
  hasFlag,
  markdownTable,
  number,
  pct,
  periodBucket,
  readCsv,
  writeCsv,
} from "./lib/validation_utils.mjs";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const DAILY_PATH = path.join(DATA_DIR, "hydro_psychology_daily.csv");
const STATES_PATH = path.join(DATA_DIR, "psychology_states.csv");
const PATTERN_INSTANCES_PATH = path.join(DATA_DIR, "pattern_instances.csv");
const WALK_FORWARD_PATH = path.join(RESULTS_DIR, "walk_forward_predictions.csv");

const SYMBOL_OUTPUT_PATH = path.join(RESULTS_DIR, "data_quality_by_symbol.csv");
const PERIOD_OUTPUT_PATH = path.join(RESULTS_DIR, "data_quality_by_period.csv");
const REPORT_PATH = path.join(RESULTS_DIR, "data_quality_report.md");

function main() {
  const dailyRows = readCsv(DAILY_PATH);
  const stateRows = readCsv(STATES_PATH);
  const instances = readCsv(PATTERN_INSTANCES_PATH);
  const predictions = readCsv(WALK_FORWARD_PATH);

  const symbolRows = buildSymbolRows(dailyRows, stateRows, instances, predictions);
  const periodRows = buildPeriodRows(dailyRows, stateRows, instances, predictions);

  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(SYMBOL_OUTPUT_PATH, symbolRows);
  writeCsv(PERIOD_OUTPUT_PATH, periodRows);
  fs.writeFileSync(REPORT_PATH, buildReport(symbolRows, periodRows), "utf8");

  console.log(`Wrote ${SYMBOL_OUTPUT_PATH} (${symbolRows.length} rows)`);
  console.log(`Wrote ${PERIOD_OUTPUT_PATH} (${periodRows.length} rows)`);
  console.log(`Wrote ${REPORT_PATH}`);
}

function buildSymbolRows(dailyRows, stateRows, instances, predictions) {
  const statesBySymbol = groupBy(stateRows, (row) => row.symbol);
  const instancesBySymbol = groupBy(instances, (row) => row.symbol);
  const predictionsBySymbol = groupBy(predictions, (row) => row.symbol);

  return [...groupBy(dailyRows, (row) => row.symbol).entries()]
    .map(([symbol, rows]) => {
      const dates = rows.map((row) => row.date).sort();
      const brokerRows = rows.filter((row) => String(row.broker_available ?? "").trim() === "1").length;
      const tapeRows = rows.filter((row) => String(row.tape_available ?? "").trim() === "1").length;
      const eventRows = rows.filter((row) => hasFlag(row, "event_window") || hasFlag(row, "lockin_window") || hasFlag(row, "nrb_event_window") || hasFlag(row, "flood_damage_window")).length;
      const forwardRows = rows.filter((row) => !hasFlag(row, "no_forward_outcome_yet")).length;
      const scoredPredictions = (predictionsBySymbol.get(symbol) ?? []).filter((row) => ["hit", "miss"].includes(row.forecast_result)).length;
      const patternRows = (instancesBySymbol.get(symbol) ?? []).length;
      const stateCount = (statesBySymbol.get(symbol) ?? []).filter((row) => row.state !== "no_clear_signal").length;
      const latestDate = dates[dates.length - 1] ?? "";

      return {
        symbol,
        first_date: dates[0] ?? "",
        latest_date: latestDate,
        price_rows: rows.length,
        broker_rows: brokerRows,
        broker_coverage_pct: pct(brokerRows, rows.length),
        tape_rows: tapeRows,
        tape_coverage_pct: pct(tapeRows, rows.length),
        event_context_rows: eventRows,
        event_context_pct: pct(eventRows, rows.length),
        rows_with_10d_forward_outcome: forwardRows,
        forward_coverage_pct: pct(forwardRows, rows.length),
        psychology_state_rows: stateCount,
        pattern_instances: patternRows,
        scored_walk_forward_predictions: scoredPredictions,
        latest_row_quality_flags: (rows.find((row) => row.date === latestDate) ?? {}).quality_flags ?? "",
        reliability_grade: gradeReliability({ rows: rows.length, brokerRows, tapeRows, scoredPredictions }),
      };
    })
    .sort((left, right) => String(left.symbol).localeCompare(String(right.symbol)));
}

function buildPeriodRows(dailyRows, stateRows, instances, predictions) {
  const stateByPeriod = groupBy(stateRows, (row) => periodBucket(row.date));
  const instanceByPeriod = groupBy(instances, (row) => periodBucket(row.signal_date));
  const predictionByPeriod = groupBy(predictions, (row) => periodBucket(row.signal_date));

  return [...groupBy(dailyRows, (row) => periodBucket(row.date)).entries()]
    .map(([period, rows]) => {
      const brokerRows = rows.filter((row) => String(row.broker_available ?? "").trim() === "1").length;
      const tapeRows = rows.filter((row) => String(row.tape_available ?? "").trim() === "1").length;
      const eventRows = rows.filter((row) => hasFlag(row, "event_window") || hasFlag(row, "lockin_window") || hasFlag(row, "nrb_event_window") || hasFlag(row, "flood_damage_window")).length;
      const forwardRows = rows.filter((row) => !hasFlag(row, "no_forward_outcome_yet")).length;
      const scoredPredictions = (predictionByPeriod.get(period) ?? []).filter((row) => ["hit", "miss"].includes(row.forecast_result)).length;
      const symbols = new Set(rows.map((row) => row.symbol));
      const stateCount = (stateByPeriod.get(period) ?? []).filter((row) => row.state !== "no_clear_signal").length;

      return {
        period,
        symbols: symbols.size,
        price_rows: rows.length,
        broker_rows: brokerRows,
        broker_coverage_pct: pct(brokerRows, rows.length),
        tape_rows: tapeRows,
        tape_coverage_pct: pct(tapeRows, rows.length),
        event_context_rows: eventRows,
        event_context_pct: pct(eventRows, rows.length),
        rows_with_10d_forward_outcome: forwardRows,
        forward_coverage_pct: pct(forwardRows, rows.length),
        psychology_state_rows: stateCount,
        pattern_instances: (instanceByPeriod.get(period) ?? []).length,
        scored_walk_forward_predictions: scoredPredictions,
        reliability_grade: gradeReliability({ rows: rows.length, brokerRows, tapeRows, scoredPredictions }),
      };
    })
    .sort((left, right) => String(left.period).localeCompare(String(right.period)));
}

function gradeReliability({ rows, brokerRows, tapeRows, scoredPredictions }) {
  const brokerPct = rows ? brokerRows / rows * 100 : 0;
  const tapePct = rows ? tapeRows / rows * 100 : 0;
  if (rows >= 500 && brokerPct >= 50 && tapePct >= 20 && scoredPredictions >= 100) return "strong";
  if (rows >= 500 && brokerPct >= 40 && scoredPredictions >= 100) return "usable_broker_partial_tape_sparse";
  if (rows >= 200 && scoredPredictions >= 25) return "usable_price_first";
  return "thin_or_incomplete";
}

function buildReport(symbolRows, periodRows) {
  const totalPriceRows = symbolRows.reduce((sum, row) => sum + (number(row.price_rows) ?? 0), 0);
  const totalBrokerRows = symbolRows.reduce((sum, row) => sum + (number(row.broker_rows) ?? 0), 0);
  const totalTapeRows = symbolRows.reduce((sum, row) => sum + (number(row.tape_rows) ?? 0), 0);
  const totalScored = symbolRows.reduce((sum, row) => sum + (number(row.scored_walk_forward_predictions) ?? 0), 0);

  const headers = [
    { key: "symbol", label: "Symbol" },
    { key: "price_rows", label: "Price rows", align: "---:" },
    { key: "broker_coverage_pct", label: "Broker %", align: "---:" },
    { key: "tape_coverage_pct", label: "Tape %", align: "---:" },
    { key: "scored_walk_forward_predictions", label: "Scored WF", align: "---:" },
    { key: "reliability_grade", label: "Grade" },
  ];

  const periodHeaders = [
    { key: "period", label: "Period" },
    { key: "price_rows", label: "Rows", align: "---:" },
    { key: "broker_coverage_pct", label: "Broker %", align: "---:" },
    { key: "tape_coverage_pct", label: "Tape %", align: "---:" },
    { key: "pattern_instances", label: "Patterns", align: "---:" },
    { key: "scored_walk_forward_predictions", label: "Scored WF", align: "---:" },
    { key: "reliability_grade", label: "Grade" },
  ];

  const lines = [
    "# Experiment 09.2 Data Quality Audit",
    "",
    "Research only. This answers which rows are strong enough to trust before we make stronger psychology or trading claims.",
    "",
    "## Main Read",
    "",
    `- price rows: ${totalPriceRows}`,
    `- broker-flow coverage: ${format(totalBrokerRows / Math.max(totalPriceRows, 1) * 100, 2)}%`,
    `- intraday tape coverage: ${format(totalTapeRows / Math.max(totalPriceRows, 1) * 100, 2)}%`,
    `- scored walk-forward predictions: ${totalScored}`,
    "- Current foundation is price-rich and broker-partial, but tape-sparse. Any intraday psychology claim must remain lower confidence until Experiment 08 has broader coverage.",
    "",
    "## By Symbol",
    "",
    ...markdownTable(symbolRows, headers, "No symbol rows."),
    "",
    "## By Period",
    "",
    ...markdownTable(periodRows, periodHeaders, "No period rows."),
    "",
    "## Reliability Use",
    "",
    "- Use `strong` and `usable_broker_partial_tape_sparse` rows for signal research.",
    "- Treat `usable_price_first` as price-pattern research, not broker/tape psychology proof.",
    "- Treat `thin_or_incomplete` rows as context only.",
  ];

  return `${lines.join("\n")}\n`;
}

main();
