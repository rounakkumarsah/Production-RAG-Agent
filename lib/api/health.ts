import { apiFetch } from "@/lib/api/client";
import { normalizeHealth } from "@/lib/api/normalize";
import type { HealthInfo } from "@/lib/types";

export async function getHealth(): Promise<HealthInfo> {
  const raw = await apiFetch<unknown>("/health");
  return normalizeHealth(raw);
}
