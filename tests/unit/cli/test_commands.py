"""CLI sample generators must produce loadable datasets."""
from cli.commands import make_option_sample_csv, make_sample_csv
from data.loaders import load_dataset


def test_make_sample_csv(tmp_path):
    ds = load_dataset(make_sample_csv(tmp_path / "s.csv", days=2))
    assert len(ds.bars) == 2 * 75
    assert {"open", "high", "low", "close", "volume"} <= ds.fields


def test_make_option_sample_csv_has_option_chain(tmp_path):
    ds = load_dataset(make_option_sample_csv(tmp_path / "o.csv", days=2))
    assert "option_chain" in ds.fields and "oi" in ds.fields
    chains = [b.extras["option_chain"] for b in ds.bars if "option_chain" in b.extras]
    assert chains and {c["opt_type"] for c in chains[0]} == {"CE", "PE"}
