import { getJson } from "./client";
export const listDatasets = () => getJson<Record<string, unknown>[]>("/datasets");
