param(
    [string]$Date = (Get-Date).ToString("yyyy-MM-dd"),
    [string]$Python = "C:\Users\ishwor\AppData\Local\Programs\Python\Python311\python.exe",
    [switch]$RebuildOnly,
    [switch]$AllowPreMarket,
    [switch]$BrokerDryRun,
    [switch]$SkipPriceScrape,
    [switch]$SkipBrokerScrape,
    [switch]$SkipExperiment07,
    [switch]$SkipExperiment08
)

$ErrorActionPreference = "Stop"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RepoRoot = Resolve-Path (Join-Path $ScriptDir "..\..")
$Today = (Get-Date).ToString("yyyy-MM-dd")
$NowTime = (Get-Date).TimeOfDay
$MarketOpen = [TimeSpan]::Parse("11:00:00")

function Invoke-Step {
    param(
        [string]$Name,
        [scriptblock]$Command
    )

    Write-Host ""
    Write-Host "==> $Name"
    & $Command
}

function Invoke-Node {
    param([string]$RelativePath)

    & node (Join-Path $RepoRoot $RelativePath)
    if ($LASTEXITCODE -ne 0) {
        throw "Node step failed: $RelativePath"
    }
}

function Invoke-Python {
    param([string[]]$Args)

    if (-not (Test-Path $Python)) {
        throw "Python runtime not found at $Python"
    }
    & $Python @Args
    if ($LASTEXITCODE -ne 0) {
        throw "Python step failed: $($Args -join ' ')"
    }
}

Set-Location $RepoRoot

Write-Host "Experiment 09 hydropower psychology refresh"
Write-Host "Date: $Date"
Write-Host "Repo: $RepoRoot"
Write-Host "Local time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss zzz')"

$PreMarketToday = ($Date -eq $Today -and $NowTime -lt $MarketOpen -and -not $AllowPreMarket)
if ($PreMarketToday -and -not $RebuildOnly) {
    Write-Host ""
    Write-Host "Market is not open yet for $Date. Live price/broker scrape will be skipped."
    Write-Host "Use -AllowPreMarket only if you intentionally want to test live scrapers before 11:00."
    $SkipPriceScrape = $true
    $SkipBrokerScrape = $true
}

if (-not $RebuildOnly -and -not $SkipPriceScrape) {
    Invoke-Step "ShareSansar price scrape" {
        Invoke-Python @("sharesansar_datascrape\scrape_nepse.py", "--start-date", $Date, "--end-date", $Date)
    }
}

if (-not $RebuildOnly) {
    Invoke-Step "Price archive integrity" {
        Invoke-Python @("market-gist\automation\price_data_integrity.py")
    }
}

if (-not $RebuildOnly -and -not $SkipBrokerScrape) {
    $brokerArgs = @("market-gist\automation\run_daily_scrape.py", "--date", $Date, "--sector", "hydropower")
    if ($BrokerDryRun) {
        $brokerArgs += "--dry-run"
    }
    Invoke-Step "Hydropower broker-flow scrape" {
        Invoke-Python $brokerArgs
    }
}

if (-not $SkipExperiment07) {
    Invoke-Step "Experiment 07 broker-flow dataset" {
        Invoke-Python @("experiments\07-hydro-broker-flow\build_dataset.py")
    }
}

if (-not $SkipExperiment08) {
    Invoke-Step "Experiment 08 volume/tape dataset" {
        Invoke-Python @("experiments\08-hydro-volume-tape-lab\build_volume_dataset.py")
    }
}

Invoke-Step "Experiment 09 master table" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_master_dataset.mjs"
}

Invoke-Step "Experiment 09 psychology scoring" {
    Invoke-Node "experiments\09-hydro-psychology-engine\score_psychology_states.mjs"
}

Invoke-Step "Experiment 09 edge report" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_edge_report.mjs"
}

Invoke-Step "Experiment 09.1 walk-forward backtest" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_walk_forward_backtest.mjs"
}

Invoke-Step "Experiment 09.1 latest forecast" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_latest_forecast.mjs"
}

Invoke-Step "Experiment 09.2 data quality audit" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_data_quality_audit.mjs"
}

Invoke-Step "Experiment 09.3 pattern robustness" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_pattern_robustness.mjs"
}

Invoke-Step "Experiment 09.5 failed bearish lab" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_failed_bearish_lab.mjs"
}

Invoke-Step "Experiment 09.4 entry/exit simulator" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_entry_exit_simulator.mjs"
}

Invoke-Step "Experiment 09.6 confirmation rule lab" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_confirmation_rule_lab.mjs"
}

Invoke-Step "Experiment 09.7 robust pattern trade lab" {
    Invoke-Node "experiments\09-hydro-psychology-engine\build_robust_pattern_trade_lab.mjs"
}

Write-Host ""
Write-Host "Done."
Write-Host "Latest watchlist: experiments\09-hydro-psychology-engine\results\latest_watchlist.csv"
Write-Host "Readable report: experiments\09-hydro-psychology-engine\results\edge_candidate_report.md"
Write-Host "Latest forecast: experiments\09-hydro-psychology-engine\results\latest_forecast.md"
Write-Host "Validation reports: experiments\09-hydro-psychology-engine\results\data_quality_report.md, pattern_robustness_report.md, failed_bearish_report.md, entry_exit_report.md, confirmation_rule_report.md, robust_pattern_trade_report.md"
