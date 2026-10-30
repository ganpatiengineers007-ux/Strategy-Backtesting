from cli.commands import make_sample_csv
from contracts import schema_check
from data.loaders import load_dataset


def test_dataset_meta_matches_contract(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=5), symbol="X", timeframe="5m")
    assert ds.quality_status == "PASS"
    assert not schema_check.check(ds.meta(), schema_check.load("data.schema.json"))
