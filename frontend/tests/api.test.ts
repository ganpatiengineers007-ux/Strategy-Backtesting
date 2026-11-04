// Type-level smoke test for the API client surface.
// Runtime integration is covered by the Python API tests; this file keeps the
// client exports type-checked when the frontend test folder is compiled.
import { getJson, postJson, setApiKey, hasApiKey } from "../src/api/client";
import { listStrategies, getStrategy } from "../src/api/strategies";

export const apiSurface = { getJson, postJson, setApiKey, hasApiKey, listStrategies, getStrategy };
