#!/usr/bin/env python3
"""
inspect_external.py : repo ke root me padi bahari files (.py, .zip) ko kholkar jaanchta hai.

Default = sirf STATIC analysis (code chalaya nahi jaata). Report: external_report.md + external_report.json

  python3 inspect_external.py                 # static report
  python3 inspect_external.py --run-imports   # har file ka import smoke-test (code chalta hai! sandbox me)
  python3 inspect_external.py --run-tests     # lab tests + zip ke andar ke test_*.py (code chalta hai!)
  python3 inspect_external.py --root /path/to/repo

Jaanch: syntax, imports (missing libraries), classes/functions, strategy-jaisi classes (adapter candidates),
risky calls (eval/exec/subprocess/network/pickle), hardcoded SECRETS (public repo me leak ka khatra).
Risky ya secret wali file ko --run-imports me chalaya nahi jaata.
"""
import argparse
import ast
import hashlib
import importlib.util
import json
import re
import subprocess
import sys
import zipfile
from pathlib import Path

LAB_DIRS = {"backend", "backtest", "cli", "config", "contracts", "data", "docs", "engines", "frontend", "indicators",
            "metrics", "observability", "optimization", "persistence", "registry", "reporting", "risk", "scripts",
            "strategies", "tests", "validation", "infra", "artifacts", "output", "runs", "external", ".git", ".venv",
            ".github", "__pycache__", "node_modules"}
SKIP_ROOT_PY = ("bootstrap", "inspect_external")
STRAT_METHODS = {"on_bar", "generate_signals", "generate_signal", "on_data", "next", "signal", "run_strategy"}
RISKY_CALLS = {"eval", "exec", "compile", "__import__"}
RISKY_ATTRS = {"os.system", "os.popen", "subprocess.run", "subprocess.Popen", "subprocess.call", "subprocess.check_output",
               "pickle.loads", "pickle.load", "shutil.rmtree", "os.remove", "os.unlink"}
NET_MODULES = {"requests", "httpx", "urllib", "urllib3", "socket", "websocket", "websockets", "aiohttp", "ftplib",
               "smtplib", "paramiko", "kiteconnect", "fyers_apiv3", "dhanhq", "upstox_client", "ccxt"}
SECRET_RE = re.compile(r"""(?ix)(api[_-]?key|api[_-]?secret|secret|token|password|passwd|access[_-]?token|client[_-]?id|
                          client[_-]?secret|totp)\s*[=:]\s*["']([^"'\s]{12,})["']""")
TOKEN_RE = re.compile(r"(ghp_[A-Za-z0-9]{20,}|github_pat_[A-Za-z0-9_]{20,}|AKIA[0-9A-Z]{16}|sk-[A-Za-z0-9]{20,})")
MAX_ZIP_BYTES = 200 * 1024 * 1024


def mask(s):
    return s[:3] + "***" + s[-2:] if len(s) > 6 else "***"


def extract_zip(zp, dest):
    """Safe extract: path traversal + size limit."""
    dest.mkdir(parents=True, exist_ok=True)
    total, notes = 0, []
    with zipfile.ZipFile(zp) as z:
        for m in z.infolist():
            name = m.filename
            if name.startswith("/") or ".." in Path(name).parts:
                notes.append(f"SKIPPED unsafe path: {name}")
                continue
            total += m.file_size
            if total > MAX_ZIP_BYTES:
                notes.append("STOPPED: zip bahut bada (>200MB)")
                break
            z.extract(m, dest)
    return notes


def dotted(node):
    parts = []
    while isinstance(node, ast.Attribute):
        parts.append(node.attr)
        node = node.value
    if isinstance(node, ast.Name):
        parts.append(node.id)
    return ".".join(reversed(parts))


