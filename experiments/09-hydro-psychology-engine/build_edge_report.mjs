import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const STATES_PATH = path.join(DATA_DIR, "psychology_states.csv");
const STATE_OUTCOMES_PATH = path.join(RESULTS_DIR, "state_outcomes.csv");
const CONFIRMATION_OUTCOMES_PATH = path.join(RESULTS_DIR, "state_confirmation_outcomes.csv");

const EDGE_CANDIDATES_PATH = path.join(RESULTS_DIR, "edge_candidates.csv");
const LATEST_WATCHLIST_CSV_PATH = path.join(RESULTS_DIR, "latest_watchlist.csv");
const EDGE_REPORT_PATH = path.join(RESULTS_DIR, "edge_candidate_report.md");

const TARGET_HORIZON = "10";
const MIN_STATE_N = 50;
const MIN_CONFIRMATION_N = 30;
const BEARISH_STATES = new Set(["distribution", "failed_rally", "markdown_continuation", "panic_selling"]);
const BULLISH_STATES = new Set(["accumulation", "panic_absorption", "markup_continuation"]);

function main() {
  const stateRows = readCsv(STATES_PATH);
  const stateOutcomes = readCsv(STATE_OUTCOMES_PATH);
  const confirmationOutcomes = readCsv(CONFIRMATION_OUTCOMES_PATH);

  const edgeCandidates = [
    ...stateOutcomes
      .filter((row) => row.horizon_days === TARGET_HORIZON && row.state !== "no_clear_signal")
      .map((row) => candidateFromStateOutcome(row))
      .filter((row) => row.edge_rating !== "reject"),
    ...confirmationOutcomes
      .filter((row) => row.horizon_days === TARGET_HORIZON && row.state !== "no_clear_signal")
      .map((row) => candidateFromConfirmationOutcome(row))
      .filter((row) => row.edge_rating !== "reject"),
  ].sort(compareCandidates);

  const stateEdgeMap = buildStateEdgeMap(stateOutcomes);
  const latestWatchlist = buildLatestWatchlist(stateRows, stateEdgeMap);

  writeCsv(EDGE_CANDIDATES_PATH, edgeCandidates);
  writeCsv(LATEST_WATCHLIST_CSV_PATH, latestWatchlist);
  fs.writeFileSync(EDGE_REPORT_PATH, buildMarkdown(edgeCandidates, latestWatchlist), "utf8");

  console.log(`Wrote ${EDGE_CANDIDATES_PATH} (${edgeCandidates.length} rows)`);
  console.log(`Wrote ${LATEST_WATCHLIST_CSV_PATH} (${latestWatchlist.length} rows)`);
  console.log(`Wrote ${EDGE_REPORT_PATH}`);
}

function candidateFromStateOutcome(row) {
  const n = number(row.n) ?? 0;
  const avgExcess = number(row.avg_excess_peer_return_pct);
  const peerHit = number(row.peer_hit_rate_pct);
  const rating = rateEdge({
    n,
    minN: MIN_STATE_N,
    avgExcess,
    peerHit,
    confirmationStatus: "all",
    state: row.state,
  });
  return {
    candidate_type: "state_base",
    state: row.state,
    confirmation_status: "all",
    horizon_days: row.horizon_days,
    n,
    avg_return_pct: row.avg_return_pct,
    avg_excess_peer_return_pct: row.avg_excess_peer_return_pct,
    peer_hit_rate_pct: row.peer_hit_rate_pct,
    worst_excess_peer_return_pct: row.worst_excess_peer_return_pct,
    best_excess_peer_return_pct: row.best_excess_peer_return_pct,
    edge_rating: rating,
    interpretation: interpretation(row.state, "all", rating),
  };
}

