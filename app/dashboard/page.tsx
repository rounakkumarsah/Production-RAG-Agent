import { AppShell } from "@/components/layout/app-shell";
import { DashboardContent } from "@/components/dashboard/dashboard-content";

export default function DashboardPage() {
  return (
    <AppShell activePath="/dashboard">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Dashboard
        </h1>
        <p className="mt-1 text-muted-foreground">
          Overview of your knowledge base and recent activity
        </p>
      </div>

      <DashboardContent />
    </AppShell>
  );
}
