# CRM 性能测试分阶段执行脚本
# 执行顺序：冒烟 → 业务流程 → 常规 → 只读高压 → 压力 → 稳定性

$ErrorActionPreference = "Continue"
$ResultsDir = "results/staged"
$LogFile = "results/staged/staged_execution_log.txt"

# 创建结果目录
if (-not (Test-Path $ResultsDir)) {
    New-Item -ItemType Directory -Path $ResultsDir -Force | Out-Null
}

# 日志函数
function Write-Log {
    param($Message, $Color = "White")
    $Timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    $LogEntry = "[$Timestamp] $Message"
    Write-Host $LogEntry -ForegroundColor $Color
    $LogEntry | Out-File -FilePath $LogFile -Append -Encoding UTF8
}

# 执行压测函数
function Invoke-Stage {
    param(
        [string]$StageName,
        [string]$StageLabel,
        [string]$Script,
        [int]$Users,
        [int]$SpawnRate,
        [string]$RunTime,
        [float]$MaxErrorRate,
        [float]$MaxAvgResponseTime,
        [float]$MinRps
    )
    
    Write-Log "========================================" "Cyan"
    Write-Log "开始执行: $StageLabel" "Cyan"
    Write-Log "  脚本: $Script" "Gray"
    Write-Log "  用户数: $Users, 孵化率: $SpawnRate/s, 时长: $RunTime" "Gray"
    Write-Log "  成功标准: 错误率<$MaxErrorRate, 平均响应<$MaxAvgResponseTime ms, RPS>=$MinRps" "Gray"
    Write-Log "========================================" "Cyan"
    
    $Timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
    $ReportFile = "$ResultsDir/${StageName}_${Timestamp}.html"
    
    $Command = "locust -f $Script --users=$Users --spawn-rate=$SpawnRate --run-time=$RunTime --headless --html=$ReportFile"
    
    Write-Log "执行命令: $Command" "Yellow"
    
    # 执行压测
    $Output = Invoke-Expression $Command 2>&1
    $ExitCode = $LASTEXITCODE
    
    # 保存完整输出
    $Output | Out-File -FilePath "$ResultsDir/${StageName}_${Timestamp}.log" -Encoding UTF8
    
    if ($ExitCode -ne 0) {
        Write-Log "❌ $StageLabel 执行失败 (退出码: $ExitCode)" "Red"
        return @{ Success = $false; Reason = "执行失败" }
    }
    
    # 解析结果
    $Lines = $Output -split "`n"
    $AggregatedLine = $Lines | Where-Object { $_ -match "Aggregated" } | Select-Object -Last 1
    
    if (-not $AggregatedLine) {
        Write-Log "⚠️ $StageLabel 无法解析结果" "Yellow"
        return @{ Success = $false; Reason = "无法解析结果" }
    }
    
    # 提取指标
    $Match = [regex]::Match($AggregatedLine, "Aggregated\s+(\d+)\s+(\d+)\(([\d.]+)%\)\s+\|\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+\|\s+([\d.]+)\s+([\d.]+)")
    
    if (-not $Match.Success) {
        Write-Log "⚠️ $StageLabel 结果格式异常" "Yellow"
        return @{ Success = $false; Reason = "结果格式异常" }
    }
    
    $TotalRequests = [int]$Match.Groups[1].Value
    $FailedRequests = [int]$Match.Groups[2].Value
    $ErrorRate = [float]$Match.Groups[3].Value / 100.0
    $AvgResponseTime = [float]$Match.Groups[4].Value
    $Rps = [float]$Match.Groups[8].Value
    
    Write-Log "📊 执行结果:" "White"
    Write-Log "  总请求数: $TotalRequests" "White"
    Write-Log "  失败数: $FailedRequests" "White"
    Write-Log "  错误率: $([math]::Round($ErrorRate * 100, 2))%" $(if ($ErrorRate -lt $MaxErrorRate) { "Green" } else { "Red" })
    Write-Log "  平均响应时间: $AvgResponseTime ms" $(if ($AvgResponseTime -lt $MaxAvgResponseTime) { "Green" } else { "Red" })
    Write-Log "  RPS: $Rps" $(if ($Rps -ge $MinRps) { "Green" } else { "Red" })
    Write-Log "  报告: $ReportFile" "Gray"
    
    # 评估是否通过
    $Passed = $ErrorRate -lt $MaxErrorRate -and $AvgResponseTime -lt $MaxAvgResponseTime -and $Rps -ge $MinRps
    
    if ($Passed) {
        Write-Log "✅ $StageLabel 通过!" "Green"
    } else {
        Write-Log "❌ $StageLabel 未通过" "Red"
        if ($ErrorRate -ge $MaxErrorRate) {
            Write-Log "   原因: 错误率 $([math]::Round($ErrorRate * 100, 2))% >= 阈值 $MaxErrorRate" "Yellow"
        }
        if ($AvgResponseTime -ge $MaxAvgResponseTime) {
            Write-Log "   原因: 平均响应 $AvgResponseTime ms >= 阈值 $MaxAvgResponseTime ms" "Yellow"
        }
        if ($Rps -lt $MinRps) {
            Write-Log "   原因: RPS $Rps < 阈值 $MinRps" "Yellow"
        }
    }
    
    return @{
        Success = $Passed
        TotalRequests = $TotalRequests
        FailedRequests = $FailedRequests
        ErrorRate = $ErrorRate
        AvgResponseTime = $AvgResponseTime
        Rps = $Rps
        ReportFile = $ReportFile
    }
}

