import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const DAILY_PATH = path.join(DATA_DIR, "hydro_psychology_daily.csv");
const STATES_PATH = path.join(DATA_DIR, "psychology_states.csv");

const PATTERN_INSTANCES_PATH = path.join(DATA_DIR, "pattern_instances.csv");
const WALK_FORWARD_PREDICTIONS_PATH = path.join(RESULTS_DIR, "walk_forward_predictions.csv");
const PATTERN_EDGE_REPORT_PATH = path.join(RESULTS_DIR, "pattern_edge_report.csv");
const WALK_FORWARD_SUMMARY_PATH = path.join(RESULTS_DIR, "walk_forward_summary.csv");
const WALK_FORWARD_REPORT_PATH = path.join(RESULTS_DIR, "walk_forward_report.md");

const HORIZONS = ["1", "3", "5", "10", "20"];
const TARGET_HORIZON = "10";
const MIN_HISTORY_N = 20;
const BEARISH_STATES = new Set(["distribution", "failed_rally", "markdown_continuation", "panic_selling"]);
const BULLISH_STATES = new Set(["accumulation", "panic_absorption", "markup_continuation"]);
const CONFIRMATION_STATUSES = new Set(["confirmed", "failed", "mixed"]);

function main() {
  const dailyRows = readCsv(DAILY_PATH).filter((row) => row.symbol && row.date);
  const stateRows = readCsv(STATES_PATH).filter((row) => row.symbol && row.date);

  const dailyIndex = buildDailyIndex(dailyRows);
  const forwardOutcomes = buildForwardOutcomes(dailyRows);
  const instances = buildPatternInstances(stateRows, dailyIndex, forwardOutcomes);
  const { predictions, patternEdges, summaryRows } = runWalkForward(instances);

  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(PATTERN_INSTANCES_PATH, instances.map(flattenInstance));
  writeCsv(WALK_FORWARD_PREDICTIONS_PATH, predictions);
  writeCsv(PATTERN_EDGE_REPORT_PATH, patternEdges);
  writeCsv(WALK_FORWARD_SUMMARY_PATH, summaryRows);
  fs.writeFileSync(WALK_FORWARD_REPORT_PATH, buildMarkdownReport(instances, predictions, patternEdges, summaryRows), "utf8");

  console.log(`Wrote ${PATTERN_INSTANCES_PATH} (${instances.length} rows)`);
  console.log(`Wrote ${WALK_FORWARD_PREDICTIONS_PATH} (${predictions.length} rows)`);
  console.log(`Wrote ${PATTERN_EDGE_REPORT_PATH} (${patternEdges.length} rows)`);
  console.log(`Wrote ${WALK_FORWARD_SUMMARY_PATH} (${summaryRows.length} rows)`);
  console.log(`Wrote ${WALK_FORWARD_REPORT_PATH}`);
}

function buildPatternInstances(stateRows, dailyIndex, forwardOutcomes) {
  const instances = [];

  for (const stateRow of stateRows) {
    if (stateRow.state === "no_clear_signal") continue;

    const sameDay = makeInstance({
      row: stateRow,
      signalMode: "same_day_close",
      sourceDate: stateRow.date,
      signalDate: stateRow.date,
      confirmationStatus: "not_used",
      outcomeStartDate: stateRow.date,
      forwardOutcomes,
    });
    instances.push(sameDay);

    const confirmationStatus = String(stateRow.confirmation_status ?? "");
    if (!CONFIRMATION_STATUSES.has(confirmationStatus)) continue;

    const next = dailyIndex.nextByKey.get(key(stateRow.symbol, stateRow.date));
    if (!next) continue;

    instances.push(makeInstance({
      row: stateRow,
      signalMode: "next_session_confirmation",
      sourceDate: stateRow.date,
      signalDate: next.date,
      confirmationStatus,
      outcomeStartDate: next.date,
      forwardOutcomes,
    }));
  }

  return instances.sort(compareInstances);
}

