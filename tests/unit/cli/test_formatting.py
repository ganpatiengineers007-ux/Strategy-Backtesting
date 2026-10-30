from cli.formatting import format_metrics


def test_format_metrics():
    out = format_metrics({"a": 1, "long_name": 2})
    assert out.splitlines()[0].startswith("a         ") and "long_name  2" in out
