export interface Report {
  run_id: string;
  status: string;
  metrics: Record<string, unknown>;
  validation: Record<string, unknown>;
  generated_at: string;
}
