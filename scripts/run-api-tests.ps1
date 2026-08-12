﻿﻿﻿﻿param(
    [ValidateSet("smoke", "full", "failed-retest")]
    [string]$Mode = "full",
    [int]$RequestTimeoutSeconds = 10,
    [string]$PytestKeyword = "",
    [string]$ForceNotExecutedReason = ""
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\stage-common.ps1")

$stageId = "5-api-automation"
$stageName = "API 自动化"
$runContext = Get-StageRunContext -StageId $stageId
$root = $Script:ProjectRoot
$rawReportDir = Join-Path $root "tests\api\reports"
$runReportDir = Join-Path $runContext.RunDir "reports"
$runDefectDir = Join-Path $runContext.RunDir "defects"
$formalReport = Join-Path $runReportDir "接口自动化测试报告.md"
$defectFile = Join-Path $runDefectDir "接口缺陷清单.md"
$caseFile = Join-Path $root "docs\cases\接口测试用例-评审版.md"
$matrixFile = Join-Path $runReportDir "API自动化覆盖矩阵.md"

New-Item -ItemType Directory -Force -Path $runReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $runDefectDir | Out-Null
New-Item -ItemType Directory -Force -Path $rawReportDir | Out-Null

function Write-ApiDocuments {
    param(
        [string]$ExecutionStatus,
        [string]$Decision,
        [string]$Summary,
        [string]$Reason,
        [int]$ExitCode,
        [string]$CommandLine,
        [string[]]$EvidencePaths,
        [string]$JunitXmlPath = ""
    )

    $rawPaths = @(
        "projects/$env:TEST_SYSTEM_ID/tests/api/reports/html/report.html",
        "projects/$env:TEST_SYSTEM_ID/tests/api/reports/junit/report.xml",
        "projects/$env:TEST_SYSTEM_ID/tests/api/reports/raw/api-test.log"
    )

    @"
# 接口自动化测试报告

## 当前阶段
接口自动化执行

## 输入文件
- projects/$env:TEST_SYSTEM_ID/docs/cases/接口测试用例-评审版.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/API自动化覆盖矩阵.md
- scripts/run-api-tests.ps1

## 产出文件
- projects/$env:TEST_SYSTEM_ID/tests/api/reports/
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/接口自动化测试报告.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/defects/接口缺陷清单.md

## 正文/核心内容
- 测试批次：$($runContext.RunId)
- 执行模式：$Mode
- pytest 关键字过滤：$(if ($PytestKeyword) { $PytestKeyword } else { "未设置" })
- 接口地址：$env:API_BASE_URL
- 请求超时秒数：$RequestTimeoutSeconds
- 执行状态：$ExecutionStatus
- 退出码：$ExitCode
- 执行命令：$CommandLine
- 关键说明：$Summary
- 原始结果路径：
  - projects/$env:TEST_SYSTEM_ID/tests/api/reports/html/report.html
  - projects/$env:TEST_SYSTEM_ID/tests/api/reports/junit/report.xml
  - projects/$env:TEST_SYSTEM_ID/tests/api/reports/raw/api-test.log

## 执行结论
- 本轮接口自动化状态：$ExecutionStatus。
- 下一步决策：$Decision。

## 风险与待确认项
- $Reason

## 下一步建议
- 如为未执行或失败，优先检查评审版输入、覆盖矩阵、服务连通性与登录态。
- 如为通过，继续结合覆盖矩阵和原始报告确认是否可进入下一专项。
"@ | Set-Content -LiteralPath $formalReport -Encoding utf8

    $defectRows = ""
    $defectCount = 0
    if ($JunitXmlPath -and (Test-Path -LiteralPath $JunitXmlPath)) {
        $defects = Get-JUnitDefects -JunitXmlPath $JunitXmlPath
        $defectCount = $defects.Count
        if ($defectCount -gt 0) {
            $defectRows = "| 序号 | 模块 | 用例名称 | 缺陷类型 | 严重程度 | 耗时(s) | 错误摘要 |`n| --- | --- | --- | --- | --- | ---: | --- |`n"
            foreach ($d in $defects) {
                $severity = Get-DefectSeverity -DefectType $d.DefectType
                $safeMsg = $d.ShortMessage -replace "`n", " " -replace "\|", "\|"
                $defectRows += "| $($d.Index) | $($d.Module) | $($d.TestName) | $($d.DefectType) | $severity | $($d.Duration) | $safeMsg |`n"
            }
        }
    }

    $defectSummary = switch ($ExecutionStatus) {
        "通过" { "本轮接口自动化未新增执行级缺陷。" }
        "未执行" { "本轮接口自动化未执行，未形成新的产品缺陷登记。" }
        default { "本轮接口自动化共 $defectCount 项用例失败，详见下方缺陷明细表。" }
    }

    @"
# 接口缺陷清单

## 当前阶段
接口自动化执行

## 输入文件
- projects/$env:TEST_SYSTEM_ID/docs/cases/接口测试用例-评审版.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/API自动化覆盖矩阵.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/接口自动化测试报告.md

## 产出文件
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/defects/接口缺陷清单.md

## 正文/核心内容
- 测试批次：$($runContext.RunId)
- 执行状态：$ExecutionStatus
- 退出码：$ExitCode
- 失败用例数：$defectCount
- 结论摘要：$defectSummary
- 证据入口：
  - projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/接口自动化测试报告.md
  - projects/$env:TEST_SYSTEM_ID/tests/api/reports/junit/report.xml
  - projects/$env:TEST_SYSTEM_ID/tests/api/reports/raw/api-test.log

## 缺陷明细
$defectRows

## 执行结论
- 当前缺陷登记状态：$ExecutionStatus。
- 需结合原始结果与覆盖矩阵继续归并缺陷。

## 风险与待确认项
- $Reason

## 下一步建议
- 如果原始结果出现断言失败，按模块补充或更新正式产品缺陷。
- 如果本轮未执行，先补齐门禁条件后再执行。
"@ | Set-Content -LiteralPath $defectFile -Encoding utf8
}

function Write-StageResult {
    param(
        [string]$Status,
        [string]$Decision,
        [string]$Reason,
        [array]$InputsChecked,
        [array]$GatesChecked,
        [array]$EvidencePaths,
        [int]$ExitCode
    )

    $outputs = @(
        (New-OutputState -Name "api-raw-report" -Path $rawReportDir),
        (New-OutputState -Name "api-formal-report" -Path $formalReport),
        (New-OutputState -Name "api-defect-doc" -Path $defectFile)
    )

    Write-StageStatusFile `
        -RunContext $runContext `
        -DisplayName $stageName `
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

$env:TEST_RUN_ID = $runContext.RunId
$env:API_TIMEOUT_SECONDS = "$RequestTimeoutSeconds"

# 从 system.yaml 加载系统配置
$systemConfig = Get-SystemConfig

if (-not $env:API_BASE_URL) {
    if ($systemConfig.BaseUrl) {
        $cleanBase = $systemConfig.BaseUrl.TrimEnd('/')
        $cleanPath = $systemConfig.ApiBasePath.TrimStart('/')
        $env:API_BASE_URL = "$cleanBase/$cleanPath"
    } else {
        $env:API_BASE_URL = "http://192.168.2.97:6089/prod-api"
    }
}
if (-not $env:API_USERNAME) {
    $env:API_USERNAME = if ($env:TEST_USERNAME) { $env:TEST_USERNAME } else { "ZhaoShengYao" }
}

# 使用 system.yaml 配置的测试目录
if ($systemConfig.ApiTestsDir) {
    $testRoot = Join-Path $root $systemConfig.ApiTestsDir
    if (Test-Path -LiteralPath $testRoot) {
        Set-Location $testRoot
    }
}

if ($ForceNotExecutedReason) {
    $notExecutedFile = Join-Path $rawReportDir "not-executed.txt"
    $ForceNotExecutedReason | Set-Content -LiteralPath $notExecutedFile -Encoding utf8
    Write-ApiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $ForceNotExecutedReason -Reason $ForceNotExecutedReason -ExitCode 2 -CommandLine "pwsh -File scripts/run-api-tests.ps1 -Mode $Mode" -EvidencePaths @($notExecutedFile)
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
    Write-ApiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-api-tests.ps1 -Mode $Mode" -EvidencePaths @()
    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths @() -ExitCode 2
    exit 2
}

$pythonExe = "python"
$depsReady = $false
$dependencyReason = ""
Set-Location "$root\tests\api"

try {
    & $pythonExe -c "import pytest, requests, yaml, pytest_html" | Out-Null
    $depsReady = ($LASTEXITCODE -eq 0)
} catch {
    $depsReady = $false
}

try {
    if (-not $depsReady -and -not (Test-Path ".venv")) {
        python -m venv .venv
    }

    if (-not $depsReady) {
        $pythonExe = ".\.venv\Scripts\python.exe"
        & $pythonExe -m pip install -r requirements.txt
        if ($LASTEXITCODE -ne 0) {
            throw "Python 依赖安装失败，退出码 $LASTEXITCODE。"
        }
    }
} catch {
    $dependencyReason = $_.Exception.Message
    Write-ApiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary "依赖准备失败。" -Reason $dependencyReason -ExitCode 2 -CommandLine "pwsh -File scripts/run-api-tests.ps1 -Mode $Mode" -EvidencePaths @()
    $allGates = @($gateChecks + @([pscustomobject]@{ name = "python-dependencies"; ok = $false; checked = $true; reason = $dependencyReason }))
    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $dependencyReason -InputsChecked $preflightInputs -GatesChecked $allGates -EvidencePaths @() -ExitCode 2
    exit 2
}

New-Item -ItemType Directory -Force -Path "reports\raw" | Out-Null
Remove-Item -LiteralPath "reports\raw\api-test.log" -Force -ErrorAction SilentlyContinue

New-Item -ItemType Directory -Force -Path "reports\junit" | Out-Null
New-Item -ItemType Directory -Force -Path "reports\html" | Out-Null

$pytestArgs = @()
if ($Mode -eq "smoke") {
    $pytestArgs += @("-m", "smoke", "--maxfail=1")
}
if ($Mode -eq "failed-retest") {
    $pytestArgs += @("-m", "retest")
}
if ($PytestKeyword) {
    $pytestArgs += @("-k", $PytestKeyword)
}

$commandLine = "python -m pytest $($pytestArgs -join ' ')".Trim()
& $pythonExe -m pytest @pytestArgs
$exitCode = $LASTEXITCODE

$evidence = @(
    "projects/$env:TEST_SYSTEM_ID/tests/api/reports",
    "projects/$env:TEST_SYSTEM_ID/tests/api/reports/html/report.html",
    "projects/$env:TEST_SYSTEM_ID/tests/api/reports/junit/report.xml",
    "projects/$env:TEST_SYSTEM_ID/tests/api/reports/raw/api-test.log"
)

$junitXmlPath = Join-Path $root "tests\api\reports\junit\report.xml"

if ($exitCode -eq 0) {
    Write-ApiDocuments -ExecutionStatus "通过" -Decision "continue" -Summary "接口自动化执行完成，正式产物与原始结果已落盘。" -Reason "待结合覆盖矩阵确认执行范围和未实现项。" -ExitCode $exitCode -CommandLine $commandLine -EvidencePaths $evidence -JunitXmlPath $junitXmlPath
    Write-StageResult -Status "passed" -Decision "continue" -Reason "" -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths $evidence -ExitCode $exitCode
    exit 0
}

$failureReason = "pytest 执行失败或存在失败用例，详见缺陷清单明细表。"
Write-ApiDocuments -ExecutionStatus "失败" -Decision "handoff" -Summary "接口自动化执行完成但存在失败。" -Reason $failureReason -ExitCode $exitCode -CommandLine $commandLine -EvidencePaths $evidence -JunitXmlPath $junitXmlPath
Write-StageResult -Status "failed" -Decision "handoff" -Reason $failureReason -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths $evidence -ExitCode $exitCode
exit $exitCode
