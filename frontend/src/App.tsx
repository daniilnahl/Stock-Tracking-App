import { useState } from "react";
import { decode, supportsExactJSON } from "./services/validation";

// This foundation screen makes no HTTP calls and accepts no credentials.
// Real shell/watchlists/settings belong to their separately reviewed issues.
const sample = '{"stock":{"symbol":"DEMO","name":"Synthetic example","exchange":"NASDAQ"},"ordinal":0,"start":"2020-01-02","end":"2020-01-02","price_basis":"raw","provenance":{"source":null,"observed_at":null,"retrieved_at":null,"currency":null,"freshness":"unknown"},"bars":[{"symbol":"DEMO","date":"2020-01-02","open":"110.0000000000000000001","high":"120","low":"100","close":"110.0000000000000000001","adjusted_close":null,"volume":9223372036854775807}]}';
export function App() {
  const [state, setState] = useState<"idle" | "success" | "error">("idle");
  const exact = supportsExactJSON();
  const history = state === "success" && exact ? decode("HistoryResponse", sample) : null;
  return <main>
    <p className="eyebrow">Stock Tracking App / M8</p>
    <p className="demo-label">Synthetic client foundation demo - no live data</p>
    <h1>Exact values.<br />A solid foundation.</h1>
    <p className="intro">The typed API client is ready for the dashboard modules. This isolated demonstration reads a built-in test document. It never connects to a service.</p>
    <section aria-labelledby="connection-title" className="panel">
      <h2 id="connection-title">Client connection</h2>
      <p>Disconnected. No saved observations are loaded.</p>
      <p role="status">{exact ? "Exact JSON decoding is supported by this browser." : "This browser cannot decode exact API numbers. Use a current supported browser."}</p>
    </section>
    <section aria-labelledby="precision-title" className="panel">
      <h2 id="precision-title">Precision check</h2>
      <p>Check an isolated synthetic raw-history response without rounding its Decimal text or 64-bit volume.</p>
      <div className="actions">
        <button disabled={!exact} onClick={() => setState("success")}>Check synthetic response</button>
        <button onClick={() => setState("error")}>Show safe error state</button>
        <button onClick={() => setState("idle")}>Clear demonstration</button>
      </div>
      <div aria-live="polite">
        {state === "idle" && <p>No demonstration values loaded.</p>}
        {state === "error" && <p role="alert">The API response is incompatible. No data was published.</p>}
        {history && <dl>
          <div><dt>Raw close / currency unknown</dt><dd>{history.bars[0]?.close}</dd></div>
          <div><dt>Volume / shares</dt><dd>{history.bars[0]?.volume?.toString()}</dd></div>
          <div><dt>Freshness</dt><dd>Unknown - synthetic fixture</dd></div>
        </dl>}
      </div>
    </section>
    <p className="footnote">This is the client foundation for issue #143. Dashboard navigation, watchlists, themes and token entry follow in their own implementation issues. History remains disabled in production pending its separate rights gate.</p>
  </main>;
}
