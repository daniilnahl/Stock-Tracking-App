// @vitest-environment jsdom
import { afterEach, expect, it } from "vitest";
import { cleanup, fireEvent, render, screen } from "@testing-library/react";
import { App } from "../src/App";

afterEach(cleanup);
it("labels synthetic disconnected state and demonstrates exact values without HTTP", () => {
  render(<App />);
  expect(screen.getByText("Synthetic client foundation demo - no live data")).toBeTruthy();
  expect(screen.getByText("Disconnected. No saved observations are loaded.")).toBeTruthy();
  fireEvent.click(screen.getByRole("button", { name: "Check synthetic response" }));
  expect(screen.getByText("110.0000000000000000001")).toBeTruthy();
  expect(screen.getByText("9223372036854775807")).toBeTruthy();
  expect(fetch).not.toHaveBeenCalled();
  fireEvent.click(screen.getByRole("button", { name: "Show safe error state" }));
  expect(screen.getByRole("alert").textContent).toBe("The API response is incompatible. No data was published.");
  expect(screen.queryByText("9223372036854775807")).toBeNull();
  fireEvent.click(screen.getByRole("button", { name: "Clear demonstration" }));
  expect(screen.getByText("No demonstration values loaded.")).toBeTruthy();
});
