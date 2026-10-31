import { lineChartSvg } from "../chart-panel";

export function equityCurve(points: [string, number][]): string {
  return lineChartSvg(points.map((p) => p[1]));
}
