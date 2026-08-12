$Script:ProjectRoot = Resolve-Path (Join-Path $PSScriptRoot "..\..")
$Script:StageContractScript = Join-Path $Script:ProjectRoot "scripts\stage_contract.py"

function Get-SystemConfig {
    param(
        [string]$SystemId = $null
    )

    if (-not $SystemId) {
        $SystemId = if ($env:TEST_SYSTEM_ID) { $env:TEST_SYSTEM_ID } else { "crm" }
    }

    $yamlPath = Join-Path $Script:ProjectRoot "projects\$SystemId\system.yaml"

    if (-not (Test-Path -LiteralPath $yamlPath)) {
        return [pscustomobject]@{
            SystemId = $SystemId
            SystemName = $SystemId
            BaseUrl = ""
            ApiBasePath = "/prod-api"
            Timeout = 30
            AuthType = ""
            ApiTestsDir = "tests\api\testsuites"
            UiTestsDir = "tests\ui\specs"
            PerfTestsDir = "tests\performance\locust"
            SecTestsDir = "tests\security"
            ApiEnabled = $true
            UiEnabled = $true
            PerfEnabled = $true
            SecEnabled = $true
            SmokeMarker = "smoke"
            UiBaseUrl = ""
            UiGlobalSetup = ""
            PerfSmokeUsers = 5
            PerfSmokeSpawnRate = 1
            PerfSmokeDuration = "30s"
            PerfFullUsers = 50
            PerfFullSpawnRate = 5
            PerfFullDuration = "120s"
            SecTargetUrl = ""
            OutputDir = "docs\test-runs"
            TestCasesDir = "docs\cases"
            TestDataDir = "tests\data"
        }
    }

    # 尝试使用 ConvertFrom-Yaml，如不可用则用 Python 解析
    $yamlText = Get-Content -LiteralPath $yamlPath -Raw -Encoding utf8
    $config = $null

    # 方法1: 使用 PowerShell-Yaml 模块
    if (Get-Command -Name ConvertFrom-Yaml -ErrorAction SilentlyContinue) {
        try {
            $config = $yamlText | ConvertFrom-Yaml -ErrorAction Stop
        } catch {
            $config = $null
        }
    }

    # 方法2: 使用 Python 解析 yaml (回退方案)
    if (-not $config) {
        try {
            $tmpScript = [System.IO.Path]::GetTempFileName() + ".py"
            @"
import yaml, json, sys
with open(r'$yamlPath') as f:
    config = yaml.safe_load(f)
if config is None:
    config = {}
print(json.dumps(config, default=str))
"@ | Set-Content -LiteralPath $tmpScript -Encoding utf8
            $jsonText = & python $tmpScript 2>$null
            Remove-Item -LiteralPath $tmpScript -Force -ErrorAction SilentlyContinue
            if ($LASTEXITCODE -eq 0 -and $jsonText) {
                $config = $jsonText | ConvertFrom-Json -Depth 20
            }
        } catch {
            $config = $null
        }
    }

    if (-not $config) {
        return [pscustomobject]@{
                SystemId = $SystemId
                SystemName = $SystemId
                BaseUrl = ""
                ApiBasePath = "/prod-api"
                Timeout = 30
                AuthType = ""
                ApiTestsDir = "tests\api\testsuites"
                UiTestsDir = "tests\ui\specs"
                PerfTestsDir = "tests\performance\locust"
                SecTestsDir = "tests\security"
                ApiEnabled = $true
                UiEnabled = $true
                PerfEnabled = $true
                SecEnabled = $true
                SmokeMarker = "smoke"
                UiBaseUrl = ""
                UiGlobalSetup = ""
                PerfSmokeUsers = 5
                PerfSmokeSpawnRate = 1
                PerfSmokeDuration = "30s"
                PerfFullUsers = 50
                PerfFullSpawnRate = 5
                PerfFullDuration = "120s"
                SecTargetUrl = ""
                OutputDir = "docs\test-runs"
                TestCasesDir = "docs\cases"
                TestDataDir = "tests\data"
            }
        }
    }

    # 安全获取嵌套值
    function Get-YamlValue {
        param($Obj, [string[]]$Keys, $Default)
        $current = $Obj
        foreach ($key in $Keys) {
            if ($null -eq $current -or -not $current.PSObject.Properties.Name -contains $key) {
                return $Default
            }
            $current = $current.$key
        }
        if ($null -eq $current) { return $Default }
        return $current
    }

    $protocolDefault = Get-YamlValue -Obj $config -Keys @("protocols", "default") -Default $null
    $protocolConfig = if ($protocolDefault) { Get-YamlValue -Obj $protocolDefault -Keys @("config") -Default $null } else { $null }

    $baseUrl = if ($protocolConfig) { Get-YamlValue -Obj $protocolConfig -Keys @("base_url") -Default "" } else { "" }
    $apiBasePath = if ($protocolConfig) { Get-YamlValue -Obj $protocolConfig -Keys @("api_base_path") -Default "/prod-api" } else { "/prod-api" }
    $timeout = if ($protocolConfig) { [int](Get-YamlValue -Obj $protocolConfig -Keys @("timeout") -Default 30) } else { 30 }

    $authType = Get-YamlValue -Obj $config -Keys @("auth", "type") -Default ""

    $apiScope = Get-YamlValue -Obj $config -Keys @("test_scope", "api") -Default $null
    $uiScope = Get-YamlValue -Obj $config -Keys @("test_scope", "ui") -Default $null
    $perfScope = Get-YamlValue -Obj $config -Keys @("test_scope", "performance") -Default $null
    $secScope = Get-YamlValue -Obj $config -Keys @("test_scope", "security") -Default $null

    $apiEnabled = if ($apiScope) { [bool](Get-YamlValue -Obj $apiScope -Keys @("enabled") -Default $true) } else { $true }
    $uiEnabled = if ($uiScope) { [bool](Get-YamlValue -Obj $uiScope -Keys @("enabled") -Default $true) } else { $true }
    $perfEnabled = if ($perfScope) { [bool](Get-YamlValue -Obj $perfScope -Keys @("enabled") -Default $true) } else { $true }
    $secEnabled = if ($secScope) { [bool](Get-YamlValue -Obj $secScope -Keys @("enabled") -Default $true) } else { $true }

    $apiTestsDir = if ($apiScope) { Get-YamlValue -Obj $apiScope -Keys @("tests_dir") -Default "tests\api\testsuites" } else { "tests\api\testsuites" }
    $uiTestsDir = if ($uiScope) { Get-YamlValue -Obj $uiScope -Keys @("tests_dir") -Default "tests\ui\specs" } else { "tests\ui\specs" }
    $perfTestsDir = if ($perfScope) { Get-YamlValue -Obj $perfScope -Keys @("tests_dir") -Default "tests\performance\locust" } else { "tests\performance\locust" }
    $secTestsDir = if ($secScope) { Get-YamlValue -Obj $secScope -Keys @("tests_dir") -Default "tests\security" } else { "tests\security" }

    $uiBaseUrl = if ($uiScope) { Get-YamlValue -Obj $uiScope -Keys @("base_url") -Default "" } else { "" }
    $uiGlobalSetup = if ($uiScope) { Get-YamlValue -Obj $uiScope -Keys @("global_setup") -Default "" } else { "" }

    $perfSmoke = if ($perfScope) { Get-YamlValue -Obj $perfScope -Keys @("smoke") -Default $null } else { $null }
    $perfFull = if ($perfScope) { Get-YamlValue -Obj $perfScope -Keys @("full") -Default $null } else { $null }

    $perfSmokeUsers = if ($perfSmoke) { [int](Get-YamlValue -Obj $perfSmoke -Keys @("users") -Default 5) } else { 5 }
    $perfSmokeSpawnRate = if ($perfSmoke) { [int](Get-YamlValue -Obj $perfSmoke -Keys @("spawn_rate") -Default 1) } else { 1 }
    $perfSmokeDuration = if ($perfSmoke) { Get-YamlValue -Obj $perfSmoke -Keys @("duration") -Default "30s" } else { "30s" }

    $perfFullUsers = if ($perfFull) { [int](Get-YamlValue -Obj $perfFull -Keys @("users") -Default 50) } else { 50 }
    $perfFullSpawnRate = if ($perfFull) { [int](Get-YamlValue -Obj $perfFull -Keys @("spawn_rate") -Default 5) } else { 5 }
    $perfFullDuration = if ($perfFull) { Get-YamlValue -Obj $perfFull -Keys @("duration") -Default "120s" } else { "120s" }

    $secTargetUrl = if ($secScope) { Get-YamlValue -Obj $secScope -Keys @("target_url") -Default "" } else { "" }

    $paths = Get-YamlValue -Obj $config -Keys @("paths") -Default $null
    $outputDir = if ($paths) { Get-YamlValue -Obj $paths -Keys @("output_dir") -Default "docs\test-runs" } else { "docs\test-runs" }
    $testCasesDir = if ($paths) { Get-YamlValue -Obj $paths -Keys @("test_cases") -Default "docs\cases" } else { "docs\cases" }
    $testDataDir = if ($paths) { Get-YamlValue -Obj $paths -Keys @("test_data") -Default "tests\data" } else { "tests\data" }

    $systemName = Get-YamlValue -Obj $config -Keys @("name") -Default $SystemId

    return [pscustomobject]@{
        SystemId = $SystemId
        SystemName = $systemName
        BaseUrl = $baseUrl
        ApiBasePath = $apiBasePath
        Timeout = $timeout
        AuthType = $authType
        ApiTestsDir = $apiTestsDir
        UiTestsDir = $uiTestsDir
        PerfTestsDir = $perfTestsDir
        SecTestsDir = $secTestsDir
        ApiEnabled = $apiEnabled
        UiEnabled = $uiEnabled
        PerfEnabled = $perfEnabled
        SecEnabled = $secEnabled
        SmokeMarker = "smoke"
        UiBaseUrl = $uiBaseUrl
        UiGlobalSetup = $uiGlobalSetup
        PerfSmokeUsers = $perfSmokeUsers
        PerfSmokeSpawnRate = $perfSmokeSpawnRate
        PerfSmokeDuration = $perfSmokeDuration
        PerfFullUsers = $perfFullUsers
        PerfFullSpawnRate = $perfFullSpawnRate
        PerfFullDuration = $perfFullDuration
        SecTargetUrl = $secTargetUrl
        OutputDir = $outputDir
        TestCasesDir = $testCasesDir
        TestDataDir = $testDataDir
    }

