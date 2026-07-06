"use client";

import { motion } from "framer-motion";
import { useState, useEffect } from "react";
import {
  AlertCircle,
  CheckCircle2,
  Database,
  Server,
  Sparkles,
  XCircle,
} from "lucide-react";
import { getApiBase } from "@/lib/api/client";
import { useHealth } from "@/lib/hooks/use-health";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { Input } from "@/components/ui/input";
import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

function StatusBadge({ status }: { status: string }) {
  const normalized = status.toLowerCase();
  const isHealthy =
    normalized.includes("connected") ||
    normalized.includes("healthy") ||
    normalized.includes("ok") ||
    normalized === "true";

  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-md px-2 py-0.5 text-xs font-medium",
        isHealthy
          ? "bg-emerald-500/10 text-emerald-700 dark:text-emerald-400"
          : "bg-destructive/10 text-destructive"
      )}
    >
      {isHealthy ? (
        <CheckCircle2 className="size-3" />
      ) : (
        <XCircle className="size-3" />
      )}
      {status}
    </span>
  );
}

const services = [
  { key: "gemini", label: "Gemini API", icon: Sparkles },
  { key: "backend", label: "Backend", icon: Server },
  { key: "qdrant", label: "Qdrant", icon: Database },
  { key: "postgres", label: "Postgres", icon: Database },
] as const;

export function SettingsPanel() {
  const { health, loading, error, refetch } = useHealth();
  const [urlInput, setUrlInput] = useState("");

  useEffect(() => {
    setUrlInput(getApiBase());
  }, []);

  const handleSaveUrl = () => {
    if (!urlInput.trim()) return;
    localStorage.setItem("rag_backend_url", urlInput.trim());
    toast.success("API URL updated successfully");
    refetch();
  };

  return (
    <div className="space-y-6">
      {error && (
        <div className="flex items-center justify-between gap-3 rounded-xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <div className="flex items-center gap-2">
            <AlertCircle className="size-4 shrink-0" />
            <span>{error}</span>
          </div>
          <button
            className="text-xs underline"
            onClick={() => refetch()}
          >
            Retry
          </button>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2">
        {services.map((service, index) => {
          const Icon = service.icon;
          const status =
            health?.[service.key as keyof typeof health]?.toString() ??
            "unknown";

          return (
            <motion.div
              key={service.key}
              initial={{ opacity: 0, y: 12 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: index * 0.05 }}
            >
              <Card>
                <CardHeader className="flex flex-row items-center justify-between pb-2">
                  <div className="flex items-center gap-2">
                    <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                      <Icon className="size-4" />
                    </div>
                    <CardTitle className="text-sm font-medium">
                      {service.label}
                    </CardTitle>
                  </div>
                  {loading ? (
                    <Skeleton className="h-5 w-20" />
                  ) : (
                    <StatusBadge status={status} />
                  )}
                </CardHeader>
              </Card>
            </motion.div>
          );
        })}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Environment Settings</CardTitle>
          <CardDescription>Runtime configuration and system info</CardDescription>
        </CardHeader>
        <CardContent className="space-y-4 text-sm">
          {loading ? (
            <Skeleton className="h-24 w-full" />
          ) : (
            <>
              <div className="flex flex-col gap-2 border-b border-border/60 pb-3">
                <span className="text-muted-foreground font-medium">API Base URL</span>
                <div className="flex gap-2 max-w-md">
                  <Input
                    value={urlInput}
                    onChange={(e) => setUrlInput(e.target.value)}
                    placeholder="http://localhost:8000"
                    className="font-mono text-xs"
                  />
                  <Button size="sm" onClick={handleSaveUrl}>
                    Save
                  </Button>
                </div>
              </div>
              <div className="flex justify-between border-b border-border/60 py-2">
                <span className="text-muted-foreground">Environment</span>
                <span>{health?.environment ?? "unknown"}</span>
              </div>
              <div className="flex justify-between border-b border-border/60 py-2">
                <span className="text-muted-foreground">Backend Status</span>
                <StatusBadge status={health?.status ?? "unknown"} />
              </div>
              {health?.version && (
                <div className="flex justify-between py-2">
                  <span className="text-muted-foreground">Version</span>
                  <span>{health.version}</span>
                </div>
              )}
            </>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
