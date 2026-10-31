from data.storage import DatasetStore
from tests._helpers import make_bars, make_dataset


def test_round_trip_and_tamper_detection(tmp_path):
    store = DatasetStore(tmp_path)
    ds = make_dataset(make_bars(15))
    store.save(ds)
    back = store.load("t")
    assert back.bars == ds.bars and back.fields == ds.fields and back.meta() == ds.meta()
    assert store.list_ids() == ["t"]
    f = tmp_path / "t" / "bars.jsonl"
    f.write_text(f.read_text().replace("100.", "999.", 1))
    try:
        store.load("t")
        raise AssertionError("expected ValueError")
    except ValueError as e:
        assert "checksum" in str(e)


def test_unsafe_id_and_unknown(tmp_path):
    store = DatasetStore(tmp_path)
    for fn in (store.load,):
        try:
            fn("..")
            raise AssertionError("expected ValueError")
        except ValueError:
            pass
    try:
        store.load("nope")
        raise AssertionError("expected KeyError")
    except KeyError:
        pass