# ============ 主执行流程 ============

Write-Host ""
Write-Host "╔══════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║     CRM 性能测试 - 分阶段执行                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

$Results = @()
$ContinueToNextStage = $true

# 阶段1: 冒烟测试（已通过，跳过）
Write-Log "阶段1 冒烟测试已通过，跳过执行" "Green"
$Results += @{ Stage = "阶段1: 冒烟测试"; Passed = $true; Note = "已通过" }

if ($ContinueToNextStage) {
    # 阶段2: 业务流程压测
    $Stage2Result = Invoke-Stage `
        -StageName "stage2_business_flow" `
        -StageLabel "阶段2: 业务流程压测" `
        -Script "api/locustfile_business_flow.py" `
        -Users 10 `
        -SpawnRate 2 `
        -RunTime "300s" `
        -MaxErrorRate 0.05 `
        -MaxAvgResponseTime 1000 `
        -MinRps 5
    
    $Results += @{ 
        Stage = "阶段2: 业务流程压测" 
        Passed = $Stage2Result.Success 
        TotalRequests = $Stage2Result.TotalRequests
        ErrorRate = $Stage2Result.ErrorRate
        AvgResponseTime = $Stage2Result.AvgResponseTime
        Rps = $Stage2Result.Rps
    }
    
    if (-not $Stage2Result.Success) {
        Write-Log "阶段2未通过，停止执行" "Red"
        $ContinueToNextStage = $false
    }
}

if ($ContinueToNextStage) {
    # 阶段3: 常规压测
    $Stage3Result = Invoke-Stage `
        -StageName "stage3_normal" `
        -StageLabel "阶段3: 常规压测" `
        -Script "api/locustfile_crm_api.py" `
        -Users 50 `
        -SpawnRate 5 `
        -RunTime "300s" `
        -MaxErrorRate 0.01 `
        -MaxAvgResponseTime 500 `
        -MinRps 50
    
    $Results += @{ 
        Stage = "阶段3: 常规压测" 
        Passed = $Stage3Result.Success 
        TotalRequests = $Stage3Result.TotalRequests
        ErrorRate = $Stage3Result.ErrorRate
        AvgResponseTime = $Stage3Result.AvgResponseTime
        Rps = $Stage3Result.Rps
    }
    
    if (-not $Stage3Result.Success) {
        Write-Log "阶段3未通过，停止执行" "Red"
        $ContinueToNextStage = $false
    }
}

