export function lineChartSvg(values: number[], w = 600, h = 160, color = "#2563eb"): string {
  if (values.length < 2) return "<p>Not enough data</p>";
  const lo = Math.min(...values);
  const span = Math.max(...values) - lo || 1;
  const pts = values.map((v, i) => `${((i * w) / (values.length - 1)).toFixed(1)},${(h - ((v - lo) / span) * (h - 10) - 5).toFixed(1)}`).join(" ");
  return `<svg viewBox="0 0 ${w} ${h}" width="100%"><polyline fill="none" stroke="${color}" stroke-width="1.5" points="${pts}"/></svg>`;
}
