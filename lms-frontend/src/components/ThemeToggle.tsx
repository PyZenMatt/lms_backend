// React import not required with new JSX transform
import useTheme from "@/hooks/useTheme";

export default function ThemeToggle() {
  const { isDark, toggle } = useTheme();

  return (
    <button
      type="button"
      onClick={toggle}
      aria-label={isDark ? "Passa a tema chiaro" : "Passa a tema scuro"}
      title={isDark ? "Passa a tema chiaro" : "Passa a tema scuro"}
      className="inline-flex h-9 w-9 items-center justify-center rounded-md border bg-card text-foreground hover:bg-accent transition"
    >
      <span aria-hidden="true" className="text-xl leading-none">
        {isDark ? "☀️" : "🌙"}
      </span>
      <span className="sr-only">{isDark ? "Tema chiaro" : "Tema scuro"}</span>
    </button>
  );
}
