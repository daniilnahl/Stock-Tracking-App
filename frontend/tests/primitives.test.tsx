// @vitest-environment jsdom
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { afterEach, expect, it, vi } from "vitest";
import { Button, Chart, DataTable, EmptyState, ErrorState, FilterPanel, SettingsField } from "../src/components/primitives";
import { ClientError } from "../src/services/validation";

afterEach(cleanup);
it("Button is a semantic non-submit control, preserves disabled and accessible labels", () => {
  const click = vi.fn();
  render(<Button onClick={click} disabled>Unavailable action</Button>);
  const button = screen.getByRole("button", { name: "Unavailable action" });
  expect(button.getAttribute("type")).toBe("button");
  fireEvent.click(button); expect(click).not.toHaveBeenCalled();
});
it("DataTable preserves exact text/duplicate rows and escapes external text", () => {
  const rows = [{ id: 0, text: "<img src=x onerror=alert(1)>" }, { id: 1, text: "110.0000000000000000001" }, { id: 2, text: "110.0000000000000000001" }];
  const { container } = render(<DataTable caption="Synthetic test rows" columns={[{ id: "value", header: "Exact value", render: row => row.text }]} rows={rows} rowKey={row => row.id} emptyMessage="No rows" />);
  expect(screen.getAllByRole("row")).toHaveLength(4);
  expect(screen.getAllByText("110.0000000000000000001")).toHaveLength(2);
  expect(container.querySelector("img")).toBeNull();
  expect(screen.getByText("<img src=x onerror=alert(1)>")).toBeTruthy();
  expect(screen.getByRole("region").getAttribute("tabindex")).toBe("0");
  expect(screen.getByText("Scroll horizontally if the table extends beyond the screen.")).toBeTruthy();
});
it("DataTable supplies an explicit empty row without fabricated observations", () => {
  render(<DataTable caption="Empty rows" columns={[{ id: "value", header: "Value", render: () => "" }]} rows={[]} rowKey={() => ""} emptyMessage="Not connected" />);
  expect(screen.getByRole("cell").textContent).toBe("Not connected");
});
it("state components expose status/safe errors and retry only when supplied", () => {
  const retry = vi.fn();
  render(<><EmptyState title="No entries" message="No saved data loaded." /><ErrorState error={new ClientError("network_error")} onRetry={retry} /></>);
  expect(screen.getByRole("status").textContent).toContain("No entries");
  expect(screen.getByRole("alert").textContent).toContain("The local API could not be reached.");
  fireEvent.click(screen.getByRole("button", { name: "Try again" })); expect(retry).toHaveBeenCalledTimes(1);
});
it("FilterPanel/SettingsField use native grouping and programmatic labels/descriptions", () => {
  render(<FilterPanel title="Synthetic controls"><SettingsField label="Example field" hint="Synthetic test only.">
    {attributes => <input {...attributes} />}
  </SettingsField></FilterPanel>);
  expect(screen.getByRole("group", { name: "Synthetic controls" })).toBeTruthy();
  const input = screen.getByRole("textbox", { name: "Example field" });
  expect(document.getElementById(input.getAttribute("aria-describedby")!)?.textContent).toBe("Synthetic test only.");
});
it("Chart explicitly shows unsupported without drawing invented points", () => {
  const { container } = render(<Chart title="Raw historical series" />);
  expect(screen.getByText("Unavailable. No historical series is loaded.")).toBeTruthy();
  expect(container.querySelector("svg,canvas")).toBeNull();
});
