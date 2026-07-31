import sys

def fix_ps1_encoding(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    bom = b'\xef\xbb\xbf'
    with open(file_path, 'wb') as f:
        f.write(bom)
        f.write(content.encode('utf-8'))
    
    print(f"Fixed encoding for: {file_path}")

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print("Usage: python fix-ps1-encoding.py <file_path>")
        sys.exit(1)
    fix_ps1_encoding(sys.argv[1])