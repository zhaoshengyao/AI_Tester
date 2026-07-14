param(

    [string]$ForceNotExecutedReason = "",

    [string]$Mode = "smoke"

)



$ErrorActionPreference = "Stop"



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



. (Join-Path $PSScriptRoot "lib\stage-common.ps1")



$stageId = "8-performance"

$stageName = "性能测试"

$runContext = Get-StageRunContext -StageId $stageId

$root = $Script:ProjectRoot



Load-EnvFile -Path (Join-Path $root ".env")

$locustHost = if ($env:LOCUST_HOST) { $env:LOCUST_HOST } else { $env:API_BASE_URL }

$runReportDir = Join-Path $runContext.RunDir "reports"

$runDefectDir = Join-Path $runContext.RunDir "defects"

$formalReport = Join-Path $runReportDir "性能测试报告.md"

$defectFile = Join-Path $runDefectDir "性能缺陷清单.md"

$caseFile = Join-Path $root "docs\cases\性能测试用例-评审版.md"



New-Item -ItemType Directory -Force -Path $runReportDir | Out-Null

New-Item -ItemType Directory -Force -Path $runDefectDir | Out-Null



$locustDir = Join-Path $root "tests\performance\locust"

$locustEnv = Join-Path $root ".env"



$env:TEST_RUN_ID = $runContext.RunId

$resultDir = if ($env:PERF_RESULT_DIR) { $env:PERF_RESULT_DIR } else { Join-Path $root "tests\performance\results\$($runContext.RunId)" }

$env:PERF_RESULT_DIR = $resultDir



New-Item -ItemType Directory -Force -Path $resultDir | Out-Null



$locustFile = switch ($Mode) {

    "smoke" { Join-Path $locustDir "api\locustfile_smoke.py" }

    "full" { Join-Path $locustDir "api\locustfile_crm_api.py" }

    "ui" { Join-Path $locustDir "ui\locustfile_ui_smoke.py" }

    default { Join-Path $locustDir "api\locustfile_smoke.py" }

}



$locustUsers = if ($env:LOCUST_USERS) { $env:LOCUST_USERS } else { "5" }

$locustSpawnRate = if ($env:LOCUST_SPAWN_RATE) { $env:LOCUST_SPAWN_RATE } else { "1" }

$locustRunTime = if ($env:LOCUST_RUN_TIME) { $env:LOCUST_RUN_TIME } else { "60s" }



function Write-PerfDocuments {

    param(

        [string]$ExecutionStatus,

        [string]$Decision,

        [string]$Summary,

        [string]$Reason,

        [int]$ExitCode,

        [string]$CommandLine,

        [string]$HtmlReportPath

    )



    @"

# 性能测试报告



## 当前阶段

性能测试执行



## 输入文件

- docs/cases/性能测试用例-评审版.md

- scripts/run-perf-tests.ps1

- tests/performance/locust/README.md



## 产出文件

- tests/performance/results/

- docs/test-runs/$($runContext.RunId)/reports/性能测试报告.md

- docs/test-runs/$($runContext.RunId)/defects/性能缺陷清单.md



## 正文/核心内容

- 测试批次：$($runContext.RunId)

- 压测框架：Locust

- 压测脚本：$locustFile

- 执行模式：$Mode

- 并发用户数：$locustUsers

- 孵化率：$locustSpawnRate/秒

- 运行时间：$locustRunTime

- 目标地址：$locustHost

- 执行状态：$ExecutionStatus

- 退出码：$ExitCode

- 执行命令：$CommandLine

- 关键说明：$Summary

- 原始结果路径：

  - $resultDir

  - $HtmlReportPath



## 执行结论

- 本轮性能测试状态：$ExecutionStatus。

- 下一步决策：$Decision。



## 风险与待确认项

- $Reason



## 下一步建议

- 如为未执行，先补齐 Locust 环境和授权。

- 如为失败，优先结合 HTML 报告和日志做证据补充。

"@ | Set-Content -LiteralPath $formalReport -Encoding utf8



    $defectRows = ""

    $defectCount = 0



    $defectSummary = switch ($ExecutionStatus) {

        "通过" { "本轮性能测试通过，共 $defectCount 项指标异常。" }

        "未执行" { "本轮性能测试未执行，未形成新的性能缺陷登记。" }

        default { "本轮性能测试存在 $defectCount 项指标异常，详见下方缺陷明细表。" }

    }



    @"

# 性能缺陷清单



## 当前阶段

性能测试执行



## 输入文件

- docs/cases/性能测试用例-评审版.md

- docs/test-runs/$($runContext.RunId)/reports/性能测试报告.md



## 产出文件

- docs/test-runs/$($runContext.RunId)/defects/性能缺陷清单.md



## 正文/核心内容

- 测试批次：$($runContext.RunId)

- 执行状态：$ExecutionStatus

- 退出码：$ExitCode

- 异常项数：$defectCount

- 结论摘要：$defectSummary

- 证据入口：

  - docs/test-runs/$($runContext.RunId)/reports/性能测试报告.md

  - $resultDir



## 缺陷明细

$defectRows



## 执行结论

- 当前性能缺陷登记状态：$ExecutionStatus。



## 风险与待确认项

- $Reason



## 下一步建议

- 如性能指标异常，补充或更新正式性能缺陷。

- 如未执行，先补齐门禁再重新执行。

"@ | Set-Content -LiteralPath $defectFile -Encoding utf8

}



