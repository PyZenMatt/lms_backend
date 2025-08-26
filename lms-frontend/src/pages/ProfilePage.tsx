import React from "react";
import { getProfile, updateProfile, type Profile } from "../services/profile";
import { Spinner } from "../components/ui/spinner";
import { Alert } from "../components/ui/alert";
// EmptyState not used here

export default function ProfilePage() {
  const [loading, setLoading] = React.useState(true);
  const [saving, setSaving] = React.useState(false);
  const [msg, setMsg] = React.useState<string>("");

  const [data, setData] = React.useState<Profile | null>(null);
  const [avatarFile, setAvatarFile] = React.useState<File | null>(null);
  const [avatarPreview, setAvatarPreview] = React.useState<string | null>(null);

  React.useEffect(() => {
    (async () => {
      setLoading(true);
      const p = await getProfile();
      setData(p);
      setLoading(false);
    })();
  }, []);

  function onChange<K extends keyof Profile>(key: K, val: Profile[K]) {
    if (!data) return;
    setData({ ...data, [key]: val });
  }

  function onPickAvatar(e: React.ChangeEvent<HTMLInputElement>) {
    const f = e.target.files?.[0] || null;
    setAvatarFile(f);
    if (f) setAvatarPreview(URL.createObjectURL(f));
    else setAvatarPreview(null);
  }

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    if (!data) return;
    setSaving(true); setMsg("Salvataggio…");

    const fd = new FormData();
    // Campi testuali
    if (data.first_name !== undefined) fd.append("first_name", data.first_name || "");
    if (data.last_name !== undefined)  fd.append("last_name", data.last_name || "");
    if (data.phone !== undefined)      fd.append("phone", data.phone || "");
    if (data.address !== undefined)    fd.append("address", data.address || "");
    if (data.bio !== undefined)        fd.append("bio", data.bio || "");
    if (data.profession !== undefined) fd.append("profession", data.profession || "");
    if (data.artistic_aspirations !== undefined) fd.append("artistic_aspirations", data.artistic_aspirations || "");
    if (data.wallet_address !== undefined) fd.append("wallet_address", data.wallet_address || "");
    // File
    if (avatarFile) fd.append("avatar", avatarFile);

    const r = await updateProfile(fd);
    if (r) {
      setData(r);
      setMsg("✅ Profilo aggiornato");
      setAvatarFile(null);
      setAvatarPreview(null);
    } else {
      setMsg("❌ Errore salvataggio (controlla la console/network)");
    }
    setSaving(false);
  }

  if (loading) return (
    <div className="p-6 flex items-center gap-3">
      <Spinner />
      <div className="text-sm text-muted-foreground">Caricamento profilo…</div>
    </div>
  );
  if (!data) return (
    <Alert variant="error" title="Errore">Impossibile caricare il profilo.</Alert>
  );

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold">Profilo</h1>

      <form onSubmit={onSubmit} className="grid md:grid-cols-2 gap-4">
        <div className="border border-border rounded-lg p-4 bg-card text-card-foreground space-y-3">
          <div className="flex items-center gap-3">
            {avatarPreview ? (
              <img src={avatarPreview} className="w-20 h-20 rounded-md object-cover border border-border" />
            ) : data.avatar ? (
              <img src={data.avatar} className="w-20 h-20 rounded-md object-cover border border-border" />
            ) : (
              <div className="w-20 h-20 rounded-md border border-border grid place-items-center text-xs text-muted-foreground">No avatar</div>
            )}
            <div>
              <label className="text-sm">Avatar</label>
              <input type="file" accept="image/*" onChange={onPickAvatar}
                     className="block text-sm mt-1" />
              <p className="text-xs text-muted-foreground">PNG/JPG. Max ~ 2-5 MB (dipende dal server).</p>
            </div>
          </div>

          <div className="grid grid-cols-2 gap-2">
            <div>
              <label className="text-sm">Nome</label>
              <input className="w-full px-3 py-2 rounded-md border border-border bg-background"
                     value={data.first_name || ""} onChange={e=>onChange("first_name", e.target.value)} />
            </div>
            <div>
              <label className="text-sm">Cognome</label>
              <input className="w-full px-3 py-2 rounded-md border border-border bg-background"
                     value={data.last_name || ""} onChange={e=>onChange("last_name", e.target.value)} />
            </div>
          </div>

          <div>
            <label className="text-sm">Telefono</label>
            <input className="w-full px-3 py-2 rounded-md border border-border bg-background"
                   value={data.phone || ""} onChange={e=>onChange("phone", e.target.value)} />
          </div>

          <div>
            <label className="text-sm">Indirizzo</label>
            <input className="w-full px-3 py-2 rounded-md border border-border bg-background"
                   value={data.address || ""} onChange={e=>onChange("address", e.target.value)} />
          </div>
        </div>

        <div className="border border-border rounded-lg p-4 bg-card text-card-foreground space-y-3">
          <div>
            <label className="text-sm">Professione</label>
            <input className="w-full px-3 py-2 rounded-md border border-border bg-background"
                   value={data.profession || ""} onChange={e=>onChange("profession", e.target.value)} />
          </div>
          <div>
            <label className="text-sm">Aspirazioni artistiche</label>
            <textarea className="w-full px-3 py-2 rounded-md border border-border bg-background"
                      rows={4} value={data.artistic_aspirations || ""}
                      onChange={e=>onChange("artistic_aspirations", e.target.value)} />
          </div>
          <div>
            <label className="text-sm">Wallet address</label>
            <input className="w-full px-3 py-2 rounded-md border border-border bg-background"
                   value={data.wallet_address || ""} onChange={e=>onChange("wallet_address", e.target.value)} />
          </div>

          <button disabled={saving}
                  className="px-4 py-2 rounded-md bg-primary text-primary-foreground">
            {saving ? "Salvataggio…" : "Salva"}
          </button>
          <div className="text-sm text-muted-foreground">{msg}</div>
        </div>
      </form>
    </div>
  );
}
