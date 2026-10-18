import { useEffect, useRef, useState } from "react";
import type { Dispatch, SetStateAction } from "react";
import { Button } from "../components/primitives";
import { blankCriterion, editCriteria, fieldId, initialCriteriaState, prepareCriteria } from "./criteria";
import type { CriteriaDraft, CriteriaError, CriteriaState, DraftCriterion } from "./criteria";
import "./criteria.css";

export function StockCriteria({ state, setState }: { state: CriteriaState; setState: Dispatch<SetStateAction<CriteriaState>> }) {
  const [errors, setErrors] = useState<readonly CriteriaError[]>([]);
  const pendingFocus = useRef<string | null>(null);
  useEffect(() => {
    if (pendingFocus.current) document.getElementById(pendingFocus.current)?.focus();
    pendingFocus.current = null;
  }, [state.draft]);
  useEffect(() => {
    const clearErrors = () => setErrors([]);
    window.addEventListener("pagehide", clearErrors);
    return () => window.removeEventListener("pagehide", clearErrors);
  }, []);
  const edit = (draft: CriteriaDraft, focus?: string) => { pendingFocus.current = focus ?? null; setState(previous => editCriteria(previous, draft)); setErrors([]); };
  const changeRow = (index: number, row: DraftCriterion) => edit({ ...state.draft, criteria: state.draft.criteria.map((item, i) => i === index ? row : item) });
  const errorFor = (id: string) => errors.find(error => error.field === id);
  const attributes = (id: string) => ({ id, "aria-invalid": errorFor(id) ? true as const : undefined, "aria-describedby": errorFor(id) ? `${id}-error` : undefined });
  const errorText = (id: string) => errorFor(id) && <p id={`${id}-error`} className="field-error">{errorFor(id)!.message}</p>;
  const prepare = () => {
    const result = prepareCriteria(state.draft);
    if (result.ok) { setErrors([]); setState(previous => ({ ...previous, prepared: result.snapshot, outdated: false })); }
    else { setErrors(result.errors); document.getElementById(result.errors[0]!.field)?.focus(); }
  };
  return <>
    <section className="panel criteria-editor" aria-labelledby="criteria-editor-title">
      <h2 id="criteria-editor-title">Your stock criteria</h2>
      <p>Choose any parameter name, then enter an inclusive numeric range with units and context, or a text requirement.</p>
      <p>These are your requests. No metric is evaluated and no stock search runs. Taurus search is unavailable.</p>
      <form onSubmit={event => { event.preventDefault(); prepare(); }} noValidate>
        <div className="settings-field"><label htmlFor="criteria-match">Match mode</label>
          <select {...attributes("criteria-match")} value={state.draft.match} onChange={event => edit({ ...state.draft, match: event.target.value as "all" | "any" })}>
            <option value="all">All criteria</option><option value="any">Any criterion</option>
          </select>{errorText("criteria-match")}</div>
        <div className="criteria-rows">{state.draft.criteria.map((row, index) => <fieldset className="criteria-row" key={index}>
          <legend>Criterion {index + 1}</legend>
          <div className="settings-field"><label htmlFor={fieldId(index, "parameter")}>Parameter name {index + 1}</label>
            <input {...attributes(fieldId(index, "parameter"))} value={row.parameter} onChange={event => changeRow(index, { ...row, parameter: event.target.value })} />{errorText(fieldId(index, "parameter"))}</div>
          <div className="settings-field"><label htmlFor={fieldId(index, "kind")}>Criterion type {index + 1}</label>
            <select {...attributes(fieldId(index, "kind"))} value={row.kind} onChange={event => changeRow(index, event.target.value === "text" ? { parameter: row.parameter, kind: "text", value: "" } : { ...blankCriterion(), parameter: row.parameter })}>
              <option value="range">Numeric range</option><option value="text">Text requirement</option>
            </select>{errorText(fieldId(index, "kind"))}</div>
          {row.kind === "range" ? <>
            <div className="settings-field"><label htmlFor={fieldId(index, "unit")}>Units and context {index + 1}</label>
              <input {...attributes(fieldId(index, "unit"))} value={row.unit} onChange={event => changeRow(index, { ...row, unit: event.target.value })} />{errorText(fieldId(index, "unit"))}</div>
            <p className="field-hint">Enter plain decimals, with at least one bound. Include the period and meaning in your context; no units are inferred.</p>
            <div className="criteria-bounds">{(["minimum", "maximum"] as const).map(field => <div className="settings-field" key={field}>
              <label htmlFor={fieldId(index, field)}>{field === "minimum" ? "Minimum" : "Maximum"} {index + 1} (inclusive)</label>
              <input {...attributes(fieldId(index, field))} type="text" value={row[field]} onChange={event => changeRow(index, { ...row, [field]: event.target.value })} />{errorText(fieldId(index, field))}
            </div>)}</div>
          </> : <div className="settings-field"><label htmlFor={fieldId(index, "value")}>Text requirement {index + 1}</label>
            <input {...attributes(fieldId(index, "value"))} type="text" value={row.value} onChange={event => changeRow(index, { ...row, value: event.target.value })} />{errorText(fieldId(index, "value"))}</div>}
          <Button onClick={() => edit({ ...state.draft, criteria: state.draft.criteria.filter((_, i) => i !== index) }, state.draft.criteria.length > 1 ? fieldId(Math.min(index, state.draft.criteria.length - 2), "parameter") : "criteria-add")}>Remove criterion {index + 1}</Button>
        </fieldset>)}</div>
        <div className="actions"><Button {...attributes("criteria-add")} disabled={state.draft.criteria.length >= 20} onClick={() => edit({ ...state.draft, criteria: [...state.draft.criteria, blankCriterion()] }, fieldId(state.draft.criteria.length, "parameter"))}>Add criterion</Button>
          <Button type="submit">Prepare criteria</Button><Button onClick={() => { pendingFocus.current = fieldId(0, "parameter"); setState(initialCriteriaState()); setErrors([]); }}>Clear criteria</Button></div>
        <p>{state.draft.criteria.length} of 20 criteria</p>
        {errors.length > 0 && <div className="error-state" role="alert">Criteria are not prepared. Review the marked fields.{errorText("criteria-add")}</div>}
      </form>
    </section>
    {state.prepared && <section className="panel" aria-labelledby="criteria-prepared-title">
      <h2 id="criteria-prepared-title">{state.outdated ? "Outdated — prepare your edited criteria" : "Prepared — Taurus search unavailable"}</h2>
      <p role="status">{state.outdated ? "This earlier snapshot is outdated. It does not represent the current draft." : "Prepared in this tab only. No search, evaluation or match is claimed."}</p>
      <p>Unevaluated user criteria; currency, periods and financial meaning require evidence before a future search can claim a match.</p>
      <pre className="criteria-preview" tabIndex={0} aria-label={state.outdated ? "Outdated criteria snapshot" : "Prepared criteria snapshot"}>{JSON.stringify(state.prepared, null, 2)}</pre>
    </section>}
  </>;
}
