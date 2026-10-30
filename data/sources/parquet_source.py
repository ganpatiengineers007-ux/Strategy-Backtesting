"""Parquet reader (pyarrow optional)."""


def read_rows(path):
    try:
        import pyarrow.parquet as pq
    except ImportError as e:
        raise RuntimeError("Parquet ke liye `pip install pyarrow` chahiye") from e
    return pq.read_table(path).to_pylist()
