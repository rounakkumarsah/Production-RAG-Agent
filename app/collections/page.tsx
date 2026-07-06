import { AppShell } from "@/components/layout/app-shell";
import { CollectionsManager } from "@/components/collections/collections-manager";

export default function CollectionsPage() {
  return (
    <AppShell activePath="/collections">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Collections
        </h1>
        <p className="mt-1 text-muted-foreground">
          Create and manage document collections
        </p>
      </div>

      <CollectionsManager />
    </AppShell>
  );
}
