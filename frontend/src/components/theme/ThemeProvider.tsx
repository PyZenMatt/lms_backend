import { useEffect, useState } from 'react';

import type { ReactNode } from 'react';

export default function ThemeProvider({ children }: { children: ReactNode }) {
  const initial = () =>
    localStorage.getItem('theme') ||
    (window.matchMedia('(prefers-color-scheme: dark)').matches ? 'dark' : 'light');
  const [theme, setTheme] = useState(initial);

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);

  return <div data-theme={theme}>{children}</div>;
}
