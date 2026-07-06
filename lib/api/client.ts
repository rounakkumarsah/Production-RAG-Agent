export const API_BASE = "/api";

export function getApiBase(): string {
  if (typeof window !== "undefined") {
    const stored = localStorage.getItem("rag_backend_url");
    if (stored) return stored.replace(/\/$/, "");
  }
  return (
    process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, "") ||
    API_BASE
  );
}

export class ApiError extends Error {
  constructor(
    public status: number,
    message: string
  ) {
    super(message);
    this.name = "ApiError";
  }
}

function parseErrorMessage(text: string, fallback: string): string {
  if (!text) return fallback;
  try {
    const json = JSON.parse(text) as { detail?: string | { msg?: string }[] };
    if (typeof json.detail === "string") return json.detail;
    if (Array.isArray(json.detail)) {
      return json.detail.map((d) => d.msg ?? String(d)).join(", ");
    }
  } catch {
    // plain text response
  }
  return text.length > 200 ? fallback : text;
}

export async function apiFetch<T>(
  path: string,
  init?: RequestInit & { timeout?: number }
): Promise<T> {
  const timeoutMs = init?.timeout ?? 30000; // default 30s
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), timeoutMs);

  const apiBase = getApiBase();

  try {
    const res = await fetch(`${apiBase}${path}`, {
      ...init,
      signal: controller.signal,
      headers: {
        Accept: "application/json",
        ...init?.headers,
      },
    });

    clearTimeout(timeoutId);

    if (!res.ok) {
      const text = await res.text().catch(() => "");
      throw new ApiError(
        res.status,
        parseErrorMessage(text, res.statusText || "Request failed")
      );
    }

    if (res.status === 204) return undefined as T;
    return res.json() as Promise<T>;
  } catch (err: any) {
    clearTimeout(timeoutId);
    if (err.name === "AbortError") {
      throw new ApiError(408, "Request timed out");
    }
    throw err;
  }
}
