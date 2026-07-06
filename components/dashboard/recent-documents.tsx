"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  AlertCircle,
  ArrowRight,
  Clock,
  FileSpreadsheet,
  FileText,
  FileType,
} from "lucide-react";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardAction,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import type { Document, DocumentStatus } from "@/lib/types";
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

interface RecentDocumentsProps {
  documents: Document[];
  loading?: boolean;
  error?: string | null;
  limit?: number;
}

export function RecentDocuments({
  documents,
  loading,
  error,
  limit = 5,
}: RecentDocumentsProps) {
  const recent = [...documents]
    .sort((a, b) => b.uploadedAt.getTime() - a.uploadedAt.getTime())
    .slice(0, limit);

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.2 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>Recent Documents</CardTitle>
          <CardDescription>
            Your latest uploads and their indexing status
          </CardDescription>
          <CardAction>
            <Button
              variant="ghost"
              size="sm"
              className="text-muted-foreground"
              asChild
            >
              <Link href="/documents">
                View all
                <ArrowRight className="size-3.5" />
              </Link>
            </Button>
          </CardAction>
        </CardHeader>
        <CardContent className="px-0">
          {error ? (
            <div className="flex items-center gap-3 px-6 py-8 text-sm text-destructive">
              <AlertCircle className="size-4 shrink-0" />
              <span>{error}</span>
            </div>
          ) : loading ? (
            <div className="space-y-4 px-6 py-2">
              {Array.from({ length: 3 }).map((_, i) => (
                <div key={i} className="flex items-center gap-4">
                  <Skeleton className="size-10 rounded-lg" />
                  <div className="flex-1 space-y-2">
                    <Skeleton className="h-4 w-48" />
                    <Skeleton className="h-3 w-32" />
                  </div>
                </div>
              ))}
            </div>
          ) : recent.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              No documents yet. Upload your first PDF to get started.
            </p>
          ) : (
            <ul className="divide-y divide-border/60">
              {recent.map((doc, index) => {
                const Icon = typeIcons[doc.type] ?? FileText;
                const status = statusConfig[doc.status];

                return (
                  <motion.li
                    key={doc.id}
                    initial={{ opacity: 0, x: -8 }}
                    animate={{ opacity: 1, x: 0 }}
                    transition={{ duration: 0.3, delay: 0.25 + index * 0.05 }}
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
                      </div>
                    </div>
                    <div className="hidden shrink-0 items-center gap-3 sm:flex">
                      <span className="flex items-center gap-1 text-xs text-muted-foreground">
                        <Clock className="size-3" />
                        {formatRelativeTime(doc.uploadedAt)}
                      </span>
                      <Badge variant={status.variant}>{status.label}</Badge>
                    </div>
                    <Badge
                      variant={status.variant}
                      className="shrink-0 sm:hidden"
                    >
                      {status.label}
                    </Badge>
                  </motion.li>
                );
              })}
            </ul>
          )}
        </CardContent>
      </Card>
    </motion.div>
  );
}
