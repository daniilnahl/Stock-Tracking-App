import { describe, expect, it } from "vitest";
import { compareDecimals, editCriteria, initialCriteriaState, prepareCriteria } from "../src/features/criteria";
const range = (minimum = "-0.25", maximum = "1.250000000000000001") => ({ parameter: "My custom parameter", kind: "range", unit: "Explicit units and period", minimum, maximum });
const draft = (row: unknown = range()) => ({ match: "all", criteria: [row] });
describe("exact descriptive criteria preparation", () => {
  it("preserves chosen fields, ordering, duplicate labels, arbitrary text and exact decimal strings", () => {
    const input = { match: "any", criteria: [range("-0.000", "0.0000"), { parameter: "__proto__", kind: "text", value: "<script>user data only</script>" }, range("", "9".repeat(128))] };
    const result = prepareCriteria(input);
    expect(result.ok).toBe(true);
    if (!result.ok) throw new Error("Expected valid input");
    expect(result.snapshot).toEqual({ schema_version: 1, kind: "user_stock_criteria", match: "any", criteria: [{ ...input.criteria[0], minimum: "-0.000", maximum: "0.0000" }, input.criteria[1], { ...input.criteria[2], minimum: null }] });
    expect(Object.isFrozen(result.snapshot)).toBe(true);
    expect(Object.isFrozen(result.snapshot.criteria)).toBe(true);
    expect(result.snapshot.criteria.every(Object.isFrozen)).toBe(true);
    input.criteria[0]!.parameter = "edited";
    expect(result.snapshot.criteria[0]!.parameter).toBe("My custom parameter");
    expect(() => Reflect.set(result.snapshot.criteria[0]!, "parameter", "changed")).not.toThrow();
    expect(result.snapshot.criteria[0]!.parameter).toBe("My custom parameter");
    expect(prepareCriteria({ match: "all", criteria: [range(), range()] }).ok).toBe(true);
    expect(prepareCriteria(draft(range("1", ""))).ok).toBe(true);
  });
  it.each([
    ["-0", "0.000", 0], ["1.250000000000000001", "1.250000000000000002", -1],
    ["-1.250000000000000002", "-1.250000000000000001", -1], ["-2", "-10", 1],
    ["999999999999999999999999999999", "1000000000000000000000000000000", -1],
    ["1.0", "1.000", 0], ["-0.001", "0", -1], ["0.1", "0.01", 1], ["-10.0", "-10", 0],
  ])("compares %s and %s without floating point", (a, b, order) => {
    expect(compareDecimals(a as string, b as string)).toBe(order);
    expect(compareDecimals(b as string, a as string)).toBe(order === 0 ? 0 : -order);
  });
  it.each(["+1", "01", "-01", ".1", "1.", "1e3", "NaN", "Infinity", "1,000", " 1", "1 ", "--1", "1\n", "1\u2028", "1\u2029", "9".repeat(129), 0, null, true])("rejects malformed endpoint %s", value => {
    expect(prepareCriteria(draft({ ...range(), minimum: value })).ok).toBe(false);
    expect(prepareCriteria(draft({ ...range(), maximum: value })).ok).toBe(false);
  });
  it("rejects inverted or empty ranges, with the first error linked to minimum", () => {
    for (const row of [range("", ""), range("1.250000000000000002", "1.250000000000000001")]) {
      const result = prepareCriteria(draft(row));
      expect(result.ok).toBe(false);
      if (!result.ok) expect(result.errors[0]!.field).toBe("criterion-0-minimum");
    }
  });
  it.each([null, [], {}, { match: "all", criteria: [] }, { match: "bad", criteria: [range()] }, { match: "all", criteria: Array(1) }, { match: "all", criteria: [null] }, { ...draft(), extra: true }, draft({ ...range(), unexpected: "do not ignore" }), draft({ ...range(), parameter: 1 }), draft({ ...range(), unit: null }), draft({ ...range(), unit: " " }), draft({ ...range(), parameter: " " }), draft({ parameter: "A", kind: "text", value: "" }), draft({ parameter: "A", kind: "unknown", value: "x" })])("rejects malformed drafts without dropping rows", input => {
    expect(prepareCriteria(input).ok).toBe(false);
  });
  it("enforces character, control and row bounds without trimming entered data", () => {
    expect(prepareCriteria(draft({ ...range(), parameter: "a".repeat(80), unit: "u".repeat(80) })).ok).toBe(true);
    for (const field of ["parameter", "unit"]) for (const value of ["a".repeat(81), "line\nvalue", "a\x7fb", "a\x80b"]) expect(prepareCriteria(draft({ ...range(), [field]: value })).ok).toBe(false);
    expect(prepareCriteria(draft({ parameter: " Name ", kind: "text", value: "x".repeat(256) })).ok).toBe(true);
    expect(prepareCriteria(draft({ parameter: "Name", kind: "text", value: "x".repeat(257) })).ok).toBe(false);
    expect(prepareCriteria(draft({ parameter: "Name", kind: "text", value: "x\ny" })).ok).toBe(false);
    expect(prepareCriteria({ match: "all", criteria: Array.from({ length: 20 }, () => range()) }).ok).toBe(true);
    expect(prepareCriteria({ match: "all", criteria: Array.from({ length: 21 }, () => range()) }).ok).toBe(false);
  });
  it("retains the earlier immutable snapshot as outdated on edits", () => {
    const result = prepareCriteria(draft());
    if (!result.ok) throw new Error("Expected valid input");
    const initial = { ...initialCriteriaState(), prepared: result.snapshot };
    const changed = editCriteria(initial, { match: "any", criteria: [] });
    expect(changed.outdated).toBe(true);
    expect(changed.prepared).toBe(result.snapshot);
    expect(changed.prepared!.match).toBe("all");
    expect(initialCriteriaState().prepared).toBeNull();
    expect(() => compareDecimals("", "1")).toThrow("Invalid decimal comparison input.");
  });
});
