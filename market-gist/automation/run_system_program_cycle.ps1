param(
    [switch]$ForceMonitoring,
    [switch]$ForceEntry,
    [switch]$ForceAll,
    [switch]$SummaryOnly,
    [switch]$Full
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerPath = Join-Path $scriptDir "run_system_program_cycle.py"

function Get-PythonCommand {
    if ($env:SYSTEM_PROGRAM_PYTHON -and (Test-Path $env:SYSTEM_PROGRAM_PYTHON)) {
        return [pscustomobject]@{
            Exe = $env:SYSTEM_PROGRAM_PYTHON
            PrefixArgs = @()
        }
    }

    $explicitCandidates = @(
        "C:\Users\ishwor\AppData\Local\Programs\Python\Python311\python.exe"
    )

    foreach ($candidate in $explicitCandidates) {
        if (Test-Path $candidate) {
            return [pscustomobject]@{
                Exe = $candidate
                PrefixArgs = @()
            }
        }
    }

    $pyCommand = Get-Command py -ErrorAction SilentlyContinue
    if ($pyCommand) {
        return [pscustomobject]@{
            Exe = $pyCommand.Source
            PrefixArgs = @("-3")
        }
    }

    $pythonCommand = Get-Command python -ErrorAction SilentlyContinue
    if ($pythonCommand) {
        return [pscustomobject]@{
            Exe = $pythonCommand.Source
            PrefixArgs = @()
        }
    }

    throw "No usable Python executable found. Set SYSTEM_PROGRAM_PYTHON or install Python 3."
}

$pythonCommand = Get-PythonCommand
$arguments = @($runnerPath)

if ($ForceMonitoring) {
    $arguments += "--force-monitoring"
}
if ($ForceEntry) {
    $arguments += "--force-entry"
}
if ($ForceAll) {
    $arguments += "--force-all"
}
if ($SummaryOnly -and $Full) {
    throw "Use either -SummaryOnly or -Full, not both."
}

if (-not $Full) {
    $arguments += "--summary-only"
}
elseif ($SummaryOnly) {
    $arguments += "--summary-only"
}

Write-Host "Using Python:" $pythonCommand.Exe ($pythonCommand.PrefixArgs -join " ")
Write-Host "Running:" ($arguments -join " ")

if ($pythonCommand.PrefixArgs.Count -gt 0) {
    & $pythonCommand.Exe @($pythonCommand.PrefixArgs) @arguments
}
else {
    & $pythonCommand.Exe @arguments
}
$exitCode = $LASTEXITCODE

if ($exitCode -ne 0) {
    exit $exitCode
}
