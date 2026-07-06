"use client";

import { useCallback, useEffect, useState } from "react";
import { getDocuments } from "@/lib/api/documents";
import { useApp } from "@/lib/context/app-context";
import type { DashboardStats, Document } from "@/lib/types";

export function useDocuments(options?: { pollProcessing?: boolean }) {
  const { refreshKey, activeCollectionId } = useApp();
  const [documents, setDocuments] = useState<Document[]>([]);
  const [stats, setStats] = useState<DashboardStats>({
    totalDocuments: 0,
    totalChunks: 0,
    storageUsed: 0,
    storageLimit: 1024 * 1024 * 1024,
  });
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  const refetch = useCallback(async () => {
    setError(null);
    try {
      const data = await getDocuments(activeCollectionId);
      setDocuments(data.documents);
      setStats(data.stats);
    } catch (err) {
      setError(err instanceof Error ? err.message : "Failed to load documents");
    } finally {
      setLoading(false);
    }
  }, [activeCollectionId]);

  useEffect(() => {
    setLoading(true);
    refetch();
  }, [refetch, refreshKey]);

  useEffect(() => {
    if (!options?.pollProcessing) return;
    const hasProcessing = documents.some((doc) => doc.status === "processing");
    if (!hasProcessing) return;

    const interval = setInterval(refetch, 3000);
    return () => clearInterval(interval);
  }, [documents, options?.pollProcessing, refetch]);

  return { documents, stats, loading, error, refetch };
}
