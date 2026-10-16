import { useEffect, useLayoutEffect, useRef, useState } from "react";
import { useLocalSession } from "../app/session";
import { routeHref } from "../app/routes";
import { Button, DataTable, EmptyState, ErrorState, SettingsField } from "../components/primitives";
import type { Column } from "../components/primitives";
import type { EntryResponse } from "../services/contracts.generated";
import { ClientError, validNamespace } from "../services/validation";
import type { Namespace } from "../services/validation";
import { SearchDisclosure } from "./ShellPages";
import { StoredRowDetail } from "./StoredRowDetail";

const namespaces: Readonly<Record<Namespace, string>> = {
  menu_watchlist: "Menu watchlist",
  daniils_stock_method: "Daniil's stock method",
};
const columns: readonly Column<EntryResponse>[] = [
  { id: "ordinal", header: "Request-local row ordinal", numeric: true, render: row => row.ordinal },
  { id: "security", header: "Security", render: row => <><strong>{row.stock.symbol}</strong><div>{row.stock.name ?? "Name unavailable"}</div><div>{row.stock.exchange ?? "Exchange unavailable"}</div></> },
  { id: "quantity", header: "Quantity / shares", numeric: true, render: row => row.quantity },
  { id: "ownership", header: "Ownership", render: row => row.average_cost === null ? "Unowned" : "Owned" },
  { id: "cost", header: "Average cost / per share", numeric: true, render: row => row.average_cost ?? "Not applicable (unowned)" },
  { id: "price", header: "Saved price / per share", numeric: true, render: row => row.current_price ?? "Unavailable" },
];

