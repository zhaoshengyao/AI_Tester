# Set Test Environment Variables
# This script configures the paths to test tools for the current session
# Usage: .\scripts\set-test-env.ps1
# All test frameworks (Playwright, Locust, API tests) read from these environment variables

$ErrorActionPreference = "Stop"

Write-Host "Configuring test environment variables..." -ForegroundColor Cyan

# Test System Configuration
$env:BASE_URL = "http://192.168.2.97:6089"
Write-Host "[OK] BASE_URL = $env:BASE_URL" -ForegroundColor Green

$env:API_BASE_URL = "http://192.168.2.97:6089/prod-api"
Write-Host "[OK] API_BASE_URL = $env:API_BASE_URL" -ForegroundColor Green

# Test Account Configuration
$env:TEST_USERNAME = "admin"
Write-Host "[OK] TEST_USERNAME = $env:TEST_USERNAME" -ForegroundColor Green

$env:TEST_PASSWORD = "admin123"
Write-Host "[OK] TEST_PASSWORD = $env:TEST_PASSWORD" -ForegroundColor Green

# JMeter Configuration (deprecated, replaced by Locust)
$env:JMETER_BIN = "D:\SoftWare\jmeter\jmeter\bin\"
Write-Host "[OK] JMETER_BIN = $env:JMETER_BIN" -ForegroundColor Yellow

# ZAP Configuration
$env:ZAP_HOME = "D:\SoftWare\ZAP\Zed Attack Proxy"
Write-Host "[OK] ZAP_HOME = $env:ZAP_HOME" -ForegroundColor Green

# Locust Configuration
$env:LOCUST_HOST = $env:BASE_URL
Write-Host "[OK] LOCUST_HOST = $env:LOCUST_HOST" -ForegroundColor Green

$env:LOCUST_USERS = "5"
Write-Host "[OK] LOCUST_USERS = $env:LOCUST_USERS" -ForegroundColor Green

$env:LOCUST_SPAWN_RATE = "1"
Write-Host "[OK] LOCUST_SPAWN_RATE = $env:LOCUST_SPAWN_RATE" -ForegroundColor Green

$env:LOCUST_RUN_TIME = "120s"
Write-Host "[OK] LOCUST_RUN_TIME = $env:LOCUST_RUN_TIME" -ForegroundColor Green

Write-Host ""
Write-Host "Test environment configured successfully!" -ForegroundColor Green
Write-Host ""
Write-Host "Available tools:" -ForegroundColor Cyan
Write-Host "  - Test System: $env:BASE_URL" -ForegroundColor White
Write-Host "  - API Endpoint: $env:API_BASE_URL" -ForegroundColor White
Write-Host "  - Locust: environment variables configured" -ForegroundColor White
Write-Host "  - JMeter: $env:JMETER_BIN (deprecated)" -ForegroundColor Yellow
Write-Host "  - ZAP: $env:ZAP_HOME" -ForegroundColor White
Write-Host ""
Write-Host "To run tests, use:" -ForegroundColor Cyan
Write-Host "  .\scripts\run-ui-tests.ps1" -ForegroundColor White
Write-Host "  .\scripts\run-api-tests.ps1" -ForegroundColor White
Write-Host "  .\scripts\run-locust-api.ps1" -ForegroundColor White
Write-Host "  .\scripts\run-locust-ui.ps1" -ForegroundColor White