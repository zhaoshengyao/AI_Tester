param(
    [string]$Target,
    [string]$ForceNotExecutedReason
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\stage-common.ps1")

$stageId = "8-security"
$stageName = "安全测试"
$runContext = Get-StageRunContext -StageId $stageId
$root = $Script:ProjectRoot

Write-Host "Using RunId: $($runContext.RunId)"

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

if (-not $Target) {
    $Target = if ($env:BASE_URL) { $env:BASE_URL } else { "http://localhost:3000" }
}

$reportDir = Join-Path $root "tests\security\reports"
$runReportDir = Join-Path $runContext.RunDir "reports"
$runDefectDir = Join-Path $runContext.RunDir "defects"
$formalReport = Join-Path $runReportDir "安全测试报告.md"
$defectFile = Join-Path $runDefectDir "安全缺陷清单.md"
$scanScope = if ($env:SECURITY_SCAN_SCOPE) { $env:SECURITY_SCAN_SCOPE } elseif ($env:ZAP_SCAN_SCOPE) { $env:ZAP_SCAN_SCOPE } else { "" }
$reportHtml = Join-Path $reportDir "security_report.html"
$reportJson = Join-Path $reportDir "security_results.json"
$notExecutedFile = Join-Path $reportDir "not-executed.txt"

New-Item -ItemType Directory -Force -Path $reportDir | Out-Null
New-Item -ItemType Directory -Force -Path $runReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $runDefectDir | Out-Null

function Write-SecurityDocuments {
    param(
        [string]$ExecutionStatus,
        [string]$Decision,
        [string]$Summary,
        [string]$Reason,
        [int]$ExitCode,
        [string]$CommandLine,
        [string[]]$EvidencePaths,
        [string]$ResultJsonPath
    )

    $evidenceText = if ($EvidencePaths -and $EvidencePaths.Count -gt 0) {
        ($EvidencePaths | ForEach-Object { "- ``$_``" }) -join "`r`n"
    } else {
        "- 无"
    }

    $defectRows = ""
    $defectCount = 0
    if ($ResultJsonPath -and (Test-Path -LiteralPath $ResultJsonPath)) {
        try {
            $jsonContent = Get-Content -LiteralPath $ResultJsonPath -Raw -Encoding utf8
            $results = $jsonContent | ConvertFrom-Json
            $defects = $results.vulnerabilities
            $defectCount = $defects.Count
            if ($defectCount -gt 0) {
                $defectRows = "| 序号 | 漏洞名称 | 风险等级 | 缺陷类型 | 影响URL | 漏洞描述 |`n| --- | --- | --- | --- | --- | --- |`n"
                $index = 1
                foreach ($d in $defects) {
                    $safeDesc = $d.evidence -replace "`r?`n", " " -replace "\|", "/"
                    $defectRows += "| $index | $($d.type) | $($d.severity) | $($d.type) | $($d.endpoint) | $safeDesc |`n"
                    $index++
                }
            }
        } catch {
            Write-Host "Error parsing security results JSON: $_"
        }
    }

    $checkInfo = ""
    if ($ResultJsonPath -and (Test-Path -LiteralPath $ResultJsonPath)) {
        try {
            $jsonContent = Get-Content -LiteralPath $ResultJsonPath -Raw -Encoding utf8
            $results = $jsonContent | ConvertFrom-Json
            $checkInfo = @"
- 扫描开始时间: $($results.scan_start)
- 扫描结束时间: $($results.scan_end)
- 扫描耗时: $($results.scan_duration)秒
- 总检查项: $($results.total_checks)
- 通过: $($results.passed_checks)
- 失败: $($results.failed_checks)
"@
        } catch {
            Write-Host "Error parsing security results JSON for check info: $_"
        }
    }

    @"
# 安全测试报告

## 当前阶段
安全测试执行

## 输入文件
- projects/$env:TEST_SYSTEM_ID/docs/cases/安全测试用例-评审版.md
- scripts/run-security-tests.ps1
- tests/security/scanner/security_scanner.py

## 产出文件
- projects/$env:TEST_SYSTEM_ID/tests/security/reports/
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/安全测试报告.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/defects/安全缺陷清单.md

## 正文/核心内容
- 测试批次：$($runContext.RunId)
- 目标地址：$Target
- 扫描范围：$(if ($scanScope) { $scanScope } else { "待确认" })
- 执行状态：$ExecutionStatus
- 退出码：$ExitCode
- 执行命令：$CommandLine
- 执行说明：$Summary
- 扫描详情：
$checkInfo
- 原始结果路径：
$evidenceText

## 执行结论
- 本轮安全测试状态：$ExecutionStatus。
- 下一步决策：$Decision。

## 风险与待确认项
- $Reason

## 下一步建议
- 如为未执行，先确认扫描范围、授权方式。
- 如为失败，结合 HTML/JSON 报告补充漏洞证据并明确误报风险。
"@ | Set-Content -LiteralPath $formalReport -Encoding utf8

    $defectSummary = switch ($ExecutionStatus) {
        "通过" { "本轮安全测试已执行，发现 $defectCount 项漏洞/告警。" }
        "未执行" { "本轮安全测试未执行，未形成新的安全漏洞登记。" }
        default { "本轮安全测试发现 $defectCount 项漏洞/告警，详见下方缺陷明细表。" }
    }

    @"
# 安全缺陷清单

## 当前阶段
安全测试执行

## 输入文件
- projects/$env:TEST_SYSTEM_ID/docs/cases/安全测试用例-评审版.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/安全测试报告.md

## 产出文件
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/defects/安全缺陷清单.md

## 正文/核心内容
- 测试批次：$($runContext.RunId)
- 执行状态：$ExecutionStatus
- 退出码：$ExitCode
- 漏洞/告警数：$defectCount
- 结论摘要：$defectSummary
- 证据入口：
$evidenceText

## 缺陷明细
$defectRows

## 执行结论
- 当前安全缺陷登记状态：$ExecutionStatus。

## 风险与待确认项
- $Reason

## 下一步建议
- 若确认存在真实安全问题，补录正式漏洞项和复测条件。
- 若未执行，补齐授权和扫描边界后重跑。
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
        (New-OutputState -Name "security-raw-report" -Path $reportDir),
        (New-OutputState -Name "security-formal-report" -Path $formalReport),
        (New-OutputState -Name "security-defect-doc" -Path $defectFile)
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

$preflight = Invoke-StageContractCheck -StageId $stageId -Mode "preflight" -RunId $runContext.RunId
$preflightInputs = @($preflight.Payload.inputs_checked)
$gateChecks = @($preflight.Payload.gates_checked)

$scannerScript = Join-Path $root "tests\security\scanner\security_scanner.py"
$apiUsername = if ($env:API_USERNAME) { $env:API_USERNAME } else { "" }
$apiPassword = if ($env:API_PASSWORD) { $env:API_PASSWORD } else { "" }
$apiClientId = if ($env:API_CLIENT_ID) { $env:API_CLIENT_ID } else { "" }

$argsList = @("--host", $Target, "--output", $reportDir)
if ($env:API_BASE_URL) { $argsList += @("--api-url", $env:API_BASE_URL) }
if ($apiUsername) { $argsList += @("--username", $apiUsername) }
if ($apiPassword) { $argsList += @("--password", $apiPassword) }
if ($apiClientId) { $argsList += @("--client-id", $apiClientId) }

$commandLine = "python $scannerScript $($argsList -join ' ')"

Write-Host "Executing security scan..."
Write-Host "Command: $commandLine"

python $scannerScript $argsList
$exitCode = $LASTEXITCODE

Write-Host "Security scan completed with exit code: $exitCode"

$evidence = @()
foreach ($path in @($reportHtml, $reportJson, $notExecutedFile)) {
    if (Test-Path -LiteralPath $path) {
        $evidence += $path
    }
}

if ($exitCode -eq 0) {
    $reason = "安全扫描执行完成，未发现高危漏洞。但漏洞定级和误报判断仍需结合报告进一步确认。"
    Write-SecurityDocuments -ExecutionStatus "通过" -Decision "collect-evidence" -Summary "Python安全扫描器执行完成。" -Reason $reason -ExitCode $exitCode -CommandLine $commandLine -EvidencePaths $evidence -ResultJsonPath $reportJson
    Write-StageResult -Status "passed" -Decision "collect-evidence" -Reason "" -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths $evidence
    exit 0
}

$failureReason = "安全扫描执行完成但发现需要人工确认的安全风险，请结合 HTML/JSON 报告继续分析。"
Write-SecurityDocuments -ExecutionStatus "失败" -Decision "collect-evidence" -Summary "安全测试执行完成但存在风险待确认。" -Reason $failureReason -ExitCode $exitCode -CommandLine $commandLine -EvidencePaths $evidence -ResultJsonPath $reportJson
Write-StageResult -Status "failed" -Decision "collect-evidence" -Reason $failureReason -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths $evidence
exit $exitCode
