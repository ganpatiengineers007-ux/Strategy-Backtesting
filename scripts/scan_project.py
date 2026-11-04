#!/usr/bin/env python3
"""
FILE   : scan_project.py
STATUS : COMPLETE (पूरी फाइल, कोई placeholder नहीं)
PATH   : ~/Strategy-Backtesting/scan_project.py   (repo की root में रखो)

काम: पूरे प्रोजेक्ट का कोड स्कैन करके प्रॉब्लम निकालना और रिपोर्ट बनाना।
सिर्फ़ पढ़ती है, कोई फाइल बदलती या डिलीट नहीं करती (सिर्फ़ scan_report.txt लिखती है)।

क्या-क्या जाँचती है:
  1. Python syntax error                       (ERROR)
  2. ऐसे import जो मिल नहीं रहे                  (ERROR)
  3. undefined name (अगर pyflakes लगा हो)         (ERROR)
  4. असली secrets (GitHub token, AWS key आदि)    (ERROR)
  5. खराब JSON / TOML फाइलें                     (ERROR)
  6. stub फंक्शन: सिर्फ pass / ... / NotImplementedError  (WARN)
  7. "add logic here", placeholder जैसे शब्द       (WARN)
  8. खाली फाइलें, bare except, चुपचाप दबाए error,
     mutable default argument, eval/exec           (WARN)
  9. Go: go vet और gofmt (अगर go लगा हो)           (WARN / INFO)
 10. TODO / FIXME                                (INFO)
 11. --tests देने पर pytest भी चलाती है            (ERROR अगर फेल)
 12. (नया) हर .zip फाइल को खोलकर उसके अंदर का सारा कोड भी
     यही सब जाँचों से स्कैन करती है। zip एक अस्थायी फोल्डर में खुलती है
     (प्रोजेक्ट में कुछ नहीं जुड़ता) और स्कैन के बाद वह फोल्डर मिटा दिया जाता है।
     रिपोर्ट में हर लाइन के आगे [zip नाम] लिखा आता है।
 13. (नया) --zip-tests देने पर zip के अंदर के टेस्ट भी चलाती है, यानी
     "यह असल में चलेगा या नहीं" की जाँच। ध्यान दो: इसमें zip का कोड चलता है।

चलाने का तरीका (venv चालू करके, repo की root से):
    python scan_project.py
    python scan_project.py --tests        # साथ में pytest भी
    python scan_project.py --zip-tests    # zip के अंदर के टेस्ट भी चलाओ
    python scan_project.py --no-zip       # zip फाइलें न खोलो
    python scan_project.py --skip all_strategies   # इस फोल्डर को छोड़ दो
    python scan_project.py --all          # स्क्रीन पर सब कुछ दिखाओ
    python scan_project.py --no-go        # Go की जाँच छोड़ो
    python scan_project.py --root /path   # किसी और फोल्डर को स्कैन करो

secrets (token/key) मिलने पर भी रिपोर्ट में सिर्फ़ शुरू के 4 अक्षर दिखते हैं,
पूरा token कभी स्क्रीन या फाइल में नहीं छपता।

रिपोर्ट: scan_report.txt (पूरी), स्क्रीन पर सिर्फ़ सार।
Exit code: कोई ERROR मिला तो 1, वरना 0।
"""

import argparse
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import zipfile
from collections import Counter, defaultdict
from pathlib import Path

SKIP_DIRS = {
    ".git", ".venv", "venv", "env", "node_modules", "__pycache__",
    ".pytest_cache", ".mypy_cache", ".ruff_cache", "vendor", "dist",
    "build", ".idea", ".vscode", "site-packages",
}
SELF_NAMES = {"scan_project.py", "scan_report.txt"}
MAX_TEXT_BYTES = 2_000_000
MAX_ZIP_MEMBERS = 20000
MAX_ZIP_BYTES = 300_000_000

SEV_ORDER = {"ERROR": 0, "WARN": 1, "INFO": 2}

