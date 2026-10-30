import { getJson } from "./client";
import { Report } from "../types/report";
export const getReport = (id: string) => getJson<Report>(`/reports/${id}`);
