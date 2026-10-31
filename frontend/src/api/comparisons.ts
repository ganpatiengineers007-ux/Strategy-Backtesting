import { postJson } from "./client";
export const compareRuns = (runIds: string[]) => postJson<Record<string, any>>("/comparisons", { run_ids: runIds });
