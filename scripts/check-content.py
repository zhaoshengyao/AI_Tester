import sys

file_path = r'D:\AICode\TestHub\AutoTest-Hub\scripts\run-api-tests.ps1'

with open(file_path, 'r', encoding='utf-8') as f:
    lines = f.readlines()
    
for i, line in enumerate(lines[:30]):
    print(f"{i+1}: {repr(line)}")

# Check for garbled characters
import re
with open(file_path, 'r', encoding='utf-8') as f:
    content = f.read()
    
garbled_pattern = re.compile(r'[\u3000-\u303F\uFF00-\uFFFF]')
garbled_matches = garbled_pattern.findall(content)
if garbled_matches:
    print(f"\nFound garbled characters: {set(garbled_matches)[:20]}")
else:
    print("\nNo garbled characters found")
