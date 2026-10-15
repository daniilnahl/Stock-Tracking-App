import { useEffect, useLayoutEffect, useState } from "react";

export const themes = {
  light: { name: "Monochrome light", scheme: "light" },
  dark: { name: "Monochrome dark", scheme: "dark" },
} as const;
export type ThemeId = keyof typeof themes;
export const themeStorageKey = "stock-tracker.theme";
export function isTheme(value: unknown): value is ThemeId {
  return typeof value === "string" && Object.hasOwn(themes, value);
}
function readPreference(): { theme: ThemeId; notice: string } {
  try {
    const saved = localStorage.getItem(themeStorageKey);
    return { theme: isTheme(saved) ? saved : "light", notice: "" };
  } catch {
    return { theme: "light", notice: "Theme preference storage is unavailable. Changes apply to this page only." };
  }
}
export function useThemePreference() {
  const [preference, setPreference] = useState(readPreference);
  useLayoutEffect(() => { document.documentElement.dataset.theme = preference.theme; }, [preference.theme]);
  useEffect(() => {
    const sync = (event: StorageEvent) => {
      // Other storage areas cannot change the persistent local preference.
      try { if (event.storageArea !== localStorage) return; } catch { return; }
      if (event.key === themeStorageKey || event.key === null) {
        setPreference({ theme: isTheme(event.newValue) ? event.newValue : "light", notice: "" });
      }
    };
    window.addEventListener("storage", sync);
    return () => window.removeEventListener("storage", sync);
  }, []);
  const setTheme = (theme: ThemeId) => {
    if (!isTheme(theme)) return;
    let notice = "";
    try { localStorage.setItem(themeStorageKey, theme); }
    catch { notice = "Theme preference could not be saved. Changes apply to this page only."; }
    setPreference({ theme, notice });
  };
  return { ...preference, setTheme };
}
export type ThemePreference = ReturnType<typeof useThemePreference>;
