import { create } from 'zustand';

export type ThemeMode = 'light' | 'dark' | 'graphite' | 'ocean';

type ThemeState = {
  theme: ThemeMode;
  setTheme: (theme: ThemeMode) => void;
  cycleTheme: () => void;
};

const orderedThemes: ThemeMode[] = ['light', 'dark', 'graphite', 'ocean'];

export const useThemeStore = create<ThemeState>((set, get) => ({
  theme: 'light',
  setTheme: (theme) => set({ theme }),
  cycleTheme: () => {
    const currentIndex = orderedThemes.indexOf(get().theme);
    const nextTheme = orderedThemes[(currentIndex + 1) % orderedThemes.length];
    set({ theme: nextTheme });
  },
}));
