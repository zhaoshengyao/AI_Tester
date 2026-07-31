import os
import re
import sys
from datetime import datetime


def scan_api_tests(base_path):
    """扫描API测试目录，提取测试函数"""
    api_tests = {}
    test_dir = os.path.join(base_path, 'tests', 'api', 'testsuites')
    
    if not os.path.exists(test_dir):
        return api_tests
    
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.startswith('test_') and file.endswith('.py'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                func_pattern = re.compile(r'\s*def (test_\w+)\(.*\):')
                functions = func_pattern.findall(content)
                
                relative_path = os.path.relpath(file_path, base_path)
                
                for func in functions:
                    api_tests[func] = {
                        'file': relative_path,
                        'type': 'api'
                    }
    
    return api_tests


def scan_ui_tests(base_path):
    """扫描UI测试目录，提取测试函数"""
    ui_tests = {}
    test_dir = os.path.join(base_path, 'tests', 'ui', 'specs')
    
    if not os.path.exists(test_dir):
        return ui_tests
    
    for root, dirs, files in os.walk(test_dir):
        for file in files:
            if file.endswith('.spec.ts'):
                file_path = os.path.join(root, file)
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                func_pattern = re.compile(r'\s*(?:test|it)\(\s*["\']([^"\']+)["\']')
                functions = func_pattern.findall(content)
                
                relative_path = os.path.relpath(file_path, base_path)
                
                for func in functions:
                    ui_tests[func] = {
                        'file': relative_path,
                        'type': 'ui'
                    }
    
    return ui_tests


def parse_case_document(file_path):
    """解析用例文档，提取用例编号和标题"""
    cases = {}
    
    if not os.path.exists(file_path):
        return cases
    
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    in_table = False
    header_indices = {}
    
    for i, line in enumerate(lines):
        if '| 用例编号' in line and '| 用例标题' in line:
            in_table = True
            headers = [h.strip() for h in line.strip().split('|') if h.strip()]
            for j, header in enumerate(headers):
                header_indices[header] = j
            continue
        
        if in_table and line.startswith('|'):
            if '|------|' in line or '|---|' in line:
                continue
            
            parts = [p.strip() for p in line.strip().split('|') if p.strip()]
            if len(parts) >= 2:
                case_id_idx = header_indices.get('用例编号', -1)
                case_title_idx = header_indices.get('用例标题', -1)
                priority_idx = header_indices.get('优先级', -1)
                scenario_idx = header_indices.get('场景类型', -1)
                
                case_id = parts[case_id_idx] if case_id_idx >= 0 and case_id_idx < len(parts) else ''
                case_title = parts[case_title_idx] if case_title_idx >= 0 and case_title_idx < len(parts) else ''
                priority = parts[priority_idx] if priority_idx >= 0 and priority_idx < len(parts) else 'P2'
                scenario_type = parts[scenario_idx] if scenario_idx >= 0 and scenario_idx < len(parts) else ''
                
                if case_id and not case_id.startswith('|') and not case_id.isdigit():
                    cases[case_id] = {
                        'title': case_title,
                        'priority': priority,
                        'scenario_type': scenario_type,
                        'document': os.path.basename(file_path)
                    }
    
    return cases


CASE_ID_TO_MODULE = {
    'API-AUTH': 'auth',
    'API-CRM-CUS': 'customer',
    'API-CRM-CLU': 'clue',
    'API-CRM-BUS': 'business',
    'API-CRM-CON': 'contact',
    'API-CRM-QTE': 'quotation',
    'API-DICT': 'dict',
    'UI-LOGIN': 'auth',
    'UI-HOME': 'home',
    'UI-CRM-CUS': 'customer',
    'UI-CRM-CLU': 'clue',
    'UI-CRM-BUS': 'business',
    'UI-CRM-CON': 'contact',
    'UI-CRM-QTE': 'quotation',
    'UI-PUB': 'public',
    'UI-REP': 'report',
    'UI-SET': 'settings',
    'FUNC-SYS': 'system',
    'FUNC-CRM-CUS': 'customer',
    'FUNC-CRM-BUS': 'business',
    'FUNC-CRM-CLU': 'clue',
    'FUNC-MKT': 'clue',
    'FUNC-QTE': 'quotation',
    'FUNC-PRD': 'product',
    'FUNC-WORK': 'work',
    'FUNC-TGT': 'target',
    'FUNC-RPT': 'report',
    'FUNC-SET': 'settings',
    'FUNC-STAT': 'stat',
    'FUNC-BUS-CHG': 'business',
    'PERF-AUTH': 'auth',
    'PERF-CRM-CUS': 'customer',
    'PERF-CRM-CLU': 'clue',
    'PERF-CRM-BUS': 'business',
}


def get_module_from_case_id(case_id):
    """从用例编号提取模块标识"""
    for prefix, module in CASE_ID_TO_MODULE.items():
        if case_id.startswith(prefix):
            return module
    return 'other'


def get_module_from_func(func_name):
    """从测试函数名提取模块标识"""
    func_lower = func_name.lower()
    if 'business' in func_lower:
        return 'business'
    elif 'customer' in func_lower or 'cus' in func_lower:
        return 'customer'
    elif 'clue' in func_lower:
        return 'clue'
    elif 'contact' in func_lower or 'con' in func_lower:
        return 'contact'
    elif 'quotation' in func_lower or 'qte' in func_lower:
        return 'quotation'
    elif 'auth' in func_lower or 'login' in func_lower:
        return 'auth'
    elif 'dict' in func_lower:
        return 'dict'
    elif 'product' in func_lower or 'prod' in func_lower:
        return 'product'
    elif 'pub' in func_lower:
        return 'public'
    elif 'home' in func_lower:
        return 'home'
    elif 'rep' in func_lower:
        return 'report'
    elif 'set' in func_lower:
        return 'settings'
    elif 'target' in func_lower or 'tgt' in func_lower:
        return 'target'
    elif 'work' in func_lower:
        return 'work'
    elif 'stat' in func_lower:
        return 'stat'
    elif 'system' in func_lower:
        return 'system'
    return 'other'


def extract_case_number(case_id):
    """从用例编号提取数字部分"""
    match = re.search(r'-(\d{3})$', case_id)
    if match:
        return match.group(1)
    return ''


def find_best_match(case_id, case_title, available_funcs, func_info_map):
    """为用例找到最佳匹配的测试函数"""
    module = get_module_from_case_id(case_id)
    case_num = extract_case_number(case_id)
    title_keywords = [k for k in ['create', 'add', 'new', 'delete', 'remove', 'update', 'edit', 
                                   'list', 'page', 'detail', 'search', 'stage', 'status', 'flow'] 
                      if k in case_title.lower()]
    
    best_match = None
    best_score = 0
    
    for func_name, info in available_funcs.items():
        if get_module_from_func(func_name) != module:
            continue
        
        score = 0
        
        if case_num and case_num in func_name:
            score += 5
        elif case_num and case_num.zfill(3) in func_name:
            score += 3
        
        for keyword in title_keywords:
            if keyword in func_name.lower():
                score += 2
        
        if module in func_name.lower():
            score += 1
        
        if score > best_score:
            best_score = score
            best_match = func_name
    
    if best_match:
        return {
            'script_file': func_info_map[best_match]['file'],
            'script_func': best_match
        }
    
    return None


def analyze_coverage(api_tests, ui_tests, api_cases, ui_cases, func_cases):
    """分析覆盖情况"""
    all_cases = {}
    
    for case_id, info in api_cases.items():
        info['type'] = 'api'
        info['implemented'] = False
        info['script_file'] = ''
        info['script_func'] = ''
        all_cases[case_id] = info
    
    for case_id, info in ui_cases.items():
        info['type'] = 'ui'
        info['implemented'] = False
        info['script_file'] = ''
        info['script_func'] = ''
        all_cases[case_id] = info
    
    for case_id, info in func_cases.items():
        info['type'] = 'func'
        info['implemented'] = False
        info['script_file'] = ''
        info['script_func'] = ''
        all_cases[case_id] = info
    
    func_name_to_info = {}
    for func_name, info in api_tests.items():
        func_name_to_info[func_name] = info
    for func_name, info in ui_tests.items():
        func_name_to_info[func_name] = info
    
    for case_id, case_info in all_cases.items():
        if case_info['type'] == 'api':
            match = find_best_match(case_id, case_info['title'], api_tests, func_name_to_info)
        elif case_info['type'] == 'ui':
            match = find_best_match(case_id, case_info['title'], ui_tests, func_name_to_info)
        else:
            ui_match = find_best_match(case_id, case_info['title'], ui_tests, func_name_to_info)
            api_match = find_best_match(case_id, case_info['title'], api_tests, func_name_to_info)
            match = ui_match if ui_match else api_match
        
        if match:
            case_info['implemented'] = True
            case_info['script_file'] = match['script_file']
            case_info['script_func'] = match['script_func']
    
    return all_cases


def check_crud_completeness(cases):
    """检查每个模块的CRUD用例完整性"""
    crud_checks = {}
    
    crud_keywords = {
        'create': ['新增', '创建', '新建', '添加'],
        'read': ['列表', '详情', '查询', '获取'],
        'update': ['更新', '修改', '编辑'],
        'delete': ['删除', '移除', '删除成功']
    }
    
    modules = {}
    for case_id, info in cases.items():
        module = get_module_from_case_id(case_id)
        if module not in modules:
            modules[module] = {'cases': [], 'type': info.get('type', 'func')}
        modules[module]['cases'].append((case_id, info['title'], info['priority']))
    
    for module, data in modules.items():
        if module == 'other':
            continue
        
        crud_status = {op: False for op in crud_keywords.keys()}
        crud_details = {op: [] for op in crud_keywords.keys()}
        
        for case_id, title, priority in data['cases']:
            for op, keywords in crud_keywords.items():
                if any(kw in title for kw in keywords):
                    crud_status[op] = True
                    crud_details[op].append((case_id, title))
        
        crud_checks[module] = {
            'status': crud_status,
            'details': crud_details,
            'total_cases': len(data['cases']),
            'type': data['type']
        }
    
    return crud_checks


def check_state_transition(cases):
    """检查状态流转用例覆盖情况"""
    transition_checks = {}
    
    state_modules = {
        'business': {
            'states': ['需求确认', '方案报价', '谈判', '赢单', '输单'],
            'keywords': ['阶段', '状态', '流转', '推进', '回退']
        },
        'clue': {
            'states': ['待领取', '已领取', '有效', '无效'],
            'keywords': ['状态', '流转', '领取', '释放', '转化']
        },
        'quotation': {
            'states': ['草稿', '审批中', '已审批', '已拒绝'],
            'keywords': ['审批', '状态', '流转']
        }
    }
    
    for module, config in state_modules.items():
        transition_cases = []
        for case_id, info in cases.items():
            if get_module_from_case_id(case_id) == module:
                if any(kw in info['title'] for kw in config['keywords']):
                    transition_cases.append((case_id, info['title'], info['priority']))
        
        transition_checks[module] = {
            'states': config['states'],
            'total_states': len(config['states']),
            'transition_cases': transition_cases,
            'total_transition_cases': len(transition_cases),
            'has_normal_transition': any('正常' in title for _, title, _ in transition_cases),
            'has_abnormal_transition': any('异常' in title or '无效' in title for _, title, _ in transition_cases),
            'has_boundary_transition': any('边界' in title or '回退' in title for _, title, _ in transition_cases)
        }
    
    return transition_checks


def generate_coverage_matrix(all_cases, crud_checks, transition_checks):
    """生成覆盖矩阵Markdown"""
    sorted_cases = sorted(all_cases.items(), key=lambda x: x[0])
    
    total = len(all_cases)
    implemented = sum(1 for c in all_cases.values() if c['implemented'])
    not_implemented = total - implemented
    
    p0_cases = [c for c in all_cases.values() if c['priority'] == 'P0']
    p0_implemented = sum(1 for c in p0_cases if c['implemented'])
    p0_rate = p0_implemented / len(p0_cases) * 100 if p0_cases else 0
    
    content = f"""# 测试用例覆盖矩阵（自动生成）

## 当前阶段
自动化执行前覆盖矩阵生成

## 生成时间
{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## 输入文件
- `docs/cases/接口测试用例-评审版.md`
- `docs/cases/UI测试用例-评审版.md`
- `docs/cases/功能测试用例-评审版.md`
- `tests/api/` 目录下的实际测试脚本
- `tests/ui/specs/` 目录下的实际测试脚本

## 产出文件
- `docs/cases/测试用例覆盖矩阵.md`

## 覆盖统计

| 统计项 | 数量 |
|--------|------|
| 总用例数 | {total} |
| 已实现脚本 | {implemented} |
| 未实现脚本 | {not_implemented} |
| 实现率 | {implemented/total*100:.1f}% |
| P0用例数 | {len(p0_cases)} |
| P0已实现 | {p0_implemented} |
| P0实现率 | {p0_rate:.1f}% |

## CRUD完整性检查

| 模块 | 新增 | 查询 | 更新 | 删除 | 总用例数 |
|------|------|------|------|------|----------|
"""
    
    for module, check in sorted(crud_checks.items()):
        create_icon = '✅' if check['status']['create'] else '❌'
        read_icon = '✅' if check['status']['read'] else '❌'
        update_icon = '✅' if check['status']['update'] else '❌'
        delete_icon = '✅' if check['status']['delete'] else '❌'
        content += f"""| {module} | {create_icon} | {read_icon} | {update_icon} | {delete_icon} | {check['total_cases']} |
"""
    
    content += """
## 状态流转用例检查

| 模块 | 状态数量 | 流转用例数 | 正常流转 | 异常流转 | 边界流转 |
|------|----------|------------|----------|----------|----------|
"""
    
    for module, check in transition_checks.items():
        normal_icon = '✅' if check['has_normal_transition'] else '❌'
        abnormal_icon = '✅' if check['has_abnormal_transition'] else '❌'
        boundary_icon = '✅' if check['has_boundary_transition'] else '❌'
        content += f"""| {module} | {check['total_states']} | {check['total_transition_cases']} | {normal_icon} | {abnormal_icon} | {boundary_icon} |
"""
    
    content += """
## 覆盖矩阵详情

| 序号 | 用例编号 | 类型 | 用例标题 | 优先级 | 场景类型 | 文档来源 | 当前状态 | 目标脚本 | 测试函数 | 说明 |
|------|----------|------|----------|--------|----------|----------|----------|----------|----------|------|
"""
    
    idx = 1
    for case_id, info in sorted_cases:
        status = '已实现' if info['implemented'] else '未实现'
        script_file = info.get('script_file', '')
        script_func = info.get('script_func', '')
        doc = info.get('document', '')
        scenario = info.get('scenario_type', '')
        
        if case_id.startswith('UNMAPPED'):
            doc = '未映射'
        
        content += f"""| {idx} | {case_id} | {info['type'].upper()} | {info['title']} | {info['priority']} | {scenario} | {doc} | {status} | `{script_file}` | {script_func} | {'' if info['implemented'] else '需要补充实现'} |
"""
        idx += 1
    
    content += """

## 未实现用例清单

| 序号 | 用例编号 | 类型 | 用例标题 | 优先级 | 场景类型 | 文档来源 |
|------|----------|------|----------|--------|----------|----------|
"""
    
    idx = 1
    for case_id, info in sorted(all_cases.items(), key=lambda x: (x[1]['priority'], x[0])):
        if not info['implemented'] and not case_id.startswith('UNMAPPED'):
            content += f"""| {idx} | {case_id} | {info['type'].upper()} | {info['title']} | {info['priority']} | {info.get('scenario_type', '')} | {info.get('document', '')} |
"""
            idx += 1
    
    if idx == 1:
        content += """| - | - | - | 所有用例均已实现 | - | - | - |
"""
    
    content += """

## 未映射脚本清单

| 序号 | 脚本文件 | 测试函数 | 类型 | 说明 |
|------|----------|----------|------|------|
"""
    
    idx = 1
    for case_id, info in sorted(all_cases.items(), key=lambda x: x[0]):
        if case_id.startswith('UNMAPPED'):
            content += f"""| {idx} | `{info['script_file']}` | {info['script_func']} | {info['type'].upper()} | 脚本未映射到用例文档中的用例编号 |
"""
            idx += 1
    
    if idx == 1:
        content += """| - | - | - | - | 所有脚本均已映射 |
"""
    
    content += """

## CRUD缺失用例详情

| 模块 | 缺失操作 | 建议补充用例 |
|------|----------|--------------|
"""
    
    has_crud_missing = False
    for module, check in sorted(crud_checks.items()):
        for op, status in check['status'].items():
            if not status:
                has_crud_missing = True
                op_name = {'create': '新增', 'read': '查询', 'update': '更新', 'delete': '删除'}[op]
                content += f"""| {module} | {op_name} | 建议补充{op_name}相关用例 |
"""
    
    if not has_crud_missing:
        content += """| - | - | 所有模块CRUD用例完整 |
"""
    
    content += """

## 状态流转缺失详情

| 模块 | 缺失类型 | 当前用例 | 建议补充 |
|------|----------|----------|----------|
"""
    
    has_transition_missing = False
    for module, check in transition_checks.items():
        if not check['has_normal_transition']:
            has_transition_missing = True
            content += f"""| {module} | 正常流转 | {check['total_transition_cases']} | 补充各状态之间的正常流转用例 |
"""
        if not check['has_abnormal_transition']:
            has_transition_missing = True
            content += f"""| {module} | 异常流转 | {check['total_transition_cases']} | 补充无效状态值、非法转换等异常用例 |
"""
        if not check['has_boundary_transition']:
            has_transition_missing = True
            content += f"""| {module} | 边界流转 | {check['total_transition_cases']} | 补充状态回退、跳级转换等边界用例 |
"""
    
    if not has_transition_missing:
        content += """| - | - | - | 所有模块状态流转用例完整 |
"""
    
    content += f"""

## 执行门禁

| 检查项 | 阈值 | 当前值 | 状态 |
|--------|------|--------|------|
| 未实现脚本数 | ≤ 0 | {not_implemented} | {'✅ 通过' if not_implemented == 0 else '❌ 未通过'} |
| P0用例实现率 | 100% | {p0_rate:.1f}% | {'✅ 通过' if p0_rate == 100 else '❌ 未通过'} |
| CRUD完整性 | 全部通过 | 检查中 | {'✅ 通过' if not has_crud_missing else '❌ 未通过'} |
| 状态流转完整性 | 全部通过 | 检查中 | {'✅ 通过' if not has_transition_missing else '❌ 未通过'} |

---

*本文件由 `scripts/scan-test-coverage.py` 自动生成，请勿手动修改。*
"""
    
    return content, {
        'total': total,
        'implemented': implemented,
        'not_implemented': not_implemented,
        'implementation_rate': implemented / total * 100 if total > 0 else 0,
        'p0_rate': p0_rate,
        'crud_complete': not has_crud_missing,
        'transition_complete': not has_transition_missing
    }


def main():
    base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    print("[SCAN] 扫描API测试脚本...")
    api_tests = scan_api_tests(base_path)
    print(f"[SCAN] 发现 {len(api_tests)} 个API测试函数")
    
    print("[SCAN] 扫描UI测试脚本...")
    ui_tests = scan_ui_tests(base_path)
    print(f"[SCAN] 发现 {len(ui_tests)} 个UI测试函数")
    
    print("[SCAN] 解析接口测试用例文档...")
    api_cases = parse_case_document(os.path.join(base_path, 'docs', 'cases', '接口测试用例-评审版.md'))
    print(f"[SCAN] 发现 {len(api_cases)} 条接口测试用例")
    
    print("[SCAN] 解析UI测试用例文档...")
    ui_cases = parse_case_document(os.path.join(base_path, 'docs', 'cases', 'UI测试用例-评审版.md'))
    print(f"[SCAN] 发现 {len(ui_cases)} 条UI测试用例")
    
    print("[SCAN] 解析功能测试用例文档...")
    func_cases = parse_case_document(os.path.join(base_path, 'docs', 'cases', '功能测试用例-评审版.md'))
    print(f"[SCAN] 发现 {len(func_cases)} 条功能测试用例")
    
    print("[ANALYZE] 分析覆盖情况...")
    all_cases = analyze_coverage(api_tests, ui_tests, api_cases, ui_cases, func_cases)
    
    print("[CHECK] 检查CRUD完整性...")
    crud_checks = check_crud_completeness(all_cases)
    
    print("[CHECK] 检查状态流转用例...")
    transition_checks = check_state_transition(all_cases)
    
    print("[GENERATE] 生成覆盖矩阵...")
    matrix_content, stats = generate_coverage_matrix(all_cases, crud_checks, transition_checks)
    
    output_path = os.path.join(base_path, 'docs', 'cases', '测试用例覆盖矩阵.md')
    with open(output_path, 'w', encoding='utf-8') as f:
        f.write(matrix_content)
    
    print(f"[DONE] 覆盖矩阵已生成: {output_path}")
    print(f"[STATS] 总用例: {stats['total']}, 已实现: {stats['implemented']}, 未实现: {stats['not_implemented']}")
    print(f"[STATS] 实现率: {stats['implementation_rate']:.1f}%, P0实现率: {stats['p0_rate']:.1f}%")
    print(f"[STATS] CRUD完整性: {'✅ 通过' if stats['crud_complete'] else '❌ 未通过'}")
    print(f"[STATS] 状态流转完整性: {'✅ 通过' if stats['transition_complete'] else '❌ 未通过'}")
    
    return stats


if __name__ == '__main__':
    main()