function candidateFromConfirmationOutcome(row) {
  const n = number(row.n) ?? 0;
  const avgExcess = number(row.avg_excess_peer_return_pct);
  const peerHit = number(row.peer_hit_rate_pct);
  const rating = rateEdge({
    n,
    minN: MIN_CONFIRMATION_N,
    avgExcess,
    peerHit,
    confirmationStatus: row.confirmation_status,
    state: row.state,
  });
  return {
    candidate_type: "confirmation",
    state: row.state,
    confirmation_status: row.confirmation_status,
    horizon_days: row.horizon_days,
    n,
    avg_return_pct: row.avg_return_pct,
    avg_excess_peer_return_pct: row.avg_excess_peer_return_pct,
    peer_hit_rate_pct: row.peer_hit_rate_pct,
    worst_excess_peer_return_pct: row.worst_excess_peer_return_pct,
    best_excess_peer_return_pct: row.best_excess_peer_return_pct,
    edge_rating: rating,
    interpretation: interpretation(row.state, row.confirmation_status, rating),
  };
}

function rateEdge({ n, minN, avgExcess, peerHit, confirmationStatus, state }) {
  if (n < minN || avgExcess === null || peerHit === null) return "reject";

  if (confirmationStatus === "failed" && BEARISH_STATES.has(state)) {
    if (avgExcess >= 1.5 && peerHit >= 58) return "strong_contrarian_edge";
    if (avgExcess >= 0.75 && peerHit >= 52) return "watch_contrarian_edge";
  }

  if (confirmationStatus === "failed" && BULLISH_STATES.has(state)) {
    return "avoid_failed_bullish";
  }

  if (avgExcess >= 0.75 && peerHit >= 52) return "strong_edge";
  if (avgExcess >= 0.25 && peerHit >= 47) return "watch_edge";
  if (avgExcess >= 0.1 && peerHit >= 50) return "small_edge";
  if (avgExcess <= -0.5 && peerHit <= 40) return "negative_edge";
  return "reject";
}

function interpretation(state, confirmationStatus, rating) {
  if (rating === "strong_contrarian_edge") {
    return `${humanState(state)} failure has historically acted like a bullish reversal setup versus peers`;
  }
  if (rating === "watch_contrarian_edge") {
    return `${humanState(state)} failure is worth watching as a reversal candidate`;
  }
  if (rating === "avoid_failed_bullish") {
    return `failed bullish state has poor behavior; avoid treating it as accumulation`;
  }
  if (rating === "strong_edge") {
    return `${state} has strong peer-relative evidence in this sample`;
  }
  if (rating === "watch_edge") {
    return `${state} has positive peer-relative evidence but still needs context`;
  }
  if (rating === "small_edge") {
    return `${state} is slightly positive versus peers; not enough alone`;
  }
  if (rating === "negative_edge") {
    return `${state} has negative peer-relative behavior`;
  }
  return "not enough edge after filters";
}

function humanState(state) {
  return String(state).replace(/_/g, " ");
}

function compareCandidates(left, right) {
  const ratingRank = {
    strong_contrarian_edge: 5,
    strong_edge: 4,
    watch_contrarian_edge: 3,
    watch_edge: 2,
    small_edge: 1,
    negative_edge: 0,
    avoid_failed_bullish: -1,
  };
  const rankDiff = (ratingRank[right.edge_rating] ?? -2) - (ratingRank[left.edge_rating] ?? -2);
  if (rankDiff !== 0) return rankDiff;
  return (number(right.avg_excess_peer_return_pct) ?? -999) - (number(left.avg_excess_peer_return_pct) ?? -999);
}

function buildStateEdgeMap(stateOutcomes) {
  const result = new Map();
  for (const row of stateOutcomes) {
    if (row.horizon_days !== TARGET_HORIZON) continue;
    result.set(row.state, row);
  }
  return result;
}

