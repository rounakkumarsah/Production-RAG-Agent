import { getApiBase, ApiError } from "@/lib/api/client";
import { normalizeSources } from "@/lib/api/normalize";
import type { QuerySource } from "@/lib/types";

export interface StreamQueryOptions {
  query: string;
  collectionId?: string | null;
  signal?: AbortSignal;
  onToken: (token: string) => void;
  onSources: (sources: QuerySource[]) => void;
  onDone: () => void;
  onError: (error: Error) => void;
}

function parseSseChunk(
  chunk: string,
  handlers: Pick<
    StreamQueryOptions,
    "onToken" | "onSources" | "onDone" | "onError"
  >
) {
  const lines = chunk.split("\n");
  for (const line of lines) {
    if (!line.startsWith("data:")) continue;
    const data = line.slice(5).trim();
    if (!data || data === "[DONE]") {
      handlers.onDone();
      return;
    }

    try {
      const parsed = JSON.parse(data) as Record<string, unknown>;
      const type = String(parsed.type ?? parsed.event ?? "");

      if (type === "sources" || parsed.sources) {
        handlers.onSources(normalizeSources(parsed.sources ?? parsed.data));
        continue;
      }

      if (type === "error") {
        handlers.onError(
          new Error(String(parsed.message ?? parsed.content ?? "Stream error"))
        );
        return;
      }

      const token = String(
        parsed.content ??
          parsed.token ??
          parsed.text ??
          parsed.delta ??
          (type === "token" ? parsed.data : "") ??
          ""
      );
      if (token) handlers.onToken(token);
    } catch {
      if (data) handlers.onToken(data);
    }
  }
}

export async function streamQuery(options: StreamQueryOptions): Promise<void> {
  const apiBase = getApiBase();
  const res = await fetch(`${apiBase}/query`, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
      Accept: "text/event-stream",
    },
    body: JSON.stringify({
      query: options.query,
      collection_id: options.collectionId ?? undefined,
      stream: true,
    }),
    signal: options.signal,
  });

  if (!res.ok) {
    const text = await res.text().catch(() => "");
    throw new ApiError(res.status, text || res.statusText);
  }

  const contentType = res.headers.get("content-type") ?? "";

  if (!contentType.includes("text/event-stream")) {
    const json = (await res.json()) as Record<string, unknown>;
    if (json.sources) {
      options.onSources(normalizeSources(json.sources));
    }
    const answer = String(json.answer ?? json.response ?? json.content ?? "");
    if (answer) options.onToken(answer);
    options.onDone();
    return;
  }

  if (!res.body) throw new ApiError(500, "No response stream");

  const reader = res.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";

  while (true) {
    const { done, value } = await reader.read();
    if (done) break;
    buffer += decoder.decode(value, { stream: true });

    const parts = buffer.split("\n\n");
    buffer = parts.pop() ?? "";
    for (const part of parts) parseSseChunk(part, options);
  }

  if (buffer.trim()) parseSseChunk(buffer, options);
  options.onDone();
}
