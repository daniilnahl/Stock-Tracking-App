import { useEffect, useId, useLayoutEffect, useRef, useState } from "react";
import type { FormEvent } from "react";
import { connectionLabel, useLocalSession } from "../app/session";
import { Button } from "../components/primitives";
import { ClientError } from "../services/validation";

export function ConnectionSettings() {
  const { client, snapshot } = useLocalSession();
  const input = useRef<HTMLInputElement>(null);
  const [error, setError] = useState<ClientError | null>(null);
  const id = useId();
  const configured = snapshot.connection === "connected";
  useLayoutEffect(() => {
    // Authentication failure or an external disconnect must clear replacement
    // drafts before painting the disconnected state. Preserve fixed errors.
    if (!configured && input.current) input.current.value = "";
  }, [configured]);
  useEffect(() => {
    const field = input.current;
    const clearDraft = () => { if (field) field.value = ""; };
    clearDraft();
    window.addEventListener("pagehide", clearDraft);
    return () => { clearDraft(); window.removeEventListener("pagehide", clearDraft); };
  }, []);
  const configure = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    const field = input.current;
    if (!field) return;
    const credential = field.value;
    field.value = "";
    setError(null);
    try { client.connect(credential); }
    catch (failure) {
      // Only fixed client diagnostics; no supplied text or raw exception is echoed.
      setError(failure instanceof ClientError ? failure : new ClientError("api_error"));
      field.focus();
    }
  };
  const disconnect = () => {
    if (input.current) input.current.value = "";
    setError(null);
    client.disconnect();
    input.current?.focus();
  };
  return <section className="panel" aria-labelledby="connection-title">
    <h2 id="connection-title">Local API connection</h2>
    <div className="connection-status" role="status" aria-live="polite" aria-atomic="true">
      <p className="state-title">{connectionLabel(snapshot)}</p>
      <p>{configured ? "Authentication is not verified. Configuring this page does not request or load private data." :
        snapshot.connection === "unsupported" ? "This page cannot use the local API. Use a supported browser on the local API page, then configure again." :
          "No local API token is held by this page."}</p>
    </div>
    <p>The API address is this local page's origin. Provider credentials remain on the server.</p>
    <form onSubmit={configure} noValidate autoComplete="off">
      <div className="settings-field"><label htmlFor={id}>Local API token</label>
        <input ref={input} id={id} type="password" autoComplete="off" autoCapitalize="none" spellCheck={false}
          aria-describedby={`${id}-hint${error ? ` ${id}-error` : ""}`} aria-invalid={error ? true : undefined}
          required onInput={() => { if (error) setError(null); }} />
        <p className="field-hint" id={`${id}-hint`}>Enter the existing local API token. It stays only in page memory and is cleared from this field after every submission.</p>
      </div>
      {error && <p className="error-state" id={`${id}-error`} role="alert">{error.message}</p>}
      <div className="actions"><Button type="submit">{configured ? "Replace connection" : "Configure connection"}</Button>
        <Button disabled={!configured} onClick={disconnect}>Disconnect</Button></div>
    </form>
    <p className="footnote">Disconnect or reload clears this page's token and private response state. Only the theme preference is saved locally. No verification request is sent by these controls.</p>
  </section>;
}
