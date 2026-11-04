import { Raw, esc, renderTable } from "./data-table";
import { statusBadge, syntheticBadge } from "./status-badge";

export function runsTable(runs: Record<string, any>[]): string {
  const rows = runs.map((r) => {
    const id = esc(r.run_id ?? "");
    return {
      run_id: r.run_id ?? "",
      strategy: r.strategy_id ?? "",
      status: new Raw(statusBadge(String(r.status ?? "UNKNOWN"))),
      validation: r.validation_status ?? "",
      data: new Raw(syntheticBadge(r.synthetic) || '<span class="badge unknown">real/unknown</span>'),
      reason: r.reason ?? "",
      open: new Raw(`<a href="#report/${id}">report</a> | <a href="#validation/${id}">validation</a> | <a href="#run/${id}">detail</a>`),
    };
  });
  return renderTable(rows);
}