PLACEHOLDER_RE = re.compile(
    r"(add (your )?(logic|code) here|your code here|implement (me|this|later)"
    r"|to be implemented|\bplaceholder\b|\bstubs?\b|rest of (the )?code)",
    re.IGNORECASE,
)
GO_PANIC_RE = re.compile(
    r'panic\(\s*"[^"]*(not implemented|unimplemented|todo)', re.IGNORECASE
)
TODO_RE = re.compile(r"\b(TODO|FIXME|XXX|HACK)\b")

SECRET_PATTERNS = [
    ("ERROR", "GitHub token", re.compile(r"\bgh[pousr]_[A-Za-z0-9]{36,}\b")),
    ("ERROR", "GitHub fine-grained token",
     re.compile(r"\bgithub_pat_[A-Za-z0-9_]{50,}\b")),
    ("ERROR", "AWS access key", re.compile(r"\bAKIA[0-9A-Z]{16}\b")),
    ("ERROR", "private key block",
     re.compile(r"-----BEGIN (RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----")),
    ("WARN", "hard-coded secret जैसा मान", re.compile(
        r"(?i)\b(api[_-]?key|secret|token|passwd|password)\b\s*[=:]\s*"
        r"['\"][A-Za-z0-9_\-./+=]{16,}['\"]")),
]

CODE_EXTS = {".py", ".go", ".proto", ".sh", ".js", ".ts"}
SECRET_EXTS = CODE_EXTS | {
    ".json", ".yaml", ".yml", ".toml", ".env", ".cfg", ".ini", ".txt", ".md",
}


class Report:
    def __init__(self):
        self.items = []  # (sev, category, path, line, message)
        self.prefix = ""  # zip के अंदर स्कैन करते समय "[zip नाम] " रहता है

    def add(self, sev, category, path, line, message):
        self.items.append((sev, category, f"{self.prefix}{path}", line, message))

    def count(self, sev):
        return sum(1 for i in self.items if i[0] == sev)


EXTRA_SKIP = []  # --skip से दिए फोल्डर (root के सापेक्ष), main() में भरता है


def walk_files(root):
    for path in sorted(root.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root)
        rel_parts = rel.parts
        if any(p in SKIP_DIRS for p in rel_parts[:-1]):
            continue
        rel_posix = rel.as_posix()
        if any(rel_posix == s or rel_posix.startswith(s + "/") for s in EXTRA_SKIP):
            continue
        if path.name in SELF_NAMES:
            continue
        yield path


def read_text(path):
    try:
        if path.stat().st_size > MAX_TEXT_BYTES:
            return None
        return path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return None


def mask(s):
    return s[:4] + "..." + "(छुपाया)"


# ---------------------------------------------------------------- Python

def stub_reason(body):
    stmts = list(body)
    had_doc = False
    if (stmts and isinstance(stmts[0], ast.Expr)
            and isinstance(stmts[0].value, ast.Constant)
            and isinstance(stmts[0].value.value, str)):
        stmts = stmts[1:]
        had_doc = True
    if not stmts:
        return "सिर्फ़ docstring है, कोड नहीं" if had_doc else "खाली body"
    if all(isinstance(s, ast.Pass) or (
            isinstance(s, ast.Expr) and isinstance(s.value, ast.Constant)
            and s.value.value is Ellipsis) for s in stmts):
        return "सिर्फ़ pass / ... है"
    if len(stmts) == 1 and isinstance(stmts[0], ast.Raise):
        exc = stmts[0].exc
        name = None
        if isinstance(exc, ast.Call) and isinstance(exc.func, ast.Name):
            name = exc.func.id
        elif isinstance(exc, ast.Name):
            name = exc.id
        if name == "NotImplementedError":
            return "सिर्फ़ NotImplementedError उठाता है"
    return None


def decorator_text(node):
    out = []
    for d in node.decorator_list:
        try:
            out.append(ast.unparse(d))
        except Exception:
            pass
    return " ".join(out)


