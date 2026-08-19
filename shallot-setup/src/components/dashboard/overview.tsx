"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Progress } from "@/components/ui/progress";
import { Separator } from "@/components/ui/separator";
import {
  ShieldCheck,
  Cpu,
  Server,
  Brain,
  Activity,
  AlertTriangle,
  CheckCircle2,
  Clock,
  Radio,
} from "lucide-react";

const SERVICES = [
  { name: "cub-agent", status: "running" as const, icon: Brain, port: "—" },
  { name: "Ollama", status: "running" as const, icon: Cpu, port: "11434" },
  { name: "Wazuh Manager", status: "running" as const, icon: Server, port: "55000" },
  { name: "Wazuh Indexer", status: "running" as const, icon: Server, port: "9200" },
  { name: "Hanko", status: "running" as const, icon: ShieldCheck, port: "8000" },
  { name: "Supermemory", status: "stopped" as const, icon: Brain, port: "6767" },
  { name: "Latitude", status: "stopped" as const, icon: Activity, port: "3000" },
];

const STATUS_COLOR = {
  running: "bg-emerald-500",
  stopped: "bg-muted-foreground/30",
  error: "bg-destructive",
} as const;

const RECENT_EVENTS = [
  { time: "14:32:01", event: "FIDO2 assertion verified", level: "info" },
  { time: "14:31:45", event: "Heartbeat received from BRICKA-01", level: "info" },
  { time: "14:30:12", event: "GRC event emitted: AC-2 (NIST)", level: "info" },
  { time: "14:28:03", event: "Scrubber redacted 2 entities", level: "info" },
  { time: "14:25:17", event: "HITL approval: CONFIDENTIAL action", level: "warning" },
  { time: "14:22:44", event: "Egress block: unauthorized cloud route", level: "error" },
];

export function OverviewPage() {
  const running = SERVICES.filter((s) => s.status === "running").length;
  const total = SERVICES.length;

  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Overview
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          SHALLOT system health and activity
        </p>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-emerald-500/10">
                <CheckCircle2 className="size-5 text-emerald-600 dark:text-emerald-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">
                  {running}/{total}
                </p>
                <p className="text-xs text-muted-foreground">Services Online</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
                <Cpu className="size-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">2</p>
                <p className="text-xs text-muted-foreground">Devices Connected</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-amber-500/10">
                <ShieldCheck className="size-5 text-amber-600 dark:text-amber-400" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">56/61</p>
                <p className="text-xs text-muted-foreground">GRC Controls</p>
              </div>
            </div>
          </CardContent>
        </Card>

        <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
          <CardContent className="p-4">
            <div className="flex items-center gap-3">
              <div className="flex size-10 items-center justify-center rounded-xl bg-primary/10">
                <Radio className="size-5 text-primary" />
              </div>
              <div>
                <p className="text-2xl font-bold text-foreground">Active</p>
                <p className="text-xs text-muted-foreground">LoRa Heartbeat</p>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Services */}
        <Card className="lg:col-span-2 shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Services</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-col gap-2">
              {SERVICES.map((svc) => {
                const Icon = svc.icon;
                return (
                  <div
                    key={svc.name}
                    className="flex items-center gap-3 rounded-xl px-3 py-2 transition-colors hover:bg-muted/20"
                  >
                    <div
                      className={`size-2 rounded-full ${STATUS_COLOR[svc.status]}`}
                    />
                    <Icon className="size-4 text-muted-foreground/60" />
                    <span className="flex-1 text-sm font-medium text-foreground">
                      {svc.name}
                    </span>
                    <span className="text-xs font-mono text-muted-foreground/50">
                      :{svc.port}
                    </span>
                    <Badge
                      variant={svc.status === "running" ? "secondary" : "outline"}
                      className="text-[10px] px-1.5 py-0 h-5 rounded-md"
                    >
                      {svc.status}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>

        {/* Recent activity */}
        <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
          <CardHeader className="pb-3">
            <CardTitle className="text-sm font-semibold">Recent Activity</CardTitle>
          </CardHeader>
          <CardContent className="px-4 pb-4">
            <div className="flex flex-col gap-2">
              {RECENT_EVENTS.map((evt, i) => (
                <div key={i} className="flex items-start gap-2.5">
                  <span className="text-[10px] font-mono text-muted-foreground/50 mt-0.5 shrink-0">
                    {evt.time}
                  </span>
                  <div className="flex-1 min-w-0">
                    <p className="text-xs text-foreground/80 leading-relaxed truncate">
                      {evt.event}
                    </p>
                  </div>
                  {evt.level === "error" && (
                    <AlertTriangle className="size-3.5 text-destructive shrink-0 mt-0.5" />
                  )}
                  {evt.level === "warning" && (
                    <AlertTriangle className="size-3.5 text-amber-500 shrink-0 mt-0.5" />
                  )}
                </div>
              ))}
            </div>
          </CardContent>
        </Card>
      </div>

      {/* System health bar */}
      <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
        <CardContent className="p-4">
          <div className="flex items-center gap-4">
            <span className="text-sm font-medium text-foreground shrink-0">
              System Health
            </span>
            <Progress value={(running / total) * 100} className="h-2 flex-1 bg-muted/40" />
            <span className="text-sm font-semibold text-foreground shrink-0">
              {Math.round((running / total) * 100)}%
            </span>
          </div>
        </CardContent>
      </Card>
    </div>
  );
}
