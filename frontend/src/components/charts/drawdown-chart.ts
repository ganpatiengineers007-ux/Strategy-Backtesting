import { lineChartSvg } from "../chart-panel";

export function drawdownChart(points: [string, number][]): string {
  let peak = -Infinity;
  const dd = points.map(([, e]) => {
    peak = Math.max(peak, e);
    return -((peak - e) / peak) * 100;
  });
  return lineChartSvg(dd, 600, 120, "#dc2626");
}
