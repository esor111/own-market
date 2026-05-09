param(
    [string]$Date = (Get-Date).ToString("yyyy-MM-dd"),
    [string]$Python = "C:\Users\ishwor\AppData\Local\Programs\Python\Python311\python.exe",
    [switch]$RebuildOnly,
    [switch]$AllowPreMarket,
    [switch]$BrokerDryRun,
    [switch]$SkipPriceScrape,
    [switch]$SkipBrokerScrape,
    [switch]$SkipExperiment07,
    [switch]$SkipExperiment08,
    [switch]$SkipRefresh,
    [switch]$ScoreOnly
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$RefreshScript = Join-Path $ScriptDir "refresh_hydro_psychology.ps1"
$AppendScript = Join-Path $ScriptDir "append_watchlist_to_ledger.py"
$ScoreScript = Join-Path $ScriptDir "score_ledger_calls.py"

if (-not (Test-Path $Python)) {
    throw "Python runtime not found at $Python"
}

Write-Host "==> Daily hydro routine"
Write-Host "Date: $Date"
Write-Host ""

if (-not $ScoreOnly -and -not $SkipRefresh) {
    Write-Host "==> Step 1/3: Refresh psychology engine"
    $refreshArgs = @{
        Date = $Date
        Python = $Python
    }
    if ($RebuildOnly)       { $refreshArgs["RebuildOnly"] = $true }
    if ($AllowPreMarket)    { $refreshArgs["AllowPreMarket"] = $true }
    if ($BrokerDryRun)      { $refreshArgs["BrokerDryRun"] = $true }
    if ($SkipPriceScrape)   { $refreshArgs["SkipPriceScrape"] = $true }
    if ($SkipBrokerScrape)  { $refreshArgs["SkipBrokerScrape"] = $true }
    if ($SkipExperiment07)  { $refreshArgs["SkipExperiment07"] = $true }
    if ($SkipExperiment08)  { $refreshArgs["SkipExperiment08"] = $true }
    & $RefreshScript @refreshArgs
    if ($LASTEXITCODE -ne 0) { throw "Refresh step failed." }
}

if (-not $ScoreOnly) {
    Write-Host ""
    Write-Host "==> Step 2/3: Append watchlist to paper-trade ledger"
    & $Python $AppendScript
    if ($LASTEXITCODE -ne 0) { throw "Append step failed." }
}

Write-Host ""
Write-Host "==> Step 3/3: Score ledger calls whose forward window has elapsed"
& $Python $ScoreScript
if ($LASTEXITCODE -ne 0) { throw "Score step failed." }

Write-Host ""
Write-Host "Done."
Write-Host "Ledger: experiments\09-hydro-psychology-engine\data\paper_trade_ledger.csv"
Write-Host "Scorecard: experiments\09-hydro-psychology-engine\results\paper_trade_scorecard.md"
