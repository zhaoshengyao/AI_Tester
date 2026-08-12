p=r'scripts/lib/stage-common.ps1'
with open(p,'r',encoding='utf-8-sig') as f:
    lines=f.readlines()
# 按 function 分段 & 计算每段 depth 结束
import re
func_re = re.compile(r'^function\s+([A-Za-z0-9\-_]+)\s*\{?', re.IGNORECASE)
depth=0
current_func = None
func_start = None
func_start_depth = None
for i,line in enumerate(lines, start=1):
    s=line
    m = func_re.match(s.strip())
    if m:
        if current_func:
            print(f'⚠️  previous func {current_func} never closed properly; start L{func_start}, end_d={depth-func_start_depth}')
        current_func = m.group(1)
        func_start = i
        func_start_depth = depth
        print(f'→ {current_func} 开始 L{i} (d={depth})')
    # 跳过字符串里的 { 和 }（粗略=把所有双引号/单引号内字符清空再统计）
    # 更粗糙：仅统计非注释行，字符串含 {} 忽略
    stripped = s.strip()
    if stripped.startswith('#'):
        continue
    in_sq=False; in_dq=False
    idx=0
    while idx < len(s):
        c=s[idx]
        if c=="'" and not in_dq:
            in_sq=not in_sq
            idx+=1; continue
        if c=='"' and not in_sq:
            in_dq=not in_dq
            idx+=1; continue
        if not in_sq and not in_dq:
            if c=='{': depth+=1
            elif c=='}': depth-=1
        idx+=1
    if current_func and depth == func_start_depth:
        # 可能结束
        print(f'  ↳ {current_func} 闭合于 L{i} (d={depth}); end content={stripped[:80]!r}')
        current_func = None
print(f'END: total depth={depth}')
