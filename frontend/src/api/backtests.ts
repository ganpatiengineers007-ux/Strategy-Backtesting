import { getJson, postJson } from "./client";
export const listRuns = () => getJson<Record<string, any>[]>("/backtests");
export const getRun = (id: string) => getJson<Record<string, any>>(`/backtests/${id}`);
export const startRun = (body: unknown) => postJson<Record<string, any>>("/backtests", body);
