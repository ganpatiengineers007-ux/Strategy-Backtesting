export interface Dataset {
  file: string;
  dataset_id: string;
  symbol: string;
  timeframe: string;
  start_time?: string;
  end_time?: string;
  bars: number;
  quality_status: string;
  content_hash: string;
  synthetic: boolean;
  data_label: "synthetic" | "real";
}
