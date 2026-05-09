param(
    [string]$Symbol = "UPPER",
    [int]$Days = 31
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

$WorkspaceRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$ScriptDir = Join-Path $WorkspaceRoot "scripts"
$NodeScript = Join-Path $ScriptDir "refresh_nepse_symbol.js"
$PythonScript = Join-Path $ScriptDir "render_volume_chart.py"
$PlaywrightSkillDir = Join-Path $env:USERPROFILE ".agents\skills\playwright"
$ChromePath = "C:\Program Files\Google\Chrome\Application\chrome.exe"
$ChromeProfile = Join-Path $env:TEMP "chrome-automation-nepse"
$CdpUrl = "http://127.0.0.1:9222"

if (-not (Test-Path -LiteralPath $NodeScript)) {
    throw "Missing scraper script: $NodeScript"
}

if (-not (Test-Path -LiteralPath $PythonScript)) {
    throw "Missing chart script: $PythonScript"
}

if (-not (Test-Path -LiteralPath $PlaywrightSkillDir)) {
    throw "Missing Playwright skill directory: $PlaywrightSkillDir"
}

if (-not (Test-Path -LiteralPath $ChromePath)) {
    throw "Missing Chrome executable: $ChromePath"
}

function Test-CdpEndpoint {
    param([string]$Url)

    try {
        $null = Invoke-WebRequest -Uri "$Url/json/version" -UseBasicParsing -TimeoutSec 2
        return $true
    } catch {
        return $false
    }
}

if (-not (Test-CdpEndpoint -Url $CdpUrl)) {
    Start-Process -FilePath $ChromePath -ArgumentList @(
        "--remote-debugging-port=9222",
        "--user-data-dir=$ChromeProfile",
        "https://nepsealpha.com/nepse-chart"
    ) | Out-Null

    $ready = $false
    foreach ($attempt in 1..20) {
        Start-Sleep -Seconds 1
        if (Test-CdpEndpoint -Url $CdpUrl) {
            $ready = $true
            break
        }
    }

    if (-not $ready) {
        throw "Chrome remote debugging endpoint did not come up at $CdpUrl"
    }
}

$nodeArgs = @(
    $NodeScript
    "--symbol", $Symbol
    "--days", $Days
    "--out-dir", $WorkspaceRoot
    "--skill-dir", $PlaywrightSkillDir
    "--cdp-url", $CdpUrl
)

$jsonText = (& node @nodeArgs | Out-String).Trim()
if ($LASTEXITCODE -ne 0) {
    throw "Node scraper failed with exit code $LASTEXITCODE"
}

$result = $jsonText | ConvertFrom-Json

$fullJsonPath = $result.fullPath
& python $PythonScript $fullJsonPath
if ($LASTEXITCODE -ne 0) {
    throw "Chart rendering failed with exit code $LASTEXITCODE"
}

$symbolLower = $Symbol.ToLowerInvariant()
$chartPath = Join-Path $WorkspaceRoot "${symbolLower}_volume_daily_chart.png"

[pscustomobject]@{
    symbol = $result.symbol
    scraped_at_np = $result.scraped_at_np
    range_start = $result.range_start
    range_end = $result.range_end
    trading_days = $result.trading_days
    minute_bar_count = $result.minute_bar_count
    total_volume = $result.total_volume
    full_json = $result.fullPath
    summary_json = $result.summaryPath
    minute_csv = $result.minuteCsvPath
    hourly_csv = $result.hourlyCsvPath
    daily_csv = $result.dailyCsvPath
    chart_png = $chartPath
} | Format-List