export function WatchlistsPage() {
  const { client, snapshot } = useLocalSession();
  const [namespace, setNamespace] = useState<Namespace>(() => snapshot.namespace ?? "menu_watchlist");
  const [showResource, setShowResource] = useState(true);
  const [failure, setFailure] = useState<ClientError | null>(null);
  const [cancelled, setCancelled] = useState(false);
  const [opening, setOpening] = useState(false);
  const request = useRef<AbortController | null>(null);
  const controls = useRef<HTMLDivElement>(null);
  const namespaceControl = useRef<HTMLSelectElement>(null);
  const attempt = useRef(0);
  const configured = snapshot.connection === "connected";
  const resource = showResource && snapshot.namespace === namespace ? snapshot.watchlist : null;
  const loading = configured && resource?.status === "loading";
  useEffect(() => () => { attempt.current++; request.current?.abort(); client.clearSelection(); }, [client]);
  useEffect(() => { if (configured) setFailure(null); }, [configured]);
  useLayoutEffect(() => { if (cancelled) controls.current?.querySelector<HTMLButtonElement>("button")?.focus(); }, [cancelled]);
  const abandon = () => {
    attempt.current++;
    request.current?.abort();
    request.current = null;
  };
  const read = async () => {
    abandon();
    const current = attempt.current;
    const controller = new AbortController();
    request.current = controller;
    client.clearSelection();
    setOpening(false);
    setShowResource(true);
    setFailure(null);
    setCancelled(false);
    try { await client.loadWatchlist(namespace, { signal: controller.signal }); }
    catch (error) {
      if (current !== attempt.current) return;
      const safe = error instanceof ClientError ? error : new ClientError("api_error");
      // Explicit Cancel owns its notice/focus. Session resets must not present
      // obsolete work as a user cancellation or move focus in a new session.
      if (safe.code !== "cancelled") setFailure(safe);
    } finally { if (current === attempt.current) request.current = null; }
  };
  const open = async (row: EntryResponse) => {
    abandon(); client.clearSelection();
    const current = attempt.current;
    const controller = new AbortController();
    request.current = controller;
    setShowResource(true); setFailure(null); setCancelled(false); setOpening(true);
    try { await client.selectRow(namespace, row.ordinal, row.stock, { signal: controller.signal }); }
    catch (error) {
      if (current === attempt.current) {
        const safe = error instanceof ClientError ? error : new ClientError("api_error");
        if (safe.code !== "cancelled") { setFailure(safe); namespaceControl.current?.focus(); }
      }
    } finally { if (current === attempt.current) { request.current = null; setOpening(false); } }
  };
  const close = () => { abandon(); client.clearSelection(); setOpening(false); namespaceControl.current?.focus(); };
  const error = failure ?? (resource?.status === "error" ? resource.error : null);
  const data = configured && resource?.status === "success" ? resource.data : null;
  const selection = snapshot.selection?.namespace === namespace && data ? snapshot.selection : null;
  const selectedEntry = selection ? data?.entries[selection.ordinal] : null;
  return <section className="panel" aria-labelledby="watchlist-title">
    <div className="panel-heading"><div><p className="eyebrow">Saved observations / read only</p><h2 id="watchlist-title">Browse a saved watchlist</h2></div></div>
    <SettingsField label="Saved namespace" hint="These are separate saved lists. Changing the selection does not request data.">
      {attributes => <select {...attributes} ref={namespaceControl} value={namespace} onChange={event => {
        if (!validNamespace(event.target.value)) return;
        abandon(); client.clearSelection(); setOpening(false); setNamespace(event.target.value); setShowResource(false); setFailure(null); setCancelled(false);
      }}>{Object.entries(namespaces).map(([id, name]) => <option key={id} value={id}>{name}</option>)}</select>}
    </SettingsField>
    <p className="footnote">Namespace: <span>{namespace}</span>. Read or reload only re-reads saved data. It does not fetch quotes, change holdings or establish current prices.</p>
    <div className="actions" ref={controls}><Button disabled={!configured || loading} onClick={() => { void read(); }}>{data ? "Reload saved entries" : "Read saved entries"}</Button>
      {loading && <Button onClick={() => { abandon(); client.clearSelection(); setOpening(false); setCancelled(true); }}>{opening ? "Cancel opening detail" : "Cancel read"}</Button>}
      <SearchDisclosure /></div>
    {error && <ErrorState error={error} {...(configured && !loading ? { onRetry: () => {
      // Retry disappears when loading starts; retain a meaningful keyboard target.
      namespaceControl.current?.focus(); void read();
    } } : {})} />}
    {error?.apiCode === "legacy_state_present" && <p>Legacy saved state needs a separate, approved migration before it can be read here.</p>}
    {!configured && <EmptyState title={snapshot.connection === "unsupported" ? "Saved reads unsupported" : "Saved reads disconnected"}
      message={snapshot.connection === "unsupported" ? "Use a supported browser at the local API origin, then configure again." : "Configure a memory-only connection in Settings before explicitly reading a saved list."} />}
    {!configured && <a href={routeHref("settings")}>Open connection settings</a>}
    {loading && <EmptyState title={opening ? "Re-reading saved row before detail" : "Reading saved entries"} message="The previous table and detail are cleared while this read is pending." />}
    {configured && !loading && !data && !error && <EmptyState title={cancelled ? "Saved read cancelled" : "Saved entries not loaded"}
      message="Choose Read saved entries when ready. No request is made automatically." />}
    {data && <><h3>{data.name}</h3><p className="state-title" role="status">Saved read complete. These observations are not live quotes.</p>
      <DataTable caption={`${namespaces[namespace]} / saved entries`} columns={[...columns, { id: "detail", header: "Stored row", render: row => <Button onClick={() => { void open(row); }}>Open detail for row {row.ordinal}</Button> }]} rows={data.entries}
        rowKey={row => `${namespace}:${row.ordinal}`} emptyMessage="This saved watchlist has no entries." />
      <p className="footnote">Rows retain saved order, including duplicates. Row ordinals belong only to this response; they are not permanent security IDs.</p></>}
    <p className="footnote">Currency: unknown for both costs and prices. Source, observation time and retrieval time: unknown. Freshness: unknown. Saved metadata does not establish currency or provenance. Exact decimal text is displayed without rounding; zero is distinct from unavailable or unowned.</p>
    {selection && selectedEntry && <StoredRowDetail key={selection.revision} entry={selectedEntry} selection={selection} onClose={close} />}
  </section>;
}
