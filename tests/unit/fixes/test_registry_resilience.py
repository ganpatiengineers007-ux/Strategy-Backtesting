"""Regression: ek kharab manifest se poori registry nahi girti."""
import os
import shutil
import tempfile

from registry.registry import Registry


def test_bad_manifest_does_not_break_registry():
    tmp = tempfile.mkdtemp(prefix="reg_test_")
    try:
        bad = os.path.join(tmp, "bad_one")
        os.makedirs(bad)
        with open(os.path.join(bad, "manifest.yaml"), "w", encoding="utf-8") as f:
            f.write("id: bad_one\n")
        reg = Registry(strategies_dir=tmp)
        ids = reg.discover()
        assert ids == []
        assert "bad_one" in reg.errors
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
