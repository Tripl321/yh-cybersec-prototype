"use client";

import { useState } from "react";
import { SidebarProvider, SidebarInset } from "@/components/ui/sidebar";
import { AppSidebar, type Page } from "@/components/app-sidebar";
import { OverviewPage } from "@/components/dashboard/overview";
import { HardwarePage } from "@/components/dashboard/hardware";
import { InfrastructurePage } from "@/components/dashboard/infrastructure";
import { SecurityPage } from "@/components/dashboard/security";
import { ModelsPage } from "@/components/dashboard/models";
import { SettingsPage } from "@/components/dashboard/settings";

export default function DashboardPage() {
  const [page, setPage] = useState<Page>("overview");

  return (
    <SidebarProvider>
      <AppSidebar active={page} onNavigate={setPage} />
      <SidebarInset>
        <main className="flex-1 overflow-auto">
          {page === "overview" && <OverviewPage />}
          {page === "hardware" && <HardwarePage />}
          {page === "infrastructure" && <InfrastructurePage />}
          {page === "security" && <SecurityPage />}
          {page === "models" && <ModelsPage />}
          {page === "settings" && <SettingsPage />}
        </main>
      </SidebarInset>
    </SidebarProvider>
  );
}