function New-OutputState {
    param(
        [string]$Name,
        [string]$Path
    )

    return [pscustomobject]@{
        name = $Name
        path = $Path
        exists = Test-Path -LiteralPath $Path
    }
}

function Get-MissingRequirementNames {
    param([array]$Checks)
    return @($Checks | Where-Object { -not $_.ok } | ForEach-Object { $_.name })
}

function Get-LatestRunId {
    param(
        [string]$TestRunsDir = $(Join-Path $Script:ProjectRoot "docs\test-runs"),
        [string]$SystemId = $null
    )

    if (-not (Test-Path -LiteralPath $TestRunsDir)) {
        return $null
    }

    # 兼容两种格式：
    #   旧格式: YYYYMMDD-HHMMSS
    #   新格式: YYYYMMDD-HHMMSS-{system}-{uuid8}
    $dirs = Get-ChildItem -LiteralPath $TestRunsDir -Directory |
            Where-Object { $_.Name -match '^\d{8}-\d{6}(-\w+-[a-f0-9]{8})?$' }

    # 按 system 过滤（新格式才有 system 段）
    if ($SystemId) {
        $dirs = $dirs | Where-Object {
            $parts = $_.Name -split '-'
            if ($parts.Count -ge 3) { $parts[2] -eq $SystemId } else { $false -or $SystemId -eq 'crm' }
        }
    }

    $latestDir = $dirs | Sort-Object Name -Descending | Select-Object -First 1

    if ($latestDir) {
        return $latestDir.Name
    }

    return $null
}

