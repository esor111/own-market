const fs = require("fs");
const os = require("os");
const path = require("path");
const { URL } = require("url");

function parseArgs(argv) {
  const out = {
    symbol: "UPPER",
    days: 31,
    outDir: process.cwd(),
    cdpUrl: "http://127.0.0.1:9222",
    skillDir:
      process.env.PLAYWRIGHT_SKILL_DIR ||
      path.join(os.homedir(), ".agents", "skills", "playwright"),
  };

  for (let i = 0; i < argv.length; i += 1) {
    const arg = argv[i];
    if (arg === "--symbol") {
      out.symbol = String(argv[i + 1] || out.symbol).toUpperCase();
      i += 1;
    } else if (arg === "--days") {
      out.days = Number(argv[i + 1] || out.days);
      i += 1;
    } else if (arg === "--out-dir") {
      out.outDir = path.resolve(argv[i + 1] || out.outDir);
      i += 1;
    } else if (arg === "--cdp-url") {
      out.cdpUrl = String(argv[i + 1] || out.cdpUrl);
      i += 1;
    } else if (arg === "--skill-dir") {
      out.skillDir = path.resolve(argv[i + 1] || out.skillDir);
      i += 1;
    }
  }

  return out;
}

function ensureDir(dirPath) {
  fs.mkdirSync(dirPath, { recursive: true });
}

function csvEscape(value) {
  if (value === null || value === undefined) {
    return "";
  }

  const text = String(value);
  if (/[",\r\n]/.test(text)) {
    return `"${text.replace(/"/g, "\"\"")}"`;
  }
  return text;
}

function writeCsv(filePath, rows) {
  const headers = Array.from(
    rows.reduce((set, row) => {
      Object.keys(row).forEach((key) => set.add(key));
      return set;
    }, new Set()),
  );

  const lines = [headers.map(csvEscape).join(",")];
  for (const row of rows) {
    lines.push(headers.map((header) => csvEscape(row[header])).join(","));
  }
  fs.writeFileSync(filePath, `${lines.join("\n")}\n`, "utf8");
}

function toKathmanduDateFormatters() {
  return {
    stamp: new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Kathmandu",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      second: "2-digit",
      hour12: false,
    }),
    datetime: new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Kathmandu",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
      hour: "2-digit",
      minute: "2-digit",
      hour12: false,
    }),
    date: new Intl.DateTimeFormat("en-CA", {
      timeZone: "Asia/Kathmandu",
      year: "numeric",
      month: "2-digit",
      day: "2-digit",
    }),
  };
}

function buildDateHelpers() {
  const fmt = toKathmanduDateFormatters();

  function npDate(ts) {
    return fmt.date.format(new Date(ts * 1000));
  }

  function npDateTime(ts) {
    const parts = fmt.datetime.formatToParts(new Date(ts * 1000));
    const map = Object.fromEntries(
      parts.filter((part) => part.type !== "literal").map((part) => [part.type, part.value]),
    );
    return `${map.year}-${map.month}-${map.day} ${map.hour}:${map.minute}`;
  }

  function scrapeStamp() {
    return fmt.stamp.format(new Date());
  }

  return { npDate, npDateTime, scrapeStamp };
}

function aggregateBars(minuteBars) {
  const dailyMap = {};
  const hourlyMap = {};

  for (const bar of minuteBars) {
    const volume = Number(bar.volume) || 0;

    let day = dailyMap[bar.date_np];
    if (!day) {
      day = dailyMap[bar.date_np] = {
        date_np: bar.date_np,
        bars: 0,
        volume: 0,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      };
    }
    day.bars += 1;
    day.volume += volume;
    day.high = Math.max(day.high, bar.high);
    day.low = Math.min(day.low, bar.low);
    day.close = bar.close;

    const hourKey = `${bar.datetime_np.slice(0, 13)}:00`;
    let hour = hourlyMap[hourKey];
    if (!hour) {
      hour = hourlyMap[hourKey] = {
        hour_np: hourKey,
        bars: 0,
        volume: 0,
        open: bar.open,
        high: bar.high,
        low: bar.low,
        close: bar.close,
      };
    }
    hour.bars += 1;
    hour.volume += volume;
    hour.high = Math.max(hour.high, bar.high);
    hour.low = Math.min(hour.low, bar.low);
    hour.close = bar.close;
  }

  const daily = Object.values(dailyMap).sort((a, b) => a.date_np.localeCompare(b.date_np));
  const hourly = Object.values(hourlyMap).sort((a, b) => a.hour_np.localeCompare(b.hour_np));

  return { daily, hourly };
}

