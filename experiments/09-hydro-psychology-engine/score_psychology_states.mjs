import fs from "node:fs";
import path from "node:path";
import { fileURLToPath } from "node:url";

const SCRIPT_DIR = path.dirname(fileURLToPath(import.meta.url));
const DATA_DIR = path.join(SCRIPT_DIR, "data");
const RESULTS_DIR = path.join(SCRIPT_DIR, "results");

const INPUT_PATH = path.join(DATA_DIR, "hydro_psychology_daily.csv");
const STATES_PATH = path.join(DATA_DIR, "psychology_states.csv");
const OUTCOMES_PATH = path.join(RESULTS_DIR, "state_outcomes.csv");
const CONFIRMATION_OUTCOMES_PATH = path.join(RESULTS_DIR, "state_confirmation_outcomes.csv");
const FINDINGS_PATH = path.join(RESULTS_DIR, "psychology_findings.md");

const HORIZONS = ["1", "3", "5", "10"];
const MIN_STATE_SCORE = 3;

function main() {
  const rows = readCsv(INPUT_PATH);
  const rowContext = buildRowContext(rows);
  const peerBenchmarks = buildPeerBenchmarks(rows);
  const stateRows = [];

  for (const row of rows) {
    const context = rowContext.get(rowKey(row)) ?? {};
    const candidates = scoreRow(row, context)
      .filter((state) => state.score >= MIN_STATE_SCORE)
      .sort((left, right) => right.score - left.score || left.state.localeCompare(right.state));

    if (candidates.length === 0) {
      stateRows.push(noClearSignal(row));
      continue;
    }

    for (const candidate of candidates) {
      const confirmation = confirmationFor(candidate.state, row, context);
      stateRows.push({
        symbol: row.symbol,
        date: row.date,
        state: candidate.state,
        score: candidate.score,
        confidence: confidence(candidate.score, row.quality_flags),
        evidence_count: candidate.positive.length + candidate.negative.length,
        positive_evidence: candidate.positive.join("|"),
        negative_evidence: candidate.negative.join("|"),
        invalidation_level: invalidation(candidate.state, row),
        confirmation_status: confirmation.status,
        confirmation_evidence: confirmation.evidence,
        expected_horizon: expectedHorizon(candidate.state),
        quality_flags: row.quality_flags ?? "",
        fwd_1d_return_pct: row.fwd_1d_return_pct ?? "",
        fwd_3d_return_pct: row.fwd_3d_return_pct ?? "",
        fwd_5d_return_pct: row.fwd_5d_return_pct ?? "",
        fwd_10d_return_pct: row.fwd_10d_return_pct ?? "",
      });
    }
  }
  decoratePeerRelative(stateRows, peerBenchmarks);

  fs.mkdirSync(DATA_DIR, { recursive: true });
  fs.mkdirSync(RESULTS_DIR, { recursive: true });
  writeCsv(STATES_PATH, stateRows);

  const outcomeRows = buildOutcomes(stateRows);
  const confirmationOutcomeRows = buildConfirmationOutcomes(stateRows);
  writeCsv(OUTCOMES_PATH, outcomeRows);
  writeCsv(CONFIRMATION_OUTCOMES_PATH, confirmationOutcomeRows);
  fs.writeFileSync(FINDINGS_PATH, buildFindings(stateRows, outcomeRows, confirmationOutcomeRows), "utf8");

  console.log(`Wrote ${STATES_PATH} (${stateRows.length} rows)`);
  console.log(`Wrote ${OUTCOMES_PATH} (${outcomeRows.length} rows)`);
  console.log(`Wrote ${CONFIRMATION_OUTCOMES_PATH} (${confirmationOutcomeRows.length} rows)`);
  console.log(`Wrote ${FINDINGS_PATH}`);
}