function makeInstance({ row, signalMode, sourceDate, signalDate, confirmationStatus, outcomeStartDate, forwardOutcomes }) {
  const keys = buildPatternKeys(row, signalMode, confirmationStatus);
  const outcomes = {};
  for (const horizon of HORIZONS) {
    outcomes[horizon] = forwardOutcomes.get(key(row.symbol, outcomeStartDate, horizon)) ?? emptyOutcome();
  }

  return {
    symbol: row.symbol,
    state: row.state,
    score: row.score,
    confidence: row.confidence,
    source_date: sourceDate,
    signal_date: signalDate,
    signal_mode: signalMode,
    confirmation_status: confirmationStatus,
    pattern_family: keys.pattern_family,
    evidence_bucket: keys.evidence_bucket,
    quality_bucket: keys.quality_bucket,
    score_bucket: keys.score_bucket,
    specific_history_key: keys.specific,
    state_history_key: keys.state,
    family_history_key: keys.family,
    global_history_key: keys.global,
    invalidation_level: row.invalidation_level,
    positive_evidence: row.positive_evidence,
    negative_evidence: row.negative_evidence,
    quality_flags: row.quality_flags,
    outcomes,
  };
}

function runWalkForward(instances) {
  const history = new Map();
  const predictions = [];
  const byDate = groupBy(instances, (row) => row.signal_date);

  for (const signalDate of [...byDate.keys()].sort()) {
    const dateInstances = byDate.get(signalDate).sort(compareInstances);

    for (const instance of dateInstances) {
      for (const horizon of HORIZONS) {
        const picked = pickHistory(instance, horizon, history);
        predictions.push(buildPredictionRow(instance, horizon, picked));
      }
    }

    for (const instance of dateInstances) {
      for (const horizon of HORIZONS) {
        updateHistoryForInstance(history, instance, horizon);
      }
    }
  }

  const patternEdges = buildPatternEdges(instances);
  const summaryRows = buildWalkForwardSummary(predictions);
  return { predictions, patternEdges, summaryRows };
}

function buildPredictionRow(instance, horizon, picked) {
  const outcome = instance.outcomes[horizon] ?? emptyOutcome();
  const edge = classifyEdge(picked);
  const forecastResult = gradeForecast(edge.forecast_bias, outcome.excess_peer_return_pct);

  return {
    symbol: instance.symbol,
    source_date: instance.source_date,
    signal_date: instance.signal_date,
    signal_mode: instance.signal_mode,
    state: instance.state,
    confirmation_status: instance.confirmation_status,
    pattern_family: instance.pattern_family,
    horizon_days: horizon,
    history_level: picked.history_level,
    history_key: picked.history_key,
    history_n: picked.n,
    expected_raw_return_pct: format(picked.avg_raw_return_pct),
    expected_excess_peer_return_pct: format(picked.avg_excess_peer_return_pct),
    historical_raw_hit_rate_pct: format(picked.raw_hit_rate_pct),
    historical_peer_hit_rate_pct: format(picked.peer_hit_rate_pct),
    forecast_action: edge.forecast_action,
    forecast_bias: edge.forecast_bias,
    forecast_confidence: forecastConfidence(picked, instance, edge),
    actual_outcome_date: outcome.outcome_date,
    actual_raw_return_pct: format(outcome.raw_return_pct),
    actual_excess_peer_return_pct: format(outcome.excess_peer_return_pct),
    forecast_result: forecastResult,
    invalidation_level: instance.invalidation_level,
    evidence_bucket: instance.evidence_bucket,
    quality_bucket: instance.quality_bucket,
    quality_flags: instance.quality_flags,
  };
}

function pickHistory(instance, horizon, history) {
  let bestLowSample = null;

  for (const item of historyKeys(instance)) {
    const stats = history.get(statsKey(item.key, horizon));
    if (!stats || stats.n === 0) continue;

    const snapshot = statsSnapshot(stats);
    const candidate = {
      ...snapshot,
      history_level: item.level,
      history_key: item.key,
      history_is_min_sample: snapshot.n >= MIN_HISTORY_N ? "1" : "0",
    };

    if (snapshot.n >= MIN_HISTORY_N) return candidate;
    if (!bestLowSample || snapshot.n > bestLowSample.n) bestLowSample = candidate;
  }

  return bestLowSample ?? {
    history_level: "none",
    history_key: "",
    history_is_min_sample: "0",
    n: 0,
    avg_raw_return_pct: null,
    avg_excess_peer_return_pct: null,
    raw_hit_rate_pct: null,
    peer_hit_rate_pct: null,
    worst_excess_peer_return_pct: null,
    best_excess_peer_return_pct: null,
  };
}

