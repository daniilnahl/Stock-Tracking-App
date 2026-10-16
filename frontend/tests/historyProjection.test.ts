import { describe, expect, it } from "vitest";
import { projectHistory } from "../src/features/historyProjection";

describe("disposable approximate chart projection", () => {
  it("uses returned calendar date spacing, preserves sparse observations and does not mutate exact values", () => {
    const bars = Object.freeze([{ date: "2020-01-02", close: "100.00000000000000000001" }, { date: "2020-01-03", close: "110" }, { date: "2020-01-06", close: "120" }].map(bar => Object.freeze(bar)));
    const before = JSON.stringify(bars);
    expect(projectHistory(bars)).toEqual([{ date: "2020-01-02", x: 30, y: 230 }, { date: "2020-01-03", x: 165, y: 130 }, { date: "2020-01-06", x: 570, y: 30 }]);
    expect(JSON.stringify(bars)).toBe(before);
  });
  it.each(["1E+9999", "1E-9999", "-1E-9999", "NaN", "Infinity"])("omits unsafe %s geometry instead of coercing or clamping", close => {
    expect(projectHistory([{ date: "2020-01-02", close }])).toBeNull();
  });
  it("allows exact zero, finite extremes and a singleton without division by zero", () => {
    expect(projectHistory([{ date: "2020-01-02", close: "0E+9999" }])).toEqual([{ date: "2020-01-02", x: 300, y: 130 }]);
    expect(projectHistory([{ date: "2020-01-02", close: "1E+308" }, { date: "2020-01-06", close: "1.1E+308" }])?.every(point => Number.isFinite(point.x) && Number.isFinite(point.y))).toBe(true);
    expect(projectHistory([])).toEqual([]);
    expect(projectHistory([{ date: "not-a-date", close: "1" }])).toBeNull();
    expect(projectHistory([{ date: "2020-01-02", close: "-1E+308" }, { date: "2020-01-06", close: "1E+308" }])).toBeNull();
  });
});
