import React from "react";

function Swatch({ name, className }: { name: string; className: string }) {
  return (
    <div className="flex items-center gap-3 border border-border rounded-lg p-3">
      <div className={`h-10 w-10 rounded ${className}`} />
      <code className="text-sm">{name}</code>
    </div>
  );
}

export default function ThemePreview() {
  return (
    <div className="min-h-dvh bg-background text-foreground p-6 space-y-8">
      <header className="flex items-center justify-between">
        <h1 className="text-2xl font-bold">Theme Preview</h1>
        <ThemeToggle />
      </header>

      <section className="grid sm:grid-cols-2 lg:grid-cols-3 gap-4">
        <Swatch name="background" className="bg-background" />
        <Swatch name="foreground" className="bg-foreground" />
        <Swatch name="card" className="bg-card" />
        <Swatch name="card-foreground" className="bg-card-foreground" />
        <Swatch name="popover" className="bg-popover" />
        <Swatch name="popover-foreground" className="bg-popover-foreground" />
        <Swatch name="primary" className="bg-primary" />
        <Swatch name="primary-foreground" className="bg-primary-foreground" />
        <Swatch name="secondary" className="bg-secondary" />
        <Swatch name="secondary-foreground" className="bg-secondary-foreground" />
        <Swatch name="accent" className="bg-accent" />
        <Swatch name="accent-foreground" className="bg-accent-foreground" />
        <Swatch name="muted" className="bg-muted" />
        <Swatch name="muted-foreground" className="bg-muted-foreground" />
        <Swatch name="destructive" className="bg-destructive" />
        <Swatch name="destructive-foreground" className="bg-destructive-foreground" />
        <Swatch name="border" className="bg-border" />
        <Swatch name="input" className="bg-input" />
        <Swatch name="ring" className="bg-ring" />
      </section>

      <section className="grid gap-4">
        <div className="rounded-lg bg-card text-card-foreground shadow p-4">
          <h2 className="font-semibold mb-2">Card example</h2>
          <p className="text-sm">
            Questo blocco usa <code>bg-card</code>/<code>text-card-foreground</code> e
            ombre da token.
          </p>
          <button className="mt-3 inline-flex items-center rounded-md px-3 py-2 bg-primary text-primary-foreground shadow hover:opacity-90">
            Primary Button
          </button>
        </div>
        <div className="rounded-lg bg-popover text-popover-foreground border border-border p-4">
          <h2 className="font-semibold mb-2">Popover example</h2>
          <input
            className="mt-2 w-full rounded-md border border-border bg-input px-3 py-2 outline-none focus:ring-2"
            placeholder="Input themed"
          />
        </div>
      </section>
    </div>
  );
}

function ThemeToggle() {
  const get = () =>
    localStorage.getItem("theme") ||
    (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light");

  const [theme, setTheme] = React.useState<string>(get);

  React.useEffect(() => {
    document.documentElement.setAttribute("data-theme", theme);
    localStorage.setItem("theme", theme);
  }, [theme]);

  return (
    <button
      className="rounded-md border border-border bg-card text-card-foreground px-3 py-1"
      onClick={() => setTheme(theme === "light" ? "dark" : "light")}
    >
      {theme === "light" ? "Switch to Dark" : "Switch to Light"}
    </button>
  );
}
