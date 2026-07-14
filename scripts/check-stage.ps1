param(
    [Parameter(Mandatory, Position = 0)]
    [string]$StageId,
    [Parameter(Position = 1)]
    [string]$RunId,
    [ValidateSet("preflight", "full")]
    [string]$Mode = "full",
    [switch]$WriteStatus
)

$ErrorActionPreference = "Stop"

$root = Resolve-Path "$PSScriptRoot\.."
Set-Location $root

$arguments = @(
    (Join-Path $root "scripts\stage_contract.py"),
    "check-stage",
    "--stage-id", $StageId,
    "--mode", $Mode
)

if ($RunId) {
    $arguments += @("--run-id", $RunId)
}
if ($WriteStatus) {
    $arguments += "--write-status"
}

& python @arguments
exit $LASTEXITCODE