def base_text(cls):
    out = []
    for b in cls.bases:
        try:
            out.append(ast.unparse(b))
        except Exception:
            pass
    return " ".join(out)


def check_functions(tree, rel, rep):
    def visit(node, cls_stack):
        for child in ast.iter_child_nodes(node):
            if isinstance(child, ast.ClassDef):
                visit(child, cls_stack + [child])
            elif isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                deco = decorator_text(child)
                in_abstract = any(
                    "Protocol" in base_text(c) or "ABC" in base_text(c)
                    for c in cls_stack)
                skip = ("abstractmethod" in deco or "overload" in deco
                        or in_abstract)
                if not skip:
                    why = stub_reason(child.body)
                    if why:
                        rep.add("WARN", "STUB", rel, child.lineno,
                                f"फंक्शन `{child.name}`: {why}")
                for d in list(child.args.defaults) + [
                        x for x in child.args.kw_defaults if x is not None]:
                    if isinstance(d, (ast.List, ast.Dict, ast.Set)):
                        rep.add("WARN", "MUTABLE-DEFAULT", rel, child.lineno,
                                f"फंक्शन `{child.name}` में mutable default argument")
                visit(child, cls_stack)
            else:
                visit(child, cls_stack)

    visit(tree, [])


def check_misc_python(tree, rel, rep):
    for node in ast.walk(tree):
        if isinstance(node, ast.ExceptHandler):
            if node.type is None:
                rep.add("WARN", "BARE-EXCEPT", rel, node.lineno,
                        "bare `except:`: हर error निगल लेता है")
            if all(isinstance(s, ast.Pass) for s in node.body):
                rep.add("WARN", "SWALLOWED-ERROR", rel, node.lineno,
                        "except के अंदर सिर्फ़ pass: error चुपचाप दब रहा है")
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name) and node.func.id in ("eval", "exec"):
                rep.add("WARN", "EVAL-EXEC", rel, node.lineno,
                        f"`{node.func.id}()` का इस्तेमाल: जोखिम भरा")


def import_skip_ids(tree):
    skip = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Try):
            catches = False
            for h in node.handlers:
                if h.type is None:
                    catches = True
                else:
                    try:
                        txt = ast.unparse(h.type)
                    except Exception:
                        txt = ""
                    if any(n in txt for n in
                           ("ImportError", "ModuleNotFoundError", "Exception")):
                        catches = True
            if catches:
                for stmt in node.body:
                    for sub in ast.walk(stmt):
                        skip.add(id(sub))
        if isinstance(node, ast.If):
            try:
                cond = ast.unparse(node.test)
            except Exception:
                cond = ""
            if "TYPE_CHECKING" in cond:
                for stmt in node.body:
                    for sub in ast.walk(stmt):
                        skip.add(id(sub))
    return skip


def module_exists_locally(base, parts):
    p = base.joinpath(*parts)
    return (Path(str(p) + ".py").is_file() or (p / "__init__.py").is_file()
            or p.is_dir())


def check_imports(tree, path, root, rel, rep):
    skip = import_skip_ids(tree)
    stdlib = getattr(sys, "stdlib_module_names", set())
    # pytest/python फाइल के ऊपर वाले हर फोल्डर को रास्ते में मान सकते हैं
    # (जैसे tests/ के ऊपर वाला फोल्डर), इसलिए सब जोड़ते हैं
    search_bases = [root, root / "src"]
    for parent in [path.parent, *path.parent.parents]:
        if parent == root or root in parent.parents:
            search_bases.append(parent)
    for node in ast.walk(tree):
        if id(node) in skip:
            continue
        if isinstance(node, ast.Import):
            for alias in node.names:
                parts = alias.name.split(".")
                check_absolute(parts, search_bases, stdlib, node, rel, rep)
        elif isinstance(node, ast.ImportFrom):
            if node.level and node.level > 0:
                base = path.parent
                for _ in range(node.level - 1):
                    base = base.parent
                if node.module:
                    parts = node.module.split(".")
                    if not module_exists_locally(base, parts):
                        rep.add("ERROR", "IMPORT", rel, node.lineno,
                                f"relative import नहीं मिला: "
                                f"{'.' * node.level}{node.module}")
            elif node.module:
                parts = node.module.split(".")
                check_absolute(parts, search_bases, stdlib, node, rel, rep)


