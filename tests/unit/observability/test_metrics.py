from observability import metrics, tracing


def test_counters_and_spans():
    metrics.reset()
    metrics.inc("runs")
    metrics.inc("runs", 2)
    assert metrics.snapshot() == {"runs": 3}
    with tracing.span("x"):
        pass
    assert tracing.SPANS[-1]["name"] == "x"