function updateHistoryForInstance(history, instance, horizon) {
  const outcome = instance.outcomes[horizon] ?? emptyOutcome();
  if (outcome.raw_return_pct === null || outcome.excess_peer_return_pct === null) return;

  for (const item of historyKeys(instance)) {
    const mapKey = statsKey(item.key, horizon);
    if (!history.has(mapKey)) {
      history.set(mapKey, emptyStats(item.key, item.level, instance.signal_mode, horizon));
    }
    updateStats(history.get(mapKey), outcome);
  }
}

function buildPatternEdges(instances) {
  const aggregate = new Map();

  for (const instance of instances) {
    for (const horizon of HORIZONS) {
      const outcome = instance.outcomes[horizon] ?? emptyOutcome();
      if (outcome.raw_return_pct === null || outcome.excess_peer_return_pct === null) continue;

      for (const item of historyKeys(instance)) {
        const mapKey = statsKey(item.key, horizon);
        if (!aggregate.has(mapKey)) {
          aggregate.set(mapKey, emptyStats(item.key, item.level, instance.signal_mode, horizon));
        }
        updateStats(aggregate.get(mapKey), outcome);
      }
    }
  }

  return [...aggregate.values()]
    .map((stats) => {
      const row = statsSnapshot(stats);
      const edge = classifyEdge(row);
      return {
        signal_mode: stats.signal_mode,
        history_level: stats.history_level,
        history_key: stats.history_key,
        horizon_days: stats.horizon_days,
        n: row.n,
        avg_raw_return_pct: format(row.avg_raw_return_pct),
        avg_excess_peer_return_pct: format(row.avg_excess_peer_return_pct),
        raw_hit_rate_pct: format(row.raw_hit_rate_pct),
        peer_hit_rate_pct: format(row.peer_hit_rate_pct),
        worst_excess_peer_return_pct: format(row.worst_excess_peer_return_pct),
        best_excess_peer_return_pct: format(row.best_excess_peer_return_pct),
        edge_rating: edge.forecast_action,
        forecast_bias: edge.forecast_bias,
      };
    })
    .sort(compareEdgeRows);
}

function buildWalkForwardSummary(predictions) {
  const groups = new Map();

  for (const prediction of predictions) {
    if (!["hit", "miss"].includes(prediction.forecast_result)) continue;
    const groupKey = [
      prediction.signal_mode,
      prediction.horizon_days,
      prediction.forecast_action,
      prediction.forecast_bias,
      prediction.history_level,
    ].join("|");
    if (!groups.has(groupKey)) groups.set(groupKey, []);
    groups.get(groupKey).push(prediction);
  }

  return [...groups.entries()].map(([groupKey, rows]) => {
    const [signalMode, horizonDays, forecastAction, forecastBias, historyLevel] = groupKey.split("|");
    const actualExcess = rows.map((row) => number(row.actual_excess_peer_return_pct)).filter((value) => value !== null);
    const expectedExcess = rows.map((row) => number(row.expected_excess_peer_return_pct)).filter((value) => value !== null);
    return {
      signal_mode: signalMode,
      horizon_days: horizonDays,
      forecast_action: forecastAction,
      forecast_bias: forecastBias,
      history_level: historyLevel,
      n_scored: rows.length,
      hit_rate_pct: format(rows.filter((row) => row.forecast_result === "hit").length / rows.length * 100),
      avg_actual_excess_peer_return_pct: format(average(actualExcess)),
      median_actual_excess_peer_return_pct: format(median(actualExcess)),
      avg_expected_excess_peer_return_pct: format(average(expectedExcess)),
    };
  }).sort((left, right) => {
    const byHorizon = Number(left.horizon_days) - Number(right.horizon_days);
    if (byHorizon !== 0) return byHorizon;
    return (number(right.hit_rate_pct) ?? 0) - (number(left.hit_rate_pct) ?? 0);
  });
}

