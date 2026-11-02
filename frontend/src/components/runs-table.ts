import { Raw, esc, renderTable } from "./data-table";

export function runsTable(runs: Record<string, any>[]): string {
  const rows = runs.map((r) => {
    const id = esc(r.run_id ?? "");
    return {
      run_id: r.run_id ?? "",
      strategy: r.strategy_id ?? "",
      status: r.status ?? "",
      validation: r.validation_status ?? "",
      created: r.created_at ?? "",
      open: new Raw(`<a href="#report/${id}">report</a> | <a href="#validation/${id}">validation</a> | <a href="#run/${id}">detail</a>`),
    };
  });
  return renderTable(rows);
}
