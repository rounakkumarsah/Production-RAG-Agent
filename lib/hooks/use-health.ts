"use client";

import { useCallback, useEffect, useState } from "react";
import { getHealth } from "@/lib/api/health";
import type { HealthInfo } from "@/lib/types";

export function useHealth(pollIntervalMs = 30000) {
  const [health, setHealth] = useState<HealthInfo | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setError(null);
    try {
      const data = await getHealth();
      setHealth(data);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load health");
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    refetch();
    if (!pollIntervalMs) return;
    const interval = setInterval(refetch, pollIntervalMs);
    return () => clearInterval(interval);
  }, [pollIntervalMs, refetch]);

  return { health, loading, error, refetch };
}
