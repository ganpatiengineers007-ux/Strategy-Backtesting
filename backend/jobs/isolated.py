import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def child_env(cpu_seconds, mem_mb):
    """Sirf zaroori env (koi API key/token child ko nahi jaata)."""
    return {"PATH": os.environ.get("PATH", "/usr/bin:/bin"), "PYTHONPATH": str(ROOT), "LANG": "C.UTF-8",
            "SVL_CPU_SECONDS": str(cpu_seconds), "SVL_MEM_MB": str(mem_mb)}


def run_isolated(request, timeout=300, mem_mb=2048):
    p = subprocess.run([sys.executable, "-m", "backend.jobs.run_job"], input=json.dumps(request), capture_output=True,
                       text=True, timeout=timeout, cwd=str(ROOT), env=child_env(timeout, mem_mb))
    if p.returncode != 0:
        tail = (p.stderr.strip().splitlines() or ["no stderr"])[-1][:300]
        raise RuntimeError(f"isolated run failed (exit {p.returncode}): {tail}")
    return json.loads(p.stdout.strip().splitlines()[-1])
