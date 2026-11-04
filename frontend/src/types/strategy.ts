export interface Strategy {
  id: string;
  version: string;
  entry_point: string;
  required_data: string[];
  parameters: Record<string, unknown>;
  execution_modes: string[];
  status: "RUNNABLE" | "BLOCKED";
  runnable: boolean;
  reason: string;
  blocked_reason?: string;
  data_hint?: string;
  live_trading_enabled?: boolean;
  source_hash?: string;
}
