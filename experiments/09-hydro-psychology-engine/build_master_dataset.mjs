import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const ROOT_DIR = path.resolve(SCRIPT_DIR, "..", "..");
const CONFIG_PATH = path.join(SCRIPT_DIR, "config.json");
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const BROKER_DAILY_PATH = path.join(ROOT_DIR, "experiments", "07-hydro-broker-flow", "data", "hydro_broker_flow_daily.csv");
const VOLUME_DAILY_PATH = path.join(ROOT_DIR, "experiments", "08-hydro-volume-tape-lab", "data", "volume_daily.csv");
const CORP_EVENTS_PATH = path.join(ROOT_DIR, "experiments", "01-corporate-action", "data", "events.csv");
const LOCKIN_EVENTS_PATH = path.join(ROOT_DIR, "experiments", "02-lockin-expiry", "data", "unlock_events.csv");
const NRB_POLICY_PATH = path.join(ROOT_DIR, "experiments", "03-nrb-rate-events", "data", "policy_events.csv");
const NRB_RATE_PATH = path.join(ROOT_DIR, "experiments", "03-nrb-rate-events", "data", "rate_move_events.csv");
const SEASONALITY_PATH = path.join(ROOT_DIR, "experiments", "04-hydro-seasonality", "data", "monthly_returns.csv");
const FLOOD_EVENTS_PATH = path.join(ROOT_DIR, "experiments", "06-hydro-flood-damage", "data", "flood_damage_event_table.csv");

const OUTPUT_DAILY_PATH = path.join(DATA_DIR, "hydro_psychology_daily.csv");
const OUTPUT_SUMMARY_PATH = path.join(RESULTS_DIR, "build_summary.md");

const TAPE_COLUMNS = [
  "open",
  "high",
  "low",
  "close",
  "volume",
  "bars",
  "volume_ratio_20d",
  "return_pct",
  "range_pct",
  "close_position",
  "volume_spike",
  "volume_drought",
  "high_volume_up",
  "high_volume_down",
  "failed_rally",
  "absorption_candle",
];

const CORP_DATE_COLUMNS = [
  "announcement_date",
  "approval_date",
  "book_close_date",
  "ex_date",
  "listing_date",
  "distribution_date",
  "meeting_date",
  "right_open_date",
  "right_close_date",
  "right_final_date",
];

function main() {
  const config = JSON.parse(fs.readFileSync(CONFIG_PATH, "utf8"));
  const symbols = new Set(config.symbols.map((symbol) => symbol.toUpperCase()));
  const windows = config.event_windows ?? {};

  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.mkdirSync(RESULTS_DIR, { recursive: true });

  const brokerRows = readCsv(BROKER_DAILY_PATH).filter((row) => symbols.has((row.symbol ?? "").toUpperCase()));
  const tapeByKey = loadTapeRows(symbols);
  const corpIndex = loadCorporateEvents(symbols, Number(windows.corporate_action_days ?? 5));
  const lockinIndex = loadLockinEvents(symbols, Number(windows.lockin_days ?? 20));
  const nrbIndex = loadMarketEvents(Number(windows.nrb_event_days ?? 3));
  const floodIndex = loadFloodEvents(symbols, Number(windows.flood_damage_days ?? 30));
  const seasonality = loadSeasonality(symbols);

  const outputRows = [];
  for (const base of brokerRows) {
    const symbol = (base.symbol ?? "").toUpperCase();
    const runDate = parseIsoDate(base.date);
    if (!runDate) continue;

    const row = { ...base };
    mergeTape(row, tapeByKey.get(key(symbol, row.date)));
    addEventContext(row, corpIndex.get(key(symbol, runDate)) ?? [], "corp_action");
    addEventContext(row, lockinIndex.get(key(symbol, runDate)) ?? [], "lockin");
    addEventContext(row, nrbIndex.get(runDate) ?? [], "nrb_event");
    addEventContext(row, floodIndex.get(key(symbol, runDate)) ?? [], "flood_damage");
    row.seasonality_month_avg_return_pct = seasonality.get(key(symbol, monthOf(runDate))) ?? "";
    row.quality_flags = buildQualityFlags(row);
    outputRows.push(row);
  }

  writeCsv(OUTPUT_DAILY_PATH, outputRows);
  fs.writeFileSync(OUTPUT_SUMMARY_PATH, buildSummary(outputRows, tapeByKey, config), "utf8");

  console.log(`Wrote ${OUTPUT_DAILY_PATH} (${outputRows.length} rows)`);
  console.log(`Wrote ${OUTPUT_SUMMARY_PATH}`);
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
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, '""')}"`;
  }
  return text;
}

function parseIsoDate(value) {
  const text = String(value ?? "").trim().slice(0, 10);
  return /^\d{4}-\d{2}-\d{2}$/.test(text) ? text : null;
}

