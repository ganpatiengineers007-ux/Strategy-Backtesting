from pathlib import Path

from data.loaders import load_dataset

FIX = Path(__file__).resolve().parents[1] / "fixtures"


def test_fixture_loads_with_extra_fields():
    ds = load_dataset(FIX / "sample_ohlcv.csv", symbol="X", timeframe="5m")
    assert ds.quality_status == "PASS" and "oi" in ds.fields and len(ds.bars) == 6
    assert len(ds.content_hash) == 64