if ($ContinueToNextStage) {
    # 阶段4: 只读高压
    $Stage4Result = Invoke-Stage `
        -StageName "stage4_readonly_heavy" `
        -StageLabel "阶段4: 只读高压" `
        -Script "api/locustfile_crm_api.py" `
        -Users 100 `
        -SpawnRate 10 `
        -RunTime "300s" `
        -MaxErrorRate 0.05 `
        -MaxAvgResponseTime 1000 `
        -MinRps 200
    
    $Results += @{ 
        Stage = "阶段4: 只读高压" 
        Passed = $Stage4Result.Success 
        TotalRequests = $Stage4Result.TotalRequests
        ErrorRate = $Stage4Result.ErrorRate
        AvgResponseTime = $Stage4Result.AvgResponseTime
        Rps = $Stage4Result.Rps
    }
    
    if (-not $Stage4Result.Success) {
        Write-Log "阶段4未通过，停止执行" "Red"
        $ContinueToNextStage = $false
    }
}

if ($ContinueToNextStage) {
    # 阶段5: 压力测试
    $Stage5Result = Invoke-Stage `
        -StageName "stage5_stress" `
        -StageLabel "阶段5: 压力测试" `
        -Script "api/locustfile_crm_api.py" `
        -Users 200 `
        -SpawnRate 10 `
        -RunTime "600s" `
        -MaxErrorRate 0.10 `
        -MaxAvgResponseTime 3000 `
        -MinRps 300
    
    $Results += @{ 
        Stage = "阶段5: 压力测试" 
        Passed = $Stage5Result.Success 
        TotalRequests = $Stage5Result.TotalRequests
        ErrorRate = $Stage5Result.ErrorRate
        AvgResponseTime = $Stage5Result.AvgResponseTime
        Rps = $Stage5Result.Rps
    }
    
    if (-not $Stage5Result.Success) {
        Write-Log "阶段5未通过，停止执行" "Red"
        $ContinueToNextStage = $false
    }
}

# ============ 汇总报告 ============

Write-Host ""
Write-Host "╔══════════════════════════════════════════════════════════╗" -ForegroundColor Cyan
Write-Host "║              CRM 性能测试 - 分阶段执行汇总                ║" -ForegroundColor Cyan
Write-Host "╚══════════════════════════════════════════════════════════╝" -ForegroundColor Cyan
Write-Host ""

Write-Host "阶段" -NoNewline -ForegroundColor White
Write-Host " | 状态" -NoNewline -ForegroundColor White
Write-Host " | 总请求" -NoNewline -ForegroundColor White
Write-Host " | 错误率" -NoNewline -ForegroundColor White
Write-Host " | 平均响应(ms)" -NoNewline -ForegroundColor White
Write-Host " | RPS" -ForegroundColor White
Write-Host "------------------------------------------------------------"

foreach ($Result in $Results) {
    $Status = if ($Result.Passed) { "✅ 通过" } else { "❌ 未通过" }
    $Color = if ($Result.Passed) { "Green" } else { "Red" }
    
    $Total = if ($Result.TotalRequests) { $Result.TotalRequests } else { "-" }
    $ErrRate = if ($Result.ErrorRate) { "$([math]::Round($Result.ErrorRate * 100, 2))%" } else { "-" }
    $AvgResp = if ($Result.AvgResponseTime) { $Result.AvgResponseTime } else { "-" }
    $Rps = if ($Result.Rps) { $Result.Rps } else { "-" }
    
    Write-Host "$($Result.Stage.PadRight(20)) | $($Status.PadRight(10)) | $($Total.ToString().PadRight(8)) | $($ErrRate.PadRight(8)) | $($AvgResp.ToString().PadRight(14)) | $Rps" -ForegroundColor $Color
}

Write-Host ""
Write-Log "分阶段执行完成" "Cyan"

# 生成汇总报告
$SummaryReport = @{
    timestamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    stages = $Results
    total_stages = $Results.Count
    passed_stages = ($Results | Where-Object { $_.Passed }).Count
    failed_stages = ($Results | Where-Object { -not $_.Passed }).Count
}

