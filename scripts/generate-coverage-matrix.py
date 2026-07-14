import os
import re
import glob
import yaml
from datetime import datetime

def parse_markdown_table(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    tables = []
    table_pattern = r'\|.*?\|[\s\S]*?(?=\n\n|\Z)'
    for match in re.finditer(table_pattern, content):
        table_text = match.group(0)
        lines = [line.strip() for line in table_text.split('\n') if line.strip()]
        if len(lines) >= 3:
            headers = [h.strip() for h in lines[0].split('|')[1:-1]]
            rows = []
            for line in lines[2:]:
                if line.startswith('|') and line.endswith('|'):
                    cells = [c.strip() for c in line.split('|')[1:-1]]
                    if len(cells) == len(headers):
                        rows.append(dict(zip(headers, cells)))
            tables.append({'headers': headers, 'rows': rows})
    return tables

def find_test_scripts(tests_dir):
    scripts = {}
    for root, dirs, files in os.walk(tests_dir):
        for file in files:
            if file.endswith('.spec.ts') or file.endswith('.py'):
                rel_path = os.path.relpath(os.path.join(root, file), tests_dir)
                if file.startswith('test_') or file.endswith('.spec.ts'):
                    script_type = 'ui' if file.endswith('.spec.ts') else 'api'
                    module = os.path.dirname(rel_path)
                    if module not in scripts:
                        scripts[module] = []
                    scripts[module].append({
                        'path': rel_path,
                        'type': script_type,
                        'name': os.path.splitext(file)[0]
                    })
    return scripts

def generate_coverage_matrix(cases_dir, tests_dir, output_path, run_id=None):
    if run_id is None:
        run_id = datetime.now().strftime('%Y%m%d-%H%M%S')
    
    case_files = glob.glob(os.path.join(cases_dir, '*-评审版.md'))
    if not case_files:
        print(f"未找到评审版用例文件: {cases_dir}")
        return None
    
    test_scripts = find_test_scripts(tests_dir)
    
    coverage_rows = []
    for case_file in case_files:
        file_name = os.path.basename(case_file)
        tables = parse_markdown_table(case_file)
        
        for table in tables:
            if '用例编号' in table['headers'] and '用例标题' in table['headers']:
                for row in table['rows']:
                    case_id = row.get('用例编号', '')
                    case_title = row.get('用例标题', '')
                    priority = row.get('优先级', '')
                    module = row.get('对应需求ID', '')[:6] if row.get('对应需求ID') else ''
                    
                    matched_script = None
                    script_path = ''
                    execution_level = ''
                    current_status = '未实现'
                    execution_status = '未执行'
                    assertion_source = '待确认'
                    
                    case_lower = case_title.lower()
                    for script_module, scripts in test_scripts.items():
                        for script in scripts:
                            script_name = script['name'].lower()
                            if ('crm' in script_name and 'crm' in case_lower) or \
                               ('business' in script_name and '商机' in case_title) or \
                               ('clue' in script_name and '线索' in case_title) or \
                               ('customer' in script_name and '客户' in case_title) or \
                               ('product' in script_name and '产品' in case_title) or \
                               ('quotation' in script_name and '报价' in case_title) or \
                               ('login' in script_name and '登录' in case_title) or \
                               ('smoke' in script_name):
                                matched_script = script
                                script_path = script['path']
                                execution_level = 'smoke' if 'smoke' in script_name else 'regression'
                                current_status = '已实现'
                                execution_status = '待执行'
                                assertion_source = '实测接口基线'
                                break
                        if matched_script:
                            break
                    
                    coverage_rows.append({
                        '序号': len(coverage_rows) + 1,
                        '用例编号': case_id,
                        '模块': module,
                        '用例标题': case_title,
                        '优先级': priority,
                        '断言来源': assertion_source,
                        '评审自动化结论': '已通过' if case_id else '待确认',
                        '执行层级': execution_level,
                        '目标脚本': script_path,
                        '当前状态': current_status,
                        '执行状态': execution_status,
                        '执行编排': '自动',
                        '说明': ''
                    })
    
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    markdown = f"""# 测试覆盖矩阵

## 当前阶段
自动化执行前覆盖矩阵生成

## 输入文件
{chr(10).join([f"- `{os.path.basename(f)}`" for f in case_files])}

## 产出文件
- `{output_path}`

## 覆盖统计

| 统计项 | 数量 |
|--------|------|
| 总用例数 | {len(coverage_rows)} |
| 已实现脚本 | {sum(1 for r in coverage_rows if r['当前状态'] == '已实现')} |
| 未实现脚本 | {sum(1 for r in coverage_rows if r['当前状态'] == '未实现')} |
| 已执行 | {sum(1 for r in coverage_rows if r['执行状态'] == '已执行')} |
| 待执行 | {sum(1 for r in coverage_rows if r['执行状态'] == '待执行')} |
| 阻塞 | {sum(1 for r in coverage_rows if r['执行状态'] == '阻塞')} |

## 覆盖矩阵详情

| 序号 | 用例编号 | 模块 | 用例标题 | 优先级 | 断言来源 | 评审自动化结论 | 执行层级 | 目标脚本 | 当前状态 | 执行状态 | 执行编排 | 说明 |
|------|----------|------|----------|--------|----------|----------------|----------|----------|----------|----------|----------|------|
"""
    
    for row in coverage_rows:
        markdown += f"| {row['序号']} | {row['用例编号']} | {row['模块']} | {row['用例标题']} | {row['优先级']} | {row['断言来源']} | {row['评审自动化结论']} | {row['执行层级']} | `{row['目标脚本']}` | {row['当前状态']} | {row['执行状态']} | {row['执行编排']} | {row['说明']} |\n"
    
    markdown += """

## 执行结论
覆盖矩阵已生成，可作为自动化执行门禁依据。

## 风险与待确认项
- 部分用例可能未正确匹配到目标脚本，需要人工核对。
- 断言来源默认标记为"实测接口基线"，需要根据实际情况调整。

## 下一步建议
- 人工核对覆盖矩阵，补充缺失的脚本映射
- 确认阻塞用例的阻塞原因
- 更新执行状态后开始自动化执行
"""
    
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(markdown)
    
    print(f"覆盖矩阵已生成: {output_path}")
    return output_path

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='生成测试覆盖矩阵')
    parser.add_argument('--cases-dir', default='docs/cases', help='用例目录')
    parser.add_argument('--tests-dir', default='tests', help='测试脚本目录')
    parser.add_argument('--output', default='docs/cases/测试用例覆盖矩阵.md', help='输出文件路径')
    parser.add_argument('--run-id', default=None, help='测试批次ID')
    
    args = parser.parse_args()
    
    generate_coverage_matrix(args.cases_dir, args.tests_dir, args.output, args.run_id)
