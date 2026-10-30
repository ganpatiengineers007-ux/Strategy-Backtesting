_counters = {}


def inc(name, n=1):
    _counters[name] = _counters.get(name, 0) + n


def snapshot():
    return dict(_counters)


def reset():
    _counters.clear()
