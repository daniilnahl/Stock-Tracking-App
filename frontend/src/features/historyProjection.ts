// The ONLY Decimal-to-Number boundary: disposable, approximate chart geometry.
// Never reuse these numbers for displayed values, storage or financial metrics.
export function projectHistory(bars: readonly { date: string; close: string }[]): readonly { date: string; x: number; y: number }[] | null {
  if (!bars.length) return [];
  const values = bars.map(bar => Number(bar.close));
  const dates = bars.map(bar => Date.parse(`${bar.date}T00:00:00Z`));
  if (values.some((value, index) => !Number.isFinite(value) ||
    (value === 0 && /[1-9]/.test(bars[index]!.close.split(/[eE]/)[0]!))) || dates.some(date => !Number.isFinite(date))) return null;
  let low = values[0]!;
  let high = low;
  for (const value of values) { if (value < low) low = value; if (value > high) high = value; }
  const spread = high - low;
  const first = dates[0]!;
  const timeSpan = dates[dates.length - 1]! - first;
  if (!Number.isFinite(spread) || !Number.isFinite(timeSpan) || timeSpan < 0) return null;
  const points = values.map((value, index) => ({ date: bars[index]!.date,
    x: timeSpan === 0 ? 300 : 30 + (dates[index]! - first) / timeSpan * 540,
    y: spread === 0 ? 130 : 230 - (value - low) / spread * 200 }));
  return points.every(point => Number.isFinite(point.x) && Number.isFinite(point.y)) ? points : null;
}
