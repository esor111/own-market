param(
    [switch]$ForceCore
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$runnerPath = Join-Path $scriptDir "run_monitoring_cycle.py"

function Get-PythonCommand {
    if ($env:MONITORING_PYTHON -and (Test-Path $env:MONITORING_PYTHON)) {
        return [pscustomobject]@{
            Exe = $env:MONITORING_PYTHON
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

    throw "No usable Python executable found. Set MONITORING_PYTHON or install Python 3."
}

$pythonCommand = Get-PythonCommand
$arguments = @($runnerPath)

if ($ForceCore) {
    $arguments += "--force-core"
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
