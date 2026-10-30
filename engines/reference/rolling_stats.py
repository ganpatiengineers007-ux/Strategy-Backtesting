"""Python reference: native (C++/Rust) result isi se match hona chahiye."""
import math


def rolling_mean(values, window):
    out, s = [math.nan] * len(values), 0.0
    if window <= 0:
        return out
    for i, v in enumerate(values):
        s += v
        if i >= window:
            s -= values[i - window]
        if i + 1 >= window:
            out[i] = s / window
    return out