def check_absolute(parts, bases, stdlib, node, rel, rep):
    top = parts[0]
    if top in stdlib or top == "__future__":
        return
    for b in bases:
        if (Path(str(b / top) + ".py").is_file() or (b / top).is_dir()):
            if not any(module_exists_locally(bb, parts) for bb in bases):
                rep.add("ERROR", "IMPORT", rel, node.lineno,
                        f"लोकल मॉड्यूल का अंदरूनी हिस्सा नहीं मिला: {'.'.join(parts)}")
            return
    try:
        spec = importlib.util.find_spec(top)
    except (ImportError, ValueError, AttributeError):
        spec = None
    if spec is None:
        rep.add("ERROR", "IMPORT", rel, node.lineno,
                f"`{top}` न इंस्टॉल है न प्रोजेक्ट में है (import {'.'.join(parts)})")


def scan_python(path, root, rep):
    rel = path.relative_to(root)
    text = read_text(path)
    if text is None:
        rep.add("WARN", "READ", rel, 0, "फाइल पढ़ी नहीं जा सकी (binary/बहुत बड़ी)")
        return
    if not text.strip() and path.name != "__init__.py":
        rep.add("WARN", "EMPTY-FILE", rel, 0, "फाइल खाली है")
        return
    try:
        tree = ast.parse(text, filename=str(path))
    except SyntaxError as e:
        rep.add("ERROR", "SYNTAX", rel, e.lineno or 0, f"syntax error: {e.msg}")
        return
    check_functions(tree, rel, rep)
    check_misc_python(tree, rel, rep)
    check_imports(tree, path, root, rel, rep)


# ---------------------------------------------------------- सभी टेक्स्ट फाइलें

def scan_text_lines(path, root, rep):
    rel = path.relative_to(root)
    ext = path.suffix.lower()
    text = read_text(path)
    if text is None:
        return
    is_code = ext in CODE_EXTS
    for no, line in enumerate(text.splitlines(), 1):
        if ext in SECRET_EXTS or path.name.startswith(".env"):
            for sev, label, rx in SECRET_PATTERNS:
                m = rx.search(line)
                if m:
                    rep.add(sev, "SECRET", rel, no, f"{label} मिला: {mask(m.group(0))}")
        if is_code:
            if PLACEHOLDER_RE.search(line):
                rep.add("WARN", "PLACEHOLDER", rel, no,
                        "placeholder/stub जैसा शब्द: " + line.strip()[:70])
            if ext == ".go" and GO_PANIC_RE.search(line):
                rep.add("WARN", "STUB", rel, no,
                        "Go: panic(\"not implemented\") जैसा stub")
            if TODO_RE.search(line):
                rep.add("INFO", "TODO", rel, no, line.strip()[:70])


def scan_data_files(path, root, rep):
    rel = path.relative_to(root)
    ext = path.suffix.lower()
    if ext not in (".json", ".toml"):
        return
    text = read_text(path)
    if text is None:
        return
    try:
        if ext == ".json":
            json.loads(text)
        else:
            import tomllib
            tomllib.loads(text)
    except Exception as e:
        rep.add("ERROR", "BAD-DATA", rel, 0, f"{ext} फाइल खराब है: {str(e)[:80]}")


# --------------------------------------------------------------- pyflakes

