import { getJson } from "./client";
export const getAudit = () => getJson<Record<string, unknown>[]>("/audit");