function addDays(isoDate, days) {
  const [year, month, day] = isoDate.split("-").map(Number);
  const utc = new Date(Date.UTC(year, month - 1, day));
  utc.setUTCDate(utc.getUTCDate() + days);
  return utc.toISOString().slice(0, 10);
}

function dateRange(center, radiusDays) {
  const values = [];
  for (let offset = -radiusDays; offset <= radiusDays; offset += 1) {
    values.push(addDays(center, offset));
  }
  return values;
}

function monthOf(isoDate) {
  return Number(isoDate.slice(5, 7));
}

function key(...parts) {
  return parts.join("|");
}

function pushIndex(index, indexKey, value) {
  if (!index.has(indexKey)) index.set(indexKey, []);
  index.get(indexKey).push(value);
}

function loadTapeRows(symbols) {
  const result = new Map();
  for (const row of readCsv(VOLUME_DAILY_PATH)) {
    const symbol = (row.symbol ?? "").toUpperCase();
    if (symbols.has(symbol) && row.date) {
      result.set(key(symbol, row.date), row);
    }
  }
  return result;
}

function mergeTape(row, tape) {
  row.tape_available = tape ? 1 : 0;
  for (const column of TAPE_COLUMNS) {
    row[`tape_${column}`] = tape?.[column] ?? "";
  }
}

function loadCorporateEvents(symbols, windowDays) {
  const index = new Map();
  for (const row of readCsv(CORP_EVENTS_PATH)) {
    const symbol = (row.symbol ?? "").toUpperCase();
    if (!symbols.has(symbol)) continue;
    const label = eventLabel(row, "event_type");
    for (const column of CORP_DATE_COLUMNS) {
      const eventDate = parseIsoDate(row[column]);
      if (!eventDate) continue;
      for (const runDate of dateRange(eventDate, windowDays)) {
        pushIndex(index, key(symbol, runDate), `${label}:${column}:${eventDate}`);
      }
    }
  }
  return index;
}

function loadLockinEvents(symbols, windowDays) {
  const index = new Map();
  for (const row of readCsv(LOCKIN_EVENTS_PATH)) {
    const symbol = (row.symbol ?? "").toUpperCase();
    if (!symbols.has(symbol)) continue;
    const eventDate = parseIsoDate(row.unlock_date_proxy);
    if (!eventDate) continue;
    const label = eventLabel(row, "event_type");
    for (const runDate of dateRange(eventDate, windowDays)) {
      pushIndex(index, key(symbol, runDate), `${label}:${eventDate}`);
    }
  }
  return index;
}

function loadMarketEvents(windowDays) {
  const index = new Map();
  for (const [filePath, fallback] of [[NRB_POLICY_PATH, "policy"], [NRB_RATE_PATH, "rate_move"]]) {
    for (const row of readCsv(filePath)) {
      const eventDate = parseIsoDate(row.event_date);
      if (!eventDate) continue;
      const label = eventLabel(row, "event_type") || fallback;
      for (const runDate of dateRange(eventDate, windowDays)) {
        pushIndex(index, runDate, `${label}:${eventDate}`);
      }
    }
  }
  return index;
}

function loadFloodEvents(symbols, windowDays) {
  const index = new Map();
  for (const row of readCsv(FLOOD_EVENTS_PATH)) {
    const symbol = (row.ticker ?? "").toUpperCase();
    if (!symbols.has(symbol)) continue;
    const eventDate = parseIsoDate(row.event_anchor_date || row.event_start_date);
    if (!eventDate) continue;
    const severity = row.severity_bucket || "unknown";
    for (const runDate of dateRange(eventDate, windowDays)) {
      pushIndex(index, key(symbol, runDate), `${severity}:${eventDate}`);
    }
  }
  return index;
}

function loadSeasonality(symbols) {
  const grouped = new Map();
  for (const row of readCsv(SEASONALITY_PATH)) {
    const symbol = (row.symbol ?? "").toUpperCase();
    if (!symbols.has(symbol)) continue;
    const month = asNumber(row.month);
    const returnPct = asNumber(row.return_pct);
    if (!month || returnPct === null) continue;
    const groupKey = key(symbol, month);
    if (!grouped.has(groupKey)) grouped.set(groupKey, []);
    grouped.get(groupKey).push(returnPct);
  }
  const result = new Map();
  for (const [groupKey, values] of grouped) {
    const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
    result.set(groupKey, avg.toFixed(4));
  }
  return result;
}

function eventLabel(row, preferred) {
  for (const column of [preferred, "event_label", "raw_title", "detail"]) {
    const value = String(row[column] ?? "").trim();
    if (value) return value.replace(/\|/g, "/");
  }
  return "event";
}