function scoreRow(row, context = {}) {
  const ret = number(row.return_pct);
  const closePos = number(row.close_position);
  const volumeRatio = number(row.volume_ratio_20d);
  const brokerRowsRatio = number(row.broker_rows_ratio_20d);
  const buyerTop3 = number(row.top3_buyer_pct);
  const sellerTop3 = number(row.top3_seller_pct);
  const top3Gap = number(row.buyer_seller_top3_gap);
  const sameBrokerPct = number(row.same_broker_pct);

  const highVolume = volumeRatio !== null && volumeRatio >= 1.5;
  const brokerSpike = brokerRowsRatio !== null && brokerRowsRatio >= 1.5;
  const buyerConcentrated = flag(row.buyer_concentrated) || (buyerTop3 !== null && buyerTop3 >= 25);
  const sellerConcentrated = flag(row.seller_concentrated) || (sellerTop3 !== null && sellerTop3 >= 25);
  const eventRisk = flag(row.corp_action_window) || flag(row.lockin_window) || flag(row.flood_damage_window);
  const missingBroker = String(row.broker_available ?? "").trim() !== "1";
  const buyPersistence = brokerPersistence(row, context.prevRows ?? [], "buy");
  const sellPersistence = brokerPersistence(row, context.prevRows ?? [], "sell");
  const supportHold = sameDaySupportHold(row, context.prevRows ?? []);
  const volumeDryupAfterPanic = dryupAfterPanic(row, context.prev1);
  const strongBuyerEvidence = buyerConcentrated || buyPersistence.persisted;
  const strongSellerEvidence = sellerConcentrated || sellPersistence.persisted;

  const states = [
    emptyState("accumulation"),
    emptyState("distribution"),
    emptyState("panic_selling"),
    emptyState("panic_absorption"),
    emptyState("failed_rally"),
    emptyState("two_sided_churn"),
    emptyState("markup_continuation"),
    emptyState("markdown_continuation"),
  ];
  const byName = new Map(states.map((state) => [state.state, state]));

  add(byName, "accumulation", flag(row.accumulation_like) && strongBuyerEvidence, 2, "experiment_07 accumulation_like with buyer evidence");
  add(byName, "accumulation", flag(row.absorption_attempt) && strongBuyerEvidence, 1, "absorption_attempt supports buyer defense");
  add(byName, "accumulation", buyPersistence.persisted, 2, `buyer broker persistence ${buyPersistence.brokers.join("/")}`);
  add(byName, "accumulation", buyerConcentrated && top3Gap !== null && top3Gap >= 3, 1, "buyer concentration exceeds seller concentration");
  add(byName, "accumulation", supportHold && ret !== null && ret >= -0.5, 1, "support held with constructive close");
  add(byName, "accumulation", volumeDryupAfterPanic, 1, "volume dried up after panic pressure");
  add(byName, "accumulation", volumeRatio !== null && volumeRatio >= 0.8 && volumeRatio <= 1.3 && closePos !== null && closePos >= 0.6 && strongBuyerEvidence, 1, "controlled volume with buyer-backed constructive close");
  subtract(byName, "accumulation", flag(row.supply_pressure), 2, "supply_pressure conflicts with clean accumulation");
  subtract(byName, "accumulation", flag(row.distribution_like), 1, "distribution_like conflicts with accumulation");
  subtract(byName, "accumulation", sellPersistence.persisted, 2, `seller broker persistence ${sellPersistence.brokers.join("/")}`);
  subtract(byName, "accumulation", eventRisk, 2, "event window can distort accumulation read");
  subtract(byName, "accumulation", missingBroker, 2, "missing broker flow blocks strong accumulation read");

  add(byName, "distribution", flag(row.distribution_like) && strongSellerEvidence, 2, "experiment_07 distribution_like with seller evidence");
  add(byName, "distribution", flag(row.supply_pressure), 2, "supply_pressure");
  add(byName, "distribution", sellPersistence.persisted, 2, `seller broker persistence ${sellPersistence.brokers.join("/")}`);
  add(byName, "distribution", sellerConcentrated && top3Gap !== null && top3Gap <= -3, 1, "seller concentration exceeds buyer concentration");
  add(byName, "distribution", flag(row.high_volume_down), 1, "high_volume_down");
  add(byName, "distribution", closePos !== null && closePos <= 0.4, 1, "weak close position");
  add(byName, "distribution", flag(row.lockin_window), 1, "lock-in window adds supply context");
  subtract(byName, "distribution", flag(row.absorption_attempt), 1, "absorption_attempt weakens distribution read");
  subtract(byName, "distribution", buyPersistence.persisted, 1, `buyer broker persistence ${buyPersistence.brokers.join("/")}`);

  add(byName, "panic_selling", ret !== null && ret <= -3, 2, "large negative return");
  add(byName, "panic_selling", flag(row.high_volume_down), 2, "high_volume_down");
  add(byName, "panic_selling", closePos !== null && closePos <= 0.25, 1, "close near low of range");
  add(byName, "panic_selling", sellerConcentrated, 1, "seller concentration");
  add(byName, "panic_selling", flag(row.nrb_event_window), 1, "macro/liquidity event window");
  subtract(byName, "panic_selling", closePos !== null && closePos >= 0.55, 1, "close recovered from lows");
  subtract(byName, "panic_selling", flag(row.absorption_attempt), 1, "absorption_attempt conflicts with pure panic");

  add(byName, "panic_absorption", flag(row.absorption_attempt) && strongBuyerEvidence, 2, "absorption_attempt with buyer evidence");
  add(byName, "panic_absorption", ret !== null && ret <= 0 && closePos !== null && closePos >= 0.6 && volumeRatio !== null && volumeRatio >= 1 && strongBuyerEvidence, 2, "down/flat day recovered into upper range on volume with buyer evidence");
  add(byName, "panic_absorption", buyPersistence.persisted, 2, `buyer broker persistence ${buyPersistence.brokers.join("/")}`);
  add(byName, "panic_absorption", buyerConcentrated && sellerConcentrated && top3Gap !== null && top3Gap >= -2, 1, "two-sided concentration with buyers not overwhelmed");
  add(byName, "panic_absorption", supportHold, 1, "same-day support hold");
  add(byName, "panic_absorption", flag(row.tape_absorption_candle), 1, "tape absorption candle");
  subtract(byName, "panic_absorption", closePos !== null && closePos <= 0.4, 2, "weak close undermines absorption");
  subtract(byName, "panic_absorption", flag(row.distribution_like), 1, "distribution_like conflicts with absorption");
  subtract(byName, "panic_absorption", sellPersistence.persisted, 2, `seller broker persistence ${sellPersistence.brokers.join("/")}`);
  subtract(byName, "panic_absorption", missingBroker, 1, "missing broker flow weakens absorption read");
  subtract(byName, "panic_absorption", eventRisk, 1, "event window can distort absorption read");

  add(byName, "failed_rally", flag(row.failed_rally_candidate), 2, "experiment_07 failed_rally_candidate");
  add(byName, "failed_rally", flag(row.tape_failed_rally), 2, "tape failed_rally");
  add(byName, "failed_rally", ret !== null && ret >= 1 && closePos !== null && closePos < 0.75 && (highVolume || brokerSpike), 1, "rally had activity but did not close near high");
  add(byName, "failed_rally", strongSellerEvidence, 1, "seller concentration or persistence appeared");
  subtract(byName, "failed_rally", closePos !== null && closePos >= 0.85, 1, "strong close weakens failed rally read");

  add(byName, "two_sided_churn", flag(row.two_sided_churn), 2, "experiment_07 two_sided_churn");
  add(byName, "two_sided_churn", buyerConcentrated && sellerConcentrated, 1, "buyer and seller concentration both high");
  add(byName, "two_sided_churn", ret !== null && Math.abs(ret) <= 1 && (highVolume || brokerSpike), 1, "high activity with limited price progress");
  add(byName, "two_sided_churn", sameBrokerPct !== null && sameBrokerPct >= 5, 1, "same-broker activity elevated");

  add(byName, "markup_continuation", flag(row.high_volume_up) && closePos !== null && closePos >= 0.7, 2, "high_volume_up with strong close");
  add(byName, "markup_continuation", flag(row.accumulation_like) && strongBuyerEvidence, 1, "accumulation_like supports continuation");
  add(byName, "markup_continuation", buyPersistence.persisted, 1, `buyer broker persistence ${buyPersistence.brokers.join("/")}`);
  add(byName, "markup_continuation", top3Gap !== null && top3Gap >= 3, 1, "buyer/seller top3 gap positive");
  subtract(byName, "markup_continuation", flag(row.failed_rally_candidate), 2, "failed_rally_candidate blocks markup read");
  subtract(byName, "markup_continuation", eventRisk, 1, "event window can distort markup read");

  add(byName, "markdown_continuation", flag(row.high_volume_down) && closePos !== null && closePos <= 0.35, 2, "high_volume_down with weak close");
  add(byName, "markdown_continuation", flag(row.distribution_like) && strongSellerEvidence, 1, "distribution_like supports continuation lower");
  add(byName, "markdown_continuation", sellPersistence.persisted, 1, `seller broker persistence ${sellPersistence.brokers.join("/")}`);
  add(byName, "markdown_continuation", flag(row.supply_pressure), 1, "supply_pressure");
  subtract(byName, "markdown_continuation", flag(row.absorption_attempt), 2, "absorption_attempt blocks markdown read");
  subtract(byName, "markdown_continuation", buyPersistence.persisted, 1, `buyer broker persistence ${buyPersistence.brokers.join("/")}`);

  return states;
}

