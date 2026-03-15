import subprocess, sys, os
from datetime import datetime

log = r"C:\Users\juanj\documents\validationidea\logs\batch.log"
os.makedirs(os.path.dirname(log), exist_ok=True)

python = r"C:\Python314\python.exe"
script = r"C:\Users\juanj\documents\validationidea\run_batch.py"

with open(log, "a", encoding="utf-8-sig") as f:
    f.write(f"\n{'='*50}\n")
    f.write(f"INICIO: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    f.flush()
    result = subprocess.run([python, script], capture_output=True, text=True, encoding="utf-8-sig", errors="replace", cwd=os.path.dirname(script))
    f.write(result.stdout)
    f.write(result.stderr)
    f.write(f"FIN: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} | exit={result.returncode}\n")

print("Log escrito OK")

