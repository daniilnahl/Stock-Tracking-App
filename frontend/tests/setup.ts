import { afterEach, beforeEach, vi } from "vitest";

beforeEach(() => {
  vi.stubGlobal("fetch", vi.fn(() => { throw new Error("Unexpected network in deterministic frontend tests"); }));
});
afterEach(() => { vi.restoreAllMocks(); vi.unstubAllGlobals(); });
