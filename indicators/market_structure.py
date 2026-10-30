"""Pivot sirf `right` bars baad confirm hota hai: result me confirm_index se pehle use mat karo."""


def _pivots(vals, left, right, better):
    out = []
    for i in range(left, len(vals) - right):
        if all(better(vals[i], vals[j]) for j in range(i - left, i)) and \
           all(not better(vals[j], vals[i]) for j in range(i + 1, i + right + 1)):
            out.append({"index": i, "confirm_index": i + right, "price": vals[i]})
    return out


def pivot_highs(bars, left=2, right=2):
    return _pivots([b.high for b in bars], left, right, lambda a, b: a > b)


def pivot_lows(bars, left=2, right=2):
    return _pivots([b.low for b in bars], left, right, lambda a, b: a < b)
