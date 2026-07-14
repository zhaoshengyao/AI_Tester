import os
import glob

def fix_encoding(filepath):
    try:
        with open(filepath, 'rb') as f:
            content = f.read()
        
        has_bom = content.startswith(b'\xef\xbb\xbf')
        if not has_bom:
            with open(filepath, 'w', encoding='utf-8-sig') as f:
                f.write(content.decode('utf-8'))
            print(f"Fixed: {filepath}")
        else:
            print(f"Already has BOM: {filepath}")
    except Exception as e:
        print(f"Error fixing {filepath}: {e}")

if __name__ == '__main__':
    scripts_dir = os.path.dirname(os.path.abspath(__file__))
    ps1_files = glob.glob(os.path.join(scripts_dir, '*.ps1'))
    ps1_files += glob.glob(os.path.join(scripts_dir, 'lib', '*.ps1'))
    
    print("Fixing UTF-8 BOM encoding for PS1 files...")
    for ps1_file in ps1_files:
        fix_encoding(ps1_file)
    print("Done!")