def equity_svg(equity, w=720, h=200):
    if len(equity) < 2:
        return ""
    step = max(1, len(equity) // 300)
    ys = [e for _, e in equity[::step]]
    lo, hi = min(ys), max(ys)
    span = (hi - lo) or 1.0
    pts = " ".join(f"{i * w / (len(ys) - 1):.1f},{h - (y - lo) / span * (h - 10) - 5:.1f}" for i, y in enumerate(ys))
    return f'<svg viewBox="0 0 {w} {h}" width="100%"><polyline fill="none" stroke="#2563eb" stroke-width="1.5" points="{pts}"/></svg>'
