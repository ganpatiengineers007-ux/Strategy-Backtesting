import { getJson } from "./client";
export const getValidation = (id: string) => getJson<Record<string, any>>(`/validations/${id}`);
