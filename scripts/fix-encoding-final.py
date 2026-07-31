file_path = r'd:\AICode\TestHub\AutoTest-Hub\scripts\run-system-report.ps1'

with open(file_path, 'rb') as f:
    bytes_data = f.read()

bom = b'\xef\xbb\xbf'

while bytes_data.startswith(bom):
    bytes_data = bytes_data[3:]

with open(file_path, 'wb') as f:
    f.write(bom)
    f.write(bytes_data)

print(f"Fixed encoding. File size: {len(bytes_data) + 3}")

with open(file_path, 'rb') as f:
    new_bytes = f.read(10)
print(f"First 10 bytes now: {new_bytes.hex(' ')}")