import { getJson } from "./client";

export interface HubStatus { quotes: number; last_quote_age_s: number | null; candle_series: number; instruments: number }
export interface ChainRow { strike: number; opt_type: string; ltp: number | null; iv: number | null; delta: number | null; gamma: number | null; oi: number | null }

const q = encodeURIComponent;
export const hubStatus = () => getJson<HubStatus>("/hub/status");
export const hubQuotes = (limit = 30) => getJson<Record<string, unknown>[]>(`/hub/quotes?limit=${limit}`);
export const hubCoverage = () => getJson<Record<string, unknown>[]>("/hub/coverage");
export const hubCandles = (symbol: string, tf: string, limit = 200) =>
  getJson<number[][]>(`/hub/candles?symbol=${q(symbol)}&tf=${q(tf)}&limit=${limit}`);
export const hubChain = (underlying: string) =>
  getJson<{ underlying: string; spot: number | null; rows: ChainRow[] }>(`/hub/chain?underlying=${q(underlying)}`);
