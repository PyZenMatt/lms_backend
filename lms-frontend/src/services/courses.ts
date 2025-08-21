// src/services/courses.ts
import { api } from "../lib/api"

// -------------------------
// Costanti / Tipi categoria
// -------------------------
export const CATEGORIES = [
  "disegno",
  "pittura-olio",
  "acquerello",
  "tempera",
  "acrilico",
  "scultura",
  "storia-arte",
  "fotografia",
  "illustrazione",
  "arte-digitale",
  "ceramica",
  "incisione",
  "mosaico",
  "restauro",
  "calligrafia",
  "fumetto",
  "design-grafico",
  "arte-contemporanea",
  "arte-classica",
  "other",
] as const

export type Category = typeof CATEGORIES[number]
export function isValidCategory(x: unknown): x is Category {
  return typeof x === "string" && (CATEGORIES as readonly string[]).includes(x)
}

// -------------------------
// Tipi corso / paginazione
// -------------------------
export type Course = {
  id: number | string
  title: string
  description?: string
  cover_image?: string | null
  price?: number | null
  currency?: string | null
  progress_percent?: number | null
  students_count?: number | null
  lessons_count?: number | null
  created_at?: string
  updated_at?: string
  category?: Category | string | null
}

type DrfPaginated<T> = {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}

export type ListParams = {
  page?: number
  page_size?: number
  search?: string
  ordering?: string // es. "title" | "-created_at"
  category?: string // facoltativo: se il BE accetta filtro categoria
}

export type ListOut = {
  ok: boolean
  status: number
  data: Course[]
  count?: number
  next?: string | null
  previous?: string | null
}

// -------------------------
// Helpers normalizzazione
// -------------------------
function normalizeList(payload: Course[] | DrfPaginated<Course>): ListOut {
  if (Array.isArray(payload)) {
    return { ok: true, status: 200, data: payload, count: payload.length, next: null, previous: null }
  }
  return {
    ok: true,
    status: 200,
    data: payload.results ?? [],
    count: payload.count,
    next: payload.next,
    previous: payload.previous,
  }
}

// -------------------------
// API
// -------------------------
export async function listCourses(params: ListParams = {}) {
  const res = await api.get<Course[] | DrfPaginated<Course>>("/v1/courses/", { query: params as any })
  if (!res.ok) return { ok: false as const, status: res.status, data: [] as Course[] } as ListOut
  return normalizeList(res.data)
}

export async function getCourse(id: number | string) {
  const res = await api.get<Course>(`/v1/courses/${id}/`)
  if (!res.ok) return { ok: false as const, status: res.status, data: null as any as Course }
  return { ok: true as const, status: res.status, data: res.data }
}
