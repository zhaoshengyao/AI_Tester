param(

    [string]$FrontendUrl = "",

    [string]$ApiBaseUrl = "",

    [string]$Username = "",

    [string]$Password = "",

    [string]$RunId = "",

    [int]$UiTimeoutSeconds = 900,

    [int]$ApiTimeoutSeconds = 240,

    [int]$PerfTimeoutSeconds = 300,

    [int]$SecurityTimeoutSeconds = 300,

    [string]$EndStage = "",

    [string[]]$Stages = @()

)



$envFile = Join-Path $PSScriptRoot "..\.env"

if (Test-Path -LiteralPath $envFile) {

    Get-Content -LiteralPath $envFile -Encoding utf8 | ForEach-Object {

        if ($_ -match '^([A-Z_]+)=(.+)$') {

            $name = $matches[1]

            $value = $matches[2] -replace '^["'']|["'']$', ''

            if (-not (Get-Item "Env:\$name" -ErrorAction SilentlyContinue)) {

                Set-Item -Path "Env:\$name" -Value $value

            }

        }

    }

}



if (-not $FrontendUrl) {

    $FrontendUrl = if ($env:BASE_URL) { $env:BASE_URL } else { "http://192.168.2.97:6089" }

}

if (-not $ApiBaseUrl) {

    $ApiBaseUrl = if ($env:API_BASE_URL) { $env:API_BASE_URL } else { "http://192.168.2.97:6089/prod-api" }

}

if (-not $Username) {

    $Username = if ($env:TEST_USERNAME) { $env:TEST_USERNAME } else { "ZhaoShengYao" }

}

if (-not $Password) {

    $Password = if ($env:TEST_PASSWORD) { $env:TEST_PASSWORD } else { "" }

}

if (-not $RunId) {

    $RunId = Get-Date -Format "yyyyMMdd-HHmmss"

}



$ErrorActionPreference = "Continue"



. (Join-Path $PSScriptRoot "lib\stage-common.ps1")



$allStages = @(

    "manifest-validation",

    "1-req-analysis",

    "2-test-design", 

    "3-case-generation",

    "4-case-review",

    "service-precheck",

    "api-smoke",

    "api",

    "ui",

    "performance",

    "security",

    "10-system-test-report",

    "11-knowledge-base"

)



function Test-ShouldExecuteStage {

    param(

        [string]$StageName

    )



    if (-not $EndStage -and $Stages.Count -eq 0) {

        return $true

    }



    if ($Stages.Count -gt 0) {

        return $Stages -contains $StageName

    }



    if ($EndStage) {

        $currentIndex = [array]::IndexOf($allStages, $StageName)

        $endIndex = [array]::IndexOf($allStages, $EndStage)

        return $currentIndex -le $endIndex

    }



    return $true

}



function Get-StageCompletionReason {

    param(

        [string]$StageName

    )



    if (-not $EndStage -and $Stages.Count -eq 0) {

        return $null

    }



    if ($Stages.Count -gt 0 -and ($Stages -notcontains $StageName)) {

        return "未在指定的执行阶段列表中：$($Stages -join ', ')"

    }



    if ($EndStage) {

        $currentIndex = [array]::IndexOf($allStages, $StageName)

        $endIndex = [array]::IndexOf($allStages, $EndStage)

        if ($currentIndex -gt $endIndex) {

            return "已到达指定的结束阶段：$EndStage"

        }

    }



    return $null

}



$root = Resolve-Path "$PSScriptRoot\.."

Set-Location $root



$env:BASE_URL = $FrontendUrl

$env:API_BASE_URL = $ApiBaseUrl

$env:TEST_USERNAME = $Username

$env:TEST_RUN_ID = $RunId

if ($Password) {

    $env:TEST_PASSWORD = $Password

}



$runDir = Join-Path $root "docs\test-runs\$RunId"

$runReportDir = Join-Path $runDir "reports"

$runDefectDir = Join-Path $runDir "defects"

$runRawDir = Join-Path $runDir "raw"

$stageStatusDir = Join-Path $runDir "stage-status"

