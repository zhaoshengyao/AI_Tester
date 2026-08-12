p=r'scripts/lib/stage-common.ps1'
with open(p,'r',encoding='utf-8-sig') as f:
    lines=f.readlines()
for i,line in enumerate(lines, start=1):
    bad=[]
    for j,c in enumerate(line):
        o=ord(c)
        if (o < 32 and c not in '\r\n\t') or o == 0x2028 or o == 0x2029 or o == 0xFEFF:
            bad.append((j, hex(o)))
    if bad:
        print(f'L{i}: ctrl chars {bad}; len={len(line)}; content={line[:150]!r}')
# 额外统计：L1~L210 语法结构
depth=0
for i,line in enumerate(lines, start=1):
    s=line.strip()
    if s.startswith('#') or s == '':
        continue
    # 只看字符
    for c in s:
        if c == '{': depth += 1
        elif c == '}': depth -= 1
    if i <= 210 and i % 50 == 0:
        print(f'L{i}: depth={depth}')
print(f'END L{len(lines)}: final depth={depth}')
