import type {
  Collection,
  DashboardStats,
  Document,
  DocumentStatus,
  HealthInfo,
  QuerySource,
} from "@/lib/types";

function pick<T>(obj: Record<string, unknown>, keys: string[]): T | undefined {
  for (const key of keys) {
    if (obj[key] !== undefined && obj[key] !== null) {
      return obj[key] as T;
    }
  }
  return undefined;
}

function normalizeStatus(raw: unknown): DocumentStatus {
  const value = String(raw ?? "processing").toLowerCase();
  if (value === "indexed" || value === "completed" || value === "ready") {
    return "indexed";
  }
  if (value === "already_exists") {
    return "already_exists";
  }
  if (value === "failed" || value === "error") return "failed";
  return "processing";
}

function inferType(name: string, rawType?: unknown): string {
  if (rawType) return String(rawType).toUpperCase();
  const ext = name.split(".").pop()?.toLowerCase();
  const map: Record<string, string> = {
    pdf: "PDF",
    md: "Markdown",
    txt: "Text",
    docx: "Document",
    xlsx: "Spreadsheet",
  };
  return map[ext ?? ""] ?? "Document";
}

export function normalizeDocument(raw: Record<string, unknown>): Document {
  const name = String(
    pick<string>(raw, ["name", "filename", "file_name", "title"]) ?? "Untitled"
  );
  const uploadedRaw = pick<string>(raw, [
    "uploaded_at",
    "uploadedAt",
    "created_at",
    "createdAt",
  ]);

  return {
    id: String(pick<string>(raw, ["id", "document_id"]) ?? ""),
    name,
    type: inferType(name, pick(raw, ["type", "file_type", "fileType"])),
    size: Number(pick<number>(raw, ["size", "size_bytes", "file_size", "file_size_bytes"]) ?? 0),
    chunks: Number(
      pick<number>(raw, ["chunks", "chunk_count", "chunks_count"]) ?? 0
    ),
    status: normalizeStatus(pick(raw, ["status", "processing_status"])),
    uploadedAt: uploadedRaw ? new Date(uploadedRaw) : new Date(),
    collectionId: pick<string>(raw, ["collection_id", "collectionId"]),
    error: pick<string>(raw, ["error", "error_message", "message"]),
  };
}

export function normalizeDocumentsPayload(raw: unknown): {
  documents: Document[];
  stats: DashboardStats;
} {
  if (Array.isArray(raw)) {
    const documents = raw.map((item) =>
      normalizeDocument(item as Record<string, unknown>)
    );
    return {
      documents,
      stats: deriveStats(documents),
    };
  }

  const obj = (raw ?? {}) as Record<string, unknown>;
  const list =
    (pick<unknown[]>(obj, ["documents", "items", "results"]) ?? []).map(
      (item) => normalizeDocument(item as Record<string, unknown>)
    );

  const stats: DashboardStats = {
    totalDocuments: Number(
      pick<number>(obj, [
        "total_documents",
        "totalDocuments",
        "total",
        "count",
      ]) ?? list.length
    ),
    totalChunks: Number(
      pick<number>(obj, ["total_chunks", "totalChunks"]) ??
        list.reduce((sum, doc) => sum + doc.chunks, 0)
    ),
    storageUsed: Number(
      pick<number>(obj, [
        "storage_used",
        "storageUsed",
        "storage_used_bytes",
      ]) ?? list.reduce((sum, doc) => sum + doc.size, 0)
    ),
    storageLimit: Number(
      pick<number>(obj, [
        "storage_limit",
        "storageLimit",
        "storage_limit_bytes",
      ]) ?? 1024 * 1024 * 1024
    ),
  };

  return { documents: list, stats };
}

function deriveStats(documents: Document[]): DashboardStats {
  return {
    totalDocuments: documents.length,
    totalChunks: documents.reduce((sum, doc) => sum + doc.chunks, 0),
    storageUsed: documents.reduce((sum, doc) => sum + doc.size, 0),
    storageLimit: 1024 * 1024 * 1024,
  };
}

export function normalizeCollection(raw: Record<string, unknown>): Collection {
  const createdRaw = pick<string>(raw, ["created_at", "createdAt"]);
  return {
    id: String(pick<string>(raw, ["id", "collection_id"]) ?? ""),
    name: String(pick<string>(raw, ["name", "title"]) ?? "Untitled"),
    documentCount: Number(
      pick<number>(raw, [
        "document_count",
        "documentCount",
        "documents_count",
        "count",
      ]) ?? 0
    ),
    createdAt: createdRaw ? new Date(createdRaw) : new Date(),
  };
}

export function normalizeCollectionsPayload(raw: unknown): Collection[] {
  if (Array.isArray(raw)) {
    return raw.map((item) =>
      normalizeCollection(item as Record<string, unknown>)
    );
  }
  const obj = (raw ?? {}) as Record<string, unknown>;
  const list = pick<unknown[]>(obj, ["collections", "items", "results"]) ?? [];
  return list.map((item) =>
    normalizeCollection(item as Record<string, unknown>)
  );
}

function normalizeServiceStatus(raw: unknown): string {
  if (typeof raw === "boolean") return raw ? "connected" : "disconnected";
  if (typeof raw === "object" && raw !== null) {
    const obj = raw as Record<string, unknown>;
    return String(
      pick(obj, ["status", "state"]) ??
        (pick<boolean>(obj, ["connected", "healthy"]) ? "connected" : "unknown")
    );
  }
  return String(raw ?? "unknown");
}

export function normalizeHealth(raw: unknown): HealthInfo {
  const obj = (raw ?? {}) as Record<string, unknown>;
  const services = (pick<Record<string, unknown>>(obj, ["services"]) ??
    {}) as Record<string, unknown>;

  return {
    status: String(pick(obj, ["status", "health"]) ?? "unknown"),
    gemini: normalizeServiceStatus(
      pick(obj, ["gemini"]) ?? services.gemini ?? services.gemini_api
    ),
    qdrant: normalizeServiceStatus(
      pick(obj, ["qdrant"]) ?? services.qdrant
    ),
    postgres: normalizeServiceStatus(
      pick(obj, ["postgres"]) ?? services.postgres ?? services.database
    ),
    backend: normalizeServiceStatus(
      pick(obj, ["backend"]) ?? services.backend ?? obj.status
    ),
    environment: String(
      pick(obj, ["environment", "env"]) ?? process.env.NODE_ENV ?? "development"
    ),
    version: pick<string>(obj, ["version"]),
  };
}

export function normalizeSources(raw: unknown): QuerySource[] {
  if (!Array.isArray(raw)) return [];
  return raw.map((item) => {
    const obj = item as Record<string, unknown>;
    return {
      documentId: pick<string>(obj, ["document_id", "documentId", "id"]),
      documentName: pick<string>(obj, [
        "document_name",
        "documentName",
        "filename",
        "name",
        "title",
      ]),
      chunkText: pick<string>(obj, [
        "chunk_text",
        "chunkText",
        "text",
        "content",
        "snippet",
        "text_snippet",
      ]),
      page: pick<number>(obj, ["page", "page_number"]),
      score: pick<number>(obj, ["score", "relevance"]),
    };
  });
}