$perfResultDir = if ($env:PERF_RESULT_DIR) { $env:PERF_RESULT_DIR } else { Join-Path $root "tests\performance\results\$RunId" }

$env:PERF_RESULT_DIR = $perfResultDir

$env:TEST_RUN_DIR = $runDir

$env:STAGE_STATUS_DIR = $stageStatusDir

$logDir = Join-Path $runRawDir "run-logs"



foreach ($path in @($runDir, $runReportDir, $runDefectDir, $runRawDir, $stageStatusDir, $logDir)) {

    New-Item -ItemType Directory -Force -Path $path | Out-Null

}



function New-FlowResult {

    param(

        [string]$Name,

        [string]$Status,

        [int]$ExitCode,

        [string]$Stdout,

        [string]$Stderr,

        [string]$Command,

        [datetime]$StartedAt,

        [datetime]$FinishedAt

    )



    [pscustomobject]@{

        Name = $Name

        Status = $Status

        ExitCode = $ExitCode

        StartedAt = $StartedAt

        FinishedAt = $FinishedAt

        DurationSeconds = [int]($FinishedAt - $StartedAt).TotalSeconds

        Stdout = $Stdout

        Stderr = $Stderr

        Command = $Command

    }

}



function New-SkippedStep {

    param(

        [string]$Name,

        [string]$Reason

    )



    $startedAt = Get-Date

    $stdout = Join-Path $logDir "$Name.stdout.log"

    $stderr = Join-Path $logDir "$Name.stderr.log"

    $Reason | Set-Content -LiteralPath $stdout -Encoding utf8

    "" | Set-Content -LiteralPath $stderr -Encoding utf8

    $finishedAt = Get-Date

    return New-FlowResult -Name $Name -Status "未执行" -ExitCode 2 -Stdout $stdout -Stderr $stderr -Command "未执行：$Reason" -StartedAt $startedAt -FinishedAt $finishedAt

}



function Invoke-ManifestValidation {

    $startedAt = Get-Date

    $stdout = Join-Path $logDir "manifest-validation.stdout.log"

    $stderr = Join-Path $logDir "manifest-validation.stderr.log"

    $command = "python scripts/stage_contract.py validate-manifests"



    $jsonText = & python (Join-Path $root "scripts\stage_contract.py") validate-manifests

    $exitCode = $LASTEXITCODE

    $jsonText | Set-Content -LiteralPath $stdout -Encoding utf8

    "" | Set-Content -LiteralPath $stderr -Encoding utf8

    $finishedAt = Get-Date

    $status = if ($exitCode -eq 0) { "通过" } else { "失败" }



    New-FlowResult -Name "manifest-validation" -Status $status -ExitCode $exitCode -Stdout $stdout -Stderr $stderr -Command $command -StartedAt $startedAt -FinishedAt $finishedAt

}



function Convert-StageStatusToFlowLabel {

    param([string]$StageStatus)



    switch ($StageStatus) {

        "completed" { "通过" }

        "ready" { "通过" }

        "needs_update" { "需更新" }

        "blocked" { "未执行" }

        "not_ready" { "未执行" }

        default { "失败" }

    }

}



function Invoke-StageCheckResult {

    param(

        [string]$Name,

        [string]$StageId,

        [string]$Mode = "full"

    )



    $startedAt = Get-Date

    $stdout = Join-Path $logDir "$Name.stdout.log"

    $stderr = Join-Path $logDir "$Name.stderr.log"

    $command = "python scripts/stage_contract.py check-stage --stage-id $StageId --mode $Mode --run-id $RunId --write-status"



    try {

        $result = Invoke-StageContractCheck -StageId $StageId -Mode $Mode -RunId $RunId -WriteStatus

        $result.RawJson | Set-Content -LiteralPath $stdout -Encoding utf8

        $reason = if ($result.Payload.needs_update_reason) { $result.Payload.needs_update_reason } else { "" }

        $reason | Set-Content -LiteralPath $stderr -Encoding utf8

        $finishedAt = Get-Date

        $flowStatus = Convert-StageStatusToFlowLabel -StageStatus $result.Payload.status

        return [pscustomobject]@{

            FlowResult = (New-FlowResult -Name $Name -Status $flowStatus -ExitCode $result.ExitCode -Stdout $stdout -Stderr $stderr -Command $command -StartedAt $startedAt -FinishedAt $finishedAt)

            Payload = $result.Payload

        }

    } catch {

        $_ | Out-File -LiteralPath $stderr -Encoding utf8

        "" | Set-Content -LiteralPath $stdout -Encoding utf8

        $finishedAt = Get-Date

        return [pscustomobject]@{

            FlowResult = (New-FlowResult -Name $Name -Status "失败" -ExitCode 4 -Stdout $stdout -Stderr $stderr -Command $command -StartedAt $startedAt -FinishedAt $finishedAt)

            Payload = $null

        }

    }

}



