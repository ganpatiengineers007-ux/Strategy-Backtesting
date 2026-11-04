import { getJson } from "./client";
import { Dataset } from "../types/dataset";
export const listDatasets = () => getJson<Dataset[]>("/datasets");
