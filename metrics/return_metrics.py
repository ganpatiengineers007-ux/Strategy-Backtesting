def compute(equity, initial):
    final = equity[-1][1] if equity else initial
    return {"final_equity": final, "total_return_pct": (final / initial - 1) * 100.0}
