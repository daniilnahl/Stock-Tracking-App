// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen, within } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import { App } from "../src/App";
import { navigation, resolveRoute, routeHref } from "../src/app/routes";
import { themeStorageKey } from "../src/themes/theme";

beforeEach(() => {
  localStorage.clear();
  window.history.replaceState(null, "", "/");
  document.documentElement.removeAttribute("data-theme");
});
afterEach(cleanup);
function navigate(hash: string) {
  act(() => {
    window.history.replaceState(null, "", `/${hash}`);
    window.dispatchEvent(new HashChangeEvent("hashchange"));
  });
}
describe("typed navigation and approved shell", () => {
  it("has the central three-item navigation and safely rejects unknown routes", () => {
    expect(navigation.map(item => item.id)).toEqual(["overview", "watchlists", "settings"]);
    expect(routeHref("settings")).toBe("#settings");
    expect(resolveRoute("")).toBe("overview");
    expect(resolveRoute("#client-foundation")).toBe("client-foundation");
    expect(resolveRoute("#constructor")).toBeNull();
    expect(resolveRoute("#<img src=x>")).toBeNull();
    expect(resolveRoute("https://example.invalid")).toBeNull();
  });
  it("matches the approved two-placeholder/three-card order without inventing data", () => {
    render(<App />);
    expect(screen.getAllByRole("main")).toHaveLength(1);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(within(screen.getByRole("navigation")).getAllByRole("link").map(link => link.textContent)).toEqual(["Overview", "Watchlists", "Settings"]);
    const recommend = screen.getByRole("heading", { name: "Recommend stock of the day" });
    const taurus = screen.getByRole("heading", { name: "Taurus Agents Menu" });
    const cards = screen.getByLabelText("Workspace status");
    expect(recommend.compareDocumentPosition(taurus) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(taurus.compareDocumentPosition(cards) & Node.DOCUMENT_POSITION_FOLLOWING).toBeTruthy();
    expect(within(cards).getAllByRole("heading")).toHaveLength(3);
    expect(screen.getAllByText("Placeholder / unavailable")).toHaveLength(2);
    expect(screen.getByText("Not loaded")).toBeTruthy();
    expect(screen.queryByText("110.0000000000000000001")).toBeNull();
    expect(screen.queryByRole("textbox")).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("changes route/current item/title and moves focus to its single page heading", () => {
    render(<App />);
    navigate("#settings");
    const heading = screen.getByRole("heading", { level: 1, name: "Make yourself at home." });
    expect(document.activeElement).toBe(heading);
    expect(document.title).toBe("Settings - Stock Tracking App");
    expect(screen.getByRole("link", { name: "Settings" }).getAttribute("aria-current")).toBe("page");
    navigate("#watchlists");
    expect(document.activeElement).toBe(screen.getByRole("heading", { level: 1, name: "Saved watchlists" }));
    navigate("#client-foundation");
    expect(screen.getAllByRole("main")).toHaveLength(1);
    expect(screen.getAllByRole("heading", { level: 1 })).toHaveLength(1);
    expect(screen.getByText("Synthetic client foundation demo - no live data")).toBeTruthy();
    navigate("#unexpected");
    expect(screen.getByRole("heading", { level: 1, name: "Page unavailable" })).toBeTruthy();
    expect(screen.queryByText("unexpected")).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("skip link focuses main without changing the hash or route", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("link", { name: "Skip to content" }));
    expect(document.activeElement).toBe(screen.getByRole("main"));
    expect(window.location.hash).toBe("");
    expect(screen.getByRole("heading", { level: 1, name: "Your watchlists, clearly." })).toBeTruthy();
  });
  it("search/add only discloses unavailability and a fixed safe source-document link", () => {
    render(<App />);
    const search = screen.getByRole("button", { name: "Search / add stock" });
    expect(search.getAttribute("aria-expanded")).toBe("false");
    fireEvent.click(search);
    expect(search.getAttribute("aria-expanded")).toBe("true");
    expect(screen.getByText("Unavailable - backend search/add is not implemented.")).toBeTruthy();
    const source = screen.getByRole("link", { name: "Read the backend and frontend TO-DO LIST" });
    expect(source.getAttribute("href")).toBe("https://github.com/daniilnahl/Stock-Tracking-App/blob/main/docs/TO-DO-LIST.md");
    expect(source.getAttribute("rel")).toBe("noopener noreferrer");
    expect(screen.queryByRole("button", { name: "Save" })).toBeNull();
    fireEvent.click(search);
    expect(search.getAttribute("aria-expanded")).toBe("false");
    expect(fetch).not.toHaveBeenCalled();
  });
});
describe("only the validated local theme persists", () => {
  it.each([null, "", "auto", "<script>", "constructor"])("defaults to light for missing/invalid stored preference %s", value => {
    if (value !== null) localStorage.setItem(themeStorageKey, value);
    render(<App />);
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(screen.getByRole("button", { name: "Dark theme" }).hasAttribute("aria-pressed")).toBe(false);
  });
  it("restores dark and changes/persists only theme through button and labeled settings control", () => {
    localStorage.setItem(themeStorageKey, "dark");
    render(<App />);
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(screen.getByRole("button", { name: "Light theme" }).hasAttribute("aria-pressed")).toBe(false);
    fireEvent.click(screen.getByRole("button", { name: "Light theme" }));
    expect(localStorage.getItem(themeStorageKey)).toBe("light");
    navigate("#settings");
    const select = screen.getByRole("combobox", { name: "Theme" });
    expect(document.getElementById(select.getAttribute("aria-describedby")!)?.textContent).toContain("Only this theme preference");
    fireEvent.change(select, { target: { value: "dark" } });
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(Object.keys(localStorage)).toEqual([themeStorageKey]);
    cleanup(); render(<App />);
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(screen.getByRole("combobox", { name: "Theme" }).getAttribute("aria-describedby")).toBeTruthy();
  });
  it("blocked storage reads fail to light with an honest page-only notice", () => {
    vi.spyOn(Storage.prototype, "getItem").mockImplementation(() => { throw new DOMException("Blocked", "SecurityError"); });
    render(<App />);
    expect(document.documentElement.dataset.theme).toBe("light");
    expect(screen.getByRole("status").textContent).toContain("Theme preference storage is unavailable");
  });
  it("blocked writes still switch themes without claiming persistence", () => {
    vi.spyOn(Storage.prototype, "setItem").mockImplementation(() => { throw new DOMException("Quota", "QuotaExceededError"); });
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Dark theme" }));
    expect(document.documentElement.dataset.theme).toBe("dark");
    expect(screen.getByRole("status").textContent).toContain("could not be saved");
  });
  it("accepts local-storage updates, ignores session storage and resets cleared/invalid preferences", () => {
    render(<App />);
    const event = (storageArea: Storage, newValue: string | null) => new StorageEvent("storage", { storageArea, key: themeStorageKey, newValue });
    act(() => window.dispatchEvent(event(sessionStorage, "dark")));
    expect(document.documentElement.dataset.theme).toBe("light");
    act(() => window.dispatchEvent(event(localStorage, "dark")));
    expect(document.documentElement.dataset.theme).toBe("dark");
    act(() => window.dispatchEvent(event(localStorage, "invalid")));
    expect(document.documentElement.dataset.theme).toBe("light");
    act(() => window.dispatchEvent(event(localStorage, null)));
    expect(document.documentElement.dataset.theme).toBe("light");
  });
});
