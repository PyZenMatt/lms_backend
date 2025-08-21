import { apiFetch } from "../lib/api";

export type Profile = {
  username: string;
  email: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  address?: string | null;
  role?: "student" | "teacher" | "admin";
  avatar?: string | null; // URL (readOnly)
  bio?: string | null;
  profession?: string | null;
  artistic_aspirations?: string | null;
  wallet_address?: string | null;
};

export async function getProfile(): Promise<Profile | null> {
  const r = await apiFetch<Profile>("/v1/profile/", { method: "GET" });
  return r.ok ? (r.data as Profile) : null;
}

/** Usa FormData per upload avatar + altri campi */
export async function updateProfile(fd: FormData): Promise<Profile | null> {
  const r = await apiFetch<Profile>("/v1/profile/", { method: "PUT", body: fd });
  return r.ok ? (r.data as Profile) : null;
}