function Get-StageRunContext {
    param(
        [Parameter(Mandatory)]
        [string]$StageId,
        [string]$RunId = $null
    )

    if (-not $RunId) {
        if ($env:TEST_RUN_ID) {
            $RunId = $env:TEST_RUN_ID
        } else {
            $latestRunId = Get-LatestRunId
            if ($latestRunId) {
                $RunId = $latestRunId
            } else {
                $RunId = Get-Date -Format "yyyyMMdd-HHmmss"
            }
        }
    }

    # 优先用 TEST_RUN_DIR 环境变量（由 run-full-test-flow 注入，实现批次隔离与并行安全）
    if ($env:TEST_RUN_DIR -and (Test-Path -LiteralPath $env:TEST_RUN_DIR)) {
        $runDir = $env:TEST_RUN_DIR
    } else {
        $runDir = Join-Path $Script:ProjectRoot "docs\test-runs\$RunId"
    }
    $stageStatusDir = Join-Path $runDir "stage-status"
    $rawRunDir = Join-Path $runDir "raw"

    New-Item -ItemType Directory -Force -Path $runDir | Out-Null
    New-Item -ItemType Directory -Force -Path $stageStatusDir | Out-Null
    New-Item -ItemType Directory -Force -Path $rawRunDir | Out-Null

    $env:TEST_RUN_ID = $RunId
    $env:TEST_RUN_DIR = $runDir
    $env:STAGE_STATUS_DIR = $stageStatusDir

    return [pscustomobject]@{
        StageId = $StageId
        RunId = $RunId
        RunDir = $runDir
        StageStatusDir = $stageStatusDir
        RawRunDir = $rawRunDir
    }
}

