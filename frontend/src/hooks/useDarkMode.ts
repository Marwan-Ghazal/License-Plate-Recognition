import { useCallback, useEffect, useState } from "react";

const KEY = "platescan:theme";

function getInitial(): "light" | "dark" {
  if (typeof window === "undefined") return "light";
  const stored = localStorage.getItem(KEY);
  if (stored === "light" || stored === "dark") return stored;
  return window.matchMedia?.("(prefers-color-scheme: dark)").matches ? "dark" : "light";
}

export function useDarkMode() {
  const [theme, setTheme] = useState<"light" | "dark">(() => getInitial());

  useEffect(() => {
    const root = document.documentElement;
    root.classList.toggle("dark", theme === "dark");
    localStorage.setItem(KEY, theme);
  }, [theme]);

  const toggle = useCallback(() => setTheme((t) => (t === "dark" ? "light" : "dark")), []);

  return { theme, toggle, setTheme };
}
