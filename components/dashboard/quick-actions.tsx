"use client";

import Link from "next/link";
import { motion } from "framer-motion";
import {
  Upload,
  MessageSquare,
  Search,
  Settings2,
  ArrowUpRight,
} from "lucide-react";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { quickActions } from "@/lib/types";
import { cn } from "@/lib/utils";

const iconMap = {
  upload: Upload,
  message: MessageSquare,
  search: Search,
  settings: Settings2,
};

export function QuickActions() {
  return (
    <motion.div
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.4, delay: 0.15 }}
    >
      <Card>
        <CardHeader>
          <CardTitle>Quick Actions</CardTitle>
          <CardDescription>Common tasks to get started quickly</CardDescription>
        </CardHeader>
        <CardContent className="grid gap-3 sm:grid-cols-2">
          {quickActions.map((action, index) => {
            const Icon = iconMap[action.icon];
            const isPrimary = action.id === "upload";

            const content = (
              <>
                <div
                  className={cn(
                    "flex size-10 shrink-0 items-center justify-center rounded-lg",
                    isPrimary
                      ? "bg-primary-foreground/15"
                      : "bg-primary/10 text-primary"
                  )}
                >
                  <Icon className="size-4" />
                </div>
                <div className="min-w-0 flex-1">
                  <p className="text-sm font-medium">{action.label}</p>
                  <p
                    className={cn(
                      "mt-0.5 truncate text-xs",
                      isPrimary
                        ? "text-primary-foreground/70"
                        : "text-muted-foreground"
                    )}
                  >
                    {action.description}
                  </p>
                </div>
                <ArrowUpRight
                  className={cn(
                    "size-4 shrink-0 opacity-0 transition-all group-hover:translate-x-0.5 group-hover:-translate-y-0.5 group-hover:opacity-100",
                    isPrimary
                      ? "text-primary-foreground/60"
                      : "text-muted-foreground"
                  )}
                />
              </>
            );

            return (
              <motion.div
                key={action.id}
                initial={{ opacity: 0, scale: 0.96 }}
                animate={{ opacity: 1, scale: 1 }}
                transition={{ duration: 0.3, delay: 0.2 + index * 0.05 }}
              >
                {action.id === "upload" ? (
                  <Button
                    variant="default"
                    className="group h-auto w-full justify-start gap-3 px-4 py-4 text-left"
                    onClick={() => {
                      const el = document.getElementById("upload");
                      el?.scrollIntoView({ behavior: "smooth" });
                    }}
                  >
                    {content}
                  </Button>
                ) : (
                  <Button
                    variant="outline"
                    className="group h-auto w-full justify-start gap-3 px-4 py-4 text-left hover:border-primary/30 hover:bg-primary/5"
                    asChild
                  >
                    <Link href={action.href}>{content}</Link>
                  </Button>
                )}
              </motion.div>
            );
          })}
        </CardContent>
      </Card>
    </motion.div>
  );
}
