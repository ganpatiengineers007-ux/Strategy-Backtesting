"""Parameter constraints. rule = (op, left_param, right_param); abhi op: lt, le."""
DEFAULT_RULES = [("lt", "stop_pct", "target_pct")]


def satisfies(params, rules):
    for op, a, b in rules:
        if a in params and b in params:
            if op == "lt" and not params[a] < params[b]:
                return False
            if op == "le" and not params[a] <= params[b]:
                return False
    return True
