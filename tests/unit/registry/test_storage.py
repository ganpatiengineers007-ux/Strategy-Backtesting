from registry.storage import RegistryStore


def _fails(fn, exc, *a, **k):
    try:
        fn(*a, **k)
    except exc:
        return True
    return False


def test_gates_and_history(tmp_path):
    s = RegistryStore(tmp_path)
    assert s.get("x")["status"] == "DRAFT"
    assert _fails(s.promote, ValueError, "x", "VALIDATED", "analyst", validation_status="FAIL")
    assert _fails(s.promote, PermissionError, "x", "REJECTED", "analyst")
    assert _fails(s.promote, ValueError, "x", "APPROVED", "admin")  # DRAFT -> APPROVED allowed nahi
    s.promote("x", "VALIDATED", "analyst", validation_status="PASS", validation_run_id="run-1")
    assert _fails(s.promote, PermissionError, "x", "APPROVED", "analyst")
    e = s.promote("x", "APPROVED", "admin", note="manual review")
    assert e["status"] == "APPROVED" and e["validation_run_id"] == "run-1" and len(e["history"]) == 2
    assert RegistryStore(tmp_path).get("x")["status"] == "APPROVED"  # disk par bacha


def test_reject_then_back_to_draft(tmp_path):
    s = RegistryStore(tmp_path)
    s.promote("y", "REJECTED", "admin")
    assert s.promote("y", "DRAFT", "admin")["status"] == "DRAFT"
