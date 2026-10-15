import { createContext, useContext } from "react";
import type { ApiClient, ClientSnapshot } from "../services/client";

export type LocalSession = Readonly<{ client: ApiClient; snapshot: ClientSnapshot }>;
export const SessionContext = createContext<LocalSession | null>(null);
export function useLocalSession(): LocalSession {
  const session = useContext(SessionContext);
  if (!session) throw new Error("Local session provider is required.");
  return session;
}
export function connectionLabel(snapshot: ClientSnapshot): string {
  if (snapshot.connection === "connected") return "Configured";
  if (snapshot.connection === "unsupported") return "Unsupported";
  return "Disconnected";
}
