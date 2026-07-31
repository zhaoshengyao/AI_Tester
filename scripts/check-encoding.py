import sys

file_path = r'D:\AICode\TestHub\AutoTest-Hub\scripts\run-api-tests.ps1'

with open(file_path, 'rb') as f:
    content = f.read()
    
print(f"First 3 bytes: {content[:3]}")
print(f"Content length: {len(content)}")

try:
    text = content.decode('utf-8')
    print("UTF-8 decode successful")
except UnicodeDecodeError as e:
    print(f"UTF-8 decode failed: {e}")
    
try:
    text = content.decode('gbk')
    print("GBK decode successful")
except UnicodeDecodeError as e:
    print(f"GBK decode failed: {e}")
    
try:
    text = content.decode('utf-16')
    print("UTF-16 decode successful")
except UnicodeDecodeError as e:
    print(f"UTF-16 decode failed: {e}")