function emptyState(state) {
  return { state, score: 0, positive: [], negative: [] };
}

function add(map, state, condition, points, evidence) {
  if (!condition) return;
  const item = map.get(state);
  item.score += points;
  item.positive.push(`+${points}:${evidence}`);
}

function subtract(map, state, condition, points, evidence) {
  if (!condition) return;
  const item = map.get(state);
  item.score -= points;
  item.negative.push(`-${points}:${evidence}`);
}

function noClearSignal(row) {
  return {
    symbol: row.symbol,
    date: row.date,
    state: "no_clear_signal",
    score: 0,
    confidence: confidence(0, row.quality_flags),
    evidence_count: 0,
    positive_evidence: "",
    negative_evidence: "no state reached minimum transparent score",
    invalidation_level: "n/a",
    confirmation_status: "not_applicable",
    confirmation_evidence: "no state candidate",
    expected_horizon: "wait",
    quality_flags: row.quality_flags ?? "",
    fwd_1d_return_pct: row.fwd_1d_return_pct ?? "",
    fwd_3d_return_pct: row.fwd_3d_return_pct ?? "",
    fwd_5d_return_pct: row.fwd_5d_return_pct ?? "",
    fwd_10d_return_pct: row.fwd_10d_return_pct ?? "",
  };
}

