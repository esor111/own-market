# Test Intraday Scraper
# Quick test to verify the scraper works for one symbol

param(
    [string]$Symbol = "AKPL"
)

Write-Host "Testing intraday scraper for $Symbol..." -ForegroundColor Cyan
Write-Host ""

# Check if refresh script exists
if (-not (Test-Path "refresh_upper_data.ps1")) {
    Write-Host "ERROR: refresh_upper_data.ps1 not found" -ForegroundColor Red
    exit 1
}

# Run the scraper
Write-Host "Running scraper (this may take 30-60 seconds)..." -ForegroundColor Yellow
try {
    $result = .\refresh_upper_data.ps1 -Symbol $Symbol -Days 31
    
    Write-Host ""
    Write-Host "✅ Scraper completed successfully!" -ForegroundColor Green
    Write-Host ""
    Write-Host "Results:" -ForegroundColor Cyan
    $result | Format-List
    
    # Check output files
    $symbolLower = $Symbol.ToLowerInvariant()
    $files = @(
        "${symbolLower}_volume_1min.csv",
        "${symbolLower}_volume_hourly.csv",
        "${symbolLower}_volume_daily.csv",
        "${symbolLower}_volume_last_month_full.json",
        "${symbolLower}_volume_last_month_summary.json"
    )
    
    Write-Host ""
    Write-Host "Output Files:" -ForegroundColor Cyan
    foreach ($file in $files) {
        if (Test-Path $file) {
            $size = (Get-Item $file).Length
            Write-Host "  ✅ $file ($size bytes)" -ForegroundColor Green
        } else {
            Write-Host "  ❌ $file (missing)" -ForegroundColor Red
        }
    }
    
    # Show sample of minute data
    if (Test-Path "${symbolLower}_volume_1min.csv") {
        Write-Host ""
        Write-Host "Sample Minute Data (first 5 rows):" -ForegroundColor Cyan
        Get-Content "${symbolLower}_volume_1min.csv" | Select-Object -First 6
    }
    
} catch {
    Write-Host ""
    Write-Host "❌ Scraper failed: $_" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "Test complete! The scraper is working." -ForegroundColor Green
