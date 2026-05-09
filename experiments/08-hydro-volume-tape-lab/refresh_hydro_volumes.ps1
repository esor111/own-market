param(
    [string]$Symbol,
    [string[]]$Symbols,
    [switch]$All,
    [int]$Days = 31
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ExperimentRoot = $ScriptDir
$WorkspaceRoot = Split-Path -Parent (Split-Path -Parent $ScriptDir)
$ExistingRefresh = Join-Path $WorkspaceRoot "refresh_upper_data.ps1"
$ConfigPath = Join-Path $ScriptDir "config.json"
$RawRoot = Join-Path $ExperimentRoot "raw"

if (-not (Test-Path -LiteralPath $ExistingRefresh)) {
    throw "Missing existing refresh script: $ExistingRefresh. This wrapper depends on it."
}

if (-not (Test-Path -LiteralPath $ConfigPath)) {
    throw "Missing config.json at $ConfigPath"
}

function Resolve-Symbols {
    param([string]$SingleSymbol, [string[]]$MultiSymbols, [switch]$UseAll)

    if ($UseAll) {
        $cfg = Get-Content -LiteralPath $ConfigPath -Raw | ConvertFrom-Json
        return @($cfg.symbols)
    }
    if ($MultiSymbols -and $MultiSymbols.Count -gt 0) {
        return $MultiSymbols | ForEach-Object { $_.ToUpper().Trim() } | Where-Object { $_ }
    }
    if ($SingleSymbol) {
        return @($SingleSymbol.ToUpper().Trim())
    }
    throw "Specify -Symbol, -Symbols, or -All"
}

function Move-SymbolArtifacts {
    param([string]$SymbolName)

    $symbolLower = $SymbolName.ToLowerInvariant()
    $symbolDir = Join-Path $RawRoot $SymbolName
    New-Item -ItemType Directory -Force -Path $symbolDir | Out-Null

    $artifacts = @(
        "${symbolLower}_volume_1min.csv",
        "${symbolLower}_volume_hourly.csv",
        "${symbolLower}_volume_daily.csv",
        "${symbolLower}_volume_last_month_full.json",
        "${symbolLower}_volume_last_month_summary.json",
        "${symbolLower}_volume_daily_chart.png"
    )

    $movedCount = 0
    foreach ($name in $artifacts) {
        $sourcePath = Join-Path $WorkspaceRoot $name
        if (Test-Path -LiteralPath $sourcePath) {
            $destPath = Join-Path $symbolDir $name
            Move-Item -LiteralPath $sourcePath -Destination $destPath -Force
            $movedCount++
        }
    }
    return $movedCount
}

$targetSymbols = Resolve-Symbols -SingleSymbol $Symbol -MultiSymbols $Symbols -UseAll:$All

if (-not $targetSymbols -or $targetSymbols.Count -eq 0) {
    throw "No symbols resolved."
}

Write-Host "Refreshing volume data for: $($targetSymbols -join ', ')"
Write-Host "Days: $Days"
Write-Host ""

$summary = @()
foreach ($sym in $targetSymbols) {
    Write-Host "=== $sym ==="
    try {
        & $ExistingRefresh -Symbol $sym -Days $Days
        $moved = Move-SymbolArtifacts -SymbolName $sym
        $summary += [pscustomobject]@{
            symbol = $sym
            status = "ok"
            files_moved = $moved
        }
    } catch {
        Write-Warning "Failed for ${sym}: $($_.Exception.Message)"
        $summary += [pscustomobject]@{
            symbol = $sym
            status = "failed"
            files_moved = 0
        }
    }
    Write-Host ""
}

Write-Host "--- Summary ---"
$summary | Format-Table -AutoSize
