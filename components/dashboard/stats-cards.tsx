"use client";

import { motion } from "framer-motion";
import { AlertCircle, FileText, HardDrive, Layers } from "lucide-react";
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { Skeleton } from "@/components/ui/skeleton";
import type { DashboardStats } from "@/lib/types";
import { formatBytes } from "@/lib/utils";

interface StatsCardsProps {
  stats: DashboardStats;
  loading?: boolean;
  error?: string | null;
}

export function StatsCards({ stats, loading, error }: StatsCardsProps) {
  const storagePercent = stats.storageLimit
    ? Math.min(
        100,
        Math.round((stats.storageUsed / stats.storageLimit) * 100)
      )
    : 0;

  const statItems = [
    {
      key: "documents",
      label: "Total Documents",
      value: stats.totalDocuments.toLocaleString(),
      icon: FileText,
      accent: "from-blue-500/10 to-blue-600/5",
      iconColor: "text-blue-600 dark:text-blue-400",
    },
    {
      key: "chunks",
      label: "Total Chunks",
      value: stats.totalChunks.toLocaleString(),
      icon: Layers,
      accent: "from-violet-500/10 to-violet-600/5",
      iconColor: "text-violet-600 dark:text-violet-400",
    },
  ];

  if (error) {
    return (
      <div className="flex items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
        <AlertCircle className="size-4 shrink-0" />
        <span>{error}</span>
      </div>
    );
  }

  return (
    <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-3">
      {statItems.map((stat, index) => (
        <motion.div
          key={stat.key}
          initial={{ opacity: 0, y: 16 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.4, delay: 0.05 * index }}
        >
          <Card className="relative overflow-hidden">
            <div
              className={`pointer-events-none absolute inset-0 bg-gradient-to-br ${stat.accent}`}
            />
            <CardHeader className="flex flex-row items-center justify-between pb-2">
              <CardTitle className="text-sm font-medium text-muted-foreground">
                {stat.label}
              </CardTitle>
              <div
                className={`flex size-9 items-center justify-center rounded-lg bg-background/80 ${stat.iconColor}`}
              >
                <stat.icon className="size-4" />
              </div>
            </CardHeader>
            <CardContent>
              {loading ? (
                <Skeleton className="h-9 w-24" />
              ) : (
                <p className="text-3xl font-bold tracking-tight">{stat.value}</p>
              )}
            </CardContent>
          </Card>
        </motion.div>
      ))}

      <motion.div
        initial={{ opacity: 0, y: 16 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.4, delay: 0.1 }}
        className="sm:col-span-2 xl:col-span-1"
      >
        <Card className="relative h-full overflow-hidden">
          <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-emerald-500/10 to-emerald-600/5" />
          <CardHeader className="flex flex-row items-center justify-between pb-2">
            <CardTitle className="text-sm font-medium text-muted-foreground">
              Storage Usage
            </CardTitle>
            <div className="flex size-9 items-center justify-center rounded-lg bg-background/80 text-emerald-600 dark:text-emerald-400">
              <HardDrive className="size-4" />
            </div>
          </CardHeader>
          <CardContent className="space-y-3">
            {loading ? (
              <>
                <Skeleton className="h-9 w-16" />
                <Skeleton className="h-2.5 w-full" />
              </>
            ) : (
              <>
                <div className="flex items-baseline justify-between">
                  <p className="text-3xl font-bold tracking-tight">
                    {storagePercent}%
                  </p>
                  <p className="text-xs text-muted-foreground">
                    {formatBytes(stats.storageUsed)} of{" "}
                    {formatBytes(stats.storageLimit)}
                  </p>
                </div>
                <Progress value={storagePercent} className="h-2.5" />
              </>
            )}
          </CardContent>
        </Card>
      </motion.div>
    </div>
  );
}
