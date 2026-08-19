"use client";

import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { CheckCircle2, Loader2, Zap, ArrowRight } from "lucide-react";

export interface FirmwareTarget {
  device: string;
  port: string;
  firmware: string;
  version: string;
  progress: number;
  status: "queued" | "flashing" | "done" | "error";
  error?: string;
}

interface FirmwareStepProps {
  targets: FirmwareTarget[];
  onNext: () => void;
  canNext: boolean;
}

const STATUS_CONFIG = {
  queued: {
    icon: ArrowRight,
    color: "text-muted-foreground/50",
    bg: "bg-muted/40",
    label: "Queued",
  },
  flashing: {
    icon: Loader2,
    color: "text-primary",
    bg: "bg-primary/10",
    label: "Flashing",
  },
  done: {
    icon: CheckCircle2,
    color: "text-emerald-600 dark:text-emerald-400",
    bg: "bg-emerald-500/10",
    label: "Done",
  },
  error: {
    icon: Zap,
    color: "text-destructive",
    bg: "bg-destructive/10",
    label: "Error",
  },
} as const;

export function FirmwareStep({ targets, onNext, canNext }: FirmwareStepProps) {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted-foreground">
        Firmware will be compiled and flashed to each device.
      </p>

      <div className="flex flex-col gap-2">
        {targets.map((t) => {
          const cfg = STATUS_CONFIG[t.status];
          const Icon = cfg.icon;
          return (
            <div
              key={t.port}
              className="rounded-2xl border border-border/50 bg-background/30 px-4 py-3.5"
            >
              <div className="flex items-center gap-3 mb-2">
                <div
                  className={`flex size-9 items-center justify-center rounded-xl ${cfg.bg}`}
                >
                  <Icon
                    className={`size-4.5 ${cfg.color} ${
                      t.status === "flashing" ? "animate-spin" : ""
                    }`}
                  />
                </div>
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2">
                    <span className="text-sm font-medium text-foreground truncate">
                      {t.device}
                    </span>
                    <Badge
                      variant={t.status === "error" ? "destructive" : "secondary"}
                      className="text-[10px] px-1.5 py-0 h-5 rounded-md"
                    >
                      {cfg.label}
                    </Badge>
                  </div>
                  <span className="text-xs text-muted-foreground/70">
                    {t.firmware} {t.version}
                  </span>
                </div>
              </div>
              {(t.status === "flashing" || t.status === "done") && (
                <Progress
                  value={t.progress}
                  className="h-1.5 bg-muted/40"
                />
              )}
              {t.status === "error" && t.error && (
                <p className="text-xs text-destructive mt-2 font-mono">
                  {t.error}
                </p>
              )}
            </div>
          );
        })}
      </div>

      {canNext && (
        <button
          onClick={onNext}
          className="self-end inline-flex items-center gap-2 rounded-xl bg-primary px-5 py-2.5 text-sm font-medium text-primary-foreground shadow-[0_1px_2px_oklch(0_0_0/0.1),0_2px_8px_oklch(0.205_0.042_265/0.15)] transition-all duration-150 hover:shadow-[0_1px_3px_oklch(0_0_0/0.12),0_4px_12px_oklch(0.205_0.042_265/0.2)] hover:scale-[1.02] active:scale-[0.98]"
        >
          Configure Settings
          <ArrowRight className="size-4" />
        </button>
      )}
    </div>
  );
}
