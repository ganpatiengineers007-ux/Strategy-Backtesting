# Data contract

Dataset metadata: dataset_id, symbol, timeframe, start/end time, timezone, source, schema_version, content_hash, quality_status.
Checks: duplicate/out-of-order timestamp, non-positive price, inconsistent OHLC. Koi ERROR => BLOCKED.

Extra columns are preserved on `Bar.extras`. Numeric extras (for example `oi`) become floats; the `option_chain` column may contain a JSON array and is parsed into a list of contract dicts.
