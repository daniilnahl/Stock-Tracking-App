import "./overview.css";
import { routeHref } from "../app/routes";
import { connectionLabel, useLocalSession } from "../app/session";
import type { ClientSnapshot } from "../services/client";

const namespaceNames = {
  menu_watchlist: "Menu watchlist",
  daniils_stock_method: "Daniil's stock method",
} as const;

// Only the last validated success for the snapshot's own namespace is evidence.
export function loadedOverviewList(snapshot: ClientSnapshot) {
  return snapshot.connection === "connected" && snapshot.watchlist.status === "success" &&
    snapshot.namespace === snapshot.watchlist.data.namespace ? snapshot.watchlist.data : null;
}

export function OverviewSummary() {
  const { snapshot } = useLocalSession();
  const loaded = loadedOverviewList(snapshot);
  const countHint = loaded ? `Rows in ${namespaceNames[loaded.namespace]}. Duplicate entries count separately.` :
    snapshot.connection === "unsupported" ? "Saved reads are unsupported in this session." :
      snapshot.connection !== "connected" ? "No saved list is available while disconnected." :
        snapshot.watchlist.status === "loading" ? "A saved read is in progress. No count is available." :
          snapshot.watchlist.status === "error" ? "The saved read failed. No count is available." :
            "Explicitly read one saved namespace in Watchlists to see its entry count.";
  return <>
    <div className="cards" aria-label="Workspace status">
      <section className="card"><h2 className="eyebrow">Connection</h2>
        <p className="value">{connectionLabel(snapshot)}</p>
        <p>{snapshot.connection === "connected" ? "Configuration alone does not verify authentication." :
          snapshot.connection === "unsupported" ? "Saved reads are unsupported in this session." : "No local API connection is configured in this page."}</p>
      </section>
      <section className="card" aria-labelledby="overview-count-title">
        <h2 className="eyebrow" id="overview-count-title">Saved entries</h2>
        <p className="value" role="status" aria-atomic="true" aria-label={loaded ? `Saved entry count for ${namespaceNames[loaded.namespace]}` : "Saved entry count unavailable"}>{loaded ? loaded.entries.length : "Unavailable"}</p>
        <p>{countHint}</p><a href={routeHref("watchlists")}>Open Watchlists</a>
      </section>
      <section className="card"><h2 className="eyebrow">Observation status</h2>
        <p className="value">Unknown</p><p>Saved prices do not establish freshness.</p>
      </section>
    </div>
  </>;
}