function Invoke-FlowStep {
    param(
        [string]$Name,
        [string]$ScriptPath,
        [int]$TimeoutSeconds,
        [string[]]$Arguments = @()
    )

    $startedAt = Get-Date
    $stdout = Join-Path $logDir "$Name.stdout.log"
    $stderr = Join-Path $logDir "$Name.stderr.log"

    if (-not (Test-Path -LiteralPath $ScriptPath)) {
        return New-SkippedStep -Name $Name -Reason "统一执行入口不存在：$ScriptPath"
    }

    $pwsh = if (Get-Command "pwsh" -ErrorAction SilentlyContinue) { "pwsh" } else { "powershell.exe" }
    $argumentList = @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $ScriptPath) + $Arguments

    try {
        $envVars = @(
            "TEST_RUN_ID=$RunId",
            "TEST_RUN_DIR=$runDir",
            "STAGE_STATUS_DIR=$stageStatusDir",
            "BASE_URL=$FrontendUrl",
            "API_BASE_URL=$ApiBaseUrl",
            "TEST_USERNAME=$Username"
        )
        if ($Password) {
            $envVars += "TEST_PASSWORD=$Password"
        }

        $process = Start-Process -FilePath $pwsh -ArgumentList $argumentList -WorkingDirectory $root -RedirectStandardOutput $stdout -RedirectStandardError $stderr -NoNewWindow -PassThru -Wait

        $waitSuccess = $true
        $exitCode = $process.ExitCode

        $stdoutContent = if (Test-Path $stdout) { Get-Content $stdout -Raw -Encoding utf8 } else { "" }
        $stderrContent = if (Test-Path $stderr) { Get-Content $stderr -Raw -Encoding utf8 } else { "" }

        $finishedAt = Get-Date
        $status = if ($exitCode -eq 0) {
            "通过"
        } elseif ($exitCode -eq 2) {
            "未执行"
        } else {
            "失败"
        }

        return New-FlowResult -Name $Name -Status $status -ExitCode $exitCode -Stdout $stdout -Stderr $stderr -Command "$pwsh -File $ScriptPath" -StartedAt $startedAt -FinishedAt $finishedAt
    } catch {
        $finishedAt = Get-Date
        $_ | Out-File -LiteralPath $stderr -Encoding utf8
        return New-FlowResult -Name $Name -Status "失败" -ExitCode 1 -Stdout $stdout -Stderr $stderr -Command "$pwsh -File $ScriptPath" -StartedAt $startedAt -FinishedAt $finishedAt
    }
}



function Invoke-ForcedStageSkip {

    param(

        [string]$Name,

        [string]$ScriptPath,

        [int]$TimeoutSeconds,

        [string]$Reason,

        [string[]]$Arguments = @()

    )



    $allArgs = @($Arguments + @("-ForceNotExecutedReason", $Reason))

    Invoke-FlowStep -Name $Name -ScriptPath $ScriptPath -TimeoutSeconds $TimeoutSeconds -Arguments $allArgs

}



function Test-LogContainsConnectivityFailure {

    param([string[]]$Paths)



    foreach ($path in $Paths) {

        if ((Test-Path -LiteralPath $path) -and (Select-String -LiteralPath $path -Pattern "ConnectionRefused|ERR_CONNECTION_REFUSED|WinError 10061|actively refused|ReadTimeout|Read timed out|timed out|连接被拒绝|拒绝连接|读取超时|请求超时" -Quiet)) {

            return $true

        }

    }



    return $false

}



