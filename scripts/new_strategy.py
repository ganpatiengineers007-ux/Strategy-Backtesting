import sys, re
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
name, cls = sys.argv[1], sys.argv[2]
sid = re.sub(r"^STR\d+_", "", name)
d = ROOT / "strategies" / name
d.mkdir(parents=True, exist_ok=False)
(d / "__init__.py").write_text("")
