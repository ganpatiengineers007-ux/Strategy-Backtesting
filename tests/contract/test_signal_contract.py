from contracts import schema_check
from strategies.models import Signal


def test_signal_matches_contract():
    assert not schema_check.check(Signal("BUY", stop_loss=1.0, target=2.0).to_dict(), schema_check.load("signal.schema.json"))