$SummaryReport | ConvertTo-Json -Depth 3 | Out-File -FilePath "$ResultsDir/summary_report.json" -Encoding UTF8

Write-Host "汇总报告已保存: $ResultsDir/summary_report.json" "Gray"
Write-Host "详细日志已保存: $LogFile" "Gray"

# ============ 综合性能测试报告生成 ============
# 规则：稳定性测试（stage6_soak）结束后，必须汇总生成一份综合性能测试报告
# 参考配置：config/load_profiles.yaml -> report_generation

function New-ComprehensiveReport {
    param($StageResults)
    
    Write-Log "========================================" "Magenta"
    Write-Log "生成综合性能测试报告" "Magenta"
    Write-Log "========================================" "Magenta"
    
    $ReportDate = Get-Date -Format "yyyyMMdd"
    $ReportFile = "results/PERFORMANCE_REPORT_$ReportDate.md"
    
    # 检查是否已存在报告（增量更新）
    $ReportExists = Test-Path $ReportFile
    
    if ($ReportExists) {
        Write-Log "综合报告已存在，执行增量更新: $ReportFile" "Yellow"
    } else {
        Write-Log "创建新综合报告: $ReportFile" "Yellow"
    }
    
    Write-Log "综合报告路径: $ReportFile" "Green"
    Write-Log "报告规则: 稳定性测试结束后强制汇总（参考 config/load_profiles.yaml）" "Gray"
    
    # 提示AI生成报告（实际报告内容由AI根据各阶段数据生成）
    Write-Host ""
    Write-Host "📋 综合报告生成提示:" -ForegroundColor Magenta
    Write-Host "   稳定性测试已结束，需汇总生成综合性能测试报告" -ForegroundColor White
    Write-Host "   报告路径: $ReportFile" -ForegroundColor Gray
    Write-Host "   必含章节:" -ForegroundColor Gray
    Write-Host "     一、分阶段执行汇总" -ForegroundColor Gray
    Write-Host "     二、详细指标分析" -ForegroundColor Gray
    Write-Host "     三、接口响应时间分布" -ForegroundColor Gray
    Write-Host "     四、系统性能评估（安全容量/拐点/崩溃点）" -ForegroundColor Gray
    Write-Host "     五、后续建议（优化建议优先级排序）" -ForegroundColor Gray
    Write-Host "     六、测试命令记录" -ForegroundColor Gray
    Write-Host ""
    Write-Host "   ⚠️ 必须给出核心结论: 系统安全容量、性能拐点、崩溃点、稳定性评估" -ForegroundColor Yellow
    Write-Host ""
    
    return @{
        ReportFile = $ReportFile
        ReportExists = $ReportExists
        Generated = $true
    }
}

