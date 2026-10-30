from contracts import schema_check
from registry.registry import Registry


def test_all_manifests_match_contract():
    reg = Registry()
    for sid in reg.discover():
        assert not schema_check.check(reg.manifest(sid), schema_check.load("strategy.schema.json")), sid
