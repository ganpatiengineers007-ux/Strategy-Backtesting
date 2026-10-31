"""RegistryStore: strategy status + history (JSON). Gates: VALIDATED ke liye validation PASS, APPROVED ke liye admin + pichhli PASS."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

from registry import lifecycle, permissions

_ACTION = {"DRAFT": "register", "VALIDATED": "run_validation", "APPROVED": "approve", "REJECTED": "reject", "RETIRED": "retire"}


class RegistryStore:
    def __init__(self, root="registry_state"):
        self.file = Path(root) / "state.json"

    def _load(self):
        return json.loads(self.file.read_text(encoding="utf-8")) if self.file.exists() else {}

    def _save(self, state):
        self.file.parent.mkdir(parents=True, exist_ok=True)
        tmp = self.file.with_suffix(".tmp")
        tmp.write_text(json.dumps(state, indent=2), encoding="utf-8")
        os.replace(tmp, self.file)

    def get(self, sid):
        return self._load().get(sid, {"status": "DRAFT", "validation_status": None, "validation_run_id": None, "history": []})

    def promote(self, sid, to, role, validation_status=None, validation_run_id=None, note=""):
        if to not in _ACTION:
            raise ValueError(f"unknown status {to}")
        permissions.require(role, _ACTION[to])
        entry = self.get(sid)
        cur = entry["status"]
        if not lifecycle.can_transition(cur, to):
            raise ValueError(f"transition {cur} -> {to} allowed nahi")
        if to == "VALIDATED":
            if validation_status != "PASS":
                raise ValueError("VALIDATED ke liye validation status PASS chahiye")
            entry["validation_status"], entry["validation_run_id"] = validation_status, validation_run_id
        if to == "APPROVED" and entry.get("validation_status") != "PASS":
            raise ValueError("APPROVED ke liye pichhli validation PASS honi chahiye")
        entry["status"] = to
        entry["history"].append({"ts": datetime.now(timezone.utc).isoformat(), "from": cur, "to": to, "role": role, "note": note})
        state = self._load()
        state[sid] = entry
        self._save(state)
        return entry
