import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useLocalSession } from "../app/session";
import { routeHref } from "../app/routes";
import { Button, DataTable, EmptyState } from "../components/primitives";
import type { Column } from "../components/primitives";
import type { UpcomingEpsObservationResponse } from "../services/contracts.generated";
import { ClientError, validDate, validUpcomingEpsRequest } from "../services/validation";
import "./upcoming-eps.css";

const columns: readonly Column<UpcomingEpsObservationResponse>[] = [
  { id: "symbol", header: "Provider symbol", render: row => row.symbol },
  { id: "period", header: "Fiscal period", render: row => `${row.fiscal_year} / Q${row.fiscal_quarter}` },
  { id: "release", header: "Vendor release date", render: row => row.release_date },
  { id: "session", header: "Release session", render: row => row.release_session ?? "Unknown" },
  { id: "estimate", header: "Non-GAAP EPS / currency-per-share", numeric: true, render: row => row.estimate ?? "Unavailable (null estimate)" },
  { id: "receipt", header: "Retrieved at / UTC", render: row => row.retrieved_at },
];
function guidance(error: ClientError): string {
  if (error.code === "unauthorized") return "Authentication is required. Private views were cleared. Configure the local API connection in Settings.";
  if (error.code === "disconnected") return "Configure the local API connection in Settings before reading EPS.";
  const known: Record<string, string> = {
    eps_disabled: "Upcoming EPS acquisition is disabled on this local API. Restart it with --enable-upcoming-eps before retrying.",
    eps_rate_limited: "The local EPS budget is unavailable during startup or cooldown, or after its request limit. Wait at least 60 seconds, then retry manually.",
    provider_rate_limited: "The provider rate limit was reached. Wait at least 60 seconds, then retry manually.",
    api_busy: "Another EPS or data operation is still finishing. Try again manually after it completes.",
    invalid_request: "The API rejected the request. Start must be after the server's UTC reference day, with at most 92 included dates.",
    provider_unavailable: "The EPS provider is unavailable or access is not configured. Ask the operator to check the server configuration.",
    provider_timeout: "The EPS request timed out. No data is displayed; retry manually when ready.",
    provider_response_invalid: "The provider returned invalid EPS data. No observations are displayed.",
  };
  return error.apiCode && Object.hasOwn(known, error.apiCode) ? known[error.apiCode]! : error.message;
}
export function UpcomingEps() {
  const { client, snapshot } = useLocalSession();
  const [symbol, setSymbol] = useState(""), [start, setStart] = useState(""), [end, setEnd] = useState("");
  const [invalid, setInvalid] = useState<string | null>(null), [failure, setFailure] = useState<ClientError | null>(null);
  const [cancelled, setCancelled] = useState(false);
  const controller = useRef<AbortController | null>(null), attempt = useRef(0), controls = useRef<HTMLDivElement>(null);
  const resource = snapshot.upcomingEps;
  const loading = resource.status === "loading";
  const data = resource.status === "success" ? resource.data : null;
  const error = failure ?? (resource.status === "error" ? resource.error : null);
  const abandon = () => { attempt.current++; controller.current?.abort(); controller.current = null; client.clearUpcomingEps(); };
  useLayoutEffect(() => { if (cancelled) controls.current?.querySelector<HTMLButtonElement>("button")?.focus(); }, [cancelled]);
  useEffect(() => {
    const clearPage = () => { attempt.current++; controller.current?.abort(); client.clearUpcomingEps(); setSymbol(""); setStart(""); setEnd(""); setFailure(null); setInvalid(null); setCancelled(false); };
    window.addEventListener("pagehide", clearPage);
    return () => { window.removeEventListener("pagehide", clearPage); attempt.current++; controller.current?.abort(); client.clearUpcomingEps(); };
  }, [client]);
  const edit = (setter: (value: string) => void, value: string) => { abandon(); setter(value); setFailure(null); setInvalid(null); setCancelled(false); };
  const read = async () => {
    abandon(); setFailure(null); setCancelled(false);
    const field = /^[A-Z0-9][A-Z0-9.-]{0,31}$/.exec(symbol)?.[0] !== symbol || !symbol ? "eps-symbol" : !validDate(start) ? "eps-start" : !validDate(end) ? "eps-end" : !validUpcomingEpsRequest({ provider_symbol: symbol, start, end }) ? "eps-start" : null;
    setInvalid(field);
    if (field) { document.getElementById(field)?.focus(); return; }
    const current = attempt.current, pending = new AbortController(); controller.current = pending;
    try { await client.loadUpcomingEps({ provider_symbol: symbol, start, end }, { signal: pending.signal }); }
    catch (error) {
      if (current === attempt.current && !pending.signal.aborted) {
        const safe = error instanceof ClientError ? error : new ClientError("api_error");
        setFailure(safe);
        if (safe.apiCode === "invalid_request") { setInvalid("eps-start"); document.getElementById("eps-start")?.focus(); }
      }
    }
    finally { if (current === attempt.current) controller.current = null; }
  };
  return <>
    <section className="panel upcoming-eps-editor" aria-labelledby="eps-form-title"><h2 id="eps-form-title">Request upcoming release estimates</h2>
      <p>Enter the exact Finnhub provider symbol and inclusive release dates.</p>
      <p>Start must be after the server UTC reference day; same-day releases are excluded.</p>
      <p>Configure your local API connection in <a href={routeHref("settings")}>Settings</a>. The Finnhub key stays on the server. Results clear on edits, navigation and reload.</p>
      <form noValidate onSubmit={event => { event.preventDefault(); void read(); }}>
        {([{ id: "eps-symbol", label: "Finnhub provider symbol", value: symbol, setter: setSymbol, hint: "Case-sensitive ASCII: 1–32 uppercase letters, digits, periods or hyphens; start with a letter or digit." },
           { id: "eps-start", label: "EPS start date", value: start, setter: setStart, hint: "Required YYYY-MM-DD. At most 92 included dates; minimum start is decided by the server." },
           { id: "eps-end", label: "EPS end date", value: end, setter: setEnd, hint: "Required YYYY-MM-DD, inclusive; end must not precede start." }] as const).map(field => <div className="settings-field" key={field.id}>
             <label htmlFor={field.id}>{field.label}</label><input id={field.id} type="text" value={field.value} onChange={event => edit(field.setter, event.target.value)} aria-invalid={invalid === field.id ? true : undefined} aria-describedby={`${field.id}-hint${invalid === field.id ? " eps-input-error" : ""}`} />
             <p id={`${field.id}-hint`} className="field-hint">{field.hint}</p>
           </div>)}
        <div className="actions" ref={controls}><Button type="submit" disabled={snapshot.connection !== "connected" || loading}>Read upcoming EPS</Button>
          {loading && <Button onClick={() => { abandon(); setFailure(null); setCancelled(true); }}>Cancel EPS read</Button>}
          <Button onClick={() => { abandon(); setSymbol(""); setStart(""); setEnd(""); setInvalid(null); setFailure(null); setCancelled(false); document.getElementById("eps-symbol")?.focus(); }}>Clear EPS</Button></div>
      </form>
      {invalid && error?.apiCode !== "invalid_request" && <p id="eps-input-error" role="alert">Enter the exact symbol and real ISO dates, ordered within a 92-date inclusive window. Values are not trimmed or converted.</p>}
      {snapshot.connection !== "connected" && <p role="status">{snapshot.connection === "unsupported" ? "Exact EPS decoding is unavailable in this browser or origin." : "Connect to the local API in Settings to read EPS."}</p>}
      {error && <div className="error-state" role="alert" id={error.apiCode === "invalid_request" ? "eps-input-error" : undefined}>{guidance(error)}</div>}
      {loading && <EmptyState title="Reading upcoming EPS" message="Wait for the response or cancel this read." />}
      {!data && !loading && !error && <EmptyState title={cancelled ? "EPS read cancelled" : "EPS not loaded"} message="Enter a symbol and dates, then choose Read upcoming EPS." />}
    </section>
    {data && <section className="panel" aria-labelledby="eps-result-title"><h2 id="eps-result-title">Returned upcoming EPS observations</h2>
      <p role="status">Provider symbol: {data.provider_symbol}. Requested release dates: {data.start} to {data.end}. Server UTC reference day: {data.analysis_date}.</p>
      <p>Provider: {data.provider}. Source: earnings_calendar. Source field: epsEstimate. Accounting basis: non-GAAP. Units: currency-per-share.</p>
      <p>Currency: unknown. Basic/diluted share basis: unknown. Publication/forecast vintage: unknown. Fiscal period end: unknown.</p>
      <p>UTC receipt time records retrieval, not forecast publication or historical availability. Release dates are vendor labels; session codes bmo/amc/dmh are displayed without an inferred timezone.</p>
      <p>Coverage: not asserted. These observations do not establish financial comparability, growth, TTM EPS or screening matches.</p>
      {data.observations.length === 0 ? <EmptyState title="No observations returned" message="This is not proof of an invalid symbol, complete coverage or no upcoming earnings. Missing data is never zero." /> :
        <DataTable caption="Exact upcoming non-GAAP EPS / unknown currency" columns={columns} rows={data.observations} rowKey={row => `${row.fiscal_year}:${row.fiscal_quarter}`} emptyMessage="No observations returned." />}
    </section>}
  </>;
}
