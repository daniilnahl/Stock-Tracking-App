import { useState } from "react";
import { Button, DataTable, SettingsField } from "../components/primitives";
import type { Column } from "../components/primitives";
import { isTheme, themes } from "../themes/theme";
import type { ThemePreference } from "../themes/theme";
import { connectionLabel, useLocalSession } from "../app/session";
import { ConnectionSettings } from "./ConnectionSettings";

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
    <DataTable caption="Saved observations - not loaded" columns={columns} rows={[]} rowKey={row => row.id}
      emptyMessage="Open Watchlists to explicitly read saved entries. This overview does not display holdings." />
    <p className="footnote">Both saved namespaces and duplicate rows remain distinct. Currency and freshness require explicit evidence.</p>
  </section>;
}
export function OverviewPage() {
  const { snapshot } = useLocalSession();
  return <>
    <div className="feature-placeholders">
      <section className="panel" aria-labelledby="recommend-title"><p className="eyebrow">Placeholder / unavailable</p>
        <h2 id="recommend-title">Recommend stock of the day</h2><p>Reserved for future research. No recommendation service is connected.</p></section>
      <section className="panel" aria-labelledby="taurus-title"><p className="eyebrow">Placeholder / unavailable</p>
        <h2 id="taurus-title">Taurus Agents Menu</h2><p>Reserved for future agent controls. No agents are configured or running.</p></section>
    </div>
    <div className="cards" aria-label="Workspace status">
      <section className="card"><h2 className="eyebrow">Connection</h2><p className="value">{connectionLabel(snapshot)}</p><p>{snapshot.connection === "connected" ? "Configuration alone does not verify authentication." : "No local API connection is configured in this page."}</p></section>
      <section className="card"><h2 className="eyebrow">Saved entries</h2><p className="value">Open Watchlists</p><p>Read saved entries explicitly on the Watchlists page.</p></section>
      <section className="card"><h2 className="eyebrow">Observation status</h2><p className="value">Unknown</p><p>Saved prices do not establish freshness.</p></section>
    </div>
    <SavedObservations />
  </>;
}
export function SettingsPage({ preference }: { preference: ThemePreference }) {
  return <><section className="panel" aria-labelledby="appearance-title"><h2 id="appearance-title">Appearance</h2>
    <SettingsField label="Theme" hint="Only this theme preference is saved in this browser. Light is the default.">
      {attributes => <select {...attributes} value={preference.theme} onChange={event => {
        if (isTheme(event.target.value)) preference.setTheme(event.target.value);
      }}>{Object.entries(themes).map(([id, theme]) => <option key={id} value={id}>{theme.name}</option>)}</select>}
    </SettingsField>
    <p>Pixel lettering applies to headings, body text, navigation, tables and controls.</p>
  </section><ConnectionSettings /></>;
}
