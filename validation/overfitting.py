def run(oos):
    if oos.get("status") == "UNAVAILABLE" or oos.get("is_expectancy", 0) <= 0:
        return {"status": "UNAVAILABLE", "reason": "NEEDS_PROFITABLE_IN_SAMPLE_AND_ENOUGH_OOS_TRADES"}
    drop = (oos["is_expectancy"] - oos["oos_expectancy"]) / oos["is_expectancy"]
    return {"status": "FAIL" if drop > 0.5 else "PASS", "degradation": drop}
