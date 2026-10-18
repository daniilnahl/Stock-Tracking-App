export const routes = {
  overview: { label: "Overview", title: "Your watchlists, clearly.", navigation: true },
  watchlists: { label: "Watchlists", title: "Saved watchlists", navigation: true },
  "stock-criteria": { label: "Stock criteria", title: "Stock criteria", navigation: true },
  settings: { label: "Settings", title: "Make yourself at home.", navigation: true },
  "client-foundation": { label: "Client foundation", title: "Client foundation", navigation: false },
} as const;
export type RouteId = keyof typeof routes;
export function routeHref(id: RouteId): `#${RouteId}` { return `#${id}`; }
export function resolveRoute(hash: string): RouteId | null {
  if (!hash || hash === "#") return "overview";
  const id = hash.slice(1);
  return hash.startsWith("#") && Object.hasOwn(routes, id) ? id as RouteId : null;
}
export const navigation = (Object.keys(routes) as RouteId[])
  .filter(id => routes[id].navigation)
  .map(id => ({ id, label: routes[id].label, href: routeHref(id) }));
