import { PropsWithChildren, useEffect } from "react";
import { create } from "zustand";

export type ThemeName = "light" | "dark" | "ocean" | "graphite";

interface ThemeStore {
  theme: ThemeName;
  setTheme: (theme: ThemeName) => void;
}

const themeStorageKey = "aila-theme";

function resolveInitialTheme(): ThemeName {
  const saved = window.localStorage.getItem(themeStorageKey) as ThemeName | null;
  if (saved) {
    return saved;
  }

  return window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export const useThemeStore = create<ThemeStore>((set) => ({
  theme: resolveInitialTheme(),
  setTheme: (theme) => set({ theme }),
}));

export function ThemeProvider({ children }: PropsWithChildren) {
  const theme = useThemeStore((state) => state.theme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(themeStorageKey, theme);
  }, [theme]);

  return children;
}

export function useTheme() {
  const theme = useThemeStore((state) => state.theme);
  const setTheme = useThemeStore((state) => state.setTheme);
  return { theme, setTheme };
}
