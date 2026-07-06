"use client";

import { useCallback, useRef, useState } from "react";
import { motion } from "framer-motion";
import { CloudUpload, FileUp, Loader2, Sparkles } from "lucide-react";
import { toast } from "sonner";
import { uploadDocuments } from "@/lib/api/upload";
import { useApp } from "@/lib/context/app-context";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

interface UploadCardProps {
  disabled?: boolean;
  onUploadComplete?: () => void;
}

export function UploadCard({ disabled, onUploadComplete }: UploadCardProps) {
  const { activeCollectionId, refresh } = useApp();
  const inputRef = useRef<HTMLInputElement>(null);
  const [isDragging, setIsDragging] = useState(false);
  const [uploading, setUploading] = useState(false);
  const [uploadProgress, setUploadProgress] = useState(0);
  const [processing, setProcessing] = useState(false);

  const isDisabled = disabled || uploading || processing;

  const handleFiles = useCallback(
    async (files: FileList | File[]) => {
      const ALLOWED_EXTENSIONS = ['.pdf', '.docx', '.pptx', '.xlsx', '.csv', '.txt', '.md', '.markdown', '.png', '.jpg', '.jpeg', '.tiff', '.bmp', '.webp', '.json', '.log'];
      const uploadableFiles = Array.from(files).filter((file) => {
        const ext = '.' + file.name.split('.').pop()?.toLowerCase();
        return ALLOWED_EXTENSIONS.includes(ext);
      });

      if (uploadableFiles.length === 0) {
        toast.error("Please upload supported document formats only (.pdf, .docx, .pptx, .xlsx, .csv, .txt, .md, .markdown, .png, .jpg, .jpeg, .tiff, .bmp, .webp, .json, .log).");
        return;
      }

      setUploading(true);
      setUploadProgress(0);

      let slowUploadTimer: NodeJS.Timeout | null = null;
      let toastId: string | number | null = null;

      slowUploadTimer = setTimeout(() => {
        toastId = toast.loading(
          "Embedding document... Large documents may take several minutes because embeddings are being generated.",
          { duration: Infinity }
        );
      }, 5000);

      try {
        const results = await uploadDocuments(uploadableFiles, {
          collectionId: activeCollectionId,
          onProgress: ({ progress }) => setUploadProgress(progress),
        });

        if (slowUploadTimer) clearTimeout(slowUploadTimer);
        if (toastId) toast.dismiss(toastId);

        setUploading(false);
        setProcessing(true);

        const alreadyExistsCount = results.filter((doc) => doc.status === "already_exists").length;
        const succeededCount = results.filter((doc) => doc.status === "indexed" || doc.status === "processing").length;
        const failedDocs = results.filter((doc) => doc.status === "failed");

        if (failedDocs.length > 0) {
          const errMsg = failedDocs
            .map((doc) => `${doc.name}: ${doc.error || "Processing failed"}`)
            .join(", ");
          if (succeededCount > 0) {
            toast.success(`${succeededCount} files uploaded successfully`);
          }
          throw new Error(errMsg);
        }

        if (alreadyExistsCount > 0 && succeededCount === 0) {
          toast.info("Already Indexed");
        } else if (alreadyExistsCount > 0) {
          toast.success(`${succeededCount} files uploaded, ${alreadyExistsCount} files Already Indexed`);
        } else {
          toast.success(
            uploadableFiles.length === 1
              ? `"${uploadableFiles[0].name}" uploaded successfully`
              : `${uploadableFiles.length} files uploaded successfully`
          );
        }

        refresh();
        onUploadComplete?.();
      } catch (err) {
        if (slowUploadTimer) clearTimeout(slowUploadTimer);
        if (toastId) toast.dismiss(toastId);
        toast.error(
          err instanceof Error ? err.message : "Upload failed"
        );
      } finally {
        setUploading(false);
        setProcessing(false);
        setUploadProgress(0);
        if (inputRef.current) inputRef.current.value = "";
      }
    },
    [activeCollectionId, onUploadComplete, refresh]
  );

  const handleDragOver = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      if (!isDisabled) setIsDragging(true);
    },
    [isDisabled]
  );

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setIsDragging(false);
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      setIsDragging(false);
      if (isDisabled || !e.dataTransfer.files.length) return;
      handleFiles(e.dataTransfer.files);
    },
    [handleFiles, isDisabled]
  );

  return (
    <motion.div
      id="upload"
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.1 }}
    >
      <Card className="relative overflow-hidden border-dashed">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-violet-500/5" />
        <CardHeader>
          <div className="flex items-center gap-2">
            <div className="flex size-9 items-center justify-center rounded-lg bg-primary/10 text-primary">
              <CloudUpload className="size-4" />
            </div>
            <div>
              <CardTitle>Upload Documents</CardTitle>
              <CardDescription>
                Drop files here or browse from your device
              </CardDescription>
            </div>
          </div>
        </CardHeader>
        <CardContent>
          <input
            ref={inputRef}
            type="file"
            accept=".pdf,application/pdf,.docx,application/vnd.openxmlformats-officedocument.wordprocessingml.document,.pptx,application/vnd.openxmlformats-officedocument.presentationml.presentation,.xlsx,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet,.csv,text/csv,.txt,text/plain,.md,text/markdown,.markdown,text/markdown,.png,image/png,.jpg,image/jpeg,.jpeg,image/jpeg,.tiff,image/tiff,.bmp,image/bmp,.webp,image/webp,.json,application/json,.log,text/plain"
            multiple
            className="hidden"
            disabled={isDisabled}
            onChange={(e) => {
              if (e.target.files?.length) handleFiles(e.target.files);
            }}
          />
          <div
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onDrop={handleDrop}
            className={cn(
              "relative flex min-h-[180px] flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-all duration-300",
              isDragging
                ? "border-primary bg-primary/5 scale-[1.01]"
                : "border-border/80 hover:border-primary/40 hover:bg-muted/30",
              isDisabled && "pointer-events-none opacity-60"
            )}
          >
            <motion.div
              animate={
                isDragging ? { scale: 1.1, y: -4 } : { scale: 1, y: 0 }
              }
              transition={{ type: "spring", stiffness: 300, damping: 20 }}
              className="mb-4 flex size-14 items-center justify-center rounded-2xl bg-primary/10 text-primary"
            >
              {uploading || processing ? (
                <Loader2 className="size-7 animate-spin" />
              ) : (
                <FileUp className="size-7" />
              )}
            </motion.div>
            <p className="text-sm font-medium">
              {uploading
                ? `Uploading… ${uploadProgress}%`
                : processing
                  ? "Processing documents…"
                  : isDragging
                    ? "Release to upload"
                    : "Drag & drop your files"}
            </p>
            <p className="mt-1 text-xs text-muted-foreground">
              PDF, DOCX, PPTX, XLSX, CSV, TXT, MD files — up to 50 MB each
            </p>
            {(uploading || processing) && (
              <Progress
                value={uploading ? uploadProgress : undefined}
                className="mt-4 h-2 w-full max-w-xs"
              />
            )}
            <Button
              className="mt-5"
              size="sm"
              disabled={isDisabled}
              onClick={() => inputRef.current?.click()}
            >
              <Sparkles className="size-3.5" />
              Browse Files
            </Button>
          </div>
        </CardContent>
      </Card>
    </motion.div>
  );
}
