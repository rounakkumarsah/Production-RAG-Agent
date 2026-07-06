"use client";

import { useCallback, useEffect, useState } from "react";
import { getCollections } from "@/lib/api/collections";
import { useApp } from "@/lib/context/app-context";
import type { Collection } from "@/lib/types";

export function useCollections() {
  const { refreshKey } = useApp();
  const [collections, setCollections] = useState<Collection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setError(null);
    try {
      const data = await getCollections();
      setCollections(data);
    } catch (err) {
      setError(
        err instanceof Error ? err.message : "Failed to load collections"
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    setLoading(true);
    refetch();
  }, [refetch, refreshKey]);

  return { collections, loading, error, refetch };
}