function buildForwardOutcomes(dailyRows) {
  const bySymbol = groupBy(dailyRows, (row) => row.symbol);
  const rawOutcomes = new Map();
  const groupedByDateHorizon = new Map();

  for (const [symbol, rows] of bySymbol.entries()) {
    const ordered = rows.slice().sort((left, right) => String(left.date).localeCompare(String(right.date)));
    for (let index = 0; index < ordered.length; index += 1) {
      const row = ordered[index];
      const startClose = number(row.close);
      if (startClose === null || startClose === 0) continue;

      for (const horizon of HORIZONS) {
        const target = ordered[index + Number(horizon)];
        const targetClose = number(target?.close);
        if (!target || targetClose === null) continue;

        const rawReturn = (targetClose - startClose) / startClose * 100;
        const item = {
          symbol,
          date: row.date,
          horizon,
          outcome_date: target.date,
          raw_return_pct: rawReturn,
        };
        rawOutcomes.set(key(symbol, row.date, horizon), item);

        const groupKey = key(row.date, horizon);
        if (!groupedByDateHorizon.has(groupKey)) groupedByDateHorizon.set(groupKey, []);
        groupedByDateHorizon.get(groupKey).push(item);
      }
    }
  }

  const result = new Map();
  for (const [rawKey, item] of rawOutcomes.entries()) {
    const peers = (groupedByDateHorizon.get(key(item.date, item.horizon)) ?? [])
      .filter((peer) => peer.symbol !== item.symbol)
      .map((peer) => peer.raw_return_pct);
    const peerAvg = average(peers);
    result.set(rawKey, {
      ...item,
      peer_return_pct: peerAvg,
      excess_peer_return_pct: peerAvg === null ? null : item.raw_return_pct - peerAvg,
      peer_count: peers.length,
    });
  }
  return result;
}

function buildDailyIndex(dailyRows) {
  const bySymbol = groupBy(dailyRows, (row) => row.symbol);
  const byKey = new Map();
  const nextByKey = new Map();

  for (const [symbol, rows] of bySymbol.entries()) {
    const ordered = rows.slice().sort((left, right) => String(left.date).localeCompare(String(right.date)));
    for (let index = 0; index < ordered.length; index += 1) {
      const row = ordered[index];
      byKey.set(key(symbol, row.date), row);
      if (ordered[index + 1]) nextByKey.set(key(symbol, row.date), ordered[index + 1]);
    }
  }

  return { byKey, nextByKey };
}

function buildPatternKeys(row, signalMode, confirmationStatus) {
  const state = row.state;
  const patternFamily = familyFor(state);
  const scoreBucket = scoreBucketFor(row.score);
  const qualityBucket = qualityBucketFor(row.quality_flags);
  const evidenceBucket = evidenceBucketFor(row);
  const confirmationToken = signalMode === "next_session_confirmation"
    ? `confirmation=${confirmationStatus}`
    : "confirmation=not_used";

  return {
    pattern_family: patternFamily,
    score_bucket: scoreBucket,
    quality_bucket: qualityBucket,
    evidence_bucket: evidenceBucket,
    specific: [
      `mode=${signalMode}`,
      `state=${state}`,
      confirmationToken,
      `score=${scoreBucket}`,
      `quality=${qualityBucket}`,
      `evidence=${evidenceBucket}`,
    ].join("|"),
    state: [`mode=${signalMode}`, `state=${state}`, confirmationToken].join("|"),
    family: [`mode=${signalMode}`, `family=${patternFamily}`, confirmationToken].join("|"),
    global: `mode=${signalMode}|all`,
  };
}

function historyKeys(instance) {
  return [
    { level: "specific", key: instance.specific_history_key },
    { level: "state", key: instance.state_history_key },
    { level: "family", key: instance.family_history_key },
    { level: "global", key: instance.global_history_key },
  ];
}

function familyFor(state) {
  if (BEARISH_STATES.has(state)) return "bearish_pressure";
  if (BULLISH_STATES.has(state)) return "bullish_defense";
  if (state === "two_sided_churn") return "churn";
  return "other";
}

function scoreBucketFor(value) {
  const score = number(value) ?? 0;
  if (score >= 6) return "very_high";
  if (score >= 4) return "high";
  if (score >= 3) return "base";
  return "low";
}