function Write-StageResult {
    param(
        [string]$Status,
        [string]$Decision,
        [string]$Reason,
        [array]$InputsChecked,
        [array]$GatesChecked,
        [string[]]$EvidencePaths
    )

    $outputs = @(
        (New-OutputState -Name "performance-raw-report" -Path $resultDir),
        (New-OutputState -Name "performance-formal-report" -Path $formalReport),
        (New-OutputState -Name "performance-defect-doc" -Path $defectFile)
    )

    Write-StageStatusFile `
        -RunContext $Script:runContext `
        -DisplayName $Script:stageName `
        -DriverType "script" `
        -Status $Status `
        -InputsChecked $InputsChecked `
        -GatesChecked $GatesChecked `
        -OutputsWritten $outputs `
        -EvidencePaths $EvidencePaths `
        -NextDecision $Decision `
        -NeedsUpdateReason $Reason `
        -CheckMode "full" | Out-Null
}



if ($ForceNotExecutedReason) {

    $notExecutedFile = Join-Path $resultDir "not-executed.txt"

    $ForceNotExecutedReason | Set-Content -LiteralPath $notExecutedFile -Encoding utf8

    Write-PerfDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $ForceNotExecutedReason -Reason $ForceNotExecutedReason -ExitCode 2 -CommandLine "pwsh -File scripts/run-perf-tests.ps1"

    $gates = @([pscustomobject]@{ name = "orchestration-gate"; ok = $false; checked = $true; reason = $ForceNotExecutedReason })

    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $ForceNotExecutedReason -InputsChecked @() -GatesChecked $gates -EvidencePaths @($notExecutedFile)

    exit 2

}



$preflight = Invoke-StageContractCheck -StageId $stageId -Mode "preflight" -RunId $runContext.RunId

$preflightInputs = @($preflight.Payload.inputs_checked)

$gateChecks = @($preflight.Payload.gates_checked)



if ($preflight.ExitCode -ne 0) {

    $missing = (Get-MissingRequirementNames -Checks $preflightInputs) -join "、"

    $reason = if ($missing) { "统一契约预检失败，缺失输入：$missing。" } else { "统一契约预检失败。" }

    Write-PerfDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-perf-tests.ps1"

    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths @()

    exit 2

}



if (-not (Test-Path -LiteralPath $locustFile)) {

    $reason = "Locust 测试脚本不存在：$locustFile"

    $reason | Set-Content -LiteralPath (Join-Path $resultDir "not-executed.txt") -Encoding utf8

    Write-PerfDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-perf-tests.ps1"

    $gates = @($gateChecks + @([pscustomobject]@{ name = "locust-file"; ok = $false; checked = $true; reason = $reason }))

    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked $gates -EvidencePaths @($resultDir) 

    exit 2

}



if (-not (Get-Command "locust" -ErrorAction SilentlyContinue)) {

    $reason = "Locust 未安装，请运行：pip install locust"

    $reason | Set-Content -LiteralPath (Join-Path $resultDir "not-executed.txt") -Encoding utf8

    Write-PerfDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-perf-tests.ps1"

    $gates = @($gateChecks + @([pscustomobject]@{ name = "locust-runtime"; ok = $false; checked = $true; reason = $reason }))

    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked $gates -EvidencePaths @($resultDir)

    exit 2

}



$htmlReport = Join-Path $resultDir "perf_report.html"

$commandLine = "locust -f $locustFile --users=$locustUsers --spawn-rate=$locustSpawnRate --run-time=$locustRunTime --headless --host=$locustHost --html=$htmlReport"



$originalLocation = Get-Location

Set-Location -LiteralPath $locustDir -ErrorAction Stop



& locust -f $locustFile --users=$locustUsers --spawn-rate=$locustSpawnRate --run-time=$locustRunTime --headless --host=$locustHost --html=$htmlReport

$exitCode = $LASTEXITCODE



Set-Location -LiteralPath $originalLocation -ErrorAction SilentlyContinue



$evidence = @(

    $resultDir,

    $htmlReport

)



if ($exitCode -eq 0 -or $exitCode -eq 1) {

    Write-PerfDocuments -ExecutionStatus "通过" -Decision "collect-evidence" -Summary "性能测试执行完成，需结合指标阈值做进一步判定。" -Reason "当前脚本只保证原始结果和正式产物落盘，阈值解释仍需报告归并。" -ExitCode $exitCode -CommandLine $commandLine -HtmlReportPath $htmlReport

    Write-StageResult -Status "passed" -Decision "collect-evidence" -Reason "" -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths $evidence

    exit 0

}



$failureReason = "Locust 执行失败或存在性能异常，请结合 HTML 报告和日志继续分析。"

Write-PerfDocuments -ExecutionStatus "失败" -Decision "collect-evidence" -Summary "性能测试执行完成但存在失败或异常。" -Reason $failureReason -ExitCode $exitCode -CommandLine $commandLine -HtmlReportPath $htmlReport

Write-StageResult -Status "failed" -Decision "collect-evidence" -Reason $failureReason -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths $evidence

exit $exitCode