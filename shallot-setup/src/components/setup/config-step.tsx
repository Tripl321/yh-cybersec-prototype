"use client";

import { Badge } from "@/components/ui/badge";
import {
  CheckCircle2,
  Circle,
  Shield,
  ExternalLink,
  Cpu,
  Database,
  Lock,
  Globe,
  Eye,
} from "lucide-react";

export interface GRCControl {
  id: string;
  framework: string;
  control: string;
  description: string;
  status: "implemented" | "partial" | "planned";
  component?: string;
}

interface ConfigStepProps {
  controls: GRCControl[];
  onStart: () => void;
  onStartDisabled: boolean;
}

const STATUS_ICON: Record<string, typeof CheckCircle2> = {
  implemented: CheckCircle2,
  partial: Circle,
  planned: Circle,
};

const STATUS_COLOR: Record<string, string> = {
  implemented: "text-emerald-600 dark:text-emerald-400",
  partial: "text-amber-600 dark:text-amber-400",
  planned: "text-muted-foreground/40",
};

const STATUS_BADGE: Record<string, string> = {
  implemented: "bg-emerald-500/10 text-emerald-700 dark:text-emerald-300 border-emerald-500/20",
  partial: "bg-amber-500/10 text-amber-700 dark:text-amber-300 border-amber-500/20",
  planned: "bg-muted/40 text-muted-foreground/60 border-border/40",
};

const COMPONENT_ICONS: Record<string, typeof Shield> = {
  "fido2-hardware": Lock,
  "scrubber-aes-siv": Shield,
  "cub-agent-llm": Cpu,
  "siem-integration": Database,
  "web-authn": Globe,
  "locha-heartbeat": Eye,
};

export function ConfigStep({ controls, onStart, onStartDisabled }: ConfigStepProps) {
  return (
    <div className="flex flex-col gap-6">
      <p className="text-sm text-muted-foreground leading-relaxed">
        Review GRC control coverage across your installed components.
        These controls will be validated during deployment.
      </p>

      <div className="flex flex-col gap-1.5">
        {controls.map((ctrl) => {
          const StatusIcon = STATUS_ICON[ctrl.status];
          const CompIcon = COMPONENT_ICONS[ctrl.component || ""] || Shield;
          return (
            <div
              key={ctrl.id}
              className="flex items-center gap-3 rounded-xl px-3 py-2.5 transition-colors duration-150 hover:bg-muted/20"
            >
              <CompIcon className="size-4 text-muted-foreground/40 shrink-0" />
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <span className="text-sm font-medium text-foreground/90 truncate">
                    {ctrl.control}
                  </span>
                  <Badge
                    variant="outline"
                    className={`text-[10px] px-1.5 py-0 h-5 rounded-md ${STATUS_BADGE[ctrl.status]}`}
                  >
                    {ctrl.framework}
                  </Badge>
                </div>
                <p className="text-xs text-muted-foreground/60 truncate">
                  {ctrl.description}
                </p>
              </div>
              <StatusIcon
                className={`size-4 shrink-0 ${STATUS_COLOR[ctrl.status]}`}
              />
            </div>
          );
        })}
      </div>

      <button
        onClick={onStart}
        disabled={onStartDisabled}
        className="self-end inline-flex items-center gap-2 rounded-xl bg-emerald-600 px-5 py-2.5 text-sm font-medium text-white shadow-[0_1px_2px_oklch(0_0_0/0.1),0_2px_8px_oklch(0.42_0.095_155/0.15)] transition-all duration-150 hover:shadow-[0_1px_3px_oklch(0_0_0/0.12),0_4px_12px_oklch(0.42_0.095_155/0.2)] hover:scale-[1.02] active:scale-[0.98] disabled:opacity-40 disabled:hover:scale-100"
      >
        <CheckCircle2 className="size-4" />
        Start Deployment
      </button>
    </div>
  );
}
