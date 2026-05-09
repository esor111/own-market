import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const PATTERN_INSTANCES_PATH = path.join(DATA_DIR, "pattern_instances.csv");
const PATTERN_EDGE_REPORT_PATH = path.join(RESULTS_DIR, "pattern_edge_report.csv");
const LATEST_FORECAST_CSV_PATH = path.join(RESULTS_DIR, "latest_forecast.csv");
const LATEST_FORECAST_MD_PATH = path.join(RESULTS_DIR, "latest_forecast.md");

const HORIZONS = ["1", "3", "5", "10", "20"];
const DISPLAY_HORIZON = "10";
const MIN_HISTORY_N = 20;

function main() {
  const instances = readCsv(PATTERN_INSTANCES_PATH);
  const edges = readCsv(PATTERN_EDGE_REPORT_PATH);

  const latestSignalDate = instances.reduce((latest, row) => row.signal_date > latest ? row.signal_date : latest, "");
  const latestInstances = instances
    .filter((row) => row.signal_date === latestSignalDate)
    .sort(compareLatestInstances);

  const edgeMap = new Map(edges.map((row) => [statsKey(row.history_key, row.horizon_days), row]));
  const forecastRows = [];

  for (const instance of latestInstances) {
    for (const horizon of HORIZONS) {
      const picked = pickEdge(instance, horizon, edgeMap);
      forecastRows.push(buildForecastRow(instance, horizon, picked));
    }
  }

  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(LATEST_FORECAST_CSV_PATH, forecastRows);
  fs.writeFileSync(LATEST_FORECAST_MD_PATH, buildMarkdown(latestSignalDate, forecastRows), "utf8");

  console.log(`Wrote ${LATEST_FORECAST_CSV_PATH} (${forecastRows.length} rows)`);
  console.log(`Wrote ${LATEST_FORECAST_MD_PATH}`);
}

function pickEdge(instance, horizon, edgeMap) {
  const keyOrder = [
    ["specific", instance.specific_history_key],
    ["state", instance.state_history_key],
    ["family", instance.family_history_key],
    ["global", instance.global_history_key],
  ];

  let bestLowSample = null;
  for (const [level, historyKey] of keyOrder) {
    const row = edgeMap.get(statsKey(historyKey, horizon));
    if (!row) continue;
    const n = number(row.n) ?? 0;
    const candidate = { ...row, history_level: level, history_key: historyKey };
    if (n >= MIN_HISTORY_N) return candidate;
    if (!bestLowSample || n > (number(bestLowSample.n) ?? 0)) bestLowSample = candidate;
  }

  return bestLowSample ?? {
    signal_mode: instance.signal_mode,
    history_level: "none",
    history_key: "",
    horizon_days: horizon,
    n: 0,
    avg_raw_return_pct: "",
    avg_excess_peer_return_pct: "",
    raw_hit_rate_pct: "",
    peer_hit_rate_pct: "",
    edge_rating: "insufficient_history",
    forecast_bias: "insufficient",
  };
}

function buildForecastRow(instance, horizon, picked) {
  const action = normalizedAction(picked);
  return {
    symbol: instance.symbol,
    source_date: instance.source_date,
    signal_date: instance.signal_date,
    signal_mode: instance.signal_mode,
    state: instance.state,
    confirmation_status: instance.confirmation_status,
    horizon_days: horizon,
    forecast_action: action.forecast_action,
    forecast_bias: action.forecast_bias,
    forecast_confidence: forecastConfidence(picked, instance, action),
    expected_raw_return_pct: picked.avg_raw_return_pct ?? "",
    expected_excess_peer_return_pct: picked.avg_excess_peer_return_pct ?? "",
    historical_peer_hit_rate_pct: picked.peer_hit_rate_pct ?? "",
    historical_raw_hit_rate_pct: picked.raw_hit_rate_pct ?? "",
    history_n: picked.n ?? 0,
    history_level: picked.history_level ?? "",
    history_key: picked.history_key ?? "",
    watch_read: watchRead(action, picked),
    invalidation_level: instance.invalidation_level,
    pattern_family: instance.pattern_family,
    score: instance.score,
    confidence: instance.confidence,
    evidence_bucket: instance.evidence_bucket,
    quality_bucket: instance.quality_bucket,
    positive_evidence: instance.positive_evidence,
    negative_evidence: instance.negative_evidence,
    quality_flags: instance.quality_flags,
  };
}

