# Data contract

Dataset metadata: dataset_id, symbol, timeframe, start/end time, timezone, source, schema_version, content_hash, quality_status.
Checks: duplicate/out-of-order timestamp, non-positive price, inconsistent OHLC. Koi ERROR => BLOCKED.
