import { getJson } from "./client";
import { Strategy } from "../types/strategy";
export const listStrategies = () => getJson<Strategy[]>("/strategies");
export const getStrategy = (id: string) => getJson<Strategy>(`/strategies/${id}`);
