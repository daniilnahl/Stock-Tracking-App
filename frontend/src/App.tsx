import { useEffect, useRef, useState } from "react";
import { resolveRoute, routeHref, routes } from "./app/routes";
import { Button, EmptyState, Navigation, PageLayout } from "./components/primitives";
import { ClientFoundation } from "./features/ClientFoundation";
import { OverviewPage, SettingsPage, WatchlistsPage } from "./features/ShellPages";
import { useThemePreference } from "./themes/theme";

export function App() {
  const [route, setRoute] = useState(() => resolveRoute(window.location.hash));
  const preference = useThemePreference();
  const heading = useRef<HTMLHeadingElement>(null);
  const previous = useRef(route);
  const title = route ? routes[route].title : "Page unavailable";
  useEffect(() => {
    const changeRoute = () => setRoute(resolveRoute(window.location.hash));
    window.addEventListener("hashchange", changeRoute);
    return () => window.removeEventListener("hashchange", changeRoute);
  }, []);
  useEffect(() => {
    document.title = `${route ? routes[route].label : "Page unavailable"} - Stock Tracking App`;
    if (previous.current !== route) heading.current?.focus();
    previous.current = route;
  }, [route]);
  return <>
    <a className="skip-link" href="#main-content" onClick={event => {
      event.preventDefault(); document.getElementById("main-content")?.focus();
    }}>Skip to content</a>
    <header className="site-header"><a href={routeHref("overview")} className="brand">stock / tracker</a>
      <Navigation current={route} />
      <Button onClick={() => preference.setTheme(preference.theme === "light" ? "dark" : "light")}>
        {preference.theme === "light" ? "Dark theme" : "Light theme"}
      </Button>
    </header>
    {preference.notice && <p className="storage-notice" role="status">{preference.notice}</p>}
    <PageLayout title={title} headingRef={heading} description={route === "client-foundation" ? "A separately labeled synthetic client check." : "Saved observations with their limits in view."}>
      {route !== "client-foundation" && <div className="notice">Dashboard shell demo / not connected. No holdings or market figures are loaded.</div>}
      {route === "overview" && <OverviewPage />}
      {route === "watchlists" && <WatchlistsPage />}
      {route === "settings" && <SettingsPage preference={preference} />}
      {route === "client-foundation" && <ClientFoundation />}
      {route === null && <EmptyState title="This page is not available" message="Choose Overview, Watchlists or Settings from the navigation." />}
      <footer className="app-footer"><a href={routeHref("client-foundation")}>Synthetic client foundation demo</a>
        <p>No recommendation or agent service is available. Historical acquisition remains disabled pending its separate rights gate.</p></footer>
    </PageLayout>
  </>;
}
