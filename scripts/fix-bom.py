import os

def remove_bom(file_path):
    with open(file_path, 'rb') as f:
        content = f.read()
    
    bom = b'\xef\xbb\xbf'
    while content.startswith(bom):
        content = content[3:]
    
    with open(file_path, 'wb') as f:
        f.write(content)
    
    print(f"Fixed BOM for: {file_path}")

files = [
    r'd:\AICode\TestHub\AutoTest-Hub\scripts\run-api-tests.ps1',
    r'd:\AICode\TestHub\AutoTest-Hub\scripts\lib\stage-common.ps1',
    r'd:\AICode\TestHub\AutoTest-Hub\scripts\run-full-test-flow.ps1'
]

for file in files:
    if os.path.exists(file):
        remove_bom(file)