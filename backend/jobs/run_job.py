"""Alag process me chalne wala entry. Pehle resource limits, phir hi koi strategy code import hota hai.
Sandbox nahi: sirf CPU/memory/time limit + saaf env. Network/filesystem isolation ke liye container/OS user chahiye."""
import json
import os
import sys


def _apply_limits():
    try:
        import resource
    except ImportError:  # non-posix
        return
    cpu = int(os.environ.get("SVL_CPU_SECONDS", "0"))
    mem = int(os.environ.get("SVL_MEM_MB", "0"))
    if cpu:
        resource.setrlimit(resource.RLIMIT_CPU, (cpu, cpu))
    if mem:
        resource.setrlimit(resource.RLIMIT_AS, (mem * 1024 * 1024, mem * 1024 * 1024))


def main():
    _apply_limits()
    req = json.load(sys.stdin)
    from backend.services.backtest_service import run_full
    record, paths = run_full(req["strategy_id"], req["data_path"], req.get("params"), req.get("config"),
                             out_root=req["out_root"], symbol=req.get("symbol", "UNKNOWN"),
                             timeframe=req.get("timeframe", "UNKNOWN"), validation_opts=req.get("validation_opts"))
    print(json.dumps({"record": record, "paths": paths}, default=str))


if __name__ == "__main__":
    main()
