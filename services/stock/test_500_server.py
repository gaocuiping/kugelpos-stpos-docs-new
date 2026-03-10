import subprocess
import time
import requests

proc = subprocess.Popen(['/home/gaocuiping/.local/bin/pipenv', 'run', 'python', '-m', 'uvicorn', 'app.main:app', '--port', '8016'], stderr=subprocess.PIPE, stdout=subprocess.PIPE, text=True)
time.sleep(3)

url = 'http://localhost:8016/api/v1/tenants/T9999/stores/5678/stock/snapshot/000000000000000000000000'
headers = {
    'Authorization': 'Bearer test',
    'X-Tenant-ID': 'T9999',
    'X-User-ID': 'admin'
}
try:
    resp = requests.get(url, headers=headers)
    print('STATUS:', resp.status_code)
except Exception as e:
    print('ERR:', e)

proc.terminate()
stdout, stderr = proc.communicate(timeout=2)
print('STDOUT:', stdout)
print('STDERR:', stderr)
