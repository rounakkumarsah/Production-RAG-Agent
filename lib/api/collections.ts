import { apiFetch } from "@/lib/api/client";
import { normalizeCollection, normalizeCollectionsPayload } from "@/lib/api/normalize";
import type { Collection } from "@/lib/types";

export async function getCollections(): Promise<Collection[]> {
  const raw = await apiFetch<unknown>("/collections");
  return normalizeCollectionsPayload(raw);
}

export async function createCollection(name: string): Promise<Collection> {
  const raw = await apiFetch<Record<string, unknown>>("/collections", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ name }),
  });
  return normalizeCollection(raw);
}

export async function deleteCollection(id: string): Promise<void> {
  await apiFetch<void>(`/collections/${id}`, { method: "DELETE" });
}