function Test-LogContainsAuthenticationBlocker {

    param([string[]]$Paths)



    foreach ($path in $Paths) {

        if ((Test-Path -LiteralPath $path) -and (Select-String -LiteralPath $path -Pattern "401 Client Error|403 Client Error|Unauthorized|Forbidden|未获取到登录|登录失败|认证失败|真实认证不可用|Authentication failed|Login failed" -Quiet)) {

            return $true

        }

    }



    return $false

}



function Get-HttpStatusCode {

    param(

        [string]$Uri,

        [string]$Method = "GET",

        [int[]]$AllowedStatusCodes = @(200)

    )



    for ($retry = 0; $retry -lt 3; $retry++) {

        try {

            $output = & curl.exe -s -o null -w "%{http_code}" -X $Method --max-time 10 --location "$Uri" 2>&1

            if ($LASTEXITCODE -eq 0 -and $output -match '^\d{3}$') {

                $statusCode = [int]$output

                if ($AllowedStatusCodes -contains $statusCode) {

                    return $statusCode

                }

            }

        } catch {

        }

        Start-Sleep -Seconds 2

    }



    throw "Failed to connect to $Uri after 3 retries"

}



function Invoke-ServicePrecheck {

    $startedAt = Get-Date

    $stdout = Join-Path $logDir "service-precheck.stdout.log"

    $stderr = Join-Path $logDir "service-precheck.stderr.log"

    $frontendCheck = $FrontendUrl

    $apiCheck = $ApiBaseUrl.TrimEnd("/") + "/api/devices/"

    $command = "Invoke-WebRequest -Uri $frontendCheck -Method GET; Invoke-WebRequest -Uri $apiCheck -Method GET"



    try {

        $frontendStatusCode = Get-HttpStatusCode -Uri $frontendCheck -Method GET -AllowedStatusCodes @(200)

        $apiStatusCode = Get-HttpStatusCode -Uri $apiCheck -Method GET -AllowedStatusCodes @(200, 401, 403, 302)

        @(

            "Frontend: HTTP $frontendStatusCode $frontendCheck",

            "API: HTTP $apiStatusCode $apiCheck",

            "API 预检说明：200 表示匿名可读；401/403/302 也视为服务可达但需要认证。"

        ) | Set-Content -LiteralPath $stdout -Encoding utf8

        "" | Set-Content -LiteralPath $stderr -Encoding utf8

        $finishedAt = Get-Date

        return New-FlowResult -Name "service-precheck" -Status "通过" -ExitCode 0 -Stdout $stdout -Stderr $stderr -Command $command -StartedAt $startedAt -FinishedAt $finishedAt

    } catch {

        "" | Set-Content -LiteralPath $stdout -Encoding utf8

        $_ | Out-File -LiteralPath $stderr -Encoding utf8

        $finishedAt = Get-Date

        return New-FlowResult -Name "service-precheck" -Status "失败" -ExitCode 1 -Stdout $stdout -Stderr $stderr -Command $command -StartedAt $startedAt -FinishedAt $finishedAt

    }

}



function Copy-DirectoryIfExists {

    param(

        [string]$SourceDirectory,

        [string]$DestinationDirectory

    )



    if (Test-Path -LiteralPath $SourceDirectory) {

        New-Item -ItemType Directory -Force -Path $DestinationDirectory | Out-Null

        Get-ChildItem -LiteralPath $SourceDirectory -Force -ErrorAction SilentlyContinue |

            ForEach-Object {

                Copy-Item -LiteralPath $_.FullName -Destination (Join-Path $DestinationDirectory $_.Name) -Recurse -Force

            }

    }

}