function qualityBucketFor(flagsText) {
  const flags = new Set(String(flagsText ?? "").split("|").filter(Boolean));
  const parts = [];
  if (flags.has("missing_broker_flow")) parts.push("no_broker");
  if (flags.has("missing_intraday_volume")) parts.push("no_tape");
  if (flags.has("event_window") || flags.has("lockin_window") || flags.has("nrb_event_window") || flags.has("flood_damage_window")) {
    parts.push("event_risk");
  }
  return parts.length ? parts.join("+") : "clean";
}

function evidenceBucketFor(row) {
  const evidence = `${row.positive_evidence ?? ""}|${row.negative_evidence ?? ""}`.toLowerCase();

  if (evidence.includes("seller broker persistence") && evidence.includes("supply_pressure")) return "persistent_supply";
  if (evidence.includes("buyer broker persistence") && evidence.includes("absorption")) return "persistent_absorption";
  if (evidence.includes("buyer broker persistence")) return "buyer_persistence";
  if (evidence.includes("seller broker persistence")) return "seller_persistence";
  if (evidence.includes("high_volume_down")) return "high_volume_down";
  if (evidence.includes("high_volume_up")) return "high_volume_up";
  if (evidence.includes("weak close")) return "weak_close";
  if (evidence.includes("support")) return "support_defense";
  return "general";
}

function classifyEdge(stats) {
  const n = number(stats.n) ?? 0;
  const avgExcess = number(stats.avg_excess_peer_return_pct);
  const peerHit = number(stats.peer_hit_rate_pct);

  if (n < MIN_HISTORY_N || avgExcess === null || peerHit === null) {
    return { forecast_action: "insufficient_history", forecast_bias: "insufficient" };
  }
  if (avgExcess >= 1.25 && peerHit >= 57) {
    return { forecast_action: "strong_outperform_watch", forecast_bias: "outperform" };
  }
  if (avgExcess >= 0.35 && peerHit >= 52) {
    return { forecast_action: "outperform_watch", forecast_bias: "outperform" };
  }
  if (avgExcess <= -1.0 && peerHit <= 43) {
    return { forecast_action: "strong_underperform_avoid", forecast_bias: "underperform" };
  }
  if (avgExcess <= -0.35 && peerHit <= 46) {
    return { forecast_action: "underperform_avoid", forecast_bias: "underperform" };
  }
  return { forecast_action: "no_edge", forecast_bias: "neutral" };
}

function forecastConfidence(stats, instance, edge) {
  const n = number(stats.n) ?? 0;
  if (n === 0 || edge.forecast_bias === "insufficient") return "0.05";

  const avgExcess = Math.abs(number(stats.avg_excess_peer_return_pct) ?? 0);
  const peerHit = number(stats.peer_hit_rate_pct) ?? 50;
  let value = 0.2;
  value += Math.min(0.25, Math.log10(Math.max(n, 1)) * 0.12);
  value += Math.min(0.2, avgExcess / 8);
  value += Math.min(0.15, Math.abs(peerHit - 50) / 100);

  if (stats.history_level === "specific") value += 0.05;
  if (stats.history_level === "family") value -= 0.04;
  if (stats.history_level === "global") value -= 0.08;
  if (String(instance.quality_bucket).includes("no_broker")) value -= 0.08;
  if (String(instance.quality_bucket).includes("no_tape")) value -= 0.04;
  if (String(instance.quality_bucket).includes("event_risk")) value -= 0.04;

  return Math.max(0.05, Math.min(0.85, value)).toFixed(2);
}

function gradeForecast(bias, actualExcess) {
  const actual = number(actualExcess);
  if (actual === null) return "pending";
  if (bias === "outperform") return actual > 0 ? "hit" : "miss";
  if (bias === "underperform") return actual < 0 ? "hit" : "miss";
  return "not_scored";
}

