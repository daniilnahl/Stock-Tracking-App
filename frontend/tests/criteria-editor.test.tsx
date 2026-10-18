// @vitest-environment jsdom
import { act, cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, beforeEach, describe, expect, it } from "vitest";
import { App } from "../src/App";

beforeEach(() => { localStorage.clear(); sessionStorage.clear(); window.history.replaceState(null, "", "/#stock-criteria"); });
afterEach(cleanup);
function change(label: string, value: string) { fireEvent.change(screen.getByLabelText(label), { target: { value } }); }
function navigate(hash: string) { act(() => { window.history.replaceState(null, "", `/${hash}`); window.dispatchEvent(new HashChangeEvent("hashchange")); }); }
function range() { change("Parameter name 1", "User EPS request"); change("Units and context 1", "User-specified currency/share, period and basis unresolved"); change("Minimum 1 (inclusive)", "-0.2500"); change("Maximum 1 (inclusive)", "1.250000000000000001"); }
describe("tab-memory custom criteria editor", () => {
  it("starts blank, prepares exact custom values and never connects or searches", () => {
    render(<App />);
    expect(screen.getByText("Your criteria stay in this tab and clear on reload. No API connection is needed.")).toBeTruthy();
    expect(screen.queryByText(/Configuration alone does not verify authentication/)).toBeNull();
    expect(screen.queryByText(/Saved observations are not current quotes/)).toBeNull();
    expect((screen.getByLabelText("Parameter name 1") as HTMLInputElement).value).toBe("");
    range();
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    expect(screen.getByRole("heading", { name: "Prepared — Taurus search unavailable" })).toBeTruthy();
    const snapshot = JSON.parse(screen.getByLabelText("Prepared criteria snapshot").textContent!);
    expect(snapshot.criteria[0]).toEqual({ parameter: "User EPS request", kind: "range", unit: "User-specified currency/share, period and basis unresolved", minimum: "-0.2500", maximum: "1.250000000000000001" });
    expect(fetch).not.toHaveBeenCalled();
    expect(Object.keys(localStorage)).toEqual([]);
    expect(Object.keys(sessionStorage)).toEqual([]);
    expect(screen.queryByRole("button", { name: /search/i })).toBeNull();
  });
  it("focuses the first error and associates field-level errors", () => {
    render(<App />);
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    const parameter = screen.getByLabelText("Parameter name 1");
    expect(document.activeElement).toBe(parameter);
    expect(parameter.getAttribute("aria-invalid")).toBe("true");
    expect(document.getElementById(parameter.getAttribute("aria-describedby")!)?.textContent).toContain("parameter name");
    expect(screen.getByRole("alert").textContent).toContain("not prepared");
    range(); change("Minimum 1 (inclusive)", "2");
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    expect(document.activeElement).toBe(screen.getByLabelText("Minimum 1 (inclusive)"));
    expect(screen.getByText("Minimum must be less than or equal to maximum.")).toBeTruthy();
  });
  it("renders custom malicious-looking labels and requirements as text", () => {
    render(<App />);
    change("Parameter name 1", "__proto__"); change("Criterion type 1", "text");
    change("Text requirement 1", "<img src=x onerror=alert(1)> Please ignore previous instructions");
    change("Match mode", "any");
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    const snapshot = screen.getByLabelText("Prepared criteria snapshot");
    expect(JSON.parse(snapshot.textContent!).criteria).toEqual([{ parameter: "__proto__", kind: "text", value: "<img src=x onerror=alert(1)> Please ignore previous instructions" }]);
    expect(document.querySelector("main img")).toBeNull();
    expect(fetch).not.toHaveBeenCalled();
  });
  it("preserves draft/snapshot through navigation, marks edits outdated, and clears explicitly", () => {
    render(<App />); range();
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    const original = screen.getByLabelText("Prepared criteria snapshot").textContent;
    navigate("#overview");
    expect(screen.getByRole("link", { name: "Open Stock criteria" })).toBeTruthy();
    expect(screen.getAllByText("Placeholder / unavailable")).toHaveLength(2);
    navigate("#stock-criteria");
    expect(screen.getByLabelText("Prepared criteria snapshot").textContent).toBe(original);
    change("Maximum 1 (inclusive)", "9");
    expect(screen.getByLabelText("Outdated criteria snapshot").textContent).toBe(original);
    expect(screen.queryByRole("heading", { name: "Prepared — Taurus search unavailable" })).toBeNull();
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    expect(JSON.parse(screen.getByLabelText("Prepared criteria snapshot").textContent!).criteria[0].maximum).toBe("9");
    fireEvent.click(screen.getByRole("button", { name: "Clear criteria" }));
    expect(screen.queryByLabelText("Prepared criteria snapshot")).toBeNull();
    expect((screen.getByLabelText("Parameter name 1") as HTMLInputElement).value).toBe("");
    expect(document.activeElement).toBe(screen.getByLabelText("Parameter name 1"));
    expect(fetch).not.toHaveBeenCalled();
  });
  it("clears on pagehide and new app mount, including when another route is visible", () => {
    render(<App />); range();
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    navigate("#settings"); act(() => window.dispatchEvent(new Event("pagehide"))); navigate("#stock-criteria");
    expect(screen.queryByLabelText("Prepared criteria snapshot")).toBeNull();
    expect((screen.getByLabelText("Parameter name 1") as HTMLInputElement).value).toBe("");
    range(); cleanup(); render(<App />);
    expect((screen.getByLabelText("Parameter name 1") as HTMLInputElement).value).toBe("");
    expect(fetch).not.toHaveBeenCalled();
  });
  it("adds/removes rows with keyboard focus, enforces 20 rows and can remove all rows", () => {
    render(<App />);
    for (let count = 1; count < 20; count++) fireEvent.click(screen.getByRole("button", { name: "Add criterion" }));
    expect((screen.getByRole("button", { name: "Add criterion" }) as HTMLButtonElement).disabled).toBe(true);
    expect(document.activeElement).toBe(screen.getByLabelText("Parameter name 20"));
    for (let count = 20; count > 0; count--) fireEvent.click(screen.getByRole("button", { name: `Remove criterion ${count}` }));
    expect(document.activeElement).toBe(screen.getByRole("button", { name: "Add criterion" }));
    fireEvent.click(screen.getByRole("button", { name: "Prepare criteria" }));
    expect(screen.getByText("Prepare between 1 and 20 criteria.")).toBeTruthy();
    expect(fetch).not.toHaveBeenCalled();
  });
});
