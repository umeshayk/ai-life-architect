import { useEffect } from 'react';
import type { PropsWithChildren } from 'react';

import { useThemeStore } from 'store/themeStore';

export function ThemeProvider({ children }: PropsWithChildren) {
  const theme = useThemeStore((state) => state.theme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
  }, [theme]);

  return children;
}
