"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  Clock,
  FileSpreadsheet,
  FileText,
  FileType,
  Loader2,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { deleteDocument } from "@/lib/api/documents";
import { useApp } from "@/lib/context/app-context";
import { useDocuments } from "@/lib/hooks/use-documents";
import type { DocumentStatus } from "@/lib/types";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { formatBytes, formatRelativeTime } from "@/lib/utils";

const typeIcons: Record<string, typeof FileText> = {
  PDF: FileText,
  Markdown: FileType,
  Spreadsheet: FileSpreadsheet,
  Document: FileText,
  Text: FileType,
};

const statusConfig: Record<
  DocumentStatus,
  { label: string; variant: "success" | "warning" | "destructive" }
> = {
  indexed: { label: "Indexed", variant: "success" },
  processing: { label: "Processing", variant: "warning" },
  failed: { label: "Failed", variant: "destructive" },
  already_exists: { label: "Already Indexed", variant: "success" },
};

export function DocumentsList() {
  const { refresh } = useApp();
  const { documents, loading, error, refetch } = useDocuments({
    pollProcessing: true,
  });
  const [deletingId, setDeletingId] = useState<string | null>(null);

  const handleDelete = async (id: string, name: string) => {
    setDeletingId(id);
    try {
      await deleteDocument(id);
      toast.success(`"${name}" deleted`);
      refresh();
      refetch();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  return (
    <Card>
      <CardHeader>
        <CardTitle>All Documents</CardTitle>
        <CardDescription>
          Manage uploaded files and indexing status
        </CardDescription>
      </CardHeader>
      <CardContent className="px-0">
        {error ? (
          <div className="flex items-center gap-3 px-6 py-8 text-sm text-destructive">
            <AlertCircle className="size-4 shrink-0" />
            <span>{error}</span>
          </div>
        ) : loading ? (
          <div className="space-y-4 px-6 py-2">
            {Array.from({ length: 5 }).map((_, i) => (
              <div key={i} className="flex items-center gap-4">
                <Skeleton className="size-10 rounded-lg" />
                <div className="flex-1 space-y-2">
                  <Skeleton className="h-4 w-48" />
                  <Skeleton className="h-3 w-32" />
                </div>
              </div>
            ))}
          </div>
        ) : documents.length === 0 ? (
          <p className="px-6 py-8 text-center text-sm text-muted-foreground">
            No documents uploaded yet.
          </p>
        ) : (
          <ul className="divide-y divide-border/60">
            {documents.map((doc, index) => {
              const Icon = typeIcons[doc.type] ?? FileText;
              const status = statusConfig[doc.status];

              return (
                <motion.li
                  key={doc.id}
                  initial={{ opacity: 0, x: -8 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.3, delay: index * 0.03 }}
                  className="flex items-center gap-4 px-6 py-4 transition-colors hover:bg-muted/40"
                >
                  <div className="flex size-10 shrink-0 items-center justify-center rounded-lg bg-muted">
                    <Icon className="size-4 text-muted-foreground" />
                  </div>
                  <div className="min-w-0 flex-1">
                    <p className="truncate text-sm font-medium">{doc.name}</p>
                    <div className="mt-0.5 flex flex-wrap items-center gap-x-3 gap-y-1 text-xs text-muted-foreground">
                      <span>{doc.type}</span>
                      <span>{formatBytes(doc.size)}</span>
                      <span>{doc.chunks} chunks</span>
                      <span className="flex items-center gap-1">
                        <Clock className="size-3" />
                        {formatRelativeTime(doc.uploadedAt)}
                      </span>
                    </div>
                  </div>
                  <Badge variant={status.variant}>{status.label}</Badge>
                  <Button
                    variant="ghost"
                    size="icon"
                    className="shrink-0 text-muted-foreground hover:text-destructive"
                    disabled={deletingId === doc.id}
                    onClick={() => handleDelete(doc.id, doc.name)}
                  >
                    {deletingId === doc.id ? (
                      <Loader2 className="size-4 animate-spin" />
                    ) : (
                      <Trash2 className="size-4" />
                    )}
                  </Button>
                </motion.li>
              );
            })}
          </ul>
        )}
      </CardContent>
    </Card>
  );
}
