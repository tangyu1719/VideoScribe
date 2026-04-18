param(
    [string]$Scenario = "tests/gui/scenarios/ops_menu_smoke.json",
    [string]$ArtifactsDir = "tests/gui/artifacts/latest"
)

$ErrorActionPreference = "Stop"

Write-Host "Running GUI macro scenario: $Scenario"
py -3 "tests/gui/gui_macro_runner.py" --scenario "$Scenario" --artifacts-dir "$ArtifactsDir"
$exitCode = $LASTEXITCODE

if ($exitCode -eq 0) {
    Write-Host "GUI macro test passed."
} else {
    Write-Host "GUI macro test failed. See artifacts in $ArtifactsDir" -ForegroundColor Red
}

exit $exitCode

