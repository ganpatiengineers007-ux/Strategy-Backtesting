export interface Report {
  run_id: string;
  status: string;
  reason?: string;
  metrics: Record<string, unknown>;
  validation: Record<string, unknown>;
  generated_at: string;
  dataset_id?: string | null;
  synthetic?: boolean;
  data_label?: string;
  equity?: [string, number][];
  trades?: { pnl: number }[];
}
