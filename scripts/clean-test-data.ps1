$ErrorActionPreference = "Stop"

$root = Resolve-Path (Join-Path $PSScriptRoot "..")

Write-Host "=== 清理历史测试数据 ===" -ForegroundColor Cyan

$dirsToClean = @(
    (Join-Path $root "docs\test-runs"),
    (Join-Path $root "tests\api\reports"),
    (Join-Path $root "tests\ui\reports"),
    (Join-Path $root "tests\performance\results"),
    (Join-Path $root "tests\security\reports")
)

foreach ($dir in $dirsToClean) {
    if (Test-Path -LiteralPath $dir) {
        Write-Host "清理目录: $dir" -ForegroundColor Yellow
        try {
            Remove-Item -LiteralPath $dir -Recurse -Force -ErrorAction Stop
            Write-Host "  ✓ 清理完成" -ForegroundColor Green
        } catch {
            Write-Host "  ✗ 清理失败: $_" -ForegroundColor Red
        }
    } else {
        Write-Host "  - 目录不存在: $dir" -ForegroundColor Gray
    }
}

Write-Host ""
Write-Host "=== 历史测试数据清理完成 ===" -ForegroundColor Cyan
