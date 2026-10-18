// User descriptions only: no metric registry, evaluation, persistence or execution.
export type RangeCriterion = Readonly<{ parameter: string; kind: "range"; unit: string; minimum: string; maximum: string }>;
export type TextCriterion = Readonly<{ parameter: string; kind: "text"; value: string }>;
export type DraftCriterion = RangeCriterion | TextCriterion;
export type CriteriaDraft = Readonly<{ match: "all" | "any"; criteria: readonly DraftCriterion[] }>;
export type PreparedCriterion = Readonly<{ parameter: string; kind: "range"; unit: string; minimum: string | null; maximum: string | null }> | TextCriterion;
export type PreparedCriteria = Readonly<{ schema_version: 1; kind: "user_stock_criteria"; match: "all" | "any"; criteria: readonly PreparedCriterion[] }>;
export type CriteriaError = Readonly<{ field: string; message: string }>;
export type Preparation = { ok: true; snapshot: PreparedCriteria } | { ok: false; errors: readonly CriteriaError[] };
export type CriteriaState = Readonly<{ draft: CriteriaDraft; prepared: PreparedCriteria | null; outdated: boolean }>;
export const blankCriterion = (): RangeCriterion => ({ parameter: "", kind: "range", unit: "", minimum: "", maximum: "" });
export const initialCriteriaState = (): CriteriaState => ({ draft: { match: "all", criteria: [blankCriterion()] }, prepared: null, outdated: false });
export const editCriteria = (state: CriteriaState, draft: CriteriaDraft): CriteriaState => ({ draft, prepared: state.prepared, outdated: state.prepared !== null });
export const fieldId = (index: number, field: string) => `criterion-${index}-${field}`;
const decimal = /^-?(?:0|[1-9][0-9]*)(?:\.[0-9]+)?$/;
const controls = /[\u0000-\u001f\u007f-\u009f]/;
const record = (value: unknown): value is Record<string, unknown> => typeof value === "object" && value !== null && !Array.isArray(value);
const exactKeys = (value: Record<string, unknown>, keys: readonly string[]) => Object.keys(value).length === keys.length && keys.every(key => Object.hasOwn(value, key));
const text = (value: unknown, limit: number): value is string => typeof value === "string" && value.trim().length > 0 && value.length <= limit && !controls.test(value);
const endpoint = (value: unknown): value is string => typeof value === "string" && (value === "" || (value.length <= 128 && !controls.test(value) && decimal.exec(value)?.[0] === value));

// Called only for validated plain decimals. Magnitudes compare lexically, with
// fractional zero padding; the entered strings themselves are never rewritten.
export function compareDecimals(first: string, second: string): -1 | 0 | 1 {
  if (!endpoint(first) || !endpoint(second) || first === "" || second === "") throw new Error("Invalid decimal comparison input.");
  const parts = (value: string) => {
    const [integer = "0", fraction = ""] = value.replace(/^-/, "").split(".");
    const zero = integer === "0" && !/[1-9]/.test(fraction);
    return { integer, fraction, negative: value.startsWith("-") && !zero };
  };
  const a = parts(first), b = parts(second);
  if (a.negative !== b.negative) return a.negative ? -1 : 1;
  let magnitude: -1 | 0 | 1 = 0;
  if (a.integer.length !== b.integer.length) magnitude = a.integer.length < b.integer.length ? -1 : 1;
  else if (a.integer !== b.integer) magnitude = a.integer < b.integer ? -1 : 1;
  else {
    const width = Math.max(a.fraction.length, b.fraction.length);
    const left = a.fraction.padEnd(width, "0"), right = b.fraction.padEnd(width, "0");
    if (left !== right) magnitude = left < right ? -1 : 1;
  }
  return a.negative ? (magnitude === 0 ? 0 : magnitude === 1 ? -1 : 1) : magnitude;
}

export function prepareCriteria(input: unknown): Preparation {
  const errors: CriteriaError[] = [];
  const add = (field: string, message: string) => errors.push({ field, message });
  if (!record(input) || !exactKeys(input, ["match", "criteria"])) return { ok: false, errors: [{ field: "criteria-match", message: "Use a criteria draft with a match mode and rows." }] };
  if (input.match !== "all" && input.match !== "any") add("criteria-match", "Choose all or any criteria.");
  if (!Array.isArray(input.criteria) || input.criteria.length < 1 || input.criteria.length > 20) return { ok: false, errors: [...errors, { field: "criteria-add", message: "Prepare between 1 and 20 criteria." }] };
  const prepared: PreparedCriterion[] = [];
  Array.from(input.criteria).forEach((row: unknown, index: number) => {
    const error = (field: string, message: string) => add(fieldId(index, field), message);
    if (!record(row)) { error("kind", "Choose a range or text criterion."); return; }
    if (!text(row.parameter, 80)) error("parameter", "Enter a parameter name of 1–80 characters without control characters.");
    if (row.kind === "range") {
      if (!exactKeys(row, ["parameter", "kind", "unit", "minimum", "maximum"])) error("kind", "The range requires only its name, units and two bound fields.");
      if (!text(row.unit, 80)) error("unit", "Enter units and context of 1–80 characters without control characters.");
      const minOK = endpoint(row.minimum), maxOK = endpoint(row.maximum);
      if (!minOK) error("minimum", "Use a plain decimal of at most 128 characters, or leave this bound blank.");
      if (!maxOK) error("maximum", "Use a plain decimal of at most 128 characters, or leave this bound blank.");
      if (minOK && maxOK) {
        if (row.minimum === "" && row.maximum === "") error("minimum", "Enter at least one bound.");
        else if (row.minimum !== "" && row.maximum !== "" && compareDecimals(row.minimum as string, row.maximum as string) > 0) error("minimum", "Minimum must be less than or equal to maximum.");
      }
      if (text(row.parameter, 80) && text(row.unit, 80) && minOK && maxOK) prepared.push(Object.freeze({ parameter: row.parameter, kind: "range", unit: row.unit, minimum: row.minimum === "" ? null : row.minimum as string, maximum: row.maximum === "" ? null : row.maximum as string }));
    } else if (row.kind === "text") {
      if (!exactKeys(row, ["parameter", "kind", "value"])) error("kind", "The text criterion requires only its name and requirement.");
      if (!text(row.value, 256)) error("value", "Enter a requirement of 1–256 characters without control characters.");
      if (text(row.parameter, 80) && text(row.value, 256)) prepared.push(Object.freeze({ parameter: row.parameter, kind: "text", value: row.value }));
    } else error("kind", "Choose a range or text criterion.");
  });
  if (errors.length) return { ok: false, errors };
  return { ok: true, snapshot: Object.freeze({ schema_version: 1, kind: "user_stock_criteria", match: input.match as "all" | "any", criteria: Object.freeze(prepared) }) };
}