function confidence(score, flagsText) {
  const flags = new Set(String(flagsText ?? "").split("|").filter(Boolean));
  let value = Math.min(0.85, 0.25 + score * 0.1);
  if (flags.has("missing_broker_flow")) value -= 0.12;
  if (flags.has("missing_intraday_volume")) value -= 0.05;
  if (flags.has("event_window") || flags.has("lockin_window") || flags.has("flood_damage_window")) value -= 0.04;
  if (flags.has("no_forward_outcome_yet")) value -= 0.03;
  return Math.max(0.05, value).toFixed(2);
}

function invalidation(state, row) {
  const low = row.low || "low";
  const high = row.high || "high";
  if (["accumulation", "panic_absorption", "markup_continuation"].includes(state)) {
    return `bearish if close breaks ${low}`;
  }
  if (["distribution", "failed_rally", "markdown_continuation", "panic_selling"].includes(state)) {
    return `bullish if close reclaims ${high}`;
  }
  if (state === "two_sided_churn") {
    return `wait for close outside ${low}-${high}`;
  }
  return "n/a";
}

function expectedHorizon(state) {
  return {
    accumulation: "5-10 sessions",
    distribution: "5-10 sessions",
    panic_selling: "1-3 sessions",
    panic_absorption: "1-5 sessions",
    failed_rally: "1-5 sessions",
    two_sided_churn: "wait for confirmation",
    markup_continuation: "3-10 sessions",
    markdown_continuation: "3-10 sessions",
  }[state] ?? "wait";
}

function rowKey(row) {
  return `${row.symbol}|${row.date}`;
}

function buildRowContext(rows) {
  const bySymbol = new Map();
  for (const row of rows) {
    if (!bySymbol.has(row.symbol)) bySymbol.set(row.symbol, []);
    bySymbol.get(row.symbol).push(row);
  }

  const result = new Map();
  for (const symbolRows of bySymbol.values()) {
    symbolRows.sort((left, right) => String(left.date).localeCompare(String(right.date)));
    for (let index = 0; index < symbolRows.length; index += 1) {
      const row = symbolRows[index];
      result.set(rowKey(row), {
        prev1: symbolRows[index - 1] ?? null,
        prevRows: symbolRows.slice(Math.max(0, index - 3), index),
        next1: symbolRows[index + 1] ?? null,
      });
    }
  }
  return result;
}

function brokerPersistence(row, prevRows, side) {
  const field = side === "buy" ? "top_net_buyers" : "top_net_sellers";
  const current = parseBrokerIds(row[field]);
  if (current.size === 0) return { persisted: false, brokers: [] };

  const previous = new Set();
  for (const prev of prevRows) {
    for (const broker of parseBrokerIds(prev[field])) previous.add(broker);
  }
  const overlap = [...current].filter((broker) => previous.has(broker));
  return { persisted: overlap.length > 0, brokers: overlap };
}