function addEventContext(row, events, prefix) {
  const uniqueEvents = [...new Set(events)].sort();
  row[`${prefix}_window`] = uniqueEvents.length > 0 ? 1 : 0;
  row[`${prefix}_events`] = uniqueEvents.join("|");
}

function buildQualityFlags(row) {
  const flags = [];
  if (String(row.broker_available ?? "").trim() !== "1") flags.push("missing_broker_flow");
  if (String(row.tape_available ?? "").trim() !== "1") flags.push("missing_intraday_volume");
  if (String(row.corp_action_window ?? "").trim() === "1") flags.push("event_window");
  if (String(row.lockin_window ?? "").trim() === "1") flags.push("lockin_window");
  if (String(row.nrb_event_window ?? "").trim() === "1") flags.push("nrb_event_window");
  if (String(row.flood_damage_window ?? "").trim() === "1") flags.push("flood_damage_window");
  if (!row.fwd_10d_return_pct) flags.push("no_forward_outcome_yet");
  return flags.join("|");
}

function asNumber(value) {
  if (value === null || value === undefined || value === "") return null;
  const number = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(number) ? number : null;
}

function buildSummary(rows, tapeByKey, config) {
  const symbolCounts = new Map();
  const flagCounts = new Map();

  for (const row of rows) {
    symbolCounts.set(row.symbol, (symbolCounts.get(row.symbol) ?? 0) + 1);
    for (const flag of String(row.quality_flags ?? "").split("|")) {
      if (flag) flagCounts.set(flag, (flagCounts.get(flag) ?? 0) + 1);
    }
  }

  const brokerRows = rows.filter((row) => String(row.broker_available) === "1").length;
  const tapeMatches = rows.filter((row) => String(row.tape_available) === "1").length;
  const eventRows = rows.filter((row) => String(row.corp_action_window) === "1").length;
  const lockinRows = rows.filter((row) => String(row.lockin_window) === "1").length;
  const nrbRows = rows.filter((row) => String(row.nrb_event_window) === "1").length;
  const floodRows = rows.filter((row) => String(row.flood_damage_window) === "1").length;

  const lines = [
    "# Experiment 09 Build Summary",
    "",
    "Phase 1 master daily table build.",
    "",
    "## Inputs",
    "",
    `- Broker-flow daily: \`${relative(BROKER_DAILY_PATH)}\``,
    `- Volume/tape daily: \`${relative(VOLUME_DAILY_PATH)}\``,
    `- Corporate events: \`${relative(CORP_EVENTS_PATH)}\``,
    `- Lock-in events: \`${relative(LOCKIN_EVENTS_PATH)}\``,
    `- NRB policy events: \`${relative(NRB_POLICY_PATH)}\``,
    `- NRB rate events: \`${relative(NRB_RATE_PATH)}\``,
    `- Seasonality: \`${relative(SEASONALITY_PATH)}\``,
    `- Flood damage events: \`${relative(FLOOD_EVENTS_PATH)}\``,
    "",
    "## Coverage",
    "",
    `- Symbols: ${config.symbols.join(", ")}`,
    `- Output rows: ${rows.length.toLocaleString("en-US")}`,
    `- Broker-backed rows: ${brokerRows.toLocaleString("en-US")}`,
    `- Tape-matched rows: ${tapeMatches.toLocaleString("en-US")}`,
    `- Loaded tape keys: ${tapeByKey.size.toLocaleString("en-US")}`,
    `- Corporate-action window rows: ${eventRows.toLocaleString("en-US")}`,
    `- Lock-in window rows: ${lockinRows.toLocaleString("en-US")}`,
    `- NRB event window rows: ${nrbRows.toLocaleString("en-US")}`,
    `- Flood damage window rows: ${floodRows.toLocaleString("en-US")}`,
    "",
    "## Rows By Symbol",
    "",
    "| Symbol | Rows |",
    "|---|---:|",
  ];

  for (const symbol of config.symbols) {
    lines.push(`| ${symbol} | ${(symbolCounts.get(symbol) ?? 0).toLocaleString("en-US")} |`);
  }

  lines.push("", "## Quality Flags", "", "| Flag | Rows |", "|---|---:|");
  for (const [flag, count] of [...flagCounts.entries()].sort(([left], [right]) => left.localeCompare(right))) {
    lines.push(`| ${flag} | ${count.toLocaleString("en-US")} |`);
  }

  lines.push(
    "",
    "## Notes",
    "",
    "- This build is read-only toward upstream experiments.",
    "- Tape coverage is expected to be sparse until experiment 08 captures more hydropower symbols.",
    "- This file is not a trading signal yet. Phase 2 will add transparent psychology scoring.",
  );
  return `${lines.join("\n")}\n`;
}

function relative(filePath) {
  return path.relative(ROOT_DIR, filePath).replace(/\\/g, "/");
}

main();