function normalizedAction(edgeRow) {
  const n = number(edgeRow.n) ?? 0;
  const avgExcess = number(edgeRow.avg_excess_peer_return_pct);
  const peerHit = number(edgeRow.peer_hit_rate_pct);
  if (n < MIN_HISTORY_N || avgExcess === null || peerHit === null) {
    return { forecast_action: "insufficient_history", forecast_bias: "insufficient" };
  }
  return {
    forecast_action: edgeRow.edge_rating || "no_edge",
    forecast_bias: edgeRow.forecast_bias || "neutral",
  };
}

function forecastConfidence(edgeRow, instance, action) {
  const n = number(edgeRow.n) ?? 0;
  if (n === 0 || action.forecast_bias === "insufficient") return "0.05";

  const avgExcess = Math.abs(number(edgeRow.avg_excess_peer_return_pct) ?? 0);
  const peerHit = number(edgeRow.peer_hit_rate_pct) ?? 50;
  let value = 0.2;
  value += Math.min(0.25, Math.log10(Math.max(n, 1)) * 0.12);
  value += Math.min(0.2, avgExcess / 8);
  value += Math.min(0.15, Math.abs(peerHit - 50) / 100);

  if (edgeRow.history_level === "specific") value += 0.05;
  if (edgeRow.history_level === "family") value -= 0.04;
  if (edgeRow.history_level === "global") value -= 0.08;
  if (String(instance.quality_bucket).includes("no_broker")) value -= 0.08;
  if (String(instance.quality_bucket).includes("no_tape")) value -= 0.04;
  if (String(instance.quality_bucket).includes("event_risk")) value -= 0.04;

  return Math.max(0.05, Math.min(0.85, value)).toFixed(2);
}

function watchRead(action, edgeRow) {
  if (action.forecast_bias === "insufficient") return "not enough prior examples for this pattern";
  if (action.forecast_bias === "outperform") return "historically outperformed peers after this pattern; still require price confirmation and invalidation discipline";
  if (action.forecast_bias === "underperform") return "historically underperformed peers after this pattern; avoid unless the pattern fails";
  if ((number(edgeRow.avg_excess_peer_return_pct) ?? 0) > 0) return "slightly positive history, but not enough to treat as a signal";
  return "no useful standalone edge in the current pattern library";
}

function buildMarkdown(latestSignalDate, forecastRows) {
  const displayRows = forecastRows
    .filter((row) => row.horizon_days === DISPLAY_HORIZON)
    .sort(compareForecastRows);
  const actionable = forecastRows
    .filter((row) => ["5", "10"].includes(row.horizon_days))
    .filter((row) => !["insufficient_history", "no_edge"].includes(row.forecast_action))
    .sort(compareForecastRows)
    .slice(0, 12);

  const lines = [
    "# Experiment 09.1 Latest Forecast",
    "",
    "Research only. This is a pattern-history forecast from the newest completed local signal date.",
    "",
    `Latest signal date: ${latestSignalDate || "n/a"}`,
    "",
    "## Current Actionable Reads",
    "",
    "| Symbol | Mode | State | Confirmation | Horizon | Action | Expected vs peer | Hit history | Confidence | Read |",
    "|---|---|---|---|---:|---|---:|---:|---:|---|",
  ];

  if (actionable.length === 0) {
    lines.push("| n/a | n/a | n/a | n/a | n/a | no actionable edge | n/a | n/a | n/a | No current row passed the actionable filters. |");
  } else {
    for (const row of actionable) {
      lines.push(
        `| ${row.symbol} | ${row.signal_mode} | ${row.state} | ${row.confirmation_status} | ${row.horizon_days} | ` +
        `${row.forecast_action} | ${row.expected_excess_peer_return_pct || "n/a"}% | ` +
        `${row.historical_peer_hit_rate_pct || "n/a"}% | ${row.forecast_confidence} | ${row.watch_read} |`,
      );
    }
  }

  lines.push(
    "",
    `## ${DISPLAY_HORIZON}-Session Forecast Table`,
    "",
    "| Symbol | Mode | State | Confirmation | Action | Bias | N | Expected vs peer | Peer hit | Invalidation |",
    "|---|---|---|---|---|---|---:|---:|---:|---|",
  );

  for (const row of displayRows) {
    lines.push(
      `| ${row.symbol} | ${row.signal_mode} | ${row.state} | ${row.confirmation_status} | ${row.forecast_action} | ` +
      `${row.forecast_bias} | ${row.history_n} | ${row.expected_excess_peer_return_pct || "n/a"}% | ` +
      `${row.historical_peer_hit_rate_pct || "n/a"}% | ${escapePipes(row.invalidation_level)} |`,
    );
  }

  lines.push(
    "",
    "## Reliability Notes",
    "",
    "- This forecast uses only completed local data already present in Experiment 09.",
    "- `same_day_close` is available at the signal day's close.",
    "- `next_session_confirmation` is available only after the next session confirms or fails the prior state.",
    "- `missing_intraday_volume` and `missing_broker_flow` reduce confidence.",
    "- Use this as a watchlist and validation loop, not as automatic trade execution.",
  );

  return `${lines.join("\n")}\n`;
}

