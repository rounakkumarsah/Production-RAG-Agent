"use client";

import { motion } from "framer-motion";
import { CheckCircle2, XCircle, RefreshCw, Server } from "lucide-react";
import { useHealth } from "@/lib/hooks/use-health";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { Button } from "@/components/ui/button";

export function HealthStatus() {
  const { health, loading, error, refetch } = useHealth();

  const services = [
    { name: "Backend API", key: "backend", value: health?.backend },
    { name: "Google Gemini", key: "gemini", value: health?.gemini },
    { name: "PostgreSQL", key: "postgres", value: health?.postgres },
    { name: "Qdrant Vector DB", key: "qdrant", value: health?.qdrant },
  ];

  const getStatusColor = (val: string | undefined) => {
    const status = String(val ?? "unknown").toLowerCase();
    if (status === "connected" || status === "ok" || status === "healthy") {
      return "text-emerald-500 bg-emerald-500/10 border-emerald-500/20";
    }
    if (status === "not_connected" || status === "disconnected" || status === "failed") {
      return "text-rose-500 bg-rose-500/10 border-rose-500/20";
    }
    return "text-amber-500 bg-amber-500/10 border-amber-500/20";
  };

  const getStatusIcon = (val: string | undefined) => {
    const status = String(val ?? "unknown").toLowerCase();
    if (status === "connected" || status === "ok" || status === "healthy") {
      return <CheckCircle2 className="size-4" />;
    }
    if (status === "not_connected" || status === "disconnected" || status === "failed") {
      return <XCircle className="size-4" />;
    }
    return <RefreshCw className="size-4 animate-spin" />;
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
    >
      <Card className="relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-primary/5 via-transparent to-violet-500/5" />
        <CardHeader className="flex flex-row items-center justify-between pb-2">
          <div>
            <CardTitle className="text-base font-bold">System Health</CardTitle>
            <CardDescription>
              Status of backend services and dependencies
            </CardDescription>
          </div>
          <Button
            variant="ghost"
            size="icon"
            onClick={refetch}
            disabled={loading}
            className="size-8"
          >
            <RefreshCw className={`size-4 ${loading ? "animate-spin" : ""}`} />
          </Button>
        </CardHeader>
        <CardContent className="mt-2 grid gap-3 sm:grid-cols-2 md:grid-cols-4">
          {services.map((service) => (
            <div
              key={service.key}
              className={`flex items-center justify-between rounded-lg border px-3.5 py-2.5 text-sm transition-all duration-300 ${getStatusColor(
                service.value
              )}`}
            >
              <div className="flex items-center gap-2">
                <Server className="size-4 opacity-70" />
                <span className="font-medium text-foreground">{service.name}</span>
              </div>
              <div className="flex items-center gap-1.5 font-semibold capitalize">
                {getStatusIcon(service.value)}
                <span className="text-xs">
                  {service.value === "connected" || service.value === "ok" || service.value === "healthy"
                    ? "Online"
                    : service.value === "not_connected" || service.value === "disconnected" || service.value === "failed"
                      ? "Offline"
                      : "Unknown"}
                </span>
              </div>
            </div>
          ))}
        </CardContent>
      </Card>
    </motion.div>
  );
}
