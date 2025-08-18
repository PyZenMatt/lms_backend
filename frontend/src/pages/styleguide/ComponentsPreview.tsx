import { Button, Input, Card, CardHeader, CardContent, CardFooter, Alert, Badge, Textarea, Select, Tabs, Label, HelperText, Dialog, Popover, Skeleton, Breadcrumb } from "@/components/ui";
import * as React from "react";

export default function ComponentsPreview() {
  const [tab, setTab] = React.useState("tab1");
  const [dialogOpen, setDialogOpen] = React.useState(false);
  const anchorRef = React.useRef<HTMLButtonElement>(null);
  const [popoverOpen, setPopoverOpen] = React.useState(false);

  return (
    <div className="min-h-dvh bg-background text-foreground p-6 space-y-8">
      <h1 className="text-2xl font-bold">Components Preview</h1>

      <section className="space-y-3">
        <h2 className="font-semibold">Button</h2>
        <div className="flex gap-2 flex-wrap">
          <Button>Primary</Button>
          <Button variant="secondary">Secondary</Button>
          <Button variant="outline">Outline</Button>
          <Button variant="ghost">Ghost</Button>
          <Button variant="destructive">Destructive</Button>
        </div>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Form</h2>
        <Label htmlFor="email">Email</Label>
        <Input id="email" placeholder="name@example.com" helperText="Non condivideremo la tua email." />
        <Label htmlFor="desc">Descrizione</Label>
        <Textarea id="desc" helperText="Max 200 caratteri" />
        <Label htmlFor="role">Ruolo</Label>
        <Select id="role" label="Ruolo" options={[{value: "studente", label: "Studente"}, {value: "docente", label: "Docente"}]} helperText="Seleziona il ruolo" />
        <HelperText>Testo di aiuto</HelperText>
        <HelperText error>Testo di errore</HelperText>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Tabs</h2>
        <Tabs tabs={[{value: "tab1", label: "Tab 1"}, {value: "tab2", label: "Tab 2"}]} value={tab} onChange={setTab} />
        <div className="mt-2">Tab attivo: {tab}</div>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Dialog & Popover</h2>
        <Button ref={anchorRef} onClick={() => setPopoverOpen(!popoverOpen)}>Toggle Popover</Button>
        <Popover open={popoverOpen} anchor={anchorRef}>
          <div>Contenuto del popover</div>
        </Popover>
        <Button onClick={() => setDialogOpen(true)}>Apri Dialog</Button>
        <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)}>
          <div>Contenuto del dialog</div>
        </Dialog>
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Skeleton</h2>
        <Skeleton width={120} height={20} />
        <Skeleton width={60} height={60} radius={30} className="mt-2" />
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Breadcrumb</h2>
        <Breadcrumb items={[{label: "Home", href: "/"}, {label: "Dashboard", href: "/dashboard"}, {label: "Impostazioni"}]} />
      </section>

      <section className="space-y-3">
        <h2 className="font-semibold">Card & Alert & Badge</h2>
        <Card>
          <CardHeader>Header</CardHeader>
          <CardContent>Contenuto</CardContent>
          <CardFooter>
            <Badge>Default</Badge>
            <Badge variant="secondary" className="ml-2">Secondary</Badge>
          </CardFooter>
        </Card>
        <Alert className="mt-3" tone="destructive">Attenzione: esempio di alert</Alert>
      </section>
    </div>
  );
}
