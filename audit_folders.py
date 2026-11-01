import os
from pathlib import Path

ROOT = Path(".")
CODE_EXTS = {".py", ".js", ".jsx", ".ts", ".tsx", ".html", ".css"}
SKIP_DIRS = {".git", "node_modules", "__pycache__", "venv", ".venv", ".env"}
SKIP_FILES = {"__init__.py"}

def count_code_lines(folder):
    total_lines = 0
    code_files = []
    for path in folder.rglob("*"):
        if path.is_dir():
            if path.name in SKIP_DIRS:
                continue
            continue
        if path.suffix not in CODE_EXTS:
            continue
        if path.name in SKIP_FILES:
            continue
        # skip if any parent dir is in SKIP_DIRS
        parts = path.parts
        if any(p in SKIP_DIRS for p in parts):
            continue
        try:
            text = path.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        lines = text.splitlines()
        nonblank = [l for l in lines if l.strip()]
        total_lines += len(nonblank)
        code_files.append(path)
    return total_lines, code_files

def status_for(lines):
    if lines == 0:
        return "KHALI FOLDER"
    if lines <= 5:
        return "STUB"
    return "OK"

results = []

for entry in sorted(ROOT.rglob("*")):
    if not entry.is_dir():
        continue
    parts = entry.parts
    if any(p in SKIP_DIRS for p in parts):
        continue
    lines, files = count_code_lines(entry)
    st = status_for(lines)
    results.append((str(entry), lines, st, files))

missing = [r for r in results if r[2] in ("STUB", "KHALI FOLDER")]

with open("audit_report.md", "w", encoding="utf-8") as f:
    f.write("# Folder Code Audit\n\n")
    f.write("| Folder | Code Lines | Status | Files |\n")
    f.write("|---|---|---|---|\n")
    for folder, lines, st, files in results:
        file_list = ", ".join(str(x) for x in files) if files else "-"
        f.write(f"| `{folder}` | {lines} | {st} | {file_list} |\n")
    f.write("\n## Folders Where Code Still Needs To Be Written\n\n")
    if missing:
        for folder, lines, st, files in missing:
            f.write(f"- `{folder}` — {st} ({lines} lines)\n")
    else:
        f.write("None\n")

print("Wrote audit_report.md")
print(f"Folders scanned: {len(results)}")
print(f"Missing/Stub folders: {len(missing)}")
