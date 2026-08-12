p=r'scripts/lib/stage-common.ps1'
with open(p,'r',encoding='utf-8-sig') as f:
    lines=f.readlines()
import re
func_re = re.compile(r'^function\s+([A-Za-z0-9\-_]+)\s*\{?', re.IGNORECASE)
depth=0
for i,line in enumerate(lines, start=1):
    s=line
    prev=depth
    stripped = s.strip()
    if stripped.startswith('#'):
        if i <= 210:
            print(f'd={depth:2d} D{i:3d}: {"#skip"}')
        continue
    in_sq=False; in_dq=False; in_hs=False  # 这里字符串
    idx=0
    while idx < len(s):
        c=s[idx]
        if c=="'":
            # PowerShell 双引号字符串内单引号不算
            if not in_dq:
                # PowerShell '' 转义：连跳
                if in_sq and idx+1 < len(s) and s[idx+1] == "'":
                    idx += 2
                    continue
                in_sq=not in_sq
            idx+=1; continue
        if c=='"':
            if not in_sq:
                # PowerShell "" 转义
                if in_dq and idx+1 < len(s) and s[idx+1] == '"':
                    idx += 2
                    continue
                in_dq=not in_dq
            idx+=1; continue
        if not in_sq and not in_dq:
            if c=='{': depth+=1
            elif c=='}': depth-=1
        idx+=1
    if i <= 210:
        print(f'd={prev:2d}→{depth:2d} L{i:3d}: {stripped[:100]!r}')
print(f'Final depth={depth}')
