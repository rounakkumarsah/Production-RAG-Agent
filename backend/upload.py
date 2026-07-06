import urllib.request
import urllib.error
import mimetypes
import os

boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'
file_path = 'test_large.txt'
filename = os.path.basename(file_path)
mimetype = 'text/plain'

with open(file_path, 'rb') as f:
    file_data = f.read()

body = (
    b'--' + boundary.encode('utf-8') + b'\r\n'
    b'Content-Disposition: form-data; name="files"; filename="' + filename.encode('utf-8') + b'"\r\n'
    b'Content-Type: ' + mimetype.encode('utf-8') + b'\r\n\r\n' +
    file_data + b'\r\n'
    b'--' + boundary.encode('utf-8') + b'--\r\n'
)

req = urllib.request.Request('http://localhost:8000/upload', data=body, method='POST', headers={
    'Content-Type': f'multipart/form-data; boundary={boundary}',
    'Content-Length': str(len(body))
})

try:
    res = urllib.request.urlopen(req)
    print(res.read().decode())
except Exception as e:
    print(e)