function compareLatestInstances(left, right) {
  const bySymbol = String(left.symbol).localeCompare(String(right.symbol));
  if (bySymbol !== 0) return bySymbol;
  const byMode = String(left.signal_mode).localeCompare(String(right.signal_mode));
  if (byMode !== 0) return byMode;
  return String(left.state).localeCompare(String(right.state));
}

function compareForecastRows(left, right) {
  const actionRank = {
    strong_outperform_watch: 5,
    outperform_watch: 4,
    underperform_avoid: 3,
    strong_underperform_avoid: 2,
    no_edge: 1,
    insufficient_history: 0,
  };
  const byAction = (actionRank[right.forecast_action] ?? -1) - (actionRank[left.forecast_action] ?? -1);
  if (byAction !== 0) return byAction;
  const byConfidence = (number(right.forecast_confidence) ?? 0) - (number(left.forecast_confidence) ?? 0);
  if (byConfidence !== 0) return byConfidence;
  return Math.abs(number(right.expected_excess_peer_return_pct) ?? 0) - Math.abs(number(left.expected_excess_peer_return_pct) ?? 0);
}

function statsKey(historyKey, horizon) {
  return JSON.stringify([historyKey, horizon]);
}

function number(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

function escapePipes(value) {
  return String(value ?? "").replace(/\|/g, " / ");
}

function readCsv(filePath) {
  if (!fs.existsSync(filePath) || fs.statSync(filePath).size === 0) return [];
  const text = fs.readFileSync(filePath, "utf8").replace(/^\uFEFF/, "");
  const rows = parseCsv(text);
  if (rows.length === 0) return [];
  const headers = rows[0];
  return rows.slice(1).filter((row) => row.some((value) => value !== "")).map((row) => {
    const object = {};
    for (let index = 0; index < headers.length; index += 1) {
      object[headers[index]] = row[index] ?? "";
    }
    return object;
  });
}

function parseCsv(text) {
  const rows = [];
  let row = [];
  let field = "";
  let inQuotes = false;

  for (let index = 0; index < text.length; index += 1) {
    const char = text[index];
    const next = text[index + 1];
    if (inQuotes) {
      if (char === '"' && next === '"') {
        field += '"';
        index += 1;
      } else if (char === '"') {
        inQuotes = false;
      } else {
        field += char;
      }
      continue;
    }
    if (char === '"') {
      inQuotes = true;
    } else if (char === ",") {
      row.push(field);
      field = "";
    } else if (char === "\n") {
      row.push(field);
      rows.push(row);
      row = [];
      field = "";
    } else if (char !== "\r") {
      field += char;
    }
  }
  if (field !== "" || row.length > 0) {
    row.push(field);
    rows.push(row);
  }
  return rows;
}

function writeCsv(filePath, rows) {
  if (rows.length === 0) {
    fs.writeFileSync(filePath, "", "utf8");
    return;
  }
  const headers = [];
  const seen = new Set();
  for (const row of rows) {
    for (const header of Object.keys(row)) {
      if (!seen.has(header)) {
        seen.add(header);
        headers.push(header);
      }
    }
  }
  const lines = [headers.map(csvEscape).join(",")];
  for (const row of rows) {
    lines.push(headers.map((header) => csvEscape(row[header] ?? "")).join(","));
  }
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`, "utf8");
}

function csvEscape(value) {
  const text = String(value);
  if (/[",\r\n]/.test(text)) return `"${text.replace(/"/g, '""')}"`;
  return text;
}

main();
