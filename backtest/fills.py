"""Exit fill rules (long). Ek candle me Stop + Target dono => conservative: stop pehle."""


def resolve_exit(bar, stop, target, policy="stop_first"):
    if policy != "stop_first":
        raise ValueError(f"unsupported ambiguous_candle_policy: {policy}")
    stop_hit = stop is not None and bar.low <= stop
    target_hit = target is not None and bar.high >= target
    if stop_hit and target_hit:
        return min(stop, bar.open), "STOP_AMBIGUOUS_CONSERVATIVE"
    if stop_hit:
        return min(stop, bar.open), "STOP"  # gap-down: open par fill
    if target_hit:
        return target, "TARGET"
    return None
