"use client";

import { StatsCards } from "@/components/dashboard/stats-cards";
import { QuickActions } from "@/components/dashboard/quick-actions";
import { RecentDocuments } from "@/components/dashboard/recent-documents";
import { UploadCard } from "@/components/dashboard/upload-card";
import { HealthStatus } from "@/components/dashboard/health-status";
import { useDocuments } from "@/lib/hooks/use-documents";

export function DashboardContent() {
  const { documents, stats, loading, error, refetch } = useDocuments({
    pollProcessing: true,
  });

  const hasProcessing = documents.some((doc) => doc.status === "processing");

  return (
    <div className="space-y-6">
      <StatsCards stats={stats} loading={loading} error={error} />
      <HealthStatus />

      <div className="grid gap-6 lg:grid-cols-5">
        <div className="lg:col-span-3">
          <UploadCard
            disabled={false}
            onUploadComplete={refetch}
          />
        </div>
        <div className="lg:col-span-2">
          <QuickActions />
        </div>
      </div>

      <RecentDocuments
        documents={documents}
        loading={loading}
        error={error}
      />
    </div>
  );
}
