import { getApiBase, ApiError } from "@/lib/api/client";
import { normalizeDocument } from "@/lib/api/normalize";
import type { Document } from "@/lib/types";

export interface UploadProgress {
  fileName: string;
  progress: number;
}

export async function uploadDocuments(
  files: File[],
  options?: {
    collectionId?: string | null;
    onProgress?: (progress: UploadProgress) => void;
    signal?: AbortSignal;
  }
): Promise<Document[]> {
  const formData = new FormData();
  files.forEach((file) => formData.append("files", file));
  if (options?.collectionId) {
    formData.append("collection_id", options.collectionId);
  }

  return new Promise((resolve, reject) => {
    const xhr = new XMLHttpRequest();
    const apiBase = getApiBase();
    xhr.open("POST", `${apiBase}/upload`);
    xhr.responseType = "json";
    
    // Set timeout to 15 minutes
    xhr.timeout = 900000;

    if (options?.signal) {
      options.signal.addEventListener("abort", () => xhr.abort());
    }

    xhr.upload.onprogress = (event) => {
      if (!event.lengthComputable || !options?.onProgress) return;
      const progress = Math.round((event.loaded / event.total) * 100);
      options.onProgress({
        fileName: files.length === 1 ? files[0].name : `${files.length} files`,
        progress,
      });
    };

    xhr.onload = () => {
      if (xhr.status >= 200 && xhr.status < 300) {
        const raw = xhr.response;
        if (Array.isArray(raw)) {
          resolve(
            raw.map((item) =>
              normalizeDocument(item as Record<string, unknown>)
            )
          );
          return;
        }
        const obj = (raw ?? {}) as Record<string, unknown>;
        const list =
          (obj.documents as unknown[]) ??
          (obj.results as unknown[]) ??
          (obj.items as unknown[]) ??
          (raw ? [raw] : []);
        resolve(
          list.map((item) =>
            normalizeDocument(item as Record<string, unknown>)
          )
        );
        return;
      }

      const rawResponse = xhr.response;
      let errorMsg = xhr.statusText || "Upload failed";
      if (rawResponse && typeof rawResponse === "object") {
        const obj = rawResponse as Record<string, unknown>;
        if (typeof obj.detail === "string") {
          errorMsg = obj.detail;
        } else if (Array.isArray(obj.detail)) {
          errorMsg = obj.detail.map((d: any) => d?.msg ?? String(d)).join(", ");
        } else if (typeof obj.error === "string") {
          errorMsg = obj.error;
        } else if (typeof obj.message === "string") {
          errorMsg = obj.message;
        }
      }
      reject(new ApiError(xhr.status, errorMsg));
    };

    xhr.ontimeout = () => reject(new ApiError(408, "Upload timed out (15 minute limit exceeded)"));
    xhr.onerror = () => reject(new ApiError(0, "Network error during upload"));
    xhr.onabort = () => reject(new ApiError(0, "Upload cancelled"));
    xhr.send(formData);
  });
}
