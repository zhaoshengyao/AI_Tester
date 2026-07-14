import os
import json
from datetime import datetime

def generate_report(results_dir, test_type, metrics):
    """
    生成性能测试报告
    
    Args:
        results_dir: 结果目录
        test_type: 测试类型 (api/ui)
        metrics: 性能指标字典
    
    Returns:
        报告文件路径
    """
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    report_dir = os.path.join(results_dir, test_type)
    os.makedirs(report_dir, exist_ok=True)
    
    report = {
        "timestamp": timestamp,
        "test_type": test_type,
        "metrics": metrics,
        "summary": _generate_summary(metrics)
    }
    
    report_file = os.path.join(report_dir, f"report_{timestamp}.json")
    with open(report_file, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)
    
    html_report_file = os.path.join(report_dir, f"report_{timestamp}.html")
    with open(html_report_file, "w", encoding="utf-8") as f:
        f.write(_generate_html_report(report))
    
    return html_report_file

def _generate_summary(metrics):
    """生成报告摘要"""
    summary = {
        "status": "PASS" if metrics.get("error_rate", 0) < 0.01 else "FAIL",
        "rps": metrics.get("rps", 0),
        "avg_response_time": metrics.get("avg_response_time", 0),
        "p95_response_time": metrics.get("p95_response_time", 0),
        "p99_response_time": metrics.get("p99_response_time", 0),
        "error_rate": metrics.get("error_rate", 0)
    }
    return summary

def _generate_html_report(report):
    """生成 HTML 格式报告"""
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>性能测试报告 - {report['test_type']}</title>
    <style>
        body {{ font-family: 'Microsoft YaHei', sans-serif; margin: 0; padding: 20px; background: #f5f5f5; }}
        .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); }}
        h1 {{ color: #333; border-bottom: 2px solid #007bff; padding-bottom: 10px; }}
        .summary {{ display: flex; gap: 20px; margin: 20px 0; }}
        .card {{ flex: 1; padding: 15px; border-radius: 8px; text-align: center; }}
        .card.success {{ background: #d4edda; color: #155724; }}
        .card.fail {{ background: #f8d7da; color: #721c24; }}
        .card.info {{ background: #d1ecf1; color: #0c5460; }}
        .metrics {{ margin-top: 20px; }}
        table {{ width: 100%; border-collapse: collapse; }}
        th, td {{ padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }}
        th {{ background: #007bff; color: white; }}
        .timestamp {{ color: #666; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="container">
        <h1>性能测试报告</h1>
        <p class="timestamp">生成时间: {report['timestamp']}</p>
        <p>测试类型: {report['test_type'].upper()}</p>
        
        <div class="summary">
            <div class="card {'success' if report['summary']['status'] == 'PASS' else 'fail'}">
                <div style="font-size: 24px; font-weight: bold;">{report['summary']['status']}</div>
                <div>测试结果</div>
            </div>
            <div class="card info">
                <div style="font-size: 24px; font-weight: bold;">{report['summary']['rps']:.1f}</div>
                <div>每秒请求数 (RPS)</div>
            </div>
            <div class="card info">
                <div style="font-size: 24px; font-weight: bold;">{report['summary']['avg_response_time']:.1f}ms</div>
                <div>平均响应时间</div>
            </div>
            <div class="card info">
                <div style="font-size: 24px; font-weight: bold;">{report['summary']['p95_response_time']:.1f}ms</div>
                <div>P95 响应时间</div>
            </div>
            <div class="card info">
                <div style="font-size: 24px; font-weight: bold;">{report['summary']['error_rate']:.2%}</div>
                <div>错误率</div>
            </div>
        </div>
        
        <div class="metrics">
            <h2>详细指标</h2>
            <table>
                <thead>
                    <tr>
                        <th>指标名称</th>
                        <th>数值</th>
                        <th>单位</th>
                    </tr>
                </thead>
                <tbody>
    """
    
    metrics_map = {
        "rps": ("每秒请求数", ""),
        "avg_response_time": ("平均响应时间", "ms"),
        "min_response_time": ("最小响应时间", "ms"),
        "max_response_time": ("最大响应时间", "ms"),
        "p90_response_time": ("P90 响应时间", "ms"),
        "p95_response_time": ("P95 响应时间", "ms"),
        "p99_response_time": ("P99 响应时间", "ms"),
        "error_rate": ("错误率", "%"),
        "total_requests": ("总请求数", ""),
        "failed_requests": ("失败请求数", ""),
        "active_users": ("活跃用户数", "")
    }
    
    for key, value in report['metrics'].items():
        if key in metrics_map:
            name, unit = metrics_map[key]
            display_value = f"{value:.2%}" if unit == "%" else f"{value:.1f}"
            html += f"<tr><td>{name}</td><td>{display_value}</td><td>{unit}</td></tr>"
    
    html += """
                </tbody>
            </table>
        </div>
    </div>
</body>
</html>
"""
    return html

def load_report(report_path):
    """加载已生成的报告"""
    with open(report_path, "r", encoding="utf-8") as f:
        return json.load(f)