# ============ 综合报告归档 ============
# 规则：综合报告生成后，必须同步归档到 docs/test-runs/YYYYMMDD-HHMMSS/ 批次目录
# 归档位置：
#   - reports/性能测试报告.md（综合报告）
#   - raw/performance/*.html（原始HTML报告）
#   - raw/performance/staged/（分阶段执行日志）
function Archive-ComprehensiveReport {
    param(
        [string]$ComprehensiveReportPath
    )
    
    Write-Log "========================================" "Magenta"
    Write-Log "归档综合性能测试报告到批次目录" "Magenta"
    Write-Log "========================================" "Magenta"
    
    # 查找最新的批次目录 docs/test-runs/YYYYMMDD-HHMMSS/
    $ProjectRoot = Resolve-Path "$PSScriptRoot\..\..\..\.."
    $TestRunsDir = Join-Path $ProjectRoot "docs\test-runs"
    
    if (-not (Test-Path $TestRunsDir)) {
        Write-Log "未找到批次目录: $TestRunsDir，跳过归档" "Yellow"
        return @{ Archived = $false; Reason = "批次目录不存在" }
    }
    
    # 获取最新批次目录
    $LatestBatch = Get-ChildItem $TestRunsDir -Directory | Sort-Object Name -Descending | Select-Object -First 1
    if (-not $LatestBatch) {
        Write-Log "批次目录为空，跳过归档" "Yellow"
        return @{ Archived = $false; Reason = "批次目录为空" }
    }
    
    $BatchDir = $LatestBatch.FullName
    $ReportsDir = Join-Path $BatchDir "reports"
    $RawPerfDir = Join-Path $BatchDir "raw\performance"
    $ResultsDir = Resolve-Path "$PSScriptRoot\..\results"
    
    Write-Log "目标批次目录: $BatchDir" "Gray"
    
    # 确保目标目录存在
    if (-not (Test-Path $ReportsDir)) {
        New-Item -ItemType Directory -Path $ReportsDir -Force | Out-Null
    }
    if (-not (Test-Path $RawPerfDir)) {
        New-Item -ItemType Directory -Path $RawPerfDir -Force | Out-Null
    }
    
    # 1. 归档综合报告（重命名为"性能测试报告.md"，符合项目命名规范）
    if (Test-Path $ComprehensiveReportPath) {
        $ArchiveReportPath = Join-Path $ReportsDir "性能测试报告.md"
        Copy-Item -Path $ComprehensiveReportPath -Destination $ArchiveReportPath -Force
        Write-Log "归档综合报告: $ArchiveReportPath" "Green"
    } else {
        Write-Log "综合报告不存在: $ComprehensiveReportPath" "Yellow"
    }
    
    # 2. 归档原始HTML报告
    $HtmlFiles = Get-ChildItem $ResultsDir -Filter "*.html" -ErrorAction SilentlyContinue
    foreach ($HtmlFile in $HtmlFiles) {
        Copy-Item -Path $HtmlFile.FullName -Destination $RawPerfDir -Force
    }
    Write-Log "归档HTML报告: $($HtmlFiles.Count) 个" "Green"
    
    # 3. 归档分阶段执行日志（如果有）
    $StagedDir = Join-Path $ResultsDir "staged"
    if (Test-Path $StagedDir) {
        $StagedArchiveDir = Join-Path $RawPerfDir "staged"
        if (-not (Test-Path $StagedArchiveDir)) {
            New-Item -ItemType Directory -Path $StagedArchiveDir -Force | Out-Null
        }
        $StagedFiles = Get-ChildItem $StagedDir -Recurse -File
        foreach ($File in $StagedFiles) {
            Copy-Item -Path $File.FullName -Destination $StagedArchiveDir -Force
        }
        Write-Log "归档分阶段日志: $($StagedFiles.Count) 个" "Green"
    }
    
    Write-Log "归档完成" "Green"
    
    return @{
        Archived = $true
        BatchDir = $BatchDir
        ReportsDir = $ReportsDir
        RawPerfDir = $RawPerfDir
    }
}

# 检查是否触发了稳定性测试（stage6）
$SoakStageExecuted = $false
foreach ($Result in $Results) {
    if ($Result.Stage -match "稳定性|stage6|soak") {
        $SoakStageExecuted = $true
        break
    }
}

# 如果稳定性测试已执行，触发综合报告生成 + 归档
if ($SoakStageExecuted) {
    Write-Log "检测到稳定性测试已执行，触发综合报告生成" "Magenta"
    $ReportResult = New-ComprehensiveReport -StageResults $Results
    Write-Log "综合报告生成状态: $($ReportResult.Generated)" "Green"
    
    # 综合报告生成后，自动归档到批次目录
    if ($ReportResult.Generated) {
        Write-Log "开始归档综合报告到批次目录" "Magenta"
        $ArchiveResult = Archive-ComprehensiveReport -ComprehensiveReportPath $ReportResult.ReportFile
        if ($ArchiveResult.Archived) {
            Write-Log "归档成功 - 批次目录: $($ArchiveResult.BatchDir)" "Green"
        } else {
            Write-Log "归档跳过 - 原因: $($ArchiveResult.Reason)" "Yellow"
        }
    }
} else {
    Write-Log "未检测到稳定性测试执行，跳过综合报告生成" "Gray"
    Write-Log "提示: 稳定性测试（stage6_soak）结束后将自动触发综合报告生成与归档" "Gray"
}