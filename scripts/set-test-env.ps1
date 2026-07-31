# Set Test Environment Variables
# This script configures the paths to test tools for the current session
# Usage: .\scripts\set-test-env.ps1
# All test frameworks (Playwright, Locust, API tests) read from these environment variables

$ErrorActionPreference = "Stop"

Write-Host "Configuring test environment variables..." -ForegroundColor Cyan

$root = Resolve-Path "$PSScriptRoot\.."
$envFile = Join-Path $root ".env"

if (Test-Path -LiteralPath $envFile) {
    Get-Content -LiteralPath $envFile -Encoding UTF8 | ForEach-Object {
        if ($_ -match '^([A-Z_]+)=(.+)$') {
            $name = $matches[1]
            $value = $matches[2] -replace '^["'']|["'']$', ''
            if (-not (Get-Item "Env:\$name" -ErrorAction SilentlyContinue)) {
                Set-Item -Path "Env:\$name" -Value $value
            }
        }
    }
}

if (-not $env:BASE_URL) {
    $env:BASE_URL = "http://192.168.2.97:6089"
}
Write-Host "[OK] BASE_URL = $env:BASE_URL" -ForegroundColor Green

if (-not $env:API_BASE_URL) {
    $env:API_BASE_URL = "http://192.168.2.97:6089/prod-api"
}
Write-Host "[OK] API_BASE_URL = $env:API_BASE_URL" -ForegroundColor Green

if (-not $env:TEST_USERNAME) {
    $env:TEST_USERNAME = "ZhaoShengYao"
}
Write-Host "[OK] TEST_USERNAME = $env:TEST_USERNAME" -ForegroundColor Green

if (-not $env:TEST_PASSWORD) {
    $env:TEST_PASSWORD = "123456"
}
Write-Host "[OK] TEST_PASSWORD = $env:TEST_PASSWORD" -ForegroundColor Green

if (-not $env:API_USERNAME) {
    $env:API_USERNAME = $env:TEST_USERNAME
}
Write-Host "[OK] API_USERNAME = $env:API_USERNAME" -ForegroundColor Green

if (-not $env:API_PASSWORD) {
    $env:API_PASSWORD = "V+GwtuX+DsY4rxGNZ9hZSg=="
}
Write-Host "[OK] API_PASSWORD = $env:API_PASSWORD" -ForegroundColor Green

if (-not $env:API_CLIENT_ID) {
    $env:API_CLIENT_ID = "e5cd7e4891bf95d1d19206ce24a7b32e"
}
Write-Host "[OK] API_CLIENT_ID = $env:API_CLIENT_ID" -ForegroundColor Green

$env:LOCUST_HOST = $env:BASE_URL
Write-Host "[OK] LOCUST_HOST = $env:LOCUST_HOST" -ForegroundColor Green

if (-not $env:LOCUST_USERS) {
    $env:LOCUST_USERS = "5"
}
Write-Host "[OK] LOCUST_USERS = $env:LOCUST_USERS" -ForegroundColor Green

if (-not $env:LOCUST_SPAWN_RATE) {
    $env:LOCUST_SPAWN_RATE = "1"
}
Write-Host "[OK] LOCUST_SPAWN_RATE = $env:LOCUST_SPAWN_RATE" -ForegroundColor Green

if (-not $env:LOCUST_RUN_TIME) {
    $env:LOCUST_RUN_TIME = "120s"
}
Write-Host "[OK] LOCUST_RUN_TIME = $env:LOCUST_RUN_TIME" -ForegroundColor Green

Write-Host ""
Write-Host "Test environment configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Available tools:" -ForegroundColor Cyan
Write-Host "  - Test System: $env:BASE_URL" -ForegroundColor White
Write-Host "  - API Endpoint: $env:API_BASE_URL" -ForegroundColor White
Write-Host "  - Locust: environment variables configured" -ForegroundColor White
Write-Host ""
Write-Host "To run tests, use:" -ForegroundColor Cyan
Write-Host "  .\scripts\run-ui-tests.ps1" -ForegroundColor White
Write-Host "  .\scripts\run-api-tests.ps1" -ForegroundColor White
Write-Host "  .\scripts\run-locust-api.ps1" -ForegroundColor White
Write-Host "  .\scripts\run-locust-ui.ps1" -ForegroundColor White