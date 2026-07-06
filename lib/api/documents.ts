import { apiFetch } from "@/lib/api/client";
import { normalizeDocumentsPayload } from "@/lib/api/normalize";
import type { DashboardStats, Document } from "@/lib/types";

export async function getDocuments(collectionId?: string | null): Promise<{
  documents: Document[];
  stats: DashboardStats;
}> {
  const params = new URLSearchParams();
  if (collectionId) params.set("collection_id", collectionId);
  const query = params.toString();
  const raw = await apiFetch<unknown>(
    `/documents${query ? `?${query}` : ""}`
  );
  return normalizeDocumentsPayload(raw);
}

export async function deleteDocument(id: string): Promise<void> {
  await apiFetch<void>(`/documents/${id}`, { method: "DELETE" });
}

export async function assignDocumentToCollection(
  documentId: string,
  collectionId: string | null
): Promise<void> {
  await apiFetch(`/documents/${documentId}`, {
    method: "PATCH",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ collection_id: collectionId }),
  });
}