function Write-FlowArtifacts {

    param(

        [System.Collections.Generic.List[object]]$Results

    )



    $generatedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"

    $recordPath = Join-Path $runReportDir "测试流程执行记录.md"

    $batchSummaryPath = Join-Path $runDir "批次摘要.md"



    $resultRows = $Results | ForEach-Object {

        $stdoutPath = if ($_.Stdout) { $_.Stdout.Replace('\', '/') } else { "" }

        $stderrPath = if ($_.Stderr) { $_.Stderr.Replace('\', '/') } else { "" }

        "| $($_.Name) | $($_.Status) | $($_.ExitCode) | $($_.DurationSeconds) | $stdoutPath | $stderrPath |"

    }



    $riskItems = New-Object System.Collections.Generic.List[string]

    foreach ($item in $Results) {

        if ($item.Status -in @("失败", "超时", "未执行", "需更新")) {

            $riskItems.Add("- $($item.Name)：$($item.Status)。详情见 $($item.Stdout) / $($item.Stderr)。")

        }

    }

    if ($riskItems.Count -eq 0) {

        $riskItems.Add("- 暂无新增风险与待确认项。")

    }



    $maskedAccount = if ($Username) { "$Username/******" } else { "待确认" }

    $failedOrTimedOut = @($Results | Where-Object { $_.Status -in @("失败", "超时") })

    $notExecuted = @($Results | Where-Object { $_.Status -eq "未执行" })

    $needsUpdate = @($Results | Where-Object { $_.Status -eq "需更新" })

    $overallStatus = if ($failedOrTimedOut.Count -gt 0) {

        "flow-blocked-or-failed"

    } elseif (($notExecuted.Count + $needsUpdate.Count) -gt 0) {

        "flow-closed-with-exceptions"

    } else {

        "execution-completed"

    }



    $record = @"

# 测试流程执行记录



## 当前阶段

完整测试流程执行入口



## 输入文件

- `AGENTS.md`

- `docs/阶段执行检查清单.md`

- `stage-manifests/*.yaml`

- `docs/cases/*-评审版.md`

- `docs/test-runs/$RunId/reports/*覆盖矩阵.md`

- `scripts/run-*.ps1`



## 产出文件

- `docs/test-runs/$RunId/raw/run-logs/`

- `docs/test-runs/$RunId/reports/测试流程执行记录.md`

- `docs/test-runs/$RunId/批次摘要.md`

- `docs/test-runs/$RunId/reports/`

- `docs/test-runs/$RunId/defects/`

- `docs/test-runs/$RunId/raw/`

- `docs/test-runs/$RunId/stage-status/`

- 各专项脚本、报告、缺陷清单或未执行说明



## 正文/核心内容

- 生成时间：$generatedAt

- 测试批次：$RunId

- 前端地址：$FrontendUrl

- 后端地址：$ApiBaseUrl

- 测试账号：$maskedAccount

- 执行边界：总控只编排执行类阶段，并通过统一契约检查 `1-4` 和 `10-11`；系统测试报告和知识沉淀仍由对应 skill 生成。

- 机器可读真源：`stage-manifests/`

- 本轮归档：`docs/test-runs/$RunId/`



| 专项/阶段 | 状态 | 退出码 | 耗时秒 | 标准输出日志 | 错误日志 |

| --- | --- | ---: | ---: | --- | --- |

$($resultRows -join "`r`n")



## 执行结论

- 本轮执行状态：$overallStatus。

- 失败或超时阶段数：$($failedOrTimedOut.Count)。

- 未执行阶段数：$($notExecuted.Count)。

- 需更新阶段数：$($needsUpdate.Count)。



## 风险与待确认项

$($riskItems -join "`r`n")



## 下一步建议

- 若 `10-system-test-report` 为未执行或需更新，使用 `system-test-report` skill 基于本轮归档和 stage-status 生成或更新系统测试报告。

- 若 `11-knowledge-base` 为未执行或需更新，使用 `knowledge-base` skill 在系统测试报告后沉淀知识资产。

- 若任一执行类专项未执行，先按日志补齐门禁输入、覆盖矩阵或工具配置，再重新执行。

"@



    $record | Set-Content -LiteralPath $recordPath -Encoding utf8



    Copy-DirectoryIfExists -SourceDirectory (Join-Path $root "tests\api\reports") -DestinationDirectory (Join-Path $runRawDir "api")

    Copy-DirectoryIfExists -SourceDirectory (Join-Path $root "tests\ui\reports") -DestinationDirectory (Join-Path $runRawDir "ui")

    Copy-DirectoryIfExists -SourceDirectory $perfResultDir -DestinationDirectory (Join-Path $runRawDir "performance")

    Copy-DirectoryIfExists -SourceDirectory (Join-Path $root "tests\security\reports") -DestinationDirectory (Join-Path $runRawDir "security")



    $summaryRows = $Results | ForEach-Object {

        "| $($_.Name) | $($_.Status) | $($_.ExitCode) | $($_.DurationSeconds) |"

    }



    $batchSummary = @"

# 批次摘要



## 当前阶段

自动化与专项执行批次摘要



## 输入文件

- `docs/test-runs/$RunId/reports/测试流程执行记录.md`

- `docs/test-runs/$RunId/raw/run-logs/`

- `docs/test-runs/$RunId/stage-status/`



## 产出文件

- `docs/test-runs/$RunId/批次摘要.md`



## 正文/核心内容

- 测试批次：$RunId

- 生成时间：$generatedAt

- 前端地址：$FrontendUrl

- 后端地址：$ApiBaseUrl

- 测试账号：$maskedAccount

- 本轮状态：$overallStatus



| 专项/阶段 | 状态 | 退出码 | 耗时秒 |

| --- | --- | ---: | ---: |

$($summaryRows -join "`r`n")



### 证据入口

- 执行记录：`docs/test-runs/$RunId/reports/测试流程执行记录.md`

- 阶段状态：`docs/test-runs/$RunId/stage-status/`

- 执行日志：`docs/test-runs/$RunId/raw/run-logs/`

- 归档报告：`docs/test-runs/$RunId/reports/`

- 归档缺陷：`docs/test-runs/$RunId/defects/`

- 原始结果：`docs/test-runs/$RunId/raw/`



## 执行结论

- 本轮执行状态：$overallStatus。

- 失败或超时阶段数：$($failedOrTimedOut.Count)。

- 未执行阶段数：$($notExecuted.Count)。

- 需更新阶段数：$($needsUpdate.Count)。



## 风险与待确认项

$($riskItems -join "`r`n")



## 下一步建议

- 系统测试报告阶段优先读取本文件、`stage-status` 和归档正式产物，再按需展开原始结果。

- 若本轮存在失败、超时、未执行或需更新阶段，先处理对应门禁、环境或工具配置，再继续后置阶段。

"@



    $batchSummary | Set-Content -LiteralPath $batchSummaryPath -Encoding utf8

}



$results = New-Object System.Collections.Generic.List[object]



$allStages = @(

    @{ Name = "manifest-validation"; Type = "check"; Action = { Invoke-ManifestValidation } },

    @{ Name = "1-req-analysis"; Type = "check"; Action = { Invoke-StageCheckResult -Name "1-req-analysis" -StageId "1-req-analysis" -Mode "full" } },

    @{ Name = "2-test-design"; Type = "check"; Action = { Invoke-StageCheckResult -Name "2-test-design" -StageId "2-test-design" -Mode "full" } },

    @{ Name = "3-case-generation"; Type = "check"; Action = { Invoke-StageCheckResult -Name "3-case-generation" -StageId "3-case-generation" -Mode "full" } },

    @{ Name = "4-case-review"; Type = "check"; Action = { Invoke-StageCheckResult -Name "4-case-review" -StageId "4-case-review" -Mode "full" } },

    @{ Name = "service-precheck"; Type = "exec"; Action = { Invoke-ServicePrecheck } },

    @{ Name = "api-smoke"; Type = "exec"; Action = { Invoke-FlowStep -Name "api-smoke" -ScriptPath (Join-Path $root "scripts\run-api-tests.ps1") -TimeoutSeconds $ApiTimeoutSeconds -Arguments @("-Mode", "smoke") } },

    @{ Name = "api"; Type = "exec"; Action = { Invoke-FlowStep -Name "api" -ScriptPath (Join-Path $root "scripts\run-api-tests.ps1") -TimeoutSeconds $ApiTimeoutSeconds -Arguments @("-Mode", "full") } },

    @{ Name = "ui"; Type = "exec"; Action = { Invoke-FlowStep -Name "ui" -ScriptPath (Join-Path $root "scripts\run-ui-tests.ps1") -TimeoutSeconds $UiTimeoutSeconds } },

    @{ Name = "performance"; Type = "exec"; Action = { Invoke-FlowStep -Name "performance" -ScriptPath (Join-Path $root "scripts\run-perf-tests.ps1") -TimeoutSeconds $PerfTimeoutSeconds } },

    @{ Name = "security"; Type = "exec"; Action = { Invoke-FlowStep -Name "security" -ScriptPath (Join-Path $root "scripts\run-security-tests.ps1") -TimeoutSeconds $SecurityTimeoutSeconds -Arguments @("-Target", $FrontendUrl) } },

    @{ Name = "10-system-test-report"; Type = "check"; Action = { Invoke-StageCheckResult -Name "10-system-test-report" -StageId "10-system-test-report" -Mode "full" } },

    @{ Name = "11-knowledge-base"; Type = "check"; Action = { Invoke-StageCheckResult -Name "11-knowledge-base" -StageId "11-knowledge-base" -Mode "full" } }

)



$prereqStages = @("manifest-validation", "1-req-analysis", "2-test-design", "3-case-generation", "4-case-review")

$execStages = @("service-precheck", "api-smoke", "api", "ui", "performance", "security")

$reportStages = @("10-system-test-report", "11-knowledge-base")



$userSpecifiedStages = ($EndStage -ne "") -or ($Stages.Count -gt 0)

$skipRemaining = $false



foreach ($stageDef in $allStages) {

    $stageName = $stageDef.Name
    

    if ($skipRemaining) {

        $results.Add((New-SkippedStep -Name $stageName -Reason "已到达指定结束阶段"))

        continue

    }
    

    if ($stageName -in $reportStages) {
        continue
    }
    

    if (-not (Test-ShouldExecuteStage -StageName $stageName)) {

        $results.Add((New-SkippedStep -Name $stageName -Reason (Get-StageCompletionReason -StageName $stageName)))

        

        if ($EndStage -ne "" -and $stageName -eq $EndStage) {

            $skipRemaining = $true

        }

        continue

    }
    

    $result = & $stageDef.Action

    if ($stageDef.Type -eq "check") {

        $results.Add($result.FlowResult)

    } else {

        $results.Add($result)

    }
    

    if ($EndStage -ne "" -and $stageName -eq $EndStage) {

        $skipRemaining = $true

    }

}


Write-FlowArtifacts -Results $results


foreach ($stageDef in $allStages) {

    $stageName = $stageDef.Name

    if ($stageName -notin $reportStages) {
        continue
    }

    if (-not (Test-ShouldExecuteStage -StageName $stageName)) {

        $results.Add((New-SkippedStep -Name $stageName -Reason (Get-StageCompletionReason -StageName $stageName)))

        continue

    }

    $result = & $stageDef.Action

    if ($stageDef.Type -eq "check") {

        $results.Add($result.FlowResult)

    } else {

        $results.Add($result)

    }

}


$results | Format-Table Name, Status, ExitCode, DurationSeconds, Stdout, Stderr -AutoSize


$pendingReportStages = @("10-system-test-report", "11-knowledge-base")

$unfinishedReportStages = @($results | Where-Object {

    $_.Name -in $pendingReportStages -and $_.Status -notin @("通过", "已完成", "completed")

})

if ($unfinishedReportStages.Count -gt 0) {

    Write-Host ""

    Write-Host "[!] 以下阶段尚未完成，需要 AI 在当前对话中立即介入并调用对应 skill：" -ForegroundColor Yellow

    foreach ($stage in $unfinishedReportStages) {

        Write-Host "    - $($stage.Name): $($stage.Status)" -ForegroundColor Yellow

    }

    Write-Host "    优先顺序：先调用 system-test-report，再调用 knowledge-base。" -ForegroundColor Yellow

    Write-Host ""

}



if ($results | Where-Object { $_.Status -in @("失败", "超时") }) {

    exit 1

}



exit 0