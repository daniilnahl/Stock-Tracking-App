import { useState } from "react";
import { Button, DataTable, EmptyState, SettingsField } from "../components/primitives";
import type { Column } from "../components/primitives";
import { isTheme, themes } from "../themes/theme";
import type { ThemePreference } from "../themes/theme";

const todoURL = "https://github.com/daniilnahl/Stock-Tracking-App/blob/main/docs/TO-DO-LIST.md";
export function SearchDisclosure() {
  const [expanded, setExpanded] = useState(false);
  return <><Button aria-expanded={expanded} aria-controls="search-note" onClick={() => setExpanded(!expanded)}>Search / add stock</Button>
    <div id="search-note" className="search-note" hidden={!expanded}>
      <p className="state-title">Unavailable - backend search/add is not implemented.</p>
      <p>This control will open stock search once the backend supports it. No search or save request is sent.</p>
      <a href={todoURL} target="_blank" rel="noopener noreferrer">Read the backend and frontend TO-DO LIST</a>
    </div></>;
}
type EmptyRow = { id: number; security: string; quantity: string; price: string; observation: string };
const columns: readonly Column<EmptyRow>[] = [
  { id: "security", header: "Security", render: row => row.security },
  { id: "quantity", header: "Quantity / shares", render: row => row.quantity, numeric: true },
  { id: "price", header: "Saved price", render: row => row.price, numeric: true },
  { id: "observation", header: "Observation", render: row => row.observation },
];
export function SavedObservations() {
  return <section className="panel" aria-labelledby="saved-title">
    <div className="panel-heading"><div><p className="eyebrow">Saved observations</p><h2 id="saved-title">Menu watchlist</h2></div></div>
    <SearchDisclosure />
    <DataTable caption="Saved observations - not connected" columns={columns} rows={[]} rowKey={row => row.id}
      emptyMessage="Connect to read saved entries. No sample prices are presented as live data." />
    <p className="footnote">Both saved namespaces and duplicate rows remain distinct. Currency and freshness require explicit evidence.</p>
  </section>;
}
export function OverviewPage() {
  return <>
    <div className="feature-placeholders">
      <section className="panel" aria-labelledby="recommend-title"><p className="eyebrow">Placeholder / unavailable</p>
        <h2 id="recommend-title">Recommend stock of the day</h2><p>Reserved for future research. No recommendation service is connected.</p></section>
      <section className="panel" aria-labelledby="taurus-title"><p className="eyebrow">Placeholder / unavailable</p>
        <h2 id="taurus-title">Taurus Agents Menu</h2><p>Reserved for future agent controls. No agents are configured or running.</p></section>
    </div>
    <div className="cards" aria-label="Workspace status">
      <section className="card"><h2 className="eyebrow">Connection</h2><p className="value">Disconnected</p><p>No local API connection is configured in this shell.</p></section>
      <section className="card"><h2 className="eyebrow">Saved entries</h2><p className="value">Not loaded</p><p>Available after an authenticated read.</p></section>
      <section className="card"><h2 className="eyebrow">Observation status</h2><p className="value">Unknown</p><p>Saved prices do not establish freshness.</p></section>
    </div>
    <SavedObservations />
  </>;
}
export function WatchlistsPage() {
  return <><EmptyState title="Not connected" message="Saved watchlist loading follows in the watchlist module. This shell makes no API requests." /><SavedObservations /></>;
}
export function SettingsPage({ preference }: { preference: ThemePreference }) {
  return <><section className="panel" aria-labelledby="appearance-title"><h2 id="appearance-title">Appearance</h2>
    <SettingsField label="Theme" hint="Only this theme preference is saved in this browser. Light is the default.">
      {attributes => <select {...attributes} value={preference.theme} onChange={event => {
        if (isTheme(event.target.value)) preference.setTheme(event.target.value);
      }}>{Object.entries(themes).map(([id, theme]) => <option key={id} value={id}>{theme.name}</option>)}</select>}
    </SettingsField>
    <p>Pixel lettering applies to headings, body text, navigation, tables and controls.</p>
  </section><section className="panel" aria-labelledby="connection-title"><h2 id="connection-title">Local API connection</h2>
    <EmptyState title="Not connected" message="Connection and token entry follow in the settings module. No token is collected or saved by this shell." /></section></>;
}
