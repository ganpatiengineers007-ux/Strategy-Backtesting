import logging
import pandas as pd
from .indicators import validate_ohlcv

log = logging.getLogger(__name__)

def load_csv(path: str, timestamp_column: str = "timestamp") -> pd.DataFrame:
    frame = pd.read_csv(path)
    if timestamp_column in frame.columns:
        frame[timestamp_column] = pd.to_datetime(frame[timestamp_column], errors="raise")
        frame = frame.set_index(timestamp_column)
    frame.columns = [str(c).strip().lower() for c in frame.columns]
    frame = frame.sort_index()
    validate_ohlcv(frame)
    log.info("Loaded %d rows from %s", len(frame), path)
    return frame