function flattenInstance(instance) {
  const row = {
    symbol: instance.symbol,
    source_date: instance.source_date,
    signal_date: instance.signal_date,
    signal_mode: instance.signal_mode,
    state: instance.state,
    confirmation_status: instance.confirmation_status,
    score: instance.score,
    confidence: instance.confidence,
    pattern_family: instance.pattern_family,
    score_bucket: instance.score_bucket,
    quality_bucket: instance.quality_bucket,
    evidence_bucket: instance.evidence_bucket,
    specific_history_key: instance.specific_history_key,
    state_history_key: instance.state_history_key,
    family_history_key: instance.family_history_key,
    global_history_key: instance.global_history_key,
    invalidation_level: instance.invalidation_level,
    positive_evidence: instance.positive_evidence,
    negative_evidence: instance.negative_evidence,
    quality_flags: instance.quality_flags,
  };

  for (const horizon of HORIZONS) {
    const outcome = instance.outcomes[horizon] ?? emptyOutcome();
    row[`outcome_${horizon}d_date`] = outcome.outcome_date;
    row[`actual_${horizon}d_return_pct`] = format(outcome.raw_return_pct);
    row[`actual_${horizon}d_excess_peer_return_pct`] = format(outcome.excess_peer_return_pct);
  }

  return row;
}

function buildMarkdownReport(instances, predictions, patternEdges, summaryRows) {
  const scored = predictions.filter((row) => ["hit", "miss"].includes(row.forecast_result));
  const hits = scored.filter((row) => row.forecast_result === "hit").length;
  const latestDate = instances.reduce((latest, row) => row.signal_date > latest ? row.signal_date : latest, "");
  const topEdges = patternEdges
    .filter((row) => row.horizon_days === TARGET_HORIZON && row.history_level !== "global" && row.n >= MIN_HISTORY_N)
    .slice(0, 10);
  const targetSummary = summaryRows
    .filter((row) => row.horizon_days === TARGET_HORIZON)
    .slice(0, 12);

  const lines = [
    "# Experiment 09.1 Walk-Forward Psychology Backtest",
    "",
    "Research only. This report tests whether psychology patterns had repeatable forward behavior without using future rows to make each historical forecast.",
    "",
    "## Guardrail",
    "",
    "- Same-day close signals only use the state visible on that same date.",
    "- Next-session confirmation signals are dated on the confirmation day, and their outcome starts after that day.",
    "- Rows with insufficient history are recorded, but they are not treated as scored predictions.",
    "",
    "## Run Summary",
    "",
    `- pattern instances: ${instances.length}`,
    `- walk-forward prediction rows: ${predictions.length}`,
    `- scored hit/miss rows: ${scored.length}`,
    `- scored hit rate: ${scored.length ? format(hits / scored.length * 100) : "n/a"}%`,
    `- latest signal date in local data: ${latestDate || "n/a"}`,
    "",
    "## Strongest Pattern Library Rows",
    "",
    "| Mode | Level | Horizon | N | Avg vs peer | Peer hit | Edge | Key |",
    "|---|---|---:|---:|---:|---:|---|---|",
  ];

  if (topEdges.length === 0) {
    lines.push("| n/a | n/a | n/a | 0 | n/a | n/a | none | No pattern passed the minimum history filter. |");
  } else {
    for (const row of topEdges) {
      lines.push(
        `| ${row.signal_mode} | ${row.history_level} | ${row.horizon_days} | ${row.n} | ` +
        `${row.avg_excess_peer_return_pct}% | ${row.peer_hit_rate_pct}% | ${row.edge_rating} | ${escapePipes(row.history_key)} |`,
      );
    }
  }

  lines.push(
    "",
    "## Walk-Forward Scored Summary",
    "",
    "| Mode | Horizon | Action | Bias | Level | N | Hit rate | Avg actual vs peer |",
    "|---|---:|---|---|---|---:|---:|---:|",
  );

  if (targetSummary.length === 0) {
    lines.push("| n/a | n/a | n/a | n/a | n/a | 0 | n/a | n/a |");
  } else {
    for (const row of targetSummary) {
      lines.push(
        `| ${row.signal_mode} | ${row.horizon_days} | ${row.forecast_action} | ${row.forecast_bias} | ` +
        `${row.history_level} | ${row.n_scored} | ${row.hit_rate_pct}% | ${row.avg_actual_excess_peer_return_pct}% |`,
      );
    }
  }

  lines.push(
    "",
    "## How To Read This",
    "",
    "- `pattern_edge_report.csv` is the pattern library.",
    "- `walk_forward_predictions.csv` is the honest historical forecast ledger.",
    "- `latest_forecast.csv` is generated separately from the same pattern keys for the newest completed session.",
    "- A forecast can help only when it has enough prior examples and the latest row has acceptable data quality.",
  );

  return `${lines.join("\n")}\n`;
}

