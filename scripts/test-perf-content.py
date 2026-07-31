file_path = r'd:\AICode\TestHub\AutoTest-Hub\docs\test-runs\20260715-113721\reports\性能测试报告.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("=== Content structure ===")
lines = content.split('\n')
for i, line in enumerate(lines[:50]):
    print(f"{i:3d}: [{repr(line)}]")

print("\n=== Looking for 运行时间 ===")
for i, line in enumerate(lines):
    if '运行时间' in line:
        print(f"Found at line {i}: [{repr(line)}]")
        print(f"  Strip: [{repr(line.strip())}]")
