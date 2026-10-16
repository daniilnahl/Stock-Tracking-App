import { useEffect, useLayoutEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { useLocalSession } from "../app/session";
import { Button, Chart, DataTable, EmptyState, ErrorState, FilterPanel, SettingsField } from "../components/primitives";
import type { Column } from "../components/primitives";
import type { Selection } from "../services/client";
import type { BarResponse, EntryResponse } from "../services/contracts.generated";
import { ClientError } from "../services/validation";
import { projectHistory } from "./historyProjection";
import "./stored-row.css";

const columns: readonly Column<BarResponse>[] = [
  { id: "date", header: "Session date", render: bar => bar.date },
  ...(["open", "high", "low", "close"] as const).map(id => ({ id, header: `${id[0]!.toUpperCase()}${id.slice(1)} / per share`, numeric: true, render: (bar: BarResponse) => bar[id] })),
  { id: "adjusted", header: "Adjusted close", render: () => "Unavailable" },
  { id: "volume", header: "Volume / shares", numeric: true, render: bar => bar.volume === null ? "Unavailable" : bar.volume.toString() },
];
const metadataLabels = {
  sector: "Sector", country: "Country", currency: "Currency label", market_cap: "Market cap display text",
  price_1d: "1-day display text", price_5d: "5-day display text", price_30d: "30-day display text", price_3m: "3-month display text",
  price_6m: "6-month display text", price_1y: "1-year display text", price_3y: "3-year display text", price_5y: "5-year display text",
} as const;
export function StoredRowDetail({ entry, selection, onClose }: { entry: EntryResponse; selection: Selection; onClose: () => void }) {
  const heading = useRef<HTMLHeadingElement>(null);
  useLayoutEffect(() => { heading.current?.focus(); }, []);
  return <section className="stored-detail" aria-labelledby="stored-detail-title">
    <div className="panel-heading"><h3 id="stored-detail-title" ref={heading} tabIndex={-1}>Stored-row detail / {entry.stock.symbol}</h3><Button onClick={onClose}>Close detail</Button></div>
    <p>Returned request-local selection: {selection.namespace} / ordinal {selection.ordinal}. This is not a permanent holding identity; identical duplicates cannot be tracked across separate reads.</p>
    <p>Saved observation only. Currency, source, observation time, retrieval time and freshness: unknown. No verified company profile or current quote is acquired.</p>
    <dl className="saved-fields">
      <div><dt>Security name</dt><dd>{entry.stock.name ?? "Unavailable"}</dd></div>
      <div><dt>Exchange</dt><dd>{entry.stock.exchange ?? "Unavailable"}</dd></div>
      <div><dt>Quantity / shares</dt><dd>{entry.quantity}</dd></div>
      <div><dt>Ownership</dt><dd>{entry.average_cost === null ? "Unowned" : "Owned"}</dd></div>
      <div><dt>Average cost / per share / currency unknown</dt><dd>{entry.average_cost ?? "Not applicable (unowned)"}</dd></div>
      <div><dt>Saved price / per share / currency unknown</dt><dd>{entry.current_price ?? "Unavailable"}</dd></div>
    </dl>
    <h4>Saved position snapshot</h4>
    {entry.snapshot === null ? <EmptyState title={entry.average_cost === null ? "Unowned / no position snapshot" : "Position snapshot unavailable"} message="No numeric snapshot values are substituted." /> :
      <dl className="saved-fields">
        <div><dt>Cost basis / currency amount / currency unknown</dt><dd>{entry.snapshot.cost_basis}</dd></div>
        <div><dt>Market value / currency amount / currency unknown</dt><dd>{entry.snapshot.market_value ?? "Unavailable"}</dd></div>
        <div><dt>Unrealized P&amp;L / currency amount / currency unknown</dt><dd>{entry.snapshot.unrealized_pnl ?? "Unavailable"}</dd></div>
        <div><dt>Unrealized return / decimal ratio</dt><dd>{entry.snapshot.unrealized_return ?? "Unavailable"}</dd></div>
      </dl>}
    <p className="footnote">Snapshot values come unchanged from the API. Return is a dimensionless ratio, not percentage points. A zero cost basis has no defined return; missing values are never replaced with zero.</p>
    <details><summary>Opaque saved metadata / not a verified profile</summary>
      <p>These are saved text labels, not numeric inputs or evidence of currency, returns or provenance.</p>
      <dl className="saved-fields">{Object.entries(metadataLabels).map(([key, label]) => <div key={key}><dt>{label}</dt><dd>{entry.metadata[key as keyof typeof metadataLabels] ?? "Unavailable"}{entry.metadata[key as keyof typeof metadataLabels] === "" ? "Empty saved text" : ""}</dd></div>)}</dl>
    </details>
    <StoredHistory selection={selection} />
  </section>;
}

function StoredHistory({ selection }: { selection: Selection }) {
  const { client, snapshot } = useLocalSession();
  const [start, setStart] = useState("");
  const [end, setEnd] = useState("");
  const [failure, setFailure] = useState<ClientError | null>(null);
  const [cancelled, setCancelled] = useState(false);
  const [showHistory, setShowHistory] = useState(true);
  const request = useRef<AbortController | null>(null);
  const attempt = useRef(0);
  const controls = useRef<HTMLDivElement>(null);
  const startField = useRef<HTMLInputElement>(null);
  const active = snapshot.selection === selection;
  const resource = active ? snapshot.history : null;
  const loading = resource?.status === "loading";
  const data = showHistory && resource?.status === "success" ? resource.data : null;
  const error = failure ?? (resource?.status === "error" ? resource.error : null);
  const disabled = !active || snapshot.connection !== "connected";
  useEffect(() => () => { attempt.current++; request.current?.abort(); }, [client, selection]);
  useLayoutEffect(() => { if (cancelled) controls.current?.querySelector<HTMLButtonElement>("button")?.focus(); }, [cancelled]);
  const read = async () => {
    attempt.current++;
    request.current?.abort();
    const current = attempt.current;
    const controller = new AbortController();
    request.current = controller;
    setFailure(null); setCancelled(false); setShowHistory(false);
    try {
      await client.loadHistory(selection, { ...(start || end ? { start, end } : {}), signal: controller.signal });
      if (current === attempt.current) setShowHistory(true);
    }
    catch (error) {
      if (current === attempt.current) {
        const safe = error instanceof ClientError ? error : new ClientError("api_error");
        if (safe.code !== "cancelled") { setFailure(safe); if (safe.code === "invalid_request") startField.current?.focus(); }
      }
    } finally { if (current === attempt.current) request.current = null; }
  };
  const submit = (event: FormEvent<HTMLFormElement>) => { event.preventDefault(); void read(); };
  const points = data ? projectHistory(data.bars) : null;
  return <section className="stored-history" aria-labelledby="stored-history-title"><h4 id="stored-history-title">Raw stored-row history</h4>
    <p>Historical acquisition remains disabled unless the operator has separately satisfied the rights gate. This page cannot enable it.</p>
    <form onSubmit={submit} noValidate>
      <FilterPanel title="History date range">
        <p>Enter both ISO dates or leave both blank for the API's resolved default range. Editing fields does not request data; results show their returned range below.</p>
        <div className="history-range">
          <SettingsField label="Start date" hint="YYYY-MM-DD, inclusive.">{attributes => <input {...attributes} ref={startField} value={start} onChange={event => setStart(event.target.value)} placeholder="YYYY-MM-DD" aria-invalid={error?.code === "invalid_request" ? true : undefined} />}</SettingsField>
          <SettingsField label="End date" hint="YYYY-MM-DD, inclusive.">{attributes => <input {...attributes} value={end} onChange={event => setEnd(event.target.value)} placeholder="YYYY-MM-DD" aria-invalid={error?.code === "invalid_request" ? true : undefined} />}</SettingsField>
        </div>
      </FilterPanel>
      <div className="actions" ref={controls}><Button type="submit" disabled={disabled || loading}>{data ? "Reload raw history" : "Read raw history"}</Button>
        {loading && <Button onClick={() => { attempt.current++; request.current?.abort(); request.current = null; setCancelled(true); }}>Cancel history read</Button>}
      </div>
    </form>
    {error && <ErrorState error={error} {...(!disabled && !loading && error.apiCode !== "history_disabled" ? { onRetry: () => { startField.current?.focus(); void read(); } } : {})} />}
    {error?.apiCode === "history_disabled" && <EmptyState title="Historical acquisition disabled" message="The server rights gate is closed. No history was acquired; this control does not change permissions." />}
    {loading && <EmptyState title="Reading raw history" message="Previous history is cleared while this request is pending." />}
    {!data && !loading && !error && <EmptyState title={cancelled ? "History read cancelled" : "History not loaded"} message="Use an explicit history read for this returned row. No request is automatic." />}
    {data && <>
      <p className="state-title" role="status">Returned inclusive range: {data.start} to {data.end}. Raw prices, currency unknown; volume in shares. Session dates are labels, not observation timestamps.</p>
      <p className="footnote">History source: {data.provenance.source ?? "unknown"}. Freshness: {data.provenance.freshness === "accepted_cache_policy" ? "accepted cache policy (not a live-price claim)" : "unknown"}. Observation time and retrieval time: unknown. Adjusted prices and adjusted returns are unavailable.</p>
      <Chart title="Approximate raw close observations / currency unknown">
        <p>Approximate chart only. Points mark returned session dates without connecting lines, inferred sessions or returns. See the exact-value table for every price and volume.</p>
        {points === null ? <p>Chart unavailable: values cannot be safely projected into finite browser coordinates. Exact data remains below.</p> : points.length === 0 ? <p>No returned observations.</p> :
          <svg viewBox="0 0 600 260" role="img" aria-label={`Approximate raw close observations, ${data.start} to ${data.end}`}>
            <desc>Horizontal position uses returned calendar dates; vertical position is an approximate close-price scale. No interpolated data is drawn. Exact values follow in the table.</desc>
            <path className="history-axis" d="M30 20 V230 H570" />
            {points.map(point => <circle key={point.date} className="history-point" cx={point.x} cy={point.y} r="5" />)}
          </svg>}
        {points !== null && points.length > 0 && <div className="history-chart-dates"><span>First returned session: {data.bars[0]!.date}</span><span>Last returned session: {data.bars[data.bars.length - 1]!.date}</span></div>}
      </Chart>
      <DataTable caption="Exact raw history / saved row" columns={columns} rows={data.bars} rowKey={bar => bar.date} emptyMessage="No returned observations." />
    </>}
  </section>;
}
