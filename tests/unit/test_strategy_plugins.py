"""Generic parametrized plug-in test: loops over every strategy discovered by Registry.

For each discovered strategy it checks:
  1. entry_point module imports
  2. manifest has all required keys
  3. entry_point class is a subclass of strategies.base.Strategy
  4. class instantiates with an empty params dict
"""
import importlib
import pytest

from registry.registry import Registry
from strategies.base import Strategy
from strategies.validation import validate_manifest


def _discovered_strategies():
    reg = Registry()
    return sorted(reg.discover())


@pytest.mark.parametrize("strategy_id", _discovered_strategies())
def test_strategy_plugin(strategy_id):
    reg = Registry()
    manifest = reg.manifest(strategy_id)

    # 1) manifest schema
    errs = validate_manifest(manifest)
    assert not errs, f"{strategy_id}: manifest missing keys {errs}"

    # 2) entry_point imports
    mod_name, cls_name = manifest["entry_point"].split(":")
    mod = importlib.import_module(mod_name)
    cls = getattr(mod, cls_name)

    # 3) class implements Strategy interface
    assert issubclass(cls, Strategy), f"{strategy_id}: {cls_name} is not a Strategy subclass"

    # 4) instantiates with empty params
    instance = cls({})
    assert instance.strategy_id == strategy_id or instance.strategy_id == manifest["id"]
