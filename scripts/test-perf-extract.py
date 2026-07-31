import re

file_path = r'd:\AICode\TestHub\AutoTest-Hub\docs\test-runs\20260715-113721\reports\性能测试报告.md'

with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()

print("=== Testing regex patterns ===")

patterns = [
    (r'运行时间[：:]\s*(\d+)', '运行时间：数字'),
    (r'运行时间.*?(\d+)', '运行时间.*?数字'),
    (r'并发用户数[：:]\s*(\d+)', '并发用户数：数字'),
    (r'压测框架[：:]\s*(\w+)', '压测框架：单词'),
]

for pattern, desc in patterns:
    match = re.search(pattern, content)
    if match:
        print(f"✓ {desc}: {match.group(1)}")
    else:
        print(f"✗ {desc}: No match")

print("\n=== Testing substring extraction ===")
index = content.find("运行时间")
if index >= 0:
    print(f"Found '运行时间' at index {index}")
    print(f"Text around: '{content[index:index+20]}'")