async function main() {
  const args = parseArgs(process.argv.slice(2));
  ensureDir(args.outDir);

  const playwrightModulePath = path.join(args.skillDir, "node_modules", "playwright");
  if (!fs.existsSync(playwrightModulePath)) {
    throw new Error(
      `Playwright dependency not found at ${playwrightModulePath}. Run setup for the Playwright skill first.`,
    );
  }

  // eslint-disable-next-line import/no-dynamic-require, global-require
  const { chromium } = require(playwrightModulePath);
  const { npDate, npDateTime, scrapeStamp } = buildDateHelpers();

  const browser = await chromium.connectOverCDP(args.cdpUrl);
  let context = browser.contexts()[0];
  if (!context) {
    context = await browser.newContext();
  }
  let page = context.pages()[0];
  let ownsPage = false;
  if (!page) {
    page = await context.newPage();
    ownsPage = true;
  }

  try {
    let fsk = null;
    const onRequest = (request) => {
      const requestUrl = request.url();
      if (requestUrl.includes("/trading/1/search?")) {
        fsk = new URL(requestUrl).searchParams.get("fsk");
      }
    };
    page.on("request", onRequest);

    if (!page.url().includes("nepsealpha.com/nepse-chart")) {
      await page.goto("https://nepsealpha.com/nepse-chart", {
        waitUntil: "domcontentloaded",
        timeout: 45000,
      });
    }
    await page.waitForTimeout(10000);

    const fskStartedAt = Date.now();
    while (!fsk && Date.now() - fskStartedAt < 45000) {
      await page.waitForTimeout(500);
    }
    if (!fsk) {
      const resourceMatch = await page.evaluate(() => {
        const resource = performance
          .getEntriesByType("resource")
          .map((entry) => entry.name)
          .find((name) => name.includes("fsk="));
        return resource || null;
      });
      if (resourceMatch) {
        fsk = new URL(resourceMatch).searchParams.get("fsk");
      }
    }
    if (!fsk) {
      throw new Error("Could not discover live fsk token from Nepse Alpha.");
    }

    let frame = null;
    const frameStartedAt = Date.now();
    while (!frame && Date.now() - frameStartedAt < 45000) {
      frame = page
        .frames()
        .find(
          (candidate) =>
            candidate !== page.mainFrame() &&
            candidate.name().toLowerCase().includes("tradingview"),
        );
      if (!frame) {
        await page.waitForTimeout(500);
      }
    }
    if (!frame) {
      throw new Error("TradingView iframe was not found on the Nepse Alpha page.");
    }

    async function getHistory(resolution) {
      return frame.evaluate(
        async ({ fskValue, symbol, resolutionValue }) => {
          const response = await fetch(
            `/trading/1/history?fsk=${encodeURIComponent(
              fskValue,
            )}&symbol=${encodeURIComponent(symbol)}&resolution=${encodeURIComponent(
              resolutionValue,
            )}&frame=1000`,
            {
              headers: {
                "x-requested-with": "XMLHttpRequest",
                accept: "application/json, text/plain, */*",
              },
            },
          );
          const text = await response.text();
          let json;
          try {
            json = JSON.parse(text);
          } catch {
            json = { raw: text.slice(0, 500) };
          }
          return { status: response.status, json };
        },
        { fskValue: fsk, symbol: args.symbol, resolutionValue: resolution },
      );
    }

    const minuteResp = await getHistory("1");
    const dayResp = await getHistory("1D");
    const res5 = await getHistory("5");
    const res30 = await getHistory("30");
    const res60 = await getHistory("60");

    const minuteJson = minuteResp.json;
    if (minuteResp.status !== 200 || minuteJson.s !== "ok" || !Array.isArray(minuteJson.t)) {
      throw new Error(
        `Minute endpoint failed for ${args.symbol}. Status ${minuteResp.status}.`,
      );
    }

    const minuteAll = minuteJson.t.map((ts, index) => ({
      symbol: args.symbol,
      resolution: "1min",
      ts,
      datetime_np: npDateTime(ts),
      date_np: npDate(ts),
      open: minuteJson.o[index],
      high: minuteJson.h[index],
      low: minuteJson.l[index],
      close: minuteJson.c[index],
      volume: minuteJson.v[index],
    }));

    const latestTs = minuteAll.at(-1).ts;
    const cutoff = latestTs - args.days * 24 * 60 * 60;
    const minuteBars = minuteAll.filter((bar) => bar.ts >= cutoff);
    const { daily, hourly } = aggregateBars(minuteBars);

    const dayJson = dayResp.json;
    const directDailyAll =
      dayResp.status === 200 && dayJson.s === "ok" && Array.isArray(dayJson.t)
        ? dayJson.t.map((ts, index) => ({
            date_np: npDate(ts),
            datetime_np: npDateTime(ts),
            open: dayJson.o[index],
            high: dayJson.h[index],
            low: dayJson.l[index],
            close: dayJson.c[index],
            volume: dayJson.v[index],
          }))
        : [];

    const summary = {
      scraped_at_np: scrapeStamp(),
      symbol: args.symbol,
      source: "https://nepsealpha.com/nepse-chart",
      endpoint: "/trading/1/history",
      timezone: "Asia/Kathmandu",
      live_fsk: fsk,
      latest_datetime_np: npDateTime(latestTs),
      cutoff_datetime_np: npDateTime(cutoff),
      endpoint_statuses: {
        minute_1: minuteResp.status,
        daily_1D: dayResp.status,
        resolution_5: res5.status,
        resolution_30: res30.status,
        resolution_60: res60.status,
      },
      endpoint_ranges: {
        minute_first: minuteAll[0]?.datetime_np ?? null,
        minute_last: minuteAll.at(-1)?.datetime_np ?? null,
        minute_bar_count: minuteAll.length,
        daily_first: directDailyAll[0]?.datetime_np ?? null,
        daily_last: directDailyAll.at(-1)?.datetime_np ?? null,
        daily_bar_count: directDailyAll.length,
      },
      minute_bar_count: minuteBars.length,
      total_volume: minuteBars.reduce((sum, row) => sum + (Number(row.volume) || 0), 0),
      trading_days: daily.length,
      first_trading_day: daily[0]?.date_np ?? null,
      last_trading_day: daily.at(-1)?.date_np ?? null,
      top_10_days_by_volume: [...daily].sort((a, b) => b.volume - a.volume).slice(0, 10),
      top_10_hours_by_volume: [...hourly].sort((a, b) => b.volume - a.volume).slice(0, 10),
    };

    const full = {
      ...summary,
      direct_daily: directDailyAll,
      daily,
      hourly,
      minute_bars: minuteBars,
    };

    const symbolLower = args.symbol.toLowerCase();
    const fullPath = path.join(args.outDir, `${symbolLower}_volume_last_month_full.json`);
    const summaryPath = path.join(args.outDir, `${symbolLower}_volume_last_month_summary.json`);
    const minuteCsvPath = path.join(args.outDir, `${symbolLower}_volume_1min.csv`);
    const hourlyCsvPath = path.join(args.outDir, `${symbolLower}_volume_hourly.csv`);
    const dailyCsvPath = path.join(args.outDir, `${symbolLower}_volume_daily.csv`);

    fs.writeFileSync(fullPath, `${JSON.stringify(full, null, 2)}\n`, "utf8");
    fs.writeFileSync(summaryPath, `${JSON.stringify(summary, null, 2)}\n`, "utf8");
    writeCsv(minuteCsvPath, minuteBars);
    writeCsv(hourlyCsvPath, hourly);
    writeCsv(dailyCsvPath, daily);

    process.stdout.write(
      `${JSON.stringify(
        {
          symbol: args.symbol,
          fullPath,
          summaryPath,
          minuteCsvPath,
          hourlyCsvPath,
          dailyCsvPath,
          scraped_at_np: summary.scraped_at_np,
          range_start: summary.cutoff_datetime_np,
          range_end: summary.latest_datetime_np,
          trading_days: summary.trading_days,
          minute_bar_count: summary.minute_bar_count,
          total_volume: summary.total_volume,
          top_day: summary.top_10_days_by_volume[0] || null,
          top_hour: summary.top_10_hours_by_volume[0] || null,
        },
        null,
        2,
      )}\n`,
    );
  } finally {
    if (ownsPage) {
      await page.close().catch(() => {});
    }
    await browser.close().catch(() => {});
  }
}

main().catch((error) => {
  console.error(error instanceof Error ? error.stack : String(error));
  process.exit(1);
});
