import os

def fix_encoding_to_bom(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    bom = b'\xef\xbb\xbf'
    with open(file_path, 'wb') as f:
        f.write(bom)
        f.write(content.encode('utf-8'))
    
    print(f"Fixed encoding for: {file_path}")

files = [
    r'd:\AICode\TestHub\AutoTest-Hub\scripts\run-full-test-flow.ps1',
    r'd:\AICode\TestHub\AutoTest-Hub\scripts\run-api-tests.ps1',
    r'd:\AICode\TestHub\AutoTest-Hub\scripts\lib\stage-common.ps1'
]

for file in files:
    if os.path.exists(file):
        fix_encoding_to_bom(file)