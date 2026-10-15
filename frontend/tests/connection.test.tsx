// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";
import { ApiClient } from "../src/services/client";
import { deferred, response, watchlist } from "./fixtures";

// Deterministically generated at runtime, never a real or embedded credential.
function credential(offset = 0) {
  return Array.from({ length: 48 }, (_, index) => String.fromCharCode(65 + (index * 7 + offset) % 26)).join("");
}
function mount(fetcher = vi.fn(async (_url: string, _init: RequestInit) => response(watchlist()))) {
  const client = new ApiClient({ origin: "http://127.0.0.1:8000", fetch: fetcher });
  const createClient = vi.fn(() => client);
  const view = render(<App createClient={createClient} />);
  return { client, createClient, fetcher, view };
}
function field() { return screen.getByLabelText("Local API token") as HTMLInputElement; }
function submit(value: string) {
  fireEvent.input(field(), { target: { value } });
  fireEvent.submit(field().form!);
}
function navigate(hash: string) {
  act(() => { window.history.replaceState(null, "", `/${hash}`); window.dispatchEvent(new HashChangeEvent("hashchange")); });
}
beforeEach(() => { localStorage.clear(); sessionStorage.clear(); window.history.replaceState(null, "", "/#settings"); });
afterEach(cleanup);

describe("masked memory-only connection controls", () => {
  it("uses a labeled native masked input with description, and never makes an implicit request", () => {
    const { client, fetcher } = mount();
    const input = field();
    expect(input.type).toBe("password");
    expect(input.getAttribute("autocomplete")).toBe("off");
    expect(input.hasAttribute("maxlength")).toBe(false);
    expect(input.form?.noValidate).toBe(true);
    expect(document.getElementById(input.getAttribute("aria-describedby")!)?.textContent).toContain("only in page memory");
    expect(input.value.length === 0).toBe(true);
    expect(client.getSnapshot().connection).toBe("disconnected");
    expect(fetcher.mock.calls.length === 0).toBe(true);
    expect(screen.getByRole("button", { name: "Disconnect" }).hasAttribute("disabled")).toBe(true);
  });
  it("configures only, clears the field and publishes no authentication success or credential", () => {
    const { client, fetcher } = mount();
    const transient = credential();
    submit(transient);
    expect(field().value.length === 0).toBe(true);
    expect(client.getSnapshot().connection).toBe("connected");
    expect(screen.getByText("Configured")).toBeTruthy();
    expect(screen.getByText("Authentication is not verified. Configuring this page does not request or load private data.")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Replace connection" })).toBeTruthy();
    expect(document.body.textContent?.includes(transient)).toBe(false);
    expect(document.documentElement.outerHTML.includes(transient)).toBe(false);
    expect(JSON.stringify(client.getSnapshot()).includes(transient)).toBe(false);
    expect(Object.keys(localStorage)).toEqual([]);
    expect(Object.keys(sessionStorage)).toEqual([]);
    expect(window.location.href.includes(transient)).toBe(false);
    expect(fetcher.mock.calls.length === 0).toBe(true);
  });
  it.each(["", "short", "leading", "trailing", "oversize"])("rejects %s input without trimming/truncating or retaining a draft", kind => {
    const { client, fetcher } = mount();
    const valid = credential();
    const supplied = kind === "leading" ? ` ${valid}` : kind === "trailing" ? `${valid}\n` : kind === "oversize" ? valid.repeat(8) : kind === "short" ? valid.slice(0, 8) : "";
    // Text controls normalize line breaks natively; test a trailing ASCII space
    // through the real DOM while client unit tests independently cover LF/CRLF.
    submit(kind === "trailing" ? `${valid} ` : supplied);
    expect(field().value.length === 0).toBe(true);
    expect(client.getSnapshot().connection).toBe("disconnected");
    expect(screen.getByRole("alert").textContent === "Request input is invalid.").toBe(true);
    expect(field().getAttribute("aria-invalid")).toBe("true");
    expect(document.activeElement).toBe(field());
    expect(document.body.textContent?.includes(valid)).toBe(false);
    expect(fetcher.mock.calls.length === 0).toBe(true);
  });
  it("retries with new input after a fixed error and suppresses unexpected exception text", () => {
    const { client } = mount();
    const transient = credential();
    vi.spyOn(client, "connect").mockImplementationOnce(() => { throw new Error(transient); });
    submit(transient);
    expect(screen.getByRole("alert").textContent === "The local API could not complete the request.").toBe(true);
    expect(document.body.textContent?.includes(transient)).toBe(false);
    submit(credential(1));
    expect(screen.queryByRole("alert")).toBeNull();
    expect(client.getSnapshot().connection).toBe("connected");
    expect(field().value.length === 0).toBe(true);
  });
  it("uses one App-owned client across theme/route changes, while drafts are discarded", () => {
    const { client, createClient, fetcher } = mount();
    submit(credential());
    fireEvent.input(field(), { target: { value: credential(1) } });
    navigate("#overview");
    expect(screen.getByText("Configured")).toBeTruthy();
    expect(screen.getByText("Authentication is not verified.")).toBeTruthy();
    fireEvent.click(screen.getByRole("button", { name: "Dark theme" }));
    navigate("#settings");
    expect(field().value.length === 0).toBe(true);
    expect(client.getSnapshot().connection).toBe("connected");
    expect(createClient).toHaveBeenCalledTimes(1);
    expect(Object.keys(localStorage)).toEqual(["stock-tracker.theme"]);
    expect(fetcher.mock.calls.length === 0).toBe(true);
  });
  it("disconnect clears draft/private state, returns focus, and never reconnects implicitly", async () => {
    const { client, fetcher } = mount();
    submit(credential());
    await act(async () => { await client.loadWatchlist("menu_watchlist"); });
    fireEvent.input(field(), { target: { value: credential(1) } });
    fireEvent.click(screen.getByRole("button", { name: "Disconnect" }));
    expect(client.getSnapshot()).toMatchObject({ connection: "disconnected", watchlist: { status: "idle" }, history: { status: "idle" }, selection: null });
    expect(field().value.length === 0).toBe(true);
    expect(document.activeElement).toBe(field());
    navigate("#overview"); navigate("#settings");
    expect(client.getSnapshot().connection).toBe("disconnected");
    expect(fetcher.mock.calls.length === 1).toBe(true); // Only the explicitly injected test read.
    expect(screen.queryByText("Synthetic only")).toBeNull();
  });
  it("pagehide clears the session/draft and cached-page restoration remains disconnected", () => {
    const { client } = mount();
    submit(credential());
    fireEvent.input(field(), { target: { value: credential(1) } });
    act(() => window.dispatchEvent(new PageTransitionEvent("pagehide", { persisted: true })));
    expect(field().value.length === 0).toBe(true);
    expect(client.getSnapshot().connection).toBe("disconnected");
    act(() => window.dispatchEvent(new PageTransitionEvent("pageshow", { persisted: true })));
    expect(client.getSnapshot().connection).toBe("disconnected");
    expect(screen.getByRole("button", { name: "Configure connection" })).toBeTruthy();
  });
  it("unmount clears the old session and a new app mount starts empty", () => {
    const { client, view } = mount();
    submit(credential());
    view.unmount();
    expect(client.getSnapshot().connection).toBe("disconnected");
    const replacement = mount();
    expect(replacement.client.getSnapshot().connection).toBe("disconnected");
    expect(field().value.length === 0).toBe(true);
  });
});
describe("shared-session lifecycle with controlled existing client reads", () => {
  it.each(["disconnect", "unauthorized"])("external %s clears a replacement draft before disconnected UI", async action => {
    const fetcher = vi.fn(async () => new Response(null, { status: 401 }));
    const { client } = mount(fetcher);
    submit(credential());
    fireEvent.input(field(), { target: { value: credential(1) } });
    await act(async () => {
      if (action === "disconnect") client.disconnect();
      else await client.loadWatchlist("menu_watchlist").catch(() => undefined);
    });
    expect(field().value.length === 0).toBe(true);
    expect(client.getSnapshot()).toMatchObject({ connection: "disconnected", watchlist: { status: "idle" }, history: { status: "idle" }, selection: null });
    expect(screen.getByText("No local API token is held by this page.")).toBeTruthy();
  });
  it.each(["replace", "disconnect", "pagehide"])("%s aborts pending work and suppresses an ignored late response", async action => {
    const delayed = deferred<Response>();
    const fetcher = vi.fn((_url: string, _init: RequestInit) => delayed.promise);
    const { client } = mount(fetcher);
    submit(credential());
    let cancelled: Promise<unknown>;
    await act(async () => { cancelled = client.loadWatchlist("menu_watchlist").catch(error => error.code); await Promise.resolve(); });
    if (action === "replace") submit(credential(1));
    else if (action === "disconnect") fireEvent.click(screen.getByRole("button", { name: "Disconnect" }));
    else act(() => window.dispatchEvent(new PageTransitionEvent("pagehide")));
    expect(await cancelled!).toBe("cancelled");
    expect(fetcher.mock.calls[0]?.[1].signal?.aborted).toBe(true);
    await act(async () => { delayed.resolve(response(watchlist())); await Promise.resolve(); });
    expect(client.getSnapshot().watchlist.status).toBe("idle");
    expect(screen.queryByText("Synthetic only")).toBeNull();
    expect(client.getSnapshot().connection).toBe(action === "replace" ? "connected" : "disconnected");
  });
  it("authentication failure clears the shared session without echoing response content", async () => {
    const transient = credential();
    const fetcher = vi.fn(async () => new Response(transient, { status: 401 }));
    const { client } = mount(fetcher);
    submit(transient);
    await act(async () => { await client.loadWatchlist("menu_watchlist").catch(() => undefined); });
    expect(client.getSnapshot()).toMatchObject({ connection: "disconnected", watchlist: { status: "idle" }, history: { status: "idle" }, selection: null });
    expect(screen.getByText("Disconnected")).toBeTruthy();
    expect(screen.getByRole("button", { name: "Configure connection" })).toBeTruthy();
    expect(field().value.length === 0).toBe(true);
    expect(document.documentElement.outerHTML.includes(transient)).toBe(false);
    expect(Object.keys(localStorage)).toEqual([]);
  });
});
