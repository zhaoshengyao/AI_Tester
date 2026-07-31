param(

    [string]$FrontendUrl = "",

    [string]$ApiBaseUrl = "",

    [string]$Username = "",

    [string]$Password = "",

    [string]$RunId = $(Get-Date -Format "yyyyMMdd-HHmmss"),

    [bool]$ContinueOnError = $false

)



$ErrorActionPreference = "Continue"



$root = Resolve-Path "$PSScriptRoot\.."

Set-Location $root



function Load-EnvFile {

    param([string]$Path)

    if (Test-Path -LiteralPath $Path) {

        Get-Content -LiteralPath $Path -Encoding UTF8 | ForEach-Object {

            if ($_ -match '^([^#=]+)=(.*)$') {

                $name = $matches[1].Trim()

                $value = $matches[2].Trim()

                if (-not [Environment]::GetEnvironmentVariable($name)) {

                    [Environment]::SetEnvironmentVariable($name, $value, "Process")

                }

            }

        }

    }

}



Load-EnvFile -Path (Join-Path $root ".env")



if (-not $FrontendUrl) { $FrontendUrl = $env:BASE_URL }

if (-not $ApiBaseUrl) { $ApiBaseUrl = $env:API_BASE_URL }

if (-not $Username) { $Username = $env:TEST_USERNAME }

if (-not $Password) { $Password = $env:TEST_PASSWORD }



$env:BASE_URL = $FrontendUrl

$env:API_BASE_URL = $ApiBaseUrl

$env:TEST_USERNAME = $Username

$env:TEST_PASSWORD = $Password

$env:TEST_RUN_ID = $RunId



$runDir = Join-Path $root "docs\test-runs\$RunId"

New-Item -ItemType Directory -Force -Path $runDir | Out-Null



$logFile = Join-Path $runDir "test-flow.log"

$script:testResults = @()



function Log {

    param([string]$Message)

    $timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    "$timestamp - $Message" | Add-Content -Path $logFile -Encoding UTF8

    Write-Host "$timestamp - $Message"

}