function parseBrokerIds(text) {
  const ids = new Set();
  for (const part of String(text ?? "").split("|")) {
    const broker = part.split(":")[0]?.trim();
    if (broker) ids.add(broker);
  }
  return ids;
}

function sameDaySupportHold(row, prevRows) {
  const close = number(row.close);
  const low = number(row.low);
  const closePos = number(row.close_position);
  if (close === null || low === null || closePos === null) return false;

  const previousLows = prevRows.map((prev) => number(prev.low)).filter((value) => value !== null);
  const recentSupport = previousLows.length ? Math.min(...previousLows) : low;
  return closePos >= 0.6 && close >= recentSupport * 0.995;
}

function dryupAfterPanic(row, prevRow) {
  if (!prevRow) return false;
  const prevReturn = number(prevRow.return_pct);
  const prevHighVolumeDown = flag(prevRow.high_volume_down);
  const volumeRatio = number(row.volume_ratio_20d);
  const ret = number(row.return_pct);
  const closePos = number(row.close_position);
  const previousPanic = (prevReturn !== null && prevReturn <= -2) || prevHighVolumeDown;
  return Boolean(previousPanic && volumeRatio !== null && volumeRatio <= 0.85 && ret !== null && ret >= -1 && closePos !== null && closePos >= 0.45);
}

function confirmationFor(state, row, context) {
  const next = context.next1;
  if (!next || state === "no_clear_signal") {
    return { status: "unconfirmed", evidence: "no next session available" };
  }

  const close = number(row.close);
  const low = number(row.low);
  const high = number(row.high);
  const nextClose = number(next.close);
  const nextLow = number(next.low);
  const nextHigh = number(next.high);
  if ([close, low, high, nextClose, nextLow, nextHigh].some((value) => value === null)) {
    return { status: "unconfirmed", evidence: "missing next-session price fields" };
  }

  if (["accumulation", "panic_absorption", "markup_continuation"].includes(state)) {
    if (nextClose < low) return { status: "failed", evidence: `next close ${nextClose} broke prior low ${low}` };
    if (nextClose >= close || nextLow >= low) return { status: "confirmed", evidence: `next session defended ${low} and closed ${nextClose}` };
    return { status: "mixed", evidence: `next low tested support but close stayed above ${low}` };
  }

  if (["distribution", "failed_rally", "markdown_continuation", "panic_selling"].includes(state)) {
    if (nextClose > high) return { status: "failed", evidence: `next close ${nextClose} reclaimed prior high ${high}` };
    if (nextClose <= close || nextHigh <= high) return { status: "confirmed", evidence: `next session failed below ${high} and closed ${nextClose}` };
    return { status: "mixed", evidence: `next session challenged resistance but did not close above ${high}` };
  }

  if (state === "two_sided_churn") {
    if (nextClose >= low && nextClose <= high) return { status: "confirmed", evidence: `next close ${nextClose} remained inside prior range` };
    return { status: "failed", evidence: `next close ${nextClose} left prior range ${low}-${high}` };
  }

  return { status: "unconfirmed", evidence: "state has no confirmation rule" };
}

function buildPeerBenchmarks(rows) {
  const grouped = new Map();
  for (const row of rows) {
    for (const horizon of HORIZONS) {
      const value = number(row[`fwd_${horizon}d_return_pct`]);
      if (value === null) continue;
      const groupKey = `${row.date}|${horizon}`;
      if (!grouped.has(groupKey)) grouped.set(groupKey, []);
      grouped.get(groupKey).push({ symbol: row.symbol, value });
    }
  }
  return grouped;
}

function decoratePeerRelative(stateRows, peerBenchmarks) {
  for (const row of stateRows) {
    for (const horizon of HORIZONS) {
      const raw = number(row[`fwd_${horizon}d_return_pct`]);
      const peers = peerBenchmarks.get(`${row.date}|${horizon}`) ?? [];
      const peerValues = peers
        .filter((peer) => peer.symbol !== row.symbol)
        .map((peer) => peer.value);
      const marketValues = peers.map((peer) => peer.value);
      const peerAvg = average(peerValues);
      const marketAvg = average(marketValues);

      row[`peer_fwd_${horizon}d_return_pct`] = peerAvg === null ? "" : peerAvg.toFixed(4);
      row[`regime_${horizon}d_avg_hydro_return_pct`] = marketAvg === null ? "" : marketAvg.toFixed(4);
      row[`excess_peer_${horizon}d_return_pct`] = raw === null || peerAvg === null ? "" : (raw - peerAvg).toFixed(4);
    }
  }
}

