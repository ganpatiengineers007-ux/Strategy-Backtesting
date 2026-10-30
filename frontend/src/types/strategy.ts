export interface Strategy {
  id: string;
  version: string;
  entry_point: string;
  required_data: string[];
  parameters: Record<string, unknown>;
  execution_modes: string[];
}