function buildLatestWatchlist(stateRows, stateEdgeMap) {
  const latestDateBySymbol = new Map();
  for (const row of stateRows) {
    const date = row.date ?? "";
    const current = latestDateBySymbol.get(row.symbol);
    if (!current || date > current) latestDateBySymbol.set(row.symbol, date);
  }

  const latestRows = stateRows
    .filter((row) => latestDateBySymbol.get(row.symbol) === row.date)
    .sort((left, right) => {
      const bySymbol = String(left.symbol).localeCompare(String(right.symbol));
      if (bySymbol !== 0) return bySymbol;
      return (number(right.score) ?? 0) - (number(left.score) ?? 0);
    });

  return latestRows.map((row) => {
    const edge = stateEdgeMap.get(row.state);
    const avgExcess = edge?.avg_excess_peer_return_pct ?? "";
    const peerHit = edge?.peer_hit_rate_pct ?? "";
    return {
      symbol: row.symbol,
      date: row.date,
      state: row.state,
      score: row.score,
      confidence: row.confidence,
      confirmation_status: row.confirmation_status,
      historical_10d_avg_excess_peer_return_pct: avgExcess,
      historical_10d_peer_hit_rate_pct: peerHit,
      watch_read: watchRead(row, edge),
      invalidation_level: row.invalidation_level,
      positive_evidence: row.positive_evidence,
      negative_evidence: row.negative_evidence,
      quality_flags: row.quality_flags,
    };
  });
}

function watchRead(row, edge) {
  if (row.state === "no_clear_signal") return "no actionable psychology state";
  const avgExcess = number(edge?.avg_excess_peer_return_pct);
  const peerHit = number(edge?.peer_hit_rate_pct);
  const confirmation = row.confirmation_status;

  if (BEARISH_STATES.has(row.state) && confirmation === "unconfirmed") {
    return "bearish state present; strongest edge appears only if this bearish read fails next session";
  }
  if (BULLISH_STATES.has(row.state) && avgExcess !== null && avgExcess < 0) {
    return "bullish-looking state has weak peer-relative history; require stronger confirmation";
  }
  if (avgExcess !== null && avgExcess > 0.25 && peerHit !== null && peerHit >= 47) {
    return "historically positive versus peers, but still research-only";
  }
  return "watch, but no strong standalone edge yet";
}

function buildMarkdown(edgeCandidates, latestWatchlist) {
  const lines = [
    "# Experiment 09 Edge Candidate Report",
    "",
    "Research only. This report filters psychology states for peer-relative evidence.",
    "",
    "## Main Read",
    "",
    "- The strongest current lesson is contrarian: failed bearish states have better peer-relative behavior than simple bullish labels.",
    "- `accumulation` and `panic_absorption` still need stricter confirmation before they deserve trade-signal treatment.",
    "- State edges are measured against same-date hydro peers, not raw returns only.",
    "",
    "## Historical Edge Candidates",
    "",
    "| Type | State | Confirmation | N | Avg vs peer | Peer hit | Rating | Interpretation |",
    "|---|---|---|---:|---:|---:|---|---|",
  ];

  if (edgeCandidates.length === 0) {
    lines.push("| n/a | n/a | n/a | 0 | n/a | n/a | none | No state passed edge filters. |");
  } else {
    for (const row of edgeCandidates) {
      lines.push(
        `| ${row.candidate_type} | ${row.state} | ${row.confirmation_status} | ${row.n} | ` +
        `${row.avg_excess_peer_return_pct}% | ${row.peer_hit_rate_pct}% | ${row.edge_rating} | ${row.interpretation} |`,
      );
    }
  }

  lines.push(
    "",
    "## Latest Watchlist",
    "",
    "| Symbol | Date | State | Score | Confidence | Historical avg vs peer | Peer hit | Read |",
    "|---|---|---|---:|---:|---:|---:|---|",
  );
  for (const row of latestWatchlist) {
    lines.push(
      `| ${row.symbol} | ${row.date} | ${row.state} | ${row.score} | ${row.confidence} | ` +
      `${row.historical_10d_avg_excess_peer_return_pct || "n/a"}% | ${row.historical_10d_peer_hit_rate_pct || "n/a"}% | ${row.watch_read} |`,
    );
  }

  lines.push(
    "",
    "## How To Use",
    "",
    "- Treat strong contrarian edges as watch setups, not automatic entries.",
    "- For a bearish state, failure means the next session reclaims the invalidation level or refuses to follow lower.",
    "- For a bullish state, failure means support breaks; v2 says those failed bullish labels were dangerous.",
    "- The next upgrade should add all-hydro intraday tape coverage so latest watchlist reads are less daily-bar dependent.",
  );
  return `${lines.join("\n")}\n`;
}

function number(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
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