def run_pyflakes(files, root, rep):
    if importlib.util.find_spec("pyflakes") is None:
        rep.add("INFO", "TOOL", "-", 0,
                "pyflakes नहीं लगा: undefined-name जाँच छूटी। "
                "लगाने के लिए: pip install pyflakes")
        return
    for i in range(0, len(files), 150):
        chunk = [str(f) for f in files[i:i + 150]]
        proc = subprocess.run(
            [sys.executable, "-m", "pyflakes", *chunk],
            capture_output=True, text=True, cwd=root)
        for line in proc.stdout.splitlines():
            if "undefined name '" in line:
                parts = line.split(":", 3)
                if len(parts) == 4:
                    try:
                        rel = Path(parts[0]).relative_to(root)
                    except ValueError:
                        rel = parts[0]
                    rep.add("ERROR", "UNDEFINED-NAME", rel,
                            int(parts[1]) if parts[1].isdigit() else 0,
                            parts[3].strip())


# ---------------------------------------------------------------------- Go

def run_go(root, rep):
    go = shutil.which("go")
    mods = [p for p in walk_files(root) if p.name == "go.mod"]
    if not mods:
        return
    if not go:
        rep.add("INFO", "TOOL", "-", 0, "go.mod मिली पर `go` लगा नहीं: Go की जाँच छूटी")
        return
    for mod in mods:
        d = mod.parent
        reld = d.relative_to(root)
        try:
            vet = subprocess.run([go, "vet", "./..."], cwd=d,
                                 capture_output=True, text=True, timeout=600)
        except subprocess.TimeoutExpired:
            rep.add("WARN", "GO-VET", reld, 0, "go vet 10 मिनट में पूरा नहीं हुआ")
            continue
        if vet.returncode != 0:
            lines = [l for l in vet.stderr.splitlines()
                     if l.strip() and not l.startswith("#")]
            for l in lines[:50]:
                rep.add("WARN", "GO-VET", reld, 0, l.strip()[:160])
            if not lines:
                rep.add("WARN", "GO-VET", reld, 0, "go vet फेल हुआ (कोई संदेश नहीं)")
        gofmt = shutil.which("gofmt")
        if gofmt:
            out = subprocess.run([gofmt, "-l", "."], cwd=d,
                                 capture_output=True, text=True)
            for l in out.stdout.splitlines():
                rep.add("INFO", "GO-FMT", reld, 0, f"gofmt चाहिए: {l}")


# ------------------------------------------------------------------ pytest

def run_pytest(root, rep):
    proc = subprocess.run([sys.executable, "-m", "pytest", "-q"], cwd=root,
                          capture_output=True, text=True)
    tail = [l for l in proc.stdout.splitlines() if l.strip()][-1:] or ["(कोई आउटपुट नहीं)"]
    if proc.returncode != 0:
        for l in proc.stdout.splitlines():
            if l.startswith("FAILED") or l.startswith("ERROR"):
                rep.add("ERROR", "PYTEST", "-", 0, l[:160])
        rep.add("ERROR", "PYTEST", "-", 0, "pytest फेल: " + tail[0])
    else:
        rep.add("INFO", "PYTEST", "-", 0, "pytest पास: " + tail[0])


# --------------------------------------------------------------------- zip

def extract_zip_safely(zpath, dest, rep):
    """zip को dest में खोलती है। खतरनाक path (../ या absolute) छोड़ देती है।
    सफल हो तो True, वरना False।"""
    dest_resolved = dest.resolve()
    try:
        with zipfile.ZipFile(zpath) as zf:
            infos = zf.infolist()
            total = sum(i.file_size for i in infos)
            if len(infos) > MAX_ZIP_MEMBERS or total > MAX_ZIP_BYTES:
                rep.add("WARN", "ZIP", "-", 0,
                        f"zip बहुत बड़ी ({len(infos)} फाइलें, {total // 1_000_000} MB): छोड़ दी")
                return False
            for info in infos:
                target = (dest / info.filename).resolve()
                if target != dest_resolved and not str(target).startswith(
                        str(dest_resolved) + os.sep):
                    rep.add("ERROR", "ZIP-UNSAFE", info.filename, 0,
                            "zip के अंदर खतरनाक path (बाहर लिखने की कोशिश): छोड़ा गया")
                    continue
                if info.is_dir():
                    target.mkdir(parents=True, exist_ok=True)
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as src, open(target, "wb") as dst:
                    shutil.copyfileobj(src, dst)
    except zipfile.BadZipFile:
        rep.add("ERROR", "ZIP", "-", 0, "zip खराब है या खुल नहीं रही")
        return False
    except (OSError, RuntimeError) as e:
        rep.add("ERROR", "ZIP", "-", 0, f"zip खोलने में दिक्कत: {str(e)[:80]}")
        return False
    return True


