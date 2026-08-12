param(
    [string]$ForceNotExecutedReason = ""
)

$ErrorActionPreference = "Stop"

. (Join-Path $PSScriptRoot "lib\stage-common.ps1")

$stageId = "6-ui-automation"
$stageName = "UI 自动化"
$runContext = Get-StageRunContext -StageId $stageId
$root = $Script:ProjectRoot
$rawReportDir = Join-Path $root "tests\ui\reports"
$runReportDir = Join-Path $runContext.RunDir "reports"
$runDefectDir = Join-Path $runContext.RunDir "defects"
$formalReport = Join-Path $runReportDir "UI自动化测试报告.md"
$compatReport = Join-Path $runReportDir "UI兼容性测试报告.md"
$defectFile = Join-Path $runDefectDir "UI缺陷清单.md"

New-Item -ItemType Directory -Force -Path $runReportDir | Out-Null
New-Item -ItemType Directory -Force -Path $runDefectDir | Out-Null
New-Item -ItemType Directory -Force -Path $rawReportDir | Out-Null

function Write-UiDocuments {
    param(
        [string]$ExecutionStatus,
        [string]$Decision,
        [string]$Summary,
        [string]$Reason,
        [int]$ExitCode,
        [string]$CommandLine,
        [string]$PlaywrightJsonPath
    )

    @"
# UI自动化测试报告

## 当前阶段
UI 自动化执行

## 输入文件
- projects/$env:TEST_SYSTEM_ID/docs/cases/功能测试用例-评审版.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI自动化覆盖矩阵.md
- scripts/run-ui-tests.ps1

## 产出文件
- projects/$env:TEST_SYSTEM_ID/tests/ui/reports/
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI自动化测试报告.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI兼容性测试报告.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/defects/UI缺陷清单.md

## 正文/核心内容
- 测试批次：$($runContext.RunId)
- 前端地址：$env:BASE_URL
- 执行状态：$ExecutionStatus
- 退出码：$ExitCode
- 执行命令：$CommandLine
- 执行说明：$Summary
- 原始结果路径：
  - projects/$env:TEST_SYSTEM_ID/tests/ui/reports/html/
  - projects/$env:TEST_SYSTEM_ID/tests/ui/reports/raw/result.json

## 执行结论
- 本轮 UI 自动化状态：$ExecutionStatus。
- 下一步决策：$Decision。

## 风险与待确认项
- $Reason

## 下一步建议
- 如果执行失败，优先查看 Playwright HTML 报告与 JSON 结果定位阻断点。
- 如果执行通过，再结合覆盖矩阵判断是否可进入性能和安全后置专项。
"@ | Set-Content -LiteralPath $formalReport -Encoding utf8

    @"
# UI兼容性测试报告

## 当前阶段
UI 兼容性执行

## 输入文件
- projects/$env:TEST_SYSTEM_ID/docs/cases/功能测试用例-评审版.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI自动化覆盖矩阵.md

## 产出文件
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI兼容性测试报告.md

## 正文/核心内容
- 测试批次：$($runContext.RunId)
- 当前默认执行项目：Chromium
- 执行状态：$ExecutionStatus
- 兼容性口径：本入口默认只保证 Chromium 功能自动化；Firefox/Edge 未显式启用时记为未执行。

## 执行结论
- Chromium：$ExecutionStatus。
- Firefox/Edge：未执行，除非显式启用兼容性项目。

## 风险与待确认项
- $Reason

## 下一步建议
- 如需完整兼容性结论，单独启用 Firefox/Edge 项目并补齐对应执行记录。
"@ | Set-Content -LiteralPath $compatReport -Encoding utf8

    $defectRows = ""
    $defectCount = 0
    if ($PlaywrightJsonPath -and (Test-Path -LiteralPath $PlaywrightJsonPath)) {
        $defects = Get-PlaywrightDefects -ResultJsonPath $PlaywrightJsonPath
        $defectCount = $defects.Count
        if ($defectCount -gt 0) {
            $defectRows = "| 序号 | 模块 | 用例编号 | 用例标题 | 缺陷类型 | 耗时(ms) | 错误摘要 |\n| --- | --- | --- | --- | --- | ---: | --- |\n"
            foreach ($d in $defects) {
                $defectRows += "| $($d.Index) | $($d.Module) | $($d.CaseId) | $($d.CaseTitle) | $($d.DefectType) | $($d.Duration) | $($d.ShortMessage) |\n"
            }
        }
    }

    $defectSummary = switch ($ExecutionStatus) {
        "通过" { "本轮 UI 自动化未新增执行级缺陷，共 0 条失败用例。" }
        "未执行" { "本轮 UI 自动化未执行，未形成新的产品缺陷登记。" }
        default { "本轮 UI 自动化存在 $defectCount 条失败用例，详见下方缺陷明细表。" }
    }

    @"
# UI缺陷清单

## 当前阶段
UI 自动化执行

## 输入文件
- projects/$env:TEST_SYSTEM_ID/docs/cases/功能测试用例-评审版.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI自动化覆盖矩阵.md
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI自动化测试报告.md

## 产出文件
- projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/defects/UI缺陷清单.md

## 正文/核心内容
- 测试批次：$($runContext.RunId)
- 执行状态：$ExecutionStatus
- 退出码：$ExitCode
- 失败用例数：$defectCount
- 结论摘要：$defectSummary
- 证据入口：
  - projects/$env:TEST_SYSTEM_ID/test-runs/$($runContext.RunId)/reports/UI自动化测试报告.md
  - projects/$env:TEST_SYSTEM_ID/tests/ui/reports/html/
  - projects/$env:TEST_SYSTEM_ID/tests/ui/reports/raw/result.json

## 缺陷明细
$defectRows

## 执行结论
- 当前缺陷登记状态：$ExecutionStatus。

## 风险与待确认项
- $Reason

## 下一步建议
- 如有失败用例，补充或更新正式 UI 缺陷。
- 如未执行，先恢复前端地址、浏览器或依赖后再执行。
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
        (New-OutputState -Name "ui-raw-report" -Path $rawReportDir),
        (New-OutputState -Name "ui-formal-report" -Path $formalReport),
        (New-OutputState -Name "ui-compat-report" -Path $compatReport),
        (New-OutputState -Name "ui-defect-doc" -Path $defectFile)
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

# 从 system.yaml 加载系统配置
$systemConfig = Get-SystemConfig

if (-not $env:BASE_URL) {
    if ($systemConfig.UiBaseUrl) {
        $env:BASE_URL = $systemConfig.UiBaseUrl
    } elseif ($systemConfig.BaseUrl) {
        $env:BASE_URL = $systemConfig.BaseUrl
    } else {
        $env:BASE_URL = "http://192.168.2.97:6089"
    }
}

if ($ForceNotExecutedReason) {
    $notExecutedFile = Join-Path $rawReportDir "not-executed.txt"
    $ForceNotExecutedReason | Set-Content -LiteralPath $notExecutedFile -Encoding utf8
    Write-UiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $ForceNotExecutedReason -Reason $ForceNotExecutedReason -ExitCode 2 -CommandLine "pwsh -File scripts/run-ui-tests.ps1"
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
    Write-UiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-ui-tests.ps1"
    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked $gateChecks -EvidencePaths @()
    exit 2
}

$dependencyGates = New-Object System.Collections.Generic.List[object]
Set-Location "$root\tests\ui"

try {
    $nodeMajorText = (& node -p "process.versions.node.split('.')[0]").Trim()
    $nodeVersion = (& node -v).Trim()
    $nodeMajor = [int]$nodeMajorText
    $dependencyGates.Add([pscustomobject]@{ name = "node-runtime"; ok = $true; checked = $true; reason = "Node.js $nodeVersion" })
} catch {
    $reason = "未找到可用 Node.js，UI 自动化未执行。"
    $dependencyGates.Add([pscustomobject]@{ name = "node-runtime"; ok = $false; checked = $true; reason = $reason })
    Write-UiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-ui-tests.ps1"
    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked @($gateChecks + $dependencyGates) -EvidencePaths @()
    exit 2
}

if ($nodeMajor -lt 18) {
    $reason = "当前 Node.js 版本为 $nodeVersion，低于 UI 自动化最低要求 Node.js 18。"
    $dependencyGates.Add([pscustomobject]@{ name = "node-version"; ok = $false; checked = $true; reason = $reason })
    Write-UiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-ui-tests.ps1"
    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked @($gateChecks + $dependencyGates) -EvidencePaths @()
    exit 2
}

$nodeVersionReason = if ($nodeMajor -gt 22) {
    "Node.js $nodeVersion 高于常见 LTS 版本，但当前 Playwright 依赖声明支持 Node 18+，允许执行并以真实运行结果为准。"
} else {
    "Node.js $nodeVersion 满足 UI 自动化最低要求。"
}
$dependencyGates.Add([pscustomobject]@{ name = "node-version"; ok = $true; checked = $true; reason = $nodeVersionReason })

$candidates = @(
    $env:CHROMIUM_EXECUTABLE_PATH,
    "C:\Program Files\Google\Chrome\Application\chrome.exe",
    "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    "C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    "C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe"
) | Where-Object { $_ -and (Test-Path -LiteralPath $_) }

# 动态查找 playwright 安装的 Chromium
$playwrightDirs = Get-ChildItem -Path "$env:LOCALAPPDATA\ms-playwright" -Filter "chromium-*" -Directory -ErrorAction SilentlyContinue
foreach ($dir in $playwrightDirs) {
    $chromiumPath = Join-Path $dir.FullName "chrome-win\chrome.exe"
    if (Test-Path -LiteralPath $chromiumPath) {
        $candidates += $chromiumPath
    }
}

# 去重
$candidates = $candidates | Select-Object -Unique

if (-not $candidates -or $candidates.Count -eq 0) {
    $reason = "未找到可用 Chromium/Chrome/Edge 浏览器，UI 自动化未执行。"
    $dependencyGates.Add([pscustomobject]@{ name = "browser-runtime"; ok = $false; checked = $true; reason = $reason })
    Write-UiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode 2 -CommandLine "pwsh -File scripts/run-ui-tests.ps1"
    Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked @($gateChecks + $dependencyGates) -EvidencePaths @()
    exit 2
}

$env:CHROMIUM_EXECUTABLE_PATH = $candidates[0]
$dependencyGates.Add([pscustomobject]@{ name = "browser-runtime"; ok = $true; checked = $true; reason = $env:CHROMIUM_EXECUTABLE_PATH })

if (Test-Path "node_modules") {
    Write-Host "检测到 node_modules，跳过依赖安装。"
} elseif (Test-Path "package-lock.json") {
    npm ci
    if ($LASTEXITCODE -ne 0) {
        $reason = "npm ci 执行失败。"
        Write-UiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode $LASTEXITCODE -CommandLine "npm ci"
        Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked @($gateChecks + $dependencyGates) -EvidencePaths @()
        exit $LASTEXITCODE
    }
} else {
    npm install
    if ($LASTEXITCODE -ne 0) {
        $reason = "npm install 执行失败。"
        Write-UiDocuments -ExecutionStatus "未执行" -Decision "stop" -Summary $reason -Reason $reason -ExitCode $LASTEXITCODE -CommandLine "npm install"
        Write-StageResult -Status "not_executed" -Decision "stop" -Reason $reason -InputsChecked $preflightInputs -GatesChecked @($gateChecks + $dependencyGates) -EvidencePaths @()
        exit $LASTEXITCODE
    }
}

$commandLine = "npm run test -- --project=chromium --workers=1"
$playwrightJsonPath = Join-Path $root "tests\ui\reports\raw\result.json"
npm run test -- --project=chromium --workers=1
$exitCode = $LASTEXITCODE

$evidence = @(
    "projects/$env:TEST_SYSTEM_ID/tests/ui/reports",
    "projects/$env:TEST_SYSTEM_ID/tests/ui/reports/html",
    "projects/$env:TEST_SYSTEM_ID/tests/ui/reports/raw/result.json"
)

if ($exitCode -eq 0) {
    Write-UiDocuments -ExecutionStatus "通过" -Decision "continue" -Summary "UI 自动化执行完成，正式产物与原始结果已落盘。" -Reason "兼容性仅默认覆盖 Chromium；Firefox/Edge 需单独执行。" -ExitCode $exitCode -CommandLine $commandLine -PlaywrightJsonPath $playwrightJsonPath
    Write-StageResult -Status "passed" -Decision "continue" -Reason "" -InputsChecked $preflightInputs -GatesChecked @($gateChecks + $dependencyGates) -EvidencePaths $evidence
    exit 0
}

$failureReason = "Playwright 执行失败或存在失败用例，请结合 HTML/JSON 报告定位。"
Write-UiDocuments -ExecutionStatus "失败" -Decision "handoff" -Summary "UI 自动化执行完成但存在失败。" -Reason $failureReason -ExitCode $exitCode -CommandLine $commandLine -PlaywrightJsonPath $playwrightJsonPath
Write-StageResult -Status "failed" -Decision "handoff" -Reason $failureReason -InputsChecked $preflightInputs -GatesChecked @($gateChecks + $dependencyGates) -EvidencePaths $evidence
exit $exitCode