def analyze(path, local_names):
    text = path.read_text(encoding="utf-8", errors="replace")
    info = {"file": str(path), "lines": text.count("\n") + 1, "sha256": hashlib.sha256(text.encode()).hexdigest()[:12],
            "syntax_ok": True, "imports": [], "third_party": [], "missing": [], "classes": {}, "functions": [],
            "strategy_candidates": [], "risky": [], "secrets": [], "network": [], "has_main": False, "import_time_calls": 0}
    for i, line in enumerate(text.splitlines(), 1):
        for m in SECRET_RE.finditer(line):
            info["secrets"].append(f"line {i}: {m.group(1)}={mask(m.group(2))}")
        for m in TOKEN_RE.finditer(line):
            info["secrets"].append(f"line {i}: token-pattern {mask(m.group(1))}")
    try:
        tree = ast.parse(text)
    except SyntaxError as e:
        info["syntax_ok"] = False
        info["syntax_error"] = f"line {e.lineno}: {e.msg}"
        return info
    mods = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            mods.update(a.name.split(".")[0] for a in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module and node.level == 0:
            mods.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            name = dotted(node.func)
            if name in RISKY_CALLS or name in RISKY_ATTRS:
                info["risky"].append(f"line {node.lineno}: {name}()")
    info["imports"] = sorted(mods)
    stdlib = set(sys.stdlib_module_names)
    info["third_party"] = sorted(m for m in mods if m not in stdlib and m not in local_names)
    info["missing"] = [m for m in info["third_party"] if importlib.util.find_spec(m) is None]
    info["network"] = sorted(m for m in mods if m in NET_MODULES)
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            methods = [n.name for n in node.body if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))]
            info["classes"][node.name] = methods
            bases = [dotted(b) for b in node.bases]
            if STRAT_METHODS & set(methods) or any("Strategy" in b for b in bases) or "Strategy" in node.name:
                info["strategy_candidates"].append({"class": node.name, "bases": bases,
                                                    "methods": sorted(STRAT_METHODS & set(methods))})
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            info["functions"].append(node.name)
        elif isinstance(node, ast.If) and "__name__" in ast.dump(node.test):
            info["has_main"] = True
        elif isinstance(node, ast.Expr) and isinstance(node.value, ast.Call):
            info["import_time_calls"] += 1
        elif isinstance(node, (ast.For, ast.While)):
            info["import_time_calls"] += 1
    return info


def smoke_import(path, root, timeout=20):
    code = ("import importlib.util,sys;p=sys.argv[1];s=importlib.util.spec_from_file_location('ext_mod',p);"
            "m=importlib.util.module_from_spec(s);s.loader.exec_module(m);print('IMPORT_OK')")
    try:
        r = subprocess.run([sys.executable, "-c", code, str(path)], capture_output=True, text=True, timeout=timeout,
                           cwd=str(path.parent), env={"PATH": "/usr/bin:/bin", "PYTHONPATH": f"{path.parent}:{root}"})
        ok = r.returncode == 0 and "IMPORT_OK" in r.stdout
        return {"ok": ok, "detail": "" if ok else (r.stderr.strip().splitlines() or ["failed"])[-1][:200]}
    except subprocess.TimeoutExpired:
        return {"ok": False, "detail": f"TIMEOUT >{timeout}s (import par kuch chalta rehta hai)"}


