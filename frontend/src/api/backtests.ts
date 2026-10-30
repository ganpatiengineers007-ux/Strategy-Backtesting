import { getJson, postJson } from "./client";
import { Run } from "../types/backtest";
export const listRuns = () => getJson<Run[]>("/backtests");
export const getRun = (id: string) => getJson<Run>(`/backtests/${id}`);
export const startRun = (body: unknown) => postJson<Run>("/backtests", body);