function Invoke-StageContractCheck {
    param(
        [Parameter(Mandatory)]
        [string]$StageId,
        [ValidateSet("preflight", "full")]
        [string]$Mode = "full",
        [string]$RunId,
        [switch]$WriteStatus
    )

    $arguments = @(
        $Script:StageContractScript,
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

    $tmpFile = [System.IO.Path]::GetTempFileName() + ".json"
    $arguments += @("--output", $tmpFile)
    & python @arguments
    $exitCode = $LASTEXITCODE

    if (-not (Test-Path -LiteralPath $tmpFile)) {
        throw "stage_contract.py did not write output file for stage '$StageId'."
    }

    $jsonText = Get-Content -LiteralPath $tmpFile -Raw -Encoding utf8
    Remove-Item -LiteralPath $tmpFile -Force -ErrorAction SilentlyContinue

    if (-not $jsonText) {
        throw "stage_contract.py returned no output for stage '$StageId'."
    }

    try {
        $payload = $jsonText | ConvertFrom-Json -Depth 10 -ErrorAction Stop
    } catch {
        $payload = $jsonText | ConvertFrom-Json
    }

    return [pscustomobject]@{
        ExitCode = $exitCode
        Payload = $payload
        RawJson = $jsonText
    }
}

function Write-StageStatusFile {
    param(
        [Parameter(Mandatory)]
        [pscustomobject]$RunContext,
        [Parameter(Mandatory)]
        [string]$DisplayName,
        [Parameter(Mandatory)]
        [string]$DriverType,
        [Parameter(Mandatory)]
        [string]$Status,
        [array]$InputsChecked = @(),
        [array]$GatesChecked = @(),
        [array]$OutputsWritten = @(),
        [string[]]$EvidencePaths = @(),
        [string]$NextDecision = "",
        [string]$NeedsUpdateReason = "",
        [string]$CheckMode = "full"
    )

    $payload = [ordered]@{
        stage_id = $RunContext.StageId
        display_name = $DisplayName
        run_id = $RunContext.RunId
        driver_type = $DriverType
        status = $Status
        inputs_checked = $InputsChecked
        gates_checked = $GatesChecked
        outputs_written = $OutputsWritten
        evidence_paths = $EvidencePaths
        next_decision = $NextDecision
        needs_update_reason = $NeedsUpdateReason
        checked_at = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
        check_mode = $CheckMode
    }

    $statusPath = Join-Path $RunContext.StageStatusDir "$($RunContext.StageId).json"
    try {
        $payload | ConvertTo-Json -Depth 10 | Set-Content -LiteralPath $statusPath -Encoding utf8
    } catch {
        $payload | ConvertTo-Json | Set-Content -LiteralPath $statusPath -Encoding utf8
    }

    return $statusPath
}

function Get-DefectSeverity {
    param([string]$DefectType)

    switch ($DefectType) {
        "服务端错误"   { return "P1-严重" }
        "连接失败"     { return "P1-严重" }
        "协议解析失败" { return "P1-严重" }
        "设备身份失败" { return "P1-严重" }
        "高危漏洞"     { return "P1-严重" }
        "认证/授权"    { return "P2-高" }
        "接口不存在"   { return "P2-高" }
        "平台接收失败" { return "P2-高" }
        "中危漏洞"     { return "P2-高" }
        "超时"         { return "P3-中" }
        "性能异常"     { return "P3-中" }
        "低危漏洞"     { return "P3-中" }
        "断言失败"     { return "P3-中" }
        "信息性"       { return "P4-低" }
        default        { return "P3-中" }
    }
}

function Get-JUnitDefects {
    param([string]$JunitXmlPath)

    if (-not (Test-Path -LiteralPath $JunitXmlPath)) {
        return @()
    }

    try {
        [xml]$xml = Get-Content -LiteralPath $JunitXmlPath -Encoding utf8
    } catch {
        return @()
    }

    $defects = [System.Collections.Generic.List[hashtable]]::new()
    $index = 0

    $testcases = $xml.SelectNodes("//testcase")
    foreach ($tc in $testcases) {
        $failure = $tc.SelectSingleNode("failure")
        $errNode = $tc.SelectSingleNode("error")
        $skipped = $tc.SelectSingleNode("skipped")
        $issue = if ($failure) { $failure } elseif ($errNode) { $errNode } else { $null }
        if (-not $issue -or $skipped) { continue }

        $index++
        $name = $tc.GetAttribute("name")
        $classname = $tc.GetAttribute("classname")
        $time = $tc.GetAttribute("time")
        $message = $issue.GetAttribute("message")

        $module = if ($classname -match "testsuites\.(\w+)\.") { $Matches[1] } else { "unknown" }

        $defType = if ($message -match "ReadTimeout|timed out|Read timed out") {
            "超时"
        } elseif ($message -match "ConnectionRefused|actively refused|10061") {
            "连接失败"
        } elseif ($message -match "404|Page not found") {
            "接口不存在"
        } elseif ($message -match "500|AssertionError.*500") {
            "服务端错误"
        } elseif ($message -match "401|403|Unauthorized|Forbidden") {
            "认证/授权"
        } else {
            "断言失败"
        }

        $shortMessage = if ($message.Length -gt 200) { $message.Substring(0, 200) + "..." } else { $message }

        $defects.Add(@{
            Index = $index
            Module = $module
            TestName = $name
            Classname = $classname
            DefectType = $defType
            Duration = $time
            ShortMessage = $shortMessage
        })
    }

    Write-Output -NoEnumerate $defects
}

function Get-PlaywrightDefects {
    param([string]$ResultJsonPath)

    if (-not (Test-Path -LiteralPath $ResultJsonPath)) {
        return @()
    }

    try {
        try {
            $json = Get-Content -LiteralPath $ResultJsonPath -Encoding utf8 -Raw | ConvertFrom-Json -Depth 20 -ErrorAction Stop
        } catch {
            $json = Get-Content -LiteralPath $ResultJsonPath -Encoding utf8 -Raw | ConvertFrom-Json
        }
    } catch {
        return @()
    }

    $defects = [System.Collections.Generic.List[hashtable]]::new()

    function Walk-PwSuites {
        param($Suites, [System.Collections.Generic.List[hashtable]]$DefectList)

        foreach ($suite in $Suites) {
            $file = $suite.file
            $module = if ($file -match "([^/\\]+)\.") { $Matches[1] } else { $file }

            foreach ($spec in $suite.specs) {
                $lastResult = $null
                $lastStatus = ""
                foreach ($t in $spec.tests) {
                    if ($t.results -and $t.results.Count -gt 0) {
                        $lastResult = $t.results[-1]
                        $lastStatus = $lastResult.status
                    }
                }

                if ($lastStatus -ne "failed" -and $lastStatus -ne "timedOut") { continue }

                $defType = switch ($lastStatus) {
                    "timedOut" { "超时" }
                    default    { "断言失败" }
                }

                $duration = if ($lastResult) { $lastResult.duration } else { 0 }
                $errorMsg = ""
                if ($lastResult -and $lastResult.errors) {
                    foreach ($err in $lastResult.errors) {
                        if ($err.message) {
                            $errorMsg = $err.message
                            break
                        }
                    }
                }
                $shortMsg = if ($errorMsg.Length -gt 200) { $errorMsg.Substring(0, 200) + "..." } else { $errorMsg }
                $safeMsg = $shortMsg -replace "`r?`n", " " -replace "\|", "/"

                $caseId = ""
                $caseTitle = $spec.title
                if ($spec.title -match "^([A-Z]+-[A-Z]+-\d+)\s+(.+)$") {
                    $caseId = $Matches[1]
                    $caseTitle = $Matches[2]
                }

                $DefectList.Add(@{
                    Index       = $DefectList.Count + 1
                    Module      = $module
                    CaseId      = $caseId
                    CaseTitle   = $caseTitle
                    DefectType  = $defType
                    Duration    = $duration
                    ShortMessage = $safeMsg
                })
            }

            if ($suite.suites -and $suite.suites.Count -gt 0) {
                Walk-PwSuites -Suites $suite.suites -DefectList $DefectList
            }
        }
    }

    if ($json.suites) {
        Walk-PwSuites -Suites $json.suites -DefectList $defects
    }

    Write-Output -NoEnumerate $defects
}

function Get-JtlDefects {
    param(
        [string]$JtlPath,
        [int]$LatencyThresholdMs = 3000,
        [double]$ErrorRateThreshold = 0.05
    )

    if (-not (Test-Path -LiteralPath $JtlPath)) {
        return @()
    }

    try {
        $rows = Import-Csv -LiteralPath $JtlPath
    } catch {
        return @()
    }

    if ($rows.Count -eq 0) { return @() }

    $groups = $rows | Group-Object -Property { $_.label }

    $defects = [System.Collections.Generic.List[hashtable]]::new()
    $index = 0

    foreach ($g in $groups) {
        $total = $g.Count
        $failed = @($g.Group | Where-Object { $_.success -eq "false" }).Count
        $errorRate = if ($total -gt 0) { $failed / $total } else { 0 }
        $latencies = $g.Group | ForEach-Object { [int]$_.elapsed }
        $sorted = $latencies | Sort-Object
        $avg = if ($total -gt 0) { [math]::Round(($latencies | Measure-Object -Average).Average, 0) } else { 0 }
        $p95Idx = [math]::Floor($total * 0.95)
        $p95 = if ($p95Idx -lt $sorted.Count) { $sorted[$p95Idx] } else { $sorted[-1] }
        $p99Idx = [math]::Floor($total * 0.99)
        $p99 = if ($p99Idx -lt $sorted.Count) { $sorted[$p99Idx] } else { $sorted[-1] }

        $isDefect = ($errorRate -gt $ErrorRateThreshold) -or ($p95 -gt $LatencyThresholdMs) -or ($failed -gt 0)
        if (-not $isDefect) { continue }

        $index++
        $defType = if ($errorRate -gt $ErrorRateThreshold) { "性能异常" } elseif ($failed -gt 0) { "断言失败" } else { "超时" }
        $url = ""
        $firstRow = $g.Group[0]
        if ($firstRow.PSObject.Properties.Name -contains "URL" -and $firstRow.URL) {
            $url = $firstRow.URL
        } elseif ($firstRow.PSObject.Properties.Name -contains "label") {
            $url = $firstRow.label
        }

        $defects.Add(@{
            Index       = $index
            Url         = $g.Name
            Total       = $total
            Failed      = $failed
            ErrorRate   = "{0:P1}" -f $errorRate
            AvgMs       = $avg
            P95Ms       = $p95
            P99Ms       = $p99
            DefectType  = $defType
            ShortMessage = "error_rate=$errorRate, p95=${p95}ms"
        })
    }

    Write-Output -NoEnumerate $defects
}

function Get-ZapDefects {
    param([string]$ZapJsonPath)

    if (-not (Test-Path -LiteralPath $ZapJsonPath)) {
        return @()
    }

    try {
        try {
            $json = Get-Content -LiteralPath $ZapJsonPath -Encoding utf8 -Raw | ConvertFrom-Json -Depth 20 -ErrorAction Stop
        } catch {
            $json = Get-Content -LiteralPath $ZapJsonPath -Encoding utf8 -Raw | ConvertFrom-Json
        }
    } catch {
        return @()
    }

    $defects = [System.Collections.Generic.List[hashtable]]::new()
    $index = 0

    $riskMap = @{ "3" = "高危"; "2" = "中危"; "1" = "低危"; "0" = "信息性" }
    $typeMap = @{ "3" = "高危漏洞"; "2" = "中危漏洞"; "1" = "低危漏洞"; "0" = "信息性" }

    $sites = if ($json.site) { $json.site } else { @() }
    foreach ($site in $sites) {
        $alerts = if ($site.alerts) { $site.alerts } else { @() }
        foreach ($alert in $alerts) {
            $index++
            $riskCode = [string]$alert.riskcode
            $riskLabel = if ($riskMap.ContainsKey($riskCode)) { $riskMap[$riskCode] } else { "未知" }
            $defType = if ($typeMap.ContainsKey($riskCode)) { $typeMap[$riskCode] } else { "断言失败" }
            $desc = if ($alert.desc) { ($alert.desc -replace "<[^>]+>", "" -replace "`r?`n", " ").Trim() } else { "" }
            $shortDesc = if ($desc.Length -gt 200) { $desc.Substring(0, 200) + "..." } else { $desc }
            $url = if ($alert.url) { $alert.url } else { $site.name }

            $defects.Add(@{
                Index       = $index
                VulnName    = $alert.alert
                RiskLevel   = $riskLabel
                Url         = $url
                DefectType  = $defType
                ShortMessage = $shortDesc
            })
        }
    }

    Write-Output -NoEnumerate $defects
}