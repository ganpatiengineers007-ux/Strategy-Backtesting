import re
from pathlib import Path

PROTO = Path(__file__).resolve().parents[2] / "contracts" / "proto"
BLOCK = re.compile(r"(message|enum)\s+(\w+)\s*\{([^{}]*)\}")
FIELD = re.compile(r"^\s*(?:repeated\s+|optional\s+)?(?:map<\s*\w+\s*,\s*[\w.]+\s*>|[\w.]+)\s+(\w+)\s*=\s*(\d+)\s*;", re.M)
ENUM_VAL = re.compile(r"^\s*(\w+)\s*=\s*(-?\d+)\s*;", re.M)


def _clean(text):
    return re.sub(r"//.*", "", text)


def test_every_proto_is_well_formed():
    files = sorted(PROTO.glob("*.proto"))
    assert len(files) == 7
    names_seen = {}
    for f in files:
        t = _clean(f.read_text(encoding="utf-8"))
        assert 'syntax = "proto3";' in t and "package svl;" in t, f.name
        assert t.count("{") == t.count("}"), f.name
        for imp in re.findall(r'import\s+"([^"]+)";', t):
            assert (PROTO / imp).exists(), f"{f.name}: missing import {imp}"
        blocks = BLOCK.findall(t)
        assert blocks, f.name
        for kind, name, body in blocks:
            assert name not in names_seen, f"duplicate type {name}"
            names_seen[name] = f.name
            if kind == "message":
                nums = [int(n) for _, n in FIELD.findall(body)]
                fields = [n for n, _ in FIELD.findall(body)]
                assert len(nums) == len(set(nums)) and len(fields) == len(set(fields)), f"{f.name}:{name}"
                assert all(n >= 1 for n in nums)
            else:
                vals = ENUM_VAL.findall(body)
                assert vals and vals[0][1] == "0", f"{f.name}:{name} pehla enum value 0 hona chahiye"
    assert {"Bar", "Dataset", "Signal", "Trade", "BacktestResult", "Metrics", "Report"} <= set(names_seen)


def test_proto_fields_cover_json_schema_trade_fields():
    from contracts import schema_check
    trade_fields = set(schema_check.load("trade.schema.json")["required"])
    body = re.search(r"message Trade\s*\{([^{}]*)\}", _clean((PROTO / "backtest.proto").read_text(encoding="utf-8"))).group(1)
    assert trade_fields <= {n for n, _ in FIELD.findall(body)}
