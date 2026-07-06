"use client";

import { useState } from "react";
import { motion } from "framer-motion";
import {
  AlertCircle,
  Check,
  FolderOpen,
  Loader2,
  Plus,
  Trash2,
} from "lucide-react";
import { toast } from "sonner";
import { assignDocumentToCollection } from "@/lib/api/documents";
import {
  createCollection,
  deleteCollection,
} from "@/lib/api/collections";
import { useApp } from "@/lib/context/app-context";
import { useCollections } from "@/lib/hooks/use-collections";
import { useDocuments } from "@/lib/hooks/use-documents";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from "@/components/ui/dialog";
import { Input } from "@/components/ui/input";
import { Skeleton } from "@/components/ui/skeleton";
import { cn, formatRelativeTime } from "@/lib/utils";

export function CollectionsManager() {
  const { activeCollectionId, setActiveCollectionId, refresh } = useApp();
  const {
    collections,
    loading: collectionsLoading,
    error: collectionsError,
    refetch: refetchCollections,
  } = useCollections();
  const { documents, loading: documentsLoading, refetch: refetchDocuments } =
    useDocuments();
  const [newName, setNewName] = useState("");
  const [creating, setCreating] = useState(false);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [deletingId, setDeletingId] = useState<string | null>(null);
  const [assigningId, setAssigningId] = useState<string | null>(null);

  const handleCreate = async () => {
    if (!newName.trim()) return;
    setCreating(true);
    try {
      const collection = await createCollection(newName.trim());
      toast.success(`Collection "${collection.name}" created`);
      setNewName("");
      setDialogOpen(false);
      refresh();
      refetchCollections();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Failed to create");
    } finally {
      setCreating(false);
    }
  };

  const handleDeleteCollection = async (id: string, name: string) => {
    setDeletingId(id);
    try {
      await deleteCollection(id);
      if (activeCollectionId === id) setActiveCollectionId(null);
      toast.success(`Collection "${name}" deleted`);
      refresh();
      refetchCollections();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Delete failed");
    } finally {
      setDeletingId(null);
    }
  };

  const handleAssign = async (documentId: string, collectionId: string | null) => {
    setAssigningId(documentId);
    try {
      await assignDocumentToCollection(documentId, collectionId);
      toast.success("Document assigned");
      refresh();
      refetchDocuments();
    } catch (err) {
      toast.error(err instanceof Error ? err.message : "Assign failed");
    } finally {
      setAssigningId(null);
    }
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <p className="text-sm text-muted-foreground">
          Organize documents into collections and switch active context
        </p>
        <Dialog open={dialogOpen} onOpenChange={setDialogOpen}>
          <DialogTrigger asChild>
            <Button size="sm">
              <Plus className="size-4" />
              New Collection
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Create Collection</DialogTitle>
              <DialogDescription>
                Group related documents for targeted queries
              </DialogDescription>
            </DialogHeader>
            <div className="flex gap-2">
              <Input
                placeholder="Collection name"
                value={newName}
                onChange={(e) => setNewName(e.target.value)}
                onKeyDown={(e) => e.key === "Enter" && handleCreate()}
              />
              <Button disabled={creating || !newName.trim()} onClick={handleCreate}>
                {creating ? (
                  <Loader2 className="size-4 animate-spin" />
                ) : (
                  "Create"
                )}
              </Button>
            </div>
          </DialogContent>
        </Dialog>
      </div>

      {collectionsError && (
        <div className="flex items-center gap-3 rounded-xl border border-destructive/20 bg-destructive/5 px-4 py-3 text-sm text-destructive">
          <AlertCircle className="size-4 shrink-0" />
          <span>{collectionsError}</span>
        </div>
      )}

      <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {collectionsLoading ? (
          Array.from({ length: 3 }).map((_, i) => (
            <Skeleton key={i} className="h-36 rounded-xl" />
          ))
        ) : collections.length === 0 ? (
          <Card className="sm:col-span-2 lg:col-span-3">
            <CardContent className="py-12 text-center text-sm text-muted-foreground">
              No collections yet. Create one to organize your documents.
            </CardContent>
          </Card>
        ) : (
          collections.map((collection, index) => {
            const isActive = activeCollectionId === collection.id;
            return (
              <motion.div
                key={collection.id}
                initial={{ opacity: 0, y: 12 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ delay: index * 0.05 }}
              >
                <Card
                  className={cn(
                    "relative overflow-hidden transition-colors",
                    isActive && "border-primary/50 ring-1 ring-primary/20"
                  )}
                >
                  <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/5 to-violet-500/5" />
                  <CardHeader>
                    <div className="flex items-start justify-between gap-2">
                      <div className="flex items-center gap-2">
                        <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
                          <FolderOpen className="size-4" />
                        </div>
                        <div>
                          <CardTitle className="text-base">
                            {collection.name}
                          </CardTitle>
                          <CardDescription>
                            {collection.documentCount} documents ·{" "}
                            {formatRelativeTime(collection.createdAt)}
                          </CardDescription>
                        </div>
                      </div>
                      {isActive && (
                        <Badge variant="success">
                          <Check className="size-3" />
                          Active
                        </Badge>
                      )}
                    </div>
                  </CardHeader>
                  <CardContent className="flex gap-2">
                    <Button
                      size="sm"
                      variant={isActive ? "secondary" : "default"}
                      className="flex-1"
                      onClick={() =>
                        setActiveCollectionId(isActive ? null : collection.id)
                      }
                    >
                      {isActive ? "Clear Active" : "Set Active"}
                    </Button>
                    <Button
                      size="sm"
                      variant="ghost"
                      className="text-muted-foreground hover:text-destructive"
                      disabled={deletingId === collection.id}
                      onClick={() =>
                        handleDeleteCollection(collection.id, collection.name)
                      }
                    >
                      {deletingId === collection.id ? (
                        <Loader2 className="size-4 animate-spin" />
                      ) : (
                        <Trash2 className="size-4" />
                      )}
                    </Button>
                  </CardContent>
                </Card>
              </motion.div>
            );
          })
        )}
      </div>

      <Card>
        <CardHeader>
          <CardTitle>Assign Documents</CardTitle>
          <CardDescription>
            Link uploaded documents to a collection
          </CardDescription>
        </CardHeader>
        <CardContent className="px-0">
          {documentsLoading ? (
            <div className="space-y-3 px-6">
              {Array.from({ length: 4 }).map((_, i) => (
                <Skeleton key={i} className="h-12 w-full" />
              ))}
            </div>
          ) : documents.length === 0 ? (
            <p className="px-6 py-8 text-center text-sm text-muted-foreground">
              Upload documents first to assign them to collections.
            </p>
          ) : (
            <ul className="divide-y divide-border/60">
              {documents.map((doc) => (
                <li
                  key={doc.id}
                  className="flex flex-col gap-3 px-6 py-4 sm:flex-row sm:items-center sm:justify-between"
                >
                  <div className="min-w-0">
                    <p className="truncate text-sm font-medium">{doc.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {doc.collectionId
                        ? `In collection ${doc.collectionId}`
                        : "Not assigned"}
                    </p>
                  </div>
                  <div className="flex flex-wrap gap-2">
                    <Button
                      size="sm"
                      variant="outline"
                      disabled={assigningId === doc.id}
                      onClick={() => handleAssign(doc.id, null)}
                    >
                      Unassigned
                    </Button>
                    {collections.map((collection) => (
                      <Button
                        key={collection.id}
                        size="sm"
                        variant={
                          doc.collectionId === collection.id
                            ? "default"
                            : "outline"
                        }
                        disabled={assigningId === doc.id}
                        onClick={() => handleAssign(doc.id, collection.id)}
                      >
                        {collection.name}
                      </Button>
                    ))}
                  </div>
                </li>
              ))}
            </ul>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
