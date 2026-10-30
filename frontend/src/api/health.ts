import { getJson } from "./client";
export const getHealth = () => getJson<{ status: string }>("/health");