function Run-Test {

    param(

        [string]$Name,

        [string]$ScriptPath,

        [string[]]$Arguments = @()

    )

    

    Log "`n[START] $Name"

    Log "Script: $ScriptPath"

    

    if (-not (Test-Path -LiteralPath $ScriptPath)) {

        Log "[SKIP] Script not found: $ScriptPath"

        $script:testResults += @{ Stage = $Name; Status = "SKIP"; Reason = "Script not found" }

        return $true

    }

    

    $pwsh = if (Get-Command "pwsh" -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell.exe" }

    $argList = @("-ExecutionPolicy", "Bypass", "-File", $ScriptPath)

    if ($Arguments -and $Arguments.Length -gt 0) {

        $argList += $Arguments

    }

    

    $command = "$pwsh $($argList -join ' ')"

    Log "Command: $command"

    

    # 使用 Start-Process 让输出实时显示

    $process = Start-Process -FilePath $pwsh -ArgumentList $argList -WorkingDirectory $root -NoNewWindow -PassThru

    

    # 实时输出进程信息，帮助诊断卡住问题

    $timeout = 7200  # 2小时超时

    $checkInterval = 30  # 每30秒检查一次

    $elapsed = 0

    

    while (-not $process.HasExited) {

        Start-Sleep -Seconds $checkInterval

        $elapsed += $checkInterval

        

        if ($elapsed % 60 -eq 0) {

            Log "INFO: $Name is still running... (${elapsed}s elapsed)"

        }

        

        if ($elapsed -ge $timeout) {

            Log "[WARN] $Name timed out after $timeout seconds, terminating..."

            Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue

            break

        }

    }

    

    $exitCode = $process.ExitCode

    

    if ($exitCode -eq 0 -or $exitCode -eq $null -or $exitCode -eq "") {

        Log "[DONE] $Name completed successfully (Exit code: $exitCode)"

        $script:testResults += @{ Stage = $Name; Status = "PASS"; Reason = $null }

        return $true

    } else {

        Log "[FAIL] $Name failed with exit code $exitCode"

        $script:testResults += @{ Stage = $Name; Status = "FAIL"; Reason = "Exit code $exitCode" }

        

        if (-not $ContinueOnError) {

            Log "[STOP] Stopping test flow due to failure (ContinueOnError=$ContinueOnError)"

            return $false

        }

        Log "[WARN] Continuing despite failure (ContinueOnError=$ContinueOnError)"

        return $true

    }

}



function Open-Reports {

    Log "`n[OPENING REPORTS]"

    

    $reports = @(

        @{ Name = "System Test Report"; Path = Join-Path $runDir "reports\系统测试报告.md"; Type = "browser" },

        @{ Name = "UI Test Report"; Path = Join-Path $root "tests\ui\reports\html\index.html"; Type = "playwright" },

        @{ Name = "API Test Report"; Path = Join-Path $root "tests\api\reports\html\report.html"; Type = "browser" }

    )

    

    foreach ($report in $reports) {

        if (Test-Path -LiteralPath $report.Path) {

            try {

                Log "Opening $($report.Name): $($report.Path)"

                if ($report.Type -eq "playwright") {

                    Start-Process -FilePath "npx" -ArgumentList "playwright", "show-report", "tests/ui/reports/html" -WorkingDirectory $root -NoNewWindow -Wait:$false

                } else {

                    Start-Process -FilePath $report.Path

                }

                Start-Sleep -Milliseconds 800

            } catch {

                Log "WARNING: Failed to open $($report.Name): $_"

            }

        } else {

            Log "INFO: $($report.Name) not found at $($report.Path)"

        }

    }

    

    Log "[REPORTS OPENED]"

}



function Show-Results {

    Log "`n[TEST RESULTS SUMMARY]"

    Log "=============================="

    

    $passed = ($testResults | Where-Object { $_.Status -eq "PASS" }).Count

    $failed = ($testResults | Where-Object { $_.Status -eq "FAIL" }).Count

    $skipped = ($testResults | Where-Object { $_.Status -eq "SKIP" }).Count

    

    foreach ($result in $testResults) {

        $statusIcon = switch ($result.Status) {

            "PASS" { "[PASS]" }

            "FAIL" { "[FAIL]" }

            "SKIP" { "[SKIP]" }

            default { "[????]" }

        }

        Log "$statusIcon $($result.Stage): $($result.Status)"

        if ($result.Reason) {

            Log "      Reason: $($result.Reason)"

        }

    }

    

    Log "=============================="

    Log "Total: $($testResults.Count) | Passed: $passed | Failed: $failed | Skipped: $skipped"

}



Log "=============================================="

Log "Starting Full Test Flow - Run ID: $RunId"

Log "Frontend: $FrontendUrl"

Log "API: $ApiBaseUrl"

Log "ContinueOnError: $ContinueOnError"

Log "=============================================="




Log ""

Log "[0/5] Running Coverage Gate Check..."

$coverageScript = Join-Path $root "scripts\scan-test-coverage.py"

if (Test-Path -LiteralPath $coverageScript) {

    $coverageProcess = Start-Process -FilePath "python" -ArgumentList $coverageScript -WorkingDirectory $root -NoNewWindow -PassThru -Wait

    $coverageExitCode = $coverageProcess.ExitCode

    if ($coverageExitCode -ne 0) {

        Log "[FAIL] Coverage gate check failed (Exit code: $coverageExitCode)"

        Log "[STOP] Stopping test flow due to coverage gate failure"

        exit 1

    } else {

        Log "[PASS] Coverage gate check passed"

    }

} else {

    Log "[SKIP] Coverage script not found: $coverageScript"

}




Log ""

Log "[1/5] Running API Full Test..."

$apiResult = Run-Test -Name "API Full" -ScriptPath (Join-Path $root "scripts\run-api-tests.ps1") -Arguments @("-Mode", "full")

if (-not $apiResult -and -not $ContinueOnError) { exit 1 }



Log ""

Log "[2/5] Running UI Test..."

$uiResult = Run-Test -Name "UI" -ScriptPath (Join-Path $root "scripts\run-ui-tests.ps1")

if (-not $uiResult -and -not $ContinueOnError) { exit 1 }



Log ""

Log "[3/5] Running Performance Test..."

$perfResult = Run-Test -Name "Performance" -ScriptPath (Join-Path $root "scripts\run-perf-tests.ps1")

if (-not $perfResult -and -not $ContinueOnError) { exit 1 }



Log ""

Log "[4/5] Running Security Test..."

$securityResult = Run-Test -Name "Security" -ScriptPath (Join-Path $root "scripts\run-security-tests.ps1") -Arguments @("-Target", $FrontendUrl)

if (-not $securityResult -and -not $ContinueOnError) { exit 1 }



Log ""

Log "[5/5] Generating System Test Report..."

$systemReportResult = Run-Test -Name "System Test Report" -ScriptPath (Join-Path $root "scripts\run-system-report.ps1")

if (-not $systemReportResult -and -not $ContinueOnError) { exit 1 }



Show-Results



Log ""

Log "=============================================="

Log "Full Test Flow completed - Run ID: $RunId"

Log "Logs saved to: $logFile"

Log "=============================================="



Open-Reports



exit 0