function average(values) {
  if (!values.length) return null;
  return values.reduce((sum, value) => sum + value, 0) / values.length;
}

function stats(values) {
  if (!values.length) {
    return { avg: "", median: "", hitRate: "", worst: "", best: "" };
  }
  const sorted = [...values].sort((left, right) => left - right);
  const avg = values.reduce((sum, value) => sum + value, 0) / values.length;
  const median = sorted[Math.floor(sorted.length / 2)];
  const hitRate = values.filter((value) => value > 0).length / values.length * 100;
  return {
    avg: avg.toFixed(4),
    median: median.toFixed(4),
    hitRate: hitRate.toFixed(2),
    worst: sorted[0].toFixed(4),
    best: sorted[sorted.length - 1].toFixed(4),
  };
}

function buildOutcomes(stateRows) {
  const rows = [];
  const states = [...new Set(stateRows.map((row) => row.state))].sort();
  for (const state of states) {
    const scoped = stateRows.filter((row) => row.state === state);
    for (const horizon of HORIZONS) {
      const field = `fwd_${horizon}d_return_pct`;
      const excessField = `excess_peer_${horizon}d_return_pct`;
      const values = scoped.map((row) => number(row[field])).filter((value) => value !== null);
      const excessValues = scoped.map((row) => number(row[excessField])).filter((value) => value !== null);
      if (values.length === 0) {
        rows.push({
          state,
          horizon_days: horizon,
          n: 0,
          avg_return_pct: "",
          median_return_pct: "",
          hit_rate_pct: "",
          avg_excess_peer_return_pct: "",
          median_excess_peer_return_pct: "",
          peer_hit_rate_pct: "",
          worst_return_pct: "",
          best_return_pct: "",
          worst_excess_peer_return_pct: "",
          best_excess_peer_return_pct: "",
        });
        continue;
      }
      const rawStats = stats(values);
      const excessStats = stats(excessValues);
      rows.push({
        state,
        horizon_days: horizon,
        n: values.length,
        avg_return_pct: rawStats.avg,
        median_return_pct: rawStats.median,
        hit_rate_pct: rawStats.hitRate,
        avg_excess_peer_return_pct: excessStats.avg,
        median_excess_peer_return_pct: excessStats.median,
        peer_hit_rate_pct: excessStats.hitRate,
        worst_return_pct: rawStats.worst,
        best_return_pct: rawStats.best,
        worst_excess_peer_return_pct: excessStats.worst,
        best_excess_peer_return_pct: excessStats.best,
      });
    }
  }
  return rows;
}

function buildConfirmationOutcomes(stateRows) {
  const rows = [];
  const groups = new Map();
  for (const row of stateRows) {
    const groupKey = `${row.state}|${row.confirmation_status}`;
    if (!groups.has(groupKey)) groups.set(groupKey, []);
    groups.get(groupKey).push(row);
  }

  for (const [groupKey, scoped] of [...groups.entries()].sort(([left], [right]) => left.localeCompare(right))) {
    const [state, confirmationStatus] = groupKey.split("|");
    for (const horizon of HORIZONS) {
      const rawValues = scoped.map((row) => number(row[`fwd_${horizon}d_return_pct`])).filter((value) => value !== null);
      const excessValues = scoped.map((row) => number(row[`excess_peer_${horizon}d_return_pct`])).filter((value) => value !== null);
      const rawStats = stats(rawValues);
      const excessStats = stats(excessValues);
      rows.push({
        state,
        confirmation_status: confirmationStatus,
        horizon_days: horizon,
        n: rawValues.length,
        avg_return_pct: rawStats.avg,
        hit_rate_pct: rawStats.hitRate,
        avg_excess_peer_return_pct: excessStats.avg,
        peer_hit_rate_pct: excessStats.hitRate,
        worst_excess_peer_return_pct: excessStats.worst,
        best_excess_peer_return_pct: excessStats.best,
      });
    }
  }
  return rows;
}

