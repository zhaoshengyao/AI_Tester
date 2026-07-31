file_path = r'd:\AICode\TestHub\AutoTest-Hub\scripts\run-system-report.ps1'

with open(file_path, 'rb') as f:
    bytes_data = f.read(10)

print(f"First 10 bytes: {bytes_data.hex(' ')}")
print(f"Has BOM: {bytes_data[:3] == b'\xef\xbb\xbf'}")

if bytes_data[:6] == b'\xef\xbb\xbf\xef\xbb\xbf':
    print("Has double BOM!")