function emptyOutcome() {
  return {
    outcome_date: "",
    raw_return_pct: null,
    peer_return_pct: null,
    excess_peer_return_pct: null,
    peer_count: 0,
  };
}

function emptyStats(historyKey, historyLevel, signalMode, horizonDays) {
  return {
    history_key: historyKey,
    history_level: historyLevel,
    signal_mode: signalMode,
    horizon_days: horizonDays,
    n: 0,
    sum_raw: 0,
    sum_excess: 0,
    raw_hits: 0,
    peer_hits: 0,
    worst_excess: null,
    best_excess: null,
  };
}

function updateStats(stats, outcome) {
  const raw = number(outcome.raw_return_pct);
  const excess = number(outcome.excess_peer_return_pct);
  if (raw === null || excess === null) return;

  stats.n += 1;
  stats.sum_raw += raw;
  stats.sum_excess += excess;
  if (raw > 0) stats.raw_hits += 1;
  if (excess > 0) stats.peer_hits += 1;
  stats.worst_excess = stats.worst_excess === null ? excess : Math.min(stats.worst_excess, excess);
  stats.best_excess = stats.best_excess === null ? excess : Math.max(stats.best_excess, excess);
}

function statsSnapshot(stats) {
  if (!stats || stats.n === 0) {
    return {
      n: 0,
      avg_raw_return_pct: null,
      avg_excess_peer_return_pct: null,
      raw_hit_rate_pct: null,
      peer_hit_rate_pct: null,
      worst_excess_peer_return_pct: null,
      best_excess_peer_return_pct: null,
    };
  }
  return {
    n: stats.n,
    avg_raw_return_pct: stats.sum_raw / stats.n,
    avg_excess_peer_return_pct: stats.sum_excess / stats.n,
    raw_hit_rate_pct: stats.raw_hits / stats.n * 100,
    peer_hit_rate_pct: stats.peer_hits / stats.n * 100,
    worst_excess_peer_return_pct: stats.worst_excess,
    best_excess_peer_return_pct: stats.best_excess,
  };
}

function statsKey(historyKey, horizon) {
  return JSON.stringify([historyKey, horizon]);
}

function compareInstances(left, right) {
  const bySignalDate = String(left.signal_date).localeCompare(String(right.signal_date));
  if (bySignalDate !== 0) return bySignalDate;
  const bySymbol = String(left.symbol).localeCompare(String(right.symbol));
  if (bySymbol !== 0) return bySymbol;
  const byMode = String(left.signal_mode).localeCompare(String(right.signal_mode));
  if (byMode !== 0) return byMode;
  return String(left.state).localeCompare(String(right.state));
}

function compareEdgeRows(left, right) {
  const rank = {
    strong_outperform_watch: 5,
    outperform_watch: 4,
    no_edge: 2,
    insufficient_history: 1,
    underperform_avoid: 0,
    strong_underperform_avoid: -1,
  };
  const byRating = (rank[right.edge_rating] ?? -2) - (rank[left.edge_rating] ?? -2);
  if (byRating !== 0) return byRating;
  const byHorizon = Number(left.horizon_days) - Number(right.horizon_days);
  if (byHorizon !== 0) return byHorizon;
  const byN = Number(right.n) - Number(left.n);
  if (byN !== 0) return byN;
  return String(left.history_key).localeCompare(String(right.history_key));
}

function groupBy(rows, keyFn) {
  const result = new Map();
  for (const row of rows) {
    const groupKey = keyFn(row);
    if (!result.has(groupKey)) result.set(groupKey, []);
    result.get(groupKey).push(row);
  }
  return result;
}

function average(values) {
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function median(values) {
  if (!values.length) return null;
  const sorted = values.slice().sort((left, right) => left - right);
  const middle = Math.floor(sorted.length / 2);
  if (sorted.length % 2) return sorted[middle];
  return (sorted[middle - 1] + sorted[middle]) / 2;
}

function number(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

function format(value, digits = 4) {
  const parsed = number(value);
  return parsed === null ? "" : parsed.toFixed(digits);
}

function key(...parts) {
  return parts.join("|");
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
