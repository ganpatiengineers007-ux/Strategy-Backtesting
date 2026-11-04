CREATE TABLE IF NOT EXISTS runs (
    run_id TEXT PRIMARY KEY,
    strategy_id TEXT NOT NULL,
    status TEXT NOT NULL,
    created_at TEXT NOT NULL,
    record TEXT NOT NULL
);
