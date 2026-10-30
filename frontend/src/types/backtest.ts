export interface Trade {
  entry_ts: string;
  exit_ts: string;
  entry_price: number;
  exit_price: number;
  qty: number;
  pnl: number;
  fees: number;
  reason: string;
}

export interface Run {
  run_id: string;
  strategy_id: string;
  strategy_version: string;
  source_hash: string;
  dataset_id: string;
  dataset_hash: string;
  status: string;
  parameters: Record<string, unknown>;
  config: Record<string, unknown>;
  engine_version: string;
  created_at: string;
}
