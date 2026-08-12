p=r'scripts/lib/stage-common.ps1'
with open(p,'r',encoding='utf-8-sig') as f:
    lines=f.readlines()
# 找到 depth=0 后下一行导致 depth=负数的位置（第一个 mismatched }）
depth=0
last_depth_line=0
for i,line in enumerate(lines, start=1):
    s=line.strip()
    if s.startswith('#') or s == '':
        continue
    prev_depth = depth
    for c in s:
        if c == '{': depth += 1
        elif c == '}': depth -= 1
    if depth < 0:
        print(f'❌ FIRST MISMATCH L{i}: depth went {prev_depth} → {depth}; line={s[:150]!r}')
        # 打印上下文
        for j in range(max(1,i-3), min(len(lines), i+4)):
            print(f'  L{j}: {lines[j-1].rstrip()[:180]!r}')
        break
    if i <= 220:
        pass
# 继续找 depth 跳变
depth=0
for i,line in enumerate(lines, start=1):
    s=line.strip()
    if s.startswith('#') or s == '':
        continue
    # 粗略：检查 function/X 开头对应 depth 是否为 0
    if s.startswith('function ') and depth != 0:
        print(f'  ⚠️ L{i}: {s[:60]!r} starts with func but depth={depth}')
    for c in s:
        if c == '{': depth += 1
        elif c == '}': depth -= 1
print(f'Final depth={depth}')