function buildFindings(stateRows, outcomeRows, confirmationOutcomeRows) {
  const stateCounts = new Map();
  const confirmationCounts = new Map();
  for (const row of stateRows) {
    stateCounts.set(row.state, (stateCounts.get(row.state) ?? 0) + 1);
    const groupKey = `${row.state}|${row.confirmation_status}`;
    confirmationCounts.set(groupKey, (confirmationCounts.get(groupKey) ?? 0) + 1);
  }

  const tenDay = outcomeRows
    .filter((row) => row.horizon_days === "10" && Number(row.n) >= 10 && row.state !== "no_clear_signal")
    .sort((left, right) => Number(right.avg_excess_peer_return_pct) - Number(left.avg_excess_peer_return_pct));
  const confirmedTenDay = confirmationOutcomeRows
    .filter((row) => row.horizon_days === "10" && row.confirmation_status === "confirmed" && Number(row.n) >= 10 && row.state !== "no_clear_signal")
    .sort((left, right) => Number(right.avg_excess_peer_return_pct) - Number(left.avg_excess_peer_return_pct));

  const lines = [
    "# Experiment 09 Psychology Findings",
    "",
    "Transparent rule-scoring pass over `data/hydro_psychology_daily.csv`.",
    "",
    "Research only. These are state candidates, not trading signals.",
    "",
    "## State Counts",
    "",
    "| State | Rows |",
    "|---|---:|",
  ];

  for (const [state, count] of [...stateCounts.entries()].sort(([left], [right]) => left.localeCompare(right))) {
    lines.push(`| ${state} | ${count.toLocaleString("en-US")} |`);
  }

  lines.push(
    "",
    "## 10-Session Peer-Relative Outcome Snapshot",
    "",
    "| State | N | Avg raw | Avg vs peer | Peer hit rate | Raw hit rate | Worst vs peer | Best vs peer |",
    "|---|---:|---:|---:|---:|---:|---:|---:|",
  );
  for (const row of tenDay) {
    lines.push(
      `| ${row.state} | ${row.n} | ${row.avg_return_pct}% | ${row.avg_excess_peer_return_pct}% | ` +
      `${row.peer_hit_rate_pct}% | ${row.hit_rate_pct}% | ${row.worst_excess_peer_return_pct}% | ${row.best_excess_peer_return_pct}% |`,
    );
  }

  lines.push(
    "",
    "## Confirmed 10-Session Peer-Relative Snapshot",
    "",
    "| State | Confirmed rows | Avg raw | Avg vs peer | Peer hit rate | Worst vs peer | Best vs peer |",
    "|---|---:|---:|---:|---:|---:|---:|",
  );
  for (const row of confirmedTenDay) {
    lines.push(
      `| ${row.state} | ${row.n} | ${row.avg_return_pct}% | ${row.avg_excess_peer_return_pct}% | ` +
      `${row.peer_hit_rate_pct}% | ${row.worst_excess_peer_return_pct}% | ${row.best_excess_peer_return_pct}% |`,
    );
  }

  lines.push("", "## Confirmation Counts", "", "| State | Confirmation | Rows |", "|---|---|---:|");
  for (const [groupKey, count] of [...confirmationCounts.entries()].sort(([left], [right]) => left.localeCompare(right))) {
    const [state, confirmationStatus] = groupKey.split("|");
    lines.push(`| ${state} | ${confirmationStatus} | ${count.toLocaleString("en-US")} |`);
  }

  lines.push(
    "",
    "## Caveats",
    "",
    "- Scores use only same-day evidence; forward returns are used only for outcome review.",
    "- Next-session confirmation is reported separately so same-day state scoring does not silently use future data.",
    "- Outcome rows now include peer-relative returns using same-date hydro peers as a first regime adjustment.",
    "- Peer-relative baselines exclude the scored symbol when enough peers have forward returns.",
    "- Tape coverage is currently sparse, so most rows carry `missing_intraday_volume`.",
    "- Broker identity is still broker-number evidence, not client identity.",
    "- These thresholds are v1 research thresholds and should be versioned when changed.",
  );
  return `${lines.join("\n")}\n`;
}

function number(value) {
  if (value === null || value === undefined || value === "") return null;
  const parsed = Number(String(value).replace(/,/g, ""));
  return Number.isFinite(parsed) ? parsed : null;
}

function flag(value) {
  return String(value ?? "").trim() === "1";
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