def run_pytest(cwd, extra=()):
    r = subprocess.run([sys.executable, "-m", "pytest", "-q", *extra], capture_output=True, text=True, cwd=str(cwd))
    tail = (r.stdout.strip().splitlines() or r.stderr.strip().splitlines() or ["no output"])[-1]
    return {"exit": r.returncode, "summary": tail}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parent))
    ap.add_argument("--run-imports", action="store_true")
    ap.add_argument("--run-tests", action="store_true")
    a = ap.parse_args()
    root = Path(a.root)
    notes, targets = [], []
    for z in sorted(root.glob("*.zip")):
        dest = root / "external" / z.stem
        try:
            notes += [f"{z.name}: {n}" for n in extract_zip(z, dest)]
            targets += [p for p in sorted(dest.rglob("*.py")) if "__pycache__" not in p.parts]
            notes.append(f"{z.name}: extracted -> {dest.relative_to(root)}")
        except zipfile.BadZipFile:
            notes.append(f"{z.name}: BAD ZIP (corrupt/incomplete upload)")
    targets += [p for p in sorted(root.glob("*.py")) if not p.name.startswith(SKIP_ROOT_PY)]
    local = {p.stem for p in targets} | LAB_DIRS
    results = [analyze(p, local) for p in targets]
    for r in results:
        if a.run_imports:
            if r["secrets"] or r["risky"] or r["network"] or not r["syntax_ok"] or r["missing"]:
                r["smoke_import"] = {"ok": None, "detail": "SKIPPED (secret/risky/network/syntax/missing-lib)"}
            else:
                r["smoke_import"] = smoke_import(Path(r["file"]), root)
    lab = run_pytest(root) if a.run_tests else None

    # ---- console summary (mobile-friendly)
    print(f"Bahari files: {len(results)} | zips: {len(list(root.glob('*.zip')))}")
    for n in notes:
        print("  note:", n)
    for r in results:
        rel = Path(r["file"]).relative_to(root)
        flags = []
        if not r["syntax_ok"]:
            flags.append("SYNTAX-ERROR")
        if r["secrets"]:
            flags.append(f"SECRETS({len(r['secrets'])})")
        if r["risky"]:
            flags.append(f"RISKY({len(r['risky'])})")
        if r["network"]:
            flags.append("NET:" + ",".join(r["network"]))
        if r["missing"]:
            flags.append("MISSING-LIB:" + ",".join(r["missing"]))
        s = r.get("smoke_import")
        if s:
            flags.append("import=" + ("OK" if s["ok"] else "skip" if s["ok"] is None else "FAIL"))
        print(f"- {rel}  {r['lines']}L  cls={len(r['classes'])} fn={len(r['functions'])} "
              f"strategy={len(r['strategy_candidates'])}  {' '.join(flags) or 'clean'}")
    if lab:
        print("Lab tests:", lab["summary"])

    # ---- report files
    md = ["# External files report\n"]
    for n in notes:
        md.append(f"- {n}")
    for r in results:
        rel = Path(r["file"]).relative_to(root)
        md.append(f"\n## {rel}  ({r['lines']} lines, sha {r['sha256']})")
        if not r["syntax_ok"]:
            md.append(f"- SYNTAX ERROR: {r['syntax_error']}")
            continue
        md.append(f"- imports: {', '.join(r['imports']) or '-'}")
        if r["missing"]:
            md.append(f"- MISSING libraries: {', '.join(r['missing'])}  (pip install ...)")
        md.append(f"- classes: " + (", ".join(f"{k}({len(v)} methods)" for k, v in r["classes"].items()) or "-"))
        md.append(f"- functions: {', '.join(r['functions'][:25]) or '-'}")
        for c in r["strategy_candidates"]:
            md.append(f"- STRATEGY CANDIDATE: {c['class']} bases={c['bases']} methods={c['methods']}")
        if r["risky"]:
            md.append("- RISKY: " + "; ".join(r["risky"][:10]))
        if r["network"]:
            md.append("- NETWORK/BROKER libs: " + ", ".join(r["network"]))
        if r["secrets"]:
            md.append("- **SECRETS FOUND (public repo me ho to turant revoke/rotate karo):** " + "; ".join(r["secrets"][:10]))
        if r["import_time_calls"]:
            md.append(f"- import par {r['import_time_calls']} top-level statements chalte hain (side-effect ka khatra)")
        if r.get("smoke_import"):
            md.append(f"- import smoke test: {r['smoke_import']}")
    if lab:
        md.append(f"\n## Lab tests\n- {lab['summary']}")
    (root / "external_report.md").write_text("\n".join(md) + "\n", encoding="utf-8")
    (root / "external_report.json").write_text(json.dumps({"notes": notes, "files": results, "lab_tests": lab}, indent=2), encoding="utf-8")
    print("\nReport: external_report.md  (aur external_report.json)")
    bad = [r for r in results if r["secrets"]]
    if bad:
        print("WARNING: secrets mile. Repo public hai to wo keys leak ho chuki maani jayein: broker/GitHub me jaakar revoke karo.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
