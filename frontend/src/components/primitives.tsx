import { useId } from "react";
import type { ButtonHTMLAttributes, ReactNode, Ref } from "react";
import type { RouteId } from "../app/routes";
import { navigation } from "../app/routes";
import type { ClientError } from "../services/validation";

export function Button({ type = "button", className = "", ...props }: ButtonHTMLAttributes<HTMLButtonElement>) {
  return <button type={type} className={`button ${className}`} {...props} />;
}
export function Navigation({ current }: { current: RouteId | null }) {
  return <nav aria-label="Main navigation">{navigation.map(item =>
    <a key={item.id} href={item.href} aria-current={current === item.id ? "page" : undefined}>{item.label}</a>)}</nav>;
}
export function PageLayout({ title, description, headingRef, children }: {
  title: string; description: string; headingRef?: Ref<HTMLHeadingElement>; children: ReactNode;
}) {
  return <main id="main-content" tabIndex={-1}>
    <p className="eyebrow">Local workspace</p>
    <h1 ref={headingRef} tabIndex={-1}>{title}</h1>
    <p className="page-description">{description}</p>
    {children}
  </main>;
}
export type Column<Row> = { id: string; header: string; render: (row: Row) => ReactNode; numeric?: boolean };
export function DataTable<Row>({ caption, columns, rows, rowKey, emptyMessage }: {
  caption: string; columns: readonly Column<Row>[]; rows: readonly Row[];
  rowKey: (row: Row) => string | number; emptyMessage: string;
}) {
  const hintId = useId();
  return <><p className="scroll-hint" id={hintId}>Scroll horizontally if the table extends beyond the screen.</p>
    <div className="table-wrap" role="region" aria-label={caption} aria-describedby={hintId} tabIndex={0}>
    <table><caption>{caption}</caption><thead><tr>{columns.map(column =>
      <th scope="col" key={column.id} className={column.numeric ? "numeric" : undefined}>{column.header}</th>)}</tr></thead>
      <tbody>{rows.length ? rows.map(row => <tr key={rowKey(row)}>{columns.map(column =>
        <td key={column.id} className={column.numeric ? "numeric" : undefined}>{column.render(row)}</td>)}</tr>) :
        <tr><td colSpan={columns.length} className="table-empty">{emptyMessage}</td></tr>}</tbody>
    </table>
  </div></>;
}
export function EmptyState({ title, message }: { title: string; message: string }) {
  return <div className="empty-state" role="status"><p className="state-title">{title}</p><p>{message}</p></div>;
}
export function ErrorState({ error, onRetry }: { error: ClientError; onRetry?: () => void }) {
  return <div className="error-state" role="alert"><p>{error.message}</p>{onRetry && <Button onClick={onRetry}>Try again</Button>}</div>;
}
export function FilterPanel({ title, children }: { title: string; children: ReactNode }) {
  return <fieldset className="filter-panel"><legend>{title}</legend>{children}</fieldset>;
}
export function SettingsField({ label, hint, children }: {
  label: string; hint: string;
  children: (attributes: { id: string; "aria-describedby": string }) => ReactNode;
}) {
  const id = useId();
  return <div className="settings-field"><label htmlFor={id}>{label}</label>
    {children({ id, "aria-describedby": `${id}-hint` })}<p id={`${id}-hint`} className="field-hint">{hint}</p></div>;
}
// Shape/semantics only. Price rendering and an exact-value table belong to #146.
export function Chart({ title }: { title: string }) {
  return <figure className="chart-placeholder"><figcaption>{title}</figcaption>
    <p>Unavailable. No historical series is loaded.</p></figure>;
}