def run_zip_tests(tmp, rep):
    has_tests = any(tmp.rglob("test_*.py")) or any(tmp.rglob("*_test.py"))
    if not has_tests:
        rep.add("INFO", "ZIP-TESTS", "-", 0, "zip में कोई टेस्ट फाइल नहीं मिली")
        return
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1")
    try:
        proc = subprocess.run([sys.executable, "-m", "pytest", "-q", "-p",
                               "no:cacheprovider"], cwd=tmp, env=env,
                              capture_output=True, text=True, timeout=300)
    except subprocess.TimeoutExpired:
        rep.add("WARN", "ZIP-TESTS", "-", 0, "zip के टेस्ट 5 मिनट में पूरे नहीं हुए")
        return
    out_lines = [l for l in proc.stdout.splitlines() if l.strip()]
    tail = out_lines[-1] if out_lines else "(कोई आउटपुट नहीं)"
    if proc.returncode == 0:
        rep.add("INFO", "ZIP-TESTS", "-", 0, "zip के टेस्ट पास: " + tail)
    else:
        for l in out_lines:
            if l.startswith("FAILED") or l.startswith("ERROR"):
                rep.add("WARN", "ZIP-TESTS", "-", 0, l[:160])
        rep.add("WARN", "ZIP-TESTS", "-", 0,
                "zip के टेस्ट फेल (कमी या तो कोड में है या dependency में): " + tail)


def scan_zip(zpath, root, rep, no_go, zip_tests):
    name = str(zpath.relative_to(root))
    old_prefix = rep.prefix
    rep.prefix = f"[zip {name}] "
    tmp = Path(tempfile.mkdtemp(prefix="scanzip_"))
    count = 0
    try:
        if extract_zip_safely(zpath, tmp, rep):
            nested = [p for p in tmp.rglob("*.zip")]
            for n in nested:
                rep.add("INFO", "ZIP", n.relative_to(tmp), 0,
                        "zip के अंदर और zip है: उसे नहीं खोला")
            files = scan_directory(tmp, rep, no_go, False)
            count = len(files)
            if zip_tests:
                run_zip_tests(tmp, rep)
            rep.add("INFO", "ZIP", "-", 0, f"इस zip की {count} फाइलें स्कैन हुईं")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
        rep.prefix = old_prefix
    return count


# ------------------------------------------------------------------ रिपोर्ट

def fmt_item(it):
    sev, cat, path, line, msg = it
    loc = f"{path}:{line}" if line else f"{path}"
    return f"[{sev}] {cat:<16} {loc}  {msg}"


def write_report(rep, root, files_scanned):
    items = sorted(rep.items, key=lambda i: (SEV_ORDER[i[0]], i[1], i[2], i[3]))
    out = root / "scan_report.txt"
    with out.open("w", encoding="utf-8") as f:
        f.write(f"स्कैन की गई फाइलें: {files_scanned}\n")
        f.write(f"ERROR: {rep.count('ERROR')}  WARN: {rep.count('WARN')}  "
                f"INFO: {rep.count('INFO')}\n\n")
        for it in items:
            f.write(fmt_item(it) + "\n")
    return out, items


