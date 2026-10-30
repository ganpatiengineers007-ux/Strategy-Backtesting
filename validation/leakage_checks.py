"""Structural checks only. Strategy-level look-ahead ka poora saboot nahi (engine next-bar-open fill karta hai)."""


def run(result, dataset):
    ts = {b.ts for b in dataset.bars}
    problems = []
    for t in result.trades:
        if t["entry_ts"] > t["exit_ts"]:
            problems.append(f"exit before entry: {t['entry_ts']}")
        if t["entry_ts"] not in ts or t["exit_ts"] not in ts:
            problems.append("trade timestamp dataset me nahi")
    times = [p[0] for p in result.equity]
    if any(times[i] >= times[i + 1] for i in range(len(times) - 1)):
        problems.append("equity timestamps strictly increasing nahi")
    return {"status": "FAIL" if problems else "PASS", "problems": problems[:10],
            "note": "structural checks only"}
