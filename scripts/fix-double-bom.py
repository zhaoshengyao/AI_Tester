file_path = r'd:\AICode\TestHub\AutoTest-Hub\scripts\run-system-report.ps1'

with open(file_path, 'rb') as f:
    bytes_data = f.read()

bom = b'\xef\xbb\xbf'
if bytes_data.startswith(bom * 2):
    bytes_data = bytes_data[3:]
elif bytes_data.startswith(bom):
    bytes_data = bytes_data[3:]

with open(file_path, 'wb') as f:
    f.write(bom)
    f.write(bytes_data)

print("Fixed double BOM")