def print_summary(rep, items, report_path, show_all, files_scanned):
    print("=" * 60)
    print(f"स्कैन की गई फाइलें : {files_scanned}")
    print(f"ERROR : {rep.count('ERROR')}   WARN : {rep.count('WARN')}   "
          f"INFO : {rep.count('INFO')}")
    print("=" * 60)
    by_cat = defaultdict(Counter)
    for sev, cat, *_ in items:
        by_cat[sev][cat] += 1
    for sev in ("ERROR", "WARN", "INFO"):
        if by_cat[sev]:
            print(f"\n{sev} किस्में:")
            for cat, n in by_cat[sev].most_common():
                print(f"  {cat:<18} {n}")
    limit = None if show_all else 40
    errs = [i for i in items if i[0] == "ERROR"]
    if errs:
        print(f"\n--- ERROR (पहले {len(errs) if show_all else min(40, len(errs))}) ---")
        for it in errs[:limit]:
            print(fmt_item(it))
    if show_all:
        rest = [i for i in items if i[0] != "ERROR"]
        for it in rest:
            print(fmt_item(it))
    print(f"\nपूरी रिपोर्ट: {report_path}")
    if rep.count("ERROR") == 0:
        print("नतीजा: कोई ERROR नहीं मिला।")
    else:
        print("नतीजा: ERROR मिले हैं, पहले उन्हें ठीक करो।")


def scan_directory(root, rep, no_go, run_tests):
    """एक फोल्डर की सारी फाइलें स्कैन करती है। स्कैन की गई फाइलों की सूची लौटाती है।"""
    files = list(walk_files(root))
    py_files = []
    for path in files:
        ext = path.suffix.lower()
        if ext == ".py":
            py_files.append(path)
            scan_python(path, root, rep)
        scan_text_lines(path, root, rep)
        scan_data_files(path, root, rep)

    run_pyflakes(py_files, root, rep)
    if not no_go:
        run_go(root, rep)
    if run_tests:
        run_pytest(root, rep)
    return files


def main():
    ap = argparse.ArgumentParser(description="प्रोजेक्ट कोड स्कैनर")
    ap.add_argument("--root", default=".", help="स्कैन करने का फोल्डर")
    ap.add_argument("--tests", action="store_true", help="pytest भी चलाओ")
    ap.add_argument("--zip-tests", action="store_true",
                    help="zip के अंदर के टेस्ट भी चलाओ (zip का कोड चलता है)")
    ap.add_argument("--no-zip", action="store_true", help="zip फाइलें न खोलो")
    ap.add_argument("--skip", action="append", default=[], metavar="FOLDER",
                    help="इस फोल्डर को स्कैन से बाहर रखो (कई बार दे सकते हो), "
                         "जैसे --skip all_strategies")
    ap.add_argument("--no-go", action="store_true", help="Go जाँच छोड़ो")
    ap.add_argument("--all", action="store_true", help="स्क्रीन पर सब दिखाओ")
    args = ap.parse_args()

    root = Path(args.root).resolve()
    if not root.is_dir():
        print(f"फोल्डर नहीं मिला: {root}")
        return 2

    EXTRA_SKIP[:] = [s.strip().strip("/") for s in args.skip if s.strip().strip("/")]

    rep = Report()
    for s in EXTRA_SKIP:
        rep.add("INFO", "SKIP", s, 0, "यह फोल्डर --skip से स्कैन के बाहर रखा गया")
    files = scan_directory(root, rep, args.no_go, args.tests)
    total_files = len(files)

    if not args.no_zip:
        zips = [p for p in files if p.suffix.lower() == ".zip"]
        for z in zips:
            total_files += scan_zip(z, root, rep, args.no_go, args.zip_tests)

    report_path, items = write_report(rep, root, total_files)
    print_summary(rep, items, report_path, args.all, total_files)
    return 1 if rep.count("ERROR") else 0


if __name__ == "__main__":
    sys.exit(main())
