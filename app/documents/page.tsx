import { AppShell } from "@/components/layout/app-shell";
import { DocumentsList } from "@/components/documents/documents-list";

export default function DocumentsPage() {
  return (
    <AppShell activePath="/documents">
      <div className="mb-8">
        <h1 className="text-2xl font-bold tracking-tight sm:text-3xl">
          Documents
        </h1>
        <p className="mt-1 text-muted-foreground">
          View and manage all uploaded documents
        </p>
      </div>

      <DocumentsList />
    </AppShell>
  );
}
