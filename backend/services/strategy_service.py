from registry.registry import Registry


def list_strategies():
    reg = Registry()
    return [{**reg.manifest(s), "source_hash": reg.source_hash(s)} for s in reg.discover()]


def get_strategy(strategy_id):
    reg = Registry()
    m = reg.manifest(strategy_id)  # KeyError agar unknown
    return {**m, "source_hash": reg.source_hash(strategy_id)}
