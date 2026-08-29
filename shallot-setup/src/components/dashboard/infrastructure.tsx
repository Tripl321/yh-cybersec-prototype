"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Server } from "lucide-react";

export function InfrastructurePage() {
  return (
    <div className="flex flex-col gap-6 p-6">
      <div>
        <h1 className="text-2xl font-bold tracking-tight text-foreground">
          Infrastructure
        </h1>
        <p className="text-sm text-muted-foreground mt-1">
          Services, containers, and deployment status
        </p>
      </div>
      <Card className="shadow-[0_1px_3px_oklch(0_0_0/0.04),0_4px_24px_oklch(0_0_0/0.06)] border-border/40 bg-card/80">
        <CardContent className="p-8 flex flex-col items-center gap-3 text-muted-foreground">
          <Server className="size-8" />
          <p className="text-sm">Coming soon</p>
        </CardContent>
      </Card>
    </div>
  );
}
