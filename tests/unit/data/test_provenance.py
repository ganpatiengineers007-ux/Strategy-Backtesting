from data.provenance import data_label, is_synthetic_path


def test_sample_paths_are_synthetic():
    assert is_synthetic_path("data/samples/sample_5m.csv")
    assert is_synthetic_path("sample_options_5m.csv")
    assert data_label("data/samples/sample_5m.csv") == "synthetic"


def test_real_paths_are_not_synthetic():
    assert not is_synthetic_path("data/real/nifty_5m.csv")
    assert data_label("data/real/nifty_5m.csv") == "real"
