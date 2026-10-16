import { useState } from "react";
import { Button, SettingsField } from "../components/primitives";
import { isTheme, themes } from "../themes/theme";
import type { ThemePreference } from "../themes/theme";
import { OverviewSummary, loadedOverviewList } from "./OverviewSummary";
import { useLocalSession } from "../app/session";
import { routeHref } from "../app/routes";
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
export function SavedObservations() {
  const { snapshot } = useLocalSession();
  const loaded = loadedOverviewList(snapshot);
  return <section className="panel overview-observations" aria-labelledby="saved-title">
    <div className="panel-heading"><div><p className="eyebrow">Saved observations</p><h2 id="saved-title">Saved watchlist access</h2></div></div>
    <SearchDisclosure />
    {loaded ? <><p>Loaded namespace: <span>{loaded.namespace}</span>.</p>
      <p>Saved list name: {loaded.name}</p>
      <p>This count covers only the loaded namespace. Overview makes no additional requests.</p></> :
      <p>No successful saved list is available for a count. Unavailable does not mean an empty list.</p>}
    <p>This overview does not duplicate holdings rows.</p>
    <a href={routeHref("watchlists")}>Browse saved watchlists</a>
    <p className="footnote">Source, observation time and retrieval time: unknown. Currency and freshness: unknown.</p>
    <p className="footnote">Both saved namespaces and duplicate rows remain distinct. Saved metadata does not establish currency or provenance.</p>
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
    <OverviewSummary />
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
